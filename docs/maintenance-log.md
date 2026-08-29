# 维护日志

这个文件用于记录项目内的重要修复、行为调整、兼容性变更和文档规则更新。

## 维护要求

- 以后任何 AI 或人工在这个仓库里做了实际改动，只要会影响运行逻辑、错误处理、文档说明、排障方式或用户使用预期，都需要在本文件追加一条记录。
- 每条记录至少写清楚：日期、问题现象、根因判断、改动文件、结果。
- 不要覆盖旧记录，只追加。
- 如果只是纯格式化、无行为变化的小改动，可以不记；但只要修了 bug、改了流程、改了提示文案、补了排障规则，就需要记。

---

## 2026-04-27

## 2026-04-28

### 在中英文 README 追加社区致谢与头像墙模板

- 现象：
  - README 里原本只有对上游项目和社区来源的常规致谢。
  - 仓库缺少一段专门感谢 issue 提交者、失败案例提供者和日志反馈者的结尾文案，也没有给出“非 contributor 也能展示头像”的写法。
- 根因判断：
  - 项目持续修复高度依赖真实失败案例和 artifact，但 README 还没有把这类社区反馈的价值明确表达出来。
  - GitHub 头像其实可以直接通过用户名链接显示，不需要 contributor 身份，只是文档里之前没有提供可复用模板。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将原有上游项目感谢重命名为“项目来源与参考 / Project Origins and References”，避免和新增的社区致谢混在一起。
  - 在中英文 README 末尾新增更走心的社区致谢，明确感谢 issue、日志、截图、artifact 和失败案例反馈者。
  - 追加 GitHub 头像墙模板说明，支持后续按用户名补充头像，不依赖 contributor 身份。

### 在社区致谢区补入首批 GitHub 头像

- 现象：
  - 社区致谢区已经有文案和模板，但页面还没有真正展示首批反馈者头像。
  - 英文 README 仍然显示了“如何追加用户名”的说明文字，中文 README 也存在半注释状态的残留内容。
- 根因判断：
  - 用户已经提供了明确的 GitHub 用户名列表，应当直接落成可见头像墙，而不是继续停留在说明阶段。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文 README 的社区致谢区加入 `AaronL725`、`cita-777`、`1208nn`、`LGDhuanghe`、`AdjieC` 五位用户的头像链接。
  - 移除页面中可见的模板说明，仅保留注释里的头像墙模板供后续继续追加。

### 将社区头像墙改为更成熟的 README 表格样式

- 现象：
  - 第一版社区头像墙只是把头像横向排成一行，观感偏像临时占位。
  - 纯头像缺少名字和反馈类型说明，识别度不高，方形小图也显得比较生硬。
- 根因判断：
  - GitHub README 不能依赖自定义 CSS 做复杂美化，直接堆一排 `<img>` 很难接近成熟开源项目的展示效果。
  - 更适合参考常见的 contributors table 形式，在 GitHub 原生 Markdown/HTML 能力范围内用表格组织头像、名字和贡献说明。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将中英文 README 的社区头像墙改为表格卡片式布局，统一展示头像、GitHub 用户名和反馈类型。
  - 同步更新注释模板，便于后续继续按同一风格追加用户。

### 将社区头像墙收敛为无边框头像加名字的简洁样式

- 现象：
  - 表格卡片版本虽然比第一版整齐，但每个头像外层都有明显边框，视觉上偏重。
  - 每人一条 `Issue · xxx` 的说明维护成本高，而且会让社区致谢区显得过于“档案化”。
- 根因判断：
  - README 里的致谢更适合轻量展示，不适合继续堆叠字段信息。
  - 对这类名单型内容，头像加名字已经足够表达感谢，继续细分反馈类型收益不高。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将中英文 README 的社区头像墙改为无边框、居中的头像排布。
  - 去掉逐人的反馈类型说明，只保留头像和名字，降低维护成本并弱化沉重感。

### 统一 README 开头文案与项目命名表述

- 现象：
  - 中英文 README 开头仍混有“自动领取项目”“weekly freebies”等旧表述，项目定位和命名不够统一。
  - 英文 README 的社区致谢区名字行仍是可见内容，而中文版已经被注释掉。
- 根因判断：
  - 项目名称已调整为“Epic 周免游戏领取助手”，但 README 顶部介绍还没有同步整理。
  - 开头文案虽然信息完整，但层次不够清楚，对“完全免费”的强调也不够集中。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 重写中英文 README 开头介绍，按“适合谁、为什么容易用、为什么完全免费、GLM 路线价值”重新组织文案。
  - 将英文标题和相关表述从 `freebies` 调整为 `free games`，与当前项目命名保持一致。
  - 将英文 README 中社区致谢区的名字行改为注释状态，与中文 README 保持一致。

### 调整私有 fork 反馈说明并增加 Actions 成功摘要

- 现象：
  - README 和部分文档仍建议用户将 fork 改为私有，但相关说明没有同步强调：私有 fork 的 Actions 页面和运行产物对维护者不可见。
  - 现有 issue 模板默认要求“只提供运行链接”，这对私有 fork 不成立。
  - workflow 成功后还没有统一的 summary 提示用户去成功反馈讨论区留言。
- 根因判断：
  - 仓库内关于“公开 fork / 私有 fork”两种反馈路径的规则还没有统一。
  - 运行成功后的后续动作缺少明确入口，不利于沉淀成功样本。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `.github/ISSUE_TEMPLATE/01-bug-report-zh.yml`
  - `.github/ISSUE_TEMPLATE/02-bug-report-en.yml`
  - `.github/workflows/epic-gamer.yml`
  - `docs/maintenance-log.md`
- 处理结果：
  - 删除 README 和 workflow 文档中“建议改为私有仓库”的表述。
  - 在中英文 README、workflow 文档和 issue 模板中补充规则：公开 fork 可附运行链接，私有 fork 必须上传本次运行实际出现的 artifact zip。
  - 为中英文 issue 模板增加 fork 可见性字段。
  - 在 workflow 成功后写入 `GITHUB_STEP_SUMMARY`，引导用户前往成功反馈讨论区，并补充私有 fork 的反馈说明。

### 统一仓库身份相关的残留命名与链接

- 现象：
  - 仓库中仍残留 `10000ge10000/epic-awesome-gamer`、`QIN2DIM/epic-awesome-gamer` 相关的运行条件、镜像地址、项目元数据和旧工作目录表述。
  - 这些内容已经不再对应当前维护仓库，容易让用户误以为默认运行目标、镜像来源和项目信息仍指向旧仓库。
- 根因判断：
  - 项目在历史迁移和持续维护过程中，README 已经逐步改成当前仓库，但 workflow、Docker、`pyproject` 和部分开发记录仍保留了旧仓库标识。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `docker/docker-compose.yaml`
  - `app/extensions/ext_celery.py`
  - `app/schedule/collect_epic_games_task.py`
  - `pyproject.toml`
  - `docs/development-log-2026-04-22.md`
  - `docs/development-log-2026-04-22.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将 workflow 的主仓库判断切换为 `Ronchy2000/epic-freebies-helper`。
  - 将 Docker Compose 的项目名、服务名、容器名和默认镜像地址切换为当前仓库命名。
  - 将 Celery app 名称与任务队列名改为 `epic-freebies-helper`。
  - 将 `pyproject.toml` 中的作者和项目 URL 切换为当前维护仓库。
  - 将开发记录中的旧工作目录表述同步为当前仓库路径。

### 补充 Gemini/AiHubMix 配置示例和模型覆盖说明

- 现象：
  - 当前代码仍支持 `Gemini / AiHubMix`，但主 README 对这一路线的配置说明过于简略。
  - 用户难以从现有文案中直接判断 `GEMINI_BASE_URL`、`GEMINI_MODEL` 以及 4 个任务模型覆盖项应该如何填写。
- 根因判断：
  - 详细说明主要分散在 workflow 文档和 `.env.example`，主 README 的快速开始部分没有把 Gemini/AiHubMix 路线补成可直接照填的示例。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.env.example`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文 README 的 Secrets 配置段增加 `GLM` 和 `Gemini / AiHubMix` 两组明确示例值。
  - 明确说明变量名是 `GEMINI_BASE_URL`，并补充推荐起步模型值。
  - 补充 4 个任务模型覆盖项的回落规则和示例值。
  - 在 `.env.example` 中补充覆盖项的填写说明，降低配置门槛。

### 检测到 Epic 2FA 必需时立即终止认证流程

- 现象：
  - 某些账号虽然已经通过验证码，但在 `POST /id/api/login` 后立即返回 `errors.com.epicgames.common.two_factor_authentication.required`。
  - 旧流程会把这类情况当作普通登录失败继续进入后续重试，浪费运行时间，也不利于用户快速判断根因。
- 根因判断：
  - 当前项目不支持处理 Epic 的邮箱 / 短信 / 验证器二步验证。
  - 对这类错误继续重试没有意义，应该直接作为不可恢复错误终止。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 为 `two_factor_authentication.required` 增加单独识别逻辑。
  - 一旦检测到 Epic 2FA 仍处于开启状态，认证流程会立即终止，不再继续后续重试。
  - 日志中会给出明确提示：该项目不支持 Epic 2FA，需先关闭 2FA 后再重跑。

### 在 README 中补充 Epic 2FA 关闭说明并移动教程图

- 现象：
  - 根目录存在一张 Epic 2FA 设置界面的教程图，但还没有纳入 README 的常见问题说明。
  - 用户遇到 `two_factor_authentication.required` 时，虽然能从日志判断是 2FA 问题，但文档中缺少直接对应的处理步骤和配图。
- 根因判断：
  - 2FA 是当前项目明确不支持的登录前置条件之一，应该在 README 里单独给出处理方式，而不是仅靠 issue 或口头说明传播。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/images/faq/epic-2fa-remove-methods.png`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将根目录教程图移动到 `docs/images/faq/epic-2fa-remove-methods.png`。
  - 在中英文 README 的 FAQ 中新增 2FA 专项说明，明确列出典型报错和 `/id/login/mfa` 跳转信号。
  - 补充处理步骤，并配图说明：进入 Epic 安全设置页面后，把启用的验证方式全部 `Remove` 掉。

### 区分 Gemini 官方接口与 AiHubMix 的配置说明

- 现象：
  - 主 README、workflow 文档和 `.env.example` 之前把 `Gemini` 与 `AiHubMix` 混写成同一组示例，并直接给出 `GEMINI_BASE_URL=https://aihubmix.com`。
  - 这会误导使用 Gemini 官方接口的用户，以为官方 Gemini 也应填写 AiHubMix 的地址。
- 根因判断：
  - 文档层没有区分“官方 Gemini 默认地址”和“第三方 Gemini 兼容中转接口”。
  - 代码层此前还将 `GEMINI_BASE_URL` 默认值设为 `https://aihubmix.com`，默认行为也不利于直连官方 Gemini。
- 改动文件：
  - `app/settings.py`
  - `app/extensions/llm_adapter.py`
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `.env.example`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将 `GEMINI_BASE_URL` 默认值改为空字符串，留空时直接走 Gemini 官方默认地址。
  - 仅在显式填写 `GEMINI_BASE_URL` 时，才启用 Gemini 兼容中转地址覆盖逻辑。
  - 在中英文 README、workflow 文档和 `.env.example` 中拆分“官方 Gemini”与“AiHubMix”两套示例，避免继续混淆。

### 重新补回 Codex 的 Karpathy 风格工作准则

- 现象：
  - 之前已经为 Codex 接入的 Karpathy 风格工作规则从项目指令中被删除。
  - 当前 `AGENTS.md` 不再包含针对 Codex 的“先澄清假设、简洁优先、精准修改、目标驱动验证”等约束。
- 根因判断：
  - 这是项目文档层面的回退，不是 Codex 全局 skill 安装失效。
  - `~/.codex/skills/karpathy-guidelines` 仍然存在，但缺少仓库级 `AGENTS.md` 约束后，当前项目内的默认行为提示会变弱。
