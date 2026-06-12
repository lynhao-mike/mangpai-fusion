# P1-1 Rule Family Audit Final

审计范围：

- theory/ziping/index.yaml
- theory/tiaohou_ditiansui/index.yaml

审计性质：Theory Governance 只读审计。本报告基于 META/rule-family-discovery.md 生成 family-level 聚类字段，用于未来校准投票去重设计；不修改规则文件、权重或 Schema，不写入生产库。

核心约束：同一 family 内多条规则在校准投票中只贡献一次主票；其余规则只作为解释、细分证据或辅助证据参与。

默认字段：

- family_weight: 1.0
- main_vote_policy: one_main_vote_per_family
- duplicate_vote_control: shared_evidence_keys 命中同源证据时去重

---

## 1. Family-Level 聚类清单

### Family-ID: FAM-001

Family-Name: 用神 / 取用 / 喜忌 / 成败救应

Rule Count: 17

Rule IDs:

- ZP-PROD-20260605-001
- ZP-PROD-20260605-003
- ZP-PROD-20260605-005
- ZP-PROD-20260605-006
- ZP-PROD-20260605-008
- ZP-PROD-20260605-010
- ZP-PROD-20260606-004
- ZP-PROD-20260606-005
- ZP-PROD-20260606-007
- ZP-PROD-20260606-034
- ZP-PROD-20260606-038
- ZP-PROD-20260606-039
- DTS-PROD-20260605-007
- DTS-PROD-20260605-014
- DTS-PROD-20260606-057
- DTS-PROD-20260606-062
- DTS-PROD-20260606-090

Shared Evidence Keys:

- yongshen定位
- yongshen来源_月令透藏
- yongshen成败
- yongshen受克救应
- 喜忌取裁
- 有情无情
- 相神护卫
- 跨类别取用

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：用神定位、成败、救应、应用域分层处理。一次命局只允许“用神定位/取用主裁”贡献一次主票；救应、相神、有情无情仅作为同 family 内辅助证据。

### Family-ID: FAM-002

Family-Name: 扶抑 / 旺衰 / 身强身弱 / 太过不及

Rule Count: 13

Rule IDs:

- ZP-PROD-20260605-004
- ZP-PROD-20260606-002
- ZP-PROD-20260606-004
- ZP-PROD-20260606-013
- DTS-PROD-20260605-006
- DTS-PROD-20260605-008
- DTS-PROD-20260605-011
- DTS-PROD-20260605-012
- DTS-PROD-20260605-015
- DTS-PROD-20260606-057
- DTS-PROD-20260606-059
- DTS-PROD-20260606-061
- DTS-PROD-20260606-062

Shared Evidence Keys:

- 日主强弱
- 月令得失
- 旺相休囚
- 衰旺进退
- 太过不及
- 扶抑去留
- 顺极势

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：旺衰判断作为上游 evidence feature；日主强弱、月令旺衰、太过不及不得分别累加为多张主票。

### Family-ID: FAM-003

Family-Name: 中和 / 偏枯 / 有病有药 / 补偏却余

Rule Count: 10

Rule IDs:

- ZP-PROD-20260605-001
- ZP-PROD-20260605-009
- ZP-PROD-20260606-013
- ZP-PROD-20260606-025
- DTS-PROD-20260605-001
- DTS-PROD-20260605-004
- DTS-PROD-20260605-013
- DTS-PROD-20260605-020
- DTS-PROD-20260606-062
- DTS-PROD-20260606-213

Shared Evidence Keys:

- 中和状态
- 偏枯点
- 有病有药
- 补偏却余
- 五行太过不及
- 性情偏枯外化

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：中和/偏枯是跨域基础判断，应作为 family gate；健康、性情、格局中的同源偏枯证据只允许继承，不再独立主投票。

### Family-ID: FAM-004

Family-Name: 调候 / 寒暖 / 燥湿 / 季令气候

Rule Count: 24

