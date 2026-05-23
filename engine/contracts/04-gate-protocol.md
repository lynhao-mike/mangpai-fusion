# 应期门协议 · 04-gate-protocol

> **本文规定 D3 任派应期三层门的接口与判定细节。**
> 这是 v1.2 的"灵魂条款"——三层齐备才下铁口断。

最后更新：2026-05-23（W1.3）
版本：v1.2.0
依赖：03-findings-schema（GateResult 结构定义在那里）

---

## 一、设计起源

v1.0 失验复盘：

| 案例 | 失验 | 根因 |
|---|---|---|
| C-2026-001 | 婚期 2013 → 实际 2005，差 8 年 | 应期判定只看流年单层引动，未校验"原局有夫宫被动 + 大运到位" |
| C-2026-002 | "婚姻极坎坷不婚" → 23 岁稳定 20 年 | 杨派"五凶煞=婚凶"被当机械铁断，未做应期三层校验 |

v1.2 的解药：**应期判定必须三层齐备 → 才允许 ★★★★★**。

---

## 二、Gate API（D3 引擎入口）

```python
# engine/yingqi/gate.py
def gate_yingqi(
    year: int,
    candidate_event: str,
    domain: Literal["婚姻","事业","财运","健康","学业","六亲","其他"],
    energy: EnergyFindings,
    picture: PictureFindings,
    parsed: ParsedInput,
) -> GateResult:
    """
    对单个候选事件做三层应期 gate 判定。

    返回 GateResult，其中 passed_layers ∈ [0, 3]：
        0 → 不输出（candidate_event 被丢弃）
        1 → confidence.star 最多 ★★★
        2 → confidence.star 最多 ★★★★
        3 → confidence.star 可达 ★★★★★
    """
```


---

## 三、L1 · 原局有（layer1_check）

> **本质**：候选事件对应的"关键字"是否在原局四柱（含藏干）中存在。

### 3.1 关键字映射表（domain → key chars）

```yaml
婚姻:
  primary:
    - 配偶星（男命：正/偏财；女命：正官/七杀）的天干
    - 婚宫支（日支）
  secondary:
    - 配偶星藏干所在地支
    - 月柱地支（杨派：父母给的婚配格局）

事业:
  primary:
    - 官杀星天干（无官杀以食伤为业）
    - 用神（D1 EnergyFindings.tiyong.purpose）
  secondary:
    - 官星藏干位置
    - 月令（事业宫主要是月柱）

财运:
  primary:
    - 财星天干
    - D1 EnergyFindings.tiyong.purpose 中财类字
  secondary:
    - 财库（辰戌丑未中藏财）
    - 食伤生财链上的字

健康:
  primary:
    - 日干本身（太弱/太旺都是病根）
    - 受刑冲穿破最重的支
  secondary:
    - 神煞（白虎/羊刃/灾煞）所挂柱

学业:
  primary:
    - 印星天干
    - 食伤天干（理科/才华）
  secondary:
    - 词馆/学堂/文昌神煞所挂柱

六亲:
  primary:
    - 父：偏财；母：正印；兄弟：比肩；子女：食伤(女)/官杀(男)
  secondary:
    - 各六亲对应宫位：年=父母 / 月=兄弟 / 日=配偶 / 时=子女

其他:
  primary: [日干, 用神]
  secondary: []
```

### 3.2 L1 判定逻辑

```python
def layer1_check(
    domain: str, parsed: ParsedInput, energy: EnergyFindings
) -> LayerCheck:
    keys_primary = get_primary_keys(domain, parsed.bazi, energy)
    keys_secondary = get_secondary_keys(domain, parsed.bazi, energy)

    found = []
    for k in keys_primary:
        if is_in_palace(k, parsed.bazi, palace="any") or is_canggan(k, parsed.bazi):
            found.append(k)

    if len(found) >= 1:
        return LayerCheck(layer="L1_原局有", passed=True,
                          evidence_chars=found, rationale=f"原局存在关键字: {found}")
    # 退而求其次：secondary
    for k in keys_secondary:
        if is_in_palace(k, parsed.bazi, palace="any") or is_canggan(k, parsed.bazi):
            return LayerCheck(layer="L1_原局有", passed=True,
                              evidence_chars=[k], rationale=f"原局存在次级关键字 {k}")

    return LayerCheck(layer="L1_原局有", passed=False,
                      evidence_chars=[], rationale="原局未见 domain 关键字")
```

