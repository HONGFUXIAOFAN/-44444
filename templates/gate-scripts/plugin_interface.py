#!/usr/bin/env python3
"""
Gate插件接口定义

所有自定义Gate插件必须实现此接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class GatePlugin(ABC):
    """Gate插件基类"""

    @abstractmethod
    def get_gate_ids(self) -> List[str]:
        """
        返回此插件支持的Gate ID列表

        Returns:
            Gate ID列表，如 ["gate7_eval_dataset", "gate9_eval_dataset"]
        """
        pass

    @abstractmethod
    def check(self, gate_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Gate检查

        Args:
            gate_config: Gate配置字典，包含id、name、checks等字段
            context: 上下文信息，包含project_root、deliverable_path等

        Returns:
            检查结果字典:
            {
                "passed": bool,          # 是否通过
                "details": str,          # 详细信息
                "checks": [              # 各个check的结果（可选）
                    {
                        "type": str,
                        "passed": bool,
                        "details": str
                    }
                ]
            }
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        返回插件元数据

        Returns:
            元数据字典:
            {
                "name": str,             # 插件名称
                "version": str,          # 版本号
                "description": str,      # 描述
                "author": str,           # 作者（可选）
            }
        """
        pass


class PluginRegistry:
    """插件注册表"""

    def __init__(self):
        self.plugins: Dict[str, GatePlugin] = {}  # gate_id -> plugin
        self.metadata: Dict[str, Dict] = {}       # plugin_name -> metadata

    def register(self, plugin: GatePlugin):
        """
        注册插件

        Args:
            plugin: GatePlugin实例
        """
        metadata = plugin.get_metadata()
        plugin_name = metadata['name']

        # 记录元数据
        self.metadata[plugin_name] = metadata

        # 注册Gate ID映射
        for gate_id in plugin.get_gate_ids():
            if gate_id in self.plugins:
                existing_plugin = self.plugins[gate_id].get_metadata()['name']
                print(f"⚠️  警告: Gate ID '{gate_id}' 已被插件 '{existing_plugin}' 注册，将被 '{plugin_name}' 覆盖")
            self.plugins[gate_id] = plugin

    def get_plugin(self, gate_id: str) -> GatePlugin:
        """
        获取处理指定Gate ID的插件

        Args:
            gate_id: Gate ID

        Returns:
            GatePlugin实例，如果未找到返回None
        """
        return self.plugins.get(gate_id)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的插件

        Returns:
            插件元数据列表
        """
        return list(self.metadata.values())

    def list_gate_ids(self) -> List[str]:
        """
        列出所有已注册的Gate ID

        Returns:
            Gate ID列表
        """
        return list(self.plugins.keys())
