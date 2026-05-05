<div align="center">
  <h1>Epic Weekly Free Games Helper</h1>
  <p>A fully free Epic weekly free-games claimer powered by GitHub Actions.</p>

  <p>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/actions/workflows/epic-gamer.yml"><img src="https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-freebies-helper/epic-gamer.yml?branch=master&style=flat-square" alt="Workflow Status" /></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/Ronchy2000/epic-freebies-helper?style=flat-square" alt="License" /></a>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/stargazers"><img src="https://img.shields.io/github/stars/Ronchy2000/epic-freebies-helper?style=flat-square" alt="Stars" /></a>
    <a href="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper"><img src="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper&left_text=views" alt="Views" /></a>
  </p>
</div>

[🇺🇸 English](README.en.md) | [🇨🇳 中文文档](README.md)

`Epic Weekly Free Games Helper` is built for regular users. It runs on GitHub Actions by default, so you do not need a server, a permanently running local machine, or any extra deployment. If you have a GitHub account, you can get started by following the setup steps below.

The key point is simple: it is **fully free**. In the common setup, you do not need to pay for a server or keep a local machine online. GitHub Actions is enough to run the weekly claim flow automatically.

The project is built upon community open-source solutions and incorporates `GLM` multimodal support. Its core objective is to ensure the stability of auto-login, captcha recognition, and checkout processes. Compared to Gemini, the GLM setup process is more straightforward, and its free quota is sufficient for regular automated execution.

**If you choose the `GLM` route, make sure the related Zhipu account has already passed real-name verification, or the API may remain unavailable.**
> 2026.4.28: Some users reported that the API can be called without real-name verification, so if you encounter unavailability, please check this setting.

