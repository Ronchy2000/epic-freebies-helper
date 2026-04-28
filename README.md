# Epic 周免游戏领取助手

<p>
  <a href="https://github.com/Ronchy2000/epic-freebies-helper/actions/workflows/epic-gamer.yml"><img src="https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-freebies-helper/epic-gamer.yml?branch=master&style=flat-square" alt="Workflow Status" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Ronchy2000/epic-freebies-helper?style=flat-square" alt="License" /></a>
  <a href="https://github.com/Ronchy2000/epic-freebies-helper/stargazers"><img src="https://img.shields.io/github/stars/Ronchy2000/epic-freebies-helper?style=flat-square" alt="Stars" /></a>
  <a href="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper"><img src="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper&left_text=views" alt="Views" /></a>
</p>

[中文文档](README.md) | [English](README.en.md)

## 项目说明

本项目用于在 GitHub Actions 中定时运行 Epic 周免游戏领取流程。

默认运行方式为 GitHub Actions。用户不需要准备服务器，也不需要在本地长期运行程序。

主要流程包括：

| 功能 | 说明 |
| --- | --- |
| 登录 Epic 账号 | 使用配置的 Epic 邮箱和密码登录 |
| 获取周免游戏 | 读取当前可领取的 Epic 免费游戏 |
| 处理验证码 | 调用配置的多模态模型处理登录或结账阶段的验证码 |
| 完成领取流程 | 进入商品页并执行领取操作 |
| 定时运行 | 默认由 GitHub Actions 按计划运行 |

## 使用前确认

开始配置前，确认以下条件已经满足：

| 项目 | 要求 |
| --- | --- |
| Epic 账号 | 已有可正常登录的 Epic 账号 |
| Epic 2FA | 当前项目不处理邮箱、短信、验证器二步验证，使用前需要关闭 |
| GitHub 账号 | 用于 Fork 仓库和运行 GitHub Actions |
| 模型接口 | 至少配置一个支持图片输入的模型 provider |
| API Key | 根据选择的 provider 配置对应 API Key |

## 风险说明

> [!WARNING]
> 本项目会自动执行 Epic 登录、验证码处理和领取流程。
>
> 使用前请自行确认该类自动化行为是否符合相关平台服务条款。
>
> 使用本项目产生的账号风控、登录异常、领取失败、API 费用、凭据泄露等后果由使用者自行承担。

## 快速开始

### 1. Fork 仓库并启用 Actions

> [!TIP]
> 如果已经 Fork 过本仓库，先在自己的仓库页面点击 `Sync fork` -> `Update branch`，再继续配置。

1. Fork 本仓库到自己的 GitHub 账号。
2. 打开 Fork 后仓库的 `Actions` 页面。
3. 启用工作流 `Epic Awesome Gamer (Scheduled)`。

### 2. 配置 Secrets

进入 `Settings` -> `Secrets and variables` -> `Actions`，添加以下 Secrets。

#### 必填 Secrets

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `EPIC_EMAIL` | Epic 登录邮箱 | `your_email@example.com` |
| `EPIC_PASSWORD` | Epic 登录密码 | `your_password` |
| `LLM_PROVIDER` | 模型 provider | `glm` |

当前 DeepSeek V4 分支支持的 `LLM_PROVIDER` 值为 `glm`、`deepseek`、`gemini`。

OpenAI / GPT 配置说明保留在 [Provider 配置说明](docs/providers.md) 中。只有在代码已包含 OpenAI provider 时，才应使用
`LLM_PROVIDER=openai`。

#### Provider 配置

按 `LLM_PROVIDER` 的值选择一组配置即可。

| Provider | Secret | 推荐值 | 说明 |
| --- | --- | --- | --- |
| `glm` | `GLM_API_KEY` | - | 智谱 API Key |
| `glm` | `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | 智谱 OpenAI 兼容接口地址 |
| `glm` | `GLM_MODEL` | `glm-4.6v` | 默认推荐模型 |
| `deepseek` | `DEEPSEEK_API_KEY` | - | DeepSeek API Key |
| `deepseek` | `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek OpenAI 兼容接口地址 |
| `deepseek` | `DEEPSEEK_MODEL` | `deepseek-v4-flash` | DeepSeek V4 默认模型 |
| `deepseek` | `DEEPSEEK_THINKING_ENABLED` | `false` | 是否启用 DeepSeek 思考模式 |
| `deepseek` | `DEEPSEEK_REASONING_EFFORT` | `high` | 启用思考模式时的推理强度 |
| `gemini` | `GEMINI_API_KEY` | - | Gemini 或 AiHubMix Key |
| `gemini` | `GEMINI_BASE_URL` | `https://aihubmix.com` | Gemini 兼容接口地址 |
| `gemini` | `GEMINI_MODEL` | `gemini-2.5-pro` | 推荐起步模型 |

说明：

- `GEMINI_BASE_URL` 不要写成 `GEMINI_BASE_MODEL`。
- 使用 `glm` 或 `deepseek` 时不需要额外配置 `GEMINI_API_KEY`。
- `glm-4.6v-flash` 在高峰期可能出现模型繁忙错误，默认建议使用 `glm-4.6v`。
- `deepseek-v4-pro` 可作为 `DEEPSEEK_MODEL` 的替代值。

