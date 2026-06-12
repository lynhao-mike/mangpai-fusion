# Phase-300 校准分析报告

生成时间：`2026-06-12T19:32:59+08:00`

数据来源：

- `META/phase-300-calibration.md`
- `META/phase-300-calibration-summary.md`
- `META/phase-300-voting-strategy.md`

执行范围：只读分析。未修改 `theory/*`、`engine/*` 或 `META/project-state.json`。

---

## 1. 执行结论

Phase-300 的投票压缩与防压制机制已经具备可进入 Phase-1000 扩展的基本形态：

1. **EVENT / TIMING 覆盖完整**：100 个案例均有 EVENT 与 TIMING 命中，覆盖率均为 100.0%。
2. **Raw 票数存在强烈 School 不均衡**：`tiaohou_ditiansui` raw vote 为 19,662，占 80.9%；`ziping` raw vote 为 4,648，占 19.1%。若直接按 raw vote 调权，DTS 会系统性压制 ZIPING。
3. **School lane 防压制设计是必要且有效的**：策略文件固定 `ziping=0.50`、`tiaohou_ditiansui=0.50`，且 School Vote 在 lane 内归一化，因此 raw 规则数量差异不会直接变成最终权重差异。
4. **重复票风险集中在少数 family**：严格按 `(raw - family) / raw > 80%` 统计，共 242 条 family 明细行超过 80% 压缩阈值，全部来自 `tiaohou_ditiansui / DITIANSUI_CHANWEI`，集中于 `FAM-011`、`FAM-018`、`FAM-010`、`FAM-004`。
5. **反馈闭环的最大短板不是 EVENT / TIMING 覆盖，而是反馈稀疏**：100 个案例中 73 个案例反馈为 `0/0/0/0`，当前反馈信号主要集中在 27 个案例；因此 Phase-300 可用于结构压力测试，但不宜直接作为最终生产权重校准依据。
6. **方法学风险明确存在**：100 个案例全部为 `fallback_yaml_trigger`，说明本轮校准是 fallback 触发下的只读统计产物；应在 Phase-1000 前修复触发入口环境问题，并重跑一轮非 fallback 校准作为对照。

---

## 2. Raw → Family → Canon → School 总览

| 层级 | 总量 | 相对 Raw | 说明 |
|---|---:|---:|---|
| Raw Rule Votes | 24,310 | 100.0% | 原始触发规则数，仅诊断 |
| Family groups | 20,240 | 83.3% | case × school × canon × family 分组数 |
| Family Votes | 22,451 | 92.4% | Shared Evidence + Family Cap 后票数 |
| Canon Main Votes | 17,256 | 71.0% | 仅 EVENT / STRUCTURE 主票进入 Canon 主口径 |
| School lanes | 200 | 0.8% | 100 case × 2 school lane |

### 2.1 压缩解读

| 指标 | 值 | 解读 |
|---|---:|---|
| raw_total | 24,310 | 全部原始触发票 |
| family_vote_total | 22,451 | Shared Evidence 与 Family Cap 处理后保留票 |
| duplicate_or_cap_compressed | 1,859 | 被重复证据或 family cap 消化的票 |
| duplicate_compression_rate | 7.6% | 全局压缩率不高，但局部 family 压缩极强 |
| case-level 最高压缩 | 19.9% | 多个 312 raw / 250 family 案例达到该档 |
| case-level 最低压缩 | 6.1% | 98 raw / 92 family 的低触发案例 |

全局 7.6% 的重复/封顶压缩率看似温和，但这是被大量低重复 family 稀释后的结果。真正需要治理的是局部 family 的高重复：`FAM-011` 聚合压缩率达到 89.9%，`FAM-018` 达到 81.4%，这类 family 一旦不封顶，会显著放大 DTS 结构判断。

---

## 3. EVENT / TIMING 覆盖情况

| 指标 | 案例数/票数 | 覆盖率或占比 |
|---|---:|---:|
| EVENT case coverage | 100 | 100.0% |
| TIMING case coverage | 100 | 100.0% |
| EVENT raw hits | 5,473 | 22.5% of raw |
| TIMING raw hits | 1,605 | 6.6% of raw |

