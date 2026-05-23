---
doc: y01-y05-theory
version: 1.0
session: session-11-y01
stage: stage-3-yang-series (1/6)
sources: [Y-01, Y-02, Y-03, Y-04, Y-05]
purpose: 杨清娟派基础教材+教学体系命例集+学员笔记 深读理论提炼
rules_range: M2-Y-019..048
total_new_rules: 30
status: complete
---

# Y-01..Y-05 深读理论提炼 · 杨派基础体系

> Stage 3 第 1 子会话产出。5 本源材料总计 ~1042KB / 18002 行。
> Y-01(294KB) 主著 + Y-02(117KB) 高级续篇 + Y-03(478KB) 教学体系命例集 + Y-04(122KB) Y-03 互校本 + Y-05(31KB) 学员笔记配套。

---

## &sect;0 &middot; 本批独特贡献摘要（&le;20行）

1. **寻根基**完整方法论：家里/家外判定 + 根vs气vs库 区分（Y-01 L3874, Y-03 L1938）
2. **天干五合做功**全体系：合化3状态 + 搅局星 + 合应事 + 暗象（Y-01 L532-786）
3. **十神暗引**5组公式：食伤→比劫/印枭→官杀/比劫→印枭/官杀→财/财→食伤（Y-01 L4073-4127）
4. **财富级别7等**排序：官杀库>食伤库>旺杀>财库>旺官>食伤当财>财（Y-01 L3801）
5. **开库原则**完整版：用自己根基开 + 中神在旺点 + 墓中物喜透出（Y-01 L3501, Y-03 L2196）
6. **气数**概念：数在前(大运) 气在后(流年) + 气数犹在/气数已尽判定（Y-01 L3481）
7. **看命方法**两套流程：家里→找十神生克→体取财官 / 打开八字定运（Y-01 L3874-3930）
8. **婚姻系统**：宫位先于星 + 印运成婚 + 星虚透理论 + 离婚条件（Y-02 L538-692）
9. **食神制杀/食伤合制**：力量对比定官vs财 + 弱制原则（Y-02 L1-67）
10. **正偏印混局/枭神夺食/食伤混局**三大混局系统（Y-01 L3691-3746）


---

## &sect;1 &middot; 全书结构 grep

### Y-01 杨清娟命理基础电子书261页（4161行）
关键章节：卷一十天干(L91) / 卷二十二地支(L123) / 卷三(L163) / 卷四(L177) / 卷五(L237,L3566) / 前言(L335) / 杨师语录(L345) / 阴阳概论(L359) / 十天干五合(L532) / 搅局星(L678) / 十神暗引(L4073) / 气数(L3481) / 官统财财统官(L3491) / 开财库(L3501) / 火土一家(L3515) / 财富级别(L3801) / 看命方法一(L3874) / 看命方法二(L3930) / 大运看法(L3948) / 劫财见财(L4030) / 食神生财(L4129)

### Y-02 杨清娟命理基础电子书261页续（1358行）
关键章节：食神制杀(L1) / 食伤合制官杀(L33) / 六亲看法(L245) / 学历看法(L299) / 官命看法(L365) / 职业看法(L468) / 情感看法(L538) / 婚姻好坏(L568) / 离婚条件(L645) / 桃花(L698) / 反局悖格悖禄(L819)

### Y-03 教学体系命例集细解245页（9419行）
关键章节：第一章十天干(L176) / 第二章十二地支(L818) / 第三章十神(L1832起) / 第四章寻根基找真假(L1938) / 第五章十神相生相克(L2256) / 命例集(L6000+约120例)

### Y-04 教学体系命例集互校本（1750行）—— Y-03 部分重复，取差异补充
### Y-05 学员笔记配套（1314行）—— 盲钳子/流星赶月口诀/民间术法


---

## &sect;2 &middot; 新规则坯

### &sect;2.1 寻根基与家里/家外判定（M2-Y-019..023，5条）

```yaml
rule_id: M2-Y-019
name: 寻根基三步法（家里有→弱制得；家外→体旺强制得）
sect: yang
author: 杨清娟
source: [Y-01 §看命方法一 L3874, Y-03 §第四章寻根基 L1938]
trigger:
  condition: 打开八字定位财官所在宫位（年月=家外/日时=家里）
  prerequisites: [已确定十神分布]
conclusion: 家里的财官弱制即得；家外的须体力>财官力方得；禄合外财可得但比劫合外财则破
level_signal: null
confidence_init: 4.5
falsifiable_by: 家外财官虽弱但日主无根无气亦不能得
case_evidence:
  - "Y-01 L3938 乾：丁乙丁※/巳卯未午 午根>年比劫=争财胜"
  - "Y-03 L2196 甲辰日主时上有禄用戌冲开辰印库发财"
  - "Y-02 L33 食伤合制 戊子合=弱制得官 命主县长"
cross_ref:
  m1_internal: M1-D-001(宾主四层)
  topics: [wealth, career]
calibration_rule_id: R-M2-01
```

```yaml
rule_id: M2-Y-020
name: 根vs气vs库的力量层级
sect: yang
author: 杨清娟
source: [Y-01 §看命方法一 L3930-3938, Y-03 §第四章 L1938]
trigger:
  condition: 判定某十神的根基强弱时
  prerequisites: [已定位地支藏干]
conclusion: 禄(本气)>根(中气/余气)>库(入墓)>气(天干虚透无根)；中神力>隅神力>墓库力
level_signal: null
confidence_init: 4.0
falsifiable_by: 月令中气在旺月时力量可能超越他柱本气
case_evidence:
  - "Y-01 L3930 根是地支比劫如亥子丑，库辰是气"
  - "Y-01 L3948 中神的力量大于隅神 食伤受制看力量"
  - "Y-03 L2196 甲辰日禄在时上=根在旺点 力量足"
cross_ref:
  m1_internal: M1-D-003(体用分类)
  topics: [wealth]
calibration_rule_id: R-M2-01
```

