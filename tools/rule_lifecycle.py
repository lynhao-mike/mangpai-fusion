"""tools/rule_lifecycle.py · v1.2 Track-G 规律生命周期状态机

落地契约：
    engine/contracts/05-rule-lifecycle.md § 二/三/四/五/六
    engine/contracts/06-confidence-model.md § 二（Beta 数学）

职责：
    1. 5 状态自动机（proposed / candidate / confirmed / flagged_for_review / deprecated）
    2. Beta 后验置信度计算 (hits+1)/(hits+misses+2) + variance
    3. 升降级判定（auto，决策 F + G）
    4. theory/{school}/index.yaml 加载/保存（仅 Track-G 自迭代字段）

只允许 Track-G 写：
    status, status_history, status_changed_at,
    hits, misses, abstained,
    misses_at_confirmed, misses_at_flagged,
    recent_5, applied_cases, confidence_cache

其他字段（id / school / topic / title / conclusion / raw_*）一律只读。

作者：Track-G
"""
from __future__ import annotations

import datetime as _dt
import math
import pathlib
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import yaml

# ============================================================
# 一、类型定义
# ============================================================

RuleStatus = Literal[
    "proposed",
    "candidate",
    "confirmed",
    "flagged_for_review",
    "deprecated",
]

# 旧 v1.0 状态名兼容映射 → v1.2 5 状态
LEGACY_STATUS_MAP: dict[str, RuleStatus] = {
    "promoted": "confirmed",
    "candidate": "candidate",
    "frozen": "deprecated",
    "retired": "deprecated",
}

THEORY_DIR = pathlib.Path(__file__).resolve().parent.parent / "theory"

# 派别目录映射（contracts 用单字"段杨高任"，目录用 duan/yang/gao/ren）
SCHOOL_DIR_MAP: dict[str, str] = {
    "段": "duan", "杨": "yang", "高": "gao", "任": "ren",
    "duan": "duan", "yang": "yang", "gao": "gao", "ren": "ren",
    # ── 预留流派入口（第 5/6 派）──────────────────────────────
    # 启用时把 "ext1"/"ext2" 改为真实目录名，"预留一"/"预留二" 改为中文派名。
    "预留一": "ext1", "ext1": "ext1",
    "预留二": "ext2", "ext2": "ext2",
}

SCHOOL_TO_CN: dict[str, str] = {
    "duan": "段", "yang": "杨", "gao": "高", "ren": "任",
    # ── 预留流派（启用时改为真实派名）─────────────────────────
    "ext1": "预留一", "ext2": "预留二",
}


# ============================================================
# 二、Confidence（与 03-findings-schema § 三 对齐，但本文件独立持有以避免循环依赖）
# ============================================================

@dataclass
class Confidence:
    """双轨置信度。

    star: 1-5 ★
    percent: 0.0-1.0（=posterior 的展示口径）
    posterior: Beta 后验均值
    variance: Beta 后验方差
    sample_n: 累计样本数（hits + misses）
    """
    star: int
    percent: float
    posterior: float
    variance: float
    sample_n: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "star": int(self.star),
            "percent": round(float(self.percent), 6),
            "posterior": round(float(self.posterior), 6),
            "variance": round(float(self.variance), 6),
            "sample_n": int(self.sample_n),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Confidence":
        return cls(
            star=int(d["star"]),
            percent=float(d["percent"]),
            posterior=float(d["posterior"]),
            variance=float(d["variance"]),
            sample_n=int(d["sample_n"]),
        )


# ============================================================
# 三、Beta 数学
# ============================================================

def beta_posterior(hits: int, misses: int) -> tuple[float, float]:
    """Beta(α=hits+1, β=misses+1) 的后验均值与方差。

    >>> mean, var = beta_posterior(0, 0)
    >>> round(mean, 3), round(var, 3)
    (0.5, 0.083)
    """
    if hits < 0 or misses < 0:
        raise ValueError(f"hits/misses 必须 >= 0，得到 hits={hits} misses={misses}")
    α = hits + 1
    β = misses + 1
    s = α + β
    mean = α / s
    variance = (α * β) / (s * s * (s + 1))
    return mean, variance


