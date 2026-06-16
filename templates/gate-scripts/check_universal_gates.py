#!/usr/bin/env python3
"""
检查通用必选Gates（gate0-gate8）是否被擅自修改。

用途: 防止Administrator在生成SSOT时擅自修改通用必选Gates的定义
检查: gate0-gate8的ID、name、description、critical是否与规范保持一致（行数限制Gate已废弃）
"""

import sys
import yaml
from pathlib import Path

# 通用必选Gates的规范定义（与ssot-template保持一致）
UNIVERSAL_GATES_SPEC = {
    "gate0_assets": {
        # 名称在不同产出物上允许差异，但需表达“本体存在性”
        "name_any_of": [
            "规则产出物存在性检查",
            "产出物本体存在性检查",
            "规则文件存在性检查",
            "产出物存在性检查",
            "三件套文件存在性检查"  # 兼容001等价语义
        ],
        "description_keywords": ["存在"],
        "critical": True
    },
    "gate0_input_ssot_assets": {
        # 统一用于“三件套存在性”
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
        "critical": False  # structural，避免未生成规则时必然报错
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
    },
    "gate7_eval_dataset": {
        "name": "评测数据集保障机制检查",
        "description_keywords": ["评测数据集", "用例"],
        "critical": False
    },
    "gate8_universal_gates_unchanged": {
        "name": "通用必选Gates未被修改检查",
        "description_keywords": ["通用Gates", "修改"],
        "critical": True
    }
}


def load_gates_yaml(gates_file):
    """加载gates.yaml文件（支持多文档YAML）"""
    try:
        with open(gates_file, 'r', encoding='utf-8') as f:
            docs = list(yaml.safe_load_all(f))
        
        # 合并所有文档
        merged = {}
        for doc in docs:
            if doc:
                merged.update(doc)
        
        return merged
    except Exception as e:
        print(f"❌ 无法加载gates.yaml: {e}")
        sys.exit(1)


def check_universal_gates(gates_data):
    """检查通用必选Gates是否被修改"""
    errors = []
    warnings = []
    
    gates_list = gates_data.get('gates', [])
    gates_dict = {g['id']: g for g in gates_list if 'id' in g}

    for gate_id, spec in UNIVERSAL_GATES_SPEC.items():
        if gate_id not in gates_dict:
            errors.append(f"缺失通用必选Gate: {gate_id}")
            continue
        gate = gates_dict[gate_id]
        expected_name = spec.get('name')
        expected_name_any = spec.get('name_any_of')
        expected_keywords = spec['description_keywords']
        expected_critical = spec['critical']

        # 检查name
        gate_name = gate.get('name')
        if expected_name_any:
            if gate_name not in expected_name_any:
                errors.append(
                    f"{gate.get('id')}: name不在允许集合内\n"
                    f"  允许: {expected_name_any}\n"
                    f"  实际: '{gate_name}'"
                )
        elif expected_name:
            if gate_name != expected_name:
                errors.append(
                    f"{gate.get('id')}: name被修改\n"
                    f"  期望: '{expected_name}'\n"
                    f"  实际: '{gate_name}'"
                )

        # 检查description关键词（允许描述有一定灵活性，但必须包含关键词）
        description = gate.get('description', '')
        missing_keywords = [kw for kw in expected_keywords if kw not in description]
        if missing_keywords:
            warnings.append(
                f"{gate.get('id')}: description可能被修改，缺少关键词: {', '.join(missing_keywords)}"
            )

        # 检查critical
        if gate.get('critical') != expected_critical:
            errors.append(
                f"{gate.get('id')}: critical标志被修改\n"
                f"  期望: {expected_critical}\n"
                f"  实际: {gate.get('critical')}"
            )
    
    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("用法: python check_universal_gates.py <gates_file>")
        sys.exit(1)
    
    gates_file = sys.argv[1]
    
    if not Path(gates_file).exists():
        print(f"❌ 文件不存在: {gates_file}")
        sys.exit(1)
    
    gates_data = load_gates_yaml(gates_file)
    errors, warnings = check_universal_gates(gates_data)
    
    if errors:
        print("❌ 通用必选Gates被擅自修改:")
        for error in errors:
            print(f"  {error}")
        print("\n⚠️ 重要: 通用必选Gates（gate0-gate8）是固定的，不应修改！")
        print("   针对特定产出物类型的检查应放在领域专属Gates（gate10+）中，长度控制等可放在Rubric长度维度。")
        sys.exit(1)
    
    if warnings:
        print("⚠️ 警告:")
        for warning in warnings:
            print(f"  {warning}")
    
    print("✅ 通用必选Gates检查通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
