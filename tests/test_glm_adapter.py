import json

from hcaptcha_challenger.models import (
    ChallengeRouterResult,
    ImageAreaSelectChallenge,
    ImageDragDropChallenge,
)

from extensions.llm_adapter import (
    _coerce_payload_for_schema,
    _extract_json_payload,
    _normalize_glm_payload,
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
