from settings import EpicSettings


def test_glm_provider_without_keys_does_not_raise_misleading_gemini_validation_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "glm"
    assert cfg.GLM_API_KEY is None
    assert cfg.GEMINI_API_KEY is None
    assert cfg.llm_configuration_error is not None
    assert "LLM_PROVIDER=glm" in cfg.llm_configuration_error
    assert "GLM_API_KEY" in cfg.llm_configuration_error
    assert "Secrets (not Variables)" in cfg.llm_configuration_error


def test_glm_provider_with_glm_key_bridges_gemini_field_cleanly(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.setenv("GLM_API_KEY", "fake-glm-key-123")
    monkeypatch.setenv("GEMINI_API_KEY", "")

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "glm"
    assert cfg.llm_configuration_error is None
    assert cfg.GLM_API_KEY is not None
    assert cfg.GEMINI_API_KEY is not None
    assert cfg.GEMINI_API_KEY.get_secret_value() == "fake-glm-key-123"


def test_gemini_provider_without_key_reports_clear_gemini_configuration_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "gemini"
    assert cfg.llm_configuration_error is not None
    assert "LLM_PROVIDER=gemini" in cfg.llm_configuration_error
    assert "GEMINI_API_KEY" in cfg.llm_configuration_error
