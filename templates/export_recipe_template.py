#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出模板：餐饮配方方案 → Word (.docx)
==============================================
基于 031-export-word-pdf 规则的强制执行模板。
每次导出时填充内容数据，禁止从零编写导出脚本。

使用方式：
    from export_recipe_template import build_document, validate_config
    config = { ... }  # 填充配方内容数据
    errors = validate_config(config)
    if errors:
        raise ValueError(f"配置不完整: {errors}")
    output_path = build_document(config)
    print(f"✅ 已生成: {output_path}")

强制规范（031规则）：
    - 字体：封面28pt / h1 24pt / h2 20pt / 正文16pt / 表格14pt
    - 配色：表头 #C62828白字 / 行白底+#FFF0F0交替 / 正文 #333333
    - 表格：tblW=20cm / 列宽智能分配 / 单元格边距上下20dxa左右40dxa
    - 禁止：分页符 / AI生成字样 / 生成日期 / 生成工具
    - 免责声明：说明资料依据、未现场实测、添加剂安全和适用边界 / #FFFDE7底色 / #333333粗体16pt
    - 文件路径：~/Desktop/{菜品名}_{客户信息}_配方方案.docx
"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os
import re
import math

# ═══════════════════════════════════════════════
# 031 规则强制常量 —— 禁止修改
# ═══════════════════════════════════════════════

# 字体大小
FONT_COVER_TITLE = Pt(28)
FONT_H1 = Pt(24)
FONT_H2 = Pt(20)
FONT_BODY = Pt(16)
FONT_TABLE = Pt(14)
FONT_TABLE_NOTE = Pt(12)

# 颜色
COLOR_HEADER_BG = "C62828"        # 表头底色（暗红）
COLOR_HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)  # 表头字色（白）
COLOR_ROW_ODD = "FFFFFF"          # 奇数行底色（白）
COLOR_ROW_EVEN = "FFF0F0"         # 偶数行底色（浅粉）
COLOR_BODY = RGBColor(0x33, 0x33, 0x33)        # 正文色（深灰）
COLOR_EMPHASIS = RGBColor(0xC6, 0x28, 0x28)    # 强调色（暗红）
COLOR_DISCLAIMER_BG = "FFFDE7"    # 免责声明底色（浅黄）
COLOR_QUICK_CARD_BG = "FFF5F0"    # 速查卡底色（浅粉）

# 页面边距
PAGE_MARGIN = Cm(1.2)

# 表格
TABLE_TOTAL_WIDTH = Cm(20)        # 所有表格总宽 20cm（A4满宽）
CELL_PAD_TOP = 20                 # 单元格上内边距 (dxa)
CELL_PAD_BOTTOM = 20              # 单元格下内边距 (dxa)
CELL_PAD_LEFT = 40                # 单元格左内边距 (dxa)
CELL_PAD_RIGHT = 40               # 单元格右内边距 (dxa)

# 段落间距
PARA_SPACE_AFTER = Pt(2)
PARA_SPACE_BEFORE = Pt(0)
HEADING_SPACE_BEFORE = Pt(8)
HEADING_SPACE_AFTER = Pt(2)

# 免责声明固定内容（逐字输出，不可改动）
DISCLAIMER_TITLE = "⚠️ 重要提示（请务必阅读）"
DISCLAIMER_TEXT = (
    "本方案依据公开研究、行业资料及可核实的供应商技术资料制定。\n"
    "本方案尚未在该门店进行现场风味实测；预期效果属于有依据的设计判断，不应视为已实测结论。\n"
    "食品添加剂须按适用食品类别、现行法规及供应商技术资料使用，不得超范围或超量使用。\n"
    "实际风味可能受原料批次、设备、汤量和操作条件影响；本方案提供具体参数与适用边界。"
)

# 字体名称
FONT_NAME = "微软雅黑"

# 文档结构（10模块强制顺序）
MODULE_ORDER = [
    "封面",
    "重要提示/免责声明",
    "配方参数表（A版与B版）",
    "A/B测试方案与比较标准",
    "标准化操作流程",
    "保存方法详解",
    "通俗原理",
    "添加剂安全清单",
    "地域适配建议",
    "厨房速查卡",
]


# ═══════════════════════════════════════════════
# 基础工具函数
# ═══════════════════════════════════════════════

def _set_run_font(run, size, bold=False, color=None, font_name=FONT_NAME):
    """统一设置 run 的字体属性"""
    run.bold = bold
    run.font.size = size
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    if color:
        run.font.color.rgb = color


