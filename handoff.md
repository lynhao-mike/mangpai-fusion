# Kiro 接管交接文档

> 当任何 Kiro 实例接管本仓库时，先读本文件，再读 `.kiro/skills/BOOT.md`。

最后更新：2026-05-23 · v1.0 首发

---

## 一、本仓库是什么

`mangpai-fusion` = **盲派四派融合八字分析系统 v1.0**，整合：
- 高德臣（盲派宗派）261 条规律
- 段建业（盲派宗派）290 条规律
- 杨清娟（盲派宗派）163 条规律
- 任付红（盲派宗派）200 条规律
- **合计 914 条规律全量索引**

---

## 二、用户角色与目标

- **用户**：专业命理师
- **使用工具**：问真八字 APP 排盘
- **核心需求**：
  1. 八字录入仓库 → AI 给出 4 派融合分析
  2. AI 必须明确标注**派别归属 + 双轨置信度（★+%）**
  3. 命主反馈应验/失验 → 自动校准引擎重算命中率
  4. 多派定一派 = 高置信
  5. 单派独门但实战应验高 = 显式提示

---

## 三、上下文文件优先级

启动后必读（按顺序）：
1. `STATUS.md` ← 当前进度（v1.0 已可投入实战）
2. `.kiro/skills/BOOT.md` ← 最小启动协议
3. `.kiro/skills/analyst.md` ← **主分析器**（最重要！10 步法 + 8 铁律）
4. `theory/SCHEMA.md` ← 规律 schema
5. `engine/confidence.yaml` ← 双轨置信度算法
6. `engine/domain-weights.yaml` ← 4 派领域权重
7. `engine/arbitration.md` ← 仲裁规则（20 条 CF）
8. `mapping/INDEX.md` ← 跨派映射总览
9. `templates/input-from-wenzhen.md` ← 输入规范
10. `templates/report.md` ← 输出规范

实战时按需加载：
- `theory/{gao,duan,yang,ren}/index.yaml`：4 派结构化规律库
- `mapping/{consensus,complementary,exclusive,conflicts}.md`：跨派映射
- `cases/cases-index.md`：历史案例索引（用于回顾相似命例）
- `META/rule-changelog.md`：规律变更日志

---

## 四、来源仓库

本仓库的 4 派理论来源于：
- `lynhao-mike/Mang.pai` ← 高派理论（迁入 sources/gao/ + theory/raw/gao/）
- `lynhao-mike/gufamangpai` ← 段+杨+任 三派理论（迁入 sources/{duan,yang,ren}/）

详细映射见 `META/source-trace.md`。

---

## 五、强约束（绝不打破）

1. **置信度必须双轨制**：每条断语必须给出 `★ 等级 + 百分比`
2. **派别必须明示**：每条断语必须标注 `[派别]` 来源
3. **应期必须可证伪**：所有应期断语必须给出具体年份/月份
4. **共识 vs 独门必须区分**：
   - ≥2 派同向 → 标注"共识"
   - 单派 → 标注"X派独门，置信度依赖 hit_rate"
5. **反馈回流必须实时**：用户每次提供反馈，必须更新对应规律的 `hit_count/miss_count`
6. **永远不替命主决策**：本系统是辅助工具，不替代命理师本人的判断
7. **冲突必须显式呈现**：派别冲突不可隐瞒（详见 `engine/arbitration.md`）
8. **报告与案例同步 commit**：reports/ 与 cases/ 必须同时归档（强制约束）

---

## 六、典型工作流

### 6.1 单案例分析流程

```
用户：[贴入按 templates/input-from-wenzhen.md 格式的八字 + 分析重点]
     ↓
Kiro:  1. 复述八字确认
       2. 询问已知信息（婚姻状态/重大事件等）
       3. 加载 .kiro/skills/strategy.yaml 路由策略 A/B/C
       4. 加载 engine/domain-weights.yaml 取 lead 派
       5. 4 派并行查询（theory/{gao,duan,yang,ren}/）
       6. 共识层匹配 → 互补层联立 → 独门补充 → 冲突仲裁
       7. 应期 4 模型交叉
       8. 按 templates/report.md 输出双轨置信度报告
       9. 同步生成 cases/C-YYYY-NNN/{input.md, analysis.md} + reports/C-YYYY-NNN-report.md
     ↓
命主反馈应验/失验
     ↓
Kiro:  填入 cases/C-YYYY-NNN/feedback.md
       触发 python3 tools/calibrate.py --case C-YYYY-NNN
     ↓
自动校准:
- 更新 theory/{school}/index.yaml 的 hit/miss/score/star
- 触发升降级（candidate → promoted / promoted → retired）
- 写入 META/rule-changelog.md
- 同步更新 mapping/ 文件
- 生成 cases/C-YYYY-NNN/calibration-report.md
```

### 6.2 当用户问"如何使用"时

直接给出：
> 「请按 `templates/input-from-wenzhen.md` 模板把您的八字（从问真八字 APP 复制）整理后贴给我，并在末尾说明您想问的核心问题。我会按 4 派融合策略给您一份双轨置信度的专业分析报告。」

---

## 七、当前状态

详见 `STATUS.md`。

简要：
- v1.0 已可投入实战
- 0 个案例归档（等待第 1 案）
- 914 条规律全部索引
- 16 组共识 + 22 组互补 + 200 条独门 + 4 个冲突登记

---

## 八、不要做的事

1. ❌ 不要为了取悦用户而虚增置信度
2. ❌ 不要为了避免冲突而隐瞒派别分歧
3. ❌ 不要给出无可证伪的应期（"未来某年"）
4. ❌ 不要单独使用某一派理论（必须 4 派融合）
5. ❌ 不要在没有共识/互补/独门标记的情况下给结论
6. ❌ 不要给医疗/法律/重大决策的专业建议
7. ❌ 不要直接修改 hit_count（必须通过 calibrate.py）
8. ❌ 不要 push 到 main 分支（请 push 到 feature 分支）

---

## 九、给后续接管者的话

- 本仓库追求"宁慢不假"，前期工程量大但置信度优先
- 不要为了快速给出结论而绕过仲裁引擎
- 不要为了避免冲突而隐瞒派别分歧——分歧本身是命主信息的一部分
- 每个案例都是一次理论校准，反馈回流是命脉
- v1.0 是基础版本，等积累 ≥ 10 个案例后会自动浮现需要改进的地方

如有疑问优先看：
- `STATUS.md` 看进度
- `META/rule-changelog.md` 看变更
- `cases/cases-index.md` 看案例
- `mapping/INDEX.md` 看跨派映射

---

## 十、版本历史

| 版本 | 日期 | 里程碑 |
|---|---|---|
| v0.1.0-bootstrap | 2026-05-23 | M1 仓库骨架 + schema |
| v0.5.0 | 2026-05-23 | M2-M5 4 派理论完整入库 + 引擎 |
| **v1.0.0** | **2026-05-23** | **M7 完成 · 首发可用版本** |
