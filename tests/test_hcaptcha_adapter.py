import asyncio
from types import SimpleNamespace

import cv2
import numpy as np
from hcaptcha_challenger.models import CaptchaResponse, PointCoordinate, SpatialPath

import extensions.hcaptcha_adapter as hcaptcha_adapter
from extensions.numbered_line_solver import NumberedDragSolution
from extensions.hcaptcha_adapter import (
    _correct_drag_source_points,
    _decode_entity_contour,
    _detect_clickable_grid_bounds,
    _detect_task_canvas_origin,
    _handle_checkcaptcha_response,
    _is_line_completion_question,
    _match_outline_contours,
    _point_answer_validation_error,
    _select_line_gap_markers,
    begin_captcha_attempt,
    end_captcha_attempt,
)


def _write_challenge_screenshot(path, *, canvas_y: int, canvas_height: int):
    image = np.full((470, 500, 3), 245, dtype=np.uint8)
    image[:108] = (143, 131, 0)
    image[canvas_y : canvas_y + canvas_height, 10:490] = (80, 120, 160)
    assert cv2.imwrite(str(path), image)


def _write_count_challenge(path, *, reference_side: str):
    image = np.full((470, 500, 3), 245, dtype=np.uint8)
    image[:108] = (143, 131, 0)
    image[130:460, 10:490] = (80, 120, 160)
    badge_x = 65 if reference_side == "left" else 435
    for badge_y in (165, 275, 385):
        cv2.ellipse(image, (badge_x, badge_y), (29, 18), 0, 0, 360, (20, 20, 20), -1)
    assert cv2.imwrite(str(path), image)


def test_drag_canvas_origin_supports_multi_shape_layout(tmp_path):
    screenshot = tmp_path / "challenge.png"
    _write_challenge_screenshot(screenshot, canvas_y=130, canvas_height=330)

    assert _detect_task_canvas_origin(screenshot) == (10, 130)


def test_count_challenge_grid_is_opposite_left_reference_strip(tmp_path):
    screenshot = tmp_path / "left-reference.png"
    _write_count_challenge(screenshot, reference_side="left")

    bounds = _detect_clickable_grid_bounds(screenshot)

    assert bounds is not None
    assert bounds[0] >= 150
    assert bounds[2] == 489


def test_count_challenge_grid_is_opposite_right_reference_strip(tmp_path):
    screenshot = tmp_path / "right-reference.png"
    _write_count_challenge(screenshot, reference_side="right")

    bounds = _detect_clickable_grid_bounds(screenshot)

    assert bounds is not None
    assert bounds[0] == 10
    assert bounds[2] <= 350


def test_point_answer_rejects_challenge_and_grid_overflow():
    challenge_bbox = {"x": 390, "y": 100, "width": 500, "height": 470}
    clickable_bounds = (560, 230, 880, 560)

    outside_challenge = _point_answer_validation_error(
        [SimpleNamespace(x=836, y=809)],
        challenge_bbox=challenge_bbox,
        clickable_bounds=clickable_bounds,
    )
    reference_strip = _point_answer_validation_error(
        [SimpleNamespace(x=426, y=300)],
        challenge_bbox=challenge_bbox,
        clickable_bounds=clickable_bounds,
    )
    valid = _point_answer_validation_error(
        [SimpleNamespace(x=700, y=400)],
        challenge_bbox=challenge_bbox,
        clickable_bounds=clickable_bounds,
    )

    assert "outside challenge bounds" in outside_challenge
    assert "outside clickable grid" in reference_strip
    assert valid is None


