# 紫微斗数旁证接入设计 · evidence-envelope/v1

> 状态：**阶段 1–4 全部落地、验收通过，2026-11-11 已入库**（commit `87fc5a29`，19 文件 / +3182 行）｜ 2026-11-10 提案 · 同日实施
> 关联约束：`AGENTS.md` §1 铁律、`docs/analysis_human_touch.md`、`templates/report-v7-human.md`、`pyproject.toml`、`requirements.txt`、`tests/` 均为保护区，**本方案不改动其中任何文件**。
> 数据侧始终只读：`F:\ziwei-data` 与 `ziwei-doushu` 项目目录**未写入任何文件**；查表与建索引都在内存/系统临时目录完成，写入只发生在本仓库的 `bridges/`、`config/`、`tools/`、`docs/`、`README.md` 与项目日志。

---

## 0. 现场核实的事实（数字均为本机实跑）

| 对象 | 实际情况 |
|---|---|
| 八字项目 | `F:\综合盲派\mangpai-fusion`，Python，远端 `github.com/lynhao-mike/mangpai-fusion`，分支 `main`；事实入口 `python -m engine.cli {chart,relations,strength,shensha,structures,all}` |
| 紫微项目 | `C:\Users\Administrator\WorkBuddy\倪海厦\ziwei-doushu`，Next.js 16 / TypeScript，远端 `github.com/Renhuai123/ziwei-doushu`；代码 MIT，排盘引擎 `lib/ziwei/algorithm.ts`，本地接口 `POST /api/chart` 返回完整 `ZiweiChart` JSON（无需联网/API Key） |
| 数据包 | `F:\ziwei-data\analysis`，**5.7 GB**，77 个 `year-YYYY.jsonl.zst`（各约 2 MB）+ 77 个 `.idx.json`（约 340 KB）+ 8 个已解压 `.jsonl`（各约 700 MB） |
| 数据性质 | 不是排盘事实，是 **v4.0 解读数据集**「13 维断语文本」：674,976 张盘 × 13 维，每张约 3 万字 Markdown，解压全量 56.6 GB；内容版本 `ca268829f7a9` |
| 索引结构 | `year-YYYY.idx.json` = `{"2001-12-31-3-female": [710394103, 84563], ...}`，即「键 → 解压后明文 JSONL 的字节偏移与行长」，单盘可 O(1) 定点读取 |
| 目标盘验证 | 键 `2001-12-31-3-female` 命中；`ms = null`（命宫空宫）；13 维齐；`career` 2271 字、`wealth` 1564 字、`overview` 4792 字 |
| 本机能力 | Node `v22.22.2` 内置 `zlib.createZstdDecompress()`；Python venv 无 `zstandard`，**无需安装任何新依赖** |
| 许可 | 数据 CC BY 4.0（可商用，**唯一要求保留署名**）；解读中引用的倪海厦《天纪》原话不在授权内，属 CC BY-NC-SA 4.0（非商用） |

**口径天然对齐**：数据集 README 第 152 行明确「按时辰序号直接排盘，未按出生地做真太阳时校正」；八字项目该盘 `true_solar_corrected = null`、出生地经度未给。两边当前都不做真太阳时校正，这是可以直接对齐的前提。

---

## 1. 核心判断：接进来的是「旁证」，不是「事实」

`AGENTS.md` §1 规定：确定性盘面事实**只从** `engine.cli` 取，理论证据**只从** `tools.query_theory` 取，Agent 负责裁决。紫微数据集给的是**另一套体系的自然语言断语**，既不是八字盘面事实，也没有指向四派经典的 `source_ref`。

因此融合的巧妙之处不是「把紫微并进引擎」，而是**新开第三类输入通道**，并把铁律写进数据结构而不是只写在文档里：

```
事实层   engine.cli            ← 唯一可核验，不动
理论层   tools.query_theory    ← source_ref，不动
旁证层   evidence-envelope/v1 ← 新增：紫微 / 未来奇门、占星等一律挂这里
裁决层   Agent + cross_check   ← 新增：输出「收敛 / 分歧 / 不核验」三态
```

