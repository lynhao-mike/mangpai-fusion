# T-180 BRIEF · 化 actor 约定审计（只读）

- 状态：✅ 交付（只读审计 / 规格建议；未改 answers、hold-out、engine、规则、测试；未写代码；无 git 写操作；未跑评分器）
- 任务卡：`tasks/T-180/PROMPT.md`
- 产物：`META/p1-hua-actor-audit-v1.json`（四条逐条 + 五类化分条款 + defined16/v4 裁决）、
  `META/p1-hua-actor-audit-v1.md`（人读版，含 `actor-rules-v1.md` §4.8 修订建议）
- 一句话：**四条化 4/4 `engine_wrong`、0 `label_wrong`、0 `convention_conflict`**——原文「A化B／B被A化」的 A 是化者，
  五行上化者恒为**受生端**（卯生巳、寅生午、巳生辰、子生寅）；答案 `a/actor` 都取化者，引擎 `sheng` 候选
  `actor=members[0]=生端=被化者`，方向全反。**defined16 的 4 化算 `reversed`，defined16 不变（4/16 = 25.0%）**；
  冻结 v4 主分母仍 **20**，化计入失败，「16 暂定／化不进失败统计」撤回。

---

## 1. 改动文件

**新建**

| 文件 | 说明 |
|---|---|
| `META/p1-hua-actor-audit-v1.json` | 输入哈希、化的力向约定（19 条 basis + 语序两式）、四条逐条（clauses/roles/verdict/engine_observed）、总判定、defined16 裁决、freeze v4 建议、规则表分条款（官杀→印 / 财→杀 / 合化 / 从化 / 自化）、spec 修订文本、风险 |
| `META/p1-hua-actor-audit-v1.md` | 同内容人读版：证据链、五类分条款（source_ref + 正例 + 反例）、四条判定、三个「为什么不」、引擎修复规格、§4.8/§5.1 具体替换文本 |
| `tasks/T-180/BRIEF.md` | 本文件 |

**修改**

| 文件 | 改动 |
|---|---|
| `tasks/T-180/STATUS.md` | 追加 Execution Log 一行（+ 状态行改为「✅ 交付待验收」） |

**未改**：`META/p1-holdout-answers-v1.json`、`META/p1-holdout-v1.json`、`META/p1-holdout-freeze-v{2,3}.json`、
`META/p1-holdout-postfix-candidates-v1.json`、`META/p1-holdout-baseline-v1.json`、`engine/**`、`docs/**`、
`sources/**`、`tests/**`、`tools/**`。
**未做**：任何 git 写操作；未跑 `tools/p1_holdout_eval.py`（默认会覆盖基线产物）；未改 `docs/specs/actor-rules-v1.md`（只给建议）。

## 2. 原始输出

### 2.1 引擎现场复核（四条化的 sheng 候选，含 mode）

```text
$ .venv\Scripts\python.exe -m engine.cli all --pillars "<四柱>" --gender 乾 --json
  （过滤 relation_kind like 'sheng*'，打印 mode/kind/members/actor）

== 癸巳 乙卯 己巳 己巳 ==  (P1-H09, 己土)
  mode=化用  sheng(main_qi)  members=M.b,Y.b  actor=M.b      # 卯→巳，actor=被化者
  mode=化用  sheng(main_qi)  members=M.b,D.b  actor=M.b
  mode=化用  sheng(main_qi)  members=M.b,H.b  actor=M.b

== 戊午 戊午 戊午 甲寅 ==  (P1-H10, 戊土)
  mode=化用  sheng(main_qi)  members=H.b,Y.b  actor=H.b      # 寅→午
  mode=化用  sheng(main_qi)  members=H.b,M.b  actor=H.b
  mode=化用  sheng(main_qi)  members=H.b,D.b  actor=H.b

== 乙巳 己丑 庚午 庚辰 ==  (P1-H11, 庚金)
  mode=化用  sheng(main_qi)  members=Y.b,H.b  actor=Y.b      # 巳→辰（跨答案端点）
  mode=化用  sheng(main_qi)  members=Y.b,M.b  actor=Y.b      # 巳→丑（不跨）
  mode=化用  sheng(main_qi)  members=D.b,M.b  actor=D.b      # 午→丑（不跨）
  mode=化用  sheng(main_qi)  members=D.b,H.b  actor=D.b      # 午→辰（不跨）

== 乙巳 乙酉 戊子 甲寅 ==  (P1-H12, 戊土)
  mode=生泄用 sheng(main_qi)  members=D.b,H.b  actor=D.b     # 子→寅，不是化用
```

结论：H09–H11 是 `mode=化用`、H12 是 `mode=生泄用`；四条一律 `members=(被化者 b, 化者 a)`、`actor=b`。

### 2.2 post-fix 逐条 direction（复核裁决书数字）

```text
direction: ok=5  reversed=5  actor_none=7  no_edge=3          (20)
defined16: ok=4（墓 H13–H16）  reversed=4（化 H09–H12）  actor_none=6（制）  no_edge=2
           → 4/16 = 25.0%
```

### 2.3 quote 逐字校验（source_ref 行内命中）

