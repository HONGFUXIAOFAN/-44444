---
name: gate-scripts|README.md
version: 2.2.0
description: Gate检查脚本库 - 统一检查器使用指南
applies_to: ["ssot-judge", "Administrator", "质量评审"]
created: 2025-10-16T00:00:00+0800
modified: 2025-10-27T09:27:00+0800
changelog:
  - "v2.2.0: 精简优化，从519行减少到约300行，提升可读性"
  - "v2.1.0: 基于5W1H框架重写，补充Why/When/Who章节"
  - "v2.0.1: 添加统一检查器和插件扩展功能"
tags: [gate-checker, unified-checker, performance, ssot-judge]
---

# Gate检查脚本库 - 统一检查器使用指南

---

## 为什么需要（Why）

传统的Gate检查方式存在**性能瓶颈**（9-14次进程启动、重复加载YAML）、**扩展困难**（每个Gate需要独立脚本）、**集成复杂**（逐个调用、错误处理分散）。

**unified_gate_checker.py** 通过批量执行、插件架构、智能路由解决这些问题，实现**67%性能提升**（0.313s → 0.103s）。

| 维度 | 传统方式 | unified_gate_checker | 提升 |
|------|---------|---------------------|------|
| **性能** | 0.313s（9个Gate） | 0.103s（9个Gate） | **67%** ↑ |
| **进程启动** | 9-14次 | 1次 | **91%** ↓ |
| **扩展性** | 创建新脚本 | 添加插件 | 更灵活 |

---

## 何时使用（When）

**推荐使用**：
- ssot-judge执行批量Gate检查（主要场景）
- 需要高性能（<0.2s响应时间）
- 需要扩展自定义Gate类型

**前置条件**：
- Python 3.7+ 环境
- unified_gate_checker.py 文件存在
- 输入文件格式正确（gates.yaml/deliverable/ssot.md/rubric.yaml）

---

## 谁来使用（Who）

| 角色 | 用途 | 期望 |
|------|------|------|
| **ssot-judge** | 批量执行Gate检查 | 高性能、自动降级 |
| **Administrator** | 测试Gate逻辑、扩展插件 | 易扩展、易调试 |

**使用前提**：
- ssot-judge集成者需理解能力查询和智能路由
- 插件开发者需了解插件接口规范

---

## 如何使用（How）

### 使用前的思考

1. **需要检查哪些Gate**？（从gates.yaml提取Gate ID列表）
2. **unified_gate_checker支持吗**？（执行 `--list-capabilities` 查询）
3. **采用哪种策略**？（100%覆盖→批量，75-99%→混合，<75%→降级）

---

### 快速开始

**基础用法**：
```bash
python3 Doc/templates/gate-scripts/unified_gate_checker.py \
  --gates-yaml <gates.yaml路径> \
  --deliverable <产出物路径> \
  --ssot <SSOT路径> \
  --rubric-yaml <rubric.yaml路径>
```

**能力查询**：
```bash
python3 Doc/templates/gate-scripts/unified_gate_checker.py --list-capabilities
```

输出：`{"all_gates": [...], "plugins_loaded": 2}`

---

### ssot-judge集成策略

**核心思路**：能力查询 → 智能决策 → 执行策略

```python
# 1. 查询能力
result = subprocess.run([...], '--list-capabilities')
capabilities = json.loads(filter_json_line(result.stdout))
supported_gates = capabilities['all_gates']

# 2. 计算覆盖率
required_gates = [gate['id'] for gate in yaml.load(gates_yaml_path)['gates']]
coverage = len([g for g in required_gates if g in supported_gates]) / len(required_gates)

# 3. 智能决策
if coverage == 1.0:
    strategy = "unified_only"    # 批量执行（67%提速）
elif coverage >= 0.75:
    strategy = "mixed"           # 混合执行（51%提速）
else:
    strategy = "fallback_only"   # 完全降级（0%提速，兼容）

# 4. 执行（示例：unified_only）
result = subprocess.run([
    'python3', 'unified_gate_checker.py',
    '--gates-yaml', gates_yaml_path,
    '--deliverable', deliverable_path,
    ...
])
gate_results = json.loads(filter_json_line(result.stdout))['results']
```

