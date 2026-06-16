---
name: "地域口味适配"
version: "0.1.0"
description: "根据用户所在地区自动调整配方的咸度、辣度、甜度、麻度、油量等口味参数，实现个性化地域适配"
applies_to:
  - "recipe-generator"
deliverable_vision: "接收用户地区信息与原始配方，输出一份口味参数调整后的适配版配方，附带调整原因说明"
deliverable_type: "规则文件-提示词"
related_rule: "rules/013-regional-taste-adaptation.md"
downstream_consumers:
  - "Administrator"
  - "ssot-judge"
configs:
  gate: "ops/recipe-generator/gates-013-regional-taste-adaptation.yaml"
  rubric: "ops/recipe-generator/rubric-013-regional-taste-adaptation.yaml"
tags:
  - "地域"
  - "口味"
  - "咸度"
  - "辣度"
  - "甜度"
  - "麻度"
  - "油量"
  - "适配"
  - "recipe-generator"
  - "rule-013"
---

# 地域口味适配 (Regional Taste Adaptation) — SSOT

## 1. 产出物定义

### 使命
基于中国（及海外）不同地区的口味偏好特征，智能调整配方的咸、辣、甜、麻、油等核心口味参数，使同一道菜在不同地域的呈现更符合当地饮食习惯。

### 核心价值
- **精准适配**：根据地区口味数据库，对各项参数做有理有据的定量/定性调整。
- **覆盖全面**：涵盖国内主要饮食区域（华北、东北、华东、华南、华中、西南、西北）及海外主要华人聚集地的口味特征。
- **透明可解释**：每次调整均附带原因说明，让用户理解「为什么这样改」。
- **保留本味**：在适配的同时不过度扭曲原配方的基础风味结构。

## 2. 思考与规划（CTA框架）

### Commonness（共性层）
- 基于中国烹饪协会及公开饮食文化研究建立的地区口味偏好知识库。
- 核心调整参数：咸度（盐/酱油）、辣度（辣椒/辣椒油）、甜度（糖）、麻度（花椒/麻椒）、油量（烹饪用油）。
- 调整方式统一为「参数偏向说明 + 调整幅度 + 原因」。

### Technique（技术层）
- 接收原始配方的口味参数向量 [咸, 辣, 甜, 麻, 油]。
- 根据目标地区的口味偏好向量计算差值，生成调整建议。
- 调整幅度控制在合理范围内（单参数变化不超过±50%），防止颠覆性改动。

### Art（艺术层）
- 不仅做数值上的调整，还需给出具体的调料替换建议（如「将生抽减半，加少许老抽上色」）。
- 对于跨地域差异极大的维度，给出「可选」「强烈建议」等分级建议，给用户选择空间。
- 适配说明语言通俗，让用户感到「贴心」而非「教条」。

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
| gate7_eval_dataset | 评测数据集存在 | universal | `eval/recipe-generator/013-regional-taste-adaptation/` 目录存在且≥3条用例 | `templates/gate-scripts/check_eval_dataset.py` |
| gate8_universal_gates_unchanged | 通用Gate未被篡改 | universal | universal gates 的定义与基线一致 | `templates/gate-scripts/check_universal_gates.py` |
| gate10_trigger | 触发器规则 | domain | 触发器明确引用 WHEN + 上游规则 012 | 手动 |
| gate10_input | 输入字段 | domain | 输入包含用户地区参数 + 原始配方 | 手动 |
| gate10_behavior | 行为规则 | domain | 依次对咸/辣/甜/麻/油参数做调整，调整有地域分类依据 | 手动 |
| gate10_output | 输出模板 | domain | 输出包含调整后配方 + 逐项调整原因说明 | 手动 |
| gate10_acceptance | 验收标准 | domain | 适配准确性≥0.75, 覆盖度≥0.75, 可解释性≥0.75 | 手动 |

### 3.2 Rubric 评分表

| 维度 | 权重 | 评分项 | 评分项描述 |
|------|------|--------|-----------|
| 适配准确性 | 0.45 | 参数调整合理 | 咸/辣/甜/麻/油各项调整是否符合目标地区口味特征 |
| 适配准确性 | 0.45 | 幅度不极端 | 单参数调整幅度是否在合理范围内，未过度扭曲原配方 |
| 覆盖度 | 0.30 | 地区覆盖 | 是否支持国内主要饮食区域及海外主要华人聚集地 |
| 覆盖度 | 0.30 | 参数覆盖 | 5个口味参数（咸/辣/甜/麻/油）是否均被考虑 |
| 可解释性 | 0.25 | 原因清晰 | 每项调整是否附带了清晰易懂的原因说明 |
| 可解释性 | 0.25 | 建议分级 | 是否对调整建议做了分级（必须/建议/可选） |

详情见 `ops/recipe-generator/rubric-013-regional-taste-adaptation.yaml`。

### 3.3 质量阈值

| 指标 | 阈值 | 说明 |
|------|------|------|
| 综合质量分 Q | ≥ 0.85 | weighted_mean 聚合后的总分 |
| 单维度最低分 | ≥ 0.75 | 任意维度不得低于 0.75 |
| Gate 通过条件 | all_critical | 所有 critical gates 必须通过 |

## 4. 评测数据集

- 目录：`eval/recipe-generator/013-regional-taste-adaptation/`
- 最低用例数：3
- 覆盖场景：北方→南方适配、沿海→内陆适配、清淡地区→重口味地区适配
- 用例格式：每个 case 包含输入（原始配方 + 目标地区）、期望输出（参数调整表 + 原因）

## 5. 验收

- 运行 `ops/recipe-generator/gates-013-regional-taste-adaptation.yaml` 全部 gate 通过。
- Rubric 评分 Q ≥ 0.85，各维度 ≥ 0.75。
- 评测数据集 3 条以上用例全部通过。
