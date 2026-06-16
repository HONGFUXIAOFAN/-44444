---
name: recipe-parameter-generation
version: 0.1.0
description: 配方参数生成 — 生成完整的原料清单与精确用量（含克数/毫升数）
applies_to: recipe-generator
deliverable_vision: 生成包含每种原料名称、精确用量（g/ml）、预处理方式的结构化配方参数表
deliverable_type: structured_ingredient_table
related_rule: input-parse-sop
downstream_consumers:
  - scientific-web-validation
  - recipe-generation-orchestrator-sop
configs:
  gates: ops/recipe-generator/recipe-parameter-generation-gates.yaml
  rubric: ops/recipe-generator/recipe-parameter-generation-rubric.yaml
tags:
  - recipe-generator
  - parameter-generation
  - ingredient-quantification
---

# 产出物定义

本规则负责根据结构化输入参数，生成完整的配方参数表，包括：

1. **配方参数表** (`recipe_params`): 核心产出，包含：
   - `ingredients`: 原料列表，每项含名称、用量(g)、用量(ml)、预处理方式、备注
   - `total_weight`: 总重量(g)
   - `servings`: 建议份数
   - `base_recipe_ref`: 参考基准配方来源

2. **用量推演过程** (`derivation_log`): 每个用料用量的推演依据（经验公式/标准配比/历史数据）
3. **参数元数据** (`param_meta`): 置信度、数据来源、生成时间戳

# 思考与规划

## Commonness（常识驱动）

- 中餐烹饪用量习惯：主料>辅料>调味料，常见比例为主料:辅料≈2:1-3:1
- 每份标准用量：肉类约150-200g/人、蔬菜约100-150g/人
- 调味料用量遵循经验比例：盐≈1.5-2%/主料重、酱油≈10-15ml/人份
- 菜品原料组合遵循"君臣佐使"结构：主料定基、辅料增色/增香/增质、调料定味

## Technique（技术驱动）

- 联网搜索获取基准配方：从多个可靠来源提取该菜品的标准原料组合与用量范围
- 用量标准化：将"适量""少许"等模糊描述转化为精确g/ml值，基于烹饪化学经验公式
- 比例归一化：不同来源的配方用量按"每100g主料"归一化后取中位数
- 参数输出格式统一：所有用量统一为g（固体/半固体）或ml（液体），保留1位小数

## Art（艺术驱动）

- 用量不追求"唯一正确答案"：烹饪是艺术，用量有合理区间而非绝对精确值
- 保留"适量"的弹性空间：对于调味料给出推荐值和可调范围，而非死板单一值
- 考虑地区口味差异：同一菜品在不同地区的用量偏好（如川菜偏重油、粤菜偏清淡）
- 参数表应"人机双可读"：既适合程序解析，也适合人类阅读和使用

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
| gate7_eval_dataset | 评测数据集 | no | eval/recipe-generator/recipe-parameter-generation/下至少3个测试用例 |
| gate8_universal_gates_unchanged | 通用Gates未修改 | yes | gate0-gate8的定义不得偏离通用模板 |
| gate10_trigger | 触发器定义 | yes | WHEN节需明确定义触发条件，依赖001输入解析结果 |
| gate10_search | 联网搜索 | yes | 需描述联网搜索获取基准配方的方法、搜索策略、来源选择标准 |
| gate10_ingredient_list | 原料清单 | yes | 需输出完整的原料清单，每种原料含名称、用量(g/ml)、预处理方式 |
| gate10_precise_quantity | 精确用量 | yes | 所有用量必须是精确数值（g或ml），不得出现"适量""少许"等模糊描述 |
| gate10_parameter_table | 配方参数表 | yes | 输出必须包含结构化的配方参数表（ingredients/total_weight/servings/base_recipe_ref） |
| gate10_acceptance | 验收检查 | no | 验收需覆盖：主料/辅料/调料比例合理、用量在合理范围、参数表可直接使用 |

## Rubric 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 精确性 | 0.40 | 原料用量是否精确到g/ml，是否消除了模糊描述，用量是否在合理范围 |
| 完整性 | 0.35 | 原料清单是否完整（主料、辅料、调味料不遗漏），参数表字段是否齐全 |
| 可用性 | 0.25 | 参数表格式是否规范统一，是否可直接供下游消费，是否附带推演依据 |

## 质量阈值

- Rubric加权平均分 >= 0.85 通过
- 任何维度单项分 >= 0.75
- 任一 critical gate 不通过则整体不通过

# 评测数据集

评测数据集存放于 `eval/recipe-generator/recipe-parameter-generation/`，至少覆盖以下场景：

1. 常见家常菜：如"西红柿炒鸡蛋"的参数生成
2. 复杂菜品：多原料组合如"宫保鸡丁"的参数生成
3. 地域变体：同一菜品不同地区的用量差异（如川味vs粤式）
4. 边角case：只有单一主料的极简菜品
5. 大量原料菜品：如"佛跳墙"等多原料组合

# 验收

- [ ] SSOT文件YAML frontmatter所有必填字段完整
- [ ] 产出物定义清晰完整，配方参数表结构明确
- [ ] CTA三层（Commonness/Technique/Art）均有实质性内容
- [ ] gates.yaml通过schema校验（gate2_gates_schema）
- [ ] rubric.yaml通过schema校验（gate3_rubric_schema）
- [ ] 评判数据集至少包含5个测试用例
- [ ] 所有critical gate通过
- [ ] Rubric加权平均分 >= 0.85
