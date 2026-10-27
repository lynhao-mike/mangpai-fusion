# T-145 · 岁运 4 原子 + 力量比较原子（兑现「能预测」）

- 状态：🔵 Ready for Execution
- 优先级：P1（但它是「能否预测」的唯一通道）
- 创建：2026-10-27（中枢）
- 决策依据：ADR-007 D3 / D4
- **前置：T-142 必须已完成并合入**（同改 `atoms.py`，同一文件同一时刻只许一个写任务）

## 1. 背景

42 个原子里管岁运的只有 5 个，其中 **3 个是空壳**：

- `atoms.py:558` `suiyun_edge` → 恒返回 `_u("岁运关系边未接入（pilot 不启用）")`
- `atoms.py:562` `sanhe_with_suiyun` → 恒返回 `_u(...)`
- `atoms.py:566` `chong_kai_muku` → 恒返回 `_u(...)`

且**没有任何比较力量的原子**。所以系统能说「婚姻怎样」，**说不出「哪一年」**，也答不了段派最核心的「制得住/制不住」。

**好消息**：岁运建边**已经存在**。`engine/facts/relation_graph.py:85` 的 `_nodes(chart, dayun_index, liunian_year)` 已生成 `DY{n}.s/b`、`LN{year}.s/b` 节点及 `scope ∈ {natal, dayun, liunian, dayun+liunian}` 的全部关系边（含天干五合/冲/生克、地支六冲/六合/穿/刑/破/暗合、以及与岁运共同构成的三合/三会）。

所以本卡的工作是**接线**，不是重建。

## 2. 要做的事

### ① 实装 3 个空壳岁运原子

前提：T-142 已给原局原子加了 `scope == "natal"` 隔离。本卡让岁运原子**专门**消费 `scope != "natal"` 的边。

- `suiyun_edge(type, at, scope?)`：在 `ctx["edges"]` 中找 `e["kind"] == type`、`at in e["members"]`、且 `e.get("scope","natal") != "natal"` 的边。若传 `scope` 则精确匹配 `dayun` / `liunian` / `dayun+liunian`。命中返回 `_t` 并绑定 `edge_id`。
- `sanhe_with_suiyun(zhi_set?)`：找 `kind ∈ {sanhe, sanhui}` 且 `completeness == "full"` 且 `scope != "natal"` 的边。
- `chong_kai_muku(zhi?, year?)`：检查原局墓库（`ctx["muku"]`，按 `zhi` 过滤）的 `addr` 是否被 `scope ∈ {dayun, liunian}` 且 `kind ∈ {chong, xing}` 的边触及。

### ② 新增 `suiyun_arrives(at, via?)`（段派「到位」）

原文（`theory/raw/duan/d01-deep-read.md:290-306`，M1-D-042/043）讲「到位」：原局所藏之干在运年天干透出，或原局天干在运年地支见禄。

**要求**：查原文确认判据后再实现，不许凭常识写。凡原文无据的部分，不实现，在 BRIEF 里标明。

### ③ 新增 `can_control(actor, target)` —— 三值力量比较

**这是段派的核心判据：制得住 / 制不住。**

原文（`sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md:1759`）：
> 「冲神之旺衰判断，**以多则为旺，寡则为衰；以合局会局为旺，以孤立受克为衰；以得令为旺，以失令为衰**。」

原文（`theory/raw/duan/d01-deep-read.md:191-196`，12 种党势）：木火一党、金水一党、水木一党、火与燥土一党、金与湿土一党、水与湿土一党。

原文（同书 `:1844`、`:1850`）：「戌辰**力量相当，互相制不了**」/「原局金水党和火土党对抗，**谁也制不了谁**」。

**代码铁律**（`engine/facts/structure_check.py:276`）：「力量对比不由代码裁决：恒为 `needs_judgment`，附日主与相关角色的地址及其通根地址。」

**设计要求（严格遵守）**：
- **True**：actor 满足至少 2 项强势条件（得令 / 有本气或中气强根或成三合三会局 / 同党字数 ≥3），**且** target 失令、无强根或根被坏、不成党。
- **False**：target 强旺成党得令有强根，而 actor 虚浮无根失令。
- **unknown**：双方均有根气，或两党对抗（力量相当）。note **必须**附双方根气与党势明细，格式自定但要可读。
- **禁止**用单一数值阈值一刀切判全部盘面。若你用了任何计数型阈值（如「同党 ≥3 字」），**必须在 BRIEF 里标注为工程取值，不是原文数值**。

### ④ 三值语义（不要引入第四种真值）

- `dayun_present` / `liunian_present`：未提供岁运时返回 **False**（「未提供」是客观输入事实）。
- `suiyun_edge` / `sanhe_with_suiyun` / `chong_kai_muku`：未提供岁运时返回 **unknown**，note 写「未提供大运/流年上下文」，使 `state = needs_fact`，让 Agent 追问。
- **不要**引入「不适用」这个第四值。只问原局时，由外层按 `time_window == "natal"` 过滤断语集合。

## 3. File Scope

- `engine/claims/condition_ir/atoms.py`
- `engine/contracts/23-claim-condition-protocol-v1.md`（原子表）
- 对应测试（`tests/claims/`）

**禁止**：改 `engine/facts/`（如需改，先报告）、`engine/api/facade.py`、`theory/claims/**`、`theory/_ir/`、`sources/`、`pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.verify_baseline
```

**必须自证（关键）**：
1. **标杆盘 A（制得住）**：`坤造 癸丑 癸亥 辛亥 癸巳` —— 段派判「伤官亥冲巳，冲去夫星忌神，婚姻好」。给出 `can_control` 对相关两端的三值结果与理由。
2. **标杆盘 B（制不住）**：原文对照组「壬子 乙巳 庚子 壬午」—— 段派判「水火力量相当，制不住夫星」。`can_control` 必须返回 **unknown**，note 说明双方力量相当。
   > 这两张盘是检验本卡成败的唯一标准。若 A 判 unknown 而 B 判 True，说明模型方向错了，**停下报告**，不要调阈值去凑。
3. 岁运原子：对同一盘传入 `liunian_year=2027`，`suiyun_edge` 能命中岁运边并绑定 `edge_id`；不传时返回 unknown 且 note 正确。
4. 原局原子隔离仍在（T-142 的成果未被破坏）。

## 5. 回报格式

4 个岁运原子 + `can_control` 各自的签名与语义；原文依据的逐条引用（含行号）；两张标杆盘的实际输出与判定理由；「工程取值 vs 原文数值」的区分清单；两条验收命令的数字与退出码。
