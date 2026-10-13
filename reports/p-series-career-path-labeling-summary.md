# P 系列 76 案“任职 vs 经营”人工标注汇总

## 产物与口径

- 标注源：`cases/fankui-feedback.md`
- 结构化产物：`cases/p-series-career-path-labels.jsonl`
- 审核状态：全部为 `manual_reviewed`
- 标注原则：只采用每案反馈 section 中已发生的直接事实；不依据八字、收入、财运、学历、迁移或职业能力反推；歧义一律归入 `unknown`。

## 标签标准

| 标签 | 标准 |
|---|---|
| `employment` | 明确受雇、任职、上班、体制内、单位员工、固定岗位等。 |
| `entrepreneurship` | 明确经商、创业、开店、老板、自营、承包，或以经营为主要职业路径。 |
| `mixed` | 同一命主有实质任职与经营双路径，或按时间发生明确转换且两者均有可靠事实。 |
| `unknown` | 反馈不足以区分任职与经营；不为凑样本强标。 |

## 汇总统计

| 指标 | 数值 |
|---|---:|
| 总案例数 | 76 |
| employment | 32 |
| entrepreneurship | 5 |
| mixed | 3 |
| unknown | 36 |
| 非 unknown 有效案例 | 40 |
| 非 unknown 有效率 | 52.63% |

### 置信度分布

| 置信度 | 数量 |
|---|---:|
| high | 57 |
| medium | 15 |
| low | 4 |

## 二次复核队列

以下 19 案置信度为 `medium` 或 `low`，建议二次复核。保留 `unknown` 比错误强标更符合本任务契约。

| case_id | 当前标签 | 置信度 | 复核原因 |
|---|---|---|---|
| P-2026-004 | employment | medium | 明确大学毕业后参加工作，但单位和岗位关系未详。 |
| P-2026-005 | unknown | low | 只能证明存在工作活动，无法确认受雇或经营关系，按约束不强标。 |
| P-2026-014 | unknown | medium | 仅说明工作不顺且无官职，无法可靠区分受雇与经营。 |
| P-2026-015 | unknown | medium | 多次变换行业不等于明确任职或经营。 |
| P-2026-022 | unknown | medium | 仅确认事业稳定和有权力，未明确受雇或经营关系。 |
| P-2026-023 | employment | medium | 工作调动通常对应岗位任职，但反馈未载单位性质。 |
| P-2026-026 | unknown | medium | 仅说明工作不如意，无法区分任职与经营。 |
| P-2026-033 | unknown | medium | 仅确认能独当一面及有技能，不能确定任职或经营。 |
| P-2026-036 | unknown | low | 只确认有经商赚钱天分，不等于实际从事经营，按保守原则不强标。 |
| P-2026-038 | employment | medium | 频繁转职表明持续的职位任职路径，但单位性质未详。 |
| P-2026-039 | employment | medium | 明确曾身兼两职，支持任职路径，但雇佣关系细节不足。 |
| P-2026-040 | unknown | low | 工作地点信息不能确认雇佣或经营关系。 |
| P-2026-043 | unknown | medium | 程序员和技艺生财只说明工种及收入方式，未明确受雇或自营。 |
| P-2026-054 | unknown | medium | 事业波折和放弃仕进不足以确认实际任职关系或经营路径。 |
| P-2026-060 | employment | medium | 工资及工作不稳定支持受雇路径，但岗位与单位未详。 |
| P-2026-066 | unknown | medium | 仅有未获得好工作及大学期间几乎未打工的负向事实，不足以形成实质任职路径。 |
| P-2026-068 | unknown | low | 只能证明工作地点，无法确认雇佣或经营关系。 |
| P-2026-071 | employment | medium | 反复失业说明存在任职经历，但单位与岗位未详。 |
| P-2026-072 | employment | medium | 失业表明此前存在受雇活动，且明确否认做生意。 |

## 全部 76 案审计表

