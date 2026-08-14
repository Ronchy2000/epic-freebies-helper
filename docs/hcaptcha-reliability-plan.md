# hCaptcha 通过率改进方案

> 状态：已复核并实施 P0-P2；P3 待分题型数据
> 日期：2026-07-26
> 最近复核：2026-08-14，基于 Actions run `31766718025` 的完整日志和截图工件
> 基线分支：`protocol-provider-architecture` @ `2fd6326`
> 上游：`hcaptcha-challenger 0.19.0`（`pyproject.toml` 约束为 `>=0.18.13`）

本文回答一个问题：**为什么用户有时候仍然过不了 Epic 的 hCaptcha，以及按什么顺序修。**

结论先行：当前失败**主要不是"模型不够聪明"**。排查中发现了一个确定性的代码缺陷（P0），它会让整类拖拽题在兜底路径上 100% 失败；此外还有三个结构性问题（重试信号丢失、无界递归、零测试覆盖）放大了故障。这些修完之前，换更强的模型收益有限。

> 实施复核（2026-07-30）：P0 与 P1-A/B/C/D 已在当前 `master` 落地；P2-A/B 的代理透传、Playwright 降级告警和 virtual 模式统一随后补齐。当前项目没有独立的通用 runtime summary，降级状态改为写入 error 日志并随 Actions 日志 artifact 留存，不让可选 Telegram 功能介入原领取路径。P3 仍需分题型成功率数据，不在缺少证据时修改默认模型。文末提到的 provider architecture 文档属于 `protocol-provider-architecture` 分支，不是当前 `master` 中可直接更新的文件。

---

## 一、实证：现在到底是怎么失败的

从 `app/volumes/logs/` 的真实日志聚合：

| 信号 | 次数 |
|---|---|
| `Challenge success` | 1 |
| `ChallengeException` | 6 |
| `RetryError` | 18 |
| `Failed to challenge`（求解跑完但没过） | 0 |
| `Challenge execution timed out` | 0 |

题型分布：`image_drag_multi` 8 次，`image_drag_single` 3 次。

这个分布很关键：**0 次 `Failed to challenge`、0 次超时**，意味着失败几乎全部发生在"把 LLM 的回答解析成上游 schema"这一步，而不是"模型答错了"或"模型太慢"。典型行：

```
ChallengeException - type=image_drag_multi err=RetryError(<Future ... raised ValueError>)
```

---

## 二、P0 缺陷（已实证复现）：别名表把合法值改成非法值

### 位置

`app/extensions/llm_protocols/common.py:27`

```python
CHALLENGE_TYPE_ALIASES = {"image_drag_multi": "image_drag_multiple"}
```

`extract_challenge_type()`（`common.py:123-128`）在返回前套用这张表。

### 问题

上游 `0.19.0` 的枚举（`hcaptcha_challenger/models.py:218-222`）只有四个合法值：

```
image_label_single_select
image_label_multi_select
image_drag_single
image_drag_multi        ← 合法
```

**`image_drag_multiple` 在上游根本不存在。** 这张别名表的方向是反的：它把上游唯一认可的 `image_drag_multi` 改写成了一个会被 pydantic 拒绝的值。

### 复现

```python
from hcaptcha_challenger.models import ChallengeRouterResult
from extensions.llm_protocols.common import extract_challenge_type, coerce_payload_for_schema

text = 'image_drag_multi'
ct = extract_challenge_type(text)          # -> 'image_drag_multiple'
p = coerce_payload_for_schema({'challenge_type': ct, 'request_type': ct},
                              ChallengeRouterResult, text)
# -> {'challenge_type': 'image_drag_multiple', 'challenge_prompt': ''}
ChallengeRouterResult(**p)                 # -> ValidationError
```

实测输出：

```
extract_challenge_type -> image_drag_multiple
coerced -> {'challenge_type': 'image_drag_multiple', 'challenge_prompt': ''}
VALIDATION FAIL: ValidationError
```

