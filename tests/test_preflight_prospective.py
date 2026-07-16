from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROSPECTIVE_INPUT = Path(
    "cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md"
)


def test_preflight_accepts_contractual_prospective_raw_input() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.preflight", str(PROSPECTIVE_INPUT)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "P-GO-2026-001-坤-壬戌己酉乙卯丁亥" in result.stdout
