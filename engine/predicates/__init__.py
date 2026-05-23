"""engine/predicates · v1.2 共用谓词原子库

模块归属（按契约 02 + 08 § 二）：
    types       - 共用类型 + 常量表 + 适配器        (Track-A)
    ganzhi      - 11 个干支基础函数                  (Track-A)
    wuxing      - 8 个五行关系函数                   (Track-A)
    relations   - 11 个合冲刑穿破函数                (Track-A)
    strength    - 6 个旺衰判定函数                   (Track-A)
    palace      - 10 个宫位/十神函数                 (Track-B)
    cycles      - 9 个大运流年函数                   (Track-C)
    tou_cang    - 5 个透藏关系函数                   (Track-C)
    shensha     - 5 个神煞辅助函数 + 2 辅助          (Track-D)

合计：11+8+11+6+10+9+5+5 = 65 函数（Track-A~D 全部已交付）
（与 02-predicate-library.md § 五 清点一致）
"""
from engine.predicates.types import (  # noqa: F401
    GAN_LIST,
    ZHI_LIST,
    WUXING_LIST,
    GAN_TO_WUXING,
    ZHI_TO_WUXING,
    GAN_YINYANG,
    ZHI_YINYANG,
    ZHI_CANGGAN_TABLE,
    CHANGSHENG_TABLE,
    Gan,
    Zhi,
    Wuxing,
    YinYang,
    ChangshengStatus,
    Shishen,
    PalaceName,
    Canggan,
    GanZhi,
    Bazi,
    DayunStep,
    Dayun,
    KnownFact,
    ParsedInput,
    adapt_bazi,
    adapt_dayun,
    adapt_parsed,
)

from engine.predicates.ganzhi import (  # noqa: F401
    is_gan,
    is_zhi,
    gan_index,
    zhi_index,
    gan_to_wuxing,
    zhi_to_wuxing,
    gan_yinyang,
    zhi_yinyang,
    get_canggan,
    jiazi_index,
    is_valid_jiazi,
)

from engine.predicates.wuxing import (  # noqa: F401
    wuxing_sheng,
    wuxing_ke,
    wuxing_same,
    wuxing_relation,
    gan_sheng_gan,
    gan_ke_gan,
    fan_sheng,
    fan_ke,
)

from engine.predicates.relations import (  # noqa: F401
    gan_he,
    zhi_liuhe,
    zhi_sanhe,
    zhi_sanhui,
    zhi_chong,
    zhi_xing,
    zhi_chuan,
    zhi_po,
    zhi_zihe,
    gan_zhi_anhe,
    relation_strength,
)

from engine.predicates.strength import (  # noqa: F401
    get_changsheng,
    is_dejin,
    is_dishi,
    is_dewang,
    calc_wuxing_strength,
    calc_gan_strength,
)

# Track-B 追加：palace.py（10 函数）
from engine.predicates.palace import (  # noqa: F401
    find_shishen_in_bazi,
    get_palace,
    get_shishen,
    is_in_palace,
    is_pianyin,
    is_piancai,
    is_qisha,
    is_zhengcai,
    is_zhengguan,
    is_zhengyin,
)

# Track-C 追加：cycles.py（9 函数）+ tou_cang.py（5 函数）
from engine.predicates.cycles import (  # noqa: F401
    get_dayun_at_age,
    get_dayun_at_year,
    liunian_ganzhi,
    is_dayun_zhi_chong_bazi,
    is_liunian_with_dayun_he,
    is_liunian_with_bazi_he,
    is_liunian_chong_bazi,
    is_liunian_yingdong_bazi_zi,
    find_year_when_zhi_appears,
    is_in_dayun_transition,  # 04 § 4.2 辅助
    get_adjacent_dayun,       # 04 § 4.2 辅助
)
from engine.predicates.tou_cang import (  # noqa: F401
    is_tou,
    is_canggan,
    tou_chu,
    get_all_tou_chars,
    is_tou_at,
)

# Track-D 追加：shensha.py（5 函数 + 2 辅助）
from engine.predicates.shensha import (  # noqa: F401
    has_shensha,
    get_shensha_at,
    is_taichi,
    is_jinyu,
    is_huagai,
    get_all_shensha_names,
    has_any_shensha,
)

__all__ = [
    # types
    "Gan", "Zhi", "Wuxing", "YinYang", "ChangshengStatus", "Shishen", "PalaceName",
    "Canggan", "GanZhi", "Bazi", "DayunStep", "Dayun", "KnownFact", "ParsedInput",
    "adapt_bazi", "adapt_dayun", "adapt_parsed",
    # ganzhi
    "is_gan", "is_zhi", "gan_index", "zhi_index",
    "gan_to_wuxing", "zhi_to_wuxing", "gan_yinyang", "zhi_yinyang",
    "get_canggan", "jiazi_index", "is_valid_jiazi",
    # wuxing
    "wuxing_sheng", "wuxing_ke", "wuxing_same", "wuxing_relation",
    "gan_sheng_gan", "gan_ke_gan", "fan_sheng", "fan_ke",
    # relations
    "gan_he", "zhi_liuhe", "zhi_sanhe", "zhi_sanhui",
    "zhi_chong", "zhi_xing", "zhi_chuan", "zhi_po",
    "zhi_zihe", "gan_zhi_anhe", "relation_strength",
    # strength
    "get_changsheng", "is_dejin", "is_dishi", "is_dewang",
    "calc_wuxing_strength", "calc_gan_strength",
    # palace (Track-B)
    "get_palace", "is_in_palace", "get_shishen",
    "is_zhengyin", "is_pianyin", "is_zhengcai", "is_piancai",
    "is_zhengguan", "is_qisha", "find_shishen_in_bazi",
    # cycles (Track-C)
    "get_dayun_at_age", "get_dayun_at_year", "liunian_ganzhi",
    "is_dayun_zhi_chong_bazi", "is_liunian_with_dayun_he",
    "is_liunian_with_bazi_he", "is_liunian_chong_bazi",
    "is_liunian_yingdong_bazi_zi", "find_year_when_zhi_appears",
    "is_in_dayun_transition", "get_adjacent_dayun",
    # tou_cang (Track-C)
    "is_tou", "is_canggan", "tou_chu", "get_all_tou_chars", "is_tou_at",
    # shensha (Track-D)
    "has_shensha", "get_shensha_at",
    "is_taichi", "is_jinyu", "is_huagai",
    "get_all_shensha_names", "has_any_shensha",
]
