# 2026-04-22 开发纪要

这份文档是从原始 Codex 会话提取出来的开发纪要，目的是把一整天的排障、修复和文档整理过程压缩成可读版本。

语言版本：

- 简体中文（当前页）
- [English](development-log-2026-04-22.en.md)

原始记录仍然保留在仓库里：

- [`codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl`](../codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl)

说明：

- 这条原始会话对应的旧工作目录是 `/Users/ronchy2000/Documents/Developer/Workshop/epic-freebies-helper`
- 当前仓库目录已经改名为 `epic-freebies-helper`
- 下面的内容是提炼后的开发纪要，不是逐行聊天转录

---

## 背景

这轮开发集中发生在 2026 年 4 月 22 日，目标不是单点修补，而是把项目从“依赖 Gemini 和第三方 API 的可用仓库”扩展成一套更适合当前仓库定位的方案：

1. 增加 `GLM` 兼容能力，并保持配置方式与现有 Provider 尽量一致。
2. 优先支持 `GitHub Actions` 的实际运行场景，而不是只做本地推导。
3. 围绕 Epic 领取流程里最不稳定的几段链路，持续做真实日志驱动的修复。
4. 把文档重写成“普通用户先跑通，开发者再深入”的结构。

---

## 主要结论

这次开发最终收敛出了几条很明确的经验：

- `GLM` 接入不是简单改 `base_url`，而是要兼容 `hcaptcha-challenger` 依赖的上层调用方式。
- 真正难的不是“发出请求”，而是把 `GLM` 在不同验证码题型下返回的非稳定结果转成 challenger 期望的结构。
- Epic 的领取链路里，登录验证码、商品页 `Get`、`Device not supported`、checkout 二次安全校验、`Place Order` 之后的确认结果，都是独立故障点。
- 只看控制台日志不够，GitHub Actions artifact 对定位 checkout 问题是关键。
- 文档层面，README 和开发者文档必须拆开，否则普通用户和维护者都会被长文打断。

---

## 时间线

### 1. 先完成 GLM 接入

一开始先做的是 Provider 兼容层扩展，核心目标是让仓库可以在原有配置风格下使用 `GLM` 识别验证码。

相关提交：

- `b6e5ded` `feat: add glm support for captcha solver`

这一步只是起点，后面的大部分问题都发生在“接入能跑起来，但请求、模型名、返回格式和实际页面流程并不稳定”。

### 2. 修配置默认值和模型选择

很快遇到的是 GitHub Actions 环境变量覆盖问题。因为 workflow 里未配置的 secret 可能以空字符串进入环境，导致默认 `GLM_BASE_URL` 和 `GLM_MODEL` 没有正确回退。

随后又确认了另一层问题：

- `GLM` 已经启用，但验证码子模型默认值仍可能错误兜底到 `GEMINI_MODEL`
- 这会让请求打到智谱接口时出现“模型不存在”

相关提交：

- `fcbd5b0` 修空字符串覆盖默认值
- `6cd05ed` 修 `LLM_PROVIDER=glm` 时的模型默认继承

### 3. 修 GLM 请求体和返回格式兼容

配置层修好后，问题转移到接口兼容本身：

- 图片字段格式不符合 `GLM` OpenAI 兼容接口要求
- `GLM` 返回内容并不总是稳定 JSON
- 不同题型会混合出现文本坐标、`source/target`、包在 `answer` 里的字符串、甚至只返回题型名

这一段是会话里修得最密集的部分，目标是把 `GLM` 的不稳定输出尽量统一转成 challenger 需要的 schema。

相关提交：

- `ed21177` 修 `GLM` 请求体图片格式，并增强错误日志
- `5f4aca1` 兼容拖拽/点选文本坐标输出
- `8ece3bd` 把 `source/target` 或 `from/to` 映射成 `paths`
- `94b1c64` 强制结构化响应格式，并增加原始文本 fallback 日志
- `0b1e5ab` 解包 `answer` 字段，兼容字符串、数组、对象和裸坐标
- `fb801ef` 兼容只返回题型名和点选 schema 的情况

### 4. 把排障重点转到 Epic 页面流程

当登录和基础求解开始变得可用后，瓶颈就从“调用模型失败”转成了“Epic 页面实际怎么领”。

这部分逐步暴露出几个独立问题：

- 商品页主按钮上下文识别不够，可能误把不可领状态当成可点击状态
- `Get` 后会出现 `Device not supported`
- checkout 阶段可能弹出 `One more step` 二次安全校验
- 安全校验可能藏在 iframe 里，不是主页面直接可见
- `Place Order` 之后即使出现过校验，也不代表订单已经真正完成

相关提交：