def _set_cell_bg(cell, color):
    """设置单元格底色"""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_cell_margins(cell):
    """设置单元格内边距：上下20dxa，左右40dxa"""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{CELL_PAD_TOP}" w:type="dxa"/>'
        f'<w:bottom w:w="{CELL_PAD_BOTTOM}" w:type="dxa"/>'
        f'<w:left w:w="{CELL_PAD_LEFT}" w:type="dxa"/>'
        f'<w:right w:w="{CELL_PAD_RIGHT}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def _set_cell_text(cell, text, bold=False, size=FONT_TABLE, color=None,
                   align=None, font_name=FONT_NAME):
    """设置单元格文本"""
    for p in cell.paragraphs:
        p.clear()
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    if align is not None:
        p.alignment = align
    run = p.add_run(str(text))
    _set_run_font(run, size, bold=bold, color=color, font_name=font_name)
    return p


# ═══════════════════════════════════════════════
# 核心表格生成
# ═══════════════════════════════════════════════

def add_recipe_table(doc, headers, rows, col_widths_cm,
                     header_color=COLOR_HEADER_BG,
                     alt_row_color=COLOR_ROW_EVEN,
                     font_size=FONT_TABLE):
    """
    按031规则生成标准表格。

    参数:
        doc: Document 对象
        headers: 表头列表
        rows: 数据行列表（二维数组）
        col_widths_cm: 各列宽度(cm)，总和必须=20
        header_color: 表头底色
        alt_row_color: 交替行底色
        font_size: 表格字号
    """
    # 校验列宽总和
    total_w = sum(col_widths_cm)
    if abs(total_w - 20.0) > 0.01:
        raise ValueError(f"列宽总和必须=20cm，当前={total_w}cm。请调整 col_widths_cm。")

    n_rows = 1 + len(rows)
    n_cols = len(headers)
    table = doc.add_table(rows=n_rows, cols=n_cols)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # 设置表格总宽 = 20cm
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else parse_xml(
        f'<w:tblPr {nsdecls("w")}/>'
    )
    tblW = parse_xml(
        f'<w:tblW {nsdecls("w")} w:w="{int(TABLE_TOTAL_WIDTH)}" w:type="dxa"/>'
    )
    # 移除旧的 tblW
    for old in tblPr.findall(qn('w:tblW')):
        tblPr.remove(old)
    tblPr.append(tblW)

    # 表头
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        _set_cell_text(cell, h, bold=True, size=font_size,
                       color=COLOR_HEADER_FG, align=WD_ALIGN_PARAGRAPH.CENTER)
        _set_cell_bg(cell, header_color)
        _set_cell_margins(cell)

    # 数据行
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            _set_cell_text(cell, str(val), size=font_size, color=COLOR_BODY)
            _set_cell_margins(cell)
            # 交替行底色
            if r_idx % 2 == 1:
                _set_cell_bg(cell, alt_row_color)

    # 设置列宽
    for i, w_cm in enumerate(col_widths_cm):
        for row in table.rows:
            row.cells[i].width = Cm(w_cm)

    # 表后小间距
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(2)

    return table


# ═══════════════════════════════════════════════
# 文档结构组件
# ═══════════════════════════════════════════════

def add_heading_styled(doc, text, level=1):
    """添加规范字号的标题"""
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = HEADING_SPACE_BEFORE
    h.paragraph_format.space_after = HEADING_SPACE_AFTER
    for run in h.runs:
        run.font.name = FONT_NAME
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
        if level == 1:
            run.font.size = FONT_H1
        elif level == 2:
            run.font.size = FONT_H2
        run.font.color.rgb = COLOR_EMPHASIS
    return h


