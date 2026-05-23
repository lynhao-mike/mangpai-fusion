# 谓词库契约 · 02-predicate-library

> **本文规定 v1.2 的 60 个共用 Python 谓词函数签名。**
> 所有 D1/D2/D3/D4 引擎和 mechanical-rules YAML 的判断逻辑都由这些原子组合而成。

最后更新：2026-05-23（W1.2）
版本：v1.2.0
依赖：B 决策（YAML 结构 + Python 谓词函数库）
模块路径：`engine/predicates/`

---

## 一、设计原则

1. **原子性**：每个函数做一件事，不耦合多个判断
2. **纯函数**：无副作用，相同输入永远相同输出（便于单测）
3. **类型严格**：所有参数和返回值都有 type hint
4. **零依赖外部库**：除了 `dataclasses`、`typing`，不依赖其他第三方库
5. **可被 YAML 调用**：mechanical-rules.yaml 通过 `predicate: name(args)` 直接引用

---

## 二、模块组织

```
engine/predicates/
├── __init__.py              ← 统一导出
├── ganzhi.py                ← 11 函数：干支基础
├── wuxing.py                ← 8 函数：五行关系
├── relations.py             ← 11 函数：合冲刑穿破等关系
├── palace.py                ← 10 函数：宫位与十神
├── cycles.py                ← 9 函数：大运流年
├── tou_cang.py              ← 5 函数：透藏关系
├── strength.py              ← 6 函数：旺衰判定
└── shensha.py               ← 5 函数：神煞辅助查询（不计算神煞）
                              共计 65 函数（预留 60 + 5 扩展位）
```


---

## 三、共用类型定义（`engine/predicates/types.py`）

```python
from dataclasses import dataclass, field
from typing import Literal, Optional

Gan = Literal["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
Zhi = Literal["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
Wuxing = Literal["金","木","水","火","土"]
YinYang = Literal["阴","阳"]
Polarity = Literal["阳干","阴干","阳支","阴支"]

@dataclass(frozen=True)
class GanZhi:
    gan: Gan
    zhi: Zhi
    def __str__(self) -> str: return f"{self.gan}{self.zhi}"

@dataclass
class Canggan:
    gan: Gan
    类型: Literal["主气","中气","余气"]
    力量: float

@dataclass
class Bazi:
    年柱: GanZhi
    月柱: GanZhi
    日柱: GanZhi
    时柱: GanZhi
    藏干: dict[Literal["年支","月支","日支","时支"], list[Canggan]]

@dataclass
class DayunStep:
    序号: int
    干支: GanZhi
    起岁: int
    止岁: int
    起讫年: tuple[int, int]

@dataclass
class Dayun:
    起运岁: float
    起运年: int
    顺逆: Literal["顺","逆"]
    排布: list[DayunStep]

Shishen = Literal["比肩","劫财","食神","伤官","正财","偏财","正官","七杀","正印","偏印"]
PalaceName = Literal["年柱","月柱","日柱","时柱","年支","月支","日支","时支"]
```


---

## 四、谓词函数签名（按模块）

### 4.1 `ganzhi.py` · 干支基础（11 函数）

```python
def is_gan(c: str) -> bool:
    """是否为天干（10 个之一）"""

def is_zhi(c: str) -> bool:
    """是否为地支（12 个之一）"""

def gan_index(g: Gan) -> int:
    """甲=0, 乙=1, ..., 癸=9"""

def zhi_index(z: Zhi) -> int:
    """子=0, 丑=1, ..., 亥=11"""

def gan_to_wuxing(g: Gan) -> Wuxing:
    """甲乙→木 / 丙丁→火 / 戊己→土 / 庚辛→金 / 壬癸→水"""

def zhi_to_wuxing(z: Zhi) -> Wuxing:
    """寅卯→木 / 巳午→火 / 申酉→金 / 亥子→水 / 辰戌丑未→土"""

def gan_yinyang(g: Gan) -> YinYang:
    """甲丙戊庚壬→阳 / 乙丁己辛癸→阴"""

def zhi_yinyang(z: Zhi) -> YinYang:
    """子寅辰午申戌→阳 / 丑卯巳未酉亥→阴"""

def get_canggan(z: Zhi) -> list[Canggan]:
    """返回地支藏干（标准表，主气1.0/中气0.3/余气0.2）"""

def jiazi_index(gz: GanZhi) -> int:
    """60 甲子序号 0-59，'甲子'=0, '癸亥'=59，非法组合抛 ValueError"""

def is_valid_jiazi(gz: GanZhi) -> bool:
    """是否合法 60 甲子组合（甲乙+子寅辰午申戌、丙丁+丑卯巳未酉亥 等阴阳同性配）"""
```


