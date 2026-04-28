# 本地调试与 Docker 部署

本文说明本地单次运行和 Docker 部署方式。

## 本地单次调试

本地调试使用和 GitHub Actions 相同的入口。

### 1. 准备环境

```bash
uv sync --group dev
```

### 2. 准备配置

复制 `.env.example` 为 `.env`，然后填写 Epic 账号和 provider 配置。

```bash
cp .env.example .env
```

`.env`、`.venv`、`app/volumes/` 已经被 `.gitignore` 忽略。

### 3. 单次运行

```bash
ENABLE_APSCHEDULER=false uv run app/deploy.py
```

本地单次运行不会启动内部调度器。

## Docker 部署

如果不使用 GitHub Actions，可以使用 Docker Compose 在服务器、NAS 或本地环境运行。

### 1. 克隆仓库

```bash
git clone https://github.com/Ronchy2000/epic-freebies-helper.git
cd epic-freebies-helper
```

### 2. 修改配置

主要入口是 [`docker/docker-compose.yaml`](../docker/docker-compose.yaml)。

根据选择的 provider 修改环境变量。

GLM 示例：

```yaml
environment:
  - LLM_PROVIDER=glm
  - GLM_API_KEY=your_glm_key
  - GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
  - GLM_MODEL=glm-4.6v
```

DeepSeek V4 示例：

```yaml
environment:
  - LLM_PROVIDER=deepseek
  - DEEPSEEK_API_KEY=your_deepseek_key
  - DEEPSEEK_BASE_URL=https://api.deepseek.com
  - DEEPSEEK_MODEL=deepseek-v4-flash
  - DEEPSEEK_THINKING_ENABLED=false
  - DEEPSEEK_REASONING_EFFORT=high
```

Gemini / AiHubMix 示例：

```yaml
environment:
  - LLM_PROVIDER=gemini
  - GEMINI_API_KEY=your_key
  - GEMINI_BASE_URL=https://aihubmix.com
  - GEMINI_MODEL=gemini-2.5-pro
```

OpenAI / GPT 示例：

```yaml
environment:
  - LLM_PROVIDER=openai
  - OPENAI_API_KEY=your_openai_key
  - OPENAI_BASE_URL=https://api.openai.com/v1
  - OPENAI_MODEL=gpt-4.1-mini
```

OpenAI / GPT 示例只适用于已经包含 OpenAI provider 的代码版本。

### 3. 启动

```bash
docker compose up -d --build
```

### 4. 查看日志

```bash
docker compose logs -f epic-freebies-helper
```

## 运行产物

本地和 Docker 运行会在 `app/volumes/` 下生成日志和运行文件。

| 路径 | 内容 |
| --- | --- |
| `app/volumes/logs/` | 运行日志 |
| `app/volumes/runtime/` | 运行期数据、调试文本、截图 |
| `app/volumes/screenshots/` | 登录、授权或风控截图 |
| `app/volumes/user_data/` | 浏览器用户数据 |

这些目录用于排障，不应提交到仓库。
