---
name: "030-user-review-confirmation-ssot"
version: "0.1.0"
description: "用户审查确认流程规则质量说明书——定义7项系统化审查检查清单，确保配方方案交付前无遗漏、无错误"
applies_to: ["recipe-generator", "030-user-review-confirmation"]
deliverable_vision: "所有前置规则产出物汇总为完整配方方案，提供7项结构化的逐项审查清单，用户逐条确认后触发导出流程"
deliverable_type: "md"
related_rule: "rules/030-user-review-confirmation.md"
downstream_consumers: ["Administrator", "ssot-judge", "031-export-word-pdf"]
configs:
  gates: "ops/recipe-generator/030-user-review-confirmation-gates.yaml"
  rubric: "ops/recipe-generator/030-user-review-confirmation-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/030-user-review-confirmation"
tags: ["审查输出", "用户审查", "recipe-generator"]
---

# 030-用户审查确认流程 SSOT（质量说明书）

---

## 一、产出物定义

### 使命
在所有规则执行完毕后，将完整配方方案汇总呈现给用户，提供系统化的7项审查检查清单，确保用户逐项确认后才能导出交付。每一审查项必须得到用户明确回复。

### 核心价值
- **零遗漏保障**：7项审查覆盖配方完整性、科学性、操作可行性、成本合理性、地域适配、添加剂安全性、整体评价
- **强制确认**：禁止跳过任何审查项，禁止默认通过，用户必须逐条回复
- **可追溯回退**：不通过项明确记录修改需求和回退路径，回退修改后重新审查受影响项
- **交付守门人**：全部7项通过是进入031导出的必要条件

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 7项审查清单必须完整呈现，无遗漏
- 每项审查包含子项检查点，覆盖该维度核心关注
- 审查顺序固定：配方完整性 -> 科学性 -> 操作可行性 -> 成本合理性 -> 地域适配 -> 添加剂安全性 -> 整体评价
- 回退修改后必须重新执行受影响的下游规则

### Technique（技术要求）
- 组装完整配方方案时引用所有前置规则产出物（010配方参数、011验证结论、020成本、012操作流程、013地域适配、014通俗原理、021添加剂）
- 审查结果处理明确分三档：全部通过/某项不通过/多项不通过
- 回退路径精准定位到具体规则ID
- 审查记录完整保留

### Art（价值判断与艺术性）
- 审查语言友好但不可省略——引导用户认真对待每一项而非走过场
- 适配用户知识水平——每个检查点用通俗语言描述（如"操作步骤是否清晰可执行"而非"操作流程架构是否符合标准"）
- 整改建议具体可执行——不说"需要改进"，说"配方参数表中XX用量需调整为YY，回退到010规则重新生成"
- 通过后的庆祝/鼓励语言体现温度

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
| gate10_trigger | 触发器：002总控完成全部生成 | 领域专项检查 | yes |
| gate10_input | 输入：所有前置规则产出物完整可用 | 领域专项检查 | yes |
| gate10_behavior | 行为：7项审查清单 + 逐项确认 + 回退路径 | 领域专项检查 | yes |
| gate10_output | 输出：审查结果（通过/不通过）+ 整改建议 | 领域专项检查 | yes |
| gate10_acceptance | 验收：全部7项用户明确确认通过 | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 审查完整度 | 0.40 | 7项审查全部呈现无遗漏；每项包含子检查点；组装方案引用所有前置产出物；审查顺序正确 |
| 用户友好度 | 0.35 | 检查项语言通俗易懂；整改建议具体可执行；通过/不通过反馈清晰；回退路径可操作 |
| 整改有效性 | 0.25 | 不通过项有明确回退规则ID；整改后重新审查受影响项；最多3轮整改循环；审查记录完整保留 |

### 3.3 质量阈值

```yaml
review_completeness: "7项审查100%覆盖，每项至少2个子检查点"
user_confirmation: "每项必须用户明确回复，禁止默认通过"
traceability: "每个不通过项记录: 问题描述+回退规则ID+重新审查范围"
max_revision_rounds: 3
delivery_gate: "全部7项通过才能进入031导出"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/030-user-review-confirmation/`

### 数据集结构
```
030-user-review-confirmation/
├── pass/          # 全部7项通过的场景
├── regression/    # 回归测试（某项不通过回退后重新审查）
├── fail/          # 应被拦截的场景（跳过审查、默认通过、未逐项确认）
└── edge/          # 边界场景（多项不通过、3轮整改后仍未通过）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：全部通过/单项不通过/多项不通过/3轮后仍未通过 四种结果
- 覆盖：回退后重新审查受影响项的逻辑

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：审查完整度 >= 0.85，用户友好度 >= 0.75，整改有效性 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 审查确认流程的逻辑完整性
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 7项审查清单全部呈现，无遗漏
- [ ] 每项审查有明确的用户确认机制
- [ ] 回退路径与规则ID映射正确
- [ ] 整改后重新审查受影响项的逻辑完整
- [ ] 审查记录格式规范

---

*SSOT v0.1.0 — 审查是交付的最后一道防线，不可跳过*