**特殊豁免**：当 `domain == "婚姻"` 且**配偶星完全不见原局**（含藏干），`L1` 仍允许 passed=True 但 rationale 标记 "无星借宫"，由 D2 PictureFindings.marriage_picture 提供配偶画像。这是杨派"无官借伤、无财借食"的体现。

---

## 四、L2 · 大运到位（layer2_check）

> **本质**：当前年份所在大运（含正在过渡的相邻大运）是否提供了"必需触发字"。

### 4.1 必需触发字定义

| domain | 必需大运字（满足任一） |
|---|---|
| 婚姻 | 配偶星天干 / 婚宫支三合三会六合 / 桃花引动字 |
| 事业 | 官杀字 / 印动字 / 用神到位 |
| 财运 | 财星 / 财库 / 食伤生财链触发字 |
| 健康 | 受刑冲穿的字 / 食神/枭神（伤食对冲） |
| 学业 | 印星 / 文昌 / 词馆字 |
| 六亲 | 对应六亲星 / 对应宫位被引动 |

### 4.2 L2 判定逻辑

```python
def layer2_check(
    year: int, domain: str, energy: EnergyFindings, parsed: ParsedInput
) -> LayerCheck:
    dayun_step = get_dayun_at_year(parsed.dayun, parsed.birth["公历年"], year)
    needed_chars = get_required_dayun_chars(domain, energy, parsed)

    # 当前大运
    current = dayun_step.干支
    found_in_current = [c for c in needed_chars if c in (current.gan, current.zhi)]

    # 过渡期：当前年距大运起讫年 ±1 年内，相邻大运字也算
    transition = is_in_dayun_transition(year, dayun_step, threshold_years=1)
    found_in_adjacent = []
    if transition:
        adjacent = get_adjacent_dayun(parsed.dayun, dayun_step)
        if adjacent:
            found_in_adjacent = [
                c for c in needed_chars
                if c in (adjacent.干支.gan, adjacent.干支.zhi)
            ]

    all_found = found_in_current + found_in_adjacent
    if all_found:
        return LayerCheck(
            layer="L2_大运到位", passed=True, evidence_chars=all_found,
            rationale=f"大运{current}{'(过渡期)' if transition else ''}提供必需字: {all_found}"
        )
    return LayerCheck(
        layer="L2_大运到位", passed=False, evidence_chars=[],
        rationale=f"大运{current}未提供 domain 必需字"
    )
```

**过渡期惩罚**：在 `passed_layers` 计算时，若 L2 仅靠过渡期字通过，最终 `confidence.star` 强制再 -1（独立于变异度惩罚）。


---

## 五、L3 · 流年引爆（layer3_check）

> **本质**：流年是否对原局/大运的关键字构成 6 触发之一。

### 5.1 6 触发完整判定（任派 §17）

