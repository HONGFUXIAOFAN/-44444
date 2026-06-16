---
name: "成本核算与平替推荐"
version: "0.1.0"
description: "对配方原料进行成本核算，标记高价原料（占比>30%），推荐价格更低但风味接近的平替方案"
applies_to:
  - "recipe-generator"
deliverable_vision: "输入配方原料表与价格数据，输出总成本、单份成本、高价原料清单，以及高性价比平替推荐"
deliverable_type: "规则文件-提示词"
related_rule: "rules/020-cost-accounting-substitute.md"
downstream_consumers:
  - "Administrator"
  - "ssot-judge"
configs:
  gate: "ops/recipe-generator/gates-020-cost-accounting-substitute.yaml"
  rubric: "ops/recipe-generator/rubric-020-cost-accounting-substitute.yaml"
tags:
  - "成本核算"
  - "原料价格"
  - "总成本"
  - "单份成本"
  - "平替"
  - "高价原料"
  - "风味接近"
  - "recipe-generator"
  - "rule-020"
---

# 成本核算与平替推荐 (Cost Accounting & Substitute Recommendation) — SSOT

## 1. 产出物定义

### 使命
基于配方原料用量与市场价格数据，自动核算总成本与单份成本，识别占比超过30%的高价原料，并为其推荐风味接近但价格更低的平替方案，帮助用户控制烹饪成本。

### 核心价值
- **计算准确**：基于原料用量 × 单价精确计算每种原料的成本贡献，汇总为总成本和单份成本。
- **平替实用**：推荐的平替原料在风味、质地上尽量接近原原料，且在市场上容易购买。
- **透明可查**：所有成本数据和替代理由清晰展示，用户可自行验证与选择。
- **降本导向**：以降低用户烹饪成本为核心目标，但不过度牺牲品质。

## 2. 思考与规划（CTA框架）

### Commonness（共性层）
- 成本计算模型：原料成本 = 用量 × 单价，总成本 = Σ所有原料成本，单份成本 = 总成本 ÷ 份数。
- 高价阈值：单一原料成本占比超过总成本的30%即标记为高价原料。
- 平替推荐逻辑：从平替数据库中匹配与原原料风味相似度 ≥ 0.7 且价格更低的替代品。

### Technique（技术层）
- 接收结构化配方参数表（原料名称、用量、单价、份数）。
- 逐项计算原料成本，排序后标记超过阈值的高价原料。
- 对每个高价原料查询平替数据库，返回 Top 3 平替方案（按综合得分 = 风味相似度 × 0.6 + 降价比率 × 0.4 排序）。
- 计算替换后的总成本和节省金额。

### Art（艺术层）
- 平替推荐不只给名称，还附上风味差异说明和使用注意事项（如「替换后需增加少许酱油补咸」）。
- 给用户选择权：标注「推荐」「可选」「仅预算紧张时考虑」等分级建议。
- 成本展示直观：使用「单份成本约X元，其中XX原料占了Y%」的叙述方式。

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
| gate7_eval_dataset | 评测数据集存在 | universal | `eval/recipe-generator/020-cost-accounting-substitute/` 目录存在且≥3条用例 | `templates/gate-scripts/check_eval_dataset.py` |
| gate8_universal_gates_unchanged | 通用Gate未被篡改 | universal | universal gates 的定义与基线一致 | `templates/gate-scripts/check_universal_gates.py` |
| gate10_trigger | 触发器规则 | domain | 触发器明确引用 WHEN + 上游规则 010 | 手动 |
| gate10_input | 输入字段 | domain | 输入包含配方参数表（原料名称、用量、单价、份数） | 手动 |
| gate10_behavior | 行为规则 | domain | 正确计算各项原料成本与总成本、识别>30%高价原料、为高价原料推荐平替方案 | 手动 |
| gate10_output | 输出模板 | domain | 输出为成本核算表 + 高价原料清单 + 平替推荐方案 | 手动 |
| gate10_acceptance | 验收标准 | domain | 计算准确性≥0.75, 平替实用性≥0.75, 透明度≥0.75 | 手动 |

### 3.2 Rubric 评分表

| 维度 | 权重 | 评分项 | 评分项描述 |
|------|------|--------|-----------|
| 计算准确性 | 0.40 | 原料成本计算正确 | 每项原料用量×单价计算是否正确 |
| 计算准确性 | 0.40 | 汇总与分摊正确 | 总成本、单份成本、占比计算是否正确 |
| 平替实用性 | 0.35 | 风味接近 | 推荐的平替原料与原原料风味相似度是否高 |
| 平替实用性 | 0.35 | 实际可得 | 推荐的平替原料在普通市场是否容易买到 |
| 透明度 | 0.25 | 计算过程清晰 | 成本计算过程是否可追溯、可验证 |
| 透明度 | 0.25 | 替代理由充分 | 每个平替推荐是否附带了风味差异说明与使用建议 |

详情见 `ops/recipe-generator/rubric-020-cost-accounting-substitute.yaml`。

### 3.3 质量阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 综合质量分 Q | ≥ 0.85 | weighted_mean 聚合后的总分 |
| 单维度最低分 | ≥ 0.75 | 任意维度不得低于 0.75 |
| Gate 通过条件 | all_critical | 所有 critical gates 必须通过 |

## 4. 评测数据集

- 目录：`eval/recipe-generator/020-cost-accounting-substitute/`
- 最低用例数：3
- 覆盖场景：海鲜类高价配方、牛肉类高价配方、菌菇类高价配方
- 用例格式：每个 case 包含输入（配方参数表）、期望输出（成本核算表 + 高价标记 + 平替方案）

## 5. 验收

- 运行 `ops/recipe-generator/gates-020-cost-accounting-substitute.yaml` 全部 gate 通过。
- Rubric 评分 Q ≥ 0.85，各维度 ≥ 0.75。
- 评测数据集 3 条以上用例全部通过。
