# GitHub Actions Guide

Language versions:

- [简体中文](README.md)
- English (this page)

The repository already includes [`.github/workflows/epic-gamer.yml`](epic-gamer.yml). Using it directly is the recommended way to run scheduled claims.

The default schedule is now once per week: `Thursday 23:20 China Standard Time` (`UTC 15:20` in GitHub cron). That puts the run after the weekly Epic refresh, which is a better default for most users.

## What the Workflow Does

The workflow runs the following steps on a GitHub-hosted runner:

1. Check out the repository.
2. Install `uv` and Python 3.12.
3. Install system dependencies.
4. Run `uv sync` to install Python dependencies.
5. Download Camoufox browser assets.
6. Install Playwright Firefox as a browser fallback.
7. Run `uv run app/deploy.py` inside `xvfb`.

The workflow is triggered by GitHub `schedule` and `workflow_dispatch`. APScheduler inside the repository is disabled in this mode to avoid duplicate scheduling.

## Default Schedule

- Default schedule: once every Thursday
- GitHub cron: `20 15 * * 4`
- Time: `Thursday 15:20 UTC` / `Thursday 23:20 China Standard Time`

If you want a different time, edit the `schedule` section inside [`.github/workflows/epic-gamer.yml`](epic-gamer.yml). The easiest way is to open that file on GitHub, click the pencil icon, update the cron line, and commit the change.

## Required Secrets

Required in all cases:

| Secret | Description |
| --- | --- |
| `EPIC_EMAIL` | Epic account email, with 2FA disabled |
| `EPIC_PASSWORD` | Epic account password, with 2FA disabled |

If you use the official Gemini API:

| Secret | Description |
| --- | --- |
| `LLM_PROVIDER` | Recommended value: `gemini` |
| `GEMINI_API_KEY` | Gemini API key |
| `GEMINI_BASE_URL` | Leave empty to use the official default endpoint |
| `GEMINI_MODEL` | Optional, defaults to `gemini-2.5-pro` |

If you use a Gemini-compatible relay such as AiHubMix:

| Secret | Description |
| --- | --- |
| `LLM_PROVIDER` | Recommended value: `gemini` |
| `GEMINI_API_KEY` | AiHubMix key |
| `GEMINI_BASE_URL` | For example `https://aihubmix.com` |
| `GEMINI_MODEL` | Optional, defaults to `gemini-2.5-pro` |

If you use GLM:

