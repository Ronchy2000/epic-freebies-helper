# Provider Configuration Guide

This document is the LLM/provider entrypoint for the repository.

It serves two purposes:

1. help regular users configure the project based on the accounts and model services they already have
2. help newcomers build a clear mental model of the difference between an API protocol family and a specific model/vendor

## Two Ideas To Keep In Mind

### 1. Protocol family

A protocol family is the API shape your application talks to.

This repository currently organizes provider support around two main families:

| Protocol family | Meaning | Typical targets |
| --- | --- | --- |
| `google_genai` | Google Gemini-style API surface | Official Gemini API, Gemini-compatible relays such as AiHubMix |
| `openai_compatible` | OpenAI-style `/v1/chat/completions` surface | OpenAI, DeepSeek, GLM, Ollama, many local gateways, some third-party platforms |

If truly needed later, a separate family may be added:

| Protocol family | Meaning | Current status |
| --- | --- | --- |
| `anthropic_compatible` | Anthropic Messages-style API surface | Not a priority yet; add it only when a real protocol-level gap appears |

### 2. preset

A preset is a named target under one protocol family, with defaults and quirks for one service.

Examples:

- `openai`
- `deepseek`
- `glm`
- `ollama`
- `minimax`
- `xiaomi_mimo`

These are not new protocol families. They are targets inside an existing family.

## How To Think About Third-Party Relays

Most relays, aggregators, and self-hosted gateways do not invent a brand-new API shape.

They usually expose one of:

- OpenAI-compatible
- Anthropic-compatible
- Gemini-compatible

So in this repository, the first question is not "which company is this?" It is:

1. Which protocol shape does it expose?
2. Does that route support image input?
3. Is structured output stable enough?
4. Does it support the image transport this captcha flow needs?

If one platform exposes both OpenAI-compatible and Anthropic-compatible routes, the current recommendation for this repository is:

1. try `openai_compatible` first
2. move to `anthropic_compatible` only if a real protocol-level gap appears

## Why This Project No Longer Adds One Provider Per Model Name

What matters for this repository is not only the model name.

The real integration requirements are:

- image input
- multimodal message formatting
- stable structured output
- the ability to turn model output into points, drag paths, and area-select targets

So the main maintenance boundary is usually the API protocol, not the vendor label.

Examples:

- `GPT`, `DeepSeek`, `GLM`, and `Ollama` often fit under `openai_compatible`
- `Gemini` and `AiHubMix` are closer to `google_genai`
- some vendors may also expose Anthropic-style routes, but that still does not justify a new family unless the existing OpenAI-compatible route is insufficient

## The Three-Layer Model

Future provider work in this repository should be understood in three layers:

### 1. protocol family

This is the API shape, for example:

- `google_genai`
- `openai_compatible`
- a future `anthropic_compatible`

### 2. preset / profile

This is a concrete target with defaults and quirks, for example:

- `openai`
- `glm`
- `deepseek`
- `ollama`
- `aihubmix`
- `custom_openai_compatible`

### 3. task model

This is the actual model name used for each captcha sub-task:

- `CHALLENGE_CLASSIFIER_MODEL`
- `IMAGE_CLASSIFIER_MODEL`
- `SPATIAL_POINT_REASONER_MODEL`
- `SPATIAL_PATH_REASONER_MODEL`

This separation lets the repository:

- map one vendor to multiple protocol routes when necessary
- reuse one protocol family across many presets
- tune per-task models without creating new provider branches

## Recommended Configuration Style

### Preferred: canonical protocol-first fields

Use these fields first:

| Secret / env | Purpose |
| --- | --- |
| `LLM_PRESET` | Select the target service |
| `LLM_API_KEY` | API key for that target |
| `LLM_BASE_URL` | Base URL override, or leave empty to use the preset default |
| `LLM_MODEL` | Default model for the captcha flow |
| `LLM_THINKING_ENABLED` | Optional thinking toggle |
| `LLM_REASONING_EFFORT` | Optional reasoning effort |

If you simply want to swap one OpenAI-compatible service for another, this is the cleanest path.

### Still supported: legacy provider-specific fields

The repository still accepts older fields such as:

- `GEMINI_*`
- `GLM_*`
- `OPENAI_*`
- `DEEPSEEK_*`
- `LLM_PROVIDER`

That means older setups do not break immediately, but the canonical fields are now the preferred long-term interface.

## Supported Presets

