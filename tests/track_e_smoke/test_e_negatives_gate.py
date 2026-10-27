"""pytest 门禁适配层：把 Track-E 8 条负向自测接进日常门禁。

`tests/track_e_smoke/test_e_negatives.py` 不是假测试：它第 17 行自述「不依赖 pytest，
纯 stdlib」，用 `_Reporter.add()` 计数并在 `main()` 里以退出码表达结果
（直接跑实测 `PASS=8 FAIL=0 EXIT=0`）。

**为什么要单独开一个适配文件**：该文件的 8 个函数都叫 `test_E00x(...)`，形参是
`(rep: _Reporter, tmp: Path)` 这类普通参数而非 pytest fixture。一旦把
`test_e_negatives.py` 本身放进 `testpaths`，pytest 会按 `python_functions = ["test_*"]`
把 8 个函数逐个收走并报 `fixture 'rep' not found`。所以门禁只收本文件，
由它调用对方唯一的公共入口 `main()`——**对方那 8 条断言一行未改**。
"""

from __future__ import annotations

from tests.track_e_smoke.test_e_negatives import main


def test_track_e_negatives() -> None:
    assert main() == 0
