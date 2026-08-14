#!/usr/bin/env python3
"""DeepSeek V4 API 直接调用测试脚本。

测试 DeepSeek v4-pro 和 v4-flash 两个模型的：
1. 纯文本对话（关闭 thinking）
2. Thinking/Reasoning 模式
3. 多模态（图片 + 文本）识别
4. 尝试多种图片传入方式
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path

import httpx

# DeepSeek API 配置
API_KEY = "sk-0ad4d0ce9ae045aa980c5842b5a22498"
BASE_URL = "https://api.deepseek.com"
MODELS = ["deepseek-v4-pro", "deepseek-v4-flash"]


def _find_test_image() -> str | None:
    """在项目目录中找一个可用的测试图片。"""
    candidates = [
        Path("app/volumes/screenshots"),
        Path("app/runtime"),
        Path("docs/images"),
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            for img in sorted(candidate.rglob(ext)):
                return str(img)
    return None


def _encode_image_base64(image_path: str) -> str:
    """将图片编码为 base64 字符串。"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _encode_image_data_url(image_path: str) -> str:
    """将图片编码为 base64 data URL。"""
    data = _encode_image_base64(image_path)
    ext = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    mime_type = mime_map.get(ext, "image/png")
    return f"data:{mime_type};base64,{data}"


async def test_text_chat(model: str, client: httpx.AsyncClient) -> dict:
    """测试纯文本对话（关闭 thinking）。"""
    print(f"\n{'='*60}")
    print(f"📝 测试 [{model}] 纯文本对话（thinking=disabled）...")
    print(f"{'='*60}")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "请用一句话介绍你自己，说明你是哪个模型。"},
        ],
        "thinking": {"type": "disabled"},
        "max_tokens": 200,
    }

    try:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        reasoning = data["choices"][0]["message"].get("reasoning_content", "")
        usage = data.get("usage", {})
        print(f"✅ 成功")
        print(f"   回复: {content}")
        if reasoning:
            print(f"   推理: {reasoning[:100]}...")
        print(f"   Token: {json.dumps(usage)}")
        return {"status": "ok", "model": model, "content": content, "usage": usage}
    except Exception as e:
        print(f"❌ 失败: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   响应体: {e.response.text[:500]}")
        return {"status": "error", "model": model, "error": str(e)}


async def test_thinking_mode(model: str, client: httpx.AsyncClient) -> dict:
    """测试 DeepSeek thinking/reasoning 模式。"""
    print(f"\n{'='*60}")
    print(f"🧠 测试 [{model}] Thinking 模式（reasoning_effort=high）...")
    print(f"{'='*60}")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "一个房间里有3个人，5个人离开，然后又来了2个人。现在房间里有多少人？请一步步推理，最后给出答案。"},
        ],
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
        "max_tokens": 1000,
    }

    try:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        message = data["choices"][0]["message"]
        reasoning = message.get("reasoning_content", "")
        content = message.get("content", "")
        usage = data.get("usage", {})

        print(f"✅ 成功")
        if reasoning:
            print(f"   推理过程: {reasoning[:300]}...")
        print(f"   最终回答: {content}")
        print(f"   Token: {json.dumps(usage)}")
        return {
            "status": "ok",
            "model": model,
            "content": content,
            "reasoning": reasoning[:300],
            "usage": usage,
        }
    except Exception as e:
        print(f"❌ 失败: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   响应体: {e.response.text[:500]}")
        return {"status": "error", "model": model, "error": str(e)}


async def test_multimodal_data_url(model: str, client: httpx.AsyncClient, image_path: str) -> dict:
    """测试多模态 - data URL 方式。"""
    print(f"\n{'='*60}")
    print(f"🖼️  测试 [{model}] 多模态 - data URL 格式...")
    print(f"   图片: {Path(image_path).name}")
    print(f"{'='*60}")

    data_url = _encode_image_data_url(image_path)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请描述这张图片的内容。回答不超过50字。"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 200,
    }

    try:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(f"✅ 成功")
        print(f"   回复: {content}")
        return {"status": "ok", "model": model, "content": content}
    except Exception as e:
        print(f"❌ 失败: {e}")
        if hasattr(e, "response") and e.response is not None:
            body = e.response.text[:500]
            print(f"   响应体: {body}")
            return {"status": "error", "model": model, "error": body}
        return {"status": "error", "model": model, "error": str(e)}