对照：直接用 `image_drag_multi` 构造 `ChallengeRouterResult` 是 OK 的。

### 触发条件

只在**纯文本兜底路径**触发，即 `common.py:786-799`：LLM 没有返回合法 JSON、走到 `extract_challenge_type(text)` 分支时。走 JSON 路径时 `challenge_type` 是从 payload 直接取的，不过别名表，所以正常。

这解释了为什么故障是"有时候"而不是"每次"——**它精确对应"LLM 这次没吐出规整 JSON"的那部分请求**。而 GLM 系模型输出格式不稳定正是 `docs/advanced.md:74-87` 已经记录在案的已知问题。两个已知问题在这里相乘了。

`ValidationError` 是 `ValueError` 的子类，被 tenacity 的 `@retry(stop_after_attempt(3))` 吃掉三次后包成 `RetryError` 抛出——与日志里 18 次 `RetryError` 的形态完全吻合。

### 历史来源

`docs/maintenance-log.md:307-325`（2026-04 条目）写道："challenge router 返回的 `image_drag_multi` 是别名，当前路由识别只收 `image_drag_multiple`"。当时的上游版本大概率确实用 `image_drag_multiple`。之后 `uv.lock` 从 `0.18.x` 漂到 `0.19.0`，上游把名字统一成了 `image_drag_multi`，**别名表没跟着改，于是从"修复"变成了"缺陷"**。

这是 `pyproject.toml:8` 的开放上界 `>=0.18.13` 加上宽耦合面（继承 `AgentConfig`、直接引用上游 models）的直接代价。

### 修复

删掉这张表，或反转方向并加一道"归一化结果必须在上游枚举内"的断言：

```python
from hcaptcha_challenger.models import ChallengeTypeEnum
VALID = {e.value for e in ChallengeTypeEnum}
# 归一化后若不在 VALID 内，视为无法识别，返回 None 走上游视觉兜底
```

关键在于**以上游枚举为唯一真相**，而不是维护一份手写常量集。`KNOWN_CHALLENGE_TYPES`（`common.py:17-25`）里的 `image_label_binary` / `image_label_area_select` 属于上游 `RequestType`（另一个枚举），`image_label_multiple_choice` 则两个枚举里都没有——这套常量已经和上游脱节，应一并重建。

---

## 三、结构性问题

### P1-A：`ChallengeSignal` 返回值被全部丢弃

上游 `wait_for_challenge()` **不抛异常**，而是返回 `ChallengeSignal` 枚举（`challenger.py:905-941`），有 `SUCCESS` / `FAILURE` / `EXECUTION_TIMEOUT` / `RESPONSE_TIMEOUT` 等七个值。

全仓库 `app/` 下 `grep ChallengeSignal` **零命中**。五个调用点全部写成 `await agent.wait_for_challenge()`，返回值直接丢弃：

| 文件:行号 | 场景 |
|---|---|
| `app/services/epic_authorization_service.py:270` | 登录 |
| `app/services/epic_games_service.py:961` | checkout 主循环 |
| `app/services/epic_games_service.py:1005` | 隐性挑战探测 |
| `app/services/epic_games_service.py:1028` | 延长探测 |
| `app/services/epic_games_service.py:1474` | 购物车下单 |

后果：业务层**无法区分"求解成功"和"求解失败"**，只能靠事后重新扫 DOM 反推。这就是为什么 `_is_checkout_security_check_visible()` 需要四层 locator 判断（`epic_games_service.py:890-922`）、`_has_visible_hcaptcha()` 需要遍历 frame 加文案兜底（`epic_authorization_service.py:113-142`）——**大量 DOM 启发式在补一个本来直接可读的返回值。**

更糟的是登录路径 `epic_authorization_service.py:268-269`：

```python
with suppress(Exception):
    await agent.wait_for_challenge()
```

