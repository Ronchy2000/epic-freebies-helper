# Advanced Developer Guide

This document is for readers who want to keep changing the project, open PRs, or build on top of it.

Language versions:

- [简体中文](advanced.md)
- English (this page)

If you only want to configure and use the project, start with:

- [README](../README.en.md)
- [Development Log (2026-04-22)](development-log-2026-04-22.en.md)
- [GitHub Actions Guide](../.github/workflows/README.en.md)

---

## Project Structure

| File | Purpose |
| --- | --- |
| [`app/deploy.py`](../app/deploy.py) | Main runtime entry, responsible for browser startup, login, claiming, and scheduling |
| [`app/services/epic_authorization_service.py`](../app/services/epic_authorization_service.py) | Login, login-result listeners, and post-login validation |
| [`app/services/epic_games_service.py`](../app/services/epic_games_service.py) | Weekly freebie discovery, product-page entry, add-to-cart, checkout, and checkout verification handling |
| [`app/settings.py`](../app/settings.py) | Environment variables, model routing, and defaults |
| [`app/extensions/llm_adapter.py`](../app/extensions/llm_adapter.py) | Gemini / AiHubMix / GLM compatibility adapter |
| [`.github/workflows/epic-gamer.yml`](../.github/workflows/epic-gamer.yml) | GitHub Actions workflow entry |

---

## Local Development

```bash
uv sync
uv run black . -C -l 100
uv run ruff check --fix
```

Notes:

1. This repository currently does not recommend adding extra test runs.
2. When changing the captcha chain, preserve logs and screenshots first.
3. When changing the checkout flow, prioritize "do not report success unless success is actually confirmed."

---

## Real Pitfalls Encountered During This Adaptation

These are not hypothetical issues. They all happened during real development and were explicitly fixed.

### 1. GLM is not a simple Base URL replacement

`hcaptcha-challenger` internally depends on a `google-genai`-style multimodal interface.

That means you cannot support GLM by only changing `GEMINI_BASE_URL` to Zhipu's endpoint.

The actual work is to preserve the upper-layer call pattern while converting images, messages, and structured outputs into a format GLM accepts in the adapter layer.

---

### 2. Challenge types really do change across phases

The challenge type during login is not guaranteed to match the challenge type during checkout.

| Phase | Challenge type |
| --- | --- |
| Login | `image_drag_single` |
| Checkout | `image_label_multi_select` |

If the adapter only handles drag challenges, the flow can still die on the second verification step at checkout.

---

### 3. GLM output format is not stable

The following response forms were seen in real runs:

| Response form | Meaning |
| --- | --- |
| `Source Position: (...)` | Coordinate text |
| `{"source": [...], "target": [...]}` | Structured drag coordinates |
| `{"answer":"..."}` | A string wrapped inside `answer` |
| `image_label_multi_select` | Only the challenge type name |
| Semi-structured JSON | Incomplete or malformed responses |

That is why [`llm_adapter.py`](../app/extensions/llm_adapter.py) now contains a lot of fallback logic that unwraps content and remaps it into the schema expected by the challenger.

---

### 3.1 Which captcha types are actually considered right now

At the adapter layer, the project currently has explicit handling for these challenge types:

| Type | Current status | Common phase |
| --- | --- | --- |
| `image_drag_single` | Supported, but still occasionally unstable | Login |
| `image_drag_multiple` / `image_drag_multi` | Supported, but only moderately stable | Login / checkout |
| `image_label_binary` | Supported | Login |
| `image_label_multi_select` | Supported, but most sensitive to model-output shape drift | Checkout |
| `image_label_area_select` | Supported, but sensitive to box-coordinate response formats | Checkout |
| `image_label_multiple_choice` | Wired in, but real-world samples are still limited | Login / checkout |

There is also one challenge prompt that is explicitly treated as out of scope for reliable support:

| Special prompt | Current strategy |
| --- | --- |
| `Please drag the crossing to complete the lines` | Explicitly ignored, not treated as a stable supported case |

So the real state of the project is not "all captcha types are solved reliably." The actual state is "common types are handled as far as practical, while special prompts and heavily drifting response shapes are still repaired case by case from artifacts."

### 3.2 Why some captcha challenges still fail

Based on the cases already fixed, failures usually come from a combination of these factors rather than one single bug:

| Failure source | Typical manifestation |
| --- | --- |
| Unstable challenge routing | The router returns only a type name, or uses an alias instead of the canonical type |
| Model-output shape drift | Only `answer` is returned, only a raw string is returned, required fields are missing, or coordinate formats change |
| Checkout verification is harder than login | Passing login does not mean the second verification during checkout will also pass |
| Page state changes too quickly | The challenge frame disappears, buttons change briefly, or Playwright misses the short observation window |
| Epic / hCaptcha risk-control changes | The same account and same challenge type can behave differently at different times |

That is why the real engineering goal here is not a literal 100% captcha pass rate. The more realistic goal is:

1. Cover the common challenge types as well as possible.
2. Fix response-shape drift in [`llm_adapter.py`](../app/extensions/llm_adapter.py) first.
3. Fix page-state recognition in [`epic_games_service.py`](../app/services/epic_games_service.py) when the page flow changes.
4. Leave enough artifacts on every failure to support the next repair.

---

### 4. Epic checkout can show more than hCaptcha

The following states were all confirmed during checkout:

| Scenario | Seen in real runs |
| --- | --- |
| `Device not supported` | Yes |
| `One more step` | Yes |
| An extra checkout iframe | Yes |
| The page still sitting on `Place Order` | Yes |

Because of that, [`epic_games_service.py`](../app/services/epic_games_service.py) now does all of the following:

1. Detects and tries to dismiss the device-not-supported dialog.
2. Detects checkout security checks explicitly.
3. Loops after `Place Order` to observe the actual result instead of assuming success.
4. Refuses to report success until success is confirmed.

