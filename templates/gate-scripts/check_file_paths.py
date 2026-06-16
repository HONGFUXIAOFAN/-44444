#!/usr/bin/env python3
"""
检查指定文件路径是否存在，并提供智能排错建议

用途：
    验证给定的一个或多个文件路径是否在文件系统中存在
    当文件不存在时，自动检测可能的路径错误并提供修正建议

输入：
    python3 check_file_paths.py <path1> [path2] [path3] ...
    - 支持相对路径（基于项目根目录）
    - 支持绝对路径

输出：
    - PASS: 所有文件存在
    - FAIL: 列出不存在的文件路径，并提供可能的修正建议

示例：
    python3 check_file_paths.py Doc/ssot/system/rule-generator-v1/001-ssot-generation-ssot.md
    python3 check_file_paths.py Doc/ops/system/rule-generator-v1/001-ssot-generation-gates.yaml Doc/ops/system/rule-generator-v1/001-ssot-generation-rubric.yaml
"""

import os
import sys
import glob
from pathlib import Path


def find_project_root(start_path):
    """
    查找项目根目录（包含 Doc/templates 和 Doc/rules 的目录）

    Args:
        start_path: 起始搜索路径

    Returns:
        项目根目录绝对路径，如果未找到则返回 None
    """
    current = os.path.dirname(os.path.abspath(start_path))
    while current != os.path.dirname(current):  # 未到达文件系统根目录
        # 检查是否存在 Doc/templates 和 Doc/rules 目录
        templates_path = os.path.join(current, 'Doc', 'templates')
        rules_path = os.path.join(current, 'Doc', 'rules')
        if os.path.isdir(templates_path) and os.path.isdir(rules_path):
            return current
        current = os.path.dirname(current)
    return None


def find_similar_paths(project_root, missing_path):
    """
    查找与缺失路径相似的现有路径，提供修正建议

    策略：
    1. 检查常见的路径模式错误（domain-overviews vs rules）
    2. 检查文件名是否存在于其他目录
    3. 检查目录结构是否正确

    Args:
        project_root: 项目根目录
        missing_path: 缺失的路径

    Returns:
        建议列表，每个建议是一个字典 {"type": "类型", "suggestion": "建议", "path": "路径"}
    """
    suggestions = []
    path_parts = Path(missing_path).parts
    filename = Path(missing_path).name

    # 策略1: 检查Doc二级路径是否合法（只允许 ops/ssot/rules/eval/templates）
    VALID_DOC_SUBDIRS = ["ops", "ssot", "rules", "eval", "templates"]

    if missing_path.startswith("Doc/"):
        parts = missing_path.split("/")
        if len(parts) >= 2:
            second_level = parts[1]

            # 检查是否是非法的二级路径
            if second_level not in VALID_DOC_SUBDIRS:
                suggestions.append({
                    "type": "非法Doc二级路径",
                    "suggestion": f"'{second_level}' 不是有效的Doc二级路径。合法路径只有: {', '.join(VALID_DOC_SUBDIRS)}",
                    "invalid_path": f"Doc/{second_level}/"
                })

                # 尝试猜测正确的路径（常见错误映射）
                path_corrections = {
                    "domain-overviews": "rules",  # domain-overviews 应该是 rules
                    "spec-driven-developer": "rules/spec-driven-developer",  # 直接跳过二级
                    "para-manager": "rules/para-manager",
                }

                if second_level in path_corrections:
                    corrected_second = path_corrections[second_level]
                    fixed_path = missing_path.replace(f"Doc/{second_level}/", f"Doc/{corrected_second}/", 1)
                    abs_fixed_path = os.path.join(project_root, fixed_path)
                    if os.path.exists(abs_fixed_path):
                        suggestions.append({
                            "type": "路径模式错误",
                            "suggestion": f"可能应该使用 Doc/{corrected_second}/ 而非 Doc/{second_level}/",
                            "path": fixed_path
                        })
                else:
                    # 尝试在合法的二级路径下查找
                    for valid_subdir in VALID_DOC_SUBDIRS:
                        # 重新组合路径：Doc/valid_subdir/原二级路径/剩余路径
                        if len(parts) >= 3:
                            # 将原二级路径作为三级路径
                            fixed_path = f"Doc/{valid_subdir}/{'/'.join(parts[1:])}"
                        else:
                            fixed_path = f"Doc/{valid_subdir}/{second_level}"

                        abs_fixed_path = os.path.join(project_root, fixed_path)
                        if os.path.exists(abs_fixed_path):
                            suggestions.append({
                                "type": "路径模式错误",
                                "suggestion": f"文件可能在 Doc/{valid_subdir}/ 下",
                                "path": fixed_path
                            })
                            break  # 找到一个就够了

    # 策略2: 在整个Doc目录下查找同名文件
    if len(suggestions) == 0 and filename:
        doc_root = os.path.join(project_root, "Doc")
        if os.path.exists(doc_root):
            # 使用glob递归查找同名文件
            pattern = f"**/{filename}"
            matching_files = []
            for match in glob.glob(os.path.join(doc_root, pattern), recursive=True):
                rel_path = os.path.relpath(match, project_root)
                matching_files.append(rel_path)

            if matching_files:
                suggestions.append({
                    "type": "文件名匹配",
                    "suggestion": f"找到 {len(matching_files)} 个同名文件",
                    "paths": matching_files[:5]  # 最多显示5个
                })

    # 策略3: 检查父目录是否存在
    parent_dir = str(Path(missing_path).parent)
    if parent_dir and parent_dir != ".":
        abs_parent = os.path.join(project_root, parent_dir)
        if not os.path.exists(abs_parent):
            suggestions.append({
                "type": "父目录不存在",
                "suggestion": f"父目录 {parent_dir} 不存在，可能需要创建",
                "path": parent_dir
            })
        else:
            # 父目录存在，列出其中的文件
            try:
                existing_files = os.listdir(abs_parent)
                if existing_files:
                    suggestions.append({
                        "type": "同目录文件",
                        "suggestion": f"父目录存在但文件不存在，目录中有 {len(existing_files)} 个其他文件",
                        "sample_files": existing_files[:3]
                    })
            except Exception:
                pass

    return suggestions


