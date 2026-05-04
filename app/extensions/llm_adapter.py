# -*- coding: utf-8 -*-
import base64
import json
import mimetypes
import re
from contextlib import suppress
from pathlib import Path
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel

KNOWN_CHALLENGE_TYPES = {
    "image_drag_single",
    "image_drag_multiple",
    "image_drag_multi",
    "image_label_binary",
    "image_label_multi_select",
    "image_label_area_select",
    "image_label_multiple_choice",
}

CHALLENGE_TYPE_ALIASES = {
    "image_drag_multi": "image_drag_multiple",
}


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _load_binary(file: Any) -> bytes:
    if hasattr(file, "read"):
        return file.read()
    if isinstance(file, (str, Path)):
        return Path(file).read_bytes()
    if isinstance(file, bytes):
        return file
    return bytes(file)


def _guess_mime_type(file: Any) -> str:
    if hasattr(file, "name"):
        candidate = getattr(file, "name", "")
    else:
        candidate = str(file)
    guessed, _ = mimetypes.guess_type(candidate)
    return guessed or "image/png"


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
        if match:
            stripped = match.group(1).strip()
    return json.loads(stripped)


def _normalize_glm_response_text(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return stripped

    if stripped.startswith("{") or stripped.startswith("```"):
        return stripped

    drag_match = re.search(
        r"Source Position:\s*\((\d+)\s*,\s*(\d+)\)\s*,\s*Target Position:\s*\((\d+)\s*,\s*(\d+)\)",
        stripped,
        flags=re.IGNORECASE,
    )
    if drag_match:
        sx, sy, tx, ty = map(int, drag_match.groups())
        return (
            "```json\n"
            + json.dumps(
                {
                    "challenge_prompt": "",
                    "paths": [
                        {
                            "start_point": {"x": sx, "y": sy},
                            "end_point": {"x": tx, "y": ty},
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n```"
        )

    tuple_drag_matches = re.findall(r"\((\d+)\s*,\s*(\d+)\)", stripped)
    if len(tuple_drag_matches) == 2:
        (sx, sy), (tx, ty) = tuple_drag_matches
        return (
            "```json\n"
            + json.dumps(
                {
                    "challenge_prompt": "",
                    "paths": [
                        {
                            "start_point": {"x": int(sx), "y": int(sy)},
                            "end_point": {"x": int(tx), "y": int(ty)},
                        }
                    ],
                },
                ensure_ascii=False,
            )
            + "\n```"
        )

    point_matches = re.findall(r"\((\d+)\s*,\s*(\d+)\)", stripped)
    if point_matches and ("position" in stripped.lower() or "point" in stripped.lower()):
        points = [{"x": int(x), "y": int(y)} for x, y in point_matches]
        return (
            "```json\n"
            + json.dumps(
                {
                    "challenge_prompt": "",
                    "points": points,
                },
                ensure_ascii=False,
            )
            + "\n```"
        )

    return stripped


def _extract_challenge_type(text: str) -> str | None:
    stripped = text.strip().strip('"').strip("'")
    stripped = CHALLENGE_TYPE_ALIASES.get(stripped, stripped)
    if stripped in KNOWN_CHALLENGE_TYPES:
        return stripped
    return None


def _extract_drag_points_from_text(text: str) -> tuple[dict[str, int], dict[str, int]] | None:
    stripped = text.strip()
    if not stripped:
        return None

    source_target_array = re.search(
        r'"source"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\][\s\S]*?"target"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]',
        stripped,
        flags=re.IGNORECASE,
    )
    if source_target_array:
        sx, sy, tx, ty = map(int, source_target_array.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    source_target_object = re.search(
        r'"source"\s*:\s*\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*\}[\s\S]*?"target"\s*:\s*\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*\}',
        stripped,
        flags=re.IGNORECASE,
    )
    if source_target_object:
        sx, sy, tx, ty = map(int, source_target_object.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    source_target_position_array = re.search(
        r'"source_position"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\][\s\S]*?"target_position"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]',
        stripped,
        flags=re.IGNORECASE,
    )
    if source_target_position_array:
        sx, sy, tx, ty = map(int, source_target_position_array.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    source_target_position_object = re.search(
        r'"source_position"\s*:\s*\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*\}[\s\S]*?"target_position"\s*:\s*\{\s*"x"\s*:\s*(\d+)\s*,\s*"y"\s*:\s*(\d+)\s*\}',
        stripped,
        flags=re.IGNORECASE,
    )
    if source_target_position_object:
        sx, sy, tx, ty = map(int, source_target_position_object.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    source_target_flat = re.search(
        r'"source_x"\s*:\s*(\d+)\s*,\s*"source_y"\s*:\s*(\d+)[\s\S]*?"target_x"\s*:\s*(\d+)\s*,\s*"target_y"\s*:\s*(\d+)',
        stripped,
        flags=re.IGNORECASE,
    )
    if source_target_flat:
        sx, sy, tx, ty = map(int, source_target_flat.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    source_position = re.search(
        r"Source Position:\s*\((\d+)\s*,\s*(\d+)\)\s*,\s*Target Position:\s*\((\d+)\s*,\s*(\d+)\)",
        stripped,
        flags=re.IGNORECASE,
    )
    if source_position:
        sx, sy, tx, ty = map(int, source_position.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    point_pairs = re.findall(r"\((\d+)\s*,\s*(\d+)\)", stripped)
    if len(point_pairs) == 2:
        (sx, sy), (tx, ty) = point_pairs
        return ({"x": int(sx), "y": int(sy)}, {"x": int(tx), "y": int(ty)})

    csv_drag = re.fullmatch(r"\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*", stripped)
    if csv_drag:
        sx, sy, tx, ty = map(int, csv_drag.groups())
        return ({"x": sx, "y": sy}, {"x": tx, "y": ty})

    return None


def _extract_points_from_text(text: str) -> list[dict[str, int]]:
    stripped = text.strip()
    if not stripped:
        return []

    with suppress(Exception):
        payload = _extract_json_payload(stripped)
        points_payload = payload.get("points")
        if isinstance(points_payload, list):
            points = []
            for point in points_payload:
                normalized = _coerce_point(point)
                if normalized:
                    points.append(normalized)
            if points:
                return points

    tuple_points = re.findall(r"\((\d+)\s*,\s*(\d+)\)", stripped)
    if tuple_points:
        return [{"x": int(x), "y": int(y)} for x, y in tuple_points]

    array_points = re.findall(r"\[\s*(\d+)\s*,\s*(\d+)\s*\]", stripped)
    if array_points:
        return [{"x": int(x), "y": int(y)} for x, y in array_points]

    return []


def _coerce_point(value: Any) -> dict[str, int] | None:
    if isinstance(value, dict):
        if "x" in value and "y" in value:
            return {"x": int(value["x"]), "y": int(value["y"])}
        return None

    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return {"x": int(value[0]), "y": int(value[1])}

    if isinstance(value, str):
        match = re.search(r"(\d+)\s*,\s*(\d+)", value)
        if match:
            x, y = map(int, match.groups())
            return {"x": x, "y": y}

    return None


def _coerce_area_box(value: Any) -> dict[str, int] | None:
    if isinstance(value, dict):
        keys = {"x_min", "y_min", "x_max", "y_max"}
        if keys.issubset(value.keys()):
            return {
                "x_min": int(value["x_min"]),
                "y_min": int(value["y_min"]),
                "x_max": int(value["x_max"]),
                "y_max": int(value["y_max"]),
            }
        return None

    if isinstance(value, (list, tuple)) and len(value) >= 4:
        return {
            "x_min": int(value[0]),
            "y_min": int(value[1]),
            "x_max": int(value[2]),
            "y_max": int(value[3]),
        }

    if isinstance(value, str):
        matches = re.findall(r"\d+", value)
        if len(matches) >= 4:
            x_min, y_min, x_max, y_max = map(int, matches[:4])
            return {
                "x_min": x_min,
                "y_min": y_min,
                "x_max": x_max,
                "y_max": y_max,
            }

    return None


def _extract_area_boxes_from_text(text: str) -> list[dict[str, int]]:
    stripped = text.strip()
    if not stripped:
        return []

    with suppress(Exception):
        payload = _extract_json_payload(stripped)
        answer_payload = payload.get("answer")
        if isinstance(answer_payload, list):
            boxes = []
            for item in answer_payload:
                normalized = _coerce_area_box(item)
                if normalized:
                    boxes.append(normalized)
            if boxes:
                return boxes

    dict_boxes = re.findall(
        r'"x_min"\s*:\s*(\d+)\s*,\s*"y_min"\s*:\s*(\d+)\s*,\s*"x_max"\s*:\s*(\d+)\s*,\s*"y_max"\s*:\s*(\d+)',
        stripped,
        flags=re.IGNORECASE,
    )
    if dict_boxes:
        return [
            {
                "x_min": int(x_min),
                "y_min": int(y_min),
                "x_max": int(x_max),
                "y_max": int(y_max),
            }
            for x_min, y_min, x_max, y_max in dict_boxes
        ]

    tuple_boxes = re.findall(
        r"\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]",
        stripped,
    )
    if tuple_boxes:
        return [
            {
                "x_min": int(x_min),
                "y_min": int(y_min),
                "x_max": int(x_max),
                "y_max": int(y_max),
            }
            for x_min, y_min, x_max, y_max in tuple_boxes
        ]

    return []


def _build_points_payload(
    points: list[dict[str, int]],
    *,
    challenge_prompt: str = "",
    inferred_rule: str = "",
) -> dict[str, Any] | None:
    if not points:
        return None

    return {
        "challenge_prompt": challenge_prompt,
        "inferred_rule": inferred_rule,
        "points": points,
    }


def _build_area_select_payload(
    boxes: list[dict[str, int]],
    *,
    challenge_prompt: str = "",
    inferred_rule: str = "",
) -> dict[str, Any] | None:
    if not boxes:
        return None

    return {
        "challenge_prompt": challenge_prompt,
        "inferred_rule": inferred_rule,
        "points": boxes,
    }


def _build_drag_payload(
    source: Any,
    target: Any,
    *,
    challenge_prompt: str = "",
    inferred_rule: str = "",
) -> dict[str, Any] | None:
    start_point = _coerce_point(source)
    end_point = _coerce_point(target)
    if not start_point or not end_point:
        return None

    return {
        "challenge_prompt": challenge_prompt,
        "inferred_rule": inferred_rule,
        "paths": [{"start_point": start_point, "end_point": end_point}],
    }


def _normalize_glm_answer_value(
    value: Any,
    *,
    challenge_prompt: str = "",
    inferred_rule: str = "",
) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return _normalize_glm_payload(
            {
                **value,
                "challenge_prompt": value.get("challenge_prompt", challenge_prompt),
                "inferred_rule": value.get("inferred_rule", inferred_rule),
            }
        )

    if not isinstance(value, str):
        return None

    stripped = value.strip()
    if not stripped:
        return None

    challenge_type = _extract_challenge_type(stripped)
    if challenge_type:
        return {
            "challenge_prompt": challenge_prompt,
            "challenge_type": challenge_type,
            "request_type": challenge_type,
        }

    points = _extract_drag_points_from_text(stripped)
    if points:
        return _build_drag_payload(
            points[0],
            points[1],
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )

    point_payload = _build_points_payload(
        _extract_points_from_text(stripped),
        challenge_prompt=challenge_prompt,
        inferred_rule=inferred_rule,
    )
    if point_payload:
        return point_payload

    normalized_text = _normalize_glm_response_text(stripped)
    with suppress(Exception):
        payload = _extract_json_payload(normalized_text)
        return _normalize_glm_payload(
            {
                **payload,
                "challenge_prompt": payload.get("challenge_prompt", challenge_prompt),
                "inferred_rule": payload.get("inferred_rule", inferred_rule),
            }
        )

    return None


def _schema_field_names(schema: Any) -> set[str]:
    if isinstance(schema, type) and issubclass(schema, BaseModel):
        return set(getattr(schema, "model_fields", {}).keys())
    if hasattr(schema, "keys"):
        with suppress(Exception):
            return set(schema.keys())
    return set()


def _coerce_payload_for_schema(payload: dict[str, Any], schema: Any, text: str) -> dict[str, Any]:
    fields = _schema_field_names(schema)
    if not fields:
        return payload

    challenge_prompt = str(payload.get("challenge_prompt") or "")
    inferred_rule = str(payload.get("inferred_rule") or "")

    if "paths" in fields:
        if "paths" in payload:
            payload.setdefault("challenge_prompt", challenge_prompt)
            payload.setdefault("inferred_rule", inferred_rule)
            return payload

        normalized_drag = None
        if "source" in payload and "target" in payload:
            normalized_drag = _build_drag_payload(
                payload.get("source"),
                payload.get("target"),
                challenge_prompt=challenge_prompt,
                inferred_rule=inferred_rule,
            )
        elif "from" in payload and "to" in payload:
            normalized_drag = _build_drag_payload(
                payload.get("from"),
                payload.get("to"),
                challenge_prompt=challenge_prompt,
                inferred_rule=inferred_rule,
            )
        elif "source_position" in payload and "target_position" in payload:
            normalized_drag = _build_drag_payload(
                payload.get("source_position"),
                payload.get("target_position"),
                challenge_prompt=challenge_prompt,
                inferred_rule=inferred_rule,
            )
        elif "start" in payload and "end" in payload:
            normalized_drag = _build_drag_payload(
                payload.get("start"),
                payload.get("end"),
                challenge_prompt=challenge_prompt,
                inferred_rule=inferred_rule,
            )

        if not normalized_drag:
            points_payload = payload.get("points")
            if isinstance(points_payload, list) and len(points_payload) >= 2:
                normalized_drag = _build_drag_payload(
                    points_payload[0],
                    points_payload[1],
                    challenge_prompt=challenge_prompt,
                    inferred_rule=inferred_rule,
                )

        if not normalized_drag:
            extracted_drag = _extract_drag_points_from_text(text)
            if extracted_drag:
                normalized_drag = _build_drag_payload(
                    extracted_drag[0],
                    extracted_drag[1],
                    challenge_prompt=challenge_prompt,
                    inferred_rule=inferred_rule,
                )

        if normalized_drag:
            return normalized_drag

    if "points" in fields:
        area_payload = _build_area_select_payload(
            _extract_area_boxes_from_text(text),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if area_payload:
            return area_payload

        answer_payload = payload.get("answer")
        if isinstance(answer_payload, list):
            boxes = []
            for item in answer_payload:
                normalized = _coerce_area_box(item)
                if normalized:
                    boxes.append(normalized)
            if boxes:
                return _build_area_select_payload(
                    boxes,
                    challenge_prompt=challenge_prompt,
                    inferred_rule=inferred_rule,
                )

        if "points" in payload:
            payload.setdefault("challenge_prompt", challenge_prompt)
            payload.setdefault("inferred_rule", inferred_rule)
            return payload
        point_payload = _build_points_payload(
            _extract_points_from_text(text),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if point_payload:
            return point_payload

    challenge_type_field = next(
        (name for name in ("challenge_type", "request_type", "task_type", "type") if name in fields),
        None,
    )
    if challenge_type_field:
        challenge_type = (
            payload.get(challenge_type_field)
            or payload.get("challenge_type")
            or payload.get("request_type")
            or _extract_challenge_type(text)
            or _extract_challenge_type(str(payload.get("answer") or ""))
        )
        if challenge_type:
            normalized = {challenge_type_field: challenge_type}
            if "challenge_prompt" in fields:
                normalized["challenge_prompt"] = challenge_prompt
            if "requester_question" in fields and challenge_prompt:
                normalized["requester_question"] = challenge_prompt
            return normalized

    return payload


def _normalize_glm_payload(payload: dict[str, Any]) -> dict[str, Any]:
    challenge_prompt = str(payload.get("challenge_prompt") or "")
    inferred_rule = str(payload.get("inferred_rule") or "")

    normalized_answer = _normalize_glm_answer_value(
        payload.get("answer"),
        challenge_prompt=challenge_prompt,
        inferred_rule=inferred_rule,
    )
    if normalized_answer:
        return normalized_answer

    if "source" in payload and "target" in payload:
        normalized = _build_drag_payload(
            payload.get("source"),
            payload.get("target"),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if normalized:
            return normalized

    if "from" in payload and "to" in payload:
        normalized = _build_drag_payload(
            payload.get("from"),
            payload.get("to"),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if normalized:
            return normalized

    if "source_position" in payload and "target_position" in payload:
        normalized = _build_drag_payload(
            payload.get("source_position"),
            payload.get("target_position"),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if normalized:
            return normalized

    if "start" in payload and "end" in payload:
        normalized = _build_drag_payload(
            payload.get("start"),
            payload.get("end"),
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if normalized:
            return normalized

    raw_text = json.dumps(payload, ensure_ascii=False)
    points = _extract_drag_points_from_text(raw_text)
    if points:
        normalized = _build_drag_payload(
            points[0],
            points[1],
            challenge_prompt=challenge_prompt,
            inferred_rule=inferred_rule,
        )
        if normalized:
            return normalized

    return payload


class _UploadedFile:
    def __init__(self, uri: str, mime_type: str):
        self.name = uri
        self.uri = uri
        self.mime_type = mime_type


class _PatchedResponse:
    def __init__(self, *, text: str, parsed: Any, raw: dict[str, Any]):
        self.text = text
        self.parsed = parsed
        self._raw = raw

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        parsed = self.parsed
        if hasattr(parsed, "model_dump"):
            parsed = parsed.model_dump(mode=mode)
        return {"text": self.text, "parsed": parsed, "raw": self._raw}


class _GLMAsyncFiles:
    def __init__(self, storage: dict[str, dict[str, Any]]):
        self._storage = storage

    async def upload(self, file: Any, **kwargs) -> _UploadedFile:
        content = _load_binary(file)
        uri = f"glm-local://{id(content)}"
        mime_type = kwargs.get("mime_type") or _guess_mime_type(file)
        self._storage[uri] = {"content": content, "mime_type": mime_type}
        return _UploadedFile(uri=uri, mime_type=mime_type)


class _GLMAsyncModels:
    def __init__(self, settings: Any, storage: dict[str, dict[str, Any]]):
        self._settings = settings
        self._storage = storage

    def _to_image_part(self, payload: bytes, mime_type: str) -> dict[str, Any]:
        encoded = base64.b64encode(payload).decode("utf-8")
        return {"type": "image_url", "image_url": {"url": encoded}}

    def _part_to_content_item(self, part: Any) -> dict[str, Any] | None:
        text = getattr(part, "text", None)
        if text:
            return {"type": "text", "text": text}

        inline_data = getattr(part, "inline_data", None)
        if inline_data and getattr(inline_data, "data", None):
            mime_type = getattr(inline_data, "mime_type", None) or "image/png"
            return self._to_image_part(inline_data.data, mime_type)

        file_data = getattr(part, "file_data", None)
        if not file_data:
            return None

        file_uri = getattr(file_data, "file_uri", None) or getattr(file_data, "uri", None)
        mime_type = getattr(file_data, "mime_type", None) or "image/png"
        if not file_uri:
            return None

        if file_uri in self._storage:
            blob = self._storage[file_uri]
            return self._to_image_part(blob["content"], blob["mime_type"])

        if str(file_uri).startswith(("http://", "https://", "data:")):
            return {"type": "image_url", "image_url": {"url": str(file_uri)}}

        return None

    def _build_messages(self, contents: Any, config: Any) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []

        system_instruction = getattr(config, "system_instruction", None)
        if system_instruction:
            messages.append({"role": "system", "content": str(system_instruction)})

        for content in _ensure_list(contents):
            role = getattr(content, "role", None) or "user"
            items = []
            for part in _ensure_list(getattr(content, "parts", None)):
                item = self._part_to_content_item(part)
                if item:
                    items.append(item)
            if not items:
                continue
            messages.append({"role": role, "content": items})

        return messages

    def _build_payload(
        self,
        *,
        model: str,
        contents: Any,
        config: Any,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._build_messages(contents, config),
        }

        temperature = getattr(config, "temperature", None)
        if temperature is not None:
            payload["temperature"] = temperature

        if getattr(config, "response_schema", None) is not None:
            payload["response_format"] = {"type": "json_object"}

        if getattr(config, "thinking_config", None) is not None and model.startswith("glm-4.5"):
            payload["thinking"] = {"type": "enabled"}

        payload.update({k: v for k, v in kwargs.items() if k not in {"config"}})
        return payload

    def _extract_text(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("GLM response does not contain choices")

        message = choices[0].get("message") or {}
        content = message.get("content")

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(parts).strip()

        raise ValueError("GLM response content is empty")

    def _parse_response(self, text: str, config: Any) -> Any:
        schema = getattr(config, "response_schema", None)
        if not schema:
            return None

        try:
            payload = _coerce_payload_for_schema(
                _normalize_glm_payload(_extract_json_payload(text)),
                schema,
                text,
            )
        except Exception:
            normalized = _normalize_glm_answer_value(text)
            if normalized:
                payload = _coerce_payload_for_schema(normalized, schema, text)
            else:
                challenge_type = _extract_challenge_type(text)
                if challenge_type:
                    payload = _coerce_payload_for_schema(
                        {"challenge_type": challenge_type, "request_type": challenge_type},
                        schema,
                        text,
                    )
                else:
                    logger.warning("GLM structured parse fallback failed | raw_text={}", text[:500])
                    return None

        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema(**payload)

        return payload

    def _log_glm_error(self, response: httpx.Response):
        body = response.text[:2000]
        code = ""
        message = ""
        with suppress(Exception):
            payload = response.json()
            error = payload.get("error") or {}
            code = str(error.get("code") or "")
            message = str(error.get("message") or "")

        if response.status_code == 429 or code in {"1302", "1303", "1304", "1308", "1113"}:
            logger.error(
                "GLM quota/rate limit issue | http_status={} | code={} | message={}",
                response.status_code,
                code,
                message or body,
            )
            return

        if response.status_code in {401, 403} or code in {"1000", "1001", "1002", "1003", "1004"}:
            logger.error(
                "GLM auth issue | http_status={} | code={} | message={}",
                response.status_code,
                code,
                message or body,
            )
            return

        logger.error(
            "GLM request failed | status={} | code={} | body={}",
            response.status_code,
            code,
            body,
        )

    async def generate_content(self, model: str, contents: Any, **kwargs) -> _PatchedResponse:
        config = kwargs.pop("config", None)
        if config is None:
            raise ValueError("config is required for GLM compatibility mode")

        endpoint = self._settings.GLM_BASE_URL.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"

        payload = self._build_payload(model=model, contents=contents, config=config, kwargs=kwargs)
        headers = {
            "Authorization": f"Bearer {self._settings.GLM_API_KEY.get_secret_value()}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            if response.is_error:
                self._log_glm_error(response)
                response.raise_for_status()
            data = response.json()

        text = _normalize_glm_response_text(self._extract_text(data))
        parsed = self._parse_response(text, config)
        return _PatchedResponse(text=text, parsed=parsed, raw=data)


class _GLMAsyncNamespace:
    def __init__(self, settings: Any, storage: dict[str, dict[str, Any]]):
        self.files = _GLMAsyncFiles(storage)
        self.models = _GLMAsyncModels(settings, storage)


class GLMCompatibleGenAIClient:
    def __init__(self, *args, **kwargs):
        from settings import settings

        self._storage: dict[str, dict[str, Any]] = {}
        self.aio = _GLMAsyncNamespace(settings, self._storage)


def apply_gemini_patch(settings: Any):
    if not settings.GEMINI_API_KEY:
        return

    try:
        from google import genai
        from google.genai import types

        orig_init = genai.Client.__init__

        def new_init(self, *args, **kwargs):
            kwargs["api_key"] = settings.GEMINI_API_KEY.get_secret_value()

            base_url = settings.GEMINI_BASE_URL.rstrip("/")
            if base_url:
                if base_url.endswith("/v1"):
                    base_url = base_url[:-3]
                if not base_url.endswith("/gemini"):
                    base_url = f"{base_url}/gemini"

                kwargs["http_options"] = types.HttpOptions(base_url=base_url)
                logger.info(
                    f"🚀 Gemini 兼容补丁已应用 | 模型: {settings.GEMINI_MODEL} | 地址: {base_url}"
                )
            else:
                logger.info(
                    f"🚀 Gemini 官方接口已应用默认配置 | 模型: {settings.GEMINI_MODEL}"
                )
            orig_init(self, *args, **kwargs)

        genai.Client.__init__ = new_init

        file_cache: dict[str, bytes] = {}

        async def patched_upload(self_files, file, **kwargs):
            content = _load_binary(file)
            file_id = f"bypass_{id(content)}"
            file_cache[file_id] = content
            return types.File(name=file_id, uri=file_id, mime_type=_guess_mime_type(file))

        orig_generate = genai.models.AsyncModels.generate_content

        async def patched_generate(self_models, model, contents, **kwargs):
            normalized = _ensure_list(contents)
            for content in normalized:
                for index, part in enumerate(_ensure_list(getattr(content, "parts", None))):
                    file_data = getattr(part, "file_data", None)
                    file_uri = getattr(file_data, "file_uri", None) if file_data else None
                    if file_uri in file_cache:
                        content.parts[index] = types.Part.from_bytes(
                            data=file_cache[file_uri],
                            mime_type=_guess_mime_type(file_uri),
                        )

            return await orig_generate(self_models, model=model, contents=normalized, **kwargs)

        genai.files.AsyncFiles.upload = patched_upload
        genai.models.AsyncModels.generate_content = patched_generate
        logger.info("🚀 Gemini 文件上传兼容补丁加载成功")
    except Exception as exc:
        logger.error(f"❌ Gemini 兼容补丁加载失败: {exc}")


def apply_glm_patch(settings: Any):
    if not settings.GLM_API_KEY:
        return

    try:
        from google import genai

        genai.Client = GLMCompatibleGenAIClient
        logger.info(
            f"🚀 GLM 兼容补丁已应用 | 模型: {settings.GLM_MODEL} | 地址: {settings.GLM_BASE_URL}"
        )
    except Exception as exc:
        logger.error(f"❌ GLM 兼容补丁加载失败: {exc}")


def apply_llm_patch(settings: Any):
    provider = settings.LLM_PROVIDER.lower()
    if provider == "glm":
        apply_glm_patch(settings)
        return
    apply_gemini_patch(settings)
