# 命名规范契约 · 09-naming-convention

> **本文规定 v1.2 起所有案例、报告、预测文件的命名格式。**
> 旧案重命名清单见末尾"附录 A"。

最后更新：2026-05-28（v1.4 W1 文档同步）
版本：v1.3.0-current
适用分支：`main`（`v1.2-build` 已合并；当前命名校验以工具实现为准）

---

## 一、案例 ID 格式

```
C-YYYY-NNN-{年柱}{月柱}{日柱}{时柱}

其中：
  YYYY = 立案年份（4 位）
  NNN  = 当年序号（3 位，001 起，左侧补零）
  年柱 = 八字第一柱的干+支（2 字）
  月柱 = 八字第二柱（2 字）
  日柱 = 八字第三柱（2 字）
  时柱 = 八字第四柱（2 字）

示例：
  C-2026-001-庚申戊寅壬子辛丑   ← 命主 1（男 1980-02-09 02:00）
  C-2026-002-壬戌庚戌戊辰丙辰   ← 命主 2（女 1982-10-12 07:20）
  C-2026-014-丙戌庚子乙亥辛巳   ← 命主 14（男 2006-12-12 09:45）
```

**为什么干支不加分隔符？** 8 个汉字连写最紧凑且无歧义；加 `·` 或 `-` 会与 case_id 分隔符冲突。

**为什么不在文件名中带性别/出生时间？** 已经被八字干支隐式编码（性别由日干强弱+大运方向定，出生日期由四柱反推唯一）。


---

## 二、文件路径规范

### 2.1 案例目录

```
cases/C-YYYY-NNN-{干支}/
├── input.md
├── analysis.md
├── feedback.md
├── lessons.md
└── findings/               （pipeline / render_report 落盘的结构化 Findings，可选）
```

示例：
```
cases/C-2026-001-庚申戊寅壬子辛丑/
cases/C-2026-014-丙戌庚子乙亥辛巳/
```

### 2.2 报告文件

```
reports/C-YYYY-NNN-{干支}-report.md
```

示例：
```
reports/C-2026-001-庚申戊寅壬子辛丑-report.md
reports/C-2026-014-丙戌庚子乙亥辛巳-report.md
```

### 2.3 预测文件（由 extract_predictions.py 自动生成）

```
predictions/PRED-YYYY-NNN-{case_id 简化}-{干支}-{用途}.md

其中 case_id 简化 = 去掉所有连字符（如 C2026001）
用途 = future / verification / 具体年份等
```

示例：
```
predictions/PRED-2026-001-C2026001-庚申戊寅壬子辛丑-future.md
predictions/PRED-2026-008-C2026014-丙戌庚子乙亥辛巳-2026gaokao.md
```

### 2.4 校准报告（自迭代输出）

```
META/calibration/{YYYY-MM-DD}-after-C-YYYY-NNN.md
META/iteration-log.md   ← 全局追加，不分文件
```


---

## 三、干支提取规则

### 3.1 来源
干支必须**严格来自 input.md 的 schema 字段**，不允许从命主自由文本中正则提取（容易错）。

input.md 必须包含以下字段（详见 `01-input-schema.md`）：
```yaml
四柱:
  年柱: 庚申
  月柱: 戊寅
  日柱: 壬子
  时柱: 辛丑
```

### 3.2 校验
立案时 `preflight.py` 校验：
1. 4 个柱必须各 2 字
2. 第 1 字必须是 10 天干之一（甲乙丙丁戊己庚辛壬癸）
3. 第 2 字必须是 12 地支之一（子丑寅卯辰巳午未申酉戌亥）
4. 干支组合必须存在于 60 甲子（不允许"甲丑"等不合法组合）
5. 案例目录名必须 = `C-YYYY-NNN-` + 4 柱 8 字 拼接

### 3.3 工具
当前未保留独立 `tools/naming.py`。命名生成 / 校验由以下入口消费同一规则：

- `tools/preflight.py`：立案输入与案例目录一致性校验。
- `tools/render_report.py`：报告落盘文件名沿用完整 case_id。
- `tools/extract_predictions.py`：生成 `PRED-YYYY-NNN-{case_id简写}-{干支}-{用途}.md`。

---

## 四、八字指纹算法（保持 v1.0）

```
fingerprint = MD5(性别 + "|" + YYYY-MM-DD HH:MM)[:12]

性别用 M/F 大写
日期格式精确到分钟
```

**指纹与文件名独立存在**：
- 文件名带干支 = 人类可读 + 命理师对应命主
- 指纹 = 系统级防重（不同时辰但同干支的极端情况由指纹区分）

立案时 preflight.py 同时校验：
1. 干支组合合法
2. 指纹未在 cases-index.md 出现过


---

## 五、特殊情形

### 5.1 私密案例
```
C-YYYY-NNN-{干支}-PRIV
```
不公开 push，本地 .gitignore 排除。

### 5.2 同一命主二次立案（追加分析）
不新建 case_id，在原 case 目录内追加：
```
cases/C-2026-001-庚申戊寅壬子辛丑/
└── analysis-v2.md   ← 第二次分析，与 analysis.md 共存
```

### 5.3 时辰未知 / 八字残缺
不允许立案。preflight.py 直接拒绝。命主必须先确定四柱。