```yaml
rule_id: M2-Y-021
name: 体取财官的层次排序（印>食伤>比劫>禄）
sect: yang
author: 杨清娟
source: [Y-01 §看命方法一 L3874 第4点, Y-01 §劫财制财 L3552]
trigger:
  condition: 判定命主取财官的方式
  prerequisites: [已确定做功结构]
conclusion: 用印取=脑力工作者；用食伤取=技术/销售；用比劫取=劳动者；用禄克财=最底层
level_signal: null
confidence_init: 4.5
falsifiable_by: 比劫有印生时层次可升（有印另当别论）
case_evidence:
  - "Y-01 L3552 用印取财官脑力；食伤技术；比劫劳动者"
  - "Y-03 L2256 食伤不生财=管理者 食伤生财=劳动者"
  - "Y-02 L405 比劫生食伤制官杀=吃皇粮"
cross_ref:
  m1_internal: M1-D-005(做功六法)
  topics: [career, wealth]
calibration_rule_id: R-M2-02
```

```yaml
rule_id: M2-Y-022
name: 天地一气五行平衡观（体旺财官旺=富贵；体旺财官弱=穷命）
sect: yang
author: 杨清娟
source: [Y-01 §看命方法一 L3874 第5点]
trigger:
  condition: 整体评估命局层次
  prerequisites: [体力量已评估, 财官力量已评估]
conclusion: 体旺+财官旺=富贵命；体旺+财官弱=穷命喜走财官运；身弱+财官旺=喜帮扶运
level_signal: L0-L4
confidence_init: 4.0
falsifiable_by: 大运补弱方后层次可升1-2级（参照L-2026-A）
case_evidence:
  - "Y-01 L3874 体旺财官旺富贵命 体旺财官弱普通命或穷命"
  - "Y-01 L3552 身旺财旺富命 身旺财弱穷命 身弱财旺穷命"
  - "Y-02 L1 食神制杀力量相当=官命 食伤力<杀力=求财"
cross_ref:
  m1_internal: M1-D-122(富贵贫贱三分)
  topics: [wealth]
calibration_rule_id: R-M2-02
```

```yaml
rule_id: M2-Y-023
name: 家里有先拿家里的（人生秩序铁律）
sect: yang
author: 杨清娟
source: [Y-01 §看命方法一 L3874 第3点, Y-03 §第四章 L1938]
trigger:
  condition: 判定命主自信/自卑/争财方向
  prerequisites: [已确定财官在家里还是家外]
conclusion: 家里有财官=自信稳定先用；家外=不确定+需竞争；别人供养无联系=亏欠心自卑
level_signal: null
confidence_init: 4.0
falsifiable_by: 家里财官受穿破时虽在家仍不安
case_evidence:
  - "Y-01 L3874 人生秩序是家里有肯定先拿家里的"
  - "Y-01 L4018 自信=拿自己家里财官 自卑=拿别人的"
  - "Y-03 L1938 寻根基 家里出来的弱制就得到"
cross_ref:
  m1_internal: M1-D-001(宾主)
  topics: [career, wealth]
calibration_rule_id: R-M2-01
```


### &sect;2.2 天干五合做功体系（M2-Y-024..028，5条）

```yaml
rule_id: M2-Y-024
name: 天干五合效率最高（合=得到，克=辛苦取）
sect: yang
author: 杨清娟
source: [Y-01 §十天干五合 L532, Y-01 §看命方法一 L3874]
trigger:
  condition: 日干与财/官存在天干五合关系
  prerequisites: [合的双方力量足够，无搅局星干扰]
conclusion: 合财=得财(阳干合财)；合官=得官(阴干合官)；合到主位=自己得；合在宾位=环境象
level_signal: null
confidence_init: 4.5
falsifiable_by: 搅局星出现时合被拆=得不到
case_evidence:
  - "Y-01 L532 甲己合化土/乙庚合化金/丙辛合化水/丁壬合化木/戊癸合化火"
  - "Y-01 L3874 禄可以合财合官就是富贵命 禄冲财冲官就是贫贱卑微命"
  - "Y-02 L33 戊子合=食神合官 弱制得到 命主县长"
cross_ref:
  m1_internal: M1-D-005(做功六法-合用)
  m2: M2 §2.1 五合化合产生物
  topics: [wealth, career]
calibration_rule_id: R-M2-03
```

```yaml
rule_id: M2-Y-025
name: 天干五合化合3状态（化成/合绊/搅局）
sect: yang
author: 杨清娟
source: [Y-01 §十天干五合 L532-594, Y-01 §搅局星 L678]
trigger:
  condition: 两天干成合时判定化合结果
  prerequisites: [合双方存在]
conclusion: 化成=地支有化神+一方有力→真合得实物；合绊=力量相当互牵→都做不了事；搅局=第三干介入→合被拆或转向
level_signal: null
confidence_init: 4.0
falsifiable_by: 化神在大运流年到来时原局不化也可化成
case_evidence:
  - "Y-01 L572 甲己合三种状态：正常合化/无常(力量不够)/反常"
  - "Y-01 L678 搅局星庚甲己=庚克甲拆合"
  - "Y-03 L662 合成后的现象：化成一种五行考试超常发挥"
cross_ref:
  m1_internal: M1-D-116(合用做功)
  topics: [career]
calibration_rule_id: R-M2-03
```

