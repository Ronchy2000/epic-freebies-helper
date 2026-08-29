# GitHub Actions 使用说明

语言版本：

- 简体中文（当前页）
- [English](README.en.md)

当前仓库已经内置 [`.github/workflows/epic-gamer.yml`](epic-gamer.yml)，推荐直接使用它来定时执行。

默认定时已经改成每周一次：`北京时间周四 23:20`（GitHub cron 使用 `UTC 15:20`）。这个时间点放在 Epic 周免刷新之后，更适合作为默认设置。

## 工作流做了什么

这个工作流会在 GitHub Hosted Runner 上完成以下步骤：

1. 检出仓库代码。
2. 安装 `uv` 和 Python 3.12。
3. 安装系统依赖。
4. 执行 `uv sync` 安装 Python 依赖。
5. 下载 Camoufox 浏览器资源。
6. 安装 Playwright Firefox 作为浏览器回退方案。
7. 在 `xvfb` 环境中运行 `uv run app/deploy.py`。

它默认由 GitHub 的 `schedule` 和 `workflow_dispatch` 触发，仓库内的 APScheduler 会被关闭，避免重复调度。

## 默认运行时间

- 默认 schedule：每周四一次
- GitHub cron：`20 15 * * 4`
- 对应时间：`UTC 周四 15:20` / `北京时间周四 23:20`

如果你想改成自己的时间，直接编辑 [`.github/workflows/epic-gamer.yml`](epic-gamer.yml) 里的 `schedule` 即可。最方便的方式是在 GitHub 网页里打开这个文件，点右上角铅笔按钮，修改 `cron` 后提交。

## Secrets 和 Variables 配置

账号、密码和 API Key 必须放在 `Secrets`。`LLM_PROVIDER` 和所有 `*_MODEL` 模型名建议放在 `Variables`，工作流会优先读取 Variables，并兼容已有的同名 Secrets。启动日志会打印包括 `SPATIAL_PATH_REASONER_MODEL` 在内的实际模型路由；仍保存在 Secrets 中的值会被 GitHub 自动遮罩为 `***`。

必须配置：

| Secret | 说明 |
| --- | --- |
| `EPIC_EMAIL` | Epic 邮箱，需关闭邮箱 / 短信 2FA |
| `EPIC_PASSWORD` | Epic 密码，需关闭邮箱 / 短信 2FA |

如果账号启用了验证器 App 2FA，可额外配置：

| Secret | 说明 |
| --- | --- |
| `EPIC_TOTP_SECRET` | 验证器二维码对应的 Base32 密钥；不要填写当前显示的 6 位动态验证码 |

未配置时保持现有登录行为。邮箱验证码、短信验证码和 Passkey 暂不支持。

如需接收 Telegram 领取结果通知，可额外配置：

| Secret | 说明 |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram 聊天 ID |

两个 Secret 需要同时存在才会发送通知。发送失败不会影响领取任务；未配置时保持现有行为。

如果共享云 IP 导致 hCaptcha 风控加重，可选添加 `BROWSER_PROXY` Secret，格式为 `http://用户名:密码@主机:端口`、`https://...`、`socks4://...` 或 `socks5://...`。未配置时网络路径保持不变。

如果你使用 Gemini 官方接口：

`LLM_PROVIDER=gemini` 时，必须填写 `GEMINI_API_KEY`，无需新建并填写 `GLM_API_KEY`。

| Secret | 说明 |
| --- | --- |
| `LLM_PROVIDER` | 建议设为 `gemini` |
| `GEMINI_API_KEY` | Gemini API Key |
| `GEMINI_BASE_URL` | 留空，走官方默认地址 |
| `GEMINI_MODEL` | 可选，默认 `gemini-2.5-pro` |

如果你使用 AiHubMix 这类 Gemini 兼容中转接口：

`LLM_PROVIDER=gemini` 时，必须填写 `GEMINI_API_KEY`，无需新建并填写 `GLM_API_KEY`。

| Secret | 说明 |
| --- | --- |
| `LLM_PROVIDER` | 建议设为 `gemini` |
| `GEMINI_API_KEY` | AiHubMix Key |
| `GEMINI_BASE_URL` | 例如 `https://aihubmix.com` |
| `GEMINI_MODEL` | 可选，默认 `gemini-2.5-pro` |

如果你使用 GLM：

`LLM_PROVIDER=glm` 时，必须填写 `GLM_API_KEY`，无需新建并填写 `GEMINI_API_KEY`。