Rule IDs:

- ZP-PROD-20260605-009
- ZP-PROD-20260606-017
- ZP-PROD-20260606-018
- ZP-PROD-20260606-019
- ZP-PROD-20260606-020
- ZP-PROD-20260606-025
- ZP-PROD-20260606-028
- ZP-PROD-20260606-029
- ZP-PROD-20260606-030
- ZP-PROD-20260606-034
- ZP-PROD-20260606-036
- ZP-PROD-20260606-037
- ZP-PROD-20260606-038
- ZP-PROD-20260606-039
- DTS-PROD-20260605-019
- DTS-PROD-20260605-020
- DTS-PROD-20260606-093
- DTS-PROD-20260606-094
- DTS-PROD-20260606-096
- DTS-PROD-20260606-097
- DTS-PROD-20260606-102
- DTS-PROD-20260606-103
- DTS-PROD-20260606-108
- DTS-PROD-20260606-113

Shared Evidence Keys:

- 寒暖状态
- 燥湿状态
- 月令季节
- 十干调候用神
- 火暖需求
- 水润需求
- 土燥土湿
- 坎离升降
- 震兑调济

Family Weight: 1.0

Potential Duplicate Vote Risk: CRITICAL

去重策略：调候 family 必须设置 family-level cap。同一寒暖燥湿证据链只产生一次主票；十干取用、坎离震兑、燥湿寒暖细则作为解释层或条件细分，不再叠加主票。

### Family-ID: FAM-005

Family-Name: 顺逆 / 顺势 / 流通 / 通关 / 源流

Rule Count: 15

Rule IDs:

- ZP-PROD-20260605-008
- ZP-PROD-20260606-001
- ZP-PROD-20260606-003
- ZP-PROD-20260606-006
- ZP-PROD-20260606-014
- ZP-PROD-20260606-015
- ZP-PROD-20260606-037
- DTS-PROD-20260605-005
- DTS-PROD-20260605-009
- DTS-PROD-20260605-016
- DTS-PROD-20260606-063
- DTS-PROD-20260606-064
- DTS-PROD-20260606-065
- DTS-PROD-20260606-090
- DTS-PROD-20260606-091

Shared Evidence Keys:

- 气机顺逆
- 源流起止
- 通关物
- 阻隔点
- 生克连续性
- 来去流向
- 有情顺接

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：气机连续性只提供一次主票；源流、通关、顺逆、来去流向在同一证据链命中时合并为一条 family-level finding。

### Family-ID: FAM-006

Family-Name: 合冲刑害 / 冲动 / 冲开 / 发用

Rule Count: 14

Rule IDs:

- ZP-PROD-20260605-006
- ZP-PROD-20260606-003
- ZP-PROD-20260606-009
- ZP-PROD-20260606-010
- ZP-PROD-20260606-011
- ZP-PROD-20260606-012
- ZP-PROD-20260606-016
- DTS-PROD-20260605-002
- DTS-PROD-20260605-011
- DTS-PROD-20260605-012
- DTS-PROD-20260605-018
- DTS-PROD-20260606-168
- DTS-PROD-20260606-169
- DTS-PROD-20260606-170

Shared Evidence Keys:

- 合冲刑害关系
- 冲动对象
- 喜忌强弱
- 冲开库钥匙
- 去凶激凶
- 运岁触发
- 六亲落点

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：合冲刑害先生成一个改局/触发 family finding；库、六亲、运岁、救应只引用该 finding，不重复主投票。

### Family-ID: FAM-007

Family-Name: 格局成败 / 层级 / 纯杂 / 有情 / 护卫

Rule Count: 12

Rule IDs:

- ZP-PROD-20260605-005
- ZP-PROD-20260605-007
- ZP-PROD-20260605-008
- ZP-PROD-20260605-010
- ZP-PROD-20260605-011
- ZP-PROD-20260605-012
- ZP-PROD-20260605-015
- ZP-PROD-20260606-005
- DTS-PROD-20260605-013
- DTS-PROD-20260606-079
- DTS-PROD-20260606-080
- DTS-PROD-20260606-082