```yaml
rule_id: M2-Y-026
name: 搅局星判定（合中第三干克合首破局）
sect: yang
author: 杨清娟
source: [Y-01 §搅局星 L678-786, Y-03 §天干五合合拌和搅局者 L678]
trigger:
  condition: 天干三字共见时存在搅局可能
  prerequisites: [两干有合关系 + 第三干能克其一]
conclusion: 克合首者为搅局星→合被拆→失去做功；搅局星力量>被搅者时100%拆；力量<时仅减效
level_signal: null
confidence_init: 4.0
falsifiable_by: 搅局星无根无气时虽在天干仍搅不动
case_evidence:
  - "Y-01 L724 庚甲己=庚克甲拆甲己合"
  - "Y-01 L732 辛乙庚=辛克乙拆乙庚合"
  - "Y-03 L712 例3-8 多个搅局星实例"
cross_ref:
  m1_internal: M1-D-116(合用做功)
  topics: [wealth]
calibration_rule_id: R-M2-03
```

```yaml
rule_id: M2-Y-027
name: 天干五合应事表（合财=得妻/得财；合官=得职/得权）
sect: yang
author: 杨清娟
source: [Y-03 §十二天干五合应事 L784, Y-01 §十天干五合 L532]
trigger:
  condition: 大运/流年触发天干五合
  prerequisites: [原局有合的配置或运来补合]
conclusion: 合财应事=得财/得妻/合作；合官应事=升职/得权/考试；合印=得学历/得房/得母助
level_signal: null
confidence_init: 4.0
falsifiable_by: 合的财官为忌神时合到反为灾
case_evidence:
  - "Y-03 L784 天干五合应事专节"
  - "Y-02 L554 印运+财流年=结婚应期（合到家里）"
  - "Y-01 L3874 日主合官有根有气就能得到这个官"
cross_ref:
  m2: M2 §2.2 化合3状态
  topics: [marriage, career, wealth]
calibration_rule_id: R-M2-03
```

```yaml
rule_id: M2-Y-028
name: 同柱干支互动规则（同柱作用/异柱干支不作用）
sect: yang
author: 杨清娟
source: [Y-01 §干支作用关系 L3994]
trigger:
  condition: 判定某干支受生受克的来源
  prerequisites: [八字四柱已排]
conclusion: 天干与天干作用/地支与地支作用/同柱干支互作用/异柱天干不直接作用地支；同柱同五行地支逢生天干旺
level_signal: null
confidence_init: 4.0
falsifiable_by: 紧邻柱在实战中有部分影响力（段派邻位论）
case_evidence:
  - "Y-01 L3994 两个柱子天干和地支不作用"
  - "Y-01 L3994 同柱同五行地支逢生天干旺 如丙寅寅逢生丙旺"
  - "Y-01 L3994 戊寅 寅逢生则戊受制"
cross_ref:
  m1_internal: M1-D-001(宾主四层)
  topics: []
calibration_rule_id: R-M2-04
```


### &sect;2.3 十神暗引与格局判定（M2-Y-029..033，5条）

```yaml
rule_id: M2-Y-029
name: 十神暗引5组公式（旺而不受伤则暗引对应十神）
sect: yang
author: 杨清娟
source: [Y-01 §十神暗引 L4073-4127]
trigger:
  condition: 某十神在旺点(月支/时支)且不受刑穿
  prerequisites: [该十神有根有气且在旺点]
conclusion: 食伤旺暗引比劫(贵人)；印枭旺暗引官杀(权)；比劫旺暗引印枭(学历)；官杀旺暗引财(过河财)；财旺暗引食伤(口才)
level_signal: null
confidence_init: 4.5
falsifiable_by: 十神虽旺但受刑穿则暗引失效
case_evidence:
  - "Y-01 L4073 食伤暗引比劫=有贵人有良好人际关系"
  - "Y-01 L4095 印枭暗引官杀=制印得权"
  - "Y-01 L4107 比劫暗引印枭 劫财旺=学历 比肩旺=技能"
cross_ref:
  m1_internal: M1-D-004(功神废神)
  m2: M2 §0 暗逻辑
  topics: [career, education]
calibration_rule_id: R-M2-05
```

```yaml
rule_id: M2-Y-030
name: 比劫暗引印枭定学历方向（劫财→正印学历/比肩→枭技能）
sect: yang
author: 杨清娟
source: [Y-01 §比劫暗引印枭 L4107-4121]
trigger:
  condition: 命局比劫重重一片旺象
  prerequisites: [比劫在旺点且不受刑穿]
conclusion: 劫财重暗引正印=有学历；比肩重暗引枭=报考技能类学校；五行金水=理科(金融/法律/医)；五行木火=文科(教育/文化)
level_signal: null
confidence_init: 4.0
falsifiable_by: 比劫旺但受穿破则暗引印弱化为函授或自考
case_evidence:
  - "Y-01 L4107 劫财重重暗引正印=有学历"
  - "Y-01 L4107 比肩重重暗引枭=报考技能方面学校"
  - "Y-01 L4107 金水=理科 木火=文科 木火库=与佛有缘"
cross_ref:
  topics: [education]
calibration_rule_id: R-M2-05
```

```yaml
rule_id: M2-Y-031
name: 格局=十神有对应配置（有格无局=闲神/懒汉/无能力）
sect: yang
author: 杨清娟
source: [Y-03 §十神相生相克 第四节 L2350+]
trigger:
  condition: 命局中某十神独存无对应制化合配
  prerequisites: [识别出体/用结构]
conclusion: 体有对应制化神=有格局=勤奋；体闲无对应=懒汉；用闲无制化=没能力；杀无制化=没格局说了不算
level_signal: null
confidence_init: 4.0
falsifiable_by: 大运补来对应神时临时形成格局（但运过则散）
case_evidence:
  - "Y-03 格局就是十神当中都有对应的神"
  - "Y-03 命中有格无局这颗神就是闲神"
  - "Y-03 杀无制化=没有格局的人 到哪都受欺负"
cross_ref:
  m1_internal: M1-D-008(十六格局)
  topics: [career]
calibration_rule_id: R-M2-05
```

