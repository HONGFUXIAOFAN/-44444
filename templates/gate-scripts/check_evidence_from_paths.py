#!/usr/bin/env python3
"""
检查gates.yaml和rubric.yaml中的evidence_from路径是否可定位

Usage:
    python3 check_evidence_from_paths.py <gates_file> <rubric_file>

Example:
    python3 check_evidence_from_paths.py gates.yaml rubric.yaml

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import os
import re

# 添加当前目录到Python路径，以便导入_yaml_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _yaml_utils import load_yaml_config

def derive_placeholders_from_gates_path(gates_file: str):
    """根据 gates.yaml 路径推导占位符 {domain}/{rule-id}（推荐）。

    兼容历史占位符 [deliverable-id]/[rule-id]/[domain]，但已统一使用 {rule-id}/{domain}。
    期望路径：Doc/ops/{domain}/{rule-id}-gates.yaml，其中 {domain} 可为多级路径（如 system/rule-generator-v1）。
    """
    norm = gates_file.replace('\\\\', '/')
    try:
        prefix = 'Doc/ops/'
        if prefix in norm:
            after = norm.split(prefix, 1)[1]
            parts = after.split('/')
            domain = '/'.join(parts[:-1])  # 可能为多级
            filename = parts[-1]
            if filename.endswith('-gates.yaml'):
                deliverable_id = filename[:-len('-gates.yaml')]
            else:
                deliverable_id = os.path.splitext(filename)[0]
            # 约定：[rule-id] 等同于完整的可交付ID（如 "001-ssot-generation"），
            # 不再截取仅数字前缀；如需纯数字可后续引入 [rule-num]
            rule_id = deliverable_id
            return domain, deliverable_id, rule_id
    except Exception:
        pass
    return None, None, None

def substitute_placeholders(val, domain: str, deliverable_id: str, rule_id: str):
    """将字符串或字符串列表中的占位符替换为实际值"""
    def sub_one(s: str) -> str:
        out = s
        if domain:
            out = out.replace('[domain]', domain).replace('{domain}', domain)
        if deliverable_id:
            out = out.replace('[deliverable-id]', deliverable_id).replace('{deliverable-id}', deliverable_id)
        if rule_id:
            out = out.replace('[rule-id]', rule_id).replace('{rule-id}', rule_id)
        return out

    if isinstance(val, str):
        return sub_one(val)
    if isinstance(val, list):
        return [sub_one(x) if isinstance(x, str) else x for x in val]
    return val

def check_evidence_value(val, where, invalid_paths, project_root):
    """检查单个evidence_from值（支持字符串或字符串数组）"""
    if isinstance(val, str):
        matches = [val]
    elif isinstance(val, list):
        matches = [s for s in val if isinstance(s, str)]
    else:
        return

    for s in matches:
        # 格式：<文件路径>:<锚点>
        match = re.match(r'^(.+?)(?::(.+))?$', s)
        if match:
            file_path = match.group(1)
            # 如果是相对路径，基于项目根目录解析
            abs_path = file_path if os.path.isabs(file_path) else os.path.join(project_root, file_path)
            if not os.path.exists(abs_path):
                invalid_paths.append((where, s, "文件不存在"))

def extract_evidence_from(obj, path, invalid_paths, project_root, domain, deliverable_id, rule_id):
    """递归提取所有evidence_from字段"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "evidence_from":
                v = substitute_placeholders(v, domain, deliverable_id, rule_id)
                check_evidence_value(v, path + "." + str(k), invalid_paths, project_root)
            extract_evidence_from(v, path + "." + str(k), invalid_paths, project_root, domain, deliverable_id, rule_id)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_evidence_from(item, path + f"[{i}]", invalid_paths, project_root, domain, deliverable_id, rule_id)

def main():
    if len(sys.argv) < 3:
        print("FAIL: 缺少参数，用法: check_evidence_from_paths.py <gates_file> <rubric_file>")
        sys.exit(0)

    gates_file = sys.argv[1]
    rubric_file = sys.argv[2]

    try:
        # 读取gates.yaml和rubric.yaml
        gates = load_yaml_config(gates_file)
        rubric = load_yaml_config(rubric_file)

        # 推导项目根目录
        def find_project_root(start_path):
            current = os.path.dirname(os.path.abspath(start_path))
            while current != os.path.dirname(current):
                # 检查是否同时存在Doc/templates和Doc/rules
                templates_path = os.path.join(current, 'Doc', 'templates')
                rules_path = os.path.join(current, 'Doc', 'rules')
                if os.path.isdir(templates_path) and os.path.isdir(rules_path):
                    return current
                current = os.path.dirname(current)
            return None

        project_root = find_project_root(gates_file)
        if not project_root:
            print(f"FAIL: 无法推导项目根目录（未找到Doc/目录）")
            sys.exit(0)

        invalid_paths = []

        # 提取所有evidence_from字段（支持占位符替换）
        domain, deliverable_id, rule_id = derive_placeholders_from_gates_path(gates_file)
        extract_evidence_from(gates, "gates", invalid_paths, project_root, domain, deliverable_id, rule_id)
        extract_evidence_from(rubric, "rubric", invalid_paths, project_root, domain, deliverable_id, rule_id)

        if len(invalid_paths) > 0:
            error_msg = "\n".join([f"{p[0]}: {p[1]} ({p[2]})" for p in invalid_paths[:5]])
            print(f"FAIL: 发现{len(invalid_paths)}个无效evidence_from路径:\n{error_msg}")
            sys.exit(0)

        print(f"PASS: 所有evidence_from路径有效")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"FAIL: 文件不存在: {e.filename if hasattr(e, 'filename') else gates_file}")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: 未知错误: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
