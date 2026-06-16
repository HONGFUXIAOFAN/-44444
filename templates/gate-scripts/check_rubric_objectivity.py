#!/usr/bin/env python3
"""
检查Rubric配置文件中的主观描述词

用途：扫描*-rubric.yaml文件，检测levels定义中的主观描述词，生成报告

输出：JSON格式的检测结果到stdout或指定文件
退出码：0=无问题，1=发现主观描述，2=错误
"""

import sys
import re
import yaml
import json
from pathlib import Path
from typing import List, Dict, Tuple

# 主观描述词关键词列表
SUBJECTIVE_KEYWORDS = [
    "非常", "较", "基本", "完全", "明显", "适当", "清晰", "充分",
    "很", "极", "相当", "略", "稍", "有点", "比较", "十分",
    "高度", "良好", "优秀", "较好", "较差", "一般", "普通",
    "简洁", "详细", "丰富", "全面", "完整", "准确", "精确"
]

def check_rubric_file(rubric_path: Path) -> Tuple[bool, List[Dict]]:
    """
    检查单个rubric.yaml文件

    返回：(有主观描述, 发现列表)
    """
    try:
        with open(rubric_path, 'r', encoding='utf-8') as f:
            docs = list(yaml.safe_load_all(f))
            config = docs[-1] if len(docs) > 1 else docs[0]

        findings = []

        if 'rubric' not in config:
            return False, []

        for dimension in config['rubric']:
            dimension_name = dimension.get('name', 'unknown')

            if 'checks' not in dimension:
                continue

            for check in dimension['checks']:
                check_id = check.get('id', 'unknown')
                check_desc = check.get('desc', '')

                if 'levels' not in check:
                    continue

                levels = check['levels']
                for level_name in ['excellent', 'good', 'acceptable', 'poor']:
                    if level_name not in levels:
                        continue

                    level_text = levels[level_name]

                    # 检查主观描述词
                    for keyword in SUBJECTIVE_KEYWORDS:
                        if keyword in level_text:
                            findings.append({
                                'file': str(rubric_path),
                                'dimension': dimension_name,
                                'check_id': check_id,
                                'check_desc': check_desc,
                                'level': level_name,
                                'level_text': level_text,
                                'keyword': keyword,
                                'line_approx': f"dimension={dimension_name}, check={check_id}"
                            })

        return len(findings) > 0, findings

    except Exception as e:
        print(f"Error processing {rubric_path}: {e}", file=sys.stderr)
        return False, []

def scan_directory(base_dir: Path) -> Dict:
    """扫描目录下所有*-rubric.yaml文件"""
    results = {
        'total_files': 0,
        'files_with_issues': 0,
        'total_findings': 0,
        'files': []
    }

    for rubric_path in base_dir.rglob('*-rubric.yaml'):
        # 跳过tmp目录
        if '/tmp/' in str(rubric_path):
            continue

        results['total_files'] += 1
        has_issues, findings = check_rubric_file(rubric_path)

        if has_issues:
            results['files_with_issues'] += 1
            results['total_findings'] += len(findings)
            results['files'].append({
                'path': str(rubric_path.relative_to(base_dir)),
                'findings_count': len(findings),
                'findings': findings
            })

    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python check_rubric_objectivity.py <rubric-file-or-directory> [--output <json-file>]")
        print("Examples:")
        print("  python check_rubric_objectivity.py Doc/ops/system/rule-generator-v1/001-ssot-generation-rubric.yaml")
        print("  python check_rubric_objectivity.py Doc/ops --output /tmp/subjective_checks.json")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_file = None

    if '--output' in sys.argv:
        output_index = sys.argv.index('--output')
        if output_index + 1 < len(sys.argv):
            output_file = Path(sys.argv[output_index + 1])

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    # 扫描
    if input_path.is_file():
        has_issues, findings = check_rubric_file(input_path)
        results = {
            'total_files': 1,
            'files_with_issues': 1 if has_issues else 0,
            'total_findings': len(findings),
            'files': [{
                'path': str(input_path),
                'findings_count': len(findings),
                'findings': findings
            }] if has_issues else []
        }
    else:
        results = scan_directory(input_path)

    # 输出结果
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results written to {output_file}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    # 返回退出码
    if results['total_findings'] > 0:
        print(f"\n❌ Found {results['total_findings']} subjective descriptions in {results['files_with_issues']}/{results['total_files']} files", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ No subjective descriptions found in {results['total_files']} files", file=sys.stderr)
        sys.exit(0)

if __name__ == '__main__':
    main()
