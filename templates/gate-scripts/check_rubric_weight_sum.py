#!/usr/bin/env python3
"""
检查rubric.yaml中所有维度权重总和是否≈1.0

Usage:
    python3 check_rubric_weight_sum.py <rubric_file> <tolerance>

Example:
    python3 check_rubric_weight_sum.py rubric.yaml 0.05

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
        print("FAIL: 缺少参数，用法: check_rubric_weight_sum.py <rubric_file> <tolerance>")
        sys.exit(0)

    rubric_file = sys.argv[1]
    tolerance = float(sys.argv[2])

    try:
        config = load_yaml_config(rubric_file)

        rubric = config.get("rubric", [])
        if not rubric:
            print(f"FAIL: {rubric_file}中rubric数组为空")
            sys.exit(0)

        total_weight = sum([d.get("weight", 0.0) for d in rubric if "weight" in d])

        min_threshold = 1.0 - tolerance
        max_threshold = 1.0 + tolerance

        if total_weight < min_threshold or total_weight > max_threshold:
            print(f"FAIL: Rubric权重总和异常: {total_weight:.2f}（应在{min_threshold:.2f}-{max_threshold:.2f}范围）")
            sys.exit(0)

        print(f"PASS: Rubric权重总和正常: {total_weight:.2f}")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {rubric_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
