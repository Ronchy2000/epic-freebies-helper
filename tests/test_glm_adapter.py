import asyncio
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
    _GLMAsyncModels,
    _coerce_payload_for_schema,
    _extract_challenge_type,
    _extract_json_payload,
    _limit_glm_provider_attempts,
    _normalize_glm_payload,
)


def _glm_config(schema, *, thinking_config=None):
    return SimpleNamespace(
        response_schema=schema,
        system_instruction=None,
        temperature=None,
        thinking_config=thinking_config,
    )


def test_multi_target_instruction_treats_either_reference_side_as_nonclickable():
    client = _GLMAsyncModels(settings=None, storage={})
    contents = SimpleNamespace(
        role="user",
        parts=[SimpleNamespace(inline_data=SimpleNamespace(data=b"image", mime_type="image/png"))],
    )

    messages = client._build_messages(contents, _glm_config(ImageAreaSelectChallenge))

    assert "can appear on either side" in messages[0]["content"]
    assert "Select only matching tiles in the separate grid" in messages[0]["content"]


def test_glm_45_point_selection_disables_thinking():
    client = _GLMAsyncModels(settings=None, storage={})

    payload = client._build_payload(
        model="glm-4.5v",
        contents=[],
        config=_glm_config(ImageAreaSelectChallenge, thinking_config=object()),
        kwargs={},
    )

    assert payload["thinking"] == {"type": "disabled"}


def test_glm_45_drag_selection_keeps_thinking_enabled():
    client = _GLMAsyncModels(settings=None, storage={})

    payload = client._build_payload(
        model="glm-4.5v",
        contents=[],
        config=_glm_config(ImageDragDropChallenge, thinking_config=object()),
        kwargs={},
    )

    assert payload["thinking"] == {"type": "enabled"}


def test_glm_46_point_selection_preserves_existing_thinking_behavior():
    client = _GLMAsyncModels(settings=None, storage={})

    payload = client._build_payload(
        model="glm-4.6v",
        contents=[],
        config=_glm_config(ImageAreaSelectChallenge, thinking_config=object()),
        kwargs={},
    )

    assert "thinking" not in payload


def test_glm_provider_retry_budget_is_limited_to_two_attempts():
    assert _limit_glm_provider_attempts() is True

    from hcaptcha_challenger.tools.internal.providers.gemini import GeminiProvider

    assert GeminiProvider.generate_with_images.retry.stop.max_attempt_number == 2


def test_glm_timeout_includes_budget_and_exception_type(monkeypatch):
    class Secret:
        @staticmethod
        def get_secret_value():
            return "not-a-real-key"

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, *_args, **_kwargs):
            raise httpx.ReadTimeout("")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: Client())
    client = _GLMAsyncModels(
        settings=SimpleNamespace(
            GLM_BASE_URL="https://example.invalid/v4",
            GLM_API_KEY=Secret(),
            GLM_REQUEST_TIMEOUT_SECONDS=50,
        ),
        storage={},
    )

    with pytest.raises(TimeoutError, match=r"50 seconds \(ReadTimeout\)"):
        asyncio.run(
            client.generate_content("glm-4.6v", [], config=_glm_config(ImageAreaSelectChallenge))
        )


def test_area_select_box_answer_is_converted_to_click_points():
    text = '{"answer":[[781,525,889,624],[1031,525,1139,624]]}'

    payload = _coerce_payload_for_schema(
        _normalize_glm_payload(_extract_json_payload(text)), ImageAreaSelectChallenge, text
    )
    challenge = ImageAreaSelectChallenge(**payload)

    assert challenge.points[0].model_dump() == {"x": 835, "y": 574}
    assert challenge.points[1].model_dump() == {"x": 1085, "y": 574}


def test_area_select_dict_boxes_are_converted_to_click_points():
    payload = {
        "answer": [
            {"x_min": 10, "y_min": 20, "x_max": 30, "y_max": 60},
            {"x_min": 101, "y_min": 201, "x_max": 200, "y_max": 300},
        ]
    }
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageAreaSelectChallenge, text
    )
    challenge = ImageAreaSelectChallenge(**coerced)

    assert [point.model_dump() for point in challenge.points] == [
        {"x": 20, "y": 40},
        {"x": 150, "y": 250},
    ]


def test_area_select_coordinates_string_with_single_quotes_is_converted():
    text = (
        '{"Challenge Prompt":"","Coordinates":"['
        "{'x': 889, 'y': 613}, {'x': 996, 'y': 538}, {'x': 817, 'y': 761}"
        ']"}'
    )

    payload = _coerce_payload_for_schema(
        _normalize_glm_payload(_extract_json_payload(text)), ImageAreaSelectChallenge, text
    )
    challenge = ImageAreaSelectChallenge(**payload)

    assert challenge.challenge_prompt == ""
    assert [point.model_dump() for point in challenge.points] == [
        {"x": 889, "y": 613},
        {"x": 996, "y": 538},
        {"x": 817, "y": 761},
    ]


