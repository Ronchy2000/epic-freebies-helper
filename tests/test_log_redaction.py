import io
import sys

import pytest
from loguru import logger

from utils import init_log, redact_sensitive_text


def test_exception_tracebacks_and_logs_never_leak_plaintext_credentials(monkeypatch, tmp_path):
    fake_email = "leakcheck@example.test"
    fake_password = "SuperSecretPassword!987"
    fake_multi_pass = "MultiSecret#456"
    fake_glm_key = "glm-secret-api-key-999"
    fake_proxy_pass = "ProxyPass777"
    fake_proxy = f"http://proxyuser:{fake_proxy_pass}@proxy.invalid:8080"
    fake_tg_token = "123456:FakeTelegramBotTokenABC"

    monkeypatch.setenv("EPIC_EMAIL", fake_email)
    monkeypatch.setenv("EPIC_PASSWORD", fake_password)
    monkeypatch.setenv("EPIC_ACCOUNTS", f"second@example.test:{fake_multi_pass}")
    monkeypatch.setenv("GLM_API_KEY", fake_glm_key)
    monkeypatch.setenv("BROWSER_PROXY", fake_proxy)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", fake_tg_token)

    captured_stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_stdout)

    runtime_log = tmp_path / "runtime.log"
    error_log = tmp_path / "error.log"
    init_log(runtime=runtime_log, error=error_log)

    @logger.catch(reraise=True)
    def failing_auth_step():
        local_email = fake_email
        local_password = fake_password
        local_multi = fake_multi_pass
        local_key = fake_glm_key
        assert local_email and local_password and local_multi and local_key
        raise RuntimeError(
            f"Simulated failure for {fake_email} with pw={fake_password} "
            f"proxy={fake_proxy} tg=https://api.telegram.org/bot{fake_tg_token}/sendMessage"
        )

    with pytest.raises(RuntimeError):
        failing_auth_step()

    logger.error(
        "Direct log test: email={} key={} multi={}", fake_email, fake_glm_key, fake_multi_pass
    )
    logger.complete()

    outputs = {
        "stdout": captured_stdout.getvalue(),
        "runtime.log": runtime_log.read_text(encoding="utf-8"),
        "error.log": error_log.read_text(encoding="utf-8"),
    }

    forbidden = (
        fake_email,
        fake_password,
        fake_multi_pass,
        fake_glm_key,
        fake_proxy_pass,
        fake_tg_token,
    )
    for name, content in outputs.items():
        assert content, f"{name} should contain logged failure"
        assert "le***@example.test" in content, f"{name} should retain masked email"
        for secret in forbidden:
            assert secret not in content, f"{name} leaked secret {secret!r}"


def test_redact_sensitive_text_masks_inline_proxy_and_telegram_urls():
    raw = (
        "Failed connecting via socks5://alice:TopSecret99@127.0.0.1:1080 "
        "to https://api.telegram.org/bot999999:AbCdEfGh/sendMessage"
    )
    redacted = redact_sensitive_text(raw)

    assert "TopSecret99" not in redacted
    assert "999999:AbCdEfGh" not in redacted
    assert "socks5://alice:***@127.0.0.1:1080" in redacted
    assert "https://api.telegram.org/bot***/sendMessage" in redacted
