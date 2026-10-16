# 断语理论提炼 · 问题清单与执行手册

> 编制日期：2026-10-16 · 编制分支：`feat/theory-duanyu-20261016`
> 用途：本文档是本机（网络不通、无法访问 GitHub）完成全部本地勘察后整理的问题清单。**接手的 Agent 必须具备 GitHub 访问能力**，按本清单逐条执行。
> 事实源约定：规则数量等易漂移数据以执令时 `python tools/rule_status_scan.py --format markdown` 为准；本文数字为 2026-10-16 本地快照。

---

## 0. 执行前必读（硬约束）

1. **分支隔离**：本次提炼内容必须在独立分支进行（本机已建 `feat/theory-duanyu-20261016`，接手方可沿用或另建 `feat/theory-*`）。**禁止直接推 `main`，禁止 `git push --force`**——远端有另一 agent 的并行提交（origin/main 于 2026-10-15 有更新，另有 `local-sync-20260807`、`feat/cfl-c016-fixes`、`fix/c-2026-015-engine-render` 三个远端分支）。
2. **推送前探盘**：`git fetch origin` 后先执行 `git log --oneline main..origin/main` 与 `git diff origin/main --stat`，确认对方变更与本次路径（`theory/`、`tools/build_indexes.py`、`META/`）无重叠或评估重叠后再合。
3. **index.yaml 是自动生成文件**（文件头 `DO NOT EDIT BY HAND`）：一切规则数据变更必须通过改 `tools/build_indexes.py` 或其输入的 raw 文件后重新生成，**禁止手改 index**。冲突时不手工解冲突，采"接受远端版 → 重跑 build_indexes.py → 提交"。
4. **规则生命周期**：新提取规则只能标 `candidate`；晋升 `promoted`/`confirmed` 必须经案例反馈（`tools/feedback_ingest.py`）。规则状态批量变更须记入 `META/rule-changelog.md`。
5. **盲测边界**（AGENTS.md §6）：新断语不得以"已知答案下的报告吻合度"自证；生产 claim-rules 的启用必须走双核盲测封存核验流程。
6. **提交卫生**：只 `git add` 显式路径，禁止 `git add .`（`.workbuddy/` 已加入 `.gitignore`，本分支首个提交即此变更）。

---

## 1. 索引构建工具缺陷（`tools/build_indexes.py`）

### TD-01 · 任派 78 条领域规则话题错标为 `lifa`（P0）

- **现象**：`theory/ren/index.yaml` 中话题分布为 `lifa 138 / hunyin 22 / yingqi 20 / shensha 14 / unmapped 6`。任派 m3-rules-registry.md §19.10~§19.16 的领域章节（财运/官运/六亲/寿元/牢狱/职业）与 §19.3/§19.5 疾病章节全部落入 `lifa`，领域路由不可见。
- **错标明细**（78 条）：

| 章节（m3-rules-registry.md） | 规则 ID | 条数 | 应为 topic |
|---|---|---|---|
| §19.3 疾病诊断基础体系 | M3-R-061..080 | 20 | `jiankang` |
| §19.5 疾病诊断进阶体系 | M3-R-091..100 | 10 | `jiankang` |
| §19.10 财运判定完整体系 | M3-R-121..132 | 12 | `caiyun` |
| §19.11 官运判定完整体系 | M3-R-133..140 | 8 | `caiyun` |
| §19.12 六亲判定完整体系 | M3-R-141..150 | 10 | `liuqin` |
| §19.14 寿元判定完整体系 | M3-R-163..170 | 8 | `jiankang` |
| §19.15 牢狱判定完整体系 | M3-R-171..175 | 5 | `jiankang` |
| §19.16 职业判定完整体系 | M3-R-176..180 | 5 | `zhiye` |

- **根因**：`tools/build_indexes.py:322` `REN_SECTION_TO_TOPIC` 的键是源文件名风格（`"财运篇"`、`"官运篇"`），而 registry 实际章节标签是 `"财运判定完整体系"` 等表述，子串不匹配 → `extract_ren()`（:346）落入默认值 `lifa`。
- **修复**：在 `REN_SECTION_TO_TOPIC` **字典首部**插入下列键（dict 按插入序迭代、首个命中即停，必须置于现有 `"婚姻"` 键之前）：

```python
REN_SECTION_TO_TOPIC = {
    "疾病诊断": "jiankang",
    "财运判定": "caiyun",
    "官运判定": "caiyun",
    "六亲判定": "liuqin",
    "寿元判定": "jiankang",
    "牢狱判定": "jiankang",
    "职业判定": "zhiye",
    "职业/婚姻/六亲": "liuqin",   # §19.9 混合节，取六亲画像为最宽容器（schema 定义含配偶）
    "十八道法门": "lifa",         # ……以下保持原有键不变
```

