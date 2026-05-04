# Development Log - 2026-04-22

This document is a condensed development log extracted from the original Codex session. The goal is to compress a full day of debugging, fixes, and documentation work into a readable summary.

Language versions:

- [简体中文](development-log-2026-04-22.md)
- English (this page)

The raw record is still kept in the repository:

- [`codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl`](../codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl)

Notes:

- The original session used the old working directory `/Users/ronchy2000/Documents/Developer/Workshop/epic-freebies-helper`
- The current repository directory has been renamed to `epic-freebies-helper`
- The content below is a distilled development summary, not a line-by-line chat transcript

---

## Background

This development round was concentrated on April 22, 2026. The goal was not a one-off patch, but to move the project from "a usable repo that depends on Gemini and third-party APIs" toward something that better matches the current repository positioning:

1. Add `GLM` compatibility while keeping the configuration style close to the existing provider setup.
2. Optimize for real `GitHub Actions` runs, not just local reasoning.
3. Keep fixing the most unstable parts of the Epic claim chain based on real logs.
4. Rewrite the docs so regular users can get started first and developers can go deeper afterward.

---

## Main Conclusions

Several conclusions became very clear by the end of the work:

- Supporting `GLM` is not just changing `base_url`; it must stay compatible with the upper-layer calling style expected by `hcaptcha-challenger`.
- The hardest part is not sending requests. It is converting GLM's unstable outputs under different captcha types into the structure expected by the challenger.
- In the Epic claim chain, the login captcha, product-page `Get`, `Device not supported`, checkout secondary verification, and the result after `Place Order` are all separate failure points.
- Console logs alone are not enough. GitHub Actions artifacts are critical for diagnosing checkout issues.
- Documentation has to be split. README and developer docs cannot stay mixed together, or both regular users and maintainers get blocked by a wall of text.

---

## Timeline

### 1. GLM support landed first

The first task was extending the provider compatibility layer so the repository could use `GLM` for captcha solving while preserving the existing configuration style.

Related commit:

- `b6e5ded` `feat: add glm support for captcha solver`

That was only the starting point. Most of the later issues came from the fact that the integration could "run", but the request body, model naming, response format, and real page flow were still unstable.

### 2. Defaults and model selection were fixed next

The next issue was GitHub Actions environment-variable override behavior. Unconfigured secrets can arrive as empty strings, which prevented `GLM_BASE_URL` and `GLM_MODEL` from falling back correctly.

Another issue showed up right after that:

- `GLM` was enabled, but the per-challenge model defaults could still fall back to `GEMINI_MODEL`
- That caused "model not found" failures against the Zhipu endpoint

Related commits:

- `fcbd5b0` fixed empty-string overrides against defaults
- `6cd05ed` fixed default-model inheritance when `LLM_PROVIDER=glm`

### 3. GLM request and response compatibility was fixed after configuration

Once the config layer was corrected, the problem shifted to API compatibility itself:

- Image fields did not initially match the GLM OpenAI-compatible request format
- GLM responses were not always stable JSON
- Different challenge types could return coordinate text, `source/target`, strings wrapped in `answer`, or even just the challenge type name

This was the densest part of the session. The goal was to normalize GLM's unstable outputs into the challenger schema as consistently as possible.

Related commits:

- `ed21177` fixed GLM image request formatting and improved error logging
- `5f4aca1` added compatibility for drag / click coordinate text
- `8ece3bd` mapped `source/target` or `from/to` into `paths`
- `94b1c64` enforced structured responses and added raw-text fallback logging
- `0b1e5ab` unpacked the `answer` field and handled strings, arrays, objects, and bare coordinates
- `fb801ef` handled cases where only the challenge type or a selection schema was returned

### 4. Debugging focus then moved to the Epic page flow

Once login and basic solving became usable, the main bottleneck moved from "the model call failed" to "how the Epic page actually behaves during a claim."

Several independent problems were exposed here:

- Product-page primary button context was not logged clearly enough, which made claimable and non-claimable states easy to confuse
- `Get` could lead to `Device not supported`
- Checkout could trigger `One more step`
- Security checks could be hidden in an iframe rather than only in the main page
- Even after solving a challenge, `Place Order` did not guarantee the order was truly complete

Related commits:

