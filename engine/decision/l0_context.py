"""L0 上下文事实账本最小实现。

只隔离自由文本事实与分析焦点，不污染排盘事实。
"""

from __future__ import annotations

from engine.decision.models import ContextFactLedger


def build_context_ledger(blocks: dict[str, str], unknown_blocks: list[str]) -> ContextFactLedger:
    """从 L0 文本区块构造上下文账本。"""

    return ContextFactLedger(
        known_fact_text=blocks.get("KNOWN_FACTS", ""),
        analysis_focus_text=blocks.get("FOCUS", ""),
        preserved_text_blocks=[f"${name}\n{blocks[name]}" for name in unknown_blocks],
    )