- 改动文件：
  - `AGENTS.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 重新在 `AGENTS.md` 追加 Karpathy 风格的 Codex 工作规则，恢复“编码前思考、简洁优先、精准修改、目标驱动执行”四个原则。
  - 保留原有项目说明不变，并继续兼容本仓库“禁止跑测试”的限制。

### 默认 GitHub Actions 调度改为每周一次

- 现象：
  - 之前 workflow 默认是每天运行一次。
  - 对大多数普通用户来说，这个频率偏高，不符合 Epic 周免按周刷新的节奏，也会额外消耗 GitHub Actions 分钟数。
- 根因判断：
  - 默认 schedule 更适合放在 Epic 周免刷新之后，并按周执行。
  - 同时需要在文档里明确告诉用户：如果他们想改成别的时间，应直接修改 workflow 里的 cron。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 默认 GitHub Actions 调度改为 `20 15 * * 4`，对应 `UTC 周四 15:20` / `北京时间周四 23:20`。
  - 将“为什么默认按周跑”“如何自己改 cron”写入中英文 GitHub Actions 文档。
  - 在中英文 README 的功能概览中同步说明默认是每周四运行一次，并支持自行调整。

### Checkout 安全校验解完后仍停在 Add to library，最终被误判失败

- 现象：
  - 某些免费游戏在 checkout 中完成一轮或多轮 hCaptcha 后，并不会立刻跳到“Thanks for your order / In Library”这类明确成功态。
  - 页面可能仍停留在商品页上的 checkout 弹层，继续显示 `Add to library`，最后主流程以 `Instant checkout ended without a confirmed claim state` 收尾，并在最终 reconciliation 后抛出失败。
- 根因判断：
  - 旧的最终确认逻辑对这类“checkout 还活着，但尚未被动变成 claimed state”的情况过于保守。
  - `final reconciliation` 主要做页面状态检查和订单历史检查，没有在发现 checkout/security 仍然存在时主动把领取流程接着跑完。
  - 同时 reconciliation 首轮不强制重开商品页，容易继续沿用已经过期的 checkout 弹层 DOM。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - `final reconciliation` 现在每轮都会重开商品页，并在发现 `checkout` 或 `security` 仍然活跃时，主动恢复即时结账流程，而不是只做被动确认。
  - `_handle_instant_checkout()` 增加内部恢复模式，允许 reconciliation 复用即时结账逻辑，但避免递归触发自己的 finalize 分支。
  - 将 unconfirmed checkout 的最终确认次数和等待窗口拉长，提升 Epic 后端状态回写较慢时的恢复能力。

### Device not supported 弹窗再次导致领取失败

- 现象：
  - 商品页点击 `Get` 后没有进入 checkout，日志连续出现 `Purchase button ... click returned without visible progress`
  - 最终保存 `purchase_debug/click_no_effect-*.txt`
  - 调试文本里已经能看到 `Device not supported`、`Cancel`、`Continue`
- 根因判断：
  - 代码虽然已有 `Device not supported` 弹窗处理逻辑，但它只会在“点击已经被判断为有进展”之后才执行。
  - 本次页面在弹出 `Device not supported` 后，没有被 `_has_purchase_progress()` 识别成有效进展，导致流程在点击阶段就提前判失败，后续弹窗处理根本没有接上。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `README.md`
  - `README.en.md`
  - `AGENTS.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增 `_is_device_not_supported_visible()`，把 `Device not supported` + `Cancel` + `Continue` 组合识别为明确的阻塞弹窗状态。
  - `_has_purchase_progress()` 现在会把该弹窗视为“点击后的有效进展”，从而继续进入现有的弹窗消除逻辑，而不是过早返回 `click_no_effect`。
  - `_handle_device_not_supported_modal()` 改为复用同一套可见性判断，避免前后条件不一致。

### 增加维护日志要求

- 现象：
  - 项目修复较多，历史经验容易散落在 issue、对话和零散文档里，后续 AI 或维护者很难快速知道哪些坑已经修过、为什么这么改。
- 根因判断：
  - 仓库里缺少一个明确的“变更必须登记”入口，也没有在项目指令里要求后续改动同步记录。
- 改动文件：
  - `AGENTS.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增本文件作为统一维护日志。
  - 在 `AGENTS.md` 中增加要求：后续所有会影响行为、排障或用户预期的改动，都必须同步写入本文件。

### Epic 隐私政策确认页导致登录后流程异常

- 现象：
  - 登录验证码通过后，日志显示 `Login success` / `Right account validation success`
  - 但后续在读取 `//egs-navigation` 时超时
  - 当前 URL 落在 `/id/login/correction/privacy-policy`
- 根因判断：
  - 这是 Epic 账号状态问题，不是 `GLM`、`Gemini` 或 `AiHubMix` 接口问题。
  - 部分账号登录后需要先手动确认一次隐私政策页面，脚本之前把它误当成普通商城页超时。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_games_service.py`
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
- 处理结果：
  - 识别 `privacy-policy correction` 特殊页面并给出明确错误提示。
  - 文档中补充说明：用户需要先用正常浏览器手动登录 Epic，完成该确认页后再重跑 workflow。

### checkout 多选题与 challenge router 的 GLM 返回格式兼容问题

- 现象：
  - `Device not supported` 修复后，流程已经能进入 checkout。
  - 但 checkout 安全校验阶段又出现新的结构化解析失败：
    - `ImageAreaSelectChallenge` 缺少 `challenge_prompt` / `points`
    - challenge router 有时只返回 `image_drag_multi`
  - 最终日志表现为 `instant_checkout_unconfirmed` 或 checkout solve loop 反复失败。
- 根因判断：
  - `llm_adapter` 之前主要补了 drag/drop 的若干变体，但还没有覆盖 area-select 返回的矩形框数组。
  - 同时 challenge router 返回的 `image_drag_multi` 是别名，当前路由识别只收 `image_drag_multiple`，导致 fallback 解析失败。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增 area-select 矩形框归一化，把 `[[x_min, y_min, x_max, y_max], ...]` 和 `[{x_min, ...}, ...]` 转成 schema 需要的 `points`。
  - 给缺失的 `challenge_prompt` / `inferred_rule` 自动补默认值。
  - 为 `image_drag_multi` 增加别名映射，统一归一化成 `image_drag_multiple`。

### `In Library` 已出现但仍被误判为 `click_no_effect`

- 现象：
  - 商品页点击 `Get` 后最终保存了 `purchase_debug/click_no_effect-*.txt`
  - 但调试文本里正文已经明确出现 `In Library`
- 根因判断：
  - `_claim_state_reason()` 对按钮文案里的 `IN LIBRARY` 有识别，但页面正文级别的 claim markers 只收了 `IN YOUR LIBRARY` / `VIEW IN LIBRARY` 等变体，没有把最常见的 `IN LIBRARY` 放进去。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 把正文级别的 `IN LIBRARY` 加入 claim markers。
  - 这样即使按钮状态没被稳定拿到，只要页面正文已经切成 `In Library`，也会被识别成已领取，不再落到 `click_no_effect`。

### 登录拖拽题返回裸坐标串时未被归一化

- 现象：
  - 登录阶段有时会返回 `{"answer": "1165,600,932,688"}`
  - 之前日志里会报 `ImageDragDropChallenge` 缺少 `challenge_prompt` / `paths`
- 根因判断：
  - `llm_adapter` 之前支持括号坐标、JSON 对象、数组等 drag 格式，但没有覆盖最简单的裸 CSV 坐标串。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 为 `x1,y1,x2,y2` 这类纯数字 CSV 形式补了 drag 坐标解析，统一归一化成 `paths`。

### 在进阶文档补充当前验证码支持面分析

- 现象：
  - 项目已经连续修过多类验证码兼容问题，但开发者文档里还没有把“当前到底考虑了哪些 challenge type、哪些仍不稳”写清楚。
- 根因判断：
  - 缺少一段集中说明，后续维护者容易误以为项目已经稳定覆盖所有验证码类型，或者不知道哪些题型是当前明确绕开的。
- 改动文件：
  - `docs/advanced.md`
  - `docs/advanced.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文进阶文档中新增“当前项目实际上考虑了哪些验证码类型”和“为什么有些验证码还是过不去”两段分析。
  - 明确列出当前已接入的 challenge type、被忽略的特殊题目，以及失败常见来源。

### 2026-04-29 OpenAI / GPT provider 接入

- 现象：
  - 用户询问项目是否能接 GPT 模型完成同样的验证码识别任务。
  - 原有配置只覆盖 `gemini` / `glm`，没有 OpenAI / GPT 的独立配置入口。
- 根因判断：
  - `hcaptcha-challenger` 上层仍按 `google-genai` 风格上传图片并调用 `generate_content`。
  - GPT 不能简单复用 `GLM_MODEL` 或 `GEMINI_BASE_URL`；OpenAI Chat Completions 的图片输入需要 `image_url`，本地图片应转成 `data:<mime>;base64,...`。
- 改动文件：
  - `app/settings.py`
  - `app/extensions/llm_adapter.py`
  - `.github/workflows/epic-gamer.yml`
  - `.env.example`
  - `docker/docker-compose.yaml`
  - `README.md`
  - `README.en.md`
  - `docs/advanced.md`
  - `docs/advanced.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增 `LLM_PROVIDER=openai`，以及 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。
  - 默认 OpenAI 模型设为 `gpt-4.1-mini`，并让 4 个验证码子模型在留空时跟随 `OPENAI_MODEL`。
  - 在适配层新增 OpenAI 兼容客户端，把 hCaptcha 图片输入转换为 OpenAI 可接受的 data URL 图片输入。
  - 中英文 README、Docker 示例、Actions secret 透传和进阶文档均补充 OpenAI / GPT 路线说明。

### 2026-04-29 README 结构与用户文档拆分

- 现象：
  - README 同时承担快速开始、完整 provider 说明、FAQ、Artifact 说明、本地调试和 Docker 部署说明。
  - 普通用户首次配置需要阅读过多与首跑无关的内容。
- 根因判断：
  - README 职责过多，详细排障和 provider 细节没有独立文档承载。
  - `.env.example` 缺少按 provider 分组的说明，不利于对照 README 配置。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.env.example`
  - `docs/providers.md`
  - `docs/troubleshooting.md`
  - `docs/local-debug.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - README 缩减为 GitHub Actions 首次配置和运行所需内容。
  - 新增 provider、排障、本地调试与 Docker 三份文档。
  - `.env.example` 改为按账号、provider、高级覆盖项和运行参数分组。
  - 保留中文 README 中 `## 社区致谢` 及其后原文。

### 2026-04-29 在 README 开头标注 OpenAI / GPT 测试分支

- 现象：
  - OpenAI / GPT 支持位于独立开发分支，用户进入分支页面时不容易立即判断该分支应测试哪个 provider。
- 根因判断：
  - README 开头缺少分支用途说明，容易和 `master` 或其他 provider 分支混淆。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文 README 开头新增分支说明。
  - 明确当前分支用于测试 `LLM_PROVIDER=openai`，推荐模型为 `gpt-4.1-mini`，并提示第三方 OpenAI 兼容网关需要支持 `image_url` 输入格式。

### 2026-04-29 补充 OpenAI 分支与 DeepSeek 配置边界

- 现象：
  - 两个 provider 开发分支同时存在，用户可能误以为可以在 OpenAI / GPT 分支中配置 `DEEPSEEK_MODEL`。
- 根因判断：
  - OpenAI 分支 README 只说明了 GPT 测试配置，没有明确排除 DeepSeek V4 测试配置。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 中英文 README 明确说明 OpenAI / GPT 分支不用于测试 DeepSeek V4。
  - 明确提示不要在本分支配置 `DEEPSEEK_MODEL`。
  - 如需测试 DeepSeek V4，应切换到 `codex/add-deepseekv4-provider` 并设置 `DEEPSEEK_MODEL=deepseek-v4-pro`。

### 2026-05-02 补充 Fork 后手动启用工作流说明

- 现象：
  - 用户不确定当前仓库是否还会自动执行领取工作流，也不确定 Fork 后是否需要额外在 GitHub 页面手动启用 Actions。
- 根因判断：
  - workflow 文件已经通过仓库条件跳过主仓库自身的定时领取任务，但中英文 README 和 workflow 文档没有直接写明 Fork 后必须先点一次 `Enable workflow`，否则 GitHub 不会为该 Fork 启用定时 `schedule`。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `docker/docker-compose.yaml`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文 README 和 workflow 文档中补充一句直白说明。
  - 明确写出操作入口：进入 Fork 仓库的 `Actions` 页面，打开 `Epic Awesome Gamer (Scheduled)`，点击一次 `Enable workflow`。

### 2026-05-05 Device not supported 弹窗阻塞购买点击

- 现象：
  - 商品页出现 `Device not supported` / 当前设备不兼容弹窗时，弹窗会挡住后续购买按钮点击。
  - 点击流程可能在看到弹窗后仍继续尝试点击购买按钮，最终保存 `purchase_debug/click_no_effect-*.png` / `.txt`。
- 根因判断：
  - 设备不兼容弹窗是一个需要先点击 `Continue` 才能继续的阻塞状态，不应被当作购买流程本身的有效进展。
  - 弹窗检测需要覆盖主页面和 frame 文本，但检测发生在点击轮询热路径中，读取 frame 文本必须带短超时，避免被默认等待时间放大。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 购买按钮点击前后都会检测并尝试关闭设备不兼容弹窗。
  - `_has_purchase_progress()` 不再把该弹窗本身视为有效购买进展。
  - `_combined_text()` / `_frame_texts()` 支持传入短超时，设备弹窗检测使用 500ms 主页面文本读取和 300ms frame 文本读取。

