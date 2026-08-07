"""CFL-C016-001..005 修复回归测试

落地：cases/C-2026-016-甲子丙子丙戌戊子/lessons.md § 二
来源：v1.3.0+v1.4 W1 上线后首例真实命主端到端 pipeline（C-2026-016）暴露的 5 条工程债

逐条断言：
  CFL-001  preflight 起运年公式 floor → round
  CFL-002  D3 应期前向预测模式 ★ 上限 4（含 ★/% 区间一致性）
  CFL-003  模板 § 一 能量等级 / 置信度分行
  CFL-004  run_pipeline 出口挂 output._parsed
  CFL-005  retrospective 不再因 'DayunStep.起讫年' 失败
"""
from __future__ import annotations

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


# ============================================================
# CFL-C016-001: preflight 起运年公式 floor → round
# ============================================================

def _make_minimal_input(qiyun_sui: float, qiyun_year: int,
                        birth_year: int = 1984) -> str:
    """构造一份最小合法 input.md（除 起运岁/年 外都用占位）。"""
    return f"""# Test Input

```yaml
schema_version: 1.2.0
case_meta:
  case_id: C-{birth_year}-999-甲子丙子丙戌戊子
  立案日期: 2026-05-26
  命主代号: 测试
  策略: B
  来源: 测试
```

```yaml
birth:
  性别: F
  公历: {birth_year}-12-18 00:50
  农历: 测
  出生地: 测
  真太阳时校正: true
```

```yaml
四柱:
  年柱: 甲子
  月柱: 丙子
  日柱: 丙戌
  时柱: 戊子
```

```yaml
藏干:
  年支:
    - {{干: 癸, 类型: 主气, 力量: 1.0}}
  月支:
    - {{干: 癸, 类型: 主气, 力量: 1.0}}
  日支:
    - {{干: 戊, 类型: 主气, 力量: 1.0}}
  时支:
    - {{干: 癸, 类型: 主气, 力量: 1.0}}
```

```yaml
大运:
  起运岁: {qiyun_sui}
  起运年: {qiyun_year}
  顺逆: 逆
  排布:
    - {{序号: 1, 干支: 乙亥, 起讫: "{qiyun_year}-{qiyun_year+10}", 起岁: 5,  止岁: 14}}
    - {{序号: 2, 干支: 甲戌, 起讫: "{qiyun_year+10}-{qiyun_year+20}", 起岁: 15, 止岁: 24}}
    - {{序号: 3, 干支: 癸酉, 起讫: "{qiyun_year+20}-{qiyun_year+30}", 起岁: 25, 止岁: 34}}
    - {{序号: 4, 干支: 壬申, 起讫: "{qiyun_year+30}-{qiyun_year+40}", 起岁: 35, 止岁: 44}}
    - {{序号: 5, 干支: 辛未, 起讫: "{qiyun_year+40}-{qiyun_year+50}", 起岁: 45, 止岁: 54}}
    - {{序号: 6, 干支: 庚午, 起讫: "{qiyun_year+50}-{qiyun_year+60}", 起岁: 55, 止岁: 64}}
    - {{序号: 7, 干支: 己巳, 起讫: "{qiyun_year+60}-{qiyun_year+70}", 起岁: 65, 止岁: 74}}
    - {{序号: 8, 干支: 戊辰, 起讫: "{qiyun_year+70}-{qiyun_year+80}", 起岁: 75, 止岁: 84}}
```

```yaml
神煞:
  年柱: []
  月柱: []
  日柱: []
  时柱: []
  整体: []
```

```yaml
十二长生:
  日干: 丙
  年支: 胎
  月支: 胎
  日支: 墓
  时支: 胎
```

```yaml
known_facts: []
```
"""


def _parse_string_to_input(text: str, tmp_path):
    from tools.preflight import parse
    path = tmp_path / "C-1984-999-甲子丙子丙戌戊子" / "input.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return parse(path)


class TestCFLC016_001_PreflightQiyunYear:
    """preflight 起运年应该用 round() 而非 floor()，支持分数年份。"""

    def test_qiyun_3_586_rounds_to_4(self, tmp_path):
        """3.586 round → 4 → birth_year+4=1988（C-2026-016 真实场景）"""
        text = _make_minimal_input(qiyun_sui=3.586, qiyun_year=1988)
        res = _parse_string_to_input(text, tmp_path)
        assert res.dayun.起运岁 == 3.586
        assert res.dayun.起运年 == 1988

    def test_qiyun_integer_9_unchanged(self, tmp_path):
        """整数起运岁 9.0 不被 round 影响（C-2026-015 兼容回归）"""
        text = _make_minimal_input(qiyun_sui=9.0, qiyun_year=1993,
                                   birth_year=1984)
        res = _parse_string_to_input(text, tmp_path)
        assert res.dayun.起运岁 == 9.0
        assert res.dayun.起运年 == 1993

    def test_qiyun_3_4_rounds_down_to_3(self, tmp_path):
        """3.4 round → 3 → birth_year+3=1987（< 0.5 时下取整）"""
        text = _make_minimal_input(qiyun_sui=3.4, qiyun_year=1987)
        res = _parse_string_to_input(text, tmp_path)
        assert res.dayun.起运年 == 1987

    def test_old_floor_value_now_rejected(self, tmp_path):
        """3.586 + 起运年=1987（旧 floor 行为）→ 应拒绝，提示用 round。"""
        from tools.preflight import PreflightError
        text = _make_minimal_input(qiyun_sui=3.586, qiyun_year=1987)
        with pytest.raises(PreflightError) as exc:
            _parse_string_to_input(text, tmp_path)
        assert "round(起运岁)" in str(exc.value)