- **验证**：`python tools/build_indexes.py && grep "^  topic:" theory/ren/index.yaml | sort | uniq -c`
  预期：`jiankang≈33 / caiyun≈20 / liuqin≈11 / zhiye=5`，`lifa` 从 138 降至约 60。
- **回归**：`pytest tests/ren_timing/test_rule_registry.py -q`（该测试引用 ren index）。

### TD-02 · 段派 128 条规则话题 `unmapped`，§20.x 章节无话题映射（P0）

- **现象**：`theory/duan/index.yaml` 290 条中 128 条 `topic: unmapped`，其中 M1-D-241..290（d-small 深读 50 条新规则）有 47 条 unmapped，其余为 m1-practice.md §20.2~§20.12 交叉引用的既有规则（如 157、192..197、204..210、44..50、78..82 等）。
- **根因**：`tools/build_indexes.py:99` `DUAN_TOPIC_BY_SECTION` 只有 `§17.x/§18.x`（m1-patterns.md）的 12 个键；m1-practice.md 的 `§20.1~§20.12` 章节头能匹配章节正则但查表落空 → `unmapped`。
- **修复**：向 `DUAN_TOPIC_BY_SECTION` 增加 12 个键：

```python
    "20.1":  ("jiaoyu",  "学历判定"),
    "20.2":  ("hunyin",  "婚姻判定"),
    "20.3":  ("liuqin",  "六亲判定"),
    "20.4":  ("zhiye",   "职业判定"),
    "20.5":  ("caiyun",  "财运判定"),
    "20.6":  ("jiankang","疾病判定"),
    "20.7":  ("jiankang","车祸判定"),
    "20.8":  ("jiankang","牢狱判定"),
    "20.9":  ("lifa",    "伤官五类"),
    "20.10": ("xiangfa", "象法+校验"),
    "20.11": ("lifa",    "干支虚实+互通+冲换象"),
    "20.12": ("caiyun",  "下岗辞职"),
```

  注意：`§20.13.x / §20.14.x` 子节标题（如 `20.13.1`）不匹配 `\d+\.\d+` 章节正则，其下均为审计表（`M1-D-001..004` 范围行），不会被误提取，无需处理。
- **验证**：重跑后 duan `unmapped` 应从 128 降至接近 0（仅剩无章节归属的兜底占位）。
- **回归**：`pytest tests/claims/test_executable_claim_rules.py -q`。

### TD-03 · 段派全部 290 条规则 `conclusion` 为空；d-small-theory.md 50 个 YAML 块未被解析（P0，断语内容核心增量）

- **现象**：duan index 无任何规则带 `conclusion` 字段。而 `theory/raw/duan/d-small-theory.md` 中存在 **50 个完整 YAML 规则块**（M1-D-241..290），每块含 `name / trigger.condition / conclusion / confidence_init / falsifiable_by / case_evidence`——这是段派断语集（D-11/D-12/D-13）+ 各专题手册已蒸馏但未入库的结构化断语。
- **样例**（M1-D-247）：`conclusion: 双坏同现→父母死亡；单坏→离异或缘薄非死`，`confidence_init: 4.5`，`falsifiable_by: 双坏但有原神救应仍存者`，3 条 case_evidence。
- **根因**：`extract_duan()`（:119）阶段 1/2 只解析 `| M1-D-\d+ | title |` 表格行，不解析 YAML 块。
- **修复**：在 `extract_duan()` 增加阶段 4 回填：

```python
def parse_dsmall_rule_blocks():
    """解析 d-small-theory.md 的 50 个 YAML 规则块，回填结论与置信初值。"""
    f = RAW / "duan" / "d-small-theory.md"
    if not f.exists():
        return {}
    blocks = {}
    for chunk in re.split(r"\n- rule_id: ", f.read_text(encoding="utf-8"))[1:]:
        rid = re.match(r"(M1-D-\d+)", chunk).group(1)
        def grab(field):
            m = re.search(rf"^  {field}: (.+)$", chunk, re.M)
            return m.group(1).strip() if m else ""
        blocks[rid] = {
            "conclusion": grab("conclusion"),
            "confidence": grab("confidence_init"),
            "falsifier": grab("falsifiable_by"),
        }
    return blocks
```

  在阶段 3（兜底）之后、`return` 之前：

