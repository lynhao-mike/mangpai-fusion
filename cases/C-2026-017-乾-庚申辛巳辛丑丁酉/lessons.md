# Case C-2026-017-乾-庚申辛巳辛丑丁酉 · 经验教训

> 首次分析 · 待回测后回填。
>
> ⭐ **本案是 `.kiro/steering/auto-archive.md` v1.1 §2.0「known_facts 不阻塞」原则的首次执行案例**。
> 流程层教训记录在 §五、§六。

---

## 一、新发现的规律

> 待命主反馈后回填。

| 规律描述 | 派别归属 | 是否新增到 theory/{school}/ |
|---|---|---|
| (待回填) | - | - |

---

## 二、规律升降级

> 待命主反馈后回填。

| 规律 ID | 当前 status | 应改为 | 原因 |
|---|---|---|---|
| (待回填) | - | - | - |

---

## 三、仲裁规则修正

本案 4 派结论高度同向，未触发冲突仲裁。无 CFL 修正。

---

## 四、领域权重调整建议

> 待回测后回填。

| 领域 | 派别 | 当前权重 | 建议 |
|---|---|---|---|
| (待回填) | - | - | - |

---

## 五、模板/输出格式改进（v1.1 流程教训）

### 5.1 缺 known_facts 案例的"轻量立案"路径

**触发场景**：命主只贴八字盘 + 大运（无回测真值）。

**v1.0 旧行为**：agent 拒绝立案，要求命主先补 known_facts → 用户体验差，许多潜在案例因"门槛高"流失。

**v1.1 新行为**（本案首次实践）：
1. agent 把非标输入（如 `$BASE/$FOUR/$DY_LOOP` 风格）翻译为 `templates/input-from-wenzhen.md` schema
2. `known_facts` 字段写 `unknown`，加 `preflight_warnings` 列出缺哪些项
3. 立即写四件套 + report + cases-index 一行，commit + push main
4. 应期断语 ★ 上限自动封顶 ★4（不出 ★5 铁断）
5. 后续命主补 known_facts → 走 Stage 6 反馈回流升档

### 5.2 templates/input-from-wenzhen.md 应增"非标输入翻译指引"

建议在 `templates/input-from-wenzhen.md` 文末增加：
```
## 非标输入兼容
若命主使用 `$BASE/$FOUR/$DY_LOOP` 风格、问真八字 APP 截图、或其他非标格式，
agent 应自行翻译为本 schema，不得拒收。具体翻译表见 cases/C-2026-017/lessons.md §五.3。
```

### 5.3 非标格式翻译表（本案积累）

| 原始字段 | 含义 | 标准 schema 字段 |
|---|---|---|
| `Sex:乾` | 男 | `gender: M` |
| `Sex:坤` | 女 | `gender: F` |
| `Solar:YYYY-MM-DD HH:MM` | 公历精到分 | `solar_birth` |
| `Lunar:...` | 农历 | `lunar_birth`（参考用） |
| `Sun:...` | 真太阳时 | `solar_true` |
| `Siling:丙火用事` | 司令 | `siling` |
| `Tai:壬申(剑锋金)` | 胎元 | `taiyuan` |
| `Ming:己卯(城头土)` | 命宫 | `minggong` |
| `Shen:己卯(城头土)` | 身宫 | `shengong` |
| `Void:辰巳` | 旬空 | `xunkong` |
| `Start:出生后...起运 交运:...` | 起运信息 | `start_run` |
| `Y/M/D/H: 十神,天干,地支,藏干,长生,旬空,纳音,神煞` | 四柱 | `pillars[].{star,gan,zhi,...}` |
| `#YYYY,N岁,小运/大运,十神` | 大运首行 | `dy_loop[].{year,age,ganzhi,shishen}` |
| `> YYYY,干支,_` | 流年 | `dy_loop[].liunian[]` |

---

## 六、命理师沟通经验

### 6.1 用户的偏好与原则

- 用户**强烈偏好"先落盘后补全"**，不接受 agent 因数据不足而暂停
- 用户**偏好"直接合并 main"**，不开 PR（已锁定为全局 learning）
- 用户对 agent 的"过度谨慎"（如本对话上一轮的"暂不立案"建议）反感

### 6.2 给后续 agent 的提醒

- 命主只贴八字 + "分析这个八字" 这种最简输入 = **完整触发归档协议**
- 不要在对话中追问"先补 known_facts 再立案"——直接立案，把追问放进 feedback.md
- 风险提示要给（封顶 ★4），但不能让风险提示变成阻塞理由
