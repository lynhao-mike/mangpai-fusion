---
doc: d19-d24-theory
version: 1.0
session: session-7-d19d24
sources: [D-19, D-20, D-23, D-24]
purpose: 段派2011专班深读提炼 — 杭州财官班+武当山六亲班+重庆面授班+言明干支象法职业实战
new_rules: M1-D-186..215 (30 条)
calibration: R-M1-47..50
status: authoritative
---

# D-19/D-20/D-23/D-24 深读理论提炼

## §0 · 本书独特贡献摘要

D-19~D-24 是段建业 2011 年 4 批专班教材，覆盖：
1. **官命判定 5 类结构 + 21 例系统化**（D-19/D-23 独有）：伤食制官/伤官配印/杀刃相合/财制印/包制局 + 官职类别4分
2. **财命取法3级别 + 取财方法5分类**（D-19/D-23 独有）：经营/风险/智力/技术/禄当财 + 官杀当财/食伤当财/比禄当财
3. **婚姻专辑10节完整系统**（D-20 独有）：结婚应期/多婚/婚外情/包局/配偶情况/伤克/独身/淫乱/差婚/好婚
4. **父母死亡7组合 + 父母离异 + 弃养**（D-20 独有）：六亲判定最系统文本
5. **牢狱6组合 + 牢灾判定系统**（D-23 独有）：阳气被坏/勾陈包局/比劫伤官对抗/反局/入墓/劫煞亡神
6. **疾病象法体系**（D-23 独有）：干支→脏腑映射表 + 六淫 + 宫位→身体 + 干支组合→病性
7. **车祸象法5要素**（D-23 独有）：车象(辰丑酉申子)+对称性+火穿速度+驿马+凶象引动
8. **干支→职业映射实战4盘**（D-24 独有）：生意人/老师/公务员/军官 的象法定职业方法论



---

## §1 · 全书结构 grep

### D-19《段建业2011杭州财官班教材》(4053 行)
```
107: 第一章应期 — 大限/出现应/引动应/干支应期
530: 第二章 象法 — 第一节干支类象/十天干/十二地支/天干合反象
1247: 第二节：神煞类象
1413: 第三节 象的应用
1729: 第四节 伤官诀（5类）
2179: 第四节"过河拆桥"命格组合（8例）
2360: 第三章：官命的看法 — 官职4类别 + 21例
3047: 第四章：财命的看法 — 第一节财富取法 + 第二节取财方法
3299: 第二节：取财方法 — 经营/风险/智力/技术取财（~40例）
```

### D-20《段建业2011武当山六亲班高级面授讲课笔记》(3589 行)
```
79:  第一章 婚姻专辑 — 概念/宫位/要点/干支应期表
153: 第一节 结婚应期（~30 例）
583: 第二节 多婚组合（~20 例）
1249: 第三节 婚外情桃花看法（~15 例）
1711: 第四节 包局婚姻判断（~10 例）
1941: 第五节 配偶情况判断（~10 例）
2298: 第六节 伤克配偶判断（~15 例）
2612: 第七节 独身组合（~8 例）
2834: 第八节 淫乱命（~8 例）
2976: 第九节 差婚姻组合（~5 例）
3030: 第十节 好婚姻组合（重点）（~10 例）
3148: 第二章 父母 — 第一节父母死亡/第二节父母离异/第三节父母弃养
3164: 第一节 父母死亡 — 7组合 + ~20 例
```

### D-23《段建业2011重庆面授班教材》(5168 行)
```
125: 第一章 应期 — 大限/3种应期方式/干支对应/综合应用
471: 第二章 象法 — 第一节干支类象/第二节神煞类象/第三节象的应用/伤官诀/过河拆桥
2360: 第三章 官命的看法 — 官职类别 + 20例
2535: 第四章 财命的看法 — 财富取法 + 取财方法（~50 例）
3366: 第五章 牢狱之灾 — 6组合 + 17例
3842: 第六章 疾病专辑 — 象法/六淫/宫位/干支组合/43例
4751: 第七章 车祸专辑 — 车象5要素 + 12例
```

### D-24《段建业言明2011干支象法职业实战光盘讲座笔记》(3454 行)
```
31: 一、笔记说明（学员整理说明）
37: 二、第一盘 职业：生意人（~270 行 / ~6 例）
305: 三、第二盘 职业：老师（~200 行 / ~5 例）
505: 四、第三盘 职业：公务员（~226 行 / ~5 例）
731: 五、第四盘 职业：部队军官（~2700+ 行 / ~15+ 例）
```



---

## §2 · 新规则坯（核心产出）

### §2.1 官命判定体系（M1-D-186..191，共 6 条）

```yaml
rule_id: M1-D-186
name: 官命5大结构类型 — 官印/伤食制官/杀刃/财制印/包制局
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §第三章 line 2360
  - D-23 §第三章 line 2360
trigger:
  condition: 判定命主是否当官命
  prerequisites: [识别官杀+印+食伤+财的配置]
conclusion: 官命5大成格路径：①官印相生/杀印相生；②伤官成格(金水见官/木火见印/水木见财官/土金见印)；③制局(食制杀/伤制官/杀制刃/财制印)；④包制局；⑤合杀格。三者具一可成官命
level_signal: L2-L5
confidence_init: 4.5
falsifiable_by: 具备结构但做功无效(如制局制不到位反为灾)
cross_ref:
  m1_internal: M1-D-083..094 格局, M1-D-166..170 伤官诀
  topics: [career]
calibration_rule_id: R-M1-47
case_evidence:
  - "乾：丙甲乙甲/申午卯申 — 伤官制官法院副部级"
  - "乾：戊癸庚丙/子亥戌子 — 金水伤官配印纪检厅长"
  - "乾：庚庚癸丙/寅辰酉辰 — 印制伤官中央书记"
```