信封里强制带 `not_usable_as: ["engine_fact", "theory_source_ref"]`。这样即使将来有人把紫微文本误喂给 Linter 或格局判定，也能在结构上被拒绝。**上一轮那份紫微对账表，就是这套机制的人工版本。**

紫微侧再分两级，别混为一谈：

| 级 | 来源 | 性质 | 用法 |
|---|---|---|---|
| L1 结构化盘面 | `lib/ziwei/algorithm.ts` → `ZiweiChart` JSON | 紫微体系内可核验的宫位星曜四化 | 可用来核对「命宫是否空宫、四化落宫」等盘面断言 |
| L2 13 维解读 | `F:\ziwei-data` v4.0 文本 | 断语，非事实 | 只做**结论层对账**，不进事实层、不进理论索引 |

用户贴来的那份分析，正是 L2 文本经改写而成。阶段 3 已把 L1 打通：目标盘 14 条盘面断言在紫微引擎内**全部成立**（见 §8），补上了「盘面无法核验」这一环。

---

## 2. 统一主键：同参不同源，且不悄悄对齐

八字与紫微用**同一组入参**，各自映射到自己的键，这是「同步调用」的最小契约：

```text
输入   --birth "2001-12-31 06:00" --gender 坤

八字   engine.cli chart / all      → chart_id = cf-281c0165ae85687dafe7
紫微   date = 2001-12-31
       hour_index = floor(((clockHour + 1) % 24) / 2) = 3   （卯时 5–7）
       gender     = 坤 → female / 乾 → male
       key        = "2001-12-31-3-female"   （现场命中 [710394103, 84563]）
```

`case_key` 建议固化为：`{birth_iso, gender, hour_index, calendar_policy, tz_policy, schema_version}`，两边产物都挂到这个键下，归档到 `cases/<case-id>/`。

**必须输出 `alignment_warnings`，不准静默对齐**（对应 `AGENTS.md` §4「保留 boundary_warnings / variants，有差异时并列呈现」）：

| 差异 | 八字 | 紫微 v4.0 | 处理 |
|---|---|---|---|
| 年月分界 | 节气（立春换年、节换月） | 公历日期索引 | 节气边界附近的盘并列两套口径 |
| 晚子时 23:00–00:59 | `late_zi_split` 变体并列 | 数据集按生成时口径；引擎 2026-11-02 起改按真太阳时判断 | 列为警告，不自动换算 |
| 真太阳时 | 本盘 `null` | 数据集未校正（一致） | 一旦将来传入出生地经度，两边分叉，必须显式警告 |
| 内容版本 | 引擎实时 | 数据集固定 `ca268829f7a9` | 信封记录版本，禁止把「引擎新结果」说成「数据集结论」 |
| 星曜亮度 | 无关 | v4.0 按「现代修正 v2」生成，引擎默认已改《斗数全书》 | L1 实时排盘与 L2 文本可能不一致，需标注 |

---

## 3. evidence-envelope/v1 契约（建议字段）

```json
{
  "envelope": "evidence-envelope/v1",
  "case_key": {
    "birth_iso": "2001-12-31 06:00",
    "gender": "坤",
    "hour_index": 3,
    "calendar_policy": { "bazi": "jieqi", "ziwei": "solar_date" },
    "tz_policy": "no_correction"
  },
  "source_system": "ziwei-doushu",
  "source_kind": "interpretation_text",
  "level": "L2",
  "dataset": {
    "version": "v4.0-13d",
    "content_version": "ca268829f7a9",
    "license": "CC BY 4.0",
    "attribution": "紫微斗数开源解读数据集 v4.0 / github.com/Renhuai123/ziwei-doushu / 王多鱼AI"
  },
  "locator": {
    "shard": "year-2001.jsonl.zst",
    "key": "2001-12-31-3-female",
    "offset": 710394103,
    "length": 84563
  },
  "claims": [{ "dim": "career", "chars": 2271, "text": "..." }],
  "alignment_warnings": ["engine_brightness_default_changed_after_v4"],
  "verifiable_by": "ziwei-doushu engine (external system)",
  "not_usable_as": ["engine_fact", "theory_source_ref"]
}
```