```python
    # 阶段 4：从 d-small-theory.md YAML 块回填结论与置信初值（仅填空，不覆盖）
    for rid, blk in parse_dsmall_rule_blocks().items():
        r = rules.get(rid)
        if not r:
            continue
        if blk["conclusion"] and not r.get("conclusion"):
            r["conclusion"] = blk["conclusion"][:400]
        if blk["confidence"] and r.get("candidate_score") is None:
            try:
                r["candidate_score"] = float(blk["confidence"])
            except ValueError:
                pass
```

- **验证**：`grep -c "conclusion:" theory/duan/index.yaml` 应从 0 升至 ≥50；抽查 M1-D-247 的 conclusion 与上文样例一致。
- **备注**：`falsifiable_by` 与 `case_evidence` 目前不在 index schema（`theory/SCHEMA.md` v1.0）字段内，如后续要入库需先走 schema 变更流程，本轮不强行扩展。

### TD-04 · 杨派 §24 全量注册表 75 条规则身份污染（P1）

- **现象**：`theory/yang/index.yaml` 75 条 `topic: unmapped`（M2-Y-019..048 共 30 条 + M2-Y-119..163 共 45 条）。这些规则全部由 m2-rules-registry.md **§24 全量注册表**产生，存在三重污染：
  1. **标签泄漏**：§24 章节头不含 `M2-Y`，`extract_yang()`（:219）的章节条件 `"M2-Y" in line` 不成立，标签沿用上一节 §23 的 `"2019年班补全"`；
  2. **锚点入结论**：注册表行格式为 `| M2-Y-019 | 寻根基三步法 | §2.3 |`，第三列是**锚点**却被正则第 3 组当作 `conclusion` 写入（如 conclusion 内容为 `§2.3`）；
  3. **状态虚高**：注册表占位行被标 `status: promoted`，实际无提取内容、无案例验证。
- **根因**：`extract_yang()` 未区分"内容章节"与"ID 完整性注册表"。
- **修复**：在 `extract_yang()` 章节匹配分支增加注册表识别与行处理：

```python
        if sec_match:
            label = sec_match.group(1).strip()
            if "M2-Y" in line:
                current_section_label = label
                current_topic = "unmapped"
                for key, topic in section_topic_map.items():
                    if key in label:
                        current_topic = topic
                        break
                in_registry = False
            elif "注册表" in label:
                current_section_label = "全量注册表"
                current_topic = "unmapped"
                in_registry = True
            else:
                current_section_label = ""
                current_topic = "unmapped"
                in_registry = False
```

  规则行匹配分支中，`in_registry` 为真时：已存在的 ID 跳过；新 ID 建占位条目——`conclusion` 置空、第三列写入 `raw_anchor`、`status: "pending_normalization"`、`topic_label: "全量注册表"`。同时在 `section_topic_map` 增加 `"补全": "lifa"`（覆盖 §21/§22/§23 三个"班补全"父标签，子节会立即覆盖，无副作用）。
- **验证**：重跑后 75 条的 `conclusion` 不再匹配 `^§\d`；`status` 均为 `pending_normalization`；`grep "topic_label: \"2019年班补全\"" theory/yang/index.yaml` 仅剩 §23 真实 3 条（M2-Y-122/125/133，其话题经 `"补全": "lifa"` 归一）。
- **治理**：75 条状态由 promoted 降为 pending_normalization 属规则生命周期变更，须在 `META/rule-changelog.md` 记录。

### TD-05 · index.yaml 头部时间戳损坏（P2）

- **现象**：三个 index.yaml 头部均为 `# Generated at: 系统无法接受输入的日期。` + `输入新日期: (年月日)`——`build_indexes.py:425` 用 `os.popen("date -Iseconds")`，在本地化 Git Bash 环境 `date` 输出错误信息被原样写入文件。
- **修复**：改用 Python 标准库：

```python
timestamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
```

  （文件头需相应 `import datetime`；保持其余输出格式不变。）
- **验证**：重跑后头部为合法 ISO 8601 时间戳。

---

## 2. 语料提取缺口（raw → index）

### TD-06 · 高派车祸篇未提取（P1）

- **现象**：`sources/gao/2018弟子班_车祸篇_9页.md` 存在，但 `theory/raw/gao/extracted/` 无对应提取文件，`GAO_FILE_TO_SOURCE`（build_indexes.py:41）无映射 → 该篇零规则入 index。
- **修复**：按 `theory/raw/gao/extracted/高派_*_候选规律提取_2026-05-19.md` 既有格式（`| **GP-XX-NN** | 规律内容 | 原文锚点 | 拟入模块 | 候选等级 |` 表格行）提取车祸篇，落入 extracted/ 后在 `GAO_FILE_TO_SOURCE` 与 `GAO_PREFIX_TO_TOPIC` 补条目（车祸归 `jiankang`），重跑 build_indexes.py。新规则一律 `status: candidate`。
- **验证**：`grep -c "id: G-" theory/gao/index.yaml` 增加；新规则带 `raw_source: 2018弟子班_车祸篇_9页.md`。

