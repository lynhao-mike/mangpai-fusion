# Calibration v2 · 2041 生产规则闭环口径

本目录用于 2041 条生产规则库的新校准闭环，避免继续混用旧 Phase-300 基线。

## 基线

- 子平：933 条，来源 [`theory/ziping/index.yaml`](../../theory/ziping/index.yaml)
- 滴天髓：1108 条，来源 [`theory/tiaohou_ditiansui/index.yaml`](../../theory/tiaohou_ditiansui/index.yaml)
- 合计：2041 条

## 硬门槛

1. 只有 [`statement_records.json`](../../cases/) 中 `rule_id / family_id / school / canon / rule_type` 完整的反馈行可进入学习。
2. `UNMAPPED`、`needs_mapping_repair=true`、无结构化 statement record 的反馈行禁止进入规则级学习。
3. `quantifiable=false` 的规则只做解释，不计 hit/miss。
4. `rule_type=TIMING` 独立进入应期 lane，不与结构主票混算。
5. 旧 [`META/phase-300-calibration.md`](../phase-300-calibration.md) 仅保留历史追溯，不作为 2041 规则库当前有效性依据。

## 首批白名单样本标准

- 反馈为明确 `y` 或 `n`
- statement_id 可命中 statement_records
- rule_id 是生产规则 ID 或已确认可学习旧规则 ID
- 非 fallback 启发式路径
- 每条反馈只对应单一可解释断语，避免多断语共用一个 verdict