`source_kind` 只枚举 `chart_fact`（L1）与 `interpretation_text`（L2）；`verifiable_by` 明确写「外部体系」，避免被误当成八字引擎已核验的事实。

---

## 4. GitHub 库 vs 本地：只搬指针，不搬数据

| 内容 | 位置 | 理由 |
|---|---|---|
| 适配器、`envelope` schema、对账脚本、设计文档、配置模板 | **入 GitHub** | 合计几十 KB，纯代码 |
| `dataset-manifest.json`（77 年 × 下载 URL / sha256 / 字节数 / 内容版本） | **入 GitHub** | 让任何 clone 可复现，不需复制数据 |
| `F:\ziwei-data` 全量 5.7 GB、解压明文、单盘 3 万字文本 | **仅本地** | GitHub 单文件 100 MB 上限、仓库体积；且含倪师原话（非商用） |
| 本机绝对路径 | `config/ziwei.local.toml`（gitignore）+ 环境变量 `ZIWEI_ANALYSIS_DIR` / `ZIWEI_PROJECT_DIR` | 跨平台，仓库只留 `ziwei.local.example.toml` |
| 对账中间产物、原文片段 | `cases/_private/<case-id>/`（**已在 `.gitignore`**） | 复用现成私有目录，不新增约定 |
| 最终结论 | 主报告 + 独立旁证附录（可入库） | 只写结论与 locator，不复制原文 |

**按年懒加载**：紫微项目已有 `scripts/dataset/fetch.mjs <year> --zst-only`（含镜像回退、sha256 校验、用完即删明文）。八字项目不必重写下载逻辑，直接调用它；单个年份只要 **2 MB**，clone 后拉一年即可跑全链路。

---

## 5. 同步调用的三种实现，推荐 A

| 方案 | 做法 | 裁决 |
|---|---|---|
| **A · 同参双 CLI（推荐）** | `python -m engine.cli all --birth ... --gender 坤 --json` 与 `python -m tools.ziwei_lookup --birth ... --gender 坤 --dim career,wealth --json` 并列跑，再交 `tools.cross_check` 出三态对账 | **采用**：零侵入、离线、无需服务、不动保护区；Agent 一次分析跑两条命令即可 |
| B · 给 `engine.cli` 加 `--corroborate` | 在引擎内部串接紫微 | **拒绝**：污染事实层、破坏无状态确定性、动核心入口与回归测试 |
| C · 常驻 Next.js HTTP | 起 `localhost:3000` 调 `/api/chart` | **拒绝为主路径**：依赖 `node_modules` 与常驻进程；仅 L1 结构化盘面需要时用 `tsx` 直接 import `algorithm.ts` 输出 JSON，不必起服务 |

查表实现走**只读流式解压**，不落 700 MB 明文（本轮已跑通）：

```js
// 从 .idx.json 取 [offset, length]，流式解压到 offset 即截取目标行，随后销毁流
const dec = zlib.createZstdDecompress({ maxOutputLength: 2 * 1024 ** 3 });
fs.createReadStream(zstPath).pipe(dec);
for await (const ch of dec) { /* 累加字节位置，命中区间就切片并提前 break */ }
```

顺带发现一个上游小缺陷：`scripts/dataset/lookup.mjs` 只在**索引缺失**时自动解压，若 `.idx.json` 存在而 `.jsonl` 不存在（本机 2001 年正是此状态），会直接 `ENOENT`。适配器须先检查明文分片，缺失时解压补齐，或统一走上面的流式路径绕开它。

`tools.cross_check` 的输出就是上一轮人工对账的结构化版：每条结论标 `converged` / `divergent` / `unverifiable`，分歧项由 Agent 站队并写理由，禁止输出「各有道理」。

---

## 6. 合规（不可省）

- 仓库 `README.md` 或本文档「数据来源」节保留署名三行：

  > 本项目使用了 **紫微斗数开源解读数据集 v4.0**（674,976 张命盘 × 13 维）
  > 来源：https://github.com/Renhuai123/ziwei-doushu
  > 作者：王多鱼AI

