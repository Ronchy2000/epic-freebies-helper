# Epic 周免助手

An Epic Games weekly-freebies claimer for GitHub Actions.

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-awesome-gamer/epic-gamer.yml?branch=master&style=flat-square)](https://github.com/Ronchy2000/epic-awesome-gamer/actions/workflows/epic-gamer.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Ronchy2000/epic-awesome-gamer?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/Ronchy2000/epic-awesome-gamer?style=flat-square)](https://github.com/Ronchy2000/epic-awesome-gamer/stargazers)

一个面向普通用户的 Epic 周免自动领取项目，最佳使用方式是直接跑在 GitHub Actions 上。

很多同类项目会优先使用 Google AI Studio 的 Gemini API，或者通过 AiHubMix 中转模型能力；这个项目更推荐直接使用 `GLM`。原因很简单：`glm-4.6v-flash` 是智谱官方免费视觉模型，如果你想尽量做到 `0` 成本上手，直接用它最合适；如果你账号里有新用户赠送额度，`glm-4.5v` 也通常足够把登录、验证码和领取流程跑通。

还没有智谱账号的话，可以直接通过这个邀请链接注册：[BigModel.cn 邀请注册链接](https://www.bigmodel.cn/invite?icode=A75tQCByIvrO4k6SLkU5BQZ3c5owLmCCcMQXWcJRS8E%3D)。

---

## 功能概览

| 功能 | 说明 |
| --- | --- |
| 自动登录 | 自动完成 Epic 账号登录 |
| 自动发现周免 | 拉取并识别当周可领取游戏 |
| 自动领取 | 自动进入商品页并完成结账流程 |
| 验证码处理 | 支持登录验证码和 checkout 二次安全校验 |
| 定时执行 | 可直接使用 GitHub Actions 定时运行 |

默认最推荐的运行方式是 GitHub Actions，因为它不需要自己开电脑挂机，仓库也已经带好了可直接使用的工作流。

---

## 为什么推荐 GLM

如果你是第一次接触这类项目，最推荐直接使用 GLM。

| 原因 | 说明 |
| --- | --- |
| 门槛最低 | 只需要配置 `GLM_API_KEY` 和 `GLM_MODEL`，默认值已经帮你兜好 |
| 免费路线最清晰 | 智谱官方提供免费视觉模型 [`glm-4.6v-flash`](https://docs.bigmodel.cn/cn/guide/models/free/glm-4.6v-flash)，直接可用 |
| 新人更容易跑通 | 如果你有新用户赠送额度，`glm-4.5v` 通常也足够跑通周免流程 |
| 比 Gemini 路线更省心 | 不用额外折腾 Gemini 的地区、配额和账号环境问题 |
| 比中转方案更直接 | 直接对接智谱官方接口，配置简单，排障路径也更清楚 |
| 能力够用 | 可以直接处理登录验证码和 checkout 二次验证 |
| 适配已经打通 | 当前仓库已经针对 GLM 的拖拽题、点选题和多选题做了兼容 |

如果你只是想尽快跑通一次周免领取，优先从 GLM 开始通常是最省心的选择。

---

## 使用前先确认

| 项目 | 是否必须 | 说明 |
| --- | --- | --- |
| Epic 账号邮箱 | 是 | 用来登录 Epic |
| Epic 账号密码 | 是 | 用来登录 Epic |
| 关闭 2FA | 是 | 必须关闭邮箱 / 短信 / App 二次验证 |
| 多模态模型 API Key | 是 | 用来识别 hCaptcha |

这个项目运行在无头自动化环境里。  
如果账号开启了邮箱验证码、短信验证码、验证器 App 等二次验证，流程通常会被卡住。

---

## 🚀 快速开始

### 1. Fork 仓库

把这个仓库 Fork 到你自己的 GitHub 账号下。

建议 Fork 完后立刻改成私有仓库，这样更适合保存自己的 Actions 配置，也更不容易误暴露运行记录。

### 2. 启用 GitHub Actions

进入你自己的 Fork 仓库后：

1. 打开 `Actions`
2. 如果 GitHub 提示是否启用工作流，点击启用

工作流名称是 `Epic Awesome Gamer (Scheduled)`，默认每天执行一次，也支持手动触发。

### 3. 配置 Secrets

进入 `Settings` -> `Secrets and variables` -> `Actions`。

#### 推荐配置：GLM

| Secret | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `EPIC_EMAIL` | 是 | `you@example.com` | Epic 登录邮箱 |
| `EPIC_PASSWORD` | 是 | `your-password` | Epic 登录密码 |
| `LLM_PROVIDER` | 是 | `glm` | 明确指定使用 GLM |
| `GLM_API_KEY` | 是 | `xxxxxxxx` | 智谱 API Key |
| `GLM_MODEL` | 是 | `glm-4.6v-flash` | 视觉模型名 |
| `GLM_BASE_URL` | 否 | `https://open.bigmodel.cn/api/paas/v4` | 不填就走默认值 |
| `CHALLENGE_CLASSIFIER_MODEL` | 否 | 留空 | 留空时跟随 `GLM_MODEL` |
| `IMAGE_CLASSIFIER_MODEL` | 否 | 留空 | 留空时跟随 `GLM_MODEL` |
| `SPATIAL_POINT_REASONER_MODEL` | 否 | 留空 | 留空时跟随 `GLM_MODEL` |
| `SPATIAL_PATH_REASONER_MODEL` | 否 | 留空 | 留空时跟随 `GLM_MODEL` |

最小可用配置如下：

```text
EPIC_EMAIL=你的 Epic 邮箱
EPIC_PASSWORD=你的 Epic 密码
LLM_PROVIDER=glm
GLM_API_KEY=你的智谱 API Key
GLM_MODEL=glm-4.6v-flash
```

如果你不知道该填哪个模型，直接从 `glm-4.6v-flash` 开始即可。

#### 可选配置：Gemini / AiHubMix

| Secret | 必填 | 示例 | 说明 |
| --- | --- | --- | --- |
| `EPIC_EMAIL` | 是 | `you@example.com` | Epic 登录邮箱 |
| `EPIC_PASSWORD` | 是 | `your-password` | Epic 登录密码 |
| `LLM_PROVIDER` | 建议 | `gemini` | 建议显式指定 |
| `GEMINI_API_KEY` | 是 | `xxxxxxxx` | Gemini 或 AiHubMix Key |
| `GEMINI_BASE_URL` | 否 | `https://aihubmix.com` | 不填就走默认值 |
| `GEMINI_MODEL` | 否 | `gemini-2.5-pro` | 不填就走默认值 |

### 4. 手动运行一次

进入 `Actions` 页面后：

1. 选择 `Epic Awesome Gamer (Scheduled)`
2. 点击 `Run workflow`
3. 等待运行完成

第一次手动跑的目的很明确：先确认 Secrets 配对正确、Epic 账号可以正常登录、模型也确实能识别当前验证码。

### 5. 确认结果

如果领取成功，常见日志通常会接近下面这种状态：

```text
Login success
Right account validation success
Authentication completed
Starting free games collection process
All week-free games are already in the library
```

---

## 运行日志与 Artifact

每次 GitHub Actions 运行结束后，工作流会自动上传两个 artifact：

| Artifact | 内容 |
| --- | --- |
| `epic-runtime-<run_id>` | 运行期截图、debug 文本、purchase_debug |
| `epic-logs-<run_id>` | 运行日志 |

下载位置：

1. 进入本次 Actions 运行页面
2. 拉到页面底部
3. 找到 `Artifacts`
4. 下载 zip 文件

下载后建议先看下面两个目录：

| 目录 | 用途 |
| --- | --- |
| `app/volumes/runtime/purchase_debug/` | 看页面截图和中间状态 |
| `app/volumes/logs/` | 看完整运行日志 |

---

## 常见问题

### 1. 登录偶尔失败，一次成功一次失败

这是正常现象之一。GitHub Actions 使用的是共享云 IP，Epic 对风控比较敏感。常见表现包括登录页验证码一次过、一次不过，偶发 `captcha_invalid`，或者同一个账号隔一会儿又能成功。

### 2. 页面弹出 `One more step`

这不是异常，是 Epic 结账阶段追加的人机校验。

现在项目已经能处理这类二次安全验证。你看到下面这种弹窗，不代表脚本坏了：

![Checkout Security Check](docs/images/checkout-security-check.png)

### 3. 页面提示 `Device not supported`

这个提示通常出现在商品只支持 Windows，而 GitHub Actions 运行环境是 Linux 的时候。

### 4. 为什么工作流显示成功，但游戏没入库

过去常见根因有：

| 原因 | 说明 |
| --- | --- |
| 商品页状态识别不准 | 页面文案和实际状态不一致 |
| `Place Order` 已点击但未完成 | 结账页仍停留在二次验证 |
| 页面出现额外弹窗 | 例如设备不支持、额外确认 |
| 旧逻辑误判 | 曾经把普通文案误判成“已拥有” |

### 5. 为什么日志里会看到 `btoa is read-only`

这是 `hcaptcha-challenger` 在某些页面注入 HSW 脚本时的兼容性噪声。  
它不一定会导致本次运行失败。

---

## Docker 部署

如果你不想用 GitHub Actions，也可以在自己的服务器、NAS 或本地 Docker 环境里跑。

### 1. 克隆仓库

```bash
git clone https://github.com/Ronchy2000/epic-awesome-gamer.git
cd epic-awesome-gamer
```

### 2. 修改配置

主要入口是 [`docker/docker-compose.yaml`](docker/docker-compose.yaml)。

GLM 示例：

```yaml
environment:
  - LLM_PROVIDER=glm
  - GLM_API_KEY=your_glm_key
  - GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
  - GLM_MODEL=glm-4.6v-flash
```

Gemini / AiHubMix 示例：

```yaml
environment:
  - LLM_PROVIDER=gemini
  - GEMINI_API_KEY=your_key
  - GEMINI_BASE_URL=https://aihubmix.com
  - GEMINI_MODEL=gemini-2.5-pro
```

### 3. 启动

```bash
docker compose up -d --build
```

---

## 进阶文档

如果你想看项目结构、适配细节、开发者排障记录和这次踩过的坑，请继续阅读：

- [开发者进阶文档](docs/advanced.md)

---

## 致谢

这个项目的实现和整理，直接受到了下面两个仓库的启发：

| 项目 | 说明 |
| --- | --- |
| [QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer) | 原始项目与核心自动化思路来源 |
| [10000ge10000/epic-kiosk](https://github.com/10000ge10000/epic-kiosk) | GitHub Actions 化和文档组织方式的重要参考 |

感谢原作者和维护者的工作。

---

## 免责声明

- 本项目仅用于学习和研究自动化流程。
- 自动化操作可能违反相关平台的服务条款，请自行评估风险。
- 使用本项目产生的后果由使用者自行承担。
