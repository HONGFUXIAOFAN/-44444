---
name: "科学原理通俗化注入"
version: "0.1.0"
description: "在配方关键步骤中注入食品科学原理的通俗化解释，用类比与日常语言让初中文化用户也能理解"
applies_to:
  - "recipe-generator"
deliverable_vision: "为配方中的关键操作步骤匹配对应的科学原理，并以通俗类比方式解释，让用户知其然更知其所以然"
deliverable_type: "规则文件-提示词"
related_rule: "rules/014-scientific-principle-injection.md"
downstream_consumers:
  - "Administrator"
  - "ssot-judge"
configs:
  gate: "ops/recipe-generator/gates-014-scientific-principle-injection.yaml"
  rubric: "ops/recipe-generator/rubric-014-scientific-principle-injection.yaml"
tags:
  - "科学原理"
  - "美拉德"
  - "蛋白质变性"
  - "乳化"
  - "通俗化"
  - "类比"
  - "初中文化"
  - "recipe-generator"
  - "rule-014"
---

# 科学原理通俗化注入 (Scientific Principle Injection) — SSOT

## 1. 产出物定义

### 使命
在配方操作流程的关键步骤中，识别背后涉及的食品科学原理，并用类比、日常现象等通俗方式解释，使初中文化程度的用户也能理解「为什么这样做」，从而提升烹饪成功率与科学素养。

### 核心价值
- **通俗易懂**：将专业术语（美拉德反应、蛋白质变性、乳化等）转化为日常类比，确保初中文化程度用户理解。
- **科学准确**：通俗化表达不扭曲科学本质，核心原理描述正确。
- **合理覆盖**：在关键步骤处精准注入原理，不过度解释避免信息过载。
- **赋能用户**：让用户理解原理后能举一反三，自主调整操作。

## 2. 思考与规划（CTA框架）

### Commonness（共性层）
- 覆盖常见烹饪科学原理：美拉德反应、焦糖化、蛋白质变性（热变性/酸变性）、淀粉糊化、乳化、发酵、酶促褐变、渗透作用等。
- 每个原理对应一个标准通俗化模板：「专业术语→日常类比→为什么这一步需要它→如果做错了会怎样」。
- 定位方式：扫描配方步骤中的关键词（如煎、煮、打蛋、和面、腌渍等），匹配对应原理。

### Technique（技术层）
- 建立「操作关键词→科学原理」映射表。
- 对每条匹配到的原理，从通俗化语料库中选取对应的类比表达。
- 控制每条解释的字数（建议30-80字），保持简洁有力。

### Art（艺术层）
- 类比素材来源于日常生活：太阳晒黑（美拉德）、鸡蛋从液态变固态（蛋白质变性）、洗洁精去油（乳化）等。
- 解释口吻亲切，如同朋友在旁讲解，避免教科书风格。
- 对初中文化程度用户使用限制词汇表进行校验，确保无超纲术语未被解释。

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
| gate7_eval_dataset | 评测数据集存在 | universal | `eval/recipe-generator/014-scientific-principle-injection/` 目录存在且≥3条用例 | `templates/gate-scripts/check_eval_dataset.py` |
| gate8_universal_gates_unchanged | 通用Gate未被篡改 | universal | universal gates 的定义与基线一致 | `templates/gate-scripts/check_universal_gates.py` |
| gate10_trigger | 触发器规则 | domain | 触发器明确引用 WHEN + 上游规则 013 | 手动 |
| gate10_input | 输入字段 | domain | 输入包含配方操作步骤文本 | 手动 |
| gate10_behavior | 行为规则 | domain | 识别关键步骤中的科学原理、用通俗类比改写、原理描述准确、语言不超过初中文化水平 | 手动 |
| gate10_output | 输出模板 | domain | 输出为含科学原理解释的增强版配方 | 手动 |
| gate10_acceptance | 验收标准 | domain | 通俗度≥0.75, 准确性≥0.75, 覆盖度≥0.75 | 手动 |

### 3.2 Rubric 评分表

| 维度 | 权重 | 评分项 | 评分项描述 |
|------|------|--------|-----------|
| 通俗度 | 0.45 | 类比恰当 | 使用的日常类比是否贴切、易于理解 |
| 通俗度 | 0.45 | 语言难度可控 | 是否避免超纲术语，初中文化用户能否读懂 |
| 准确性 | 0.30 | 原理正确 | 科学原理描述是否在通俗化过程中保持准确、未歪曲 |
| 准确性 | 0.30 | 关键步骤匹配 | 原理注入是否发生在确实涉及该原理的步骤中（不张冠李戴） |
| 覆盖度 | 0.25 | 关键步骤覆盖 | 配方中涉及科学原理的关键步骤是否均有解释 |
| 覆盖度 | 0.25 | 恰到好处 | 是否在合理位置解释，不过度或遗漏 |

详情见 `ops/recipe-generator/rubric-014-scientific-principle-injection.yaml`。

### 3.3 质量阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 综合质量分 Q | ≥ 0.85 | weighted_mean 聚合后的总分 |
| 单维度最低分 | ≥ 0.75 | 任意维度不得低于 0.75 |
| Gate 通过条件 | all_critical | 所有 critical gates 必须通过 |

## 4. 评测数据集

- 目录：`eval/recipe-generator/014-scientific-principle-injection/`
- 最低用例数：3
- 覆盖场景：煎炒类（美拉德反应）、煮炖类（蛋白质变性、胶原蛋白转化）、烘焙类（酵母发酵、淀粉糊化）
- 用例格式：每个 case 包含输入（配方步骤文本）、期望输出（标注了科学原理与通俗解释的步骤）

## 5. 验收

- 运行 `ops/recipe-generator/gates-014-scientific-principle-injection.yaml` 全部 gate 通过。
- Rubric 评分 Q ≥ 0.85，各维度 ≥ 0.75。
- 评测数据集 3 条以上用例全部通过。
