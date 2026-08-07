# as-of life-state 下一任务格局裁决（A / C / D）

- 日期：2026-07-29
- 范围：只裁决优先级，不实施 A、C 或 D
- 执行边界：LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION
- 证据边界：以当前冻结事实为限；不把历史 handoff 当作现行 Gate 事实源

## 1. Thesis

**下一步不该继续给旧治理链补文件，也不该在目标尚未定义时替 F10 发明目标；应该把 as-of 引擎接入正式 blind-bundle 隔离协议，让“看不见答案地冻结判断”第一次成为可重复运行的系统能力，而不是依赖操作者纪律和脆弱命令载体的手工仪式。**

置信度：**高（85%）**。

原因不是 A 最容易，而是本轮 N50 扩样再次暴露了当前系统的根本缺口：候选池有 92 案，真正阻断扩样的不是数据不足，也不是命理规则不足，而是盲态边界、执行载体、冻结落盘和反馈释放尚未合成一条可靠的机器协议。

## 2. 当前陷阱

当前最危险的误判，是把三个不同层级的问题当成并列待办：

- A 是认识论与执行基础设施问题：系统能否在答案不可见时产生可复验冻结证据；
- C 是历史治理阻塞项，但现行控制证据已显示其后续实现与验证完成；
- D 是业务目标选择问题，当前明确处于 HOLD，尚没有唯一目标、owner 和依赖。

若按“哪个文档看起来还没收尾”排序，会重开已被后续证据覆盖的 C；若按“哪个 Gate 编号最大”排序，会在无目标条件下启动 D。两者都会绕开唯一已经被真实失败重复证明的主矛盾：盲断闭环目前不能稳定、批量、无污染地执行。

## 3. 高位方向

终局不应是“有一个 as-of 引擎，再有一个 prospective blind-bundle 工具，靠人记住先运行谁、不能打开什么文件”。终局应是单一不可逆协议：

1. blind-bundle 成为唯一可消费输入载体；
2. as-of runner 只能读取 bundle 明示允许的盲态材料；
3. 冻结包成功落盘、哈希复验前，反馈材料在接口层不可达；
4. feedback release 由冻结制品身份触发，而不是由操作者决定何时打开文件；
5. 单案与批量使用同一 runner、同一 schema、同一 create-only 与幂等语义；
6. 污染、无效样本和执行失败都成为结构化结果，不再依赖会话叙述补记。

这不是为 N50 单独造脚本，而是把真实盲断变成平台级实验能力。N50 只是第一批能检验它的证明材料。

## 4. Kill-list

### 4.1 杀掉候选 C 作为“当前下一任务”

历史 [`handoff.md`](../handoff.md:152) 第 8 节确实记录过 P-2 producer-owned current-run identity authority 为 BLOCKED，第 9 节也要求先做 G6 全局恢复；但它同时明确 handoff 不是现行 Gate 事实源。更新的 [`production-implementation-control.md`](production-implementation-control.md:70) 已记录：

- G6、G7、G8、G9 均为 COMPLETED；
- current-run authority 精确测试 16 passed；
- `tests/f09` 1172 passed；
- G10.9 已 evidence-bounded freeze。

因此，C 作为原始措辞中的“解决 BLOCKED”已经 stale / superseded。可以保留其历史追溯价值，但不得重开为新实施任务，除非出现更新、更权威的回归证据证明 current-run authority 再次失效。

### 4.2 杀掉“先替 F10 找个目标再说”

[`production-implementation-control.md`](production-implementation-control.md:328) 明确冻结 `G10.10 = HOLD F10`，原因是业务目标、owner 与依赖尚未由现有事实唯一确定。HOLD 不是待实现功能清单。没有业务目标时启动 F10，只会制造新的治理壳层并稀释已暴露的真实问题。

### 4.3 杀掉手工会话隔离作为规模化方案