Shared Evidence Keys:

- 格局成立
- 格局破败
- 纯杂状态
- 有情无情
- 护卫周全
- 相神状态
- 层级高低

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：格局成败作为结构结论只投一次主票；纯杂、有情、护卫、相神作为评分维度，不各自独立主投。

### Family-ID: FAM-008

Family-Name: 清浊 / 清气 / 清枯 / 澄浊求清

Rule Count: 8

Rule IDs:

- ZP-PROD-20260605-007
- ZP-PROD-20260605-011
- ZP-PROD-20260605-015
- DTS-PROD-20260606-079
- DTS-PROD-20260606-080
- DTS-PROD-20260606-081
- DTS-PROD-20260606-082
- DTS-PROD-20260606-216

Shared Evidence Keys:

- 清气
- 浊气
- 清中枯
- 澄浊求清
- 官格清纯
- 科名清气

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：清浊判断作为格局质地 evidence，只贡献一次主票；科名、官格、层级引用同一清气 finding。

### Family-ID: FAM-009

Family-Name: 财官承载 / 财官相生 / 财官取用

Rule Count: 11

Rule IDs:

- ZP-PROD-20260605-002
- ZP-PROD-20260605-011
- ZP-PROD-20260605-013
- ZP-PROD-20260606-004
- ZP-PROD-20260606-005
- ZP-PROD-20260606-009
- DTS-PROD-20260606-219
- DTS-PROD-20260606-220
- DTS-PROD-20260606-221
- DTS-PROD-20260606-222
- DTS-PROD-20260606-223

Shared Evidence Keys:

- 财星承载
- 官星承载
- 财官相生
- 身财关系
- 财官取用
- 地位资源
- 异路功名

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM-HIGH

去重策略：财官作为事业/财富共享 evidence；财富、事业、地位域引用同一承载判断，避免多域重复主票。

### Family-ID: FAM-010

Family-Name: 官杀 / 伤官 / 制化 / 杀印相生

Rule Count: 10

Rule IDs:

- ZP-PROD-20260605-011
- ZP-PROD-20260605-012
- ZP-PROD-20260606-004
- ZP-PROD-20260606-013
- DTS-PROD-20260606-064
- DTS-PROD-20260606-065
- DTS-PROD-20260606-087
- DTS-PROD-20260606-088
- DTS-PROD-20260606-222
- DTS-PROD-20260606-224

Shared Evidence Keys:

- 官杀状态
- 伤官见官
- 伤官伤尽
- 杀印相生
- 制杀化杀
- 刃杀成权
- 克泄引从

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM-HIGH

去重策略：制化链路只计一次主票；伤官、官杀、印绶、刃杀作为链路节点参与解释。

### Family-ID: FAM-011

Family-Name: 从格 / 从象 / 从势 / 从旺 / 从强 / 从财杀儿

Rule Count: 14

Rule IDs:

- ZP-PROD-20260605-014
- DTS-PROD-20260606-061
- DTS-PROD-20260606-171
- DTS-PROD-20260606-172
- DTS-PROD-20260606-173
- DTS-PROD-20260606-174
- DTS-PROD-20260606-175
- DTS-PROD-20260606-176
- DTS-PROD-20260606-177
- DTS-PROD-20260606-178
- DTS-PROD-20260606-179
- DTS-PROD-20260606-180
- DTS-PROD-20260606-195
- DTS-PROD-20260606-196

Shared Evidence Keys:

- 特殊格疑似
- 从格gate
- 从象
- 从旺
- 从强
- 从气
- 从势
- 从财
- 从杀
- 从儿
- 破格条件

Family Weight: 1.0

Potential Duplicate Vote Risk: CRITICAL

