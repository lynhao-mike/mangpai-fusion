# T-163 · `rule_contract_report` 加 `--out-prefix`（防止覆盖 v1）

- 状态：🔵 Ready for Execution
- 优先级：**P2（工具安全；T-156 已踩过一次）**
- 创建：2026-10-29（中枢）
- 依据：T-156 验收陷阱（工具写死 v1 路径，跑一次覆盖 v1）
- 前置：无

## 0. 一句话

`tools/rule_contract_report.py:52-53` 把输出路径写死为 `META/rule-contract-dryrun-v1.{json,md}`。
加 `--out-prefix` 参数，让调用方指定输出前缀；**默认保持 v1 路径**（不破坏现有用法），
但生成 v2 时不再需要手动备份/还原。

## 1. 现状（已核实）

- `OUT_JSON = ROOT / "META" / "rule-contract-dryrun-v1.json"`、`OUT_MD = ...-v1.md`（约 :52-53）。
- 每次运行都会写这两个文件；T-156 生成 v2 时只能「备份 v1 → 跑 → 按 SHA256 还原」。
- 工具本身只读规则与语料，不改产品代码；本卡只动输出路径参数，不动任何数字/判据。

## 2. 修法

1. `argparse` 增加 `--out-prefix PATH`：接受不带扩展名的路径前缀，例如
   `--out-prefix META/rule-contract-dryrun-v2`；实际写 `<prefix>.json` 与 `<prefix>.md`。
2. 默认值保持 `META/rule-contract-dryrun-v1` → 现有调用行为不变。
3. 控制台打印实际写出的两个路径。
4. 若前缀所在目录不存在 → 退出码 2，不写；若只写成功一个文件 → 报错退出码 2。
5. 不改任何统计逻辑、规则读取、表格输出。

## 3. 测试（新建 `tests/tools/test_rule_contract_report.py`）

用 `tmp_path` 作为前缀：

1. `--out-prefix <tmp>/dryrun-v9` → 生成 `dryrun-v9.json` 与 `dryrun-v9.md`，退出码 0；
2. 默认调用（不带参数）仍写 `META/rule-contract-dryrun-v1.*`（可在测试里 monkeypatch 路径，避免污染仓库）；
3. 目录不存在 → 退出码 2，且不产生文件；
4. 两次运行输出逐字节一致（可只比对 JSON 的数值字段）。

## 4. File Scope

**允许修改**

- `tools/rule_contract_report.py`

**允许新建**

- `tests/tools/test_rule_contract_report.py`

**只读**

- `theory/production/claim-rules-v1.yaml`
- `META/rule-contract-dryrun-v1.{json,md}`（对照，不改）
- `META/timing-eval-set-v1.json`

**禁止**

- 改统计逻辑、规则、阈值、v1 产物
- 改既有测试、`engine/**`、`theory/**`、`sources/**`
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest tests/tools/test_rule_contract_report.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m tools.rule_contract_report --out-prefix "$env:TEMP\t163-dryrun"   # 退出码 0
git status --porcelain META/rule-contract-dryrun-v1.json META/rule-contract-dryrun-v1.md       # 必须为空
.venv\Scripts\python.exe -m pytest -q                                                          # 0 failed
```

中枢额外检查：

- 默认调用仍写 v1（行为不变）；
- `--out-prefix` 写出的 JSON 数值与 v1 完全一致（只路径不同）；
- 不覆盖 v1。

## 6. 回报格式（`tasks/T-163/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（测试 + 用 tmp 前缀跑一次）
3. **未完成与风险**（默认值是否该改成必填、其他工具是否也有硬编码）
4. **下游须知**（参数格式、默认行为）

## 7. 禁止

- 不许改统计结果。
- 不许把默认路径改掉（会破坏现有调用）。
- 不许覆盖 v1 来「验证」。