```yaml
rule_id: M2-Y-032
name: 化杀生枭>化官生印>合官（杨派官命层次排序）
sect: yang
author: 杨清娟
source: [Y-03 §十神相生相克 第四节, Y-02 §官命看法 L365]
trigger:
  condition: 评估官命层次时
  prerequisites: [命局中有官/杀且有化/合配置]
conclusion: 化杀生枭+枭生身不见食神=官最大；化官生印=官大有名气；财生官+合官=官大但低于化杀；食神制杀=技术官企业官
level_signal: L2-L4
confidence_init: 4.0
falsifiable_by: 枭化官为异性(如丁化甲)则化不尽官不长久
case_evidence:
  - "Y-03 化杀生枭枭生身不见食神此命的官肯定大"
  - "Y-02 L371 化官生印=行政官或党务官"
  - "Y-03 枭化官=丁化甲异性不能完全化 官干不长远"
cross_ref:
  m1_internal: M1-D-008(格局通辨)
  m2: M2 §1.3 化敌为友
  topics: [career]
calibration_rule_id: R-M2-06
```

```yaml
rule_id: M2-Y-033
name: 食伤制杀力量对比定官vs财
sect: yang
author: 杨清娟
source: [Y-02 §食神制杀 L1-32, Y-02 §食伤合制官杀 L33]
trigger:
  condition: 命局有食伤与官杀对峙
  prerequisites: [食伤/杀双方力量可比较]
conclusion: 食伤力=杀力→求官(有大不做小)；食伤力>杀力→当官(级别看杀旺衰)；食伤力<杀力→100%求财；弱制(家里官杀)也得到
level_signal: null
confidence_init: 4.5
falsifiable_by: 大运来印制食伤则官命转灾
case_evidence:
  - "Y-02 L1 食神杀力量相当一定求官"
  - "Y-02 L1 食伤力<杀=100%求财 流年制食神必破财"
  - "Y-02 L33 官出自家里弱制可得到 命主县长"
cross_ref:
  m1_internal: M1-D-008(格局-食神制杀格)
  topics: [career, wealth]
calibration_rule_id: R-M2-06
```


### &sect;2.4 开库与财富级别（M2-Y-034..037，4条）

```yaml
rule_id: M2-Y-034
name: 开库原则（用自己根基开+中神在旺点+墓中物喜透）
sect: yang
author: 杨清娟
source: [Y-01 §开财库 L3501, Y-03 §开库原则 L2196, Y-01 §三合局特殊性 L3750]
trigger:
  condition: 命局存在墓库且有冲/合开库配置
  prerequisites: [库的五行已确定, 开库的字与日主有联系]
conclusion: 我的根参与开库=发财；根不参与看别人发财；财库喜在坐下；开官杀库=德才兼备有能力；有库不能开=有才无德不可培养
level_signal: null
confidence_init: 4.5
falsifiable_by: 开库的字被穿破则库开不彻底
case_evidence:
  - "Y-01 L3501 开财库我的根没参与看别人发财"
  - "Y-01 L3501 原命有印生身喜开官杀库既发财又当官"
  - "Y-01 L3858 能开官杀库=德才兼备 有库无开=有才无德"
cross_ref:
  m1_internal: M1-D-005(做功-墓用)
  topics: [wealth, career]
calibration_rule_id: R-M2-07
```

```yaml
rule_id: M2-Y-035
name: 财富级别7等排序
sect: yang
author: 杨清娟
source: [Y-01 §财富级别 L3801-3819]
trigger:
  condition: 评估命主财富层次
  prerequisites: [已识别命局做功方式]
conclusion: 官杀库>食伤库>旺杀>财库>旺官>食伤当财>财（最小）；同八字不同地区财富数字不同按当地经济能力定
level_signal: L1-L4
confidence_init: 4.5
falsifiable_by: 开库但库小则级别有限；旺杀无制则不当财看
case_evidence:
  - "Y-01 L3801 官杀库→食伤库→旺杀→财库→旺官→食伤当财→财最小"
  - "Y-01 L3801 成都开官杀库顶多5000万 深圳至少3亿"
  - "Y-01 L3534 官杀为财所代表财富级别>以财为财"
cross_ref:
  m1_internal: M1-D-122(富贵贫贱)
  topics: [wealth]
calibration_rule_id: R-M2-07
```

```yaml
rule_id: M2-Y-036
name: 三合局/三会局中神必须在旺点（月令/时支）
sect: yang
author: 杨清娟
source: [Y-01 §三合局三会局的特殊性 L3750-3763]
trigger:
  condition: 命局出现三合/三会局配置
  prerequisites: [三个字齐全]
conclusion: 中神在月令或时支=合成/会成；中神不在旺点=到齐也合不成；合成后不分阴阳统一生克
level_signal: null
confidence_init: 4.0
falsifiable_by: 中神虽不在旺点但得大运帮扶时可临时合成
case_evidence:
  - "Y-01 L3750 中神必须在旺点月令或时支才能合成"
  - "Y-01 L3750 合成局的卯木不破午火但现象还是要出来有惊无险"
  - "Y-01 L3750 会局能解灾但现象还是要有"
cross_ref:
  m1_internal: M1-D-116(合用做功)
  topics: []
calibration_rule_id: R-M2-04
```

```yaml
rule_id: M2-Y-037
name: 气数判定（数=大运，气=流年残余）
sect: yang
author: 杨清娟
source: [Y-01 §气数 L3481-3491]
trigger:
  condition: 好大运走完紧接第一年流年同神
  prerequisites: [大运交替期]
conclusion: 前好运走完+流年同神=气数犹在(还好一年)；前好运完+流年克神=气数已尽；指导客户在气尽前收场止损
level_signal: null
confidence_init: 4.0
falsifiable_by: 流年虽同神但该神被当年太岁冲克则气数提前尽
case_evidence:
  - "Y-01 L3481 大运走完又来同一个神叫气数犹在"
  - "Y-01 L3481 前好运走完紧接来午年午制酉=气数已尽"
  - "Y-01 L3481 好大运10年第8年坏流年来了=叫人家八年赶紧退"
cross_ref:
  m1_internal: M1-D-138(应期-大运流年)
  topics: [wealth]
calibration_rule_id: R-M2-08
```


