# -*- coding: utf-8 -*-
"""
Multi-account support for Epic Games freebies helper.

Supports two input formats:
  1. EPIC_ACCOUNTS: multiline env var, one "email:password" per line (optional)
  2. EPIC_EMAIL + EPIC_PASSWORD: single-account path (default / fallback)
"""

from __future__ import annotations

from typing import List, Tuple

from loguru import logger
from pydantic import SecretStr


def mask_email(email: str) -> str:
    """Mask an email address before writing it to logs or notifications."""
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"

    masked_local = f"{local[:2]}***" if len(local) > 2 else f"{local[:1]}***"
    return f"{masked_local}@{domain}"


def is_valid_email(email: str) -> bool:
    """Lightweight email shape check used for EPIC_ACCOUNTS validation."""
    email = (email or "").strip()
    if not email or any(character.isspace() for character in email):
        return False
    if any(character in email for character in ("/", "\\")):
        return False
    if any(ord(character) < 32 or ord(character) == 127 for character in email):
        return False
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


def parse_multi_accounts(raw: str) -> tuple[list[tuple[str, str]], list[int]]:
    """
    Parse multiline EPIC_ACCOUNTS content.

    Returns:
        (valid accounts, invalid 1-based line numbers)
    """
    accounts: list[tuple[str, str]] = []
    invalid_lines: list[int] = []

    for line_number, raw_line in enumerate(raw.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue

        if ":" not in line:
            invalid_lines.append(line_number)
            continue

        email, password = line.split(":", 1)
        email = email.strip()
        password = password.strip()

        if not is_valid_email(email) or not password:
            invalid_lines.append(line_number)
            continue

        accounts.append((email, password))

    return accounts, invalid_lines


def get_epic_accounts_raw() -> str:
    """Return stripped EPIC_ACCOUNTS content, or empty string when unset."""
    from settings import settings

    if settings.EPIC_ACCOUNTS is None:
        return ""
    return settings.EPIC_ACCOUNTS.get_secret_value().strip()


def parse_accounts() -> List[Tuple[str, str]]:
    """
    Backward-compatible helper that returns only valid account tuples.

    Prefer the deploy path that uses get_epic_accounts_raw() + parse_multi_accounts()
    so partially invalid multi-account configs can fail visibly.
    """
    raw = get_epic_accounts_raw()
    if raw:
        accounts, invalid_lines = parse_multi_accounts(raw)
        if accounts and not invalid_lines:
            logger.info("Parsed {} account(s) from EPIC_ACCOUNTS", len(accounts))
            return accounts
        if accounts and invalid_lines:
            # Callers that still use this helper should not silently drop lines.
            raise RuntimeError(
                "Invalid EPIC_ACCOUNTS entries on line(s): " + ", ".join(map(str, invalid_lines))
            )
        logger.warning(
            "EPIC_ACCOUNTS is set but no valid entries were parsed; "
            "falling back to EPIC_EMAIL / EPIC_PASSWORD if available"
        )

    from settings import settings

    email = (settings.EPIC_EMAIL or "").strip()
    password = settings.EPIC_PASSWORD.get_secret_value().strip()
    if email and password:
        logger.info("Using single account from EPIC_EMAIL/EPIC_PASSWORD")
        return [(email, password)]
    return []


def swap_account(email: str, password: str) -> None:
    """Swap the active account credentials on the global settings object."""
    from settings import settings

    settings.EPIC_EMAIL = email
    settings.EPIC_PASSWORD = SecretStr(password)

    logger.info("Switched to account: {}", mask_email(email))