去重策略：从格必须先过 family-level gate。gate 未通过时，本 family 不得贡献主票；gate 通过后，从象、从旺、从强、从财、从杀、从儿只作为细分标签，不累加主票。

### Family-ID: FAM-012

Family-Name: 化格 / 合化 / 真化 / 假化 / 合而不化

Rule Count: 12

Rule IDs:

- ZP-PROD-20260605-014
- ZP-PROD-20260606-003
- DTS-PROD-20260606-168
- DTS-PROD-20260606-169
- DTS-PROD-20260606-170
- DTS-PROD-20260606-183
- DTS-PROD-20260606-184
- DTS-PROD-20260606-185
- DTS-PROD-20260606-186
- DTS-PROD-20260606-187
- DTS-PROD-20260606-188
- DTS-PROD-20260606-189

Shared Evidence Keys:

- 合化关系
- 化神得力
- 真化
- 假化
- 合而不化
- 贪合忘用
- 逢冲得用

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：合化先形成 family-level finding；真化、假化、合而不化为互斥标签，不得同时贡献多张主票。

### Family-ID: FAM-013

Family-Name: 月令 / 时令 / 旺相休囚 / 四时进退

Rule Count: 12

Rule IDs:

- ZP-PROD-20260605-003
- ZP-PROD-20260606-002
- ZP-PROD-20260606-017
- ZP-PROD-20260606-018
- ZP-PROD-20260606-019
- ZP-PROD-20260606-034
- ZP-PROD-20260606-038
- ZP-PROD-20260606-039
- DTS-PROD-20260605-006
- DTS-PROD-20260605-015
- DTS-PROD-20260606-057
- DTS-PROD-20260606-059

Shared Evidence Keys:

- 月令
- 提纲
- 四时
- 旺相休囚
- 进退
- 得令失令
- 季令取用

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：月令/时令设为公共 evidence feature，不作为多 family 的重复票源；用神、旺衰、调候只引用同一个月令证据。

### Family-ID: FAM-014

Family-Name: 六亲 / 婚姻 / 子息 / 家庭落点

Rule Count: 7

Rule IDs:

- ZP-PROD-20260606-010
- ZP-PROD-20260606-011
- ZP-PROD-20260606-012
- DTS-PROD-20260606-200
- DTS-PROD-20260606-201
- DTS-PROD-20260606-202
- DTS-PROD-20260606-203

Shared Evidence Keys:

- 六亲映射
- 婚姻宫
- 配偶星
- 子息星
- 刑冲破害落点
- 家庭关系反馈

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM

去重策略：六亲作为应用域 family；若其证据来自合冲、财官、用神，应引用上游 finding，不再重复主投票。

### Family-ID: FAM-015

Family-Name: 运岁 / 动态成败 / 触发转化

Rule Count: 7

Rule IDs:

- ZP-PROD-20260605-016
- ZP-PROD-20260606-016
- DTS-PROD-20260606-080
- DTS-PROD-20260606-091
- DTS-PROD-20260606-168
- DTS-PROD-20260606-216
- DTS-PROD-20260606-218

Shared Evidence Keys:

- 大运触发
- 流年触发
- 岁运合冲
- 原局成败转化
- 清浊随运
- 来去随运
- 科名运途

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM-HIGH

去重策略：运岁 family 作为 timing layer，不与原局结构同层投票；同一岁运触发只贡献一次 timing 主票。

### Family-ID: FAM-016

Family-Name: 性情 / 行为风格 / 中和偏枯外化

Rule Count: 5

Rule IDs:

- DTS-PROD-20260606-213
- DTS-PROD-20260606-214
- DTS-PROD-20260606-215
- ZP-PROD-20260606-013
- ZP-PROD-20260606-025

Shared Evidence Keys:

- 性情中和
- 性情偏枯
- 行为风格
- 诚信风险
- 五行偏颇外化

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM

去重策略：性情反馈只校准性情落点，不反向重复强化中和/调候 family 主票。