### 4.2 `wuxing.py` · 五行关系（8 函数）

```python
def wuxing_sheng(a: Wuxing, b: Wuxing) -> bool:
    """a 是否生 b（木→火 / 火→土 / 土→金 / 金→水 / 水→木）"""

def wuxing_ke(a: Wuxing, b: Wuxing) -> bool:
    """a 是否克 b（木→土 / 土→水 / 水→火 / 火→金 / 金→木）"""

def wuxing_same(a: Wuxing, b: Wuxing) -> bool:
    """同行（比劫关系）"""

def wuxing_relation(a: Wuxing, b: Wuxing) -> Literal["生我","我生","克我","我克","同我"]:
    """以 a 为参照，b 是何种关系"""

def gan_sheng_gan(a: Gan, b: Gan) -> bool:
    """天干生天干（基于五行）"""

def gan_ke_gan(a: Gan, b: Gan) -> bool:
    """天干克天干"""

def fan_sheng(a: Wuxing, b: Wuxing) -> bool:
    """反生：当 b 过旺，a 生不动反被埋（金多水浊 / 水多木漂 / 木多火塞 / 火多土焦 / 土多金埋）
    返回 True 当 b 五行力量 > 阈值且 a 弱"""

def fan_ke(a: Wuxing, b: Wuxing) -> bool:
    """反克：当 b 过旺，反过来欺负本应克它的 a"""
```

### 4.3 `relations.py` · 合冲刑穿破等（11 函数）

```python
def gan_he(a: Gan, b: Gan) -> Optional[tuple[Wuxing, Literal["化成","合绊","搅局"]]]:
    """天干五合：甲己合化土 / 乙庚合化金 / 丙辛合化水 / 丁壬合化木 / 戊癸合化火
    返回 (化神, 合的状态) 或 None"""

def zhi_liuhe(a: Zhi, b: Zhi) -> Optional[Wuxing]:
    """地支六合：子丑合土 / 寅亥合木 / 卯戌合火 / 辰酉合金 / 巳申合水 / 午未合
    返回化神，无合返回 None"""

def zhi_sanhe(zhis: list[Zhi]) -> Optional[Wuxing]:
    """地支三合局：申子辰水 / 寅午戌火 / 巳酉丑金 / 亥卯未木
    需要 3 个或半合（缺一不缺中支可成局），返回化神"""

def zhi_sanhui(zhis: list[Zhi]) -> Optional[Wuxing]:
    """地支三会方：寅卯辰木 / 巳午未火 / 申酉戌金 / 亥子丑水"""

def zhi_chong(a: Zhi, b: Zhi) -> bool:
    """地支六冲：子午 / 丑未 / 寅申 / 卯酉 / 辰戌 / 巳亥"""

def zhi_xing(a: Zhi, b: Zhi) -> Optional[Literal["三刑","自刑","互刑"]]:
    """地支刑：寅巳申三刑 / 丑戌未三刑 / 子卯互刑 / 辰午酉亥自刑"""

def zhi_chuan(a: Zhi, b: Zhi) -> bool:
    """地支六穿：子未 / 丑午 / 寅巳 / 卯辰 / 申亥 / 酉戌（任派核心，"穿不可调和"）"""

def zhi_po(a: Zhi, b: Zhi) -> bool:
    """地支六破：子酉 / 寅亥 / 卯午 / 辰丑 / 巳申 / 戌未"""

def zhi_zihe(z: Zhi) -> Optional[GanZhi]:
    """地支自合（藏干自合）：辰中戊癸合 / 戌中辛丙合 等"""

def gan_zhi_anhe(g: Gan, z: Zhi) -> bool:
    """干支暗合：甲与丑（藏己） / 戊与子（藏癸） 等"""

def relation_strength(rel: str) -> float:
    """5 大制法力度排序（段派 M1-D-XX 标准）：
    合 0.6 / 冲 1.0 / 刑 0.7 / 克 0.8 / 穿 0.9 / 破 0.4
    返回该关系的相对力度"""
```


### 4.4 `palace.py` · 宫位与十神（10 函数）

