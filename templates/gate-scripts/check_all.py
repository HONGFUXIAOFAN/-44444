#!/usr/bin/env python3
"""
通用YAML验证脚本，支持多种检查类型

Usage:
    python3 check_all.py <check_type> <args...>

Supported check_types:
    rubric_weight_sum <rubric_file> <tolerance>
    required_gates <gates_file>
    yaml_structure <yaml_file> <required_keys>
    configs_paths <ssot_file>
    evidence_from_paths <gates_file> <rubric_file>

Output:
    PASS: <message> 或 FAIL: <message>
"""

import sys
import yaml
import re
import os

def load_yaml_config(filepath):
    """加载YAML配置，自动处理多文档格式，合并所有配置文档"""
    with open(filepath, 'r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))
    
    if not docs:
        raise ValueError("YAML文件为空")
    
    # 合并所有配置文档（跳过纯元数据文档）
    merged = {}
    metadata_keys = {'rule_id', 'version', 'description', 'changelog'}
    
    for doc in docs:
        if isinstance(doc, dict):
            # 如果不是纯元数据文档，合并进结果
            if not set(doc.keys()).issubset(metadata_keys):
                merged.update(doc)
    
    return merged if merged else docs[0]

def check_rubric_weight_sum(rubric_file, tolerance):
    """检查Rubric权重总和"""
    config = load_yaml_config(rubric_file)
    rubric = config.get("rubric", [])
    
    if not rubric:
        return False, f"{rubric_file}中rubric数组为空"
    
    total_weight = sum([d.get("weight", 0.0) for d in rubric if "weight" in d])
    min_threshold = 1.0 - float(tolerance)
    max_threshold = 1.0 + float(tolerance)
    
    if total_weight < min_threshold or total_weight > max_threshold:
        return False, f"Rubric权重总和异常: {total_weight:.2f}（应在{min_threshold:.2f}-{max_threshold:.2f}范围）"
    
    return True, f"Rubric权重总和正常: {total_weight:.2f}"

def check_required_gates(gates_file):
    """检查必需Gates存在"""
    config = load_yaml_config(gates_file)
    gates = config.get("gates", [])
    gate_ids = [g.get("id") for g in gates if "id" in g]
    
    missing_gates = []
    if "gate0" not in gate_ids:
        missing_gates.append("gate0 (资产存在性检查)")
    if "gate1" not in gate_ids:
        missing_gates.append("gate1 (Schema有效性检查)")
    
    if missing_gates:
        return False, f"缺少必需Gate: {', '.join(missing_gates)}"
    
    return True, "gates.yaml包含所有必需Gate（gate0和gate1）"

def check_yaml_structure(yaml_file, required_keys_str):
    """检查YAML结构"""
    config = load_yaml_config(yaml_file)
    required_keys = [k.strip() for k in required_keys_str.split(',')]
    
    missing_keys = [k for k in required_keys if k not in config]
    
    if missing_keys:
        return False, f"{yaml_file}缺少必需顶层键: {', '.join(missing_keys)}"
    
    return True, f"{yaml_file}包含所有必需顶层键: {', '.join(required_keys)}"

def check_configs_paths(ssot_file):
    """检查configs路径有效性"""
    with open(ssot_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取YAML前置元数据
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return False, "SSOT文档YAML头解析失败"
    
    frontmatter = yaml.safe_load(match.group(1))
    
    if "configs" not in frontmatter:
        return False, "SSOT文档YAML头缺少configs字段"
    
    configs = frontmatter["configs"]
    gates_path = configs.get("gates")
    rubric_path = configs.get("rubric")
    
    if not gates_path:
        return False, "configs.gates字段缺失"
    if not rubric_path:
        return False, "configs.rubric字段缺失"
    if not os.path.exists(gates_path):
        return False, f"configs.gates路径无效: {gates_path}"
    if not os.path.exists(rubric_path):
        return False, f"configs.rubric路径无效: {rubric_path}"
    
    return True, f"configs路径有效（gates: {gates_path}, rubric: {rubric_path}）"

def check_evidence_from_paths(gates_file, rubric_file):
    """检查evidence_from路径有效性"""
    gates = load_yaml_config(gates_file)
    rubric = load_yaml_config(rubric_file)
    
    invalid_paths = []
    
    def check_value(val, where):
        if isinstance(val, str):
            matches = [val]
        elif isinstance(val, list):
            matches = [s for s in val if isinstance(s, str)]
        else:
            return
        
        for s in matches:
            match = re.match(r'^(.+?)(?::(.+))?$', s)
            if match:
                file_path = match.group(1)
                if not os.path.exists(file_path):
                    invalid_paths.append((where, s, "文件不存在"))
    
    def extract(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "evidence_from":
                    check_value(v, path + "." + str(k))
                extract(v, path + "." + str(k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract(item, path + f"[{i}]")
    
    extract(gates, "gates")
    extract(rubric, "rubric")
    
    if invalid_paths:
        error_msg = "\n".join([f"{p[0]}: {p[1]} ({p[2]})" for p in invalid_paths[:5]])
        return False, f"发现{len(invalid_paths)}个无效evidence_from路径:\n{error_msg}"
    
    return True, "所有evidence_from路径有效"

def main():
    if len(sys.argv) < 2:
        print("FAIL: 缺少参数，用法: check_all.py <check_type> <args...>")
        sys.exit(0)
    
    check_type = sys.argv[1]
    
    try:
        if check_type == "rubric_weight_sum" and len(sys.argv) >= 4:
            passed, msg = check_rubric_weight_sum(sys.argv[2], sys.argv[3])
        elif check_type == "required_gates" and len(sys.argv) >= 3:
            passed, msg = check_required_gates(sys.argv[2])
        elif check_type == "yaml_structure" and len(sys.argv) >= 4:
            passed, msg = check_yaml_structure(sys.argv[2], sys.argv[3])
        elif check_type == "configs_paths" and len(sys.argv) >= 3:
            passed, msg = check_configs_paths(sys.argv[2])
        elif check_type == "evidence_from_paths" and len(sys.argv) >= 4:
            passed, msg = check_evidence_from_paths(sys.argv[2], sys.argv[3])
        else:
            print(f"FAIL: 不支持的检查类型或参数不足: {check_type}")
            sys.exit(0)
        
        if passed:
            print(f"PASS: {msg}")
        else:
            print(f"FAIL: {msg}")
        sys.exit(0)
    
    except Exception as e:
        import traceback
        print(f"FAIL: 未知错误: {e}")
        traceback.print_exc()
        sys.exit(0)

if __name__ == "__main__":
    main()
