# 开发者进阶文档

这份文档面向想继续改项目、提 PR、或者自己二次开发的读者。

语言版本：

- 简体中文（当前页）
- [English](advanced.en.md)

如果你只是想配置并使用项目，请先看：

- [README](../README.md)
- [2026-04-22 开发纪要](development-log-2026-04-22.md)
- [README (English)](../README.en.md)
- [Development Log (English)](development-log-2026-04-22.en.md)

---

## 项目结构

| 文件 | 作用 |
| --- | --- |
| [`app/deploy.py`](../app/deploy.py) | 运行入口，负责浏览器启动、登录、领取和调度 |
| [`app/services/epic_authorization_service.py`](../app/services/epic_authorization_service.py) | 登录、登录结果监听和登录后验证 |
| [`app/services/epic_games_service.py`](../app/services/epic_games_service.py) | 周免发现、商品页进入、加购、结账、checkout 验证处理 |
| [`app/settings.py`](../app/settings.py) | 环境变量、模型路由和默认值 |
| [`app/extensions/llm_adapter.py`](../app/extensions/llm_adapter.py) | Gemini / AiHubMix / GLM 兼容适配 |
| [`.github/workflows/epic-gamer.yml`](../.github/workflows/epic-gamer.yml) | GitHub Actions 工作流入口 |

---

## 本地开发

```bash
uv sync
uv run black . -C -l 100
uv run ruff check --fix
```

说明：

1. 这个仓库当前不建议补跑测试。
2. 改动验证码链路时，优先保留日志和截图。
3. 改动 checkout 流程时，优先保证“未确认成功就不要报成功”。

---

## 这次适配里实际踩过的坑

下面这些不是猜测，都是这次实际遇到并修过的问题。

### 1. GLM 不是简单改个 Base URL 就能用

`hcaptcha-challenger` 内部调用的是 `google-genai` 风格的多模态接口。  
所以接 GLM 时，不能只把 `GEMINI_BASE_URL` 改成智谱地址。

真正要做的是保留上层调用方式，再在适配层里把图片、消息和结构化输出转换成 GLM 能接受的格式。

---

### 2. 不同验证码阶段，题型真的会变

登录阶段和 checkout 阶段的题型不一定一样。

| 阶段 | 题型 |
| --- | --- |
| 登录 | `image_drag_single` |
| checkout | `image_label_multi_select` |

如果适配层只对拖拽题做兼容，结账时就会死在第二道验证上。

---

### 3. GLM 的输出格式并不稳定

这次遇到过的返回形式包括：

| 返回形式 | 说明 |
| --- | --- |
| `Source Position: (...)` | 文本坐标 |
| `{"source": [...], "target": [...]}` | 结构化拖拽坐标 |
| `{"answer":"..."}` | 被包在 `answer` 里的字符串 |
| `image_label_multi_select` | 只返回题型名 |
| 半结构化 JSON | 字段不完整或坏掉的响应 |

所以 [`llm_adapter.py`](../app/extensions/llm_adapter.py) 现在做了很多“解包和转 schema”的兼容。

---

### 3.1 当前项目实际上考虑了哪些验证码类型

目前项目在适配层里明确考虑过这些 challenge type：

| 类型 | 当前状态 | 常见出现阶段 |
| --- | --- | --- |
| `image_drag_single` | 已支持，但仍可能偶发失败 | 登录 |
| `image_drag_multiple` / `image_drag_multi` | 已支持，但稳定性一般 | 登录 / checkout |
| `image_label_binary` | 已支持 | 登录 |
| `image_label_multi_select` | 已支持，但最容易受模型返回结构波动影响 | checkout |
| `image_label_area_select` | 已支持，但对返回框选坐标格式较敏感 | checkout |
| `image_label_multiple_choice` | 已接入题型识别，但真实样本相对少 | 登录 / checkout |

另外，项目里还有一类明确绕开的题目：

| 特殊题目 | 当前策略 |
| --- | --- |
| `Please drag the crossing to complete the lines` | 明确加入忽略列表，不作为当前稳定支持对象 |

