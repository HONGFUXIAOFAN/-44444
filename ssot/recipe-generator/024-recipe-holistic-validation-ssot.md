---
name: "024-recipe-holistic-validation-ssot"
version: "0.1.0"
description: "配方整体科学协同性验证规则质量说明书——五维度整体验证+多源交叉验证，确保配方是科学协同的有机整体而非各模块的机械拼凑"
applies_to: ["recipe-generator", "024-recipe-holistic-validation"]
deliverable_vision: "对配方整体进行香料配伍/参数互恰/风味逻辑链/操作时序/体系稳定性五维度协同验证，配合≥4个独立来源交叉验证，产出整体评级（A/B/C/D），确保配方具有内在科学逻辑链"
deliverable_type: "md"
related_rule: "rules/024-recipe-holistic-validation.md"
downstream_consumers: ["Administrator", "ssot-judge", "022-practical-effectiveness-validation", "030-user-review-confirmation"]
configs:
  gates: "ops/recipe-generator/024-recipe-holistic-validation-gates.yaml"
  rubric: "ops/recipe-generator/024-recipe-holistic-validation-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/024-recipe-holistic-validation"
tags: ["整体验证", "科学协同", "交叉验证", "香料配伍", "风味逻辑", "recipe-generator"]
---

# 024-配方整体科学协同性验证 SSOT（质量说明书）

---

## 一、产出物定义

### 使命
在跨模块逻辑一致性（023）通过后，对配方作为有机整体进行系统性协同验证。不同于011（验证单个参数来源）和022（验证实用性），024回答"这些参数放在一起是否构成一个科学合理、协同运作的整体"。

### 核心价值
- **不是拼凑是配方**：通过五维度验证确保配方有内在逻辑链，而非各模块的机械堆砌
- **香料配伍有据**：君臣佐使关系清晰，药性不冲突，处理方式不自相矛盾
- **风味逻辑完整**：前味→中味→后味→回味→香气五层次检查，缺失诚实标注
- **多源交叉验证**：≥4个独立来源（2学术+1商业+1实操），从不同角度验证整体合理性

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 023全部✅通过后方可触发
- 五维度每个维度必须评分（✅/⚠️/❌）+给出依据+标注风险等级
- 多源交叉验证 ≥ 4个来源，不足时必须联网补充搜索
- 整体评级 C 或 D 时必须回退修改，评级 B 时标注风险后可进入022
- 每个结论必须有联网搜索结果支撑（非主观判断）

### Technique（技术要求）
- 香料配伍：君臣佐使角色分配 + 药性温凉冲突检查 + 处理方式协同检查 + 剂量比例校验
- 参数互恰：逐对检查关键参数的潜在冲突（≥5对），联网验证相互作用
- 风味逻辑链：构建五层次风味轮，逐层检查承担者，缺失时给出补充建议
- 操作时序：绘制操作时序图，验证关键等待/冷却/醒发时间是否充分
- 体系稳定性：防腐体系四重保障检查 + 油脂抗氧化体系完整性 + 乳化/悬浮稳定性
- 多源验证：2学术标准+1商业配方参考+1实操经验

### Art（价值判断与艺术性）
- 验证报告不是学术审稿——是向用户证明"这个配方整体上站得住脚"
- 诚实标注局限性："本配方后味层次偏弱，因为XX原因，可通过增加XX改善"
- 每个维度的"为什么"比"是什么"更重要：不只说"香料配伍通过"，要说"因为丁香为佐去腥+八角为臣增香，比例在经典范围内"
- 建立信心：用户看到024报告后可以确信"这个配方有科学骨架，不是东拼西凑"

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
| gate10_trigger | 触发器：023全部✅后强制触发 | 领域专项检查 | yes |
| gate10_input | 输入：010+012+013+021+023报告 | 领域专项检查 | yes |
| gate10_behavior | 行为：五维度协同验证 + 风味轮构建 + 参数互恰检查 + 多源交叉验证 | 领域专项检查 | yes |
| gate10_output | 输出：整体协同验证报告（五维度评分+风味轮+参数互恰+多源验证+整体评级） | 领域专项检查 | yes |
| gate10_acceptance | 验收：五维度全部≥⚠️（无❌）+ 多源验证≥4个 + 整体评级A或B | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 验证深度 | 0.40 | 五维度每个维度有评分+依据+风险等级；香料君臣佐使分析完整；参数互恰≥5对；风味轮五层次覆盖；多源验证≥4个 |
| 科学严谨性 | 0.35 | 每个结论有联网搜索结果支撑；香料配伍符合经典理论；参数冲突分析有食品科学依据；多源验证来源可查证 |
| 诚实透明度 | 0.25 | 风味缺失诚实标注；体系局限性明确说明；评级客观无虚高；风险项不隐瞒 |

### 3.3 质量阈值

```yaml
five_dimension_coverage: "五维度全部评分，无跳过维度"
spice_analysis_depth: "君臣佐使角色分配完整 + 药性冲突检查 + 处理方式协同"
cross_validation_sources: "≥4个独立来源（2学术+1商业+1实操）"
holistic_rating: "A或B方可进入022，C或D必须回退"
evidence_quality: "每条结论至少1处联网搜索结果引用"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/024-recipe-holistic-validation/`

### 数据集结构
```
024-recipe-holistic-validation/
├── pass/          # 五维度全部通过、整体评级A/B的配方
├── regression/    # 回归测试（曾因协同问题被驳回后修复的场景）
├── fail/          # 应被拦截的场景（香料冲突/参数互掐/风味空洞的拼凑配方）
└── edge/          # 边界场景（极简配料/超长配方/跨菜系融合配方）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：香料配伍冲突/参数互恰冲突/风味逻辑链缺失/操作时序不合理/体系稳定性不足 五种典型问题

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：验证深度 >= 0.85，科学严谨性 >= 0.85，诚实透明度 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 检查验证报告的深度和结论合理性
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 五维度全部评分（无跳过）
- [ ] 香料君臣佐使分析引用了经典配伍理论来源
- [ ] 风味轮五层次检查，缺失诚实标注
- [ ] 多源交叉验证 ≥ 4 个可查证来源
- [ ] 整体评级客观，C/D 时已阻止进入022
- [ ] 所有结论有联网搜索证据支撑

---

*SSOT v0.1.0 — 配方是有机整体，不是零件清单*