| preset | Protocol family | Default base URL | Default model | Notes |
| --- | --- | --- | --- | --- |
| `gemini` | `google_genai` | empty, uses the official Gemini default endpoint | `gemini-2.5-pro` | Can also work with a custom Gemini-compatible base URL |
| `aihubmix` | `google_genai` | `https://aihubmix.com` | `gemini-2.5-pro` | For AiHubMix-style Gemini relays |
| `openai` | `openai_compatible` | `https://api.openai.com/v1` | `gpt-4.1-mini` | Vision-capable model required |
| `deepseek` | `openai_compatible` | `https://api.deepseek.com` | `deepseek-v4-pro` | Supports thinking and reasoning toggles |
| `glm` | `openai_compatible` | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.6v` | Keeps the repository's proven GLM compatibility logic |
| `ollama` | `openai_compatible` | `http://127.0.0.1:11434/v1` | `qwen3-vl:8b` | Local Ollama. Pull a vision model first |
| `minimax` | `openai_compatible` | `https://api.minimaxi.com/v1` | `MiniMax-M2.7` | Replace with a vision-capable official model |
| `xiaomi_mimo` | `openai_compatible` | no default | no default | Fill the official endpoint and model from your MiMo console |
| `custom_openai_compatible` | `openai_compatible` | no default | no default | Self-hosted or third-party OpenAI-compatible service |

If a service officially supports both OpenAI-compatible and Anthropic-compatible access, do not rush to make it a new family. Model it as a preset/profile under an existing family first.

## How To Choose Based On Your Situation

### 1. I use the official Gemini API

```env
LLM_PRESET=gemini
LLM_API_KEY=your_gemini_key
LLM_BASE_URL=
LLM_MODEL=gemini-2.5-pro
```

Notes:

- Leave `LLM_BASE_URL` empty to use the official Gemini endpoint.
- Legacy `LLM_PROVIDER=gemini + GEMINI_API_KEY` still works.

### 2. I use a Gemini relay such as AiHubMix

```env
LLM_PRESET=aihubmix
LLM_API_KEY=your_aihubmix_key
LLM_BASE_URL=https://aihubmix.com
LLM_MODEL=gemini-2.5-pro
```

Notes:

- This is still a `google_genai` family target.
- Replace `LLM_BASE_URL` if your relay uses a different endpoint.

### 3. I use OpenAI / GPT

