# -*- coding: utf-8 -*-
from __future__ import annotations

from loguru import logger
from pydantic import BaseModel, Field

from models import PromotionGame
from services.epic_games_service import EpicAgent, EpicFreeGameRateLimitError, get_promotions


class CollectionSummary(BaseModel):
    all_promotions: list[PromotionGame] = Field(default_factory=list)
    newly_claimed_promotions: list[PromotionGame] = Field(default_factory=list)
    previously_claimed_promotions: list[PromotionGame] = Field(default_factory=list)
    unconfirmed_promotions: list[PromotionGame] = Field(default_factory=list)
    failed_promotions: list[PromotionGame] = Field(default_factory=list)
    error_message: str = ""


class EpicCollectionSummaryError(RuntimeError):
    def __init__(self, message: str, summary: CollectionSummary):
        super().__init__(message)
        self.summary = summary


def _promotion_key(promotion: PromotionGame) -> str:
    return promotion.namespace or promotion.id or promotion.url


def _unique_promotions(promotions: list[PromotionGame]) -> list[PromotionGame]:
    result: list[PromotionGame] = []
    keys: set[str] = set()
    for promotion in promotions:
        key = _promotion_key(promotion)
        if key in keys:
            continue
        result.append(promotion)
        keys.add(key)
    return result


def _promotions_in_namespaces(
    promotions: list[PromotionGame], namespaces: set[str]
) -> list[PromotionGame]:
    return _unique_promotions(
        [promotion for promotion in promotions if promotion.namespace in namespaces]
    )


def _promotions_missing_from_snapshot(
    promotions: list[PromotionGame], namespaces: set[str]
) -> list[PromotionGame]:
    return _unique_promotions(
        [
            promotion
            for promotion in promotions
            if not promotion.namespace or promotion.namespace not in namespaces
        ]
    )


async def collect_epic_games_with_summary(agent: EpicAgent) -> CollectionSummary:
    summary_errors: list[str] = []
    try:
        all_promotions = get_promotions()
    except Exception as err:
        logger.warning(
            "Failed to load promotions for collection summary | error_type={}", type(err).__name__
        )
        all_promotions = []
        summary_errors.append(f"promotion snapshot unavailable: {type(err).__name__}")

    try:
        before_namespaces: set[str] | None = await agent.refresh_order_namespaces()
    except Exception as err:
        logger.warning(
            "Failed to load Epic order history before collection | error_type={}",
            type(err).__name__,
        )
        before_namespaces = None
        summary_errors.append(f"pre-collection order snapshot unavailable: {type(err).__name__}")

    if before_namespaces is None:
        previously_claimed: list[PromotionGame] = []
        pending_promotions = all_promotions
    else:
        previously_claimed = _promotions_in_namespaces(all_promotions, before_namespaces)
        pending_promotions = _unique_promotions(
            [
                promotion
                for promotion in all_promotions
                if promotion.namespace not in before_namespaces
            ]
        )

    try:
        await agent.collect_epic_games()
    except Exception as err:
        if isinstance(err, EpicFreeGameRateLimitError):
            summary = CollectionSummary(
                all_promotions=all_promotions,
                previously_claimed_promotions=previously_claimed,
                unconfirmed_promotions=pending_promotions,
                error_message="; ".join([str(err), *summary_errors]),
            )
            raise EpicCollectionSummaryError(str(err), summary) from err

        try:
            after_namespaces = await agent.refresh_order_namespaces()
        except Exception as snapshot_err:
            logger.warning(
                "Failed to refresh Epic order history after collection error | error_type={}",
                type(snapshot_err).__name__,
            )
            snapshot_message = (
                f"post-error order snapshot unavailable: {type(snapshot_err).__name__}"
            )
            summary = CollectionSummary(
                all_promotions=all_promotions,
                previously_claimed_promotions=previously_claimed,
                unconfirmed_promotions=pending_promotions,
                error_message="; ".join([str(err), *summary_errors, snapshot_message]),
            )
        else:
            newly_claimed = (
                _promotions_in_namespaces(all_promotions, after_namespaces - before_namespaces)
                if before_namespaces is not None
                else []
            )
            unconfirmed_promotions = (
                _promotions_missing_from_snapshot(pending_promotions, after_namespaces)
                if before_namespaces is not None
                else all_promotions
            )
            summary = CollectionSummary(
                all_promotions=all_promotions,
                newly_claimed_promotions=newly_claimed,
                previously_claimed_promotions=previously_claimed,
                unconfirmed_promotions=unconfirmed_promotions,
                error_message="; ".join([str(err), *summary_errors]),
            )
        raise EpicCollectionSummaryError(str(err), summary) from err

    try:
        after_namespaces = await agent.refresh_order_namespaces()
    except Exception as err:
        logger.warning(
            "Failed to refresh Epic order history after collection | error_type={}",
            type(err).__name__,
        )
        message = f"Failed to refresh Epic order history after collection: {type(err).__name__}"
        summary = CollectionSummary(
            all_promotions=all_promotions,
            previously_claimed_promotions=previously_claimed,
            unconfirmed_promotions=pending_promotions,
            error_message="; ".join([message, *summary_errors]),
        )
        return summary

    if before_namespaces is None:
        return CollectionSummary(
            all_promotions=all_promotions,
            unconfirmed_promotions=all_promotions,
            error_message="; ".join(summary_errors),
        )

    newly_claimed = _promotions_in_namespaces(all_promotions, after_namespaces - before_namespaces)
    unconfirmed_promotions = _promotions_missing_from_snapshot(pending_promotions, after_namespaces)

    return CollectionSummary(
        all_promotions=all_promotions,
        newly_claimed_promotions=newly_claimed,
        previously_claimed_promotions=previously_claimed,
        unconfirmed_promotions=unconfirmed_promotions,
        error_message="; ".join(summary_errors),
    )
