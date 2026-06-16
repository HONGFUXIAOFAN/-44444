#!/usr/bin/env python3
"""
评测数据集检查插件

支持的Gate IDs:
- gate7_eval_dataset (001规则)
- gate9_eval_dataset (003规则)
"""

import os
import sys

# 添加父目录到路径以导入plugin_interface
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_interface import GatePlugin
from typing import Dict, Any, List, Tuple


class EvalDatasetPlugin(GatePlugin):
    """评测数据集检查插件"""

    def get_gate_ids(self) -> List[str]:
        return [
            "gate7_eval_dataset",  # 001规则
            "gate9_eval_dataset",  # 003规则
        ]

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "eval_dataset_checker",
            "version": "1.0.0",
            "description": "检查评测数据集目录结构和最小配置要求",
            "author": "Administrator"
        }

    def check(self, gate_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查评测数据集

        要求:
        - pass/ 目录存在且包含至少3个有效案例（包含文件的子目录）
        - fail/、edge/、regression/ 目录可选
        """
        # 获取评测数据集目录路径
        checks_config = gate_config.get('checks', [])
        if not checks_config:
            return {"passed": False, "details": "缺少checks配置"}

        check = checks_config[0]
        params = check.get('params', {})
        eval_dir = params.get('p1', '')

        # 替换占位符
        for placeholder, replacement in context.items():
            eval_dir = eval_dir.replace(f'{{{placeholder}}}', str(replacement))

        # 转换为绝对路径
        project_root = context.get('project_root', '')
        if not os.path.isabs(eval_dir):
            eval_dir = os.path.join(project_root, eval_dir)

        # 检查评测数据集目录是否存在
        if not os.path.exists(eval_dir):
            return {
                "passed": False,
                "details": f"评测数据集目录不存在: {eval_dir}"
            }

        # 检查pass/目录（必需）
        pass_dir = os.path.join(eval_dir, 'pass')
        if not os.path.isdir(pass_dir):
            return {
                "passed": False,
                "details": "缺少 pass/ 目录（Golden案例，必需）"
            }

        # 检查pass/目录的案例数量和有效性
        total_cases, valid_cases, empty_cases = self._check_case_directories(pass_dir)

        if valid_cases < 3:
            details = f"pass/ 目录有效案例不足: {valid_cases}/{total_cases} 个（最小要求3个）"
            if empty_cases:
                details += f"\n  空目录: {', '.join(empty_cases)}"
            return {
                "passed": False,
                "details": details
            }

        # 检查可选目录（fail/、edge/、regression/）
        optional_dirs = ['fail', 'edge', 'regression']
        optional_status = []
        for dir_name in optional_dirs:
            dir_path = os.path.join(eval_dir, dir_name)
            if os.path.isdir(dir_path):
                total, valid, _ = self._check_case_directories(dir_path)
                optional_status.append(f"{dir_name}={valid}/{total}")
            else:
                optional_status.append(f"{dir_name}=缺失")

        # 构建成功消息
        details = f"评测数据集满足最小配置 (pass={valid_cases}/{total_cases}"
        if optional_status:
            details += f", {', '.join(optional_status)}"
        details += ")"

        return {
            "passed": True,
            "details": details
        }

    def _has_files(self, directory: str) -> bool:
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

    def _check_case_directories(self, directory: str) -> Tuple[int, int, List[str]]:
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
                    if self._has_files(item_path):
                        valid_cases += 1
                    else:
                        empty_cases.append(item)
        except PermissionError:
            return 0, 0, []

        return total_cases, valid_cases, empty_cases
