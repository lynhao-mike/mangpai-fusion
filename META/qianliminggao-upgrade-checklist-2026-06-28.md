# 千里命稿系统升级执行清单 · 2026-06-28

> 目标：把 `sources/qianliminggao` 从孤立材料推进到可审、可绑定、可验证的子平候选升级包。
> 原则：先候选，后反馈，再生产；不直接改 `theory/ziping/index.yaml`。
> ponytail: 到这里先停，三份小文件已经覆盖审查闭环；别写脚本，除非同类升级重复第二次。

## 一、当前产物

| 产物 | 路径 | 用途 | 状态 |
|---|---|---|---|
| 候选理论提取 | `theory/raw/ziping/extracted/子平_千里命稿_候选理论提取_2026-06-28.md` | 30 条候选规则与证据锚点 | done |
| 去重审查清单 | `META/qianliminggao-upgrade-review-2026-06-28.md` | 裁出前 10 条、标记 keep/merge/drop/evidence_only | done |
| 反馈绑定草案 | `META/qianliminggao-feedback-bindings-2026-06-28.jsonl` | 前 10 条候选的反馈标签、命中/失验标准 | done |

## 二、人工执行顺序

1. 打开候选理论提取，快速核对 30 条候选是否忠于原文。
2. 打开去重审查清单，确认建议前 10 条是否保留。
3. 对 `merge` 条目写入合并对象，不新增规则 ID。
4. 对 `evidence_only` 条目确认是否只用于报告表达或治理原则。
5. 打开反馈绑定草案，逐条确认命中标准和失验标准是否可被案例反馈判断。
6. 仅当前 10 条都通过人工确认后，再考虑生成候选 YAML 或接入 statement 绑定。

## 三、禁止动作

- 不直接把 30 条写入 `theory/ziping/index.yaml`。
- 不把《千里命稿》新建成独立派别。
- 不把历史命例单案结论直接升级为通用规则。
- 不把 `evidence_only` 条目纳入 hit/miss 计分。
- 不为这一次性审查新增抽取脚本。

## 四、可进入下一阶段的条件

| 条件 | 验收方式 |
|---|---|
| 30 条候选已人审 | 每条有 keep/merge/drop/evidence_only 裁决 |
| 前 10 条可反馈绑定 | JSONL 每条都有 hit_criteria 与 miss_criteria |
| 重复候选已合并 | `merge` 条目有明确对照对象 |
| 证据型条目不计分 | `evidence_only` 不进入规则生命周期 |
| 生产规则仍未改动 | `theory/ziping/index.yaml` 无本次直接写入 |

## 五、最短下一步

人工先审 `META/qianliminggao-upgrade-review-2026-06-28.md` 的“建议前 10 条”。通过后，再把 `META/qianliminggao-feedback-bindings-2026-06-28.jsonl` 接到具体案例反馈。