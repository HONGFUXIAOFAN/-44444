#!/usr/bin/env python3
"""
检查ssot.md的YAML头中configs字段指向的路径是否有效

Usage:
    python3 check_configs_paths.py <ssot_file>

Example:
    python3 check_configs_paths.py Doc/ssot/system/rule-generator-v1/001-ssot-generation-ssot.md

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import yaml
import re
import os

def extract_yaml_frontmatter(content):
    """提取Markdown文件的YAML前置元数据"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None
    return yaml.safe_load(match.group(1))

def find_project_root(start_path):
    """查找项目根目录（包含Doc/templates和Doc/rules的目录）"""
    current = os.path.dirname(os.path.abspath(start_path))
    while current != os.path.dirname(current):  # 未到达根目录
        # 检查是否同时存在Doc/templates和Doc/rules
        templates_path = os.path.join(current, 'Doc', 'templates')
        rules_path = os.path.join(current, 'Doc', 'rules')
        if os.path.isdir(templates_path) and os.path.isdir(rules_path):
            return current
        current = os.path.dirname(current)
    return None

def main():
    if len(sys.argv) < 2:
        print("FAIL: 缺少参数，用法: check_configs_paths.py <ssot_file>")
        sys.exit(0)

    ssot_file = sys.argv[1]

    # 如果是相对路径，基于项目根目录解析
    if not os.path.isabs(ssot_file):
        project_root = find_project_root(__file__)
        if project_root:
            ssot_file = os.path.join(project_root, ssot_file)

    try:
        with open(ssot_file, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter = extract_yaml_frontmatter(content)
        if not frontmatter:
            print(f"FAIL: SSOT文档YAML头解析失败")
            sys.exit(0)

        if "configs" not in frontmatter:
            print(f"FAIL: SSOT文档YAML头缺少configs字段")
            sys.exit(0)

        configs = frontmatter["configs"]
        gates_path = configs.get("gates")
        rubric_path = configs.get("rubric")

        if not gates_path:
            print(f"FAIL: configs.gates字段缺失")
            sys.exit(0)

        if not rubric_path:
            print(f"FAIL: configs.rubric字段缺失")
            sys.exit(0)

        # 如果是相对路径，基于SSOT文件所在目录解析
        ssot_dir = os.path.dirname(os.path.abspath(ssot_file))

        # 如果相对路径以 "Doc/" 开头，说明是基于项目根目录的路径
        # 向上查找到 Doc/ 的父目录作为项目根目录
        if gates_path.startswith("Doc/") or rubric_path.startswith("Doc/"):
            # 从 ssot_file 向上查找，找到包含 "Doc" 目录的父目录
            current = ssot_dir
            while current != os.path.dirname(current):
                parent = os.path.dirname(current)
                if os.path.basename(current) == "Doc":
                    project_root = parent
                    break
                current = parent
            else:
                print(f"FAIL: 无法推导项目根目录（未找到Doc/目录的父目录）")
                sys.exit(0)

            gates_abs_path = gates_path if os.path.isabs(gates_path) else os.path.join(project_root, gates_path)
            rubric_abs_path = rubric_path if os.path.isabs(rubric_path) else os.path.join(project_root, rubric_path)
        else:
            # 否则基于SSOT文件所在目录解析相对路径
            gates_abs_path = gates_path if os.path.isabs(gates_path) else os.path.join(ssot_dir, gates_path)
            rubric_abs_path = rubric_path if os.path.isabs(rubric_path) else os.path.join(ssot_dir, rubric_path)

        if not os.path.exists(gates_abs_path):
            print(f"FAIL: configs.gates路径无效: {gates_path} (resolved: {gates_abs_path})")
            sys.exit(0)

        if not os.path.exists(rubric_abs_path):
            print(f"FAIL: configs.rubric路径无效: {rubric_path} (resolved: {rubric_abs_path})")
            sys.exit(0)

        print(f"PASS: configs路径有效（gates: {gates_path}, rubric: {rubric_path}）")
        sys.exit(0)

    except FileNotFoundError:
        print(f"FAIL: 文件不存在: {ssot_file}")
        sys.exit(0)
    except yaml.YAMLError as e:
        print(f"FAIL: YAML解析失败: {e}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