### 2026-05-05 GLM 框坐标导致 hCaptcha 点选解析失败

- 现象：
  - 登录 hCaptcha `image_label_multi_select` / `image_label_area_select` 流程中，GLM 返回 `{"answer":[[x_min,y_min,x_max,y_max], ...]}`。
  - `ImageAreaSelectChallenge` 校验时报 `points.*.x` / `points.*.y` 缺失，最终触发 `RetryError`。
- 根因判断：
  - 上游 `ImageAreaSelectChallenge.points` 只接受点击点坐标 `{"x": ..., "y": ...}`。
  - GLM 兼容层只要求模型返回 JSON，模型可能用视觉检测常见的框坐标格式回答。
  - 适配层已经识别了框坐标，但错误地把 `x_min/y_min/x_max/y_max` 原样塞入 `points`。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `tests/test_glm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - GLM 返回框坐标时，适配层会转成矩形中心点击点后再构造 `ImageAreaSelectChallenge`。
  - 增加回归测试覆盖数组框坐标和对象框坐标两种返回格式。

### 2026-05-06 GLM/Gemini provider 错配导致登录验证码走错接口

- 现象：
  - 某些 workflow 日志里已经明确打印 `LLM_PROVIDER=glm`，但运行配置同时出现 `GLM_API_KEY=null`、`GEMINI_API_KEY=**********`。
  - 登录验证码阶段没有直接报出 provider 配置错误，而是继续进入 Gemini 上传接口，最终在 `generativelanguage.googleapis.com/upload/v1beta/files` 处报 `API_KEY_INVALID`。
  - 用户看到的是深层 `RetryError` / `ClientError` 栈追踪，不容易判断根因其实是 provider 与 API key 配置不一致。
- 根因判断：
  - 代码此前允许 `LLM_PROVIDER=glm` 与空 `GLM_API_KEY` 一起继续启动。
  - 在这种错配下，GLM 兼容补丁不会生效，但 `hcaptcha-challenger` 仍可能继续使用 `GEMINI_API_KEY` 路径，导致错误表象落在 Gemini/Google 接口上。
- 改动文件：
  - `app/settings.py`
  - `app/extensions/llm_adapter.py`
  - `app/deploy.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 增加 `llm_configuration_error` 统一判断显式 provider 与对应 API key 是否匹配。
  - `apply_llm_patch()` 在 provider 显式错配时会先打出明确日志，不再静默跳过。
  - `deploy()` 在浏览器启动前就会直接终止这类配置错误，并给出清晰提示：`LLM_PROVIDER=glm` 必须配置 `GLM_API_KEY`，`LLM_PROVIDER=gemini` 必须配置 `GEMINI_API_KEY`。

### 2026-05-06 在主文档和 workflow 文档中明确 provider 与 API key 必须一一对应

- 现象：
  - README 和 workflow 文档虽然分别给了 `GLM`、`Gemini`、`AiHubMix` 的示例，但没有把“`LLM_PROVIDER` 必须和实际填写的那组 API key 对应”写得足够直白。
  - 用户可能会误以为只要填了任意一组 key 即可，例如把 `LLM_PROVIDER=glm` 和 `GEMINI_API_KEY` 混在一起使用。
- 根因判断：
  - 现有文档强调了 `GLM` 路线“不需要额外配置 `GEMINI_API_KEY`”，但没有同步强调反向约束：显式选择哪个 provider，就必须填写该 provider 对应的 key。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `.env.example`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在中英文 README 和 workflow 文档中增加显式规则与错配示例。
  - 在 `.env.example` 里增加注释，直接说明 `LLM_PROVIDER=glm -> GLM_API_KEY`、`LLM_PROVIDER=gemini -> GEMINI_API_KEY`。

### 2026-05-06 将 provider 配置提示收敛成直接句式

- 现象：
  - 上一版文档已经补上 provider 与 key 的对应关系，但有些位置仍然通过“不要这样错配”的反例来解释。
  - 这类规则对普通用户更适合写成单句指令，而不是先讲错法再反推对法。
- 根因判断：
  - 配置型文档越接近“照着填”越不容易出错，应该直接告诉用户“选这个 provider，就只填这一组 key”。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `.env.example`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将中英文主文档和 workflow 文档统一改成直接句式：
    - `LLM_PROVIDER=glm` -> 填 `GLM_API_KEY`，无需填 `GEMINI_API_KEY`
    - `LLM_PROVIDER=gemini` -> 填 `GEMINI_API_KEY`，无需填 `GLM_API_KEY`

### 2026-05-06 将“无需填写”进一步明确成“无需新建并填写”

- 现象：
  - 即使写成了“无需填写另一组 key”，部分用户仍可能理解成“要先新建一个空的 Secret，只是不填值”。
- 根因判断：
  - 这类 GitHub Secrets 说明需要把“无需新建”也说清楚，否则普通用户容易把空 Secret 当成必要步骤。
- 改动文件：
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `.env.example`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将中英文文档进一步统一为：
    - `LLM_PROVIDER=glm` -> 填 `GLM_API_KEY`，无需新建并填写 `GEMINI_API_KEY`
    - `LLM_PROVIDER=gemini` -> 填 `GEMINI_API_KEY`，无需新建并填写 `GLM_API_KEY`

### 2026-05-09 登录验证码通过后又跳转隐私政策页时的认证稳态校验

- 现象：
  - 某些运行日志里，hCaptcha 已经成功通过，随后日志显示 `Login success` / `Right account validation success`。
  - 但新开的领取页稍后又被重定向到 `/id/login/correction/privacy-policy`，最终以 `Could not determine Epic login state because //egs-navigation did not appear` 失败。
  - Celery 调度入口即使认证失败，也没有像主入口那样立即中止任务。
- 根因判断：
  - 认证服务此前把“登录阶段收到成功信号”当成了“整个 Epic 商店会话已经可用于领取”，缺少登录后对领取页可用性的稳态确认。
  - 领取前状态检查只做了一次性判断，没有覆盖延迟发生的 `privacy-policy correction` 重定向。
  - `app/schedule/collect_epic_games_task.py` 没有校验 `agent.invoke()` 的返回值，认证失败后仍可能继续执行后续领取逻辑。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_games_service.py`
  - `app/schedule/collect_epic_games_task.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 登录成功后会主动跳转一次周免页，并等待 `isloggedin=true`，只有真正拿到可用商店会话才继续后续流程。
  - 对延迟出现的 `/id/login/correction/privacy-policy` 重定向改为显式识别，给出明确的人工确认提示，不再落成泛化的 `//egs-navigation` 超时异常。
  - 领取页登录态检查改成短轮询稳态等待，避免刚跳转时的瞬时中间页被误判成未知异常。
  - Celery 调度入口与主入口统一：认证失败会立即终止，而不是继续进入领取阶段。

### 2026-05-17 设备不兼容弹窗探测与按钮上下文采样加固

- 现象：
  - 最新运行里，登录已经成功并完成 `Epic store session verification success`，但 `the-telltale-batman` 商品页连续出现 `Purchase button ... click returned without visible progress`。
  - 调试截图和文本已经明确显示 `Device not supported` / `This product is not compatible with your current device` / `Continue`，但运行日志里没有进入设备弹窗处理分支。
  - 随后处理下一个商品时，`_log_purchase_button_context()` 在读取 `purchase-cta-button` 文本时触发 `Locator.text_content: Timeout 30000ms exceeded`，把异常放大成整轮失败。
- 根因判断：
  - 现有设备弹窗探测把“弹窗存在”绑定在“Continue 按钮 locator 也必须短时间内可见”上；当 Epic 弹窗 DOM 形态变化或按钮可见性探测抖动时，会出现“页面文本里弹窗明明存在，但代码判断为不存在”的漏判。
  - `click_no_effect` 路径在最终判失败前没有做一次更强的 blocker 复查，因此会把“仍被设备弹窗挡住”误收口成普通点击无效。
  - 购买按钮上下文采样使用默认长超时，不适合作为调试函数直接挂在主流程里。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 将设备弹窗存在判定改为基于 page/frame 文本 marker 的独立检测，不再要求 `Continue` locator 先可见才承认弹窗存在。
  - `Continue` 点击兜底新增面向 dialog/modal/overlay 容器的浏览器端扫描：优先点击容器内最后一个可见的 `Continue` 按钮，抓不到时再退化成容器内最后一个可见按钮。
  - `_click_purchase_button()` 在所有点击策略都无进展后，会先做一次强复查并再次尝试清理设备弹窗，再决定是否落成 `click_no_effect`。
  - `_log_purchase_button_context()` 改成短超时采样和受控降级，不再让调试信息读取本身触发 30 秒硬超时。

### 2026-06-08 登录后 MFA 推荐页、启动后端与 GLM 拖拽格式加固

- 现象：
  - 社区反馈中登录验证码已经通过，但登录后页面可能停在 `/id/login/mfa/add/default`，后续领取阶段最终报 `Failed to confirm claim flow for promotions`。
  - 本地真实运行时，`browserforge` 的 `fingerprint-network.zip` 下载中断会让 `browser_context` 在 import 阶段直接失败，导致 `BROWSER_BACKEND=playwright` 也无法绕过 Camoufox 初始化问题。
  - Camoufox 本地真实运行中还出现过 `NS_ERROR_UNKNOWN_HOST` 这类浏览器内 DNS 导航错误，旧领取页入口只重试 Playwright timeout。
  - 本地真实运行还发现 GLM 可能返回 `source_coordinates` / `target_coordinates` 拖拽坐标，旧归一化逻辑会让 `ImageDragDropChallenge` 缺少 `paths`。
- 根因判断：
  - `/id/login/mfa/add/default` 是 Epic 登录后的 MFA 设置推荐中间页，不等同于领取失败；代码此前只显式处理隐私政策页和强制 2FA 错误，没有统一识别和跳过 MFA 推荐页。
  - Camoufox、`browserforge` 的重型依赖在模块加载时导入，削弱了 `auto` / `playwright` fallback 的意义。
  - GLM 兼容层的拖拽坐标别名覆盖还不完整。
- 改动文件：
  - `app/services/browser_context.py`
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_games_service.py`
  - `app/extensions/llm_adapter.py`
  - `tests/test_glm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - Camoufox 和 `browserforge.fingerprints.Screen` 改为按后端懒加载，避免 Playwright fallback 被 Camoufox 指纹数据下载失败提前拖死。
  - 周免页登录态入口的导航重试同时覆盖 Playwright timeout 和通用导航错误，降低临时 DNS / 网络错误直接终止运行的概率。
  - 认证流程新增 `/id/login/mfa/add` 检测与跳过逻辑；若无法自动跳过，会明确提示用户手动跳过或完成 MFA 推荐页，不再把它收口成模糊领取失败。
  - 领取页登录态检查也会识别 MFA 推荐页，避免新开页面被重定向后继续进入商品领取逻辑。
  - GLM 拖拽归一化新增 `source_coordinates` / `target_coordinates` 别名，并追加回归测试。
  - 本地验证：`py_compile` 通过；`PYTHONPATH=app pytest tests/test_glm_adapter.py -q` 通过。真实本地领取未能跑到领取阶段：Playwright 后端连续触发 hCaptcha 失败；Camoufox 已能安装并启动，但本机 Camoufox 内访问 Epic 出现 `NS_ERROR_UNKNOWN_HOST`。

### 2026-06-09 Epic 新结账页 Add to Library 与 GLM 结账验证码修复

- 现象：
  - 本地真实运行中，登录和初始 `Get` 点击已经正常，但商品页点击后最终报 `Failed to confirm claim flow for promotions`。
  - 调试快照显示点击后实际已经打开 Epic 结账 iframe，文案为 `THIS IS FREE` / `ADD TO LIBRARY`，旧逻辑只识别 `PLACE ORDER`，因此误判为点击无效。
  - 结账 hCaptcha 中，GLM 会返回 `image_label_single_select`、裸 `x,y` 点坐标、`source_coordinates` / `target_coordinates` 或局部/网格坐标混用，旧兼容层会触发 schema 校验失败或坐标偏移。
  - 结账验证码通过后，Epic 会重建 checkout DOM，旧 `_submit_place_order()` 继续使用失效的按钮 locator，导致后续点击策略各自等待到超时。
