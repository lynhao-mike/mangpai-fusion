# as-of root_level gate 三案例严格盲断验证（2026-07-30）

## 1. 验证目标与隔离协议

本轮对 3 个此前无 `asof-blind-freeze.json`、无 `asof-feedback-verdict.json` 的 RF 案例执行两阶段验证：

1. 冻结前仅读取 `input.md` 的盲态视图、公共年度门控结果和理论库；不读取对应 `feedback.md`，不读取候选报告中的反馈摘要。
2. 先独立形成职业中心、备选、`root_level`、完成方式和年度候选，再实际调用 `search_theory()`。
3. 调用 `build_natal_capacity_graph()`、`build_annual_traces_with_gate()`、`evaluate_event_candidate()` 与更新后的 `run_contract_gate()`。
4. 契约门通过后，以 create-only 方式写入冻结文件并从盘独立复算 SHA-256。
5. 仅在 SHA 一致后揭示对应反馈，以独立裁决文件记录职业基本面、备选和 E1。

三案 `truncate_blind_section()` 均未找到边界，未将“无边界”默认视为安全。人工豁免仅在以下条件同时满足时成立：`known_facts` 严格等于空列表、`detect_table_embedded_annotation()` 返回空、冻结中显式记录 `no_boundary_manual_exception=true`。RF 自动排盘输入缺少严格 preflight 的完整字段，本轮采用 `RF_AUTO_PAIPAN_BLIND_EMPTY_FACTS` 兼容适配，未声称 strict preflight 通过。

## 2. 汇总结果

| case_id | root_level | root shortcut | 理论采纳 | 查库改变判断 | 正式 E1 | 职业中心裁决 | E1 裁决 | 冻结 SHA-256 |
|---|---|---:|---|---:|---:|---|---|---|
| C-2026-RF000032-乾-庚辰丙戌丙寅辛卯 | WEAK_ROOT | false | gao:G-CS-035 | false | 2001 | ABSTAIN | ABSTAIN | `f4c350eaab5d400552b2096be5c2b6e3fd19c23baef355a71205dc48e50d25f7` |
| C-2026-RF000169-乾-丁卯辛亥甲申辛未 | STRONG_ROOT | false | ziping:ZP-PROD-20260622-292 | false | 1997 | CENTER_HIT | ABSTAIN | `649acbfe3a03b89782d6bfc9c28903169eb09d6a94bb14e003c245f299c878a4` |
| C-2026-RF000193-乾-庚辰乙酉丁亥丙午 | STRONG_ROOT | false | ziping:ZP-PROD-20260622-439 | false | 2012 | ABSTAIN | ABSTAIN | `ecae9f55463c39152539dc90fc5f5081d6cb6437cdbf093e2bc9853a6d5c9561` |

三案 `run_contract_gate()` 均为 `passes_gate=true`，理论证据硬门通过；两个 `STRONG_ROOT` 案例的 `root_level_finding.likely_shortcut` 均为 `false`。RF000032 为 `WEAK_ROOT`，root shortcut 启发式只对 `STRONG_ROOT` 运行，冻结中仍显式记录 `false`。

## 3. 分案记录

### 3.1 C-2026-RF000032-乾-庚辰丙戌丙寅辛卯

- 冻结中心：以专业技能与持续输出为主，收入更可能通过项目成果或市场化交付兑现。
- `root_level=WEAK_ROOT`：事业功能定位在戌、辰所藏食神/伤官节点，食伤向年干庚偏财、时干辛正财形成“输出到收益”路径；食伤未透且兑现链隔层，不以日主根气替代事业证据。
- 理论检索：
  - `伤官 + 生财`：30 条命中；采纳 `gao:G-CS-035`。
  - `正财 + 透出`：2 条命中。
  - `偏财 + 透出`：4 条命中。
- 查库后判断：不变。命中支持“专业输出向收益兑现”的既有方向，未出现足以改写中心的反证。
- 正式 E1：2001 年成长阶段的家庭资源、照护安排或生活环境调整。年度轨迹真实越过 L1+L2 门，公共事件 API 返回 `CANDIDATE_FROZEN`。
- 反馈裁决：反馈只记录 2024 年辞职并准备跨专业考研，无法核验持续专业输出、项目成果或市场交付机制，职业中心 `ABSTAIN`；2001 年无反馈材料，E1 `ABSTAIN`，不进入日期事件分母。
- 产物：
  - `cases/C-2026-RF000032-乾-庚辰丙戌丙寅辛卯/asof-blind-freeze.json`
  - `cases/C-2026-RF000032-乾-庚辰丙戌丙寅辛卯/asof-feedback-verdict.json`

### 3.2 C-2026-RF000169-乾-丁卯辛亥甲申辛未