def add_body_text(doc, text, bold=False, size=FONT_BODY, color=None,
                  align=None, indent=False):
    """添加正文段落"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = PARA_SPACE_BEFORE
    p.paragraph_format.space_after = PARA_SPACE_AFTER
    if align is not None:
        p.alignment = align
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.7)
    run = p.add_run(text)
    _set_run_font(run, size, bold=bold, color=color or COLOR_BODY)
    return p


def add_cover_page(doc, config):
    """
    封面：菜品名称 + 客户信息 + 核心参数

    config 期望字段:
        dish_name: str       — 菜品名称
        customer_info: str   — 客户信息
        core_params: list    — [(标签, 值), ...]  如 [("出餐速度", "3分钟/份"), ("保存期", "冷藏7天")]
    """
    # 顶部留白
    for _ in range(4):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)

    # 菜品名称
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(config.get("dish_name", "未命名菜品"))
    _set_run_font(run, FONT_COVER_TITLE, bold=True, color=COLOR_EMPHASIS)

    # 副标题
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("标准化配方操作方案")
    _set_run_font(run, FONT_H2, color=COLOR_BODY)

    # 空行
    for _ in range(2):
        doc.add_paragraph()

    # 客户信息
    customer = config.get("customer_info", "")
    if customer:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"客户：{customer}")
        _set_run_font(run, FONT_BODY, color=COLOR_BODY)

    # 核心参数
    for label, value in config.get("core_params", []):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{label}：{value}")
        _set_run_font(run, FONT_BODY, color=COLOR_BODY)


def add_disclaimer(doc):
    """免责声明 —— 固定内容，固定样式，不可改动"""
    # 标题
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(DISCLAIMER_TITLE)
    _set_run_font(run, Pt(18), bold=True, color=COLOR_EMPHASIS)

    # 免责声明段落 —— 浅黄底色框
    disclaimer_p = doc.add_paragraph()
    disclaimer_p.paragraph_format.space_before = Pt(0)
    disclaimer_p.paragraph_format.space_after = Pt(4)

    # 段落底色（通过段落底纹）
    pPr = disclaimer_p._p.get_or_add_pPr()
    shd = parse_xml(
        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{COLOR_DISCLAIMER_BG}"/>'
    )
    pPr.append(shd)

    # 段落内边距
    ind = parse_xml(
        f'<w:ind {nsdecls("w")} w:left="120" w:right="120" w:firstLine="0"/>'
    )
    # 移除旧 ind
    for old in pPr.findall(qn('w:ind')):
        pPr.remove(old)
    pPr.append(ind)

    # 段前段后间距
    spacing = parse_xml(
        f'<w:spacing {nsdecls("w")} w:before="80" w:after="80" w:line="240" w:lineRule="auto"/>'
    )
    for old in pPr.findall(qn('w:spacing')):
        pPr.remove(old)
    pPr.append(spacing)

    run = disclaimer_p.add_run(DISCLAIMER_TEXT)
    _set_run_font(run, FONT_BODY, bold=True, color=COLOR_BODY)


def add_section_title(doc, number, title):
    """添加带编号的一级标题"""
    return add_heading_styled(doc, f"{number}、{title}", level=1)


# ═══════════════════════════════════════════════
# 列宽计算辅助
# ═══════════════════════════════════════════════

def calc_col_widths(specs):
    """
    根据列内容类型计算列宽，确保总和=20cm。

    specs: [(内容类型, 建议宽度或None), ...]
      内容类型: "序号" | "用量" | "合规" | "名称" | "说明" | "要点"
      None 表示自动分配

    返回: [宽度cm, ...]
    """
    # 基准映射
    type_base = {
        "序号": 1.2,
        "用量": 2.0,
        "合规": 1.5,
        "温度": 2.0,
        "时间": 2.0,
        "名称": 4.0,
        "说明": 7.0,
        "要点": 7.0,
    }

    widths = []
    auto_indices = []
    fixed_sum = 0.0

    for i, (ctype, custom_w) in enumerate(specs):
        if custom_w is not None:
            widths.append(custom_w)
            fixed_sum += custom_w
        elif ctype in type_base:
            w = type_base[ctype]
            widths.append(w)
            fixed_sum += w
        else:
            widths.append(0)
            auto_indices.append(i)

    # 自动分配剩余宽度
    remaining = 20.0 - fixed_sum
    if auto_indices and remaining > 0:
        per_auto = remaining / len(auto_indices)
        for i in auto_indices:
            widths[i] = round(per_auto, 1)

    # 微调使总和=20
    current_sum = sum(widths)
    if widths and auto_indices:
        widths[auto_indices[-1]] += round(20.0 - current_sum, 1)

    return widths


# ═══════════════════════════════════════════════
# 配置校验
# ═══════════════════════════════════════════════

REQUIRED_KEYS = [
    "dish_name",
    "customer_info",
    "core_params",
    "recipe_tables",
    "ab_test_design",
    "final_numeric_audit",
    "operation_procedures",
    "storage_methods",
    "popular_principles",
    "additive_list",
    "regional_adaptations",
    "quick_reference_cards",
]

def validate_config(config):
    """检查必需配置、A/B完整性、最终数值基准与算术核验。返回错误列表。"""
    errors = []
    for key in REQUIRED_KEYS:
        if key not in config:
            errors.append(f"缺少必需字段: {key}")

    if not isinstance(config.get("core_params"), list):
        errors.append("core_params必须是列表 [(标签, 值), ...]")

    tables = config.get("recipe_tables")
    if not isinstance(tables, list) or not tables:
        errors.append("recipe_tables必须是非空列表，且包含A/B完整配方表")
        tables = []
    for i, tbl in enumerate(tables):
        if not isinstance(tbl, dict):
            errors.append(f"配方表[{i}]必须是字典")
            continue
        if "col_widths" in tbl:
            try:
                width_sum = sum(float(x) for x in tbl["col_widths"])
                if abs(width_sum - 20.0) > 0.01:
                    errors.append(f"配方表[{i}]列宽总和={width_sum}cm，必须=20cm")
            except (TypeError, ValueError):
                errors.append(f"配方表[{i}]列宽配置无效")

    titles = [re.sub(r"\s+", "", str(tbl.get("section_title", ""))).upper()
              for tbl in tables if isinstance(tbl, dict)]
    a_tables = [tbl for tbl in tables if any(mark in re.sub(r"\s+", "", str(tbl.get("section_title", ""))).upper()
               for mark in ("A版", "版本A", "A方案"))]
    b_tables = [tbl for tbl in tables if any(mark in re.sub(r"\s+", "", str(tbl.get("section_title", ""))).upper()
               for mark in ("B版", "版本B", "B方案"))]
    if not a_tables:
        errors.append("recipe_tables必须包含至少一个标题明确标记为A版/版本A/A方案的完整配方表")
    if not b_tables:
        errors.append("recipe_tables必须包含至少一个标题明确标记为B版/版本B/B方案的完整配方表")
    if a_tables and b_tables:
        def rows_signature(group):
            return tuple(tuple(str(x).strip() for x in row)
                         for tbl in group for row in tbl.get("rows", []))
        if rows_signature(a_tables) == rows_signature(b_tables):
            errors.append("A/B配方表内容完全相同；必须设计并落实有意义的配方差异")

    design = config.get("ab_test_design")
    if not isinstance(design, dict):
        errors.append("ab_test_design必须是字典，包含A/B设计目标、差异、风险和比较规则")
    else:
        for key in ("version_a", "version_b"):
            version = design.get(key)
            if not isinstance(version, dict):
                errors.append(f"ab_test_design缺少{key}")
                continue
            for field in ("design_goal", "differences", "expected_effect", "risks"):
                if not version.get(field):
                    errors.append(f"ab_test_design.{key}缺少{field}")
        for field in ("comparison_metrics", "comparison_conditions", "decision_rule"):
            if not design.get(field):
                errors.append(f"ab_test_design缺少{field}")

    audit = config.get("final_numeric_audit")
    if not isinstance(audit, dict):
        errors.append("final_numeric_audit必须是结构化字典，包含A/B最终基准、引用和总量核算")
        audit = {}
    reviewed_sections = set(audit.get("reviewed_sections", []))
    required_review_sections = {
        "recipe_tables", "operation_procedures", "additive_list",
        "storage_methods", "popular_principles", "quick_reference_cards"
    }
    missing_sections = required_review_sections - reviewed_sections
    if missing_sections:
        errors.append("最终数字审计未声明已逐项复核的模块: " + "、".join(sorted(missing_sections)))

    versions = audit.get("versions", [])
    if not isinstance(versions, list):
        errors.append("final_numeric_audit.versions必须是列表")
        versions = []
    by_version = {str(v.get("version", "")).upper(): v
                  for v in versions if isinstance(v, dict)}
    for version_key in ("A", "B"):
        if version_key not in by_version:
            errors.append(f"final_numeric_audit缺少版本{version_key}")
            continue
        version = by_version[version_key]
        canonical = version.get("canonical_values", [])
        if not isinstance(canonical, list) or not canonical:
            errors.append(f"版本{version_key}缺少canonical_values最终数值基准")
            continue

        canonical_by_name = {}
        for item in canonical:
            if not isinstance(item, dict):
                errors.append(f"版本{version_key}存在格式无效的最终数值项: {item}")
                continue
            name = str(item.get("name", "")).strip()
            unit = str(item.get("unit", "")).strip()
            amount = item.get("amount")
            if not name or not unit or not isinstance(amount, (int, float)) or not math.isfinite(float(amount)):
                errors.append(f"版本{version_key}存在无效最终数值项: {item}")
                continue
            if name in canonical_by_name:
                errors.append(f"版本{version_key}最终数值基准中原料/参数重复: {name}")
            canonical_by_name[name] = {"amount": float(amount), "unit": unit}

        refs = version.get("references", [])
        if not isinstance(refs, list) or not refs:
            errors.append(f"版本{version_key}references不能为空；需登记每个重复数字的出现位置")
            refs = []
        referenced_names = {str(ref.get("name", "")).strip()
                            for ref in refs if isinstance(ref, dict)}
        for name in canonical_by_name:
            if name not in referenced_names:
                errors.append(f"版本{version_key}缺少原料/参数{name}的全文引用审计记录")

        split_sums = {}
        for ref in refs:
            if not isinstance(ref, dict):
                errors.append(f"版本{version_key}存在无效引用记录: {ref}")
                continue
            name = str(ref.get("name", "")).strip()
            unit = str(ref.get("unit", "")).strip()
            amount = ref.get("amount")
            mode = str(ref.get("mode", "full")).lower()
            location = str(ref.get("location", "未注明位置"))
            if name not in canonical_by_name:
                errors.append(f"版本{version_key}引用了未登记的原料/参数{name}（{location}）")
                continue
            if not isinstance(amount, (int, float)) or not math.isfinite(float(amount)):
                errors.append(f"版本{version_key}引用数值无效：{name}（{location}）")
                continue
            base = canonical_by_name[name]
            if unit != base["unit"]:
                errors.append(f"版本{version_key}单位不一致：{name}基准{base['unit']}，引用{unit}（{location}）")
            if mode == "split":
                split_sums[name] = split_sums.get(name, 0.0) + float(amount)
            elif abs(float(amount) - base["amount"]) > 0.0001:
                errors.append(f"版本{version_key}数字不一致：{name}基准{base['amount']}{base['unit']}，引用{amount}{unit}（{location}）")
        for name, amount in split_sums.items():
            base = canonical_by_name[name]
            if abs(amount - base["amount"]) > 0.0001:
                errors.append(f"版本{version_key}分次用量合计错误：{name}分次合计{amount}{base['unit']}，基准为{base['amount']}{base['unit']}")

        totals = version.get("totals", [])
        if not isinstance(totals, list) or not totals:
            errors.append(f"版本{version_key}缺少必须的分项/总量计算记录")
            totals = []
        for total in totals:
            if not isinstance(total, dict):
                errors.append(f"版本{version_key}总量检查格式无效：{total}")
                continue
            components = total.get("components", [])
            if not isinstance(components, list) or not components:
                errors.append(f"版本{version_key}总量检查缺少components：{total.get('label', '未命名')}")
                continue
            try:
                component_values = [float(c["amount"]) for c in components]
                if not all(math.isfinite(x) for x in component_values):
                    raise ValueError("非有限数字")
                calc = sum(component_values)
                declared = float(total["declared_total"])
                if abs(calc - declared) > float(total.get("tolerance", 0.01)):
                    errors.append(f"版本{version_key}总量不一致：{total.get('label', '未命名')}计算值{calc}，标注值{declared}")
            except (KeyError, TypeError, ValueError):
                errors.append(f"版本{version_key}总量检查格式无效：{total}")

        batches = version.get("batch_checks", [])
        for batch in batches:
            try:
                calc = float(batch["per_batch"]) * float(batch["count"])
                declared = float(batch["total"])
                if not all(math.isfinite(x) for x in (calc, declared)):
                    raise ValueError("非有限数字")
                if abs(calc - declared) > float(batch.get("tolerance", 0.01)):
                    errors.append(f"版本{version_key}批量换算不一致：{batch.get('label', '未命名')}计算值{calc}，标注值{declared}")
            except (KeyError, TypeError, ValueError):
                errors.append(f"版本{version_key}批量换算格式无效：{batch}")

        # Compare each recipe table's actual ingredient quantities with the frozen canonical values.
        title_markers = ("A版", "版本A", "A方案") if version_key == "A" else ("B版", "版本B", "B方案")
        version_tables = [tbl for tbl in tables
                          if any(mark in re.sub(r"\s+", "", str(tbl.get("section_title", "")))
                                 for mark in title_markers)]
        table_quantities = {}
        for tbl in version_tables:
            headers = [str(h).strip() for h in tbl.get("headers", [])]
            name_idx = next((i for i, h in enumerate(headers)
                             if ("原料" in h or "名称" in h) and "用量" not in h), None)
            qty_idx = next((i for i, h in enumerate(headers)
                            if any(term in h for term in ("用量", "数量", "添加量", "净重"))), None)
            if name_idx is None or qty_idx is None:
                errors.append(f"版本{version_key}配方表“{tbl.get('section_title', '未命名')}”缺少可识别的原料名称/用量列")
                continue
            for row in tbl.get("rows", []):
                if name_idx >= len(row) or qty_idx >= len(row):
                    errors.append(f"版本{version_key}配方表行列数不一致：{row}")
                    continue
                name = str(row[name_idx]).strip()
                raw_qty = str(row[qty_idx]).replace(",", "").strip()
                match = re.search(r"-?\d+(?:\.\d+)?", raw_qty)
                if not name or not match:
                    continue
                table_quantities[name] = table_quantities.get(name, 0.0) + float(match.group(0))
        for name, amount in table_quantities.items():
            if name not in canonical_by_name and name not in ("合计", "总计", "总重", "配方总重", "小计"):
                errors.append(f"版本{version_key}配方表出现未登记的原料/参数：{name}")
        for name, item in canonical_by_name.items():
            if name not in table_quantities:
                errors.append(f"版本{version_key}配方表缺少最终数值基准项：{name}")
            elif abs(table_quantities[name] - item["amount"]) > 0.0001:
                errors.append(f"版本{version_key}配方表用量与最终数值基准不一致：{name}表格合计{table_quantities[name]}，基准{item['amount']}")

    return errors

# ═══════════════════════════════════════════════
# 主构建函数
# ═══════════════════════════════════════════════

def build_document(config, output_dir=None):
    """
    构建完整的配方方案文档。

    参数:
        config: {
            "dish_name": str,              # 菜品名称
            "customer_info": str,          # 客户信息
            "core_params": [(标签, 值), ...],  # 封面核心参数
            "recipe_tables": [             # A/B各自完整的配方参数表列表；标题必须标记A版或B版
                {
                    "section_title": str,   # 小节标题（如"A版配方"或"B版配方"）
                    "headers": [str, ...],
                    "rows": [[str, ...], ...],
                    "col_widths": [float, ...],  # 列宽cm，和为20
                    "note": str or None,    # 表后注释（可选）
                },
                ...
            ],
            "ab_test_design": {             # 必需：A/B设计目标、差异、预期、风险、比较条件/指标/决策规则
                "version_a": {"design_goal": str, "differences": str, "expected_effect": str, "risks": str},
                "version_b": {"design_goal": str, "differences": str, "expected_effect": str, "risks": str},
                "comparison_conditions": str, "comparison_metrics": [str, ...], "decision_rule": str,
            },
            "final_numeric_audit": {        # 必需：reviewed_sections + versions[A/B] canonical_values/references/totals/batch_checks
                "reviewed_sections": [str, ...],
                "versions": [
                    {"version": "A|B", "canonical_values": [{"name": str, "amount": float, "unit": str}],
                     "references": [{"name": str, "amount": float, "unit": str, "location": str, "mode": "full|split"}],
                     "totals": [{"label": str, "components": [{"amount": float}], "declared_total": float}],
                     "batch_checks": [{"label": str, "per_batch": float, "count": float, "total": float}]},
                ],
            },
            "operation_procedures": [      # A/B操作流程（共用步骤需明确标注）
                {
                    "phase": str,           # 阶段名
                    "steps": [             # 步骤列表
                        {"num": str, "action": str, "key": str, "right": str, "wrong": str},
                        ...
                    ],
                },
                ...
            ],
            "storage_methods": str or [(标题, 内容), ...],  # 保存方法
            "popular_principles": [        # 通俗原理
                {"title": str, "content": str},
                ...
            ],
            "additive_list": [             # 添加剂安全清单
                {"name": str, "usage": str, "limit": str, "gb": str, "note": str},
                ...
            ],
            "regional_adaptations": str or dict,  # 地域适配
            "quick_reference_cards": [     # 速查卡
                {"title": str, "headers": [str, ...], "rows": [[str, ...], ...], "col_widths": [float, ...]},
                ...
            ],
        }
        output_dir: str — 输出目录，默认 ~/Desktop/

    返回: str — 生成的文件路径
    """
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("配置未通过031门禁，禁止导出：\\n- " + "\\n- ".join(config_errors))

    if output_dir is None:
        output_dir = os.path.expanduser("~/Desktop")

    dish_name = config.get("dish_name", "未命名")
    customer = config.get("customer_info", "")

    # 文件名
    filename = f"{dish_name}_{customer}_配方方案.docx" if customer else f"{dish_name}_配方方案.docx"
    output_path = os.path.join(output_dir, filename)

    doc = Document()

    # 页面设置
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = PAGE_MARGIN
    section.bottom_margin = PAGE_MARGIN
    section.left_margin = PAGE_MARGIN
    section.right_margin = PAGE_MARGIN

    # 默认样式
    style = doc.styles["Normal"]
    font = style.font
    font.name = FONT_NAME
    font.size = FONT_BODY
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_NAME)
    style.paragraph_format.space_after = PARA_SPACE_AFTER

    # ═══════════════════════════════════
    # 1. 封面
    # ═══════════════════════════════════
    add_cover_page(doc, config)

    # ═══════════════════════════════════
    # 2. 重要提示/免责声明
    # ═══════════════════════════════════
    add_disclaimer(doc)

    # ═══════════════════════════════════
    # 3. 配方参数表
    # ═══════════════════════════════════
    add_section_title(doc, "一", "配方参数表")

    for tbl_cfg in config.get("recipe_tables", []):
        if tbl_cfg.get("section_title"):
            add_heading_styled(doc, tbl_cfg["section_title"], level=2)

        if tbl_cfg.get("intro"):
            add_body_text(doc, tbl_cfg["intro"])

        add_recipe_table(
            doc,
            headers=tbl_cfg["headers"],
            rows=tbl_cfg["rows"],
            col_widths_cm=tbl_cfg["col_widths"],
        )

        if tbl_cfg.get("note"):
            add_body_text(doc, tbl_cfg["note"], size=FONT_TABLE_NOTE, color=COLOR_EMPHASIS)

    # ═══════════════════════════════════
    # 4. A/B测试方案与比较标准
    # ═══════════════════════════════════
    add_section_title(doc, "二", "A/B测试方案与比较标准")
    design = config["ab_test_design"]
    for key, label in (("version_a", "版本A"), ("version_b", "版本B")):
        item = design[key]
        add_heading_styled(doc, label, level=2)
        add_body_text(doc, "设计目标：" + str(item["design_goal"]))
        add_body_text(doc, "关键差异：" + str(item["differences"]))
        add_body_text(doc, "预期效果：" + str(item["expected_effect"]))
        add_body_text(doc, "风险与边界：" + str(item["risks"]))
    add_heading_styled(doc, "比较条件", level=2)
    add_body_text(doc, str(design["comparison_conditions"]))
    add_heading_styled(doc, "比较指标", level=2)
    add_body_text(doc, "；".join(str(x) for x in design["comparison_metrics"]))
    add_heading_styled(doc, "选择原则", level=2)
    add_body_text(doc, str(design["decision_rule"]))

    # ═══════════════════════════════════
    # 5. 标准化操作流程
    # ═══════════════════════════════════
    add_section_title(doc, "三", "标准化操作流程")

    for phase in config.get("operation_procedures", []):
        add_heading_styled(doc, phase["phase"], level=2)

        # 每阶段：操作步骤表 + 正误对比
        step_headers = ["步骤", "操作内容", "关键参数/判断标准", "✅ 正确做法", "❌ 常见错误"]
        step_rows = []
        for s in phase.get("steps", []):
            step_rows.append([
                s.get("num", ""),
                s.get("action", ""),
                s.get("key", ""),
                s.get("right", ""),
                s.get("wrong", ""),
            ])

        step_widths = [1.2, 4.0, 5.0, 5.0, 4.8]  # 总和=20
        add_recipe_table(doc, step_headers, step_rows, step_widths)

    # ═══════════════════════════════════
    # 5. 保存方法详解
    # ═══════════════════════════════════
    add_section_title(doc, "四", "保存方法详解")

    storage = config.get("storage_methods", [])
    if isinstance(storage, str):
        add_body_text(doc, storage)
    elif isinstance(storage, list):
        for item in storage:
            if isinstance(item, tuple):
                add_heading_styled(doc, item[0], level=2)
                add_body_text(doc, item[1])
            elif isinstance(item, dict):
                if item.get("title"):
                    add_heading_styled(doc, item["title"], level=2)
                if item.get("headers") and item.get("rows"):
                    add_recipe_table(
                        doc,
                        headers=item["headers"],
                        rows=item["rows"],
                        col_widths_cm=item.get("col_widths", [5, 15]),
                    )
                if item.get("content"):
                    add_body_text(doc, item["content"])

    # ═══════════════════════════════════
    # 6. 通俗原理
    # ═══════════════════════════════════
    add_section_title(doc, "五", "通俗原理")

    for pp in config.get("popular_principles", []):
        add_heading_styled(doc, pp["title"], level=2)
        add_body_text(doc, pp["content"])

    # ═══════════════════════════════════
    # 7. 添加剂安全清单
    # ═══════════════════════════════════
    add_section_title(doc, "六", "添加剂安全清单（GB 2760 合规）")

    add_headers = ["添加剂名称", "用量", "国标上限", "GB 2760类别", "安全提示"]
    add_rows = []
    for a in config.get("additive_list", []):
        add_rows.append([
            a.get("name", ""),
            a.get("usage", ""),
            a.get("limit", ""),
            a.get("gb", ""),
            a.get("note", ""),
        ])

    if add_rows:
        add_widths = [3.5, 2.5, 2.5, 4.5, 7.0]  # 总和=20
        add_recipe_table(doc, add_headers, add_rows, add_widths)
    else:
        add_body_text(doc, "本配方未使用食品添加剂。")

    # ═══════════════════════════════════
    # 8. 地域适配建议
    # ═══════════════════════════════════
    add_section_title(doc, "七", "地域适配建议")

    regional = config.get("regional_adaptations", "")
    if isinstance(regional, str):
        add_body_text(doc, regional)
    elif isinstance(regional, dict):
        for key, val in regional.items():
            add_heading_styled(doc, key, level=2)
            add_body_text(doc, str(val))

    # ═══════════════════════════════════
    # 9. 厨房速查卡
    # ═══════════════════════════════════
    add_section_title(doc, "八", "厨房速查卡（建议单独打印张贴）")

    for card in config.get("quick_reference_cards", []):
        if card.get("title"):
            add_body_text(doc, card["title"], bold=True, size=FONT_H2)

        if card.get("intro"):
            add_body_text(doc, card["intro"])

        if card.get("headers") and card.get("rows"):
            add_recipe_table(
                doc,
                headers=card["headers"],
                rows=card["rows"],
                col_widths_cm=card.get("col_widths", [5, 15]),
            )

    # ═══════════════════════════════════
    # 保存
    # ═══════════════════════════════════
    doc.save(output_path)
    return output_path


# ═══════════════════════════════════════════════
# 自检工具
# ═══════════════════════════════════════════════

def self_check(output_path):
    """打开生成的文档进行格式与客户文案边界自检，返回检查结果"""
    doc = Document(output_path)
    results = []

    for i, p in enumerate(doc.paragraphs):
        for run in p.runs:
            if run._r.xml.count('w:br w:type="page"') > 0:
                results.append(("❌", f"发现分页符: 段落{i}"))

    all_text_parts = [p.text for p in doc.paragraphs]
    all_text_parts.extend(cell.text for table in doc.tables for row in table.rows for cell in row.cells)
    for section in doc.sections:
        all_text_parts.extend(p.text for p in section.header.paragraphs)
        all_text_parts.extend(p.text for p in section.footer.paragraphs)
        all_text_parts.extend(cell.text for table in section.header.tables for row in table.rows for cell in row.cells)
        all_text_parts.extend(cell.text for table in section.footer.tables for row in table.rows for cell in row.cells)
    all_text = "\n".join(all_text_parts)

    ai_keywords = ["AI生成", "自动生成", "人工智能", "生成工具", "生成日期"]
    for kw in ai_keywords:
        if kw in all_text:
            results.append(("❌", f"发现禁用词'{kw}'"))

    if "A版" not in all_text or "B版" not in all_text:
        results.append(("❌", "最终文档缺少A版或B版配方"))
    if "A/B测试方案与比较标准" not in all_text:
        results.append(("❌", "最终文档缺少A/B比较说明"))

    forbidden_content = ["成本预算", "成本核算表", "配方总成本", "预估单份成本", "成本合理性", "预算范围"]
    for term in forbidden_content:
        if term in all_text:
            results.append(("❌", f"最终客户文档包含禁止的成本内容：{term}"))

    forbidden_test_requirements = ["建议先做小锅测试", "必须先做小锅测试", "需实测后才能交付", "测试后才能批量采用"]
    for term in forbidden_test_requirements:
        if term in all_text:
            results.append(("❌", f"最终文档把测试写成交付前提：{term}"))

    if DISCLAIMER_TEXT not in all_text:
        results.append(("❌", "免责声明缺失或与031固定内容不一致"))

    for i, table in enumerate(doc.tables):
        tblPr = table._tbl.tblPr
        if tblPr is not None:
            tblW = tblPr.findall(qn('w:tblW'))
            if tblW:
                w = int(tblW[0].get(qn('w:w'), '0'))
                expected = int(TABLE_TOTAL_WIDTH)
                if abs(w - expected) > 100:
                    results.append(("⚠️", f"表格{i}宽度={w}dxa，期望={expected}dxa"))

    section = doc.sections[0]
    margin_expected = int(PAGE_MARGIN)
    for mname, mval in [("上", section.top_margin), ("下", section.bottom_margin),
                         ("左", section.left_margin), ("右", section.right_margin)]:
        if mval and abs(mval - margin_expected) > 5000:
            results.append(("⚠️", f"页边距{mname}={mval}，期望={margin_expected}"))

    for i, p in enumerate(doc.paragraphs[:20]):
        for run in p.runs:
            if run.font.size and run.font.size < Pt(12) and run.text.strip():
                results.append(("⚠️", f"段落{i}字号过小({run.font.size}): '{run.text[:30]}...'"))
                break

    if not results:
        results.append(("✅", "格式与最终文案边界自检通过"))
    return results

# ═══════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("餐饮配方方案导出模板 - 031规则强制执行版")
    print("=" * 60)
    print()
    print("⚠️ 此文件是模板，不应直接运行。")
    print("   请通过 build_document(config) 函数调用。")
    print()
    print("强制规范：")
    print(f"  - 封面标题: {FONT_COVER_TITLE}")
    print(f"  - 一级标题: {FONT_H1}")
    print(f"  - 二级标题: {FONT_H2}")
    print(f"  - 正文: {FONT_BODY}")
    print(f"  - 表格: {FONT_TABLE}")
    print(f"  - 表头配色: #{COLOR_HEADER_BG} + 白字")
    print(f"  - 交替行: 白底 / #{COLOR_ROW_EVEN}")
    print(f"  - 表格总宽: {TABLE_TOTAL_WIDTH}")
    print(f"  - 页边距: {PAGE_MARGIN}")
    print(f"  - 免责声明: #{COLOR_DISCLAIMER_BG}底色 + {FONT_BODY}粗体")
    print(f"  - 9模块固定顺序: {' → '.join(MODULE_ORDER)}")
    print(f"  - 禁止: 分页符 / AI生成字样 / 生成日期")