### &sect;2.5 婚姻与六亲系统（M2-Y-038..042，5条）

```yaml
rule_id: M2-Y-038
name: 婚姻看法三步（宫位先→星→应期=印运+人到）
sect: yang
author: 杨清娟
source: [Y-02 §情感看法 L538-568, Y-02 §结婚应期 L552]
trigger:
  condition: 断婚姻状态时
  prerequisites: [夫妻宫已确定(日支), 配偶星已确定]
conclusion: 第一看宫位静否(喜静忌刑冲穿)；第二看星强弱(虚透=不稳)；应期=大运走印运(家到)+流年配偶星到(人到)
level_signal: null
confidence_init: 4.5
falsifiable_by: 宫位虽静但星太弱时仍难成婚
case_evidence:
  - "Y-02 L542 首看宫位而不是星"
  - "Y-02 L558 大运是印运流年为夫妻星到=应期"
  - "Y-02 L568 婚姻宫安静一般都是好婚姻"
cross_ref:
  m1_internal: M1-D-170(婚姻系统)
  topics: [marriage]
calibration_rule_id: R-M2-09
```

```yaml
rule_id: M2-Y-039
name: 星虚透理论（虚透见根=人来；根走=离婚）
sect: yang
author: 杨清娟
source: [Y-02 §婚姻好坏 L578-590]
trigger:
  condition: 配偶星在天干虚透无根
  prerequisites: [配偶星已确定]
conclusion: 星虚透=感情不稳/不易找到如意/易变心；见根年=人来结婚；根走年=离婚；若还犯比劫则需同时解决比劫问题
level_signal: null
confidence_init: 4.0
falsifiable_by: 星虚透但坐实在库中运开库时也能稳定
case_evidence:
  - "Y-02 L578 星虚透代表情感不稳弱代表缺"
  - "Y-02 L578 虚透的星见根时容易借力动情"
  - "Y-02 L578 丁火虚立不住 帮扶运能成 运走人走"
cross_ref:
  topics: [marriage]
calibration_rule_id: R-M2-09
```

```yaml
rule_id: M2-Y-040
name: 离婚条件（比劫见财型/食伤生财型）
sect: yang
author: 杨清娟
source: [Y-02 §离婚条件 L645-675]
trigger:
  condition: 命局存在比劫见财或食伤生财组合
  prerequisites: [已确定婚姻宫状态]
conclusion: 比劫见财离婚条件=比劫力>财力+宫位受冲；食伤生财离婚条件=食伤泄身太过+财星外露；官杀混杂女命基本都离(比劫争夺日主)
level_signal: null
confidence_init: 4.0
falsifiable_by: 比劫见财但有印通关则可化解不离
case_evidence:
  - "Y-02 L647 比劫见财离婚条件"
  - "Y-02 L653 食伤生财离婚条件"
  - "Y-02 L675 官杀混杂女命基本都犯桃花都会离婚"
cross_ref:
  m1_internal: M1-D-170(婚姻)
  topics: [marriage]
calibration_rule_id: R-M2-09
```

```yaml
rule_id: M2-Y-041
name: 六亲看法定位公式（印=母/财=父/比劫=兄弟/食伤=子女/官杀=配偶或上司）
sect: yang
author: 杨清娟
source: [Y-02 §六亲看法 L245-295, Y-01 §六亲情况 L3538]
trigger:
  condition: 断六亲吉凶时
  prerequisites: [六亲星已在四柱定位]
conclusion: 看六亲以宫位+星双重定位；枭神夺食按宫位断=时支女命100%子女灾/月干兄弟灾/日支自身灾；印合财=母管全家
level_signal: null
confidence_init: 4.0
falsifiable_by: 同一星在不同宫位应事方向完全不同（须结合L-2026-D全扫）
case_evidence:
  - "Y-01 L3699 枭神夺食食神落时支女命百分百子女有灾"
  - "Y-01 L3538 辰酉合铲乙木=母亲流产或兄弟腿脚伤"
  - "Y-02 L245 六亲情况 看兄弟姐妹 看克父克母"
cross_ref:
  m1_internal: M1-D-186(六亲判定)
  topics: [family, health]
calibration_rule_id: R-M2-10
```

```yaml
rule_id: M2-Y-042
name: 官命9种取法（化杀/化官/合官/财生官/食制杀/比劫暗制/制印得权/劫财制财/伤官伤尽）
sect: yang
author: 杨清娟
source: [Y-02 §官命看法 L365-468]
trigger:
  condition: 判定命主是否为官命及级别
  prerequisites: [已确定官杀配置]
conclusion: 9种取官法按层次排=化杀生枭>化官生印>合完整官>财生官合官>食制杀>比劫生食伤制杀>劫财制财>伤官伤尽>制印得权；与官方有缘=官根在我家
level_signal: L1-L4
confidence_init: 4.5
falsifiable_by: 取法存在但官不完整时级别大打折扣
case_evidence:
  - "Y-02 L371 化官生印=行政官"
  - "Y-02 L389 财生官合官级别大"
  - "Y-02 L445 伤官伤尽始为奇=当官命 条件伤官暗制官"
cross_ref:
  m1_internal: M1-D-008(格局通辨)
  topics: [career]
calibration_rule_id: R-M2-06
```


### &sect;2.6 混局系统与枭神夺食（M2-Y-043..046，4条）