#### 高级模型覆盖项

以下配置通常不需要填写。留空时会自动使用当前 provider 的默认模型。

| Secret | 说明 |
| --- | --- |
| `CHALLENGE_CLASSIFIER_MODEL` | 验证码类型识别模型 |
| `IMAGE_CLASSIFIER_MODEL` | 图片分类模型 |
| `SPATIAL_POINT_REASONER_MODEL` | 点选类验证码推理模型 |
| `SPATIAL_PATH_REASONER_MODEL` | 拖拽路径类验证码推理模型 |

只有在需要为不同验证码步骤指定不同模型时再填写上述变量。

### 3. 手动运行工作流

1. 进入 `Actions` 页面。
2. 选择 `Epic Awesome Gamer (Scheduled)`。
3. 点击 `Run workflow`。

> [!IMPORTANT]
> 受 Epic 风控机制影响，脚本在验证码及结账环节可能触发多次重试。
>
> 单次运行可能持续 15 到 20 分钟。不要在运行结束前手动取消工作流。

### 4. 查看运行结果

成功时日志通常会出现以下内容：

```text
Login success
Right account validation success
Authentication completed
Starting free games collection process
All week-free games are already in the library
```

示例日志：

![中间报错但最终成功的日志示例](docs/images/tutorial/step4-log-success-with-warnings-1.png)

## 常用配置

常用 provider 配置见 [Provider 配置说明](docs/providers.md)。

本地运行和 Docker 部署见 [本地调试与 Docker 部署](docs/local-debug.md)。

## 运行日志与 Artifact

每次 GitHub Actions 运行结束后，工作流会尝试上传以下 artifact。

| Artifact | 内容 | 出现条件 |
| --- | --- | --- |
| `epic-logs-<run_id>` | 运行日志 | 通常每次运行都会上传 |
| `epic-runtime-<run_id>` | `promotions.json`、`purchase_debug` 截图和文本 | 进入商品页或 checkout 阶段后常见 |
| `epic-screenshots-<run_id>` | 登录失败、风控页、授权页截图 | 登录或授权阶段保存过截图时出现 |

GitHub Actions 只显示实际上传成功且包含文件的 Artifact。不同运行记录中显示的 Artifact 可能不同。

完整说明见 [排障说明](docs/troubleshooting.md)。

## 常见问题

| 日志或现象 | 阶段 | 处理方式 |
| --- | --- | --- |
| `two_factor_authentication.required` | 登录 | 关闭 Epic 邮箱、短信、验证器二步验证后重新运行 |
| 页面跳转到 `/id/login/mfa` | 登录 | 关闭 Epic 2FA |
| `privacy-policy correction` | 登录后跳转 | 使用浏览器手动登录 Epic 并完成隐私政策确认 |
| `One more step` | 结账 | 等待脚本处理，不要立即取消 |
| `Device not supported` | 商品页或结账 | 等待脚本点击 `Continue` |
| 工作流成功但游戏未入库 | 结账 | 下载 Artifact 并提交 Issue |

完整 FAQ 和 Issue 信息要求见 [排障说明](docs/troubleshooting.md)。

## 更多文档

| 文档 | 内容 |
| --- | --- |
| [Provider 配置说明](docs/providers.md) | 模型 provider、模型要求、常见接口错误 |
| [排障说明](docs/troubleshooting.md) | 日志、Artifact、常见问题、Issue 信息 |
| [本地调试与 Docker 部署](docs/local-debug.md) | 本地单次运行、Docker 运行方式 |
| [开发者进阶文档](docs/advanced.md) | 项目结构、适配细节、维护注意事项 |
| [维护日志](docs/maintenance-log.md) | 重要修复、行为调整和文档变更记录 |

## 项目来源与参考

本项目基于 `QIN2DIM/epic-awesome-gamer` 实现，并参考了 `10000ge10000/epic-kiosk`：

| 项目 | 说明 |
| --- | --- |
| [QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer) | 原始项目与核心自动化思路来源 |
| [10000ge10000/epic-kiosk](https://github.com/10000ge10000/epic-kiosk) | GitHub Actions 化和文档组织方式参考 |
| [LINUX DO](https://linux.do/t/topic/2036835/4) | 社区交流与反馈入口 |

## 免责声明

- 本项目仅用于学习和研究自动化流程。
- 自动化操作可能违反相关平台的服务条款，请自行评估风险。
- 使用本项目产生的后果由使用者自行承担。

## Star 趋势

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

## 社区致谢

本项目的持续完善，离不开每一位在遇到报错时没有选择放弃，而是耐心回传完整错误现场的使用者。

许多边界情况的修复，并非源自开发者的独自排查，而是建立在大家主动提供的详实日志、截图与复现步骤之上。正是这些真实的报错数据，让各种隐蔽的问题得以被精准定位并解决。

在此，向所有提供过反馈的用户致以由衷的感谢。是你们投入的时间与提供的测试数据，逐步扫除了开发过程中的盲区，让这个项目日益稳定，切实帮助到了更多人。

<div align="center">
  <sub>感谢每一位提过 issue、上传过 artifact、留下过真实失败案例的朋友。</sub>
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
