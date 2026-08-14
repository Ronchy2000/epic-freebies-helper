#!/usr/bin/env python3
from hcaptcha_challenger.models import ChallengeRouterResult, ChallengeTypeEnum, RequestType

from extensions.llm_adapter import (
    CHALLENGE_TYPE_VALUES,
    KNOWN_CHALLENGE_TYPES,
    REQUEST_TYPE_VALUES,
    _coerce_payload_for_schema,
    _extract_challenge_type,
)


def main() -> None:
    expected_challenge_types = frozenset(member.value for member in ChallengeTypeEnum)
    expected_request_types = frozenset(member.value for member in RequestType)
    expected_known_types = expected_challenge_types | expected_request_types

    if CHALLENGE_TYPE_VALUES != expected_challenge_types:
        raise SystemExit(
            "ChallengeTypeEnum contract mismatch: "
            f"adapter={sorted(CHALLENGE_TYPE_VALUES)} "
            f"upstream={sorted(expected_challenge_types)}"
        )
    if REQUEST_TYPE_VALUES != expected_request_types:
        raise SystemExit(
            "RequestType contract mismatch: "
            f"adapter={sorted(REQUEST_TYPE_VALUES)} upstream={sorted(expected_request_types)}"
        )
    if KNOWN_CHALLENGE_TYPES != expected_known_types:
        raise SystemExit("Known hCaptcha type set contains values outside upstream enums")

    challenge_type = _extract_challenge_type("image_drag_multi")
    payload = _coerce_payload_for_schema(
        {"challenge_type": challenge_type}, ChallengeRouterResult, "image_drag_multi"
    )
    result = ChallengeRouterResult(**payload)
    if result.challenge_type is not ChallengeTypeEnum.IMAGE_DRAG_MULTI:
        raise SystemExit(
            f"image_drag_multi contract mismatch: result={result.challenge_type.value}"
        )

    print(
        "hCaptcha contract OK: "
        f"{len(CHALLENGE_TYPE_VALUES)} challenge types, "
        f"{len(REQUEST_TYPE_VALUES)} request types"
    )


if __name__ == "__main__":
    main()
