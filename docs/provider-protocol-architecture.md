# Provider Protocol Architecture

This document is the canonical architecture note for future LLM/provider work in this repository.

It exists because `master` currently has working Gemini/GLM logic, while `add-openai-provider` and `add-deepseekv4-provider` already contain successful branch-isolated work that should be **reused**, not re-invented.

## Current Repository State

As of `2026-05-09`:

- `master` contains the currently shipped Gemini/GLM path.
- `add-openai-provider` contains a working OpenAI/GPT branch implementation.
- `add-deepseekv4-provider` contains a working DeepSeek V4 branch implementation.
- Those two feature branches have **not** been merged into `master`.

Do not treat `master` as if it already has a generic multi-protocol provider architecture. It does not.

## Primary Goal

Support more LLM backends by **protocol family** rather than by adding one custom provider branch per vendor/model.

That means:

- `OpenAI`, `DeepSeek`, `MiniMax`, `Ollama`, and many local gateways should first be evaluated as `openai_compatible`.
- `Gemini official` and `Gemini-compatible relays` should stay under `google_genai`.
- A new top-level adapter family should be introduced only when official docs prove that an existing protocol family cannot cover the target.

## Non-Goals

- Do not rewrite checkout/login business flow to be provider-aware.
- Do not delete the existing provider branches.
- Do not merge branch-specific README wording into `master` before the actual protocol code lands.
- Do not assume that "OpenAI-compatible" automatically means "good enough for captcha". Image input and structured-output stability still need validation.

## Why Protocol-First Is The Right Boundary

This repository does not call every vendor SDK directly from business code.

The current integration point is:

- `app/settings.py`
- `app/extensions/llm_adapter.py`

`hcaptcha-challenger` still expects a `google-genai`-style surface. The repo works by adapting other providers into that surface.

So the stable engineering boundary is:

1. Normalize repo config into one resolved provider spec.
2. Route by protocol family.
3. Apply vendor quirks as preset-level overrides inside that family.
4. Keep login/checkout/captcha business flow unaware of provider differences.

## Three-Layer Mental Model

Future provider work in this repository should be described in three layers:

1. `protocol family`
   - the API shape the repository talks to
   - examples: `google_genai`, `openai_compatible`, and a future `anthropic_compatible`
2. `preset/profile`
   - a concrete target under one protocol family
   - examples: `openai`, `glm`, `deepseek`, `ollama`, `aihubmix`, `custom_openai_compatible`
3. `task model selection`
   - which model name is used for which captcha sub-task
   - examples: challenge classification, image classification, point reasoning, drag-path reasoning

This matters because a single vendor can expose more than one protocol shape, and one third-party gateway can front multiple upstream model families.

## Supported Protocol Families

Phase-1 families:

| Protocol family | Intended targets | Why it exists |
| --- | --- | --- |
| `google_genai` | Gemini official, Gemini-compatible relays | This is the current native path used by upstream expectations. |
| `openai_compatible` | OpenAI, DeepSeek, Ollama `/v1`, MiniMax if compatible, many local gateways, possibly GLM with preset quirks | Most non-Gemini model services converge here. |

Phase-2 optional family:

| Protocol family | Intended targets | Status |
| --- | --- | --- |
| `anthropic_compatible` | Claude or vendors exposing Anthropic Messages compatibility | Add only if a real target cannot be covered by the two phase-1 families. |

### Third-Party Gateway Rule

Many relays and API gateways expose one of these shapes:

- OpenAI-compatible
- Anthropic-compatible
- Gemini-compatible

They should not be modeled as new protocol families just because the company name is different.

Classification rule:

1. Check the official gateway docs.
2. Identify the primary protocol shape it actually supports for image input and structured outputs.
3. Map it to an existing family first.
4. Add a new top-level family only when protocol behavior truly cannot be expressed by preset flags.

## Presets Versus Protocol Families

These names should normally be implemented as **presets**, not as new top-level families:

| Preset name | Protocol family | Notes |
| --- | --- | --- |
| `openai` | `openai_compatible` | Official OpenAI target. |
| `deepseek` | `openai_compatible` | Reuse the existing DeepSeek branch work. |
| `ollama` | `openai_compatible` first | Prefer `http://localhost:11434/v1`. Native Ollama API is optional later. |
| `minimax` | `openai_compatible` if official docs confirm it | Verify official protocol first. |
| `glm` | `openai_compatible` with preset quirks | Keep current successful behavior while refactoring. |
| `gemini_official` | `google_genai` | Official Gemini API. |
| `gemini_compatible` | `google_genai` | Existing relay/base-url override pattern. |
| `custom_openai_compatible` | `openai_compatible` | For self-hosted/local gateways. |

For unfamiliar names such as `MiMo` or other local deployments, first classify the official interface. If the service exposes OpenAI-compatible or Anthropic-compatible endpoints, add a preset entry instead of a new adapter family.

If a service exposes both OpenAI-compatible and Anthropic-compatible routes, the phase-1 default for this repository should still be:

- prefer `openai_compatible` first
- only add `anthropic_compatible` after a real capability gap is observed

## Official Protocol References

Use official docs before implementation. Re-check them when behavior is unclear.