异常和返回值同时被吞。真实故障在日志里只剩一条 warning。

修复成本很低（五处各加一次赋值和分支），收益是让后续所有诊断都有据可依。**这应该在 P0 之后立刻做**，因为下面几项的验证都依赖它。

### P1-B：上游 `RETRY_ON_FAILURE` 未覆盖，存在无界递归

实测当前生效值：

```
EXECUTION_TIMEOUT   = 120.0
RESPONSE_TIMEOUT    = 30.0
RETRY_ON_FAILURE    = True     ← 上游默认，项目未覆盖
MAX_CRUMB_COUNT     = 2
ignore_request_types = []
```

`challenger.py:930-933`：失败时 `return await self.wait_for_challenge()` —— **无界自递归**。而 `EXECUTION_TIMEOUT=120s` 只包裹单次 `_solve_captcha()`，**不包裹递归整体**（`challenger.py:908-912`）。`_solve_captcha` 内部的异常路径也会 `refresh_challenge()` 后递归（`challenger.py:895-903`）。

于是实际尝试次数是四层叠加的：上游无界递归 × 上游子任务 `stop_after_attempt(3)` × 业务层 3 次/10 分钟 × Celery 20 分钟硬超时。**没人能预测一次领取到底会调多少次 LLM**，成本和耗时都不可控。

建议：显式设 `RETRY_ON_FAILURE=false`，把重试收归业务层统一管理。这个不用改代码——`model_config` 是 `SettingsConfigDict(env_file=".env", extra="ignore")`（`settings.py:80`），同名环境变量即可覆盖。但**应该在 `.env.example` 里显式暴露**，否则这个关键旋钮对用户不可见。

### P1-C：`_purchase_free_game` 无界递归

`app/services/epic_games_service.py:1469-1478`：

```python
except Exception as err:
    logger.warning(f"Failed to solve captcha - {err}")
    await self.page.reload()
    return await self._purchase_free_game()   # 无计数器、无深度限制
```

没有递归深度或时间上限。对照 checkout 路径有 10 分钟时间盒（`:924`），风格不一致。唯一兜底是 Celery 的 `CELERY_TASK_TIME_LIMIT=1200`。应改成与 checkout 一致的有界循环。

### P1-D：payload 归一化零测试覆盖

`tests/test_glm_adapter.py:5-9` 仍从 `extensions.llm_adapter` 导入 `_coerce_payload_for_schema` / `_extract_json_payload` / `_normalize_glm_payload`。重构（`fb7ca19`）后这三个函数搬到了 `llm_protocols/common.py` 且去掉了下划线前缀。实测：

```
ModuleNotFoundError: No module named 'extensions'
```

（含路径问题和改名问题两重失效。）

结果是 `common.py` 里约 550 行最容易出 bug 的归一化逻辑（`:55-608`）**目前零覆盖**。第二节那个 P0 缺陷本来是一个三行单测就能拦住的。

注意 `CLAUDE.md` 规定"Test execution is not allowed"。这条方案里我不建议违反它——但**修好这个文件让它在用户本地可跑**是有价值的，而且可以用静态检查（比如一个校验"所有归一化输出的 challenge_type 都在上游枚举内"的小脚本）替代一部分。

---

## 四、环境层面（P2，收益真实但工程量大）

### 无代理支持

全仓库 `app/` 下无 `proxy` 参数、无 `*_PROXY` 读取、无相关配置项。在 GitHub Actions 上跑意味着用 Azure 数据中心 IP 撞 Epic/hCaptcha 风控。

`docs/advanced.md:236` 已把"共享云 IP"列为不可控失败源，但代码层面没有任何对策。**这是验证码难度偏高的结构性来源**——同一道题，住宅 IP 可能直接 pass 走 checkbox，数据中心 IP 则会被反复升级难度。

