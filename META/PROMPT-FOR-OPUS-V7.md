# 给 Opus 的提示词（精简版）

```
Claude 在动手前最后一轮核实，发现你的阶段 1 会让代码直接崩。

## 事实

你的 v6 路线图里：
- 阶段 1 要删 12 个「0 外部调用」的辅助函数
- 阶段 3 要保留 build_report_v6_context（150 行）

但这 12 个函数正是 build_report_v6_context 的私有辅助层，它内部调用了 14 个：

    report_view.py:267   _claims_by_domain_school
    report_view.py:302   _l7_school_evidence_for_domain
    report_view.py:308   _l7_conflict_for_domain
    report_view.py:311   _l7_conclusion_for_domain
    report_view.py:324   _l7_conclusion_for_domain
    report_view.py:384-397  _prediction_* 系列（8 个）

「0 外部调用」≠「可以删」。删了它们，build_report_v6_context 立刻 NameError。

## 五轮推演的收敛轨迹

    v1: -800 行              漏了生产依赖
    v2: 删 build_chart_from_input   CLI 断链
    v3: -430 行              render_report 是薄包装（错）
    v4: -2657 行             render_report 零调用（会引爆生产链）
    v5: -250 行              承认是活代码
    v6: 阶段 1 -150 行        0 外部调用 ≠ 可删（本轮）

每轮都在收缩，说明在逼近真实边界，但边际收益已经很低。

## Claude 的决定

不再做代码删除（阶段 1、5 全部暂停）。直接执行三个确定可做的：

    阶段 2：断点 4 域重分类（+20 行）
      BLIND_TOPIC_DOMAINS 把 lifa(448条)/dayun(75条) 映射成「事业」，
      真实事业规则只有 40 条 = 7.1%。
      → lifa/dayun 改为「总体」
      → 这是你认定的「唯一必修」，且 Agent 走 CLI 路线时直接受益

    阶段 3：修 22 处桩文本（~22 行字符串替换）
      「MVP 阶段待细化」→「待补充（引擎未产出该域的结构裁决）」
      → 符合第一性原则：诚实声明缺失 > 冒充结论

    阶段 4：CLI picture 子命令（+30 行）
      engine.cli 当前缺杨派画面，Agent 拿不到 picture 事实

## 请你回答一句话

「同意，执行 2/3/4」或者「不同意，理由是 X」

如果同意，Claude 立即开始阶段 2，每阶段独立跑回归验证。
```