- OpenAI:
  - [Responses API migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses)
  - [Structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- Gemini:
  - [Gemini API image understanding](https://ai.google.dev/gemini-api/docs/vision)
  - [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- Ollama:
  - [OpenAI compatibility](https://docs.ollama.com/openai)
  - [Vision capability](https://docs.ollama.com/capabilities/vision)
  - [Structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- DeepSeek:
  - [DeepSeek API docs](https://api-docs.deepseek.com/)
- Anthropic:
  - [Messages API](https://docs.anthropic.com/en/api/messages)
  - [Vision](https://docs.anthropic.com/en/docs/build-with-claude/vision)

When adding a new preset, document the official source that proves which protocol family it belongs to.

## Recommended Canonical Config Model

Introduce a normalized internal config model even if legacy environment variables remain supported.

Recommended canonical fields:

| Field | Purpose |
| --- | --- |
| `LLM_PROTOCOL` | `google_genai`, `openai_compatible`, or future protocol family |
| `LLM_PRESET` | `openai`, `deepseek`, `ollama`, `glm`, `gemini_official`, `gemini_compatible`, `custom_openai_compatible`, etc. |
| `LLM_API_KEY` | Main API key for the active target |
| `LLM_BASE_URL` | Base URL for the active target |
| `LLM_MODEL` | Default model for captcha tasks |
| `LLM_IMAGE_INPUT_MODE` | Usually auto/resolved by preset; only expose if needed |
| `LLM_STRUCTURED_OUTPUT_MODE` | Usually auto/resolved by preset; only expose if needed |

### Backward Compatibility Rule

Do not break existing secrets immediately.

`app/settings.py` should:

1. Prefer the new canonical fields when present.
2. Otherwise resolve legacy branch-era fields such as:
   - `GEMINI_*`
   - `GLM_*`
   - `OPENAI_*`
   - `DEEPSEEK_*`
3. Convert them into one resolved internal provider spec.
4. Validate the final resolved spec once, before browser startup.

## Recommended Code Split

Keep `app/services/*` provider-agnostic.

Recommended ownership:

- `app/settings.py`
  - Parse legacy and canonical env vars
  - Resolve `protocol + preset + capabilities`
  - Validate required credentials early
- `app/extensions/llm_adapter.py`
  - Thin entry point only
  - Select protocol adapter and apply patch
- New protocol modules
  - `app/extensions/llm_protocols/base.py`
  - `app/extensions/llm_protocols/presets.py`
  - `app/extensions/llm_protocols/google_genai.py`
  - `app/extensions/llm_protocols/openai_compatible.py`

This keeps the current monkeypatch strategy but removes vendor sprawl from one giant file.

## Capability Flags To Resolve Per Preset

Every preset should resolve into explicit capability flags instead of scattered `if provider == ...` checks.

Suggested flags:

| Capability | Why it matters |
| --- | --- |
| `request_api` | `chat_completions`, `responses`, or Gemini native shape |
| `image_transport` | `data_url`, raw base64, uploaded file, remote URL |
| `structured_output_mode` | JSON mode, schema mode, or validation-and-retry fallback |
| `supports_thinking_toggle` | Needed for DeepSeek/GLM-style options |
| `supports_reasoning_effort` | Some vendors support it, others ignore it |
| `supports_remote_image_url` | Local gateways often differ here |
| `supports_data_url_images` | Critical for local-image captcha inputs |
| `supports_inline_base64_images` | Useful when a service accepts images but rejects remote URLs |
| `supports_json_schema` | Some protocol surfaces differ here even when they share vendor branding |

Do not hardcode these choices in business flow.

## Key Design Decision: OpenAI-Compatible Baseline

Official OpenAI now recommends the Responses API for many modern uses.

However, this repository should still use **`openai_compatible` as a least-common-denominator transport layer first**, because:

- DeepSeek compatibility usually centers around chat-completions-style requests.
- Ollama exposes OpenAI compatibility for local models.
- Many self-hosted gateways emulate OpenAI chat endpoints before anything else.

So the recommended phase-1 baseline is:

- family: `openai_compatible`
- baseline transport: `/chat/completions`
- optional future enhancement: official OpenAI `responses` mode as a preset-specific optimization

This also means:

- OpenAI official can be treated as one preset under `openai_compatible`
- GLM can stay under the same family even if it later exposes another official protocol route
- third-party relays that say "supports OpenAI API" should usually enter through this family first

Do not force the whole repo onto OpenAI Responses mode before parity is proven for the captcha workflow.

## Existing Branch Work That Must Be Reused

### `add-openai-provider`

This branch already proved:

- local image inputs can be converted to `data:` URLs for OpenAI-style image messages
- the adapter/config boundary is the correct place for OpenAI support
- branch-specific docs and env wiring were already validated once

### `add-deepseekv4-provider`

This branch already proved:

- DeepSeek should not be treated as a totally separate architecture
- preset-specific options such as thinking/reasoning knobs can live inside an OpenAI-compatible style adapter
- branch-specific docs and env wiring were already validated once

### Reuse Rule

When implementation starts, port proven logic from those branches into the unified architecture. Do not copy branch-specific README identity text into `master` unless the corresponding code is merged.

## Validation Rules

Before declaring a preset supported, verify:

1. local image input works
2. structured output is stable enough for captcha parsing
3. request/response time is acceptable for GitHub Actions runtime
4. error messages are explicit when keys or protocol settings are mismatched
5. existing Gemini/GLM success paths still behave correctly

Because full test execution is not allowed here, use targeted static checks and focused smoke verification where possible.

## Immediate Strategic Recommendation

For this repository, the practical support order should be:

1. keep `google_genai` for Gemini official and Gemini-style relays
2. use `openai_compatible` as the main expansion path for:
   - OpenAI official
   - GLM OpenAI-compatible route
   - DeepSeek if/when its multimodal path is good enough
   - OpenRouter-like relays
   - self-hosted gateways
3. add `anthropic_compatible` only when:
   - an actual target is important to users
   - OpenAI-compatible coverage is not enough
   - the capability gap is protocol-level, not just a preset quirk