- 根因判断：
  - Epic 免费领取页已从旧 `PLACE ORDER` 流程变成部分商品使用 `ADD TO LIBRARY` 的即时结账流程，状态机的 checkout marker 和提交按钮候选不完整。
  - GLM OpenAI 兼容响应格式比 Gemini 更松散，需要对当前 hCaptcha 的路由枚举、裸坐标和图片坐标提示做额外归一化。
  - 结账验证码通过后 checkout iframe/按钮可能被替换，提交阶段必须重新扫描当前按钮，不能复用验证码前的 locator。
  - 机械拖拽轨迹会降低 drag 类结账验证码通过率，应默认使用 Bezier 轨迹。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `app/extensions/llm_adapter.py`
  - `app/deploy.py`
  - `app/settings.py`
  - `docker/docker-compose.yaml`
  - `docker/.env`
  - `tests/test_glm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - checkout 识别新增 `ADD TO LIBRARY` / `THIS IS FREE` / `ADD IT TO YOUR LIBRARY` marker，并把 `ADD TO LIBRARY` 当作可提交按钮。
  - 结账验证码识别新增 `PLEASE TRY AGAIN` + `VERIFY` 组合，避免验证码 iframe 被误判为普通 checkout。
  - `_submit_place_order()` 每个点击策略前都会重新扫描当前 checkout 按钮，并给 dispatch/dom 点击加短超时，避免 DOM 重建后卡住旧 locator。
  - GLM 图片请求改为标准 data URL；图片坐标任务追加网格坐标提示；兼容 `image_label_single_select`、当前 hCaptcha `image_drag_multi` 枚举、裸 `x,y` 点坐标和更多拖拽坐标别名。
  - `HEADLESS=false` 可用于本地可视化排查；默认和 Docker 配置改为启用 Bezier 轨迹。
  - 本地验证：`py_compile` 通过；`PYTHONPATH=app pytest tests/test_glm_adapter.py -q` 通过，7 个用例通过。
  - 真实本地领取验证成功：`Rogue Waters` 已显示 `In Library`；`Songs of Conquest` 通过结账 hCaptcha 后确认 `IN LIBRARY`；最终日志为 `Browser tasks execution finished successfully` / `Scheduler is disabled, deployment completed`。

### 2026-06-09 GitHub Actions 同入口完整领取收口复测

- 现象：
  - 需要确认修复不只是本地已登录账号成功，还要覆盖 GitHub Actions 使用的 `uv run app/deploy.py` 主入口完整收口。
  - 第二个 Epic 账号首次运行会经历完整登录、登录 hCaptcha、MFA 推荐页跳过、商店稳态验证、两个商品即时结账和结账 hCaptcha。
- 根因判断：
  - GitHub Actions 与本地测试共用 `app/deploy.py` 入口；如果 Actions 没有显式传入 Bezier 轨迹配置，虽然代码默认已修正，日志和 fork 配置仍不够直观。
  - 完整收口必须覆盖“验证码后无可解 frame 但稍后出现 `IN LIBRARY`”和“验证码后按钮被 overlay 拦截但 force 点击继续推进”两条路径。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `docs/maintenance-log.md`
- 处理结果：
  - GitHub Actions 入口显式设置 `DISABLE_BEZIER_TRAJECTORY=false`，与本地成功配置一致。
  - 使用 `ronchy2000@gmail.com` 账号按 Actions 同入口配置真实复测成功：登录 hCaptcha 通过，MFA 推荐页自动跳过，`Epic store session verification success` 后进入领取。
  - `Rogue Waters` 通过 `ADD TO LIBRARY` 即时结账后确认 `IN LIBRARY`。
  - `Songs of Conquest` 结账 hCaptcha 首轮失败后重试成功，验证码后标准点击被 overlay 拦截，但 force 点击推进并最终确认 `IN LIBRARY`。
  - 最终日志为 `Confirmed 2 instant claim(s)`、`Browser tasks execution finished successfully`、`Scheduler is disabled, deployment completed`，进程退出码为 0。

### 2026-06-12 Camoufox 清理阶段双重关闭导致 GitHub Actions 假失败

- 现象：
  - 某些 GitHub Actions 日志里，登录、MFA 推荐页跳过、商店会话验证、甚至商品发现都已经正常完成。
  - 但 run 最终不是死在领取状态机里，而是在退出浏览器上下文时抛出 `BrowserContext.close: Connection closed while reading from the driver`，随后整轮以 exit code 1 结束。
  - 日志尾部还伴随多条 `Target page, context or browser has been closed` 的 future 异常。
- 根因判断：
  - `execute_browser_tasks()` 在 `async with open_browser_context(...)` 内部手动调用了 `await browser.close()`。
  - 同时 `open_browser_context()` 自己也负责在退出时关闭 Camoufox / Playwright 持久化 context。
  - 在 GitHub runner 上，一旦 Camoufox 驱动已先断开，第二次关闭会把原本应当成功或至少更准确的主异常覆盖成收尾阶段异常，造成“假失败”。
- 改动文件：
  - `app/deploy.py`
  - `app/services/browser_context.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 浏览器关闭职责统一收回 `open_browser_context()`，移除了 `execute_browser_tasks()` 内部的重复 `browser.close()`。
  - Camoufox 分支改为手动托管 `__aenter__` / `__aexit__`，并在退出时抑制关闭阶段异常，避免驱动已断开时把 run 改写成失败。
  - 这样即使浏览器进程先一步结束，GitHub Actions 也不会因为清理阶段双重关闭而额外翻成 exit code 1。

### 2026-06-16 Epic Store 导航组件缺失导致 Actions 登录态误判

- 现象：
  - 多个用户的 GitHub Actions 日志显示登录 hCaptcha、MFA 推荐页跳过、账号校验和商店会话验证已经完成。
  - 进入领取前检查时，页面停在 `https://store.epicgames.com/free-games?lang=en-US`，但 `//egs-navigation` 长时间没有出现，最终报 `Could not determine Epic login state because //egs-navigation did not appear`。
  - 另一些日志在认证后的商店稳态检查阶段反复输出 `Timed out while waiting for //egs-navigation during auth check`，说明同一依赖点在 Actions 环境下不稳定。
- 根因判断：
  - Epic Store 的导航 Web Component 在 GitHub Actions / Camoufox 环境中可能延迟、失败或被部分加载卡住。
  - 旧逻辑把 `egs-navigation[isloggedin]` 作为唯一登录态来源；即使账号接口已经可访问，也会因为前端导航壳层缺失而终止任务。
  - 这不是 `Device not supported` 或 `ADD TO LIBRARY` 结账状态机回退，而是领取前的会话探针过窄。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 认证后的商店稳态检查和领取前登录态检查保留 `egs-navigation` 快路径。
  - 如果 8 秒内仍拿不到导航登录态，会访问 Epic 账号订单接口 `ajaxGetOrderHistory` 做后备会话探针。
  - 只有后备接口返回合法 JSON 且包含 `orders` 列表时才视为已登录；未登录、重定向、页面错误或非 JSON 响应仍会继续失败，不会把匿名页面误判成有效会话。
  - 领取前订单同步复用同一订单接口解析逻辑，并保留已有 `Device not supported`、`ADD TO LIBRARY`、结账 hCaptcha 和订单历史最终确认逻辑。

### 2026-07-06 收紧即时结账确认链并修复多游戏连续领取的第二单易失败问题

- 现象：
  - 有些账号实际已经把周免领进库里，GitHub Actions 最终却仍以 `Failed to confirm claim flow for promotions` 退出。
  - 另一类高频反馈是：同一轮两个周免里，第一个能成功，第二个更容易卡在 checkout 安全校验、`Place Order` / `Add to library` 后无收口，最终误报失败。
- 根因判断：
  - 旧的即时结账收尾只做了偏短的一次性确认，遇到 Epic 商品页状态回写或订单历史同步稍慢时，容易把“已完成但未及时显现”的 case 判成失败。
  - `Place Order` / `Add to library` 的提交逻辑在第一次 click 调用不抛异常时就直接返回，即使按钮、overlay 和页面状态完全没变化，也不会继续尝试后续提交策略。
  - 连续领取多个游戏时，第二个商品更容易遇到更重的 checkout 风控；同时旧逻辑固定偏向首个 purchase iframe，遇到遗留或非活动 iframe 时更容易点到错误容器。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - checkout 容器扫描改为优先遍历当前页面上更像活动 checkout 的 frame / page 容器，不再固定依赖首个 purchase iframe。
  - `Place Order` / `Add to library` 提交改为只有在按钮消失、进入 claimed、安全校验出现或按钮/overlay 状态发生变化时才算本次 click 真正生效；否则继续尝试后续提交策略。
  - 即时结账末尾增加 promotion 级 reconciliation：可回到商品页重新确认，并额外轮询订单历史，降低“实际已领到但最后没收好”的误报率。
  - `collect_weekly_games()` 会在真正抛错前，再对所有未确认 promotion 统一执行一轮最终 reconciliation，尽量把第二单的延迟成功补收回来。
  - 本地验证限制：未执行测试；已执行 `python3 -m py_compile app/services/epic_games_service.py` 与 `git diff --check` 做静态校验。

### 2026-07-10 更新 BrowserForge 运行时数据依赖

- 现象：
  - 部分 fork 的 GitHub Actions 在进入 Epic 登录前就失败。
  - 日志显示 `camoufox` 导入 `browserforge` 时尝试读取 `browserforge/headers/data/headers-order.json`，但当前锁定的 `browserforge 1.2.3` wheel 中没有该运行时数据文件。
- 根因判断：
  - `uv.lock` 仍锁定 `browserforge 1.2.3`。
  - `browserforge 1.2.4` 已将模型 / 指纹数据改为通过 `apify-fingerprint-datapoints` 依赖提供，不再依赖旧的包内 `headers-order.json` 路径。
- 改动文件：
  - `pyproject.toml`
  - `uv.lock`
  - `docs/maintenance-log.md`
- 处理结果：
  - 在项目依赖中显式增加 `browserforge>=1.2.4`，避免后续重新锁定到缺少运行时数据文件的版本。
  - 刷新 `uv.lock`，将 `browserforge` 从 `1.2.3` 更新到 `1.2.4`，并锁定新增的 `apify-fingerprint-datapoints` 传递依赖。
  - 本地验证：`from browserforge.headers import HeaderGenerator`、`from browserforge.fingerprints import FingerprintGenerator`、`from camoufox import AsyncCamoufox` 均可正常导入。

### 2026-07-17 GLM 复杂验证码多路径丢失并导致 Epic 登录失败

- 现象：
  - 同一提交在维护者账号上可以完成登录和领取，但部分 Fork 会在 Epic 登录 hCaptcha 阶段连续失败，三轮认证后以 `Authentication failed, aborting this run` 退出。
  - 失败日志包含 `ImageDragDropChallenge` 的 `challenge_prompt` / `paths` 缺失校验错误；模型实际返回过 `answer` 四元坐标列表和 `src` 点对。
  - 失败账号主要收到 `image_drag_multi`、多目标点选和补全线段题；成功账号只收到相对简单的 `image_drag_single`。`/checkcaptcha/` 空响应在成功任务中也会出现，因此不是决定性根因。
- 根因判断：
  - GLM 兼容层只稳定归一化单条拖动路径，不能按 `ImageDragDropChallenge` schema 保留 `answer=[[sx,sy,tx,ty], ...]` 中的全部路径，也不兼容 `src` / `dst` 点对。
  - 模型即使识别了多个可移动部件，结构校验重试也可能把结果收缩成单条合法路径，导致复杂拖动题只执行第一步并被 hCaptcha 拒绝。
  - 验证码 frame 消失但页面退回已填写的密码表单时，登录逻辑不会重新提交 `Sign in`，会空等登录结果后重建整轮认证。
  - GitHub Actions 把模型名与 API Key 一起配置为 Secrets，导致有效的 `SPATIAL_PATH_REASONER_MODEL` 在诊断日志中被自动遮罩。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `app/settings.py`
  - `app/deploy.py`
  - `.github/workflows/epic-gamer.yml`
  - `tests/test_glm_adapter.py`
  - `README.md`
  - `README.en.md`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 拖动题按目标 schema 归一化，兼容标准 `paths`、四元坐标列表、点对、`answer`、`src` / `dst` 等返回形式，并按原顺序保留全部拖动路径。
  - GLM 视觉提示增加复杂拖动和多目标点选约束：先统计全部可移动部件；补全线段题按编号端点、形状、颜色和方向匹配；每个动作必须输出独立 `paths` 项。
  - 登录验证码消失但仍停留密码表单时，会在现有三次 solve 预算内重新提交登录，不增加认证总轮数，也不改变领取复核或 GitHub Actions 30 分钟限制。
  - 默认 GLM 模型与文档统一为 `glm-4.6v`。工作流对 provider 和模型名改为 GitHub Variables 优先、同名 Secrets 兼容回退，并增加有效模型路由日志。模型名迁移到 Variables 后，`SPATIAL_PATH_REASONER_MODEL` 可直接显示；仍放在 Secrets 时继续遵守 GitHub 自动遮罩。
  - 增加多路径四元坐标、分号分隔路径和 `src` 点对回归用例。按仓库规则未执行测试；已通过 Black、Ruff、`py_compile` 和 `git diff --check` 静态验证。

### 2026-07-17 Actions 复杂验证码别名校验失败与密码表单恢复异常