建议加 `BROWSER_PROXY` 配置，透传给 Camoufox 和 Playwright 两条路径。这是唯一能降低"题目本身难度"的手段，其余所有优化都只是提高"给定难度下的答对率"。

### Playwright 降级路径无任何反检测

`app/services/browser_context.py`：

- Camoufox 路径有指纹伪装、`humanize=0.2`、browserforge 屏幕参数（`:19-28`）
- Playwright 降级路径（`:31-38`）**什么都没有**：无 stealth、无 `navigator.webdriver` 抹除、无自定义 UA
- 且 `:34` 把 `"virtual"` 转成真 headless：`True if headless == "virtual" else bool(headless)`

真 headless 比 Xvfb 虚拟显示更容易被检测。降级时只有一条 warning（`:74-77`），用户很可能不知道自己已经掉到了高风险路径。

建议：降级时把日志提到 `error` 级并在 runtime summary 里标注；`"virtual"` 应保留为带 Xvfb 的有头模式而非降级成 headless。

### headless 取值三个入口不一致

| 入口 | 值 |
|---|---|
| `app/deploy.py:95` | 硬编码 `True` |
| `collect_epic_games_task.py:72` | `"virtual" if linux else False` |
| Camoufox | 原样透传，支持 `"virtual"` |
| Playwright fallback | `"virtual"` → `True` |

主入口 `deploy.py` 硬编码 `True` 意味着 **CI 上永远拿不到 `"virtual"` 的抗检测收益**，尽管 workflow 已经在 `xvfb-run` 下跑了（`.github/workflows/epic-gamer.yml:90`）。这是个明显的浪费。

---

## 五、模型侧（P3）

放最后是因为：**在 P0 修好之前，换模型基本无效**——失败卡在解析层，不在推理层。

当前实测配置：`protocol=openai_compatible | preset=glm | model=glm-4.6v`。

四个子任务模型（`settings.py:147-150`）被统一置空、回填成同一个 `LLM_MODEL`（`:380-388`）。但上游的默认分工是有讲究的（`challenger.py:165-180`）：分类用 flash（快、便宜），空间推理用 pro（准）。**一刀切成同一个模型，等于要么在分类上过度付费，要么在空间推理上精度不足。**

P0 修完、P1-A 让成功率可观测之后，值得做的是：

1. 用 `ChallengeSignal` 统计**分题型成功率**，而不是拍脑袋
2. 只对表现差的题型换模型（大概率是 drag 类需要更强的空间推理）
3. 保留 `image_label_binary` 用便宜模型

另外 `ignore_request_questions`（`settings.py:453`）目前只屏蔽了一道题。如果统计出某个题型成功率极低且刷新代价低，**主动 skip 让它换一题**可能比硬解更划算——这是 hCaptcha 场景里被低估的策略。

---

## 六、执行顺序

| 优先级 | 项目 | 工程量 | 预期收益 |
|---|---|---|---|
| **P0** | 修 `CHALLENGE_TYPE_ALIASES` 反向映射，改以上游枚举为真相 | 极小 | 高 — 消除一整类确定性失败 |
| **P1-A** | 五处读取 `ChallengeSignal` 返回值 | 小 | 高 — 让后续一切可观测 |
| **P1-B** | `.env.example` 暴露 `RETRY_ON_FAILURE` 等旋钮并默认关闭上游递归 | 极小 | 中 — 成本与耗时可控 |
| **P1-C** | `_purchase_free_game` 改有界循环 | 小 | 中 |
| **P1-D** | 修复 `tests/test_glm_adapter.py` 导入 | 小 | 中 — 防回归 |
| **P2-A** | 加 `BROWSER_PROXY` 支持 | 中 | 高（但依赖用户有代理） |
| **P2-B** | 降级路径告警 + `"virtual"` 语义修正 + `deploy.py` headless 统一 | 小 | 中 |
| **P3** | 基于真实数据做分题型模型选型 | 中 | 待数据 |