# ============================================================
# CFL-C016-002: D3 应期前向预测模式 ★ 上限 4
# ============================================================

class TestCFLC016_002_GateForwardPredictionCap:
    """gate_yingqi(verified=False) 在 3 层齐备时也应 ★ ≤ 4。"""

    def test_compute_yingqi_confidence_verified_default_true(self):
        """verified 默认 True，向后兼容 — 3 层齐备 + 强触发可上 ★5。"""
        from engine.yingqi.gate import compute_yingqi_confidence
        from engine.yingqi.types import TriggerEvent
        triggers = [
            TriggerEvent(type="倒象成立", target="子", evidence_chars=["子"],
                         rationale="ok"),
        ]
        conf = compute_yingqi_confidence(
            passed_layers=3,
            triggers=triggers,
            primary_trigger=triggers[0],
            l2_via_transition=False,
            upstream_consistent=True,
        )
        assert conf.star == 5  # 默认 verified=True → 走 ★5 路径

    def test_compute_yingqi_confidence_verified_false_caps_at_4(self):
        """verified=False（前向预测）即使 3 层齐备 + 强触发也最多 ★4。"""
        from engine.yingqi.gate import compute_yingqi_confidence
        from engine.yingqi.types import TriggerEvent
        triggers = [
            TriggerEvent(type="倒象成立", target="子", evidence_chars=["子"],
                         rationale="ok"),
        ]
        conf = compute_yingqi_confidence(
            passed_layers=3,
            triggers=triggers,
            primary_trigger=triggers[0],
            l2_via_transition=False,
            upstream_consistent=True,
            verified=False,
        )
        assert conf.star == 4, f"verified=False ★ 应上限 4，得到 {conf.star}"

    def test_posterior_capped_to_star_band(self):
        """★ 被压低后，posterior 应同步 cap 到该 ★ 区间上限（避免 E1 lint 告警）。"""
        from engine.yingqi.gate import compute_yingqi_confidence
        from engine.yingqi.types import TriggerEvent
        triggers = [
            TriggerEvent(type="倒象成立", target="子", evidence_chars=["子"],
                         rationale="ok"),
        ]
        conf = compute_yingqi_confidence(
            passed_layers=3,
            triggers=triggers,
            primary_trigger=triggers[0],
            l2_via_transition=False,
            upstream_consistent=True,
            verified=False,
        )
        # ★4 区间 [0.70, 0.84]
        assert conf.star == 4
        assert 0.70 <= conf.percent <= 0.84, (
            f"★4 时 percent 应在 [0.70, 0.84]，得到 {conf.percent}"
        )

    def test_passed_layers_2_verified_false_caps_at_3(self):
        """passed=2 + verified=False → ★ 上限 4 - 1 = 3。"""
        from engine.yingqi.gate import compute_yingqi_confidence
        from engine.yingqi.types import TriggerEvent
        triggers = [
            TriggerEvent(type="本字到", target="子", evidence_chars=["子"],
                         rationale="ok"),
        ]
        conf = compute_yingqi_confidence(
            passed_layers=2,
            triggers=triggers,
            primary_trigger=triggers[0],
            l2_via_transition=False,
            upstream_consistent=True,
            verified=False,
        )
        # passed=2 → gate_ceiling=4 → -1 = 3
        assert conf.star <= 3


# ============================================================
# CFL-C016-002 (KnownFact.应验度 → verified 路由)
# ============================================================

