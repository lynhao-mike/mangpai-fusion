# mapping/ · 跨派映射总览

> 4 派 914 条规律 → 共识金字塔 3 层 + 冲突登记。

---

## 当前覆盖

| 层级 | 文件 | 条目数 | 主题覆盖 |
|---|---|---|---|
| 底层·共识 | `consensus.md` | 16 组 | 理法 / 格局 / 婚姻 / 应期 |
| 中层·互补 | `complementary.md` | 22 组 | 婚 / 学 / 财 / 健 / 应期 / 格 / 子 |
| 上层·独门 | `exclusive.md` | ~200 条 | 4 派各自独门武器 |
| 冲突仲裁 | `conflicts.md` | 4+ | 冲突原则 + 已登记冲突 |
| **合计** | — | **~242 个映射点** | 覆盖最常用 50-80 个实战场景 |

---

## 覆盖率说明

```
4 派全部规律            914 条 (100%)
已纳入金字塔分层        约 250 条 (27%)
剩余规律                664 条 → 仍可通过 theory/{school}/index.yaml 直接调用
                       仅缺少跨派映射元数据
```

**覆盖策略**：先覆盖最常用的 27%（实战 80% 时间用得到），剩余 73% 在使用过程中按需补全。  
这与"宁慢不假"原则相符——映射质量比覆盖量更重要。

---

## 实战调用流程

```
用户提问 → 主分析器 analyst.md
              ↓
         策略选择器 strategy.yaml 路由
              ↓
   ┌──────────────────────────────────┐
   │ Step 1: 查 mapping/consensus.md   │ ← 优先匹配共识层（最铁）
   │ Step 2: 查 mapping/complementary  │ ← 多派同向加权
   │ Step 3: 查 mapping/exclusive.md   │ ← 独门武器补强
   │ Step 4: 查 mapping/conflicts.md   │ ← 显式呈现冲突
   └──────────────────────────────────┘
              ↓
   置信度引擎 (engine/confidence.yaml)
              ↓
   仲裁引擎 (engine/arbitration.md)
              ↓
       双轨置信度报告输出
```

---

## 维护更新

每完成一个案例分析后，根据反馈：

1. 验证应验/失验的规律 → 更新 hit_count / miss_count
2. 升级互补层 → 共识层（满足 4 派齐全 + ≥3 例命中 + 命中率 ≥80%）
3. 降级共识层 → 互补层（命中率 <80% 暴露问题）
4. 新独门规律 → 写入 exclusive.md
5. 新冲突 → 写入 conflicts.md

详见 `META/calibration-methodology.md`。

---

## 与既有体系的关系

本仓库 mapping 层是 gufamangpai 的 `shared-rules/confirmed-rules.md` 的**升级版**：

| 旧 (gufamangpai) | 新 (mangpai-fusion) | 增强 |
|---|---|---|
| confirmed-rules.md (6 条) | consensus.md (16 组) | +10 条共识 + 加入高派 |
| consensus-candidates.md (33 条) | complementary.md (22 组) | 重新分组 + 加入高派 |
| (无独门层) | exclusive.md (~200 条) | 新增层级 + 4 派独门武器 |
| (隐式冲突) | conflicts.md | 显式冲突仲裁规则 |

---

## 下一步扩充计划

| 优先级 | 任务 | 预计条目 |
|---|---|---|
| P0 | 补全财运层（高+段联手）共识层 | +5 |
| P0 | 补全应期层（任派 18 道完整映射） | +10 |
| P1 | 父母六亲互补层 | +8 |
| P1 | 健康灾厄共识层 | +5 |
| P2 | 性格画像层（4 派对照） | +10 |
| P2 | 职业行业映射层 | +8 |

每次实战使用一条新规律时，按需补入对应文件。