- `4124639` 增强商品页按钮上下文日志、截图和点击兜底
- `36332bb` 上传 artifact，并保存 checkout 失败时的截图和文本
- `38c3e5a` 自动处理 `Device not supported`
- `c8291a1` 轮询确认领取结果，避免“未确认成功却报成功”，并顺手处理 Node 24 警告
- `87b32a5` 修正“整页文本误命中 `owned by ...` 导致误判已拥有”
- `3c8a9b1` 显式识别 `One more step` checkout 安全校验并进入求解循环
- `ac3684c` 把校验检测扩展到主页面和 iframe
- `ea9ae2a` 把 `Place Order` 后流程改成明确的提交周期和重新观察

### 5. 文档重写和仓库定位收束

功能和排障链路稳定后，后半段工作转到文档和项目命名整理。

这部分做了两件事：

1. 把 README 改成更适合普通用户上手的首页。
2. 把开发者内容拆进 `docs/advanced.md`，不再和首页混写。

最后围绕项目名和仓库名做了收束，形成了“`Epic 周免助手` + `epic-freebies-helper`”这套最终方向。

相关提交：

- `95940e1` README 首次按“用户优先”重构
- `3379fa7` 收紧 README 结构
- `f4377c4` 拆出独立开发者进阶文档
- `93563c6` 优化首页观感、命名和致谢
- `4d27845` 收紧 README 首屏定位
- `1855c96` 最终确认 `Epic 周免助手` / `epic-freebies-helper`

---

## 这轮开发里真正解决了什么

如果只看结果，这次会话一共把下面几类问题推进到了可维护状态：

### GLM 接入

- 新增了 `GLM` 作为可选 Provider
- 兼容了 `GLM` 默认地址、模型配置和 GitHub Actions secret 回退
- 让验证码子模型在 `LLM_PROVIDER=glm` 时默认跟随 `GLM_MODEL`

### 验证码求解兼容

- 兼容了拖拽题和点选题
- 兼容了 `GLM` 多种非稳定输出格式
- 增加了更多结构化 fallback 和原始返回日志

### Epic 领取流程

- 增加商品页按钮上下文记录
- 增加失败截图和页面文本保存
- 处理 `Device not supported`
- 处理 checkout 二次安全校验
- 改善 `Place Order` 后的提交和观察节奏
- 修掉“未确认成功却误报成功”的问题

### GitHub Actions 运行体验

- 增加 artifact 上传，便于下载 runtime 和 logs
- 顺手处理了 Node 20 弃用带来的 Node 24 警告

### 文档结构

- README 改成面向普通用户
- `docs/advanced.md` 改成面向开发者
- 项目名称、推荐模型和部署方式表达更一致

---

## 开发方法上的经验

这条会话很典型地体现了这个仓库后续维护应该怎么做：

1. 不要只盯着模型接口，要把“模型输出格式”和“Epic 页面状态机”分开看。
2. 一旦进入 checkout 问题，优先看 artifact，不要只靠控制台日志猜。
3. 对“已拥有”“已领取成功”这类状态，必须使用高精度判断，不能扫整页模糊文本。
4. 对 GitHub Actions 场景，默认要考虑空字符串 env、Linux runner 平台限制、Node 版本警告这类平台问题。
5. 文档不要和排障记录混在首页；首页负责上手，进阶文档负责维护。

---

## 关键提交清单

| 提交 | 作用 |
| --- | --- |
| `b6e5ded` | 初始 GLM 兼容接入 |
| `fcbd5b0` | 修默认值被空 secret 覆盖 |
| `ed21177` | 修图片请求格式并增强 GLM 错误日志 |
| `6cd05ed` | 修 `glm` provider 下子模型默认值 |
| `5f4aca1` | 兼容文本坐标输出 |
| `8ece3bd` | 把 `source/target` 转成 `paths` |
| `4124639` | 增强商品页按钮日志、截图和点击兜底 |
| `36332bb` | 保存 debug 文件并上传 artifact |
| `38c3e5a` | 自动处理 `Device not supported` |
| `c8291a1` | 收紧领取结果确认，避免误报成功 |
| `87b32a5` | 修“owned by ...”误判已拥有 |
| `3c8a9b1` | 显式处理 checkout `One more step` |
| `ac3684c` | 扩展到 iframe 内安全校验检测 |
| `ea9ae2a` | 重构 `Place Order` 后的提交周期 |
| `94b1c64` | 增加结构化响应和 parse fallback 日志 |
| `0b1e5ab` | 解包 `answer` 并兼容更多拖拽返回格式 |
| `fb801ef` | 兼容题型名和点选 schema |
| `95940e1` | README 首次重构 |
| `f4377c4` | 拆出 `docs/advanced.md` |
| `1855c96` | 最终收束项目名和 README 首屏定位 |

---

## 现在这份纪要和原始记录的关系

如果你要快速理解这次开发过程，看这份文档就够。

如果你要做更细的事情，比如：

- 回看某一次日志到底触发了什么判断
- 查某一轮修复前后的原话
- 重新提取更完整的聊天纪要或 changelog

再去看原始文件：

- [`codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl`](../codex-records/epic-awesome-gamer-rollout-2026-04-22.jsonl)