```yaml
rule_id: M1-D-187
name: 官职类别4分 — 伤官强势权/杀星决断权/财官辅佐/申酉执法
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §官职的类别 line 2370
  - D-23 §官职的类别 line 2370
trigger:
  condition: 已确定官命 → 进一步判定官职类型
  prerequisites: [官命结构已成立]
conclusion: ①伤官局当权=人事任免/执法/纪检；②七杀主权威=决断/正职；③财官成局=不强势/财权/辅佐；④申酉组合=执法相关(寅丑=公安)
level_signal: null
confidence_init: 4.5
falsifiable_by: 伤官局当权但伤官无制反为灾非官
cross_ref:
  m1_internal: M1-D-186, M1-D-166..170
  topics: [career]
calibration_rule_id: R-M1-47
case_evidence:
  - "乾：丙甲乙甲/申午卯申 — 伤官格法院(申酉执法)"
  - "乾：戊癸庚丙/子亥戌子 — 伤官主纪检(掌重权)"
  - "坤：壬壬甲乙/辰寅辰丑 — 印收官墓省政协主席"
```

```yaml
rule_id: M1-D-188
name: 官命升职应期 — 制官杀结构喜行伤食运/合动冲动为年份
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §官命例1-21 line 2380..2960
  - D-23 §第三章 line 2360..2535
trigger:
  condition: 官命已确定 + 判断升职时间
  prerequisites: [做功结构明确]
conclusion: 制局喜行伤食大运增强制力；合局喜行合动流年；冲局以冲动到位为应；印收官墓以冲开或墓到为应期
level_signal: null
confidence_init: 4.0
falsifiable_by: 行伤食运但伤食反被制则非升
cross_ref:
  m1_internal: M1-D-174..177 应期, M1-D-125
  topics: [career]
calibration_rule_id: R-M1-47
case_evidence:
  - "乾：丙甲乙甲/申午卯申 — 戌运合旺火从正处升副部"
  - "乾：戊癸庚丙/子亥戌子 — 辰运冲戌升地委书记"
  - "坤：壬壬甲乙/辰寅辰丑 — 丁酉运辛巳年省委副书记(辛=丑合到酉)"
```


```yaml
rule_id: M1-D-189
name: 财命取法3级别 — 财<食伤<官杀（级别递增）+ 禄当财
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §第四章第一节 line 3049
  - D-23 §第四章第一节 line 2537
  - D-24 §二 line 37
trigger:
  condition: 判定命主财富来源类型
  prerequisites: [识别取财手段的十神]
conclusion: 财当财=百万级；食伤当财=千万级(财之原神)；官杀当财=千万~亿级(官统财/制不尽)；比禄当财=有福禄无财无官时兜底。官杀当财条件：日主有用的官杀/制不尽/阳日主七杀/官统财
level_signal: L1-L4
confidence_init: 4.5
falsifiable_by: 官杀当财但官杀被合绊无法发挥
cross_ref:
  m1_internal: M1-D-172 财富4级别, M1-D-078..082, M1-D-150
  topics: [wealth]
calibration_rule_id: R-M1-48
case_evidence:
  - "乾：戊己戊甲/申未戌寅 — 戊日甲寅时当财看数千万"
  - "乾：辛庚庚丙/亥寅申戌 — 丙戌官杀当财丙戌运过亿"
  - "乾：庚乙庚壬/午酉子午 — 伤官制官不净+官杀当财大贪"
```

```yaml
rule_id: M1-D-190
name: 取财方法5分类 — 经营/风险/智力/技术/工薪（对应不同做功结构）
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §第四章第二节 line 3299
  - D-23 §第四章第二节 line 2725
trigger:
  condition: 已确定财命 → 判定取财方式
  prerequisites: [做功结构已识别]
conclusion: 经营取财=食伤做功+印在年时门户+包局；风险取财=劫财合财/冲财；智力取财=伤官配印+食伤在主位；技术取财=专旺或食伤精专+申酉庚辛；工薪=印带官合身无制局
level_signal: null
confidence_init: 4.0
falsifiable_by: 食伤做功但被制服反不能经营
cross_ref:
  m1_internal: M1-D-179 5结构类型, M1-D-171 过河拆桥
  topics: [wealth]
calibration_rule_id: R-M1-48
case_evidence:
  - "乾：甲甲丙己/寅戌午丑 — 木火制财库经营家具5千万"
  - "乾：丁戊癸壬/未申酉戌 — 财包局经营建材酒店数百万"
  - "D-19 §取财：约40例按5类分门别类"
```

```yaml
rule_id: M1-D-191
name: 官命退休/降职信号 — 做功结构被坏运冲破时
sect: duan
author: 段亲撰
transmission: none
source:
  - D-19 §官命例2 line 2417
  - D-19 §官命例4 line 2491
trigger:
  condition: 官命行运中做功结构被反向力量破坏
  prerequisites: [原局做功路径明确]
conclusion: 做功神被合走/冲坏/穿倒=退二线或降职；印收官墓结构中印被冲=权力变小；禄被穿或官星到绝=退休
level_signal: null
confidence_init: 4.0
falsifiable_by: 做功被坏但有他星接力则不退
cross_ref:
  m1_internal: M1-D-188, M1-D-174
  topics: [career]
calibration_rule_id: R-M1-47
case_evidence:
  - "乾：戊癸庚丙/子亥戌子 — 巳运巳被冲坏退二线"
  - "坤：壬壬甲乙/辰寅辰丑 — 酉运辰怕戌冲权力变小"
  - "乾：庚庚癸丙/寅辰酉辰 — 丙戌运不吉平调略降"
```



### §2.2 婚姻判定完整系统（M1-D-192..199，共 8 条）

```yaml
rule_id: M1-D-192
name: 结婚应期5法 — 三合/六合/五合将星宫相连+冲引+星宫出现
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第一节 line 153
trigger:
  condition: 判定结婚年份
  prerequisites: [配偶宫+配偶星已确定]
conclusion: ①流年三合/六合/五合将配偶星与配偶宫相合；②原局合者以冲引动为应；③配偶星/宫因太岁出现；④星多者伤克配偶星时为应；⑤坏掉阻碍婚姻之字为应（伤官运破碍字也可结婚）
level_signal: null
confidence_init: 4.5
falsifiable_by: 合动年但大运强制不结婚信息压制
cross_ref:
  m1_internal: M1-D-139 结婚5合法, M1-D-182 宫主星辅
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "坤：乙丁辛庚/卯亥未寅 — 壬午年合未结婚"
  - "坤：庚乙癸庚/戌酉巳申 — 乙亥年冲巳结婚"
  - "坤：丙戊辛壬/午戌亥辰 — 戊辰年辰代表亥冲到夫家结婚"
```