```python
def get_palace(bazi: Bazi, palace: PalaceName) -> GanZhi | Zhi:
    """取四柱中的指定宫位（年/月/日/时柱完整 GanZhi 或 单支）"""

def is_in_palace(c: Gan | Zhi, bazi: Bazi, palace: PalaceName) -> bool:
    """字 c 是否出现在指定宫位（含藏干检查）"""

def get_shishen(c: Gan, day_master: Gan) -> Shishen:
    """以日干为我，c 字相对我的十神（10 神之一）"""

def is_zhengyin(c: Gan, day_master: Gan) -> bool:
    """是否为正印（生我且阴阳异）"""

def is_pianyin(c: Gan, day_master: Gan) -> bool:
    """是否为偏印（生我且阴阳同）"""

def is_zhengcai(c: Gan, day_master: Gan) -> bool:
    """是否为正财（我克且阴阳异）"""

def is_piancai(c: Gan, day_master: Gan) -> bool:
    """是否为偏财（我克且阴阳同）"""

def is_zhengguan(c: Gan, day_master: Gan) -> bool:
    """是否为正官（克我且阴阳异）"""

def is_qisha(c: Gan, day_master: Gan) -> bool:
    """是否为七杀（克我且阴阳同）"""

def find_shishen_in_bazi(shishen: Shishen, bazi: Bazi) -> list[tuple[PalaceName, Gan|Zhi]]:
    """在整个八字中找十神出现的位置（含藏干）"""
```

### 4.5 `cycles.py` · 大运流年（9 函数）

```python
def get_dayun_at_age(dayun: Dayun, age: int) -> DayunStep:
    """指定年龄所在大运步"""

def get_dayun_at_year(dayun: Dayun, birth_year: int, target_year: int) -> DayunStep:
    """指定公历年所在大运步"""

def liunian_ganzhi(year: int) -> GanZhi:
    """公历年份的流年干支（基于 60 甲子推算，公元 4 年=甲子）"""

def is_dayun_zhi_chong_bazi(dayun_step: DayunStep, bazi: Bazi) -> list[PalaceName]:
    """大运地支冲八字哪些柱（返回被冲的柱名列表）"""

def is_liunian_with_dayun_he(year: int, dayun_step: DayunStep) -> Optional[Wuxing]:
    """流年与大运是否构成合（六合或三合半合），返回化神"""

def is_liunian_with_bazi_he(year: int, bazi: Bazi) -> list[tuple[PalaceName, Wuxing]]:
    """流年与八字哪些柱合，返回 [(柱名, 化神), ...]"""

def is_liunian_chong_bazi(year: int, bazi: Bazi) -> list[PalaceName]:
    """流年地支冲八字哪些柱"""

def is_liunian_yingdong_bazi_zi(year: int, target_char: Gan|Zhi, bazi: Bazi) -> bool:
    """流年是否引动八字中的 target_char（合/冲/刑/穿任一）"""

def find_year_when_zhi_appears(start: int, end: int, target_zhi: Zhi) -> list[int]:
    """[start, end] 区间内地支等于 target_zhi 的所有年份（每 12 年一次）"""
```


### 4.6 `tou_cang.py` · 透藏关系（5 函数）

```python
def is_tou(c: Gan, bazi: Bazi) -> bool:
    """天干 c 是否透出在四柱天干上（任一柱）"""

def is_canggan(c: Gan, bazi: Bazi) -> list[PalaceName]:
    """天干 c 是否藏在地支中，返回藏在哪些支（含余气）"""

def tou_chu(c: Gan, bazi: Bazi) -> Optional[tuple[PalaceName, PalaceName]]:
    """c 是否"透出"——藏在某支且对应天干在四柱上出现
    返回 (藏的支, 透出的天干位置)，无则 None
    任派核心概念：藏干透出 = 6 触发之一"""

def get_all_tou_chars(bazi: Bazi) -> list[Gan]:
    """所有"透出"的天干清单（去重）"""

def is_tou_at(c: Gan, palace: PalaceName, bazi: Bazi) -> bool:
    """c 是否透出在指定柱"""
```

### 4.7 `strength.py` · 旺衰判定（6 函数）