### 3.1 覆盖判断

- EVENT 与 TIMING 在 case 层均无空白，说明规则库对 100 个案例至少均能产出事件与应期触发。
- EVENT raw hits 占 22.5%，具备稳定主票入口。
- TIMING raw hits 占 6.6%，覆盖完整但票量偏低，应在 Phase-1000 中继续观察应期准确率，而不是仅看是否触发。

### 3.2 低 EVENT / TIMING 触发案例

| case_id | raw | family | EVENT | TIMING | 反馈 |
|---|---:|---:|---:|---:|---|
| C-2026-RF000164-乾-戊寅戊午乙未壬午 | 98 | 92 | 22 | 7 | 0/0/0/0 |
| C-2026-RF000175-坤-乙亥己卯丁未乙巳 | 98 | 92 | 22 | 7 | 0/0/0/0 |
| C-2026-RF000373-乾-丙子庚子辛巳己亥 | 98 | 92 | 22 | 7 | 0/0/0/0 |
| C-2026-RF000535-乾-戊寅丁巳壬戌己酉 | 98 | 92 | 22 | 7 | 0/0/0/0 |
| C-2026-RF000763-乾-壬午辛亥辛巳己亥 | 98 | 92 | 22 | 7 | 0/0/0/0 |
| C-2026-RF000123-坤-壬午甲辰戊申庚申 | 114 | 102 | 27 | 7 | 0/0/0/0 |
| C-2026-RF000396-坤-甲申丁卯丙午壬辰 | 114 | 102 | 27 | 7 | 0/0/0/0 |

这些案例不是 EVENT/TIMING 未命中，而是低触发 + 无反馈叠加。Phase-1000 中应优先补这些低触发样本的真实反馈，以判断低触发是否意味着规则覆盖不足，还是命式本身可触发结构较少。

---

## 4. 家族级风险与高重复规则

### 4.1 严格 `>80%` 压缩 family 明细行

| 指标 | 值 |
|---|---:|
| family 明细行总数 | 2,812 |
| 严格 `>80%` 压缩行 | 242 |
| 占 family 明细行比例 | 8.6% |
| 涉及 school | tiaohou_ditiansui: 242 |
| 涉及 canon | DITIANSUI_CHANWEI: 242 |

按 family_id 分布：

| family_id | `>80%` 压缩行 | 聚合 raw | 聚合 family | 聚合压缩率 | 风险含义 |
|---|---:|---:|---:|---:|---|
| FAM-011 | 83 | 990 | 100 | 89.9% | 从格条件重复触发极高，若不 cap 会放大格局判断 |
| FAM-018 | 75 | 564 | 105 | 81.4% | 月令 / 坎离升降证据复用强，解释票与应期票易叠加 |
| FAM-010 | 50 | 491 | 117 | 76.2% | 局部行超过 80%，聚合后低于 80%，但仍属高压缩族 |
| FAM-004 | 34 | 611 | 205 | 66.4% | 调候/月令 shared evidence 极多，局部高压缩明显 |

### 4.2 聚合压缩率最高 family

| family_id | rows | raw | family | shared | 聚合压缩率 | strict rows |
|---|---:|---:|---:|---:|---:|---:|
| FAM-011 | 100 | 990 | 100 | 325 | 89.9% | 83 |
| FAM-018 | 105 | 564 | 105 | 840 | 81.4% | 75 |
| FAM-010 | 100 | 491 | 117 | 100 | 76.2% | 50 |
| FAM-008 | 100 | 408 | 100 | 100 | 75.5% | 0 |
| FAM-012 | 100 | 681 | 195 | 0 | 71.4% | 0 |
| FAM-016 | 100 | 300 | 100 | 100 | 66.7% | 0 |
| FAM-017 | 100 | 300 | 100 | 100 | 66.7% | 0 |
| FAM-004 | 205 | 611 | 205 | 1,665 | 66.4% | 34 |
| FAM-002 | 190 | 776 | 290 | 1,095 | 62.6% | 0 |
| FAM-015 | 105 | 415 | 205 | 176 | 50.6% | 0 |