```python
def layer3_check(
    year: int, domain: str, energy: EnergyFindings,
    picture: PictureFindings, parsed: ParsedInput
) -> tuple[LayerCheck, list[TriggerEvent], Optional[TriggerEvent]]:
    liunian = liunian_ganzhi(year)
    triggers: list[TriggerEvent] = []

    # 触发 1：本字到（流年地支 = 原局某关键字）
    target_keys = get_primary_keys(domain, parsed.bazi, energy) + \
                  get_secondary_keys(domain, parsed.bazi, energy)
    for k in target_keys:
        if liunian.zhi == k or liunian.gan == k:
            triggers.append(TriggerEvent(
                type="本字到",
                description=f"流年{liunian}的{k}字 = 原局关键字",
                target_chars=[k]))

    # 触发 2：伏吟（流年柱 = 原局某柱）
    for palace in ["年柱","月柱","日柱","时柱"]:
        pillar: GanZhi = get_palace(parsed.bazi, palace)
        if liunian == pillar:
            triggers.append(TriggerEvent(
                type="伏吟",
                description=f"流年{liunian}与{palace}伏吟",
                target_chars=[liunian.gan, liunian.zhi]))

    # 触发 3：合冲引动（流年合/冲原局某柱地支）
    for palace_zhi in ["年支","月支","日支","时支"]:
        zhi = get_palace(parsed.bazi, palace_zhi)
        if zhi_liuhe(liunian.zhi, zhi) or zhi_chong(liunian.zhi, zhi) \
           or zhi_xing(liunian.zhi, zhi) or zhi_chuan(liunian.zhi, zhi):
            triggers.append(TriggerEvent(
                type="合冲引动",
                description=f"流年{liunian.zhi}与{palace_zhi}({zhi})合/冲/刑/穿",
                target_chars=[liunian.zhi, zhi]))

    # 触发 4：墓库开闭（流年地支为墓库 + 当年大运构成开/冲）
    if liunian.zhi in ["辰","戌","丑","未"]:
        dayun_step = get_dayun_at_year(parsed.dayun, parsed.birth["公历年"], year)
        if zhi_chong(liunian.zhi, dayun_step.干支.zhi):
            triggers.append(TriggerEvent(
                type="墓库开闭",
                description=f"流年{liunian.zhi}墓库被大运{dayun_step.干支.zhi}冲开",
                target_chars=[liunian.zhi]))

    # 触发 5：藏干透出（流年天干 = 原局某支藏干）
    for palace_zhi in ["年支","月支","日支","时支"]:
        zhi = get_palace(parsed.bazi, palace_zhi)
        cangs = get_canggan(zhi)
        if any(c.gan == liunian.gan for c in cangs):
            triggers.append(TriggerEvent(
                type="藏干透出",
                description=f"流年透出原局{palace_zhi}({zhi})藏干{liunian.gan}",
                target_chars=[liunian.gan]))

    # 触发 6：倒象成立（关键字同时被合+冲+刑/克 → 必凶）
    inverted = check_daoxiang(liunian, energy.tiyong.purpose, parsed.bazi)
    if inverted:
        triggers.append(TriggerEvent(
            type="倒象成立",
            description=f"用神{inverted.target}同时被{inverted.relations}, 倒象=必凶",
            target_chars=inverted.related_chars))

    primary = pick_primary_trigger(triggers, domain)
    passed = len(triggers) > 0
    return (LayerCheck(layer="L3_流年引爆", passed=passed,
                      evidence_chars=[t.target_chars for t in triggers],
                      rationale=f"{len(triggers)} 个触发: {[t.type for t in triggers]}"),
            triggers, primary)
```

### 5.2 6 触发的优先级（同年多触发时取主导）

```
优先级（高→低）：
  倒象成立 (必凶)        ← 强信号，凶性优先
  伏吟                   ← 第二强
  本字到 + 合冲引动      ← 双触发等价
  墓库开闭               ← 中等
  藏干透出               ← 中等
  单合/单冲              ← 弱（在合冲引动里已统计）
```

`pick_primary_trigger()` 按此优先级返回 `primary_trigger`。

---

## 六、综合判定 + 12 道门归属