def test_payload_entity_centers_replace_invalid_model_sources(tmp_path):
    screenshot = tmp_path / "challenge.png"
    _write_challenge_screenshot(screenshot, canvas_y=130, canvas_height=330)
    payload = SimpleNamespace(
        tasklist=[
            SimpleNamespace(
                entities=[SimpleNamespace(coords=[416, 55]), SimpleNamespace(coords=[406, 219])]
            )
        ]
    )
    paths = [
        SpatialPath(
            start_point=PointCoordinate(x=819, y=323), end_point=PointCoordinate(x=533, y=323)
        ),
        SpatialPath(
            start_point=PointCoordinate(x=819, y=623), end_point=PointCoordinate(x=461, y=422)
        ),
    ]

    corrected = _correct_drag_source_points(
        paths,
        captcha_payload=payload,
        crumb_id=0,
        challenge_screenshot=screenshot,
        challenge_bbox={"x": 390, "y": 100, "width": 500, "height": 470},
    )

    assert [(path.start_point.x, path.start_point.y) for path in corrected] == [
        (816, 285),
        (806, 449),
    ]
    assert [(path.end_point.x, path.end_point.y) for path in corrected] == [(533, 323), (461, 422)]


def test_source_correction_requires_one_entity_per_model_path(tmp_path):
    screenshot = tmp_path / "challenge.png"
    _write_challenge_screenshot(screenshot, canvas_y=135, canvas_height=320)
    payload = SimpleNamespace(
        tasklist=[SimpleNamespace(entities=[SimpleNamespace(coords=[414, 60])])]
    )
    paths = [
        SpatialPath(
            start_point=PointCoordinate(x=800, y=300), end_point=PointCoordinate(x=500, y=300)
        ),
        SpatialPath(
            start_point=PointCoordinate(x=800, y=450), end_point=PointCoordinate(x=500, y=450)
        ),
    ]

    corrected = _correct_drag_source_points(
        paths,
        captcha_payload=payload,
        crumb_id=0,
        challenge_screenshot=screenshot,
        challenge_bbox={"x": 390, "y": 100, "width": 500, "height": 470},
    )

    assert [(path.start_point.x, path.start_point.y) for path in corrected] == [
        (800, 300),
        (800, 450),
    ]