| case_id | 标签 | 置信度 | 直接证据原文 | 标注说明 | 复核状态 |
|---|---|---|---|---|---|
| P-2026-001 | entrepreneurship | high | 97年外出经商致富 | 明确外出经商并致富，经营路径成立。 | manual_reviewed |
| P-2026-002 | unknown | high |  | 反馈仅含婚姻、赌博与破财，无职业路径事实。 | manual_reviewed |
| P-2026-003 | unknown | high |  | 反馈仅含家庭破财与婚恋事件，无职业路径事实。 | manual_reviewed |
| P-2026-004 | employment | medium | 直到大学毕业参加工作后才补办结婚证 | 明确大学毕业后参加工作，但单位和岗位关系未详。 | manual_reviewed |
| P-2026-005 | unknown | low | 反馈时在非洲工作 | 只能证明存在工作活动，无法确认受雇或经营关系，按约束不强标。 | manual_reviewed |
| P-2026-006 | unknown | high |  | 职业信息均指向命主母亲，不可据此标注命主。 | manual_reviewed |
| P-2026-007 | employment | high | 同一岗位做了几年了，很顺手，效率也很高，事业运很不旺 | 明确长期在同一会计岗位工作。 | manual_reviewed |
| P-2026-008 | employment | high | 在电信部门打工，维修线路，属半体力劳动 | 明确在电信部门打工。 | manual_reviewed |
| P-2026-009 | employment | high | 上班打工（具体行业未提供） | 明确上班打工。 | manual_reviewed |
| P-2026-010 | unknown | high |  | 反馈无职业路径信息。 | manual_reviewed |
| P-2026-011 | employment | high | 13年工资及奖金85万 | 工资及奖金是明确受雇收入证据。 | manual_reviewed |
| P-2026-012 | unknown | high |  | 当时仍在读并准备求职，尚无已发生的任职或经营事实。 | manual_reviewed |
| P-2026-013 | employment | high | 参加工作 | 招工考试、培训后明确参加工作，后续还有失业事实。 | manual_reviewed |
| P-2026-014 | unknown | medium | 我工作方面一直不太顺 | 仅说明工作不顺且无官职，无法可靠区分受雇与经营。 | manual_reviewed |
| P-2026-015 | unknown | medium | 也好变换行业 | 多次变换行业不等于明确任职或经营。 | manual_reviewed |
| P-2026-016 | unknown | high | 和我姐姐一起 | 仅有共同做事业的计划，未证明实际发生任职或经营。 | manual_reviewed |
| P-2026-017 | employment | high | 4月份，为了更多收入我已经辞职，跳槽了、月薪过万，但无职 | 明确辞职、跳槽及月薪，属于受雇路径。 | manual_reviewed |
| P-2026-018 | employment | high | 事业上能得信任，很快便能任职务 | 命主确认已获信任并任职务。 | manual_reviewed |
| P-2026-019 | employment | high | 管人对，官还算不上 | 在单位负责管理人员，且工作未变，受雇路径明确。 | manual_reviewed |
| P-2026-020 | unknown | high |  | 反馈仅含受骗、丧父、负债和躲债，无职业路径事实。 | manual_reviewed |
| P-2026-021 | employment | high | 05年工作是有变动，单位和工种都没变，工作地址变了。从广州搬到东莞。 | 明确单位、工种不变而工作地点迁移，任职关系成立。 | manual_reviewed |
| P-2026-022 | unknown | medium | 恩~~慢慢开始稳定了~~ | 仅确认事业稳定和有权力，未明确受雇或经营关系。 | manual_reviewed |
| P-2026-023 | employment | medium | 上半年有调动 | 工作调动通常对应岗位任职，但反馈未载单位性质。 | manual_reviewed |
| P-2026-024 | unknown | high | 個人正在读书，大四实习当中 | 仅为在校实习，不能据此确定主要职业路径。 | manual_reviewed |
| P-2026-025 | employment | high | 以前在工商局上班好好的给跑出来的 | 明确曾在工商局上班，虽然后来离开但无经营事实。 | manual_reviewed |
| P-2026-026 | unknown | medium | 又經常破財，工作上也不見得如意 | 仅说明工作不如意，无法区分任职与经营。 | manual_reviewed |
| P-2026-027 | employment | high | 30多年来只要经历有风险的事（行政机关工作……）总能避过 | 明确在行政机关工作。 | manual_reviewed |
| P-2026-028 | unknown | high | 现在无业,在家天天上网 | 当前无业，反馈未提供此前命主职业路径。 | manual_reviewed |
| P-2026-029 | unknown | high |  | 反馈仅含学业、外貌及长辈信息，无职业路径事实。 | manual_reviewed |
| P-2026-030 | employment | high | 1、小职员 | 明确职业为小职员。 | manual_reviewed |
| P-2026-031 | employment | high | 现在在国企上班呢 | 明确在国企上班。 | manual_reviewed |
| P-2026-032 | unknown | high |  | 反馈仅含婚姻信息，无职业路径事实。 | manual_reviewed |
| P-2026-033 | unknown | medium | 也是正确的 | 仅确认能独当一面及有技能，不能确定任职或经营。 | manual_reviewed |
| P-2026-034 | employment | high | 做建筑的 | 背景明确为建筑行业上班族，且反馈提及所在单位。 | manual_reviewed |
| P-2026-035 | entrepreneurship | high | 事业多波折，经商有所发展 | 明确经商并有所发展。 | manual_reviewed |
| P-2026-036 | unknown | low | 对 | 只确认有经商赚钱天分，不等于实际从事经营，按保守原则不强标。 | manual_reviewed |
| P-2026-037 | entrepreneurship | high | 从商有地下活动、无证经营 | 明确从商且存在无证经营。 | manual_reviewed |
| P-2026-038 | employment | medium | 财运不安定，频繁转职 | 频繁转职表明持续的职位任职路径，但单位性质未详。 | manual_reviewed |
| P-2026-039 | employment | medium | 身兼2职就试得多了 | 明确曾身兼两职，支持任职路径，但雇佣关系细节不足。 | manual_reviewed |
| P-2026-040 | unknown | low | 我家现靠江，工作地也靠江 | 工作地点信息不能确认雇佣或经营关系。 | manual_reviewed |
| P-2026-041 | employment | high | 副处级，公路方面的！今年被双规了 | 明确为公路系统副处级官员。 | manual_reviewed |
| P-2026-042 | unknown | high |  | 学历、援交及交往经历不足以判定任职或经营职业路径。 | manual_reviewed |
| P-2026-043 | unknown | medium | 技艺生财 | 程序员和技艺生财只说明工种及收入方式，未明确受雇或自营。 | manual_reviewed |
| P-2026-044 | unknown | high |  | 反馈无明确职业路径事实。 | manual_reviewed |
| P-2026-045 | employment | high | 本来就想在公司慢慢打工到老算了。可是被裁员了 | 明确在公司打工并被裁员，后又找到新工作。 | manual_reviewed |
| P-2026-046 | employment | high | 2012年说要建房子才开始做一些工作，不过老在跳槽 | 明确开始工作并频繁跳槽，属于任职路径。 | manual_reviewed |
| P-2026-047 | mixed | high | 之前一直打工，因各种原因，去年开始创业 | 明确先长期打工，2012年转为创业，两个路径均有可靠事实。 | manual_reviewed |
| P-2026-048 | entrepreneurship | high | 前年合伙做生意，本来生意还可以，结果那人硬拆分，导致赔钱折算 | 明确与人合伙做生意。 | manual_reviewed |
| P-2026-049 | employment | high | 现在国企基层搞技术，至今无官 | 明确在国企基层技术岗位任职。 | manual_reviewed |
| P-2026-050 | unknown | high |  | 反馈仅含经济纠纷、拘押和释放，无职业路径事实。 | manual_reviewed |
| P-2026-051 | mixed | high | 06年离职，跟两个朋友合伙搞手机，没赚钱，还跟两个朋友有矛盾 | 明确先离职，随后与朋友合伙经营手机生意，任职与经营两路径均成立。 | manual_reviewed |
| P-2026-052 | unknown | high |  | 命主为儿童，反馈仅含家庭变故、伤残与就医。 | manual_reviewed |
| P-2026-053 | unknown | high |  | 命主仍在校，仅有机械技能兴趣与学习表现，无职业路径事实。 | manual_reviewed |
| P-2026-054 | unknown | medium | 我遭遇了两次重大波折，一次是05.06年……第一次是事业上的，我由此绝了仕进之心 | 事业波折和放弃仕进不足以确认实际任职关系或经营路径。 | manual_reviewed |
| P-2026-055 | employment | high | 31岁进体制，39有个小职务。口才差，确实有些闷葫芦。 | 明确进入体制并获得职务。 | manual_reviewed |
| P-2026-056 | employment | high | 虽然才正式工作了4年，但是已经换了好几份工作……职业道路和一开始算是完全改变了。 | 明确正式工作多年并更换多份工作。 | manual_reviewed |
| P-2026-057 | unknown | high |  | 反馈仅含学历及灾祸预测否定，无职业路径事实。 | manual_reviewed |
| P-2026-058 | employment | high | 我母亲这半辈子确实换过好几个单位，都是公办单位。做过老师，做过财务工作。 | 明确在多个公办单位任职，做过教师和财务。 | manual_reviewed |
| P-2026-059 | unknown | high |  | 反馈仅含求学退学与家庭事件，无职业路径事实。 | manual_reviewed |
| P-2026-060 | employment | medium | 工作一直不稳定，工资不高，没挣着钱。 | 工资及工作不稳定支持受雇路径，但岗位与单位未详。 | manual_reviewed |
| P-2026-061 | unknown | high |  | 命主本科在读并保研，尚无已发生职业路径事实。 | manual_reviewed |
| P-2026-062 | employment | high | 初中未毕业，打工。 | 明确外出打工。 | manual_reviewed |
| P-2026-063 | employment | high | 今年刚转正两个月又考上公务员了。 | 事业单位转正后考取公务员，体制任职路径明确。 | manual_reviewed |
| P-2026-064 | unknown | high |  | 反馈仅含两段感情结束事件，无职业路径事实。 | manual_reviewed |
| P-2026-065 | unknown | high |  | 经营小买卖的是命主妻子，不可转标为命主职业路径。 | manual_reviewed |
| P-2026-066 | unknown | medium | 这一年上的大学，身体不好几乎没打工。 | 仅有未获得好工作及大学期间几乎未打工的负向事实，不足以形成实质任职路径。 | manual_reviewed |
| P-2026-067 | mixed | high | 我创业好多次了都赔本了。 | 约17岁已参加工作，之后又多次创业，任职与经营双路径均有事实。 | manual_reviewed |
| P-2026-068 | unknown | low | 我祖籍是广东的，但生在东北长在东北工作在东北，很少回广东老家。 | 只能证明工作地点，无法确认雇佣或经营关系。 | manual_reviewed |
| P-2026-069 | unknown | high |  | 反馈仅含学历、父母去世及遗产，无职业路径事实。 | manual_reviewed |
| P-2026-070 | unknown | high |  | 命主为在读少年，反馈仅含健康和读书信息。 | manual_reviewed |
| P-2026-071 | employment | medium | 我的事业运特别差，总失业。 | 反复失业说明存在任职经历，但单位与岗位未详。 | manual_reviewed |
| P-2026-072 | employment | medium | 头胎是女儿，今年怀孕，失业在家。 | 失业表明此前存在受雇活动，且明确否认做生意。 | manual_reviewed |
| P-2026-073 | employment | high | 高中毕业后直升国家计划内本科大学，毕业后为乡镇干部。 | 明确毕业后任乡镇干部。 | manual_reviewed |
| P-2026-074 | employment | high | 丈夫早逝，婆家很恶，生活不如意，工作降职。 | 明确发生工作降职，属于岗位任职路径。 | manual_reviewed |
| P-2026-075 | entrepreneurship | high | 我创业好多次了都赔本了。 | 明确多次创业，经营路径成立；保险从业未载明雇佣关系。 | manual_reviewed |
| P-2026-076 | unknown | high |  | 反馈仅含留级、求学地区与早年家境，无职业路径事实。 | manual_reviewed |

## 可审计性说明

- 每个 `case_id` 恰好一条结构化记录。
- `evidence_quote` 保留源文件原文；无足够直接证据时为空字符串。
- `mixed` 的 `rationale` 明确记录任职与经营的先后或并存关系。
- 校验覆盖条数、ID 连续唯一性、枚举值、固定字段及证据在所属 section 内的逐字可检索性。
