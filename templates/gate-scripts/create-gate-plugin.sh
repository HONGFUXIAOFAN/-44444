#!/bin/bash
# Gate插件模板生成器
#
# 用法: ./create-gate-plugin.sh <gate_id>
# 示例: ./create-gate-plugin.sh gate11_custom_logic

set -e

if [ $# -eq 0 ]; then
    echo "用法: $0 <gate_id>"
    echo "示例: $0 gate11_custom_logic"
    exit 1
fi

GATE_ID=$1
# 提取gate_后的部分作为文件名
GATE_NAME=$(echo "$GATE_ID" | sed 's/gate[0-9]*_//')
PLUGIN_FILE="$(dirname "$0")/plugins/gate_${GATE_NAME}.py"

# 检查文件是否已存在
if [ -f "$PLUGIN_FILE" ]; then
    echo "❌ 插件文件已存在: $PLUGIN_FILE"
    echo "请先删除现有文件或使用其他名称"
    exit 1
fi

# 生成插件代码
cat > "$PLUGIN_FILE" << 'EOF'
#!/usr/bin/env python3
"""
{GATE_NAME_UPPER}检查插件

支持的Gate IDs:
- {GATE_ID}
"""

import os
import sys

# 添加父目录到路径以导入plugin_interface
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugin_interface import GatePlugin
from typing import Dict, Any, List


class {CLASS_NAME}Plugin(GatePlugin):
    """{GATE_NAME_UPPER}检查插件"""

    def get_gate_ids(self) -> List[str]:
        return ["{GATE_ID}"]

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "{GATE_NAME}_checker",
            "version": "1.0.0",
            "description": "{GATE_NAME_UPPER}检查",
            "author": "Administrator"
        }

    def check(self, gate_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行{GATE_NAME_UPPER}检查

        Args:
            gate_config: Gate配置字典
            context: 上下文信息（包含project_root、deliverable_path等）

        Returns:
            检查结果字典
        """
        # 获取检查参数
        checks_config = gate_config.get('checks', [])
        if not checks_config:
            return {"passed": False, "details": "缺少checks配置"}

        check = checks_config[0]
        params = check.get('params', {})

        # TODO: 实现你的检查逻辑
        # 示例：检查文件存在性
        # file_path = params.get('p1', '')
        # if not os.path.exists(file_path):
        #     return {"passed": False, "details": f"文件不存在: {file_path}"}

        # TODO: 返回检查结果
        return {
            "passed": True,
            "details": "TODO: 实现检查逻辑"
        }
EOF

# 替换占位符
GATE_NAME_UPPER=$(echo "$GATE_NAME" | tr '[:lower:]' '[:upper:]' | tr '_' ' ')
CLASS_NAME=$(echo "$GATE_NAME" | sed -E 's/(^|_)([a-z])/\U\2/g')

sed -i '' "s/{GATE_NAME}/$GATE_NAME/g" "$PLUGIN_FILE"
sed -i '' "s/{GATE_NAME_UPPER}/$GATE_NAME_UPPER/g" "$PLUGIN_FILE"
sed -i '' "s/{GATE_ID}/$GATE_ID/g" "$PLUGIN_FILE"
sed -i '' "s/{CLASS_NAME}/$CLASS_NAME/g" "$PLUGIN_FILE"

chmod +x "$PLUGIN_FILE"

echo "✅ 插件模板已创建: $PLUGIN_FILE"
echo ""
echo "下一步:"
echo "1. 编辑插件文件，实现check()方法"
echo "2. 测试插件: python3 unified_gate_checker.py --gates-yaml <path> --deliverable <path>"
echo "3. 插件将自动被unified_gate_checker.py加载"
