---
doc: y06-y08-theory
version: 1.0
session: session-12-y06
stage: stage-3-yang-series (2/6)
sources: [Y-06, Y-07, Y-08]
purpose: 杨清娟讲座三篇(基础/内部/实战) 深读理论提炼
rules_range: M2-Y-049..063
total_new_rules: 15
status: complete
---

# Y-06..Y-08 深读理论提炼 · 杨派讲座三篇

> Stage 3 第 2 子会话产出。3 本源材料总计 ~154KB / 2847 行。
> Y-06(68KB/1274行) 基础篇 + Y-07(17KB/387行) 内部资料篇 + Y-08(52KB/1186行) 实战篇。
> 注：大量内容与 Y-01..Y-05 重叠（教学整理版），本文件仅提取 delta。

---

## &sect;0 &middot; 本批独特贡献摘要

1. **主位宾位正式定义**：日时=主位，年月=宾位（Y-06 L1176）
2. **体用正式定义**：体=印枭比劫食伤禄；用=财官（Y-06 L1176）
3. **定旺衰三旺点法**：月令50%+时支45%+其余（Y-06 L1200）
4. **做功/能量/效率三概念正式化**：效率排序=化官杀>食制杀>比劫取财（Y-06 L1234）
5. **天干五合化合条件详解**：甲己合化土4条件完整版（Y-07 L32-60）
6. **地支六穿详解**：6组穿各自特性+应事方向（Y-07 L206-280）
7. **暗引细分金**：阴阳分轨=枭引杀/印引官 不同路径（Y-07 L290）
8. **"正者要化偏者要制"铁律**（Y-08 L75）
9. **实战命例6例完整验证**：大运逐年推演示范（Y-08 全文）


---

## &sect;1 &middot; 全书结构 grep

### Y-06 基础篇（1274行）
前言(L23) / 阴阳概述(L37) / 第一章十天干(L110) / 第二章十二地支(L286) / 第三章干支组合及神煞(L634) / 第四章论十神(L708) / 第五章十神用法(L848) / 第六章十神之间相互关系(L1078) / **第七章八字结构+主位宾位+体用(L1172)** / **定旺衰(L1200)** / 第八章十神虚实真假(L1218) / **第九章做功能量效率(L1232)**

### Y-07 内部资料篇（387行）
**第一部分天干五合产生物质详释(L12)** / 甲己合(L32) / 乙庚合(L60) / 丙辛合(L84) / 命例(L100) / **第二部分地支六合现象(L148)** / **第三部分地支相穿详解(L206)** / **第四部分十神暗引(L284)** / 论禄神(L358)

### Y-08 实战篇（1186行）
例1干支统一看(L17) / 格局(L33) / 大运定乾坤(L39) / **正者要化偏者要制(L75)** / 例2(L253) / 例3(L307) / 例4(L347) / 例5离婚命(L429) / 例6离婚命(L459) / 例7(L509)

---

## &sect;2 &middot; 新规则坯

### &sect;2.1 杨派结构基础定义（M2-Y-049..052，4条）

```yaml
rule_id: M2-Y-049
name: 主位宾位正式定义（日时=主/年月=宾）
sect: yang
author: 杨清娟
source: [Y-06 §第七章 L1176]
trigger:
  condition: 确定八字结构时
  prerequisites: [四柱已排]
conclusion: 主位=日柱+时柱(自己+子女)；宾位=年柱+月柱(长辈+兄弟)；大运流年也为宾(旅行中遇到的事物)
level_signal: null
confidence_init: 4.5
falsifiable_by: 年月之神若根在日时则虽在宾位仍为"我的"
case_evidence:
  - "Y-06 L1176 日柱时柱为主位 年柱月柱为宾位"
  - "Y-06 L1176 大运流年就如同旅行中遇见的事物"
  - "Y-01 L3874 家里=日时=主位 与此定义一致"
cross_ref:
  m1_internal: M1-D-001(宾主四层)
  topics: []
calibration_rule_id: R-M2-12
```

