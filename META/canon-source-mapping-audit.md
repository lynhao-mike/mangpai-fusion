# Canon Source Mapping Audit

生成时间：2026-06-12（Asia/Shanghai）

## 1. 审计结论

**明确结论：当前系统不是 A「《子平真诠》 + 《滴天髓》」的双经典系统，而是 B「子平派专家系统 + 滴天髓调候派专家系统」。**

证据：

- 子平生产规则的 canon 覆盖 `ZIPING_ZHENQUAN`、`SANMING_TONGHUI`、`QIONGTONG_BAOJIAN` 三类经典来源，而非仅 `ZIPING_ZHENQUAN`。
- 滴天髓调候生产规则的 canon 覆盖 `DITIANSUI` 与 `DITIANSUI_CHANWEI`，大量规则来自任铁樵《滴天髓阐微》，而非仅《滴天髓》原文。
- 两个规则文件的 `expert_system` 分别为 `ziping` 与 `tiaohou_ditiansui`，其规则主题、触发条件与应用域均按专家系统组织，而不是按单本经典组织。
- 因此较准确的产品表述应为：**以子平派多经典来源为规则底座的子平专家系统 + 以《滴天髓》原文及《滴天髓阐微》为规则底座的调候/气势专家系统**。

## 2. 审计范围与字段口径

审计文件：

- `theory/ziping/index.yaml`：`expert_system=ziping`，生产规则数 `57`。
- `theory/tiaohou_ditiansui/index.yaml`：`expert_system=tiaohou_ditiansui`，生产规则数 `255`。

合计生产规则数：`312`。

字段口径：

- `rule_id`：读取规则 `id`。
- `school`：读取规则级 `expert_system`，缺省时使用文件级 `expert_system`。
- `source_book`：读取 `source.path`；若未来出现多路径，使用分号拼接。
- `canon`：仅按限定枚举归类，优先依据 `source.path`，不因摘要文本含义扩展。
- `family`：当前规则未见显式 `family` 字段，本审计按 `topic` 作为 family 代理，不回写、不改 schema。
- `rule_type`：当前规则未见显式 `rule_type` 字段，本审计按 `conditions.trigger` 作为 rule_type 代理，不回写、不改 schema。

canon 映射规则：

| source.path 特征 | canon |
|---|---|
| `《子平真诠》` | `ZIPING_ZHENQUAN` |
| `三命通会` | `SANMING_TONGHUI` |
| `穷通宝鉴` | `QIONGTONG_BAOJIAN` |
| `滴天髓_part` | `DITIANSUI` |
| `滴天髓阐微` | `DITIANSUI_CHANWEI` |
| 多个来源路径跨 canon | `MIXED_SOURCE` |
| 无法识别或缺 source | `UNKNOWN` |

## 3. Canon 汇总统计

| canon | source_book | 规则数 | family 数 |
|---|---|---:|---:|
| `ZIPING_ZHENQUAN` | 《子平真诠》 | 18 | 18 |
| `SANMING_TONGHUI` | 《三命通会》 | 12 | 12 |
| `QIONGTONG_BAOJIAN` | 《穷通宝鉴》 | 27 | 27 |
| `DITIANSUI` | 《滴天髓》 | 41 | 41 |
| `DITIANSUI_CHANWEI` | 《滴天髓阐微》 | 214 | 184 |

## 4. Canon × rule_type 分布

### 4.1 `ZIPING_ZHENQUAN`

| rule_type（conditions.trigger 代理） | 规则数 |
|---|---:|
| `has_wealth_picture` | 7 |
| `has_marriage_picture` | 6 |
| `always` | 3 |
| `has_official_picture` | 2 |

### 4.2 `SANMING_TONGHUI`

| rule_type（conditions.trigger 代理） | 规则数 |
|---|---:|
| `has_wealth_picture` | 5 |
| `has_official_picture` | 3 |
| `has_zhi_chong` | 3 |
| `has_marriage_picture` | 1 |

### 4.3 `QIONGTONG_BAOJIAN`

| rule_type（conditions.trigger 代理） | 规则数 |
|---|---:|
| `has_wealth_picture` | 14 |
| `always` | 12 |
| `has_marriage_picture` | 1 |

### 4.4 `DITIANSUI`

| rule_type（conditions.trigger 代理） | 规则数 |
|---|---:|
| `always` | 14 |
| `has_marriage_picture` | 10 |
| `has_wealth_picture` | 8 |
| `has_zhi_chong` | 5 |
| `has_official_picture` | 2 |
| `has_tiaohou_advice` | 2 |

### 4.5 `DITIANSUI_CHANWEI`

