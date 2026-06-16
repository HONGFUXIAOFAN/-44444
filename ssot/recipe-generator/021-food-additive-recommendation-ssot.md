---
name: "021-food-additive-recommendation-ssot"
version: "0.1.0"
description: "添加剂合理推荐规则质量说明书——在GB 2760范围内推荐食品添加剂/复合调味料，附带精确用量、使用方法、安全上限和禁忌人群"
applies_to: ["recipe-generator", "021-food-additive-recommendation"]
deliverable_vision: "为中小B端餐饮用户提供合法合规的食品添加剂推荐方案，每种添加剂附带完整安全说明（用量上限+使用方法+禁忌），在提升风味竞争力的同时确保安全红线不被触碰"
deliverable_type: "md"
related_rule: "rules/021-food-additive-recommendation.md"
downstream_consumers: ["Administrator", "ssot-judge", "030-user-review-confirmation"]
configs:
  gates: "ops/recipe-generator/021-food-additive-recommendation-gates.yaml"
  rubric: "ops/recipe-generator/021-food-additive-recommendation-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/021-food-additive-recommendation"
tags: ["增强补充", "添加剂", "食品安全", "GB2760", "recipe-generator"]
---

# 021-添加剂合理推荐 SSOT（质量说明书）

---

## 一、产出物定义

### 使命
在 GB 2760-2024 食品安全国家标准范围内，为中小B端餐饮用户的菜品配方推荐可适量使用、能显著提升风味的食品添加剂/复合调味料，附带精确用量、使用方法、安全上限和注意事项。

### 核心价值
- **安全合规**：所有推荐严格限定在 GB 2760-2024 范围内，杜绝违规推荐
- **精确可操作**：每种添加剂附带 g/kg 精确用量、具体使用方法（温度/时机/器具要求）
- **完整安全档案**：用量上限、禁忌人群、LD50/ADI 数据、法规依据齐全
- **用户自主选择**：所有推荐均为可选，不强制；提供"无需使用添加剂"的判断路径

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 添加剂推荐仅限 GB 2760-2024 已批准的食品添加剂品种
- 用量不得超过标准最大使用量（如乙基麦芽酚 <= 0.2g/kg）
- 必须区分"食品添加剂"与"天然调味料"的法规差异
- 所有用量以 g/kg 原料和本配方具体用量两种方式标注

### Technique（技术要求）
- 遵循"五维增味体系"逻辑：鲜味打底 -> 厚度支撑 -> 香味提魂 -> 圆润调和 -> 酸度平衡
- 按菜品类型（肉类卤制/汤羹火锅/素食豆制品/酱料调味品/腌制肉类）匹配黄金配比
- 部分添加剂需复配使用（如磷酸盐复配比 2:1:1，亚硝酸钠必须搭配 D-异抗坏血酸钠）
- 体现协同效应说明（如味精+I+G 鲜度提升 3~8 倍）

### Art（价值判断与艺术性）
- 优先判断传统工艺是否能满足需求（传统工艺 > 复合调味料 > 单一食品添加剂）
- 对用户可能的顾虑保持敏感，不强制推荐
- "不推荐"也是一种有价值的输出，给出替代方案路径
- 安全红线绝对不可触碰（亚硝酸盐精确称量条件、脱氢乙酸钠禁用条款等）

---

## 三、质量标准

### 3.1 Gates 门禁表

| Gate ID | 检查项 | 检查方式 | Critical |
|---------|--------|---------|----------|
| gate0_assets | SSOT/Gates/Rubric 三件套存在 | check_file_paths.py | yes |
| gate0_input_ssot_assets | 同上（alias） | check_file_paths.py | yes |
| gate1_ssot_frontmatter | YAML头完整性 | check_yaml_structure.py | no |
| gate2_gates_schema | Gates文件结构校验 | check_yaml_structure.py | yes |
| gate3_rubric_schema | Rubric文件结构校验 | check_yaml_structure.py | yes |
| gate4_path_validity | configs路径有效 | check_configs_paths.py | no |
| gate5_required_gates | 必选gate全部存在 | check_required_gates.py | yes |
| gate6_weight_sum | Rubric权重总和=1.0（容差0.05） | check_rubric_weight_sum.py | no |
| gate7_eval_dataset | 评测数据集 >= 3条 | check_eval_dataset.py | no |
| gate8_universal_gates_unchanged | 通用gate未被修改 | check_universal_gates.py | yes |
| gate10_trigger | 触发器：012确认后 + 与013并行 | 领域专项检查 | yes |
| gate10_input | 输入：012操作流程 + 010配方参数表 | 领域专项检查 | yes |
| gate10_behavior | 行为：GB 2760查询 + 五维增味推荐 + 安全说明 | 领域专项检查 | yes |
| gate10_output | 输出：添加剂安全卡（含精确用量+方法+上限+禁忌） | 领域专项检查 | yes |
| gate10_acceptance | 验收：用户逐项确认每种添加剂 | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 安全性 | 0.50 | 所有推荐在GB 2760范围内；用量不超过最大使用量；禁用品种不出现；亚硝酸盐有精确称量要求；安全红线完整 |
| 可操作性 | 0.25 | 用量精确（g/kg）；使用方法步进清晰；温度/时机/器具标注明确；协同效应有说明 |
| 完整性 | 0.25 | 安全档案完整（ADI/LD50/法规依据）；禁忌人群已标注；禁忌器具已标注；存储条件已说明；配方修正对照表完整（如涉及修改） |

### 3.3 质量阈值

```yaml
additive_compliance: "GB 2760-2024 100%合规"
dosage_accuracy: "所有用量精确到g/kg，标注占比百分比"
safety_completeness: "每种添加剂至少包含: 用量上限+使用方法+禁忌人群+存储条件"
user_confirmation: "每种添加剂逐项确认"
five_dimension_coverage: "五维增味体系完整覆盖（按菜品类型）"
traditional_first: "优先判断传统工艺可行性"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/021-food-additive-recommendation/`

### 数据集结构
```
021-food-additive-recommendation/
├── pass/          # 合规推荐场景（如红烧肉乙基麦芽酚推荐）
├── regression/    # 回归测试（禁用品种拦截）
├── fail/          # 应被拦截的场景（如超出用量上限、脱氢乙酸钠用于面包）
└── edge/          # 边界场景（传统工艺优先判断、不推荐场景）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：肉类卤制/汤羹火锅/素食豆制品/酱料/腌制肉类 五种菜品类型
- 覆盖：合规推荐/不推荐判断/安全红线拦截 三种场景

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：安全性 >= 0.85，可操作性 >= 0.75，完整性 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 确认安全红线和合规性
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 所有添加剂推荐在 GB 2760-2024 合法范围内
- [ ] 脱氢乙酸钠未用于面包/糕点场景
- [ ] 亚硝酸钠使用场景有精确称量条件要求
- [ ] 每种添加剂安全档案完整
- [ ] "无需使用添加剂"的判断路径有效

---

*SSOT v0.1.0 — 添加剂安全是红线，精确用量是底线*