def _contour_from_mask(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return max(contours, key=cv2.contourArea)


def test_outline_topology_matching_ignores_candidate_position():
    square = np.zeros((80, 80), dtype=np.uint8)
    cv2.rectangle(square, (15, 15), (55, 55), 255, -1)
    triangle = np.zeros((80, 80), dtype=np.uint8)
    cv2.fillPoly(triangle, [np.array([[40, 10], [70, 65], [10, 65]])], 255)
    source_contours = [_contour_from_mask(square), _contour_from_mask(triangle)]
    targets = [
        (_contour_from_mask(triangle), (100.0, 100.0)),
        (_contour_from_mask(square), (200.0, 200.0)),
    ]

    matched = _match_outline_contours(source_contours, targets)

    assert matched is not None
    assert matched[0] == [1, 0]


def test_entity_contour_uses_png_alpha_channel():
    image = np.zeros((40, 40, 4), dtype=np.uint8)
    cv2.circle(image, (20, 20), 10, (100, 150, 200, 255), -1)
    encoded, content = cv2.imencode(".png", image)

    contour = _decode_entity_contour(content.tobytes())

    assert encoded
    assert contour is not None
    assert cv2.contourArea(contour) > 250


def test_line_gap_markers_use_cyan_three_and_yellow_five():
    markers = [
        ((320.0, 290.0), (128.0, 104.0, 137.0)),
        ((275.0, 220.0), (117.0, 84.0, 110.0)),
        ((280.0, 325.0), (107.0, 79.0, 81.0)),
        ((158.0, 243.0), (75.0, 132.0, 149.0)),
    ]

    assert _select_line_gap_markers(markers) == ((280.0, 325.0), (158.0, 243.0))


def test_line_question_detection_tolerates_confusable_words():
    assert _is_line_completion_question("Please ԁrag the segment on the right to сomplete the line")


def test_line_path_uses_numbered_circle_target_for_source_three(monkeypatch, tmp_path):
    payload = SimpleNamespace(
        get_requester_question=lambda: "Please drag the segment on the right to complete the line"
    )
    monkeypatch.setattr(hcaptcha_adapter, "_payload_source_points", lambda **_kwargs: [(810, 310)])
    monkeypatch.setattr(
        hcaptcha_adapter,
        "solve_numbered_line_drag",
        lambda *_args: NumberedDragSolution(
            start=(830, 300), end=(520, 410), source_label=3, digit_count=6, score=0.1
        ),
    )

    paths = hcaptcha_adapter._resolve_line_path(
        captcha_payload=payload,
        crumb_id=0,
        challenge_screenshot=tmp_path / "challenge.png",
        challenge_bbox={"x": 390.0, "y": 100.0, "width": 500.0, "height": 470.0},
    )

    assert paths is not None
    assert paths[0].start_point.model_dump() == {"x": 810, "y": 310}
    assert paths[0].end_point.model_dump() == {"x": 520, "y": 410}


class _CaptchaPage:
    def __init__(self):
        self.request_handler = None

    def on(self, event, handler):
        if event == "request":
            self.request_handler = handler


class _CaptchaRequest:
    def __init__(self, url):
        self.url = url


class _CaptchaResponse:
    status = 200

    def __init__(self, request, body):
        self.request = request
        self.url = request.url
        self._body = body

    async def body(self):
        return self._body


def test_late_checkcaptcha_response_from_previous_attempt_is_ignored():
    async def scenario():
        page = _CaptchaPage()
        agent = SimpleNamespace(page=page, _captcha_response_queue=asyncio.Queue())

        first_generation = await begin_captcha_attempt(agent)
        old_request = _CaptchaRequest("https://api.hcaptcha.com/checkcaptcha/old")
        page.request_handler(old_request)
        await end_captcha_attempt(agent)

        # Avoid waiting for the production grace period in this focused state-machine test.
        agent._epic_captcha_attempt_finished_at = 0
        second_generation = await begin_captcha_attempt(agent)
        new_request = _CaptchaRequest("https://api.hcaptcha.com/checkcaptcha/new")
        page.request_handler(new_request)

        await _handle_checkcaptcha_response(agent, _CaptchaResponse(old_request, b'{"pass": true}'))
        assert agent._captcha_response_queue.empty()

        await _handle_checkcaptcha_response(agent, _CaptchaResponse(new_request, b'{"pass": true}'))
        queued = await agent._captcha_response_queue.get()
        await end_captcha_attempt(agent)
        return first_generation, second_generation, queued

    first_generation, second_generation, queued = asyncio.run(scenario())

    assert second_generation > first_generation
    assert queued.is_pass is True


def test_checkcaptcha_empty_response_does_not_discard_queued_pass():
    async def scenario():
        page = _CaptchaPage()
        agent = SimpleNamespace(page=page, _captcha_response_queue=asyncio.Queue())
        await begin_captcha_attempt(agent)
        request = _CaptchaRequest("https://api.hcaptcha.com/checkcaptcha/example")
        page.request_handler(request)
        agent._captcha_response_queue.put_nowait(CaptchaResponse.model_validate({"pass": True}))
        await _handle_checkcaptcha_response(agent, _CaptchaResponse(request, b""))
        queued = await asyncio.wait_for(agent._captcha_response_queue.get(), timeout=0.1)
        await end_captcha_attempt(agent)
        return queued

    queued = asyncio.run(scenario())

    assert queued.is_pass is True


def test_checkcaptcha_pass_supersedes_delayed_failure():
    async def scenario():
        page = _CaptchaPage()
        agent = SimpleNamespace(page=page, _captcha_response_queue=asyncio.Queue())
        await begin_captcha_attempt(agent)

        empty_request = _CaptchaRequest("https://api.hcaptcha.com/checkcaptcha/empty")
        pass_request = _CaptchaRequest("https://api.hcaptcha.com/checkcaptcha/pass")
        page.request_handler(empty_request)
        await _handle_checkcaptcha_response(agent, _CaptchaResponse(empty_request, b""))
        page.request_handler(pass_request)
        await _handle_checkcaptcha_response(
            agent, _CaptchaResponse(pass_request, b'{"pass": true}')
        )
        queued = await asyncio.wait_for(agent._captcha_response_queue.get(), timeout=0.1)
        await end_captcha_attempt(agent)
        return queued, agent._captcha_response_queue.empty()

    queued, queue_empty = asyncio.run(scenario())

    assert queued.is_pass is True
    assert queue_empty is True
