#!/usr/bin/env python3
"""
检查规则文件的“输入”章节中引用的文件路径是否有效

Usage:
    python3 check_input_paths.py <rule_file>

Example:
    python3 check_input_paths.py Doc/rules/system/rule-generator-v1/003-rule.md

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import os
import re

# 添加当前目录到Python路径，以便导入_yaml_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yaml_utils import find_project_root


def extract_section(markdown_text: str, heading: str) -> str:
    """提取从 `### heading` 到下一个同级标题之间的文本（不含下一个标题）"""
    # 兼容带空格的标题，如 "### 输入"、"###  输入"
    pattern = rf"^###\s*{re.escape(heading)}\s*$"
    lines = markdown_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(pattern, line.strip()):
            start = i + 1
            break
    if start is None:
        return ""
    # 查找下一个以 ### 开头的同级标题
    end = len(lines)
    for i in range(start, len(lines)):
        if re.match(r"^###\s+", lines[i].strip()):
            end = i
            break
    return "\n".join(lines[start:end])


def find_paths(text: str):
    """在文本中查找形如 Doc/... 的文件路径（忽略 URL）"""
    # 捕获 Doc/ 开头直到空白或右括号结束的片段
    # 支持 Markdown 链接 [name](Doc/...) 或纯文本 Doc/...
    candidates = set()
    # Markdown 链接
    for m in re.finditer(r"\[[^\]]*\]\((Doc/[^)\s]+)\)", text):
        candidates.add(m.group(1))
    # 纯文本 Doc/...
    for m in re.finditer(r"(?<!\()\b(Doc/[A-Za-z0-9_./\-]+\.(md|yaml))\b", text):
        candidates.add(m.group(1))
    return sorted(candidates)


def main():
    if len(sys.argv) < 2:
        print("FAIL: 缺少参数，用法: check_input_paths.py <rule_file>")
        sys.exit(0)

    rule_file = sys.argv[1]

    # 解析项目根目录
    project_root = find_project_root(__file__)
    if not project_root:
        print("FAIL: 无法推导项目根目录（未找到Doc/目录）")
        sys.exit(0)

    # 解析规则文件路径
    rule_path = rule_file if os.path.isabs(rule_file) else os.path.join(project_root, rule_file)
    if not os.path.exists(rule_path):
        print(f"FAIL: 规则文件不存在: {rule_file}")
        sys.exit(0)

    # 读取规则文件
    with open(rule_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取“输入”章节
    input_text = extract_section(content, "输入")
    if not input_text.strip():
        print("FAIL: 未找到 ‘### 输入’ 章节或章节为空")
        sys.exit(0)

    # 查找路径并验证存在性
    paths = find_paths(input_text)
    if not paths:
        print("FAIL: 输入章节未发现任何 Doc/ 开头的路径引用")
        sys.exit(0)

    missing = []
    for p in paths:
        abs_p = p if os.path.isabs(p) else os.path.join(project_root, p)
        if not os.path.exists(abs_p):
            missing.append(p)

    if missing:
        print("FAIL: 输入章节存在无效路径:\n  - " + "\n  - ".join(missing))
        sys.exit(0)

    print(f"PASS: 输入章节路径有效（共 {len(paths)} 个）")
    sys.exit(0)


if __name__ == "__main__":
    main()