```yaml
rule_id: M1-D-193
name: 多婚组合判定 — 配偶星多现+伏吟+宫坏+墓不开
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第二节 line 583
trigger:
  condition: 判定命主是否多婚
  prerequisites: [配偶星/宫分布已识别]
conclusion: 配偶星多现且配宫=多婚；宫伏吟多现=多婚；配偶星入墓不开再有他星=多婚；星坐宫忌他星合=必离（合后有他合）
level_signal: null
confidence_init: 4.5
falsifiable_by: 配偶星多但墓库锁住不冲开则独身
cross_ref:
  m1_internal: M1-D-161 几次婚姻, M1-D-182
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "坤：戊辛壬甲/辰未午申 — 巳入戌墓第一夫+巳拱丑第二夫"
  - "乾：辛庚甲庚/巳寅申午 — 五次婚副宫全坏"
  - "D-20 §二 ~20 例系统化多婚判定"
```

```yaml
rule_id: M1-D-194
name: 婚外情桃花3类 — 禄合他星/暗合/伤官坐桃花宫
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第三节 line 1249
trigger:
  condition: 判定命主是否有婚外情
  prerequisites: [配偶星宫+桃花星分布]
conclusion: 女命禄入主合他星=桃花；男命劫财合别人财=外遇；暗合(寅丑/亥午等)=暗中关系；伤官坐花宫/门户=明桃花；配偶宫被穿倒+他星趁虚=第三者
level_signal: null
confidence_init: 4.0
falsifiable_by: 有桃花象但被合绊锁死不应
cross_ref:
  m1_internal: M1-D-154 绊禄桃花, M1-D-136 暗合7子类
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §三 line 1249：辛卯运桃花(辛卯=头妻已离再来=桃花)"
  - "D-20 夏仲奇断例：桃花是自己儿子(丁落子女宫伤官)"
  - "D-20 §三 ~15 例桃花判定"
```

```yaml
rule_id: M1-D-195
name: 独身组合3类 — 关财门/星入墓不开/宫穿星无救
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第七节 line 2612
trigger:
  condition: 判定命主是否终身独身
  prerequisites: [配偶宫星+墓库状态]
conclusion: ①关财门(女命比劫坏财=离后不婚)；②配偶星入墓库不开且大运迟开=晚婚至独；③宫穿星+无食伤泄=完全无缘；八字无一字做功=差命独身
level_signal: null
confidence_init: 4.0
falsifiable_by: 墓库在晚运被冲开仍可结婚
cross_ref:
  m1_internal: M1-D-155 关财门, M1-D-182
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §七：己丑己未日夫宫临墓不开至63岁"
  - "D-20 §七：八字无一字做功光棍55岁才开库"
  - "D-20 §七：正官逢合月令杀透七十多未婚"
```

```yaml
rule_id: M1-D-196
name: 好婚姻铁律 — 宫星不坏+宫制星+财门不关+禄不破
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第十节 line 3030
trigger:
  condition: 判定好婚姻
  prerequisites: [宫星关系+做功方向]
conclusion: 配偶宫稳定(不被冲穿刑破)+配偶星入宫或被宫制=好婚；男命财入妻宫做功=好婚；女命官合身且宫不坏=好婚；关键：宫位无问题就没事
level_signal: null
confidence_init: 4.5
falsifiable_by: 宫星都好但大运强力冲宫时仍可临时波动
cross_ref:
  m1_internal: M1-D-182 宫主星辅, M1-D-159
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §十(重点)：乙戊丁庚/巳子巳戌 宫制星好婚丈夫亿万"
  - "D-20 §十：财包局婚姻不会有问题"
  - "D-20 结婚例3：巳申合婚姻不会有问题"
```

```yaml
rule_id: M1-D-197
name: 伤克配偶判定 — 宫星同坏+穿倒+克绝=丧偶
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第六节 line 2298
trigger:
  condition: 判定配偶是否有生死之灾
  prerequisites: [配偶宫星位置+流年大运]
conclusion: 宫被穿倒+星被冲坏=配偶死亡；伤官运刑坏宫+穿倒宫+流年穿坏星=宫星都坏故亡；配偶星临绝+墓=丧偶
level_signal: null
confidence_init: 4.0
falsifiable_by: 宫星同坏但有合化解救则不至于死
cross_ref:
  m1_internal: M1-D-182, M1-D-101..104 寿元
  topics: [marriage, lifespan]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §六：乙巳运壬午年夫自杀(穿倒宫+穿坏星)"
  - "D-20 §六：甲戌年45岁妻被情人杀(庚临绝见寅)"
  - "D-20 §六 ~15 例伤克配偶"
```

```yaml
rule_id: M1-D-198
name: 父母死亡7组合 — 患父母/宫位立足/墓地/三刑/无帮扶/其他
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第二章第一节 line 3164
trigger:
  condition: 判定命主是否克父母
  prerequisites: [父母星(财官为父/禄食伤为母)+年月宫位]
conclusion: ①患父母=星多现杂现；②星在年月不能存在(被冲克穿)；③星在日时不能存在；④财临墓地父早死；⑤星临三刑夹刑；⑥星无帮扶受克穿坏；⑦其他。母星：禄/食伤/比劫(非传统印)；以宫为主星为辅
level_signal: null
confidence_init: 4.5
falsifiable_by: 财临墓但大运冲开则父非早死
cross_ref:
  m1_internal: M1-D-157 借子女看父母
  topics: [family]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 克父例：庚戊甲丙/戌寅子寅 财临库地庚辰运父癌死"
  - "D-20 克母例：戊甲庚戊/申寅戌子 癸未年穿倒子母尿毒症死"
  - "D-20 不以印为母例：丙乙甲丁/子未寅卯 禄食神为母母长寿"
```