```text
STRUCT+INLINE quote checks: 68 ok; 0 miss
  （basis 19 + engine code 4 + 四条 answer/clauses + 分条款正例/反例内联引用；
    校验脚本在 %TEMP%，未写入仓库）
```

两次修正记录（已改）：`30..命理珍宝_2056044626612874` → 实际 `2056044626612772864`；
`《盲派高级面授班笔记》` → 实际 `《盲派高级班面授班笔记》`（两条引用）。

### 2.4 两次运行 JSON 一致

```text
run1 canonical sha256 = run2 canonical sha256 = e941e8d5164bc8c962e10d4589d58c62bc1092c3551bb7749b50f06b9337131d
json file sha256 = bb603cdd168aaa436f5871b7515618e5d629b60e081d2d45e1d8299e76f98ccf
md   file sha256 = cd419b81102aa8a0280d32c06acf8d1844df424a4c6068021422dccb65e2cd8c
```

JSON 无时间戳/随机序；`json.dumps(sort_keys=True, ensure_ascii=False)` 两次独立进程哈希相同。

### 2.5 回归（未改代码，确认现状 0 failed）

```text
$ .venv\Scripts\python.exe -m pytest -q
1425 passed, 1 skipped, 1 warning in 144.68s     exit 0
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 脱敏脚本缺失（T-114 已知项）
```

与 `docs/reviews/p1-postfix-candidates-verdict-v1.md` 记录的 1425/1 一致。

## 3. 未完成与风险

1. **H12 修不到（中）**：H12 的化是 财→杀（水生木），引擎 `mode=生泄用`（化用谓词只认 官杀→印，
   `structure_check.py:L487-488`）。即使翻转化用 actor，H12 仍 `reversed`；要修须另卡立「财化杀／忌神受生化」子类
   （须原文判据，不能用 hold-out 反推），否则 v4 明记已知缺口。
2. **转化句的坑（中）**：`21:L1461`「七杀化印再生身」是不及物转化句，主语是被化者；若按语序标 actor 会把
   被化者当施力方（引擎现状）。规则表须显式写「转化句 actor=null」，否则将来会再出同类分歧。
3. **契约文档（中）**：`docs/specs/single-chart-analysis-v1.md:L165` 把「化」的方向契约写成「引擎 actor」；
   引擎修好前下游报告会照抄反端。该文档不在本卡 File Scope，需另卡同步。
4. **spec 自相矛盾（高，但属规格层）**：`actor-rules-v1.md` §0 规则 3 禁止「用五行流向代替句法主语」，
   §4.8 陷阱句却写「actor 恒为生者……不要写受方」，§5.1 化行又写「members[0]｜保持」——这两处正是四条 reversed 的成因，
   必须在另卡里按本审计 §9 的替换文本改掉。
5. **产物 header 过时（低）**：`META/p1-holdout-postfix-candidates-v1.json` 的 header 仍是
   `artifact=pre_fix_baseline` / `task=T-177`，与 post-fix 内容不符；引用以逐条 `direction` 为准。
6. **freeze v3 注记过时（低）**：`h13_note` 说 H13 修后仍 `no_candidate`；T-179 后 post-fix 已 `ok`。
7. **裁决书自相矛盾（低）**：§4 表格把 4 化记 reversed，§5 第 2 条又说 pending／不进失败统计；以 reversed 为准。
8. **无 Blocker**：审计可交付、规则可实施；剩余是中枢决策（v4 冻结、是否扩化用子类）与另卡的代码落地。

## 4. 下游须知

1. **判定**：四条化 **4/4 `engine_wrong`**；`label_wrong`=0、`convention_conflict`=0；a/b/actor 全部维持，不更正、不剔除。
2. **力向**：化者=受生端（被化者生入化者），化与生的力向相反；同一个字可同时是某边的化者、另一边的生者。
   H09 巳（卯生巳）、H10 午（寅生午）、H11 辰（巳生辰）、H12 寅（子生寅）。
3. **分条款**：官杀→印（化者=印）／财→杀（化者=杀，H12）／合化=null／从化=null／自化=null；
   每条都有 source_ref + 正例 + 反例，见审计 MD §3。
4. **defined16**：4 化算 **reversed**，defined16 仍是 **4/16 = 25.0%**；`definition_pending` 对四条作废，
   裁决书 §5.2 的「暂定 16／化不进失败统计」应撤回。
5. **冻结 v4**：主分母 **20**、defined16 只作诊断；阈值 80%/60% 不变；化计入失败；写清 H12 缺口；
   撤回「16 暂定」；修 freeze v3 的 h13 注记与 postfix header。
6. **修复按哪条规则**：只翻 `mode=化用` 的候选为 `members=(化者,被化者)`、`actor=化者`；
   **不得全局翻转** `sheng/生泄用`（会毁掉生）。副作用：`_binzhu` 不变（`_ti_yong_ends` 补位）、distance 无关、
   候选召回不变；`tests/facts/test_structure_check.py:L147-151` 与 `tests/api/test_engine_reset_regression.py:L135-136`
   的化用 fixture 须按新约定重写（ADR-004：可改测试，不得放宽断言）。
7. **顺序**：先冻结规则（spec 修订）→ 再改引擎 → 再跑 post-fix；不得用 hold-out 结果回头调规则。