- 解读中引用的倪海厦《天纪》原话**不在 CC BY 4.0 授权范围内**（CC BY-NC-SA 4.0、非商用）；故单盘 3 万字原文只留在 `cases/_private/`，不进公开仓库、不批量导出。
- `lib/ziwei/algorithm.ts` 等代码为 MIT，调用与引用均无额外限制；两个仓库各自保留原有许可，不合并、不改名。

---

## 7. 分阶段实施与验收

| 阶段 | 产出 | 验收命令 / 判据 |
|---|---|---|
| ✅ 0 · 可行性 | 三边只读调研 + 目标盘流式查表命中 | `2001-12-31-3-female` 返回 `ms=null`、13 维齐，**已通过** |
| ✅ 1 · 桥接 | `bridges/ziwei/case_key.py`、`lookup.py`、`ziwei_reader.mjs`、`tools/ziwei_lookup.py`、配置模板与本机配置、`.gitignore` | CLI 退出码 0，`locator.offset=710394103`；**明文 seek 与 zst 流式解压两条路径结果一致** |
| ✅ 2 · 信封与对账 | `bridges/ziwei/envelope.py`、`tools/cross_check.py`、`bridges/ziwei/verify.py` | `verify.py` 18 项 ALL PASS；`not_usable_as`、三态落定、禁骑墙措辞均被钉住 |
| ✅ 3 · 报告层与 L1 | `bridges/ziwei/ziwei_chart_l1.mts`（`node --import tsx`）、`chart_l1.py`、`tools/ziwei_chart.py`、`build_l1_envelope`、`tools/ziwei_appendix.py` | L1 十四条断言 14/14 成立、指纹可复现；附录每条带 locator；主报告 Linter 仍零 ERROR；**已通过** |
| ✅ 4 · 可复现 | `config/dataset-manifest.json`（77 年 × 字节数 / sha256 / URL / 镜像）、`tools/ziwei_fetch.py`、`ziwei_reader.mjs --build-index` | 清单 29 KB 可入库；77 年全量哈希 `ALL OK`；合成样本明文 / zst 两条建索引路径结果一致；**已通过** |

验收沿用 `AGENTS.md` §5：`python -m pytest -q`、`engine.cli` 冒烟、`human_touch_linter`；新增能力用只依赖标准库的 `verify.py` 表达退出码。**不修改测试或断言使其通过**；版本提交由人工执行（本次已于 2026-11-11 以 `87fc5a29` 入库）。

---

## 8. 阶段 1–4 实施记录（2026-11-10）

**新增文件**

| 文件 | 职责 |
|---|---|
| `bridges/ziwei/case_key.py` | 同参映射（`hour_index = floor(((h+1)%24)/2)`、坤→female）、`alignment_warnings` 生成；晚子时不静默换日 |
| `bridges/ziwei/ziwei_reader.mjs` | Node 22 只读查表：明文分片 `seek`，或 zstd 流式解压到 `[offset, offset+length)` 即截取并销毁流；**不落盘、不写数据目录** |
| `bridges/ziwei/lookup.py` | 配置加载（toml < 环境变量）、Node 子进程调度、错误归一 |
| `bridges/ziwei/envelope.py` | `evidence-envelope/v1`；强制 `not_usable_as`、许可署名、locator、口径警告 |
| `tools/ziwei_lookup.py` | 与 `engine.cli` 同参的 CLI；`--dim` 才输出正文，默认只给元数据与字数 |
| `tools/cross_check.py` | 三态对账骨架；`--claims` 带八字侧出处，`--verdicts` 落定裁决；骑墙措辞直接报错 |
| `bridges/ziwei/verify.py` | 黄金样本验收（标准库 + 本机 node），退出码表达结果 |
| `config/ziwei.local.example.toml` / `ziwei.local.toml` | 模板入库 / 本机绝对路径不入库（`git check-ignore` 已确认） |
| `README.md` 新增节 | 使用命令 + CC BY 4.0 署名与引文边界 |
| `bridges/ziwei/ziwei_chart_l1.mts` | L1 runner；`node --import tsx` 直接 import `lib/ziwei/algorithm.ts::generateChart`，不联网、不写盘、不起 Next.js 服务 |
| `bridges/ziwei/chart_l1.py` | L1 调度 + 声明式断言求值器（`DEFAULT_CLAIMS` 14 条）+ chart 指纹 sha256 + 盘面摘要 |
| `envelope.py::build_l1_envelope` | L1 信封：`source_kind=chart_fact`、`verified_within`、断言表、`dataset=None`，`not_usable_as` 原样保留 |
| `tools/ziwei_chart.py` | L1 CLI；`--claims` 可换断言集，`--full` 才附完整 `ZiweiChart` |
| `tools/ziwei_appendix.py` | 独立旁证附录 Markdown；消费 L1 / L2 / cross 三份信封，不改 v7 模板与 Linter 契约 |
| `tools/cross_check.py` 加固 | 明确拒绝 L1 信封（三态对账只服务 L2），`dataset` 缺省防御 |
| `config/dataset-manifest.json` | 77 年 × 分片字节数 / sha256 / idx 键数 / Release URL / 镜像，29 KB 可入库 |
| `tools/ziwei_fetch.py` | `--verify-only` / `--download` / `--rebuild-manifest`；缺省 dry-run，已存在且校验和匹配一律跳过、绝不覆盖 |
| `ziwei_reader.mjs --build-index` | 缺 idx 时流式解压 zst 逐行扫 `k` 键，索引 JSON 直接输出到 stdout，**不生成 700 MB 明文**；语义与上游 `build-index.mjs` 一致 |