也就是说，项目当前不是“所有验证码都能稳定通过”，而是“常见题型尽量兼容，特殊题型或结构漂移严重的返回继续按 artifact 修”。

### 3.2 为什么有些验证码还是过不去

从已经修过的 case 看，失败通常不是一个单点原因，而是下面几类问题叠加：

| 失败来源 | 具体表现 |
| --- | --- |
| 题型识别不稳 | router 只回一个题型名，或者题型名有别名 |
| 模型返回结构漂移 | 只返回 `answer`、只返回裸字符串、字段缺失、坐标格式变化 |
| checkout 验证比登录更复杂 | 登录能过，不代表结账二次验证也能过 |
| 页面状态切换太快 | challenge frame 消失、按钮短暂变化、Playwright 观察窗口错过状态 |
| Epic / hCaptcha 风控变化 | 同一账号、同一题型，不同时段结果也可能不同 |

所以当前项目的真实目标不是“绝对 100% 通过所有验证码”，而是：

1. 尽量覆盖常见题型。
2. 返回结构变了时优先在 [`llm_adapter.py`](../app/extensions/llm_adapter.py) 里修兼容。
3. 页面流程变了时优先在 [`epic_games_service.py`](../app/services/epic_games_service.py) 里补状态识别。
4. 每次失败都留下足够 artifact，支撑下一轮修复。

---

### 4. Epic checkout 不只会弹 hCaptcha

这次已经确认过，结账过程中可能出现下面这些状态：

| 场景 | 是否遇到过 |
| --- | --- |
| `Device not supported` | 是 |
| `One more step` | 是 |
| 额外的 checkout iframe | 是 |
| 页面仍停留在 `Place Order` | 是 |

因此 [`epic_games_service.py`](../app/services/epic_games_service.py) 现在做了这些事：

1. 检查设备不支持弹窗并尝试继续。
2. 识别 checkout 安全校验。
3. 在 `Place Order` 后循环观察真实结果。
4. 没确认成功就不误报成功。

---

### 5. “已拥有”判断不能扫整页文本

曾经误把页面里的版权文本 `owned by ...` 当成了“已拥有”。

后来修正成：

1. 优先看按钮和 checkout 状态。
2. 只识别高精度成功文案。

---

### 6. Artifact 非常重要

真正把问题定位清楚，靠的不只是控制台日志，还包括：

| 文件 | 作用 |
| --- | --- |
| `epic-logs-<run_id>` 解压后的日志文件 | 看完整执行链路 |
| `epic-runtime-<run_id>` 解压后的 `purchase_debug/*.png` | 如果存在，看商品页或 checkout 实际长什么样 |
| `epic-runtime-<run_id>` 解压后的 `purchase_debug/*.txt` | 如果存在，看商品页文本和 frame 内容 |
| `epic-screenshots-<run_id>` 解压后的截图 | 如果存在，看登录、风控或授权阶段的页面状态 |

`epic-runtime` 和 `epic-screenshots` 不一定同时出现。工作流会尝试上传它们，但 GitHub 只显示实际有文件的 artifact。没有进入商品页时可能没有 `runtime`；没有保存登录/风控截图时可能没有 `screenshots`。

---

## 2026-04-24 多用户反馈后的鲁棒性方案

这轮问题来自多组真实用户 artifact，不是单个偶发异常。分析时不要只看最后一行 traceback，要同时看：

1. `runtime.log` 里的最后一个业务动作。
2. `error.log` 里的 Playwright / hCaptcha 异常类型。
3. `purchase_debug/*.png` 里页面是否已经出现按钮、iframe、弹窗或成功确认。
4. `purchase_debug/*.txt` 里的主页面文本和 frame 文本。

### 失败模式归类

