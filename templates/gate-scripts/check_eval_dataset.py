#!/usr/bin/env python3
"""
检查评测数据集目录结构和最小配置要求

用途：
    验证SSOT的评测数据集是否满足最小配置要求：
    - pass/ 目录存在且包含至少3个Golden案例
    - fail/、edge/、regression/ 目录存在（可为空）

输入：
    python3 check_eval_dataset.py <eval_dir>
    - eval_dir: 评测数据集根目录，如 Doc/eval/system/rule-generator-v1/001

输出：
    - PASS: 评测数据集满足最小配置（pass/目录含N个案例）
    - FAIL: 具体问题说明

示例：
    python3 check_eval_dataset.py Doc/eval/system/rule-generator-v1/001
"""

import os
import sys


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


def has_files(directory):
    """检查目录下是否包含文件（递归检查）"""
    if not os.path.isdir(directory):
        return False

    try:
        for root, dirs, files in os.walk(directory):
            # 过滤掉隐藏文件
            files = [f for f in files if not f.startswith('.')]
            if len(files) > 0:
                return True
    except PermissionError:
        return False

    return False


def check_case_directories(directory):
    """
    检查案例目录并返回统计信息

    Returns:
        (total_cases, valid_cases, empty_cases): 总案例数、有效案例数、空案例列表
    """
    if not os.path.isdir(directory):
        return 0, 0, []

    total_cases = 0
    valid_cases = 0
    empty_cases = []

    try:
        for item in os.listdir(directory):
            # 跳过隐藏目录
            if item.startswith('.'):
                continue
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                total_cases += 1
                if has_files(item_path):
                    valid_cases += 1
                else:
                    empty_cases.append(item)
    except PermissionError:
        return 0, 0, []

    return total_cases, valid_cases, empty_cases


def main():
    if len(sys.argv) < 2:
        print("FAIL: 未提供评测数据集目录参数")
        sys.exit(0)

    eval_dir = sys.argv[1]

    # 如果是相对路径，基于项目根目录解析
    if not os.path.isabs(eval_dir):
        project_root = find_project_root(__file__)
        if project_root:
            eval_dir = os.path.join(project_root, eval_dir)

    # 检查评测数据集根目录是否存在；若不存在，尝试 Doc/eval 与 eval 根路径的兼容切换
    def try_alt_roots(path: str) -> str:
        # 优先尝试将 Doc/eval ↔ eval 互换，以兼容两种仓库布局
        if path.startswith('Doc/eval/'):
            candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), path.replace('Doc/eval/', 'eval/', 1))
            if os.path.exists(candidate):
                return candidate
        elif path.startswith('eval/'):
            candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), path.replace('eval/', 'Doc/eval/', 1))
            if os.path.exists(candidate):
                return candidate
        return path

    if not os.path.exists(eval_dir):
        alt = try_alt_roots(sys.argv[1] if os.path.isabs(sys.argv[1]) else eval_dir)
        if os.path.exists(alt):
            eval_dir = alt
        else:
            print(f"FAIL: 评测数据集目录不存在: {sys.argv[1]} (resolved: {eval_dir})")
            sys.exit(0)

    if not os.path.isdir(eval_dir):
        print(f"FAIL: 路径不是目录: {eval_dir}")
        sys.exit(0)

    # 检查必需的子目录结构
    required_dirs = {
        'pass': '必需，至少3个Golden案例',
        'fail': '可选，Adversarial案例',
        'edge': '可选，Edge案例',
        'regression': '可选，Regression案例'
    }

    issues = []
    pass_dir = os.path.join(eval_dir, 'pass')

    # 检查 pass/ 目录（必需）
    if not os.path.isdir(pass_dir):
        issues.append("缺少 pass/ 目录（Golden案例，必需）")
    else:
        # 统计 Golden 案例数量和有效性
        total_cases, valid_cases, empty_cases = check_case_directories(pass_dir)
        if total_cases < 3:
            issues.append(f"pass/ 目录案例不足: 仅 {total_cases} 个（最小要求3个）")
        elif valid_cases < 3:
            issues.append(f"pass/ 目录有效案例不足: {valid_cases}/{total_cases} 个有文件（最小要求3个）")
            if len(empty_cases) > 0:
                issues.append(f"  空目录: {', '.join(empty_cases[:5])}{'...' if len(empty_cases) > 5 else ''}")

    # 检查其他目录（可选，但需要存在）
    optional_dirs = ['fail', 'edge', 'regression']
    missing_optional = []

    for dir_name in optional_dirs:
        dir_path = os.path.join(eval_dir, dir_name)
        if not os.path.exists(dir_path):
            missing_optional.append(dir_name)

    # 输出结果
    if len(issues) > 0:
        print(f"FAIL: 评测数据集不满足最小配置:")
        for issue in issues:
            print(f"  - {issue}")
        if len(missing_optional) > 0:
            print(f"  提示: 缺少可选目录 {', '.join(missing_optional)}/ (可在迭代时补充)")
        sys.exit(0)

    # 通过检查
    total_golden, valid_golden, _ = check_case_directories(pass_dir)
    optional_status = []

    for dir_name in optional_dirs:
        dir_path = os.path.join(eval_dir, dir_name)
        if os.path.isdir(dir_path):
            total, valid, _ = check_case_directories(dir_path)
            optional_status.append(f"{dir_name}={valid}/{total}")
        else:
            optional_status.append(f"{dir_name}=缺失")

    print(f"PASS: 评测数据集满足最小配置 (pass={valid_golden}/{total_golden}, {', '.join(optional_status)})")
    sys.exit(0)


if __name__ == "__main__":
    main()