---

### 5. Ownership detection cannot scan the whole page loosely

At one point, copyright text like `owned by ...` was incorrectly interpreted as "already owned."

The fix was:

1. Look at the purchase button and checkout state first.
2. Only accept high-confidence success markers.

---

### 6. Artifacts are critical

Checkout problems were not diagnosed from console output alone. These files were essential:

| File | Why it matters |
| --- | --- |
| Log files extracted from `epic-logs-<run_id>` | Shows the full execution chain |
| `purchase_debug/*.png` extracted from `epic-runtime-<run_id>` | If present, shows the actual product-page or checkout rendering |
| `purchase_debug/*.txt` extracted from `epic-runtime-<run_id>` | If present, shows product-page text and iframe text |
| Screenshots extracted from `epic-screenshots-<run_id>` | If present, shows login, risk-control, or auth page state |

`epic-runtime` and `epic-screenshots` do not always appear together. The workflow attempts to upload them, but GitHub only shows artifacts that actually contain files. A run that never reaches product pages may have no `runtime` artifact; a run that never saves login/risk-control screenshots may have no `screenshots` artifact.

---

## Robustness Plan After the 2026-04-24 User Reports

This round came from multiple real user artifact bundles, not from a single isolated failure. When analyzing these reports, do not only read the final traceback. Check all of the following:

1. The last business action in `runtime.log`.
2. The Playwright / hCaptcha exception type in `error.log`.
3. Whether `purchase_debug/*.png` already shows a button, iframe, dialog, or success confirmation.
4. Main-page text and frame text in `purchase_debug/*.txt`.

### Failure Classes

| Symptom | Log signature | Technical read | Direction |
| --- | --- | --- | --- |
| Repeated login failure | `Timed out waiting for Epic login outcome`, `btoa is read-only`, `Challenge execution timed out` | hCaptcha is still visible, or the page is polluted by a previous solve attempt | Retry login challenge in smaller phases; rebuild the page and clear cookies after a failed login attempt |
| Product page navigation failure | `Page.goto: Timeout 30000ms exceeded` | The usable page body may already be present, while `load` is blocked by images, scripts, or third-party resources | Use `domcontentloaded`; continue when a partially loaded page is usable |
| Visible `Get` button click hangs | `Locator.click: Timeout 10000ms exceeded`, while the screenshot shows the button | Playwright is waiting for the click action to finish, but the page does not return in the expected way | Layer standard click, dispatch, DOM click, coordinate click, and force click |
| Checkout progressed but is unconfirmed | The page remains on `Place Order` or a security check | A successful click is not the same as a successful claim | Continue observing order confirmation, button state, checkout iframe, and order history |
| Config contains trailing whitespace | Model names in logs look like `glm-4.6v\n` | GitHub Secrets or copied values can contain whitespace | Strip string settings centrally |

### Current Design Principles

1. **Do not treat a single Playwright timeout as business failure**  
   In browser automation, `click()` can time out because an action wait condition was not satisfied. If the page already shows a checkout iframe, security check, success text, or button-state change, the flow should continue observing the next stage instead of throwing immediately.

2. **Retry by stage, not by whole workflow**  
   Login, product-page entry, purchase-button click, checkout submission, hCaptcha solving, and final confirmation are separate failure points. When one stage fails, reset only the state needed for that stage.

3. **Success must be high-confidence**  
   A returned click, redirect, or loose page-text match is not enough. Success signals should be prioritized roughly as follows:

   | Priority | Signal |
   | --- | --- |
   | High | `Thanks for your order` + `Order number` |
   | High | Matching namespace / offerId appears in order history |
   | Medium | Button changes to `In Library` / `Owned` / `View in Library` |
   | Low | Loose body-text markers |

4. **Failures must leave artifacts**  
   Navigation failure, missing button, ineffective click, and unconfirmed checkout should save screenshots and text. Future fixes should be based on artifact classes instead of guessing more selectors.

### Implementation Points

| File | Plan |
| --- | --- |
| [`app/services/epic_authorization_service.py`](../app/services/epic_authorization_service.py) | Detect visible hCaptcha during login; if login-outcome wait times out while captcha remains, retry solving; rebuild the page and clear cookies after a failed login attempt |
| [`app/services/epic_games_service.py`](../app/services/epic_games_service.py) | Make product-page navigation recoverable; use layered purchase-button click strategies; decide progress by page state after clicking |
| [`app/settings.py`](../app/settings.py) | Strip string settings such as model names, base URLs, provider, and account email |

### Future Triage Workflow

For similar reports, use this order:

1. Classify the failure as login, product page, button click, checkout, security check, or final confirmation.
2. Inspect `purchase_debug` screenshots to understand the real page state instead of trusting the traceback alone.
3. If the page already advanced to the next stage, improve state detection and confirmation logic before adding longer timeouts.
4. If Epic introduces new copy or a new dialog, add high-precision text handling first, then add a screenshot capture point.
5. If model output shape changes, normalize it in [`llm_adapter.py`](../app/extensions/llm_adapter.py) instead of spreading provider-specific behavior into the business flow.

This project cannot honestly guarantee a literal 100% success rate because Epic risk controls, shared cloud IPs, captcha types, and third-party model responses are outside the codebase's control. The engineering target is recoverability, observability, no false success reports, and enough evidence on every failure to support the next fix.

---

## Maintenance Priorities

If you continue maintaining this project, keep watching these classes of change first:

1. Whether Epic changes the captcha type on the login page.
2. Whether product-page button labels change.
3. Whether checkout iframe behavior or `Place Order` behavior changes.
4. Whether GLM / Gemini response formats change again.
5. Whether the GitHub Actions runtime environment changes.