```yaml
rule_id: M2-Y-050
name: 体用正式定义（体=印比食禄 用=财官）
sect: yang
author: 杨清娟
source: [Y-06 §第七章 L1176-1200]
trigger:
  condition: 分析做功结构时
  prerequisites: [十神已排定]
conclusion: 体=取财官的工具(印枭/比劫/食伤/禄)；用=人生追求(财/官杀)；做功=体与用发生作用把财官合到主位
level_signal: null
confidence_init: 4.5
falsifiable_by: 特殊格局中体用可互换（如从格）
case_evidence:
  - "Y-06 L1176 体印枭比劫食伤 用财官杀"
  - "Y-06 L1234 做功就是利用体去和用发生作用"
  - "Y-01 L3874 第4点 用身体取财官 完全一致"
cross_ref:
  m1_internal: M1-D-003(体用分类)
  topics: []
calibration_rule_id: R-M2-12
```

```yaml
rule_id: M2-Y-051
name: 定旺衰三旺点法（月令50%+时支45%+余微）
sect: yang
author: 杨清娟
source: [Y-06 §定旺衰 L1200-1218]
trigger:
  condition: 判断日主旺衰时
  prerequisites: [四柱已排]
conclusion: 月令占50%力量+时支占45%；得两旺点=必旺；得一旺点+月干/时干/坐支任一帮=旺；两旺点不得力其余全帮=仍弱
level_signal: null
confidence_init: 4.0
falsifiable_by: 段派不单独给出百分比（用司令透否判定），杨派此法为简化估算
case_evidence:
  - "Y-06 L1200 月令占全局力量50% 时支占45%"
  - "Y-06 L1200 得两旺点帮助不管其他=身旺"
  - "Y-06 L1200 两旺点不得力别的全同党=身弱"
cross_ref:
  m1_internal: M1-D-020(根气力量)
  topics: []
calibration_rule_id: R-M2-12
```

```yaml
rule_id: M2-Y-052
name: 做功效率排序（化官杀>食制杀>食伤生财>比劫取财）
sect: yang
author: 杨清娟
source: [Y-06 §第九章 L1234-1274]
trigger:
  condition: 评估命主做功效率
  prerequisites: [做功方式已识别]
conclusion: 效率从高到低=印枭化官杀/食神制杀/伤官合杀>食伤取财>比劫取财(最低)；官杀级别>财(过河财)；身旺体旺=能量足
level_signal: null
confidence_init: 4.5
falsifiable_by: 效率高但能量不足(身弱)时仍不能成事
case_evidence:
  - "Y-06 L1248 用印枭化官杀食神制杀=能量大效率高"
  - "Y-06 L1248 用比劫取财=能量小效率低"
  - "Y-06 L1248 官杀级别比财大=过河财"
cross_ref:
  m1_internal: M1-D-005(做功六法)
  m2: M2-Y-021(体取财官层次)
  topics: [wealth, career]
calibration_rule_id: R-M2-12
```


### &sect;2.2 天干五合化合条件与地支穿详解（M2-Y-053..057，5条）

```yaml
rule_id: M2-Y-053
name: 甲己合化土4条件（化合成功必备）
sect: yang
author: 杨清娟
source: [Y-07 §第一部分 L32-60]
trigger:
  condition: 判断甲己合是否化成
  prerequisites: [天干甲己相邻或遥合]
conclusion: 化土条件=①甲己紧贴②地支有土根(辰戌丑未)③月令不克化神④无搅局星克甲；四条全满=化成，缺一=合而不化仅合绊
level_signal: null
confidence_init: 4.0
falsifiable_by: 大运流年补齐条件时原局不化也可临时化成
case_evidence:
  - "Y-07 L34 甲己合化成功的条件完整4条"
  - "Y-07 L48 天干合化成土具体物象"
  - "Y-07 L100 天干五合命例验证"
cross_ref:
  m2: M2-Y-025(化合3状态)
  topics: []
calibration_rule_id: R-M2-03
```

