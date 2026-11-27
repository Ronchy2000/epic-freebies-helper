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
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "gemini"
    assert cfg.llm_configuration_error is not None
    assert "LLM_PROVIDER=gemini" in cfg.llm_configuration_error
    assert "GEMINI_API_KEY" in cfg.llm_configuration_error


def test_deepseek_provider_without_key_reports_clear_configuration_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "deepseek"
    assert cfg.DEEPSEEK_MODEL == "deepseek-flash"
    assert cfg.DEEPSEEK_API_KEY is None
    assert cfg.GEMINI_API_KEY is None
    assert cfg.llm_configuration_error is not None
    assert "LLM_PROVIDER=deepseek" in cfg.llm_configuration_error
    assert "DEEPSEEK_API_KEY" in cfg.llm_configuration_error
    assert "Secrets (not Variables)" in cfg.llm_configuration_error


def test_deepseek_provider_with_key_defaults_to_deepseek_flash_and_bridges_gemini(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-fake-deepseek-123")
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "")

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "deepseek"
    assert cfg.llm_configuration_error is None
    assert cfg.DEEPSEEK_MODEL == "deepseek-flash"
    assert cfg.DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert cfg.CHALLENGE_CLASSIFIER_MODEL == "deepseek-flash"
    assert cfg.IMAGE_CLASSIFIER_MODEL == "deepseek-flash"
    assert cfg.SPATIAL_POINT_REASONER_MODEL == "deepseek-flash"
    assert cfg.SPATIAL_PATH_REASONER_MODEL == "deepseek-flash"
    assert cfg.GEMINI_API_KEY is not None
    assert cfg.GEMINI_API_KEY.get_secret_value() == "sk-fake-deepseek-123"


def test_deepseek_provider_auto_selected_when_only_deepseek_key_is_set(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-auto-deepseek-456")
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    cfg = EpicSettings(_env_file=None)

    assert cfg.LLM_PROVIDER == "deepseek"
    assert cfg.DEEPSEEK_MODEL == "deepseek-flash"
    assert cfg.llm_configuration_error is None