```env
LLM_PRESET=openai
LLM_API_KEY=your_openai_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

Requirements:

- The model must support image input.
- OpenAI officially recommends the Responses API for many modern workloads, but this repository still uses OpenAI-compatible `chat/completions` as the phase-1 baseline because that aligns better with many third-party services.

### 4. I use DeepSeek

```env
LLM_PRESET=deepseek
LLM_API_KEY=your_deepseek_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
LLM_THINKING_ENABLED=false
LLM_REASONING_EFFORT=high
```

Notes:

- `deepseek` is treated as an `openai_compatible` preset.
- When `LLM_THINKING_ENABLED=true`, the adapter also forwards reasoning-related flags.

### 5. I use GLM

```env
LLM_PRESET=glm
LLM_API_KEY=your_glm_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4.6v
```

Notes:

- This preset keeps the existing GLM-specific compatibility behavior that already worked in this repository.
- For this project, `glm-4.6v` is usually more reliable than `glm-4.6v-flash`.
- GLM image transport differs from most other OpenAI-compatible targets, and the project handles that separately.

### 6. I use Ollama

```env
LLM_PRESET=ollama
LLM_API_KEY=
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen3-vl:8b
```

Notes:

- Use Ollama's official OpenAI-compatible `/v1` surface first.
- `LLM_API_KEY` may be left empty.
- You must pull a vision-capable local model before running the workflow.

### 7. I use MiniMax

```env
LLM_PRESET=minimax
LLM_API_KEY=your_minimax_key
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=your_vision_capable_model
```

Notes:

- The preset default model is only a placeholder.
- This project is a multimodal captcha workflow, so you should switch to an official MiniMax model that supports image input.

### 8. I use Xiaomi MiMo

```env
LLM_PRESET=xiaomi_mimo
LLM_API_KEY=your_mimo_key
LLM_BASE_URL=fill_from_official_console
LLM_MODEL=fill_from_official_console
```

Notes:

- This route is implemented as `openai_compatible`.
- The repository does not hardcode the MiMo endpoint or model name because the publicly crawlable official entry points were not enough to confirm those values safely in this turn.
- Use the official endpoint and a vision-capable model from your own MiMo console.

### 9. I use another OpenAI-compatible service

```env
LLM_PRESET=custom_openai_compatible
LLM_API_KEY=optional_or_required_by_your_gateway
LLM_BASE_URL=https://your-gateway.example.com/v1
LLM_MODEL=your_model_name
```

This is the right path for:

- local gateways
- self-hosted vLLM / TGI / LocalAI / LM Studio style services
- other third-party `/v1/chat/completions` implementations

### 10. I use a third-party platform that supports the Anthropic protocol

This protocol branch has not yet made `anthropic_compatible` a completed runtime path.

So if your platform supports both:

- OpenAI-compatible
- Anthropic-compatible

start with the OpenAI-compatible route first, then evaluate:

- whether image input works correctly
- whether JSON / structured output is stable
- whether point/drag captcha tasks remain reliable

Only when the OpenAI-compatible route is truly insufficient, and the Anthropic route clearly solves that protocol-level gap, should this repository grow a dedicated `anthropic_compatible` family.

## What Secrets To Fill In GitHub Actions

Required in all cases:

| Secret | Meaning |
| --- | --- |
| `EPIC_EMAIL` | Epic email |
| `EPIC_PASSWORD` | Epic password |

Preferred canonical LLM secrets:

| Secret | Meaning |
| --- | --- |
| `LLM_PRESET` | target service |
| `LLM_API_KEY` | API key |
| `LLM_BASE_URL` | base URL |
| `LLM_MODEL` | model name |
| `LLM_THINKING_ENABLED` | optional |
| `LLM_REASONING_EFFORT` | optional |

Legacy fields still work too:

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `GLM_API_KEY`
- `GEMINI_API_KEY`
- `LLM_PROVIDER`

## What The Logs Show

At startup, the workflow now logs a small runtime summary that includes:

- the active `protocol`
- the active `preset`
- the active `model`
- the active `base_url`
- a masked Epic email such as `du***@example.com`

This makes it much easier to confirm from GitHub Actions logs that:

- the correct provider route was selected
- the model name is what you expected
- the Secrets were not mismatched

## Model Requirements

No matter which route you use, a model should ideally satisfy all of these:

1. supports image input
2. can produce stable JSON or near-JSON output
3. can handle point, drag, and area-select style captcha tasks
4. has acceptable latency

A model that is only good at plain chat is not automatically suitable for this project.

## How Structured Output Is Handled

To maximize compatibility, the current implementation prefers an OpenAI-compatible `chat/completions` baseline plus JSON-mode and parser fallbacks.

That means:

- services with stable JSON output behave best
- services that occasionally return semi-structured text may still work through normalization fallbacks
- services whose models cannot follow output constraints reliably will remain unstable for captcha solving

## Official Documentation Entrypoints

These official sources were referenced during this implementation and should be checked again when adding more presets:

- OpenAI
  - [Responses API migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses)
  - [Structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- Gemini
  - [Gemini API vision](https://ai.google.dev/gemini-api/docs/vision)
  - [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- Ollama
  - [OpenAI compatibility](https://docs.ollama.com/openai)
  - [Vision capability](https://docs.ollama.com/capabilities/vision)
  - [Structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- DeepSeek
  - [DeepSeek API docs](https://api-docs.deepseek.com/)
- MiniMax
  - [MiniMax OpenAI API compatibility](https://platform.minimaxi.com/document/Intelligent%20Assistant/OpenAI%20API%20Compatibility)
- Anthropic
  - [Messages API](https://docs.anthropic.com/en/api/messages)
  - [Vision](https://docs.anthropic.com/en/docs/build-with-claude/vision)

## Recommended Decision Order

If you are extending the repository instead of just trying one provider, use this order:

1. first ask whether the target fits `google_genai` or `openai_compatible`
2. if it fits an existing family, add only a preset/profile instead of a new adapter family
3. if one platform supports both OpenAI and Anthropic styles, do not build both at once; start with OpenAI-compatible
4. only promote `anthropic_compatible` to implementation work when a real protocol-level gap has been identified

## If You Just Want The Fastest Working Route

The simplest routes are usually:

1. `LLM_PRESET=glm`
2. `LLM_PRESET=openai`
3. `LLM_PRESET=deepseek`
4. `LLM_PRESET=gemini`

If you want to learn the API landscape from this project, a good reading order is:

1. `gemini` / `aihubmix`
2. `openai`
3. `deepseek`
4. `glm`
5. `ollama`
6. `custom_openai_compatible`