```yaml
rule_id: M2-Y-043
name: 正偏印混局（做事不专一/考试失利/合作变卦）
sect: yang
author: 杨清娟
source: [Y-01 §细解正偏印混局 L3691-3699]
trigger:
  condition: 命局正印偏印同时透出或流年正偏印同出
  prerequisites: [正偏印双见且都有力]
conclusion: 性格双重做事不专一好变；考试年正偏印混=失利走神发挥不好；合作年混印=上午答应下午反悔；去掉一个印=清=可合作/超常发挥
level_signal: null
confidence_init: 4.0
falsifiable_by: 混局但合成一种五行时反为清=超常发挥
case_evidence:
  - "Y-01 L3691 正偏印混局做事不专一好变丢三落四"
  - "Y-01 L3691 考试时正偏印同出一定失利走神"
  - "Y-01 L3691 合成一种五行考试超常发挥"
cross_ref:
  topics: [education, career]
calibration_rule_id: R-M2-11
```

```yaml
rule_id: M2-Y-044
name: 枭神夺食完整判法（宫位定灾方向+富贵不减条件）
sect: yang
author: 杨清娟
source: [Y-01 §细解枭神夺食 L3699-3721]
trigger:
  condition: 命局偏印旺+食神被制
  prerequisites: [枭与食同见且枭力>食力]
conclusion: 枭生身有利=富贵不减(条件:身弱枭为用)；食神在时支女命=子女灾；食神在月干=兄弟灾；食神与家里无关=仅精神层面；枭逢生就夺=投资/被欠款
level_signal: null
confidence_init: 4.5
falsifiable_by: 枭旺但不见食神时不叫夺食而是偏印生身有利
case_evidence:
  - "Y-01 L3699 偏印生身有利先断贵 再看夺食是命中灾"
  - "Y-01 L3699 食神落时支女命百分百子女有灾"
  - "Y-01 L3721 连着体的食神不能坏 坏了身体有灾"
cross_ref:
  m1_internal: M1-D-008(格局)
  topics: [health, family]
calibration_rule_id: R-M2-11
```

```yaml
rule_id: M2-Y-045
name: 食伤混局性格与管理（顺毛捋/不能逆）
sect: yang
author: 杨清娟
source: [Y-01 §细解食伤混局 L3721-3727]
trigger:
  condition: 命局食神伤官同见
  prerequisites: [食伤双透或双根]
conclusion: 食伤混局=顺毛捋性格不能逆；奉献+聪明结合=可创造价值；逆则造反；土一片无泄=死犟负面+不可培养
level_signal: null
confidence_init: 3.5
falsifiable_by: 食伤混但有印制一方时归为清
case_evidence:
  - "Y-01 L3721 食伤混局顺毛捋不能逆着来"
  - "Y-01 L3721 食神大度+伤官聪明结合就完美"
  - "Y-01 L3727 命局一摊土没有泄的死犟不可培养"
cross_ref:
  topics: [career]
calibration_rule_id: R-M2-11
```

```yaml
rule_id: M2-Y-046
name: 财坏印判定条件（身弱时财克印=道德败坏；印合财=用知识赚钱）
sect: yang
author: 杨清娟
source: [Y-01 §财坏印 L3727-3746]
trigger:
  condition: 命局财星克制印星
  prerequisites: [印为用神且身弱需印]
conclusion: 财克印+身弱=道德败坏/去官罢职/贫困/女命离婚；印合财=四两拨千斤用知识赚钱；命有官杀通关则财不直接坏印
level_signal: null
confidence_init: 4.0
falsifiable_by: 财弱印旺时财克不动印 不算财坏印
case_evidence:
  - "Y-01 L3727 真正财坏印印一定是家里的身弱要用的印"
  - "Y-01 L3727 印合财=学有所用四两拨千斤"
  - "Y-01 L3746 财坏印有时是道德败坏有时是管理能力(看组合)"
cross_ref:
  m1_internal: M1-D-005(做功)
  topics: [wealth, career]
calibration_rule_id: R-M2-11
```


### &sect;2.7 大运流年与劫财见财（M2-Y-047..048，2条）

```yaml
rule_id: M2-Y-047
name: 大运流年作用关系（好运坏年=挫折非失败；坏运好年=虚像）
sect: yang
author: 杨清娟
source: [Y-01 §大运看法 L3948-3990, Y-01 §自信自负自卑受挫折 L4018]
trigger:
  condition: 评估某年吉凶时
  prerequisites: [大运吉凶已判, 流年吉凶已判]
conclusion: 好运+坏年=坏不到哪去只是挫折有贵人；好运+好年=一发不可收拾；坏运+好年=虚像看别人赚钱自己投资必败；命好运差=龙盘虎卧
level_signal: null
confidence_init: 4.5
falsifiable_by: 好运中连续2年坏流年=提前收场（大运末2年坏流年进来）
case_evidence:
  - "Y-01 L3948 好大运坏流年坏不到哪里去"
  - "Y-01 L3948 坏大运好项目看别人赚钱自己投资不攻自破"
  - "Y-01 L4018 好大运坏流年叫受挫折不叫失败 能遇贵人"
cross_ref:
  m1_internal: M1-D-138(应期-大运流年)
  topics: [wealth, career]
calibration_rule_id: R-M2-08
```

```yaml
rule_id: M2-Y-048
name: 劫财见财完整判法（有印=扩大经营；无印无力=必破财）
sect: yang
author: 杨清娟
source: [Y-01 §细解劫财见财 L4030-4073]
trigger:
  condition: 命局比劫与财对峙 + 大运流年引动
  prerequisites: [比劫/财力量已比较]
conclusion: 家里有印+比劫来=事业扩大(比劫给我打工)；无印+比劫>我=必破财；官杀引动比劫=100%破财；流年地支家里=决策失误/地支外来=被骗；中神力>隅神力定竞争胜负
level_signal: null
confidence_init: 4.5
falsifiable_by: 比劫见财但财从家出+力量平衡=事业勉强扩大不破
case_evidence:
  - "Y-01 L4030 家里有印比劫来=事业扩大 贵人"
  - "Y-01 L4030 无印无力必破财 官杀引动比劫必破"
  - "Y-01 L4030 乾造 戊子年比劫合财投资失误破财2000多万"
cross_ref:
  m1_internal: M1-D-170(婚姻-劫财见财)
  topics: [wealth]
calibration_rule_id: R-M2-08
```


