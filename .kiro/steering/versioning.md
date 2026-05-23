# 版本号同步规则

> inclusion: auto

## 规则

每次对 `engine/`、`tools/`、`templates/` 目录下的 `.py` 或 `.md` 文件做出功能性改动时，必须同步更新版本号：

1. **`VERSION` 文件**（仓库根目录）：纯文本，仅一行 `X.Y.Z`
2. **`engine/__init__.py`** 中的 `__version__ = "X.Y.Z"`
3. **commit message** 中标注新版本号（如 `bump: 1.2.1`）

## 版本号规则（语义化）

- **MAJOR (X)**：不兼容的 API 变更（如 GateResult 字段删除/重命名）
- **MINOR (Y)**：新增功能（如新增 Track/新增 domain/新增触发类型）
- **PATCH (Z)**：bug 修复 / 文档修正 / 测试补充

## 当前版本

`1.2.0`（v1.2 首发）

## 自动检查

commit 前确认：
```bash
cat VERSION                           # 应与本次改动匹配
grep __version__ engine/__init__.py   # 应与 VERSION 一致
```

若忘记更新，下次 commit 时补一个 `bump: X.Y.Z` commit。