本轮 [`as-of-life-state-blind-judgment-n50-extension-report.md`](../reports/as-of-life-state-blind-judgment-n50-extension-report.md:39) 已记录：

- RF000118 因读取越过 `known_facts:` 发生污染；
- RF000149 因三种 shell / Python 载体解析失败，未形成冻结包；
- 92 个机械安全候选最终新增有效 N=0。

继续依靠“操作者小心一点”和更长的内嵌命令，不是扩样方案。

### 4.4 杀掉为 N50 特制一次性批处理器

如果新 runner 只认识本轮 50 案、只产出本轮命名的 JSON、或把反馈路径硬编码进脚本，它会通过一次任务，却不会形成可复用能力。目标应是通用 blind-bundle → as-of freeze → release → verify 协议，N50 只是调用方。

### 4.5 杀掉以规则扩充替代未知答案检验

在正式盲态执行协议建立前，继续扩规则、调权重或提高已知答案报告吻合度，无法证明真实预测能力。先把“不知道答案时能否稳定运行并留下证据”做成系统事实。

## 5. 三种方案

| 方案 | 动作 | 优点 | 代价 / 风险 | 裁决 |
|---|---|---|---|---|
| 保守 | 选择 D，继续澄清 F10 业务目标、owner 与依赖；A 保持手工 | 治理顺序整齐，不立即触碰工具集成 | 不解决本轮真实阻断；F10 目标仍可能是人为发明；N50 继续停摆 | 不推荐 |
| 干净 | 直接选择 A，把 as-of 完整接入 [`tools/school_capability_prospective.py`](../tools/school_capability_prospective.py) 的 blind-bundle 协议，并一次性统一单案、批量、冻结、释放、核验 | 终局最清晰；消除双轨与人工纪律 | 变更面大；若一次覆盖全部流程，容易把协议设计、迁移和 N50 执行耦合成巨型 Gate | 方向正确，但不应一次性全量实施 |
| 分阶段 | 选择 A，但先做最薄纵切：一个正式 blind-bundle 经一个稳定 runner 生成真实 as-of 冻结包并完成不可逆反馈释放；首证通过后再扩到小批量，最后恢复 N50 | 直接打主矛盾；证明点小；失败可定位；不会用架构蓝图代替运行证据 | 需要严格禁止临时旁路和 N50 特例；首阶段不等于 N50 完成 | **推荐** |

## 6. 明确推荐

**推荐候选 A，采用分阶段方案。**

优先级排序：

1. **A — NOW：** 建立 blind-bundle 到 as-of 冻结/释放/核验的最薄纵切；
2. **D — HOLD：** 等 A 的 First Proof Point 产生真实运行边界后，再据此判断 F10 是否应以“可验证盲断实验平台”作为业务目标，以及谁是 owner；
3. **C — DROP AS STALE：** 不作为当前工作项重开；仅当新鲜权威验证推翻 G6–G10 已完成证据时恢复。

A 先于 D，不是因为技术天然高于业务，而是因为这里已经有明确业务问题：真实盲断扩样被执行协议阻断。A 能以一个可证伪纵切回答“这条路是否可行”；D 当前却没有足够事实唯一确定另一个更高价值目标。

## 7. First Proof Point

首个证明点必须小于 N50，但必须端到端且不可伪装：

> **从一个新鲜、未触碰反馈的 RF 案例创建正式 blind-bundle；仅通过稳定的文件式或模块式 runner 调用真实 as-of API；create-only 生成冻结包；独立复验 canonical hash 幂等；证明 feedback 在冻结前接口不可达；冻结复验后由制品身份释放对应 feedback；再生成一条权威核验结果。整个过程不使用长内嵌 shell 程序，不直接读取原始 feedback 路径，不手写引擎结果 JSON。**

首证验收至少包含：