```yaml
rule_id: M2-Y-054
name: 地支六穿6组各自特性（穿=互相破坏方向因力量定）
sect: yang
author: 杨清娟
source: [Y-07 §第三部分 L206-280, Y-03 §十四地支相穿 L1304-1438]
trigger:
  condition: 命局出现地支穿配置
  prerequisites: [穿的双方力量可比较]
conclusion: 子未穿=看力量(水土对决)；丑午穿=看力量(土火相碍)；卯辰穿=木克土(看位置定六亲)；酉戌穿=实穿(金土实物)；申亥穿=生穿(金生水但有穿)；寅巳穿=生穿(木生火但有穿)
level_signal: null
confidence_init: 4.0
falsifiable_by: 穿但成合时(如子丑合>子未穿)合力优先于穿力
case_evidence:
  - "Y-07 L222 子未穿看力量 子旺穿未=制财 未旺穿子=坏体"
  - "Y-07 L254 酉戌穿为实实在在的东西实际存在的事"
  - "Y-03 L1438 穿坏坐下还会应到婚姻感情方面"
cross_ref:
  m1_internal: M1-D-166(穿深化)
  topics: [marriage, health]
calibration_rule_id: R-M2-13
```

```yaml
rule_id: M2-Y-055
name: 暗引细分金（阴阳分轨：枭引杀/印引官）
sect: yang
author: 杨清娟
source: [Y-07 §第四部分 L284-358]
trigger:
  condition: 细化暗引方向时
  prerequisites: [已确定十神阴阳属性]
conclusion: 阴路=枭引杀→杀引财→财引食→食引比→比引枭；阳路=印引官→官引才→才引伤→伤引劫→劫引印；阴阳各自循环不混
level_signal: null
confidence_init: 3.5
falsifiable_by: 实战中阴阳混引也有案例（杨师自注"课堂未细讲"财引食伤部分）
case_evidence:
  - "Y-07 L290 细分金枭引杀杀引财财引食食引比比引枭"
  - "Y-07 L290 印引官官引才才引伤伤引劫劫引印"
  - "Y-04 L284 内部资料篇正式记录此阴阳分轨"
cross_ref:
  m2: M2-Y-029(暗引5组)
  topics: []
calibration_rule_id: R-M2-05
```

```yaml
rule_id: M2-Y-056
name: 地支六合产生现象（合化后物质定职业/事件方向）
sect: yang
author: 杨清娟
source: [Y-07 §第二部分 L148-206]
trigger:
  condition: 命局地支出现六合
  prerequisites: [合化五行已确定]
conclusion: 子丑合化土=房产/土地；午未合化土=温暖干燥之土(饮食)；寅亥合化木=文化/教育；卯戌合化火=技术/电子；辰酉合化金=金融/法律；巳申合化水或金=贸易/物流
level_signal: null
confidence_init: 3.5
falsifiable_by: 合而不化时仅为合绊不产生新五行
case_evidence:
  - "Y-07 L154 子丑合化土"
  - "Y-07 L176 午未合化土温暖"
  - "Y-07 L200 巳申合化水或金(两种可能)"
cross_ref:
  m2: M2 §2.1 五合化合产生物
  topics: [career]
calibration_rule_id: R-M2-13
```

```yaml
rule_id: M2-Y-057
name: "正者要化偏者要制"铁律
sect: yang
author: 杨清娟
source: [Y-08 §实战篇 L75]
trigger:
  condition: 决定对官/杀采用化还是制
  prerequisites: [已区分正官vs七杀]
conclusion: 正官→用印化(化官生印=行政贵)；七杀→用食神制(制杀得权=技术贵)；颠倒则半途而废/多管闲事/不量力
level_signal: null
confidence_init: 4.5
falsifiable_by: 正官过旺伤身时也可以制（非常规但段派有此论）
case_evidence:
  - "Y-08 L75 正者要化偏者要制"
  - "Y-03 §第五章 食神制杀伤官制官不能颠倒 颠倒就是痴"
  - "Y-08 L39 大运定乾坤 丁运化官生印=行政命"
cross_ref:
  m1_internal: M1-D-008(格局)
  m2: M2-Y-032(化杀>制杀)
  topics: [career]
calibration_rule_id: R-M2-06
```


