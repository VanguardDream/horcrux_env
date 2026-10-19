"""Horcrux v2 전환 학습 연구 정리 덱 생성 (python-pptx).

모든 수치는 CLAUDE_CHANGES.md / policies/unified/TRAINING_HISTORY.txt / 데모 result.txt 기록값.
영상은 pptx에 임베드(재생 가능) + 포스터 프레임(PDF 미리보기용).
"""
import json
import sys
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path("/home/bong/projects/horcrux_env")
SC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
POSTERS = SC / "posters"
OUT = ROOT / "docs" / "Horcrux_transition_research_2026-09.pptx"
CURVES = json.load(open(SC / "curves.json"))

# ----------------------------------------------------------------------------- 디자인 시스템
NAVY, NAVY2, MINT, MINT_D = "0F2A44", "1B3A5C", "2EC4B6", "1A9E92"
TEXT, MUTED, LINE = "1F2933", "5C6B7A", "D9E1E8"
CARD, CARD2 = "F2F5F8", "E8EEF3"
RED, AMBER, BLUE, GREEN = "D64550", "E9A23B", "3E7CB1", "3A9D5D"
WHITE = "FFFFFF"
FONT = "Calibri"
EA_FONT = "Malgun Gothic"
W, H = 13.333, 7.5

VIDEOS = {
    "experts_square": ROOT / "runs/path_follow_demo/20260909-105155_square/path_demo.mp4",
    "experts_star": ROOT / "runs/path_follow_demo/20260909-105200_star/path_demo.mp4",
    "hybrid_gauntlet": ROOT / "runs/path_follow_demo/20260908-212803_gauntlet/path_demo.mp4",
    "align_hard": ROOT / "runs/path_follow_demo/align_showcase/bl_to_right_hard.mp4",
    "align_align": ROOT / "runs/path_follow_demo/align_showcase/bl_to_right_align.mp4",
    "smooth_align_only": ROOT / "runs/path_follow_demo/smooth_showcase/bl_to_right_align_only.mp4",
    "smooth_align_xfade": ROOT / "runs/path_follow_demo/smooth_showcase/bl_to_right_align_xfade.mp4",
    "unified_square": ROOT / "runs/path_follow_demo/20260909-220058_square_unified/path_demo.mp4",
    "unified_star": ROOT / "runs/path_follow_demo/20260909-220104_star_unified/path_demo.mp4",
    "unified_gauntlet": ROOT / "runs/path_follow_demo/20260909-220111_gauntlet_unified/path_demo.mp4",
    "stage1_train": ROOT / "runs/ppo_unified_transition_stage1/20260909-153324-183674_ppo_unified_transition_stage1/videos/iteration-009610-timesteps-039362560-episode-0.mp4",
    "fade_bl_to_right_fade_1p25s": ROOT / "runs/path_follow_demo/fade_showcase/bl_to_right_fade_1p25s.mp4",
}
FIGS = {
    "experts_square_traj": ROOT / "runs/path_follow_demo/20260909-105155_square/trajectory.png",
    "experts_star_traj": ROOT / "runs/path_follow_demo/20260909-105200_star/trajectory.png",
    "unified_gauntlet_traj": ROOT / "runs/path_follow_demo/20260909-220111_gauntlet_unified/trajectory.png",
    "unified_square_traj": ROOT / "runs/path_follow_demo/20260909-220058_square_unified/trajectory.png",
    "hybrid_gauntlet_traj": ROOT / "runs/path_follow_demo/20260908-212803_gauntlet/trajectory.png",
}

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


def rgb(h):
    return RGBColor.from_string(h)


def _ea(run):
    rPr = run._r.get_or_add_rPr()
    if rPr.find(qn("a:ea")) is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
        ea.set("typeface", EA_FONT)


def _style_run(run, size, bold=False, color=TEXT, italic=False):
    f = run.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = rgb(color)
    _ea(run)


def _bullet(para, level=0, char="•", color=MINT_D):
    pPr = para._p.get_or_add_pPr()
    indent = 0.22
    pPr.set("marL", str(Emu(Inches(indent * (level + 1)))))
    pPr.set("indent", str(-Emu(Inches(indent))))
    bu = etree.SubElement(pPr, qn("a:buClr"))
    srgb = etree.SubElement(bu, qn("a:srgbClr"))
    srgb.set("val", color)
    bc = etree.SubElement(pPr, qn("a:buChar"))
    bc.set("char", char)