| rule_type（conditions.trigger 代理） | 规则数 |
|---|---:|
| `has_wealth_picture` | 58 |
| `has_official_picture` | 48 |
| `always` | 43 |
| `has_marriage_picture` | 33 |
| `has_zhi_chong` | 18 |
| `has_tiaohou_advice` | 14 |

## 5. Canon × source_book 分布

### `ZIPING_ZHENQUAN`

| source_book | 规则数 |
|---|---:|
| `sources/ziping/《子平真诠》.md` | 18 |

### `SANMING_TONGHUI`

| source_book | 规则数 |
|---|---:|
| `sources/ziping/《三命通会》.md` | 12 |

### `QIONGTONG_BAOJIAN`

| source_book | 规则数 |
|---|---:|
| `sources/ziping/穷通宝鉴-明-余春台_part1.md` | 14 |
| `sources/ziping/穷通宝鉴-明-余春台_part2.md` | 13 |

### `DITIANSUI`

| source_book | 规则数 |
|---|---:|
| `sources/tiaohou_ditiansui/滴天髓_part1.md` | 19 |
| `sources/tiaohou_ditiansui/滴天髓_part2.md` | 12 |
| `sources/tiaohou_ditiansui/滴天髓_part3.md` | 10 |

### `DITIANSUI_CHANWEI`