def posterior_to_star(posterior: float) -> int:
    """05 § 四·2 与 06 § 二 的 5 ★ 映射。

    [0.00, 0.40) → 1
    [0.40, 0.55) → 2
    [0.55, 0.70) → 3
    [0.70, 0.85) → 4
    [0.85, 1.00] → 5
    """
    if posterior < 0.40:
        return 1
    if posterior < 0.55:
        return 2
    if posterior < 0.70:
        return 3
    if posterior < 0.85:
        return 4
    return 5


def compute_rule_confidence(
    hits: int,
    misses: int,
    *,
    variance_threshold: float = 0.15,
) -> Confidence:
    """05 § 四·2 数据驱动置信度（含变异度惩罚）。

    数据示例（与 05 § 四·3 表格对齐）：
        (0,0) → ★★ posterior=0.500
        (1,0) → ★★★ posterior=0.667
        (2,0) → ★★★★ posterior=0.750
        (3,1) → ★★★ posterior=0.667
        (5,0) → ★★★★★ posterior=0.857
        (7,1) → ★★★★ posterior=0.800
        (7,3) → ★★★ posterior=0.667
        (1,1) → ★★ posterior=0.500
        (0,2) → ★ posterior=0.250
    """
    posterior, variance = beta_posterior(hits, misses)
    base_star = posterior_to_star(posterior)
    # 决策 E：变异度 > 阈值 → -1★（不低于 1）
    star = base_star
    if variance > variance_threshold:
        star = max(1, star - 1)
    return Confidence(
        star=star,
        percent=posterior,
        posterior=posterior,
        variance=variance,
        sample_n=hits + misses,
    )


# ============================================================
# 四、Rule 数据结构（只持有 Track-G 关心的字段）
# ============================================================

@dataclass
class StatusChange:
    """status_history 中的一条记录。"""
    date: str            # ISO YYYY-MM-DD
    from_status: RuleStatus
    to_status: RuleStatus
    case_id: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "from": self.from_status,
            "to": self.to_status,
            "case_id": self.case_id,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "StatusChange":
        return cls(
            date=str(d["date"]),
            from_status=d["from"],  # type: ignore[arg-type]
            to_status=d["to"],  # type: ignore[arg-type]
            case_id=str(d.get("case_id", "")),
            reason=str(d.get("reason", "")),
        )


@dataclass
class AppliedCase:
    case_id: str
    year: Optional[int]
    hit: bool
    evidence_chain: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "year": self.year,
            "hit": bool(self.hit),
            "evidence_chain": list(self.evidence_chain),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AppliedCase":
        return cls(
            case_id=str(d["case_id"]),
            year=int(d["year"]) if d.get("year") is not None else None,
            hit=bool(d.get("hit", False)),
            evidence_chain=list(d.get("evidence_chain", [])),
            note=str(d.get("note", "")),
        )