---

## &sect;3 &middot; 既有规则的强化字段

| 既有 rule_id | 强化字段 | 本批补充内容 | 章节锚点 |
|---|---|---|---|
| M2 §1.1 真假虚实 | examples_y01 | 十神真假=有根有气为真/无根无气为假；虚实≠真假两个概念 | Y-03 L1938 §第四章 |
| M2 §1.2 完整性原则 | deepening_y01 | 完整=不受穿破克坏；官命要求官完整独立存在 | Y-02 L383 |
| M2 §1.3 化敌为友 | cases_y03 | 化杀生枭>化官生印>合官 层次排序首次量化 | Y-03 §第五章 |
| M2 §1.4 财官取得层次 | detail_y01 | 补充"禄合外财可得但禄冲外财=贫贱" | Y-01 L3874 |
| M2 §2.1 五合化合产生物 | validated | Y-01 L532-660 原始出处确认 | Y-01 §十天干五合 |
| M2 §2.2 化合3状态 | cases_y01 | 搅局星6组具体实例+力量对比判定 | Y-01 L678-786 |
| M2 §0 与M3差异表 | deepening | 暗引5组是M2独有；段派无此概念 | Y-01 L4073 |
| M1-D-001 宾主四层 | yang_parallel | 杨派家里/家外=段派主位/宾位 对等 | Y-01 L3874 |
| M1-D-003 体用分类 | yang_terms | 杨派体=印比食伤禄；用=财官 完全一致 | Y-01 L3874 |
| M1-D-005 做功六法 | yang_合用 | 杨派天干五合=段派合用；强调效率最高 | Y-01 L532 |
| M1-D-008 格局通辨 | yang_version | 杨派格局=十神有对应配置；化杀>制杀层次 | Y-03 §第五章 |
| M1-D-116 合用做功 | yang_搅局 | 搅局星6组+三状态补充 | Y-01 L678 |
| M1-D-122 富贵贫贱 | yang_7等 | 杨派7等财富级别排序 | Y-01 L3801 |
| M1-D-138 应期 | yang_气数 | 气数犹在/气数已尽 概念 | Y-01 L3481 |
| M1-D-170 婚姻 | yang_3步 | 宫位先于星+印运成婚+星虚透理论 | Y-02 L538 |

---

## &sect;4 &middot; 关键案例归档

| 例号 | 八字 | 触发规则 | 一句话断 |
|---|---|---|---|
| Y02-ex1 | 乾：壬寅丙午己酉壬申 | M2-Y-033 食伤制杀力量对比 | 食伤力≈杀力 副部级国家电网 |
| Y02-ex2 | 乾：食神合官 戊子合=弱制 | M2-Y-033 弱制得官 | 命主县长 |
| Y01-ex1 | 坤：甲己合+巳申合食神制杀 | M2-Y-034 开库+M2-Y-035 | 发财命 取之不尽 |
| Y01-ex2 | 乾：劫财见财 月令水>日主 | M2-Y-048 劫财见财 | 戊子年投资失误破财2000万 |
| Y02-ex3 | 坤：日水坐辰 子巳合 | M2-Y-038 婚姻 | 己巳年谈对象庚午年结婚 分居十年 |
| Y01-ex3 | 月令劫财 印先生劫再生我 | M2-Y-021 体取财官 | 品牌代理老板 |
| Y03-ex96 | 蒋介石：丙戌丁亥 | M2-Y-032 化杀生枭 | 伤官伤尽是为奇 大贵 |
| Y01-ex4 | 甲辰日 时上有禄 戌冲辰 | M2-Y-034 开库 | 用禄冲开印库发财 |

---

## &sect;5 &middot; 跨派/跨源不一致点

| 矛盾点 | 本批论断 | 已有段派论断 | 进入rule-conflicts? |
|---|---|---|---|
| 干支作用范围 | 杨派：异柱天干与地支不作用(Y-01 L3994) | 段派：邻位有限制作用(M1-D-001宾主论) | 待观察 |
| 格局定义 | 杨派：十神有对应配置=格局(Y-03) | 段派：16格局正变体系(M1-D-008) | 互补非矛盾 |
| 财富排序 | 杨派：7等明确排序(官杀库最大) | 段派：L5极少下断(M1整体保守) | 互补 |
| 开库主体 | 杨派：必须用自己根基开(Y-01 L3501) | 段派：冲开/合开均可(M1-D-005) | 待细化 |

---

## &sect;6 &middot; 关键论断（&le;20条直引）

