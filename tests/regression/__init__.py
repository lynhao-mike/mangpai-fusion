"""tests/regression · v1.2 整合回归测试套件

把 Track-A/E/G 已有的 smoke 整合为统一 pytest 测试集，并加入 v1.2 vs v1.0
的 6 项发布门槛断言。

子模块：
    test_a_energy.py        - 整合 Track-A A-001~A-005（D1 段派能量）
    test_e_guardrails.py    - 整合 Track-E E-001~E-008（兜底护栏负向测试）
    test_g_iteration.py     - 整合 Track-G G-001（自迭代回放）
    test_v1_2_vs_v1_0.py    - v1.2 严格优于 v1.0 的 6 项断言（决策 I）
"""
from __future__ import annotations