@dataclass
class Rule:
    """theory/{school}/index.yaml 中一条规律的 Track-G 视图。

    只暴露自迭代关心的字段；其他原始字段 (title/conclusion/raw_*/topic) 透传保留在
    `_raw` 字典中，save_rule() 时与新值合并写回。
    """
    id: str
    school: str                         # 单字符 "段杨高任" 或 拼音 duan/yang/gao/ren
    topic: str

    # 生命周期
    status: RuleStatus = "proposed"
    status_changed_at: Optional[str] = None
    status_history: list[StatusChange] = field(default_factory=list)

    # 命中数据
    hits: int = 0
    misses: int = 0
    abstained: int = 0

    # 状态分水岭
    misses_at_confirmed: int = 0
    misses_at_flagged: Optional[int] = None

    # 滑动窗
    recent_5: list[bool] = field(default_factory=list)

    # 案例 trace
    applied_cases: list[AppliedCase] = field(default_factory=list)

    # 置信度缓存
    confidence_cache: Optional[Confidence] = None

    # v1.4 V1：quantifiable=False 表示框架性心法（不参与 hit/miss 计数）
    # v1.4 V2：domain_restriction 非空表示仅在列出的域内 ingest 时计 hit/miss
    quantifiable: bool = True
    domain_restriction: list[str] = field(default_factory=list)

    # 原始 yaml 透传字段（不可被 Track-G 改写）
    _raw: dict[str, Any] = field(default_factory=dict)

    # ----- 工具 ----------------------------------------------

    @property
    def n(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return (self.hits / self.n) if self.n > 0 else 0.0

    def update_recent_window(self, hit: bool, *, window_size: int = 5) -> None:
        """每次 hit/miss 后调用。append + 截断。"""
        self.recent_5.append(bool(hit))
        if len(self.recent_5) > window_size:
            self.recent_5 = self.recent_5[-window_size:]

    def recompute_confidence(
        self, *, variance_threshold: float = 0.15
    ) -> Confidence:
        c = compute_rule_confidence(
            self.hits, self.misses, variance_threshold=variance_threshold
        )
        self.confidence_cache = c
        return c


# ============================================================
# 五、状态机判定
# ============================================================

@dataclass
class LifecycleConfig:
    """从 engine/calibration.yaml 加载的阈值。"""
    candidate_min_hits: int = 1
    candidate_min_rate: float = 0.50
    confirmed_min_n: int = 5
    confirmed_min_rate: float = 0.70
    confirmed_demote_misses: int = 3
    flagged_demote_misses: int = 1
    drift_window_size: int = 5
    drift_min_n: int = 8
    drift_min_rate: float = 0.50
    variance_threshold: float = 0.15
    cross_school_every_n_cases: int = 10
    freeze_iteration: bool = False

    @classmethod
    def from_yaml(cls, path: Optional[pathlib.Path] = None) -> "LifecycleConfig":
        if path is None:
            path = pathlib.Path(__file__).resolve().parent.parent / "engine" / "calibration.yaml"
        if not path.exists():
            return cls()
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(
            candidate_min_hits=int(data.get("candidate_min_hits", 1)),
            candidate_min_rate=float(data.get("candidate_min_rate", 0.50)),
            confirmed_min_n=int(data.get("confirmed_min_n", 5)),
            confirmed_min_rate=float(data.get("confirmed_min_rate", 0.70)),
            confirmed_demote_misses=int(data.get("confirmed_demote_misses", 3)),
            flagged_demote_misses=int(data.get("flagged_demote_misses", 1)),
            drift_window_size=int(data.get("drift_window_size", 5)),
            drift_min_n=int(data.get("drift_min_n", 8)),
            drift_min_rate=float(data.get("drift_min_rate", 0.50)),
            variance_threshold=float(data.get("variance_threshold", 0.15)),
            cross_school_every_n_cases=int(data.get("cross_school_every_n_cases", 10)),
            freeze_iteration=bool(data.get("freeze_iteration", False)),
        )


def maybe_upgrade(
    rule: Rule, *, cfg: Optional[LifecycleConfig] = None
) -> Optional[RuleStatus]:
    """05 § 五·1 升级规则（auto，决策 F）。

    proposed → candidate：n ≥ candidate_min_hits 且 hit_rate ≥ candidate_min_rate
    candidate → confirmed：n ≥ confirmed_min_n 且 hit_rate ≥ confirmed_min_rate
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    if rule.status == "proposed":
        if rule.n >= cfg.candidate_min_hits and rule.hit_rate >= cfg.candidate_min_rate:
            return "candidate"
    elif rule.status == "candidate":
        if rule.n >= cfg.confirmed_min_n and rule.hit_rate >= cfg.confirmed_min_rate:
            return "confirmed"
    return None


def maybe_downgrade(
    rule: Rule, *, cfg: Optional[LifecycleConfig] = None
) -> Optional[RuleStatus]:
    """05 § 五·2 降级规则（auto + 缓冲，决策 G）。

    confirmed → flagged_for_review：misses 自 confirmed 起累计 ≥ confirmed_demote_misses
    flagged_for_review → deprecated：misses 自 flagged 起累计 ≥ flagged_demote_misses
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    if rule.status == "confirmed":
        misses_since = rule.misses - rule.misses_at_confirmed
        if misses_since >= cfg.confirmed_demote_misses:
            return "flagged_for_review"
    elif rule.status == "flagged_for_review":
        baseline = rule.misses_at_flagged if rule.misses_at_flagged is not None else rule.misses
        misses_since = rule.misses - baseline
        if misses_since >= cfg.flagged_demote_misses:
            return "deprecated"
    return None


def apply_status_change(
    rule: Rule,
    new_status: RuleStatus,
    *,
    case_id: str,
    reason: str = "",
    today: Optional[str] = None,
) -> StatusChange:
    """统一执行状态跃迁：写 history + 设分水岭。"""
    today = today or _dt.date.today().isoformat()
    change = StatusChange(
        date=today,
        from_status=rule.status,
        to_status=new_status,
        case_id=case_id,
        reason=reason,
    )
    rule.status_history.append(change)
    rule.status = new_status
    rule.status_changed_at = today
    if new_status == "confirmed":
        rule.misses_at_confirmed = rule.misses
    if new_status == "flagged_for_review":
        rule.misses_at_flagged = rule.misses
    return change


# ============================================================
# 六、yaml 加载/保存（Track-G 写权限 = 自迭代字段）
# ============================================================

class RuleNotFoundError(KeyError):
    """规律 ID 在所有 4 派 index.yaml 中均未找到。"""


def _index_yaml_for_school(school: str) -> pathlib.Path:
    sub = SCHOOL_DIR_MAP.get(school)
    if not sub:
        raise ValueError(f"未知 school: {school!r}（合法值 段/杨/高/任 或 duan/yang/gao/ren）")
    return THEORY_DIR / sub / "index.yaml"


def _all_index_yamls() -> list[pathlib.Path]:
    return [
        THEORY_DIR / sub / "index.yaml"
        for sub in ("duan", "yang", "gao", "ren")
        if (THEORY_DIR / sub / "index.yaml").exists()
    ]


def _read_yaml(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_yaml(path: pathlib.Path, data: dict[str, Any]) -> None:
    """保留文件头部注释 + dump rules."""
    # 提取已有头部注释（# 起头的连续行，止于 'rules:' 或非注释行）
    header_lines: list[str] = []
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or line.strip() == "":
                    header_lines.append(line.rstrip("\n"))
                else:
                    break
    body = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    )
    text = "\n".join(header_lines).rstrip() + "\n\n" + body if header_lines else body
    path.write_text(text, encoding="utf-8")


def _entry_to_rule(entry: dict[str, Any]) -> Rule:
    """yaml dict → Rule。未提供的字段使用默认。"""
    raw_status = entry.get("status", "proposed")
    if raw_status in LEGACY_STATUS_MAP and raw_status not in (
        "proposed", "candidate", "confirmed", "flagged_for_review", "deprecated",
    ):
        status: RuleStatus = LEGACY_STATUS_MAP[raw_status]
    elif raw_status in (
        "proposed", "candidate", "confirmed", "flagged_for_review", "deprecated",
    ):
        status = raw_status  # type: ignore[assignment]
    else:
        status = "proposed"

    history_raw = entry.get("status_history", []) or []
    history = [StatusChange.from_dict(h) for h in history_raw]

    applied_raw = entry.get("applied_cases", []) or []
    applied = [AppliedCase.from_dict(a) for a in applied_raw]

    conf_raw = entry.get("confidence_cache")
    conf: Optional[Confidence] = (
        Confidence.from_dict(conf_raw) if isinstance(conf_raw, dict) else None
    )

    rule = Rule(
        id=str(entry["id"]),
        school=str(entry.get("school", "")),
        topic=str(entry.get("topic", "")),
        status=status,
        status_changed_at=entry.get("status_changed_at"),
        status_history=history,
        hits=int(entry.get("hits", 0)),
        misses=int(entry.get("misses", 0)),
        abstained=int(entry.get("abstained", 0)),
        misses_at_confirmed=int(entry.get("misses_at_confirmed", 0)),
        misses_at_flagged=(
            int(entry["misses_at_flagged"])
            if entry.get("misses_at_flagged") is not None
            else None
        ),
        recent_5=[bool(x) for x in entry.get("recent_5", [])],
        applied_cases=applied,
        confidence_cache=conf,
        # v1.4 V1/V2：兼容旧 yaml（无字段时默认 quantifiable=True / 空 domain_restriction）
        quantifiable=bool(entry.get("quantifiable", True)),
        domain_restriction=list(entry.get("domain_restriction", []) or []),
        _raw=dict(entry),
    )
    return rule


def _rule_to_entry(rule: Rule) -> dict[str, Any]:
    """Rule → yaml dict。覆盖 self-iter 字段，其他字段从 _raw 透传。"""
    entry: dict[str, Any] = dict(rule._raw)  # 透传 title/conclusion/raw_* etc.
    entry["id"] = rule.id
    entry["school"] = rule.school
    entry["topic"] = rule.topic
    entry["status"] = rule.status
    if rule.status_changed_at is not None:
        entry["status_changed_at"] = rule.status_changed_at
    entry["status_history"] = [h.to_dict() for h in rule.status_history]
    entry["hits"] = rule.hits
    entry["misses"] = rule.misses
    entry["abstained"] = rule.abstained
    entry["misses_at_confirmed"] = rule.misses_at_confirmed
    if rule.misses_at_flagged is None:
        entry["misses_at_flagged"] = None
    else:
        entry["misses_at_flagged"] = rule.misses_at_flagged
    entry["recent_5"] = list(rule.recent_5)
    entry["applied_cases"] = [a.to_dict() for a in rule.applied_cases]
    if rule.confidence_cache is not None:
        d = rule.confidence_cache.to_dict()
        d["last_updated"] = _dt.date.today().isoformat()
        entry["confidence_cache"] = d
    # v1.4 V1/V2：仅在显式标注（非默认值）时写入 yaml，保持旧 yaml 干净
    if rule.quantifiable is not True:
        entry["quantifiable"] = rule.quantifiable
    elif "quantifiable" in entry and entry["quantifiable"] is True:
        # 已显式标注 true 的保留
        entry["quantifiable"] = True
    if rule.domain_restriction:
        entry["domain_restriction"] = list(rule.domain_restriction)
    elif "domain_restriction" in entry:
        # 显式空列表时清掉
        entry.pop("domain_restriction", None)
    return entry


def _locate_rule_in_yaml(
    rule_id: str,
) -> tuple[pathlib.Path, dict[str, Any], int]:
    """返回 (yaml_path, full_data, rule_index_in_rules_list)。

    raise RuleNotFoundError if 不存在。
    """
    for path in _all_index_yamls():
        data = _read_yaml(path)
        rules = data.get("rules", [])
        for idx, entry in enumerate(rules):
            if str(entry.get("id")) == rule_id:
                return path, data, idx
    raise RuleNotFoundError(f"规律 {rule_id!r} 在所有 4 派 index.yaml 中均未找到")


def load_rule(rule_id: str) -> Rule:
    """从对应 theory/{school}/index.yaml 加载一条规律。"""
    path, data, idx = _locate_rule_in_yaml(rule_id)
    entry = data["rules"][idx]
    return _entry_to_rule(entry)


def save_rule(rule: Rule) -> None:
    """把 Rule 的自迭代字段写回所属 index.yaml（透传其他字段）。"""
    path, data, idx = _locate_rule_in_yaml(rule.id)
    rules = data["rules"]
    rules[idx] = _rule_to_entry(rule)
    data["rules"] = rules
    _write_yaml(path, data)


def list_rule_ids(school: Optional[str] = None) -> list[str]:
    """枚举规律 ID。可指定派别。"""
    if school:
        paths = [_index_yaml_for_school(school)]
    else:
        paths = _all_index_yamls()
    out: list[str] = []
    for p in paths:
        data = _read_yaml(p)
        for entry in data.get("rules", []):
            out.append(str(entry["id"]))
    return out


def find_rule_id_by_predicate(
    school: str, *, topic: Optional[str] = None,
    keywords: Optional[list[str]] = None,
) -> Optional[str]:
    """在指定派别 index.yaml 中按 topic + 关键词找一条规律 ID。

    用于自动 fallback：若契约里写的某个 ID 不存在，按 topic / keywords 找一条
    真实存在的规律替代。
    """
    p = _index_yaml_for_school(school)
    data = _read_yaml(p)
    for entry in data.get("rules", []):
        if topic and entry.get("topic") != topic:
            continue
        if keywords:
            blob = " ".join(
                str(entry.get(k, "")) for k in ("title", "conclusion", "topic_label")
            )
            if not all(kw in blob for kw in keywords):
                continue
        return str(entry["id"])
    return None


# ============================================================
# 七、smoke / 单测
# ============================================================

def _smoke() -> None:
    """覆盖 05 § 四·3 的 9 行示例表 + 升降级路径。"""
    # 1. Beta 数学（9 个示例）
    cases: list[tuple[int, int, float, int]] = [
        # (hits, misses, expected_posterior, expected_star_after_variance)
        (0, 0, 0.500, 2),
        (1, 0, 0.667, 3),
        (2, 0, 0.750, 4),
        (3, 1, 0.667, 3),
        (5, 0, 0.857, 5),
        (7, 1, 0.800, 4),
        (7, 3, 0.667, 3),
        (1, 1, 0.500, 2),
        (0, 2, 0.250, 1),
    ]
    for hits, misses, exp_post, exp_star in cases:
        c = compute_rule_confidence(hits, misses)
        assert math.isclose(c.posterior, exp_post, abs_tol=0.001), (
            f"posterior 不符: hits={hits} misses={misses} got={c.posterior:.3f} exp={exp_post}"
        )
        assert c.star == exp_star, (
            f"★ 不符: hits={hits} misses={misses} got=★{c.star} exp=★{exp_star}"
        )
    print(f"[OK] beta + posterior_to_star + variance penalty: 9/9")

    # 2. 升级路径（proposed → candidate → confirmed）
    r = Rule(id="TEST-001", school="段", topic="test")
    assert maybe_upgrade(r) is None  # n=0 时不升
    r.hits = 1
    assert maybe_upgrade(r) == "candidate"
    apply_status_change(r, "candidate", case_id="C-TEST")
    r.hits = 4  # n=4 不到 5
    assert maybe_upgrade(r) is None
    r.hits = 5  # n=5 hit_rate=100%
    assert maybe_upgrade(r) == "confirmed"
    apply_status_change(r, "confirmed", case_id="C-TEST")
    print(f"[OK] proposed → candidate → confirmed 升级路径")

    # 3. 降级路径（confirmed → flagged → deprecated，3 次缓冲）
    r2 = Rule(id="TEST-002", school="杨", topic="test", status="confirmed",
              hits=5, misses=0, misses_at_confirmed=0)
    # 失验 1 次
    r2.misses = 1
    assert maybe_downgrade(r2) is None  # 缓冲中
    r2.misses = 2
    assert maybe_downgrade(r2) is None
    r2.misses = 3
    assert maybe_downgrade(r2) == "flagged_for_review"
    apply_status_change(r2, "flagged_for_review", case_id="C-TEST")
    # flagged 再失验 1 次 → deprecated
    r2.misses = 4
    assert maybe_downgrade(r2) == "deprecated"
    print(f"[OK] confirmed → flagged_for_review → deprecated 降级路径（3+1 缓冲）")

    # 4. round-trip yaml 序列化
    r3 = Rule(id="DEMO-RT", school="段", topic="test")
    r3.hits = 2
    r3.misses = 1
    r3.update_recent_window(True)
    r3.update_recent_window(False)
    r3.update_recent_window(True)
    r3.recompute_confidence()
    entry = _rule_to_entry(r3)
    r4 = _entry_to_rule(entry)
    assert r3.hits == r4.hits and r3.misses == r4.misses
    assert r3.recent_5 == r4.recent_5
    assert r4.confidence_cache is not None
    assert math.isclose(
        r3.confidence_cache.posterior, r4.confidence_cache.posterior, abs_tol=1e-6
    )
    print(f"[OK] Rule yaml round-trip OK")

    # 5. LifecycleConfig 加载
    cfg = LifecycleConfig.from_yaml()
    assert cfg.confirmed_demote_misses == 3
    assert cfg.candidate_min_rate == 0.50
    assert cfg.cross_school_every_n_cases == 10
    print(f"[OK] LifecycleConfig 加载: confirmed_demote_misses={cfg.confirmed_demote_misses}")

    print("\n=== rule_lifecycle.smoke 全部通过 ===")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
