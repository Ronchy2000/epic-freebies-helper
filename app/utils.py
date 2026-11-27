# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
import sys
import traceback
from zoneinfo import ZoneInfo

from loguru import logger

_SECRET_ENV_KEYS = (
    "EPIC_PASSWORD",
    "EPIC_ACCOUNTS",
    "GLM_API_KEY",
    "GEMINI_API_KEY",
    "EPIC_TOTP_SECRET",
    "BROWSER_PROXY",
    "TELEGRAM_BOT_TOKEN",
    "WXPUSH_TOKEN",
)
_PROXY_CREDENTIAL_PATTERN = re.compile(r"([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^/\s@]+)(@)", re.I)
_TELEGRAM_TOKEN_PATTERN = re.compile(r"(https?://api\.telegram\.org/bot)([^/\s]+)")


def _mask_email_value(email: str) -> str:
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"
    masked_local = f"{local[:2]}***" if len(local) > 2 else f"{local[:1]}***"
    return f"{masked_local}@{domain}"


def _collect_sensitive_replacements() -> list[tuple[str, str]]:
    """Collect active secret values from env/settings for defense-in-depth redaction."""
    secrets: set[str] = set()
    emails: set[str] = set()

    def add_secret(value: str | None) -> None:
        if not value:
            return
        cleaned = value.strip()
        if len(cleaned) >= 3:
            secrets.add(cleaned)

    def add_accounts_blob(raw: str | None) -> None:
        if not raw:
            return
        add_secret(raw)
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            add_secret(stripped)
            if ":" in stripped:
                email_part, password_part = stripped.split(":", 1)
                email_part = email_part.strip()
                if "@" in email_part:
                    emails.add(email_part)
                add_secret(password_part)

    for key in _SECRET_ENV_KEYS:
        val = os.getenv(key)
        if not val:
            continue
        if key == "EPIC_ACCOUNTS":
            add_accounts_blob(val)
        else:
            add_secret(val)

    env_email = (os.getenv("EPIC_EMAIL") or "").strip()
    if "@" in env_email:
        emails.add(env_email)

    # Also read live settings object if already imported (handles multi-account swap_account
    # and values loaded from .env without triggering circular imports).
    settings_mod = sys.modules.get("settings")
    live_settings = getattr(settings_mod, "settings", None)
    if live_settings is not None:
        live_email = (getattr(live_settings, "EPIC_EMAIL", "") or "").strip()
        if "@" in live_email:
            emails.add(live_email)
        for attr in ("EPIC_PASSWORD", "GLM_API_KEY", "GEMINI_API_KEY", "BROWSER_PROXY"):
            secret_obj = getattr(live_settings, attr, None)
            if secret_obj is not None and hasattr(secret_obj, "get_secret_value"):
                add_secret(secret_obj.get_secret_value())
        accounts_obj = getattr(live_settings, "EPIC_ACCOUNTS", None)
        if accounts_obj is not None and hasattr(accounts_obj, "get_secret_value"):
            add_accounts_blob(accounts_obj.get_secret_value())

    replacements: list[tuple[str, str]] = []
    # Scrub longer values first so substrings don't break longer secret matches.
    for secret in sorted(secrets, key=len, reverse=True):
        replacements.append((secret, "***"))
    for email in sorted(emails, key=len, reverse=True):
        replacements.append((email, _mask_email_value(email)))
    return replacements


def redact_sensitive_text(text: str) -> str:
    """Scrub active credentials, tokens, proxy passwords, and raw emails from log text."""
    if not text:
        return text

    redacted = _PROXY_CREDENTIAL_PATTERN.sub(r"\1***\3", text)
    redacted = _TELEGRAM_TOKEN_PATTERN.sub(r"\1***", redacted)
    for target, replacement in _collect_sensitive_replacements():
        if target in redacted:
            redacted = redacted.replace(target, replacement)
    return redacted


def _redacting_patcher(record) -> None:
    record["time"] = record["time"].astimezone(ZoneInfo("Asia/Shanghai"))
    message = record.get("message")
    if isinstance(message, str):
        record["message"] = redact_sensitive_text(message)

    exc = record.get("exception")
    if exc is not None:
        # Format with stdlib traceback (never expands frame locals) and scrub any
        # secret values embedded inside exception messages for every sink (stdout & files).
        formatted = "".join(traceback.format_exception(exc.type, exc.value, exc.traceback))
        record["extra"]["_redacted_exception"] = redact_sensitive_text(formatted)
        record["exception"] = None
    else:
        record["extra"]["_redacted_exception"] = ""


def timezone_filter(record):
    record["time"] = record["time"].astimezone(ZoneInfo("Asia/Shanghai"))
    return record


def _format_log_record(record) -> str:
    base = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | " "{name}:{function}:{line} - {message}\n"
    )
    if record["extra"].get("_redacted_exception"):
        return base + "{extra[_redacted_exception]}"
    return base


def init_log(**sink_channel):
    """Initialize stdout and file log sinks with diagnose=False and secret redaction."""
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    logger.remove()
    logger.configure(patcher=_redacting_patcher)

    # Always disable diagnose=True so Loguru never dumps local variables (such as
    # EPIC_PASSWORD, EPIC_ACCOUNTS, or API keys) in exception tracebacks.
    logger.add(
        sink=sys.stdout,
        level=log_level,
        format=_format_log_record,
        filter=timezone_filter,
        backtrace=False,
        diagnose=False,
    )

    if error_path := sink_channel.get("error"):
        logger.add(
            sink=error_path,
            level="ERROR",
            rotation="5 MB",
            format=_format_log_record,
            filter=timezone_filter,
            backtrace=False,
            diagnose=False,
        )
    if runtime_path := sink_channel.get("runtime"):
        logger.add(
            sink=runtime_path,
            level="TRACE",
            rotation="5 MB",
            format=_format_log_record,
            filter=timezone_filter,
            backtrace=False,
            diagnose=False,
        )

    return logger