def add_text(slide, x, y, w, h, paras, size=14, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, margin=0.05, space_after=4, line_spacing=1.08):
    """paras: str | list of (str | dict(text|runs, size, bold, color, bullet, level, align, space_after))."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = anchor
    if isinstance(paras, str):
        paras = [paras]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(p, str):
            p = {"text": p}
        para.alignment = p.get("align", align)
        para.line_spacing = line_spacing
        para.space_after = Pt(p.get("space_after", space_after))
        runs = p.get("runs") or [(p.get("text", ""), {})]
        for text, opt in runs:
            r = para.add_run()
            r.text = text
            _style_run(r, opt.get("size", p.get("size", size)), opt.get("bold", p.get("bold", bold)),
                       opt.get("color", p.get("color", color)), opt.get("italic", False))
        if p.get("bullet"):
            _bullet(para, p.get("level", 0), color=p.get("bullet_color", MINT_D))
    return tb


def rect(slide, x, y, w, h, fill, rounded=True, radius=0.06, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill)
    if line:
        shp.line.color.rgb = rgb(line)
        shp.line.width = Pt(0.75)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    if rounded:
        shp.adjustments[0] = radius
    return shp


def badge(slide, x, y, d, text, fill=MINT, color=WHITE, size=13):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill)
    shp.line.fill.background()
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _style_run(r, size, True, color)
    return shp


def background(slide, color):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = rgb(color)


def content_slide(title, subtitle=None):
    s = prs.slides.add_slide(BLANK)
    background(s, WHITE)
    tsize = 30 if len(title) <= 34 else (26 if len(title) <= 42 else 23)
    add_text(s, 0.55, 0.35, 12.2, 0.75, [{"text": title, "size": tsize, "bold": True, "color": NAVY}], margin=0)
    if subtitle:
        add_text(s, 0.55, 1.02, 12.2, 0.4, [{"text": subtitle, "size": 13, "color": MUTED}], margin=0)
    add_text(s, 0.55, 7.08, 8, 0.3, [{"text": "Horcrux v2 · 경로 추종 → gait 전환 학습 · 2026-09", "size": 9, "color": MUTED}], margin=0)
    return s


def dark_slide(title, subtitle=None, kicker=None):
    s = prs.slides.add_slide(BLANK)
    background(s, NAVY)
    if kicker:
        add_text(s, 0.9, 2.2, 11.5, 0.5, [{"text": kicker, "size": 16, "bold": True, "color": MINT}], margin=0)
    add_text(s, 0.9, 2.7, 11.5, 1.6, [{"text": title, "size": 40, "bold": True, "color": WHITE}], margin=0,
             anchor=MSO_ANCHOR.TOP)
    if subtitle:
        add_text(s, 0.9, 4.4, 11.5, 1.4, [{"text": subtitle, "size": 17, "color": "CADCFC"}], margin=0)
    return s


def fit_image(slide, path, x, y, w, h, frame=True):
    img = Image.open(path)
    ar = img.width / img.height
    bw, bh = w, h
    if bw / bh > ar:
        bw = bh * ar
    else:
        bh = bw / ar
    ox, oy = x + (w - bw) / 2, y + (h - bh) / 2
    if frame:
        rect(slide, ox - 0.05, oy - 0.05, bw + 0.1, bh + 0.1, CARD2, radius=0.03)
    slide.shapes.add_picture(str(path), Inches(ox), Inches(oy), Inches(bw), Inches(bh))
    return ox, oy, bw, bh


def add_video(slide, key, x, y, w, h, caption=None):
    path = VIDEOS[key]
    poster = POSTERS / f"{key}.png"
    ar = 16 / 9
    bw, bh = w, h
    if bw / bh > ar:
        bw = bh * ar
    else:
        bh = bw / ar
    ox, oy = x + (w - bw) / 2, y + (h - bh) / 2
    rect(slide, ox - 0.05, oy - 0.05, bw + 0.1, bh + 0.1, NAVY2, radius=0.03)
    slide.shapes.add_movie(str(path), Inches(ox), Inches(oy), Inches(bw), Inches(bh),
                           poster_frame_image=str(poster), mime_type="video/mp4")
    if caption:
        add_text(slide, ox, oy + bh + 0.06, bw, 0.32, [{"text": "▶ " + caption, "size": 10, "color": MUTED}], margin=0)
    return ox, oy, bw, bh


def intent_result(slide, x, y, w, h, intent, result, split=0.42):
    """의도 / 결과 요약 카드 두 개 (세로)."""
    ih = h * split - 0.08
    rect(slide, x, y, w, ih, CARD)
    add_text(slide, x + 0.15, y + 0.08, w - 0.3, 0.3, [{"text": "의도", "size": 11, "bold": True, "color": MINT_D}], margin=0)
    add_text(slide, x + 0.15, y + 0.36, w - 0.3, ih - 0.4, [{"text": t, "size": 12, "bullet": True, "space_after": 2} for t in intent], margin=0)
    ry = y + ih + 0.12
    rh = h - ih - 0.12
    rect(slide, x, ry, w, rh, NAVY)
    add_text(slide, x + 0.15, ry + 0.08, w - 0.3, 0.3, [{"text": "결과 요약", "size": 11, "bold": True, "color": MINT}], margin=0)
    add_text(slide, x + 0.15, ry + 0.36, w - 0.3, rh - 0.4,
             [{"text": t, "size": 12, "color": WHITE, "bullet": True, "bullet_color": MINT, "space_after": 2} for t in result], margin=0)


def add_table(slide, rows, x, y, w, h, col_w=None, size=10, header=True, first_col_bold=False, zebra=True):
    nr, nc = len(rows), len(rows[0])
    gf = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "1" if header else "0")
    tblPr.set("bandRow", "0")
    # 기본 스타일 제거(플레인)
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No Style, Table Grid
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(h / nr)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            is_head = header and i == 0
            _style_run(r, size, is_head or (first_col_bold and j == 0), WHITE if is_head else TEXT)
            cell.fill.solid()
            if is_head:
                cell.fill.fore_color.rgb = rgb(NAVY)
            elif zebra and i % 2 == 0:
                cell.fill.fore_color.rgb = rgb(CARD)
            else:
                cell.fill.fore_color.rgb = rgb(WHITE)
    return tbl


def _chart_common(chart, title, legend=True, size=9):
    chart.font.size = Pt(size)
    chart.font.name = FONT
    chart.has_title = bool(title)
    if title:
        chart.chart_title.text_frame.text = title
        p = chart.chart_title.text_frame.paragraphs[0]
        p.runs[0].font.size = Pt(11)
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = rgb(TEXT)
        _ea(p.runs[0])
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(9)


def bar_chart(slide, cats, series, x, y, w, h, title=None, colors=None, fmt="0.00", legend=True,
              stacked=False, ymin=None, ymax=None, label_size=8, horizontal=False):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    ctype = (XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED)
    gf = slide.shapes.add_chart(ctype, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    _chart_common(ch, title, legend)
    plot = ch.plots[0]
    plot.gap_width = 80
    plot.overlap = -10
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = rgb(TEXT)
    colors = colors or [NAVY, MINT, AMBER, RED, BLUE]
    for s, c in zip(ch.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(c)
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(LINE)
    va.tick_labels.font.size = Pt(9)
    va.format.line.fill.background()
    if ymin is not None:
        va.minimum_scale = ymin
    if ymax is not None:
        va.maximum_scale = ymax
    ca = ch.category_axis
    ca.tick_labels.font.size = Pt(9)
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = rgb(LINE)
    return ch


def line_chart(slide, series, x, y, w, h, title=None, colors=None, xtitle="steps (M)", ytitle=None, legend=True,
               ymin=None, ymax=None, fmt=None):
    cd = XyChartData()
    for name, pts in series:
        s = cd.add_series(name)
        for px, py in pts:
            s.add_data_point(px, py)
    gf = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    _chart_common(ch, title, legend)
    colors = colors or [NAVY, MINT, AMBER, RED]
    for s, c in zip(ch.series, colors):
        s.format.line.color.rgb = rgb(c)
        s.format.line.width = Pt(1.75)
        s.smooth = False
    va, ca = ch.value_axis, ch.category_axis
    for ax in (va, ca):
        ax.tick_labels.font.size = Pt(9)
        ax.format.line.color.rgb = rgb(LINE)
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(LINE)
    ca.has_major_gridlines = False
    if ymin is not None:
        va.minimum_scale = ymin
    if ymax is not None:
        va.maximum_scale = ymax
    if fmt:
        va.tick_labels.number_format = fmt
        va.tick_labels.number_format_is_linked = False
    if xtitle:
        ca.has_title = True
        ca.axis_title.text_frame.text = xtitle
        ca.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    if ytitle:
        va.has_title = True
        va.axis_title.text_frame.text = ytitle
        va.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    return ch


def step_row(slide, x, y, w, steps, d=0.42, fill=MINT, text_size=11, title_size=12, gap=0.15, start=1):
    """번호 배지 + 제목 + 설명 카드 가로 나열."""
    n = len(steps)
    cw = (w - gap * (n - 1)) / n
    for i, (t, desc) in enumerate(steps):
        cx = x + i * (cw + gap)
        rect(slide, cx, y, cw, 1.55, CARD)
        badge(slide, cx + 0.15, y + 0.15, d, str(i + start), fill)
        add_text(slide, cx + 0.15 + d + 0.1, y + 0.13, cw - d - 0.35, 0.5, [{"text": t, "size": title_size, "bold": True, "color": NAVY}], margin=0)
        add_text(slide, cx + 0.15, y + 0.62, cw - 0.3, 0.9, [{"text": desc, "size": text_size, "color": TEXT}], margin=0)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ============================================================================= 슬라이드
# 1. 표지
s = dark_slide("Horcrux v2 뱀 로봇:\n경로 추종에서 gait 전환 학습까지",
               "전문가 10명 → 경로 추종 데모 → 전환 메커니즘 → 전문가 증류 → 전환 커리큘럼 RL → 통합 정책 검증",
               kicker="연구 흐름 정리 · 2026-09-08 ~ 09-09")
add_text(s, 0.9, 6.5, 11, 0.4, [{"text": "Gait Decomposition(GD) 패러다임 · MuJoCo 14-DOF · PPO(SB3) · DGIST BRM Lab", "size": 12, "color": "8FA8C4"}], margin=0)
notes(s, "본 덱은 2026-09-08~09 이틀간 진행한 실험(경로 추종 데모, 전환 메커니즘, 증류, 전환 학습)을 흐름대로 정리한다. 수치는 CLAUDE_CHANGES.md와 TRAINING_HISTORY.txt 기록값.")

# 2. 연구 흐름 타임라인
s = content_slide("연구 흐름 한눈에 보기", "여덟 단계 — 각 단계의 질문과 얻은 답")
flow = [
    ("전문가 로스터", "8방위 + CW/CCW 회전 정책 10개, 3-stage KL 튜닝 레시피로 각 ~85M 스텝 학습"),
    ("경로 추종 데모", "웨이포인트 커맨더가 전문가를 스위칭 — 사각형·별 경로 완주 (CTE 0.19 / 0.33 m)"),
    ("전환 문제 발견", "\"backward/right 정책 문제\" → 진짜 원인은 gait 교체 순간의 위상 충돌"),
    ("전환 메커니즘 탐구", "페이드 → 위상 정렬 → 위험쌍 align+크로스페이드 하이브리드 (음성 결과 3건 포함)"),
    ("방위 화살표 렌더", "웨이포인트 목표 방위 vs 로봇 yaw 시각화 — 회전 미반영 확인"),
    ("전문가 증류", "BC + DART 노이즈 + DAgger 4회 → 9/10 명령 전문가 대비 0.95~1.01"),
    ("전환 커리큘럼 RL", "무작위 90쌍·시점·위상 전환, 앵커 근접 보상 설계 — Stage 1 완료, Stage 2 진행"),
    ("통합 정책 검증", "정책 하나로 경로 추종: gauntlet CTE −27%, 전환 1/3, 시간 절반"),
]
for r_ in range(2):
    step_row(s, 0.55, 1.6 + r_ * 2.05, 12.2, [(t, d) for t, d in flow[r_ * 4:(r_ + 1) * 4]], text_size=10.5, start=1 + 4 * r_)
rect(s, 0.55, 5.85, 12.2, 1.0, NAVY)
add_text(s, 0.8, 5.95, 11.8, 0.85, [
    {"runs": [("핵심 메시지  ", {"bold": True, "color": MINT}), ("GD 패러다임에서 \"방향은 gait, 세기는 정책\"이므로 전환의 본질은 gait 부호 패턴의 연속성이다. ", {"color": WHITE}),
              ("외부 메커니즘(위상 정렬)으로 그 연속성을 확보한 뒤, 정책 자체가 전환을 흡수하도록 학습시키는 것이 본 연구의 흐름이다.", {"color": WHITE})], "size": 13},
], margin=0)

# 3. 배경
s = content_slide("배경: GD 패러다임, 전문가 로스터, 튜닝 레시피")
# GD 다이어그램
rect(s, 0.55, 1.5, 4.0, 2.55, CARD)
add_text(s, 0.75, 1.6, 3.6, 0.35, [{"text": "Gait Decomposition (GD)", "size": 13, "bold": True, "color": NAVY}], margin=0)
bx = 0.75
for i, (lab, col, txt) in enumerate([("정책 출력", MINT, "진폭 a ∈ [0, 2.7]¹⁴\n(얼마나 세게)"), ("×", None, ""), ("gait 부호 패턴", NAVY, "motion vector ±1\n(어느 방향, 매 스텝 위상 진행)"), ("=", None, ""), ("관절 토크", MINT_D, "τ = a ⊙ mvec")]):
    if col is None:
        add_text(s, bx, 2.35, 0.35, 0.5, [{"text": lab, "size": 20, "bold": True, "color": MUTED, "align": PP_ALIGN.CENTER}], margin=0)
        bx += 0.35
        continue
    rect(s, bx, 2.05, 1.0, 1.1, col)
    add_text(s, bx, 2.1, 1.0, 0.3, [{"text": lab, "size": 10, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    add_text(s, bx, 2.42, 1.0, 0.7, [{"text": txt, "size": 8.5, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    bx += 1.0 + 0.05
add_text(s, 0.75, 3.25, 3.6, 0.8, [{"text": "정책은 진폭만, gait는 부호만 — 전환 시 관절 토크 부호가 바뀌는 순간이 곧 문제의 근원", "size": 10.5, "color": MUTED}], margin=0)
# 로스터 표
rows = [["명령", "joy", "gait δ (역재생)", "명령", "joy", "gait δ (역재생)"],
        ["forward", "(1, 0)", "0", "backward", "(−1, 0)", "0 (역)"],
        ["left", "(0, 1)", "45", "diag_bl", "(−.71, .71)", "203 (역)"],
        ["right", "(0, −1)", "225", "diag_br", "(−.71, −.71)", "23 (역)"],
        ["diag_fl", "(.71, .71)", "23", "ccw", "yaw +1", "315"],
        ["diag_fr", "(.71, −.71)", "203", "cw", "yaw −1", "135"]]
add_table(s, rows, 4.85, 1.5, 7.9, 2.55, col_w=[1.15, 1.15, 1.65, 1.15, 1.15, 1.65], size=10)
add_text(s, 4.85, 4.1, 7.9, 0.3, [{"text": "공통 진폭/시간 파라미터 (30, 30, 40, 40). gait 대수: y-거울 = δ+180°, 후진 계열 = 반대 전진 gait의 시간 역재생.", "size": 9.5, "color": MUTED}], margin=0)
# 레시피 + 회전 설계
rect(s, 0.55, 4.55, 6.0, 2.35, CARD)
add_text(s, 0.75, 4.65, 5.6, 0.35, [{"text": "검증된 3-stage KL 튜닝 레시피 (10개 계보에서 재현)", "size": 12.5, "bold": True, "color": NAVY}], margin=0)
add_text(s, 0.75, 5.05, 5.6, 1.8, [
    {"text": "Stage 1: lr 1e-4, n_epochs 2, target_kl 0.04 → 말기 approx_kl ≪ 0.01이면 \"KL 유휴\"", "size": 11, "bullet": True},
    {"text": "Stage 2: n_epochs 3 → KL이 0.04에 붙으면 \"포화\"", "size": 11, "bullet": True},
    {"text": "Stage 3: lr 5e-5 (연장 시 2.5e-5) — 정책을 흔들지 않는 옵티마이저 수준 조정만", "size": 11, "bullet": True},
    {"text": "모델과 VecNormalize 통계는 항상 쌍으로 보관", "size": 11, "bullet": True},
], margin=0)
rect(s, 6.75, 4.55, 6.0, 2.35, CARD)
add_text(s, 6.95, 4.65, 5.6, 0.35, [{"text": "회전 정책 v2 \"안정 우선\" 설계 (CW/CCW)", "size": 12.5, "bold": True, "color": NAVY}], margin=0)
add_text(s, 6.95, 5.05, 5.6, 1.8, [
    {"text": "속도보다 속도의 안정: 45·clip(부호·yaw_vel, ±0.5) + 과속 페널티", "size": 11, "bullet": True},
    {"text": "앵커: 시작점 0.2 m 이탈이 60스텝 지속되면 실패, 포화 앵커 비용 50·min(d, 2)", "size": 11, "bullet": True},
    {"text": "종료 페널티 −1000 + γ 0.99 (v1의 무한 비용은 critic 붕괴 → 포화 비용으로 교정)", "size": 11, "bullet": True},
    {"text": "is_terminated 이중 호출 결함 수정 (스텝당 1회 카운터)", "size": 11, "bullet": True},
], margin=0)

# 4. 섹션
dark_slide("Part 1. 경로 추종 데모와\n전환 메커니즘", "전문가 10명을 스위칭해 사각형·별을 그린다 — 그리고 전환의 물리를 이해한다", kicker="PART 1")

# 5. 데모 설계 + 사각형 영상
s = content_slide("경로 추종 데모: 웨이포인트 커맨더 + 전문가 스위칭", "뱀 로봇에게 고전적으로 어려웠던 사각형·별 경로를 GD 전문가 10명으로 주행")
add_video(s, "experts_square", 0.55, 1.5, 6.3, 3.55, "사각형 2 m (전문가 스위칭, 방위 화살표 렌더 포함)")
add_text(s, 7.15, 1.5, 5.6, 2.2, [
    {"text": "커맨더 (pure-pursuit식)", "size": 12.5, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "목표 방향을 몸통 좌표계에서 8-명령으로 양자화, 제어 주기 25스텝", "size": 11, "bullet": True},
    {"text": "34° 각도 히스테리시스(채터링 방지), capture 0.35 m, 근접 동결 0.85 m", "size": 11, "bullet": True},
    {"text": "시각화", "size": 12.5, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "fovy 80° 광각 + CoM 추적 카메라, 웨이포인트(도달 시 어둡게), 궤적 점열(현재 구간 진하게)", "size": 11, "bullet": True},
], margin=0)
intent_result(s, 7.15, 3.85, 5.6, 3.05,
              ["10명 전문가 + 고전 추종기로 사전 계획 경로가 주행 가능한지 확인", "결과를 영상(녹화)과 궤적 그림으로 남겨 실험 재현성 확보"],
              ["사각형 CTE 평균 0.193 m / 전환 5회 / 20 s 완주", "별(5각 한붓그리기) 0.334 m / 전환 10회 완주", "카메라·마커 요구 4건 반영 (광각, CoM 추적, 웨이포인트, 궤적)"])
add_text(s, 0.55, 5.5, 6.3, 1.4, [
    {"text": "산출물 규약", "size": 12, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "runs/path_follow_demo/<시각>_<경로>/ : path_demo.mp4, trajectory.png, result.txt(실험 요약 헤더 + CTE/완주/전환)", "size": 10.5, "bullet": True},
    {"text": "result.txt 헤더는 \"어떤 실험이었는지\" 5줄 요약 — 로그 누적 시 식별용 (요청 반영)", "size": 10.5, "bullet": True},
], margin=0)

# 6. 문제 발견
s = content_slide("문제 발견: 정책이 아니라 전환이 원인이었다", "\"backward·right 정책이 이상하다\"는 사각형 경로 관찰에서 출발한 진단")
rows = [["단계", "관찰 / 조치", "결과"],
        ["전문가 단독 검증", "backward, right 정책을 고정 명령으로 주행", "방향 오차 ±1.5° — 정책은 정상"],
        ["전환 진단 (56 순서쌍)", "기존 set_gait: 위상 비율 보존 교체", "12/56 쌍 붕괴, yaw 최대 160° 뒤집힘 (거울쌍 최악)"],
        ["k=0 재시작", "새 gait를 주기 시작 위상에서", "7쌍 해결, 3쌍 잔존"],
        ["잔존 위험쌍", "diag_bl→right / diag_bl→diag_fr / diag_br→diag_fl", "152° / 61° / 156° (역재생→순재생, 부호 정면 충돌)"]]
add_table(s, rows, 0.55, 1.5, 7.6, 2.6, col_w=[1.7, 3.0, 2.9], size=10.5)
rect(s, 0.55, 4.3, 7.6, 2.6, CARD)
add_text(s, 0.75, 4.4, 7.2, 2.4, [
    {"text": "왜 거울쌍·역재생쌍이 위험한가", "size": 12.5, "bold": True, "color": NAVY, "space_after": 4},
    {"text": "GD에서 방향은 gait 부호 패턴이 결정한다. 후진 계열은 전진 gait의 시간 역재생이라, 전환 순간 여러 관절의 토크 부호가 동시에 뒤집힌다.", "size": 11, "bullet": True},
    {"text": "정책(진폭)은 관측의 motion vector로 gait를 알지만, 몸통은 이전 패턴의 관성을 갖고 있어 부호 충돌이 곧 전복으로 이어진다.", "size": 11, "bullet": True},
    {"text": "즉 전환 문제 = \"연속된 두 gait 사이의 위상·부호 정합\" 문제로 재정의됨 → Part 1의 나머지는 이 정합을 만드는 방법 탐구.", "size": 11, "bullet": True},
], margin=0)
intent_result(s, 8.4, 1.5, 4.35, 5.4,
              ["사용자 관찰(\"backward/right 정책 문제\")의 진위 확인", "정책 vs 전환 메커니즘 중 어디가 원인인지 분리"],
              ["전문가는 무죄 — 원인은 gait 교체 순간의 위상 처리", "k=0 재시작만으로 12쌍 중 9쌍 해결", "역재생↔순재생 3쌍이 남아 별도 메커니즘 필요"])

# 7. 메커니즘 ① 소프트 핸드오프 → 에너지 페이드
s = content_slide("전환 메커니즘 ①: 행동 블렌딩 실패 → 에너지 페이드", "통신의 소프트 핸드오프처럼 두 정책의 행동을 섞자는 제안에서 출발")
add_video(s, "fade_bl_to_right_fade_1p25s", 0.55, 1.45, 5.6, 2.95, "diag_bl → right, 에너지 페이드 (10/5/10 = 1.25 s)")
rows = [["방식", "동작", "결과"],
        ["행동 블렌딩 (제안)", "두 정책 행동 가중 평균", "forward→right 3°→83° 악화: 옛 정책이 새 gait 부호 위에서 행동"],
        ["에너지 페이드", "감쇠 → 정지(gait 교체) → 상승", "위험 3쌍 정상화, 안전쌍은 부작용"],
        ["타이밍 (20,15,20)=2.75 s", "긴 정지", "15회 중 12회 성공 (위상 민감)"],
        ["타이밍 (10,5,10)=1.25 s", "짧은 정지", "15/15 성공, 최악 3.8° — 채택"],
        ["전면 적용", "모든 전환에 페이드", "사각형 CTE 0.19→0.83, 전환 56회 — 코너 오버슈트 연쇄"]]
add_table(s, rows, 6.4, 1.5, 6.35, 3.15, col_w=[1.75, 1.8, 2.8], size=9.5)
intent_result(s, 0.55, 5.0, 12.2, 1.9,
              ["두 정책 행동을 섞어 급변을 피할 수 있는지(소프트 핸드오프)", "안 되면 \"에너지를 낮추고 바꾸는\" 대안의 타이밍 민감도 파악"],
              ["행동 블렌딩은 gait 부호 문맥 충돌로 실패 — 섞을 대상은 행동이 아니라 gait 위상", "페이드는 위험쌍엔 유효하나 시간 지연(≥1.25 s)과 감속 표류가 비용 — 안전쌍에 쓰면 손해"], split=0.5)

# 8. 메커니즘 ② 위상 정렬
s = content_slide("전환 메커니즘 ②: 위상 정렬 — 가장 닮은 위상에서 시작", "사용자 제안: 다음 motion vector와 유사도가 높은 벡터부터 시작하자")
add_video(s, "align_hard", 0.55, 1.45, 4.1, 2.35, "hard (k=0): 오차 172.8°, 전복")
add_video(s, "align_align", 0.55, 4.05, 4.1, 2.35, "위상 정렬: 오차 0.9°, max yaw 10.5°")
rect(s, 4.9, 1.45, 4.2, 2.65, CARD)
add_text(s, 5.05, 1.52, 3.9, 2.55, [
    {"text": "알고리즘", "size": 12.5, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "M: 새 gait의 MotionMatrix (14 × 위상 수), 현재 벡터 m ∈ {±1}¹⁴", "size": 10.5, "bullet": True},
    {"text": "각 열과 m의 내적 = (일치 관절 수) − (불일치 관절 수)", "size": 10.5, "bullet": True},
    {"text": "k* = argmax(Mᵀm) → 그 위상에서 새 gait 시작 (지연 0)", "size": 10.5, "bullet": True},
    {"text": "역재생 gait는 getMvec(k)가 열 −k를 반환 → k = −k* (전환 학습 준비 중 발견·수정)", "size": 10.5, "bullet": True},
], margin=0)
bar_chart(s, ["bl→right", "bl→diag_fr", "br→diag_fl"], [("hard (k=0)", [152.5, 61.4, 155.7]), ("위상 정렬", [1.0, 0.5, 3.1])],
          4.9, 4.2, 4.2, 2.7, title="위험 3쌍 방향 오차 (°)", colors=[RED, MINT], fmt="0.0")
intent_result(s, 9.35, 1.45, 3.4, 5.45,
              ["gait 부호의 연속성을 직접 맞추면 지연 없이 전환이 가능한지", "페이드의 시간 비용을 없앨 근본책 탐색"],
              ["위험 3쌍 152/61/156° → 1.0/0.5/3.1°, 시간 지연·감속 없음", "단, 전면 적용은 사각형 0.193→0.448로 악화 — 전문가가 k=0에서만 학습돼 정렬 시작에 취약", "→ 위험쌍에만 선택 적용", "확장 아이디어(이전 W개 벡터 윈도우 매칭)는 실측 기각: W=10에서 안전쌍 붕괴(113°)"], split=0.3)

# 9. 3방식 A/B + 음성 결과
s = content_slide("결정적 A/B: hard vs fade vs 위상 정렬, 그리고 기각된 확장 3건", "동일 커맨더·시드에서 경로별 cross-track 오차")
bar_chart(s, ["square", "star", "gauntlet"], [("hard", [0.193, 0.742, 0.485]), ("fade", [0.193, 0.497, 0.301]), ("align", [0.193, 0.433, 0.472])],
          0.55, 1.45, 6.2, 3.3, title="경로별 CTE 평균 (m) — 낮을수록 좋음", colors=[RED, AMBER, MINT], fmt="0.000")
add_text(s, 0.55, 4.8, 6.2, 0.6, [{"text": "square는 위험쌍이 발동하지 않아 3방식 동일. star는 align, gauntlet(위험쌍 집중)은 fade가 우세 — 둘 다 hard를 확실히 이김.", "size": 10.5, "color": MUTED}], margin=0)
rows = [["기각된 확장", "실험", "결과 (왜 안 되나)"],
        ["윈도우 위상 매칭", "최근 W=5/10 벡터 궤적으로 정렬", "W=1이 전 쌍 ≤3.1°인데 W=5 right→left 10.2°, W=10 diag_fl→fr 113.6° — 주기 불일치·역재생 비선형, 과거는 이미 물리 상태에 반영"],
        ["정렬 + 페이드 결합", "위상 정렬 후 페이드(10/5/10)", "diag_bl→diag_fr 1°→76° 붕괴 — 정지 구간에 몸이 관성으로 변형되는데 k는 정지 전 벡터로 고정"],
        ["정지 제거 결합", "페이드(10/0/10) + 정렬", "붕괴는 사라지나(2°) 정렬 단독을 넘지 못함(right→left 1→7°) — 부호 연속성이 확보된 뒤 페이드는 순수 교란"]]
add_table(s, rows, 7.0, 1.45, 5.75, 3.95, col_w=[1.35, 1.6, 2.8], size=9.5)
intent_result(s, 0.55, 5.5, 12.2, 1.4,
              ["단일 메커니즘으로 충분한지, 결합·확장이 이득인지 실측으로 결정"],
              ["위상 정렬(W=1) 단독이 최선 — 원인(부호 충돌)을 제거하면 페이드는 중복. 음성 결과는 재논의 방지용으로 CLAUDE_CHANGES에 기록"], split=0.45)

# 10. 매끄러움
s = content_slide("안정을 넘어 매끄러움: 지표 정의 → 5후보 계측 → 하이브리드", "사용자 질문 \"안정적으로, 그리고 매끄럽게\" — 저크를 재기 시작하다")
add_video(s, "smooth_align_only", 0.55, 1.45, 3.9, 2.25, "align만: 가속 스파이크 155")
add_video(s, "smooth_align_xfade", 0.55, 3.95, 3.9, 2.25, "align + 크로스페이드 12스텝: 57 (−63%)")
rows = [["후보 (위험쌍 평균)", "방향오차°", "헤딩 저크°", "가속 스파이크"],
        ["hard", "123.2", "165", "119"],
        ["align", "1.6", "120", "142"],
        ["align + 토크 저역통과", "1.0", "144", "151"],
        ["align + 크로스페이드", "0.9", "99", "89"],
        ["align + 정책 블렌딩", "1.2", "141", "116"]]
add_table(s, rows, 4.7, 1.45, 4.4, 2.6, col_w=[1.9, 0.8, 0.85, 0.85], size=9.5)
add_text(s, 4.7, 4.1, 4.4, 0.75, [{"text": "안전쌍에 진폭 변조(크로스페이드/저역통과/softstart)를 쓰면 방향오차 5~28°로 악화 → 위험쌍에만 적용. 크로스페이드는 위상 정렬 위에서만 유효(부호 문맥 일치 필요).", "size": 10, "color": MUTED}], margin=0)
bar_chart(s, ["square", "star", "gauntlet"], [("align (위험쌍만)", [0.193, 0.433, 0.472]), ("align + xfade (위험쌍만)", [0.193, 0.334, 0.345])],
          4.7, 4.9, 4.4, 2.0, title="경로 CTE (m): 하이브리드 효과", colors=[NAVY, MINT], fmt="0.000", label_size=7.5)
intent_result(s, 9.35, 1.45, 3.4, 5.45,
              ["\"매끄러움\"을 스텝당 속도·헤딩 변화, IMU 가속 스파이크로 정량화", "안정(전복 없음)과 매끄러움(저크)을 동시에 최적화하는 조합 탐색"],
              ["채택: 안전쌍 즉시 k=0 / 위험 3쌍 위상 정렬 + 12스텝 행동 크로스페이드", "위상 정렬 = 안정, 크로스페이드 = 매끄러움 — 역할 분담", "보너스로 경로 CTE도 개선: star 0.433→0.334, gauntlet 0.472→0.345"], split=0.34)

# 11. 방위 화살표
s = content_slide("방위 렌더: 웨이포인트 목표 방위(초록) vs 로봇 yaw(파랑)", "\"회전은 아직 감안하지 않았다\"는 지적 → 1단계로 시각화부터")
add_video(s, "experts_star", 0.55, 1.45, 5.2, 2.8, "별 1.5 m — 초록 화살표: 접선 목표 방위, 파랑: 몸통 yaw")
fit_image(s, FIGS["experts_star_traj"], 5.95, 1.45, 3.3, 2.8)
rect(s, 0.55, 4.75, 8.7, 2.15, CARD)
add_text(s, 0.75, 4.83, 8.3, 2.0, [
    {"text": "구현", "size": 12.5, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "웨이포인트를 (x, y, yaw°)로 확장 — 기본 방위 = 접선(다음 점 방향, 마지막 점은 도착 방향)", "size": 11, "bullet": True},
    {"text": "MuJoCo ARROW 마커: pos에서 로컬 +z로 뻗음 → z축=방위, y축=세계 +Z 회전행렬 (0/90/180° 렌더 실증)", "size": 11, "bullet": True},
    {"text": "trajectory.png에도 목표 방위 quiver 추가. 추종 결과 수치 불변(사각형 0.193 / 별 0.334) — 렌더 전용 변경 확인", "size": 11, "bullet": True},
], margin=0)
intent_result(s, 9.5, 1.45, 3.25, 5.45,
              ["크랩워크 추종이 몸통 yaw를 전혀 제어하지 않음을 영상에서 드러내기", "2단계(도달 시 CW/CCW로 제자리 회전 후 진행)의 근거 마련"],
              ["파란 화살표는 내내 +X, 초록 목표는 꼭짓점마다 90°씩 회전 — 방위 오차가 한눈에 보임", "2단계는 회전→직진이라는 새 전환 유형 검증이 필요 — 대신 전환 학습(Part 2)으로 우선순위 이동"], split=0.4)

# 12. 섹션
dark_slide("Part 2. 전환 학습 —\n전문가 증류와 전환 커리큘럼 RL", "외부 메커니즘이 아니라 정책 자신이 전환을 흡수하도록: 증류로 출발선을 옮기고, 무작위 전환 속에서 미세조정한다", kicker="PART 2")

# 13. 설계 결정
s = content_slide("설계 결정 3가지와 근거", "사용자 요청: \"이전 정책에서 이어서, 모든 쌍을 랜덤으로, 시점·위치도 다양하게\"")
rows = [["결정", "선택지", "선택과 근거"],
        ["출발점 (warm-start)", "forward 전문가 가중치 / 10명 증류(Phase B)", "증류. 9개 명령을 RL로 새로 익히는 불확실성(속도·망각)을 제거해 RL이 \"전환\"만 배우게 함. 증류는 정답(전문가 행동)이 있는 회귀라 분 단위"],
        ["전환 메커니즘", "k0 / align / random(50:50)", "align. 물리적으로 가장 연속이고, 정책이 정렬 시작을 학습하면 k=0 전문가의 취약점이 사라짐. 배포도 단일 메커니즘. 크로스페이드는 두 정책이 필요해 단일 정책엔 정의 불가"],
        ["할인율 γ", "0.95 (방위 계보) / 0.99 (회전 계보)", "0.99. 전환 후 ~100스텝 뒤의 낙상을 critic이 보려면 유효 지평 100스텝 필요(0.95는 20스텝). 학생 critic도 0.99 return에 사전 회귀"],
        ["Stage 1 옵티마이저", "검증 레시피", "lr 1e-4, n_epochs 2, target_kl 0.04, 40M. 정책 std는 보수적 log_std −1.2로 시작"]]
add_table(s, rows, 0.55, 1.45, 12.2, 3.9, col_w=[1.9, 2.9, 7.4], size=10.5)
rect(s, 0.55, 5.55, 12.2, 1.35, NAVY)
add_text(s, 0.8, 5.65, 11.7, 1.2, [
    {"runs": [("설명 방식에 대한 피드백  ", {"bold": True, "color": MINT}), ("선택지만 던진 첫 질문에 \"비약이 많다\"는 지적 → 각 선택지의 배경·의미·비용·위험을 풀어 설명한 뒤 결정. ", {"color": WHITE}),
              ("증류 소요 시간(1~2시간)에 대한 의문에는 \"새 능력의 발견(RL)이 아니라 있는 능력을 옮겨 담는 회귀(BC)\"라는 구분으로 답함.", {"color": WHITE})], "size": 12},
], margin=0)

# 14. 증류 파이프라인
s = content_slide("전문가 증류 파이프라인 (training/distill_experts.py)", "10명 전문가 → 명령 조건부 단일 정책, PPO 체크포인트 형식으로 저장")
steps = [("수집", "전문가 10명을 통합 env(명령 고정, RL과 동일 보상)에서 병렬 롤아웃 — 원본 관측·전문가 행동·보상 기록"),
         ("통합 정규화", "전체 관측으로 학생 전용 obs_rms 생성 (전문가는 각자 통계, 학생은 하나)"),
         ("BC + critic", "PPO MlpPolicy 동일 구조. actor: MSE 모방 / critic: γ=0.99 MC return 회귀(절단 꼬리 마스크) / log_std −1.2"),
         ("DAgger", "학생을 굴려 방문 상태에 전문가 라벨 → 데이터에 합쳐 재학습 (오차 누적 보정)"),
         ("검증", "명령별 학생 vs 전문가 10 에피소드: 리턴·낙상·진행 속도·yaw·앵커"),
         ("패키징", "model.zip + vecnormalize.pkl(쌍) + metadata + DISTILL_REPORT.md → train.py resume 호환")]
step_row(s, 0.55, 1.5, 12.2, steps[:3], text_size=10.5)
step_row(s, 0.55, 3.25, 12.2, steps[3:], text_size=10.5, fill=NAVY, start=4)
intent_result(s, 0.55, 5.0, 12.2, 1.9,
              ["RL 전에 \"10개 명령을 이미 할 줄 아는\" 출발점 만들기 (스승을 넘진 못해도 전환을 배울 준비)"],
              ["v1(결정론 롤아웃만): 데이터 안 모방은 정확(검증 MSE 0.0025)했지만 닫힌 루프에서 절반의 명령이 실패 → 공변량 이동", "처방: 전문가 자체 가우시안 노이즈로 실행한 롤아웃(DART식, 라벨은 평균 행동) + DAgger"], split=0.4)

# 15. 증류 결과
s = content_slide("증류 결과: 공변량 이동 → DART 노이즈 + DAgger → 9/10 합격", "policies/unified/00_distilled — 총 180만 샘플, 최종 검증 MSE 0.0017")
cmds = ["forward", "left", "right", "diag_fl", "diag_fr", "backward", "diag_bl", "diag_br", "ccw", "cw"]
v1 = [0.42, -0.08, -0.19, 0.54, -0.30, 0.48, 0.69, 0.80, 1.09, 0.23]  # diag_fr 실제 −2.57 (표시 −0.30 클립)
fin = [1.00, 0.98, 0.99, 0.98, 1.00, 0.95, 1.00, 1.00, 1.01, 0.60]
bar_chart(s, cmds, [("v1 결정론 롤아웃만", v1), ("최종 (DART+DAgger×4)", fin)], 0.55, 1.45, 8.0, 3.6,
          title="명령별 학생 리턴 / 전문가 리턴 (1.0 = 전문가 동급)", colors=[RED, MINT], fmt="0.00", ymin=-0.4, ymax=1.2, label_size=7.5)
add_text(s, 0.55, 5.05, 8.0, 0.4, [{"text": "v1의 diag_fr는 실제 −2.57(역방향 이동)이며 표시는 −0.30으로 클립. v1은 left/right/cw 낙상 100%.", "size": 9.5, "color": MUTED}], margin=0)
rect(s, 0.55, 5.5, 8.0, 1.4, CARD)
add_text(s, 0.75, 5.58, 7.6, 1.3, [
    {"text": "cw만 미달(0.60)인 이유 — \"칼날 상태\"", "size": 12, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "yaw 0.592 rad/s 정상이나 앵커가 서서히 밀려 729스텝에 종료(결정론). 행동 노이즈 0.05면 8회 중 5회 1000스텝 생존", "size": 10.5, "bullet": True},
    {"text": "전문가 자체 여유가 36스텝(0.2 m 초과 최장 24/60). BC 라벨에 \"앵커 복귀\" 행동이 없어 DAgger로 개선되지 않음 → RL 단계가 교정할 알려진 출발 조건", "size": 10.5, "bullet": True},
], margin=0)
intent_result(s, 8.8, 1.45, 3.95, 5.45,
              ["전문가 대비 90% 이상·낙상 악화 없음을 합격 기준으로 검증", "미달 명령은 데이터 보강/DAgger로 처방"],
              ["v2 (결정론 40만 + 노이즈 40만 + DAgger 2회): 9/10 명령 0.96~1.14, 낙상 0", "DAgger 3·4회 추가: forward/diag_fr/bl/br 1.00, ccw 1.01, 나머지 0.95~0.99", "9/10 합격, cw는 RL로 이월 — 증류 총 소요 약 9분(수집 3분 포함)"], split=0.32)

# 16. 전환 커리큘럼 환경
s = content_slide("전환 커리큘럼 환경: 무작위 쌍·시점·위상, 관측 즉시 재생성", "plane-unified-v0의 switch_enabled 옵션 (기본 꺼짐 → 기존 동작 보존)")
# 에피소드 타임라인 다이어그램
rect(s, 0.55, 1.5, 7.9, 1.75, CARD)
add_text(s, 0.75, 1.58, 7.5, 0.3, [{"text": "에피소드 타임라인 (horizon 1000스텝 = 50 s)", "size": 11.5, "bold": True, "color": NAVY}], margin=0)
tx, tw = 0.85, 7.3
rect(s, tx, 2.35, tw, 0.22, LINE, rounded=False)
segs = [(0, 0.28, "forward", NAVY), (0.28, 0.55, "diag_bl", MINT_D), (0.55, 0.82, "ccw", AMBER), (0.82, 1.0, "right", BLUE)]
for a, b, lab, col in segs:
    rect(s, tx + a * tw, 2.35, (b - a) * tw, 0.22, col, rounded=False)
    add_text(s, tx + a * tw, 2.6, (b - a) * tw, 0.3, [{"text": lab, "size": 9, "color": TEXT, "align": PP_ALIGN.CENTER}], margin=0)
for a in (0.28, 0.55, 0.82):
    badge(s, tx + a * tw - 0.11, 2.16, 0.22, "↕", RED, size=9)
add_text(s, 0.75, 2.9, 7.5, 0.35, [{"text": "↕ 전환 시점: 1~4회, 최소 체류 100스텝 간격으로 균등 무작위. 다음 명령은 현재 명령 제외 균등(90 순서쌍). 초기 위상 k 무작위.", "size": 9.5, "color": MUTED}], margin=0)
rows = [["설계 항목", "내용"],
        ["전환 적용 시점", "물리 스텝 뒤·관측 반환 전 → 정책이 그 스텝 관측에서 새 motion vector/joy를 봄 (1스텝 불일치 없음). 해당 스텝 보상은 옛 명령 기준"],
        ["전환 메커니즘", "switch_mode align (k0 / random 옵션). 역재생 gait는 k = −argmax"],
        ["콜백 지표", "env_switch/post50_reward, fail_within100, 도착 명령별 분해, per_episode"],
        ["스모크 (전문가 구동)", "40 에피소드, 전환 50회·35쌍, 정렬 정확성 역재생 12회 포함 전부 통과, 간격 ≥100. 전문가 스위칭은 27/40 에피소드가 전환 후 33~121스텝 뒤 낙상 — 학습 대상 그 자체"]]
add_table(s, rows, 0.55, 3.45, 7.9, 3.45, col_w=[1.7, 6.2], size=9.5)
intent_result(s, 8.7, 1.5, 4.05, 5.4,
              ["\"모든 쌍을 랜덤으로, 시점·상태도 다양하게\" 요청을 환경 옵션으로 구현", "정책이 전환을 관측하고 반응하도록 학습·배포 규약 정합"],
              ["스모크에서 잡은 함정 2건: ① env 인자명 max_episode_steps는 gym.make가 가로챔 → episode_horizon으로 개명 ② set_gait 역재생 정렬 버그(k=col → −col) — 위험 3쌍이 모두 순재생 목표라 그동안 드러나지 않음", "train.py resume·콜백·TB 기록까지 스모크 통과"], split=0.3)

# 17. 앵커 문제 → 근접 보상
s = content_slide("Stage 1 첫 시도의 함정: 회전 진입 전환의 관성 vs 앵커 종료 규칙", "2M 점검에서 ccw 0.60 / cw 0.63 실패율 → 증류 정책으로 직접 진단")
rows = [["진단 (증류 정책, 회전 진입 전환 24회)", "값"],
        ["100스텝 내 종료", "54% (선형 진입은 9%)"],
        ["전환 직전 속도", "평균 0.44 m/s"],
        ["전환 후 앵커 최대거리", "평균 0.37 m (실패 사례 0.51 m), 88%가 0.2 m 초과"],
        ["60스텝 뒤 재앵커 시 이탈", "0.04 m, 0.2 m 초과 0% — 미끄러짐은 3 s 안에 멈춤"]]
add_table(s, rows, 0.55, 1.45, 5.9, 2.45, col_w=[3.3, 2.6], size=10)
rect(s, 0.55, 4.05, 5.9, 2.85, CARD)
add_text(s, 0.75, 4.13, 5.5, 2.75, [
    {"text": "해석", "size": 12, "bold": True, "color": NAVY, "space_after": 3},
    {"text": "앵커가 전환 순간 COM에 고정되는데 몸은 0.44 m/s로 미끄러져 관성만으로 0.2 m를 넘고, 회전 gait는 제동·복귀를 못 하니 60스텝 규칙에 걸림", "size": 10.5, "bullet": True},
    {"text": "정책이 고칠 수 없는 규칙 문제 + \"무작위 회전 전환에 대비해 평소 느리게\"라는 왜곡 인센티브 위험", "size": 10.5, "bullet": True},
    {"text": "유예(grace) 재앵커를 제안했으나 사용자가 \"종료 대신 앵커에 가까우면 더 높은 보상\"을 제안 → 미끄러짐이 치명이 아닌, 진폭 조절로 줄일 수 있는 학습 가능한 손실이 됨", "size": 10.5, "bullet": True},
], margin=0)
rows2 = [["앵커 거리 d", "근접 보상", "앵커 비용", "스텝 합계*"],
         ["0 m", "+10", "0", "+35"], ["0.1 m", "+5", "−5", "+25"], ["0.2 m", "0", "−10", "+15"],
         ["0.4 m (관성 평균)", "0", "−20", "+5"], ["≥ 0.55 m", "0", "≤ −27", "음수"]]
add_table(s, rows2, 6.7, 1.45, 6.05, 2.45, col_w=[1.9, 1.3, 1.3, 1.55], size=10)
add_text(s, 6.7, 3.92, 6.05, 0.3, [{"text": "* 목표 속도 회전 보상 22.5 + 건강 2 기준. 근접 보상 10·max(0, 1−d/0.2), 기존 포화 비용 50·min(d, 2) 유지, 앵커 종료 제거.", "size": 9, "color": MUTED}], margin=0)
intent_result(s, 6.7, 4.3, 6.05, 2.6,
              ["회전 진입 실패가 정책 실력인지 규칙 문제인지 분리", "종료 대신 연속 보상으로 대체하는 설계의 스텝당 수지 검증"],
              ["검증: 보상 프로파일 설계대로(d<0.1 +30.7 / 0.1–0.2 +22.4 / 0.2–0.3 +17.8), 회전 진입 종료 54%→19%(잔여는 낙상), 기본값 env는 옛 동작 그대로", "첫 run(4.25M) 중단·보존, 증류 정책에서 재시작"], split=0.42)

# 18. Stage 1 결과
s = content_slide("Stage 1 결과 (40M): 붕괴 없이 상승, 회전 진입 실패 해소", "run 20260909-153324 · resume = 증류 정책 · lr 1e-4 / ep 2 / target_kl 0.04 / γ 0.99")
line_chart(s, [("평가 리턴 (10 ep)", CURVES["s1_eval"]), ("롤아웃 에피소드 리턴 (이동평균)", CURVES["s1_ep_rew"])],
           0.55, 1.4, 4.15, 2.6, title="리턴", colors=[MINT, NAVY], fmt="#,##0")
line_chart(s, [("explained_variance", CURVES["s1_ev"])], 4.85, 1.4, 3.95, 2.6, title="critic 설명력", colors=[BLUE], ymin=-0.2, ymax=1.0, legend=False)
line_chart(s, [("전환 후 100스텝 내 실패율 (이동평균)", CURVES["s1_fail"])], 8.95, 1.4, 3.8, 2.6, title="전환 실패율", colors=[RED], ymin=0, ymax=0.5, legend=False)
f0, f1 = CURVES["s0_fail_to"], CURVES["s1_fail_to"]
bar_chart(s, cmds, [("첫 run 2M (앵커 종료 규칙)", [round(f0[c], 3) for c in cmds]), ("Stage 1 말기 (근접 보상)", [round(f1[c], 3) for c in cmds])],
          0.55, 4.1, 7.2, 2.8, title="도착 명령별 전환 후 100스텝 내 실패율", colors=[RED, MINT], fmt="0.00", ymax=0.8, label_size=7)
intent_result(s, 8.0, 4.1, 4.75, 2.8,
              ["BC 초기값 보존 여부와 전환 능력 향상 여부 확인"],
              ["최고 평가 22,624 @27.5M · 말기 ep_rew −16K→+13.0K, ep_len 873/1000", "전환 후 실패 0.123→0.099, 50스텝 보상 −31.9→−8.5, EV 0.92, KL 0.0010(유휴)→Stage 2 ep 3", "회전 진입(ccw/cw) 실패 0.6대→0.10/0.03 · 남은 난관 diag_fr·diag_bl 0.33 (δ=203)"], split=0.24)
notes(s, "1.5M 부근 KL 0.033·clip 0.24·EV≈0의 과도기(보상 분포 변화에 critic 지연)가 있었으나 4M 이후 회복. 정책 std는 0.301로 고정(ent_coef 0).")

# 19. Stage 2 + 정책 영상
s = content_slide("Stage 2 진행 상황 (n_epochs 3) — 안정적이나 정체 조짐", f"자료 작성 시점 누적 {CURVES.get('s2_last_step', 48):.1f}M · Stage 3 레버 검토")
line_chart(s, [("평가 리턴 (20 ep)", CURVES.get("s2_eval", [])), ("롤아웃 에피소드 리턴 (이동평균)", CURVES.get("s2_ep_rew", []))],
           0.55, 1.4, 5.0, 2.9, title="Stage 2 리턴 (누적 스텝)", colors=[MINT, NAVY], fmt="#,##0")
line_chart(s, [("approx_kl (이동평균)", CURVES.get("s2_kl", []))], 5.7, 1.4, 3.4, 2.9, title="approx_kl (target 0.04)", colors=[AMBER], legend=False, ymin=0, fmt="0.000")
add_video(s, "stage1_train", 9.25, 1.4, 3.5, 2.9, "학습 영상: 무작위 전환 속 정책 (Stage 1 말기)")
rows = [["지표", "Stage 1 말기", "Stage 2 8M 지점"],
        ["평가 리턴 최고 / 최근 평균", "22,624 / 15,115", "21,450 / 15,841"],
        ["롤아웃 에피소드 리턴", "13.0K", "13.3K (횡보)"],
        ["explained_variance", "0.92", "0.92~0.97"],
        ["approx_kl / clip_fraction", "0.0010 / 0.0015", "0.0004~0.0076 / ≈0"],
        ["정책 std", "0.301", "0.301 (고정)"]]
add_table(s, rows, 0.55, 4.5, 6.6, 2.4, col_w=[2.6, 2.0, 2.0], size=10)
intent_result(s, 7.4, 4.5, 5.35, 2.4,
              ["검증 레시피(KL 유휴 → ep 3)가 이 과제에서도 통하는지"],
              ["ep 3에도 KL이 target의 1/20 — 무작위 전환으로 advantage가 잡음에 묻히고 탐색 std 0.30이 작아 신호가 약한 것으로 추정", "Stage 3 레버: lr 1e-4→2e-4 (1순위, 신뢰영역 여유 큼), ep 4, 탐색 폭 확대(정책 영향 있어 논의 필요)"], split=0.3)

# 20. 통합 정책 경로 추종
s = content_slide("통합 정책 단독 경로 추종: 전문가 스위칭 없이 정책 하나가 전환까지", "Stage 1 final(40M) · 전환은 학습과 동일 규약(위상 정렬 + 관측 즉시 재생성), 크로스페이드 없음")
add_video(s, "unified_square", 0.55, 1.4, 3.9, 2.2, "사각형: 0.180 m / 8회 / 37.5 s")
add_video(s, "unified_star", 4.7, 1.4, 3.9, 2.2, "별: 0.343 m / 15회 / 58.8 s")
add_video(s, "unified_gauntlet", 8.85, 1.4, 3.9, 2.2, "gauntlet: 0.253 m / 13회 / 58.8 s")
bar_chart(s, ["square", "star", "gauntlet"], [("전문가 스위칭+xfade", [0.193, 0.334, 0.345]), ("통합 정책", [0.180, 0.343, 0.253])],
          0.55, 3.95, 4.0, 2.95, title="CTE 평균 (m)", colors=[NAVY, MINT], fmt="0.000", label_size=8)
bar_chart(s, ["square", "star", "gauntlet"], [("전문가 스위칭+xfade", [20.0, 42.5, 128.8]), ("통합 정책", [37.5, 58.8, 58.8])],
          4.7, 3.95, 4.0, 2.95, title="완주 시간 (s)", colors=[NAVY, MINT], fmt="0.0", label_size=8)
intent_result(s, 8.85, 3.95, 3.9, 2.95,
              ["전환 학습의 효과를 전문가 스위칭(+하이브리드) 기준선과 같은 경로에서 비교"],
              ["gauntlet(위험 전환 집중): CTE −27%, 전환 34→13회, 시간 절반 — 목적 그대로", "사각형·별: CTE 동급, 주행 시간은 길고 전환 잦음(순항 속도·전환 직후 감속) → Stage 2·3 관찰 포인트"], split=0.3)

# 21. 통찰
s = content_slide("배운 것 7가지")
insights = [
    ("전환의 본질은 부호 정합", "GD에서 방향은 gait가 정한다. 전환 실패는 정책이 아니라 연속된 두 gait의 위상·부호 충돌이었다."),
    ("위상 정렬 > 페이드", "원인(부호 충돌)을 제거하면 시간 지연 없이 해결된다. 페이드는 증상 완화이며 정렬 위에 얹으면 중복·교란이다."),
    ("선택 적용의 원칙", "전문가는 k=0에서만 학습돼 정렬 시작에 취약 — 위험쌍에만 정렬(+크로스페이드), 안전쌍은 k=0."),
    ("음성 결과도 자산", "윈도우 매칭·align+fade·정지 제거·전면 페이드는 실측으로 기각하고 기록해 재논의를 막았다."),
    ("증류는 분 단위, 함정은 공변량 이동", "결정론 전문가+동일 초기 자세는 얇은 분포를 만든다. 노이즈 주입(DART)과 DAgger가 절반의 실패를 9/10 합격으로 바꿨다."),
    ("규칙이 물리를 이길 수 없다", "이동 중 회전 진입의 관성 미끄러짐을 종료로 처벌하면 왜곡 인센티브가 생긴다. 연속 보상으로 바꾸자 실패 54%→19%."),
    ("단일 정책의 이점은 어려운 곳에서 드러난다", "쉬운 경로는 동급, 위험 전환이 몰린 gauntlet에서 CTE −27%·전환 1/3·시간 절반."),
]
for i, (t, d) in enumerate(insights):
    col, row = i % 2, i // 2
    x = 0.55 + col * 6.2
    y = 1.35 + row * 1.42
    if i == 6:
        x = 0.55
    rect(s, x, y, 6.0 if i < 6 else 12.2, 1.27, CARD)
    badge(s, x + 0.15, y + 0.18, 0.42, str(i + 1), MINT if i < 6 else NAVY)
    add_text(s, x + 0.7, y + 0.12, (6.0 if i < 6 else 12.2) - 0.85, 0.35, [{"text": t, "size": 12.5, "bold": True, "color": NAVY}], margin=0)
    add_text(s, x + 0.7, y + 0.5, (6.0 if i < 6 else 12.2) - 0.85, 0.75, [{"text": d, "size": 10.5, "color": TEXT}], margin=0)

# 22. 다음 단계
s = content_slide("다음 단계")
nxt = [("Stage 3 전환 학습", "Stage 2 KL 진단에 따라 lr 2e-4 또는 ep 4. 완료 후 정책 폴더 정리(policies/unified/01~03), 통합 정책 데모 재비교", MINT),
       ("방위 추종 2단계", "웨이포인트 도달 시 yaw 오차 ≥20°면 CW/CCW 회전 후 진행 — 회전→직진 전환 유형 검증, 통합 정책으로 직접 수행 가능", MINT),
       ("δ-보간 연속 조향", "heading ≈ 2δ 가설 검증 — 8-명령 양자화를 넘어 연속 방향 명령으로 (gait provider 확장 지점)", NAVY),
       ("지속 학습 (Phase D)", "새 작업 추가 시 망각 방지: Progress & Compress(증류+EWC), Kickstarting(교사 KL 정규화) — 참고문헌 §3·§6", NAVY),
       ("Sim-to-Real 준비", "마찰 무작위화(use_friction_chg) 재도입, 관측 지연·노이즈 강건성, 지형 굴곡(e_d2 > e_l2 파라미터 스터디 연계)", NAVY2)]
for i, (t, d, c) in enumerate(nxt):
    y = 1.4 + i * 1.08
    rect(s, 0.55, y, 12.2, 0.95, CARD)
    badge(s, 0.75, y + 0.26, 0.42, str(i + 1), c)
    add_text(s, 1.35, y + 0.1, 3.0, 0.75, [{"text": t, "size": 13, "bold": True, "color": NAVY}], margin=0, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, 4.4, y + 0.1, 8.2, 0.75, [{"text": d, "size": 11, "color": TEXT}], margin=0, anchor=MSO_ANCHOR.MIDDLE)

# 23. 참고문헌·산출물
s = content_slide("참고문헌과 산출물 위치", "docs/references_transition_learning.md — 8개 주제 48편, 서지정보 웹 검증")
rows = [["주제", "대표 문헌", "본 연구와의 대응"],
        ["정책 증류", "Rusu+ Policy Distillation (ICLR'16), Parisotto+ Actor-Mimic (ICLR'16), Merel+ NPMP (ICLR'19)", "10 전문가 → 단일 명령 조건부 정책"],
        ["BC / DAgger", "Ross+ DAgger (AISTATS'11), Laskey+ DART (CoRL'17)", "공변량 이동 처방: 노이즈 주입 + 학생 상태 라벨링"],
        ["BC→RL 워밍업", "Rajeswaran+ DAPG (RSS'18), Uchendu+ JSRL (ICML'23), Ball+ RLPD (ICML'23)", "critic 사전 회귀·보수적 std로 초기 붕괴 방지"],
        ["다중 보행·전환", "Yang+ MELA (Sci. Robot.'20), Margolis & Agrawal Walk These Ways (CoRL'22)", "보행 조건부 단일 정책, 전환 커리큘럼"],
        ["뱀 로봇·CPG 위상", "Hirose '93, Tesch+ '09, Ijspeert '08, Song+ GD (ICAE'25)", "serpenoid gait, 위상 정렬(위상 리셋 유사)"],
        ["지속 학습", "Kirkpatrick+ EWC (PNAS'17), Schwarz+ Progress & Compress (ICML'18), Schmitt+ Kickstarting ('18)", "Phase D: 작업 추가 시 망각 방지"]]
add_table(s, rows, 0.55, 1.45, 8.2, 3.9, col_w=[1.4, 4.2, 2.6], size=9.5)
rect(s, 8.95, 1.45, 3.8, 5.45, NAVY)
add_text(s, 9.15, 1.55, 3.4, 5.3, [
    {"text": "산출물", "size": 13, "bold": True, "color": MINT, "space_after": 6},
    {"text": "policies/unified/00_distilled/ — 증류 정책(model.zip + vecnormalize.pkl), DISTILL_REPORT.md", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
    {"text": "policies/unified/TRAINING_HISTORY.txt — 통합 계보 원장", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
    {"text": "training/distill_experts.py, training/path_following.py(--policy unified), training/configs/ppo_unified_transition_stage{1,2}.yaml", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
    {"text": "horcrux_env/envs/plane_unified_v1.py — 전환 커리큘럼·앵커 근접 보상·위상 정렬", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
    {"text": "runs/path_follow_demo/ — 모든 데모 영상·궤적·result.txt", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
    {"text": "CLAUDE_CHANGES.md — 요청 맥락·변경·수치가 담긴 변경 이력", "size": 10.5, "color": WHITE, "bullet": True, "bullet_color": MINT},
], margin=0)
add_text(s, 0.55, 5.5, 8.2, 1.4, [{"text": "문헌 검증: arXiv 초록·출판사·Crossref로 제목/저자/게재처/연도/ID 확인, 검증 실패로 제외한 항목 없음. 문서 말미에 파이프라인 구성요소↔문헌 대응표 수록.", "size": 10.5, "color": MUTED}], margin=0)

# 24. 부록: 설정 요약
s = content_slide("부록: Stage 1/2 설정 요약과 변경 이력 색인")
rows = [["구분", "항목", "값"],
        ["환경", "보상 계수 (frozen)", "forward 60 · efficiency 3 · healthy 2 · rotation_norm 10 · proj_dist 0 · ctrl 0"],
        ["환경", "종료", "롤 범위 이탈 30스텝(선형) / 60스텝(회전) · 앵커 종료 없음(anchor_terminate false)"],
        ["환경", "앵커 근접 보상", "10·max(0, 1−d/0.2) + 포화 비용 50·min(d, 2)"],
        ["환경", "전환 커리큘럼", "1~4회 · dwell 100 · align · 초기 위상 무작위 · horizon 1000 · 90쌍 균등"],
        ["PPO", "Stage 1 / Stage 2", "lr 1e-4 · n_epochs 2 → 3 · target_kl 0.04 · γ 0.99 · n_steps 512 · batch 512 · 5×512 tanh"],
        ["샘플링", "num_envs / fps", "8 subproc · ≈2,150 fps · 40M ≈ 5.2 h"],
        ["평가", "eval_freq / 에피소드", "250k · 10 (Stage 1) → 20 (Stage 2) 결정론"]]
add_table(s, rows, 0.55, 1.35, 12.2, 3.3, col_w=[1.0, 2.4, 8.8], size=10)
rect(s, 0.55, 4.85, 12.2, 1.55, CARD)
add_text(s, 0.75, 4.93, 11.8, 1.45, [
    {"text": "CLAUDE_CHANGES.md 주요 항목 (2026-09-08 ~ 09)", "size": 12, "bold": True, "color": NAVY, "space_after": 4},
    {"text": "위상 정렬 채택·3방식 A/B → 윈도우 매칭 기각 → align+fade 기각 → 정지 제거 진단 정정 → 매끄러움 하이브리드 → result.txt 헤더(+60배 중복 버그 수정)", "size": 10.5, "bullet": True},
    {"text": "방위 화살표 렌더 → 전환 학습 파이프라인(env·증류·콜백·YAML) → 증류 완료(v1 실패/v2/DAgger) → Stage 1 착수 → 앵커 근접 보상 설계·재시작 → Stage 1 완료 → Stage 2 착수 → 통합 정책 데모 모드", "size": 10.5, "bullet": True},
], margin=0)

prs.save(OUT)
print("saved", OUT, f"{OUT.stat().st_size/1e6:.1f} MB, slides", len(prs.slides))
