# 子平生产规则库

本目录存放已接入默认分析 pipeline 的子平正式生产规则。

- 生产规则入口：`index.yaml`
- 状态要求：顶层 `status: active`，单条规则 `status: active`
- 来源材料：`sources/ziping/`
- 旁路候选材料仍保留在 `theory/raw/yaml/`，不得由生产加载器读取