**注意**：需过滤插件加载日志，提取JSON行：
```python
def filter_json_line(stdout):
    return [line for line in stdout.split('\n') if line.startswith('{')][0]
```

---

## 输出产出物（What）

**Gate检查结果**（JSON格式）：
```json
{
  "results": [
    {"id": "gate0_assets", "passed": true, "message": "...", "details": {...}},
    ...
  ],
  "summary": {"total": 9, "passed": 9, "failed": 0}
}
```

**输出说明**：
- stdout：JSON结果（最后一行） + 插件加载日志（前几行）
- stderr：错误信息
- 退出码：0=成功，非0=失败

---

## 插件扩展与降级

### 创建新插件

```bash
# 1. 生成插件模板
./Doc/templates/gate-scripts/create-gate-plugin.sh gate11_custom_logic

# 2. 编辑插件，实现 check() 方法
vim Doc/templates/gate-scripts/plugins/gate_custom_logic.py

# 3. 验证（自动加载，无需重启）
python3 unified_gate_checker.py --list-capabilities
```

### 当前插件

| 插件 | 支持的Gate IDs | 功能 |
|------|---------------|------|
| gate_eval_dataset.py | gate7/gate9 | 评测数据集检查 |
| gate_universal_gates.py | gate8/gate10 | 通用Gates未修改检查 |

### 自动降级

当Gate ID不在支持列表时，自动调用 `script_template` 指定的外部脚本。

**降级示例**：
```yaml
gates:
  - id: gate11_custom_logic  # unified_gate_checker不支持
    checks:
      - type: custom_script
        script_template: "Doc/templates/gate-scripts/check_custom_logic.py"
```

执行流程：查询能力 → 发现不支持 → 调用外部脚本 → 解析PASS/FAIL

---

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 能力查询返回空列表 | 插件加载失败 | 检查插件目录，手动测试插件 |
| Gate结果与预期不符 | 新旧实现不一致 | 双轨验证，对比结果 |
| 性能没有提升 | 大部分Gate不支持 | 创建缺失插件，提升覆盖率 |
| JSON解析失败 | stdout含插件日志 | 过滤非JSON行：`filter_json_line()` |

---

## 进阶文档

- **详细文档**：[README-legacy.md](./README-legacy.md)（730行完整说明）
- **架构设计**：[gate-extensibility-architecture.md](../../eval/system/gate-extensibility-architecture.md)
- **性能分析**：[gate-scripts-performance-analysis.md](../../eval/system/gate-scripts-performance-analysis.md)
- **集成策略**：[ssot-judge-integration-strategy.md](../../eval/system/ssot-judge-integration-strategy.md)

---

## 核心命令速查

```bash
# 批量执行Gate检查
python3 unified_gate_checker.py --gates-yaml <path> --deliverable <path> --ssot <path> --rubric-yaml <path>

# 查询支持的Gate IDs
python3 unified_gate_checker.py --list-capabilities

# 创建新插件
./create-gate-plugin.sh gate11_custom_logic

# 测试性能
time python3 unified_gate_checker.py ...
```

---

## 验收标准

**使用指南验收**：
- [ ] ssot-judge集成者能理解何时使用、如何实现智能路由
- [ ] Administrator能基于本指南扩展新Gate插件
- [ ] 文档简洁清晰，核心信息一目了然

**工具功能验收**：
- [ ] 批量执行Gate检查，性能提升达67%
- [ ] 插件机制和降级机制正常工作

---

**版本**：2.2.0 | **维护者**：Administrator | **最后更新**：2025-10-27
