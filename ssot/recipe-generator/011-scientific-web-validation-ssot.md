---
name: scientific-web-validation
version: 0.1.0
description: 科学性联网验证 — 通过联网搜索交叉验证配方参数（至少2个来源）
applies_to: recipe-generator
deliverable_vision: 生成配方参数的科学性验证报告，包含交叉验证结果、各参数置信度、不一致项标注
deliverable_type: validation_report
related_rule: recipe-parameter-generation
downstream_consumers:
  - recipe-generation-orchestrator-sop
configs:
  gates: ops/recipe-generator/scientific-web-validation-gates.yaml
  rubric: ops/recipe-generator/scientific-web-validation-rubric.yaml
tags:
  - recipe-generator
  - web-validation
  - cross-reference
  - scientific-verification
---

# 产出物定义

本规则负责对上游生成的配方参数表进行科学性联网验证，输出：

1. **验证报告** (`validation_report`): 核心产出，包含：
   - `overall_confidence`: 整体置信度评分(0-1)
   - `source_summary`: 所参考来源摘要（来源URL、权威性评分、收录时间）
   - `ingredient_validation`: 原料种类验证结果（是否常见组合、是否缺失关键原料、是否含危险搭配）
   - `quantity_validation`: 用量比例验证结果（各原料用量比例是否符合行业基准范围）
   - `temp_time_validation`: 温度时间验证结果（烹饪温度、时长是否符合科学范围）
   - `safety_validation`: 安全性验证结果（是否含禁忌搭配、过敏原料标注、食品安全温度）

2. **不一致项清单** (`discrepancies`): 与主流配方存在偏差的参数项及建议修正值
3. **验证元数据** (`validation_meta`): 搜索时间、来源数量、最低置信度参数

# 思考与规划

## Commonness（常识驱动）

- 互联网上的食谱质量参差不齐：从专业厨师博客到用户随意分享，权威性差异巨大
- 同一菜品存在多种"正宗"做法：不应强制唯一标准，而应标注参考范围
- 食品安全有硬性科学标准：如中心温度>74°C、某些食材禁忌搭配
- 专业烹饪知识网站（下厨房、美食杰等）相对可靠，纯社交媒体来源权重应降低

## Technique（技术驱动）

- 来源权威性评估：根据域名信誉、内容专业度、引用量建立来源可信度评分模型
- 多源交叉验证：至少从2个独立来源提取配方参数，计算一致性指标
- 置信度计算：来源数量 × 一致性 × 来源权威性的加权结果
- 科学边界检查：用量是否超出食品安全范围、温度是否达到杀菌要求
- 差异分析与报告：对不一致参数标注差异幅度、可能原因、建议取值

## Art（艺术驱动）

- 验证不应"粗暴否定"：部分"非主流"做法可能正是该菜品的特色所在
- 验证结果要"人可读"：不仅给出Yes/No，更要解释为什么、是否可以接受
- 对"家常配方"与"专业配方"的差异保持宽容：家庭做法和专业后厨存在天然差异
- 不确定时不武断：低置信度参数标注"待人工复核"而非强行修正

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
| gate7_eval_dataset | 评测数据集 | no | eval/recipe-generator/scientific-web-validation/下至少3个测试用例 |
| gate8_universal_gates_unchanged | 通用Gates未修改 | yes | gate0-gate8的定义不得偏离通用模板 |
| gate10_trigger | 触发器定义 | yes | WHEN节需明确定义触发条件，依赖010配方参数生成结果 |
| gate10_web_search | 联网搜索交叉验证 | yes | 需描述联网搜索策略：至少≥2个独立来源，跨平台搜索，权威性评分 |
| gate10_confidence | 置信度计算 | yes | 需定义置信度计算方法：来源数量×一致性×权威性的加权结果 |
| gate10_ingredient_check | 原料种类验证 | yes | 验证原料组合是否常见、是否缺失关键原料、是否含危险食材搭配 |
| gate10_quantity_check | 用量比例验证 | yes | 验证各原料用量比例是否在行业基准范围内，超出范围需标注 |
| gate10_temp_time_check | 温度时间验证 | yes | 验证烹饪温度/时长是否符合科学标准，特别是食品安全相关参数 |
| gate10_safety_check | 安全性验证 | yes | 验证是否存在食材禁忌搭配、过敏风险、食品安全隐患 |
| gate10_acceptance | 验收检查 | no | 验收需覆盖：多源交叉验证有效、置信度计算合理、不一致项正确标注 |

## Rubric 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 验证深度 | 0.40 | 是否覆盖原料种类、用量比例、温度时间、安全性四个验证维度 |
| 来源可靠性 | 0.35 | 引用来源是否有权威性评分，是否使用至少2个独立来源进行交叉验证 |
| 透明度 | 0.25 | 验证过程是否可追溯，不一致项是否充分解释，置信度是否有计算依据 |

## 质量阈值

- Rubric加权平均分 >= 0.85 通过
- 任何维度单项分 >= 0.75
- 任一 critical gate 不通过则整体不通过

# 评测数据集

评测数据集存放于 `eval/recipe-generator/scientific-web-validation/`，至少覆盖以下场景：

1. 高一致性验证：多个来源食材用量高度一致的菜品验证
2. 低一致性验证：不同来源用量差异显著的菜品验证
3. 安全性触发：含潜在危险搭配或食品安全风险的参数验证
4. 数据稀缺：搜索结果极少的小众菜品验证
5. 来源权威性差异：专业来源vs用户生成内容的对比验证

# 验收

- [ ] SSOT文件YAML frontmatter所有必填字段完整
- [ ] 产出物定义清晰完整，验证报告结构覆盖四个验证维度
- [ ] CTA三层（Commonness/Technique/Art）均有实质性内容
- [ ] gates.yaml通过schema校验（gate2_gates_schema）
- [ ] rubric.yaml通过schema校验（gate3_rubric_schema）
- [ ] 评判数据集至少包含5个测试用例
- [ ] 所有critical gate通过
- [ ] Rubric加权平均分 >= 0.85
