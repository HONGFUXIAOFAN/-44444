#!/usr/bin/env python3
"""
检查 gates.yaml 的 decision.critical_gates 引用是否与 gates[*].id 一致

Usage:
    python3 check_critical_refs.py <gates_file>

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
        print("FAIL: 缺少参数，用法: check_critical_refs.py <gates_file>")
        sys.exit(0)

    gates_file = sys.argv[1]

    try:
        config = load_yaml_config(gates_file)

        gates = config.get("gates", [])
        decision = config.get("decision", {})
        critical = decision.get("critical_gates", [])

        gate_ids = {g.get("id") for g in gates if isinstance(g, dict) and g.get("id")}
        missing = [gid for gid in critical if gid not in gate_ids]

        if missing:
            print(f"FAIL: decision.critical_gates 包含未定义的 Gate ID: {', '.join(missing)}")
            sys.exit(0)

        print(f"PASS: decision.critical_gates 引用有效，共 {len(critical)} 项")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {gates_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()