```python
def gate_yingqi(year, candidate_event, domain, energy, picture, parsed) -> GateResult:
    l1 = layer1_check(domain, parsed, energy)
    l2 = layer2_check(year, domain, energy, parsed)
    l3, triggers, primary = layer3_check(year, domain, energy, picture, parsed)

    passed_layers = sum([l1.passed, l2.passed, l3.passed])

    # 上游约束校验
    energy_consistent = check_against_energy(candidate_event, domain, energy)
    picture_consistent = check_against_picture(candidate_event, domain, picture, year)
    if not picture_consistent:
        # 例：D2 marriage_picture.初婚年龄=23, 不能在 35 岁判"初婚"
        passed_layers = min(passed_layers, 1)

    # 12 道门归属
    door = classify_into_12_doors(triggers, domain, energy, picture, parsed)

    # 置信度（详见 06-confidence-model）
    confidence = compute_yingqi_confidence(
        passed_layers=passed_layers,
        triggers=triggers,
        l2_via_transition=l2_uses_transition(l2),
        upstream_consistent=energy_consistent and picture_consistent,
    )

    return GateResult(
        year=year, candidate_event=candidate_event, domain=domain,
        layer1=l1, layer2=l2, layer3=l3, passed_layers=passed_layers,
        triggers=triggers, primary_trigger=primary, door=door,
        confidence=confidence,
        energy_consistent=energy_consistent, picture_consistent=picture_consistent,
        evidence=collect_evidence(l1, l2, l3, triggers),
        upstream_energy_hash=findings_hash(energy),
        upstream_picture_hash=findings_hash(picture),
    )
```

### 6.1 12 道门分类规则（任派 §16）

```yaml
动门:
  trigger: 流年合冲引动且引动到关键宫位
  domains: [婚姻, 事业, 财运, 健康]

格局门:
  trigger: 流年破坏或成全原局格局
  domains: [事业, 财运]

天地门:
  trigger: 流年天干地支同时引动同一柱
  domains: [全]

统领门:
  trigger: 财统官 / 官统财 / 杀统财 等层次跃升
  domains: [事业, 财运]

墓库门:
  trigger: 触发=墓库开闭
  domains: [财运, 六亲, 健康]

夹拱门:
  trigger: 流年与原局形成夹/拱配置
  domains: [事业, 婚姻]

旬空门:
  trigger: 关键字落入年柱旬空
  domains: [六亲, 财运]

鸳鸯门:
  trigger: 配偶星与日干形成五合 + 流年引动
  domains: [婚姻]

寿元门:
  trigger: 日干被严重克泄 + 流年填实
  domains: [健康, 寿命]

伤残门:
  trigger: 刑冲落在身宫 + 神煞(羊刃/血刃/白虎)
  domains: [健康, 灾厄]

牢灾门:
  trigger: 七杀+羊刃+刑冲在年/月柱
  domains: [灾厄, 牢狱]
```

---

## 七、置信度等级映射（与 03-findings-schema § 七 一致）

```python
def confidence_ceiling_by_passed_layers(passed: int) -> int:
    """根据 passed_layers 给出 ★ 上限"""
    return {0: 0, 1: 3, 2: 4, 3: 5}[passed]
```

最终 `confidence.star = min(规律置信度上限, 三层 gate 上限) - 变异度惩罚 - 过渡期惩罚`。

详见 `06-confidence-model.md`。


---

## 八、回放：用三层门复核 C-2026-001 婚期

> 验证 v1.2 三层门是否能修正 v1.0 的失验。

**命盘**：庚申·戊寅·壬子·辛丑（壬日干，男）
**v1.0 预测**：婚期 2013 → **实际 2005 结婚**

### 8.1 v1.0 旧逻辑（无 gate）

仅看：2013 癸巳，杨派"流年与日支构合" + 任派"流年引动夫宫" → 综合 ★★★★ → 输出。

### 8.2 v1.2 新逻辑（三层 gate）

#### 候选 A：2005 乙酉
- **L1 原局有**：日支子（婚宫）✓ 配偶星正财（丁/T-paste 看丙丁）藏在月支寅 ✓ → **PASS**
- **L2 大运到位**：2005 在 18-27 岁庚辰运，辰=配偶星正财库的对冲字 ✓ → **PASS**
- **L3 流年引爆**：乙酉，酉与日支子无合无冲 ✗ ；但酉与年支申合 → 触发 3 合冲引动 ✓ → **PASS**
- `passed_layers = 3` → 允许 ★★★★★

