# blind_ledger 使用说明 · 2026-10-17

> 配套代码：[`tools/blind_ledger.py`](../tools/blind_ledger.py)
> 配套测试：[`tests/tools/test_blind_ledger.py`](../tests/tools/test_blind_ledger.py)（24 tests，全过）
> 设计契约：`engine/contracts/22-dual-core-blind-validation-v1.md`

## 一、它解决什么问题

`META/six-month-capability-baseline-2026-07-15.json` 显示：六派 3840 次盲断里
195 条 claim 的 `observed_positive` **全是 None**——下了断语，但从未被评过对错。
六派 `accuracy` 全 0。

blind_ledger 就是补这个缺口：**把"下了什么断语"与"后来发生了什么"对上账。**

## 二、四个命令

### 1. seal —— 封存

```bash
python -m tools.blind_ledger seal \
  --case "C-2026-001-乾-庚申戊寅壬子辛丑" \
  --report reports/1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md \
  --mode blind \
  --sources cases/C-2026-001/input.md
```

- 对报告文本与 claims 各算一个 sha256，写入不可变快照；
- **claims 不手填**，从 v7 报告文末《附：关键依据索引与可核验断语表》机械解析；
- 解析不出任何 claim 会**拒绝封存**（防止零 claim 的假封存）。

**`--mode` 两种**：

| mode | 含义 | reveal |
|---|---|---|
| `blind` | 严格盲测：未读反馈前完成分析 | 允许 |
| `consult` | 普通咨询：已知事实可用 | 不允许（永久不标盲测） |

**`--sources` 是硬门禁**：blind 模式下若声明里出现 `feedback` / `analysis.md` /
`事件年表` / `known_facts` 等字样，**直接拒绝**。因为工具无法验证"封存前真的
没读过反馈"，只能把声明写进快照供事后审计——这是机械拦截，不是提醒。

### 2. reveal —— 揭示反馈

```bash
python -m tools.blind_ledger reveal \
  --case "C-2026-001-乾-庚申戊寅壬子辛丑" \
  --feedback cases/C-2026-001-乾-庚申戊寅壬子辛丑/feedback.md
```

- 仅 blind 模式可调用；**只能调一次**（防止反复读反馈改结论）；
- 对 feedback.md 也算 sha256。

### 3. adjudicate —— 逐条对账

```bash
python -m tools.blind_ledger adjudicate \
  --case "C-2026-001-乾-庚申戊寅壬子辛丑" \
  --round 1 --claim seq:1 \
  --verdict hit \
  --evidence "2013 年结婚，与'2027 丁未确定关系'的预测方向一致" \
  --rule M1-D-045
```

verdict 四选一：`hit` / `miss` / `partial` / `unverifiable`。

- **已对账的 claim 不可改**（返回错误）。要更正只能新增 round 重新分析；
- `--rule` 可省略，默认取该 claim 的首个规则 ID。

### 4. stats —— 统计

```bash
python -m tools.blind_ledger stats                    # 全部
python -m tools.blind_ledger stats --rule M1-D-045    # 按规则过滤
python -m tools.blind_ledger stats --matter career    # 按领域过滤
```

输出两级：

- **案例级**：已对账 claim 数 / hit 数 / 准确率
- **规则级**：每个 `rule_id` 的 n / hit / miss / partial / unverifiable / 命中率

> 本工具**只做统计，永不修改规则库**。规则修改须命理师确认。

## 三、数据落在哪

`META/blind_ledger/<case_id>.json`，单文件单案例，无跨案例状态。

```json
{
  "schema_version": "blind-ledger/v1",
  "case_id": "...",
  "mode": "blind",
  "rounds": [
    {
      "seq": 1,
      "sealed_at": "...",
      "report_file": "...",
      "report_sha256": "sha256:...",
      "claims_sha256": "sha256:...",
      "declared_sources": ["cases/.../input.md"],
      "claims": [
        {
          "claim_id": "seq:1",
          "seq": 1,
          "section": "一",
          "assertion": "杀印相生，扛责换权",
          "grade": "板上钉钉",
          "addrs": ["M.s", "Y.s"],
          "edges": ["e001", "e005"],
          "rule_ids": ["M1-D-045"]
        }
      ]
    }
  ],
  "reveal": {
    "revealed_at": "...",
    "feedback_file": "...",
    "feedback_sha256": "sha256:...",
    "outcomes": [
      {"round_seq": 1, "claim_id": "seq:1", "verdict": "hit",
       "evidence": "...", "rule_id": "M1-D-045", "version": 1}
    ]
  }
}
```

## 四、与 RF 案例 facts 的配合

`tools/rf_facts_hydrate.py` 已为 446 个 RF 案例落盘 `facts/all.json` 与
`facts/facts_summary.json`。典型工作流：

```bash
# 1. 确保有引擎事实（幂等，已有则跳过）
python -m tools.rf_facts_hydrate

# 2. 选案例 → 写 v7 人话报告（只依据 facts，不读 feedback.md）
# 3. 封存
python -m tools.blind_ledger seal --case <id> --report <file> --mode blind \
  --sources cases/<id>/input.md cases/<id>/facts/facts_summary.json

# 4. 揭示反馈
python -m tools.blind_ledger reveal --case <id> --feedback cases/<id>/feedback.md

# 5. 逐条对账
python -m tools.blind_ledger adjudicate --case <id> --round 1 --claim seq:1 \
  --verdict hit --evidence "..."

# 6. 统计
python -m tools.blind_ledger stats
```

## 五、已知边界（不是 bug）

1. **工具无法验证封存前真没读反馈**——只能靠 `--sources` 黑名单拦截 + 人工自律。
   这是设计边界：机械手段能防"不小心"，防不了"故意"。
2. **`_RULE_RE` 对四段式 ID（如 `DTS-CW-P3-20260606-001`）会截断到第三段**。
   实测这类 ID 在索引中极少，且 `source_ref` 字段兜底，不影响对账。
3. **pillar-only 案例没有 `siling` 与起运年份**，其流年只做原局引动。
   `facts_summary.json` 的 `input_limitations` 已标明，统计时可按
   `--matter` 过滤掉依赖这两项的断言。

## 六、测试覆盖

24 个测试，全部通过。关键几条：

| 测试 | 防什么 |
|---|---|
| `test_seal_rejects_zero_claims` | 零 claim 假封存 |
| `test_seal_rejects_duplicate_round` | 覆盖已封存 round |
| `test_seal_locks_mode` | blind/consult 中途互换 |
| `test_seal_detects_tampering` | 封存后改报告文本 |
| `test_seal_blind_rejects_feedback_sources` | 把非盲产物封成盲测 |
| `test_reveal_only_once` | 反复读反馈改结论 |
| `test_adjudicate_rejects_duplicate` | 对账结果被静默改写 |
| `test_parse_claims_on_real_benchmark_report` | 模板漂移导致解析失效 |
