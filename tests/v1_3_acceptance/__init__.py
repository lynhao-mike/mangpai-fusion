"""v1.3 验收门槛 H1-H6（plans/architecture-v1.3.md § 六）。

H1 statement_id 稳定性
H2 双版报告差分校验
H3 feedback_ingest 解析正确率
H4 边界挖掘可解释性（软指标，人工 review，不在自动测试中）
H5 自迭代不退化（依赖 G1-G6 v1.2 门槛存在，由 CI 单独跑回归）
H6 完整闭环跑通

H1-H3 + H6 落到本目录的 pytest 测试文件中。
所有测试打 ``pytest.mark.v1_3_acceptance`` 标签。
"""