- 输入 bundle 的允许读取集合与禁止读取集合可机械检查；
- runner 不接受任意 feedback 路径；
- 冻结前读取反馈必须 fail-closed；
- 冻结包由真实 as-of API 生成；
- 相同输入幂等复跑得到相同 canonical hash，且 create-only 不覆写；
- release 与 freeze package identity 绑定；
- 阶段二结果可追溯到同一冻结哈希；
- 一次污染或 runner 失败以结构化失败结果退出，不留下半成品；
- 精确自动化测试与一个真实案例 smoke 均通过。

首证通过只证明协议纵切可行，不证明 N50、命中率、生产就绪或 F10 自动 GO。

## 8. 推翻条件

以下任一条件成立，就推翻“现在优先做 A”的推荐：

1. 新鲜权威证据证明 [`tools/school_capability_prospective.py`](../tools/school_capability_prospective.py) 的 blind-bundle 协议无法承载 as-of 所需的盲态四柱、大运、截止日与冻结身份，且适配必须破坏其既有不可逆边界；
2. 仓库中已存在另一条正式、自动化、无反馈路径注入、可批量、可幂等的 as-of blind-bundle runner，本轮失败仅因未使用它；
3. G10.10 获得新的明确裁决，F10 被唯一确定为更紧急、带 owner、依赖和时限的业务目标，并且延迟它的可量化损失显著高于延迟盲断闭环；
4. current-run authority 的新鲜精确测试或权威合同出现回归，推翻 [`production-implementation-control.md`](production-implementation-control.md:70) 中 G6–G9 COMPLETED 与 16 passed 的后续证据，使 C 再次成为真实主阻塞；
5. First Proof Point 必须修改生产默认路径或扩大到不可审查的大写集才能成立，无法保持隔离原型与 fail-closed。

若 1 或 5 成立，不应退回手工脚本；应重新裁决更干净的统一隔离载体。若 2 成立，应删除重复建设，直接恢复 N50。若 3 或 4 成立，再重新排序 D 或 C。

## 9. 收益账单

| 收益项 | 直接收益 | 后续杠杆 |
|---|---|---|
| 认识论可信度 | 真正区分“未知答案下的预测”与“已知答案后的解释” | 命中率、规则价值和路由价值第一次有可信基线 |
| 防污染 | 从操作者纪律升级为接口不可达与 fail-closed | 批量扩样不再随会话长度提高污染概率 |
| 可执行性 | 从长内嵌命令升级为稳定 runner | Windows shell 转义不再是研究主阻塞 |
| 可审计性 | freeze、release、verification 共用制品身份和哈希链 | 可独立复核单案，也可汇总 N50 |
| 可复用性 | 单案与批量共享同一协议 | 事业域之外的未来扩展不必复制手工流程 |
| 治理降噪 | C 被判 stale，D 保持有理由的 HOLD | 避免重开已完成链路或制造无目标 F10 |
| 投资顺序 | 先证明最小纵切，再扩大样本 | 把大改造风险压缩到首个可证伪证明点 |

最大的收益不是“终于能跑 50 案”，而是以后每一次规则、模型、派别路由或报告质量改进，都可以接受同一套未知答案检验。没有这条能力，优化只能继续依赖已知事实下的吻合感；有了它，项目才开始拥有可累计的预测证据。

## 10. 最终裁决与唯一下一动作

最终裁决：**A > D > C；执行策略选择 A 的分阶段纵切。**

- A：推荐，进入下一独立合同设计 Gate；
- D：继续 HOLD，不在本轮替 F10 发明目标；
- C：按更新证据从候选集中删除，不重开历史 BLOCKED。

**唯一下一动作：在新的受控任务中，仅设计并冻结“A 的 First Proof Point 合同”，明确 blind-bundle 输入边界、稳定 runner 接口、freeze-before-release 状态机、create-only / 哈希幂等、精确写集与验收测试；合同获独立批准前不实施 A，不启动 D，不重开 C。**

本裁决没有修改生产代码、测试、既有合同、案例原文件或 [`handoff.md`](../handoff.md)，也没有执行 Git 或 GitHub 操作。