### TD-07 · 杨派 M2-Y-019..048 / 119..163 真实内容缺失（P1）

- **现象**：§23 注记称 M2-Y-119..143 中 22 条"已在 §2/§5/§9/§10/§11 展开"，但 registry 这些章节**并无对应表格行**；M2-Y-019..048（30 条）在 §19~§23 内容节中完全缺失，仅存于 §24 注册表。即约 49~75 条杨派规则目前只有标题、无结论。
- **修复方向**：定位杨派原始讲义（`sources/yang/` 下 26 份，重点 `MinerU_markdown_01.杨清娟命理基础电子书261页` 与 `教学体系命例集细解245页`）中对应章节，按 TD-04 修复后的提取器补内容；暂无法定位的保持 `pending_normalization` 占位，不得虚标 promoted。
- **验证**：这些 ID 的 `conclusion` 非空且非锚点。

### TD-08 · 段派 263 例案例集未结构化（P2，验证素材）

- **现象**：`sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）` 未结构化。d-small-theory.md 仅将其定位为"验证库"（M1-D-289/290 两条元规则）。
- **修复方向**：建成案例索引（主题 × 触发规则 × 吻合度），作为 TD-01~TD-04 修复后规则晋升 promoted 的验证样本来源；不新增规则，只产验证数据。

---

## 3. 生产断语层与空白域（`theory/production/`）

### TD-09 · 生产 claim-rules 仅 18 条且覆盖不均（P2）

- **现状**：`claim-rules-v1.yaml` 10 条（DUAN 6 / GAO 3 / YANG 1）+ `ren-career-timing-rules-v1.yaml` 5 条 + `ziping-career-structure-rules-v1.yaml` 2 条。子平、滴天髓在生产断语层为 0 条独立 claim；高风险域（牢狱、寿夭、健康）无生产断语。
- **前提**：生产 claim-rules 每条需 `conditions / exclusions / counter_conditions / conclusion_template / falsifier / confidence cap` 六要素。**必须先完成 TD-01~TD-04 的话题与结论修复**，否则无可路由的断言语料；再按 AGENTS.md §6 走盲测，禁止以 known-facts 报告吻合度直接晋升。

### TD-10 · 空白域无系统规则（P2）

- **性格**：六源仅 2 条散规（高派"12神属性断人性格" candidate、段派"干支象法定性格" unmapped）。
- **子女**：无任何显式 topic 规则。
- **修复方向**：段派象法篇、任派十八道法门、三命通会六亲章节中提炼 candidate；入 index 前保持 candidate 状态。

---

## 4. 环境与推送附注（本机实测）

- **TD-11**：本机 `git fetch origin` 失败（`schannel: failed to receive handshake, SSL/TLS connection failed`），`gh` CLI 未安装。接手方环境需先确认 GitHub 可达与凭据有效（`git fetch origin` 成功即通）。
- **TD-12**：本机已备：隔离分支 `feat/theory-duanyu-20261016`（含 `.gitignore` 增补 `.workbuddy/` 一个提交）；本地 main 另领先 origin/main 2 个未推送提交（`9e41c57`、`e905b89`，facts 引擎，与本次无关），需单独确认后处理，**不得混入本次提炼提交**。
- **推送顺序建议**：TD-01/TD-02/TD-03/TD-05 为纯工具修复+重生成，可打一个提交；TD-04 与 TD-06/TD-07 因涉及规则生命周期变更，单独提交并在 `META/rule-changelog.md` 记录。

---

## 5. 执行顺序总览

```
TD-05（时间戳，5分钟）
  → TD-01 + TD-02 + TD-03（build_indexes.py 三处修复 + 重生成，一个提交）
    → 回归：pytest tests/ren_timing/test_rule_registry.py tests/claims/test_executable_claim_rules.py -q
    → TD-04（杨派注册表治理，单独提交 + changelog）
      → TD-06 / TD-07 / TD-08（语料补提，按 ingestion-protocol §I.1.3 分支 A）
        → TD-09 / TD-10（生产断语与空白域，须过盲测门）
```

> 每完成一条，在本文档对应条目追加"已完成 + 提交号 + 验证输出摘要"，保持清单可审计。