### Family-ID: FAM-017

Family-Name: 健康 / 寿元 / 元神 / 体用风险

Rule Count: 5

Rule IDs:

- DTS-PROD-20260606-204
- DTS-PROD-20260606-205
- DTS-PROD-20260606-206
- ZP-PROD-20260606-025
- ZP-PROD-20260606-037

Shared Evidence Keys:

- 元神状态
- 寿元风险
- 健康五行偏颇
- 燥湿健康
- 水源断续
- 土滞健康

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM

去重策略：健康 family 作为事件/体用落点；中和、调候、水土状态只作为共享证据，不重复投主票。

### Family-ID: FAM-018

Family-Name: 金木震兑 / 水火坎离 / 对待制化调济

Rule Count: 12

Rule IDs:

- ZP-PROD-20260606-017
- ZP-PROD-20260606-019
- ZP-PROD-20260606-028
- ZP-PROD-20260606-034
- ZP-PROD-20260606-038
- DTS-PROD-20260606-102
- DTS-PROD-20260606-103
- DTS-PROD-20260606-104
- DTS-PROD-20260606-105
- DTS-PROD-20260606-108
- DTS-PROD-20260606-109
- DTS-PROD-20260606-113

Shared Evidence Keys:

- 金木对待
- 水火既济
- 震兑制化
- 坎离升降
- 木火金水调济
- 季令制化

Family Weight: 1.0

Potential Duplicate Vote Risk: HIGH

去重策略：本 family 是调候 family 的细分子簇；默认并入 FAM-004 的 family cap，不单独额外贡献主票。

### Family-ID: FAM-019

Family-Name: 真假神 / 假神得局 / 真神失势

Rule Count: 7

Rule IDs:

- DTS-PROD-20260606-084
- DTS-PROD-20260606-085
- DTS-PROD-20260606-086
- DTS-PROD-20260606-183
- DTS-PROD-20260606-188
- ZP-PROD-20260605-005
- ZP-PROD-20260605-006

Shared Evidence Keys:

- 真神
- 假神
- 假神得局
- 真神失势
- 用神成败
- 救应
- 真化假化

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM-HIGH

去重策略：真假神作为用神/化格交叉子簇；若已在 FAM-001 或 FAM-012 投主票，本 family 只保留解释标签。

### Family-ID: FAM-020

Family-Name: 透藏 / 隐显 / 根气 / 得地

Rule Count: 8

Rule IDs:

- ZP-PROD-20260605-003
- ZP-PROD-20260606-002
- ZP-PROD-20260606-006
- ZP-PROD-20260606-008
- DTS-PROD-20260605-009
- DTS-PROD-20260606-057
- DTS-PROD-20260606-059
- DTS-PROD-20260606-094

Shared Evidence Keys:

- 透干
- 藏干
- 根气
- 得地
- 隐显
- 月令司令
- 有根无气

Family Weight: 1.0

Potential Duplicate Vote Risk: MEDIUM

去重策略：透藏根气应作为公共 evidence feature；默认不独立主投票，只为用神、旺衰、调候、格局提供证据。

---

## 2. 高风险 Family 去重优先级

| Priority | Family-ID | Family-Name | Risk | 去重动作 |
|---:|---|---|---|---|
| 1 | FAM-004 | 调候 / 寒暖 / 燥湿 / 季令气候 | CRITICAL | family-level cap；同一寒暖燥湿证据只出一票 |
| 2 | FAM-011 | 从格 / 从象 / 从势 / 从旺 / 从强 / 从财杀儿 | CRITICAL | family-level gate；gate 未过不投主票 |
| 3 | FAM-001 | 用神 / 取用 / 喜忌 / 成败救应 | HIGH | 定位、成败、救应、应用域分层，只允许定位主票 |
| 4 | FAM-005 | 顺逆 / 顺势 / 流通 / 通关 / 源流 | HIGH | 气机连续性合并为一个 family finding |
| 5 | FAM-013 | 月令 / 时令 / 旺相休囚 / 四时进退 | HIGH | 作为公共 evidence feature，不作为重复票源 |
| 6 | FAM-002 | 扶抑 / 旺衰 / 身强身弱 / 太过不及 | HIGH | 旺衰判断只出一票，强弱/月令/太过不及不叠加 |
| 7 | FAM-012 | 化格 / 合化 / 真化 / 假化 / 合而不化 | HIGH | 真化/假化/不化互斥，不并列投票 |
| 8 | FAM-008 | 清浊 / 清气 / 清枯 / 澄浊求清 | HIGH | 清浊作为格局质地证据，科名/官格引用同一 finding |

