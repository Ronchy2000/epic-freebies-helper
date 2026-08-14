# -*- coding: utf-8 -*-
import asyncio

from hcaptcha_challenger.agent import AgentV
from hcaptcha_challenger.models import ChallengeSignal
from loguru import logger


async def wait_for_challenge_signal(
    agent: AgentV, *, context: str, timeout_seconds: float
) -> ChallengeSignal:
    try:
        signal = await asyncio.wait_for(agent.wait_for_challenge(), timeout=timeout_seconds)
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
