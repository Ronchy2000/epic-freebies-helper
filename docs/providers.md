# Provider 配置说明

本文是本仓库的 LLM/provider 入口说明。

目标有两个：

1. 让普通用户能按自己的账号、平台和模型能力完成配置。
2. 让第一次接触 LLM API 的用户，能从这个项目建立对“协议家族”和“具体模型”之间关系的宏观认识。

## 先记住这两个概念

### 1. 协议家族

协议家族是“你的程序和模型服务怎么对话”。

本仓库当前主要围绕两个协议家族设计：

| 协议家族 | 说明 | 典型对象 |
| --- | --- | --- |
| `google_genai` | Google Gemini 原生接口风格 | Gemini 官方接口、AiHubMix 这类 Gemini 兼容中转 |
| `openai_compatible` | OpenAI 风格的 `/v1/chat/completions` 接口 | OpenAI、DeepSeek、GLM、Ollama、很多本地网关、部分第三方平台 |

如果后续真的需要，再单独引入：

| 协议家族 | 说明 | 当前状态 |
| --- | --- | --- |
| `anthropic_compatible` | Anthropic Messages 风格接口 | 暂不优先；只有出现明确的协议级能力缺口时再加 |

### 2. preset

preset 是“在同一个协议家族下，给某个服务准备的一组默认值和特殊规则”。

例如：

- `openai`
- `deepseek`
- `glm`
- `ollama`
- `minimax`
- `xiaomi_mimo`

这些 preset 并不是新的协议家族，而是同一协议家族下的不同目标。

## 第三方中转站应该怎么理解

很多“中转站”“聚合平台”“自建网关”本质上不会发明一套全新协议，而是暴露下面这几种之一：

- OpenAI-compatible
- Anthropic-compatible
- Gemini-compatible

所以在这个项目里，接第三方中转站时优先问的不是“它是哪家公司”，而是：

1. 它对外是哪种协议？
2. 这条协议是否支持图片输入？
3. 这条协议的结构化输出是否稳定？
4. 这条协议是否支持当前验证码链路需要的图片传输方式？

如果同一个平台同时支持 OpenAI 和 Anthropic 两种协议，这个仓库当前的推荐顺序是：

1. 先试 `openai_compatible`
2. 如果确实出现协议级能力缺口，再考虑 `anthropic_compatible`

## 这个项目为什么不再按模型名逐个写 provider

因为项目真正依赖的是：

- 图片输入
- 多模态消息格式
- 稳定的结构化输出
- 能把验证码结果转换成点击点、拖拽路径、框选中心点

所以决定兼容成本的，通常不是“模型叫什么名字”，而是“它暴露的 API 协议长什么样”。

例如：

- `GPT`、`DeepSeek`、`GLM`、`Ollama` 很多时候都能落在 `openai_compatible`
- `Gemini` 和 `AiHubMix` 更接近 `google_genai`
- 某些平台虽然也提供 `Anthropic` 风格入口，但只有在 OpenAI-compatible 路线覆盖不了时才值得为它单独维护一个新协议家族

## 三层结构怎么分

这个仓库后续接模型时，建议固定按三层理解：

### 1. protocol family

这是 API 形状，例如：

- `google_genai`
- `openai_compatible`
- 未来可能的 `anthropic_compatible`

### 2. preset / profile

这是某个具体目标的默认配置和特殊规则，例如：

- `openai`
- `glm`
- `deepseek`
- `ollama`
- `aihubmix`
- `custom_openai_compatible`

### 3. task model

这是验证码子任务实际用哪个模型名：

- `CHALLENGE_CLASSIFIER_MODEL`
- `IMAGE_CLASSIFIER_MODEL`
- `SPATIAL_POINT_REASONER_MODEL`
- `SPATIAL_PATH_REASONER_MODEL`

这样设计后：

- 同一家厂商可以暴露多个协议入口
- 同一个协议家族可以复用多个 provider preset
- 不同验证码子任务还能继续独立调模型，而不需要新加 provider 分支