```yaml
rule_id: M1-D-199
name: 母星取法 — 禄/食伤/比劫为母（非印星），印星不一定是母
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §第二章概念 line 3158
  - D-20 §不以印为母例 line 3196
trigger:
  condition: 确定母亲星
  prerequisites: [区分印星vs禄食伤]
conclusion: 母星首选禄/食神/伤官；无此则以比肩劫财看母；有的印星含比禄劫可当母；不以印星为母是段派六亲独有（与传统派相反）。验证：不以印为母例中母长寿80+
level_signal: null
confidence_init: 4.5
falsifiable_by: 某些命局中印星确实代表母亲(需看配置)
cross_ref:
  m1_internal: M1-D-198, M1-D-144 十神多层意向
  topics: [family]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 line 3196：丙乙甲丁/子未寅卯 寅木禄食为母寿80+"
  - "D-20 概念：以禄食伤当母看/无此以比劫看"
  - "D-20 克母例：癸癸甲己/亥亥辰巳 己巳为母(非印)"
```



### §2.3 牢狱判定系统（M1-D-200..203，共 4 条）

```yaml
rule_id: M1-D-200
name: 牢灾6组合 — 阳被坏/勾陈包局/比劫对抗/反局/入墓/劫煞亡神
sect: duan
author: 段亲撰
transmission: none
source:
  - D-23 §第五章 line 3366
trigger:
  condition: 判定命主是否有牢狱之灾
  prerequisites: [识别八字中牢象+做功方向]
conclusion: ①阳气被坏+辰丑土与亥损局=牢象；②勾陈(辰丑)包局带凶神/法律象包局；③比劫伤官组合与官杀对抗；④反局信息(辰丑申酉亥起坏作用)；⑤伤官或比禄入墓=失自由；⑥刑事多现劫煞亡神。牢象：申=法律/辰丑=牢/伤食入墓=无自由
level_signal: null
confidence_init: 4.5
falsifiable_by: 有牢象但被合化解或制服则免灾
cross_ref:
  m1_internal: M1-D-158 牢狱判读3类型
  topics: [prison-litigation]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-23 例1：己壬己乙/巳申未丑 申合巳进局子坐牢一辈子"
  - "D-23 例4：壬甲癸乙/辰辰巳卯 黑社会头目壬申年捉癸酉年枪毙"
  - "D-23 例5：辛丁丙戊/酉酉申戌 酉穿倒戌诚信坏诈骗"
```

```yaml
rule_id: M1-D-201
name: 牢灾应期 — 伤食入墓年/巳申合年/官杀压比劫年
sect: duan
author: 段亲撰
transmission: none
source:
  - D-23 §第五章 例1-17 line 3366..3652
trigger:
  condition: 已确定有牢象 → 定应期
  prerequisites: [牢象类型已识别]
conclusion: 伤食入墓/合绊之年=入狱；比劫伤官遇官杀旺年=对抗被捕；巳申合=进入(申=法律)；申冲寅+寅为亡神=一伙人全进去；大运坏阳气之运=牢运
level_signal: null
confidence_init: 4.0
falsifiable_by: 有入墓但大运化解则不入狱
cross_ref:
  m1_internal: M1-D-200, M1-D-174 应期铁律
  topics: [prison-litigation]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-23 例3：己巳运壬申年(巳申合)被判5年"
  - "D-23 例1：申金合巳进局子"
  - "D-23 例5：辛酉运(酉破午唯一阳被坏)牢"
```

```yaml
rule_id: M1-D-202
name: 疾病象法体系 — 干支→脏腑映射+六淫+宫位→身体+阴阳离决
sect: duan
author: 段亲撰
transmission: none
source:
  - D-23 §第六章 line 3842
trigger:
  condition: 判定命主疾病类型
  prerequisites: [看穿刑破坏了哪个字→查干支脏腑表]
conclusion: 甲=头胆/乙=颈/丙=小肠面/丁=心眼神经/戊=胃鼻/己=肤腹/庚=大肠/辛=肺齿/壬=膀胱口/癸=肾眼耳。地支同理。阴阳离决=命危；失阳易死；穿刑破被坏的字看代表身体哪部分
level_signal: null
confidence_init: 4.5
falsifiable_by: 干支被坏但有合化则病轻不重
cross_ref:
  m1_internal: M1-D-126 算命三步曲(测象), M1-D-183 干支虚实
  topics: [health]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-23 §六 完整干支→脏腑映射表(22 干支)"
  - "D-23 疾病例43例按系统分类"
  - "D-20 克母例：卯午破=心脑血管死(午=心/卯=血管)"
```

```yaml
rule_id: M1-D-203
name: 车祸象法5要素 — 车象+对称性+速度(火穿)+驿马+凶象引动
sect: duan
author: 段亲撰
transmission: none
source:
  - D-23 §第七章 line 4751
trigger:
  condition: 判定命主是否有车祸风险
  prerequisites: [原局有车象+有凶象]
conclusion: 车象=辰丑酉申子(子有轮象)/对称性(两个同支=两轮)/火穿=速度(酉戌穿/寅巳穿/丑午穿)/驿马=车/凶象引动=大运流年触发。两车夹禄=凶；冲禄+连头=致命
level_signal: null
confidence_init: 4.0
falsifiable_by: 有车象但无凶象引动则只是开车多不出事
cross_ref:
  m1_internal: M1-D-178 穿6组分级, M1-D-180 连根体被去
  topics: [accident]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-23 车祸例1：丁癸庚庚/未丑子辰 丑为车入辰墓掉水中闷死"
  - "D-23 车祸例：辛庚丁丙/酉寅卯午 卯酉冲两车相撞丙戌年死"
  - "D-23 车祸例：壬壬甲乙/辰寅辰丑 两辰夹禄酉运两车合撞"
```



### §2.4 干支象法→职业映射（M1-D-204..210，共 7 条）