If you do not have a Zhipu account yet, you can register through this invite link: [BigModel.cn invite link](https://www.bigmodel.cn/invite?icode=A75tQCByIvrO4k6SLkU5BQZ3c5owLmCCcMQXWcJRS8E%3D).

Community discussion and feedback are welcome on [LINUX DO](https://linux.do/t/topic/2036835/4).

If the project worked for you, feel free to leave a message here too: [🎉 Success Stories / Successful runs](https://github.com/Ronchy2000/epic-freebies-helper/discussions/3).

If you run into an error, please feel free to open an [Issue](https://github.com/Ronchy2000/epic-freebies-helper/issues). The choice is always yours, and I respect that; still, if you are willing to leave feedback instead of deleting the repo and walking away, those real reports and user experiences directly help improve the project and keep this effort moving forward.

---

## Feature Overview

| Feature | Description |
| --- | --- |
| Auto login | Signs in to your Epic account automatically |
| Weekly free games discovery | Fetches and identifies currently claimable free titles |
| Auto claim | Opens product pages and completes the checkout flow |
| Captcha handling | Supports login captcha and checkout security checks |
| Scheduled execution | Runs once every Thursday by default on GitHub Actions and can be adjusted |

---

## Why GLM Is Recommended

The GLM path is primarily recommended for the following advantages:

- Less configuration: in most cases you only need `GLM_API_KEY` and `GLM_MODEL`.
- Lower cost: the free quota of `glm-4.6v` is often enough for the weekly-claim use case.
- More stable for this project: `glm-4.6v-flash` can occasionally fail under load with "the current model is too busy", so `glm-4.6v` is the safer default.
- Better fit for users in China: you do not need to solve Google AI Studio registration or availability first.
- Capability already validated: login captcha, checkout verification, drag, click, and multi-select challenges have all been verified in real runs.

---

## Prerequisites

- Your Epic account email and password.
- Epic account 2FA must be disabled (email, SMS, or authenticator app).
- A GLM account with `GLM_API_KEY` prepared for captcha solving.

---

## 🚀 Quick Start

Basic configuration and execution steps:

### 1. Fork the repository and enable Actions

> [!TIP]
> If you have already forked this repository before, go to your fork on GitHub first and click `Sync fork` -> `Update branch` so your copy is aligned with the latest upstream changes before you continue.

After forking, open the `Actions` page in your fork, enter `Epic Awesome Gamer (Scheduled)`, and click `Enable workflow` once, or GitHub will not activate the scheduled run for that fork.

- Fork the repo to your own GitHub account.
- Open `Actions` and enable the workflow named `Epic Awesome Gamer (Scheduled)`.

### 2. Configure Secrets

Go to `Settings` -> `Secrets and variables` -> `Actions`.

Required in all cases:

| Secret | Example value |
| --- | --- |
| `EPIC_EMAIL` | your_epic_email@example.com |
| `EPIC_PASSWORD` | your_epic_password |

If you use `GLM`, start with this set:

**If you plan to use `GLM_API_KEY`, make sure the related Zhipu account has already passed real-name verification, or the API may remain unavailable.**

| Secret | Example value |
| --- | --- |
| `LLM_PROVIDER` | glm |
| `GLM_API_KEY` | Your Zhipu API key |
| `GLM_BASE_URL` | https://open.bigmodel.cn/api/paas/v4 |
| `GLM_MODEL` | glm-4.6v |

Configuration page example:
![GLM API setup](docs/images/tutorial/GLM-API.png)

![GitHub Actions Secrets example](docs/images/tutorial/step2-actions-secrets.png)

If you use the `official Gemini API`, use this set:

| Secret | Example value |
| --- | --- |
| `LLM_PROVIDER` | gemini |
| `GEMINI_API_KEY` | Your Gemini API key |
| `GEMINI_BASE_URL` | leave empty |
| `GEMINI_MODEL` | gemini-2.5-pro |

If you use a Gemini-compatible relay such as `AiHubMix`, use this set:

| Secret | Example value |
| --- | --- |
| `LLM_PROVIDER` | gemini |
| `GEMINI_API_KEY` | Your AiHubMix key |
| `GEMINI_BASE_URL` | https://aihubmix.com |
| `GEMINI_MODEL` | gemini-2.5-pro |

Notes:

- The current codebase supports both the `official Gemini API` and Gemini-compatible relays such as `AiHubMix`.
- The variable name is `GEMINI_BASE_URL`, not `GEMINI_BASE_MODEL`.
- When you use the `official Gemini API`, leave `GEMINI_BASE_URL` empty so the SDK uses Google's default endpoint.
- Only set `GEMINI_BASE_URL` when you use `AiHubMix` or another Gemini-compatible relay.
- For `GLM`, `glm-4.6v` is the recommended starting value; `glm-4.6v-flash` can fail during peak traffic.
- For `Gemini` / `AiHubMix`, `GEMINI_MODEL=gemini-2.5-pro` is the recommended starting value.
- If `CHALLENGE_CLASSIFIER_MODEL`, `IMAGE_CLASSIFIER_MODEL`, `SPATIAL_POINT_REASONER_MODEL`, and `SPATIAL_PATH_REASONER_MODEL` are left empty, they automatically follow the active provider default, meaning `GLM_MODEL` or `GEMINI_MODEL`.
- If you do not want to split models by task yet, leave all four override fields empty.
- The `GLM` path does not require an extra `GEMINI_API_KEY`.

If you do want to override those four model fields explicitly, use values like these:

| Secret | GLM example | Gemini / AiHubMix example |
| --- | --- | --- |
| `CHALLENGE_CLASSIFIER_MODEL` | empty or `glm-4.6v` | empty or `gemini-2.5-pro` |
| `IMAGE_CLASSIFIER_MODEL` | empty or `glm-4.6v` | empty or `gemini-2.5-pro` |
| `SPATIAL_POINT_REASONER_MODEL` | empty or `glm-4.6v` | empty or `gemini-2.5-pro` |
| `SPATIAL_PATH_REASONER_MODEL` | empty or `glm-4.6v` | empty or `gemini-2.5-pro` |

### 3. Run the workflow manually once

- Open the `Actions` page.
- Select `Epic Awesome Gamer (Scheduled)`.
- Click `Run workflow`.

> [!IMPORTANT]
> **Note**: Due to Epic's risk-control mechanisms, the script may trigger multiple retries during captcha and checkout stages, which can extend the total runtime to 15-20 minutes. It is recommended not to interrupt the workflow manually while it is in progress.

### 4. Check the logs

When the run succeeds, the logs usually contain lines like:

```text
Login success
Right account validation success
Authentication completed
Starting free games collection process
All week-free games are already in the library
```

Example log with warnings but final success:

![Warnings but final success log example](docs/images/tutorial/step4-log-success-with-warnings-1.png)

If the logs show repeated retries and you cancel the run manually, like the example below, that still does not prove the automation had already failed. In many cases it simply had not finished yet:

![Do not cancel the Actions run too early](docs/images/faq/action-cancel-too-early.svg)

---

## Run Logs and Artifacts

Each GitHub Actions run attempts to upload the artifacts below. GitHub only shows artifacts that actually contain files, so different users may see only some of them. That is normal.

| Artifact | Content | When it usually appears |
| --- | --- |
| `epic-logs-<run_id>` | Runtime logs | Almost every run |
| `epic-runtime-<run_id>` | `promotions.json`, `purchase_debug` screenshots, and debug text | Common after the run reaches freebie discovery, product pages, or checkout |
| `epic-screenshots-<run_id>` | Extra screenshots for login failures, risk-control pages, and auth debugging | Only when the login, risk-control, or auth flow saved screenshots |

Download location:

1. Open the specific Actions run page.
2. Scroll to the bottom.
3. Find `Artifacts`.
4. Download the zip files.

What to inspect first:

| Package | What to inspect first |
| --- | --- |
| `epic-logs-<run_id>.zip` | After extraction, open the log files directly |
| `epic-runtime-<run_id>.zip` | If present, check the screenshots and debug text inside `purchase_debug/` first |
| `epic-screenshots-<run_id>.zip` | If present, check login, risk-control, or auth screenshots first |

These files are generated and uploaded after each GitHub Actions run. They are not fixed directories pre-shipped in the repository root.

If you need to open an issue, do not paste only a short log excerpt.

- If your fork is public, the Actions run URL is usually enough because maintainers can inspect the run page directly.
- If your fork is private, you must upload the artifact zip files that were actually generated for that run. Maintainers cannot access private Actions pages or private run artifacts.

---

## Local One-Shot Debugging

If you want to reproduce the same entrypoint locally, use the repository's built-in one-shot run path:

1. Copy [`.env.example`](.env.example) to `.env`
2. Fill in your own account and model configuration
3. Run `uv sync --group dev`
4. Run `ENABLE_APSCHEDULER=false uv run app/deploy.py`

`.env`, `.venv`, and `app/volumes/` are already ignored by `.gitignore`, so they will not be committed to GitHub.

> [!TIP]
> If your password or API key contains `$`, `\`, `#`, or `` ` ``, wrap the value in single quotes (e.g. `EPIC_PASSWORD='abc$def'`) so that `python-dotenv` does not treat `$xxx` as variable interpolation and silently drop characters. GitHub Actions Secrets are not affected.

---

## FAQ

### 1. Login randomly fails

**Cause**: GitHub Actions environments use shared cloud IPs, which easily trigger Epic's strict risk control, causing fluctuations in captcha success rates. This is an expected behavioral pattern.

### 2. Logs mention `privacy-policy correction` or the run gets stuck on a privacy-policy page

This is usually not a model-provider issue. It is an Epic account state issue. Some accounts are redirected after login to a page like `/id/login/correction/privacy-policy`, which requires a one-time privacy-policy confirmation.

The fix is simple: sign in to Epic once in a normal browser, complete that confirmation page manually, and then rerun the workflow.

### 3. Logs show `two_factor_authentication.required` or the page goes to `/id/login/mfa`

This means Epic two-factor authentication is still enabled on the account. The current project does not support Epic email / SMS / authenticator-based 2FA, so you need to disable it in the Epic account settings before rerunning the workflow.

If you see signals like these, treat them as “Epic 2FA is still enabled”:

- `errors.com.epicgames.common.two_factor_authentication.required`
- `Two-Factor authentication required to process request`
- A redirect to `/id/login/mfa`

How to fix it:

1. Sign in to the Epic account in a normal browser
2. Open the account security settings page
3. Click `Remove` for every enabled verification method
4. Make sure email, SMS, authenticator, and any other Epic 2FA methods are all disabled
5. Rerun the workflow

Reference page:

![Epic 2FA remove methods](docs/images/faq/epic-2fa-remove-methods.png)

### 4. The page shows `One more step`

This is not automatically a bug. It is Epic's extra human-verification step during checkout.

**Description**: This is an additional security verification step during checkout. The workflow already contains automation logic for this stage, so seeing the prompt below does not automatically mean the script is broken.

![Checkout Security Check](docs/images/faq/checkout-security-check.png)

### 5. The page shows `Device not supported`

This usually happens when the product officially supports Windows while GitHub Actions is running on Linux.

By itself, this does not always mean the claim failed. The current automation will try to click `Continue` on that dialog and keep going.

### 6. Why can the workflow report success while the game is not in the library?

Historically, the common root causes were:

| Cause | Description |
| --- | --- |
| Product-page state recognition was inaccurate | The page copy and the real state did not match |
| `Place Order` was clicked but checkout was still incomplete | The checkout page was still blocked by a security check |
| Another popup interrupted the flow | For example `Device not supported` or an extra confirmation |
| Older logic misclassified page text | Some non-ownership text was previously misread as "already owned" |

---

## Docker Deployment

If you do not want to use GitHub Actions, you can also run the project on your own server, NAS, or local Docker environment.

### 1. Clone the repository

```bash
git clone https://github.com/Ronchy2000/epic-freebies-helper.git
cd epic-freebies-helper
```

### 2. Edit the configuration

The main entry is [`docker/docker-compose.yaml`](docker/docker-compose.yaml).

GLM example:

```yaml
environment:
  - LLM_PROVIDER=glm
  - GLM_API_KEY=your_glm_key
  - GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
  - GLM_MODEL=glm-4.6v
```

Official Gemini API example:

```yaml
environment:
  - LLM_PROVIDER=gemini
  - GEMINI_API_KEY=your_gemini_key
  - GEMINI_BASE_URL=
  - GEMINI_MODEL=gemini-2.5-pro
```

AiHubMix example:

```yaml
environment:
  - LLM_PROVIDER=gemini
  - GEMINI_API_KEY=your_key
  - GEMINI_BASE_URL=https://aihubmix.com
  - GEMINI_MODEL=gemini-2.5-pro
```

### 3. Start the stack

```bash
docker compose up -d --build
```

---

## Additional Documentation

If you want the project structure, adapter details, and developer-oriented troubleshooting notes, continue with:

- [Advanced Guide](docs/advanced.en.md)
- [GitHub Actions Guide](.github/workflows/README.en.md)
- [Development Log (2026-04-22)](docs/development-log-2026-04-22.en.md)
- [Maintenance Log](docs/maintenance-log.md)

---

## Project Origins and References

This project is based on `QIN2DIM/epic-awesome-gamer` and also references `10000ge10000/epic-kiosk`:

| Project | Description |
| --- | --- |
| [QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer) | Original project and source of the core automation ideas |
| [10000ge10000/epic-kiosk](https://github.com/10000ge10000/epic-kiosk) | Important reference for GitHub Actions packaging and documentation layout |
| [LINUX DO](https://linux.do/t/topic/2036835/4) | Community discussion, feedback, and project promotion support |

Thanks to the original authors, maintainers, and the community work that made this project possible.

---

## Disclaimer

- This project is for learning and research around automation flows.
- Automated actions may violate the target platform's terms of service. Evaluate the risk yourself.
- You are responsible for any consequences caused by using this project.

---

## Star History

<a href="https://www.star-history.com/?type=date&repos=ronchy2000%2Fepic-freebies-helper">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://api.star-history.com/chart?repos=ronchy2000/epic-freebies-helper&type=date&theme=dark&legend=top-left"
    />
    <source
      media="(prefers-color-scheme: light)"
      srcset="https://api.star-history.com/chart?repos=ronchy2000/epic-freebies-helper&type=date&legend=top-left"
    />
    <img
      alt="Star History Chart"
      src="https://api.star-history.com/chart?repos=ronchy2000/epic-freebies-helper&type=date&legend=top-left"
    />
  </picture>
</a>

---

## Community Thanks

The continuous improvement of this project relies not only on code iterations, but heavily on every user who, upon encountering an error, chose not to give up, but patiently submitted a complete error report.

The resolution of many edge cases did not stem from unilateral developer testing, but was built upon the detailed logs, screenshots, and reproduction steps actively provided by the community. It is this authentic diagnostic data that enabled obscure and hidden issues to be accurately isolated and resolved.

We extend our most genuine gratitude to everyone who has submitted feedback. The time you invested and the real-world data you shared have steadily illuminated the blind spots in development, allowing this project to mature and genuinely benefit a wider audience.

<div align="center">
  <sub>Thank you to everyone who opened issues, uploaded artifacts, and shared real failure cases.</sub>
</div>

<p align="center">
  <a href="https://github.com/AaronL725"><img src="https://github.com/AaronL725.png?size=96" width="64" height="64" alt="@AaronL725" /></a>
  <a href="https://github.com/cita-777"><img src="https://github.com/cita-777.png?size=96" width="64" height="64" alt="@cita-777" /></a>
  <a href="https://github.com/1208nn"><img src="https://github.com/1208nn.png?size=96" width="64" height="64" alt="@1208nn" /></a>
  <a href="https://github.com/LGDhuanghe"><img src="https://github.com/LGDhuanghe.png?size=96" width="64" height="64" alt="@LGDhuanghe" /></a>
  <a href="https://github.com/AdjieC"><img src="https://github.com/AdjieC.png?size=96" width="64" height="64" alt="@AdjieC" /></a>
</p>

<!-- <p align="center">
  <sub>
    <a href="https://github.com/AaronL725"><b>AaronL725</b></a> ·
    <a href="https://github.com/cita-777"><b>cita-777</b></a> ·
    <a href="https://github.com/1208nn"><b>1208nn</b></a> ·
    <a href="https://github.com/LGDhuanghe"><b>LGDhuanghe</b></a> ·
    <a href="https://github.com/AdjieC"><b>AdjieC</b></a>
  </sub>
</p> -->

<!--
Avatar wall template:

<p align="center">
  <a href="https://github.com/<username-1>"><img src="https://github.com/<username-1>.png?size=96" width="64" height="64" alt="@<username-1>" /></a>
  <a href="https://github.com/<username-2>"><img src="https://github.com/<username-2>.png?size=96" width="64" height="64" alt="@<username-2>" /></a>
  <a href="https://github.com/<username-3>"><img src="https://github.com/<username-3>.png?size=96" width="64" height="64" alt="@<username-3>" /></a>
</p>

<p align="center">
  <sub>
    <a href="https://github.com/<username-1>"><b><username-1></b></a> ·
    <a href="https://github.com/<username-2>"><b><username-2></b></a> ·
    <a href="https://github.com/<username-3>"><b><username-3></b></a>
  </sub>
</p>
-->
