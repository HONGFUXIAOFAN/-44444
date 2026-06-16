---
name: input-parse-sop
version: 0.1.0
description: 输入解析SOP — 将用户输入的菜品名称、所在地区、出餐场景解析为结构化参数
applies_to: recipe-generator
deliverable_vision: 生成结构化的输入参数对象，包含标准化后的菜品名称、地区标识、场景类型，供下游规则消费
deliverable_type: structured_parameters
related_rule: recipe-generation-orchestrator-sop
downstream_consumers:
  - recipe-generation-orchestrator-sop
  - recipe-parameter-generation
configs:
  gates: ops/recipe-generator/input-parse-sop-gates.yaml
  rubric: ops/recipe-generator/input-parse-sop-rubric.yaml
tags:
  - recipe-generator
  - input-parsing
  - orchestration-input
---

# 产出物定义

本SOP负责解析用户的原始输入，输出一个标准化的结构化参数对象，包含：

1. **菜品名称** (`dish_name`): 经标准化的菜品名称（去除冗余修饰词，统一别名）
2. **所在地区** (`region`): 标准化地区标识（省/市/区域），用于地域口味适配
3. **出餐场景** (`scene`): 标准化场景类型（家庭/餐厅/外卖/宴席/其他）
4. **附加约束** (`constraints`): 用户额外指定的限制条件（忌口、预算范围、人数等）
5. **解析元数据** (`parse_meta`): 解析置信度、备选解释、异常标记

# 思考与规划

## Commonness（常识驱动）

- 用户输入具有高度随意性：同一道菜可能有多种称呼（如"西红柿炒鸡蛋"/"番茄炒蛋"）
- 地区信息可能隐含在菜品名称中（如"川味回锅肉"隐含四川）
- 场景信息常以短语形式混入输入（如"家里做的红烧肉"）
- 需建立菜品别名映射表和地区-口味关联表作为知识底座

## Technique（技术驱动）

- 分词与NER：识别输入中的菜品实体、地名实体、场景关键词
- 别名归一化：通过别名映射表将用户口语化表达统一为标准菜名
- 缺失字段推断：当地区/场景缺失时，根据菜品发源地、季节、时间等上下文推断默认值
- 置信度评估：对每个解析字段输出置信度分数，低置信度字段触发人工确认

## Art（艺术驱动）

- 保留用户意图的"人情味"：不将"随便来点下饭菜"机械地映射为空输入
- 模糊输入不应粗暴拒绝，而应友好引导并给出合理推测
- 解析过程应"透明可解释"——用户能看到系统如何理解了自己的输入
- 对地域文化差异保持敏感（如"红烧肉"在南北方做法差异显著）

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
| gate7_eval_dataset | 评测数据集 | no | eval/recipe-generator/input-parse-sop/下至少3个测试用例 |
| gate8_universal_gates_unchanged | 通用Gates未修改 | yes | gate0-gate8的定义不得偏离通用模板 |
| gate10_trigger | 触发器定义 | yes | WHEN节需明确定义触发条件，包含"用户输入已触发配方生成流程" |
| gate10_input | 必需输入字段 | yes | 必需输入字段包括：菜品名称、所在地区、出餐场景，缺一不可 |
| gate10_behavior | 解析行为 | yes | 行为层需描述：解析输入、标准化菜品名、识别地区、识别场景、输出结构化参数 |
| gate10_output | 输出定义 | no | 输出需包含dish_name/region/scene/constraints/parse_meta五个字段 |
| gate10_acceptance | 验收检查 | no | 验收需覆盖：解析覆盖率≥90%、边界case处理、低置信度降级策略 |

## Rubric 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 系统性 | 0.35 | 解析流程是否完整覆盖所有输入形态（完整输入/部分缺失/歧义输入/对抗输入） |
| 可操作性 | 0.35 | 每个解析步骤是否有明确的输入-处理-输出定义，步骤粒度是否适宜 |
| 实用性 | 0.30 | 解析结果是否可直接被下游规则消费，边界case处理是否合理 |

## 质量阈值

- Rubric加权平均分 >= 0.85 通过
- 任何维度单项分 >= 0.75
- 任一 critical gate 不通过则整体不通过

# 评测数据集

评测数据集存放于 `eval/recipe-generator/input-parse-sop/`，至少覆盖以下场景：

1. 完整输入：菜品名称 + 地区 + 场景齐全
2. 部分缺失：仅提供菜品名称（不提供地区和场景）
3. 歧义输入：菜名存在多义（如"红烧肉"对应多种地域做法）
4. 模糊输入：非标准表达（如"随便来个家常菜"）
5. 对抗输入：明显错误或冲突的输入组合

# 验收

- [ ] SSOT文件YAML frontmatter所有必填字段完整
- [ ] 产出物定义清晰完整，五个输出字段均有说明
- [ ] CTA三层（Commonness/Technique/Art）均有实质性内容
- [ ] gates.yaml通过schema校验（gate2_gates_schema）
- [ ] rubric.yaml通过schema校验（gate3_rubric_schema）
- [ ] 评判数据集至少包含5个测试用例
- [ ] 所有critical gate通过
- [ ] Rubric加权平均分 >= 0.85