```python
def get_changsheng(g: Gan, z: Zhi) -> Literal[
    "长生","沐浴","冠带","临官","帝旺","衰","病","死","墓","绝","胎","养"]:
    """天干 g 在地支 z 的 12 长生状态"""

def is_dejin(g: Gan, yueling_zhi: Zhi) -> bool:
    """天干是否得令（在月令上为旺/相）"""

def is_dishi(g: Gan, bazi: Bazi) -> bool:
    """天干是否得地（在四支中至少一支为长生/临官/帝旺）"""

def is_dewang(g: Gan, bazi: Bazi) -> bool:
    """天干是否得旺（在天干上有比劫帮扶）"""

def calc_wuxing_strength(bazi: Bazi) -> dict[Wuxing, float]:
    """计算 5 行在原局的总力量（藏干力量 + 月令加权）
    返回 {木: 0.45, 火: 0.20, 土: 0.30, 金: 0.05, 水: 0.0} 之类
    总和约为 1.0"""

def calc_gan_strength(g: Gan, bazi: Bazi) -> float:
    """单个天干在原局的力量（0.0-1.5，超过1.0表示极旺）
    考虑：得令 + 得地 + 得势 + 透干"""
```

### 4.8 `shensha.py` · 神煞辅助（5 函数）

> ⚠️ **本系统不计算神煞**——只查询 input.md 中已录入的神煞列表。

```python
def has_shensha(name: str, input_doc: dict) -> bool:
    """input_doc.神煞 中是否含 name（不分柱）"""

def get_shensha_at(name: str, input_doc: dict) -> list[PalaceName]:
    """name 神煞挂在哪些柱"""

def is_taichi(input_doc: dict) -> bool: """is 太极贵人在原局"""

def is_jinyu(input_doc: dict) -> bool: """is 金舆在原局"""

def is_huagai(input_doc: dict) -> bool: """is 华盖在原局"""
```


---

## 五、谓词函数总数清点

| 模块 | 函数数 | 关键函数 |
|---|---|---|
| ganzhi.py | 11 | `is_valid_jiazi` `get_canggan` `jiazi_index` |
| wuxing.py | 8 | `wuxing_relation` `fan_sheng` `fan_ke` |
| relations.py | 11 | `gan_he` `zhi_chuan` `relation_strength` |
| palace.py | 10 | `get_shishen` `find_shishen_in_bazi` |
| cycles.py | 9 | `is_liunian_yingdong_bazi_zi` `find_year_when_zhi_appears` |
| tou_cang.py | 5 | `tou_chu` `is_canggan` |
| strength.py | 6 | `calc_wuxing_strength` `calc_gan_strength` |
| shensha.py | 5 | `has_shensha` `get_shensha_at` |
| **合计** | **65** | |

> 60 个核心 + 5 个扩展位 = 65 个。覆盖盲派 4 派核心判断 95% 的原子操作。

---

## 六、YAML 调用谓词的语法（mechanical-rules 用法）

```yaml
# engine/mechanical-rules.yaml 示例
rules:
  - id: MR-001
    name: 财动婚动联检
    description: 财星动 + 婚宫动 = 婚姻应期
    condition:
      - predicate: is_liunian_yingdong_bazi_zi
        args: [year, "$财星", bazi]
      - predicate: is_liunian_yingdong_bazi_zi
        args: [year, "$婚宫支", bazi]
    action: yield_yingqi(婚姻, year, ★★★★)
```

**调用约定**：
- `$变量` 表示从上下文取值（如 `$财星` = 该命的财星天干）
- `args:` 必须严格匹配函数签名
- 多个 condition 默认 AND；用 `or:` `not:` 显式
- `action:` 调用引擎层 API（详见 `04-gate-protocol.md` `05-rule-lifecycle.md`）

---

## 七、单元测试要求

每个谓词函数必须有：
1. 至少 3 个 happy path 用例
2. 至少 2 个边界用例（空输入、非法字符）
3. 1 个反向用例（应返回 False/None）

测试位置：`tests/predicates/test_<module>.py`

H · 测试 agent 在 W2 创建 fixture 时同步创建 baseline 测试。

---

## 八、版本演进

| 版本 | 变更 |
|---|---|
| 1.2.0 | 初版，65 函数 |

新增谓词必须：
1. PR 到 `v1.2-build`，title 前缀 `[PRED]`
2. 至少 1 个引擎模块（A/B/C/D）声明依赖
3. 整合 agent 批准

---

**契约结束。下一份请阅读 `03-findings-schema.md`（W1.2 第 3 份）。**
