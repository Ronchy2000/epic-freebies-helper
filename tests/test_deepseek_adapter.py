import asyncio
import base64
import json
from types import SimpleNamespace

import httpx
import pytest
from hcaptcha_challenger.models import (
    ChallengeRouterResult,
    ImageAreaSelectChallenge,
    ImageDragDropChallenge,
)

from extensions.llm_adapter import (
    DeepSeekCompatibleGenAIClient,
    _DeepSeekAsyncModels,
    _OpenAICompatibleAsyncFiles,
    apply_deepseek_patch,
)


def _ds_config(schema, *, system_instruction=None, temperature=None, thinking_config=None):
    return SimpleNamespace(
        response_schema=schema,
        system_instruction=system_instruction,
        temperature=temperature,
        thinking_config=thinking_config,
    )


def _ds_settings(
    *,
    thinking_enabled=False,
    reasoning_effort="high",
    timeout=50.0,
    base_url="https://api.deepseek.com",
    model="deepseek-flash",
):
    class Secret:
        @staticmethod
        def get_secret_value():
            return "sk-fake-deepseek-test-key"

    return SimpleNamespace(
        DEEPSEEK_API_KEY=Secret(),
        DEEPSEEK_BASE_URL=base_url,
        DEEPSEEK_MODEL=model,
        DEEPSEEK_REQUEST_TIMEOUT_SECONDS=timeout,
        DEEPSEEK_THINKING_ENABLED=thinking_enabled,
        DEEPSEEK_REASONING_EFFORT=reasoning_effort,
    )


def test_deepseek_payload_defaults_to_disabled_thinking_and_data_url_images():
    storage = {}
    files = _OpenAICompatibleAsyncFiles(storage, "deepseek-local")
    uploaded = asyncio.run(files.upload(b"png-bytes", mime_type="image/png"))

    client = _DeepSeekAsyncModels(settings=_ds_settings(thinking_enabled=False), storage=storage)
    contents = SimpleNamespace(
        role="user",
        parts=[
            SimpleNamespace(text="Locate the red circle."),
            SimpleNamespace(
                file_data=SimpleNamespace(file_uri=uploaded.uri, mime_type=uploaded.mime_type)
            ),
        ],
    )

    payload = client._build_payload(
        model="deepseek-flash",
        contents=contents,
        config=_ds_config(ImageAreaSelectChallenge, thinking_config=object()),
        kwargs={},
    )

    assert payload["model"] == "deepseek-flash"
    assert payload["thinking"] == {"type": "disabled"}
    assert "reasoning_effort" not in payload
    assert payload["response_format"] == {"type": "json_object"}

    system_msg = payload["messages"][0]
    assert system_msg["role"] == "system"
    assert "JSON Schema" in system_msg["content"]
    assert "points" in system_msg["content"]

    user_items = payload["messages"][1]["content"]
    expected_url = f"data:image/png;base64,{base64.b64encode(b'png-bytes').decode('utf-8')}"
    assert user_items[1] == {"type": "image_url", "image_url": {"url": expected_url}}


def test_deepseek_payload_enables_thinking_and_reasoning_effort_when_configured():
    client = _DeepSeekAsyncModels(
        settings=_ds_settings(thinking_enabled=True, reasoning_effort="high"), storage={}
    )

    payload = client._build_payload(
        model="deepseek-flash", contents=[], config=_ds_config(ImageDragDropChallenge), kwargs={}
    )

    assert payload["thinking"] == {"type": "enabled"}
    assert payload["reasoning_effort"] == "high"


def test_deepseek_payload_omits_unsupported_reasoning_effort():
    client = _DeepSeekAsyncModels(
        settings=_ds_settings(thinking_enabled=True, reasoning_effort="invalid-level"), storage={}
    )

    payload = client._build_payload(
        model="deepseek-flash", contents=[], config=_ds_config(ChallengeRouterResult), kwargs={}
    )

    assert payload["thinking"] == {"type": "enabled"}
    assert "reasoning_effort" not in payload


def test_deepseek_text_only_schema_request_still_includes_json_instruction():
    client = _DeepSeekAsyncModels(settings=_ds_settings(), storage={})
    contents = SimpleNamespace(role="user", parts=[SimpleNamespace(text="Classify this prompt")])

    payload = client._build_payload(
        model="deepseek-flash",
        contents=contents,
        config=_ds_config(ChallengeRouterResult),
        kwargs={},
    )

    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert "json" in payload["messages"][0]["content"].lower()
    assert "challenge_type" in payload["messages"][0]["content"]


def test_deepseek_timeout_uses_deepseek_budget_and_provider_label(monkeypatch):
    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            raise httpx.ReadTimeout("")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: TimeoutClient())
    client = _DeepSeekAsyncModels(settings=_ds_settings(timeout=35.0), storage={})

    with pytest.raises(TimeoutError, match=r"DeepSeek request timed out after 35 seconds"):
        asyncio.run(
            client.generate_content(
                "deepseek-flash", [], config=_ds_config(ImageAreaSelectChallenge)
            )
        )


def test_deepseek_generate_content_parses_multimodal_area_select_response(monkeypatch):
    captured = {}

    class FakeResponse:
        is_error = False

        @staticmethod
        def json():
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "challenge_prompt": "Click the target",
                                    "points": [{"x": 210, "y": 100}],
                                }
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, endpoint, headers=None, json=None):
            captured["endpoint"] = endpoint
            captured["headers"] = headers
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    client = _DeepSeekAsyncModels(settings=_ds_settings(), storage={})
    contents = SimpleNamespace(
        role="user",
        parts=[
            SimpleNamespace(
                inline_data=SimpleNamespace(data=b"fake-image-bytes", mime_type="image/png")
            )
        ],
    )

    resp = asyncio.run(
        client.generate_content(
            "deepseek-flash", contents, config=_ds_config(ImageAreaSelectChallenge)
        )
    )

    assert captured["endpoint"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-fake-deepseek-test-key"
    assert captured["payload"]["model"] == "deepseek-flash"
    assert isinstance(resp.parsed, ImageAreaSelectChallenge)
    assert resp.parsed.challenge_prompt == "Click the target"
    assert [pt.model_dump() for pt in resp.parsed.points] == [{"x": 210, "y": 100}]
    dumped = resp.model_dump()
    assert dumped["parsed"]["points"] == [{"x": 210, "y": 100}]


def test_apply_deepseek_patch_installs_client_and_limits_retries(monkeypatch):
    from google import genai
    from hcaptcha_challenger.tools.internal.providers.gemini import GeminiProvider

    monkeypatch.setattr(genai, "Client", object)
    apply_deepseek_patch(_ds_settings())

    assert genai.Client is DeepSeekCompatibleGenAIClient
    assert GeminiProvider.generate_with_images.retry.stop.max_attempt_number == 2