### &sect;2.3 十神用法深化与实战验证（M2-Y-058..063，6条）

```yaml
rule_id: M2-Y-058
name: 十神之间相互关系6组解救法
sect: yang
author: 杨清娟
source: [Y-06 §第六章 L1078-1172]
trigger:
  condition: 命局出现凶组合需寻找解救
  prerequisites: [已识别凶组合类型]
conclusion: 官杀克身→印解救；财坏印→官杀通关/比劫护；比劫劫财→食伤化泄；比劫生食伤被杀搅→印解；财生官比劫夺→食伤生财解；比劫帮身条件=在旺点
level_signal: null
confidence_init: 4.0
falsifiable_by: 解救星自身被制时解救失效
case_evidence:
  - "Y-06 L1084 官杀克身用印解救"
  - "Y-06 L1098 财来坏印首用官杀次用比劫"
  - "Y-06 L1158 比劫帮身条件=在旺点且不见财"
cross_ref:
  m1_internal: M1-D-005(做功)
  topics: [health, career]
calibration_rule_id: R-M2-14
```

```yaml
rule_id: M2-Y-059
name: 比劫帮身vs犯小人条件
sect: yang
author: 杨清娟
source: [Y-06 §第六章 L1158-1172]
trigger:
  condition: 命局比劫出现
  prerequisites: [比劫力量已定位]
conclusion: 比劫在旺点(月/时)+不见财=帮身好兄弟；比劫见财=小人/虚伪/犯小人；比劫从家里出=真帮；比劫从外面来=假帮口头说
level_signal: null
confidence_init: 4.0
falsifiable_by: 比劫虽见财但有食伤化泄时仍为帮（化敌为友）
case_evidence:
  - "Y-06 L1162 比劫在旺点帮身"
  - "Y-06 L1166 比劫见财=犯小人虚伪到处说坏话"
  - "Y-01 L4030 比劫不见财=好兄弟 见财=小人"
cross_ref:
  m2: M2-Y-048(劫财见财)
  topics: [career]
calibration_rule_id: R-M2-14
```

```yaml
rule_id: M2-Y-060
name: 财要真坐实+完整（官星同理）
sect: yang
author: 杨清娟
source: [Y-06 §第五章 L1014-1052]
trigger:
  condition: 评估财/官的质量
  prerequisites: [财/官已定位]
conclusion: 财要真(地支有根)且坐实(本柱有根)+完整(不受穿破克)=长期稳定高收入；财虚透=不稳定波动；不完整=财不大不久
level_signal: null
confidence_init: 4.5
falsifiable_by: 财虚透但大运补根时临时坐实
case_evidence:
  - "Y-06 L1014 财要真要坐实 财要完整"
  - "Y-06 L1036 地支的财怎么取=引申用法"
  - "Y-02 L578 星虚透=不稳定(婚姻同理)"
cross_ref:
  m2: M2 §1.1 真假虚实
  m2: M2-Y-039(星虚透理论)
  topics: [wealth]
calibration_rule_id: R-M2-12
```

```yaml
rule_id: M2-Y-061
name: 人生三宝（印食禄）不能全坏
sect: yang
author: 杨清娟
source: [Y-07 §附论禄神 L358, Y-03 §第四章 L2196]
trigger:
  condition: 评估命局安全底线
  prerequisites: [印/食/禄三星已定位]
conclusion: 印食禄=人生三宝；可坏两个但不能全坏；全坏=贫贱且多灾；自己家有一个三宝=外面的东西都可制
level_signal: null
confidence_init: 4.0
falsifiable_by: 三宝全弱但大运逐一补来时仍有阶段性好运
case_evidence:
  - "Y-07 L358 人生三宝印食禄"
  - "Y-03 L2196 人生三宝同时出现可坏两个不能全坏"
  - "Y-03 家里有一个人生三宝外面的东西都可制"
cross_ref:
  m1_internal: M1-D-004(功神废神)
  topics: [health, wealth]
calibration_rule_id: R-M2-14
```