### 4.3 核心风险 family 解读

#### FAM-011：从格条件

- 风险等级：CRITICAL。
- Family Cap：1。
- 聚合 raw 990 → family 100，压缩率 89.9%。
- 83 条明细行严格超过 80% 压缩。
- 典型明细：raw 13 → family 1，压缩 92.3%，类型组合为 `EVENT:3, GENERAL_PRINCIPLE:1, STRUCTURE:9`。

判断：`FAM-011` 是本轮最强重复源。它既有 STRUCTURE，又混入 EVENT 与 GENERAL_PRINCIPLE，如果不先 family cap，会把“从格条件”变成跨规则重复投票器。当前 cap=1 是正确且必须保留的。

#### FAM-004：月令/调候/寒暖燥湿

- 风险等级：CRITICAL。
- Family Cap：1。
- 聚合 raw 611 → family 205，压缩率 66.4%。
- shared evidence 合计 1,665，为所有高风险 family 中非常突出的证据复用源。
- 34 条明细行严格超过 80% 压缩。
- 典型明细：raw 8 → family 1，压缩 87.5%，类型组合为 `ANTI_PATTERN:1, EVENT:1, GENERAL_PRINCIPLE:1, STRUCTURE:4, TIMING:1`。

判断：`FAM-004` 的聚合压缩率不如 `FAM-011`，但 shared evidence 规模更大，说明其问题不是单纯 raw 票重复，而是同一“月令/调候/寒暖燥湿”证据被多种 rule type 复用。Phase-1000 应继续保留 cap=1，并将其作为 shared evidence 去重质量的重点观察对象。

#### FAM-018 / FAM-010：二级重点

- `FAM-018` 聚合压缩率 81.4%，strict rows 75，且同时涉及 TIMING 与辅助票，说明其对“应期 + 结构解释”有叠加风险。
- `FAM-010` 聚合压缩率 76.2%，但 strict rows 50，属于“局部强重复、全局被稀释”的 family，应在 Phase-1000 继续观察是否需要从 MEDIUM cap=3 下调为 HIGH cap=2。

---

## 5. School 分布与防压制效果

### 5.1 Raw vote 分布

| School | Raw votes | Raw 占比 | Phase-300 School prior |
|---|---:|---:|---:|
| tiaohou_ditiansui | 19,662 | 80.9% | 0.50 |
| ziping | 4,648 | 19.1% | 0.50 |
| 合计 | 24,310 | 100.0% | 1.00 |

### 5.2 Canon 分布

| Canon | Raw votes | Raw 占比 | School |
|---|---:|---:|---|
| DITIANSUI_CHANWEI | 16,218 | 66.7% | tiaohou_ditiansui |
| DITIANSUI | 3,444 | 14.2% | tiaohou_ditiansui |
| QIONGTONG_BAOJIAN | 2,326 | 9.6% | ziping |
| ZIPING_ZHENQUAN | 1,397 | 5.7% | ziping |
| SANMING_TONGHUI | 925 | 3.8% | ziping |

### 5.3 防压制判断

Raw 层 DTS:ZIPING 约为 4.23:1。若直接按 raw vote 调权，`DITIANSUI_CHANWEI` 会支配结果，ZIPING 三个 canon 的合计影响力会被显著压低。

Phase-300 策略通过三层机制防止这一点：

1. Raw Rule Votes 只作诊断，不直接进入最终权重。
2. Canon Vote 前先做 family-level normalization，先消化高重复 family。
3. School Vote 在各自 school lane 内归一化，并使用 `ziping=0.50`、`tiaohou_ditiansui=0.50` 初始先验。

结论：当前校准后 School Vote 设计是均衡的；不是因为 raw vote 均衡，而是因为治理模型明确阻断了 raw rule count 到 final school weight 的直接传导。

---

## 6. 反馈闭环信号

### 6.1 总体反馈统计

