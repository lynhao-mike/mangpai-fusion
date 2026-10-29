# T-195b STATUS

- 状态：🟢 Delivered（15/15；待中枢按 97 项评分）
- 执行者：子代理 AW（未污染）
- 任务卡：`tasks/T-195b/PROMPT.md`
- 验收：中枢按 97 项算 recall；runner 不自评

## 交付物

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| `META/r-tool-run-routing-v1.json` | 172037 | `9774d7d7074750f41a0fe6fa874af027e2442fa08d55756ba1bbf05b12840290` |
| `tasks/T-195b/run_r_tool_routing.py` | 12873 | `eb1cd1ce821e37a3e72fbe25ff29af78cd442b87e8dc4aa161ac9ecdcaf38f1f` |
| `tasks/T-195b/verify_pack.py` | 7280 | `2a62aa50568c9679c9d858ed84fc3375d84a8f39c502700f3852e1cb7c691977` |
| `tasks/T-195b/BRIEF.md` | 6882 | `18e841dae9ae06ee2b47889d095907fecd39a2e74a18f51edf9e1d559eb8867b` |

输入 `META/routing-questions-runner-v1.json` SHA-256：`fd2876ad6d4e6b682337d7e94d0e13aed8a89aebf83b439de18391c905c8163c`（5559 字节，与任务卡 `fd2876ad…` 一致）。

## 硬约束自检

- 读到 `expected_evidence`：**否**
- 读到 `META/routing-prereg-v1.json`：**否**
- 读到任何 answers / anchor / fresh / holdout / golden / `p1-system-run*`：**否**
- 重跑 fixed-20：**否**
- 评分 / 自评：**否**
- git 写：**否**

## 结果摘要

- 证据包：**15/15**，无缺题、无空包
- 证据项：**116** = 宫位 37 + 关系边 49 + `source_ref` 30
- `out_of_class_emissions`：**0**；所有边 `direction=undetermined`、`actor=null`、`target=null`
- 独立核验 `tasks/T-195b/verify_pack.py`：退出码 **0**（`PASS: 15/15 packs, evidence items resolvable, quotes verbatim, no direction`）
- 输出 JSON 全文扫描：`expected_evidence` / `is_conclusion` / `fixed_facts` / `party_direction` token 均为 0
- 本包不含量化评分；macro_recall 由中枢计算

## Execution Log

| 时间 | 动作 |
|---|---|
| 00:10 | T-195 routing 泄漏作废；sanitized 15 题 hash fd2876ad；派 T-195b |
| 00:06 | 读任务卡 / R 规格 / sanitized runner / T-195 runner 可见逻辑；确认输入 hash `fd2876ad…` |
| 00:07 | 写 `tasks/T-195b/run_r_tool_routing.py`（导入 T-195 routing 逻辑，输入改 sanitized）并跑通：15/15、116 证据项 |
| 00:08 | 写 `tasks/T-195b/verify_pack.py` 独立核验通过（退出码 0） |
| 00:09 | 写 `BRIEF.md` / 更新 `STATUS.md`；记录 hash；未评分、未做 git 写 |
| 00:12 | 清理输出 JSON 中的字段名 token（否定声明去字段名），重跑后 token 扫描全 0；更新全部 hash |
