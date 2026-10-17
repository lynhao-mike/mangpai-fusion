---
batch: gao-fix-b01
school: gao
scope: 高派 261 条候选的锚点审计 · 修正批（30 条）
audit_method: 规则文本与 sources/gao 原稿逐行最长公共子串（LCS）；仅收录 LCS>=7 且可精确回读的条目
date: 2026-10-17
record_count: 36
note: |
  原 index.yaml 的 raw_anchor 为「第X课 §Y（"…"）」节号描述，不可按行回读。
  本批将 30 条改为原稿真实行号锚点（raw_file 指向 sources/gao 原稿），
  statement 为提取稿归纳文本（非原文摘录），verify_fragment 为原稿该行精确子串。
  legacy_anchor 保留原节号锚点以便对照。
---

# 高派锚点修正 · b01（30 条）

```yaml
- id: G-MG-005
  school: gao
  classic_name: 高德臣盲派
  title: 命宫与八字关系12条
  domain: mingong
  topic: mingong
  tags:
  - 命宫与八字关系12条
  - MG
  - 锚点修正
  statement: 命宫与八字关系12条：①命宫旺衰以月令为标准②命宫可补四柱不足③命宫与日/年支犯刑冲=贫贱短寿④命宫地支被月支冲克=一举成名⑤命宫地支为日干财星=财源旺盛⑥命宫地支与月支同=果断智能⑦命宫与年柱天合地合=补救婚姻⑧命宫刑冲克穿日柱=夫妻缘差⑨命宫宜生旺忌衰败⑩命宫子午卯酉=多情⑪命宫寅申巳亥=血光⑫命宫辰戌丑未=多变
  conclusion: 命宫与八字关系12条：①命宫旺衰以月令为标准②命宫可补四柱不足③命宫与日/年支犯刑冲=贫贱短寿④命宫地支被月支冲克=一举成名⑤命宫地支为日干财星=财源旺盛⑥命宫地支与月支同=果断智能⑦命宫与年柱天合地合=补救婚姻⑧命宫刑冲克穿日柱=夫妻缘差⑨命宫宜生旺忌衰败⑩命宫子午卯酉=多情⑪命宫寅申巳亥=血光⑫命宫辰戌丑未=多变
  content_status: full
  full_statement: 命宫与八字关系12条：①命宫旺衰以月令为标准②命宫可补四柱不足③命宫与日/年支犯刑冲=贫贱短寿④命宫地支被月支冲克=一举成名⑤命宫地支为日干财星=财源旺盛⑥命宫地支与月支同=果断智能⑦命宫与年柱天合地合=补救婚姻⑧命宫刑冲克穿日柱=夫妻缘差⑨命宫宜生旺忌衰败⑩命宫子午卯酉=多情⑪命宫寅申巳亥=血光⑫命宫辰戌丑未=多变
  raw_file: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
  raw_anchor: line:226
  source_ref:
    path: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
    anchor: line:226
  verify_fragment: 命宫旺衰以月令为标准
  legacy_anchor: 第 2 课 §三（三）（"命宫与八字的关系…1-12条"）
  anchor_confidence: high
- id: G-MG-012
  school: gao
  classic_name: 高德臣盲派
  title: 月限推步法
  domain: mingong
  topic: mingong
  tags:
  - 月限推步法
  - MG
  - 锚点修正
  statement: 月限推步法：以流年小限地支起正月→逆推各月→五虎遁配天干=月限干支；月限反吟(流月与月限天克地冲)/月限同途(相同)=有变；流月主季节状态=前提，月限吉凶程度取决于该月五行状态
  conclusion: 月限推步法：以流年小限地支起正月→逆推各月→五虎遁配天干=月限干支；月限反吟(流月与月限天克地冲)/月限同途(相同)=有变；流月主季节状态=前提，月限吉凶程度取决于该月五行状态
  content_status: full
  full_statement: 月限推步法：以流年小限地支起正月→逆推各月→五虎遁配天干=月限干支；月限反吟(流月与月限天克地冲)/月限同途(相同)=有变；流月主季节状态=前提，月限吉凶程度取决于该月五行状态
  raw_file: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
  raw_anchor: line:548
  source_ref:
    path: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
    anchor: line:548
  verify_fragment: 以流年小限地支起正月
  legacy_anchor: 第 4 课 §如何推月限（"以流年小限为坐标…流月顺排, 月限逆排, 12建星顺排"）
  anchor_confidence: high
- id: G-MG-020
  school: gao
  classic_name: 高德臣盲派
  title: ⚠禄马同槽与马倒禄斜判定铁律
  domain: mingong
  topic: mingong
  tags:
  - ⚠禄马同槽与马倒禄斜判定
  - MG
  - 锚点修正
  statement: ⚠禄马同槽与马倒禄斜判定铁律：禄马同槽=日干起禄与时干起马查到地支与天干相同；禄马天克地冲=马倒禄斜；禄马支到长生地不论男女命归天；马交冠带衰病口/禄交墓上死病缠
  conclusion: ⚠禄马同槽与马倒禄斜判定铁律：禄马同槽=日干起禄与时干起马查到地支与天干相同；禄马天克地冲=马倒禄斜；禄马支到长生地不论男女命归天；马交冠带衰病口/禄交墓上死病缠
  content_status: full
  full_statement: ⚠禄马同槽与马倒禄斜判定铁律：禄马同槽=日干起禄与时干起马查到地支与天干相同；禄马天克地冲=马倒禄斜；禄马支到长生地不论男女命归天；马交冠带衰病口/禄交墓上死病缠
  raw_file: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
  raw_anchor: line:940
  source_ref:
    path: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
    anchor: line:940
  verify_fragment: 日干起禄与时干起马
  legacy_anchor: 第 13 课 §五（"禄马同槽就是日干起禄与时干起马…天克地冲则是马倒禄斜"）
  anchor_confidence: high
- id: G-MG-024
  school: gao
  classic_name: 高德臣盲派
  title: 择日六大禁忌铁律
  domain: mingong
  topic: mingong
  tags:
  - 择日六大禁忌铁律
  - MG
  - 锚点修正
  statement: 择日六大禁忌铁律：①红砂大煞（四孟月金鸡四仲蛇四季丑）②十恶大败日（十干无禄日）③杨公忌日（正月十三/二月初一…共13日）④日时不可三煞年命⑤岁破月破日⑥日时不可冲事主年命+四绝日/四离日
  conclusion: 择日六大禁忌铁律：①红砂大煞（四孟月金鸡四仲蛇四季丑）②十恶大败日（十干无禄日）③杨公忌日（正月十三/二月初一…共13日）④日时不可三煞年命⑤岁破月破日⑥日时不可冲事主年命+四绝日/四离日
  content_status: full
  full_statement: 择日六大禁忌铁律：①红砂大煞（四孟月金鸡四仲蛇四季丑）②十恶大败日（十干无禄日）③杨公忌日（正月十三/二月初一…共13日）④日时不可三煞年命⑤岁破月破日⑥日时不可冲事主年命+四绝日/四离日
  raw_file: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
  raw_anchor: line:1376
  source_ref:
    path: sources/gao/2018弟子班_命宫长生诀择日篇_78页.md
    anchor: line:1376
  verify_fragment: 日时不可三煞年命
  legacy_anchor: 第 16 课 §1-10（"择日的主要禁忌…破碎煞…十恶大败日…杨公忌日…"）
  anchor_confidence: medium
- id: G-DY-002
  school: gao
  classic_name: 高德臣盲派
  title: 岁运进入命局顺序铁律
  domain: dayun
  topic: dayun
  tags:
  - 岁运进入命局顺序铁律
  - DY
  - 锚点修正
  statement: 岁运进入命局顺序铁律：流年→大运→命局（通过作用大运进入）；流年亦可越过大运直接进入命局；先后顺序=合冲为先，刑害次之，生克又次之
  conclusion: 岁运进入命局顺序铁律：流年→大运→命局（通过作用大运进入）；流年亦可越过大运直接进入命局；先后顺序=合冲为先，刑害次之，生克又次之
  content_status: full
  full_statement: 岁运进入命局顺序铁律：流年→大运→命局（通过作用大运进入）；流年亦可越过大运直接进入命局；先后顺序=合冲为先，刑害次之，生克又次之
  raw_file: sources/gao/2018弟子班_大运流年篇_55页.md
  raw_anchor: line:55
  source_ref:
    path: sources/gao/2018弟子班_大运流年篇_55页.md
    anchor: line:55
  verify_fragment: 合冲为先，刑害次之，生克又次之
  legacy_anchor: 第 1 课 §5（"岁运进入命局的顺序…以合冲为先"）
  anchor_confidence: high
- id: G-DY-001
  school: gao
  classic_name: 高德臣盲派
  title: 发动五法铁律
  domain: dayun
  topic: dayun
  tags:
  - 发动五法铁律
  - DY
  - 锚点修正
  statement: 发动五法铁律：岁运通过合、冲、刑、害、值五种方式介入命局，无此五种关系则不发动，不发动则无生克权
  conclusion: 发动五法铁律：岁运通过合、冲、刑、害、值五种方式介入命局，无此五种关系则不发动，不发动则无生克权
  content_status: full
  full_statement: 发动五法铁律：岁运通过合、冲、刑、害、值五种方式介入命局，无此五种关系则不发动，不发动则无生克权
  raw_file: sources/gao/2018弟子班_大运流年篇_55页.md
  raw_anchor: line:45
  source_ref:
    path: sources/gao/2018弟子班_大运流年篇_55页.md
    anchor: line:45
  verify_fragment: 通过合、冲、刑、害、值
  legacy_anchor: 第 1 课 §4（"命、运、岁只有存在这五种关系才为发动"）
  anchor_confidence: high
- id: G-DY-009
  school: gao
  classic_name: 高德臣盲派
  title: 突然失衡加灾铁律
  domain: dayun
  topic: dayun
  tags:
  - 突然失衡加灾铁律
  - DY
  - 锚点修正
  statement: 突然失衡加灾铁律：某步大运让命局突然失衡（身弱突然身旺/身旺突然身弱），吉运乐极生悲，凶运加大凶灾
  conclusion: 突然失衡加灾铁律：某步大运让命局突然失衡（身弱突然身旺/身旺突然身弱），吉运乐极生悲，凶运加大凶灾
  content_status: full
  full_statement: 突然失衡加灾铁律：某步大运让命局突然失衡（身弱突然身旺/身旺突然身弱），吉运乐极生悲，凶运加大凶灾
  raw_file: sources/gao/2018弟子班_大运流年篇_55页.md
  raw_anchor: line:145
  source_ref:
    path: sources/gao/2018弟子班_大运流年篇_55页.md
    anchor: line:145
  verify_fragment: 步大运让命局突然失衡（
  legacy_anchor: 第 2 课（五）
  anchor_confidence: high
- id: G-DY-003
  school: gao
  classic_name: 高德臣盲派
  title: 大运地支为重铁律
  domain: dayun
  topic: dayun
  tags:
  - 大运地支为重铁律
  - DY
  - 锚点修正
  statement: 大运地支为重铁律：运支力量决定运干力量，决定吉凶大方向；运支对运干起损益作用（甲申运甲被截脚/甲寅运甲得禄）
  conclusion: 大运地支为重铁律：运支力量决定运干力量，决定吉凶大方向；运支对运干起损益作用（甲申运甲被截脚/甲寅运甲得禄）
  content_status: full
  full_statement: 大运地支为重铁律：运支力量决定运干力量，决定吉凶大方向；运支对运干起损益作用（甲申运甲被截脚/甲寅运甲得禄）
  raw_file: sources/gao/2018弟子班_大运流年篇_55页.md
  raw_anchor: line:67
  source_ref:
    path: sources/gao/2018弟子班_大运流年篇_55页.md
    anchor: line:67
  verify_fragment: 运支对运干起损益作用
  legacy_anchor: 第 1 课 §6（"大运以方位而论…运支的力量决定运干的力量"）
  anchor_confidence: high
- id: G-LF-023
  school: gao
  classic_name: 高德臣盲派
  title: 寒暖转化铁律
  domain: lifa
  topic: lifa
  tags:
  - 寒暖转化铁律
  - LF
  - 锚点修正
  statement: 寒暖转化铁律（《滴天髓》引用）："寒虽甚，要暖有气，暖虽至，要寒有根，则能生成万物。若寒甚而暖无气，暖至而寒无根，必无生成之妙也"——阴极则阳生，阳极则阴生
  conclusion: 寒暖转化铁律（《滴天髓》引用）："寒虽甚，要暖有气，暖虽至，要寒有根，则能生成万物。若寒甚而暖无气，暖至而寒无根，必无生成之妙也"——阴极则阳生，阳极则阴生
  content_status: full
  full_statement: 寒暖转化铁律（《滴天髓》引用）："寒虽甚，要暖有气，暖虽至，要寒有根，则能生成万物。若寒甚而暖无气，暖至而寒无根，必无生成之妙也"——阴极则阳生，阳极则阴生
  raw_file: sources/gao/2018弟子班_理法篇_31页.md
  raw_anchor: line:425
  source_ref:
    path: sources/gao/2018弟子班_理法篇_31页.md
    anchor: line:425
  verify_fragment: 寒虽甚，要暖有气，暖虽至，要寒有根，则能生成万物。若寒甚而暖无气，暖至而寒无根，必无生成之妙也
  legacy_anchor: 第 5 课 §2 第 3 段
  anchor_confidence: high
- id: G-LF-013
  school: gao
  classic_name: 高德臣盲派
  title: 论命心法16字诀
  domain: lifa
  topic: lifa
  tags:
  - 论命心法16字诀
  - LF
  - 锚点修正
  statement: 论命心法16字诀（铁律级）：<br>"四柱生成，先定体用，同根同旬，日时我宫；<br>干查根源，支找去处，人生追求，财官印禄；<br>有得有失，方法思路，天地君臣，配合适度；<br>内外感应，天地有情，我为他用，为人打工；<br>明看五行，暗推长生，神煞空亡，参考应用。"
  conclusion: 论命心法16字诀（铁律级）：<br>"四柱生成，先定体用，同根同旬，日时我宫；<br>干查根源，支找去处，人生追求，财官印禄；<br>有得有失，方法思路，天地君臣，配合适度；<br>内外感应，天地有情，我为他用，为人打工；<br>明看五行，暗推长生，神煞空亡，参考应用。"
  content_status: full
  full_statement: 论命心法16字诀（铁律级）：<br>"四柱生成，先定体用，同根同旬，日时我宫；<br>干查根源，支找去处，人生追求，财官印禄；<br>有得有失，方法思路，天地君臣，配合适度；<br>内外感应，天地有情，我为他用，为人打工；<br>明看五行，暗推长生，神煞空亡，参考应用。"
  raw_file: sources/gao/2018弟子班_理法篇_31页.md
  raw_anchor: line:189
  source_ref:
    path: sources/gao/2018弟子班_理法篇_31页.md
    anchor: line:189
  verify_fragment: 明看五行，暗推长生，神煞空亡，参考应用。
  legacy_anchor: 第 3 课 §3（"八字论命心法"完整 32 字版）
  anchor_confidence: high
- id: G-LF-015
  school: gao
  classic_name: 高德臣盲派
  title: 三点一线两项定一项
  domain: lifa
  topic: lifa
  tags:
  - 三点一线两项定一项
  - LF
  - 锚点修正
  statement: 三点一线两项定一项：盲派断命铁律——同一结论必须从不同角度、用不同方法都证明一件事，才可以铁口直断
  conclusion: 三点一线两项定一项：盲派断命铁律——同一结论必须从不同角度、用不同方法都证明一件事，才可以铁口直断
  content_status: full
  full_statement: 三点一线两项定一项：盲派断命铁律——同一结论必须从不同角度、用不同方法都证明一件事，才可以铁口直断
  raw_file: sources/gao/2018弟子班_理法篇_31页.md
  raw_anchor: line:211
  source_ref:
    path: sources/gao/2018弟子班_理法篇_31页.md
    anchor: line:211
  verify_fragment: 方法都证明一件事，才可以铁口直断
  legacy_anchor: 第 3 课 §3（"明看五行，暗推长生…盲派讲究三点一线，两项定一项"）
  anchor_confidence: high
- id: G-LF-003
  school: gao
  classic_name: 高德臣盲派
  title: 黄大陆三论
  domain: lifa
  topic: lifa
  tags:
  - 黄大陆三论
  - LF
  - 锚点修正
  statement: 黄大陆三论：①月令=父母宫=先天遗传信息②看命先看父母给你遗传了什么③看你家里有什么东西可以为你所用
  conclusion: 黄大陆三论：①月令=父母宫=先天遗传信息②看命先看父母给你遗传了什么③看你家里有什么东西可以为你所用
  content_status: full
  full_statement: 黄大陆三论：①月令=父母宫=先天遗传信息②看命先看父母给你遗传了什么③看你家里有什么东西可以为你所用
  raw_file: sources/gao/2018弟子班_理法篇_31页.md
  raw_anchor: line:27
  source_ref:
    path: sources/gao/2018弟子班_理法篇_31页.md
    anchor: line:27
  verify_fragment: 看你家里有什么东西可以为你所用
  legacy_anchor: 第 1 课 §1（"为什么要从月令取用神呢…父母宫带有先天遗传信息"）
  anchor_confidence: high
- id: G-BD-024
  school: gao
  classic_name: 高德臣盲派
  title: 串宫三种起太岁用法
  domain: shensha
  topic: shensha
  tags:
  - 串宫三种起太岁用法
  - BD
  - 锚点修正
  statement: 串宫三种起太岁用法：①流年地支起太岁看一年；②大运地支起太岁看十年；③日干通地支起太岁看一生祸福
  conclusion: 串宫三种起太岁用法：①流年地支起太岁看一年；②大运地支起太岁看十年；③日干通地支起太岁看一生祸福
  content_status: full
  full_statement: 串宫三种起太岁用法：①流年地支起太岁看一年；②大运地支起太岁看十年；③日干通地支起太岁看一生祸福
  raw_file: sources/gao/盲派神煞应用宝典.md
  raw_anchor: line:2706
  source_ref:
    path: sources/gao/盲派神煞应用宝典.md
    anchor: line:2706
  verify_fragment: 日干通地支起太岁看一生祸福
  legacy_anchor: 第 9 课 §二（"(一)流年起太岁用法…(二)大运起太岁用法…(三)日主起太岁用法"）
  anchor_confidence: high
- id: G-BD-018
  school: gao
  classic_name: 高德臣盲派
  title: 孤辰寡宿用于命宫而非四柱
  domain: shensha
  topic: shensha
  tags:
  - 孤辰寡宿用于命宫而非四柱
  - BD
  - 锚点修正
  statement: 孤辰寡宿用于命宫而非四柱：命宫见孤辰寡宿=感情难归/孤独；但须区分真假(申年生人忌未不忌亥)
  conclusion: 孤辰寡宿用于命宫而非四柱：命宫见孤辰寡宿=感情难归/孤独；但须区分真假(申年生人忌未不忌亥)
  content_status: full
  full_statement: 孤辰寡宿用于命宫而非四柱：命宫见孤辰寡宿=感情难归/孤独；但须区分真假(申年生人忌未不忌亥)
  raw_file: sources/gao/盲派神煞应用宝典.md
  raw_anchor: line:961
  source_ref:
    path: sources/gao/盲派神煞应用宝典.md
    anchor: line:961
  verify_fragment: 申年生人忌未不忌亥
  legacy_anchor: 第 4 课 §四·孤辰寡宿（"我习惯的用法是用于命宫…命宫见孤辰寡宿就是感情难归"）
  anchor_confidence: high
- id: G-BD-019
  school: gao
  classic_name: 高德臣盲派
  title: 串宫压运12神体系
  domain: shensha
  topic: shensha
  tags:
  - 串宫压运12神体系
  - BD
  - 锚点修正
  statement: 串宫压运12神体系：太岁(中)/青龙(吉)/丧门(小凶)/六合(吉)/官符(中)/小耗(小凶)/大耗(大凶)/朱雀(大凶)/白虎(大凶)/贵神(吉)/吊客(小凶)/病符(小凶)；以流年地支起太岁
  conclusion: 串宫压运12神体系：太岁(中)/青龙(吉)/丧门(小凶)/六合(吉)/官符(中)/小耗(小凶)/大耗(大凶)/朱雀(大凶)/白虎(大凶)/贵神(吉)/吊客(小凶)/病符(小凶)；以流年地支起太岁
  content_status: full
  full_statement: 串宫压运12神体系：太岁(中)/青龙(吉)/丧门(小凶)/六合(吉)/官符(中)/小耗(小凶)/大耗(大凶)/朱雀(大凶)/白虎(大凶)/贵神(吉)/吊客(小凶)/病符(小凶)；以流年地支起太岁
  raw_file: sources/gao/盲派神煞应用宝典.md
  raw_anchor: line:2737
  source_ref:
    path: sources/gao/盲派神煞应用宝典.md
    anchor: line:2737
  verify_fragment: 以流年地支起太岁
  legacy_anchor: 第 9 课 §一·(二)(四)（"串宫总序：1太岁、2青龙、3丧门…十二神详诀"）
  anchor_confidence: medium
- id: G-BD-002
  school: gao
  classic_name: 高德臣盲派
  title: 天乙贵人阴阳贵辨别法
  domain: shensha
  topic: shensha
  tags:
  - 天乙贵人阴阳贵辨别法
  - BD
  - 锚点修正
  statement: 天乙贵人阴阳贵辨别法：日元地支属阴者以阳贵人为真，属阳者以阴贵人为真；地支阴阳非子阳丑阴，乃卯辰巳午未申为阳、酉戌亥子丑寅为阴
  conclusion: 天乙贵人阴阳贵辨别法：日元地支属阴者以阳贵人为真，属阳者以阴贵人为真；地支阴阳非子阳丑阴，乃卯辰巳午未申为阳、酉戌亥子丑寅为阴
  content_status: full
  full_statement: 天乙贵人阴阳贵辨别法：日元地支属阴者以阳贵人为真，属阳者以阴贵人为真；地支阴阳非子阳丑阴，乃卯辰巳午未申为阳、酉戌亥子丑寅为阴
  raw_file: sources/gao/盲派神煞应用宝典.md
  raw_anchor: line:296
  source_ref:
    path: sources/gao/盲派神煞应用宝典.md
    anchor: line:296
  verify_fragment: 酉戌亥子丑寅为阴
  legacy_anchor: 第 2 课 §天乙贵人 补充（"首先要看日元地支阴阳…命宫节所论卯辰巳午未申为阳"）
  anchor_confidence: medium
- id: G-SS-005
  school: gao
  classic_name: 高德臣盲派
  title: 天月二德长寿之星
  domain: shensha
  topic: shensha
  tags:
  - 天月二德长寿之星
  - SS
  - 锚点修正
  statement: 天月二德长寿之星（《玉照定真经》引）："卦逢生气，天德合，世世长年"——命主可高寿，后人也延年
  conclusion: 天月二德长寿之星（《玉照定真经》引）："卦逢生气，天德合，世世长年"——命主可高寿，后人也延年
  content_status: full
  full_statement: 天月二德长寿之星（《玉照定真经》引）："卦逢生气，天德合，世世长年"——命主可高寿，后人也延年
  raw_file: sources/gao/2018弟子班_神煞篇_34页.md
  raw_anchor: line:107
  source_ref:
    path: sources/gao/2018弟子班_神煞篇_34页.md
    anchor: line:107
  verify_fragment: 卦逢生气，天德合，世世长年
  legacy_anchor: 第 2 课 §二第 4 条
  anchor_confidence: high
- id: G-SS-015
  school: gao
  classic_name: 高德臣盲派
  title: 飞刃倒戈铁律
  domain: shensha
  topic: shensha
  tags:
  - 飞刃倒戈铁律
  - SS
  - 锚点修正
  statement: 飞刃倒戈铁律：冲羊刃的字=飞刃；"羊刃更兼倒戈，必作无头之鬼"；别柱羊刃冲刑日支=羊刃倒戈→凶
  conclusion: 飞刃倒戈铁律：冲羊刃的字=飞刃；"羊刃更兼倒戈，必作无头之鬼"；别柱羊刃冲刑日支=羊刃倒戈→凶
  content_status: full
  full_statement: 飞刃倒戈铁律：冲羊刃的字=飞刃；"羊刃更兼倒戈，必作无头之鬼"；别柱羊刃冲刑日支=羊刃倒戈→凶
  raw_file: sources/gao/2018弟子班_神煞篇_34页.md
  raw_anchor: line:402
  source_ref:
    path: sources/gao/2018弟子班_神煞篇_34页.md
    anchor: line:402
  verify_fragment: 羊刃更兼倒戈，必作无头之鬼
  legacy_anchor: 第 6 课 §三
  anchor_confidence: high
- id: G-SS-003
  school: gao
  classic_name: 高德臣盲派
  title: 昼夜分阳贵阴贵
  domain: shensha
  topic: shensha
  tags:
  - 昼夜分阳贵阴贵
  - SS
  - 锚点修正
  statement: 昼夜分阳贵阴贵：白天生用阳贵人，夜生用阴贵人——干=丁，昼用亥（猪）/夜用酉（鸡）
  conclusion: 昼夜分阳贵阴贵：白天生用阳贵人，夜生用阴贵人——干=丁，昼用亥（猪）/夜用酉（鸡）
  content_status: full
  full_statement: 昼夜分阳贵阴贵：白天生用阳贵人，夜生用阴贵人——干=丁，昼用亥（猪）/夜用酉（鸡）
  raw_file: sources/gao/2018弟子班_神煞篇_34页.md
  raw_anchor: line:19
  source_ref:
    path: sources/gao/2018弟子班_神煞篇_34页.md
    anchor: line:19
  verify_fragment: 生用阳贵人，夜生用阴贵人
  legacy_anchor: 第 1 课 §二（"择吉使用贵人有两种说法"）
  anchor_confidence: high
- id: G-SS-016
  school: gao
  classic_name: 高德臣盲派
  title: 冲天煞=干支伏吟
  domain: shensha
  topic: shensha
  tags:
  - 冲天煞=干支伏吟
  - SS
  - 锚点修正
  statement: 冲天煞=干支伏吟：年干支与月干支相同/日干支与时干支相同→短命可能；干支天克地冲（甲子见庚午）→返吟→"返吟伏吟，哭泣淋淋"
  conclusion: 冲天煞=干支伏吟：年干支与月干支相同/日干支与时干支相同→短命可能；干支天克地冲（甲子见庚午）→返吟→"返吟伏吟，哭泣淋淋"
  content_status: full
  full_statement: 冲天煞=干支伏吟：年干支与月干支相同/日干支与时干支相同→短命可能；干支天克地冲（甲子见庚午）→返吟→"返吟伏吟，哭泣淋淋"
  raw_file: sources/gao/2018弟子班_神煞篇_34页.md
  raw_anchor: line:566
  source_ref:
    path: sources/gao/2018弟子班_神煞篇_34页.md
    anchor: line:566
  verify_fragment: 年干支与月干支相同
  legacy_anchor: 第 9 课 §二
  anchor_confidence: high
- id: G-XF-021
  school: gao
  classic_name: 高德臣盲派
  title: 辰戌丑未四库取像+库归属铁律
  domain: xiangfa
  topic: xiangfa
  tags:
  - 辰戌丑未四库取像+库归属
  - XF
  - 锚点修正
  statement: 辰戌丑未四库取像+库归属铁律：辰=木库/水墓；未=火库/木墓；戌=金库/火墓；丑=水库/金墓；古书引『杂气财官刑冲则发』『辰戌丑未遇刑冲无人不发』；额外口诀：丑寅好学医/丑卯不相逢/辰巳坐地网/辰午官煞重药石连床/辰未自带印华盖星坐命
  conclusion: 辰戌丑未四库取像+库归属铁律：辰=木库/水墓；未=火库/木墓；戌=金库/火墓；丑=水库/金墓；古书引『杂气财官刑冲则发』『辰戌丑未遇刑冲无人不发』；额外口诀：丑寅好学医/丑卯不相逢/辰巳坐地网/辰午官煞重药石连床/辰未自带印华盖星坐命
  content_status: full
  full_statement: 辰戌丑未四库取像+库归属铁律：辰=木库/水墓；未=火库/木墓；戌=金库/火墓；丑=水库/金墓；古书引『杂气财官刑冲则发』『辰戌丑未遇刑冲无人不发』；额外口诀：丑寅好学医/丑卯不相逢/辰巳坐地网/辰午官煞重药石连床/辰未自带印华盖星坐命
  raw_file: sources/gao/2018弟子班_象法篇_83页.md
  raw_anchor: line:1245
  source_ref:
    path: sources/gao/2018弟子班_象法篇_83页.md
    anchor: line:1245
  verify_fragment: 辰未自带印 华盖星坐命
  legacy_anchor: 第 14 课 §一-§五（库归属表 + 古书引 + 5 条口诀）
  anchor_confidence: high
- id: G-XF-009
  school: gao
  classic_name: 高德臣盲派
  title: 暗合三种形式=见不得光的关系
  domain: xiangfa
  topic: xiangfa
  tags:
  - 暗合三种形式=见不得光的
  - XF
  - 锚点修正
  statement: 暗合三种形式=见不得光的关系：①通合（如午亥暗合=丁壬暗合）②通禄合（如寅丑暗合=甲己暗合）③天干与地支通禄合（如丁亥=丁壬合）——暗合主『私情/隐瞒/见不得光的连结』
  conclusion: 暗合三种形式=见不得光的关系：①通合（如午亥暗合=丁壬暗合）②通禄合（如寅丑暗合=甲己暗合）③天干与地支通禄合（如丁亥=丁壬合）——暗合主『私情/隐瞒/见不得光的连结』
  content_status: full
  full_statement: 暗合三种形式=见不得光的关系：①通合（如午亥暗合=丁壬暗合）②通禄合（如寅丑暗合=甲己暗合）③天干与地支通禄合（如丁亥=丁壬合）——暗合主『私情/隐瞒/见不得光的连结』
  raw_file: sources/gao/2018弟子班_象法篇_83页.md
  raw_anchor: line:341
  source_ref:
    path: sources/gao/2018弟子班_象法篇_83页.md
    anchor: line:341
  verify_fragment: 天干与地支通禄合
  legacy_anchor: 第 4 课 §四（"暗合 = 见不得光"）
  anchor_confidence: medium
- id: G-XF-012
  school: gao
  classic_name: 高德臣盲派
  title: 三刑+自刑取像
  domain: xiangfa
  topic: xiangfa
  tags:
  - 三刑+自刑取像
  - XF
  - 锚点修正
  statement: 三刑+自刑取像：寅巳申/丑戌未三刑全=责难损坏；子卯刑=无礼之刑；辰辰/酉酉/午午/亥亥四自刑=自损；丑戌未三刑见金多→六亲伤病
  conclusion: 三刑+自刑取像：寅巳申/丑戌未三刑全=责难损坏；子卯刑=无礼之刑；辰辰/酉酉/午午/亥亥四自刑=自损；丑戌未三刑见金多→六亲伤病
  content_status: full
  full_statement: 三刑+自刑取像：寅巳申/丑戌未三刑全=责难损坏；子卯刑=无礼之刑；辰辰/酉酉/午午/亥亥四自刑=自损；丑戌未三刑见金多→六亲伤病
  raw_file: sources/gao/2018弟子班_象法篇_83页.md
  raw_anchor: line:365
  source_ref:
    path: sources/gao/2018弟子班_象法篇_83页.md
    anchor: line:365
  verify_fragment: ；丑戌未三刑见金
  legacy_anchor: 第 5 课 §一（"三刑 / 子卯无礼之刑 / 自刑"）
  anchor_confidence: medium
- id: G-XF-006
  school: gao
  classic_name: 高德臣盲派
  title: 干支带象铁律+发表归根
  domain: xiangfa
  topic: xiangfa
  tags:
  - 干支带象铁律+发表归根
  - XF
  - 锚点修正
  statement: 干支带象铁律+发表归根：天干为头/地支为肢/干为表象支为内里；地支藏干透出到天干→干以支为根（实象）/不透出→浮象（不兑现）→"发表归根定体用"
  conclusion: 干支带象铁律+发表归根：天干为头/地支为肢/干为表象支为内里；地支藏干透出到天干→干以支为根（实象）/不透出→浮象（不兑现）→"发表归根定体用"
  content_status: full
  full_statement: 干支带象铁律+发表归根：天干为头/地支为肢/干为表象支为内里；地支藏干透出到天干→干以支为根（实象）/不透出→浮象（不兑现）→"发表归根定体用"
  raw_file: sources/gao/2018弟子班_象法篇_83页.md
  raw_anchor: line:233
  source_ref:
    path: sources/gao/2018弟子班_象法篇_83页.md
    anchor: line:233
  verify_fragment: 发表归根定体用
  legacy_anchor: 第 3 课 §1 + §2（"天干为头地支为肢…发表归根定体用"）
  anchor_confidence: medium
- id: G-CS-008
  school: gao
  classic_name: 高德臣盲派
  title: 无财看财三法
  domain: caiyun
  topic: caiyun
  tags:
  - 无财看财三法
  - CS
  - 锚点修正
  statement: 无财看财三法：①禄当财看(禄头财=偏财/体力求财辛苦)②食伤当财(靠智力/级别更大)③我宫派出工具所克制/控制的也是财(即使原局有财也不当财看)
  conclusion: 无财看财三法：①禄当财看(禄头财=偏财/体力求财辛苦)②食伤当财(靠智力/级别更大)③我宫派出工具所克制/控制的也是财(即使原局有财也不当财看)
  content_status: full
  full_statement: 无财看财三法：①禄当财看(禄头财=偏财/体力求财辛苦)②食伤当财(靠智力/级别更大)③我宫派出工具所克制/控制的也是财(即使原局有财也不当财看)
  raw_file: sources/gao/财运事业断法弟子提高班_105页.md
  raw_anchor: line:513
  source_ref:
    path: sources/gao/财运事业断法弟子提高班_105页.md
    anchor: line:513
  verify_fragment: 即使原局有财也不当财看
  legacy_anchor: 第 8 课 + 第 5 课 例 4（"局中不见财星…以年支巳禄当财…食伤当财看"）
  anchor_confidence: high
- id: G-CS-005
  school: gao
  classic_name: 高德臣盲派
  title: 我宫透出代表命主说话铁律
  domain: caiyun
  topic: caiyun
  tags:
  - 我宫透出代表命主说话铁律
  - CS
  - 锚点修正
  statement: 我宫透出代表命主说话铁律：我宫透到年月的字=命主派出的特使=可代表命主行使权力/获取财富的工具；我宫透出定义他宫=掌控他宫
  conclusion: 我宫透出代表命主说话铁律：我宫透到年月的字=命主派出的特使=可代表命主行使权力/获取财富的工具；我宫透出定义他宫=掌控他宫
  content_status: full
  full_statement: 我宫透出代表命主说话铁律：我宫透到年月的字=命主派出的特使=可代表命主行使权力/获取财富的工具；我宫透出定义他宫=掌控他宫
  raw_file: sources/gao/财运事业断法弟子提高班_105页.md
  raw_anchor: line:158
  source_ref:
    path: sources/gao/财运事业断法弟子提高班_105页.md
    anchor: line:158
  verify_fragment: 代表命主行使权力
  legacy_anchor: 第 3 课 例 1（"我宫透出去的东西可以代表命主说话…一个国家总统派出的特使"）
  anchor_confidence: medium
- id: G-CS-017
  school: gao
  classic_name: 高德臣盲派
  title: 风险求财四特征
  domain: caiyun
  topic: caiyun
  tags:
  - 风险求财四特征
  - CS
  - 锚点修正
  statement: 风险求财四特征：①劫财制财格②杀制比劫格③财旺身弱格④财星破印格；刃头财主风险之财/伤官生偏财适合风险投资
  conclusion: 风险求财四特征：①劫财制财格②杀制比劫格③财旺身弱格④财星破印格；刃头财主风险之财/伤官生偏财适合风险投资
  content_status: full
  full_statement: 风险求财四特征：①劫财制财格②杀制比劫格③财旺身弱格④财星破印格；刃头财主风险之财/伤官生偏财适合风险投资
  raw_file: sources/gao/财运事业断法弟子提高班_105页.md
  raw_anchor: line:841
  source_ref:
    path: sources/gao/财运事业断法弟子提高班_105页.md
    anchor: line:841
  verify_fragment: 刃头财主风险之财
  legacy_anchor: 第 14 课 §偏业求财（"具有以下几个特征…第一劫财制财格…"）
  anchor_confidence: medium
- id: G-CS-022
  school: gao
  classic_name: 高德臣盲派
  title: 限运用法总纲
  domain: caiyun
  topic: caiyun
  tags:
  - 限运用法总纲
  - CS
  - 锚点修正
  statement: 限运用法总纲：年柱管1-18/月柱管19-36/日柱管37-54/时柱管55-72；运限>大运(限吉运凶不简单凶/限凶运吉不简单吉)
  conclusion: 限运用法总纲：年柱管1-18/月柱管19-36/日柱管37-54/时柱管55-72；运限>大运(限吉运凶不简单凶/限凶运吉不简单吉)
  content_status: full
  full_statement: 限运用法总纲：年柱管1-18/月柱管19-36/日柱管37-54/时柱管55-72；运限>大运(限吉运凶不简单凶/限凶运吉不简单吉)
  raw_file: sources/gao/财运事业断法弟子提高班_105页.md
  raw_anchor: line:1336
  source_ref:
    path: sources/gao/财运事业断法弟子提高班_105页.md
    anchor: line:1336
  verify_fragment: 月柱管 19-36 岁运程
  legacy_anchor: 第 24 课（"运限是大于高于大运的…运限吉利即使大运凶也不可简单以凶看"）
  anchor_confidence: medium
- id: G-CY-012
  school: gao
  classic_name: 高德臣盲派
  title: 求财四模式铁律
  domain: caiyun
  topic: caiyun
  tags:
  - 求财四模式铁律
  - CY
  - 锚点修正
  statement: 求财四模式铁律：①单位求财=我宫与年月财官印有必然联系/强烈感应②商业求财=财与印关联/官杀与食伤配合/用财求财③技术求财=食伤与官印产生联系④体力求财=比劫禄与财官联系/官杀多而无制
  conclusion: 求财四模式铁律：①单位求财=我宫与年月财官印有必然联系/强烈感应②商业求财=财与印关联/官杀与食伤配合/用财求财③技术求财=食伤与官印产生联系④体力求财=比劫禄与财官联系/官杀多而无制
  content_status: full
  full_statement: 求财四模式铁律：①单位求财=我宫与年月财官印有必然联系/强烈感应②商业求财=财与印关联/官杀与食伤配合/用财求财③技术求财=食伤与官印产生联系④体力求财=比劫禄与财官联系/官杀多而无制
  raw_file: sources/gao/2018弟子班_财运篇_43页.md
  raw_anchor: line:519
  source_ref:
    path: sources/gao/2018弟子班_财运篇_43页.md
    anchor: line:519
  verify_fragment: 我宫与年月财官印有必然联系
  legacy_anchor: 第 6 课 §二（"第一种方式…第四种方式"4 段完整定义）
  anchor_confidence: high
- id: G-CY-006
  school: gao
  classic_name: 高德臣盲派
  title: 有财无财核心判定2步
  domain: caiyun
  topic: caiyun
  tags:
  - 有财无财核心判定2步
  - CY
  - 锚点修正
  statement: 有财无财核心判定2步：①他宫之财与我宫是否有联系（有联系才有可能从外面挣钱）②我宫透到年月的工具所获取并有办法获取的为大财
  conclusion: 有财无财核心判定2步：①他宫之财与我宫是否有联系（有联系才有可能从外面挣钱）②我宫透到年月的工具所获取并有办法获取的为大财
  content_status: full
  full_statement: 有财无财核心判定2步：①他宫之财与我宫是否有联系（有联系才有可能从外面挣钱）②我宫透到年月的工具所获取并有办法获取的为大财
  raw_file: sources/gao/2018弟子班_财运篇_43页.md
  raw_anchor: line:195
  source_ref:
    path: sources/gao/2018弟子班_财运篇_43页.md
    anchor: line:195
  verify_fragment: 他宫之财与我宫是否有联系
  legacy_anchor: 第 3 课 §二（"关键是看他宫之财与我宫是否有联系…我宫透到年月的工具"）
  anchor_confidence: high
- id: G-CY-004
  school: gao
  classic_name: 高德臣盲派
  title: 财气通门户三层铁律
  domain: caiyun
  topic: caiyun
  tags:
  - 财气通门户三层铁律
  - CY
  - 锚点修正
  statement: 财气通门户三层铁律：①财星与命主有必然联系（途径/渠道/办法）②财星组合与命主有情（非恶意，能为我所用）③财星旺相（值月令或受生有力→决定财大财小）
  conclusion: 财气通门户三层铁律：①财星与命主有必然联系（途径/渠道/办法）②财星组合与命主有情（非恶意，能为我所用）③财星旺相（值月令或受生有力→决定财大财小）
  content_status: full
  full_statement: 财气通门户三层铁律：①财星与命主有必然联系（途径/渠道/办法）②财星组合与命主有情（非恶意，能为我所用）③财星旺相（值月令或受生有力→决定财大财小）
  raw_file: sources/gao/2018弟子班_财运篇_43页.md
  raw_anchor: line:105
  source_ref:
    path: sources/gao/2018弟子班_财运篇_43页.md
    anchor: line:105
  verify_fragment: 财星组合与命主有情
  legacy_anchor: 第 2 课（"本人认为财气通门户有三层含义"完整三段）
  anchor_confidence: high
- id: G-CY-008
  school: gao
  classic_name: 高德臣盲派
  title: 发财应期6条铁律
  domain: caiyun
  topic: caiyun
  tags:
  - 发财应期6条铁律
  - CY
  - 锚点修正
  statement: 发财应期6条铁律：①原局有发财组合岁运引动为应期②原局有忌神岁运克制忌神为应期③求库财岁运开库/制库/伏吟库为应期④原局有基因岁运组合新格局为应期⑤求财工具透干得生扶为应期⑥岁运中财星主动送到我宫为应期
  conclusion: 发财应期6条铁律：①原局有发财组合岁运引动为应期②原局有忌神岁运克制忌神为应期③求库财岁运开库/制库/伏吟库为应期④原局有基因岁运组合新格局为应期⑤求财工具透干得生扶为应期⑥岁运中财星主动送到我宫为应期
  content_status: full
  full_statement: 发财应期6条铁律：①原局有发财组合岁运引动为应期②原局有忌神岁运克制忌神为应期③求库财岁运开库/制库/伏吟库为应期④原局有基因岁运组合新格局为应期⑤求财工具透干得生扶为应期⑥岁运中财星主动送到我宫为应期
  raw_file: sources/gao/2018弟子班_财运篇_43页.md
  raw_anchor: line:257
  source_ref:
    path: sources/gao/2018弟子班_财运篇_43页.md
    anchor: line:257
  verify_fragment: 财星主动送到我宫为
  legacy_anchor: 第 4 课 §经验总结 1~6 条
  anchor_confidence: high
- id: G-CH-035
  school: gao
  classic_name: 高德臣盲派
  title: 二奶命5种组合
  domain: hunyin
  topic: hunyin
  tags:
  - 二奶命5种组合
  - CH
  - 锚点修正
  statement: 二奶命5种组合：①比肩争夫+偏印佐证（"姐妹刚强必嫁偏房"）②财星太旺太多③伤官+七杀同透④天干同时透官星和伤官⑤官星+七杀俱透；日支坐伤官/七杀也易做偏房
  conclusion: 二奶命5种组合：①比肩争夫+偏印佐证（"姐妹刚强必嫁偏房"）②财星太旺太多③伤官+七杀同透④天干同时透官星和伤官⑤官星+七杀俱透；日支坐伤官/七杀也易做偏房
  content_status: full
  full_statement: 二奶命5种组合：①比肩争夫+偏印佐证（"姐妹刚强必嫁偏房"）②财星太旺太多③伤官+七杀同透④天干同时透官星和伤官⑤官星+七杀俱透；日支坐伤官/七杀也易做偏房
  raw_file: sources/gao/2018弟子班_车祸婚姻篇_85页.md
  raw_anchor: line:1482
  source_ref:
    path: sources/gao/2018弟子班_车祸婚姻篇_85页.md
    anchor: line:1482
  verify_fragment: 天干同时透官星和伤官
  legacy_anchor: 婚姻篇第 13 课（"二奶命的突出命理特征…姐妹刚强乃作填房之妇"）
  anchor_confidence: high
- id: G-CH-013
  school: gao
  classic_name: 高德臣盲派
  title: ⚠空亡断死期8法
  domain: hunyin
  topic: hunyin
  tags:
  - ⚠空亡断死期8法
  - CH
  - 锚点修正
  statement: ⚠空亡断死期8法：①73/84岁遇空亡②岁运并临遇空亡③天克地冲遇空亡④身旺羊刃重重遇空亡⑤刑冲克害遇空亡⑥身旺会合生身遇空亡⑦身弱生身太过遇空亡⑧身弱七杀重重遇空亡
  conclusion: ⚠空亡断死期8法：①73/84岁遇空亡②岁运并临遇空亡③天克地冲遇空亡④身旺羊刃重重遇空亡⑤刑冲克害遇空亡⑥身旺会合生身遇空亡⑦身弱生身太过遇空亡⑧身弱七杀重重遇空亡
  content_status: full
  full_statement: ⚠空亡断死期8法：①73/84岁遇空亡②岁运并临遇空亡③天克地冲遇空亡④身旺羊刃重重遇空亡⑤刑冲克害遇空亡⑥身旺会合生身遇空亡⑦身弱生身太过遇空亡⑧身弱七杀重重遇空亡
  raw_file: sources/gao/2018弟子班_车祸婚姻篇_85页.md
  raw_anchor: line:2631
  source_ref:
    path: sources/gao/2018弟子班_车祸婚姻篇_85页.md
    anchor: line:2631
  verify_fragment: 身旺羊刃重重遇空亡
  legacy_anchor: 寿限专题（"空亡定生死"1~8 + 空亡表）
  anchor_confidence: high
- id: G-CH-033
  school: gao
  classic_name: 高德臣盲派
  title: 合婚五步归纳法
  domain: hunyin
  topic: hunyin
  tags:
  - 合婚五步归纳法
  - CH
  - 锚点修正
  statement: 合婚五步归纳法：①首看年命纳音（相生为首）②看双方年柱正五行（生合好/刑冲不行）③看双方日柱天干五行（财官正合最有情）④属相配婚（最忌穿）⑤双方旺神互为喜用；重点前三条
  conclusion: 合婚五步归纳法：①首看年命纳音（相生为首）②看双方年柱正五行（生合好/刑冲不行）③看双方日柱天干五行（财官正合最有情）④属相配婚（最忌穿）⑤双方旺神互为喜用；重点前三条
  content_status: full
  full_statement: 合婚五步归纳法：①首看年命纳音（相生为首）②看双方年柱正五行（生合好/刑冲不行）③看双方日柱天干五行（财官正合最有情）④属相配婚（最忌穿）⑤双方旺神互为喜用；重点前三条
  raw_file: sources/gao/2018弟子班_车祸婚姻篇_85页.md
  raw_anchor: line:1110
  source_ref:
    path: sources/gao/2018弟子班_车祸婚姻篇_85页.md
    anchor: line:1110
  verify_fragment: 双方日柱天干五行
  legacy_anchor: 婚姻篇第 8 课 §归纳合婚法（"首先看年命纳音…重点是前三条"）
  anchor_confidence: medium
- id: G-CH-010
  school: gao
  classic_name: 高德臣盲派
  title: 寿元星确定4法
  domain: hunyin
  topic: hunyin
  tags:
  - 寿元星确定4法
  - CH
  - 锚点修正
  statement: 寿元星确定4法：①食神（无食用伤官）②印绶（护身符）③禄神（日主之禄=身体）④财星（养命之源，以上皆无时用）；寿元星条件：命中少而精/靠近日主或兼月令/一般通根得气
  conclusion: 寿元星确定4法：①食神（无食用伤官）②印绶（护身符）③禄神（日主之禄=身体）④财星（养命之源，以上皆无时用）；寿元星条件：命中少而精/靠近日主或兼月令/一般通根得气
  content_status: full
  full_statement: 寿元星确定4法：①食神（无食用伤官）②印绶（护身符）③禄神（日主之禄=身体）④财星（养命之源，以上皆无时用）；寿元星条件：命中少而精/靠近日主或兼月令/一般通根得气
  raw_file: sources/gao/2018弟子班_车祸婚姻篇_85页.md
  raw_anchor: line:2299
  source_ref:
    path: sources/gao/2018弟子班_车祸婚姻篇_85页.md
    anchor: line:2299
  verify_fragment: 靠近日主或兼月令
  legacy_anchor: 寿限专题（"确定哪个是寿元星…寿元星的具备条件"）
  anchor_confidence: medium
```

