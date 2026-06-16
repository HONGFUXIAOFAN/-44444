#!/usr/bin/env python3
"""
检查YAML文件结构是否包含必需的顶层键

Usage:
    python3 check_yaml_structure.py <yaml_file> <required_keys>

Example:
    python3 check_yaml_structure.py gates.yaml "context,gates,decision"

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import os

# 添加当前目录到Python路径，以便导入_yaml_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yaml_utils import load_yaml_config

def main():
    if len(sys.argv) < 3:
        print("FAIL: 缺少参数，用法: check_yaml_structure.py <yaml_file> <required_keys>")
        sys.exit(0)

    yaml_file = sys.argv[1]
    required_keys = [k.strip() for k in sys.argv[2].split(',')]

    try:
        config = load_yaml_config(yaml_file)

        # 检查每个必需键是否存在
        missing_keys = []
        for key in required_keys:
            if key not in config:
                missing_keys.append(key)

        if missing_keys:
            print(f"FAIL: {yaml_file}缺少必需顶层键: {', '.join(missing_keys)}")
            sys.exit(0)

        print(f"PASS: {yaml_file}包含所有必需顶层键: {', '.join(required_keys)}")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {yaml_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
