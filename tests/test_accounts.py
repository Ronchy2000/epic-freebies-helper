# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"


def _load_accounts_module():
    """Load accounts.py under a unique module name without permanently stubbing settings."""
    saved_loguru = sys.modules.get("loguru")
    log_mod = types.ModuleType("loguru")

    class _Logger:
        def info(self, *args, **kwargs):
            return None

        def warning(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

        def success(self, *args, **kwargs):
            return None

        def debug(self, *args, **kwargs):
            return None

        def catch(self, *args, **kwargs):
            def decorator(fn):
                return fn

            if args and callable(args[0]) and not kwargs:
                return args[0]
            return decorator

    log_mod.logger = _Logger()
    sys.modules["loguru"] = log_mod

    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    try:
        spec = importlib.util.spec_from_file_location(
            "accounts_under_test", APP_DIR / "accounts.py"
        )
        module = importlib.util.module_from_spec(spec)
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        if saved_loguru is None:
            sys.modules.pop("loguru", None)
        else:
            sys.modules["loguru"] = saved_loguru


accounts = _load_accounts_module()


@pytest.fixture
def fake_settings(monkeypatch):
    """Install a temporary settings stub only for the duration of one test."""
    settings_mod = types.ModuleType("settings")

    class _Settings:
        EPIC_ACCOUNTS = None
        EPIC_EMAIL = ""
        EPIC_PASSWORD = SecretStr("")

    settings_obj = _Settings()
    settings_mod.settings = settings_obj
    monkeypatch.setitem(sys.modules, "settings", settings_mod)
    return settings_obj


@pytest.fixture
def deploy_module():
    import deploy

    return deploy


def test_mask_email():
    assert accounts.mask_email("abc@example.com") == "ab***@example.com"
    assert accounts.mask_email("a@example.com") == "a***@example.com"
    assert accounts.mask_email("not-an-email") == "***"


def test_is_valid_email():
    assert accounts.is_valid_email("user@example.com")
    assert not accounts.is_valid_email("not-an-email")
    assert not accounts.is_valid_email("user@localhost")
    assert not accounts.is_valid_email("user name@example.com")
    assert not accounts.is_valid_email("../../user@example.com")
    assert not accounts.is_valid_email("user\\name@example.com")
    assert not accounts.is_valid_email("user\tname@example.com")


def test_parse_multi_accounts_passwords_may_contain_colons():
    raw = "a@example.com:pass:with:colons\nb@example.com:plain"
    parsed, invalid = accounts.parse_multi_accounts(raw)
    assert invalid == []
    assert parsed == [("a@example.com", "pass:with:colons"), ("b@example.com", "plain")]


def test_parse_multi_accounts_collects_invalid_line_numbers():
    raw = "\n".join(
        [
            "good@example.com:secret",
            "missing-colon",
            "not-an-email:password",
            " :empty-email",
            "empty-pass@example.com:",
            "also@example.com:ok",
        ]
    )
    parsed, invalid = accounts.parse_multi_accounts(raw)
    assert parsed == [("good@example.com", "secret"), ("also@example.com", "ok")]
    assert invalid == [2, 3, 4, 5]


def test_parse_accounts_absent_epic_accounts_uses_single_account(fake_settings):
    fake_settings.EPIC_ACCOUNTS = None
    fake_settings.EPIC_EMAIL = "solo@example.com"
    fake_settings.EPIC_PASSWORD = SecretStr("solo-pass")
    assert accounts.parse_accounts() == [("solo@example.com", "solo-pass")]


def test_parse_accounts_fully_invalid_falls_back_to_single_account(fake_settings):
    fake_settings.EPIC_ACCOUNTS = SecretStr("bad-line\nalso-bad")
    fake_settings.EPIC_EMAIL = "solo@example.com"
    fake_settings.EPIC_PASSWORD = SecretStr("solo-pass")
    assert accounts.parse_accounts() == [("solo@example.com", "solo-pass")]


def test_parse_accounts_partially_invalid_raises(fake_settings):
    fake_settings.EPIC_ACCOUNTS = SecretStr("good@example.com:pw\nbad-line")
    fake_settings.EPIC_EMAIL = "solo@example.com"
    fake_settings.EPIC_PASSWORD = SecretStr("solo-pass")
    with pytest.raises(RuntimeError, match="line\\(s\\): 2"):
        accounts.parse_accounts()


def test_swap_account_updates_settings(fake_settings):
    accounts.swap_account("swapped@example.com", "new-secret")
    assert fake_settings.EPIC_EMAIL == "swapped@example.com"
    assert fake_settings.EPIC_PASSWORD.get_secret_value() == "new-secret"


def test_run_accounts_without_multi_config_preserves_legacy_exception(monkeypatch, deploy_module):
    original_error = RuntimeError("legacy failure")
    calls: list[tuple[bool | str, str | None]] = []

    monkeypatch.setattr(deploy_module, "get_epic_accounts_raw", lambda: "")

    async def legacy_runner(headless=True, *, account_label=None):
        calls.append((headless, account_label))
        raise original_error

    async def unexpected_multi_runner(*args, **kwargs):
        pytest.fail("multi-account runner must not be called for legacy configuration")

    monkeypatch.setattr(deploy_module, "execute_browser_tasks_with_notification", legacy_runner)
    monkeypatch.setattr(deploy_module, "execute_multiple_accounts", unexpected_multi_runner)
    monkeypatch.setattr(
        deploy_module,
        "swap_account",
        lambda *args, **kwargs: pytest.fail("legacy configuration must not swap credentials"),
    )

    with pytest.raises(RuntimeError) as captured:
        asyncio.run(deploy_module._run_accounts(headless="virtual"))

    assert captured.value is original_error
    assert calls == [("virtual", None)]


def test_run_accounts_fully_invalid_uses_complete_legacy_credentials(monkeypatch, deploy_module):
    calls: list[bool | str] = []
    monkeypatch.setattr(deploy_module, "get_epic_accounts_raw", lambda: "invalid-line")
    monkeypatch.setattr(deploy_module.settings, "EPIC_EMAIL", "solo@example.com")
    monkeypatch.setattr(deploy_module.settings, "EPIC_PASSWORD", SecretStr("solo-pass"))

    async def legacy_runner(headless=True, *, account_label=None):
        calls.append(headless)

    async def unexpected_multi_runner(*args, **kwargs):
        pytest.fail("fully invalid multi-account input must use valid legacy credentials")

    monkeypatch.setattr(deploy_module, "execute_browser_tasks_with_notification", legacy_runner)
    monkeypatch.setattr(deploy_module, "execute_multiple_accounts", unexpected_multi_runner)

    asyncio.run(deploy_module._run_accounts(headless=False))

    assert calls == [False]


def test_run_accounts_fully_invalid_without_legacy_credentials_fails_early(
    monkeypatch, deploy_module
):
    monkeypatch.setattr(deploy_module, "get_epic_accounts_raw", lambda: "invalid-line")
    monkeypatch.setattr(deploy_module.settings, "EPIC_EMAIL", "")
    monkeypatch.setattr(deploy_module.settings, "EPIC_PASSWORD", SecretStr(""))

    async def unexpected_legacy_runner(*args, **kwargs):
        pytest.fail("browser flow must not start without any valid account credentials")

    monkeypatch.setattr(
        deploy_module, "execute_browser_tasks_with_notification", unexpected_legacy_runner
    )

    with pytest.raises(RuntimeError, match="contains no valid entries"):
        asyncio.run(deploy_module._run_accounts(headless=True))