**实际命令**

```bash
# 同参双 CLI + 三态对账
python -m engine.cli chart --birth "2001-12-31 06:00" --gender 坤 --json > bazi_chart.json
python -m tools.ziwei_lookup --birth "2001-12-31 06:00" --gender 坤 --dim career,wealth --json > ziwei_envelope.json
python -m tools.cross_check --bazi bazi_chart.json --ziwei ziwei_envelope.json --out 对账.md

# 阶段 3：L1 盘面核验 + 独立旁证附录
python -m tools.ziwei_chart --birth "2001-12-31 06:00" --gender 坤 --json > l1.json
python -m tools.cross_check --bazi bazi_chart.json --ziwei ziwei_envelope.json \
    --claims claims.json --verdicts verdicts.json --json > cross.json
python -m tools.ziwei_appendix --l1 l1.json --l2 ziwei_envelope.json \
    --cross cross.json --out 旁证附录.md

# 阶段 4：清单、按年懒加载（缺省 dry-run，--download 才联网）
python -m tools.ziwei_fetch --rebuild-manifest
python -m tools.ziwei_fetch --year 2001 --verify-only
python -m tools.ziwei_fetch --year 2001 --download

# 验收
python bridges/ziwei/verify.py --require-data --require-l1
python -m pytest -q
python -m tools.human_touch_linter reports/2001-12-31-坤-辛巳庚子戊辰乙卯-human-report.md
```

**验收结果（实跑）**：`verify.py --require-data --require-l1` **37 项 ALL PASS**；`pytest -q` **229 passed**；既有主报告 Linter **0 ERROR**；`engine.cli` 冒烟正常；`config/ziwei.local.toml` 被 `.gitignore:43` 忽略。

- 阶段 1–2：`offset=710394103`、`ms=null`、13 维、`career=2271` 字、同参 `chart_id=cf-281c0165ae85687dafe7`、明文 seek 与 zst 流式结果一致、三态可落定、禁骑墙。
- 阶段 3：L1 排盘 `chart_sha256=d76315da3bb14bc9…`（8494 字节，两次运行一致）；**14 条盘面断言 14/14 成立**——命宫酉位空宫只坐禄存、羊陀夹命、对宫卯紫微贪狼、身宫落迁移、官禄丑天府+铃星、财帛巳天相、天魁在仆役、巨门化禄在疾厄、太阳化权在田宅、文昌化忌与文曲化科同落夫妻、26–35 亥宫福德武破天马天虚。附录声明「不是主报告」、每行带 locator、拒骑墙；`cross_check` 明确拒绝 L1 信封。
- 阶段 4：清单 77 年 / 29,623 字节 / 压缩总量 153.9 MB / 2001 分片 8,760 键；`--all --verify-only` **ALL OK**；合成样本明文与 zst 两条建索引路径都给出 `[0,46]`、`[47,44]`。

