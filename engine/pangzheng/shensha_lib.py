"""engine/pangzheng/shensha_lib.py · v1.2 D4 神煞旁证速查库

按高派 GP-BD-01~07（《盲派神煞应用宝典》）+ GP-CH-08~22（《车祸婚姻篇》）
构造神煞 → 领域 boost 速查表。

规则来源（高派"宝典"系）：
  - 金舆 = 富贵 / 婚姻 / 豪车
  - 驿马 = 奔波 / 调动 / 外出
  - 华盖 = 艺术 / 宗教 / 孤高
  - 词馆 / 学堂 / 文昌 = 学业辅佐
  - 天乙贵人 = 贵人扶持（学业/事业 双补）
  - 太极贵人 = 玄学 / 学术
  - 羊刃 = 武职 / 凶煞 / 健康风险
  - 血刃 / 童子煞 / 孤鸾煞 = 婚姻 / 健康负面信号
  - 红艳煞 / 天喜 = 桃花 / 喜事

每条规则：
    {
        "name": 神煞名,
        "domains": {domain: {"boost": float, "tags": [str], "contribution": str}},
        "school": "高",
        "rule_id": "GP-BD-XX",
    }

domain key 与 SupportFindings.shensha_supports 一致：
    "marriage" / "career" / "wealth" / "health" / "education" / "general"

作者：Track-D
"""
from __future__ import annotations

from typing import Any


# ============================================================
# 神煞速查表
# ============================================================
# 规则编号 GP-BD = 高派《盲派神煞应用宝典》
# 规则编号 GP-CH = 高派《车祸婚姻篇》
# boost 范围：单条 0.02-0.10；每个 domain 总 boost ≤ 0.20（cap in SupportFindings）