- 现象：
  - Fork 运行 `29562510108` 使用上一轮修复提交后仍在登录阶段失败；日志证明模型路由和 GLM 补丁已经生效，并且 `image_drag_multi` 已能输出两条路径。
  - 同一运行中 GLM 还返回了 `src` + `tgt`、`src` + `dest` 和 `answer="840,322|640,470"` 等变体，这些响应在执行拖动前被 `ImageDragDropChallenge.paths` 必填校验拒绝。
  - hCaptcha 消失后页面实际回到了已填写密码的 `Enter your password` 表单，但恢复逻辑报 `Frame.is_visible() got an unexpected keyword argument 'timeout'`，三轮认证都无法重新提交登录。
  - 运行时产物路径只有 `app/volumes/runtime/`，而 hCaptcha 挑战原图位于隐藏目录 `app/volumes/hcaptcha/.challenge/`，失败后只能看到密码页截图，无法复核模型对复杂题型的视觉配对。
- 根因判断：
  - GLM 返回格式仍存在未覆盖的目标字段别名和坐标分隔符；归一化在 Pydantic 响应模型校验前没有把这些真实返回统一成 `paths`。
  - Camoufox 使用的 Playwright 兼容层不接受当前 `is_visible(timeout=...)` 调用路径，密码表单恢复分支因此在点击 `Sign in` 之前异常退出。
  - 复杂拖动提示虽然要求保留多路径，但没有明确强调按题目数量、实心可移动图形与空心轮廓、完整形状和方向逐一配对，模型仍可能按同一行等弱特征选择目标。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `.github/workflows/epic-gamer.yml`
  - `tests/test_glm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 拖动坐标归一化新增 `src` 对 `tgt` / `dest` / `destination` 等目标别名，并支持 `x,y|x,y`、箭头和冒号分隔的单路径答案；这些变体会在 Pydantic 校验前转换为标准 `start_point` / `end_point`。
  - 复杂拖动提示要求路径数与题目显式数量一致，先区分实心可移动部件和空心目标轮廓，再按形状、颜色、尺寸和方向匹配，避免仅按行位置配对。
  - 密码表单恢复改用 `Locator.wait_for(state="visible")`，避免不兼容的 `is_visible(timeout=...)`；重新提交后会先等待登录结果，只有新 hCaptcha 出现时才进入下一次 solve，保留原有三轮预算。
  - `epic-runtime` 产物同时上传 `.challenge` 隐藏目录，后续失败运行可以直接复核挑战原图和模型缓存；领取多轮复核与 Actions 30 分钟限制均未修改。
  - 按仓库规则未执行测试；提交前只执行格式化、Ruff、`py_compile`、workflow YAML 解析和 `git diff --check` 静态校验。

### 2026-07-17 本地 Camoufox 端到端复测与编号线段题目标修正

- 现象：
  - 按用户要求使用本地真实 Epic 账号和 GLM `glm-4.6v` 复测时，普通 Playwright Firefox 能进入登录挑战，但 hCaptcha `/checkcaptcha/` 持续返回空响应并刷新题目。
  - 保存的挑战原图显示，GLM 在线段补全题中把可移动编号 `4` 线段的目标中心选在了已有编号 `3` 端点上，没有推断整段线条在 `3` 与 `5` 之间的最终落位。
  - 本机 Camoufox 启动器访问 GitHub Releases API 时触发 403 速率限制，无法自动获取浏览器二进制。
- 根因判断：
  - 普通 Playwright Firefox 的空校验响应属于本地浏览器环境差异，不能代表 GitHub Actions 默认使用的 Camoufox 路径。
  - 现有提示要求匹配编号和方向，但没有明确区分“连接端点”与“整段平移后的中心目标坐标”，模型容易直接返回已有编号标记的位置。
  - Camoufox 二进制可以从官方 release 资源直链下载，403 只发生在未认证 GitHub API 元数据请求。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 编号线段题提示明确要求：编号 `N` 的可移动线段放入固定 `N-1` 与 `N+1` 之间，按两端连接关系推断整段最终位置；`end_point` 必须是最终落位后的线段中心，不能使用已有编号标记或端点坐标。
  - 本机安装兼容版本 Camoufox 后，以 `BROWSER_BACKEND=camoufox` 完成真实端到端运行，程序确认 Epic 会话有效、查询到两款本周周免、通过订单历史确认均已入库，并正常清理浏览器和以 exit code 0 退出。
  - 因该账号两款本周周免都已拥有，本次端到端运行按设计在订单预检阶段结束，无法重复触发真实 checkout 提交；登录、周免查询、订单核对和任务正常收口均已实测成功。

### 2026-07-17 Actions 拖拽起点偏离实体导致登录验证码令牌无效

- 现象：
  - GitHub Actions 运行 `29565564269` 已加载复杂题型提示和多路径归一化修复，但登录 hCaptcha 仍在三轮认证后失败。
  - 运行时产物显示模型能输出两条拖动路径，但起点坐标会落在可移动卡片的空白处；其中一条路径甚至给出挑战区域之外的 `y=623`。
  - hCaptcha 曾返回一次页面级 `Challenge success`，Epic 登录接口随后仍明确返回 `captcha_invalid`。
- 根因判断：
  - `hcaptcha-challenger 0.19.0` 的挑战载荷已经在 `tasklist[].entities[].coords` 中提供可拖动物体中心点，但实际拖动流程完全没有使用这些坐标，而是把起点和目标点都交给视觉模型估算。
  - GLM 对复杂图形的目标配对可以保留，但让模型同时估算右侧卡片中的起点会引入无必要的误差；起点落空后，目标推理正确也无法完成拖动。
  - 编号线段题的目标落位仍不够稳定，继续提交这类题会显著增加无效令牌概率。
- 改动文件：
  - `app/extensions/hcaptcha_adapter.py`
  - `app/settings.py`
  - `tests/test_hcaptcha_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增 hCaptcha 拖动执行适配：视觉模型继续负责目标图形配对，执行前使用挑战载荷中的实体中心坐标修正每条路径的起点。
  - 根据实际挑战截图自动识别 320px / 330px 两种任务画布原点，再映射到浏览器页面坐标；只有实体数与模型路径数完全一致时才覆盖，无法可靠识别时保留模型结果并记录告警。
  - 起点和路径按纵向顺序配对，兼容双图形题中模型起点整体偏移或超出边界的情况，且不修改模型推断的目标点。
  - 将当前仍不稳定的单线段补全题加入刷新列表，保留多轮探测、最终复核和 GitHub Actions 30 分钟强制终止逻辑不变。
  - 使用失败运行上传的 19 组真实挑战截图、载荷和模型答案逐组回放，320px / 330px 画布均识别正确，所有修正后起点都位于挑战区域内；新增用例与 GLM 兼容用例合计 16 个通过。
  - 使用全新 Camoufox 用户目录完成真实本地运行，邮箱密码登录、Epic 会话验证、周免查询、订单历史核对和浏览器清理全部成功，进程退出码为 0；本次登录未下发拖拽题，当前两款周免均已拥有，因此没有重复执行 checkout。

### 2026-07-17 单线段题刷新循环与多轮验证码超时

- 现象：
  - GitHub Actions 运行 `29572502088` 确认加载提交 `481dbec` 和拖拽起点修复，但三次登录挑战仍失败。
  - 多个 `image_drag_single` 从开始到 `Challenge execution timed out` 正好耗时 120 秒，期间没有模型调用或坐标修正日志。
  - 部分双图形题已经修正起点，但 GLM 仍按上下行位置匹配轮廓；`/checkcaptcha/` 返回空响应时还会打印 JSON 解析堆栈并额外等待响应超时。
- 根因判断：
  - 单线段题被加入 `ignore_request_questions` 后，该账号持续收到同类题，递归刷新直到耗尽每轮 120 秒执行预算。
  - 多六边形轮廓题本质是拓扑匹配，继续依赖视觉模型会引入按行猜测和几十秒推理延迟。
  - hCaptcha 的空校验响应未被转换为明确失败信号，导致无效题目无法及时进入下一轮。
- 改动文件：
  - `app/extensions/hcaptcha_adapter.py`
  - `app/extensions/llm_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `app/settings.py`
  - `tests/test_hcaptcha_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 撤销单线段题跳过策略，避免同类题无限刷新；线段题继续求解，并注入载荷中的真实起点及 3/5 号线段之间的几何走廊约束。
  - 多图形轮廓题优先下载挑战载荷中的透明实体 PNG，通过轮廓 Hu 矩和全局一对一分配匹配目标；置信度不足时才回退 GLM。
  - 空的 `/checkcaptcha/` 响应立即进入失败队列并刷新挑战，不再打印 JSON 解码堆栈或空等 30 秒。
  - 登录结果等待期间不再在 `/id/login` 页面查询不存在的 `egs-navigation`；商店页面和认证后会话探针保持不变。
  - 从运行 `29572502088` 下载的最新产物中回放全部 7 组多轮廓真实挑战，确定性拓扑匹配均返回完整一对一路径，最大轮廓匹配分数为 `0.0606`，无需调用 GLM。
  - 完整测试集共 20 个通过；Black、Ruff、`py_compile` 和 `git diff --check` 均通过。
  - 使用全新 Camoufox 用户目录完成本地真实端到端复测：邮箱密码登录、账号校验、商店会话校验、周免查询、订单历史核对和浏览器清理全部成功，进程退出码为 0；本次登录未下发拖拽题，两款本周周免均已拥有，因此没有重复执行 checkout。

### 2026-07-17 同提交跨区域运行波动与单线段题推理超时

- 现象：
  - GitHub Actions 运行 `29577646160` 与 `29580804524` 均使用提交 `ffe6386`；前者在 `eastus` 成功，后者在 `westus` 三轮认证后失败，因此不是提交或模型配置漂移。
  - 失败运行的首个单线段题没有生成模型答案并耗尽 120 秒；另一个单线段题等待 GLM 116 秒后把目标选到 3/5 号线段之外。相同运行中的多轮廓题均在约 3.5 秒内完成本地拓扑匹配。
  - hCaptcha 的空 `/checkcaptcha/` 响应后经常在约 2 秒内继续到达有效结果，但上一版会立即压入失败信号；多个挑战显示成功后，Epic 仍因区域 IP 风险或挑战状态交错返回 `captcha_invalid`。
- 根因判断：
  - 编号单线段题仍依赖跨区域 GLM 视觉请求，单次 120 秒网络预算既会耗尽整个挑战，也无法保证 3/5 号线段配对正确。
  - 空响应本身可能只是同一校验过程的中间响应，立即判失败会让旧失败信号与随后到达的有效结果交错。
  - 三次独立认证在区域 IP 风险较高时容错不足；失败运行约 12 分钟即退出，尚未利用 Actions 现有 30 分钟上限内的剩余重试机会。
- 改动文件：
  - `app/extensions/hcaptcha_adapter.py`
  - `app/extensions/llm_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `app/settings.py`
  - `tests/test_hcaptcha_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 单线段题使用 Hough 圆检测提取编号标记，并通过稳定的青色 3 号、黄色 5 号色彩关系定位缺口中点；起点继续使用挑战载荷坐标。置信度不足时才回退 GLM。
  - 题目识别只依赖稳定的 `segment` 与 `line` 关键词，兼容 hCaptcha 在 `Please`、`drag`、`the`、`complete` 中混入的西里尔同形字符。
  - 空校验响应增加 5 秒配对宽限；有效非空响应会取消延迟失败信号，确实没有后续结果时才刷新挑战。
  - GLM 单次请求默认限制为 50 秒，避免一个区域网络慢请求独占 120 秒挑战预算；独立认证会话从 3 次增加到 5 次，GitHub Actions 的 30 分钟强制终止保持不变。
  - 对成功与失败两次运行上传的全部 7 张真实单线段题回放，本地目标均成功解析；成功运行最终通过题的本地目标与已通过模型目标仅相差约 7 像素。
  - 完整测试集共 23 个通过，Black、Ruff、`py_compile` 和 `git diff --check` 均通过。
  - 使用全新 Camoufox 用户目录完成本地真实端到端复测，登录、账号校验、商店会话校验、周免查询、订单历史核对和浏览器清理全部成功，进程退出码为 0；本周周免已拥有，因此未重复进入 checkout。

### 2026-07-18 单线段颜色定位未覆盖可移动编号 3 的布局

- 现象：
  - 现有颜色定位能准确处理 `1-5 / source=4` 布局，但对此前 Actions 产物中的 `1-6 / source=3` 布局会选择错误的固定颜色标记。
  - 回放 13 张真实编号线段题时，颜色定位有 3 张无法解析；其余 source=3 样本与编号圆中点相差 24 至 79 像素。
- 根因判断：
  - 将青色与黄色固定解释为编号 3 和 5，只适用于缺少编号 4 的布局；缺少编号 3 时，目标应由编号 2 和 4 的圆心决定。
  - 编号圆中的数字在已观察样本中稳定，可用有限数字模板做全局唯一编号分配，不需要调用外部视觉模型。
