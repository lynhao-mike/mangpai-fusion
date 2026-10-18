# StructureCheck 语义校核报告 · 首批（OPUS 终审启动项）

> 日期：2026-10-17
> 依据：OPUS 5.5 终审「共存可以支持发现候选，不能自动证明有效生克」
> 方法：合成盘实测（`opus_probe3.py`，四柱直排精确构造）
> 结论性质：**行为事实记录 + 边界澄清建议**。未改任何 engine/ 代码（红线）。

---

## 一、实测发现（两条宽松入口的实锤）

### 1.1 阳刃驾杀（`ziping_qisha` 的 `xs_ren_he_sha`）

目录定义（structures_mvp.yaml:240-248）三条 any 路径：

```yaml
any:
  - {pred: has_edge, kind: wuhe, from_role: 劫财, to_role: 七杀}
  - {pred: month_branch_is, mark: 阳刃}      # ← 问题路径
  - {pred: day_master_sits_on, mark: 坐羊刃} # ← 问题路径
```

实测对照：

| 盘面 | 月支 | 天干七杀 | `xs_ren_he_sha` | 证据 |
|---|---|---|---|---|
| 甲辰 丁卯 甲寅 庚午 | 卯（甲刃） | 庚（有） | **met** | 仅 `M.b` |
| 甲辰 丁卯 甲寅 丁卯 | 卯（甲刃） | 无 | **met** | 仅 `M.b` |

**事实**：有杀无杀，结果完全相同——只要月支是刃就 `met`。
「驾杀」这个动作（刃合杀/刃制杀）在无杀时无从发生。

### 1.2 财生官（`ziping_zhengguan` 的 `aux_cai_sheng_guan`）

```yaml
any:
  - {pred: has_edge, kind: sheng, from_role: 财, to_role: 正官}
  - {pred: coexist, role_a: 财, role_b: 正官}   # ← 问题路径
```

实测：辛丑 庚寅 辛巳 甲午（财透时干、官藏月支，**无生边**）
→ `aux_cai_sheng_guan = met`，证据 `H.s, M.b, D.b` 纯共存地址，无一条 sheng 边。

**事实**：`coexist` 路径命中即 `met`，是否真「生」不参与判定。

---

## 二、边界澄清（按 OPUS 裁定，不动代码）

这两条是**候选筛选入口**（candidate filter）：「材料在盘上」的宽口径发现。
它们**不是**「要件满足」（requirement satisfied）：不宣称生官/制杀已生效。

设计上这个区分是自洽的：
- `structure_check.py` 模块 docstring 明言「凡涉及力量对比一律 needs_judgment，
  交调用方裁决」「刻意不输出成格/破格结论」；
- `strength_judgment` 谓词恒返 `needs_judgment`。

**缺口在消费端语义**：`CheckItem.status="met"` 对 kind=requirement 的条目
（如 `xs_ren_he_sha` 的 text 是「相神：阳刃合杀/驾杀」）读起来就是
「相神已成立」。宽口径命中 + 断语式条目文本 = 误读温床。

## 三、给消费方（裁决层/报告层）的使用规则

1. **`met` 只能表述为「候选成立/材料在盘」**，不得表述为「生官已成立/
   制杀已成立」。推荐措辞：`xs_ren_he_sha 候选成立（刃位在盘；是否成驾待裁决）`。
2. **区分证据形态**：证据里出现 Edge.id → 有真实作用边；只有 Addr → 仅共存/位置。
   报告引用时应注明（「刃位在盘」vs「刃合杀边 e014」是两种强度完全不同的依据）。
3. **`judgment: true` 条目**（如 `brk_cai_zi_sha`）已按设计转 `needs_judgment`，
   这是对的；同类「力量语义」条目（驾杀、生官）建议后续同样标注。

## 四、后续目录扩充的准入标准（OPUS 四条，全文收录）

- 能用已有确定性事实、现有组合表达：直接组合。
- 定义明确、可返回事实地址、可独立检查的事实缺口：允许增加小谓词，
  即使暂时只有一个高价值调用方。
- 涉及力量、有效性、适用域权衡：返回待裁决，保留事实证据。
- 原文含义或缺项语义尚未明确：暂缓自动化，列明缺少什么。

**本次新增目录条目：0 条。** 首批按 OPUS 要求「先校核语义、再扩目录」执行，
两条宽松入口的边界已查明并书面化；是否把 `xs_ren_he_sha`/`aux_cai_sheng_guan`
改为 `judgment: true`（命中即转 needs_judgment），属 engine/ 代码变更，留待
项目所有者裁决（改动一行 `judgment: true`，附测试更新，工作量极小）。

## 五、复现方式

```bash
python .workbuddy-ai/opus_probe3.py
```

探针为一次性诊断脚本，不入仓库主线；本报告为持久交付物。