#### 候选 B：2013 癸巳
- **L1 原局有**：✓
- **L2 大运到位**：2013 在 28-37 岁辛巳运，辛巳本运 ✓
- **L3 流年引爆**：癸巳，巳冲日柱时柱无关；与原局申支合（巳申合水）→ 触发 3 ✓
- `passed_layers = 3` → 也允许 ★★★★★

**问题**：两个候选都过门。

### 8.3 真正的修正：D2 PictureFindings 上游约束

D2 杨派 picture_matcher 在跑五步法时，会标记：

```yaml
picture.marriage_picture:
  初婚最佳窗口: [22, 28]    # 由 D2 计算（杨派"印来了+人来了"）
  早婚信号: 强               # D1 EnergyFindings 配偶星贴身 + 大运早期到位
```

D3 在做 picture_consistent 检查时：
- 2005 ∈ [22, 28] 窗口 ✓
- 2013 不在 [22, 28] 窗口 ✗ → `picture_consistent = False` → `passed_layers = min(3, 1) = 1`

**结论**：v1.2 在 D2 D3 的联合约束下，2005 ★★★★★，2013 ★★★。
**主输出**：2005，与实际一致。

### 8.4 这就是"三层门 + 上游约束"的力量

不仅是 D3 自检，还要：D1 给级别约束、D2 给画面约束、D3 才在画面允许的窗口里搜索应期。

**v1.0 失败的根因**：让 D3 自由搜索全时间轴，没有 D2 给的"早婚窗口"。

---

## 九、Domain-specific 注意事项

### 9.1 婚姻 Gate
- L1 配偶星缺则启用"无星借宫"豁免
- L3 必须含至少 1 个 `合冲引动` 或 `本字到` 或 `鸳鸯门`触发
- **picture_consistent 严校**（婚期窗口）

### 9.2 健康 Gate
- L1 优先看刑冲穿最重的支
- L3 倒象成立 = 直接 ★★★★★（任派"倒象=必凶"硬规律 MR-006）
- D4 高派的 health_findings.risk_years 作为额外加权（不算独立层）

### 9.3 财运 Gate
- L2 必须含财库相关字（辰戌丑未中含财方算）
- 统领门触发 = 层次跃升（如打工→老板）

### 9.4 事业 Gate
- L2 官星动 + L3 官星到 = 标准升迁
- L3 含"统领门" = 跨层级跃升

---

## 十、回归测试要求

`tests/yingqi/test_gate_replays.py` 必须包含：

| 测试 | 输入 | 期望输出 |
|---|---|---|
| C-2026-001 真婚期 | year=2005, domain=婚姻 | passed_layers=3, ★★★★★ |
| C-2026-001 旧错婚期 | year=2013, domain=婚姻 | passed_layers≤1（被 picture_consistent 拒）, ★★★ |
| C-2026-002 真婚期 | year=2005, domain=婚姻 | passed_layers≥2, ★★★★+ |
| C-2026-001 母亡 | year=2020, domain=六亲 | passed_layers=3, ★★★★★ |
| C-2026-001 提副科 | year=2020, domain=事业 | passed_layers=3, ★★★★★ |

每条 fail 都让 v1.2 不达 §I 发布门槛。

---

## 十一、版本演进

| 版本 | 变更 |
|---|---|
| 1.2.0 | 初版，三层门 + 6 触发 + 12 道门 + 上游约束 |

新增 trigger 类型 / 新增 door 类型必须：
1. PR 标记 `[GATE]`
2. 提供至少 1 个真实案例验证
3. 整合 agent 批准
4. tests/yingqi/ 新增对应单测

---

**契约结束。下一份请阅读 `05-rule-lifecycle.md`（W1.3 第 2 份）。**