- 改动文件：
  - `app/extensions/numbered_line_solver.py`
  - `app/extensions/hcaptcha_adapter.py`
  - `tests/test_numbered_line_solver.py`
  - `tests/test_hcaptcha_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 线段题优先识别 `1-5 / source=4` 与 `1-6 / source=3` 的编号圆，并将目标设为源编号前后两个圆心的中点；低置信度时保留现有颜色定位，再失败才回退 LLM。
  - 13 张真实编号线段题全部解析，最高模板距离为 `0.185`；非线段的双形状题没有产生编号解。
  - Fork 运行 `29563199230` 使用相同编号模板和中点规则完成登录及两款游戏领取，运行 `29563952219` 再次完成登录并从订单历史确认两款均已领取。
  - 基于最新上游的 Fork 运行 `29622500920` 完成登录、商店会话验证和订单历史核对；该轮没有下发编号线段题，因此只作为集成无回归证据，不替代上述题图回放。
  - 按仓库规则未执行测试；使用 Black、Ruff、`py_compile`、真实挑战图离线回放和 `git diff --check` 验证。

### 2026-07-22 验证器 2FA 账号无法自动完成登录

- 现象：
  - 当前登录流程遇到 Epic 验证器 MFA 页面时直接终止，使用验证器 App 2FA 的账号必须先关闭该安全设置才能运行。
- 根因判断：
  - 登录状态机只识别二步验证错误，没有生成、填写和重新提交 TOTP 的处理路径，也没有对应的 Secret 注入配置。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `README.md`
  - `README.en.md`
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_totp_service.py`
  - `pyproject.toml`
  - `uv.lock`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增可选的 `EPIC_TOTP_SECRET`，使用 Base32 密钥生成 6 位 TOTP，并支持单输入框和分离式输入框。
  - 验证码临近过期时等待新时间窗口；Epic 返回无效或过期时重新生成，hCaptcha 打断后如仍需 MFA 则重新提交。
  - TOTP 总提交次数限制为 6 次，无效或过期拒绝次数限制为 3 次；未配置密钥时保持原有行为。
  - 密钥不写入日志，验证码输入框在填写前进行视觉遮罩，并在失败截图前清空，避免完整验证码进入日志、截图或录屏；邮箱验证码、短信验证码和 Passkey 不在本次范围。
  - 按仓库规则未执行测试；使用 Black、Ruff、`py_compile`、workflow YAML 解析、依赖锁核对和 `git diff --check` 进行静态验证。

### 2026-07-22 领取结果只能通过 Actions 日志查看

- 现象：
  - 定时任务结束后没有外部结果摘要，用户需要打开 GitHub Actions 日志才能确认本周游戏、领取状态及失败原因。
- 根因判断：
  - 领取入口没有保存执行前后的订单历史快照，也没有统一的结果分类模型和可选通知通道。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `README.md`
  - `README.en.md`
  - `app/deploy.py`
  - `app/services/epic_collection_summary_service.py`
  - `app/services/epic_games_service.py`
  - `app/services/telegram_notification_service.py`
  - `pyproject.toml`
  - `uv.lock`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增领取前后订单历史快照，根据命名空间区分本次新领取、此前已拥有、未确认成功及明确失败的游戏。
  - 异常后仍尝试刷新订单历史，避免把已经入库的游戏误报为失败；订单历史不可用时降级为未确认。
  - 新增可选的 `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID`，发送运行状态、游戏分类和精简失败原因。
  - Telegram 消息转义 HTML 并按完整行截断；格式化、配置或网络错误均按非致命失败处理，不改变领取结果。
  - 未配置两个 Telegram Secret 时保持原有领取行为，不额外发送通知。
  - 按仓库规则未执行测试；Ruff、`py_compile`、workflow YAML 解析、依赖锁核对和 `git diff --check` 通过，Black 对入口及两个新增服务检查通过；共享游戏服务保留上游既有换行格式，避免引入无关格式化差异。

### 2026-07-30 补充 GLM 资源包到期提示并忽略本地 Claude 配置

- 现象：
  - GLM 首次实名认证赠送的资源包存在有效期，资源包到期后运行日志会出现余额不足或无可用资源包的 `429` 错误。
  - `.claude/settings.local.json` 属于开发者本机权限配置，不应继续由仓库跟踪。
- 根因判断：
  - README 尚未说明 GLM 免费资源包的有效期和对应错误含义。
  - `.claude/` 目录此前未被 `.gitignore` 排除。
- 改动文件：
  - `.gitignore`
  - `.claude/settings.local.json`
  - `README.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - README 补充 GLM 资源包有效期及 `429` 余额不足错误的处理说明。
  - Git 忽略整个 `.claude/` 目录，并停止跟踪现有的本地 Claude 配置文件。

### 2026-07-30 修复登录挑战抢占与 hCaptcha 重试契约

- 现象：
  - Fork Actions 运行 `30520354795` 在 `westus` 连续 5 次登录失败，日志均显示等待 `#sign-in` 超时。
  - 运行上传的失败截图显示 hCaptcha 拖拽题已经覆盖登录表单，说明挑战在代码点击登录按钮前或点击过程中就已出现，但 solver 尚未进入 `wait_for_challenge()`。
  - 当前 `hcaptcha-challenger 0.19.0` 只接受 `image_drag_multi`，适配层却仍会在纯文本兜底路径中把它改写为无效的 `image_drag_multiple`。
  - 上游 `RETRY_ON_FAILURE` 默认开启，业务层未读取 `ChallengeSignal`，购物车购买路径还会在失败后无界递归调用自身。
- 根因判断：
  - 登录流程把“点击 `#sign-in` 成功返回”作为启动 solver 的前置条件，没有处理 hCaptcha 抢先覆盖按钮的竞态。
  - challenge type 使用了脱离上游枚举的手写别名，且依赖允许跨 minor 版本自由漂移。
  - 上游和业务层同时拥有重试控制，但两层都缺少统一信号日志和明确上限。
- 改动文件：
  - `app/extensions/hcaptcha_runtime.py`
  - `app/extensions/llm_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_games_service.py`
  - `app/settings.py`
  - `scripts/check_hcaptcha_contract.py`
  - `tests/test_glm_adapter.py`
  - `.github/workflows/epic-gamer.yml`
  - `.env.example`
  - `pyproject.toml`
  - `uv.lock`
  - `docs/maintenance-log.md`
- 处理结果：
  - 登录提交现在会识别“hCaptcha 已经出现”以及“挑战在点击过程中替换按钮”两种状态，直接进入 solver，不再把挑战页误报为 `#sign-in` 缺失。
  - 登录、checkout、隐性挑战探测、延长探测和购物车购买统一读取并记录 `ChallengeSignal`，外层等待均有明确超时。
  - challenge type 直接来自上游 `ChallengeTypeEnum` / `RequestType`；无效别名被删除，schema 不再接受枚举外的归一化结果。
  - `RETRY_ON_FAILURE` 默认关闭，购物车购买最多尝试 3 次；`hcaptcha-challenger` 依赖限制为 `>=0.19,<0.20`。
  - Actions 增加 hCaptcha 协议契约检查；纯文本 `image_drag_multi` 增加回归用例代码，pytest 路径配置为 `app`。
  - 按仓库规则未执行测试；hCaptcha 契约脚本、Ruff、Black、`py_compile` 和 `git diff --check` 用于静态验证。

### 2026-07-30 修正 Telegram 领取摘要的非致命降级

- 现象：
  - PR #25 在领取前直接读取促销和订单历史，任一摘要快照失败都会阻止核心领取流程。
  - 领取过程抛错后，代码会把所有尚未出现在订单历史中的游戏标记为明确失败，即使它们可能尚未尝试或订单历史尚未同步。
- 根因判断：
  - 可选通知的观测步骤位于核心领取调用之前且没有降级边界；异常分类又把“没有成功证据”错误等同于“存在失败证据”。
- 改动文件：
  - `app/services/epic_collection_summary_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 领取前促销或订单快照失败时继续执行核心领取，并在摘要中记录快照不可用。
  - 领取后的订单快照失败时返回未确认摘要，不再把已经完成的领取改判为任务失败。
  - 领取异常时只确认快照能够证明的新领取项目，其余项目归为未确认，不再无证据地标记为失败。

### 2026-07-30 收紧 TOTP 输入与 hCaptcha 恢复边界

- 现象：
  - PR #24 的兜底输入路径即使没有成功聚焦验证码控件，也会向当前页面焦点键入完整 TOTP。
  - MFA 阶段调用 hCaptcha solver 后没有检查 `ChallengeSignal`，失败信号也会被当成已解决；多次等待登录结果还会重置 TOTP 次数限制。
- 根因判断：
  - 兜底输入、挑战完成和重试上限分别依赖“已调用”而不是可验证的成功结果，状态又被限制在单次等待函数内部。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_totp_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 只有成功聚焦并遮罩候选验证码控件后才允许键盘输入 TOTP。
  - MFA hCaptcha 统一使用有外层超时的挑战 helper，并且只接受 `ChallengeSignal.SUCCESS`。
  - TOTP 提交、无效拒绝和验证码后刷新状态在整个认证运行中累计，无法通过重复进入等待函数绕过上限。

### 2026-07-30 保证 Telegram 与 TOTP 未配置时不改变旧流程

- 现象：
  - Telegram 未配置时虽然发送函数会跳过，但领取入口仍无条件建立摘要，并额外读取促销与领取前后的订单历史。
  - TOTP 未配置时，认证异常清理仍会检查并尝试清空 MFA 输入框；进入 MFA 分支后才会发现缺少 Secret。
- 根因判断：
  - 两个可选功能只在各自执行末端判断配置，门控位置晚于它们新增的页面和网络操作。
- 改动文件：
  - `app/deploy.py`
  - `app/services/telegram_notification_service.py`
  - `app/services/epic_authorization_service.py`
  - `app/services/epic_totp_service.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 只有 `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID` 同时存在时才启用摘要快照和通知；缺少任一配置时直接执行原始领取路径。
  - 只有 `EPIC_TOTP_SECRET` 存在时才选择验证器方式、读取或清理 MFA 输入框以及生成和提交 TOTP。
  - 两项功能完整配置后保持现有功能；未配置或配置不完整时不报错，也不增加对应的页面、订单历史或通知请求。

### 2026-07-30 补齐浏览器代理与 virtual 降级语义

- 现象：
  - GitHub Actions 使用共享云 IP，但浏览器没有可选代理入口，用户无法自行降低数据中心 IP 带来的 hCaptcha 风控。
  - workflow 已运行在 Xvfb 中，主入口却把浏览器固定为真 headless；Playwright fallback 又把 `virtual` 转成 headless，浪费虚拟显示环境。
  - Camoufox 自动降级到普通 Playwright Firefox 时只有普通 warning，且 Docker 示例仍开启上游无界 `RETRY_ON_FAILURE`。
- 根因判断：
  - 浏览器配置只覆盖后端选择，没有统一网络出口、显示模式和降级可观测性；Docker 示例也未同步业务层已接管重试上限的新策略。
