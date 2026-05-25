"""engine/mechanical_rules.py · Decision B 合规的机械铁断登记表

本模块是 v1.2 重构 W2 末锁定的「决策 B」红线在机械铁断领域的落地：

    判定语义（predicate / action / 联检 / 黑名单替换）= 纯 Python
    元数据 + 阈值（id / schools / domains / 描述 / 置信下限 / 星级上限） = YAML

历史背景：
  早期 ``engine/mechanical-rules.yaml`` 同时承载「元数据」与「判定语义」，
  其 ``rules[].condition`` / ``rules[].action`` / ``rules[].excludes`` /
  ``rules[].coupled_with + require_n_of`` / ``blacklist[].replacement_rules``
  五处字段属于「YAML 表达判定逻辑」，违反 ``engine/contracts/decisions-locked.md``
  对决策 B 的红线约束（参见 ``plans/architecture-review.md`` 债务 4）。

本模块抽离上述五处判定语义，使用 dataclass + Python 字面量重写，
保留 ``02-predicate-library.md`` 中的谓词名作为「符号引用」（args 中的
``$bazi`` / ``$year`` 等占位符将在执行器接入时由调用方绑定）。

消费者：
  * ``tools/output_linter.py``：通过 ``get_replacement_rules()`` 在 E10
    告警的建议文案中给出实际替代 MR 编号（无须再读 YAML 字段）。
  * 未来 D1-D4 引擎接入时：通过 ``MECHANICAL_RULES`` / ``BLACKLIST`` 读取
    判定语义并连接到 ``engine.predicates`` 已实现的原子函数。

依赖：标准库 + PyYAML（仅用于读元数据）
版本：v1.2.1
作者：决策 B 清道夫（2026-05-25）
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    import yaml  # type: ignore
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "engine/mechanical_rules.py 需要 PyYAML，请运行: pip install pyyaml"
    ) from e


# ============================================================
# 一、判定语义 dataclass（取代 YAML 中的 condition / action / coupling）
# ============================================================

@dataclass(frozen=True)
class PredicateCall:
    """对 ``02-predicate-library.md`` 中谓词的符号引用。

    args 中可使用 ``$bazi`` / ``$year`` / ``$domain`` 等占位符，由执行器
    在运行时绑定。args 必须是可哈希的 tuple（嵌套元组替代 list）。
    """
    name: str
    args: tuple[Any, ...] = ()


@dataclass(frozen=True)
class FindingAction:
    """规则触发后产出一条画像 finding。"""
    domain: str
    statement: str
    confidence_floor: float
    confidence_ceiling: Optional[float] = None


@dataclass(frozen=True)
class YingqiAction:
    """规则触发后产出一条应期 finding（年份在执行期绑定）。"""
    domain: str          # 可写 "$domain" 表示由执行器从触发上下文推导
    year_var: str        # 占位符名，例如 "$year"
    confidence_floor: float


@dataclass(frozen=True)
class CouplingSpec:
    """N-of-M 联检（如 MR-005 坤造婚期三项联检）。"""
    coupled_with: tuple[str, ...]
    require_n_of: int


@dataclass(frozen=True)
class MechanicalRuleLogic:
    """单条 MR-XXX 的纯 Python 判定语义。"""
    rule_id: str
    condition: tuple[PredicateCall, ...]
    excludes: tuple[PredicateCall, ...] = ()
    finding: Optional[FindingAction] = None
    yingqi: Optional[YingqiAction] = None
    coupling: Optional[CouplingSpec] = None


@dataclass(frozen=True)
class BlacklistLogic:
    """单条 XF-XXX 的纯 Python 替代规则映射。"""
    blacklist_id: str
    replacement_rules: tuple[str, ...]


# ============================================================
# 二、机械铁断登记表（判定语义的唯一可执行来源）
# ============================================================

MECHANICAL_RULES: dict[str, MechanicalRuleLogic] = {
    "MR-001": MechanicalRuleLogic(
        rule_id="MR-001",
        condition=(
            PredicateCall("has_yin_in_palace", ("月柱", "$bazi")),
            PredicateCall(
                "is_fuyin_with_palace",
                ("月柱", ("年柱", "日柱"), "$bazi"),
            ),
        ),
        finding=FindingAction(
            domain="六亲",
            statement="母亲感情反复（多婚倾向）",
            confidence_floor=0.85,
            confidence_ceiling=0.95,
        ),
    ),
    "MR-002": MechanicalRuleLogic(
        rule_id="MR-002",
        condition=(
            PredicateCall("wuxing_strength_at_least", ("土", 0.55, "$bazi")),
            PredicateCall("wuxing_strength_at_most",  ("火", 0.30, "$bazi")),
            PredicateCall("wuxing_strength_at_most",  ("金", 0.30, "$bazi")),
        ),
        finding=FindingAction(
            domain="体貌",
            statement="肤色偏暗",
            confidence_floor=0.85,
        ),
    ),
    "MR-003": MechanicalRuleLogic(
        rule_id="MR-003",
        condition=(
            PredicateCall("day_master_is", ("丙", "$bazi")),
            PredicateCall("shishen_tou", (("食神", "伤官"), "$bazi")),
        ),
        finding=FindingAction(
            domain="体貌",
            statement="大眼/嘴大/开朗外向",
            confidence_floor=0.85,
        ),
    ),
    "MR-004": MechanicalRuleLogic(
        rule_id="MR-004",
        condition=(
            PredicateCall("zhi_in_xunkong", ("$target_zhi", "$bazi")),
            PredicateCall("liunian_chong_or_tianshi", ("$year", "$target_zhi")),
        ),
        yingqi=YingqiAction(
            domain="$domain",
            year_var="$year",
            confidence_floor=0.85,
        ),
    ),
    "MR-005": MechanicalRuleLogic(
        rule_id="MR-005",
        condition=(
            PredicateCall("gender_is", ("F", "$birth")),
            PredicateCall("liunian_gan_is_caixing", ("$year", "$caixing")),
            PredicateCall(
                "liunian_caixing_not_seriously_kepa",
                ("$year", "$bazi"),
            ),
        ),
        yingqi=YingqiAction(
            domain="婚姻",
            year_var="$year",
            confidence_floor=0.85,
        ),
        coupling=CouplingSpec(
            # 三项联检：① 官杀格局动 (MR-008-guansha-dong, 待登记)
            #          ② 财动婚动 (本条 MR-005)
            #          ③ 空亡冲实 (MR-004)
            coupled_with=("MR-004", "MR-008-guansha-dong"),
            require_n_of=2,
        ),
    ),
    "MR-006": MechanicalRuleLogic(
        rule_id="MR-006",
        condition=(
            PredicateCall("nianzhu_zhi_is_yima", ("$bazi",)),
        ),
        excludes=(
            PredicateCall("yima_zhi_he_zhu", ("$bazi",)),
        ),
        finding=FindingAction(
            domain="配偶",
            statement="首任配偶含流动/远方/军警属性",
            confidence_floor=0.70,
            confidence_ceiling=0.85,
        ),
    ),
}


# ============================================================
# 三、黑名单替代规则映射
# ============================================================

BLACKLIST: dict[str, BlacklistLogic] = {
    "XF-001": BlacklistLogic("XF-001", ("MR-004", "MR-005")),
    "XF-002": BlacklistLogic("XF-002", ("MR-004", "MR-005")),
    "XF-003": BlacklistLogic("XF-003", ("MR-004",)),
}


def get_replacement_rules(blacklist_id: str) -> tuple[str, ...]:
    """返回某条 XF 黑名单规律的替代 MR-XXX 元组（未登记则返回空元组）。"""
    entry = BLACKLIST.get(blacklist_id)
    return entry.replacement_rules if entry else ()


def evaluate_coupling(
    rule_id: str,
    fired_partners: Iterable[str],
) -> Optional[bool]:
    """N-of-M 联检判定（如 MR-005 三项联检）。

    :param rule_id: 待判定的 MR 编号
    :param fired_partners: 已触发的伙伴规律 ID（来自上游引擎）
    :return:
        * True/False —— 该规律存在 coupling 规约时的最终判定
        * None       —— 该规律没有 coupling 规约（无需联检）
    """
    logic = MECHANICAL_RULES.get(rule_id)
    if logic is None or logic.coupling is None:
        return None
    fired = set(fired_partners) & set(logic.coupling.coupled_with)
    return len(fired) >= logic.coupling.require_n_of


# ============================================================
# 四、元数据 dataclass（仅由 YAML 提供）
# ============================================================

@dataclass(frozen=True)
class RuleMetadata:
    rule_id: str
    name: str
    type: str
    schools: tuple[str, ...]
    domains: tuple[str, ...]
    description: str
    confidence_floor: float
    confidence_ceiling: Optional[float]
    star_ceiling: int
    application_case: str
    falsifiable: str


@dataclass(frozen=True)
class BlacklistMetadata:
    blacklist_id: str
    pattern: str
    aliases: tuple[str, ...]
    schools_originally_blamed: tuple[str, ...]
    rejected_in_cases: tuple[str, ...]
    reason: str
    blocked_in_outputs: tuple[str, ...]


@dataclass(frozen=True)
class ForbiddenPhrase:
    phrase: str
    reason: str


@dataclass(frozen=True)
class MechanicalRulesRegistry:
    """合并视图：YAML 元数据 + 本模块的判定语义。"""
    schema_version: str
    rules_meta: dict[str, RuleMetadata]
    blacklist_meta: dict[str, BlacklistMetadata]
    forbidden_hard: tuple[ForbiddenPhrase, ...]
    forbidden_soft: tuple[ForbiddenPhrase, ...]


DEFAULT_RULES_YAML: Path = (
    Path(__file__).resolve().parent / "mechanical-rules.yaml"
)


def load_registry(yaml_path: Optional[Path] = None) -> MechanicalRulesRegistry:
    """从 YAML 加载元数据，与本模块的判定语义合成完整登记表。"""
    p = Path(yaml_path) if yaml_path else DEFAULT_RULES_YAML
    if not p.exists():
        return MechanicalRulesRegistry(
            schema_version="0.0.0",
            rules_meta={},
            blacklist_meta={},
            forbidden_hard=(),
            forbidden_soft=(),
        )
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    rules_meta: dict[str, RuleMetadata] = {}
    for r in data.get("rules") or []:
        rid = str(r["id"])
        ceiling = r.get("confidence_ceiling")
        rules_meta[rid] = RuleMetadata(
            rule_id=rid,
            name=str(r.get("name", "")),
            type=str(r.get("type", "")),
            schools=tuple(r.get("schools") or ()),
            domains=tuple(r.get("domains") or ()),
            description=str(r.get("description", "")),
            confidence_floor=float(r.get("confidence_floor", 0.0)),
            confidence_ceiling=float(ceiling) if ceiling is not None else None,
            star_ceiling=int(r.get("star_ceiling", 5)),
            application_case=str(r.get("application_case", "")),
            falsifiable=str(r.get("falsifiable", "")),
        )

    blacklist_meta: dict[str, BlacklistMetadata] = {}
    for b in data.get("blacklist") or []:
        bid = str(b["id"])
        blacklist_meta[bid] = BlacklistMetadata(
            blacklist_id=bid,
            pattern=str(b.get("pattern", "")),
            aliases=tuple(b.get("aliases") or ()),
            schools_originally_blamed=tuple(
                b.get("schools_originally_blamed") or ()
            ),
            rejected_in_cases=tuple(b.get("rejected_in_cases") or ()),
            reason=str(b.get("reason", "")),
            blocked_in_outputs=tuple(b.get("blocked_in_outputs") or ()),
        )

    fp = data.get("forbidden_phrases") or {}
    hard = tuple(
        ForbiddenPhrase(str(x["phrase"]), str(x.get("reason", "")))
        for x in (fp.get("hard") or [])
        if isinstance(x, dict)
    )
    soft = tuple(
        ForbiddenPhrase(str(x["phrase"]), str(x.get("reason", "")))
        for x in (fp.get("soft") or [])
        if isinstance(x, dict)
    )

    return MechanicalRulesRegistry(
        schema_version=str(data.get("schema_version", "")),
        rules_meta=rules_meta,
        blacklist_meta=blacklist_meta,
        forbidden_hard=hard,
        forbidden_soft=soft,
    )


# ============================================================
# 五、自检：YAML 元数据 ID 与 Python 判定语义 ID 必须一一对应
# ============================================================

def check_consistency(
    yaml_path: Optional[Path] = None,
) -> list[str]:
    """返回不一致项的人类可读列表（空 = 通过）。

    保障 sync_invariants：YAML 中的 rules / blacklist 数量 == Python 登记数。
    """
    reg = load_registry(yaml_path)
    issues: list[str] = []

    py_mr_ids = set(MECHANICAL_RULES.keys())
    yaml_mr_ids = set(reg.rules_meta.keys())
    only_py = py_mr_ids - yaml_mr_ids
    only_yaml = yaml_mr_ids - py_mr_ids
    if only_py:
        issues.append(
            f"Python 有判定语义但 YAML 缺元数据: {sorted(only_py)}"
        )
    if only_yaml:
        issues.append(
            f"YAML 有元数据但 Python 缺判定语义: {sorted(only_yaml)}"
        )

    py_xf_ids = set(BLACKLIST.keys())
    yaml_xf_ids = set(reg.blacklist_meta.keys())
    only_py_xf = py_xf_ids - yaml_xf_ids
    only_yaml_xf = yaml_xf_ids - py_xf_ids
    if only_py_xf:
        issues.append(
            f"Python 有黑名单替代映射但 YAML 缺元数据: {sorted(only_py_xf)}"
        )
    if only_yaml_xf:
        issues.append(
            f"YAML 有黑名单元数据但 Python 缺替代映射: {sorted(only_yaml_xf)}"
        )

    return issues


__all__ = [
    # 判定语义 dataclass
    "PredicateCall", "FindingAction", "YingqiAction", "CouplingSpec",
    "MechanicalRuleLogic", "BlacklistLogic",
    # 登记表
    "MECHANICAL_RULES", "BLACKLIST",
    # 判定 helper
    "get_replacement_rules", "evaluate_coupling",
    # 元数据 dataclass
    "RuleMetadata", "BlacklistMetadata", "ForbiddenPhrase",
    "MechanicalRulesRegistry",
    # 加载 / 自检
    "DEFAULT_RULES_YAML", "load_registry", "check_consistency",
]


if __name__ == "__main__":  # pragma: no cover
    issues = check_consistency()
    if issues:
        print("[FAIL] mechanical_rules consistency:")
        for i in issues:
            print("  -", i)
        raise SystemExit(1)
    print(
        f"[OK] mechanical_rules consistency: "
        f"{len(MECHANICAL_RULES)} MR · {len(BLACKLIST)} XF"
    )