## 推荐使用方式

### 首选：canonical 协议配置

新配置优先使用下面这组变量：

| Secret / env | 作用 |
| --- | --- |
| `LLM_PRESET` | 选择目标服务 |
| `LLM_API_KEY` | 当前 preset 的 API key |
| `LLM_BASE_URL` | 当前 preset 的 base URL，留空时使用 preset 默认值 |
| `LLM_MODEL` | 当前运行默认模型 |
| `LLM_THINKING_ENABLED` | 某些 preset 的 thinking 开关 |
| `LLM_REASONING_EFFORT` | 某些 preset 的 reasoning effort |

如果你只是想“换一个 OpenAI-compatible 服务”，优先只改这一组。

### 兼容：legacy provider 配置

仓库仍兼容旧字段：

- `GEMINI_*`
- `GLM_*`
- `OPENAI_*`
- `DEEPSEEK_*`
- `LLM_PROVIDER`

也就是说，旧配置不会立刻失效，但后续更推荐迁移到 `LLM_PRESET + LLM_API_KEY + LLM_BASE_URL + LLM_MODEL`。

## 当前支持的 preset

| preset | 协议家族 | 默认 base URL | 默认模型 | 备注 |
| --- | --- | --- | --- | --- |
| `gemini` | `google_genai` | 留空，走 Gemini 官方默认地址 | `gemini-2.5-pro` | 也可配自定义 Gemini 兼容 base URL |
| `aihubmix` | `google_genai` | `https://aihubmix.com` | `gemini-2.5-pro` | 适合 AiHubMix 这类 Gemini 中转 |
| `openai` | `openai_compatible` | `https://api.openai.com/v1` | `gpt-4.1-mini` | 需要支持图片输入 |
| `deepseek` | `openai_compatible` | `https://api.deepseek.com` | `deepseek-v4-pro` | 支持 thinking / reasoning 参数 |
| `glm` | `openai_compatible` | `https://open.bigmodel.cn/api/paas/v4` | `glm-4.6v` | 保留 GLM 既有兼容逻辑 |
| `ollama` | `openai_compatible` | `http://127.0.0.1:11434/v1` | `qwen3-vl:8b` | 本地 Ollama，需提前 `ollama pull` 视觉模型 |
| `minimax` | `openai_compatible` | `https://api.minimaxi.com/v1` | `MiniMax-M2.7` | 你需要改成官方支持图片输入的模型 |
| `xiaomi_mimo` | `openai_compatible` | 无默认值 | 无默认值 | 需从你的 MiMo 控制台填写官方 base URL 与模型名 |
| `custom_openai_compatible` | `openai_compatible` | 无默认值 | 无默认值 | 自建网关、本地代理、第三方兼容服务 |

如果某个服务官方同时支持 OpenAI-compatible 和 Anthropic-compatible，不要急着把它做成新 family，先把它当作现有 family 下的 preset/profile。

## 如何按需求选择

### 1. 我用 Gemini 官方接口

```env
LLM_PRESET=gemini
LLM_API_KEY=your_gemini_key
LLM_BASE_URL=
LLM_MODEL=gemini-2.5-pro
```

说明：

- `LLM_BASE_URL` 留空时，程序会走 Gemini 官方默认地址。
- 如果你想继续沿用旧配置，也可以用 `LLM_PROVIDER=gemini + GEMINI_API_KEY`。

### 2. 我用 AiHubMix 这类 Gemini 中转

```env
LLM_PRESET=aihubmix
LLM_API_KEY=your_aihubmix_key
LLM_BASE_URL=https://aihubmix.com
LLM_MODEL=gemini-2.5-pro
```

说明：

- `aihubmix` 本质上仍属于 `google_genai` 家族。
- 如果你的中转地址不是 `https://aihubmix.com`，直接改 `LLM_BASE_URL`。

