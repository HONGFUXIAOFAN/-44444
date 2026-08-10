---
name: "023-cross-module-consistency-check-ssot"
version: "0.1.0"
description: "跨模块逻辑一致性校验规则质量说明书——强制010配方参数/012操作流程/014通俗原理三向对比，确保配方方案前后自洽、无矛盾"
applies_to: ["recipe-generator", "023-cross-module-consistency-check"]
deliverable_vision: "对配方方案的全部内容模块进行三向逐实体对比校验，发现并消除所有前后矛盾，确保每个原料的处理方式三方一致、每个知识点的操作指引有明确落地"
deliverable_type: "md"
related_rule: "rules/023-cross-module-consistency-check.md"
downstream_consumers: ["Administrator", "ssot-judge", "024-recipe-holistic-validation", "022-practical-effectiveness-validation"]
configs:
  gates: "ops/recipe-generator/023-cross-module-consistency-check-gates.yaml"
  rubric: "ops/recipe-generator/023-cross-module-consistency-check-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/023-cross-module-consistency-check"
tags: ["一致性校验", "逻辑验证", "跨模块", "三向对比", "recipe-generator"]
---

# 023-跨模块逻辑一致性校验 SSOT（质量说明书）

---

## 一、产出物定义

### 使命
在全部内容模块（010配方参数/012操作流程/014通俗原理）生成完成后，强制执行三向一致性校验。逐原料、逐参数、逐知识点对比三份产出，发现并消除所有前后矛盾，确保配方方案不是各自独立模块的堆砌，而是一个前后一致、逻辑自洽的有机整体。

### 核心价值
- **零矛盾交付**：任何前后矛盾（如"全部打粉" vs "丁香整粒"）在023阶段被拦截，不得进入下游
- **三向全覆盖**：每个原料的处理方式在010/012/014三方中必须一致，不遗漏
- **说了就教了**：010列出的每个原料，012必须有操作说明，014必须有原理说明
- **可追溯**：每条对比引用原文位置，校验报告清晰可查

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 每次014完成后强制触发，不可跳过
- 三向对比矩阵覆盖010配方参数表中的全部原料
- 不一致项分级：✅通过 / ⚠️需补充 / ❌阻塞
- 存在❌时阻塞后续所有步骤，必须回退修改后重新全量校验
- 修改后必须重新执行023全量校验（不可只检查修改项）

### Technique（技术要求）
- 逐实体建立对比矩阵：010列 × 012列 × 014列
- 专项校验：数量一致性/顺序一致性/温度时间一致性/添加剂一致性/"说了就教了"原则
- 每条对比必须引用三份产出中的原文位置
- 校验报告必须包含"修改建议"，不能只指出问题不给出方案
- 添加剂用量在010/012/021中三方交叉校验

### Art（价值判断与艺术性）
- 校验报告不是找茬清单——是帮助用户理解"为什么会矛盾、怎么改"的沟通工具
- 坦率诚实的错误承认："010写打粉+012写整粒=矛盾，应以012实际可操作为准修正010"
- 可操作：每条修改建议指向具体规则文件和段落
- 建立信任：用户看到023报告后可以确信"这份方案不会让我操作时犯难"

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
| gate10_trigger | 触发器：014完成后强制触发 | 领域专项检查 | yes |
| gate10_input | 输入：010+012+014三份完整产出 | 领域专项检查 | yes |
| gate10_behavior | 行为：逐实体三向对比 + 专项逻辑校验 + 校验报告 | 领域专项检查 | yes |
| gate10_output | 输出：一致性校验报告（对比矩阵+问题汇总+校验结论+修改建议） | 领域专项检查 | yes |
| gate10_acceptance | 验收：全项✅通过方可进入024 | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 覆盖完整性 | 0.35 | 010中所有原料均已纳入对比矩阵；专项校验5项全部执行；添加剂三方交叉校验完成 |
| 对比准确性 | 0.35 | 每条对比引用原文位置；不一致判定有据；分级（✅/⚠️/❌）准确无遗漏 |
| 改进可操作性 | 0.30 | 每个❌/⚠️项有明确修改建议；回退路径清晰；修改指向具体文件和段落 |

### 3.3 质量阈值

```yaml
coverage_completeness: "010中100%原料纳入对比矩阵，5项专项校验全部执行"
contradiction_zero: "交付时零❌矛盾项（全部解决后方可进入024）"
traceability: "每条对比引用原文位置，每条修改建议指向具体文件"
recheck_enforcement: "修改后重新全量校验，不可只检查修改项"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/023-cross-module-consistency-check/`

### 数据集结构
```
023-cross-module-consistency-check/
├── pass/          # 三向全部一致的配方方案
├── regression/    # 回归测试（曾出现矛盾后修复的场景）
├── fail/          # 应被拦截的场景（存在❌矛盾强行通过）
└── edge/          # 边界场景（大量香料/复杂添加剂/多阶段操作的配方）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：香料处理矛盾/温度参数矛盾/添加剂用量矛盾/"说了没教"四类典型不一致

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：覆盖完整性 >= 0.85，对比准确性 >= 0.85，改进可操作性 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 检查校验报告的完整性和矛盾判定的准确性
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 010中100%原料纳入对比矩阵
- [ ] 所有矛盾项有原文引用支撑
- [ ] 零❌项进入下游
- [ ] 每个❌/⚠️项有可执行的修改建议
- [ ] 修改后已全量重新校验

---

*SSOT v0.1.0 — 零矛盾是底线，不是目标*