- 改动文件：
  - `app/settings.py`
  - `app/services/browser_context.py`
  - `app/deploy.py`
  - `app/schedule/collect_epic_games_task.py`
  - `.env.example`
  - `.github/workflows/epic-gamer.yml`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `README.md`
  - `README.en.md`
  - `docker/docker-compose.yaml`
  - `docker/.env`
  - `docs/advanced.md`
  - `docs/advanced.en.md`
  - `docs/hcaptcha-reliability-plan.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 新增可选且日志遮罩的 `BROWSER_PROXY`，严格解析 HTTP(S)/SOCKS URL，并同时透传 Camoufox 与 Playwright；未配置时保留原网络路径。
  - Linux、Actions 与 Celery 统一使用 `virtual`；Playwright fallback 优先复用外部 `DISPLAY`，没有时自行创建并清理 Xvfb，不再退化成真 headless。
  - 自动从 Camoufox 降级时记录 error 级后端状态，运行日志只显示是否启用代理，不输出代理地址或凭据。
  - Camoufox fallback 只捕获浏览器启动异常；领取过程中的业务异常会原样上抛，不会被误判为启动失败并重复执行。
  - Docker 示例关闭上游递归重试，与应用层有界重试保持一致；模型分工建议因缺少分题型数据暂不调整。

### 2026-07-31 修复 README Star 趋势图失效

- 现象：
  - 中英文 README 引用的 `api.star-history.com/chart` 明暗主题图片均返回 HTTP 503，仓库首页无法显示 Star 趋势。
- 根因判断：
  - GitHub 在 2026 年 7 月将 Stargazers 列表及时间戳限制为仓库管理员和协作者可读，Star History 公共服务不具备本仓库权限，旧的匿名实时图无法继续生成。
- 改动文件：
  - `scripts/generate_star_history.py`
  - `.github/workflows/update-star-history.yml`
  - `docs/images/star-history-light.svg`
  - `docs/images/star-history-dark.svg`
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - README 改用仓库内的明暗主题 SVG，不再依赖会返回 503 的第三方实时图片接口。
  - 新增每日定时及手动触发的 Action，使用本仓库短期 `GITHUB_TOKEN` 从 GitHub API 获取 Stargazer 时间戳并更新图表，不需要公开个人 PAT。
  - 更新任务只在上游仓库执行，Fork 与原有领取工作流不受影响；Star 数据没有变化时不会创建空提交。

### 2026-07-31 可选多账号支持（保持单账号路径不变）

- 现象：
  - 需要在同一个 Fork / 同一次 workflow 中顺序处理多个 Epic 账号，但现有用户仍只配置 `EPIC_EMAIL` / `EPIC_PASSWORD`。
  - 早期多账号实现会把单账号也送进聚合循环，改写异常类型与诊断栈；部分非法 `EPIC_ACCOUNTS` 行会被静默跳过。
  - 多账号场景下 Telegram 摘要无法区分是哪个账号的结果。
- 根因判断：
  - 多账号必须是完全可选能力：未启用时要走与 master 完全相同的单账号调用链。
  - `EPIC_ACCOUNTS` 部分合法、部分非法时若静默省略，会造成“配置写了 3 个账号但只跑了 2 个却显示成功”的假阴性。
  - Telegram 通知在多账号下需要账号归因，同时单账号默认文案不能变。
- 改动文件：
  - `app/accounts.py`
  - `app/deploy.py`
  - `app/settings.py`
  - `app/services/telegram_notification_service.py`
  - `.github/workflows/epic-gamer.yml`
  - `.env.example`
  - `README.md`
  - `README.en.md`
  - `tests/test_accounts.py`
  - `tests/test_telegram_account_label.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 可选 `EPIC_ACCOUNTS`（多行 `email:password`）；未配置或全非法时回退/直通原有 `EPIC_EMAIL` / `EPIC_PASSWORD` 单账号路径，直接调用 `execute_browser_tasks_with_notification()`，不做 `swap_account` 或异常聚合。
  - 仅在全部非空行都合法时进入多账号顺序执行；若同时存在合法与非法行，任务以配置错误失败并列出非法行号，不会静默跳过。
  - 密码允许包含冒号（只按第一个 `:` 分割）；邮箱做轻量格式校验。
  - 每个账号切换 `settings.EPIC_EMAIL` / `EPIC_PASSWORD` 后复用现有登录、hCaptcha、TOTP、Telegram 与 browser runtime；浏览器 profile 仍按邮箱隔离。
  - 多账号 Telegram 摘要增加打码后的 `账号：` 标签；单账号不传 `account_label`，消息格式保持不变。
  - `EPIC_TOTP_SECRET` 仍为全局限制（本版已知限制，文档已说明）；工作流超时可通过 `JOB_TIMEOUT_MINUTES` 配置（默认 60）。
  - 补充针对缺省 `EPIC_ACCOUNTS`、全非法回退、部分非法失败、密码含冒号、单账号通知格式不变的回归测试。

### 2026-07-31 收紧多账号无效配置与 profile 路径边界

- 现象：
  - `EPIC_ACCOUNTS` 全部无效且没有备用单账号凭据时，分发器仍会以空邮箱和密码启动浏览器。
  - 多账号邮箱的轻量校验允许路径分隔符，而浏览器 profile 目录直接按邮箱派生。
  - 既有测试覆盖了解析函数，但没有验证单账号分发器保持原始调用链和异常对象。
- 根因判断：
  - 全无效配置的回退条件没有确认 `EPIC_EMAIL` 与 `EPIC_PASSWORD` 同时存在。
  - 邮箱格式判断只检查了 `@`、域名和普通空格，没有覆盖文件路径与控制字符。
- 改动文件：
  - `app/accounts.py`
  - `app/deploy.py`
  - `tests/test_accounts.py`
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 全无效多账号配置仅在备用邮箱和密码完整时回退；否则在启动浏览器前报告明确配置错误。
  - 多账号邮箱拒绝 `/`、`\`、空白和控制字符，避免 profile 路径逃逸。
  - 增加分发器回归覆盖，验证单账号直通、原始异常对象不被替换、合法回退以及无凭据快速失败。

### 2026-08-08 取消仓库自更新 Star 趋势图

- 现象：
  - Star 趋势图依赖每日 GitHub Action 生成并提交 SVG，持续制造与业务无关的提交；Fork 用户也会继承这套更新工作流。
- 根因判断：
  - 仓库内生成方案把展示数据维护耦合到代码仓库写权限；Star History 当前 `/svg` 接口可直接提供带 CDN 缓存的动态明暗主题图，无需仓库自行更新。
- 改动文件：
  - `.github/workflows/update-star-history.yml`（删除）
  - `scripts/generate_star_history.py`（删除）
  - `docs/images/star-history-light.svg`（删除）
  - `docs/images/star-history-dark.svg`（删除）
  - `README.md`
  - `README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 中英文 README 直接引用 Star History 托管的动态 SVG，并保留明暗主题适配。
  - 仓库和 Fork 不再包含 Star 图定时任务，不需要 `contents: write` 权限，也不会再产生 `chore: update star history chart` 提交。
  - Star 趋势展示改为第三方可用性依赖；即使外链暂时不可用，也不会影响领取工作流或修改仓库内容。

### 2026-08-08 修复 checkout 容器等待放大至任务超时

- 现象：
  - Actions run `31149757724` 在成功打开 Beacon Pines checkout 并多次处理 hCaptcha 后，持续输出 `Primary buttons not found in checkout containers`，最终在 60 分钟 job timeout 时被取消，后续周免未处理。
- 根因判断：
  - checkout 等待循环使用手工累加的固定步长统计耗时，但一次容器扫描会按 frame、按钮和 locator timeout 串行放大；日志中标称 1 秒的轮询实际可耗时约 60–90 秒。
  - `_observe_checkout_outcome()` 在没有发现领取成功、安全检查或 checkout 按钮时仍固定返回 `checkout`，把空白/失效弹窗误判为可继续提交。
  - 四轮即时结账按状态机循环次数计数，单纯恢复 hCaptcha 的轮次也会消耗一次提交机会；本次实际只提交两次便进入漫长核验。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `tests/test_checkout_state_machine.py`
  - `tests/test_helper_env_generator.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 容器扫描、checkout ready、购买状态和提交结果观察统一改用 `time.monotonic()` 的真实截止时间；单次扫描共享总预算，不再按 frame 倍增。
  - 没有发现有效 checkout 容器时返回 `pending`，并以最后一次扫描状态为准；hCaptcha 消失后必须恢复到 `claimed` 或 `checkout` 才视为成功，空白弹窗会进入有界最终核验。
  - 仅实际点击 `Add to library` / `Place order` 时增加提交计数，安全检查恢复不再吞掉四次提交额度。
  - 单商品即时 checkout 增加 15 分钟总时间盒，最终核验中的 checkout 恢复每次限制为 2 分钟，避免单个商品占满 60 分钟任务。
  - 新增容器总预算、pending 判定及安全检查/提交计数回归测试。
  - env generator 测试改在 pytest 临时目录输出并增加断言，完整测试不再污染仓库的 `docker/` 目录。

### 2026-08-08 修复可见 Add to library 按钮未被 checkout 扫描命中

- 现象：
  - Actions run `31257535606` 的失败截图中 checkout 弹窗及 `Add to library` 按钮已经可见，但程序仍连续报告 `Primary buttons not found in checkout containers`，最终核验失败。
  - 上一轮修复仅通过状态机单元测试，没有使用本地真实账号完成端到端领取验证。
- 根因判断：
  - 本地 Camoufox 探针确认真实 purchase frame 中提交按钮的复合选择器、大小写不敏感正则和标题文本定位都返回一个元素，DOM 和选择器本身并未缺失。
  - 当前 Playwright 1.53 的 `Locator.is_visible(timeout=...)` 会把已声明为忽略的 `timeout` 参数继续传给不接受该参数的 `Frame.is_visible()`，实际抛出 `TypeError`；结账容器扫描的宽泛异常处理吞掉该错误后，将“按钮可见但可见性检查异常”误报成“按钮不存在”。
  - 早期后备定位同时使用区分大小写的精确文本匹配和全大写常量，无法命中页面实际的 `Add to library` 文本；失败工件又会在任一 frame 读取异常时遗漏整个 frame，掩盖了上述证据。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `tests/test_checkout_state_machine.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 直接把 `webPurchaseContainer` 的 `FrameLocator` 放在扫描首位，再使用 URL 和文本启发式作为回退，避免不必要的 frame handle 转换。
  - 在读取 frame body 前先扫描可见提交控件，并以大小写不敏感的精确 `Add to library` / `Place order` 正则作为后备入口后向上寻找可点击祖先；移除 Epic 领取路径中传给 `Locator.is_visible()` 的无效 timeout 参数。
  - 失败工件逐 frame 记录去除查询参数后的 URL、可见操作控件和探测异常；单个 frame 失败不再导致该 frame 从报告中消失。
  - 本地真实 Camoufox 流程已从持续报告按钮不存在恢复为命中 `ADD TO LIBRARY` 并执行提交；实际领取被账号 24 小时免费游戏限流阻断，未将其误报为领取成功。
  - 增加 hCaptcha frame 共存、标题大小写文本和 Playwright 无参数可见性调用的回归覆盖。

### 2026-08-08 识别 Epic 账号 24 小时免费游戏领取限流并快速终止

- 现象：
  - 本地真实 checkout 点击 `Add to library` 后同时出现 hCaptcha 和提示 `Your account is unable to download any more free games ... please wait 24 hours`，程序仍进入挑战求解及重复提交。
- 根因判断：
  - 该提示是 Epic 对账号施加的免费游戏领取限流，继续求解 hCaptcha、重试按钮或最终核验都无法完成本次领取。
  - 现有状态机只有 `claimed`、`security`、`checkout` 和 `pending` 状态，没有账号级不可恢复终止状态，因此把限流场景当作可恢复安全检查。
- 改动文件：
  - `app/services/epic_games_service.py`
  - `tests/test_checkout_state_machine.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 仅在完整匹配“无法继续领取免费游戏”和“等待 24 小时”两段固定文案时判定账号限流，避免普通错误误判。
  - 在购买状态等待、提交后观察和 hCaptcha 求解前优先检查限流，并通过专用异常穿透 checkout fallback，立即终止本次任务且保留调试截图。
  - 限流不会被标记为领取成功，也不会继续消耗挑战 API、提交次数或任务总时长。

### 2026-08-08 修正 GitHub Actions 失败后的最终领取结论

- 现象：
  - 领取进程因 Epic 24 小时账号限流退出后，工作流只有 `if: success()` 的成功摘要，没有在 Actions 最终摘要中明确说明本次未领取成功。
- 根因判断：
  - Python 进程和 Telegram 已把限流作为失败处理，但 GitHub Actions 缺少对应的 `if: failure()` Step Summary，用户只能从长错误堆栈中判断最终结果。
- 改动文件：
  - `.github/workflows/epic-gamer.yml`
  - `docs/maintenance-log.md`
- 处理结果：
  - 工作流失败后检查本次日志和 runtime 工件；命中 Epic 限流固定文案时，明确显示受影响账号未确认领取成功并建议至少等待 24 小时。
  - 其他失败显示通用“领取未完成”摘要并引导查看失败步骤和上传工件；成功摘要仍只在任务成功时执行。

### 2026-08-08 将 Epic 24 小时封控改为绿色终止分支

- 现象：
  - 账号已明确进入 Epic 24 小时免费游戏领取封控后，继续运行验证码没有意义；上一版虽然会停止验证码和重试，但仍让 Action 以红色失败结束。
- 根因判断：
  - 封控不是程序故障，而是当前账号暂时不可领取的预期业务终止状态；专用限流异常尚未在部署编排层转换为正常终止结果。
  - 直接把所有领取异常改成绿色会掩盖真实故障，因此只能特殊处理 `EpicFreeGameRateLimitError` 及其被通知汇总异常包装后的 cause 链。
- 改动文件：
  - `app/deploy.py`
  - `app/services/epic_collection_summary_service.py`
  - `.github/workflows/epic-gamer.yml`
  - `docs/maintenance-log.md`
- 处理结果：
  - 单账户检测到 24 小时封控后立即结束浏览器流程、不再重试，并由部署层转换为正常返回，使 Action 保持绿色；其他异常仍抛出并保持红色。
  - 启用 Telegram 时直接生成“未确认领取”的限流通知摘要，不再执行封控后的订单历史核验，随后立即关闭浏览器。
  - 多账户中的封控账号单独计为 `rate-limited`，不计入领取成功，也不阻断其他账号；只有真实失败账号才让整个 Action 失败。
  - 绿色 Action 的最终摘要会优先识别限流日志并显示“正常结束但本次领取未成功”，不会进入普通成功领取提示。

### 2026-08-11 收紧 GLM 动物计数多选提示与点选推理模式

- 现象：
  - 动物计数类 hCaptcha 多选题同时展示左侧可选网格和右侧示例动物、数量徽标；通用多选提示未明确两者的交互边界，模型可能将右侧参考内容当作可点击目标。
  - 当前 GLM 4.5 思考模式会对所有结构化题型统一开启；点选题通常需要在较短的 hCaptcha 响应窗口内返回坐标，额外推理会增加超时风险。
- 根因判断：
  - 多选提示只要求返回全部目标，缺少“参考栏不可点击”和“按数量精确选择左侧网格”的约束。
  - thinking payload 只按模型和配置开关判断，没有按 `points` 与 `paths` schema 区分延迟需求。
- 改动文件：
  - `app/extensions/llm_adapter.py`
  - `tests/test_glm_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：
  - 多选提示明确将右侧动物/数量栏定义为不可点击参考区，要求只从左侧网格按指定数量返回目标中心点。
  - GLM 4.5 的点选 schema 关闭 thinking；拖拽 schema 保持开启，GLM 4.6 的既有行为不变。
  - 新增提示注入和 thinking-mode 分支回归测试，覆盖点选、拖拽和 GLM 4.6 保持默认行为。

