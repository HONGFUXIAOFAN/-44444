---
name: "标准化操作流程生成"
version: "0.1.0"
description: "从备料到成品，生成5阶段标准化操作流程的规则，确保每一步可操作、可判断、可避坑"
applies_to:
  - "recipe-generator"
deliverable_vision: "为每道配方输出一份包含备料、预处理、烹饪、调味、成品5个阶段的标准化操作流程，每个阶段标注关键节点与判断标准，并附常见错误与避坑提示"
deliverable_type: "规则文件-提示词"
related_rule: "rules/012-operation-procedure-generation.md"
downstream_consumers:
  - "Administrator"
  - "ssot-judge"
configs:
  gate: "ops/recipe-generator/gates-012-operation-procedure-generation.yaml"
  rubric: "ops/recipe-generator/rubric-012-operation-procedure-generation.yaml"
tags:
  - "操作流程"
  - "5阶段"
  - "标准化"
  - "避坑"
  - "recipe-generator"
  - "rule-012"
---

# 标准化操作流程生成 (Operation Procedure Generation) — SSOT

## 1. 产出物定义

### 使命
为任意餐饮配方自动生成一份结构完整、步骤清晰、可被普通家庭用户执行的5阶段标准化操作流程，降低操作门槛，减少失败率。

### 核心价值
- **可执行性**：每一步均有可操作的动作描述，而非模糊指导。
- **可判断性**：关键节点提供可观测的判断标准（颜色、温度、质感、时间等）。
- **避坑能力**：在容易出错的步骤旁标注常见错误及规避方法。
- **结构化**：统一使用「备料→预处理→烹饪→调味→成品」5阶段框架，便于用户按阶段准备与执行。

## 2. 思考与规划（CTA框架）

### Commonness（共性层）
- 规则适用于中餐、西餐、烘焙等各类配方。
- 五阶段模板为所有操作流程的统一骨架。
- 关键节点判断标准优先使用感官可观察的指标（色、香、味、质地），其次使用量化指标（温度、重量、时间）。

### Technique（技术层）
- 自动识别配方中的操作步骤并归类到5个阶段。
- 对每个阶段提取关键操作节点，生成判断标准。
- 根据常见烹饪失败原因数据库（如粘锅、糊底、未熟、过咸等）匹配对应步骤，生成避坑提示。

### Art（艺术层）
- 语言风格亲切但专业，适用于初中文化程度的用户理解。
- 避坑提示采用「常见误区 + 正确做法」的对比式表达，增强记忆点。
- 在保证完整性的前提下控制篇幅，避免信息过载。

## 3. 质量标准

### 3.1 Gates 门禁表

| Gate ID | 名称 | 类型 | 通过条件 | 对应脚本/检查项 |
|---------|------|------|---------|---------------|
| gate0_assets | 三件套文件存在性 | universal | SSOT、Gates、Rubric 文件均存在 | `templates/gate-scripts/check_file_paths.py` |
| gate0_input_ssot_assets | 输入资产存在性 | universal | 同上（alias） | 同上 |
| gate1_ssot_frontmatter | SSOT 元数据完整性 | universal | name, version, description, applies_to, deliverable_vision, configs 字段齐全 | 手动 |
| gate2_gates_schema | Gates 结构合规 | universal | context, gates, decision 三要素齐全 | `templates/gate-scripts/check_yaml_structure.py` |
| gate3_rubric_schema | Rubric 结构合规 | universal | scale, aggregation, rubric 三要素齐全 | `templates/gate-scripts/check_yaml_structure.py` |
| gate4_path_validity | 配置路径有效 | universal | SSOT 中引用的 gate/rubric 路径存在 | `templates/gate-scripts/check_configs_paths.py` |
| gate5_required_gates | 必需 Gate 齐全 | universal | universal gates + domain gates 均存在 | `templates/gate-scripts/check_required_gates.py` |
| gate6_weight_sum | 权重总和校验 | universal | 各维度权重之和在 [0.95, 1.05] 范围内 | `templates/gate-scripts/check_rubric_weight_sum.py` |
| gate7_eval_dataset | 评测数据集存在 | universal | `eval/recipe-generator/012-operation-procedure-generation/` 目录存在且≥3条用例 | `templates/gate-scripts/check_eval_dataset.py` |
| gate8_universal_gates_unchanged | 通用Gate未被篡改 | universal | universal gates 的定义与基线一致 | `templates/gate-scripts/check_universal_gates.py` |
| gate10_trigger | 触发器规则 | domain | 触发器描述明确引用 WHEN + 上游规则 011 | 手动 |
| gate10_input | 输入字段 | domain | 输入包含配方数据（原料、步骤、成品信息） | 手动 |
| gate10_behavior | 行为规则 | domain | 按5阶段组织步骤、每个关键节点有判断标准、错误步骤有避坑提示 | 手动 |
| gate10_output | 输出模板 | domain | 输出为5阶段操作流程模板，格式统一 | 手动 |
| gate10_acceptance | 验收标准 | domain | 可操作性≥0.75, 完整性≥0.75, 避坑有效性≥0.75 | 手动 |

### 3.2 Rubric 评分表

| 维度 | 权重 | 评分项 | 评分项描述 |
|------|------|--------|-----------|
| 可操作性 | 0.40 | 步骤可操作 | 每一步是否有具体可执行的动作说明，而非模糊描述 |
| 可操作性 | 0.40 | 判断标准明确 | 关键节点是否提供了可观测的判断标准 |
| 完整性 | 0.30 | 5阶段覆盖 | 是否完整涵盖备料、预处理、烹饪、调味、成品5个阶段 |
| 完整性 | 0.30 | 关键节点无遗漏 | 每个阶段的关键操作节点是否有遗漏 |
| 避坑有效性 | 0.30 | 错误识别精准 | 易错步骤是否被准确识别并标注 |
| 避坑有效性 | 0.30 | 避坑建议实用 | 避坑提示是否具体、可执行，而非泛泛而谈 |

详情见 `ops/recipe-generator/rubric-012-operation-procedure-generation.yaml`。

### 3.3 质量阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 综合质量分 Q | ≥ 0.85 | weighted_mean 聚合后的总分 |
| 单维度最低分 | ≥ 0.75 | 任意维度不得低于 0.75 |
| Gate 通过条件 | all_critical | 所有 critical gates 必须通过 |

## 4. 评测数据集

- 目录：`eval/recipe-generator/012-operation-procedure-generation/`
- 最低用例数：3
- 覆盖场景：中餐家常菜、西餐简餐、烘焙甜点
- 用例格式：每个 case 包含输入（配方原料+步骤）、期望输出（5阶段流程）、评分参考

## 5. 验收

- 运行 `ops/recipe-generator/gates-012-operation-procedure-generation.yaml` 全部 gate 通过。
- Rubric 评分 Q ≥ 0.85，各维度 ≥ 0.75。
- 评测数据集 3 条以上用例全部通过。