## 审计结论（261 条全量）

- 原锚点全部为节号描述（如「第 1 课 §二.2」），**0 条可直接按行回读**；原稿仅「# 第N课、」级标题，无「§」子节标记。
- 全量 LCS 审计：LCS≥10 仅 12 条；LCS≥7 共 99 条（其中标题级锚点 23 条）；其余 162 条为归纳型摘要（①②③式多条合并），**原稿中不存在可精确回读的连续文本**，属"合理归纳但不可逐字回溯"。
- 本批 30 条为 LCS≥7 中置信度最高者（跨 9 个原稿文件各 4 条），已全部改为真实行锚。
- 剩余 231 条建议：① 维持节号锚点并在 index.yaml 标注 anchor_type=section（可追溯但不可行级回读）；② 或按原稿重新抽取（成本高）。请人类裁决。

## 附录 · 99 条可回读清单（LCS≥7）

| id | line | LCS | 标题级 | 片段 |
|---|---|---|---|---|
| G-LF-023 | 425 | 47 |  | 寒虽甚，要暖有气，暖虽至，要寒有根，则能生成万物。若寒甚而暖无气，暖至而寒无根，必无生成之妙也 |
| G-LF-013 | 189 | 20 |  | 明看五行，暗推长生，神煞空亡，参考应用。 |
| G-LF-015 | 211 | 16 |  | 方法都证明一件事，才可以铁口直断 |
| G-DY-002 | 55 | 15 |  | 合冲为先，刑害次之，生克又次之 |
| G-LF-003 | 27 | 15 |  | 看你家里有什么东西可以为你所用 |
| G-BD-024 | 2706 | 13 | Y | 日干通地支起太岁看一生祸福 |
| G-CY-012 | 519 | 13 |  | 我宫与年月财官印有必然联系 |
| G-SS-005 | 107 | 13 |  | 卦逢生气，天德合，世世长年 |
| G-SS-015 | 402 | 13 |  | 羊刃更兼倒戈，必作无头之鬼 |
| G-CY-006 | 195 | 12 |  | 他宫之财与我宫是否有联系 |
| G-LF-005 | 31 | 12 |  | 先天一气是本元，要看清浊 |
| G-SS-003 | 19 | 12 |  | 生用阳贵人，夜生用阴贵人 |
| G-CS-008 | 513 | 11 |  | 即使原局有财也不当财看 |
| G-DY-001 | 45 | 11 |  | 通过合、冲、刑、害、值 |
| G-DY-009 | 145 | 11 |  | 步大运让命局突然失衡（ |
| G-LF-006 | 45 | 11 |  | 独财值千金，独官掌万民 |
| G-CH-035 | 1482 | 10 | Y | 天干同时透官星和伤官 |
| G-DY-003 | 67 | 10 |  | 运支对运干起损益作用 |
| G-LF-001 | 19 | 10 |  | 月令是天地主气的发源 |
| G-LF-021 | 427 | 10 |  | 命局中阴阳二气在大运 |
| G-MG-005 | 226 | 10 |  | 命宫旺衰以月令为标准 |
| G-MG-012 | 548 | 10 |  | 以流年小限地支起正月 |
| G-XF-021 | 1245 | 10 | Y | 辰未自带印华盖星坐命 |
| G-BD-018 | 961 | 9 |  | 申年生人忌未不忌亥 |
| G-CH-013 | 2631 | 9 |  | 身旺羊刃重重遇空亡 |
| G-CY-004 | 105 | 9 |  | 财星组合与命主有情 |
| G-CY-008 | 257 | 9 |  | 财星主动送到我宫为 |
| G-DY-007 | 133 | 9 |  | 大运有成格变格之权 |
| G-LF-020 | 411 | 9 |  | 四个基本特征：对立 |
| G-MG-020 | 940 | 9 |  | 日干起禄与时干起马 |
| G-SS-016 | 566 | 9 |  | 年干支与月干支相同 |
| G-SS-020 | 510 | 9 |  | 填实，岁运才能填实 |
| G-BD-002 | 296 | 8 |  | 酉戌亥子丑寅为阴 |
| G-BD-016 | 2314 | 8 |  | 己酉丙子己卯甲子 |
| G-BD-019 | 2737 | 8 | Y | 以流年地支起太岁 |
| G-BD-028 | 1143 | 8 |  | 法：甲鸡乙犬丙羊 |
| G-CH-010 | 2299 | 8 |  | 靠近日主或兼月令 |
| G-CH-014 | 2665 | 8 |  | 甲己追未申铲丑寅 |
| G-CH-019 | 383 | 8 |  | 盲派配偶方向诀： |
| G-CH-023 | 557 | 8 |  | 日干与配偶星相合 |
| G-CH-032 | 1290 | 8 |  | 比肩透干争合官星 |
| G-CH-033 | 1110 | 8 | Y | 双方日柱天干五行 |
| G-CS-005 | 158 | 8 |  | 代表命主行使权力 |
| G-CS-017 | 841 | 8 |  | 刃头财主风险之财 |
| G-CS-022 | 1336 | 8 |  | 月柱管19-36 |
| G-CS-025 | 771 | 8 |  | 我宫与年月财官印 |
| G-CS-029 | 1628 | 8 |  | 代表职业的那个字 |
| G-CS-033 | 1966 | 8 |  | ⑤无金看财星做功 |
| G-CY-016 | 693 | 8 |  | 四柱见财食在岁月 |
| G-LF-004 | 29 | 8 |  | 人生在世名利二字 |
| G-LF-019 | 447 | 8 |  | 阳，丑卯巳未酉亥 |
| G-MG-007 | 316 | 8 |  | 初年初运必损父母 |
| G-MG-009 | 426 | 8 |  | 盲派神煞流年断诀 |
| G-MG-024 | 1376 | 8 | Y | 日时不可三煞年命 |
| G-SS-023 | 620 | 8 |  | 48岁前有大坎坷 |
| G-XF-009 | 341 | 8 |  | 天干与地支通禄合 |
| G-XF-012 | 365 | 8 |  | ；丑戌未三刑见金 |
| G-BD-003 | 378 | 7 |  | 时支为日干归禄 |
| G-BD-020 | 2350 | 7 | Y | 天干通地支表： |
| G-CH-001 | 21 | 7 |  | 印星金舆代表车 |
| G-CH-002 | 29 | 7 | Y | 命带天马有刑冲 |
| G-CH-003 | 43 | 7 |  | 地支并排有车像 |
| G-CH-004 | 57 | 7 |  | 身坐真马穿带冲 |
| G-CH-006 | 97 | 7 | Y | 天透戊土地有冲 |
| G-CH-007 | 117 | 7 | Y | 地支寅寅天干丙 |
| G-CH-008 | 2165 | 7 | Y | 身带自刑两星战 |
| G-CH-011 | 2307 | 7 |  | 刑冲穿合反复冲 |
| G-CH-021 | 505 | 7 | Y | 天干五合来串宫 |
| G-CS-002 | 72 | 7 | Y | 天干五合看得失 |
| G-CS-003 | 88 | 7 | Y | 天干生助看得失 |
| G-CS-009 | 533 | 7 |  | 财统官或官统财 |
| G-CS-016 | 943 | 7 |  | 大运流年见财库 |
| G-CS-020 | 1184 | 7 |  | 十神配置定格局 |
| G-CS-032 | 1856 | 7 | Y | 医务工作者命理 |
| G-CY-003 | 71 | 7 |  | 财临库地逢三合 |
| G-CY-005 | 137 | 7 |  | 财生官印印通身 |
| G-CY-011 | 347 | 7 |  | 我能获取到的财 |
| G-CY-013 | 485 | 7 | Y | 基础财富看财星 |
| G-DY-011 | 165 | 7 |  | 甲寅乙卯，其次 |
| G-DY-015 | 239 | 7 |  | 本人或配偶不利 |
| G-DY-016 | 292 | 7 |  | ：流年干支谁在 |
| G-DY-021 | 398 | 7 |  | 某字与克神之间 |
| G-DY-022 | 410 | 7 | Y | 远近组合断流年 |
| G-DY-024 | 472 | 7 |  | 大运生助主克者 |
| G-DY-028 | 925 | 7 |  | 长生遇杀最有灾 |
| G-LF-009 | 101 | 7 |  | 竖看天干与地支 |
| G-MG-001 | 33 | 7 |  | 子起正月逆查行 |
| G-MG-003 | 168 | 7 |  | 胎元与年柱不和 |
| G-MG-004 | 218 | 7 |  | 日干与身干相合 |
| G-MG-008 | 282 | 7 | Y | 命宫与大运流年 |
| G-MG-021 | 912 | 7 |  | 禄马支到长生地 |
| G-MG-022 | 1106 | 7 | Y | 大小黄道择日法 |
| G-MG-026 | 1725 | 7 | Y | 夫星天嗣死墓绝 |
| G-MG-030 | 1841 | 7 | Y | 八字五行取名法 |
| G-SS-001 | 35 | 7 |  | 与贵人干支相合 |
| G-SS-010 | 117 | 7 |  | 财官入库不得用 |
| G-SS-012 | 123 | 7 |  | 日干或食神入墓 |
| G-XF-006 | 233 | 7 | Y | 发表归根定体用 |
| G-XF-014 | 1217 | 7 | Y | 库神虚透不收物 |