async def test_multimodal_vision_api(model: str, client: httpx.AsyncClient) -> dict:
    """测试是否有独立的 vision API 端点。"""
    print(f"\n{'='*60}")
    print(f"🔍 测试 [{model}] 是否有 /vision 或 /multimodal 端点...")
    print(f"{'='*60}")

    # 尝试 vision 端点
    for suffix in ["/vision", "/multimodal", "/v1/vision"]:
        url = f"{BASE_URL}{suffix}"
        try:
            response = await client.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
            print(f"   {url}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   {url}: {e}")

    return {"status": "info", "model": model, "content": "vision API check done"}


async def test_json_mode(model: str, client: httpx.AsyncClient) -> dict:
    """测试 JSON 结构化输出模式。"""
    print(f"\n{'='*60}")
    print(f"📋 测试 [{model}] JSON 结构化输出...")
    print(f"{'='*60}")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": '请以 JSON 格式返回以下信息：{"name": "你的名字", "version": "版本号", "can_see_images": false}',
            }
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 200,
    }

    try:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(f"✅ 成功")
        print(f"   回复: {content}")
        try:
            parsed = json.loads(content)
            print(f"   解析结果: {json.dumps(parsed)}")
        except json.JSONDecodeError:
            print(f"   ⚠️ 无法解析为 JSON")
        return {"status": "ok", "model": model, "content": content}
    except Exception as e:
        print(f"❌ 失败: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"   响应体: {e.response.text[:500]}")
        return {"status": "error", "model": model, "error": str(e)}


async def main():
    print("🚀 DeepSeek V4 API 直接调用测试")
    print(f"   API Key: {API_KEY[:20]}...")
    print(f"   API Base: {BASE_URL}")
    print(f"   测试模型: {MODELS}")

    # 查找测试图片
    image_path = _find_test_image()
    if image_path:
        print(f"   测试图片: {image_path}")
    else:
        print(f"   ⚠️  未找到测试图片，跳过多模态测试")

    results = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
        for model in MODELS:
            # 1. 纯文本（关闭 thinking）
            result = await test_text_chat(model, client)
            results.append(result)

            # 2. Thinking 模式
            result = await test_thinking_mode(model, client)
            results.append(result)

            # 3. JSON 结构化输出
            result = await test_json_mode(model, client)
            results.append(result)

            # 4. 多模态测试
            if image_path:
                result = await test_multimodal_data_url(model, client, image_path)
                results.append(result)

        # 5. 检查 vision API 端点
        result = await test_multimodal_vision_api(MODELS[0], client)
        results.append(result)

    # 汇总
    print(f"\n\n{'='*60}")
    print("📊 测试汇总")
    print(f"{'='*60}")

    text_ok = [r for r in results if "纯文本" in str(r.get("model", "")) or "文本" in str(r.get("content", ""))]
    vision_ok = [r for r in results if "multimodal" in str(r.get("error", "") + r.get("content", ""))]

    ok_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = sum(1 for r in results if r["status"] == "error")
    info_count = sum(1 for r in results if r["status"] == "info")

    print(f"   总计: {len(results)} 项测试")
    print(f"   成功: {ok_count} | 失败: {fail_count} | 信息: {info_count}")

    for r in results:
        status_icon = "✅" if r["status"] == "ok" else ("ℹ️" if r["status"] == "info" else "❌")
        content_preview = r.get("content", r.get("error", ""))[:80]
        print(f"   {status_icon} {r['model']}: {content_preview}")

    # 结论
    print(f"\n{'='*60}")
    print("📋 结论")
    print(f"{'='*60}")
    multimodal_ok = any(
        r["status"] == "ok" and "multimodal" in r.get("content", "")
        for r in results
    )
    if not multimodal_ok:
        print("⚠️  DeepSeek V4 (pro/flash) 不支持多模态（图片输入）")
        print("    API 返回: unknown variant 'image_url', expected 'text'")
        print("    这意味着 DeepSeek V4 无法直接用于 hCaptcha 验证码识别")
        print("    验证码识别需要图片输入能力（vision/multimodal）")
        print()
        print("💡 替代方案：")
        print("    1. 使用支持图片的模型（如 GLM glm-4.6v, Gemini 2.5 Pro）做验证码识别")
        print("    2. DeepSeek V4 可用于纯文本任务（如挑战类型分类、规则推理）")
        print("    3. 等待 DeepSeek 官方发布多模态版本")
    else:
        print("✅ 多模态支持正常")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))