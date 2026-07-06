# Provider Protocol Migration Plan

This document turns the protocol architecture into an execution plan.

## Scope

The near-term goal is not "support every model immediately".

The near-term goal is:

1. introduce a unified protocol-first config/adapter shape
2. port proven OpenAI and DeepSeek work into that shape
3. make future targets such as Ollama and local gateways additive presets instead of new architecture forks

The execution order should follow protocol reuse, not vendor branding:

- first consolidate `google_genai`
- then make `openai_compatible` the main reusable expansion path
- only after that, decide whether `anthropic_compatible` is truly needed

## Do Not Repeat Existing Work

Before editing code, inspect these branches:

- `add-openai-provider`
- `add-deepseekv4-provider`

Port logic from them. Do not re-derive:

- OpenAI image `data:` URL handling
- DeepSeek preset fields and reasoning toggles
- branch-era env validation patterns that already worked

## Phase 0: Documentation And Rules

Status in this branch:

- done: `AGENTS.md` updated with protocol-first rules
- done: `CLAUDE.md` updated to mirror the same plan
- done: architecture and migration docs added

## Phase 1: Normalize Settings Without Breaking Existing Users

Primary file:

- `app/settings.py`

Tasks:

1. Add canonical internal concepts:
   - `LLM_PROTOCOL`
   - `LLM_PRESET`
   - `LLM_API_KEY`
   - `LLM_BASE_URL`
   - `LLM_MODEL`
2. Keep legacy env vars working:
   - `GEMINI_*`
   - `GLM_*`
   - `OPENAI_*`
   - `DEEPSEEK_*`
3. Resolve everything into one internal object, for example:
   - `ResolvedProviderConfig`
4. Keep the current "fail before browser startup" validation behavior.

Acceptance criteria:

- existing `master` Gemini/GLM configs still resolve
- OpenAI and DeepSeek branch-era configs can be mapped into the same internal shape
- config errors remain explicit and early

## Phase 2: Split Adapter Logic By Protocol Family

Primary files:

- `app/extensions/llm_adapter.py`
- new `app/extensions/llm_protocols/*`

Tasks:

1. Move Gemini-native patching into `google_genai.py`
2. Move the generic OpenAI-compatible client into `openai_compatible.py`
3. Leave `llm_adapter.py` as a small router:
   - resolve family
   - select adapter
   - apply patch

Suggested module split:

- `base.py`: shared types/helpers
- `presets.py`: preset registry and capability flags
- `google_genai.py`: Gemini-native patch path
- `openai_compatible.py`: generic OpenAI-style transport path

Acceptance criteria:

- no provider-specific branching leaks into business services
- the router chooses by protocol family, not by vendor everywhere

## Phase 3: Fold OpenAI And DeepSeek Into Presets

OpenAI work source:

- `add-openai-provider`

DeepSeek work source:

- `add-deepseekv4-provider`

Tasks:

1. Create `openai` preset under `openai_compatible`
2. Create `deepseek` preset under `openai_compatible`
3. Port:
   - OpenAI local-image handling
   - DeepSeek reasoning/thinking preset options
4. Keep vendor quirks as preset capability flags, not as whole new protocol branches

Acceptance criteria:

- there is one OpenAI-compatible transport implementation
- OpenAI and DeepSeek only differ through preset config and capability toggles

## Phase 4: Add Ollama And Other Local/OpenAI-Compatible Targets

Priority target:

- `ollama` through `http://localhost:11434/v1`

Tasks:

1. Add `ollama` preset under `openai_compatible`
2. Document required model capability assumptions:
   - vision support
   - stable JSON/structured outputs
   - acceptable latency
3. Validate local image flow and structured parsing

Important:

- Do not create `ollama` as a separate top-level family first.
- Add an Ollama-native path only if the OpenAI-compatible path fails for a protocol reason that cannot be solved by preset flags.

This same rule applies to most third-party relays:

- if a gateway offers an OpenAI-compatible route, try that first
- if it offers both OpenAI-compatible and Anthropic-compatible routes, still start with OpenAI-compatible in this repo
- only promote Anthropic support when a real gateway/model target proves OpenAI-compatible is not enough

## Phase 5: Evaluate GLM Placement

Current repo history shows that GLM has been successful, but it also had adapter quirks.

Tasks:

1. Try to express GLM as an `openai_compatible` preset with explicit image/response quirks
2. If that keeps current behavior stable, keep it there
3. If not, allow a temporary special-case preset implementation inside the same family

Rule:

- GLM should not force business-flow branching
- if GLM keeps special handling, isolate it at preset/capability level

## Phase 6: Optional Future Family

Only after phase 1 to 5 are stable:

- evaluate `anthropic_compatible`

Do not start here. It is not the current bottleneck.

Decision gate before phase 6:

1. identify a target users actually need
2. confirm its official or gateway docs expose Anthropic Messages semantics
3. confirm the needed image-input or structured-output behavior cannot be covered by the existing OpenAI-compatible route
4. confirm the gain is worth another maintained adapter family

## Preset Registry Recommendation

A registry entry should carry the resolved operational facts, for example:

| Field | Example |
| --- | --- |
| `protocol` | `openai_compatible` |
| `preset_name` | `deepseek` |
| `base_url_default` | `https://api.deepseek.com` |
| `model_default` | `deepseek-v4-pro` |
| `request_api` | `chat_completions` |
| `image_transport` | `data_url` |
| `supports_reasoning_effort` | `true` |
| `supports_thinking_toggle` | `true` |

This avoids re-encoding vendor facts in many files.

Also treat relay/gateway facts as first-class registry data, for example:

| Field | Example |
| --- | --- |
| `gateway_kind` | `official`, `third_party_relay`, `self_hosted` |
| `supports_image_input` | `true` |
| `supports_data_url_images` | `true` |
| `supports_remote_image_url` | `false` |
| `supports_json_schema` | `false` |

This keeps "what the gateway can really do" separate from its marketing name.

## File-Level Change Budget

Prefer this order:

1. `app/settings.py`
2. `app/extensions/llm_adapter.py`
3. new `app/extensions/llm_protocols/*`
4. `.env.example`
5. `README.md` / `README.en.md`
6. workflow docs

Do not start by rewriting README copy before the internal config/adapter design exists.

## Documentation Rules During Implementation

When code lands:

- keep README focused on first-run usage
- place provider protocol detail in dedicated docs
- explain presets separately from protocol families
- state clearly when a target is supported only through `openai_compatible`

## Verification Checklist

Minimum checks for each implementation step:

1. `uv run black . -C -l 100`
2. `uv run ruff check`
3. targeted `py_compile` or equivalent syntax validation
4. a focused import/smoke check for resolved config selection when safe

Do not claim full runtime validation unless a real run was actually performed.

## What "Done On This Branch" Should Mean

For the protocol branch, "done" should be interpreted in two stages:

1. design done
   - protocol family boundaries are clear
   - preset/profile rules are documented
   - gateway classification rules are explicit
2. runtime done
   - adapter code exists
   - config resolution exists
   - at least one real target was validated through the chosen route

This branch is meant to finish stage 1 clearly before stage 2 is executed further.
