#!/usr/bin/env python3
"""
检查gates.yaml是否包含所有通用必选Gates（gate0-gate8）：
- gate0_assets, gate0_input_ssot_assets
- gate1*, gate2*, gate3*, gate4*, gate5*, gate6*
- gate7_eval_dataset, gate8_universal_gates_unchanged

注：gate9_length_limit已废弃，不再检查

Usage:
    python3 check_required_gates.py <gates_file>

Example:
    python3 check_required_gates.py gates.yaml

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import os

# 添加当前目录到Python路径，以便导入_yaml_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yaml_utils import load_yaml_config

def main():
    if len(sys.argv) < 2:
        print("FAIL: 缺少参数，用法: check_required_gates.py <gates_file>")
        sys.exit(0)

    gates_file = sys.argv[1]

    try:
        config = load_yaml_config(gates_file)

        gates = config.get("gates", [])
        gate_ids = [g.get("id") for g in gates if "id" in g]

        def has_prefix(gate_list, prefix):
            for gid in gate_list:
                if isinstance(gid, str) and gid.startswith(prefix):
                    return True
            return False

        # 检查所有通用必选Gates（gate0-gate8）
        required_gates = {
            "gate0_assets": "产出物存在性",
            "gate0_input_ssot_assets": "SSOT三件套存在性",
            "gate7_eval_dataset": "评测数据集",
            "gate8_universal_gates_unchanged": "通用Gates一致性"
        }

        required_prefixes = ["gate1", "gate2", "gate3", "gate4", "gate5", "gate6"]

        missing_gates = []

        # 检查具体Gate ID
        for gate_id, desc in required_gates.items():
            if gate_id not in gate_ids:
                missing_gates.append(f"{gate_id} ({desc})")

        # 检查前缀Gate
        for prefix in required_prefixes:
            if not has_prefix(gate_ids, prefix):
                missing_gates.append(f"{prefix}* (结构检查)")

        if len(missing_gates) > 0:
            print(f"FAIL: 缺少必需Gate: {', '.join(missing_gates)}")
            sys.exit(0)

        print(f"PASS: gates.yaml包含所有通用必选Gates（gate0-gate8）")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {gates_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