---

## 3. Family-Level 去重规则建议

### 3.1 主票规则

每个 family 在同一命局、同一分析域、同一 evidence key 命中时，只允许贡献一次主票。

建议伪字段：

```yaml
family_id: FAM-004
family_name: 调候 / 寒暖 / 燥湿 / 季令气候
family_weight: 1.0
main_vote_policy: one_main_vote_per_family
shared_evidence_keys:
  - 寒暖状态
  - 燥湿状态
  - 月令季节
duplicate_vote_control:
  enabled: true
  cap: 1_main_vote
```

### 3.2 互斥规则

以下 family 内存在互斥或半互斥标签，应避免同时计主票：

- FAM-011：从旺、从强、从气、从势、从财、从杀、从儿。
- FAM-012：真化、假化、合而不化。
- FAM-019：真神得势、假神得局、真神失势。

### 3.3 上游证据规则

以下 family 更适合作为公共 evidence feature，而不是独立主票源：

- FAM-013：月令 / 时令 / 旺相休囚 / 四时进退。
- FAM-020：透藏 / 隐显 / 根气 / 得地。
- FAM-002：扶抑 / 旺衰 / 身强身弱 / 太过不及。

### 3.4 子簇并入规则

以下 family 是高风险 family 的细分子簇，默认应受上级 family cap 约束：

- FAM-018 默认并入 FAM-004 调候 family 的 cap。
- FAM-019 默认受 FAM-001 用神 family 与 FAM-012 化格 family 共同约束。
- FAM-016、FAM-017 默认引用 FAM-003 中和偏枯、FAM-004 调候的共享证据，不反向加主票。

---

## 4. 校准投票影响说明

若不做 family-level 去重，未来校准会出现以下偏差：

1. 调候规则数量过多会让寒暖燥湿命局获得多张同源票，导致调候 family 权重虚高。
2. 从格规则在滴天髓中拆分过密，可能让特殊格判断以数量优势压制普通扶抑判断。
3. 用神类规则既是上游定位，又在格局、财富、事业、运岁中反复出现，错误会系统性扩散。
4. 月令、旺衰、透藏根气等公共证据若被多个 family 同时计票，会把同一证据误当作多个独立证据。
5. 顺逆、流通、通关、源流若不合并，会重复奖励“气机顺畅”或重复惩罚“气机阻隔”。

建议在未来 30 案例校准中记录两个计数：

- raw_rule_hits：原始规则命中数。
- deduped_family_votes：family 去重后的主票数。

校准时优先使用 deduped_family_votes 调整主权重，raw_rule_hits 仅用于解释丰富度与细分证据密度。

---

## 5. 结论

本报告完成了 P1-1 Rule Family 建设的只读版本：

- 已基于 META/rule-family-discovery.md 形成 20 个 family-level 聚类。
- 每个 family 均给出 family_id、family_name、rules、family_weight、shared_evidence_keys 与重复投票风险。
- 高风险 family 已明确去重优先级：调候、从格、用神、顺逆/流通、月令/旺衰。
- 本报告仅为治理审计输出，不修改 theory/ziping/index.yaml、theory/tiaohou_ditiansui/index.yaml、权重或 Schema。
