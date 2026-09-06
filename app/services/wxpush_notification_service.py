# -*- coding: utf-8 -*-
"""
WXPush (WeChat template message) notification service.

Delivers the Epic claim summary to a self-hosted wxpush deployment
(https://github.com/frankiejun/wxpush) via its ``POST /wxsend`` API.

WeChat caps template-message title fields at roughly 20 characters per field
without newlines, so the title carries a dense single-line result summary
(e.g. ``Epic 周免领取:新领2/共7款``). The content carries the full game list:
WeChat shows only its beginning in the native popup, and the complete message
is rendered on the wxpush ``/skin`` page when the template message is tapped.

Import boundary: this module must NOT import ``services.telegram_notification_service``
or ``services.epic_games_service`` — the test harness stubs dependencies per
module, and cross-importing another service would silently break that stubbing.
"""

import json
import os
from urllib.parse import urlsplit

import httpx
from loguru import logger

from services.epic_collection_summary_service import CollectionSummary

TITLE_FIELD_MAX_CHARS = 20
CONTENT_MAX_CHARS = 500


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def wxpush_notifications_enabled() -> bool:
    return bool(_env("WXPUSH_TOKEN") and _normalize_wxsend_endpoint())


def _normalize_wxsend_endpoint() -> str:
    """Return the full ``/wxsend`` URL, or "" when the endpoint is unusable."""
    endpoint = _env("WXPUSH_ENDPOINT")
    # Validate with an actual parse: a malformed value (e.g. "https://[broken")
    # must disable the channel, not raise later at delivery time.
    try:
        parts = urlsplit(endpoint)
    except ValueError:
        return ""
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc:
        return ""
    endpoint = endpoint.rstrip("/")
    if not endpoint.endswith("/wxsend"):
        endpoint += "/wxsend"
    return endpoint


def _default_skin_base_url() -> str:
    """Fallback tap-through target: wxpush's built-in markdown skin page."""
    parts = urlsplit(_normalize_wxsend_endpoint())
    if not parts.scheme or not parts.netloc:
        return ""
    return f"{parts.scheme}://{parts.netloc}/skin"


def _claim_status(summary: CollectionSummary) -> str:
    if summary.error_message and summary.newly_claimed_promotions:
        return "部分成功"
    if summary.error_message:
        return "失败"
    if summary.unconfirmed_promotions:
        return "需确认"
    return "成功"


def _clip_field(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars]


def _first_error_line(error: str) -> str:
    for line in error.splitlines():
        line = line.strip()
        if line:
            return line
    return error.strip()


def _format_games(games) -> str:
    if not games:
        return "无"
    return "\n".join(f"- {game.title or game.url or 'Unknown'}" for game in games)


def build_wxpush_title(summary: CollectionSummary) -> str:
    """
    Dense single-line title, hard-clipped to the WeChat field limit.

    Shapes:
    - all claimed:            ``Epic 周免领取:新领2/共7款``
    - all owned already:      ``Epic 周免领取:均已有/共7款``
    - partial / unconfirmed:  ``Epic 周免领取:新领2 失败1`` / ``...新领2 待确认1``
    - total failure:          ``Epic 周免领取失败:密码错误...``
    """
    status = _claim_status(summary)
    prefix = "Epic 周免领取"
    n_all = len(summary.all_promotions)
    n_new = len(summary.newly_claimed_promotions)
    n_failed = len(summary.failed_promotions)
    n_unconfirmed = len(summary.unconfirmed_promotions)

    if status == "失败":
        reason = _first_error_line(summary.error_message) or "未知原因"
        return _clip_field(f"{prefix}失败:{reason}", TITLE_FIELD_MAX_CHARS)

    segments = []
    if n_new:
        segments.append(f"新领{n_new}")
    elif n_all and status == "成功":
        segments.append("均已有")
    if n_failed:
        segments.append(f"失败{n_failed}")
    if n_unconfirmed:
        segments.append(f"待确认{n_unconfirmed}")
    if status == "部分成功" and not n_failed and not n_unconfirmed:
        segments.append("部分成功")

    tail = ""
    if not segments:
        segments.append(f"共{n_all}款")
    elif not n_failed and not n_unconfirmed and status != "部分成功":
        tail = f"/共{n_all}款"

    return _clip_field(f"{prefix}:{' '.join(segments)}{tail}", TITLE_FIELD_MAX_CHARS)