| 反馈信号 | 计数 | 占反馈信号比例 |
|---|---:|---:|
| hit | 340 | 54.5% |
| miss | 109 | 17.5% |
| partial | 94 | 15.1% |
| unknown | 81 | 13.0% |
| 合计 | 624 | 100.0% |

### 6.2 案例反馈覆盖

| 指标 | 值 |
|---|---:|
| 总案例数 | 100 |
| 反馈为 `0/0/0/0` 的案例 | 73 |
| 有任一反馈信号的案例 | 27 |
| 案例级反馈覆盖率 | 27.0% |

反馈稀疏是当前最大限制。虽然总反馈信号有 624 条，但它们集中在少数案例，导致 family 与 school 级校准容易受少量高反馈案例牵引。

### 6.3 高 miss / unknown 案例

| case_id | raw | EVENT | TIMING | hit/miss/partial/unknown | 观察 |
|---|---:|---:|---:|---|---|
| C-2026-018-坤-乙丑戊寅乙酉乙酉 | 312 | 73 | 19 | 18/26/12/0 | miss 最高，应优先复核规则误伤 |
| C-2026-001-乾-庚申戊寅壬子辛丑 | 312 | 73 | 19 | 41/22/12/30 | hit 高但 unknown 也最高，反馈标注不充分 |
| C-2026-016-坤-甲子丙子丙戌戊子 | 296 | 68 | 19 | 32/15/5/0 | miss 偏高，仍有较强有效命中 |
| C-2026-002-坤-壬戌庚戌戊辰丙辰 | 312 | 73 | 19 | 13/13/12/4 | hit/miss/partial 接近，结论分歧大 |
| C-2026-014-乾-丙戌庚子乙亥辛巳 | 312 | 73 | 19 | 15/11/16/4 | partial 最高之一，规则表达可能过宽 |
| C-2026-015-乾-甲寅乙亥丙辰辛卯 | 312 | 73 | 19 | 41/6/17/14 | hit 高但 partial/unknown 偏高 |
| C-2026-033-坤-戊午己未乙酉丁亥 | 296 | 68 | 19 | 5/0/0/13 | unknown 高，反馈缺口明显 |
| C-2026-013-坤-壬申甲辰丙辰己丑 | 312 | 73 | 19 | 4/5/0/9 | 低 hit + 高 unknown，应复核是否样本信息不足 |

### 6.4 系统偏差判断

当前不能断言存在稳定“命理系统偏差”，因为 73% 案例没有反馈信号，且所有案例均为 fallback 触发。可以确认的是三个弱信号：

1. **反馈覆盖弱域**：低触发 RF 案例普遍无反馈，无法校准低覆盖命式。
2. **FAM-011 / FAM-004 高重复弱域**：重复压缩强，说明这些 family 的证据边界仍需治理。
3. **DTS raw 支配风险**：即使最终 school lane 已防压制，raw 层仍显示 DTS 规则密度远高于 ZIPING，Phase-1000 若新增 DTS 规则必须同步扩充 ZIPING 对照证据或保持 school prior 不变。

---

## 7. Methodology 风险

### 7.1 fallback 触发

100 个案例触发模式均为 `fallback_yaml_trigger`。

这意味着本轮统计更适合作为“规则库压力测试”和“投票治理验证”，不应直接等同于完整生产 pipeline 的真实性能。Phase-1000 前建议修复 fallback 原因并重跑对照批次。

### 7.2 反馈样本偏置

有反馈案例仅 27 个，且高反馈集中在少数前序 case。当前 hit rate 54.5% 是“反馈信号级”比例，不是“案例级准确率”，不可简单宣传为系统准确率。

### 7.3 raw vote 与 family vote 口径差异

`Family groups` 为 20,240，而 `Family Votes` 为 22,451。两者不是同一口径：前者是分组数，后者是 Shared Evidence + Family Cap 后的票数。报告和后续仪表盘应避免把两者误写成简单递减链条。

---

## 8. Phase-300 → Phase-1000 改进建议

### 8.1 必须保留的机制

