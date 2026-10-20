# 给 Gemini 的终审提示词

```
你是本项目的架构终审者。请基于以下事实做最后方案终审。

重要：你读的是本地代码库的最新状态，但今天有多次会话内变更可能未同步到你的快照。
凡涉及代码位置，以下方「已落地变更」为准。

═══════════════════════════════════════════

## 一、项目第一性原则（AGENTS.md 铁律）

1. 确定性盘面事实只从 python -m engine.cli 获取，禁止心算排盘或编造干支关系
2. 经典与流派理论通过 python -m tools.query_theory 检索
3. 综合推理、证据权衡与最终裁决由 Agent 完成
4. 系统价值 = 证据链可追溯。任何「假阳性」或「静默失败」都比「没有功能」更糟

用户原话：「我的目的是能将真实八字分析准确」——
任意 agent 接入后能通过引擎得出确定性东西，结合语料库和断语，
加上大模型能力进行真实预测，而不是一堆废话。

═══════════════════════════════════════════

## 二、今天的量化成果（已落地并验证）

### 2.1 索引重建（T-108）

派    总数  空conclusion  §指针  trigger  score
gao   630      0           0       0      225
duan   428      0           0     239      290
yang   400      0           0     145      145
ren   200      0           0      30       30

恢复：484 条空正文 + 72 条 § 指针 + 414 条 trigger + 175 条初始分
任派 topic 归位：lifa 144→71，新增 jiankang 38 / zhiye 13 / caiyun 12 / liuqin 10

### 2.2 代码修复

- blind_rule_gate：只有 evaluable 才短路 evaluate_trigger；
  关键词兜底只扫 topic/title/conclusion（不扫 condition/trigger，避免否定词反向召回）
- score_blind_rule：raw>1.0 除以 5.0（段派 3.0~5.0 分制归一化）
- _picture_rank_within：用 rank 门槛代替 bool()，防 204 条 *_picture 恒真
- manifest 污染已修（T-106）；locator 校验已加报警模式（T-110）

### 2.3 当前测试基线

python -m pytest -q                          → 229 passed
python -m pytest tests/tools -q -o addopts="" → 294 passed
python -m pytest tests/v5 -q -o addopts=""   → 130 passed
python -m pytest tests/r10 -q -o addopts=""  → 4 failed, 60 passed

═══════════════════════════════════════════

## 三、经过五轮推演收敛的方案（Opus 指挥，Claude Review）

### 3.1 战略结论

- engine.cli 服务 Agent（人话推理），engine/v5/runner 服务度量（balanced_accuracy）
- **两条链必须并存，数据契约不兼容，不应强行融合**
  （CLI 输出 chart/relations/strength/shensha/structures/duan_zuogong；
   run_v5 需要 case_id/current_dayun/{y,m,d,h}_{stem,branch}/pillars/... 共 16 字段，零交集）
- CLI 无 --input 参数，只有 --birth/--pillars/--gender

### 3.2 推演收敛轨迹（每轮都发现新问题）

v1: 砍 v5 报告生成 -800 行        → 漏了 engine/application/production_service.py 依赖
v2: 删 build_chart_from_input     → CLI 断链（无 --input，结构零交集）
v3: -430 行                      → render_report.py 不是薄包装，是 2281 行渲染器
v4: -2657 行                     → render_report 零调用（错，实际 10+ 处调用）
v5: -250 行                      → 承认 render_report 是活代码
v6: 阶段 1 删 -150 行             → 0 外部调用 ≠ 可删，那 12 个是保留函数的私有辅助层

### 3.3 最终确定执行的三个阶段

阶段 2：断点 4 域重分类（+20 行）
  问题：BLIND_TOPIC_DOMAINS（runner.py:52-69）把 lifa(448)/dayun(75) 映射成「事业」，
        真实事业规则 zhiye 只有 40 条 = 7.1%；ziping 的 domains[0] 有 87.9% 是「事业」
  修复：lifa/dayun → 总体；shensha 删映射（150 条中 83 条语义不符）；
        liuqin/geju → 总体；jiaoyu → 学业
  理由：Agent 走 CLI 路线时直接消费域检索，这是唯一必修

阶段 3：修 22 处桩文本为诚实声明（~22 行字符串替换）
  问题：report_view.py:288-353 硬编码「MVP 阶段待细化」「待反馈细分学校层级」等
  修复：改为「待补充（引擎未产出该域的结构裁决）」这类诚实声明
  理由：第一性原则——诚实声明缺失 > 冒充结论

阶段 4：CLI 增加 picture 子命令（+30 行）
  问题：engine.cli 缺杨派画面，Agent 拿不到 picture 事实
  修复：新增 picture 子命令，调用 engine/facts/picture.py:match_picture()

### 3.4 已决定不做的事

- 不删 render_report.py（2281 行，10+ 处调用，engine/application/dual_engine_adapter.py
  的 docstring 明确推荐「新代码请使用 run_v5 + tools.render_report.render_from_output」）
- 不删 build_report_v6_context / render_report_v6_from_output（render_report 依赖）
- 不删 build_chart_from_input（run_v5 的唯一输入适配器）
- 不写 CLI→run_v5 适配器（代价 > 收益）
- 不实现 22 个缺失计算（投入产出比低，非核心需求）

═══════════════════════════════════════════

## 四、请你终审的 6 个问题

### 问题 1：阶段 2 的域重分类方向对吗？

具体映射改动：
  lifa    事业 → 总体     （448 条方法论）
  dayun   事业 → 总体     （75 条时间维度）
  shensha 健康 → 删除映射  （150 条，83 条语义不符）
  liuqin  无   → 总体     （34 条六亲）
  geju    无   → 总体     （117 条格局）
  jiaoyu  无   → 学业     （12 条，当前被「财」字抓去财富）

有没有遗漏的 topic？有没有改错方向的？

### 问题 2：阶段 3 的桩文本修法对吗？

从「MVP 阶段待细化」改成「待补充（引擎未产出该域的结构裁决）」。
你认为这个措辞合适吗？还有更好的表达吗？

### 问题 3：阶段 4 的 CLI picture 子命令够不够？

Agent 走 CLI 路线时，除了 picture 还缺什么事实？
（当前 CLI 已输出 chart/relations/strength/shensha/structures/duan_zuogong）

### 问题 4：这三个阶段之后，最高杠杆的下一步是什么？

可选方向：
  a. 修 tests/evaluation 的 320 个失败（8 个文件依赖已删除的 .omo 草稿）
  b. 修 tests/asof 的 2 个红灯（模块越界导入 + 哈希基线漂移）
  c. 修 tests/r10 的 4 个失败（召回策略回归）
  d. 收编 theory/ziping/index-new.yaml 的 127 条唯一规则
  e. 扩充语料
  f. 其他

请按对「指标 A 45.3% / 指标 B 0.3625」的预期影响排序。

### 问题 5：我们可能漏掉了什么更高杠杆的事？

今天五轮推演全在「删代码」和「修映射」上打转。
有没有一个我们完全没看到的切入口，能更直接提升预测准确率？

### 问题 6：指标 A/B 有没有明确的提升路径？

指标 A：盲断严格口径 45.3%（77/170），过吉 37 > 过凶 22
指标 B：balanced_accuracy 0.3625，门槛 0.425/0.60，eligible is False

这两个数字是用户的核心目标。以当前架构，它们有明确的提升路径吗？
如果没有，缺什么？

═══════════════════════════════════════════

## 五、输出要求

1. 逐条回答 6 个问题，直接给结论
2. 如果某个阶段的方向错了，直接说错在哪
3. 问题 5 和 6 最重要——请重点回答
4. 不需要给 diff，需要的是方向和优先级判断
```