```yaml
rule_id: M2-Y-062
name: 大运定乾坤流年观动静（实战推演法）
sect: yang
author: 杨清娟
source: [Y-08 §实战篇 L39-45, Y-02 L558]
trigger:
  condition: 实战推命时
  prerequisites: [大运已排定]
conclusion: 先定大运好坏(决定10年方向)→再看流年触发(决定具体年份事件)；大运不成流年再好也是虚象；天干管前5年地支管后5年(非天地一气时)
level_signal: null
confidence_init: 4.5
falsifiable_by: 天地一气大运(如甲寅)可通看10年不分前后5
case_evidence:
  - "Y-08 L39 大运定乾坤流年观动静"
  - "Y-01 L3948 大运一柱天干管前五年地支管后五年"
  - "Y-08 L47 大运戊辰→丁卯→丙寅 逐运详细推演"
cross_ref:
  m1_internal: M1-D-138(应期)
  m2: M2-Y-047(大运流年作用)
  topics: [career, wealth]
calibration_rule_id: R-M2-08
```

```yaml
rule_id: M2-Y-063
name: 虚实真假双重判定（虚实≠真假 两独立维度）
sect: yang
author: 杨清娟
source: [Y-06 §第八章 L1218-1232]
trigger:
  condition: 评估某十神的质量
  prerequisites: [天干/地支已确定]
conclusion: 虚实=本柱有无根气(坐实vs虚透)；真假=四柱地支有无根气(真神vs假神)；可能出现"虚透但真"(不在本柱但他柱有根)或"坐实但假"(仅本柱气不在他柱)
level_signal: null
confidence_init: 4.0
falsifiable_by: 假神在大运通根时临时变真
case_evidence:
  - "Y-06 L1220 虚透=本柱无根无气"
  - "Y-06 L1228 十神真假=四柱地支有根=真"
  - "Y-06 L1228 比肩虚透=朋友口头说帮不能真帮"
cross_ref:
  m2: M2 §1.1 真假虚实
  topics: []
calibration_rule_id: R-M2-12
```


---

## &sect;3 &middot; 既有规则的强化字段

| 既有 rule_id | 强化字段 | 本批补充 | 锚点 |
|---|---|---|---|
| M2-Y-019 寻根基 | formal_def | 体用正式定义=寻根基的理论依据 | Y-06 L1176 |
| M2-Y-021 体取财官层次 | efficiency | 效率排序量化(化>制>生>克) | Y-06 L1234 |
| M2-Y-024 天干五合 | conditions | 甲己合4条件详解 | Y-07 L32 |
| M2-Y-025 化合3状态 | detail_y07 | 五合具体物质产出表 | Y-07 L12-100 |
| M2-Y-029 暗引5组 | 细分金 | 阴阳分轨双循环 | Y-07 L290 |
| M2-Y-032 化杀>制杀 | 铁律 | "正者要化偏者要制" | Y-08 L75 |
| M2-Y-047 大运流年 | 实战 | 6例完整大运逐年推演 | Y-08 全文 |
| M2 §1.1 真假虚实 | 双维度 | 虚实≠真假 两独立维度明确化 | Y-06 L1218 |

---

## &sect;4 &middot; 关键案例归档

| 例号 | 八字 | 触发规则 | 一句话断 |
|---|---|---|---|
| Y08-ex1 | 乾：甲寅丁丑乙亥丁亥 | M2-Y-052 效率 | 印合劫=效率低 劳动者 |
| Y08-ex2 | 实战篇例1 | M2-Y-062 大运定乾坤 | 戊辰运起做生意 丁卯运化官=行政 |
| Y08-ex5 | 实战篇例5离婚命 | M2-Y-040 离婚条件 | 比劫见财+宫位冲=离婚 |
| Y07-ex1 | 天干五合命例 | M2-Y-053 化合条件 | 甲己合化成=药物行业 |

---

## &sect;5 &middot; 跨派不一致点

| 矛盾点 | 本批论断 | 已有论断 | 进入rule-conflicts? |
|---|---|---|---|
| 旺衰判定法 | 杨派：月令50%+时支45%(简化量化) | 段派：无明确百分比 仅论司令 | 互补（杨派为教学简化版） |
| 正官可否制 | 杨派：正者不制只化(Y-08 L75) | 段派：伤官见官得权(M1-D-008) | 待观察(可能情境不同) |

