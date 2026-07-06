# Provider 配置说明

本文说明模型 provider 的配置方式、模型要求和常见接口错误。

## 支持的 Provider

当前分支建议使用以下 provider：

| Provider | 状态 | 用途 |
| --- | --- | --- |
| `glm` | 当前分支可用 | 通过智谱 OpenAI 兼容接口处理验证码 |
| `deepseek` | 预留占位，暂不启用 | 等官方多模态能力适合当前验证码链路后再启用 |
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

## DeepSeek V4

当前先不要把 DeepSeek 作为正式 provider 启用。
这部分配置和代码保留在分支里，目的是等 DeepSeek 官方提供适合当前验证码流程的稳定多模态能力后再继续推进。

### Secrets

| Secret | 说明 | 示例 |
| --- | --- | --- |
| `LLM_PROVIDER` | 预留值 | `deepseek` |
| `DEEPSEEK_API_KEY` | 预留占位 | - |
| `DEEPSEEK_BASE_URL` | 预留接口地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 预留模型值 | `deepseek-v4-pro` |
| `DEEPSEEK_THINKING_ENABLED` | 预留占位 | `false` |
| `DEEPSEEK_REASONING_EFFORT` | 预留占位 | `high` |

### 当前状态

- 当前不建议实际启用 `LLM_PROVIDER=deepseek`。
- 这组变量仅保留为后续恢复实验时的占位配置。
- 如果未来 DeepSeek 官方多模态能力成熟，再回到本分支继续启用和验证。

### 模型要求

当前项目的验证码流程依赖图片输入和稳定的多模态响应。

DeepSeek 这条线虽然保留了 OpenAI-compatible 适配草稿，但在官方多模态能力适合这条链路之前，不应视为可运行 provider。

### 注意事项

- 当前不要把 DeepSeek 配置接入正式运行。
- 如果只是保留配置占位，建议继续使用 `deepseek-v4-pro` 作为文档中的占位模型值。
- 等 DeepSeek 官方多模态能力适合当前流程后，再重新评估 `DEEPSEEK_THINKING_ENABLED` 和 `DEEPSEEK_REASONING_EFFORT` 的实际建议值。

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
