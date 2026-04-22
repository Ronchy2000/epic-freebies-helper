<div align="center">
  <h1>Epic 周免助手</h1>
  <p>An Epic Games weekly-freebies claimer for GitHub Actions.</p>

  <p>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/actions/workflows/epic-gamer.yml"><img src="https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-freebies-helper/epic-gamer.yml?branch=master&style=flat-square" alt="Workflow Status" /></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/Ronchy2000/epic-freebies-helper?style=flat-square" alt="License" /></a>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/stargazers"><img src="https://img.shields.io/github/stars/Ronchy2000/epic-freebies-helper?style=flat-square" alt="Stars" /></a>
    <a href="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper"><img src="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper&left_text=views" alt="Views" /></a>
  </p>
</div>

面向普通用户的 Epic 周免自动领取项目，默认通过 GitHub Actions 运行，不需要服务器或本地常驻环境；只要有 GitHub 账号，就可以直接开始。

本项目基于社区开源方案持续完善，并接入了国产 `GLM` 多模态模型。实测可稳定处理登录、验证码和领取流程；对于不方便注册 Google AI Studio、难以使用 Gemini API 的用户，GLM 路线更省心，`0` 成本即可跑通。

还没有智谱账号的话，可以通过这个邀请链接注册：[BigModel.cn 邀请注册链接](https://www.bigmodel.cn/invite?icode=A75tQCByIvrO4k6SLkU5BQZ3c5owLmCCcMQXWcJRS8E%3D)。

---

## 功能概览

| 功能 | 说明 |
| --- | --- |
| 自动登录 | 自动完成 Epic 账号登录 |
| 自动发现周免 | 拉取并识别当周可领取游戏 |
| 自动领取 | 自动进入商品页并完成结账流程 |
| 验证码处理 | 支持登录验证码和 checkout 二次安全校验 |
| 定时执行 | 可直接使用 GitHub Actions 定时运行 |

推荐运行方式是 GitHub Actions，因为它不需要自己开电脑挂机，仓库也已经带好了可直接使用的工作流。

---

## 为什么推荐 GLM

如果你是第一次接触这类项目，直接从 GLM 开始会更容易跑通。核心原因很简单：

- 配置更少：主要只要设置 `GLM_API_KEY` 和 `GLM_MODEL`。
- 成本更低：`glm-4.6v-flash` 和 `glm-4.5v` 的免费额度足够覆盖周免领取场景。
- 对国内用户更友好：不需要先解决 Google AI Studio 注册和可用性问题。
- 能力已验证：登录验证码、checkout 二次验证、拖拽/点选/多选题都能正常处理。

---

## 使用前先确认

- Epic 账号邮箱与密码（用于登录）。
- 关闭 Epic 账号 2FA（邮箱/短信/验证器）。
- 注册 GLM 并准备 `GLM_API_KEY`（用于验证码识别）。

这个项目运行在无头自动化环境里。  
如果账号开启了邮箱验证码、短信验证码、验证器 App 等二次验证，流程通常会被卡住。

---

## 🚀 快速开始

只做下面 4 步，通常 10 分钟内就能完成首次验证。

### 1. Fork 并启用 Actions

- Fork 到自己的 GitHub 账号，建议改为私有仓库。
- 打开 `Actions`，启用工作流 `Epic Awesome Gamer (Scheduled)`。

### 2. 配置 Secrets

进入 `Settings` -> `Secrets and variables` -> `Actions`，先填这 5 个：

| Secret | 示例值 |
| --- | --- |
| `EPIC_EMAIL` | 你的 Epic 邮箱 |
| `EPIC_PASSWORD` | 你的 Epic 密码 |
| `LLM_PROVIDER` | glm |
| `GLM_API_KEY` | 你的智谱 API Key |
| `GLM_MODEL` | glm-4.6v-flash |

配置页面示例：

![GitHub Actions Secrets 配置示例](docs/images/tutorial/step2-actions-secrets.png)

可选项：

- `GLM_BASE_URL` 留空即可使用默认值。
- `CHALLENGE_CLASSIFIER_MODEL`、`IMAGE_CLASSIFIER_MODEL`、`SPATIAL_POINT_REASONER_MODEL`、`SPATIAL_PATH_REASONER_MODEL` 留空即可跟随 `GLM_MODEL`。
- 如果要改 Gemini 路线，把 `LLM_PROVIDER` 设为 `gemini` 并配置 `GEMINI_API_KEY`。

### 3. 手动运行一次

- 进入 `Actions` 页面。
- 选择 `Epic Awesome Gamer (Scheduled)`。
- 点击 `Run workflow`。

### 4. 看日志确认是否跑通

成功时日志通常会出现类似内容：

```text
Login success
Right account validation success
Authentication completed
Starting free games collection process
All week-free games are already in the library
```

说明：流程中间偶尔会看到报错（例如 `wait for captcha response timeout` 或 `btoa is read-only`），这在当前场景下可能是正常噪声；只要最后出现成功日志并正常结束，就可以视为本次执行成功。

示例日志（中间有报错但最终成功）：

![中间报错但最终成功的日志示例 1](docs/images/tutorial/step4-log-success-with-warnings-1.png)

![中间报错但最终成功的日志示例 2](docs/images/tutorial/step4-log-success-with-warnings-2.png)

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

![Checkout Security Check](docs/images/faq/checkout-security-check.png)

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
git clone https://github.com/Ronchy2000/epic-freebies-helper.git
cd epic-freebies-helper
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

本项目基于 `QIN2DIM/epic-awesome-gamer` 实现，并参考了 `10000ge10000/epic-kiosk`：

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

---

## Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=Ronchy2000/epic-freebies-helper&type=Date)](https://star-history.com/#Ronchy2000/epic-freebies-helper&Date)
