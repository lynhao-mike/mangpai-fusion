# 职业路径关系推理引擎实施计划

**目标：** 停止全局十神计数路线，将职业路径能力重建为“职业柱定位—左柱定性—我宫/他宫关系—力量与制化—大运时序状态”的可审计推理器，并只在全新未见验证集上执行一次预注册竞争评估。

**范围与风险：** 本工作跨越评估数据、领域契约、命盘特征抽取、时序状态机和晋级门禁。最大风险是复用已被 v1-v3 观察过的 P 系列 40 案造成数据泄漏，或在标签揭示后修改规则。旧 40 案只保留为开发回归集，不再承担晋级证据。v1-v3 代码和冻结产物保留为失败基线，不切换生产入口。

**架构/顺序：**

1. 先冻结数据用途与预注册评估协议，阻断跨版本泄漏；
2. 再将高派职业五步法固化成无权重关系契约；
3. 依据契约构建命盘职业关系图和可审计 trace；
4. 在关系图上实现原局倾向与大运现实状态的双层裁决；
5. 最后才允许在全新 holdout 上运行一次三模型竞争实验和晋级门禁。

**不可妥协原则：**

- 旧 P 系列 40 案不得作为独立 holdout 或晋级证据；
- 预测阶段不得读取标签、反馈、occupation 或 known facts；
- 规则、样本清单、指标和阈值必须先于预测冻结；
- 没有可靠大运日期边界时，当前路径层必须显式 unknown/abstain；
- 任职、经营、mixed、transitioning 和 unknown 不得互相静默压缩；
- 新关系模型未通过门禁前不得进入生产默认路由。

## 任务 1：封存开发集并建立未见验证集准入/预注册契约

- **文件：**
  - 新增 `META/as-of-evaluation/career-path-dataset-registry-v1.json`；
  - 新增 `META/as-of-evaluation/career-path-holdout-preregistration-v1.json`；
  - 新增 `engine/contracts/14-career-path-evaluation-protocol-v1.md`；
  - 新增 `tools/career_path_holdout_gate.py`；
  - 新增 `tests/test_career_path_holdout_gate.py`。
- **边界：** 数据注册表明确旧 40 案为 `development_replay_only`，记录禁止用途；新 holdout 清单只能包含未出现在旧 cohort、旧预测、旧冻结和旧标签开发集中的 case_id。真实未见案例不足 30 时，门禁必须关闭，不得用占位样本伪造评分。
- **实现：** 门禁校验样本数量、两类最低数量、case_id 排他性、双人标注/裁决状态、标签文件哈希、预注册时间顺序和 `labels_revealed=false`。预注册文件固定三模型、指标、阈值及一次冻结要求。
- **验证：** 构造重叠、样本不足、单类不足、标签提前揭示等负例测试；合法但尚未凑足数据时应返回“not ready”，而不是生成成绩。
- **完成：** 仓库可机器判定“哪些数据只能开发、哪些数据有资格做晋级 holdout”，且当前若无 30 个未见严格样本会诚实阻塞任务 5 的最终评分。

## 任务 2：实现职业柱五步法的可执行关系契约

- **文件：**
  - 新增 `engine/asof/career_relation_contract.py`；
  - 新增 `engine/contracts/15-career-relation-inference-v1.md`；
  - 新增 `tests/asof/test_career_relation_contract.py`。
- **边界：** 契约只表达职业柱候选、选择步骤、我宫/他宫、左柱、关系类型、证据和冲突；不得内置经验权重或读取职业标签。
- **实现：** 定义冻结枚举/数据类：柱位、宫位、职业柱选择步骤、关系类型（合、冲、刑、害、藏透、邻柱、通根、入库等）、候选状态、否决/弃权原因。明确多个候选、时柱无左柱、他宫无我宫感应等边界行为。
- **验证：** 测试类型不变量、非法关系拒绝、步骤优先级、无候选和多候选冲突；契约序列化必须确定性稳定。
- **完成：** 理论中的“五步先定柱、左柱辨性质”成为独立、可测试、无浮点权重的数据契约。

## 任务 3：实现命盘职业关系图与可审计 trace

- **文件：**
  - 新增 `engine/asof/career_relation_graph.py`；
  - 新增 `tests/asof/test_career_relation_graph.py`；
  - 视需要复用但不破坏 `engine/predicates/palace.py`、`engine/features/chart_feature_vector.py` 的现有谓词。
- **边界：** 输入限于四柱事实；输出关系图、职业柱候选和 trace。不得输出最终职业真值，不得读取反馈。首版只实现仓库已有确定性谓词可以支撑的关系；无法可靠计算的“通根强弱/力量四态”必须标为 unresolved，禁止伪精确。
- **实现：**
  - 节点：四柱干支、藏干、十神、宫位、职业柱候选；
  - 边：邻柱、透藏、六合/冲/刑/害、已支持的生克与库关系；
  - 选择器：严格执行五步职业柱优先级；
  - trace：逐步记录候选、命中关系、淘汰理由、左柱性质和 unresolved 信号。
