# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Epic 免费人 (Epic Awesome Gamer) is a Python automation tool that gracefully claims weekly free games from the Epic Games Store. It uses browser automation with Playwright and includes an AI-powered hCaptcha solver using the `hcaptcha-challenger` library.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Alternative: install dev dependencies
uv sync --group dev
```

### Code Quality
```bash
# Format code with Black
uv run black . -C -l 100

# Lint with Ruff
uv run ruff check --fix
```

## Architecture

### Core Components

- **`app/models.py`**: Pydantic models for Epic Games data structures (OrderItem, Order, PromotionGame)
- **`app/settings.py`**: Configuration management using pydantic-settings, extends hcaptcha-challenger's AgentConfig
- **`app/services/epic_games_service.py`**: Main game collection logic and Epic Store interaction
- **`app/services/epic_authorization_service.py`**: Authentication and login handling
- **`app/jobs.py`**: Job orchestration functions for collecting and adding games to cart
- **`app/deploy.py`**: Main deployment/execution entry point

### Key Dependencies

- **hcaptcha-challenger[camoufox]**: AI-powered captcha solving with Camoufox browser
- **playwright**: Browser automation framework
- **pydantic-settings**: Configuration management with environment variable support
- **apscheduler**: Task scheduling for automated runs

### Directory Structure

- `app/logs/`: Application logs (error.log, runtime.log, serialize.log)
- `app/runtime/`: Runtime data including screenshots, recordings, and hcaptcha cache
- `app/user_data/`: Browser profile and session data
- `docker/`: Docker compose configuration and environment files

### Configuration

Environment variables are managed through `EpicSettings` class in `settings.py`:

- `EPIC_EMAIL`: Epic Games account email (2FA must be disabled)
- `EPIC_PASSWORD`: Epic Games account password
- `GEMINI_API_KEY`: Google Gemini API key for captcha solving
- `CRON_SCHEDULE`: Cron expression for scheduled runs (default: every 5 hours)

### Browser Automation Flow

1. Initialize Epic agent with Playwright page
2. Handle authentication via `EpicAuthorization`
3. Fetch promotions from Epic Games API
4. Navigate to game pages and add free games to cart
5. Handle any hCaptcha challenges using AI solver
6. Complete checkout process

## Testing

Test execution is not allowed.

## Development Notes

- Any change that affects runtime behavior, bug handling, troubleshooting flow, user-facing guidance, or expected outcomes must be appended to `docs/maintenance-log.md` before finishing the task.
- Each maintenance-log entry should include at least: date, symptom, root-cause judgment, changed files, and result.
- Append only. Do not rewrite or remove older records unless the user explicitly asks for cleanup.

## Karpathy-Inspired Codex Working Rules

These guidelines supplement the project instructions above and should be applied by Codex for non-trivial work in this repository.

### Think Before Coding

- State assumptions explicitly when the codebase or request is ambiguous.
- If multiple interpretations are plausible, surface them instead of silently picking one.
- Prefer asking for clarification over guessing when a wrong guess could cause rework or risky edits.
- If a simpler approach exists, say so before implementing a more complex one.

### Simplicity First

- Implement the minimum change that solves the requested problem.
- Do not add speculative abstractions, configuration, or extensibility that was not requested.
- Match the repository's existing patterns unless the task explicitly requires a different design.
- If a smaller solution is clearly sufficient, prefer it.

### Surgical Changes

- Touch only files and lines that are directly relevant to the request.
- Do not refactor adjacent code, rewrite comments, or clean unrelated dead code unless asked.
- Remove only the unused code or imports made obsolete by your own change.
- Every changed line should be traceable to the requested outcome.

### Goal-Driven Execution

- For multi-step work, define a brief success path before editing.
- Verify the result with the strongest safe check available in this repository.
- Because test execution is not allowed here, use static inspection, linting, or targeted non-test verification when possible, and clearly report any verification limits.