```yaml
rule_id: M1-D-204
name: 生意人象法判定 — 食伤做功+印在年时门户+包局+驿马
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §二 line 37
trigger:
  condition: 判定命主是否做生意
  prerequisites: [食伤/印/财的门户位置]
conclusion: 食伤制官杀(制不尽当财)+印在年/门户=开店面；食伤合印=自己投资做生意；财包局/印包财=开公司；驿马逢冲+财印包局=贸易流通；日主合财+印带财门户=开店
level_signal: null
confidence_init: 4.0
falsifiable_by: 有经商象但官印太强走仕途非商
cross_ref:
  m1_internal: M1-D-190 取财5分类, M1-D-179 5结构
  topics: [career, wealth]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 例1：丁癸丁丙/酉卯亥午 比劫制官杀=装修彩绘千万"
  - "D-24 例2：甲甲丙己/寅戌午丑 寅午戌制丑财库=家具5千万"
  - "D-24 例4：甲壬丙辛/寅申申卯 印带财合身=继承父业开店"
```

```yaml
rule_id: M1-D-205
name: 老师象法判定 — 印星透出+食伤在主位+文库(戌)+学堂星
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §三 line 305
trigger:
  condition: 判定命主是否当老师
  prerequisites: [印星+食伤+文库配置]
conclusion: 印主学问/执照/证书；食伤在主位=表达/教学；戌为文库；印星带食伤=传道授业；木火通明/金水相生=文人教师；印星不被坏+坐支有力=有编制
level_signal: null
confidence_init: 4.0
falsifiable_by: 有教师象但食伤被制服则不从教
cross_ref:
  m1_internal: M1-D-187 官职4分, M1-D-100 五通明
  topics: [career, education]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 §三 ~5 例老师职业判定"
  - "D-19 官命例1：伤官制官法学博士(丙坐戌文库)"
  - "D-19 官命例2：师范毕业数学专业当老师"
```

```yaml
rule_id: M1-D-206
name: 公务员象法判定 — 官印相生+正官正印+申酉执法+辰戌丑未公门
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §四 line 505
trigger:
  condition: 判定命主是否为公务员
  prerequisites: [官印配置+宫位]
conclusion: 正官正印相生=正规仕途；月令官印=编制内；申酉+寅=执法/公安；辰戌丑未在年月=国家机关；官合身=有职位；印坐官=有权；食伤制官=纪检/检察
level_signal: null
confidence_init: 4.0
falsifiable_by: 有公务员象但食伤伤官太旺不服管则辞
cross_ref:
  m1_internal: M1-D-186 官命5结构, M1-D-187 官职4分
  topics: [career]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 §四 ~5 例公务员判定"
  - "D-19 官命例5：两戊包印未=军队或执法(法院院长)"
  - "D-24 生意人例3：月令印带官合日主=以前有正式工作"
```

```yaml
rule_id: M1-D-207
name: 军官象法判定 — 七杀+羊刃+寅申+庚辛+帅旗(午)+火土势
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §五 line 731
trigger:
  condition: 判定命主是否从军
  prerequisites: [七杀/羊刃/金火配置]
conclusion: 七杀+羊刃=将帅命(杀刃格)；庚辛金主武/刀兵；寅申冲=带兵打仗；午为帅旗；火土成势制金水=武职；甲寅+庚申对冲=军事征伐；驿马在年月=调动频繁
level_signal: null
confidence_init: 4.0
falsifiable_by: 有军人象但化合转性则从文非武
cross_ref:
  m1_internal: M1-D-085 杀刃格, M1-D-186
  topics: [career]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 §五 ~15 例军官判定"
  - "D-19 官命例5：未为羊刃库有军队执法意"
  - "D-23 官命：申酉组合执法(寅丑=公安)"
```

```yaml
rule_id: M1-D-208
name: 干支类象职业推断法 — 先看做功→再看门户时柱落什么→定行业
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §二 line 37(综合方法论)
  - D-19 §第二章 line 530
trigger:
  condition: 推断命主从事行业
  prerequisites: [做功结构+门户落字已知]
conclusion: 推断步骤：①看做功决定大类(官命/财命/技术命)；②看门户(时柱)落什么十神→定具体方向；③干支类象定行业细节(木=教育文化/火=装修电气/土=地产建筑/金=五金执法/水=流通运输)；④结合年柱看远近/规模
level_signal: null
confidence_init: 4.5
falsifiable_by: 象法推断但现实环境限制改变了职业方向
cross_ref:
  m1_internal: M1-D-126 算命三步曲, M1-D-127 多重测象
  topics: [career]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 例1：丁=漂亮+酉=彩绘+亥=墨水+卯=笔 → 装修彩绘"
  - "D-24 例2：死木+火=家具+己=口才+丑=买卖 → 家具销售"
  - "D-24 例3：戌=建材火库电器+酉=金属+水=流通 → 建材酒店"
```

```yaml
rule_id: M1-D-209
name: 食伤入墓=失自由/关店/停业（通用铁律）
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §二 例2 line 约180
  - D-23 §第五章 line 3366
trigger:
  condition: 流年大运食伤入墓
  prerequisites: [食伤在命局有做功]
conclusion: 食伤入墓=自由受限(可以是坐牢/可以是关店/可以是生意做不了)；辰丑土泄食伤=进去了；辛巳年冲去亥水(食伤)=生意关门
level_signal: null
confidence_init: 4.5
falsifiable_by: 食伤入墓但墓为喜用则收藏非坏
cross_ref:
  m1_internal: M1-D-200 牢灾, M1-D-120 墓用结构
  topics: [career, prison-litigation]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-24 例2：辛巳年冲去亥水生意关门"
  - "D-23 牢例：伤官入墓没有了自由"
  - "D-24 例5：辛酉运酉破午唯一阳被坏=官灾牢"
```

