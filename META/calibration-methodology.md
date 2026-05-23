# 置信度校准方法论 · v1.0

> 双轨制置信度的精确数学定义与升降级规则。

---

## 一、双轨制定义

每条规律的置信度由 2 个数值表达：

```
final_score (0-100)  → 决定 stars (1-5)
```

输出格式：`★★★★ (87%)`

---

## 二、组成公式

```
final_score = α × static_score + β × dynamic_score

其中：
α = 0.4   (静态权重，理论强度)
β = 0.6   (动态权重，应验权重)

约束：当 hit_count + miss_count < 3 时，dynamic_score 不可信
      → 此时 final_score = static_score（暂用静态分）
```

---

## 三、静态分（static_score）

```
static_score = base + adjustment

base = 60     (单派独门基线)
     + 8      (有 1 条同向支持)
     + 12     (有 2 条同向支持)
     + 15     (3+ 条同向支持，封顶)
     = 60 ~ 75

base 上调 → 共识层规律 base = 80
            互补层规律 base = 65
            独门层规律 base = 50

adjustment 范围 -15 ~ +15：
+5  来源为大师亲口讲义
+5  规律明确给出量化条件
+5  规律有具体应期时间窗
-5  规律表达模糊（"或"、"大约"）
-10 规律与基础理论冲突
+10 规律在 4 派理论之外的古籍中也有印证
```

---

## 四、动态分（dynamic_score）

```
hit_rate = hit_count / (hit_count + miss_count)
sample_size = hit_count + miss_count

dynamic_score = hit_rate × 100 × confidence_factor

其中 confidence_factor =
  0.7  当 sample_size = 3
  0.85 当 sample_size = 5
  0.95 当 sample_size = 8
  1.0  当 sample_size ≥ 10

样本越大，hit_rate 越可信，乘以的 confidence_factor 越接近 1.0。
```

---

## 五、★ 等级映射

```
final_score >= 90  → ★★★★★
80 <= final_score < 90  → ★★★★
65 <= final_score < 80  → ★★★
50 <= final_score < 65  → ★★
final_score < 50  → ★
```

---

## 六、升降级触发

| 触发 | 当前 status | 新 status |
|---|---|---|
| sample ≥ 3 且 hit_rate ≥ 0.66 | candidate | promoted |
| sample ≥ 3 且 hit_rate ≤ 0.33 | candidate / promoted | retired |
| 暴露严重冲突 | promoted | candidate |
| 用户审定不适用 | * | frozen |

---

## 七、跨派联立加权（仲裁场景）

当多派规律对**同一对象**给出**同向结论**时，置信度联立加权：

```
joint_score = max(scores) + Σ (other_scores × 0.15)
封顶 100。

例：
  - D-LIFA-005  static=75
  - Y-LIFA-002  static=70
  - G-LIFA-008  static=72

joint_score = 75 + 70×0.15 + 72×0.15 = 75 + 10.5 + 10.8 = 96.3 → ★★★★★ (96%)
```

---

## 八、冲突场景

当多派结论**相反**时，按 `engine/arbitration.md` 的领域权重决定优先级：

```
winner_score = winner.static × winner.domain_weight - loser.static × 0.3
loser_score  = loser.static × 0.6

输出时：
  胜出方按 winner_score 计算 ★+%
  败出方在报告中显式提示："X派持反对意见，权重低于本结论"
```

---

## 九、置信度校准触发点

每次实战分析完成后：
1. 用户提供反馈（applied=true → 应验/失验）
2. `tools/calibrate.py` 自动：
   a. 更新 hit_count / miss_count
   b. 重算 hit_rate / dynamic_score / final_score / star
   c. 触发升降级判定
   d. 写入 `META/rule-changelog.md`
   e. 同步更新 `mapping/` 文件（如果分层变化）

---

## 十、防作弊保护

为避免置信度被单一案例污染：
1. 同一案例的反馈 = **1 个样本**（不论涉及多少条规律的多少次断验）
2. 单条规律 sample_size < 3 时，dynamic_score 暂不参与（默认用 static）
3. 命主自报数据 vs 客观可证伪数据要分级（自报数据 confidence_factor × 0.8）
4. 大幅升降级（star 一次跳 2 级）必须人工 review
