# -*- coding: utf-8 -*-
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

from hcaptcha_challenger.agent import AgentConfig
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import SettingsConfigDict

from extensions.hcaptcha_adapter import apply_hcaptcha_drag_patch
from extensions.llm_adapter import apply_llm_patch

# --- 核心路径定义 ---
PROJECT_ROOT = Path(__file__).parent
VOLUMES_DIR = PROJECT_ROOT.joinpath("volumes")
LOG_DIR = VOLUMES_DIR.joinpath("logs")
USER_DATA_DIR = VOLUMES_DIR.joinpath("user_data")
RUNTIME_DIR = VOLUMES_DIR.joinpath("runtime")
SCREENSHOTS_DIR = VOLUMES_DIR.joinpath("screenshots")
RECORD_DIR = VOLUMES_DIR.joinpath("record")
HCAPTCHA_DIR = VOLUMES_DIR.joinpath("hcaptcha")


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _coerce_secret_input(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, SecretStr):
        value = value.get_secret_value()
    value = str(value).strip()
    return value or None


# === 配置类定义 ===
class EpicSettings(AgentConfig):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    GEMINI_API_KEY: SecretStr | None = Field(default=None, description="Gemini/AiHubMix API key")

    GEMINI_BASE_URL: str = Field(
        default="", description="Optional Gemini-compatible base URL override"
    )

    GEMINI_MODEL: str = Field(default="gemini-2.5-pro", description="Gemini default model")

    LLM_PROVIDER: str = Field(default="", description="Supported values: gemini, glm")

    GLM_API_KEY: SecretStr | None = Field(default=None, description="GLM API key")

    GLM_BASE_URL: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", description="GLM OpenAI-compatible base URL"
    )

    GLM_MODEL: str = Field(default="glm-4.6v", description="GLM vision-capable default model")
    GLM_REQUEST_TIMEOUT_SECONDS: float = Field(default=50.0, gt=5.0, le=120.0)

    BROWSER_BACKEND: str = Field(
        default="auto", description="Supported values: auto, camoufox, playwright"
    )
    BROWSER_PROXY: SecretStr | None = Field(
        default=None, description="Optional HTTP(S) or SOCKS proxy URL shared by browser backends."
    )

    EPIC_ACCOUNTS: SecretStr | None = Field(
        default=None, description="Optional multiline email:password account list"
    )
    EPIC_EMAIL: str = Field(default_factory=lambda: _env("EPIC_EMAIL", ""))
    EPIC_PASSWORD: SecretStr = Field(default_factory=lambda: _env("EPIC_PASSWORD", ""))
    DISABLE_BEZIER_TRAJECTORY: bool = Field(default=False)
    RETRY_ON_FAILURE: bool = Field(
        default=False,
        description="Disable hcaptcha-challenger recursive retries; callers own retry limits.",
    )
    WAIT_FOR_CHALLENGE_VIEW_TO_RENDER_MS: int = Field(default=3000)

    CHALLENGE_CLASSIFIER_MODEL: str = Field(default="")
    IMAGE_CLASSIFIER_MODEL: str = Field(default="")
    SPATIAL_POINT_REASONER_MODEL: str = Field(default="")
    SPATIAL_PATH_REASONER_MODEL: str = Field(default="")

    cache_dir: Path = HCAPTCHA_DIR.joinpath(".cache")
    challenge_dir: Path = HCAPTCHA_DIR.joinpath(".challenge")
    captcha_response_dir: Path = HCAPTCHA_DIR.joinpath(".captcha")

    ENABLE_APSCHEDULER: bool = Field(default=True)
    TASK_TIMEOUT_SECONDS: int = Field(default=900)
    # A successful hosted-runner login has taken nearly four minutes. Keep enough room for a
    # second challenge while still bounding one authentication attempt.
    AUTH_TIMEOUT_SECONDS: int = Field(default=420, ge=120, le=900)
    # Repeated login attempts increase Epic's risk score; one clean retry is enough before
    # handing the account back to a normal browser.
    AUTH_MAX_ATTEMPTS: int = Field(default=2, ge=1, le=8)
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    CELERY_WORKER_CONCURRENCY: int = Field(default=1)
    CELERY_TASK_TIME_LIMIT: int = Field(default=1200)
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=900)

    @model_validator(mode="before")
    @classmethod
    def _bridge_provider_credentials(cls, raw_data):
        data = dict(raw_data) if isinstance(raw_data, dict) else {}

        provider = str(data.get("LLM_PROVIDER") or "").strip().lower()
        glm_key = _coerce_secret_input(data.get("GLM_API_KEY"))
        gemini_key = _coerce_secret_input(data.get("GEMINI_API_KEY"))

        if provider not in {"gemini", "glm"}:
            data["LLM_PROVIDER"] = "glm" if glm_key else "gemini"

        # `hcaptcha-challenger` still expects GEMINI_API_KEY in its base settings model.
        # Seed it before field validation so GLM-only environments work in local runs and CI.
        if gemini_key is None and glm_key is not None:
            data["GEMINI_API_KEY"] = glm_key

        return data

    @model_validator(mode="after")
    def _apply_runtime_defaults(self):
        for field_name in (
            "GEMINI_BASE_URL",
            "GEMINI_MODEL",
            "LLM_PROVIDER",
            "GLM_BASE_URL",
            "GLM_MODEL",
            "BROWSER_BACKEND",
            "EPIC_EMAIL",
            "CHALLENGE_CLASSIFIER_MODEL",
            "IMAGE_CLASSIFIER_MODEL",
            "SPATIAL_POINT_REASONER_MODEL",
            "SPATIAL_PATH_REASONER_MODEL",
        ):
            value = getattr(self, field_name, None)
            if isinstance(value, str):
                setattr(self, field_name, value.strip())

        provider = (self.LLM_PROVIDER or "").strip().lower()
        if provider not in {"gemini", "glm"}:
            provider = "glm" if self.GLM_API_KEY else "gemini"
        self.LLM_PROVIDER = provider

        if self.GEMINI_API_KEY is None and self.GLM_API_KEY is not None:
            self.GEMINI_API_KEY = self.GLM_API_KEY

        provider_default = self.GLM_MODEL if provider == "glm" else self.GEMINI_MODEL
        if not self.CHALLENGE_CLASSIFIER_MODEL:
            self.CHALLENGE_CLASSIFIER_MODEL = provider_default
        if not self.IMAGE_CLASSIFIER_MODEL:
            self.IMAGE_CLASSIFIER_MODEL = provider_default
        if not self.SPATIAL_POINT_REASONER_MODEL:
            self.SPATIAL_POINT_REASONER_MODEL = provider_default
        if not self.SPATIAL_PATH_REASONER_MODEL:
            self.SPATIAL_PATH_REASONER_MODEL = provider_default

        browser_backend = (self.BROWSER_BACKEND or "").strip().lower()
        self.BROWSER_BACKEND = browser_backend or "auto"

        return self

    @property
    def user_data_dir(self) -> Path:
        target_ = self.user_data_dir_for("camoufox")
        return target_

    def user_data_dir_for(self, backend: str) -> Path:
        backend = (backend or "camoufox").strip().lower()
        suffix = f".{backend}"
        target_ = USER_DATA_DIR.joinpath(f"{self.EPIC_EMAIL}{suffix}")
        target_.mkdir(parents=True, exist_ok=True)
        return target_

    @property
    def llm_configuration_error(self) -> str | None:
        provider = (self.LLM_PROVIDER or "").strip().lower()

        if provider == "glm" and self.GLM_API_KEY is None:
            return (
                "Invalid LLM configuration: LLM_PROVIDER=glm but GLM_API_KEY is empty. "
                "Set GLM_API_KEY in GitHub Actions Secrets, or switch LLM_PROVIDER to gemini "
                "if you intend to use Gemini/AiHubMix."
            )

        if provider == "gemini" and self.GEMINI_API_KEY is None:
            return (
                "Invalid LLM configuration: LLM_PROVIDER=gemini but GEMINI_API_KEY is empty. "
                "Set GEMINI_API_KEY in GitHub Actions Secrets, or switch LLM_PROVIDER to glm "
                "if you intend to use GLM."
            )

        return None


settings = EpicSettings()
settings.ignore_request_questions = ["Please drag the crossing to complete the lines"]
apply_llm_patch(settings)
apply_hcaptcha_drag_patch()
