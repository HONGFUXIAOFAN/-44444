"""
YAML工具函数，处理多文档YAML文件
"""

import yaml
import os


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


def load_yaml_config(filepath):
    """
    加载YAML配置文件，自动处理多文档格式

    规则：
    - 如果第一个文档只包含元数据字段（rule_id, version, description, changelog），则跳过该文档
    - 合并所有非元数据文档的内容
    - 返回合并后的配置
    - 自动解析相对路径（相对于项目根目录）

    Args:
        filepath: YAML文件路径（支持绝对路径和相对路径）

    Returns:
        dict: 配置数据

    Raises:
        ValueError: YAML文件为空
        FileNotFoundError: 文件不存在
    """
    # 如果是相对路径，基于项目根目录解析
    if not os.path.isabs(filepath):
        project_root = find_project_root(__file__)
        if project_root:
            filepath = os.path.join(project_root, filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))

    if not docs:
        raise ValueError("YAML文件为空")

    # 元数据字段
    metadata_keys = {'rule_id', 'version', 'description', 'changelog'}

    # 合并所有配置文档（跳过纯元数据文档）
    merged = {}
    for doc in docs:
        if isinstance(doc, dict):
            # 如果不是纯元数据文档，合并进结果
            if not set(doc.keys()).issubset(metadata_keys):
                merged.update(doc)

    # 如果没有配置文档，返回第一个文档（兼容旧格式）
    return merged if merged else docs[0]