def main():
    if len(sys.argv) < 2:
        print("FAIL: 未提供文件路径参数")
        sys.exit(0)

    # 查找项目根目录
    project_root = find_project_root(__file__)
    if project_root is None:
        print("FAIL: 无法找到项目根目录（未找到包含 Doc/templates 和 Doc/rules 的目录）")
        sys.exit(0)

    # 检查所有路径
    paths_to_check = sys.argv[1:]
    missing_paths = []
    path_diagnostics = {}  # 存储每个缺失路径的诊断信息

    for path in paths_to_check:
        # 如果是相对路径，基于项目根目录解析
        if os.path.isabs(path):
            abs_path = path
        else:
            abs_path = os.path.join(project_root, path)

        if not os.path.exists(abs_path):
            missing_paths.append(path)
            # 查找可能的修正建议
            suggestions = find_similar_paths(project_root, path)
            if suggestions:
                path_diagnostics[path] = suggestions

    # 输出结果
    if len(missing_paths) == 0:
        print(f"PASS: 所有文件存在 ({len(paths_to_check)} 个)")
    else:
        print(f"FAIL: {len(missing_paths)} 个文件不存在:")
        for path in missing_paths:
            print(f"\n  ❌ {path}")

            # 输出排错建议
            if path in path_diagnostics:
                suggestions = path_diagnostics[path]
                print(f"     💡 排错建议:")
                for i, suggestion in enumerate(suggestions, 1):
                    suggestion_type = suggestion.get("type", "未知")
                    suggestion_text = suggestion.get("suggestion", "")

                    if suggestion_type == "非法Doc二级路径":
                        invalid_path = suggestion.get("invalid_path", "")
                        print(f"        {i}. ⚠️  {suggestion_text}")
                        print(f"           非法路径: {invalid_path}")

                    elif suggestion_type == "路径模式错误":
                        fixed_path = suggestion.get("path", "")
                        print(f"        {i}. {suggestion_text}")
                        print(f"           建议路径: {fixed_path}")

                    elif suggestion_type == "文件名匹配":
                        paths = suggestion.get("paths", [])
                        print(f"        {i}. {suggestion_text}:")
                        for match_path in paths:
                            print(f"           - {match_path}")

                    elif suggestion_type == "父目录不存在":
                        parent_path = suggestion.get("path", "")
                        print(f"        {i}. {suggestion_text}")
                        print(f"           父目录: {parent_path}")

                    elif suggestion_type == "同目录文件":
                        sample_files = suggestion.get("sample_files", [])
                        print(f"        {i}. {suggestion_text}")
                        if sample_files:
                            print(f"           示例文件: {', '.join(sample_files)}")
            else:
                print(f"     💡 未找到相似路径，请检查路径是否正确")


if __name__ == "__main__":
    main()
