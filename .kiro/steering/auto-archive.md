# Steering · 案例自动归档协议

> **作用域**：本仓库（lynhao-mike/mangpai-fusion）所有 agent 实例
> **优先级**：强制（高于一切流程优化建议）
> **生效日期**：2026-05-23

---

## 一、触发条件

只要满足以下**全部条件**，即触发本协议：

1. 用户在对话中贴入了八字盘信息（含至少：性别 + 公历生日 + 四柱）
2. Kiro 已经在本会话中**首次输出了分析结果**（无论篇幅长短，无论是否完整）

不再触发的情形：
- 用户只是询问理论 / 规律 / 工具用法，未贴八字
- 用户在已立案案例上追加分析（走"原案追加"路径，见 §五）

## 二、强制动作（默认执行，不再询问）

首次输出分析结果**之后**，必须**立即且自动**完成以下所有动作，作为同一回合（同一次 commit）的一部分：

### 2.1 立案号分配

```
扫描 cases/C-YYYY-NNN/ 取当年最大序号 + 1
→ 本次立案号 = C-YYYY-NNN（NNN 三位补零）
```

### 2.2 指纹计算与防重

```bash
fingerprint = $(echo -n "M|YYYY-MM-DD HH:MM" | md5sum | cut -c1-12)
# 性别用 M / F 大写；时间精确到分钟（真太阳时优先）
```

- 在 `cases/cases-index.md` §二「八字指纹防重」检索
- 命中已有指纹 → 走「原案追加」（§五）；未命中 → 继续 §2.3

### 2.3 案例四件套生成

必须**同时**创建（缺一不可）：

| 文件 | 内容 |
|---|---|
| `cases/C-YYYY-NNN/input.md` | 复述八字盘 + 命主已知信息 + 分析重点 + 指纹 |
| `cases/C-YYYY-NNN/analysis.md` | 4 派各自定性 + 共识/互补/独门/冲突 + 仲裁 + 规律使用清单 |
| `cases/C-YYYY-NNN/feedback.md` | 空模板，标注"待命主反馈" |
| `cases/C-YYYY-NNN/lessons.md` | 首案模板，标注"首次分析·待回测后回填" |

### 2.4 正式报告生成

- `reports/C-YYYY-NNN-report.md`
- 格式严格遵循 `templates/report.md`（如不存在，参照最近一份 reports/C-2026-NNN-report.md）
- 内容必须包含：八字盘 / 4 派定性表 / 共识层 / 互补层 / 独门层 / 冲突登记 / 财富等级 / 应期总表 / 命主画像版 / 风险提示
- 所有断语必须双轨置信度（★+%）+ 派别归属

### 2.5 索引更新

`cases/cases-index.md` 必须同步更新：
- §一 案例统计（总数 +1，待应期 +1）
- §一 按策略分布（对应策略 +1）
- §二 已立案指纹（追加一行）
- §三 案例列表（顶部插入一行）
- 4 派表现总表保持不动（无反馈数据时不动）

### 2.6 提交策略

- **直接在 main 分支** commit + push
- **绝不开新分支，绝不创建 PR**（用户全局 learning）
- commit message 格式：`case: C-YYYY-NNN 立案 - <八字签名> - <策略代号>`
- 例：`case: C-2026-014 立案 - 丙戌庚子乙亥辛巳·乾造 - 策略B全面画像`

## 三、与既有规则的关系

本协议是对 `cases/cases-index.md §五` 与 `reports/README.md` 中"必须同一次 commit"约束的**强化**：

| 既有约束 | 本协议升级 |
|---|---|
| 二者必须同一次 commit 提交 | ✅ 保持 + 新增"自动执行不询问" |
| `analyst.md` Step 10 输出报告 | ✅ Step 11 自动归档（不再 BOOT.md 第 7 条"询问是否归档"） |

`.kiro/skills/BOOT.md` §五「开始工作」第 7 条「询问用户是否要归档为案例」**已废止**——默认归档，不询问。

## 四、隐私模式（用户显式触发）

用户若说"这是隐私案例 / 不要立案 / 仅本地分析"等任一语义：
- case_id 改为 `C-YYYY-NNN-PRIV`
- 仍然在本地生成四件套 + report
- **不 push** 到 GitHub
- 在 cases-index.md 中只记录指纹，不记录详情

## 五、原案追加（指纹命中已有案例）

若用户贴入的八字指纹已在 `cases/cases-index.md` 中：
- 不创建新 case_id
- 在 `cases/C-YYYY-NNN/analysis.md` 末尾追加 `## 二次分析（YYYY-MM-DD）` 段落
- `reports/C-YYYY-NNN-report.md` 升级为 v2/v3...
- cases-index.md 备注栏更新"二次分析日期"

## 六、自检清单

每次执行完毕，agent 必须自检：

- [ ] cases/C-YYYY-NNN/ 四件套是否齐全？
- [ ] reports/C-YYYY-NNN-report.md 是否生成？
- [ ] cases-index.md 指纹是否登记？
- [ ] cases-index.md 案例列表是否更新？
- [ ] 是否一次 commit 包含所有变更？
- [ ] 是否已 push 到 main？

任一不通过 → 立即补救。

## 七、版本

v1.0 · 2026-05-23 · 由用户反馈触发首次入库