| Secret | 说明 |
| --- | --- |
| `LLM_PROVIDER` | 建议设为 `glm` |
| `GLM_API_KEY` | 智谱 API Key |
| `GLM_BASE_URL` | 可选，默认 `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | 可选，推荐 `glm-4.6v` |

`GLM` 路线只填写 `GLM_API_KEY`；`Gemini / AiHubMix` 路线只填写 `GEMINI_API_KEY`。另一组 key 无需新建并填写。如果 provider 和 key 对不上，工作流会直接报配置错误。
不要把 `LLM_PROVIDER` 和 API key 填错位：例如 `LLM_PROVIDER=glm` 却只填了 `GEMINI_API_KEY`，或者 `LLM_PROVIDER=gemini` 却只填了 `GLM_API_KEY`。这种情况下工作流会直接报配置错误。

程序会优先读取这些模型覆盖项，如果未设置，则自动回落到 `GLM_MODEL` 或 `GEMINI_MODEL`：

- `CHALLENGE_CLASSIFIER_MODEL`
- `IMAGE_CLASSIFIER_MODEL`
- `SPATIAL_POINT_REASONER_MODEL`
- `SPATIAL_PATH_REASONER_MODEL`

这些非敏感配置建议作为 GitHub Variables 配置。为兼容已有 Fork，工作流仍会回退读取同名 Secrets。

## 本地单次调试

如果你要在本地复现 GitHub Actions 的执行入口，推荐直接沿用同一个启动路径：

1. 复制 [`.env.example`](../../.env.example) 为 `.env`
2. 填入你自己的账号和模型配置
3. 执行 `uv sync --group dev`
4. 执行 `ENABLE_APSCHEDULER=false uv run app/deploy.py`

`.env`、`.venv`、`app/volumes/` 都已经在 `.gitignore` 中忽略，不会被误提交。

## 为什么 GLM 不能直接替换 Gemini 地址

因为仓库底层依赖 `hcaptcha-challenger`，而它内部用的是 `google-genai` 的多模态上传和 `generate_content` 接口。

这次仓库已经新增适配层：

- Gemini 官方接口和 AiHubMix 兼容接口继续使用原有兼容补丁。
- GLM 会自动转成智谱 OpenAI-compatible `chat/completions` 请求。

这也是为什么 GLM 这里推荐 `glm-4.6v` 这类视觉模型，而不是纯文本的编码模型。
如果你用 `glm-4.6v-flash` 遇到“该模型当前访问量过大，请您稍后重试”，直接改成 `GLM_MODEL=glm-4.6v` 通常更稳。

## 建议的首次启动流程

Fork 之后先打开自己仓库的 `Actions` 页面，进入 `Epic Awesome Gamer (Scheduled)` 并点一次 `Enable workflow`，否则 GitHub 不会让这个 Fork 的定时 `schedule` 自动生效。

1. Fork 仓库。
2. 配置 Secrets。
3. 到 `Actions` 页面手动运行一次。
4. 查看日志确认是否完成登录和领取。

> [!IMPORTANT]
> 不要看到工作流运行了 5 分钟左右还在重试就手动取消。登录验证码和 checkout 二次校验可能会连续失败、反复重试，甚至中途出现 timeout；这属于正常现象，有些最终成功的案例会持续 15 到 20 分钟。

如果某次 runner 上 `Camoufox` 下载失败或启动失败，新的工作流会继续依赖已安装的 Playwright Firefox 回退运行，而不是直接在浏览器准备阶段终止。

## Fork 后如何和主仓库同步

为了避免你 Fork 的仓库代码落后，建议定期和上游主仓库（`Ronchy2000/epic-freebies-helper`）同步，尤其在遇到异常报错时先同步再重试。网页端直接在 Fork 仓库默认分支点击 `Sync fork` -> `Update branch` 即可；如果提示冲突，就点 `Compare changes` 按引导发起并合并 Pull Request，之后再回到 Actions 重新运行一次工作流。

## 常见问题

### 1. Action 运行了但登录卡住

GitHub 的共享出口 IP 可能被 Epic 风控。通常换个时间重新执行就能恢复。

如果日志里一直在做 captcha 重试，不要太早点 `Cancel workflow`。下面这种“最后是取消结束”的例子，并不代表脚本在第 5 分钟就已经真正失败了：

![不要过早取消 Actions 运行](../../docs/images/faq/action-cancel-too-early.svg)

新的工作流会尝试上传 `epic-screenshots-<run_id>`。这个 artifact 只有在登录、风控或授权阶段实际保存过截图时才会出现在页面底部；如果日志里只看到 `Timeout waiting for #email`、`Just a moment...`、`One more step` 这类提示，并且 Artifacts 区域里有截图包，优先看截图 artifact。

### 2. 日志里出现 `privacy-policy correction`

这通常不是 `GLM`、`Gemini` 或 `AiHubMix` 的接口问题，而是 Epic 账号登录后被重定向到了 `/id/login/correction/privacy-policy` 这类确认页面。