- 冻结中心：更适合规则明确的组织或专业体系，以责任、资格与规范执行建立职业位置。
- `root_level=STRONG_ROOT`：月干、时干辛正官双透，日支申中庚七杀为贴身压力节点，月支亥中壬印承接官杀并向甲木日主转化；领域节点与承载路径明确，不以长生或一般木根证明强根。
- 理论检索：
  - `正官 + 透出`：7 条命中；采纳 `ziping:ZP-PROD-20260622-292`。
  - `七杀 + 制化`：1 条命中。
  - `正印 + 化杀`：0 条命中，保留真实零命中审计。
- 查库后判断：不变。正官透出命中支持组织规则与责任位置方向；零命中组未被伪造为证据。
- 正式 E1：1997 年学习环境、家庭安排或居住节奏调整。年度轨迹真实越门，公共事件 API 返回 `CANDIDATE_FROZEN`。
- 反馈裁决：2017 年进入国企且明确“非常稳定”，职业中心 `CENTER_HIT`；2022—2024 年事业转差、单位挤兑并强迫离职，使“兑现不稳、组织压力反复”备选 `ALTERNATIVE_HIT`。反馈最早事实为 2006 年，不能挪入 1997 单年窗口，E1 `ABSTAIN`。
- 产物：
  - `cases/C-2026-RF000169-乾-丁卯辛亥甲申辛未/asof-blind-freeze.json`
  - `cases/C-2026-RF000169-乾-丁卯辛亥甲申辛未/asof-feedback-verdict.json`

### 3.3 C-2026-RF000193-乾-庚辰乙酉丁亥丙午

- 冻结中心：职业更可能落在组织化专业岗位，以知识资质承接规则压力，并兼顾资源或业务结果。
- `root_level=STRONG_ROOT`：日支亥中壬正官、月干乙偏印、年干庚与月支酉中辛财星构成“官—印—日主”和“财—官”双路径；不以午禄根或比劫帮身替代领域定位。
- 理论检索：
  - `七杀 + 制化`：1 条命中。
  - `正财 + 生官`：2 条命中；采纳 `ziping:ZP-PROD-20260622-439`。
  - `偏印 + 化杀`：0 条命中，保留真实零命中审计。
- 查库后判断：不变。财生官命中支持资源或业务结果向组织责任承载的既有方向。
- E1 门控修正：查库前草稿曾列 2008，但 2008 仅为 preflight high，未通过公共年度 L1+L2 crossed gate。冻结没有伪造通过结果，正式 E1 改为真实越门的 2012 年；公共事件 API 返回 `CANDIDATE_FROZEN`。
- 反馈裁决：反馈说明 2024 年从事医疗器械类工作但工作不稳定并被裁员。行业标签不足以补全知识资质、规则责任或业务结果机制，职业中心 `ABSTAIN`；2012 年无反馈，E1 `ABSTAIN`。2008 年反馈为疝气手术，只能说明被拒绝的预览年出现健康事件，不能挪作 2012 E1 的命中或反证。
- 产物：
  - `cases/C-2026-RF000193-乾-庚辰乙酉丁亥丙午/asof-blind-freeze.json`
  - `cases/C-2026-RF000193-乾-庚辰乙酉丁亥丙午/asof-feedback-verdict.json`

## 4. 方法结论

1. **root gate 的直接收益**：两个强根案例均必须写出事业十神/宫位节点和承载路径，且 `likely_shortcut=false`；未以日主临官、长生、帝旺或一般帮身替代事业领域证据。
2. **理论硬门有效但不等于正确性证明**：九组关键词均为“十神名 + 动作词”，真实命中和零命中都进入审计；三案查库均未改变盲态中心判断。
3. **年度门控阻止了后验伪造**：RF000193 的 2008 年在反馈中确有事件，但冻结前公共 API 未越门，因此没有因事后看到 2008 手术而回写 E1；正式 E1 使用 2012，最终因反馈缺失裁为 `ABSTAIN`。
4. **ABSTAIN 保护分母**：三案 E1 均没有对应单年反馈，故全部不进入日期事件分母。缺失事实不是 `MISS`。
5. **当前样本不能证明日期预测精度**：本轮 E1 可评价数为 0；可确认的是隔离、契约门、root shortcut 检查、create-only 冻结、SHA 绑定和反馈后不回写协议均按要求执行。

## 5. 证据边界

- 本报告不声称 strict preflight 通过。
- 公共 `LifeEventCandidate` 原型固定为 career 域；幼年学习/家庭描述只作为年度双证据门候选，不能据 API 的 `domain=career` 冒充现实职业事实。
- 理论命中支持结构解释，不独立证明现实因果。
- 反馈只用于冻结后的现实核验，不回写中心、E1 或 `root_level`。
- 所有最终裁决以各案 `asof-feedback-verdict.json` 为准，冻结内容以对应 SHA-256 绑定的 `asof-blind-freeze.json` 为准。
