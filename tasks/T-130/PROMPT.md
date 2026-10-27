# T-130 · 案例排盘口径普查（A1 收口）

- 状态：🔵 Ready for Execution
- 优先级：P0（阻塞 A1 与 B4 分层验证）
- 创建：2026-10-27（中枢）
- 决策依据：[`docs/adr/ADR-005-case-time-basis.md`](../../docs/adr/ADR-005-case-time-basis.md)

## 1. 背景

A1 长期卡住。ADR-005 已裁决口径语义，现在要把 485 个案例逐例判定成三元组：`time_basis` + `basis_evidence`。

**这不是改造案例**，是给案例做一次只读体检并输出机器可读清单。案例文件一个字都不许改。

## 2. 判定规则（严格按 ADR-005，不得自行发挥）

`time_basis` 三值：

| 值 | 判定条件 |
|---|---|
| `true_solar` | 有出生地经度且可复现换算；**或**案例内直接给出校正后的具体时刻 |
| `clock_beijing` | 只有钟表时间，未见校正证据 |
| `unknown` | 无可用出生时刻，或证据互相矛盾无法判定 |

`basis_evidence` 四值：`longitude_calc` / `explicit_time` / `label_only` / `none`

**硬规则：沉默一律 `unknown`，不得默认 `clock_beijing`。** 只有「真太阳时校正: true」字样而无经度、无校正后时刻 → `true_solar` + `label_only`。

案例元数据至少存在三种互不兼容写法，三种都要认（见 ADR-005 背景第 2 条）。

## 3. File Scope

- **新建** `tools/case_time_basis_audit.py`（只依赖标准库 + 项目 `.venv`）
- **新建** `META/case-time-basis-v1.json`（产物）
- **只读** `cases/*/input.md`、`cases/*/manifest.json`

**禁止修改** `cases/` 下任何文件、`theory/`、`sources/`、`engine/`。

## 4. 验收（中枢会亲自跑，看退出码）

```bash
.venv\Scripts\python.exe -m tools.case_time_basis_audit --json   # 退出码 0
```

输出必须满足：

1. 覆盖数 == `cases/*/input.md` 的目录数（现场数得出，当前为 485），逐个列出，不许抽样、不许跳过。
2. 每例两个字段齐全，取值在允许集合内。
3. `true_solar` / `clock_beijing` / `unknown` 三档计数之和 == 覆盖数。
4. `--summary` 模式下打印分档计数表。
5. `git status --porcelain cases/` 必须为空（证明没动案例）。

## 5. 回报格式（BRIEF.md）

必须包含：三档实际计数、`basis_evidence` 四值计数、`unknown` 中「确实无出生时刻」与「有时刻但判定不了」各多少、三种写法的各自命中数、以及你会怎么抽核 5 例证明判定没错（列出这 5 例 id）。
