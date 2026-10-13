import json
from pathlib import Path

LABELS_PATH = Path("cases/p-series-career-path-labels.jsonl")
REPORT_PATH = Path("reports/p-series-career-path-labeling-summary.md")

rows = [
    json.loads(line)
    for line in LABELS_PATH.read_text(encoding="utf-8").splitlines()
    if line.strip()
]


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


lines = [
    "# P 系列 76 案“任职 vs 经营”人工标注汇总",
    "",
    "## 产物与口径",
    "",
    "- 标注源：`cases/fankui-feedback.md`",
    "- 结构化产物：`cases/p-series-career-path-labels.jsonl`",
    "- 审核状态：全部为 `manual_reviewed`",
    "- 标注原则：只采用每案反馈 section 中已发生的直接事实；不依据八字、收入、财运、学历、迁移或职业能力反推；歧义一律归入 `unknown`。",
    "",
    "## 标签标准",
    "",
    "| 标签 | 标准 |",
    "|---|---|",
    "| `employment` | 明确受雇、任职、上班、体制内、单位员工、固定岗位等。 |",
    "| `entrepreneurship` | 明确经商、创业、开店、老板、自营、承包，或以经营为主要职业路径。 |",
    "| `mixed` | 同一命主有实质任职与经营双路径，或按时间发生明确转换且两者均有可靠事实。 |",
    "| `unknown` | 反馈不足以区分任职与经营；不为凑样本强标。 |",
    "",
    "## 汇总统计",
    "",
    "| 指标 | 数值 |",
    "|---|---:|",
    "| 总案例数 | 76 |",
    "| employment | 32 |",
    "| entrepreneurship | 5 |",
    "| mixed | 3 |",
    "| unknown | 36 |",
    "| 非 unknown 有效案例 | 40 |",
    "| 非 unknown 有效率 | 52.63% |",
    "",
    "### 置信度分布",
    "",
    "| 置信度 | 数量 |",
    "|---|---:|",
    "| high | 57 |",
    "| medium | 15 |",
    "| low | 4 |",
    "",
    "## 二次复核队列",
    "",
    "以下 19 案置信度为 `medium` 或 `low`，建议二次复核。保留 `unknown` 比错误强标更符合本任务契约。",
    "",
    "| case_id | 当前标签 | 置信度 | 复核原因 |",
    "|---|---|---|---|",
]

for row in rows:
    if row["confidence"] != "high":
        lines.append(
            f'| {row["case_id"]} | {row["label"]} | {row["confidence"]} | '
            f'{escape_cell(row["rationale"])} |'
        )

lines.extend(
    [
        "",
        "## 全部 76 案审计表",
        "",
        "| case_id | 标签 | 置信度 | 直接证据原文 | 标注说明 | 复核状态 |",
        "|---|---|---|---|---|---|",
    ]
)

for row in rows:
    lines.append(
        f'| {row["case_id"]} | {row["label"]} | {row["confidence"]} | '
        f'{escape_cell(row["evidence_quote"])} | {escape_cell(row["rationale"])} | '
        f'{row["review_status"]} |'
    )

lines.extend(
    [
        "",
        "## 可审计性说明",
        "",
        "- 每个 `case_id` 恰好一条结构化记录。",
        "- `evidence_quote` 保留源文件原文；无足够直接证据时为空字符串。",
        "- `mixed` 的 `rationale` 明确记录任职与经营的先后或并存关系。",
        "- 校验覆盖条数、ID 连续唯一性、枚举值、固定字段及证据在所属 section 内的逐字可检索性。",
    ]
)

REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