class TestCFLC016_002_KnownFactVerifiedRouting:
    """KnownFact.应验度 ≥ 0.7 → verified=True；< 0.7 → False。"""

    def test_known_fact_default_verified_legacy(self):
        """KnownFact 默认 应验度=1.0（legacy compat）→ verified=True。"""
        from engine.predicates.types import KnownFact
        kf = KnownFact(type="婚姻", year=2010, event="结婚")
        assert kf.应验度 == 1.0

    def test_extract_candidates_returns_4_tuple(self):
        """_extract_candidates 返回 (year, event, domain, verified) 4 元组。"""
        from engine.pipeline import _extract_candidates
        from engine.predicates.types import ParsedInput, KnownFact

        stub = ParsedInput.__new__(ParsedInput)
        object.__setattr__(stub, "known_facts", [
            KnownFact(type="婚姻", year=2010, event="结婚", 应验度=1.0),
            KnownFact(type="事业", year=2026, event="升迁", 应验度=0.0),
        ])
        cands = _extract_candidates(stub)
        assert len(cands) == 2
        assert cands[0] == (2010, "结婚", "婚姻", True), \
            f"应验度=1.0 → verified=True，得到 {cands[0]}"
        assert cands[1] == (2026, "升迁", "事业", False), \
            f"应验度=0.0 → verified=False，得到 {cands[1]}"

    @pytest.mark.parametrize("应验度,expected", [
        (1.0, True),
        (0.7, True),    # 边界
        (0.69, False),
        (0.5, False),
        (0.0, False),
    ])
    def test_verified_threshold_at_0_7(self, 应验度, expected):
        from engine.pipeline import _extract_candidates
        from engine.predicates.types import ParsedInput, KnownFact

        stub = ParsedInput.__new__(ParsedInput)
        object.__setattr__(stub, "known_facts", [
            KnownFact(type="事业", year=2020, event="x", 应验度=应验度),
        ])
        _, _, _, verified = _extract_candidates(stub)[0]
        assert verified is expected


# ============================================================
# CFL-C016-004 / 005: run_pipeline 入口 adapt + 出口挂 _parsed
# ============================================================

class TestCFLC016_004_005_PipelineAdaptAndMount:
    """run_pipeline 应该 (a) 接受 preflight.ParsedInput 不崩，
    (b) 在 output._parsed 挂 adapt 后的 parsed，
    (c) retrospective 不因 DayunStep.起讫年 失败。"""

    def test_run_pipeline_accepts_preflight_parsed_input(self):
        """直接传 preflight.ParsedInput 不再崩（CFL-005 retrospective 不再 warn）。"""
        from tools.preflight import parse
        from engine.pipeline import run_pipeline
        import pathlib
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        case_path = repo_root / "cases" / "C-2026-016-甲子丙子丙戌戊子" / "input.md"
        if not case_path.exists():
            pytest.skip(f"案例不存在: {case_path}")
        parsed = parse(case_path)  # 注意：未 adapt_parsed
        out = run_pipeline(parsed, write_findings=False)
        assert out is not None

    def test_output_parsed_attribute_set(self):
        """run_pipeline 出口必须设置 output._parsed。"""
        from tools.preflight import parse
        from engine.pipeline import run_pipeline
        import pathlib
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        case_path = repo_root / "cases" / "C-2026-016-甲子丙子丙戌戊子" / "input.md"
        if not case_path.exists():
            pytest.skip(f"案例不存在: {case_path}")
        parsed = parse(case_path)
        out = run_pipeline(parsed, write_findings=False)
        assert hasattr(out, "_parsed"), "output._parsed 未挂载"
        assert out._parsed is not None
        # 必须是 adapt 后的（有 day_master 等属性）
        assert hasattr(out._parsed.bazi, "day_master"), \
            "output._parsed 必须是 engine.predicates.types.ParsedInput（带 day_master）"

    def test_retrospective_no_attribute_error(self, caplog):
        """retrospective scan 不应再因 'DayunStep.起讫年' 失败而 warn。"""
        from tools.preflight import parse
        from engine.pipeline import run_pipeline
        import pathlib
        import logging
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        case_path = repo_root / "cases" / "C-2026-016-甲子丙子丙戌戊子" / "input.md"
        if not case_path.exists():
            pytest.skip(f"案例不存在: {case_path}")
        parsed = parse(case_path)
        with caplog.at_level(logging.WARNING):
            out = run_pipeline(parsed, write_findings=False)
        assert hasattr(out, "retrospective")
        for record in caplog.records:
            assert "起讫年" not in record.getMessage(), (
                f"CFL-005 修复后不应再有 起讫年 warning：{record.getMessage()}"
            )


# ============================================================
# CFL-C016-003: 模板 § 一 能量等级 / 置信度分行
# ============================================================

class TestCFLC016_003_TemplateEnergyClarity:
    """report-v1.3.md § 一 应该把命主能量等级和引擎置信度分两行展示。"""

    def test_template_has_separate_energy_and_confidence_lines(self):
        import pathlib
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        tpl = (repo_root / "templates" / "report-v1.3.md").read_text(encoding="utf-8")
        assert "**命主能量等级**" in tpl, \
            "模板必须包含 '命主能量等级' 标题（CFL-003）"
        assert "**引擎置信度" in tpl, \
            "模板必须包含 '引擎置信度' 标题（CFL-003）"
        assert "**整体能量**：{{ energy_ordinal }} ({{ energy_score_pct }}%)" not in tpl, \
            "旧的 '整体能量：(评分%)' 显式格式应已替换"
