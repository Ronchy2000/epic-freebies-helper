<div align="center">
  <h1>Epic 周免领取助手</h1>
  <p>An Epic Games weekly-freebies claimer for GitHub Actions.</p>

  <p>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/actions/workflows/epic-gamer.yml"><img src="https://img.shields.io/github/actions/workflow/status/Ronchy2000/epic-freebies-helper/epic-gamer.yml?branch=master&style=flat-square" alt="Workflow Status" /></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue?style=flat-square" alt="Python" /></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/Ronchy2000/epic-freebies-helper?style=flat-square" alt="License" /></a>
    <a href="https://github.com/Ronchy2000/epic-freebies-helper/stargazers"><img src="https://img.shields.io/github/stars/Ronchy2000/epic-freebies-helper?style=flat-square" alt="Stars" /></a>
    <a href="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper"><img src="https://visitor-badge.laobi.icu/badge?page_id=Ronchy2000.epic-freebies-helper&left_text=views" alt="Views" /></a>
  </p>
</div>

[🇨🇳 中文文档](README.md) | [🇺🇸 English](README.en.md)

面向普通用户的 Epic 周免自动领取项目，默认通过 GitHub Actions 运行，不需要服务器或本地常驻环境；只要有 GitHub 账号，就可以直接开始。

完全免费。  
用 GitHub Actions 就能自动领取 Epic 周免，不需要服务器，不需要本地挂机。

本项目基于社区开源方案持续完善，并接入了国产 `GLM` 多模态模型。实测可稳定处理登录、验证码和领取流程；对于不方便注册 Google AI Studio、难以使用 Gemini API 的用户，GLM 路线更省心，`0` 成本即可跑通。

**如果你选择 `GLM` 路线，请先确认对应智谱账号已经完成实名认证，否则通常无法正常使用 API。**