### 3. 我用 OpenAI / GPT

```env
LLM_PRESET=openai
LLM_API_KEY=your_openai_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4.1-mini
```

要求：

- 模型必须支持图片输入。
- OpenAI 官方现在更推荐 Responses API，但为了兼容更多第三方实现，本仓库 phase-1 仍以 OpenAI-compatible `chat/completions` 作为统一基线。

### 4. 我用 DeepSeek

```env
LLM_PRESET=deepseek
LLM_API_KEY=your_deepseek_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-v4-pro
LLM_THINKING_ENABLED=false
LLM_REASONING_EFFORT=high
```

说明：

- `deepseek` 被当作 `openai_compatible` preset 处理。
- `LLM_THINKING_ENABLED=true` 时，会一起传递 reasoning 参数。

### 5. 我用 GLM

```env
LLM_PRESET=glm
LLM_API_KEY=your_glm_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4.6v
```

说明：

- 这个 preset 保留了仓库原来验证过的 GLM 兼容逻辑。
- 对本项目来说，`glm-4.6v` 比 `glm-4.6v-flash` 更稳。
- GLM 的图片输入处理与大多数 OpenAI-compatible 服务不同，项目里已经单独兼容。

### 6. 我用 Ollama

```env
LLM_PRESET=ollama
LLM_API_KEY=
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen3-vl:8b
```

说明：

- 优先走 Ollama 官方提供的 OpenAI-compatible `/v1` 接口。
- `LLM_API_KEY` 可以留空，程序会使用兼容占位值。
- 你必须提前准备一个支持视觉输入的本地模型，例如：
  - `qwen3-vl:8b`
  - 其他你本地已拉取并验证可处理图片输入的模型

### 7. 我用 MiniMax

```env
LLM_PRESET=minimax
LLM_API_KEY=your_minimax_key
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=your_vision_capable_model
```

说明：

- `MiniMax-M2.7` 是 preset 的默认占位模型，但本项目是验证码多模态场景，建议你改成 MiniMax 控制台里官方支持图片输入的模型。
- 如果你使用国际域名或不同接入地址，直接覆盖 `LLM_BASE_URL`。

### 8. 我用 Xiaomi MiMo

```env
LLM_PRESET=xiaomi_mimo
LLM_API_KEY=your_mimo_key
LLM_BASE_URL=fill_from_official_console
LLM_MODEL=fill_from_official_console
```

说明：

- 这一路线按 `openai_compatible` 设计。
- 本次实现里没有硬编码 MiMo 的 base URL 和模型名，因为公开可抓取的官方文档入口不足以稳定确认这两个值。
- 你需要从自己的 MiMo 控制台填入官方给出的 endpoint 和支持图片输入的模型。

### 9. 我用别的 OpenAI-compatible 服务

```env
LLM_PRESET=custom_openai_compatible
LLM_API_KEY=optional_or_required_by_your_gateway
LLM_BASE_URL=https://your-gateway.example.com/v1
LLM_MODEL=your_model_name
```

这适用于：

- 本地代理
- 自建 vLLM / TGI / LocalAI / LM Studio 网关
- 其他兼容 `/v1/chat/completions` 的第三方服务

### 10. 我用支持 Anthropic 协议的第三方平台

当前这个 protocol 分支还没有把 `anthropic_compatible` 作为运行时主路径落完。

所以如果你手上的平台同时支持：

- OpenAI-compatible
- Anthropic-compatible

优先先按 OpenAI-compatible 接入，再观察：

- 图片输入是否正常
- JSON / 结构化输出是否稳定
- 验证码坐标与拖拽任务是否稳定

只有当这些能力在 OpenAI-compatible 路线上确实不够，而 Anthropic 协议能明显补齐时，才值得继续实现新的 `anthropic_compatible` family。

## GitHub Actions 里应该填哪些 Secrets

所有路线都需要：

