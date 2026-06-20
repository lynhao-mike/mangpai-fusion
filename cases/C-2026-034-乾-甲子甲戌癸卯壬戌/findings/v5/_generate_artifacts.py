from __future__ import annotations

import json
from pathlib import Path

from engine.v5 import run_v5
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence

CASE_ID = "C-2026-034-乾-甲子甲戌癸卯壬戌"
BASE = Path("cases") / CASE_ID / "findings" / "v5"
BASE.mkdir(parents=True, exist_ok=True)

chart = {
    "case_id": CASE_ID,
    "sex": "乾造",
    "solar": "1984-11-05 20:25:00",
    "pillars": ["甲子", "甲戌", "癸卯", "壬戌"],
    "day_master": "癸",
    "month_command": "戌月，戊土司令",
    "current_luck": "己卯，2025-2034",
    "luck_sequence": ["乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未"],
    "known_feedback": "暂无命主现实反馈",
}


def ev(evidence_id: str, source: str, text: str, *rules: str) -> V5Evidence:
    return V5Evidence(
        evidence_id=evidence_id,
        source=source,
        text=text,
        node_refs=["chart:root"],
        rule_ids=list(rules),
    )


claims = [
    V5Claim(
        claim_id="v5-034-ziping-structure-001",
        school="ziping",
        domain="总体",
        claim_type="structure_claim",
        claim="癸水生戌月，戊土司令，年支子禄与时干壬劫使日主有根有帮；年月甲木、日支卯木泄秀，双戌藏官印财，结构为身有根、食伤旺、官杀暗重、财藏待引。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★★", 0.80, "子平结构证据清晰，但暂无现实反馈"),
        evidence=[ev("v5ev-034-zp-001", "input.md", "四柱甲子、甲戌、癸卯、壬戌；戌月戊土司令；子为癸禄，壬水帮身。", "ZP-STRUCTURE")],
        probabilistic=False,
        falsifiable="若现实长期无表达/技术/项目输出特征，则食伤主线需降权。",
    ),
    V5Claim(
        claim_id="v5-034-ziping-career-001",
        school="ziping",
        domain="事业",
        claim_type="structure_claim",
        claim="事业不宜按单纯自由才艺看，应按伤官食神输出纳入官杀规则平台论；2015-2034 官杀运连续，是责任、职位、项目与合规压力递增期。",
        stance="support",
        polarity="positive",
        confidence=V5Confidence("★★★★", 0.78, "大运与原局同向"),
        evidence=[ev("v5ev-034-zp-career", "input.md", "戊寅、己卯两步官杀运接续，原局甲卯食伤成势、双戌官库重。", "ZP-LUCK-CAREER")],
        timing_hints=[{"window": "2015-2034", "type": "dayun"}],
        probabilistic=True,
        falsifiable="若2015后完全无责任、岗位、项目或规则压力变化，则此命题需回调。",
    ),
    V5Claim(
        claim_id="v5-034-ditiansui-structure-001",
        school="ditiansui",
        domain="总体",
        claim_type="structure_claim",
        claim="戌月癸水重在润燥与通关；局中子壬可润、甲卯可泄，双戌使土燥成病。成败关键是先有水源与制度承载，再引财火，不可火土燥烈而失衡。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★★", 0.76, "调候病药明确"),
        evidence=[ev("v5ev-034-dts-001", "input.md", "戌月燥土、双戌夹卯，子水壬水为润源，甲卯泄秀引火。", "DTS-QI-FLOW")],
        probabilistic=False,
        falsifiable="若火土旺年反而无钱事/健康/压力同题，则火土风险需降权。",
    ),
    V5Claim(
        claim_id="v5-034-ditiansui-health-001",
        school="ditiansui",
        domain="健康",
        claim_type="counter_claim",
        claim="健康判断不宜铁口重疾，应降级为燥土压力型风险：脾胃代谢、睡眠焦虑、炎症、血压血脂与水系统恢复力管理。",
        stance="support",
        polarity="negative",
        confidence=V5Confidence("★★★", 0.68, "有结构风险但无病史反馈"),
        evidence=[ev("v5ev-034-dts-health", "input.md", "戌月戊土司令、双戌燥土，癸水被甲卯泄，子壬仍可恢复。", "DTS-HEALTH-BOUNDARY")],
        timing_hints=[{"window": "2024-2027", "type": "liunian_cluster"}],
        probabilistic=True,
        falsifiable="若2024-2027无体检异常、睡眠压力或脾胃炎症问题，则该风险窗口需降权。",
    ),
    V5Claim(
        claim_id="v5-034-gao-work-001",
        school="gao_dechen",
        domain="事业",
        claim_type="event_claim",
        claim="做功路径在水木输出打土中财官：以技能、方案、内容、销售、产品、项目协调、工程流程或资源整合变现，越到中年越需要合同、流程与交付边界。",
        stance="support",
        polarity="positive",
        confidence=V5Confidence("★★★★", 0.79, "做功路径与既有报告一致"),
        evidence=[ev("v5ev-034-gao-work", "input.md", "年柱甲子、月柱甲戌、日坐癸卯、时柱壬戌形成水木输出与双戌责任库。", "GAO-ZUOGONG")],
        timing_hints=[{"window": "2025-2034", "type": "dayun"}],
        probabilistic=True,
        falsifiable="若职业完全不依赖输出、项目、客户或规则平台，则做功取象需复核。",
    ),
    V5Claim(
        claim_id="v5-034-gao-wealth-001",
        school="gao_dechen",
        domain="财富",
        claim_type="event_claim",
        claim="财在双戌库中，靠项目、客户、房土、合作、火土年份引出；2026-2027 财星透旺，机会与支出压力并见，忌高杠杆、担保与口头合伙。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★★", 0.75, "财库与流年触发明确"),
        evidence=[ev("v5ev-034-gao-wealth", "input.md", "丙丁财藏戌，2026丙午、2027丁未引财，未戌刑动库。", "GAO-WEALTH-VAULT")],
        timing_hints=[{"window": "2026-2027", "type": "liunian"}],
        probabilistic=True,
        falsifiable="若2026-2027无收入、投资、家庭资产或大额支出议题，则财库触发需降权。",
    ),
    V5Claim(
        claim_id="v5-034-duan-event-001",
        school="duan_jianye",
        domain="婚姻",
        claim_type="event_claim",
        claim="乾造以财为妻，财藏双戌，夫妻宫卯合戌火，婚缘有但不轻松，多与房宅、钱事、父母家族、事业节奏和责任绑定；2025-2027 为关系财务沟通重点期。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★", 0.69, "婚姻需现实状态反馈校准"),
        evidence=[ev("v5ev-034-duan-marriage", "input.md", "日支卯、月时双戌、卯戌合火，财星藏戌，日柱红鸾、年支桃花。", "DUAN-MARRIAGE-PALACE")],
        timing_hints=[{"window": "2025-2027", "type": "liunian_cluster"}],
        probabilistic=True,
        falsifiable="若婚恋、家宅、财务责任完全不绑定，则婚姻事件取象需回调。",
    ),
    V5Claim(
        claim_id="v5-034-duan-career-001",
        school="duan_jianye",
        domain="事业",
        claim_type="event_claim",
        claim="事业宫甲戌显示伤官坐官库：有专业判断和表达能力，也容易与规则、上级、合同、流程发生拉扯；适合把观点变成制度化交付。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★★", 0.77, "宫位与十神落点明确"),
        evidence=[ev("v5ev-034-duan-career", "input.md", "月柱甲戌为事业环境，伤官临官库；时柱壬戌为后续资源责任。", "DUAN-CAREER-PALACE")],
        timing_hints=[{"window": "2015-2034", "type": "dayun"}],
        probabilistic=True,
        falsifiable="若长期无上级/制度/合同/交付矛盾，则官库压力需降权。",
    ),
    V5Claim(
        claim_id="v5-034-yang-image-001",
        school="yang_qingjuan",
        domain="性格",
        claim_type="event_claim",
        claim="命主聪明、反应快、有表达欲和方案意识，外柔内倔，讲逻辑也讲感受；压力大时容易话直、焦虑、睡眠和脾胃先受影响。",
        stance="support",
        polarity="mixed",
        confidence=V5Confidence("★★★★", 0.82, "画像证据集中但仍待反馈"),
        evidence=[ev("v5ev-034-yang-personality", "input.md", "年月两甲伤官，日坐卯食神，年支子禄，时干壬劫，月时双戌。", "YANG-IMAGE")],
        probabilistic=False,
        falsifiable="若命主现实长期不表现表达欲、主见和规则敏感，则画像需修正。",
    ),
    V5Claim(
        claim_id="v5-034-yang-family-health-001",
        school="yang_qingjuan",
        domain="健康",
        claim_type="event_claim",
        claim="2024-2027 易出现钱事、家宅、关系、压力与身体管理同题，重点关注体检、睡眠、脾胃代谢、炎症、牙齿皮肤与筋骨。",
        stance="support",
        polarity="negative",
        confidence=V5Confidence("★★★", 0.66, "细节风险需反馈验证"),
        evidence=[ev("v5ev-034-yang-health", "input.md", "2024甲辰冲戌，2025乙巳、2026丙午、2027丁未火土渐旺，原局双戌燥土。", "YANG-HEALTH-DETAIL")],
        timing_hints=[{"window": "2024-2027", "type": "liunian_cluster"}],
        probabilistic=True,
        falsifiable="若该阶段无压力体感、体检或家宅钱事同题，则健康细节取象需降权。",
    ),
]

output = run_v5(chart, case_id=CASE_ID, claims=claims)
artifacts = {
    "chart-model.json": chart,
    "school-claims.json": [claim.to_dict() for claim in claims],
    "structure-graph.json": output.structure_graph.to_dict(),
    "arbitration.json": [item.to_dict() for item in output.arbitration_results],
    "prediction-ledger.json": output.prediction_ledger.to_dict(),
    "learning-signals.json": [item.to_dict() for item in output.learning_signals],
    "v5-output.json": output.to_dict(),
}
for name, payload in artifacts.items():
    (BASE / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"wrote {len(artifacts)} artifacts to {BASE}")
print(f"claims={len(output.claims)} arbitration={len(output.arbitration_results)} predictions={len(output.prediction_ledger.predictions)}")
