#!/usr/bin/env python3
"""
通用Gates未修改检查插件

支持的Gate IDs:
- gate8_universal_gates_unchanged (001规则)
- gate10_universal_gates_unchanged (003规则)
"""

import os
import sys
import yaml

# 添加父目录到路径以导入plugin_interface
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_interface import GatePlugin
from typing import Dict, Any, List


# 通用必选Gates的规范定义
UNIVERSAL_GATES_SPEC = {
    "gate0_assets": {
        "name_any_of": [
            "规则产出物存在性检查",
            "产出物本体存在性检查",
            "规则文件存在性检查",
            "产出物存在性检查",
            "三件套文件存在性检查"
        ],
        "description_keywords": ["存在"],
        "critical": True
    },
    "gate0_input_ssot_assets": {
        "name_any_of": [
            "三件套文件存在性检查",
            "三件套文件存在性检查（别名）"
        ],
        "description_keywords": ["ssot", "存在"],
        "critical": True
    },
    "gate1_ssot_frontmatter": {
        "name": "SSOT统筹文档YAML头检查",
        "description_keywords": ["ssot.md", "YAML头", "必填字段"],
        "critical": False
    },
    "gate2_gates_schema": {
        "name": "gates.yaml 顶层结构检查",
        "description_keywords": ["gates.yaml", "顶层键"],
        "critical": True
    },
    "gate3_rubric_schema": {
        "name": "rubric.yaml 顶层结构检查",
        "description_keywords": ["rubric.yaml", "顶层键"],
        "critical": True
    },
    "gate4_path_validity": {
        "name": "路径引用有效性检查",
        "description_keywords": ["路径", "有效"],
        "critical": False
    },
    "gate5_required_gates": {
        "name": "Gates必需项完整性检查",
        "description_keywords": ["gates.yaml", "gate0", "gate1"],
        "critical": True
    },
    "gate6_weight_sum": {
        "name": "Rubric权重总和检查",
        "description_keywords": ["权重", "总和"],
        "critical": False
    }
}


class UniversalGatesPlugin(GatePlugin):
    """通用Gates未修改检查插件"""

    def get_gate_ids(self) -> List[str]:
        return [
            "gate8_universal_gates_unchanged",   # 001规则
            "gate10_universal_gates_unchanged",  # 003规则
        ]

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "universal_gates_checker",
            "version": "1.0.0",
            "description": "检查通用必选Gates（gate0-gate6）是否被擅自修改",
            "author": "Administrator"
        }

    def check(self, gate_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查通用必选Gates是否被修改

        检查项:
        - gate0-gate6的name是否符合规范
        - gate0-gate6的critical标志是否正确
        """
        # 获取gates.yaml路径
        checks_config = gate_config.get('checks', [])
        if not checks_config:
            return {"passed": False, "details": "缺少checks配置"}

        check = checks_config[0]
        params = check.get('params', {})
        # 兼容两种参数名: p1 或 gates_file
        gates_file = params.get('gates_file', params.get('p1', ''))

        # 替换占位符
        for placeholder, replacement in context.items():
            gates_file = gates_file.replace(f'{{{placeholder}}}', str(replacement))

        # 转换为绝对路径
        project_root = context.get('project_root', '')
        if not os.path.isabs(gates_file):
            gates_file = os.path.join(project_root, gates_file)

        # 加载gates.yaml
        try:
            gates_data = self._load_gates_yaml(gates_file)
        except Exception as e:
            return {"passed": False, "details": f"无法加载gates.yaml: {e}"}

        # 检查通用Gates
        errors = self._check_universal_gates(gates_data)

        if errors:
            return {
                "passed": False,
                "details": "通用必选Gates被修改:\n" + "\n".join(errors)
            }
        else:
            return {
                "passed": True,
                "details": "✅ 通用必选Gates检查通过"
            }

    def _load_gates_yaml(self, gates_file: str) -> Dict:
        """加载gates.yaml文件（支持多文档YAML）"""
        with open(gates_file, 'r', encoding='utf-8') as f:
            docs = list(yaml.safe_load_all(f))

        # 合并所有文档
        merged = {}
        for doc in docs:
            if doc:
                merged.update(doc)

        return merged

    def _check_universal_gates(self, gates_data: Dict) -> List[str]:
        """检查通用必选Gates是否被修改"""
        errors = []

        gates_list = gates_data.get('gates', [])
        gates_dict = {g['id']: g for g in gates_list if 'id' in g}

        for gate_id, spec in UNIVERSAL_GATES_SPEC.items():
            if gate_id not in gates_dict:
                errors.append(f"缺失通用必选Gate: {gate_id}")
                continue

            gate = gates_dict[gate_id]

            # 检查name（支持name_any_of或单个name）
            expected_names = spec.get('name_any_of', [])
            if expected_names:
                # 允许多个name
                actual_name = gate.get('name', '')
                if actual_name not in expected_names:
                    errors.append(
                        f"{gate_id}的name被修改为'{actual_name}'（应为{expected_names}之一）"
                    )
            else:
                # 单个name
                expected_name = spec.get('name', '')
                actual_name = gate.get('name', '')
                if expected_name and actual_name != expected_name:
                    errors.append(
                        f"{gate_id}的name被修改为'{actual_name}'（应为'{expected_name}'）"
                    )

            # 检查critical标志
            expected_critical = spec.get('critical', False)
            actual_critical = gate.get('critical', False)
            if actual_critical != expected_critical:
                errors.append(
                    f"{gate_id}的critical被修改为{actual_critical}（应为{expected_critical}）"
                )

        return errors