还没有智谱账号的话，可以通过这个邀请链接注册：[BigModel.cn 邀请注册链接](https://www.bigmodel.cn/invite?icode=A75tQCByIvrO4k6SLkU5BQZ3c5owLmCCcMQXWcJRS8E%3D)。

社区交流与反馈欢迎前往：[LINUX DO](https://linux.do/t/topic/2036835/4)。

如果你已经成功跑通，也欢迎来这里留言打卡：[🎉 成功反馈 / Success Stories](https://github.com/Ronchy2000/epic-freebies-helper/discussions/3)。

如果你遇到报错，也欢迎直接提 [Issue](https://github.com/Ronchy2000/epic-freebies-helper/issues)。当然，是否继续使用完全由你决定；但如果你愿意留下反馈，而不是直接删库放弃，这些真实问题和使用体验，都会帮助这个项目继续改进，也会成为我们一起把它做得更稳的动力。

---

## 功能概览

| 功能 | 说明 |
| --- | --- |
| 自动登录 | 自动完成 Epic 账号登录 |
| 自动发现周免 | 拉取并识别当周可领取游戏 |
| 自动领取 | 自动进入商品页并完成结账流程 |
| 验证码处理 | 支持登录验证码和 checkout 二次安全校验 |
| 定时执行 | 可直接使用 GitHub Actions 定时运行 |

---

## 为什么推荐 GLM

如果你是第一次接触这类项目，直接从 GLM 开始会更容易跑通。核心原因很简单：

- 配置更少：主要只要设置 `GLM_API_KEY` 和 `GLM_MODEL`。
- 成本更低：`glm-4.6v` 的免费额度通常足够覆盖周免领取场景。
- 更稳：`glm-4.6v-flash` 在高峰期偶尔会报“该模型当前访问量过大，请您稍后重试”，建议直接使用 `glm-4.6v`。
- 对国内用户更友好：不需要先解决 Google AI Studio 注册和可用性问题。
- 能力已验证：登录验证码、checkout 二次验证、拖拽/点选/多选题都能正常处理。

---

## 使用前先确认

- Epic 账号邮箱与密码（用于登录）。
- 关闭 Epic 账号 2FA（邮箱/短信/验证器）。
- 注册 GLM 并准备 `GLM_API_KEY`（用于验证码识别）。

---

## 🚀 快速开始

只做下面 4 步，通常 10 分钟内就能完成首次验证。

### 1. Fork 并启用 Actions

> [!TIP]
> 如果你已经 Fork 过这个仓库，建议先在 GitHub 网页上进入你自己的仓库，点击 `Sync fork` -> `Update branch`，先和最新项目保持一致，再继续后面的配置和运行。

- Fork 到自己的 GitHub 账号，建议改为私有仓库。
- 打开 `Actions`，启用工作流 `Epic Awesome Gamer (Scheduled)`。

### 2. 配置 Secrets

进入 `Settings` -> `Secrets and variables` -> `Actions`，先填这 5 个：

**如果你使用 `GLM_API_KEY`，请先确认对应智谱账号已经完成实名认证，否则 API 很可能不可用。**

| Secret | 示例值 |
| --- | --- |
| `EPIC_EMAIL` | 你的 Epic 邮箱 |
| `EPIC_PASSWORD` | 你的 Epic 密码 |
| `LLM_PROVIDER` | glm |
| `GLM_API_KEY` | 你的智谱 API Key |
| `GLM_MODEL` | glm-4.6v |

配置页面示例：
![GLM API获取](docs/images/tutorial/GLM-API.png)

![GitHub Actions Secrets 配置示例](docs/images/tutorial/step2-actions-secrets.png)

可选项：

- `GLM_BASE_URL` 留空即可使用默认值。
- 推荐把 `GLM_MODEL` 设为 `glm-4.6v`；`glm-4.6v-flash` 在高峰期可能报“该模型当前访问量过大，请您稍后重试”。
- `CHALLENGE_CLASSIFIER_MODEL`、`IMAGE_CLASSIFIER_MODEL`、`SPATIAL_POINT_REASONER_MODEL`、`SPATIAL_PATH_REASONER_MODEL` 留空即可跟随 `GLM_MODEL`。
- 如果要改 Gemini 路线，把 `LLM_PROVIDER` 设为 `gemini` 并配置 `GEMINI_API_KEY`。
- 走 `GLM` 路线时不需要额外再填 `GEMINI_API_KEY`。

### 3. 手动运行一次

- 进入 `Actions` 页面。
- 选择 `Epic Awesome Gamer (Scheduled)`。
- 点击 `Run workflow`。

> [!IMPORTANT]
> 不要看到运行了 5 分钟左右还在重试就手动取消。登录验证码和 checkout 二次校验本来就可能反复失败、重试、超时后再继续，有些最终成功的案例会持续 15 到 20 分钟；只要工作流还在继续跑，请先耐心等待。

### 4. 看日志确认是否跑通

成功时日志通常会出现类似内容：

```text
Login success
Right account validation success
Authentication completed
Starting free games collection process
All week-free games are already in the library
```

示例日志（中间有报错但最终成功）：

![中间报错但最终成功的日志示例 1](docs/images/tutorial/step4-log-success-with-warnings-1.png)

如果你在日志里看到多次重试后手动取消，像下面这样，也不一定代表脚本已经失败；很多时候只是还没跑完：

![不要过早取消 Actions 运行](docs/images/faq/action-cancel-too-early.svg)

---

## 运行日志与 Artifact

每次 GitHub Actions 运行结束后，工作流会自动上传三个 artifact：

| Artifact | 内容 |
| --- | --- |
| `epic-runtime-<run_id>` | 运行期截图、debug 文本、purchase_debug |
| `epic-logs-<run_id>` | 运行日志 |
| `epic-screenshots-<run_id>` | 登录失败、风控页、授权页等额外截图 |

下载位置：

1. 进入本次 Actions 运行页面
2. 拉到页面底部
3. 找到 `Artifacts`
4. 下载 zip 文件

说明：

| 文件包 | 先看什么 |
| --- | --- |
| `epic-runtime-<run_id>.zip` | 解压后优先看 `purchase_debug/` 里的截图和调试文本 |
| `epic-logs-<run_id>.zip` | 解压后直接看里面的日志文件 |

这些内容是 GitHub Actions 每次运行后打包上传的产物，不是仓库根目录里预置好的固定目录。

如果你要提 issue，请不要只粘贴一小段日志。最有用的做法是：

1. 打开出问题的 GitHub Actions 运行页面。
2. 拉到页面底部，找到 `Artifacts`。
3. 下载这些文件：
   - `epic-logs-<run_id>.zip`
   - `epic-runtime-<run_id>.zip`
   - `epic-screenshots-<run_id>.zip`
4. 新建 issue。
5. 把这些 zip 直接拖进 issue 编辑框，或者点击附件按钮上传。

这些 zip 里通常已经包含定位问题所需的完整日志、截图和 `purchase_debug` 文本。GitHub issue 支持直接上传 `.zip` 文件。

---

## 本地单次调试

如果你想在本地复现和 GitHub Actions 相同的入口，可以直接用仓库内置单次执行方式：

1. 复制 [`.env.example`](.env.example) 为 `.env`
2. 填好你自己的账号和模型配置
3. 执行 `uv sync --group dev`
4. 执行 `ENABLE_APSCHEDULER=false uv run app/deploy.py`

`.env`、`.venv`、`app/volumes/` 都已经被 `.gitignore` 忽略，不会被提交到 GitHub。

---

## 常见问题

### 1. 登录偶尔失败，一次成功一次失败

这是正常现象之一。GitHub Actions 使用的是共享云 IP，Epic 对风控比较敏感。常见表现包括登录页验证码一次过、一次不过，偶发 `captcha_invalid`，或者同一个账号隔一会儿又能成功。

另外，不要看到运行了几分钟还没结束就手动点 `Cancel workflow`。有些成功案例会在大量重试后，10 到 20 分钟才最终通过。

### 2. 日志里出现 `privacy-policy correction` 或卡在隐私政策页面

这通常不是模型接口问题，而是 Epic 账号状态问题。某些账号在登录成功后，会被额外重定向到类似 `/id/login/correction/privacy-policy` 的页面，要求先确认一次隐私政策。

处理方式很简单：先在你自己的正常浏览器里手动登录 Epic，完成这个确认页，然后再重新运行 Actions。

### 3. 页面弹出 `One more step`

这不是异常，是 Epic 结账阶段追加的人机校验。

现在项目已经能处理这类二次安全验证。你看到下面这种弹窗，不代表脚本坏了：

![Checkout Security Check](docs/images/faq/checkout-security-check.png)

### 4. 页面提示 `Device not supported`

这个提示通常出现在商品只支持 Windows，而 GitHub Actions 运行环境是 Linux 的时候。

### 5. 为什么工作流显示成功，但游戏没入库

过去常见根因有：

| 原因 | 说明 |
| --- | --- |
| 商品页状态识别不准 | 页面文案和实际状态不一致 |
| `Place Order` 已点击但未完成 | 结账页仍停留在二次验证 |
| 页面出现额外弹窗 | 例如设备不支持、额外确认 |
| 旧逻辑误判 | 曾经把普通文案误判成“已拥有” |

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
  - GLM_MODEL=glm-4.6v
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
- [Advanced Guide (English)](docs/advanced.en.md)

---

## 致谢

本项目基于 `QIN2DIM/epic-awesome-gamer` 实现，并参考了 `10000ge10000/epic-kiosk`：

| 项目 | 说明 |
| --- | --- |
| [QIN2DIM/epic-awesome-gamer](https://github.com/QIN2DIM/epic-awesome-gamer) | 原始项目与核心自动化思路来源 |
| [10000ge10000/epic-kiosk](https://github.com/10000ge10000/epic-kiosk) | GitHub Actions 化和文档组织方式的重要参考 |
| [LINUX DO](https://linux.do/t/topic/2036835/4) | 社区交流、反馈与项目推广支持 |

感谢原作者和维护者的工作。

---

## 免责声明

- 本项目仅用于学习和研究自动化流程。
- 自动化操作可能违反相关平台的服务条款，请自行评估风险。
- 使用本项目产生的后果由使用者自行承担。

---

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
