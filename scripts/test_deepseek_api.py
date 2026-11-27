#!/usr/bin/env python3
"""DeepSeek V4.1 Flash API 直接调用验证脚本。

从本地 `.env` 或环境变量读取 `DEEPSEEK_API_KEY`，验证 DeepSeek OpenAI 兼容接口的：
1. 纯文本对话（关闭 thinking）
2. Thinking / Reasoning 模式
3. JSON 结构化输出
4. 多模态（图片 data URL + JSON 结构化输出）
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import os
import struct
import sys
import zlib
from pathlib import Path

import httpx

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional fallback outside project venv
    load_dotenv = None


DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"

# Prevent pytest from collecting this standalone CLI diagnostic script as a test module.
__test__ = False


def _mask_secret(secret: str) -> str:
    if len(secret) <= 8:
        return "***"
    return f"{secret[:5]}***{secret[-4:]}"


def _build_synthetic_test_png() -> bytes:
    """生成本地合成几何测试图（不依赖外部文件，避免误传敏感截图）。"""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (300, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse((170, 60, 250, 140), fill=(220, 40, 40))
        draw.rectangle((40, 180, 120, 260), fill=(40, 90, 220))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        # Fallback: pure-Python 16x16 solid red PNG
        width, height = 16, 16
        raw = b"".join(b"\x00" + b"\xdc\x28\x28" * width for _ in range(height))

        def _chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack("!I", len(data))
                + tag
                + data
                + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
        return (
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw))
            + _chunk(b"IEND", b"")
        )


def _encode_image_data_url(image_path: str | None) -> tuple[str, str]:
    """将指定图片或合成测试图编码为 base64 data URL。"""
    if image_path:
        path = Path(image_path)
        raw = path.read_bytes()
        ext = path.suffix.lower()
        mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
        mime_type = mime_map.get(ext, "image/png")
        label = path.name
    else:
        raw = _build_synthetic_test_png()
        mime_type = "image/png"
        label = "synthetic-300x300-shapes.png"

    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}", label


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


async def check_text_chat(
    model: str, base_url: str, api_key: str, client: httpx.AsyncClient
) -> dict:
    """测试纯文本对话（关闭 thinking）。"""
    print(f"\n{'=' * 60}")
    print(f"📝 测试 [{model}] 纯文本对话（thinking=disabled）...")
    print(f"{'=' * 60}")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请用一句话回复确认连接正常。"}],
        "thinking": {"type": "disabled"},
        "max_tokens": 120,
    }

    try:
        response = await client.post(
            f"{base_url}/chat/completions", headers=_headers(api_key), json=payload
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        print("✅ 成功")
        print(f"   回复: {content}")
        print(f"   Token: {json.dumps(usage, ensure_ascii=False)}")
        return {"test": "text", "status": "ok", "model": model, "content": content, "usage": usage}
    except Exception as exc:
        print(f"❌ 失败: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            print(f"   响应体: {exc.response.text[:500]}")
        return {"test": "text", "status": "error", "model": model, "error": str(exc)}


async def check_thinking_mode(
    model: str, base_url: str, api_key: str, client: httpx.AsyncClient
) -> dict:
    """测试 DeepSeek thinking/reasoning 模式。"""
    print(f"\n{'=' * 60}")
    print(f"🧠 测试 [{model}] Thinking 模式（reasoning_effort=high）...")
    print(f"{'=' * 60}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "一个盒子里有 3 个球，拿出 1 个后又放入 4 个，现在有多少个球？只给出简短结论。",
            }
        ],
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
        "max_tokens": 500,
    }

    try:
        response = await client.post(
            f"{base_url}/chat/completions", headers=_headers(api_key), json=payload
        )
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]
        reasoning = message.get("reasoning_content", "") or ""
        content = message.get("content", "") or ""
        usage = data.get("usage", {})

        print("✅ 成功")
        if reasoning:
            print(f"   推理过程: {reasoning[:200]}...")
        print(f"   最终回答: {content}")
        print(f"   Token: {json.dumps(usage, ensure_ascii=False)}")
        return {
            "test": "thinking",
            "status": "ok",
            "model": model,
            "content": content,
            "reasoning": reasoning[:200],
            "usage": usage,
        }
    except Exception as exc:
        print(f"❌ 失败: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            print(f"   响应体: {exc.response.text[:500]}")
        return {"test": "thinking", "status": "error", "model": model, "error": str(exc)}


async def check_json_mode(
    model: str, base_url: str, api_key: str, client: httpx.AsyncClient
) -> dict:
    """测试 JSON 结构化输出模式。"""
    print(f"\n{'=' * 60}")
    print(f"📋 测试 [{model}] JSON 结构化输出...")
    print(f"{'=' * 60}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": '请严格返回 JSON：{"status": "ok", "multimodal_ready": true}',
            }
        ],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "max_tokens": 120,
    }

    try:
        response = await client.post(
            f"{base_url}/chat/completions", headers=_headers(api_key), json=payload
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        print("✅ 成功")
        print(f"   解析结果: {json.dumps(parsed, ensure_ascii=False)}")
        return {"test": "json", "status": "ok", "model": model, "content": content}
    except Exception as exc:
        print(f"❌ 失败: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            print(f"   响应体: {exc.response.text[:500]}")
        return {"test": "json", "status": "error", "model": model, "error": str(exc)}


async def check_multimodal_json(
    model: str, base_url: str, api_key: str, client: httpx.AsyncClient, image_path: str | None
) -> dict:
    """测试多模态 data URL 输入与 JSON 结构化输出。"""
    data_url, label = _encode_image_data_url(image_path)
    print(f"\n{'=' * 60}")
    print(f"🖼️  测试 [{model}] 多模态（image_url data URL + JSON）...")
    print(f"   图片: {label}")
    print(f"{'=' * 60}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Identify the shapes and colors visible in this image and return a "
                            'valid JSON object with keys "shapes" (list of strings) and '
                            '"summary" (short string).'
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "max_tokens": 200,
    }

    try:
        response = await client.post(
            f"{base_url}/chat/completions", headers=_headers(api_key), json=payload
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        usage = data.get("usage", {})
        print("✅ 成功")
        print(f"   解析结果: {json.dumps(parsed, ensure_ascii=False)}")
        print(f"   Token: {json.dumps(usage, ensure_ascii=False)}")
        return {"test": "multimodal", "status": "ok", "model": model, "content": content}
    except Exception as exc:
        print(f"❌ 失败: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            body = exc.response.text[:500]
            print(f"   响应体: {body}")
            return {"test": "multimodal", "status": "error", "model": model, "error": body}
        return {"test": "multimodal", "status": "error", "model": model, "error": str(exc)}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify DeepSeek API text/thinking/multimodal JSON"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override (default: DEEPSEEK_MODEL env or deepseek-flash)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL override (default: DEEPSEEK_BASE_URL env or https://api.deepseek.com)",
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Optional local image path (defaults to an in-memory synthetic geometric PNG)",
    )
    return parser.parse_args()


async def main() -> int:
    if load_dotenv is not None:
        load_dotenv()

    args = _parse_args()
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        print("❌ 缺少 DEEPSEEK_API_KEY，请在本地 .env 或环境变量中配置后再运行。")
        return 2

    base_url = (args.base_url or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    model = (args.model or os.getenv("DEEPSEEK_MODEL") or DEFAULT_MODEL).strip()

    print("🚀 DeepSeek V4.1 Flash API 直接调用测试")
    print(f"   API Key: {_mask_secret(api_key)}")
    print(f"   API Base: {base_url}")
    print(f"   测试模型: {model}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        results = [
            await check_text_chat(model, base_url, api_key, client),
            await check_thinking_mode(model, base_url, api_key, client),
            await check_json_mode(model, base_url, api_key, client),
            await check_multimodal_json(model, base_url, api_key, client, args.image),
        ]

    ok_count = sum(1 for item in results if item["status"] == "ok")
    fail_count = sum(1 for item in results if item["status"] == "error")
    multimodal_ok = any(item["test"] == "multimodal" and item["status"] == "ok" for item in results)

    print(f"\n{'=' * 60}")
    print("📊 测试汇总")
    print(f"{'=' * 60}")
    print(f"   总计: {len(results)} 项 | 成功: {ok_count} | 失败: {fail_count}")
    for item in results:
        icon = "✅" if item["status"] == "ok" else "❌"
        preview = str(item.get("content", item.get("error", ""))).replace("\n", " ")[:80]
        print(f"   {icon} [{item['test']}] {item['model']}: {preview}")

    print(f"\n{'=' * 60}")
    if multimodal_ok and fail_count == 0:
        print(f"✅ [{model}] 纯文本 / Thinking / JSON / 多模态图片输入全部验证通过")
    elif not multimodal_ok:
        print(f"❌ [{model}] 多模态图片输入未通过，请检查模型名与接口配置")
    else:
        print(f"⚠️  [{model}] 部分检查失败（失败 {fail_count} 项），请查看上方日志")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
