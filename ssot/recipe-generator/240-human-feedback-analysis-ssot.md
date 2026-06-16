---
name: "240-human-feedback-analysis-ssot"
version: "0.1.0"
description: "人类反馈RCA根因分析规则质量说明书——基于RCA框架分析用户反馈，识别配方方案问题根因，驱动方案迭代改进"
applies_to: ["recipe-generator", "240-human-feedback-analysis"]
deliverable_vision: "对每条用户反馈执行结构化根因分析（5-Whys），区分症状与根因，产出可执行的改进方案，确保迭代有据可依、过程可追溯"
deliverable_type: "md"
related_rule: "rules/240-human-feedback-analysis.md"
downstream_consumers: ["Administrator", "ssot-judge", "030-user-review-confirmation", "031-export-word-pdf"]
configs:
  gates: "ops/recipe-generator/240-human-feedback-analysis-gates.yaml"
  rubric: "ops/recipe-generator/240-human-feedback-analysis-rubric.yaml"
  eval_base_dir: "eval/recipe-generator/240-human-feedback-analysis"
tags: ["反馈分析", "RCA", "根因分析", "迭代改进", "recipe-generator"]
---

# 240-人类反馈RCA根因分析 SSOT（质量说明书）

---

## 一、产出物定义

### 使命
对用户在审查确认环节或交付后提出的反馈意见，进行结构化根因分析（RCA+5-Whys），区分症状与根因，产出可执行的改进方案，确保每次迭代都有据可依，过程可追溯。

### 核心价值
- **不猜测**：所有结论基于用户反馈原文和方案证据，不凭空推测
- **深挖根因**：不满足于"改这里"，追问"为什么这里会出问题"直到找到底层原因
- **可追溯**：每条反馈独立分析，生成完整分析报告（问题定义->证据收集->根因识别->改进建议）
- **驱动迭代**：分析结果可触发规则文件修改、方案回退修改、规则体系优化

---

## 二、思考与规划 CTA 框架

### Commonness（基础共性要求）
- 每次反馈必须先经过5步完整流程：问题定义 -> 证据收集 -> 根因识别 -> 改进建议 -> 执行改进
- 所有结论基于证据（用户反馈原文+方案原文），不允许主观推测
- 每条反馈独立分析，逐个处理
- 修改后必须告知用户改了什么、为什么这样改

### Technique（技术要求）
- 根因分析区分症状（用户看到的）与根因（底层原因）
- 应用5-Whys方法逐层追问
- 根因分类：规则设计缺陷/规则执行偏差/用户需求未对齐/外部信息不足
- 改进建议包含：改进方向/涉及文件/改进步骤/验收标准
- 改进前向用户汇报初步识别，等待确认

### Art（价值判断与艺术性）
- 分析报告不是技术文档——是向用户解释"为什么出了问题"的沟通工具
- 坦率承担的改进态度："这个参数生成偏差是因为XX规则对XX场景没有覆盖到"
- 改进建议可操作可量化——不是说"改进配方生成"，而是"在010规则第3步增加XX验证逻辑"
- 建立信任闭环——让用户看到每次反馈都被认真对待、有据可查

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
| gate10_trigger | 触发器：用户提出反馈意见 | 领域专项检查 | yes |
| gate10_input | 输入：反馈原文 + 相关产出物 + 涉及规则文件 | 领域专项检查 | yes |
| gate10_behavior | 行为：RCA分析（5-Whys）+ 根因分类 + 改进方案 | 领域专项检查 | yes |
| gate10_output | 输出：分析报告（问题定义+证据+根因+建议）+ 改进执行记录 | 领域专项检查 | yes |
| gate10_acceptance | 验收：根因分析有据可查 + 改进建议可执行 + 用户确认 | 领域专项检查 | yes |

### 3.2 Rubric 评分表

| 维度 | 权重 | 检查要点 |
|------|:----:|---------|
| 分析深度 | 0.40 | 5-Whys逐层递进有理有据；症状与根因区分清晰；根因分类准确；不满足于表面修改 |
| 改进可行性 | 0.35 | 改进建议具体可执行；涉及文件明确；改进步骤分步清晰；验收标准可量化 |
| 反馈闭环 | 0.25 | 每条反馈独立分析；用户确认后方执行修改；修改后告知原因；分析报告完整可追溯 |

### 3.3 质量阈值

```yaml
root_cause_depth: "至少3层Why追问，不允许止于表层症状"
evidence_quality: "每条结论至少引用1处原文证据"
improvement_actionable: "每个改进建议包含: 涉及文件+具体步骤+验收标准"
user_confirmation: "初步识别和改后均等待用户确认"
independent_analysis: "多条反馈逐条独立分析，不可合并处理"
```

---

## 四、评测数据集

### 数据集路径
`eval/recipe-generator/240-human-feedback-analysis/`

### 数据集结构
```
240-human-feedback-analysis/
├── pass/          # 成功完成RCA分析并驱动有效改进的场景
├── regression/    # 回归测试（同类型问题的二次反馈）
├── fail/          # 应被拦截的场景（跳过分析直接修改、主观推测、未引用证据）
└── edge/          # 边界场景（多条反馈同时提交、反馈模糊难以定位）
```

### 最低要求
- 每个目录至少 3 个测试用例
- 覆盖：配方数据错误/流程缺失/内容遗漏/结构不当/格式问题/措辞不当 六种问题分类
- 覆盖：规则设计缺陷/规则执行偏差/用户需求未对齐/外部信息不足 四种根因分类

---

## 五、验收

### 验收流程
1. **自动检查**：执行 Gates 门禁，所有 critical gates 必须通过
2. **Rubric 评分**：分析深度 >= 0.85，改进可行性 >= 0.75，反馈闭环 >= 0.75，加权总分 >= 0.85
3. **人工审核**：Administrator 检查RCA分析的逻辑严谨性
4. **整改循环**：不通过项最多 3 轮整改

### 关键验收项
- [ ] 每条反馈经过完整的5步分析流程
- [ ] 5-Whys至少3层追问
- [ ] 根因分类准确，不张冠李戴
- [ ] 改进建议具体到文件+步骤+标准
- [ ] 无凭空推测——所有结论有原文引用支撑

---

*SSOT v0.1.0 — 不猜测，找根因，可追溯*