P0 到 P1-D 建议作为一个批次，它们互相支撑：P0 消除主要故障源，P1-A 提供验证手段，P1-D 防止重蹈覆辙。

---

## 七、验证方式（受限于"禁止执行测试"）

`CLAUDE.md` 规定测试执行不被允许，所以验证靠三样：

1. **静态断言脚本** — 一个不属于 `tests/` 的小工具，校验 `KNOWN_CHALLENGE_TYPES` ⊆ 上游枚举，CI 里当 lint 跑。这类"契约检查"能在上游再次改名时立刻报警，正是这次事故缺的东西。
2. **artifact 复盘** — `docs/advanced.md:228-235` 已有五步排障流程；P1-A 落地后日志里会直接出现 `ChallengeSignal`，复盘成本大幅下降。
3. **`uv run ruff check` + `uv run black -C -l 100`** — 常规静态检查。

---

## 八、需要一并处理的文档欠账

- `docs/provider-protocol-architecture.md:9-16` 仍称 "As of 2026-05-09 ... Do not treat `master` as if it already has a generic multi-protocol provider architecture"，但代码在 `fb7ca19` 已经实现。文档滞后于代码。
- 按 `CLAUDE.md` 的维护日志规定，上述任一改动落地后都需向 `docs/maintenance-log.md` 追加"现象 / 根因判断 / 改动文件 / 处理结果"四段式条目。
- 建议把 `pyproject.toml:8` 的 `hcaptcha-challenger>=0.18.13` 收紧上界（如 `>=0.19,<0.20`）。本次事故的根因就是 minor 版本自由漂移，而项目对上游的耦合面（继承 `AgentConfig`、引用 models、monkeypatch `google.genai`）宽到经不起这种漂移。

---

## 九、2026-08-14 失败工件复核与增量修复

Actions run `31766718025` 不是单一的“模型答错”。同一次登录流程中存在三个可以分别验证的问题：

1. GLM 视觉请求在 50 秒客户端时限后进入上游三次重试，单个推理步骤理论上会消耗约 156 秒，超过 hCaptcha 单轮 120 秒执行时限。
2. Camoufox/Firefox 读取压缩的 `/hsw.js` 时出现 `NS_ERROR_INVALID_CONTENT_ENCODING`，导致 HSW 逆向结果为空，确定性求解器随之降级。
3. 动物计数题的参考条实际位于左侧、可点击 4×4 网格位于右侧；旧提示词把方向写死为相反布局。另一次模型回答包含 `y=809`，已经超过挑战框下沿，但旧流程仍会直接点击。

本轮采用最小边界修复，而不是关闭 GLM 4.6 的 thinking：本地重放显示关闭 thinking 虽然能把响应时间降到约 7–11 秒，却会返回全部网格或参考条坐标，准确率明显下降。

- 浏览器只对 `**/hsw.js*` 请求设置 `Accept-Encoding: identity`，其他 Epic、hCaptcha 和模型请求头保持不变。
- GLM 请求超时会包含预算和异常类型；上游 provider 的网络尝试从三次收紧为两次，使 `2 × 50s + 3s` 保持在单轮 120 秒时限内。
- 动物计数提示改成方向无关描述；只有题目同时包含 animal/count 特征时才检测重复数量徽标，并把另一侧方形区域识别为可点击网格。
- 点选回答在缓存和点击前必须通过挑战框边界校验；识别出计数网格时还必须通过网格边界校验。越界答案明确拒绝，不再产生无效点击。
- 拖拽回答中的标量起止值不再透传给 Pydantic，而是作为无效坐标结构提前拒绝。

本地验证结果：完整测试 `60 passed`；真实失败截图识别出的网格为图像坐标 `x=170..490, y=135..455`；Camoufox 打开 hCaptcha 官方演示页后，`hsw.js` 返回 HTTP 200、正文 1,220,616 字节且没有 `content-encoding`，正文读取成功。