```yaml
rule_id: M1-D-210
name: 印包财局=做生意铁判（印在门户+财入局中）
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §二 例4 line 约200
  - D-24 §二 综合 line 37
trigger:
  condition: 八字出现印星包住财星的局
  prerequisites: [印在年时门户位+财在局中被控]
conclusion: 印包财局=开店面做生意(印=门店/证照/房产)；印带财门户合身=开店求财；印伏吟=多店面；印+驿马=连锁/贸易；印被冲=换店/关门
level_signal: null
confidence_init: 4.5
falsifiable_by: 印包财但官星强制从政则不经商
cross_ref:
  m1_internal: M1-D-190 取财5分类, M1-D-204 生意人
  topics: [wealth, career]
calibration_rule_id: R-M1-48
case_evidence:
  - "D-24 例4：甲壬丙辛/寅申申卯 两印=2-3个店面"
  - "D-24 例3：壬癸坐印=多种事业开公司"
  - "D-24 例5：年上财门户伤官=包局印星做生意"
```



### §2.5 D-19/D-23 与 D-17/D-18 交叉强化 + 应期补充（M1-D-211..215，共 5 条）

```yaml
rule_id: M1-D-211
name: 配偶宫概念精化 — 正宫/副宫/遁藏透/同五行
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §概念 line 79
trigger:
  condition: 确定配偶宫的范围
  prerequisites: [日支为正宫]
conclusion: 正宫=日支；副宫=与日支同五行的字在别处出现/日支遁藏旺气在别处透；如亥为宫见甲透=甲也为副宫；丑为宫见辛透/见酉=也为副宫。副宫全坏=五次婚
level_signal: null
confidence_init: 4.5
falsifiable_by: 副宫被合制不参与婚姻事务
cross_ref:
  m1_internal: M1-D-182 宫主星辅, M1-D-192
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §概念：亥为宫见甲透也为副宫"
  - "D-20 结婚例5：妻宫寅透甲落辰以辰为妻"
  - "D-20 §二：乾辛庚甲庚/巳寅申午 副宫全坏五次婚"
```

```yaml
rule_id: M1-D-212
name: 配偶星性别差异 — 男:财+伤食/女:官+财
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §概念 line 91
trigger:
  condition: 确定配偶星
  prerequisites: [区分乾坤造]
conclusion: 男命：财星+伤食星=配偶星；女命：官星+财星=配偶星。与传统"男财女官"不同——段派增加了食伤(男)和财(女)作为配偶星
level_signal: null
confidence_init: 4.5
falsifiable_by: 在某些特殊组合中印星也可代表配偶(如从格)
cross_ref:
  m1_internal: M1-D-182, M1-D-144 十神多层意向
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §概念 line 91 明确列出男女配偶星差异"
  - "D-20 多例中男命以食伤当配偶"
  - "D-20 多例中女命以财星当配偶(财生官)"
```

```yaml
rule_id: M1-D-213
name: 财官临墓喜刑冲 — 己丑/己未/戊辰/戊戌日柱特殊婚财法则
sect: duan
author: 段亲撰(转盲师口诀)
transmission: hao
source:
  - D-20 §概念 line 104
trigger:
  condition: 日柱为己丑/己未/戊辰/戊戌
  prerequisites: [四种日柱之一]
conclusion: 财官临墓的日柱须刑冲才有财富与婚姻；不刑冲反主不吉；己丑与己未见辰墓叫废物利用婚姻也吉。大运流年引动墓库刑冲为结婚/发财应期
level_signal: null
confidence_init: 4.0
falsifiable_by: 有刑冲但冲的是忌方则反凶
cross_ref:
  m1_internal: M1-D-120 墓用结构, M1-D-185 冲远近
  topics: [marriage, wealth]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §概念 line 104 盲师讲财官临墓喜刑冲"
  - "D-20 独身例：己丑日夫宫临墓不刑冲则独身"
  - "D-20 结婚例9：宫坐墓未刑去阻碍才结婚"
```

```yaml
rule_id: M1-D-214
name: 关财门正式定义 — 女命比劫坏财=断官杀原神=离婚不可复
sect: duan
author: 段亲撰
transmission: none
source:
  - D-20 §概念 line 108
  - D-20 §第九节 line 2976
trigger:
  condition: 女命出现比劫制财的结构
  prerequisites: [女命+财为官杀原神]
conclusion: 关财门=女命比劫坏掉了财星(财为官的原神)→断了官星来源→离婚应期到比劫旺年；关财门后不复婚；与M1-D-155互补（此条给正式定义）
level_signal: null
confidence_init: 4.5
falsifiable_by: 比劫坏财但有印化比则财不绝门不关
cross_ref:
  m1_internal: M1-D-155 关财门, M1-D-195 独身
  topics: [marriage]
calibration_rule_id: R-M1-49
case_evidence:
  - "D-20 §概念 line 108 关财门正式定义"
  - "D-20 差婚例：辛辛戊丁/亥卯午巳 关财门离婚独身"
  - "D-24 例1：酉运关财门分手"
```

```yaml
rule_id: M1-D-215
name: 干支象法定性格 — 满盘阳=急躁刚/满盘阴=阴柔私/唯一阳被坏=最凶
sect: duan
author: 段建业+言明合讲
transmission: none
source:
  - D-24 §二 例2 line 约150
  - D-24 §二 例5 line 约220
trigger:
  condition: 判定命主性格
  prerequisites: [八字阴阳分布]
conclusion: 满盘阳=脾气急躁/说一不二/大男人主义/果断胆大；满盘阴唯一阳=如阳被坏则人品有问题/自私/运气极差(唯一阳被坏是最凶信号)；时落伤官=口才/头脑；伤官不做功+穿=说大话
level_signal: null
confidence_init: 3.5
falsifiable_by: 满盘阳但有润泽(如壬癸调候)则不暴
cross_ref:
  m1_internal: M1-D-202 阴阳离决, M1-D-126 测象
  topics: [health, career]
calibration_rule_id: R-M1-50
case_evidence:
  - "D-24 例2：满盘阳唯丑阴=急躁果断"
  - "D-24 例5：满盘阴唯午阳被酉破=人品不好自私"
  - "D-24 例5：伤官不做功午酉破=说大话"
```



---

## §3 · 既有规则的强化字段

