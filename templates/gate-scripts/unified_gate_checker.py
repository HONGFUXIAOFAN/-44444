#!/usr/bin/env python3
"""
统一Gate检查器 - 插件式架构

功能:
- 集成gate0-gate6通用检查逻辑
- 支持动态加载gate7+插件
- 支持降级到外部script_template和内联script
- 批量执行，减少进程启动和文件读取开销

用法:
    python3 unified_gate_checker.py \\
        --gates-yaml <path> \\
        --deliverable <path> \\
        [--plugins-dir <path>]

输出:
    JSON格式的检查结果
"""

import os
import sys
import json
import yaml
import glob
import argparse
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入插件接口
from plugin_interface import GatePlugin, PluginRegistry


class UnifiedGateChecker:
    """统一Gate检查器"""

    def __init__(self, project_root: str, plugins_dir: Optional[str] = None):
        """
        初始化检查器

        Args:
            project_root: 项目根目录
            plugins_dir: 插件目录（可选）
        """
        self.project_root = project_root
        self.plugins_dir = plugins_dir or os.path.join(project_root, "Doc/templates/gate-scripts/plugins")
        self.plugin_registry = PluginRegistry()
        self.yaml_cache = {}  # YAML文件缓存
        self.file_cache = {}  # 文件存在性缓存

        # 加载插件
        self._load_plugins()

    def _load_plugins(self):
        """自动发现和加载插件"""
        if not os.path.exists(self.plugins_dir):
            return

        plugin_files = glob.glob(os.path.join(self.plugins_dir, "gate_*.py"))
        for plugin_file in plugin_files:
            try:
                # 动态加载Python模块
                spec = importlib.util.spec_from_file_location("plugin", plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 查找插件类（继承自GatePlugin）
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, GatePlugin) and attr != GatePlugin:
                        plugin_instance = attr()
                        self.plugin_registry.register(plugin_instance)
                        print(f"✅ 加载插件: {plugin_instance.get_metadata()['name']}")

            except Exception as e:
                print(f"⚠️  加载插件失败 {plugin_file}: {e}")

    def _load_yaml(self, yaml_path: str) -> Dict:
        """
        加载YAML文件（带缓存）

        Args:
            yaml_path: YAML文件路径（相对或绝对）

        Returns:
            YAML内容字典
        """
        # 转换为绝对路径
        if not os.path.isabs(yaml_path):
            yaml_path = os.path.join(self.project_root, yaml_path)

        # 检查缓存
        if yaml_path in self.yaml_cache:
            return self.yaml_cache[yaml_path]

        # 加载并缓存
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                docs = list(yaml.safe_load_all(f))
                # 合并多文档YAML
                merged = {}
                for doc in docs:
                    if doc:
                        merged.update(doc)
                self.yaml_cache[yaml_path] = merged
                return merged
        except Exception as e:
            print(f"❌ 加载YAML失败 {yaml_path}: {e}")
            return {}

    def _check_file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在（带缓存）

        Args:
            file_path: 文件路径（相对或绝对）

        Returns:
            是否存在
        """
        # 转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.project_root, file_path)

        # 检查缓存
        if file_path in self.file_cache:
            return self.file_cache[file_path]

        # 检查并缓存
        exists = os.path.exists(file_path)
        self.file_cache[file_path] = exists
        return exists

    # ========== 核心Gates检查逻辑（gate0-gate6） ==========

    def _check_gate0_assets(self, gate_config: Dict, context: Dict) -> Dict:
        """gate0: 产出物存在性检查"""
        checks_config = gate_config.get('checks', [])
        if not checks_config:
            return {"passed": False, "details": "缺少checks配置"}

        check = checks_config[0]
        params = check.get('params', {})

        # 提取文件路径参数（p1, p2, p3, ...）
        file_paths = []
        for key in sorted(params.keys()):
            if key.startswith('p'):
                file_paths.append(params[key])

        # 批量检查文件存在性
        missing_paths = []
        for path in file_paths:
            # 替换所有占位符
            for placeholder, replacement in context.items():
                path = path.replace(f'{{{placeholder}}}', str(replacement))

            if not self._check_file_exists(path):
                missing_paths.append(path)

        if missing_paths:
            return {
                "passed": False,
                "details": f"缺失文件: {', '.join(missing_paths)}"
            }
        else:
            return {
                "passed": True,
                "details": f"所有文件存在 ({len(file_paths)} 个)"
            }

    def _check_gate1_frontmatter(self, gate_config: Dict, context: Dict) -> Dict:
        """gate1: SSOT统筹文档YAML头检查"""
        ssot_path = context.get('ssot_path', '')
        if not self._check_file_exists(ssot_path):
            return {"passed": False, "details": f"SSOT文件不存在: {ssot_path}"}

        # 读取文件前几行提取YAML头
        abs_path = os.path.join(self.project_root, ssot_path) if not os.path.isabs(ssot_path) else ssot_path
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取YAML frontmatter
            if not content.startswith('---'):
                return {"passed": False, "details": "缺少YAML frontmatter"}

            parts = content.split('---', 2)
            if len(parts) < 3:
                return {"passed": False, "details": "YAML frontmatter格式错误"}

            frontmatter = yaml.safe_load(parts[1])

            # 检查必填字段
            required_fields = ['name', 'version', 'description', 'applies_to']
            missing_fields = [f for f in required_fields if f not in frontmatter]

            if missing_fields:
                return {
                    "passed": False,
                    "details": f"缺少必填字段: {', '.join(missing_fields)}"
                }
            else:
                return {
                    "passed": True,
                    "details": f"YAML头包含所有必填字段: {', '.join(required_fields)}"
                }

        except Exception as e:
            return {"passed": False, "details": f"解析YAML头失败: {e}"}

    def _check_gate2_gates_schema(self, gate_config: Dict, context: Dict) -> Dict:
        """gate2: gates.yaml顶层结构检查"""
        gates_yaml_path = context.get('gates_yaml_path', '')
        gates_data = self._load_yaml(gates_yaml_path)

        if not gates_data:
            return {"passed": False, "details": "无法加载gates.yaml"}

        # 检查必需顶层键
        required_keys = ['context', 'gates', 'decision']
        missing_keys = [k for k in required_keys if k not in gates_data]

        if missing_keys:
            return {
                "passed": False,
                "details": f"缺少必需顶层键: {', '.join(missing_keys)}"
            }

        # 检查rule_id格式（如果存在）
        rule_id = gates_data.get('rule_id', '')
        if rule_id and not self._is_valid_rule_id(rule_id):
            return {
                "passed": False,
                "details": f"rule_id格式错误: {rule_id}（应为XXX-YYY格式）"
            }

        return {
            "passed": True,
            "details": f"包含所有必需顶层键: {', '.join(required_keys)}"
        }

    def _check_gate3_rubric_schema(self, gate_config: Dict, context: Dict) -> Dict:
        """gate3: rubric.yaml顶层结构检查"""
        rubric_yaml_path = context.get('rubric_yaml_path', '')
        rubric_data = self._load_yaml(rubric_yaml_path)

        if not rubric_data:
            return {"passed": False, "details": "无法加载rubric.yaml"}

        # 检查必需顶层键
        required_keys = ['rubric', 'scale', 'aggregation']
        missing_keys = [k for k in required_keys if k not in rubric_data]

        if missing_keys:
            return {
                "passed": False,
                "details": f"缺少必需顶层键: {', '.join(missing_keys)}"
            }

        # 检查rule_id格式（如果存在）
        rule_id = rubric_data.get('rule_id', '')
        if rule_id and not self._is_valid_rule_id(rule_id):
            return {
                "passed": False,
                "details": f"rule_id格式错误: {rule_id}（应为XXX-YYY格式）"
            }

        return {
            "passed": True,
            "details": f"包含所有必需顶层键: {', '.join(required_keys)}"
        }

    def _check_gate4_path_validity(self, gate_config: Dict, context: Dict) -> Dict:
        """gate4: 路径引用有效性检查（简化版，仅检查configs路径）"""
        ssot_path = context.get('ssot_path', '')
        abs_path = os.path.join(self.project_root, ssot_path) if not os.path.isabs(ssot_path) else ssot_path

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取YAML frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                configs = frontmatter.get('configs', {})

                # 检查gates和rubric路径
                gates_path = configs.get('gates', '')
                rubric_path = configs.get('rubric', '')

                invalid_paths = []
                if gates_path and not self._check_file_exists(gates_path):
                    invalid_paths.append(f"gates: {gates_path}")
                if rubric_path and not self._check_file_exists(rubric_path):
                    invalid_paths.append(f"rubric: {rubric_path}")

                if invalid_paths:
                    return {
                        "passed": False,
                        "details": f"configs路径无效: {', '.join(invalid_paths)}"
                    }
                else:
                    return {
                        "passed": True,
                        "details": f"configs路径有效（gates: {gates_path}, rubric: {rubric_path}）"
                    }

        except Exception as e:
            return {"passed": False, "details": f"检查路径失败: {e}"}

        return {"passed": True, "details": "路径检查通过"}

    def _check_gate5_required_gates(self, gate_config: Dict, context: Dict) -> Dict:
        """gate5: Gates必需项完整性检查"""
        gates_yaml_path = context.get('gates_yaml_path', '')
        gates_data = self._load_yaml(gates_yaml_path)

        if not gates_data:
            return {"passed": False, "details": "无法加载gates.yaml"}

        gates_list = gates_data.get('gates', [])
        gate_ids = [g.get('id', '') for g in gates_list]

        # 检查必需的gate0*和gate1*
        has_gate0 = any(gid.startswith('gate0') for gid in gate_ids)
        has_gate1 = any(gid.startswith('gate1') for gid in gate_ids)

        missing = []
        if not has_gate0:
            missing.append('gate0*（资产存在性检查）')
        if not has_gate1:
            missing.append('gate1*（Schema有效性检查）')

        if missing:
            return {
                "passed": False,
                "details": f"缺少必需Gate: {', '.join(missing)}"
            }
        else:
            return {
                "passed": True,
                "details": "gates.yaml包含所有必需Gate（gate0*、gate1*）"
            }

    def _check_gate6_weight_sum(self, gate_config: Dict, context: Dict) -> Dict:
        """gate6: Rubric权重总和检查"""
        rubric_yaml_path = context.get('rubric_yaml_path', '')
        rubric_data = self._load_yaml(rubric_yaml_path)

        if not rubric_data:
            return {"passed": False, "details": "无法加载rubric.yaml"}

        rubric_list = rubric_data.get('rubric', [])
        if not rubric_list:
            return {"passed": False, "details": "rubric为空"}

        # 计算权重总和
        total_weight = sum(r.get('weight', 0) for r in rubric_list)

        # 容差检查（0.95 <= total <= 1.05）
        if 0.95 <= total_weight <= 1.05:
            return {
                "passed": True,
                "details": f"Rubric权重总和正常: {total_weight:.2f}"
            }
        else:
            return {
                "passed": False,
                "details": f"Rubric权重总和异常: {total_weight:.2f}（应在0.95-1.05范围）"
            }

    def _is_valid_rule_id(self, rule_id: str) -> bool:
        """检查rule_id格式是否为XXX-YYY"""
        import re
        return bool(re.match(r'^\d{3}-[a-z-]+$', rule_id))

    def _check_regex_match(self, check: Dict, context: Dict) -> Dict:
        """
        检查文件内容是否匹配所有正则表达式

        Args:
            check: check配置（包含file和patterns）
            context: 上下文信息

        Returns:
            检查结果
        """
        file_path = check.get('file', '')
        patterns = check.get('patterns', [])

        # 替换占位符
        for placeholder, replacement in context.items():
            file_path = file_path.replace(f'{{{placeholder}}}', str(replacement))

        # 转换为绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.project_root, file_path)

        # 检查文件是否存在
        if not self._check_file_exists(file_path):
            return {"passed": False, "details": f"文件不存在: {file_path}"}

        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"passed": False, "details": f"读取文件失败: {e}"}

        # 检查每个模式
        import re
        missing_patterns = []
        for pattern in patterns:
            if not re.search(pattern, content):
                missing_patterns.append(pattern)

        if missing_patterns:
            return {
                "passed": False,
                "details": f"缺少匹配模式: {', '.join(missing_patterns)}"
            }
        else:
            return {
                "passed": True,
                "details": f"所有模式都匹配（{len(patterns)}个）"
            }

    def _check_length_limit(self, check: Dict, context: Dict) -> Dict:
        """
        检查文件行数是否超过限制

        Args:
            check: check配置（包含files和max_lines）
            context: 上下文信息

        Returns:
            检查结果
        """
        file_paths = check.get('files', [])
        max_lines = check.get('max_lines', 200)

        if not file_paths:
            return {"passed": False, "details": "配置错误：缺少files字段"}

        # 检查所有文件
        failures = []
        stats = []

        for file_path in file_paths:
            # 替换占位符
            for placeholder, replacement in context.items():
                file_path = file_path.replace(f'{{{placeholder}}}', str(replacement))

            # 转换为绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)

            # 检查文件是否存在
            if not self._check_file_exists(file_path):
                failures.append(f"{os.path.basename(file_path)}: 文件不存在")
                continue

            # 统计行数
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = len(f.readlines())

                filename = os.path.basename(file_path)
                stats.append(f"{filename}:{line_count}/{max_lines}")

                if line_count > max_lines:
                    failures.append(f"{filename}超限: {line_count}行 > {max_lines}行")

            except Exception as e:
                failures.append(f"{os.path.basename(file_path)}: 读取失败 - {e}")

        # 汇总结果
        if failures:
            return {
                "passed": False,
                "details": f"文件行数超限 - {'; '.join(failures)}"
            }
        else:
            return {
                "passed": True,
                "details": f"文件行数合规 ({', '.join(stats)})"
            }

    def _check_yaml_frontmatter(self, check: Dict, context: Dict) -> Dict:
        """
        检查文件的YAML frontmatter是否包含必需字段

        Args:
            check: check配置（包含file/files和required_fields）
            context: 上下文信息

        Returns:
            检查结果
        """
        # 兼容 file 和 files 两种写法
        file_paths = []
        if 'file' in check:
            file_paths = [check['file']]
        elif 'files' in check:
            file_paths = check['files']
        else:
            return {"passed": False, "details": "配置错误：缺少file或files字段"}

        required_fields = check.get('required_fields', [])

        # 检查所有文件
        all_passed = True
        details_list = []

        for file_path in file_paths:
            # 替换占位符
            for placeholder, replacement in context.items():
                file_path = file_path.replace(f'{{{placeholder}}}', str(replacement))

            # 转换为绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)

            # 检查文件是否存在
            if not self._check_file_exists(file_path):
                all_passed = False
                details_list.append(f"文件不存在: {file_path}")
                continue

            # 读取并解析YAML frontmatter
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取YAML frontmatter
                if not content.startswith('---'):
                    all_passed = False
                    details_list.append(f"{os.path.basename(file_path)}: 缺少YAML frontmatter")
                    continue

                parts = content.split('---', 2)
                if len(parts) < 3:
                    all_passed = False
                    details_list.append(f"{os.path.basename(file_path)}: YAML frontmatter格式错误")
                    continue

                frontmatter = yaml.safe_load(parts[1])

                # 检查必需字段
                missing_fields = [f for f in required_fields if f not in frontmatter]

                if missing_fields:
                    all_passed = False
                    details_list.append(
                        f"{os.path.basename(file_path)}: 缺少必填字段 {', '.join(missing_fields)}"
                    )
                else:
                    details_list.append(
                        f"{os.path.basename(file_path)}: YAML头包含所有必填字段"
                    )

            except Exception as e:
                all_passed = False
                details_list.append(f"{os.path.basename(file_path)}: 解析YAML头失败 - {e}")

        # 汇总结果
        if all_passed:
            return {
                "passed": True,
                "details": f"YAML头包含所有必填字段 ({len(file_paths)}个文件)"
            }
        else:
            return {
                "passed": False,
                "details": "; ".join(details_list)
            }

    # ========== Gate检查主逻辑 ==========

    def check_gate(self, gate_config: Dict, context: Dict) -> Dict:
        """
        执行单个Gate检查

        Args:
            gate_config: Gate配置字典
            context: 上下文信息

        Returns:
            检查结果字典
        """
        gate_id = gate_config.get('id', '')

        # 优先级1: 核心Gates（gate0-gate6）
        core_gate_handlers = {
            'gate0_assets': self._check_gate0_assets,
            'gate0_input_ssot_assets': self._check_gate0_assets,  # 复用gate0逻辑
            'gate1_ssot_frontmatter': self._check_gate1_frontmatter,
            'gate2_gates_schema': self._check_gate2_gates_schema,
            'gate3_rubric_schema': self._check_gate3_rubric_schema,
            'gate4_path_validity': self._check_gate4_path_validity,
            'gate5_required_gates': self._check_gate5_required_gates,
            'gate6_weight_sum': self._check_gate6_weight_sum,
        }

        if gate_id in core_gate_handlers:
            return core_gate_handlers[gate_id](gate_config, context)

        # 优先级2: 插件Gates（gate7+）
        plugin = self.plugin_registry.get_plugin(gate_id)
        if plugin:
            return plugin.check(gate_config, context)

        # 优先级3: 降级处理（外部脚本或内联脚本）
        return self._execute_fallback(gate_config, context)

    def _execute_fallback(self, gate_config: Dict, context: Dict) -> Dict:
        """
        降级处理：调用外部script_template或执行内联检查

        Args:
            gate_config: Gate配置字典
            context: 上下文信息

        Returns:
            检查结果字典
        """
        checks_config = gate_config.get('checks', [])
        if not checks_config:
            return {"passed": False, "details": "缺少checks配置"}

        check = checks_config[0]
        check_type = check.get('type', '')

        # 方式1: regex_match 类型（正则匹配）
        if check_type == 'regex_match':
            return self._check_regex_match(check, context)

        # 方式2: yaml_frontmatter 类型（YAML头检查）
        if check_type == 'yaml_frontmatter':
            return self._check_yaml_frontmatter(check, context)

        # 方式3: length_limit 类型（行数限制检查）
        if check_type == 'length_limit':
            return self._check_length_limit(check, context)

        # 方式4: 外部script_template
        if 'script_template' in check:
            script_path = check['script_template']
            params = check.get('params', {})

            # 替换占位符并构建命令行参数
            args = []
            for key in sorted(params.keys()):
                if key.startswith('p'):
                    value = params[key]
                    # 替换常见占位符
                    for placeholder, replacement in context.items():
                        value = value.replace(f'{{{placeholder}}}', str(replacement))
                    args.append(value)

            # 执行外部脚本
            script_abs_path = os.path.join(self.project_root, script_path)
            cmd = ['python3', script_abs_path] + args

            import subprocess
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                output = result.stdout.strip()

                # 解析输出（PASS/FAIL）
                if output.startswith('PASS'):
                    return {"passed": True, "details": output.replace('PASS: ', '')}
                else:
                    return {"passed": False, "details": output.replace('FAIL: ', '')}

            except Exception as e:
                return {"passed": False, "details": f"执行脚本失败: {e}"}

        # 方式2: 内联script（暂不支持，需要更复杂的沙箱执行）
        if 'script' in check:
            return {
                "passed": False,
                "details": "内联script暂不支持，请使用script_template或插件"
            }

        return {"passed": False, "details": "未找到可执行的检查方式"}

    def check_all_gates(self, gates_yaml_path: str, context: Dict) -> List[Dict]:
        """
        批量执行所有Gates检查

        Args:
            gates_yaml_path: gates.yaml文件路径
            context: 上下文信息

        Returns:
            检查结果列表
        """
        gates_data = self._load_yaml(gates_yaml_path)
        if not gates_data:
            return [{"gate_id": "ERROR", "passed": False, "details": "无法加载gates.yaml"}]

        gates_list = gates_data.get('gates', [])
        results = []

        # 批量检查所有Gates
        for gate_config in gates_list:
            gate_id = gate_config.get('id', 'UNKNOWN')
            try:
                result = self.check_gate(gate_config, context)
                results.append({
                    "gate_id": gate_id,
                    "gate_name": gate_config.get('name', ''),
                    "critical": gate_config.get('critical', False),
                    **result
                })
            except Exception as e:
                results.append({
                    "gate_id": gate_id,
                    "passed": False,
                    "details": f"检查异常: {e}"
                })

        return results


def find_project_root(start_path: str) -> Optional[str]:
    """查找项目根目录（包含Doc/templates和Doc/rules的目录）"""
    current = os.path.dirname(os.path.abspath(start_path))
    while current != os.path.dirname(current):  # 未到达文件系统根目录
        templates_path = os.path.join(current, 'Doc', 'templates')
        rules_path = os.path.join(current, 'Doc', 'rules')
        if os.path.isdir(templates_path) and os.path.isdir(rules_path):
            return current
        current = os.path.dirname(current)
    return None


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='统一Gate检查器')
    parser.add_argument('--gates-yaml', help='gates.yaml文件路径')
    parser.add_argument('--deliverable', help='待检查的产出物路径')
    parser.add_argument('--ssot', help='SSOT文件路径（可选）')
    parser.add_argument('--rubric-yaml', help='rubric.yaml文件路径（可选）')
    parser.add_argument('--plugins-dir', help='插件目录路径（可选）')
    parser.add_argument('--list-capabilities', action='store_true',
                       help='列出所有支持的Gate IDs（能力查询）')

    args = parser.parse_args()

    # 查找项目根目录
    project_root = find_project_root(__file__)
    if not project_root:
        print(json.dumps({
            "error": "无法找到项目根目录",
            "results": []
        }))
        sys.exit(1)

    # 初始化检查器
    checker = UnifiedGateChecker(project_root, args.plugins_dir)

    # 能力查询模式
    if args.list_capabilities:
        # 收集所有支持的Gate IDs
        core_gates = [
            'gate0_assets',
            'gate0_input_ssot_assets',
            'gate1_ssot_frontmatter',
            'gate2_gates_schema',
            'gate3_rubric_schema',
            'gate4_path_validity',
            'gate5_required_gates',
            'gate6_weight_sum',
        ]
        plugin_gates = checker.plugin_registry.list_gate_ids()

        capabilities = {
            "project_root": project_root,
            "core_gates": core_gates,
            "plugin_gates": plugin_gates,
            "all_gates": core_gates + plugin_gates,
            "plugins_loaded": len(checker.plugin_registry.list_plugins()),
            "plugin_details": checker.plugin_registry.list_plugins()
        }

        print(json.dumps(capabilities, indent=2, ensure_ascii=False))
        sys.exit(0)

    # 从 gates-yaml 路径推导 domain 和 rule-id
    # 例如: Doc/ops/system/rule-generator-v1/003-rule-generation-gates.yaml
    #   -> domain=system/rule-generator-v1, rule-id=003-rule-generation
    domain = ''
    rule_id = ''

    if args.gates_yaml:
        parts = args.gates_yaml.split('/')
        if 'ops' in parts:
            ops_idx = parts.index('ops')
            # domain 是 ops/ 之后到文件名之前的部分
            if len(parts) > ops_idx + 2:
                domain_parts = parts[ops_idx+1:-1]
                domain = '/'.join(domain_parts)

            # rule-id 从文件名提取
            if parts:
                filename = parts[-1]
                # 例如: 003-rule-generation-gates.yaml -> 003-rule-generation
                rule_id = filename.replace('-gates.yaml', '').replace('-rubric.yaml', '')

    # 如果没有提供 ssot 和 rubric_yaml，从 domain 和 rule-id 推导
    ssot_path = args.ssot
    rubric_yaml_path = args.rubric_yaml

    if not ssot_path and domain and rule_id:
        ssot_path = f"Doc/ssot/{domain}/{rule_id}-ssot.md"

    if not rubric_yaml_path and domain and rule_id:
        rubric_yaml_path = f"Doc/ops/{domain}/{rule_id}-rubric.yaml"

    # 构建上下文
    context = {
        'project_root': project_root,
        'deliverable_path': args.deliverable,
        'gates_yaml_path': args.gates_yaml,
        'ssot_path': ssot_path or '',
        'rubric_yaml_path': rubric_yaml_path or '',
        'domain': domain,
        'rule-id': rule_id,
    }

    # 执行检查
    results = checker.check_all_gates(args.gates_yaml, context)

    # 输出JSON结果
    output = {
        "project_root": project_root,
        "deliverable": args.deliverable,
        "total_gates": len(results),
        "passed_gates": sum(1 for r in results if r.get('passed', False)),
        "results": results
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
