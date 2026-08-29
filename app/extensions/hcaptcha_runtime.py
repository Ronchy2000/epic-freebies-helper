# -*- coding: utf-8 -*-
from hcaptcha_challenger.agent import AgentV
from hcaptcha_challenger.models import ChallengeSignal
from loguru import logger

from extensions.hcaptcha_adapter import wait_for_scoped_challenge


async def wait_for_challenge_signal(
    agent: AgentV, *, context: str, timeout_seconds: float
) -> ChallengeSignal:
    try:
        signal = await wait_for_scoped_challenge(agent, timeout_seconds=timeout_seconds)
    except Exception as err:
        logger.warning(
            "hCaptcha challenge wait failed | context={} | timeout={}s | err={!r}",
            context,
            timeout_seconds,
            err,
        )
        raise

    logger.info("hCaptcha challenge result | context={} | signal={}", context, signal.value)
    return signal