| 现象 | 日志特征 | 技术判断 | 处理方向 |
| --- | --- | --- | --- |
| 登录连续失败 | `Timed out waiting for Epic login outcome`、`btoa is read-only`、`Challenge execution timed out` | hCaptcha 仍在页面上，或页面状态被上一轮求解污染 | 登录挑战分段重试；失败后重建页面并清 cookie |
| 商品页打开失败 | `Page.goto: Timeout 30000ms exceeded` | 页面主体可能已可用，但 `load` 被图片、脚本或第三方资源拖住 | 改成 `domcontentloaded`；允许部分加载后继续 |
| `Get` 按钮点击卡死 | `Locator.click: Timeout 10000ms exceeded`，截图里按钮可见 | Playwright 等待点击动作完成，但页面没有按预期返回 | 点击策略改成标准点击、dispatch、DOM click、坐标点击、force click 分层兜底 |
| checkout 已推进但未确认 | 页面停留在 `Place Order` 或安全验证 | 点击成功不等于领取成功 | 必须继续观察订单确认、按钮状态、checkout iframe 和订单历史 |
| 配置带换行 | 日志里模型名类似 `glm-4.6v\n` | GitHub Secrets 或用户复制配置时带入空白字符 | settings 层统一 `strip()` 字符串配置 |

### 当前采用的设计原则

1. **不要把单次 Playwright 超时等同于业务失败**  
   浏览器自动化里，`click()` 超时可能只是动作等待条件没有满足。只要页面已经出现 checkout iframe、安全校验、成功文案或按钮状态变化，就应该进入下一阶段观察，而不是直接抛异常。

2. **领取链路按阶段隔离重试**  
   登录、商品页进入、购买按钮点击、checkout 下单、hCaptcha 求解、最终确认是不同故障点。一个阶段失败时，只重置这个阶段必要的状态，避免整轮流程被无关状态拖垮。

3. **成功必须高置信确认**  
   不再因为点击返回、页面跳转、或扫到宽泛文本就报成功。成功信号优先级应接近：

   | 优先级 | 信号 |
   | --- | --- |
   | 高 | `Thanks for your order` + `Order number` |
   | 高 | 订单历史里出现对应 namespace / offerId |
   | 中 | 按钮变成 `In Library` / `Owned` / `View in Library` |
   | 低 | 页面正文里的泛化文本 |

4. **失败必须留下 artifact**  
   商品页打不开、按钮找不到、点击无效、checkout 未确认，都要保存截图和文本。后续修复应基于 artifact 归类，而不是在代码里继续猜新选择器。

### 修复落点

| 文件 | 方案 |
| --- | --- |
| [`app/services/epic_authorization_service.py`](../app/services/epic_authorization_service.py) | 登录阶段识别可见 hCaptcha；登录结果等待超时后，如果验证码仍在，继续求解；单次登录失败后重建页面并清 cookie |
| [`app/services/epic_games_service.py`](../app/services/epic_games_service.py) | 商品页导航改成可恢复加载；购买按钮点击改成多策略兜底；点击后以页面进展判断是否进入下一阶段 |
| [`app/settings.py`](../app/settings.py) | 对模型名、Base URL、Provider、账号等字符串配置统一去除首尾空白 |

### 后续排障流程

后续再收到类似反馈时，建议按下面顺序处理：

1. 先确认失败属于登录、商品页、按钮点击、checkout、安全验证、最终确认里的哪一段。
2. 对照 `purchase_debug` 截图判断页面实际状态，不要只看 traceback。
3. 如果页面已经推进到下一阶段，优先补“状态识别”和“确认逻辑”，不要只加更长 timeout。
4. 如果是新文案或新弹窗，先把文案加入高精度判断，再加截图保存点。
5. 如果是模型输出结构变化，优先修 [`llm_adapter.py`](../app/extensions/llm_adapter.py) 的归一化，不要把 provider 特殊逻辑散进业务流程。

这类项目无法承诺绝对 100% 成功率，因为 Epic 风控、共享云 IP、验证码题型和第三方模型响应都不可控。代码层面的目标应该是：可恢复、可观测、不错报成功，并且每次失败都能留下足够证据支撑下一轮修复。

---

## 维护建议

如果你继续维护这个项目，优先关注下面几类变化：

1. Epic 登录页是否更换验证码类型。
2. 商品页按钮文案是否变化。
3. checkout iframe 和 `Place Order` 行为是否变化。
4. GLM / Gemini 的响应格式是否变化。
5. GitHub Actions 运行环境是否变化。