| source_book | 规则数 |
|---|---:|
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | 50 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | 44 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | 37 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | 26 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | 21 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | 20 |
| `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | 16 |

## 6. TOP 风险

### A. `MIXED_SOURCE` 规则

- 未发现 `source.path` 跨多个 canon 的生产规则。

### B. `UNKNOWN` 规则

- 未发现缺失来源或无法映射 canon 的生产规则。

### C. 一个规则引用多个经典的情况

- 未发现同一规则在 `source.path`、`source.excerpt` 或 `review.notes` 中明确同时引用多个经典。

风险解读：

- 当前审计按生产规则自身记录的 `source.path` 看，来源归属整体清晰，未发现 `MIXED_SOURCE` 与 `UNKNOWN`。
- 主要结构性风险不是“找不到来源”，而是**命名误读风险**：若对外称作《子平真诠》+《滴天髓》，会掩盖 `SANMING_TONGHUI`、`QIONGTONG_BAOJIAN`、`DITIANSUI_CHANWEI` 的实际规则占比。
- 另一个风险是字段语义风险：生产规则当前未显式提供 `family` 与 `rule_type` 字段，本报告只能使用 `topic` 与 `conditions.trigger` 作为代理统计。

## 7. 全量 rule_id → canon 映射

| rule_id | school | source_book | canon | family(topic 代理) | rule_type(trigger 代理) |
|---|---|---|---|---|---|
| `ZP-PROD-20260605-001` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `yongshen` | `has_wealth_picture` |
| `ZP-PROD-20260605-002` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `wealth_structure` | `has_wealth_picture` |
| `ZP-PROD-20260605-003` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `yongshen_month_branch` | `has_wealth_picture` |
| `ZP-PROD-20260605-004` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `shenqiang_shenruo` | `has_wealth_picture` |
| `ZP-PROD-20260605-005` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `yongshen_success_failure` | `has_marriage_picture` |
| `ZP-PROD-20260605-006` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `jiuying` | `has_marriage_picture` |
| `ZP-PROD-20260605-007` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `geju_chunza` | `has_wealth_picture` |
| `ZP-PROD-20260605-008` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `yongshen_youqing` | `has_marriage_picture` |
| `ZP-PROD-20260605-009` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `tiaohou_priority` | `always` |
| `ZP-PROD-20260605-010` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `xiangshen` | `has_marriage_picture` |
| `ZP-PROD-20260605-011` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `sijishen` | `has_wealth_picture` |
| `ZP-PROD-20260605-012` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `sixiongshen_zhihua` | `always` |
| `ZP-PROD-20260605-013` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `zhengguan_ge` | `has_official_picture` |
| `ZP-PROD-20260605-014` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `special_geju` | `has_wealth_picture` |
| `ZP-PROD-20260605-015` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `geju_level_composite` | `has_marriage_picture` |
| `ZP-PROD-20260605-016` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `timing_transformation` | `has_marriage_picture` |
| `ZP-PROD-20260605-017` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `wealth_official_quantity` | `has_official_picture` |
| `ZP-PROD-20260605-018` | `ziping` | `sources/ziping/《子平真诠》.md` | `ZIPING_ZHENQUAN` | `geju_index` | `always` |
| `ZP-PROD-20260606-001` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `wuxing_ganzhi_framework` | `has_wealth_picture` |
| `ZP-PROD-20260606-002` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `yueling_tigang` | `has_wealth_picture` |
| `ZP-PROD-20260606-003` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `he_chong_xing_hai` | `has_zhi_chong` |
| `ZP-PROD-20260606-004` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `shishen_by_strength` | `has_official_picture` |
| `ZP-PROD-20260606-005` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `tong_yueqi_yituo` | `has_wealth_picture` |
| `ZP-PROD-20260606-006` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `lugui_shizhu` | `has_wealth_picture` |
| `ZP-PROD-20260606-007` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `ku_key_open` | `has_zhi_chong` |
| `ZP-PROD-20260606-008` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `rishi_shizhu` | `has_official_picture` |
| `ZP-PROD-20260606-009` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `shangguan_official` | `has_official_picture` |
| `ZP-PROD-20260606-010` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `special_geju_authenticity` | `has_wealth_picture` |
| `ZP-PROD-20260606-011` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `yunshi_geju_change` | `has_marriage_picture` |
| `ZP-PROD-20260606-012` | `ziping` | `sources/ziping/《三命通会》.md` | `SANMING_TONGHUI` | `xingchong_liuqin_zixi` | `has_zhi_chong` |
| `ZP-PROD-20260606-013` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `wuxing_zhongdao` | `has_wealth_picture` |
| `ZP-PROD-20260606-014` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `wuxing_laitu_zaihua` | `has_wealth_picture` |
| `ZP-PROD-20260606-015` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `mu_shuisheng_piaoliu` | `always` |
| `ZP-PROD-20260606-016` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `chunmu_huoshui_xiangji` | `always` |
| `ZP-PROD-20260606-017` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `jiamu_hanmu_xiangyang` | `has_wealth_picture` |
| `ZP-PROD-20260606-018` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `shuifan_mufu_wuji` | `always` |
| `ZP-PROD-20260606-019` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `xiamu_shuirun_jihuowang` | `always` |
| `ZP-PROD-20260606-020` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `qiujiamu_dinggeng_chengcai` | `has_wealth_picture` |
| `ZP-PROD-20260606-021` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `dongjiamu_dinggeng_bingzuo` | `always` |
| `ZP-PROD-20260606-022` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `yimu_binggui` | `has_marriage_picture` |
| `ZP-PROD-20260606-023` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `binghuo_renshui_jiji` | `always` |
| `ZP-PROD-20260606-024` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `dinghuo_jiayin_gengpi` | `has_wealth_picture` |
| `ZP-PROD-20260606-025` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `tuju_tuzhi_shuimu` | `has_wealth_picture` |
| `ZP-PROD-20260606-026` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part1.md` | `QIONGTONG_BAOJIAN` | `wutu_bingjiagui` | `has_wealth_picture` |
| `ZP-PROD-20260606-027` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `xiaji_gui_bing` | `has_wealth_picture` |
| `ZP-PROD-20260606-028` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `qiuji_gui_bing` | `has_wealth_picture` |
| `ZP-PROD-20260606-029` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `dongji_binghuo` | `has_wealth_picture` |
| `ZP-PROD-20260606-030` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `jinhuo_chengqi` | `always` |
| `ZP-PROD-20260606-031` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `jinju_shuihuotu` | `always` |
| `ZP-PROD-20260606-032` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `jin_chengqi_zaihuo` | `always` |
| `ZP-PROD-20260606-033` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `chunjin_huotu` | `always` |
| `ZP-PROD-20260606-034` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `gengjin_yueling_quyong` | `has_wealth_picture` |
| `ZP-PROD-20260606-035` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `gengjin_maihan` | `has_wealth_picture` |
| `ZP-PROD-20260606-036` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `xinjin_jiren` | `always` |
| `ZP-PROD-20260606-037` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `shuiju_jinyuan_tudi` | `has_wealth_picture` |
| `ZP-PROD-20260606-038` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `renshui_yueling` | `has_wealth_picture` |
| `ZP-PROD-20260606-039` | `ziping` | `sources/ziping/穷通宝鉴-明-余春台_part2.md` | `QIONGTONG_BAOJIAN` | `guishui_xinbing` | `always` |
| `DTS-PROD-20260605-001` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `zhonghe_pianku` | `always` |
| `DTS-PROD-20260605-002` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `chong_dong` | `has_zhi_chong` |
| `DTS-PROD-20260605-003` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `sanyuan` | `has_wealth_picture` |
| `DTS-PROD-20260605-004` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `pianku_pianquan` | `always` |
| `DTS-PROD-20260605-005` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `shunni` | `has_marriage_picture` |
| `DTS-PROD-20260605-006` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `wangshuai_jintui` | `always` |
| `DTS-PROD-20260605-007` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `yongshen_functional` | `has_marriage_picture` |
| `DTS-PROD-20260605-008` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `fuyi_quliu` | `has_wealth_picture` |
| `DTS-PROD-20260605-009` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `ganzhi_flow` | `has_marriage_picture` |
| `DTS-PROD-20260605-010` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `yinyang_shiling` | `always` |
| `DTS-PROD-20260605-011` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `chong_strength` | `has_zhi_chong` |
| `DTS-PROD-20260605-012` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `chong_de令_strength` | `has_zhi_chong` |
| `DTS-PROD-20260605-013` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `zhonghe_vs_qiyi` | `always` |
| `DTS-PROD-20260605-014` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `yongshen_cross_category` | `has_marriage_picture` |
| `DTS-PROD-20260605-015` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `season_strength` | `always` |
| `DTS-PROD-20260605-016` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `shunni_vs_strength` | `has_marriage_picture` |
| `DTS-PROD-20260605-017` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `jintui_dynamic` | `always` |
| `DTS-PROD-20260605-018` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `falsifiable_application` | `always` |
| `DTS-PROD-20260605-019` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part1.md` | `DITIANSUI` | `chong_quji_jiji` | `has_zhi_chong` |
| `DTS-PROD-20260606-001` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `han暖_shengji` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-002` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `zaoshi_balance` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-003` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `yinxian_jixiong` | `has_marriage_picture` |
| `DTS-PROD-20260606-004` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `zhonggua_shili` | `has_wealth_picture` |
| `DTS-PROD-20260606-005` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `zhendui_seasonal_strategy` | `always` |
| `DTS-PROD-20260606-006` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `kanli_shengjiang` | `has_zhi_chong` |
| `DTS-PROD-20260606-007` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `hezhi_index` | `always` |
| `DTS-PROD-20260606-008` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `yuanshen_shouyao` | `always` |
| `DTS-PROD-20260606-009` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `female_fuxing_qingzhuo` | `has_marriage_picture` |
| `DTS-PROD-20260606-010` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `child_qishi_yangcheng` | `always` |
| `DTS-PROD-20260606-011` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `congxiang_types` | `has_wealth_picture` |
| `DTS-PROD-20260606-012` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part2.md` | `DITIANSUI` | `huaxiang_huashen` | `has_marriage_picture` |
| `DTS-PROD-20260606-013` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `jiacong_zhenyun` | `has_wealth_picture` |
| `DTS-PROD-20260606-014` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `jiacong_fencai_fenguan` | `has_official_picture` |
| `DTS-PROD-20260606-015` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `jiacong_yuanzhuoliuqing` | `has_wealth_picture` |
| `DTS-PROD-20260606-016` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `jiahua_zaxiang` | `has_marriage_picture` |
| `DTS-PROD-20260606-017` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `jiahua_suiyun_fuzhen` | `has_marriage_picture` |
| `DTS-PROD-20260606-018` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `shunju_shishang_shengcai` | `has_wealth_picture` |
| `DTS-PROD-20260606-019` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `shunju_ji_yinguan` | `has_official_picture` |
| `DTS-PROD-20260606-020` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `fanju_junlai_chensheng` | `has_wealth_picture` |
| `DTS-PROD-20260606-021` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `erneng_jiumu_shihou` | `always` |
| `DTS-PROD-20260606-022` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓_part3.md` | `DITIANSUI` | `muci_miezi` | `always` |
| `DTS-PROD-20260606-023` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `sanyuan_ganzhi_canggan` | `has_wealth_picture` |
| `DTS-PROD-20260606-024` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `shunbei_ganzhi` | `has_marriage_picture` |
| `DTS-PROD-20260606-025` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `zhonghe_pingzheng` | `always` |
| `DTS-PROD-20260606-026` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `wuzhi_yongshen_fanshensha` | `has_marriage_picture` |
| `DTS-PROD-20260606-027` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `yongshen_buju_mingmu` | `has_marriage_picture` |
| `DTS-PROD-20260606-028` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `wangxiang_xiuqiu_jintui` | `always` |
| `DTS-PROD-20260606-029` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `shigan_fan_jixieleixiang` | `always` |
| `DTS-PROD-20260606-030` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `jiamu_chenglong_qihu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-031` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `binghuo_jirenxin` | `always` |
| `DTS-PROD-20260606-032` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `dizhi_chongdong_fenlei` | `has_zhi_chong` |
| `DTS-PROD-20260606-033` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `xinghai_po_shengke` | `has_marriage_picture` |
| `DTS-PROD-20260606-034` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `anchong_anhui_biwo` | `has_zhi_chong` |
| `DTS-PROD-20260606-035` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `wangshuai_chong` | `has_zhi_chong` |
| `DTS-PROD-20260606-036` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `tianfu_dizai` | `has_wealth_picture` |
| `DTS-PROD-20260606-037` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `shizhong_desuo` | `has_wealth_picture` |
| `DTS-PROD-20260606-038` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md` | `DITIANSUI_CHANWEI` | `liangqi_chengxiang` | `has_wealth_picture` |
| `DTS-PROD-20260606-039` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `shengju_shiqi` | `has_wealth_picture` |
| `DTS-PROD-20260606-040` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `wuqi_chengxing` | `has_wealth_picture` |
| `DTS-PROD-20260606-041` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `sui_yun_bucheng` | `has_wealth_picture` |
| `DTS-PROD-20260606-042` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `duxiang_huashen` | `has_wealth_picture` |
| `DTS-PROD-20260606-043` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `duxiang_hexuang` | `has_wealth_picture` |
| `DTS-PROD-20260606-044` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `quanxiang_cai` | `has_wealth_picture` |
| `DTS-PROD-20260606-045` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `xishen_zuhe` | `has_official_picture` |
| `DTS-PROD-20260606-046` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `xingquan_xingque` | `has_wealth_picture` |
| `DTS-PROD-20260606-047` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `xieshang_bangzhu` | `always` |
| `DTS-PROD-20260606-048` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `fangju_hunju` | `always` |
| `DTS-PROD-20260606-049` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `fangju_tiangan` | `has_wealth_picture` |
| `DTS-PROD-20260606-050` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `chengfang_congqiang` | `has_wealth_picture` |
| `DTS-PROD-20260606-051` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `bage_quyong` | `has_marriage_picture` |
| `DTS-PROD-20260606-052` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `zhengli_waige` | `has_wealth_picture` |
| `DTS-PROD-20260606-053` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `geju_bingyao` | `has_wealth_picture` |
| `DTS-PROD-20260606-054` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `tiyong_xingqi` | `always` |
| `DTS-PROD-20260606-055` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `wangji_ruoji` | `has_wealth_picture` |
| `DTS-PROD-20260606-056` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `jingshenqi` | `always` |
| `DTS-PROD-20260606-057` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `yueling_tigang` | `has_marriage_picture` |
| `DTS-PROD-20260606-058` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `shizhu_guishu` | `always` |
| `DTS-PROD-20260606-059` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `shuaiwang_sifa` | `has_wealth_picture` |
| `DTS-PROD-20260606-060` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `genqi_bijian` | `has_wealth_picture` |
| `DTS-PROD-20260606-061` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `taiwang_tairuo` | `has_wealth_picture` |
| `DTS-PROD-20260606-062` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `zhonghe_bingyao` | `has_wealth_picture` |
| `DTS-PROD-20260606-063` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `yuanliu` | `has_marriage_picture` |
| `DTS-PROD-20260606-064` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md` | `DITIANSUI_CHANWEI` | `tongguan` | `has_zhi_chong` |
| `DTS-PROD-20260606-065` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `tongguan_shayin` | `has_official_picture` |
| `DTS-PROD-20260606-066` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `guansha_hunza` | `has_official_picture` |
| `DTS-PROD-20260606-067` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `quguan_qusha` | `has_official_picture` |
| `DTS-PROD-20260606-068` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `cai_zi_ruosha` | `has_official_picture` |
| `DTS-PROD-20260606-069` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shazhong_yinyin` | `has_official_picture` |
| `DTS-PROD-20260606-070` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shishen_zhisha` | `has_official_picture` |
| `DTS-PROD-20260606-071` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `heguan_liusha` | `has_official_picture` |
| `DTS-PROD-20260606-072` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `guansha_zuoyin` | `has_official_picture` |
| `DTS-PROD-20260606-073` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `zhisha_taiguo` | `has_official_picture` |
| `DTS-PROD-20260606-074` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shangguan_jianguan` | `has_official_picture` |
| `DTS-PROD-20260606-075` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shangguan_yongyin_yongcai` | `has_official_picture` |
| `DTS-PROD-20260606-076` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shangguan_fenxing` | `has_official_picture` |
| `DTS-PROD-20260606-077` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `jia_shangguan` | `has_official_picture` |
| `DTS-PROD-20260606-078` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `shangguan_yongshen_sun` | `has_zhi_chong` |
| `DTS-PROD-20260606-079` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `qingqi` | `has_wealth_picture` |
| `DTS-PROD-20260606-080` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `chengzhuo_qiuqing` | `has_zhi_chong` |
| `DTS-PROD-20260606-081` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `zhuoqi_fenlei` | `has_wealth_picture` |
| `DTS-PROD-20260606-082` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `qingku` | `always` |
| `DTS-PROD-20260606-083` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `zhenshen` | `has_wealth_picture` |
| `DTS-PROD-20260606-084` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md` | `DITIANSUI_CHANWEI` | `jiashen_deju` | `has_wealth_picture` |
| `DTS-PROD-20260606-085` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `jiashen_deju` | `has_wealth_picture` |
| `DTS-PROD-20260606-086` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `jiashen_deju` | `has_wealth_picture` |
| `DTS-PROD-20260606-087` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `gangrou_zhihua` | `always` |
| `DTS-PROD-20260606-088` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `gangrou_zhihua` | `has_wealth_picture` |
| `DTS-PROD-20260606-089` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `wangshuai_quyong` | `has_wealth_picture` |
| `DTS-PROD-20260606-090` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `shunni` | `has_wealth_picture` |
| `DTS-PROD-20260606-091` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `shunni` | `has_marriage_picture` |
| `DTS-PROD-20260606-092` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `shunni` | `has_wealth_picture` |
| `DTS-PROD-20260606-093` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `han暖_tiaohou` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-094` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `han暖_tiaohou` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-095` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `dizhi_chong` | `has_zhi_chong` |
| `DTS-PROD-20260606-096` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zaoshi_tiaohou` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-097` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zaoshi_tiaohou` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-098` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `yinxian` | `has_marriage_picture` |
| `DTS-PROD-20260606-099` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `yinxian` | `has_marriage_picture` |
| `DTS-PROD-20260606-100` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhonggua` | `has_wealth_picture` |
| `DTS-PROD-20260606-101` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhonggua` | `has_wealth_picture` |
| `DTS-PROD-20260606-102` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `always` |
| `DTS-PROD-20260606-103` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `always` |
| `DTS-PROD-20260606-104` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `has_wealth_picture` |
| `DTS-PROD-20260606-105` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-106` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `always` |
| `DTS-PROD-20260606-107` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `zhendui` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-108` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `has_wealth_picture` |
| `DTS-PROD-20260606-109` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `always` |
| `DTS-PROD-20260606-110` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `has_wealth_picture` |
| `DTS-PROD-20260606-111` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `always` |
| `DTS-PROD-20260606-112` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `has_wealth_picture` |
| `DTS-PROD-20260606-113` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `kanli` | `has_wealth_picture` |
| `DTS-PROD-20260606-114` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_fuqi` | `has_marriage_picture` |
| `DTS-PROD-20260606-115` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_fuqi` | `has_official_picture` |
| `DTS-PROD-20260606-116` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_fuqi` | `has_marriage_picture` |
| `DTS-PROD-20260606-117` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_zinv` | `always` |
| `DTS-PROD-20260606-118` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_zinv` | `always` |
| `DTS-PROD-20260606-119` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_zinv` | `has_official_picture` |
| `DTS-PROD-20260606-120` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_zinv` | `always` |
| `DTS-PROD-20260606-121` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_fumu` | `has_official_picture` |
| `DTS-PROD-20260606-122` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_fumu` | `has_zhi_chong` |
| `DTS-PROD-20260606-123` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_xiongdi` | `has_wealth_picture` |
| `DTS-PROD-20260606-124` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `liuqin_xiongdi` | `has_official_picture` |
| `DTS-PROD-20260606-125` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `caiqi_tongmenhu` | `has_wealth_picture` |
| `DTS-PROD-20260606-126` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `caiqi_tongmenhu` | `has_official_picture` |
| `DTS-PROD-20260606-127` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `guanxing_lihui` | `has_official_picture` |
| `DTS-PROD-20260606-128` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `guansha_hunza` | `has_official_picture` |
| `DTS-PROD-20260606-129` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `caishen_buzhen` | `has_wealth_picture` |
| `DTS-PROD-20260606-130` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `cai_guan_chengzai` | `has_official_picture` |
| `DTS-PROD-20260606-131` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `guanxing_bujian` | `has_official_picture` |
| `DTS-PROD-20260606-132` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `xishen_fubi` | `has_wealth_picture` |
| `DTS-PROD-20260606-133` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `jishen_gong` | `has_wealth_picture` |
| `DTS-PROD-20260606-134` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md` | `DITIANSUI_CHANWEI` | `shouyuan_yuanshen` | `always` |
| `DTS-PROD-20260606-135` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `shouyuan_yuanshen` | `always` |
| `DTS-PROD-20260606-136` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `shouyuan_fenlun` | `has_official_picture` |
| `DTS-PROD-20260606-137` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `shishen_zhisha` | `has_official_picture` |
| `DTS-PROD-20260606-138` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `qizhuo_shouyao` | `always` |
| `DTS-PROD-20260606-139` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `shouxi_zixi_fenlun` | `always` |
| `DTS-PROD-20260606-140` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `shenku_shouyao` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-141` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_fuxing_geju` | `has_marriage_picture` |
| `DTS-PROD-20260606-142` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_fanshensha` | `has_marriage_picture` |
| `DTS-PROD-20260606-143` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_fuzi_tongbian` | `has_marriage_picture` |
| `DTS-PROD-20260606-144` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_caiyong` | `has_official_picture` |
| `DTS-PROD-20260606-145` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_yinweifu` | `has_official_picture` |
| `DTS-PROD-20260606-146` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_banlv_yali` | `has_official_picture` |
| `DTS-PROD-20260606-147` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_zixi` | `has_official_picture` |
| `DTS-PROD-20260606-148` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `tanhe_hunlian` | `has_marriage_picture` |
| `DTS-PROD-20260606-149` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_fuzi_shenghua` | `has_official_picture` |
| `DTS-PROD-20260606-150` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `nvming_shangguan_zhihua` | `has_official_picture` |
| `DTS-PROD-20260606-151` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `hanmu_xiangyang` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-152` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `zaoshi_tu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-153` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xiaoer_heping` | `has_zhi_chong` |
| `DTS-PROD-20260606-154` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xiaoer_yiyang` | `always` |
| `DTS-PROD-20260606-155` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xiaoer_nanyang` | `has_official_picture` |
| `DTS-PROD-20260606-156` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `jinshui_pianhan` | `always` |
| `DTS-PROD-20260606-157` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `guansha_qiangruo` | `has_official_picture` |
| `DTS-PROD-20260606-158` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `caide_lun` | `always` |
| `DTS-PROD-20260606-159` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `deshengcai` | `always` |
| `DTS-PROD-20260606-160` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `caishengde` | `always` |
| `DTS-PROD-20260606-161` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `fenfa_zhiji` | `always` |
| `DTS-PROD-20260606-162` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `chenmai_zhiqi` | `always` |
| `DTS-PROD-20260606-163` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `enxuan_mei` | `has_marriage_picture` |
| `DTS-PROD-20260606-164` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `enxuan_yuan` | `has_marriage_picture` |
| `DTS-PROD-20260606-165` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xianshen_budong` | `has_marriage_picture` |
| `DTS-PROD-20260606-166` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xianshen_zuoyong` | `has_marriage_picture` |
| `DTS-PROD-20260606-167` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `xiji_dynamic` | `has_marriage_picture` |
| `DTS-PROD-20260606-168` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `hehua_xiji` | `has_marriage_picture` |
| `DTS-PROD-20260606-169` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `tanhe_shiyong` | `has_marriage_picture` |
| `DTS-PROD-20260606-170` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `fengchong_deyong` | `has_zhi_chong` |
| `DTS-PROD-20260606-171` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `zhencong` | `has_official_picture` |
| `DTS-PROD-20260606-172` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congxiang_zonggang` | `has_official_picture` |
| `DTS-PROD-20260606-173` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congwang` | `has_official_picture` |
| `DTS-PROD-20260606-174` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congqiang` | `has_official_picture` |
| `DTS-PROD-20260606-175` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congqi` | `has_wealth_picture` |
| `DTS-PROD-20260606-176` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congshi` | `has_official_picture` |
| `DTS-PROD-20260606-177` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congcai_shishang` | `has_wealth_picture` |
| `DTS-PROD-20260606-178` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md` | `DITIANSUI_CHANWEI` | `congsha_poge` | `has_zhi_chong` |
| `DTS-PROD-20260606-179` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `congwang_congqi_shunni` | `always` |
| `DTS-PROD-20260606-180` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `cong_jinshui_poge` | `has_wealth_picture` |
| `DTS-PROD-20260606-181` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `congshi_congguan_tongguan` | `has_zhi_chong` |
| `DTS-PROD-20260606-182` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conghua_jinshui_zaotu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-183` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `zhenhua_tiaojian` | `has_marriage_picture` |
| `DTS-PROD-20260606-184` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `zhenhua_huashen` | `has_marriage_picture` |
| `DTS-PROD-20260606-185` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `huashen_youyu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-186` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `huashen_buzu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-187` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `heerbuhua_jiban` | `has_marriage_picture` |
| `DTS-PROD-20260606-188` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiacong_tiaojian` | `has_official_picture` |
| `DTS-PROD-20260606-189` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiacong_zhenyun` | `has_wealth_picture` |
| `DTS-PROD-20260606-190` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiacongcai_xiyun` | `has_official_picture` |
| `DTS-PROD-20260606-191` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiacong_guansha_xiyun` | `has_official_picture` |
| `DTS-PROD-20260606-192` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiacong_yuanzhuoliuqing` | `has_wealth_picture` |
| `DTS-PROD-20260606-193` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiahua_leixing` | `has_marriage_picture` |
| `DTS-PROD-20260606-194` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `jiahua_zhenyun` | `has_wealth_picture` |
| `DTS-PROD-20260606-195` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conger_menhu` | `always` |
| `DTS-PROD-20260606-196` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conger_bulun_shenqiangruo` | `always` |
| `DTS-PROD-20260606-197` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conger_shishangshengcai` | `has_wealth_picture` |
| `DTS-PROD-20260606-198` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conger_jiyun` | `has_official_picture` |
| `DTS-PROD-20260606-199` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `conger_caixing_chengjiu` | `has_wealth_picture` |
| `DTS-PROD-20260606-200` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `junlai_chensheng` | `has_wealth_picture` |
| `DTS-PROD-20260606-201` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `erneng_jiumu` | `has_tiaohou_advice` |
| `DTS-PROD-20260606-202` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `muci_miezi` | `has_wealth_picture` |
| `DTS-PROD-20260606-203` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `fujian_paqi` | `has_marriage_picture` |
| `DTS-PROD-20260606-204` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `zhanju_tiandizhan` | `has_zhi_chong` |
| `DTS-PROD-20260606-205` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `chong_fayong` | `has_zhi_chong` |
| `DTS-PROD-20260606-206` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `tiandi_jiaozhan` | `always` |
| `DTS-PROD-20260606-207` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `heju_yihe` | `has_zhi_chong` |
| `DTS-PROD-20260606-208` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `heju_buyi` | `has_marriage_picture` |
| `DTS-PROD-20260606-209` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `junxiang` | `has_wealth_picture` |
| `DTS-PROD-20260606-210` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `chenxiang` | `always` |
| `DTS-PROD-20260606-211` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `muxiang` | `always` |
| `DTS-PROD-20260606-212` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `zixiang` | `always` |
| `DTS-PROD-20260606-213` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `xingqing_zhonghe_pianku` | `always` |
| `DTS-PROD-20260606-214` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `xingqing_pinghe` | `has_zhi_chong` |
| `DTS-PROD-20260606-215` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md` | `DITIANSUI_CHANWEI` | `xingqing_chengxin_fengxian` | `always` |
| `DTS-PROD-20260606-216` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `keming_qingqi_guanxing` | `has_official_picture` |
| `DTS-PROD-20260606-217` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `keming_yuntu_poqing` | `always` |
| `DTS-PROD-20260606-218` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `keming_yuntu_zhuxi` | `always` |
| `DTS-PROD-20260606-219` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `yilu_gongming_caiguan` | `has_official_picture` |
| `DTS-PROD-20260606-220` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `yilu_gongming_gaodi` | `has_wealth_picture` |
| `DTS-PROD-20260606-221` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `yilu_chengbai_chengzai` | `has_official_picture` |
| `DTS-PROD-20260606-222` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `diwei_qingqi_xishen` | `always` |
| `DTS-PROD-20260606-223` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `rensha_shenqing` | `has_official_picture` |
| `DTS-PROD-20260606-224` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `rensha_xingqing_fengxian` | `has_official_picture` |
| `DTS-PROD-20260606-225` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `diwei_caiguan_renzhi` | `has_official_picture` |
| `DTS-PROD-20260606-226` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `shiye_jiating_fenyu` | `has_marriage_picture` |
| `DTS-PROD-20260606-227` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `diwei_qingzhuo_jiceng` | `always` |
| `DTS-PROD-20260606-228` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `qingzhuo_ganzhi_shengjiang` | `has_wealth_picture` |
| `DTS-PROD-20260606-229` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_dayun_zhengti` | `has_marriage_picture` |
| `DTS-PROD-20260606-230` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_xiyun_houbao` | `has_wealth_picture` |
| `DTS-PROD-20260606-231` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_gaitou_jiejiao` | `has_marriage_picture` |
| `DTS-PROD-20260606-232` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_taisui_tiankedichong` | `has_zhi_chong` |
| `DTS-PROD-20260606-233` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_zhanchonghehao` | `has_zhi_chong` |
| `DTS-PROD-20260606-234` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `hehua_jiban` | `has_marriage_picture` |
| `DTS-PROD-20260606-235` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `suiyun_haotonglei_tonggen` | `has_wealth_picture` |
| `DTS-PROD-20260606-236` | `tiaohou_ditiansui` | `sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md` | `DITIANSUI_CHANWEI` | `zhenyuan_jieduan_chuancheng` | `has_wealth_picture` |

## 8. 审计边界

- 本次仅生成审计报告，未修改 `theory/*`、`engine/*`、权重、schema、family 或 rule_type。
- 本次 canon 判断以生产规则记录的 `source.path` 为准；未对原始经典全文做语义重标注。
- 若后续需要更强可追溯性，建议另行设计只读校验脚本，将 `source.excerpt` 与 `sources/*` 原文片段做模糊匹配，但不应在本次审计中改写规则。