| Secret | Description |
| --- | --- |
| `LLM_PROVIDER` | Recommended value: `glm` |
| `GLM_API_KEY` | Zhipu API key |
| `GLM_BASE_URL` | Optional, defaults to `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | Optional, recommended: `glm-4.6v` |

The `GLM` path does not require a separate `GEMINI_API_KEY`. The project now bridges that lower-level compatibility requirement automatically.

The program also checks these per-task overrides first. If they are not set, they fall back automatically to `GLM_MODEL` or `GEMINI_MODEL`:

- `CHALLENGE_CLASSIFIER_MODEL`
- `IMAGE_CLASSIFIER_MODEL`
- `SPATIAL_POINT_REASONER_MODEL`
- `SPATIAL_PATH_REASONER_MODEL`

These values can also be configured directly as GitHub Secrets. The workflow already passes them through.

## Local One-Shot Debugging

To reproduce the same entrypoint locally, use the same runtime path as the workflow:

1. Copy [`.env.example`](../../.env.example) to `.env`
2. Fill in your own account and model configuration
3. Run `uv sync --group dev`
4. Run `ENABLE_APSCHEDULER=false uv run app/deploy.py`

`.env`, `.venv`, and `app/volumes/` are already ignored by `.gitignore`, so local sensitive/runtime files stay out of commits.

## Why GLM Cannot Simply Reuse the Gemini Base URL

The lower-level dependency is `hcaptcha-challenger`, and internally it uses `google-genai`-style multimodal upload plus `generate_content`.

This repository now includes an adapter layer:

- The official Gemini API and AiHubMix-style Gemini-compatible relays continue to use the existing compatibility patch.
- GLM is translated automatically into Zhipu's OpenAI-compatible `chat/completions` requests.

That is why GLM here should use a vision-capable model such as `glm-4.6v`, not a plain text coding model.
If `glm-4.6v-flash` starts returning overload messages such as "the current model is too busy", switching to `GLM_MODEL=glm-4.6v` is usually more stable.

## Recommended First Run

After forking, open the `Actions` page in your fork, enter `Epic Awesome Gamer (Scheduled)`, and click `Enable workflow` once, or GitHub will not activate the scheduled run for that fork.

1. Fork the repository.
2. Make the fork private.
3. Configure Secrets.
4. Trigger one manual run from the `Actions` page.
5. Inspect the logs to confirm that login and claiming both completed.

> [!IMPORTANT]
> Do not cancel the workflow just because it is still retrying after around 5 minutes. Login captcha and checkout verification can fail repeatedly, retry many times, and even hit timeouts before finally passing. Some successful runs still take 15 to 20 minutes.

If `Camoufox` fails to download or bootstrap on a specific runner, the workflow now continues with an installed Playwright Firefox fallback instead of failing immediately during browser setup.

## Keeping Your Fork Updated

To avoid running outdated code in your fork, sync regularly with the upstream repository (`Ronchy2000/epic-freebies-helper`), especially before retrying after an unexpected failure.

On the GitHub web UI, open your fork's default branch, click `Sync fork` -> `Update branch`, and rerun the workflow afterward. If GitHub reports a conflict, click `Compare changes`, follow the prompt to create and merge the pull request, and then return to `Actions` to run the workflow again.

## FAQ

### 1. The Action ran but login got stuck

Epic may rate-limit or risk-control GitHub's shared outbound IPs. In many cases, rerunning at a different time resolves it.

If the logs are still retrying captcha challenges, do not click `Cancel workflow` too early. A run that ends in a manual cancel like the example below does not prove the automation had already failed after only a few minutes:

![Do not cancel the Actions run too early](../../docs/images/faq/action-cancel-too-early.svg)

The workflow now attempts to upload an extra `epic-screenshots-<run_id>` artifact. This artifact only appears at the bottom of the run page when the login, risk-control, or auth flow actually saved screenshots. If the logs only show messages like `Timeout waiting for #email`, `Just a moment...`, or `One more step`, and the Artifacts section contains a screenshot package, inspect that artifact first.

If you need to report a failed or suspicious run, keep this distinction in mind:

- For a public fork, the Actions run URL is usually enough because maintainers can inspect the run page directly.
- For a private fork, upload the artifact zip files that were actually generated for that run. Maintainers cannot access private Actions pages or private run artifacts.

### 2. Logs mention `privacy-policy correction`

This is usually not a `GLM`, `Gemini`, or `AiHubMix` API issue. It means the Epic account was redirected after login to a page like `/id/login/correction/privacy-policy`.

Fix it by signing in to Epic once in a normal browser, completing the privacy-policy confirmation page manually, and then rerunning the workflow.

### 3. GLM returns 429 / 400 / 401

Check these items first:

- If logs contain `message=该模型当前访问量过大，请您稍后再试` or HTTP `429`, switch `GLM_MODEL` to `glm-4.6v` first and avoid `glm-4.6v-flash`.
- Confirm `LLM_PROVIDER=glm`.
- Confirm `GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`.
- Confirm `GLM_MODEL=glm-4.6v`.
- Confirm the API key is still valid.

Example log for a 429 rate-limit case:

![GLM 429 rate limit log](../../docs/images/faq/glm-429-rate-limit.png)

### 4. Why is the default schedule weekly now?

Epic weekly freebies usually refresh on Thursday. For most regular users, running once after the refresh is a better default: it uses fewer GitHub Actions minutes and matches the real claim cycle more closely.

If you prefer more redundancy, you can still edit the workflow and run it multiple times per week, or keep using manual `Run workflow` as a fallback.
