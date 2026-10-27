# ADR（Architecture Decision Record，架构决策记录）索引

> 本目录只记录**已裁决**的架构决策。讨论稿、待审稿、会话摘要一律不放这里。
> 一条 ADR 被新决策取代时，**不删不改原文**，只把状态改为 `superseded`（已被取代）并指向新条目。

## 状态词

| 状态 | 含义 | 能否作为实现依据 |
|---|---|---|
| `proposed`（提议中） | 已写出方案，尚未裁决 | 否 |
| `accepted`（已接受） | 决策人已明确同意 | 是 |
| `superseded`（已被取代） | 被更新的 ADR 替代，保留供追溯 | 否（按新条目执行） |
| `rejected`（已否决） | 讨论后被否，保留原因 | 否 |

## 当前条目

| 编号 | 标题 | 状态 | 日期 | 说明 |
|---|---|---|---|---|
| [ADR-001](ADR-001-engine-agent-boundary.md) | 引擎/Agent 边界 | accepted（已接受） | 2026-10-26 | 取代 `contracts/00-OVERVIEW.md` 决策 D「AI 仅润色」 |
| [ADR-002](ADR-002-delivery-vs-metric.md) | 交付与指标的双层记分 | accepted（已接受） | 2026-10-26 | 解决「交付优先 / 指标优先」之争 |
| [ADR-003](ADR-003-claim-conditions-and-school-routing.md) | 断语条件化与流派路由协议 | accepted（已接受） | 2026-10-26 | 回答「为什么人能用、系统不能」并给出四段协议 |
| [ADR-004](ADR-004-hub-commander-authority.md) | 中枢指挥官授权：完全自主重构及其边界 | accepted（已接受） | 2026-10-27 | 授权中枢指挥官重写已实现逻辑、改 `tests/`、退役 v5；保留三条红线 |
| [ADR-005](ADR-005-case-time-basis.md) | 排盘口径：案例必须声明 `time_basis`，引擎不做换算 | accepted（已接受） | 2026-10-27 | 定案 A1 前置：三值口径 + 证据强度字段 + 断语验证分层 |

## 与既有文档的关系

- `META/project-state.json` 的 `decision_log`（决策日志）字段指向本目录，作为机器可读入口。
- `plans/layered-decision-system.md` 是**设计论证**（L0–L9 分层、流派路由的完整推演），不是裁决；本目录的 ADR 才是裁决。
- ADR 只增不改；实施细节放契约（`engine/contracts/`），不放 ADR。