SHENSHA_RULES: list[dict[str, Any]] = [
    # ---------------- 富贵 / 婚姻类 ----------------
    {
        "name": "金舆",
        "rule_id": "GP-BD-01",
        "domains": {
            "marriage": {
                "boost": 0.05,
                "tags": ["配偶贵气", "豪车", "富贵婚"],
                "contribution": "金舆 = 富贵神煞，配偶有车有产 / 婚姻富贵跃升",
            },
            "wealth": {
                "boost": 0.04,
                "tags": ["豪车", "财气"],
                "contribution": "金舆 = 财富表象，主名下产权 / 大件资产",
            },
        },
    },
    {
        "name": "天乙贵人",
        "rule_id": "GP-BD-02",
        "domains": {
            "career": {
                "boost": 0.06,
                "tags": ["贵人扶持", "提拔"],
                "contribution": "天乙贵人 = 贵人扶持，逢凶化吉 / 上司器重",
            },
            "education": {
                "boost": 0.04,
                "tags": ["贵人扶持", "学业辅佐"],
                "contribution": "天乙贵人 = 贵人扶持学业 / 老师赏识",
            },
            "general": {
                "boost": 0.03,
                "tags": ["贵人"],
                "contribution": "天乙贵人 = 一生有贵人援助",
            },
        },
    },
    {
        "name": "太极贵人",
        "rule_id": "GP-BD-03",
        "domains": {
            "education": {
                "boost": 0.03,
                "tags": ["玄学", "学术", "探索"],
                "contribution": "太极贵人 = 主玄学 / 学术 / 哲思，学业偏深度",
            },
            "general": {
                "boost": 0.02,
                "tags": ["玄学倾向"],
                "contribution": "太极贵人 = 性情好探索玄理 / 道家",
            },
        },
    },
    {
        "name": "月德贵人",
        "rule_id": "GP-BD-04",
        "domains": {
            "general": {
                "boost": 0.04,
                "tags": ["逢凶化吉", "贵人"],
                "contribution": "月德 = 一生有德神扶持，遇灾减半",
            },
            "health": {
                "boost": 0.03,
                "tags": ["逢凶化吉"],
                "contribution": "月德 = 灾厄减轻信号",
            },
        },
    },
    {
        "name": "月德合",
        "rule_id": "GP-BD-04b",
        "domains": {
            "general": {
                "boost": 0.04,
                "tags": ["逢凶化吉", "贵人"],
                "contribution": "月德合 = 月德的合化形式，效力相当",
            },
            "marriage": {
                "boost": 0.03,
                "tags": ["和合"],
                "contribution": "月德合 = 婚姻和合信号",
            },
        },
    },
    {
        "name": "天德贵人",
        "rule_id": "GP-BD-05",
        "domains": {
            "general": {
                "boost": 0.04,
                "tags": ["逢凶化吉", "贵人"],
                "contribution": "天德 = 一生有天德扶持 / 逢凶化吉",
            },
            "health": {
                "boost": 0.03,
                "tags": ["逢凶化吉"],
                "contribution": "天德 = 灾厄减轻",
            },
        },
    },
    {
        "name": "天德合",
        "rule_id": "GP-BD-05b",
        "domains": {
            "general": {
                "boost": 0.04,
                "tags": ["逢凶化吉", "贵人"],
                "contribution": "天德合 = 天德的合化形式",
            },
        },
    },

    # ---------------- 学业辅佐类 ----------------
    {
        "name": "词馆",
        "rule_id": "GP-XL-01",
        "domains": {
            "education": {
                "boost": 0.05,
                "tags": ["学业", "文采", "高等教育"],
                "contribution": "词馆 = 学业核心辅佐神，主翰林 / 高等教育 / 文笔",
            },
        },
    },
    {
        "name": "学堂",
        "rule_id": "GP-XL-02",
        "domains": {
            "education": {
                "boost": 0.05,
                "tags": ["学业", "正规学历"],
                "contribution": "学堂 = 学业核心辅佐神，主正规高等学历",
            },
        },
    },
    {
        "name": "文昌",
        "rule_id": "GP-XL-03",
        "domains": {
            "education": {
                "boost": 0.04,
                "tags": ["学业", "聪慧"],
                "contribution": "文昌 = 学业辅佐 / 头脑聪慧 / 考试运",
            },
            "career": {
                "boost": 0.02,
                "tags": ["文职"],
                "contribution": "文昌 = 利文职 / 文化产业",
            },
        },
    },

    # ---------------- 走动 / 变迁类 ----------------
    {
        "name": "驿马",
        "rule_id": "GP-CH-01",
        "domains": {
            "career": {
                "boost": 0.04,
                "tags": ["奔波", "调动", "外出", "出差"],
                "contribution": "驿马 = 工作奔波 / 调动 / 出差 / 外出多",
            },
            "general": {
                "boost": 0.03,
                "tags": ["奔波", "迁动"],
                "contribution": "驿马 = 一生迁动多 / 居处不定",
            },
        },
    },

    # ---------------- 艺术 / 孤高类 ----------------
    {
        "name": "华盖",
        "rule_id": "GP-BD-06",
        "domains": {
            "career": {
                "boost": 0.03,
                "tags": ["艺术", "清贵", "宗教"],
                "contribution": "华盖 = 艺术 / 宗教 / 学术清贵之业",
            },
            "education": {
                "boost": 0.03,
                "tags": ["清贵", "文化"],
                "contribution": "华盖 = 清贵文化教育倾向",
            },
            "marriage": {
                "boost": -0.03,  # 负 boost：华盖独守易孤
                "tags": ["孤高"],
                "contribution": "华盖独守 = 婚姻孤高 / 迟婚信号（轻微负向）",
            },
        },
    },

    # ---------------- 桃花 / 喜事类 ----------------
    {
        "name": "天喜",
        "rule_id": "GP-BD-08",
        "domains": {
            "marriage": {
                "boost": 0.04,
                "tags": ["喜事", "桃花"],
                "contribution": "天喜 = 桃花喜事 / 配偶缘",
            },
        },
    },
    {
        "name": "红艳煞",
        "rule_id": "GP-BD-09",
        "domains": {
            "marriage": {
                "boost": 0.02,
                "tags": ["桃花", "异性缘"],
                "contribution": "红艳 = 异性缘旺（双刃剑：旺则桃花 / 凶则烂桃花）",
            },
        },
    },
    {
        "name": "红鸾",
        "rule_id": "GP-BD-09b",
        "domains": {
            "marriage": {
                "boost": 0.03,
                "tags": ["桃花", "婚喜"],
                "contribution": "红鸾 = 婚喜信号",
            },
        },
    },

    # ---------------- 凶煞 / 武职类 ----------------
    {
        "name": "羊刃",
        "rule_id": "GP-CH-08-1",
        "domains": {
            "career": {
                "boost": 0.03,
                "tags": ["武职", "刚烈"],
                "contribution": "羊刃 = 武职 / 公检法 / 刚烈职业适合",
            },
            "health": {
                "boost": 0.04,
                "tags": ["伤残风险", "刑伤"],
                "contribution": "羊刃 = 健康刑伤风险信号（GP-CH-08 阳刃被刑穿=下身伤）",
            },
            "marriage": {
                "boost": -0.03,  # 羊刃克婚（命主刚烈伤偶）
                "tags": ["刚烈"],
                "contribution": "羊刃 = 命主刚烈，对婚姻有耗（负向信号）",
            },
        },
    },
    {
        "name": "将星",
        "rule_id": "GP-BD-10",
        "domains": {
            "career": {
                "boost": 0.04,
                "tags": ["统领", "权位"],
                "contribution": "将星 = 统御之神，主握权 / 团队领导",
            },
        },
    },
    {
        "name": "魁罡",
        "rule_id": "GP-BD-11",
        "domains": {
            "career": {
                "boost": 0.04,
                "tags": ["决断", "刚烈", "纪检"],
                "contribution": "魁罡 = 断事如刀 / 适合纪检 / 司法",
            },
            "marriage": {
                "boost": -0.02,
                "tags": ["刚烈"],
                "contribution": "魁罡 = 命主刚烈，婚姻易刚硬",
            },
        },
    },

    # ---------------- 健康类 ----------------
    {
        "name": "天医",
        "rule_id": "GP-CS-32",
        "domains": {
            "career": {
                "boost": 0.04,
                "tags": ["医疗", "卫生"],
                "contribution": "天医 = 医疗 / 卫生职业首选",
            },
            "health": {
                "boost": 0.03,
                "tags": ["健康守护"],
                "contribution": "天医 = 健康守护 / 病时易遇良医",
            },
        },
    },
    {
        "name": "血刃",
        "rule_id": "GP-CH-09",
        "domains": {
            "health": {
                "boost": 0.04,
                "tags": ["手术", "外伤"],
                "contribution": "血刃 = 手术 / 外伤 / 出血风险（健康警示信号）",
            },
        },
    },

    # ---------------- 婚姻警示类 ----------------
    {
        "name": "孤鸾煞",
        "rule_id": "GP-CH-21",
        "domains": {
            "marriage": {
                "boost": -0.04,
                "tags": ["孤独", "迟婚"],
                "contribution": "孤鸾 = 婚姻孤独信号 / 易迟婚或独居（GP-CH-21 离婚六条之一）",
            },
        },
    },
    {
        "name": "童子煞",
        "rule_id": "GP-BD-12",
        "domains": {
            "marriage": {
                "boost": -0.03,
                "tags": ["童子煞", "婚姻波折"],
                "contribution": "童子煞 = 婚姻早期波折 / 易二婚信号",
            },
            "health": {
                "boost": 0.02,
                "tags": ["童子身"],
                "contribution": "童子煞 = 童子身，幼年体弱信号",
            },
        },
    },
    {
        "name": "九丑日",
        "rule_id": "GP-BD-13",
        "domains": {
            "marriage": {
                "boost": -0.02,
                "tags": ["婚姻杂事"],
                "contribution": "九丑日 = 婚姻易遇杂事波折",
            },
        },
    },
    {
        "name": "阴差阳错",
        "rule_id": "GP-BD-07",
        "domains": {
            "marriage": {
                "boost": -0.05,
                "tags": ["阴差阳错", "婚姻不顺"],
                "contribution": "阴差阳错日 = 婚姻一生不顺铁律（D.9-A，可降级为小杂音 D.9-D）",
            },
        },
    },

    # ---------------- 财厨 / 食禄类 ----------------
    {
        "name": "天厨",
        "rule_id": "GP-BD-14",
        "domains": {
            "wealth": {
                "boost": 0.03,
                "tags": ["食禄", "饮食"],
                "contribution": "天厨 = 食禄丰足 / 饮食业适合",
            },
            "career": {
                "boost": 0.02,
                "tags": ["饮食业"],
                "contribution": "天厨 = 餐饮 / 食品业有利",
            },
        },
    },
    {
        "name": "德秀",
        "rule_id": "GP-BD-15",
        "domains": {
            "career": {
                "boost": 0.03,
                "tags": ["清贵", "文职"],
                "contribution": "德秀 = 清贵之神，秘书 / 研究室 / 文职适合",
            },
            "general": {
                "boost": 0.02,
                "tags": ["清贵"],
                "contribution": "德秀 = 一生清贵 / 风评好",
            },
        },
    },
]


