---
name: recipe-generation-orchestrator-sop
version: 0.1.0
description: 配方生成总控SOP — 编排所有生成步骤，管理规则间依赖关系
applies_to: recipe-generator
deliverable_vision: 生成一份完整的标准化菜谱配方，包含原料清单、用量参数、操作步骤、时间温度、验证结果，呈现在统一界面
deliverable_type: orchestrated_recipe
related_rule: input-parse-sop
downstream_consumers:
  - interface-renderer
  - recipe-storage
configs:
  gates: ops/recipe-generator/recipe-generation-orchestrator-sop-gates.yaml
  rubric: ops/recipe-generator/recipe-generation-orchestrator-sop-rubric.yaml
tags:
  - recipe-generator
  - orchestration
  - workflow-control
---

# 产出物定义

本SOP为配方生成流程的总控制器，负责编排以下步骤的执行顺序与数据流：

1. **输入解析** (调用 input-parse-sop): 将原始用户输入转为结构化参数
2. **配方参数生成** (调用 recipe-parameter-generation): 生成原料清单与精确用量
3. **科学性验证** (调用 scientific-web-validation): 联网交叉验证配方参数
4. **步骤生成** (后续扩展): 生成操作步骤与时间温度参数
5. **最终组装与呈现**: 整合所有子步骤输出，生成完整的配方文档

总控器还需处理：
- 步骤间的依赖管理与数据传递
- 并行执行优化（可并行的子任务同时触发）
- 用户确认节点（关键步骤完成后等待用户确认再继续）
- 错误处理与重试策略
- 整体流程的执行日志与追踪

# 思考与规划

## Commonness（常识驱动）

- 完整的配方生成流程包含多个专业步骤，每步有明确的输入输出
- 部分步骤存在依赖关系（如验证必须在参数生成之后），部分可并行
- 用户在关键节点需要确认（如参数生成后的原料确认），避免后续返工
- 工业化的食谱生成应标准化流程，确保每次产出一致性

## Technique（技术驱动）

- 有向无环图(DAG)编排：将各规则节点建模为DAG，按依赖关系拓扑排序执行
- 数据契约：每个子规则定义输入schema和输出schema，总控器负责校验和传递
- 并行执行引擎：无依赖关系的节点并行触发，减少总耗时
- 确认点机制：在DAG中标记需要用户交互的节点，暂存结果等待确认
- 回滚与重试：当某步骤失败时，根据依赖关系决定仅重试当前步骤还是级联重试

## Art（艺术驱动）

- 编排应"透明可视化"：用户能看到当前处于流程的哪个阶段、哪些已完成
- 确认点不应"机械打断"：在自然停顿处（而非任意位置）请求确认
- 流程进度应给人"稳步推进"的感受，而非"长时间等待后突然完成"
- 错误恢复应优雅降级，而非直接中断——提供备选路径或人工干预入口

# 质量标准

## Gates 门禁

| Gate编号 | 名称 | critical | 说明 |
|---------|------|---------|------|
| gate0_assets | 三件套文件存在性 | yes | ssot/gates/rubric三个文件必须存在 |
| gate0_input_ssot_assets | 输入SSOT三件套存在性 | yes | 输入规则的三件套文件必须存在 |
| gate1_ssot_frontmatter | YAML头必填字段 | no | name/version/description/applies_to/deliverable_vision/deliverable_type/related_rule/configs必须填写 |
| gate2_gates_schema | gates.yaml结构合规 | yes | gates文件必须符合schema |
| gate3_rubric_schema | rubric.yaml结构合规 | yes | rubric文件必须符合schema |
| gate4_path_validity | 路径有效性 | no | configs中引用的gates/rubric路径必须存在 |
| gate5_required_gates | 必需Gate齐全 | yes | 所有required_gates必须在gates文件中定义 |
| gate6_weight_sum | 权重总和 | no | rubric各维度权重之和应在0.95~1.05之间 |
| gate7_eval_dataset | 评测数据集 | no | eval/recipe-generator/recipe-generation-orchestrator-sop/下至少3个测试用例 |
| gate8_universal_gates_unchanged | 通用Gates未修改 | yes | gate0-gate8的定义不得偏离通用模板 |
| gate10_trigger | 触发器定义 | yes | WHEN节需明确定义触发条件，包含"用户输入已通过input-parse-sop解析完成" |
| gate10_workflow | 工作流编排 | yes | 需描述完整的工作流编排：步骤列表、依赖关系、并行策略、用户确认节点 |
| gate10_step_orchestration | 步骤编排 | yes | 需明确定义各步骤的执行顺序、数据传递方式、并行执行的分支 |
| gate10_user_confirmation | 用户确认节点 | yes | 需定义用户确认的触发时机、确认内容、超时处理 |
| gate10_error_handling | 错误处理 | no | 需定义各步骤失败时的重试策略、降级方案、人工干预入口 |
| gate10_acceptance | 验收检查 | no | 验收需覆盖：完整流程走通、并行执行正确、确认节点交互正常、异常恢复可工作 |

## Rubric 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 完整性 | 0.40 | 是否覆盖所有配方生成所需步骤，依赖关系是否完整正确 |
| 可操作性 | 0.35 | 每个编排步骤是否有明确的触发条件、执行指令、输出定义 |
| 鲁棒性 | 0.25 | 是否考虑异常处理、重试策略、降级方案、边界case |

## 质量阈值

- Rubric加权平均分 >= 0.85 通过
- 任何维度单项分 >= 0.75
- 任一 critical gate 不通过则整体不通过

# 评测数据集

评测数据集存放于 `eval/recipe-generator/recipe-generation-orchestrator-sop/`，至少覆盖以下场景：

1. 正常流程：标准输入下全流程走通
2. 并行执行：验证可并行步骤的并发执行正确性
3. 用户确认：确认节点的触发与等待机制
4. 步骤失败恢复：某步骤失败后的重试与降级
5. 依赖中断：上游步骤失败对下游的影响处理

# 验收

- [ ] SSOT文件YAML frontmatter所有必填字段完整
- [ ] 产出物定义清晰完整，覆盖所有编排步骤
- [ ] CTA三层（Commonness/Technique/Art）均有实质性内容
- [ ] gates.yaml通过schema校验（gate2_gates_schema）
- [ ] rubric.yaml通过schema校验（gate3_rubric_schema）
- [ ] 评判数据集至少包含5个测试用例
- [ ] 所有critical gate通过
- [ ] Rubric加权平均分 >= 0.85