### 2026-08-14 修复 hCaptcha HSW 解码、GLM 超时预算和越界点击

- 现象：
  - Actions run `31766718025` 在登录 hCaptcha 阶段运行约 25 分钟后失败；同一轮任务中多次出现 GLM 约 50 秒读取超时、`HSW reverse failed` 和挑战执行超时。
  - Firefox 读取 `/hsw.js` 正文时报 `NS_ERROR_INVALID_CONTENT_ENCODING`，随后 payload/count 为空，确定性求解器无法使用。
  - 动物计数题真实截图中的参考条在左、可点击网格在右，但旧提示词写成相反方向；模型还返回过超出挑战框下沿的 `y=809` 坐标，旧流程会直接点击。
- 根因判断：
  - Camoufox/Firefox 对该次压缩的 HSW 响应解码失败；问题位于浏览器响应正文读取层，不是 HSW 算法本身。
  - GLM 50 秒客户端时限叠加上游三次网络重试和固定等待，最坏耗时超过 hCaptcha 单轮 120 秒执行时限；日志只打印空的 `ReadTimeout` 文本，难以辨认。
  - 点选流程缺少挑战框/可点击区域校验，计数题提示又错误依赖固定左右布局，模型的参考条和越界坐标都可能进入鼠标点击。
- 改动文件：
  - `app/services/browser_context.py`
  - `app/extensions/llm_adapter.py`
  - `app/extensions/hcaptcha_adapter.py`
  - `tests/test_browser_context.py`
  - `tests/test_glm_adapter.py`
  - `tests/test_hcaptcha_adapter.py`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `docs/hcaptcha-reliability-plan.md`
  - `.gitignore`
- 处理结果：
  - 仅对 `hsw.js` 强制无压缩传输，保留其他请求头和网络行为；真实 Camoufox 探针读取到 HTTP 200、1,220,616 字节正文，且响应不再包含 `content-encoding`。
  - GLM 超时异常包含时限和异常类型，上游网络尝试从三次限制为两次；保留 GLM 4.6 thinking，因为失败截图重放显示全局关闭会降低坐标准确率。
  - 计数题提示改为方向无关；通过重复数量徽标识别参考条方向并约束另一侧网格。所有点选答案在缓存和点击前验证挑战边界，计数题额外验证可点击网格，越界答案直接拒绝。
  - 无效的标量拖拽坐标提前报告为结构错误；新增浏览器请求头、超时信息、重试预算、左右参考条和越界坐标回归覆盖。
  - 本地定向测试 `35 passed`，完整测试 `60 passed`，Ruff、变更文件 Black 和 `git diff --check` 均通过。

### 2026-08-28 核对 fork 同步状态并收敛 Epic 登录 challenge 状态机

- 现象：
  - Actions run `33106170399` 使用提交 `f689bcc`，在 runner、依赖安装、Camoufox、hCaptcha 协议检查之后失败；首个明确卡点是邮箱页的 `#continue` 处于 disabled，旧逻辑仍直接点击并等待超时。
  - 旧流程在同一页面连续调用 hCaptcha 等待器。日志先出现 `signal=failure`，之后即使出现 `Challenge success` 也没有稳定地重新提交仍停留在密码页的登录表单，最后回到邮箱页并以 `Incorrect response. Please refresh the page.` 结束；没有登录成功、商店会话或入库证据。
  - fork 的 `origin/master=f689bcc` 与上游 `upstream/master=50043c4` 看起来 SHA 不同，但 `50043c4` 已经是 `f689bcc` 的祖先；两者的实际差异只有 fork 自己新增的 `sync-upstream.yml`。同步 Action 输出 `Upstream is already included in fork history` 是正确的无操作结果，不是漏拉上游功能提交。
- 根因判断：
  - 本次失败不是上游代码未同步，而是登录状态机把“checkbox iframe 仍挂载”误当成“仍有可处理 challenge”，并在同一响应队列上重复消费结果；失败信号也没有立即结束当前认证尝试。
  - Hosted Runner 每次都是临时环境，无法跨周复用 `app/volumes/user_data`，共享出口 IP 又会增加 Epic 风控波动，因此即使代码修好，Hosted Runner 仍不可能达到自托管持久 profile 的稳定性。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `app/settings.py`
  - `.env.example`
  - `.github/workflows/README.md`
  - `.github/workflows/README.en.md`
  - `docs/maintenance-log.md`
- 处理结果：
  - 邮箱阶段现在只点击 enabled 的 `Continue`；发现真实 challenge 时只处理一次，成功后等待 challenge iframe 消失再继续。
  - 密码/MFA 阶段按提交状态区分 challenge；失败立即结束当前页面尝试，成功后仅当密码表单仍存在时重新提交，不再在同一页面无界循环。
  - 外层认证默认限制为两次，并在换页重试时保留浏览器会话；移除每次登录强制追加的 `sessionInvalidated=true`，让自托管持久 profile 能复用登录状态。
  - 已通过 Black、Ruff、`py_compile` 和 `git diff --check`；按仓库规则未执行测试。修复后的 Actions 运行尚未触发，因此当前不能把运行时登录或领取宣称为已验证成功。
  - 文档补充了自托管/NAS/Docker 持久 profile 的优先部署建议，并明确不应把 Cookie 或浏览器 profile 上传到 artifact/cache。

### 2026-08-28 收敛登录重试并阻止 Actions 并发认证

- 现象：修复前的登录流程可能在邮箱阶段重复点击禁用按钮，或在 hCaptcha 成功后继续消费旧响应；一次运行最多重复认证 5 次。邮箱阶段的实现还没有完全遵守新增的认证超时配置。
- 根因判断：Epic 登录页和 hCaptcha iframe 都是异步状态；并发运行或无界重试会增加账号风控，而不是提高成功率。checkbox iframe 的通用固定选择器也可能与当前实际 iframe 不一致。
- 改动文件：
  - `app/services/epic_authorization_service.py`
  - `.github/workflows/epic-gamer.yml`
  - `docs/maintenance-log.md`
- 处理结果：checkbox 改为使用已发现的实际 iframe 直接点击；邮箱阶段使用完整 `AUTH_TIMEOUT_SECONDS`；认证重试默认限制为 2 次；同一仓库的定时和手动工作流使用互斥组且不取消正在运行的任务。
- 验证结果：变更文件 Black、Ruff、`py_compile`、`git diff --check` 和 `PYTHONPATH=app .venv/bin/python scripts/check_hcaptcha_contract.py` 均通过；按仓库规则未执行测试。新的 Actions 运行仍需推送后才能验证真实 Epic 登录和入库结果。

### 2026-08-28 修正 hCaptcha 成功响应在异步回调中的丢失

- 现象：`/checkcaptcha/` 已返回成功后，后续空响应或 `/getcaptcha/` 回调可能清空 `AgentV` 的响应队列，导致登录流程再次收到失败或超时；此前只在空响应路径上做延迟处理，无法覆盖非空失败响应和回调并发。
- 根因判断：`hcaptcha-challenger 0.19.0` 的原始 `/getcaptcha/` 处理器会无条件清空响应队列；Playwright 的 response 回调并发执行，空、失败、成功响应的先后顺序不能假设。
- 改动文件：`app/extensions/hcaptcha_adapter.py`、`tests/test_hcaptcha_adapter.py`、`docs/maintenance-log.md`。
- 处理结果：统一在锁内读取和分类 `/checkcaptcha/` 响应；空或非 pass 结果延迟一个短暂窗口，后续 pass 优先；开始新的 hCaptcha 尝试时清理旧失败但保留已经排队的 pass，避免上游 `/getcaptcha/` 清理操作丢失成功结果；新增成功先到和失败延迟后被成功覆盖的回归用例。
- 验证边界：需要推送后的真实 Actions 运行确认 Epic 登录、Store session 和逐款入库证据；按仓库规则不执行测试。

### 2026-08-28 隔离迟到的 hCaptcha 与 Epic 登录响应

- 现象：一次 hCaptcha 或登录请求结束后，迟到的 `/checkcaptcha/`、`/getcaptcha/` 或 `/id/api/login` 响应可能被下一次尝试消费；邮箱步骤也可能在对应登录 POST 尚未返回时继续填写密码，形成异步竞态。
- 根因判断：此前响应处理只依赖当前队列/generation，未记录响应对应的 request；未知响应会被当作当前尝试处理。登录提交状态同样缺少严格的 request-response 绑定，且非 JSON 登录响应不会唤醒等待屏障。
- 改动文件：
  - `app/extensions/hcaptcha_adapter.py`
  - `app/services/epic_authorization_service.py`
  - `tests/test_hcaptcha_adapter.py`
  - `docs/maintenance-log.md`
- 处理结果：在 request 事件记录 hCaptcha 和登录请求的尝试 generation，response 只接受同一 generation 的已登记请求；迟到或未知响应直接丢弃。邮箱提交、密码重提交和 TOTP 提交均等待对应登录 POST 返回后再推进；非 JSON 响应也会形成完成信号。补充了跨尝试迟到响应和成功覆盖延迟失败的回归用例。已进行静态检查，真实 Epic 登录与入库仍需新的 Actions 运行确认。

### 2026-08-29 修正验证码尝试启动晚于登录和结账点击的竞态

- 现象：验证码响应按 request generation 隔离后，登录提交或结账按钮可能先触发 hCaptcha；调用方要等到 challenge iframe 可见后才启动 response window，期间返回的 `getcaptcha` payload 可能被误判为未登记或过期。
- 根因判断：hCaptcha 的初始化请求发生在 UI 状态轮询之前，不能把“发现可见 challenge”作为尝试起点；Hosted Runner 的异步网络时序会放大这个窗口。
- 改动文件：`app/services/epic_authorization_service.py`、`app/services/epic_games_service.py`、`docs/maintenance-log.md`。
- 处理结果：登录 agent 和 checkout agent 创建后立即登记初始验证码窗口；邮箱 Continue、密码提交、MFA 提交、Place Order 和购物车确认订单均在点击前确保当前 generation active。跨尝试的 request identity/generation 过滤保持不变，避免用放宽过滤来掩盖迟到响应问题。
- 验证边界：已重新执行编译检查和 diff 检查计划；新的线上 Actions 运行尚未触发，因此仍需以登录成功、Store session 和每款游戏的入库证据完成运行时验证。按仓库规则不执行测试。

### 2026-08-29 隔离连续浏览器动作的验证码响应窗口

- 现象：同一个 `AgentV` 在连续邮箱、密码、MFA 或下单动作之间可能保持 active response window；后一动作会复用前一动作的 generation，迟到响应仍可能进入错误的业务阶段。
- 根因判断：响应 generation 需要绑定“浏览器动作”，而不是只绑定 Agent 生命周期；无动作时提前开启窗口还会扩大旧 payload 与新点击之间的关联范围。
- 改动文件：`app/extensions/hcaptcha_adapter.py`、`app/services/epic_authorization_service.py`、`app/services/epic_games_service.py`。
- 处理结果：`begin_captcha_attempt(..., fresh=True)` 为新点击立即轮换 generation 和响应队列；同一动作内由等待器继续复用当前窗口。密码重提交、邮箱 Continue、MFA、Place Order 和购物车最终确认使用 fresh 窗口；移除登录/即时结账/进入购物车结账页时的无动作预启动。
- 验证边界：已执行编译、hCaptcha 协议契约和 diff 检查；按仓库规则未执行测试，仍需新的 Actions 运行确认登录、Store session 与逐款入库。