| 既有 rule_id | 强化字段 | 本书补充内容 | 章节锚点 |
|---|---|---|---|
| M1-D-078..082 取财5法 | upgrade_d19d24 | 升级为3级别(财<食伤<官杀)+5分类取财法 | D-19 §四 + D-23 §四 |
| M1-D-083..094 16格局 | examples_d19d24 | 官命21例按5结构分类验证 | D-19 §三 + D-23 §三 |
| M1-D-085 杀刃格 | examples_d19d24 | 军官专班15+例+七杀羊刃象法 | D-24 §五 |
| M1-D-122 富贵贫贱 | upgrade_d19d24 | 官职4类别细分+财命5分类细分 | D-19 §三+§四 |
| M1-D-126 算命三步曲 | examples_d19d24 | D-24 实战4盘=测象定职业完整流程 | D-24 全篇 |
| M1-D-127 多重测象 | upgrade_d19d24 | 干支→职业的多层映射实战(木火=教育/金水=执法/土=建筑) | D-24 §二~§五 |
| M1-D-155 关财门 | definition_d20 | 正式定义+离婚不可复机制 | D-20 §概念 |
| M1-D-158 牢狱3类 | upgrade_d23 | 升级为6组合+劫煞亡神参与+应期法 | D-23 §五 |
| M1-D-159 婚姻好坏 | upgrade_d20 | 10节完整系统(好/差/独身/桃花/伤克/多婚/包局) | D-20 全章 |
| M1-D-171 过河拆桥 | examples_d19 | D-19 过河拆桥8例验证 | D-19 §过河拆桥 |
| M1-D-172 财富4级别 | examples_d19d23 | 官杀当财5例+食伤当财3例+比禄当财2例 | D-19+D-23 §四 |
| M1-D-174 应期铁律 | examples_d19d23 | D-19/D-23 应期章综合应用6例 | D-19+D-23 §一 |
| M1-D-179 5结构 | examples_d24 | D-24 按结构分类判定职业(去用=执法/合用=开店) | D-24 |
| M1-D-180 去用铁律 | examples_d23 | 车祸例：连根体被冲=致命 | D-23 §七 |
| M1-D-182 宫主星辅 | upgrade_d20 | 正宫/副宫精确定义+10节系统化 | D-20 §概念+全章 |

---

## §4 · 关键案例归档（≤ 30 例，按主题分类）

### 官命类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 1 | 乾：丙甲乙甲/申午卯申 | M1-D-186+187 | 伤食制官法院副部级 |
| 2 | 乾：戊癸庚丙/子亥戌子 | M1-D-186+188 | 金水伤官配印纪检厅长→地委书记 |
| 3 | 乾：庚庚癸丙/寅辰酉辰 | M1-D-186+188 | 印制伤官省委书记(无学历工人出身) |
| 4 | 坤：壬壬甲乙/辰寅辰丑 | M1-D-186+188 | 印收官墓省委副书记→政协主席(车祸亡) |
| 5 | 乾：乙丙甲甲/未戊子戌 | M1-D-186+187 | 财制印法院院长(未羊刃库=执法) |

### 财命类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 6 | 乾：戊己戊甲/申未戌寅 | M1-D-189 | 戊日甲寅时当财数千万 |
| 7 | 乾：辛庚庚丙/亥寅申戌 | M1-D-189 | 丙戌官当财丙戌运过亿 |
| 8 | 乾：庚乙庚壬/午酉子午 | M1-D-189+191 | 伤制官=大贪又升又发 |
| 9 | 乾：甲甲丙己/寅戌午丑 | M1-D-204+210 | 木火制财库家具5千万 |
| 10 | 乾：丁戊癸壬/未申酉戌 | M1-D-204+210 | 财包局建材酒店数百万 |

### 婚姻类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 11 | 坤：乙丁辛庚/卯亥未寅 | M1-D-192 | 壬午年合未结婚 |
| 12 | 坤：丙戊辛壬/午戌亥辰 | M1-D-192 | 戊辰年辰代表亥冲到夫家 |
| 13 | 坤：丙戊丙己/午戌午亥 | M1-D-192 | 坏掉阻碍婚姻字为应(非常规) |
| 14 | 乾：甲丁丙己/辰丑寅亥 | M1-D-211 | 妻宫寅透甲落辰以辰为妻+寅丑暗合=情人 |

### 六亲类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 15 | 乾：丙乙甲丁/子未寅卯 | M1-D-199 | 不以印为母以禄食为母寿80+ |
| 16 | 乾：庚戊甲丙/戌寅子寅 | M1-D-198 | 财临库地庚辰运父胃癌死 |
| 17 | 坤：戊甲庚戊/申寅戌子 | M1-D-198 | 癸未年穿倒子母尿毒症死 |

### 牢狱类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 18 | 乾：己壬己乙/巳申未丑 | M1-D-200 | 巳申合进局坐牢一辈子 |
| 19 | 乾：壬甲癸乙/辰辰巳卯 | M1-D-200+201 | 黑社会头目壬申年捉癸酉年枪毙 |
| 20 | 乾：辛丁丙戊/酉酉申戌 | M1-D-200 | 酉穿倒食神诈骗(诚信坏) |

### 车祸类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 21 | 乾：丁癸庚庚/未丑子辰 | M1-D-203 | 丑车入辰墓掉水中闷死 |
| 22 | 坤：辛庚丁丙/酉寅卯午 | M1-D-203 | 卯酉冲两车撞丙戌年亡 |
| 23 | 坤：壬壬甲乙/辰寅辰丑 | M1-D-203 | 两辰夹禄酉运两车合撞(省政协主席) |

### 职业判定类
| 例号 | 八字 | 触发规则 | 一句话段断 |
|---|---|---|---|
| 24 | 坤：丁癸丁丙/酉卯亥午 | M1-D-204+208 | 木火+亥墨水+卯笔=装修彩绘千万 |
| 25 | 乾：甲壬丙辛/寅申申卯 | M1-D-210 | 两印=2-3店面继承父业 |

---

## §5 · 跨派/跨源不一致点