def test_area_select_bare_csv_point_is_converted():
    text = '{"answer":"1139, 729"}'

    payload = _coerce_payload_for_schema(
        _normalize_glm_payload(_extract_json_payload(text)), ImageAreaSelectChallenge, text
    )
    challenge = ImageAreaSelectChallenge(**payload)

    assert challenge.challenge_prompt == ""
    assert [point.model_dump() for point in challenge.points] == [{"x": 1139, "y": 729}]


def test_drag_source_coordinates_are_converted_to_paths():
    payload = {
        "source_coordinates": {"x": 765, "y": 545},
        "target_coordinates": {"x": 960, "y": 545},
    }
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert challenge.challenge_prompt == ""
    assert challenge.paths[0].start_point.model_dump() == {"x": 765, "y": 545}
    assert challenge.paths[0].end_point.model_dump() == {"x": 960, "y": 545}


def test_drag_answer_quadruplets_preserve_all_paths():
    payload = {"answer": [[802, 345, 584, 322], [802, 470, 460, 420]]}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 802, "y": 345}, "end_point": {"x": 584, "y": 322}},
        {"start_point": {"x": 802, "y": 470}, "end_point": {"x": 460, "y": 420}},
    ]


def test_drag_src_point_pair_is_converted_to_path():
    payload = {"src": [{"x": 805, "y": 358}, {"x": 535, "y": 425}]}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 805, "y": 358}, "end_point": {"x": 535, "y": 425}}
    ]


def test_drag_semicolon_answer_preserves_all_paths():
    payload = {"answer": "801,345,584,322;801,460,477,421"}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 801, "y": 345}, "end_point": {"x": 584, "y": 322}},
        {"start_point": {"x": 801, "y": 460}, "end_point": {"x": 477, "y": 421}},
    ]


def test_drag_src_tgt_aliases_are_converted_to_path():
    payload = {"src": [840, 322], "tgt": [640, 470]}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 840, "y": 322}, "end_point": {"x": 640, "y": 470}}
    ]


def test_drag_scalar_coordinates_are_rejected_before_schema_validation():
    payload = {"paths": [{"start_point": 842, "end_point": 676}]}

    with pytest.raises(ValueError, match="valid coordinate pairs"):
        _coerce_payload_for_schema(payload, ImageDragDropChallenge, json.dumps(payload))


def test_drag_src_dest_aliases_are_converted_to_path():
    payload = {"src": {"x": 830, "y": 322}, "dest": {"x": 533, "y": 446}}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 830, "y": 322}, "end_point": {"x": 533, "y": 446}}
    ]


def test_drag_pipe_separated_answer_is_converted_to_path():
    payload = {"answer": "840,322|640,470"}
    text = json.dumps(payload)

    coerced = _coerce_payload_for_schema(
        _normalize_glm_payload(payload), ImageDragDropChallenge, text
    )
    challenge = ImageDragDropChallenge(**coerced)

    assert [path.model_dump() for path in challenge.paths] == [
        {"start_point": {"x": 840, "y": 322}, "end_point": {"x": 640, "y": 470}}
    ]


def test_router_answer_single_select_is_converted_to_challenge_type():
    text = '{"answer":"image_label_single_select"}'

    payload = _coerce_payload_for_schema(
        _normalize_glm_payload(_extract_json_payload(text)), ChallengeRouterResult, text
    )
    challenge = ChallengeRouterResult(**payload)

    assert challenge.challenge_prompt == ""
    assert challenge.challenge_type.value == "image_label_single_select"


def test_router_drag_multi_alias_matches_current_schema_enum():
    text = '{"answer":"image_drag_multi"}'

    payload = _coerce_payload_for_schema(
        _normalize_glm_payload(_extract_json_payload(text)), ChallengeRouterResult, text
    )
    challenge = ChallengeRouterResult(**payload)

    assert challenge.challenge_prompt == ""
    assert challenge.challenge_type.value == "image_drag_multi"


def test_router_plain_text_drag_multi_remains_upstream_enum_value():
    text = "image_drag_multi"
    challenge_type = _extract_challenge_type(text)

    payload = _coerce_payload_for_schema(
        {"challenge_type": challenge_type}, ChallengeRouterResult, text
    )
    challenge = ChallengeRouterResult(**payload)

    assert challenge.challenge_type.value == "image_drag_multi"
