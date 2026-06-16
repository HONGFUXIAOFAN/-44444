#!/usr/bin/env python3
"""
检查 YAML 配置中的 rule_id 是否符合命名正则

Usage:
    python3 check_rule_id_pattern.py <yaml_file> [pattern]

Default pattern:
    ^\d{3}-[a-z-]+$

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
        print("FAIL: 缺少参数，用法: check_rule_id_pattern.py <yaml_file> [pattern]")
        sys.exit(0)

    yaml_file = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) >= 3 else r'^\d{3}-[a-z-]+$'

    try:
        cfg = load_yaml_config(yaml_file)
        rule_id = cfg.get('rule_id')

        if rule_id is None:
            # rule_id 在模板中属推荐字段（可选），缺失时不作为失败
            print(f"PASS: {yaml_file} 未定义 rule_id（可选字段）")
            sys.exit(0)

        if re.fullmatch(pattern, str(rule_id)):
            print(f"PASS: rule_id 符合命名规范: {rule_id}")
            sys.exit(0)
        else:
            print(f"FAIL: rule_id 不符合命名规范: {rule_id}（应匹配正则 {pattern}）")
            sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {yaml_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)


if __name__ == "__main__":
    main()