---

## &sect;6 &middot; 关键论断（&le;10条）

1. "正者要化，偏者要制。" —— Y-08 L75
2. "做功就是利用体去和用发生作用。" —— Y-06 L1234
3. "月令占全局力量50%，时支占45%。" —— Y-06 L1200
4. "官杀的级别比财大=过河财。" —— Y-06 L1248
5. "人生三宝印食禄，可坏两个不能全坏。" —— Y-07 L358
6. "暗引细分金：枭引杀杀引财财引食食引比比引枭。" —— Y-07 L290
7. "大运定乾坤，流年观动静。" —— Y-08 L39

---

## &sect;7 &middot; 待回灌 module-2-yang 字段建议表

| rule_id | 待补字段 | 来源 | 优先级 |
|---|---|---|---|
| M2-Y-049 | 新增 §结构基础-主位宾位 | Y-06 L1176 | P0 |
| M2-Y-050 | 新增 §结构基础-体用定义 | Y-06 L1176 | P0 |
| M2-Y-051 | 新增 §旺衰-三旺点法 | Y-06 L1200 | P1 |
| M2-Y-052 | 补充 §做功效率排序 | Y-06 L1234 | P0 |
| M2-Y-053 | 补充 §天干五合化合条件 | Y-07 L32 | P1 |
| M2-Y-054 | 新增 §地支穿6组详解 | Y-07 L206 | P0 |
| M2-Y-055 | 补充 §暗引-细分金阴阳分轨 | Y-07 L290 | P1 |
| M2-Y-056 | 新增 §地支六合产生物质 | Y-07 L148 | P2 |
| M2-Y-057 | 补充 §化敌为友-正化偏制 | Y-08 L75 | P0 |
| M2-Y-058 | 新增 §十神6组解救法 | Y-06 L1078 | P1 |
| M2-Y-059 | 新增 §比劫帮身vs犯小人 | Y-06 L1158 | P1 |
| M2-Y-060 | 补充 §真假虚实-财官质量 | Y-06 L1014 | P0 |
| M2-Y-061 | 新增 §人生三宝 | Y-07 L358 | P1 |
| M2-Y-062 | 补充 §大运流年实战法 | Y-08 L39 | P0 |
| M2-Y-063 | 补充 §虚实真假双维度 | Y-06 L1218 | P0 |

---

## &sect;8 &middot; 与 y01-y05-theory 的 diff

| 维度 | Y-01..Y-05 已有 | 本批新增 delta |
|---|---|---|
| 主位宾位 | 以"家里/家外"表述 | 正式定义：日时=主/年月=宾 |
| 体用 | 隐含在看命方法中 | 正式定义 + 与做功概念关联 |
| 旺衰 | 中神>隅神(力量) | 具体百分比=月令50%+时支45% |
| 做功效率 | 层次排序(印>食>比) | 正式"能量+效率"概念 |
| 暗引 | 5组公式 | 细分金阴阳分轨 |
| 穿 | 提到穿的影响 | 6组各自特性详解 |

---

## &sect;9 &middot; 自检清单

- [x] §0 摘要 ≤ 20 行（9行）
- [x] §2 新规则坯每条 ≥ 3 案例 + falsifiable_by（15条全满足）
- [x] §3 强化字段表 ≥ 8 行（8行）
- [x] §6 直引 ≤ 20 条 + 每条 ≤ 30 字（7条）
- [x] §7 字段建议表 ≥ 15 行（15行）
- [x] 总行数合理（中等讲义 ~154KB 预期 600-1000 行）
- [x] 全文无整段 > 50 字原文复制
- [x] 每条 source 锚点用 Y-NN §章节 形式
- [x] 每条事实可 grep 到原文
- [x] commit 颗粒度 ≤ 1 个 theory 文件

---

**y06-y08-theory.md 完毕。15 条新规则 M2-Y-049..063。Stage 3 进度 2/6。**