def build_wxpush_content(summary: CollectionSummary, *, account_label: str | None = None) -> str:
    """Full plain-text run report (markdown-lite), truncated at a safe size."""
    lines = []
    if account_label:
        lines.append(f"账号：{account_label}")
    lines.append(f"运行状态：{_claim_status(summary)}")

    sections = (
        ("本周游戏", summary.all_promotions),
        ("本次新领取", summary.newly_claimed_promotions),
        ("之前已领取", summary.previously_claimed_promotions),
    )
    for heading, games in sections:
        lines.extend([f"{heading}：", _format_games(games)])
    if summary.unconfirmed_promotions:
        lines.extend(["未确认成功：", _format_games(summary.unconfirmed_promotions)])
    if summary.failed_promotions:
        lines.extend(["领取失败：", _format_games(summary.failed_promotions)])
    if summary.error_message:
        lines.append(f"失败原因：{_first_error_line(summary.error_message)}")

    message = "\n".join(lines)
    if len(message) > CONTENT_MAX_CHARS:
        keep = CONTENT_MAX_CHARS - len("...(内容已截断)")
        message = message[:keep].rsplit("\n", 1)[0] + "\n...(内容已截断)"
    return message


def _success_message(text: str) -> str | None:
    """Confirm a wxpush response actually delivered, returning its msg.

    wxpush answers a successful ``/wxsend`` call with JSON whose ``msg`` starts
    with "Successfully sent messages"; anything else (an HTML skin page, a
    proxy error page, a malformed body) must not be reported as a delivery.
    """
    try:
        body = json.loads(text)
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    msg = body.get("msg")
    if not isinstance(msg, str) or not msg.startswith("Successfully sent messages"):
        return None
    return msg


async def send_collection_summary_to_wxpush(
    summary: CollectionSummary, *, account_label: str | None = None
) -> None:
    if not wxpush_notifications_enabled():
        logger.debug("WXPush notification is not configured; skipping delivery")
        return

    # Endpoint parsing, message construction and delivery all sit under the
    # same notification-only protection: a config or transport problem must
    # never surface as a claim-task failure.
    try:
        endpoint = _normalize_wxsend_endpoint()
        payload: dict[str, object] = {
            "title": build_wxpush_title(summary),
            "content": build_wxpush_content(summary, account_label=account_label),
        }
        if userid := _env("WXPUSH_USERID"):
            payload["userid"] = userid
        if template_id := _env("WXPUSH_TEMPLATE_ID"):
            payload["template_id"] = template_id
        if base_url := _env("WXPUSH_BASE_URL") or _default_skin_base_url():
            payload["base_url"] = base_url

        headers = {"Authorization": _env("WXPUSH_TOKEN")}
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as err:
        logger.warning("WXPush notification failed | status={}", err.response.status_code)
        return
    except httpx.HTTPError as err:
        logger.warning("WXPush notification failed | error_type={}", type(err).__name__)
        return
    except Exception as err:
        logger.warning(
            "WXPush notification failed before delivery | error_type={}", type(err).__name__
        )
        return

    # Reading and confirming the response must stay under notification-level
    # protection too: an unreadable body must not surface as a claim failure.
    try:
        text = response.text
        msg = _success_message(text)
    except Exception as err:
        logger.warning(
            "WXPush notification delivered but response could not be read | error_type={}",
            type(err).__name__,
        )
        return

    if msg:
        logger.success("WXPush claim summary sent | msg={}", msg)
    else:
        logger.warning(
            "WXPush notification delivered but response did not confirm success | status={}",
            response.status_code,
        )
