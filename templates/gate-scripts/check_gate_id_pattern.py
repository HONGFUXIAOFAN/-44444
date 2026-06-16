#!/usr/bin/env python3
"""
检查 gates.yaml 中所有 Gate ID 是否符合命名正则

Usage:
    python3 check_gate_id_pattern.py <gates_file> [pattern]

Default pattern:
    ^gate\d+(_\d+)?_[a-z_]+$

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import os
import re

# 添加当前目录到Python路径，以便导入_yaml_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yaml_utils import load_yaml_config


def main():
    if len(sys.argv) < 2:
        print("FAIL: 缺少参数，用法: check_gate_id_pattern.py <gates_file> [pattern]")
        sys.exit(0)

    gates_file = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) >= 3 else r'^gate\d+(_\d+)?_[a-z_]+' + r'$'

    try:
        cfg = load_yaml_config(gates_file)
        gates = cfg.get('gates', [])
        if not isinstance(gates, list):
            print("FAIL: 配置中缺少 gates 数组或类型错误")
            sys.exit(0)

        bad = []
        for g in gates:
            if not isinstance(g, dict):
                continue
            gid = g.get('id')
            if not isinstance(gid, str):
                bad.append('(缺失或非字符串)')
                continue
            if not re.fullmatch(pattern, gid):
                bad.append(gid)

        if bad:
            listed = ", ".join(bad[:10]) + ("..." if len(bad) > 10 else "")
            print(f"FAIL: 存在不符合命名规范的 Gate ID: {listed}（应匹配正则 {pattern}）")
            sys.exit(0)

        print(f"PASS: 所有 Gate ID 符合命名规范（共 {len(gates)} 项）")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {gates_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()