**几个真实踩到的坑（已修，未改断言迁就）**
1. `lookup.mjs` 在「有 idx 无 jsonl」时会 `ENOENT`；新 reader 按需选明文或 zst 路径，并在缺 idx 时自己流式建索引，不依赖上游修复。
2. `tools.ziwei_chart --json` 输出 `indent=2` 多行 JSON，验收里按「最后一行」解析会失败；改整段解析。
3. Windows `Path.write_text` 默认把 `\n` 写成 `\r\n`，索引按磁盘字节计长会多 1；合成样本显式 `newline=""` 保持 LF，与真实 JSONL 一致。
4. `--build-index` 走 stdout 输出约 340 KB 索引 JSON，由 CLI 决定写哪，reader 本身始终不写盘。

**上游小缺陷已绕开**：见第 1 条。

**仍未做 / 边界**：没有把紫微盘面写进 `engine.cli`、没有改 `templates/` 与 Linter 契约、没有把 5.7 GB 或单盘 3 万字原文库入仓。入库提交为 `87fc5a29`（2026-11-11，人工授权执行），只新增文件与 `README.md` / `.gitignore` 尾部，未改写历史。L1 需要紫微项目已 `npm install`（`tsx` / `iztro` / `lunar-javascript`），L2 只需 Node ≥ 22；两者缺一时 `verify.py` 自动跳过对应断言，可用 `--require-data` / `--require-l1` 强制要求。附录若含数据集原文片段，入库前须人工确认不含倪师《天纪》引文，否则放 `cases/_private/ziwei-*/`。

**一句话**：不搬 5.7 GB、不并引擎、不改模板——用「同一出生主键 + 证据信封」把紫微挂成可插拔旁证；L1 在紫微体系内核盘面、L2 只做结论对账，GitHub 只留指针与校验和，本地留数据，Agent 留裁决权。

---

## 9. 接入点复核与已知缺口（2026-11-11）

代码落地不等于「可被发现」。本节逐个核对本方案在各入口上的可见性，避免下一个人（或下一个 Agent）不知道这条路存在。

| 入口 | 状态 | 说明 |
|---|---|---|
| `docs/agent_tools.md` 工具 3 | ✅ 已补 | Agent 的实际调用手册：四工具用途/禁用边界表、可粘贴命令、`--dim` 语义、缺数据降级 |
| `README.md`「外部体系旁证（可选）」 | ✅ 已补 | 面向人：一段定位 + 全链路命令 + CC BY 4.0 署名与引文边界 |
| 本文档 §3 契约 vs `envelope.py` | ✅ 一致 | 实际字段与 §3 示例逐项对照无出入；实装多出 `verified_within`（L1）与 `alignment_warnings` 实值枚举 |
| 本文档 §7 阶段表 | ✅ 一致 | 五个阶段产出文件与验收判据均可在仓库内对应到实际路径 |
| `AGENTS.md` §2 导航图 / §1 铁律 | ⚠️ **未收录** | 该文件属保护区，需任务卡明确授权。**后果**：新 Agent 只读 `AGENTS.md` 时不知道旁证层与五个工具的存在，必须由人指向 `docs/agent_tools.md` 工具 3 |
| `META/project-state.json` | ⚠️ 未收录 | 保护区（由维护流程更新），不在本方案范围 |
| `reports/` 内命盘报告 | ⚠️ 未入库 | 按隐私口径留在本地；本文档 §8 命令中的报告路径仅示例 |

**待授权的最小补丁**（两处，均改保护区 `AGENTS.md`）：

1. §2 导航图加一行：`bridges/ziwei/ + tools/ziwei_*.py  外部体系旁证层：evidence-envelope/v1（见 docs/agent_tools.md 工具 3）`
2. §1 铁律补一句：`外部体系（紫微等）一律走 evidence-envelope/v1 旁证层，不作 engine_fact、不作 theory_source_ref；分歧由 Agent 站队。`

除此之外，本设计在文档侧无未闭合项。
