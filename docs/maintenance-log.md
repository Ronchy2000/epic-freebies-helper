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
