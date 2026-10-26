# T-114 · 脱敏逻辑生产化（tools/bundle_sanitize.py）

- 状态：🔵 Ready for Execution
- 优先级：P1（门禁相关，但不阻塞断语条件化）
- 创建：2026-10-26（中枢）
- 来源：`tests/tools/test_bundle_pii.py` 依赖的 `.workbuddy-ai/make_bundle_v2.py` 已不存在；该目录被 `.gitignore` 忽略，默认 `pytest -q` 曾因此在收集阶段直接失败。

## 目标

把 `sanitize_input` 的脱敏逻辑做成受版本控制的生产模块，测试改为导入它，从而：

1. 默认门禁 `pytest -q` 真正变绿（不是 skip）；
2. 脱敏规则可维护、可回归；
3. `tools/blind_candidate_pick.py` 不再指向仓库外脚本。

## 验收

```bash
python -m pytest tests/tools/test_bundle_pii.py -q -o addopts="-ra --tb=short"   # 全绿，不 skip
python -m pytest -q                                                              # 无 skipped
python -m tools.bundle_sanitize <样例 input.md>                                   # 输出仍为合法 YAML
```

## 硬约束

- 契约以 `tests/tools/test_bundle_pii.py` 的用例为准（剥离：精确出生时刻 / 出生地 / 命主代号 / 来源路径 / 指纹行；保留：性别乾坤 / 口径说明 / 四柱与全部命理内容）。
- 不得改动该测试的断言；只允许改导入路径与删除过渡 skip 段。
- 完成后：删除 `tests/tools/test_bundle_pii.py` 顶部的 skip 段；更新 `AGENTS.md` §5「已知红灯」；把 `tools/blind_candidate_pick.py` 的提示改为新入口。

## File Scope

- `tools/bundle_sanitize.py`（新建）
- `tests/tools/test_bundle_pii.py`（仅导入段）
- `tools/blind_candidate_pick.py`（提示文案）
- `AGENTS.md` §5（删除红灯说明）
