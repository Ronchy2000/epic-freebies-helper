<div align="center">
  <h1>Epic Weekly Freebies Helper</h1>
  <p>An Epic Games weekly-freebies claimer for GitHub Actions.</p>

  <p>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/actions/workflows/epic-gamer.yml"><img src="https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-freebies-helper/epic-gamer.yml?branch=master&style=flat-square" alt="Workflow Status" /></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/Ronchy2000/epic-freebies-helper?style=flat-square" alt="License" /></a>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/stargazers"><img src="https://img.shields.io/github/stars/Ronchy2000/epic-freebies-helper?style=flat-square" alt="Stars" /></a>
    <a href="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper"><img src="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper&left_text=views" alt="Views" /></a>
  </p>
</div>

[🇺🇸 English](README.en.md) | [🇨🇳 中文文档](README.md)

This project is aimed at regular users who want to auto-claim Epic Games weekly freebies. The default setup runs on GitHub Actions, so you do not need a server or a machine that stays online all the time. If you have a GitHub account, you can get started directly.

Completely free.  
With GitHub Actions, you can automate Epic weekly freebies without a server or a machine running 24/7.

The project is built on top of community open-source work and now includes domestic `GLM` multimodal support. In practice it can handle login, captcha solving, and the claim flow reliably. If Google AI Studio or the Gemini API is inconvenient for you, the GLM path is usually easier and can often be run at `0` cost.

**If you choose the `GLM` route, make sure the related Zhipu account has already passed real-name verification, or the API may remain unavailable.**

