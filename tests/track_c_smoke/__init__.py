"""tests/track_c_smoke · Track-C 验收测试

5 项验收（08 § 六 Track-C 行）：
    C-001 C-2026-001 year=2005 婚姻       → passed_layers=3, ★≥4
    C-002 C-2026-001 year=2013 婚姻       → passed_layers≤1（picture_consistent=False）
    C-003 C-2026-001 year=2020 六亲(母)   → passed_layers=3, ★★★★★
    C-004 C-2026-001 year=2020 事业       → passed_layers≥2
    C-005 C-2026-014 year=2024 学业       → passed_layers≥2

C-001 + C-002 是 v1.2 的 G2 圣杯：v1.0 婚期偏差 8 年的修复。
"""