| Secret | 说明 |
| --- | --- |
| `EPIC_EMAIL` | Epic 邮箱 |
| `EPIC_PASSWORD` | Epic 密码 |

推荐使用 canonical 变量：

| Secret | 说明 |
| --- | --- |
| `LLM_PRESET` | 选择服务 |
| `LLM_API_KEY` | 当前服务 key |
| `LLM_BASE_URL` | 当前服务 base URL |
| `LLM_MODEL` | 当前服务模型 |
| `LLM_THINKING_ENABLED` | 可选 |
| `LLM_REASONING_EFFORT` | 可选 |

如果你已经在用旧配置，也仍然可用，例如：

- `OPENAI_API_KEY`
- `DEEPSEEK_API_KEY`
- `GLM_API_KEY`
- `GEMINI_API_KEY`
- `LLM_PROVIDER`

## 本项目会在日志里输出什么

启动时会输出一段精简的 runtime summary，重点包括：

- 当前使用的 `protocol`
- 当前使用的 `preset`
- 当前使用的 `model`
- 当前使用的 `base_url`
- 当前 Epic 邮箱的脱敏值，例如 `du***@example.com`

这样你在 GitHub Actions 日志里可以快速确认：

- 到底跑的是哪条 provider 路线
- 模型名是不是你想要的那个
- 有没有把 Secrets 配错

## 模型要求

不管你走哪条路线，都要尽量满足下面几点：

1. 支持图片输入
2. 能稳定输出 JSON 或近似 JSON
3. 能处理验证码这种坐标/路径/区域选择任务
4. 单次响应延迟不要太高

单纯“支持聊天”的模型，不代表适合本项目。

## 结构化输出是怎么处理的

为了兼容更多服务，本项目当前优先走“OpenAI-compatible chat completions + JSON mode / 解析兜底”。

这意味着：

- 如果服务能稳定返回 JSON，效果最好
- 如果服务偶尔返回半结构化文本，项目会尝试做兼容解析
- 如果模型完全不擅长按规则输出，验证码链路就会不稳

## 官方文档入口

这些是本次实现实际参考过的官方入口，后续要新增 preset 时也应该优先看这里：

- OpenAI
  - [Responses API migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses)
  - [Structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- Gemini
  - [Gemini API vision](https://ai.google.dev/gemini-api/docs/vision)
  - [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- Ollama
  - [OpenAI compatibility](https://docs.ollama.com/openai)
  - [Vision capability](https://docs.ollama.com/capabilities/vision)
  - [Structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- DeepSeek
  - [DeepSeek API docs](https://api-docs.deepseek.com/)
- MiniMax
  - [MiniMax OpenAI API compatibility](https://platform.minimaxi.com/document/Intelligent%20Assistant/OpenAI%20API%20Compatibility)
- Anthropic
  - [Messages API](https://docs.anthropic.com/en/api/messages)
  - [Vision](https://docs.anthropic.com/en/docs/build-with-claude/vision)

## 选择顺序建议

如果你是在继续完善这个项目，而不是只是想跑通一次，建议按这个顺序考虑新接入：

1. 先判断目标能不能归到 `google_genai` 或 `openai_compatible`
2. 如果能归到现有协议家族，就只新增 preset/profile，不新增 adapter family
3. 如果一个平台同时支持 OpenAI 和 Anthropic，两条都别急着一起做，先走 OpenAI-compatible
4. 只有在明确出现协议级能力缺口时，再把 `anthropic_compatible` 提升为下一阶段任务

## 如果你只是想最快跑起来

最省心的几条路线通常是：

1. `LLM_PRESET=glm`
2. `LLM_PRESET=openai`
3. `LLM_PRESET=deepseek`
4. `LLM_PRESET=gemini`

如果你是想学习“不同 LLM API 协议长什么样”，建议按这个顺序看：

1. `gemini` / `aihubmix`
2. `openai`
3. `deepseek`
4. `glm`
5. `ollama`
6. `custom_openai_compatible`