If you do not have a Zhipu account yet, you can register through this invite link: [BigModel.cn invite link](https://www.bigmodel.cn/invite?icode=A75tQCByIvrO4k6SLkU5BQZ3c5owLmCCcMQXWcJRS8E%3D).

Community discussion and feedback are welcome on [LINUX DO](https://linux.do/t/topic/2036835/4).

If the project worked for you, feel free to leave a message here too: [🎉 Success Stories / Successful runs](https://github.com/Ronchy2000/epic-freebies-helper/discussions/3).

---

## Feature Overview

| Feature | Description |
| --- | --- |
| Auto login | Signs in to your Epic account automatically |
| Weekly freebies discovery | Fetches and identifies currently claimable free titles |
| Auto claim | Opens product pages and completes the checkout flow |
| Captcha handling | Supports login captcha and checkout security checks |
| Scheduled execution | Can run directly on GitHub Actions |

---

## Why GLM Is Recommended

If this is your first time using a project like this, starting with GLM is usually the easiest path. The reasons are practical:

- Less configuration: in most cases you only need `GLM_API_KEY` and `GLM_MODEL`.
- Lower cost: the free quota of `glm-4.6v` is often enough for the weekly-claim use case.
- More stable for this project: `glm-4.6v-flash` can occasionally fail under load with "the current model is too busy", so `glm-4.6v` is the safer default.
- Better fit for users in China: you do not need to solve Google AI Studio registration or availability first.
- Capability already validated: login captcha, checkout verification, drag, click, and multi-select challenges have all been verified in real runs.

---

## Before You Start

- Your Epic account email and password.
- Epic account 2FA must be disabled (email, SMS, or authenticator app).
- A GLM account with `GLM_API_KEY` prepared for captcha solving.

---

## 🚀 Quick Start

In most cases, the first successful validation can be finished in about 10 minutes.

### 1. Fork the repository and enable Actions

> [!TIP]
> If you have already forked this repository before, go to your fork on GitHub first and click `Sync fork` -> `Update branch` so your copy is aligned with the latest upstream changes before you continue.

- Fork the repo to your own GitHub account. A private fork is recommended.
- Open `Actions` and enable the workflow named `Epic Awesome Gamer (Scheduled)`.

### 2. Configure Secrets

Go to `Settings` -> `Secrets and variables` -> `Actions`, then fill in these five values first:

**If you plan to use `GLM_API_KEY`, make sure the related Zhipu account has already passed real-name verification, or the API may remain unavailable.**

| Secret | Example value |
| --- | --- |
| `EPIC_EMAIL` | Your Epic email |
| `EPIC_PASSWORD` | Your Epic password |
| `LLM_PROVIDER` | glm |
| `GLM_API_KEY` | Your Zhipu API key |
| `GLM_MODEL` | glm-4.6v |

Configuration page example:
![GLM API setup](docs/images/tutorial/GLM-API.png)

![GitHub Actions Secrets example](docs/images/tutorial/step2-actions-secrets.png)

Optional notes:

- Leave `GLM_BASE_URL` empty to use the default value.
- `glm-4.6v` is the recommended `GLM_MODEL`; `glm-4.6v-flash` can fail during peak traffic.
- Leave `CHALLENGE_CLASSIFIER_MODEL`, `IMAGE_CLASSIFIER_MODEL`, `SPATIAL_POINT_REASONER_MODEL`, and `SPATIAL_PATH_REASONER_MODEL` empty if you want them to follow `GLM_MODEL`.
- If you want the Gemini route instead, set `LLM_PROVIDER=gemini` and configure `GEMINI_API_KEY`.

### 3. Run the workflow manually once

- Open the `Actions` page.
- Select `Epic Awesome Gamer (Scheduled)`.
- Click `Run workflow`.

> [!IMPORTANT]
> Do not cancel the workflow just because it is still retrying after about 5 minutes. Login captcha and checkout security checks can legitimately fail, retry, time out, and then continue again. Some runs still succeed only after 15 to 20 minutes, so as long as the workflow is still progressing, wait a bit longer.

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

Each GitHub Actions run uploads two artifacts automatically:

| Artifact | Content |
| --- | --- |
| `epic-runtime-<run_id>` | Runtime screenshots, debug text, and `purchase_debug` files |
| `epic-logs-<run_id>` | Runtime logs |

Download location:

1. Open the specific Actions run page.
2. Scroll to the bottom.
3. Find `Artifacts`.
4. Download the zip files.

What to inspect first:

| Package | What to inspect first |
| --- | --- |
| `epic-runtime-<run_id>.zip` | After extraction, check the screenshots and debug text inside `purchase_debug/` first |
| `epic-logs-<run_id>.zip` | After extraction, open the log files directly |

These files are generated and uploaded after each GitHub Actions run. They are not fixed directories pre-shipped in the repository root.

---

## FAQ

### 1. Login sometimes fails and sometimes succeeds

That is normal. GitHub Actions uses shared cloud IPs and Epic is sensitive to risk control. Typical symptoms include a captcha that passes once and fails the next time, occasional `captcha_invalid`, or the same account succeeding again after some delay.

Also, do not hit `Cancel workflow` just because the run has been active for a few minutes. Some successful cases only finish after heavy retry loops and can take 10 to 20 minutes.

### 2. Logs mention `privacy-policy correction` or the run gets stuck on a privacy-policy page

This is usually not a model-provider issue. It is an Epic account state issue. Some accounts are redirected after login to a page like `/id/login/correction/privacy-policy`, which requires a one-time privacy-policy confirmation.

The fix is simple: sign in to Epic once in a normal browser, complete that confirmation page manually, and then rerun the workflow.

### 3. The page shows `One more step`

This is not automatically a bug. It is Epic's extra human-verification step during checkout.

The project can already handle this secondary verification. Seeing the popup below does not mean the automation is broken:

![Checkout Security Check](docs/images/faq/checkout-security-check.png)

### 4. The page shows `Device not supported`

This usually happens when the product officially supports Windows while GitHub Actions is running on Linux.

### 5. Why can the workflow report success while the game is not in the library?

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

Gemini / AiHubMix example:

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

---

## Acknowledgements

This project is based on `QIN2DIM/epic-awesome-gamer` and also references `10000ge10000/epic-kiosk`:

| Project | Description |
| --- | --- |
| [QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer) | Original project and source of the core automation ideas |
| [10000ge10000/epic-kiosk](https://github.com/10000ge10000/epic-kiosk) | Important reference for GitHub Actions packaging and documentation layout |
| [LINUX DO](https://linux.do/t/topic/2036835/4) | Community discussion, feedback, and project promotion support |

Thanks to the original authors and maintainers.

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