# ============================================================
# 索引：name → rule
# ============================================================

_NAME_INDEX: dict[str, dict[str, Any]] = {r["name"]: r for r in SHENSHA_RULES}


def get_rule(name: str) -> dict[str, Any] | None:
    """按神煞名取规则。"""
    return _NAME_INDEX.get(name)


def get_all_rule_names() -> list[str]:
    return list(_NAME_INDEX.keys())


# ============================================================
# 学业专门：词馆/学堂/文昌/天乙 综合评估
# ============================================================

EDUCATION_SHENSHA: tuple[str, ...] = (
    "词馆", "学堂", "文昌", "天乙贵人", "太极贵人",
)


def evaluate_ciguan_xuetang(input_doc: Any) -> dict[str, Any]:
    """评估词馆/学堂综合学业辅佐。

    返回 {
        has_ciguan: bool,
        has_xuetang: bool,
        has_wenchang: bool,
        has_taiyi: bool,
        boost: float (cap 0.10),
        contribution: str,
    }

    cap：避免 D-002 案例的"词馆+天乙×2 → boost 学业 ≤ 0.10"硬约束。
    """
    from engine.predicates.shensha import has_shensha, get_shensha_at

    has_ciguan = has_shensha("词馆", input_doc)
    has_xuetang = has_shensha("学堂", input_doc)
    has_wenchang = has_shensha("文昌", input_doc)
    has_taiyi = has_shensha("天乙贵人", input_doc)
    has_taichi = has_shensha("太极贵人", input_doc)

    # 出现次数（不同柱位算多次）
    taiyi_count = len(get_shensha_at("天乙贵人", input_doc))

    raw_boost = 0.0
    parts: list[str] = []

    if has_ciguan:
        raw_boost += 0.05
        parts.append("词馆+0.05")
    if has_xuetang:
        raw_boost += 0.05
        parts.append("学堂+0.05")
    if has_wenchang:
        raw_boost += 0.04
        parts.append("文昌+0.04")
    if has_taiyi:
        # 一柱 +0.04；多柱（×2）+0.06；上限 +0.06
        ty_boost = min(0.04 + (taiyi_count - 1) * 0.02, 0.06)
        raw_boost += ty_boost
        parts.append(f"天乙×{taiyi_count}+{ty_boost:.2f}")
    if has_taichi:
        raw_boost += 0.03
        parts.append("太极+0.03")

    # cap 0.10（防过冲，08 § 六 D-002 "boost 学业 ≤ 0.10"）
    boost = min(raw_boost, 0.10)

    contribution = (
        f"学业辅佐神煞：{'/'.join(parts) if parts else '无'} → 累加 {raw_boost:.3f}, "
        f"capped to {boost:.3f}"
    ) if parts else "无学业辅佐神煞"

    return {
        "has_ciguan": has_ciguan,
        "has_xuetang": has_xuetang,
        "has_wenchang": has_wenchang,
        "has_taiyi": has_taiyi,
        "raw_boost": raw_boost,
        "boost": boost,
        "contribution": contribution,
    }


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    # 神煞表完整性
    assert "金舆" in _NAME_INDEX
    assert "驿马" in _NAME_INDEX
    assert "词馆" in _NAME_INDEX
    assert "天乙贵人" in _NAME_INDEX
    print(f"[OK] 神煞规则库 {len(SHENSHA_RULES)} 条")

    # evaluate_ciguan_xuetang
    fake_shensha = {
        "年柱": ["天乙贵人"],  # C-014 风格
        "月柱": ["词馆", "天乙贵人"],
        "日柱": [],
        "时柱": [],
    }
    result = evaluate_ciguan_xuetang(fake_shensha)
    assert result["has_ciguan"]
    assert result["has_taiyi"]
    # 词馆 0.05 + 天乙×2(0.04+0.02=0.06) = 0.11 → cap 0.10
    assert result["raw_boost"] >= 0.10
    assert result["boost"] == 0.10, f"应 cap 到 0.10，实 {result['boost']}"
    print(f"[OK] D-002 约束验证：词馆+天乙×2 → boost={result['boost']:.3f} ≤ 0.10")

    # 仅词馆
    fake2 = {"年柱": [], "月柱": ["词馆"], "日柱": [], "时柱": []}
    r2 = evaluate_ciguan_xuetang(fake2)
    assert r2["boost"] == 0.05

    # 无任何
    fake3 = {"年柱": [], "月柱": [], "日柱": [], "时柱": []}
    r3 = evaluate_ciguan_xuetang(fake3)
    assert r3["boost"] == 0.0

    print("[OK] shensha_lib smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
