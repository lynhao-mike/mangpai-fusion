# T-149 BRIEF · `can_control` 克关系门 + 「力量相当」语义 + 基线刷新

- 执行：子代理（T-149）
- 完成时间：2026-10-28
- 依据：`tasks/T-149/PROMPT.md`；`docs/reviews/verdict-chatgpt6.md` §1.2 硬伤一 / §4.3 三处修正
- 范围：仅 File Scope 三文件，未扩范围；未 `git commit / push / checkout / stash / reset`

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/claims/condition_ir/atoms.py` | 只改 `can_control` 及其判据注释：① 旺衰比较前新增克关系门——复用已导入的 `engine.predicates.types.KE_MAP`（木克土、土克水、水克火、火克金、金克木；五行相克为命理常识，非本文推断，注释已写明），actor 不克 target 直接 `False`「不构成制：X不克Y」；② 同五行仍 `None`；③ 原判 `unknown` 的「力量相当 / 各有旺项 / 两党对抗」一档改判 `False`「力量相当，制不了（MinerU_22:1812/:1824）」；④ 同步修正函数 docstring 与上方判据注释中「力量相当即不可裁」「双方各有旺项一律 unknown」的旧表述 |
| `tests/claims/test_condition_ir_atoms.py` | ⑧ 区更新 6 条 → 9 条：重写标杆盘 B 用例（旧断言 `None` → `False`，docstring 写明旧判据为何错）；新增非克对参数化 3 例（木生火 / 水生木 / 反向相克）；反向方向用例的 note 断言随克关系门更新（`False` 不变）；补充「事实缺失仍为 unknown」用例 |
| `META/baseline-v1.json` | `--save` 生成：`pytest_passed 220 → 1043`、`zuogong_day_branch 350 → 346`，其余字段不变 |

**未改动**：`engine/facts/**`、`engine/api/**`、`theory/_ir/**`、`sources/**`、`theory/claims/**`、`engine/predicates/types.py`（只读复用 `KE_MAP`）、`pyproject.toml`、`AGENTS.md`。`git status` 为：上述 3 个文件 modified + 本卡 `BRIEF.md` / `STATUS.md` 两个新文件，无其他改动。

## 2. 判定语义（改后）

| 顺序 | 情形 | 返回 | note 关键片段 |
|---|---|---|---|
| 0 | actor / target 地址解析失败 | `None` | 无法把 actor/target 定位到原局地址 |
| 1 | 同五行 | `None` | actor 与 target 同属X，不构成对抗 |
| 2 | actor 五行不克 target 五行 | **`False`** | 不构成制：X不克Y |
| 3 | 确实相克 + facts 缺 `strength.climate.wuxing_layered` | `None` | facts 未提供五行层次计数 |
| 4 | 相克 + actor 旺项 ≥2 且 target 旺项 0 | `True` | 制得住（MinerU_22:1762） |
| 5 | 相克 + target 旺项 ≥2 且 actor 旺项 0 | `False` | 制不住（MinerU_22:1762） |
| 6 | 其余相克情形（力量相当 / 各有旺项 / 两党对抗） | **`False`** | 力量相当，制不了（MinerU_22:1812/:1824） |

阈值 `DUO_MIN=3 / GUA_MAX=1 / STRONG_MIN=2`、旺项/衰项定义、`SIDE_KE_KINDS` **一律未动**。

## 3. 旧判据为什么错（必须记录，涉及改断言）

旧测试 `test_plate_b_is_undecidable` 断言「力量相当 → `None`」；该判据与原文相反：

- `sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md:1812`
  「戌辰**力量相当，互相制不了**。」
- 同书 `:1824`「原局金水党和火土党对抗，**谁也制不了谁**。」

「制不了」是**确定的否定结论**，不是「不知道」。把这一档记为 `None`，等于用「不可裁」替换掉原文唯一给出的裁决点（`docs/reviews/verdict-chatgpt6.md` §1.2 第 37 行、§4.3 第 2 条明确指出）。因此这是**把错误判据改成原文判据**，不是删断言放水：

- 断言没有消失：`None` 改为 `False` 的**同时多断言** `"制不了" in note`；
- 判别力是变强不是变弱：该档从「交给人判」变成「按原文判制不了」；
- 另外两条真/假分支的断言（`True` / `False`）完全未动。

同时 `test_plate_a_reverse_direction_is_false` 的 note 断言由 `"制不住"` 改为 `"不构成制：火不克水"`：`value is False` 这个实质断言不变，只是克关系门先于旺衰比较触发，note 归因更准确（火不克水，而不是「水比火旺」）。

## 4. 自证四条（原始输出）

### 4.1 非克对返回假（盘 丁卯 癸卯 丁卯 癸卯）

```text
can_control({"actor": "Y.b", "target": "Y.s"})
  value=False
  note=不构成制：木不克火
```

Y.b 是卯（木），Y.s 是丁（火）：木生火，不克火。改前同一调用返回 `True` 且 note 写「制得住」（见 §5 改前交叉表：135 个非克 `True` 之一）。

### 4.2 真克对仍为真（标杆盘 A 癸丑 癸亥 辛亥 癸巳）

```text
can_control({"actor": "D.b", "target": "H.b"})
  value=True
  note=制者 水（Y.s/M.s/H.s/M.b/D.b）旺项[得令(亥月)、多(5字)]衰项[无]；被制 火（H.b）旺项[无]衰项[失令(亥月)、寡(1字)、受克(M.b(水)克火)] → 制得住（MinerU_22:1762 旺衰对句）
  bind={'actor_addr': 'D.b', 'target_addr': 'H.b'}
```

### 4.3 力量相当返回假（标杆盘 B 壬子 乙巳 庚子 壬午）

```text
can_control({"actor": "D.b", "target": "M.b"})
  value=False
  note=制者 水（Y.s/H.s/Y.b/D.b）旺项[多(4字)]衰项[失令(巳月)]；被制 火（M.b/H.b）旺项[得令(巳月)]衰项[受克(Y.b(水)克火)] → 力量相当，制不了（MinerU_22:1812/:1824「力量相当，互相制不了」）
```

（其余两对 `子→巳`、`子→午` 同为 `False`，note 含「力量相当」。）

### 4.4 基线 pytest_passed 与实际一致

```text
.venv\Scripts\python.exe -m pytest -q
→ 1043 passed, 1 skipped, 1 warning in 84.54s (0:01:24)   EXIT=0
  （skip = tests/tools/test_bundle_pii.py，AGENTS.md 记录的 T-114 过渡措施，非本卡引入）
  （最后只微调了 docstring 措辞，再复跑：1043 passed, 1 skipped in 83.80s，EXIT=0，数字不变）

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 1043 / failed 0 / pytest_rc 0 / audit_errors 0 / audit_rc 0 /
  relations_ok true / zuogong_charts 477 / zuogong_day_branch 346 / zuogong_rc 0  EXIT=0
```

`META/baseline-v1.json` 现为 `pytest_passed: 1043`，与上面两次实测（本机前台 pytest、`verify_baseline --save` 内部 pytest）一致。1040 → 1043 的 +3 来自本卡测试：`-1`（旧 plate B 用例重写）+ `+3`（非克对参数化 3 例）+ `+1`（事实缺失用例）= 净 +3。

## 5. 36 期铁口箓盘三值分布（改前 / 改后）

口径与 `verdict-chatgpt6.md` §7 的 `mp_probe_cc.py` 一致：题库里带性别且能解析真太阳时的 36 期，每盘 8 个原局地址（`Y.s…H.b`），枚举全部 `actor ≠ target` 且**五行不同**的有序对，共 **1578** 对。探针脚本在 `%TEMP%`（只读、不写仓库），未提交。

| 结果 | 改前 | 占比 | 改后 | 占比 |
|---|---:|---:|---:|---:|
| `True` 制得住 | 169 | 10.7% | **34** | 2.2% |
| `False` 制不住 | 169 | 10.7% | **1544** | 97.8% |
| `None` 未知 | 1240 | 78.6% | **0** | 0.0% |
| 合计 | 1578 | 100% | 1578 | 100% |

真克对（`KE_MAP[actor五行] == target五行`）与结果交叉表：

| 结果 | 改前 ke | 改前 非克 | 改后 ke | 改后 非克 |
|---|---:|---:|---:|---:|
| `True` | 34 | **135** | **34** | **0** |
| `False` | 45 | 124 | 359 | 1185 |
| `None` | 314 | 926 | **0** | **0** |

读法：

- 135 个「非克却判真」全部消失（`True` 里非克对 135 → 0），剩余 34 个 `True` 全是真克对——与复审「169 个真里 135 个（79.9%）是非克对」逐字复现（135/169 = 79.9%）。
- 非克对 1185 个现在**全部** `False`（135 + 124 + 926 = 1185 全部归入「不构成制」）。
- 未知 1240 → 0：这 1578 对只含异五行、地址全部可解析、facts 全部完整，恰好都不属于「未知只保留三种」；314 个原本落在「力量相当」的**真克对**按原文改判 `False`（制不了）。
- 改后分布随克关系门收紧是必然结果，不是 bug：`True` 只剩「确实克 + 制者极旺 + 被制全无旺项」的 34 对。

## 6. 基线新旧对比

| 字段 | 旧基线 | 新基线 | 说明 |
|---|---:|---:|---|
| `pytest_passed` | 220 | **1043** | 旧数字是更早（T-143/T-145 之前）的测量值，2026-10-27 写入文件时即已过期；T-145 记录当时实际已 1040，本卡 +3 条测试 → 1043 |
| `pytest_failed` | 0 | 0 | 未变 |
| `pytest_rc` | 0 | 0 | 未变 |
| `audit_errors` | 0 | 0 | 未变 |
| `audit_rc` | 0 | 0 | 未变 |
| `relations_ok` | true | true | 未变 |
| `relations_rc` | 0 | 0 | 未变 |
| `zuogong_charts` | 477 | 477 | 未变 |
| `zuogong_day_branch` | 350 | **346** | **下降 4**，见 §7 风险 2 |
| `zuogong_rc` | 0 | 0 | 未变 |
| `quick` | false | false | 未变 |

`zuogong_charts` 未变、`audit_errors` 仍 0、`relations_ok` 仍 true → 无「上升即退步」的指标恶化。

## 7. 未完成与风险

1. **契约 23 与代码现在不一致（不在本卡 File Scope，未改，必须由中枢处理）**：
   `engine/contracts/23-claim-condition-protocol-v1.md:227` 仍写「`unknown` 力量相当不可裁」、
   `:234` 仍写「双方各有旺项时，`unknown` 不是算不出来，而是原文的结论」、
   `:245` 判定表仍把「其余全部情形（双方均有根气 / 两党对抗 / 力量相当）」列为 `unknown`。
   T-149 后这三处都与实现相反。建议升级契约 23 到 v1.3 并补 §九 变更登记。
2. **`zuogong_day_branch` 350 → 346（-4）不是本卡造成的**：本卡只改 `atoms.py` / 测试 / 基线；
   `tools/zuogong_probe.py` 不 import `condition_ir` 或 `can_control`（已检索确认）。
   旧基线写于 2026-10-27 09:33，其后 `2ad78e49`（2026-10-27 16:15，`fix(facts)+test: 体用 SSOT 修 _crosses`）
   改了事实层，是最可能的来源。`tools/verify_baseline.py:71-84` 的 `regressions()` **并不把
   `zuogong_day_branch` 列为退步项**，故 `--compare` 不会报；按 ADR-004 红线三仍在此写明，请中枢裁决是否接受 346。
3. **未补的测试**：`verdict-chatgpt6.md` §4.3 第 3 点还要求覆盖「原局 301 个制用候选中的冲/刑/穿」。
   那 56 个候选的 `actor is None`，属事实层 `engine/facts/structure_check.py:475-478` 的方向绑定问题，
   超出本卡 File Scope（本卡只修原子语义），未做。
4. **`None` 在本次压力测试上降到 0** 不等于「永远不会未知」：地址解析失败 / 事实缺失 / 同五行
   三类仍由测试覆盖（新增「缺 `wuxing_layered` → unknown」用例）。
5. **`_resolve_natal` 单字多命中只取首个地址**（如某字在同柱重复出现）是旧行为，本卡未动；
   若下游发现方向歧义需另开卡。
6. **`False` 现在承载三种不同语义**（不克 / 制不住 / 力量相当），调用方若只看布尔值会丢信息；
   note 前缀可区分（`不构成制：` / `制不住` / `力量相当，制不了`）。断语层接入时应按 note 分派。

## 8. 下游须知

- 任何「能否制住」的调用现在都可拿到**确定布尔**（除三种未知），`False` 不再意味着「需要人判」。
- 若按 T-147 的思路把 `can_control` 接进断语：克关系门会把「生我 / 我生 / 反向克」类误配全部挡成 `False`，
  但 `False` 仍包含「力量相当」这一档，**不要**把 `False` 直接读成「对方旺、我方衰」。
- 契约 23 §4.8、`tasks/T-145/BRIEF.md` §2.5 与 `:1812` 相关表述已过期，引用时以本 BRIEF §2 为准。
- 未 commit / 未 push；`META/baseline-v1.json` 由 `--save` 直接生成，未手改数字。