- `4124639` improved product-page button context logging, screenshots, and click fallback
- `36332bb` uploaded artifacts and saved checkout failure screenshots and text
- `38c3e5a` handled `Device not supported` automatically
- `c8291a1` tightened claim-result confirmation to avoid reporting success before success was real, and also cleaned up Node 24 warnings
- `87b32a5` fixed false "owned" detection caused by matching `owned by ...`
- `3c8a9b1` explicitly detected the `One more step` checkout security check and entered a solve loop
- `ac3684c` extended security-check detection across both the main page and iframes
- `ea9ae2a` refactored the post-`Place Order` flow into explicit submission cycles and re-observation

### 5. Documentation and repository positioning were tightened at the end

After the feature and debugging chain became more stable, the later work focused on documentation and naming cleanup.

Two major things happened here:

1. README was rewritten into a homepage better suited for regular users.
2. Developer-focused material was moved into `docs/advanced.md` instead of staying mixed into the homepage.

The repository name and project naming were also tightened around the final direction: `Epic 周免助手` plus `epic-freebies-helper`.

Related commits:

- `95940e1` first user-first README restructure
- `3379fa7` tightened README structure
- `f4377c4` split out the dedicated advanced developer guide
- `93563c6` improved homepage presentation, naming, and acknowledgements
- `4d27845` tightened the README first-screen positioning
- `1855c96` finalized `Epic 周免助手` / `epic-freebies-helper`

---

## What This Round Actually Solved

If you look only at the resulting state, this session pushed the following areas into something maintainable:

### GLM integration

- Added `GLM` as an optional provider
- Handled default base URL, model configuration, and GitHub Actions secret fallback
- Made per-challenge model defaults follow `GLM_MODEL` when `LLM_PROVIDER=glm`

### Captcha-solving compatibility

- Added compatibility for drag and selection challenges
- Handled multiple unstable GLM output forms
- Added more structured fallbacks and raw-response logging

### Epic claim flow

- Added product-page button context logging
- Added failure screenshots and page text capture
- Handled `Device not supported`
- Handled checkout secondary verification
- Improved the submission and observation rhythm after `Place Order`
- Fixed the class of bugs where success could be reported before success was actually confirmed

### GitHub Actions runtime experience

- Added artifact upload for runtime and logs
- Cleaned up the Node 20 deprecation issue by moving to the Node 24 path

### Documentation structure

- README now targets regular users
- `docs/advanced.md` now targets developers
- Naming, recommended models, and deployment language are now more consistent

---

## Process Lessons

This session is a good example of how future maintenance on this repository should work:

1. Do not stare only at the model interface. Separate "model output format" from "Epic page state machine."
2. Once the problem is in checkout, inspect artifacts first instead of guessing from console logs.
3. For states like "already owned" or "claim succeeded", always use high-confidence checks. Loose full-page scanning is not good enough.
4. For GitHub Actions, assume platform issues by default: empty-string env values, Linux runner limitations, and Node version warnings all matter.
5. Do not keep onboarding docs and debugging records mixed in the homepage. The homepage is for getting started; advanced docs are for maintenance.

---

## Key Commit List

| Commit | Purpose |
| --- | --- |
| `b6e5ded` | Initial GLM compatibility |
| `fcbd5b0` | Fixed defaults being overridden by empty secrets |
| `ed21177` | Fixed image request formatting and improved GLM error logging |
| `6cd05ed` | Fixed per-challenge defaults under the `glm` provider |
| `5f4aca1` | Added compatibility for text-coordinate outputs |
| `8ece3bd` | Converted `source/target` into `paths` |
| `4124639` | Improved product-page button logs, screenshots, and click fallback |
| `36332bb` | Saved debug files and uploaded artifacts |
| `38c3e5a` | Auto-handled `Device not supported` |
| `c8291a1` | Tightened claim-result confirmation to avoid false success |
| `87b32a5` | Fixed false ownership matches from `owned by ...` |
| `3c8a9b1` | Explicitly handled checkout `One more step` |
| `ac3684c` | Extended security-check detection into iframes |
| `ea9ae2a` | Refactored post-`Place Order` submission cycles |
| `94b1c64` | Added structured-response enforcement and parse fallback logs |
| `0b1e5ab` | Unpacked `answer` and handled more drag-return shapes |
| `fb801ef` | Handled type-name-only and selection-schema responses |
| `95940e1` | First README restructuring |
| `f4377c4` | Split out `docs/advanced.md` |
| `1855c96` | Finalized project naming and README positioning |

---

## Relationship Between This Summary and the Raw Record

If you want a fast understanding of this development round, this document is enough.

If you need finer detail, for example:

- to verify what exactly triggered a specific branch in the logs
- to re-read the original wording before or after a fix
- to extract a more complete change log from the full session

then go back to the raw file:

- [`codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl`](../codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl)