- **验证：** 使用合成命盘覆盖五个选择步骤、我宫优先、他宫必须关联、左柱边界、多候选冲突；同一输入重复构建结果必须完全一致。
- **完成：** 任意合法四柱都能产生可审计关系图或明确弃权，且“见财/见食伤”不再自动构成经营结论。

## 任务 4：实现原局倾向/大运现实状态双层时序裁决

- **文件：**
  - 新增 `engine/asof/career_relation_reasoner.py`；
  - 修改 `engine/asof/career_path_state.py`（仅在现有契约不足时向后兼容扩展）；
  - 修改 `engine/contracts/13-career-path-state-machine-v1.md` 或新增 v2 契约；
  - 新增 `tests/asof/test_career_relation_reasoner.py`。
- **边界：** 第一层只由原局关系图产生倾向；第二层必须有 `as_of_date` 和可定位的大运起止边界。现实状态仍只能来自已核验事件，不得由命理倾向补写。
- **实现：**
  - 原局层根据职业柱及左柱性质输出 employment/entrepreneurship 双布尔或冲突弃权；
  - 大运层计算大运干支与职业关系图的新增/破坏关系；
  - 日期缺失、区间重叠或无法定位时返回 `insufficient_dayun_information`；
  - mixed 与 transitioning 保持一等状态；
  - 输出必要条件、反证和未决关系。
- **验证：** 覆盖原局任职/经营/双链/无证据，大运开放/抑制/冲突，日期边界缺失，先任职后经营等状态轨；禁止 `as_of_date=None` 时生成当前大运裁决。
- **完成：** 系统能明确区分“原局路径倾向”“某时点大运上下文”“截至该时点的已核验现实状态”。

## 任务 5：实现预注册三模型竞争实验与一次冻结门禁

- **文件：**
  - 新增 `tools/career_path_competition_harness.py`；
  - 修改 `tools/career_path_promotion_gate.py` 以兼容正式时序标签 schema，同时保持旧 schema 行为；
  - 新增 `tests/test_career_path_competition_harness.py`；
  - 新增 `tests/test_career_path_promotion_gate.py` 或扩展现有测试；
  - 仅在 holdout 准入通过后生成 `predictions/`、`META/as-of-evaluation/` 和 `reports/` 下的冻结产物。
- **边界：** 固定比较多数类/弃权基线、冻结的旧计数基线、新关系模型。预测、冻结、揭示标签、评分严格分阶段；一个预注册 ID 只能评分一次。没有合格未见集时只交付可运行 harness 和阻塞证据，不得生成虚假结果。
- **实现：** 统一预测 schema；冻结预测 SHA256、代码/规则版本、cohort 哈希和预注册哈希；重新计算 balanced accuracy、两类 recall、coverage、majority baseline，并增加职业柱定位一致率、trace 完整率、mixed/transitioning 识别指标。promotion gate 接受标签字段适配器，但禁止自动猜测未知 schema。
- **验证：** 测试哈希篡改、ID 不一致、重复评分、标签提前读取、开发集混入、新旧标签 schema、阈值边界；运行现有职业分类器相关回归测试。
- **完成：** 合格新 holdout 到位后可一次性运行三模型竞争；未达门槛时关系模型保持实验状态并降级为结构证据助手。

## 子任务编排

- **子任务 A（先行、不可并行绕过）：** 任务 1，建立数据隔离和预注册门禁。
- **子任务 B（任务 1 后可开始）：** 任务 2，冻结关系契约。
- **子任务 C（依赖任务 2）：** 任务 3，构建关系图。
- **子任务 D（依赖任务 3）：** 任务 4，构建双层时序裁决。
- **子任务 E（依赖任务 1 和任务 4）：** 任务 5，竞争 harness 与晋级门禁。

每个子任务必须返回：修改文件清单、契约变化、测试命令和测试结果、尚未解决的证据缺口。后一任务不得假设前一任务成功，必须以仓库实际产物和测试为准。

## 最终验证

- 运行新增专项测试；
- 运行现有职业路径分类器、状态机和 promotion gate 相关测试；
- 运行 `pytest tests/asof tests/test_p_series_career_blind_harness.py tests/test_career_path_holdout_gate.py tests/test_career_path_competition_harness.py -q`（仅包含实际存在文件）；
- 检查旧 40 案未进入新 holdout；
- 检查预测阶段依赖图不包含反馈、标签或 occupation；
- 检查没有生产默认入口切换；
- 完成声明前执行独立验证证据 Gate。

## 风险与回退

- **未见样本不足：** 不回退到旧 40 案；任务 5 停在“评估未就绪”，等待新样本。
- **理论无法稳定操作化：** 若职业柱选择在合成测试或双人解释中不一致，停止任务 3/4 扩张，先修订契约。
- **现有谓词缺少关系：** 不临时用分数近似；关系标记 unresolved，并用最小新增谓词补齐。
- **关系模型未胜基线：** 不继续在新 holdout 调参；模型降级为证据助手，下一版本必须使用另一批未见数据。
- **兼容风险：** v1-v3 和生产入口保持不变；新能力使用独立模块和显式实验入口，门禁通过后再另行决定迁移。