### 5.4 真太阳时调整
若问真 APP 已应用真太阳时，干支按 APP 输出；input.md 中标记 `真太阳时校正: true`。
若未应用，input.md 标记 `真太阳时校正: false`，preflight.py 给出告警但不拒绝。

---

## 六、cases-index.md 内容更新规范

```markdown
| Case ID | 日期 | 命主代号 | 性别 | 八字 | 主领域 | 策略 | 应验状态 | 报告链接 |

✓ 第一列必须使用完整 case_id（含干支）：
   [C-2026-001-庚申戊寅壬子辛丑](C-2026-001-庚申戊寅壬子辛丑/)

✓ "八字"列保留单独显示（人类阅读时仍要直观）：
   庚申·戊寅·壬子·辛丑

✓ 报告链接：
   [report v2](../reports/C-2026-001-庚申戊寅壬子辛丑-report.md)
```

---

## 七、工具支持

当前生效入口：
- `tools/preflight.py` 校验立案与案例目录名。
- `tools/render_report.py` 输出报告时使用统一文件名。
- `tools/extract_predictions.py` 生成预测文件名时使用统一规则。

历史计划中的 `tools/naming.py` / `tools/rename_legacy_cases.py` 当前不存在，不作为可执行入口；如需独立命名库，应先补工具注册表与测试。


---

## 附录 A · 旧案重命名清单（10 案）

> 这是一个**独立 PR** 的工作清单，先于 v1.2 引擎建设执行。
> 仅文件搬运 + 引用更新，不修改任何 case 内容。

### A.1 目录重命名

| 旧路径 | 新路径 |
|---|---|
| `cases/C-2026-001/` | `cases/C-2026-001-庚申戊寅壬子辛丑/` |
| `cases/C-2026-002/` | `cases/C-2026-002-壬戌庚戌戊辰丙辰/` |
| `cases/C-2026-007/` | `cases/C-2026-007-乙丑庚辰己丑庚午/` |
| `cases/C-2026-008/` | `cases/C-2026-008-壬申癸卯丁未壬寅/` |
| `cases/C-2026-009/` | `cases/C-2026-009-庚辰乙酉丙申乙未/` |
| `cases/C-2026-010/` | `cases/C-2026-010-甲子丁卯癸卯庚申/` |
| `cases/C-2026-011/` | `cases/C-2026-011-乙丑乙酉丁丑癸卯/` |
| `cases/C-2026-012/` | `cases/C-2026-012-壬戌癸丑丙申壬辰/` |
| `cases/C-2026-013/` | `cases/C-2026-013-壬申甲辰丙辰己丑/` |
| `cases/C-2026-014/` | `cases/C-2026-014-丙戌庚子乙亥辛巳/` |

### A.2 报告文件重命名

| 旧路径 | 新路径 |
|---|---|
| `reports/C-2026-001-report.md` | `reports/C-2026-001-庚申戊寅壬子辛丑-report.md` |
| `reports/C-2026-002-report.md` | `reports/C-2026-002-壬戌庚戌戊辰丙辰-report.md` |
| `reports/C-2026-007-report.md` | `reports/C-2026-007-乙丑庚辰己丑庚午-report.md` |
| `reports/C-2026-008-report.md` | `reports/C-2026-008-壬申癸卯丁未壬寅-report.md` |
| `reports/C-2026-009-report.md` | `reports/C-2026-009-庚辰乙酉丙申乙未-report.md` |
| `reports/C-2026-010-report.md` | `reports/C-2026-010-甲子丁卯癸卯庚申-report.md` |
| `reports/C-2026-011-report.md` | `reports/C-2026-011-乙丑乙酉丁丑癸卯-report.md` |
| `reports/C-2026-012-report.md` | `reports/C-2026-012-壬戌癸丑丙申壬辰-report.md` |
| `reports/C-2026-013-report.md` | `reports/C-2026-013-壬申甲辰丙辰己丑-report.md` |
| `reports/C-2026-014-report.md` | `reports/C-2026-014-丙戌庚子乙亥辛巳-report.md` |

### A.3 预测文件重命名

| 旧路径 | 新路径 |
|---|---|
| `predictions/PRED-2026-001-C2026001-future.md` | `predictions/PRED-2026-001-C2026001-庚申戊寅壬子辛丑-future.md` |

### A.4 引用更新（grep + sed 全仓扫描）

需要更新所有引用（约 30+ 处）：
- `cases/cases-index.md`（10 处链接）
- `cases/README.md`（如有）
- `reports/README.md`
- `handoff.md`
- `STATUS.md`
- `META/INDEX.md`、`META/source-trace.md`、`META/rule-changelog.md`
- `predictions/README.md`
- `theory/{school}/index.yaml` 中的 `tested_cases:` 字段（若有 case_id 引用）

### A.5 重命名 PR 验收标准

1. 所有 10 个旧案目录、报告、预测均按新规范命名
2. `git mv` 保留 git 历史（不能 rm + add）
3. 全仓 `grep -r "C-2026-00[1-9]\|C-2026-01[0-4]"` 不应再出现旧 case_id（不带干支的）
4. 重命名后 cases-index.md 内容渲染正确，链接全部可点击
5. 不修改任何 case 内部内容（hash 验证）

---

**命名规范契约结束。下一份请阅读 `01-input-schema.md`（W1 第 3 份）。**
