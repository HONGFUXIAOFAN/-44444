---
name: "031-export-word-pdf-ssot"
version: "0.2.0"
description: "导出Word/PDF规则质量说明书——强制基于模板脚本生成文档，17项格式规范逐项自检通过后方可交付，禁止从零手写导出脚本"
applies_to: ["recipe-generator", "031-export-word-pdf"]
deliverable_vision: "基于 templates/export_recipe_template.py 标准模板，生成格式规范、打印友好、手机可读的标准配方方案文档。强制门禁：必须使用模板（禁止手写）+ 生成前逐项自检 + 生成后 self_check() + 脚本用后即删"
deliverable_type: "docx/pdf"
related_rule: "rules/031-export-word-pdf.md"
downstream_consumers: ["Administrator", "ssot-judge"]
configs:
  gates: "ops/recipe-generator/031-export-word-pdf-gates.yaml"
  rubric: "ops/recipe-generator/031-export-word-pdf-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/031-export-word-pdf"
tags: ["审查输出", "导出", "文档生成", "强制模板", "recipe-generator"]
---

# 031-导出Word/PDF SSOT（质量说明书）

---

## 一、产出物定义

### 使命
将030规则通过的完整配方方案转换格式化为标准美观的 Word/PDF 文档，支持打印张贴、员工培训和配方库存档，字体适配手机阅读。

### 核心价值
- **强制模板化**：所有导出必须基于 `templates/export_recipe_template.py` 的 `build_document()` 函数，禁止从零手写导出脚本
- **格式规范统一**：字体/配色/列宽/间距在模板中预置为常量，调用方不可覆盖
- **手机优先可读**：正文16pt、表格14pt、标题20-28pt，确保手机查看清晰
- **厨房可用**：速查卡可单独打印张贴，配色醒目（暗红表头+白底/浅粉交替）
- **干净交付**：无"AI生成"字样，无分页符，无生成工具元数据
- **自检验证**：生成后运行 `self_check()` 自动检测分页符/AI字样/表格宽度/页边距/字号违规

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 仅在030审查全部通过后触发
- 文件保存至用户桌面（~/Desktop/）
- 文件名格式：{菜品名}_{客户信息}_配方方案.docx
- 必须包含9个模块：封面/配方参数表/操作流程/保存方法/通俗原理/添加剂安全/成本核算/地域适配/速查卡

### Technique（技术要求）
- **强制模板使用**：调用 `templates/export_recipe_template.py` 的 `build_document(config)` 函数填充内容，禁止从零写 `from docx import Document` 后逐段手写
- **排版规范强制执行**：字体（封面28pt/一级24pt/二级20pt/正文16pt/表格14pt）、配色（暗红#C62828表头白字+白底浅粉#FFF0F0交替）、列宽智能分配（总和=20cm）、单元格内边距（上下20dxa左右40dxa）、表间紧凑规则——全部在模板中预置为不可覆盖常量
- **禁用分页符**：内容自然流排，A4页边距1.0-1.2cm
- **禁止元数据标注**：无"AI生成""自动生成""人工智能""生成工具""生成日期"
- **生成脚本（调用方）用后即删**：仅保留 `.docx` 产出文件和模板
- **强制自检**：生成后运行 `self_check()` 函数，结果展示给用户确认

### Art（价值判断与艺术性）
- 文档美学服务于实用性——不是学术论文，是厨房操作指南
- 配色服务于视觉层次——表头吸引注意，数据行便于快速扫读
- 速查卡设计为独立可撕页——单独打印张贴在厨房操作台
- 成本/时间等关键信息放在封面——用户第一眼就能获取核心商业参数

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
| gate10_trigger | 触发器：030审查全部通过 | 领域专项检查 | yes |
| gate10_input | 输入：030审查通过标志 + 完整配方方案 | 领域专项检查 | yes |
| gate10_behavior | 行为：基于模板脚本 build_document(config) 生成 + 禁止手写 + 格式检查 + 用后即删 | 领域专项检查 | yes |
| gate10_output | 输出：.docx文件（~/Desktop/）+ self_check()结果 + 交付确认 | 领域专项检查 | yes |
| gate10_acceptance | 验收：文档9模块完整 + 17项格式规范逐项通过 + self_check()通过 + 无元数据泄漏 + 模板使用证明 | 领域专项检查 | yes |
| gate11_template_enforcement | 强制模板使用：是否调用 build_document() 而非从零手写 | 领域专项检查 | yes |
| gate12_self_check | 强制自检：生成后是否运行 self_check() 并展示结果 | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 格式规范性 | 0.40 | 字体字号正确；配色方案统一（暗红表头+交替行）；无分页符；列宽智能分配；单元格内边距规则被执行 |
| 内容完整性 | 0.35 | 9个模块全部呈现；速查卡可独立打印；添加剂安全卡完整；成本核算表覆盖全部原料；封面信息齐全 |
| 可打印性 | 0.25 | A4边距合理（1.0-1.2cm）；手机字号可读；无"AI生成"等元数据；文件名规范；文件保存路径正确 |

### 3.3 质量阈值

```yaml
template_enforcement: "100%基于模板脚本导出，0次从零手写"
format_compliance: "字体字号/配色/列宽/边距 100%符合规范（17项格式自检清单逐项通过）"
module_completeness: "9个模块全部存在，无遗漏"
no_metadata_leak: "零'AI生成''自动生成''人工智能''生成工具''生成日期'字样"
no_page_breaks: "零分页符"
smart_column_width: "用量/成本/时间等窄列 1.0-2.5cm，说明/做法等内容列 >= 7cm，总和=20cm"
self_check_passed: "self_check() 零❌项，⚠️项已标注并向用户说明"
script_cleanup: "调用方脚本已删除，仅保留.docx和模板"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/031-export-word-pdf/`

### 数据集结构
```
031-export-word-pdf/
├── pass/          # 格式规范的导出文档
├── regression/    # 回归测试（格式一致性）
├── fail/          # 应被拦截的场景（含分页符/含元数据泄漏/字型过小）
└── edge/          # 边界场景（超长配方文档、特殊字符处理）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：完整导出/部分导出失败/格式违规 三种场景
- 覆盖：不同菜品类型的导出（汤羹/肉类/素食）

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：格式规范性 >= 0.85，内容完整性 >= 0.85，可打印性 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 检查输出文档的实际可读性和打印效果
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 基于模板脚本 `build_document()` 生成（非从零手写）
- [ ] `self_check()` 零❌项，结果已展示给用户
- [ ] 文档在手机上可清晰阅读
- [ ] 打印预览效果良好
- [ ] 速查卡作为独立页可撕下张贴
- [ ] 无任何AI生成痕迹（含生成日期）
- [ ] 配色视觉层次清晰（暗红表头+白底/浅粉交替）
- [ ] 调用方脚本已删除，仅保留 .docx + 模板

---

*SSOT v0.2.0 — 强制模板化，零手写容忍*