| 机制 | 建议 | 原因 |
|---|---|---|
| Family Cap | 保留，尤其 `FAM-004`、`FAM-011` cap=1 | 局部高重复极强，取消会导致结构票放大 |
| Shared Evidence | 保留并增强审计 | `FAM-004` shared evidence 高达 1,665，证据复用风险突出 |
| School lane normalization | 保留 | DTS raw 占 80.9%，直接 raw 调权会压制 ZIPING |
| Rule Type 分层 | 保留 | GENERAL_PRINCIPLE / ANTI_PATTERN 不应直接进入正向主票 |
| TIMING 单独统计 | 保留 | TIMING 票量仅 6.6%，混入结构票会掩盖应期质量 |

### 8.2 Phase-1000 优先任务

1. **修复 fallback 触发环境并重跑对照**
   - 目标：至少生成一版非 fallback 校准摘要。
   - 验证：比较 fallback 与正常 pipeline 下 raw/family/event/timing 分布是否稳定。

2. **建立 family 压缩 leaderboard**
   - 固定输出 family 聚合 raw、family、shared、compression、strict rows。
   - 对 `FAM-011`、`FAM-018`、`FAM-010`、`FAM-004` 做每轮追踪。

3. **扩充低触发案例反馈**
   - 优先补 `98 raw / 22 EVENT / 7 TIMING` 档案例。
   - 判断低触发是否对应覆盖不足。

4. **把反馈覆盖率纳入校准门槛**
   - 建议 Phase-1000 不只看 hit/miss 总量，还看案例级有反馈比例。
   - 建议最低门槛：有效反馈案例 ≥ 60%，否则仅允许产出诊断报告，不允许自动调权。

5. **将 partial 单独治理**
   - `partial` 占 15.1%，不是简单正确或错误。
   - 建议把 partial 拆为：范围过宽、应期偏移、事件类别近似、证据链不足。

6. **对 `FAM-010` 重新评估 cap 等级**
   - 当前聚合压缩 76.2%，strict rows 50。
   - 若 Phase-1000 仍保持高 strict rows，建议从 MEDIUM cap=3 调整为 HIGH cap=2。

7. **对 ZIPING 做对照扩充而非 raw 补票竞争**
   - 不建议为了追平 DTS raw 数量而机械新增 ZIPING 规则。
   - 应优先补 ZIPING 在 EVENT/TIMING 与高风险 family 对照上的缺口，保持 school lane 内质量优先。

---

## 9. Phase-1000 验证路径

| 验证点 | 第一证明点 | 反证条件 |
|---|---|---|
| School 防压制有效 | DTS raw 仍高但 School prior 维持 0.50/0.50，ZIPING 结论不被 raw 数压制 | School 输出与 raw DTS 占比高度同向漂移 |
| Family Cap 有效 | `FAM-011` raw 高但 family vote 稳定为 cap 后有限票 | 去掉 cap 后结论大幅偏向从格/调候 |
| EVENT 覆盖有效 | 1000 case 中 EVENT coverage 仍 ≥ 95% | 低触发样本 EVENT 大面积缺失 |
| TIMING 可校准 | TIMING coverage 与应期反馈可分离统计 | TIMING 被结构票淹没，无法独立评估 |
| 反馈闭环可用 | 有反馈案例 ≥ 60%，且 unknown 比例下降 | 反馈继续集中在少数案例，unknown 持续高位 |

---

## 10. 最终建议

Phase-300 的核心价值不是证明规则已足够准确，而是证明投票治理链路已经必要且基本有效：

- Raw vote 不能直接用于权重。
- Family Cap 必须在 Canon Vote 前执行。
- `FAM-011`、`FAM-004` 是必须持续治理的高风险 family。
- DTS 与 ZIPING 必须维持 school lane 防压制，不应按规则数量重新分配权重。
- Phase-1000 的关键不是盲目扩规则，而是补反馈、修 fallback、追踪高重复 family，并把 partial / unknown 纳入可解释闭环。

因此，建议进入 Phase-1000 前先执行一轮“非 fallback 重跑 + family compression leaderboard + 低触发反馈补齐”的预备校验；校验通过后，再扩大样本规模并逐步开放人工仲裁后的权重调整。