处理方式：先在你自己的浏览器里手动登录 Epic，一次性完成隐私政策确认页，然后再重新运行 workflow。

### 3. GLM 报 429/400/401

优先检查：

- 如果日志里出现 `message=该模型当前访问量过大，请您稍后再试` 或 HTTP `429`，优先把 `GLM_MODEL` 改为 `glm-4.6v`（不要用 `glm-4.6v-flash`）。
- `LLM_PROVIDER=glm`
- `GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`
- `GLM_MODEL=glm-4.6v`
- API Key 是否仍然有效

示例日志（429 限流）：

![GLM 429 rate limit log](../../docs/images/faq/glm-429-rate-limit.png)

### 4. hCaptcha 日志反复出现 GLM 超时或 HSW 解码失败

先同步主仓库的最新 `master`。当前版本会把 GLM 单次请求超时明确记录为 `GLM request timed out after ...`，并限制单轮网络尝试次数，避免模型重试耗尽整个验证码时限；浏览器也会自动对 `hsw.js` 使用无压缩传输，规避 `NS_ERROR_INVALID_CONTENT_ENCODING`。

这些处理不会绕过 Epic/hCaptcha 的风控。若同步后仍持续收到更难的挑战，优先检查 GLM API 是否稳定，并考虑配置 `BROWSER_PROXY`；GitHub Hosted Runner 的共享出口 IP 仍可能提高挑战难度。不要通过关闭 `glm-4.6v` thinking 来单纯换取速度，本项目的失败样本重放中，这会显著降低点选准确率。

### 5. 为什么现在默认改成每周一次

Epic 周免通常在每周四刷新。对大多数普通用户来说，把默认 schedule 放在周免刷新之后、每周跑一次，更省配额，也更符合实际使用习惯。

如果你需要补充容错，可以保留手动触发 `Run workflow`，但不要在同一天短时间连续重跑，以免增加 Epic 风控和验证码难度。

### 6. 想提高长期稳定性

GitHub Hosted Runner 每次运行都是临时机器，`app/volumes/user_data` 不会跨运行保留；同时，所有用户共享云出口 IP。结果是工作流每周都可能重新触发 Epic 登录和 hCaptcha，单纯增加重试次数反而可能提高风控概率。

对当前项目，稳定性优先级建议如下：

1. **优先使用自己的 Linux 主机、NAS 或 Docker**：把 `app/volumes/` 挂载到持久化磁盘，首次在正常浏览器中完成 Epic 登录和必要确认，之后由定时任务复用同一个 profile。
2. **必须使用 GitHub Actions 时**：保持每周刷新后运行一次，失败后先看截图和日志，不要在短时间内连续手动重跑；`BROWSER_PROXY` 只能改变出口条件，不能绕过 Epic 或 hCaptcha 风控。
3. **不要把 Cookie、浏览器 profile 或登录状态上传到 artifact/cache**：这些文件包含可复用的账号会话，泄露风险高，且缓存生命周期并不适合保存长期登录状态。

如果选择基于 Epic device authorization 的其他项目，首次登录通常比密码加 hCaptcha 稳定，但部分项目已经取消全自动下单，最后仍需要人工确认；它们不能直接视为当前工作流的无缝替代。

## 如何提 issue 才方便排查

如果你遇到的是“登录失败”“checkout 卡住”“日志显示失败但实际已领取”“日志显示成功但实际没入库”这类问题，请按下面步骤提 issue：

1. 打开出问题的 GitHub Actions 运行页面。
2. 滚动到页面底部的 `Artifacts` 区域。
3. 下载页面里实际出现的 artifact：
   - `epic-logs-<run_id>.zip`：运行日志，通常每次都有
   - `epic-runtime-<run_id>.zip`：如果存在，里面通常有商品页、checkout 和 `purchase_debug` 信息
   - `epic-screenshots-<run_id>.zip`：如果存在，里面通常是登录、风控或授权截图
4. 到仓库的 `Issues` 页面新建 bug issue。
5. 把下载到的 zip 直接拖进 issue 编辑框，或者点击附件按钮上传。
6. 同时附上本次 Actions 运行链接，并简单说明“期望结果”和“实际结果”。

不要只贴一小段控制台日志。很多 checkout / captcha / 页面状态问题，必须结合完整日志、`purchase_debug` 和截图一起看，才能真正定位。

补充说明：

- 如果你的 fork 是公开仓库，附上本次 Actions 运行链接通常就够了，维护者一般可以直接查看对应页面。
- 如果你的 fork 是私有仓库，请务必上传本次运行实际出现的 artifact zip；维护者无法直接访问私有仓库的 Actions 页面和运行产物。
