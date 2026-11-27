# Provider 配置说明

本文说明模型 provider 的配置方式、模型要求和常见接口错误。

## 支持的 Provider

当前分支建议使用以下 provider：

| Provider | 状态 | 用途 |
| --- | --- | --- |
| `glm` | 当前分支可用 | 通过智谱 OpenAI 兼容接口处理验证码 |
| `deepseek` | 当前分支可用 | 通过 DeepSeek OpenAI 兼容接口（`deepseek-flash`，即 DeepSeek-V4.1-Flash-1017）处理验证码 |
| `gemini` | 当前分支可用 | 通过 Gemini 或 AiHubMix 兼容接口处理验证码 |
| `openai` | 需要包含 OpenAI provider 的代码版本 | 通过 OpenAI Chat Completions 处理验证码 |

如果当前代码的 `app/settings.py` 中没有 `openai`，不要在该版本中设置 `LLM_PROVIDER=openai`。

## GLM

### Secrets

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `LLM_PROVIDER` | 固定为 `glm` | `glm` |
| `GLM_API_KEY` | 智谱 API Key | - |
| `GLM_BASE_URL` | 智谱 OpenAI 兼容接口地址 | `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | 视觉模型 | `glm-4.6v` |

### 推荐配置

| Secret | 推荐值 |
| --- | --- |
| `LLM_PROVIDER` | `glm` |
| `GLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` |
| `GLM_MODEL` | `glm-4.6v` |

### 注意事项

- `glm-4.6v` 作为默认推荐模型。
- `glm-4.6v-flash` 在高峰期可能出现模型繁忙错误。
- 如果 API 无法调用，先检查 API Key、账户状态和接口权限。
- 使用 GLM 时不需要额外配置 `GEMINI_API_KEY`。

## DeepSeek (V4.1 Flash)

DeepSeek 现已支持多模态视觉输入与 OpenAI 兼容 Chat Completions 接口，可在本分支直接作为正式 provider 启用。

### 配置项

| 配置项 | 存放位置（GitHub Actions） | 说明 | 推荐值 |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | Variables（兼容 Secrets） | 固定为 `deepseek` | `deepseek` |
| `DEEPSEEK_API_KEY` | **Secrets**（勿填 Variables） | DeepSeek API Key | - |
| `DEEPSEEK_BASE_URL` | Variables（兼容 Secrets） | OpenAI 兼容接口地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | Variables（兼容 Secrets） | 视觉多模态模型 | `deepseek-flash` |
| `DEEPSEEK_THINKING_ENABLED` | Variables（兼容 Secrets） | 是否开启推理模式 | `false` |
| `DEEPSEEK_REASONING_EFFORT` | Variables（兼容 Secrets） | 开启推理模式时的强度 | `high` |

### 模型与接口说明

- 推荐模型名填写 `deepseek-flash`，该模型现已由 `DeepSeek-V4.1-Flash-1017` 提供服务，原生支持 `image_url`（base64 data URL）多模态输入及 `json_object` 结构化输出。
- 旧模型名 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 虽仍可转发至 `DeepSeek-V4.1-Flash-1017`，但建议统一使用 `deepseek-flash`。
- 本项目走 OpenAI 兼容端点 `https://api.deepseek.com`（DeepSeek 另提供 Anthropic 兼容端点 `https://api.deepseek.com/anthropic`，但本项目适配器对接的是 `/chat/completions`）。
- 使用 DeepSeek 时不需要额外配置 `GEMINI_API_KEY`。

### 注意事项

- 默认关闭 `DEEPSEEK_THINKING_ENABLED=false` 以降低单次验证码求解延迟；若复杂题目准确率不足，可按需开启 `DEEPSEEK_THINKING_ENABLED=true` 并配合 `DEEPSEEK_REASONING_EFFORT=high`。
- 在 GitHub Actions 中务必把 `DEEPSEEK_API_KEY` 填在仓库 **Secrets** 中（不要放到 Variables）。
- 可在本地配置 `.env` 后运行 `uv run python scripts/test_deepseek_api.py` 快速验证纯文本、Thinking、JSON 与多模态图片接口连通性。

## OpenAI / GPT

### Secrets

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `LLM_PROVIDER` | 固定为 `openai` | `openai` |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `OPENAI_BASE_URL` | OpenAI API 地址 | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 支持图片输入的模型 | `gpt-4.1-mini` |

### 使用前提

OpenAI / GPT 配置只适用于已经包含 OpenAI provider 的代码版本。

如果当前版本的 `app/settings.py` 中没有以下字段，不要在该版本中使用 OpenAI / GPT：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

### 模型要求

OpenAI provider 要求模型支持图片输入。

如果使用第三方 OpenAI 兼容网关，需要确认该网关支持 Chat Completions 的 `image_url` 输入格式。

### 常见错误

| 现象 | 可能原因 | 处理方式 |
| --- | --- | --- |
| HTTP 400 | 模型不支持图片输入 | 更换支持图片输入的模型 |
| `unsupported image` | 网关不支持图片参数 | 更换网关或使用官方接口 |
| `invalid content type` | 请求格式不被兼容接口支持 | 检查 `OPENAI_BASE_URL` 和模型能力 |
| `authentication failed` | API Key 无效或未配置 | 检查 `OPENAI_API_KEY` |

## Gemini / AiHubMix

### Secrets

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `LLM_PROVIDER` | 固定为 `gemini` | `gemini` |
| `GEMINI_API_KEY` | Gemini 或 AiHubMix Key | - |
| `GEMINI_BASE_URL` | Gemini 兼容接口地址 | `https://aihubmix.com` |
| `GEMINI_MODEL` | Gemini 模型 | `gemini-2.5-pro` |

### 推荐配置

| Secret | 推荐值 |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_BASE_URL` | `https://aihubmix.com` |
| `GEMINI_MODEL` | `gemini-2.5-pro` |

### 注意事项

- 变量名是 `GEMINI_BASE_URL`，不是 `GEMINI_BASE_MODEL`。
- 使用 AiHubMix 时，确认该服务当前支持所填模型。
- 如果模型返回结构不稳定，先检查日志中的 provider 响应错误。

## 高级模型覆盖项

以下配置通常不需要填写。留空时会自动使用当前 provider 的默认模型。

| Secret | 说明 |
| --- | --- |
| `CHALLENGE_CLASSIFIER_MODEL` | 验证码类型识别模型 |
| `IMAGE_CLASSIFIER_MODEL` | 图片分类模型 |
| `SPATIAL_POINT_REASONER_MODEL` | 点选类验证码推理模型 |
| `SPATIAL_PATH_REASONER_MODEL` | 拖拽路径类验证码推理模型 |

默认情况下不需要单独配置上述 4 个变量。只有在需要为不同验证码步骤指定不同模型时再填写。

## 配置检查清单

配置完成后，检查以下项目：

| 项目 | 检查内容 |
| --- | --- |
| `LLM_PROVIDER` | 是否与实际选择的 provider 一致 |
| API Key | 是否配置了当前 provider 对应的 Key |
| Base URL | 是否使用当前 provider 的接口地址 |
| 模型名 | 是否为支持图片输入的模型 |
| Gemini 变量名 | 是否使用 `GEMINI_BASE_URL` |
| 高级覆盖项 | 不需要拆分模型时是否保持为空 |
