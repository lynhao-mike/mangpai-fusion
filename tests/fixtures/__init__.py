"""tests/fixtures · v1.2 测试夹具

- ``cases.py`` 提供 10 旧案 input.md 的 fixture 加载器
- ``feedback_ground_truth.yaml`` 含 3 真实失验案例的 ground truth
- ``v1_0_baseline.yaml`` 含 v1.0 当前实绩基线（v1.2 必须超过）

加载示例：
    >>> from tests.fixtures.cases import load_case, list_real_cases
    >>> parsed = load_case("C-2026-001")  # 短形式自动找完整目录
    >>> parsed = load_case("C-2026-001-庚申戊寅壬子辛丑")  # 完整形式
"""
from __future__ import annotations