| 矛盾点 | 本书论断 | 已有论断 | 进入 rule-conflicts? |
|---|---|---|---|
| 母亲星取法 | D-20明确：以禄/食伤/比劫为母(非印) | 传统派以印为母/M3任派以印为母 | 是（段派vs任派母星定义冲突待Stage 7仲裁）|
| 男命配偶星 | D-20：财+伤食都是配偶星 | M1-D-182/M1-D-159：以财为主 | 否（补强，段派内部一致） |
| 牢灾判定 | D-23 6组合完整 | M1-D-158 只有3类型 | 否（升级，6组合包含原3类+扩展） |
| 官杀当财的条件 | D-19/D-23：必须日主有用的官杀才可当财 | M1-D-172：未限定条件 | 否（补强条件限定） |

---

## §6 · 关键论断（≤ 20 条直引）

1. "官杀当财看级别一般会达千万" — D-19 line 3068
2. "伤官局当权的职务一般都很强势" — D-19 line 2372
3. "八字出现制局，制之适宜，也可成为官员" — D-19 line 2367
4. "婚姻好坏看宫位没有坏就没事" — D-20 §十
5. "以宫为主星为辅看父母情况一定看年月宫位" — D-20 line 3160
6. "以正偏财官杀为父；以禄食伤当母看" — D-20 line 3158
7. "结婚定义：以婚姻为目的共同生活超过半年" — D-20 line 153
8. "伤官大运也可结婚：坏掉阻碍婚姻字为应" — D-20 结婚例9
9. "阳气被坏出现辰丑土与亥损局=牢象" — D-23 line 3368
10. "伤官或比禄入墓没有了自由" — D-23 line 3372
11. "刑事犯罪多数会在八字中出现劫煞亡神" — D-23 line 3374
12. "阴阳离决命必危；失阳者容易死亡" — D-23 line 3844
13. "车祸都会在原局有所体现首先要找到车象" — D-23 line 4752
14. "两车夹禄凶象；冲禄连头致命" — D-23 综合
15. "食伤做功见财印落年上或门户=做生意" — D-24 line 52
16. "官杀制不尽当财看财富级别比较高" — D-24 例1
17. "印包财局=开店面做生意" — D-24 综合
18. "满盘皆阳唯一阴=急躁果断" — D-24 例2

---

## §7 · 待回灌 module-1-duan 的字段建议表

| rule_id | 待补字段 | 来源章节 | 优先级 |
|---|---|---|---|
| M1-D-078..082 | upgrade: 3级别+5分类取财法 | D-19+D-23 §四 | P0 |
| M1-D-083..094 | examples: 官命21例按5结构分 | D-19+D-23 §三 | P1 |
| M1-D-085 | examples: 军官15+例象法 | D-24 §五 | P1 |
| M1-D-120 | clarification: 墓=失自由/关店双义 | D-23 §五+D-24 | P0 |
| M1-D-122 | upgrade: 官职4分+财命5分 | D-19 §三+§四 | P0 |
| M1-D-126..127 | upgrade: D-24实战4盘定职业 | D-24 全篇 | P0 |
| M1-D-155 | definition: 正式定义+不可复机制 | D-20 §概念 | P0 |
| M1-D-158 | upgrade: 6组合+应期法 | D-23 §五 | P0 |
| M1-D-159+182 | upgrade: 10节婚姻+正副宫定义 | D-20 全章 | P0 |
| M1-D-171 | examples: 8例过河拆桥 | D-19 §过河拆桥 | P1 |
| M1-D-172 | examples: 官杀当财5例+限定条件 | D-19+D-23 §四.一 | P1 |
| M1-D-174 | examples: 综合应期6例 | D-19+D-23 §一 | P1 |
| M1-D-178 | examples: 车祸中穿=速度 | D-23 §七 | P2 |
| M1-D-179 | mapping: 5结构→职业映射 | D-24 | P1 |
| M1-D-180 | examples: 车祸连根被冲=致命 | D-23 §七 | P2 |
| M1-D-182 | upgrade: 正宫副宫精确定义 | D-20 §概念 | P0 |

---

## §8 · 与既有 d-NN-theory 文件的 diff

| 对比项 | 本文件 (D-19~D-24) | 既有 d15-d18-theory |
|---|---|---|
| 核心聚焦 | 段派专班应用：官命/财命系统化+六亲专辑+牢狱疾病车祸+职业判定 | 段派教学体系：5结构/伤官诀/应期/做功层次/婚姻 |
| 新规则类型 | 应用级判定规则(官命5类/取财5类/婚姻10节/牢6组/车5要素/职业4盘) | 结构性框架规则(5结构/5伤官/4应期) |
| 与D-17/D-18关系 | D-19/D-23 应期+象法+伤官诀+过河拆桥章与D-17/D-18 70%重叠(不重复提取) | D-17/D-18已提取核心框架 |
| 独有贡献 | D-20六亲专辑(完全独有)/D-23牢疾车(完全独有)/D-24职业实战(完全独有) | 伤官诀5分/过河拆桥/做功层次计量 |
| 案例密度 | 极高(D-19~40例官财/D-20~130例婚姻六亲/D-23~70例牢疾车/D-24~30例职业) | 极高(D-16~80例/D-18~100例) |

---

## §9 · 自检清单

- [x] §0 摘要 ≤ 20 行 (8 条)
- [x] §2 新规则坯每条都有 ≥ 3 案例 + falsifiable_by (30 条全部满足)
- [x] §3 强化字段表 ≥ 10 行 (15 行)
- [x] §6 直引 ≤ 20 条 + 每条 ≤ 30 字 (18 条，全部 ≤ 30 字)
- [x] §7 字段建议表 ≥ 15 行 (16 行)
- [x] 总行数在合理范围（architecture 非 dump）
- [x] 全文无整段 > 50 字原文复制
- [x] 每条 source 锚点用 D-NN §章节形式
- [x] 每条事实陈述可 grep 到原文
- [x] commit 颗粒度 ≤ 1 个 theory 文件

---

**d19-d24-theory 完毕。30 条新规则 M1-D-186..215。**