1. "天干五合做功效率最高。合财合官层次高，克财克官层次低。" —— Y-01 L3874
2. "禄可以合财合官就是富贵命，禄冲财冲官就是贫贱卑微命。" —— Y-01 L3874
3. "家里有的肯定先拿家里的，外面的东西再好我也不敢轻易拿。" —— Y-01 L3874
4. "食伤旺暗引比劫=有良好人际关系=有贵人命。" —— Y-01 L4073
5. "化杀生枭枭生身不见食神此命官肯定大。" —— Y-03 §第五章
6. "好大运坏流年坏不到哪里去。" —— Y-01 L3948
7. "坏大运好项目看别人赚钱轻松自己投资不攻自破。" —— Y-01 L3948
8. "星虚透见根时容易借力动情。" —— Y-02 L578
9. "官杀混杂女命基本都犯桃花都会离婚。" —— Y-02 L675
10. "开财库我的根没参与看别人发财。" —— Y-01 L3501
11. "食神和杀力量相当一定求官有大不做小。" —— Y-02 L1
12. "正偏印混局考试一定失利走神。" —— Y-01 L3691
13. "枭神夺食食神落时支女命百分百子女有灾。" —— Y-01 L3699
14. "气数犹在=前好运走完流年同神还好一年。" —— Y-01 L3481
15. "劫财见财引动比劫必破财定律。" —— Y-01 L4030
16. "财坏印=道德败坏；印合财=四两拨千斤。" —— Y-01 L3727
17. "三合局中神必须在旺点才能合成。" —— Y-01 L3750
18. "命中有财无官食伤当财看财过河级别大。" —— Y-01 L4121


---

## &sect;7 &middot; 待回灌 module-2-yang 的字段建议表

| rule_id | 待补字段 | 来源章节 | 优先级 |
|---|---|---|---|
| M2-Y-019 | 新增 §3.1 寻根基方法论 | Y-01 L3874, Y-03 L1938 | P0 |
| M2-Y-020 | 新增 §3.2 根/气/库力量层级 | Y-01 L3930 | P0 |
| M2-Y-021 | 补充 §1.4 财官取得层次排序 | Y-01 L3874, L3552 | P0 |
| M2-Y-024 | 补充 §2 天干五合 完整规则 | Y-01 L532-786 | P0 |
| M2-Y-025 | 补充 §2.2 化合3状态 详细判定 | Y-01 L532-594 | P1 |
| M2-Y-026 | 新增 §2.3 搅局星6组 | Y-01 L678-786 | P1 |
| M2-Y-029 | 补充/重写 §暗引系统 5组公式 | Y-01 L4073-4127 | P0 |
| M2-Y-030 | 新增 §暗引→学历方向 | Y-01 L4107 | P1 |
| M2-Y-031 | 新增 §格局判定 杨派版 | Y-03 §第五章 | P1 |
| M2-Y-032 | 补充 §化敌为友 层次排序量化 | Y-03 §第五章 | P0 |
| M2-Y-033 | 新增 §食制杀力量判定 | Y-02 L1-32 | P0 |
| M2-Y-034 | 补充 §开库 完整原则 | Y-01 L3501, Y-03 L2196 | P0 |
| M2-Y-035 | 新增 §财富7等排序 | Y-01 L3801 | P0 |
| M2-Y-036 | 补充 §三合局 中神条件 | Y-01 L3750 | P1 |
| M2-Y-037 | 新增 §气数 大运流年交替 | Y-01 L3481 | P1 |
| M2-Y-038 | 新增 §婚姻3步法 | Y-02 L538 | P0 |
| M2-Y-039 | 新增 §星虚透理论 | Y-02 L578 | P0 |
| M2-Y-040 | 新增 §离婚条件 | Y-02 L645 | P1 |
| M2-Y-041 | 补充 §六亲 宫位+星定位 | Y-02 L245 | P1 |
| M2-Y-042 | 新增 §官命9种取法 | Y-02 L365 | P0 |
| M2-Y-043 | 新增 §正偏印混局 | Y-01 L3691 | P1 |
| M2-Y-044 | 新增 §枭神夺食完整判法 | Y-01 L3699 | P0 |
| M2-Y-045 | 新增 §食伤混局 | Y-01 L3721 | P2 |
| M2-Y-046 | 新增 §财坏印判定 | Y-01 L3727 | P1 |
| M2-Y-047 | 补充 §大运流年作用 | Y-01 L3948 | P0 |
| M2-Y-048 | 新增 §劫财见财完整判法 | Y-01 L4030 | P0 |

---

## &sect;8 &middot; 与既有 d-NN-theory / M1 的 diff

| 维度 | M1 段派已有 | 本批杨派新增 delta |
|---|---|---|
| 宾主/家里家外 | M1-D-001 四层递进 | 杨派"家里/家外"=段派"主位/宾位" 等价但表述更直白 |
| 做功方式 | M1-D-005 六法（制/化/生泄/合/墓/复合）| 杨派强调"合=效率最高"且给出明确层次排序 |
| 格局通辨 | M1-D-008 16格局正变 | 杨派格局="十神有对应配置"+化杀>制杀层次 |
| 富贵判定 | M1-D-122 三分法 | 杨派7等财富级别+天地一气平衡观 |
| 应期 | M1-D-138 三法则 | 杨派气数犹在/气数已尽+好运坏年法则 |
| 婚姻 | M1-D-170 系统化 | 杨派宫位先于星+星虚透理论+印运成婚 |
| 暗引 | 段派无此概念 | **杨派独有** 十神暗引5组 |
| 开库 | M1-D-005 墓用 | 杨派"自己根参与"条件更严格 |

---

## &sect;9 &middot; 自检清单

- [x] §0 摘要 ≤ 20 行（10行）
- [x] §2 新规则坯每条都有 ≥ 3 案例 + falsifiable_by（30条全部满足）
- [x] §3 强化字段表 ≥ 10 行（15行）
- [x] §6 直引 ≤ 20 条 + 每条 ≤ 30 字（18条全部符合）
- [x] §7 字段建议表 ≥ 25 行（26行）
- [x] 总行数 800-2000 行（预估~950行）
- [x] 全文 grep 不到任何整段 > 50 字的原文复制
- [x] 每条 source 锚点都用 Y-NN §章节 形式（L-002）
- [x] 每条事实陈述都可 grep 到原文（L-003）
- [x] commit 颗粒度 ≤ 1 个 theory 文件（L-007）

---

**y01-y05-theory.md 完毕。30 条新规则 M2-Y-019..048。Stage 3 进度 1/6。**
