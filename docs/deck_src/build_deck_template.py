"""Horcrux 전환 학습 연구 정리 덱 — 사용자 템플릿(docs/PPT샘플.pptx, ETRI 4:3) 위에 재구성.

템플릿 규약(샘플 슬라이드에서 추출): 제목 플레이스홀더 "주제 (날짜) ― 소제목" 맑은 고딕 16pt bold 203864,
카드 = 둥근 사각형 EEF3FA / 테두리 C7D3E3 0.75pt, 카드 헤더 11.5pt bold 203864, ▪ 불릿 9.5~10.5pt 2E75B6,
캡션 8.5pt 8A8A8A, 표 헤더 203864(흰 글씨 10.5pt) / 본문 흰색, 보조 텍스트 9.5pt 595959.
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
TEMPLATE = ROOT / "docs" / "PPT샘플.pptx"
OUT = ROOT / "docs" / "Horcrux_transition_research_2026-09_template.pptx"
CURVES = json.load(open(SC / "curves.json"))
BENCH = json.load(open(SC.parent / "bench_ckpts.json")) if (SC.parent / "bench_ckpts.json").exists() else None

# ----------------------------------------------------------------------------- 템플릿 팔레트
NAVY = "203864"       # 제목/헤더
BLUE = "2E75B6"       # 불릿/강조
CARD, CARD_LINE = "EEF3FA", "C7D3E3"
TEXT, SUB, CAP = "262626", "595959", "8A8A8A"
ORANGE, GREEN, RED, TEAL = "E97132", "196B24", "C0392B", "156082"
WHITE = "FFFFFF"
FONT = "맑은 고딕"
DATE = "20260910"
TOPIC = "gait 전환 학습"
# 콘텐츠 영역 (4:3): x 0.55~9.45, y 1.25~6.85
X0, X1, Y0, Y1 = 0.55, 9.45, 1.25, 6.85
CW = X1 - X0

VIDEOS = {
    "experts_square": ROOT / "runs/path_follow_demo/20260909-105155_square/path_demo.mp4",
    "experts_star": ROOT / "runs/path_follow_demo/20260909-105200_star/path_demo.mp4",
    "align_hard": ROOT / "runs/path_follow_demo/align_showcase/bl_to_right_hard.mp4",
    "align_align": ROOT / "runs/path_follow_demo/align_showcase/bl_to_right_align.mp4",
    "smooth_align_only": ROOT / "runs/path_follow_demo/smooth_showcase/bl_to_right_align_only.mp4",
    "smooth_align_xfade": ROOT / "runs/path_follow_demo/smooth_showcase/bl_to_right_align_xfade.mp4",
    "unified_square": ROOT / "runs/path_follow_demo/20260909-220058_square_unified/path_demo.mp4",
    "unified_star": ROOT / "runs/path_follow_demo/20260909-220104_star_unified/path_demo.mp4",
    "unified_gauntlet": ROOT / "runs/path_follow_demo/20260909-220111_gauntlet_unified/path_demo.mp4",
    "stage1_train": ROOT / "runs/ppo_unified_transition_stage1/20260909-153324-183674_ppo_unified_transition_stage1/videos/iteration-009610-timesteps-039362560-episode-0.mp4",
    "fade_bl_to_right_fade_1p25s": ROOT / "runs/path_follow_demo/fade_showcase/bl_to_right_fade_1p25s.mp4",
    # 정책 시각화 (policy_showcase.py, S3 final, 오버레이 포함)
    "show_tour": ROOT / "runs/policy_showcase/20260910-111945_S3final/command_tour.mp4",
    "show_close_ok": ROOT / "runs/policy_showcase/20260910-111945_S3final/closeup_forward_to_diag_fr.mp4",
    "show_close_fail": ROOT / "runs/policy_showcase/20260910-111945_S3final/closeup_backward_to_diag_bl.mp4",
    "show_path_gauntlet": ROOT / "runs/policy_showcase/20260910-111945_S3final/path_gauntlet.mp4",
    "show_path_star": ROOT / "runs/policy_showcase/20260910-111945_S3final/path_star.mp4",
    "show_path_square": ROOT / "runs/policy_showcase/20260910-111945_S3final/path_square.mp4",
}
FIGS = {
    "experts_star_traj": ROOT / "runs/path_follow_demo/20260909-105200_star/trajectory.png",
    "unified_gauntlet_traj": ROOT / "runs/path_follow_demo/20260909-220111_gauntlet_unified/trajectory.png",
}

prs = Presentation(str(TEMPLATE))
# 샘플 슬라이드 제거 (레이아웃/마스터/테마는 유지)
sldIdLst = prs.slides._sldIdLst
for sldId in list(sldIdLst):
    prs.part.drop_rel(sldId.rId)
    sldIdLst.remove(sldId)
LAYOUT = {lay.name: lay for lay in prs.slide_layouts}
L_COVER, L_SECTION, L_TITLE_ONLY = LAYOUT["제목 슬라이드"], LAYOUT["간지"], LAYOUT["속지-제목만"]


def rgb(h):
    return RGBColor.from_string(h)


def _style_run(run, size, bold=False, color=TEXT, italic=False):
    f = run.font
    f.name = FONT
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.color.rgb = rgb(color)
    rPr = run._r.get_or_add_rPr()
    if rPr.find(qn("a:ea")) is None:
        ea = etree.SubElement(rPr, qn("a:ea"))
        ea.set("typeface", FONT)


def _bullet(para, level=0, char="▪", color=BLUE):
    pPr = para._p.get_or_add_pPr()
    indent = 0.16
    pPr.set("marL", str(Emu(Inches(indent * (level + 1)))))
    pPr.set("indent", str(-Emu(Inches(indent))))
    bu = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(bu, qn("a:srgbClr")).set("val", color)
    etree.SubElement(pPr, qn("a:buChar")).set("char", char)


def add_text(slide, x, y, w, h, paras, size=10, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, margin=0.04, space_after=2, line_spacing=1.05):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
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
            _bullet(para, p.get("level", 0), color=p.get("bullet_color", BLUE))
    return tb


def rect(slide, x, y, w, h, fill=CARD, line=CARD_LINE, rounded=True, radius=0.05):
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


def card(slide, x, y, w, h, header, bullets, size=9.5, fill=CARD, line=CARD_LINE, header_color=NAVY,
         text_color=TEXT, bullet_color=BLUE, header_size=11):
    """템플릿 카드: 헤더 + ▪ 불릿."""
    rect(slide, x, y, w, h, fill, line)
    add_text(slide, x + 0.12, y + 0.07, w - 0.24, 0.3, [{"text": header, "size": header_size, "bold": True, "color": header_color}], margin=0)
    add_text(slide, x + 0.12, y + 0.36, w - 0.24, h - 0.4,
             [{"text": b, "size": size, "color": text_color, "bullet": True, "bullet_color": bullet_color, "space_after": 2}
              if isinstance(b, str) else b for b in bullets], margin=0)


def intent_result(slide, x, y, w, h, intent, result, split=0.42, size=9.5):
    ih = h * split - 0.06
    card(slide, x, y, w, ih, "의도", intent, size=size)
    ry, rh = y + ih + 0.1, h - ih - 0.1
    card(slide, x, ry, w, rh, "결과 요약", result, size=size, fill=NAVY, line=None, header_color=WHITE, text_color=WHITE, bullet_color="9DC3E6")


def label(slide, x, y, w, text, size=11):
    add_text(slide, x, y, w, 0.3, [{"text": text, "size": size, "bold": True, "color": NAVY}], margin=0)


def caption(slide, x, y, w, text):
    add_text(slide, x, y, w, 0.28, [{"text": text, "size": 8.5, "color": CAP}], margin=0)


def note(slide, x, y, w, h, text, size=9.5):
    add_text(slide, x, y, w, h, [{"text": text, "size": size, "color": SUB}], margin=0)


def tag(slide, x, y, text, fill=BLUE, w=None):
    w = w or (0.16 * len(text) + 0.3)
    shp = rect(slide, x, y, w, 0.26, fill, None, radius=0.5)
    tf = shp.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    _style_run(r, 8, True, WHITE)


def badge(slide, x, y, d, text, fill=BLUE, size=10):
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
    _style_run(r, size, True, WHITE)


def content_slide(sub):
    s = prs.slides.add_slide(L_TITLE_ONLY)
    t = s.shapes.title
    tf = t.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    r = p.add_run()
    full = f"{TOPIC} ({DATE}) ― {sub}"
    r.text = full
    _style_run(r, 16 if len(full) <= 34 else (14 if len(full) <= 40 else 12.5), True, NAVY)
    return s


def section_slide(title, body):
    s = prs.slides.add_slide(L_SECTION)
    for ph in s.placeholders:
        idx = ph.placeholder_format.idx
        if idx == 0:
            tf = ph.text_frame
            tf.clear()
            r = tf.paragraphs[0].add_run()
            r.text = title
            _style_run(r, 26, True, WHITE)
        elif idx == 1:
            tf = ph.text_frame
            tf.clear()
            r = tf.paragraphs[0].add_run()
            r.text = body
            _style_run(r, 12, False, "DCE6F2")
    return s


def fit_image(slide, path, x, y, w, h):
    img = Image.open(path)
    ar = img.width / img.height
    bw, bh = w, h
    if bw / bh > ar:
        bw = bh * ar
    else:
        bh = bw / ar
    ox, oy = x + (w - bw) / 2, y + (h - bh) / 2
    slide.shapes.add_picture(str(path), Inches(ox), Inches(oy), Inches(bw), Inches(bh))
    return ox, oy, bw, bh


def add_video(slide, key, x, y, w, h=None, cap=None):
    """16:9 영상 (너비 기준), 아래 캡션. 반환: 하단 y."""
    h = h or w * 9 / 16
    rect(slide, x - 0.03, y - 0.03, w + 0.06, h + 0.06, "D9E2F0", None, radius=0.02)
    slide.shapes.add_movie(str(VIDEOS[key]), Inches(x), Inches(y), Inches(w), Inches(h),
                           poster_frame_image=str(POSTERS / f"{key}.png"), mime_type="video/mp4")
    if cap:
        caption(slide, x, y + h + 0.05, w, "▶ " + cap)
    return y + h + (0.33 if cap else 0.05)


def add_table(slide, rows, x, y, w, h, col_w=None, size=9, header=True):
    nr, nc = len(rows), len(rows[0])
    gf = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "1" if header else "0")
    tblPr.set("bandRow", "0")
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"
    if col_w:
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(h / nr)
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.015)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            is_head = header and i == 0
            _style_run(r, size + (0.5 if is_head else 0), is_head, WHITE if is_head else TEXT)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(NAVY if is_head else (CARD if i % 2 == 0 else WHITE))
    return tbl


def _chart_common(chart, title, legend=True, size=8):
    chart.font.size = Pt(size)
    chart.font.name = FONT
    chart.has_title = bool(title)
    if title:
        chart.chart_title.text_frame.text = title
        r = chart.chart_title.text_frame.paragraphs[0].runs[0]
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = rgb(NAVY)
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(8)


def bar_chart(slide, cats, series, x, y, w, h, title=None, colors=None, fmt="0.00", legend=True, ymin=None, ymax=None, label_size=7):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    _chart_common(ch, title, legend)
    plot = ch.plots[0]
    plot.gap_width = 70
    plot.overlap = -10
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = rgb(TEXT)
    for s_, c in zip(ch.series, colors or [NAVY, BLUE, ORANGE, RED, GREEN]):
        s_.format.fill.solid()
        s_.format.fill.fore_color.rgb = rgb(c)
    va, ca = ch.value_axis, ch.category_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E1E6EC")
    va.tick_labels.font.size = Pt(8)
    va.format.line.fill.background()
    if ymin is not None:
        va.minimum_scale = ymin
    if ymax is not None:
        va.maximum_scale = ymax
    ca.tick_labels.font.size = Pt(8)
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = rgb("C7D3E3")
    return ch


def line_chart(slide, series, x, y, w, h, title=None, colors=None, xtitle="steps (M)", legend=True, ymin=None, ymax=None, fmt=None):
    cd = XyChartData()
    for name, pts in series:
        s_ = cd.add_series(name)
        for px, py in pts:
            s_.add_data_point(px, py)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    _chart_common(ch, title, legend)
    for s_, c in zip(ch.series, colors or [BLUE, NAVY, ORANGE, RED]):
        s_.format.line.color.rgb = rgb(c)
        s_.format.line.width = Pt(1.5)
        s_.smooth = False
    va, ca = ch.value_axis, ch.category_axis
    for ax in (va, ca):
        ax.tick_labels.font.size = Pt(8)
        ax.format.line.color.rgb = rgb("C7D3E3")
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E1E6EC")
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
        ca.axis_title.text_frame.paragraphs[0].runs[0].font.size = Pt(8)
    return ch


def step_cards(slide, x, y, w, steps, cols, card_h, start=1, size=9, gap=0.12, fill=BLUE):
    cw_ = (w - gap * (cols - 1)) / cols
    for i, (t, d) in enumerate(steps):
        r_, c_ = divmod(i, cols)
        cx, cy = x + c_ * (cw_ + gap), y + r_ * (card_h + gap)
        rect(slide, cx, cy, cw_, card_h)
        badge(slide, cx + 0.1, cy + 0.1, 0.3, str(i + start), fill, size=9)
        add_text(slide, cx + 0.48, cy + 0.08, cw_ - 0.58, 0.34, [{"text": t, "size": 10, "bold": True, "color": NAVY}], margin=0)
        add_text(slide, cx + 0.1, cy + 0.46, cw_ - 0.2, card_h - 0.5, [{"text": d, "size": size, "color": TEXT}], margin=0)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


cmds = ["forward", "left", "right", "diag_fl", "diag_fr", "backward", "diag_bl", "diag_br", "ccw", "cw"]

# ============================================================================= 슬라이드
# 1. 표지
s = prs.slides.add_slide(L_COVER)
for ph in s.placeholders:
    idx = ph.placeholder_format.idx
    tf = ph.text_frame
    tf.clear()
    r = tf.paragraphs[0].add_run()
    if idx == 0:
        r.text = "뱀 로봇 경로 추종과 gait 전환 학습"
        _style_run(r, 30, True, NAVY)
    elif idx == 1:
        r.text = "연구 흐름 정리: 전문가 10명 → 경로 추종 데모 → 전환 메커니즘 → 전문가 증류 → 전환 커리큘럼 RL (2026-09-08 ~ 09-10)"
        _style_run(r, 12, False, SUB)
add_text(s, 3.31, 6.95, 3.38, 0.4, [{"text": "지능로봇시스템연구실", "size": 11, "color": SUB, "align": PP_ALIGN.CENTER}], margin=0)
notes(s, "2026-09-08~10 실험 정리. 수치는 CLAUDE_CHANGES.md / policies/unified/TRAINING_HISTORY.txt 기록값.")

# 2. 연구 흐름
s = content_slide("연구 흐름 요약")
flow = [
    ("전문가 로스터", "8방위 + CW/CCW 회전 정책 10개. 3-stage KL 튜닝 레시피로 각 ~85M 스텝"),
    ("경로 추종 데모", "웨이포인트 커맨더가 전문가를 스위칭. 사각형·별 완주 (CTE 0.19 / 0.33 m)"),
    ("전환 문제 발견", "\"backward/right 정책 문제\"의 진짜 원인은 gait 교체 순간의 위상 충돌"),
    ("전환 메커니즘 탐구", "페이드 → 위상 정렬 → 위험쌍 align+크로스페이드 하이브리드 (기각 3건)"),
    ("방위 화살표 렌더", "웨이포인트 목표 방위 vs 로봇 yaw 시각화 — 회전 미반영 확인"),
    ("전문가 증류", "BC + DART 노이즈 + DAgger 4회 → 9/10 명령 전문가 대비 0.95~1.01"),
    ("전환 커리큘럼 RL", "무작위 90쌍·시점·위상, 앵커 근접 보상 설계. Stage 1~3 (누적 120M) 완료"),
    ("통합 정책 검증", "정책 하나로 경로 추종: gauntlet CTE 0.345→0.223, 전환 34→7회, 시간 1/4 (S3 final)"),
]
step_cards(s, X0, 1.3, CW, flow, cols=4, card_h=1.55, size=8.5)
card(s, X0, 4.75, CW, 1.05, "핵심 메시지",
     ["GD 패러다임에서 \"방향은 gait, 세기는 정책\" — 전환의 본질은 gait 부호 패턴의 연속성이다.",
      "외부 메커니즘(위상 정렬)으로 연속성을 확보한 뒤, 정책 자체가 전환을 흡수하도록 학습시키는 것이 본 연구의 흐름."], size=9.5)
note(s, X0, 5.95, CW, 0.8, "본 자료의 모든 수치는 변경 이력(CLAUDE_CHANGES.md)·학습 원장(TRAINING_HISTORY.txt)·데모 result.txt의 기록값이며, 영상은 슬라이드에 임베드되어 있다(클릭 재생).", size=9)

# 3. 배경 ① GD·레시피·회전 설계
s = content_slide("배경 ① GD·튜닝 레시피")
rect(s, X0, 1.3, 4.3, 2.35)
add_text(s, X0 + 0.12, 1.37, 4.0, 0.3, [{"text": "Gait Decomposition (GD)", "size": 11, "bold": True, "color": NAVY}], margin=0)
bx = X0 + 0.15
for lab, col, txt in [("정책 출력", BLUE, "진폭 a∈[0,2.7]¹⁴\n(얼마나 세게)"), ("×", None, ""), ("gait 부호 패턴", NAVY, "motion vector ±1\n(어느 방향)"), ("=", None, ""), ("관절 토크", TEAL, "τ = a ⊙ mvec")]:
    if col is None:
        add_text(s, bx, 2.05, 0.3, 0.5, [{"text": lab, "size": 16, "bold": True, "color": CAP, "align": PP_ALIGN.CENTER}], margin=0)
        bx += 0.3
        continue
    rect(s, bx, 1.75, 1.1, 1.05, col, None)
    add_text(s, bx, 1.8, 1.1, 0.3, [{"text": lab, "size": 9, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    add_text(s, bx, 2.1, 1.1, 0.65, [{"text": txt, "size": 8, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    bx += 1.15
note(s, X0 + 0.12, 2.9, 4.05, 0.7, "정책은 진폭만, gait는 부호만 → 전환 시 관절 토크 부호가 바뀌는 순간이 문제의 근원", size=9)
card(s, 5.05, 1.3, 4.4, 2.35, "검증된 3-stage KL 튜닝 레시피 (10개 계보 재현)",
     ["Stage 1: lr 1e-4, n_epochs 2, target_kl 0.04 → 말기 KL ≪ 0.01이면 \"유휴\"",
      "Stage 2: n_epochs 3 → KL이 0.04에 붙으면 \"포화\"",
      "Stage 3: lr 5e-5 — 정책을 흔들지 않는 옵티마이저 수준 조정만",
      "모델과 VecNormalize 통계는 항상 쌍으로 보관"], size=9)
card(s, X0, 3.85, CW, 2.9, "회전 정책 v2 \"안정 우선\" 설계 (CW/CCW)",
     ["속도보다 속도의 안정: 45·clip(부호·yaw_vel, ±0.5) + 과속 페널티",
      "앵커: 시작점 0.2 m 이탈이 60스텝 지속되면 실패, 포화 앵커 비용 50·min(d, 2)",
      "종료 페널티 −1000 + γ 0.99 (v1의 무한 비용은 critic 붕괴 → 포화 비용으로 교정)",
      "is_terminated 이중 호출 결함 수정 (스텝당 1회 카운터)",
      "관측 계약: 97차원(센서 + motion vector 14 + joy 3), 행동 [−1,1]→[0,2.7], 5×512 tanh MLP"], size=9.5)

# 4. 배경 ② 로스터
s = content_slide("배경 ② 전문가 로스터")
rows = [["명령", "joy", "gait δ (역재생)", "명령", "joy", "gait δ (역재생)"],
        ["forward", "(1, 0)", "0", "backward", "(−1, 0)", "0 (역)"],
        ["left", "(0, 1)", "45", "diag_bl", "(−.71, .71)", "203 (역)"],
        ["right", "(0, −1)", "225", "diag_br", "(−.71, −.71)", "23 (역)"],
        ["diag_fl", "(.71, .71)", "23", "ccw", "yaw +1", "315"],
        ["diag_fr", "(.71, −.71)", "203", "cw", "yaw −1", "135"]]
label(s, X0, 1.3, CW, "검증된 10개 명령 (공통 진폭/시간 파라미터 30, 30, 40, 40)")
add_table(s, rows, X0, 1.65, CW, 2.2, col_w=[1.3, 1.35, 1.8, 1.3, 1.35, 1.8], size=9)
card(s, X0, 4.05, 4.35, 2.7, "gait 대수 (실측으로 검증)",
     ["y-거울 = δ+180° (부호 반전이 아님 — δ=−45/−23은 수치로 기각)",
      "후진 계열 = 반대 전진 gait의 시간 역재생 (reverse 플래그)",
      "회전 CW/CCW = δ 135 / 315 거울쌍",
      "plane_v3.py 주석 표의 부호 반전 거울 항목은 모두 오류"], size=9.5)
card(s, 5.1, 4.05, 4.35, 2.7, "전문가 성능 (고정 명령, 1000스텝)",
     ["선형 8명령 진행 속도 0.45~0.68 m/s, 낙상 0",
      "회전 yaw 0.58~0.60 rad/s, 앵커 최대 0.25 m (여유 36스텝)",
      "가장 느린 전문가 diag_fr (0.455 m/s) — 뒤에서 δ=203 전환 난이도와 연결",
      "정책 폴더: policies/path_tracking/*, policies/rotation/* (원장 TRAINING_HISTORY.txt)"], size=9.5)

# 5. 간지 Part 1
section_slide("Part 1. 경로 추종 데모와 전환 메커니즘", "전문가 10명을 스위칭해 사각형·별을 그린다 — 그리고 전환의 물리를 이해한다")

# 6. 데모 설계
s = content_slide("경로 추종 데모")
yb = add_video(s, "experts_square", X0, 1.3, 4.4, cap="사각형 2 m (전문가 스위칭, 방위 화살표 렌더 포함)")
card(s, 5.15, 1.3, 4.3, 2.75, "설계 (웨이포인트 커맨더 + 전문가 스위칭)",
     ["커맨더(pure-pursuit식): 목표 방향을 몸통 좌표계에서 8-명령으로 양자화, 제어 주기 25스텝",
      "34° 각도 히스테리시스(채터링 방지), capture 0.35 m, 근접 동결 0.85 m",
      "시각화: fovy 80° 광각 + CoM 추적 카메라, 웨이포인트(도달 시 어둡게), 궤적 점열",
      "산출물: runs/path_follow_demo/<시각>_<경로>/ (mp4, trajectory.png, result.txt 요약 헤더)"], size=9)
intent_result(s, X0, 4.25, CW, 2.55,
              ["10명 전문가 + 고전 추종기로 사전 계획 경로가 주행 가능한지 확인, 영상·궤적으로 재현성 확보"],
              ["사각형 CTE 평균 0.193 m / 전환 5회 / 20 s 완주 · 별(5각 한붓그리기) 0.334 m / 전환 10회 완주",
               "카메라·마커 요구 4건 반영 (광각, CoM 추적, 웨이포인트, 궤적) · result.txt 헤더로 실험 식별"], split=0.36)

# 7. 문제 발견
s = content_slide("문제 발견: 전환이 원인")
rows = [["단계", "관찰 / 조치", "결과"],
        ["전문가 단독 검증", "backward, right 정책을 고정 명령으로 주행", "방향 오차 ±1.5° — 정책은 정상"],
        ["전환 진단 (56 순서쌍)", "기존 set_gait: 위상 비율 보존 교체", "12/56 쌍 붕괴, yaw 최대 160° (거울쌍 최악)"],
        ["k=0 재시작", "새 gait를 주기 시작 위상에서", "7쌍 해결, 3쌍 잔존"],
        ["잔존 위험쌍", "diag_bl→right / diag_bl→diag_fr / diag_br→diag_fl", "152° / 61° / 156° (역재생→순재생 부호 충돌)"]]
add_table(s, rows, X0, 1.3, CW, 2.1, col_w=[1.7, 3.6, 3.6], size=9)
card(s, X0, 3.6, 4.35, 3.15, "왜 거울쌍·역재생쌍이 위험한가",
     ["GD에서 방향은 gait 부호 패턴이 결정. 후진 계열은 전진 gait의 시간 역재생이라 전환 순간 여러 관절의 토크 부호가 동시에 뒤집힘",
      "정책(진폭)은 관측의 motion vector로 gait를 알지만 몸통은 이전 패턴의 관성을 갖고 있어 부호 충돌이 곧 전복",
      "전환 문제 = \"연속된 두 gait의 위상·부호 정합\" 문제로 재정의"], size=9)
intent_result(s, 5.1, 3.6, 4.35, 3.15,
              ["\"backward/right 정책 문제\" 관찰의 진위 확인", "정책 vs 전환 메커니즘 원인 분리"],
              ["전문가는 무죄 — 원인은 gait 교체 순간의 위상 처리", "k=0 재시작만으로 12쌍 중 9쌍 해결, 역재생↔순재생 3쌍 잔존"], split=0.42, size=9)

# 8. 메커니즘 ①
s = content_slide("메커니즘 ① 에너지 페이드")
yb = add_video(s, "fade_bl_to_right_fade_1p25s", X0, 1.3, 4.4, cap="diag_bl → right, 에너지 페이드 (10/5/10 = 1.25 s)")
rows = [["방식", "결과"],
        ["행동 블렌딩 (소프트 핸드오프 제안)", "forward→right 3°→83° 악화: 옛 정책이 새 gait 부호 위에서 행동"],
        ["에너지 페이드 (감쇠→정지→상승)", "위험 3쌍 정상화, 안전쌍은 부작용"],
        ["타이밍 (20,15,20)=2.75 s", "15회 중 12회 성공 (위상 민감)"],
        ["타이밍 (10,5,10)=1.25 s", "15/15 성공, 최악 3.8° — 채택"],
        ["전면 적용", "사각형 CTE 0.19→0.83, 전환 56회 (코너 오버슈트 연쇄)"]]
add_table(s, rows, 5.15, 1.3, 4.3, 2.75, col_w=[1.9, 2.4], size=8.5)
intent_result(s, X0, 4.25, CW, 2.55,
              ["두 정책 행동을 섞어 급변을 피할 수 있는지(소프트 핸드오프); 안 되면 \"에너지를 낮추고 바꾸는\" 대안의 타이밍 민감도"],
              ["행동 블렌딩은 gait 부호 문맥 충돌로 실패 — 섞을 대상은 행동이 아니라 gait 위상",
               "페이드는 위험쌍엔 유효하나 시간 지연(≥1.25 s)·감속 표류가 비용, 안전쌍에 쓰면 손해"], split=0.36)

# 9. 메커니즘 ② 위상 정렬
s = content_slide("메커니즘 ② 위상 정렬")
y2 = add_video(s, "align_hard", X0, 1.3, 3.9, cap="hard (k=0): 오차 172.8°, 전복")
add_video(s, "align_align", X0, y2 + 0.05, 3.9, cap="위상 정렬: 오차 0.9°, max yaw 10.5°")
card(s, 4.65, 1.3, 4.8, 2.35, "알고리즘 (사용자 제안)",
     ["M: 새 gait의 MotionMatrix (14 × 위상 수), 현재 벡터 m ∈ {±1}¹⁴",
      "각 열과 m의 내적 = (일치 관절 수) − (불일치 관절 수)",
      "k* = argmax(Mᵀm) → 그 위상에서 새 gait 시작 (지연 0)",
      "역재생 gait는 getMvec(k)가 열 −k 반환 → k = −k* (전환 학습 준비 중 발견·수정)"], size=9)
intent_result(s, 4.65, 3.8, 4.8, 3.0,
              ["부호 연속성을 직접 맞추면 지연 없이 전환 가능한지 — 페이드의 시간 비용을 없앨 근본책"],
              ["위험 3쌍 152/61/156° → 1.0/0.5/3.1°, 지연·감속 없음",
               "단, 전면 적용은 사각형 0.193→0.448 악화(전문가가 k=0에서만 학습) → 위험쌍에만 선택 적용",
               "확장안(이전 W개 벡터 윈도우 매칭)은 실측 기각: W=10에서 안전쌍 113° 붕괴"], split=0.3, size=9)

# 10. A/B + 기각
s = content_slide("A/B 비교와 기각된 확장")
bar_chart(s, ["square", "star", "gauntlet"], [("hard", [0.193, 0.742, 0.485]), ("fade", [0.193, 0.497, 0.301]), ("align", [0.193, 0.433, 0.472])],
          X0, 1.3, 4.4, 2.7, title="경로별 CTE 평균 (m) — 낮을수록 좋음", colors=[RED, ORANGE, BLUE], fmt="0.000")
bar_chart(s, ["bl→right", "bl→diag_fr", "br→diag_fl"], [("hard (k=0)", [152.5, 61.4, 155.7]), ("위상 정렬", [1.0, 0.5, 3.1])],
          5.15, 1.3, 4.3, 2.7, title="위험 3쌍 방향 오차 (°)", colors=[RED, BLUE], fmt="0.0")
rows = [["기각된 확장", "결과 (왜 안 되나)"],
        ["윈도우 위상 매칭 (W=5/10)", "W=1이 전 쌍 ≤3.1°인데 W=5 right→left 10.2°, W=10 diag_fl→fr 113.6° — 주기 불일치·역재생 비선형, 과거는 이미 물리 상태에 반영"],
        ["정렬 + 페이드 결합", "diag_bl→diag_fr 1°→76° 붕괴 — 정지 중 몸이 관성으로 변형되는데 k는 정지 전 벡터로 고정"],
        ["정지 제거 결합 (10/0/10)", "붕괴는 사라지나(2°) 정렬 단독을 넘지 못함(right→left 1→7°) — 부호 연속성 확보 후 페이드는 순수 교란"]]
add_table(s, rows, X0, 4.15, CW, 1.9, col_w=[2.2, 6.7], size=8.5)
note(s, X0, 6.1, CW, 0.7, "square는 위험쌍이 발동하지 않아 3방식 동일. star는 align, gauntlet(위험쌍 집중)은 fade 우세 — 둘 다 hard를 확실히 이김. 결론: 위상 정렬(W=1) 단독이 최선, 음성 결과는 CLAUDE_CHANGES에 기록.", size=9)

# 11. 매끄러움 ① 지표·후보
s = content_slide("매끄러움 ① 지표·후보")
y2 = add_video(s, "smooth_align_only", X0, 1.3, 3.9, cap="align만: 가속 스파이크 155")
add_video(s, "smooth_align_xfade", X0, y2 + 0.05, 3.9, cap="align + 크로스페이드 12스텝: 57 (−63%)")
rows = [["후보 (위험쌍 평균)", "방향오차°", "헤딩 저크°", "가속 스파이크"],
        ["hard", "123.2", "165", "119"], ["align", "1.6", "120", "142"],
        ["align + 토크 저역통과", "1.0", "144", "151"], ["align + 크로스페이드", "0.9", "99", "89"],
        ["align + 정책 블렌딩", "1.2", "141", "116"]]
add_table(s, rows, 4.65, 1.3, 4.8, 2.4, col_w=[1.9, 0.9, 1.0, 1.0], size=8.5)
card(s, 4.65, 3.85, 4.8, 2.95, "지표와 발견",
     ["매끄러움 = 전환 창의 스텝당 속도 변화(jerk_vel)·헤딩 변화(jerk_head)·IMU 가속 스파이크",
      "align은 안정(전복 없음)은 확보하나 가속 스파이크 142로 잔여 저크",
      "align+크로스페이드가 위험쌍에서 가속 142→89, 헤딩 저크 120→99로 최고 매끄러움, 안정성 동일",
      "안전쌍에 진폭 변조(크로스페이드/저역통과/softstart)를 쓰면 방향오차 5~28°로 악화 → 위험쌍에만"], size=9)

# 12. 매끄러움 ② 하이브리드
s = content_slide("매끄러움 ② 하이브리드")
bar_chart(s, ["square", "star", "gauntlet"], [("align (위험쌍만)", [0.193, 0.433, 0.472]), ("align + xfade (위험쌍만)", [0.193, 0.334, 0.345])],
          X0, 1.3, 4.4, 2.8, title="경로 CTE (m): 하이브리드 효과", colors=[NAVY, BLUE], fmt="0.000")
card(s, 5.15, 1.3, 4.3, 2.8, "채택 메커니즘 (2026-09-08)",
     ["안전쌍: 즉시 k=0 전환 (전문가가 학습한 시작 위상)",
      "위험 3쌍: 위상 정렬 + 12스텝 행동 크로스페이드",
      "역할 분담 — 위상 정렬 = 안정(부호 충돌 제거), 크로스페이드 = 매끄러움(잔여 저크 흡수)",
      "크로스페이드는 위상 정렬 위에서만 유효 (부호 문맥 일치가 전제)"], size=9)
intent_result(s, X0, 4.3, CW, 2.5,
              ["안정(전복 없음)과 매끄러움(저크)을 동시에 최적화하는 조합 탐색"],
              ["쇼케이스 bl→right 가속 스파이크 155→57 (63%↓)",
               "보너스로 경로 CTE 개선: star 0.433→0.334, gauntlet 0.472→0.345, square 0.193 유지"], split=0.36)

# 13. 방위 렌더
s = content_slide("방위 화살표 렌더")
y2 = add_video(s, "experts_star", X0, 1.3, 4.4, cap="별 1.5 m — 초록: 접선 목표 방위, 파랑: 몸통 yaw")
fit_image(s, FIGS["experts_star_traj"], X0, y2 + 0.05, 4.4, 2.35)
card(s, 5.15, 1.3, 4.3, 2.55, "구현",
     ["웨이포인트를 (x, y, yaw°)로 확장 — 기본 방위 = 접선(다음 점 방향, 마지막 점은 도착 방향)",
      "MuJoCo ARROW 마커: pos에서 로컬 +z로 뻗음 → z축=방위, y축=세계 +Z 회전행렬 (0/90/180° 렌더 실증)",
      "trajectory.png에 목표 방위 quiver 추가. 추종 수치 불변(사각형 0.193 / 별 0.334) — 렌더 전용 변경"], size=9)
intent_result(s, 5.15, 4.0, 4.3, 2.8,
              ["크랩워크 추종이 몸통 yaw를 제어하지 않음을 영상에서 드러내기 (\"회전은 아직 감안하지 않았다\")"],
              ["파란 화살표는 내내 +X, 초록 목표는 꼭짓점마다 90°씩 회전 — 방위 오차가 한눈에",
               "2단계(도달 시 CW/CCW 회전 후 진행)는 회전→직진 전환 검증이 필요 → 전환 학습으로 우선순위 이동"], split=0.38, size=9)

# 14. 간지 Part 2
section_slide("Part 2. 전환 학습 — 전문가 증류와 전환 커리큘럼 RL", "외부 메커니즘이 아니라 정책 자신이 전환을 흡수하도록: 증류로 출발선을 옮기고, 무작위 전환 속에서 미세조정한다")

# 15. 설계 결정
s = content_slide("전환 학습 설계 결정")
rows = [["결정", "선택지", "선택과 근거"],
        ["출발점 (warm-start)", "forward 전문가 / 10명 증류(Phase B)", "증류. 9개 명령을 RL로 새로 익히는 불확실성(속도·망각)을 제거해 RL이 \"전환\"만 배우게 함. 증류는 정답(전문가 행동)이 있는 회귀라 분 단위"],
        ["전환 메커니즘", "k0 / align / random", "align. 물리적으로 가장 연속이고 정책이 정렬 시작을 학습하면 k=0 전문가의 취약점이 사라짐. 크로스페이드는 두 정책이 필요해 단일 정책엔 정의 불가"],
        ["할인율 γ", "0.95 (방위) / 0.99 (회전)", "0.99. 전환 후 ~100스텝 뒤의 낙상을 critic이 보려면 유효 지평 100스텝 필요. 학생 critic도 0.99 return에 사전 회귀"],
        ["Stage 1 옵티마이저", "검증 레시피", "lr 1e-4, n_epochs 2, target_kl 0.04, 40M. 정책 std는 보수적 log_std −1.2로 시작"]]
add_table(s, rows, X0, 1.3, CW, 3.6, col_w=[1.6, 2.1, 5.2], size=8.5)
card(s, X0, 5.1, CW, 1.7, "설명 방식에 대한 피드백",
     ["선택지만 던진 첫 질문에 \"비약이 많다\"는 지적 → 각 선택지의 배경·의미·비용·위험을 풀어 설명한 뒤 결정",
      "증류 소요(1~2시간)에 대한 의문: \"새 능력의 발견(RL)이 아니라 있는 능력을 옮겨 담는 회귀(BC)\" — 스승을 넘지 못하고 새 상황(전환)은 RL 몫"], size=9)

# 16. 증류 파이프라인
s = content_slide("증류 파이프라인")
steps = [("수집", "전문가 10명을 통합 env(명령 고정, RL과 동일 보상)에서 병렬 롤아웃 — 원본 관측·행동·보상"),
         ("통합 정규화", "전체 관측으로 학생 전용 obs_rms (전문가는 각자 통계, 학생은 하나)"),
         ("BC + critic", "PPO MlpPolicy 동일 구조. actor MSE 모방 / critic γ=0.99 MC return 회귀 / log_std −1.2"),
         ("DAgger", "학생을 굴려 방문 상태에 전문가 라벨 → 합쳐 재학습 (오차 누적 보정)"),
         ("검증", "명령별 학생 vs 전문가 10 에피소드: 리턴·낙상·진행 속도·yaw·앵커"),
         ("패키징", "model.zip + vecnormalize.pkl(쌍) + metadata + DISTILL_REPORT.md → train.py resume 호환")]
step_cards(s, X0, 1.3, CW, steps, cols=3, card_h=1.5, size=8.5)
intent_result(s, X0, 4.55, CW, 2.25,
              ["RL 전에 \"10개 명령을 이미 할 줄 아는\" 출발점 만들기"],
              ["v1(결정론 롤아웃만): 데이터 안 모방은 정확(검증 MSE 0.0025)했지만 닫힌 루프에서 절반의 명령 실패 → 공변량 이동",
               "처방: 전문가 자체 가우시안 노이즈로 실행한 롤아웃(DART식, 라벨은 평균 행동) + DAgger"], split=0.34)

# 17. 증류 결과
s = content_slide("증류 결과")
v1 = [0.42, -0.08, -0.19, 0.54, -0.30, 0.48, 0.69, 0.80, 1.09, 0.23]
fin = [1.00, 0.98, 0.99, 0.98, 1.00, 0.95, 1.00, 1.00, 1.01, 0.60]
bar_chart(s, cmds, [("v1 결정론 롤아웃만", v1), ("최종 (DART+DAgger×4)", fin)], X0, 1.3, CW, 2.75,
          title="명령별 학생 리턴 / 전문가 리턴 (1.0 = 전문가 동급)", colors=[RED, BLUE], fmt="0.00", ymin=-0.4, ymax=1.2, label_size=6.5)
note(s, X0, 4.05, CW, 0.3, "v1의 diag_fr는 실제 −2.57(역방향 이동), 표시는 −0.30 클립. v1은 left/right/cw 낙상 100%.", size=8.5)
card(s, X0, 4.4, 4.35, 2.4, "cw만 미달(0.60)인 이유 — \"칼날 상태\"",
     ["yaw 0.592 rad/s 정상, 앵커가 서서히 밀려 729스텝에 종료(결정론). 행동 노이즈 0.05면 8회 중 5회 1000스텝 생존",
      "전문가 자체 여유 36스텝(0.2 m 초과 최장 24/60). BC 라벨에 \"앵커 복귀\"가 없어 DAgger로 개선 안 됨 → RL 단계가 교정"], size=8.5)
intent_result(s, 5.1, 4.4, 4.35, 2.4,
              ["전문가 대비 90% 이상·낙상 악화 없음을 합격 기준으로 검증"],
              ["v2(결정론 40만 + 노이즈 40만 + DAgger 2회): 9/10 명령 0.96~1.14, 낙상 0",
               "DAgger 3·4회 추가: 4명령 1.00, ccw 1.01, 나머지 0.95~0.99 · 총 180만 샘플, 검증 MSE 0.0017"], split=0.3, size=8.5)

# 18. 전환 커리큘럼 env
s = content_slide("전환 커리큘럼 환경")
rect(s, X0, 1.3, CW, 1.45)
add_text(s, X0 + 0.12, 1.36, 8.6, 0.3, [{"text": "에피소드 타임라인 (horizon 1000스텝 = 50 s)", "size": 10.5, "bold": True, "color": NAVY}], margin=0)
tx, tw = X0 + 0.2, CW - 0.4
rect(s, tx, 1.95, tw, 0.2, "E1E6EC", None, rounded=False)
for a, b, lab, col in [(0, 0.28, "forward", NAVY), (0.28, 0.55, "diag_bl", TEAL), (0.55, 0.82, "ccw", ORANGE), (0.82, 1.0, "right", BLUE)]:
    rect(s, tx + a * tw, 1.95, (b - a) * tw, 0.2, col, None, rounded=False)
    add_text(s, tx + a * tw, 2.17, (b - a) * tw, 0.25, [{"text": lab, "size": 8, "color": TEXT, "align": PP_ALIGN.CENTER}], margin=0)
for a in (0.28, 0.55, 0.82):
    badge(s, tx + a * tw - 0.1, 1.78, 0.2, "↕", RED, size=8)
note(s, X0 + 0.12, 2.42, 8.6, 0.3, "↕ 전환 시점: 1~4회, 최소 체류 100스텝 간격 균등 무작위 · 다음 명령은 현재 제외 균등(90 순서쌍) · 초기 위상 k 무작위", size=8.5)
rows = [["설계 항목", "내용"],
        ["전환 적용 시점", "물리 스텝 뒤·관측 반환 전 → 정책이 그 스텝 관측에서 새 motion vector/joy를 봄 (1스텝 불일치 없음)"],
        ["전환 메커니즘", "switch_mode align (k0 / random 옵션). 역재생 gait는 k = −argmax"],
        ["콜백 지표", "env_switch/post50_reward, fail_within100, 도착 명령별 분해, per_episode"],
        ["스모크 (전문가 구동)", "40 에피소드, 전환 50회·35쌍, 정렬 정확성 역재생 12회 포함 전부 통과. 전문가 스위칭은 27/40 에피소드가 전환 후 33~121스텝 뒤 낙상"]]
add_table(s, rows, X0, 2.9, CW, 2.2, col_w=[1.7, 7.2], size=8.5)
card(s, X0, 5.25, CW, 1.55, "스모크에서 잡은 함정 2건",
     ["env 인자명 max_episode_steps는 gym.make가 자기 인자로 가로채 env에 전달되지 않음 → episode_horizon으로 개명",
      "set_gait 역재생 정렬 버그(k=col → −col) — 위험 3쌍이 모두 순재생 목표라 그동안 드러나지 않음"], size=9)

# 19. 앵커 문제 ① 진단
s = content_slide("앵커 문제 ① 진단")
rows = [["진단 (증류 정책, 회전 진입 전환 24회)", "값"],
        ["100스텝 내 종료", "54% (선형 진입은 9%)"],
        ["전환 직전 속도", "평균 0.44 m/s"],
        ["전환 후 앵커 최대거리", "평균 0.37 m (실패 0.51 m), 88%가 0.2 m 초과"],
        ["60스텝 뒤 재앵커 시 이탈", "0.04 m, 0.2 m 초과 0% — 미끄러짐은 3 s 안에 멈춤"]]
add_table(s, rows, X0, 1.3, CW, 2.0, col_w=[4.4, 4.5], size=9)
card(s, X0, 3.5, 4.35, 3.3, "해석",
     ["앵커가 전환 순간 COM에 고정되는데 몸은 0.44 m/s로 미끄러져 관성만으로 0.2 m를 넘고, 회전 gait는 제동·복귀를 못 하니 60스텝 규칙에 걸림",
      "정책이 고칠 수 없는 규칙 문제 + \"무작위 회전 전환에 대비해 평소 느리게\"라는 왜곡 인센티브 위험",
      "첫 run 2M 점검: 붕괴 없음(ep_rew −9K 저점 후 +4.2K, EV 0.51 회복)이나 회전 진입 실패 ccw 0.60 / cw 0.63"], size=9)
intent_result(s, 5.1, 3.5, 4.35, 3.3,
              ["회전 진입 실패가 정책 실력인지 규칙 문제인지 분리"],
              ["유예(grace) 재앵커를 제안했으나 사용자가 \"종료 대신 앵커에 가까우면 더 높은 보상\"을 제안 → 채택",
               "미끄러짐이 치명이 아닌, 진폭 조절로 줄일 수 있는 학습 가능한 손실이 됨 · 첫 run(4.25M) 중단·보존 후 재시작"], split=0.3, size=9)

# 20. 앵커 문제 ② 근접 보상 설계
s = content_slide("앵커 문제 ② 근접 보상")
rows2 = [["앵커 거리 d", "근접 보상", "앵커 비용", "스텝 합계*"],
         ["0 m", "+10", "0", "+35"], ["0.1 m", "+5", "−5", "+25"], ["0.2 m", "0", "−10", "+15"],
         ["0.4 m (관성 평균)", "0", "−20", "+5"], ["≥ 0.55 m", "0", "≤ −27", "음수"]]
add_table(s, rows2, X0, 1.3, 4.4, 2.3, col_w=[1.5, 0.95, 0.95, 1.0], size=9)
note(s, X0, 3.65, 4.4, 0.7, "* 목표 속도 회전 보상 22.5 + 건강 2 기준. 근접 보상 10·max(0, 1−d/0.2), 기존 포화 비용 50·min(d, 2) 유지, 앵커 종료 제거(anchor_terminate false). 근접 보상 10 < 회전 보상 22.5로 \"정지가 회전보다 유리\" 국소해 차단.", size=8.5)
card(s, 5.15, 1.3, 4.3, 3.05, "설계 원칙",
     ["가까울수록 단조 증가, 멀어져도 유한(critic 안전) — v1의 무한 비용 붕괴 재현 안 함",
      "관성 미끄러짐 0.4 m는 치명이 아니라 \"세그먼트 내내 +5/스텝\"의 손해 → 0.15 m로 줄이면 +20/스텝: 부드러운 회전 진입을 배울 기울기",
      "곱셈 게이팅(회전 보상 × 근접도)은 멀어지면 회전 유인이 사라지는 국소해 위험으로 배제"], size=9)
intent_result(s, X0, 4.5, CW, 2.3,
              ["종료를 연속 보상으로 대체하는 설계의 스텝당 수지와 부작용 검증"],
              ["보상 프로파일 설계대로: d<0.1 +30.7 / 0.1–0.2 +22.4 / 0.2–0.3 +17.8 per step",
               "회전 진입 100스텝 내 종료 54% → 19% (잔여는 낙상) · 기본값 env는 옛 동작 그대로 (cw 729스텝 앵커 종료 재현)"], split=0.34)

# 21. Stage 1 결과
s = content_slide("Stage 1 결과 (40M)")
line_chart(s, [("평가 리턴", CURVES["s1_eval"]), ("롤아웃 리턴 (이동평균)", CURVES["s1_ep_rew"])], X0, 1.3, 3.0, 2.2, title="리턴", colors=[BLUE, NAVY], fmt="#,##0")
line_chart(s, [("explained_variance", CURVES["s1_ev"])], 3.5, 1.3, 2.95, 2.2, title="critic 설명력", colors=[TEAL], ymin=-0.2, ymax=1.0, legend=False)
line_chart(s, [("전환 후 100스텝 내 실패율", CURVES["s1_fail"])], 6.5, 1.3, 2.95, 2.2, title="전환 실패율 (이동평균)", colors=[RED], ymin=0, ymax=0.5, legend=False)
f0, f1 = CURVES["s0_fail_to"], CURVES["s1_fail_to"]
bar_chart(s, cmds, [("첫 run 2M (앵커 종료 규칙)", [round(f0[c], 3) for c in cmds]), ("Stage 1 말기 (근접 보상)", [round(f1[c], 3) for c in cmds])],
          X0, 3.6, 5.3, 3.2, title="도착 명령별 전환 후 100스텝 내 실패율", colors=[RED, BLUE], fmt="0.00", ymax=0.8, label_size=6.5)
intent_result(s, 6.0, 3.6, 3.45, 3.2,
              ["BC 초기값 보존 여부와 전환 능력 향상 여부"],
              ["최고 평가 22,624 @27.5M · 말기 ep_rew −16K→+13.0K, ep_len 873/1000",
               "전환 후 실패 0.123→0.099, EV 0.92, KL 0.0010(유휴)→Stage 2 ep 3",
               "회전 진입(ccw/cw) 실패 0.6대→0.10/0.03 · 남은 난관 diag_fr·diag_bl 0.33"], split=0.24, size=8.5)
notes(s, "1.5M 부근 KL 0.033·clip 0.24·EV≈0 과도기(보상 분포 변화에 critic 지연)가 있었으나 4M 이후 회복. 정책 std는 0.301 고정(ent_coef 0).")

# 22. Stage 2·3 결과
s = content_slide("Stage 2·3 결과 (누적 120M)")
line_chart(s, [("Stage 2 평가", CURVES["s2_eval"]), ("Stage 3 평가", CURVES["s3_eval"]), ("Stage 2 롤아웃", CURVES["s2_ep_rew"]), ("Stage 3 롤아웃", CURVES["s3_ep_rew"])],
           X0, 1.3, 4.4, 2.6, title="리턴 (누적 스텝)", colors=[BLUE, ORANGE, NAVY, "8E44AD"], fmt="#,##0")
line_chart(s, [("Stage 2 approx_kl", CURVES["s2_kl"]), ("Stage 3 approx_kl", CURVES["s3_kl"])], 5.15, 1.3, 4.3, 2.6, title="approx_kl (target 0.04)", colors=[BLUE, ORANGE], ymin=0, fmt="0.000")
f2, f3 = CURVES["s2_fail_to"], CURVES["s3_fail_to"]
bar_chart(s, cmds, [("Stage 2 말기", [round(f2[c], 3) for c in cmds]), ("Stage 3 말기", [round(f3[c], 3) for c in cmds])],
          X0, 4.0, 5.3, 2.8, title="도착 명령별 전환 후 100스텝 내 실패율", colors=[BLUE, ORANGE], fmt="0.00", ymax=0.5, label_size=6.5)
rows = [["지표", "S1 말기", "S2 말기", "S3 말기"],
        ["평가 최고 / 최근 10회 평균", "22.6K / 15.1K", "24.1K / 17.0K", "23.1K / 16.2K"],
        ["롤아웃 리턴", "13.0K", "15.0K", "14.6K"],
        ["전환 후 실패율", "0.099", "0.097", "0.074"],
        ["approx_kl / clip", "0.0010 / 0.002", "0.0028 / 0.011", "0.011 / 0.059"],
        ["diag_fr / diag_bl 도착 실패", "0.33 / 0.33", "0.33 / 0.35", "0.26 / 0.12"]]
add_table(s, rows, 6.0, 4.0, 3.45, 2.8, col_w=[1.35, 0.7, 0.7, 0.7], size=7.5)
notes(s, "Stage 2: n_epochs 3에도 KL 유휴(0.0028) → Stage 3: lr 2e-4로 KL 정상 범위(0.010~0.012) 진입. 리턴은 평가 잡음 범위에서 정체, diag_bl 진입 실패 0.35→0.12로 개선.")

# 23. 정체 원인 진단
s = content_slide("정체 원인: 부호 가족·δ=203")
rows = [["출발 \\ 도착", "forward", "left", "right", "diag_fl", "diag_fr", "backward", "diag_bl", "diag_br", "ccw", "cw"],
        ["forward", "-", "12.0", "7.7", "14.0", "5.3", "14.0", "5.3", "14.0", "11.7", "8.0"],
        ["left", "13.0", "-", "5.3", "13.0", "5.8", "13.0", "5.8", "13.0", "8.2", "11.0"],
        ["right", "5.8", "5.3", "-", "5.8", "13.0", "5.8", "13.0", "5.8", "11.0", "8.2"],
        ["diag_fl", "14.0", "13.5", "5.9", "-", "4.8", "14.0", "4.8", "14.0", "9.9", "9.5"],
        ["diag_fr", "4.8", "5.9", "13.5", "4.8", "-", "4.8", "14.0", "4.8", "9.5", "9.9"],
        ["backward", "14.0", "12.0", "7.7", "14.0", "5.3", "-", "5.3", "14.0", "11.7", "8.0"],
        ["diag_bl", "4.8", "5.9", "13.5", "4.8", "14.0", "4.8", "-", "4.8", "9.5", "9.9"],
        ["diag_br", "14.0", "13.5", "5.9", "14.0", "4.8", "14.0", "4.8", "-", "9.9", "9.5"],
        ["ccw", "12.8", "8.8", "11.0", "12.8", "7.0", "12.8", "7.0", "12.8", "-", "5.7"],
        ["cw", "7.0", "11.0", "8.8", "7.0", "12.8", "7.0", "12.8", "7.0", "5.7", "-"]]
label(s, X0, 1.3, CW, "정렬 후 달성 가능한 최대 부호 유사도 (14 = 완전 일치; 출발 gait 전 위상 평균)")
add_table(s, rows, X0, 1.62, CW, 2.85, col_w=[1.1] + [0.78] * 10, size=7.5)
card(s, X0, 4.6, 4.35, 2.2, "두 부호 가족",
     ["{forward, backward, diag_fl, diag_br, left} vs {right, diag_fr, diag_bl} (δ+180 거울 가족)",
      "가족 안 13~14, 가족 간 5~6 — 어느 위상에서 시작해도 관절 ~9개 부호 반전. 위상 정렬이 힘을 못 쓰는 전환 유형"], size=8.5)
card(s, 5.1, 4.6, 4.35, 2.2, "δ=203 진입 실험 (Stage 2 정책, 출발 6×변형 3×6회)",
     ["diag_fr 진입: 정책 낙상 0~0.83 → 20스텝 정지 후 시작하면 ≈0 — 진폭 조절로 피할 수 있으나 정책이 \"잠깐 멈춤\"을 발견 못 함 (선형 낙상 페널티 2로 사실상 없음)",
      "diag_bl(역재생 δ=203): 정지해도 낙상 0.17~0.83 → 정렬 위상 자체가 나쁜 시작점 (가족 간 유사도가 고르게 낮아 argmax가 임의)"], size=8)

# 24. 통합 정책 경로 추종 ① 영상
s = content_slide("통합 정책 경로 추종 ①")
vw = 2.85
add_video(s, "unified_square", X0, 1.3, vw, cap="사각형: 0.180 m / 8회 / 37.5 s")
add_video(s, "unified_star", X0 + vw + 0.17, 1.3, vw, cap="별: 0.343 m / 15회 / 58.8 s")
add_video(s, "unified_gauntlet", X0 + 2 * (vw + 0.17), 1.3, vw, cap="gauntlet: 0.253 m / 13회 / 58.8 s")
card(s, X0, 3.35, CW, 1.4, "실험 규약",
     ["단일 정책 + 통합 정규화 통계, 명령 전환 시 학습과 동일하게 set_command(align_phase=True) 뒤 관측을 즉시 재생성 (current_observation), 크로스페이드 없음",
      "path_following.py --policy unified --model … --vecnorm … (전문가 모드 기본값 불변)"], size=9)
intent_result(s, X0, 4.9, CW, 1.9,
              ["전환 학습의 효과를 전문가 스위칭(+하이브리드) 기준선과 같은 경로에서 비교"],
              ["gauntlet(위험 전환 집중): CTE 0.345→0.253 (−27%), 전환 34→13회, 시간 128.8→58.8 s",
               "사각형·별: CTE 동급, 주행 시간은 길고 전환이 잦음 (순항 속도·전환 직후 감속)"], split=0.36, size=9)

# 25. 통합 정책 경로 추종 ② 비교
s = content_slide("통합 정책 경로 추종 ②")
bar_chart(s, ["square", "star", "gauntlet"], [("전문가 스위칭+xfade", [0.193, 0.334, 0.345]), ("통합 정책 (S1 final)", [0.180, 0.343, 0.253])],
          X0, 1.3, 4.4, 2.5, title="CTE 평균 (m)", colors=[NAVY, BLUE], fmt="0.000")
bar_chart(s, ["square", "star", "gauntlet"], [("전문가 스위칭+xfade", [20.0, 42.5, 128.8]), ("통합 정책 (S1 final)", [37.5, 58.8, 58.8])],
          5.15, 1.3, 4.3, 2.5, title="완주 시간 (s)", colors=[NAVY, BLUE], fmt="0.0")
rows = [["체크포인트", "square", "star", "gauntlet", "평균 CTE", "총 시간"],
        ["전문가 스위칭+xfade", "0.193 / 20 s", "0.334 / 43 s", "0.345 / 129 s", "0.291", "192 s"],
        ["S1 final (40M)", "0.180 / 38 s", "0.343 / 59 s", "0.253 / 59 s", "0.259", "155 s"],
        ["S2 best (62.8M)", "0.321 / 30 s", "0.273 / 46 s", "0.219 / 70 s", "0.271", "146 s"],
        ["S2 final (80M)", "0.164 / 21 s", "0.280 / 40 s", "0.408 / 86 s", "0.284", "147 s"],
        ["S3 best (111M)", "0.211 / 19 s", "0.472 / 125 s", "0.298 / 49 s", "0.327", "193 s"],
        ["S3 final (120M)", "0.447 / 50 s", "0.306 / 61 s", "0.223 / 33 s", "0.325", "144 s"]]
add_table(s, rows, X0, 3.95, CW, 2.1, col_w=[2.0, 1.45, 1.45, 1.45, 1.25, 1.3], size=8)
note(s, X0, 6.1, CW, 0.7, "한 판씩의 결정론 주행(초기 자세 동일)은 전환 한 번의 실패가 평균을 좌우해 체크포인트 간 우열이 갈리지 않는다. 대표 체크포인트는 무작위 전환 에피소드 40개 고정 시드 벤치마크로 결정" + (" — 아래 부록 참조." if BENCH else "(진행 중)."), size=8.5)


# 25a. 정책 시각화 ① 명령 투어
s = content_slide("정책 시각화 ① 명령 투어")
yb = add_video(s, "show_tour", X0, 1.3, 4.6, cap="10개 명령 순차 전환, 세그먼트 6 s — 오버레이: 명령·목표 나침반·전환 경과·진폭 바")
rows = [["세그먼트", "명령", "불건강 스텝 /120"],
        ["1 / 3 / 4 / 5", "forward / right / diag_br / backward", "0"],
        ["2", "diag_fr (δ=203 진입)", "12"],
        ["6", "diag_bl (역재생 δ=203 진입)", "24"],
        ["7", "left", "0"],
        ["8", "diag_fl (6의 여파)", "63"],
        ["9 / 10", "ccw / cw", "0"]]
add_table(s, rows, 5.35, 1.3, 4.1, 2.7, col_w=[1.0, 2.1, 1.0], size=8.5)
card(s, 5.35, 4.15, 4.1, 2.65, "오버레이 읽는 법",
     ["좌상단: 현재 명령·전환 후 경과·누적 전환 횟수 / 나침반: 세계 좌표 목표 방향(회전은 ↻↺)",
      "좌하단: 정책이 내는 14관절 진폭(0~2.7) — 전환 직후 진폭 변화가 보임",
      "바닥 노란 박스 = 전환 지점, 빨간 점열 = 궤적, 파란 화살표 = 로봇 yaw, 우상단 빨간 배지 = 불건강 판정"], size=8.5)
intent_result(s, X0, yb + 0.05, 4.6, 6.8 - yb - 0.05,
              ["정책 하나가 10개 명령과 그 사이 전환을 어떻게 수행하는지 한 에피소드로 확인"],
              ["8/10 세그먼트 깨끗, δ=203 진입(diag_fr·diag_bl)에서만 불건강 — 벤치마크가 가리킨 약점이 영상에서 그대로",
               "전환 규약은 학습과 동일(위상 정렬 + 관측 즉시 재생성)"], split=0.34, size=8.5)

# 25b. 정책 시각화 ② 전환 클로즈업
s = content_slide("정책 시각화 ② 전환 클로즈업")
y2 = add_video(s, "show_close_ok", X0, 1.3, 4.4, cap="forward → diag_fr: 전환 후 150스텝 불건강 0 (성공)")
add_video(s, "show_close_fail", X0, y2 + 0.05, 4.4, cap="backward → diag_bl: 150스텝 중 61 불건강 (낙상)")
card(s, 5.15, 1.3, 4.3, 2.65, "관찰 (진폭 바를 보면)",
     ["성공 사례: 전환 직후 몇 스텝 진폭을 낮췄다가 새 gait 리듬에 맞춰 올림 — 학습된 \"부드러운 진입\"",
      "실패 사례(역재생 δ=203): 진폭을 조절해도 몸이 뒤집힘 — 정렬이 고른 시작 위상 자체가 나쁨(가족 간 유사도 5~6/14)",
      "나머지 3쌍(left→diag_fr, diag_br→diag_bl, forward→ccw)은 불건강 0"], size=8.5)
intent_result(s, 5.15, 4.1, 4.3, 2.7,
              ["위험 전환에서 정책이 실제로 무엇을 하는지(진폭 조절) 슬로모션으로 관찰"],
              ["diag_fr 진입은 진폭 조절로 해결되는 유형, diag_bl 진입은 시작 위상(env 측) 개선이 필요한 유형 — 어제 진단과 일치",
               "다음 단계 후보: 가족 간 전환용 상태 인식 정렬, 선형 낙상 페널티 상향"], split=0.34, size=8.5)

# 25c. 정책 시각화 ③ 경로 추종 오버레이
s = content_slide("정책 시각화 ③ 경로 추종")
vw = 2.85
add_video(s, "show_path_square", X0, 1.3, vw, cap="사각형: 0.341 m / 24회 / 91 s")
add_video(s, "show_path_star", X0 + vw + 0.17, 1.3, vw, cap="별: 0.306 m / 13회 / 61 s")
add_video(s, "show_path_gauntlet", X0 + 2 * (vw + 0.17), 1.3, vw, cap="gauntlet: 0.223 m / 7회 / 32.5 s")
rows = [["경로", "전문가 스위칭+xfade", "통합 S1 final", "통합 S3 final"],
        ["square", "0.193 m / 5회 / 20 s", "0.180 / 8회 / 38 s", "0.341 / 24회 / 91 s"],
        ["star", "0.334 / 10회 / 43 s", "0.343 / 15회 / 59 s", "0.306 / 13회 / 61 s"],
        ["gauntlet", "0.345 / 34회 / 129 s", "0.253 / 13회 / 59 s", "0.223 / 7회 / 33 s"]]
add_table(s, rows, X0, 3.4, CW, 1.55, col_w=[1.3, 2.6, 2.5, 2.5], size=8.5)
intent_result(s, X0, 5.1, CW, 1.7,
              ["대표 체크포인트로 세 경로를 다시 주행해 기준선과 비교 (오버레이로 전환 지점·명령 확인)"],
              ["gauntlet·star는 개선(gauntlet 전환 7회·33 s: 전문가 대비 시간 1/4), square는 전환 한 번의 흔들림이 시간·CTE를 키움(결정론 단일 궤적)"], split=0.4, size=8.5)

# 26. 통찰
s = content_slide("배운 것 7가지")
insights = [
    ("전환의 본질은 부호 정합", "GD에서 방향은 gait가 정한다. 전환 실패는 정책이 아니라 연속된 두 gait의 위상·부호 충돌이었다."),
    ("위상 정렬 > 페이드", "원인(부호 충돌)을 제거하면 시간 지연 없이 해결된다. 페이드는 증상 완화이며 정렬 위에 얹으면 중복·교란이다."),
    ("선택 적용의 원칙", "전문가는 k=0에서만 학습돼 정렬 시작에 취약 — 위험쌍에만 정렬(+크로스페이드), 안전쌍은 k=0."),
    ("음성 결과도 자산", "윈도우 매칭·align+fade·정지 제거·전면 페이드는 실측으로 기각하고 기록해 재논의를 막았다."),
    ("증류는 분 단위, 함정은 공변량 이동", "결정론 전문가+동일 초기 자세는 얇은 분포를 만든다. DART 노이즈와 DAgger가 절반의 실패를 9/10 합격으로."),
    ("규칙이 물리를 이길 수 없다", "이동 중 회전 진입의 관성 미끄러짐을 종료로 처벌하면 왜곡 인센티브가 생긴다. 연속 보상으로 바꾸자 실패 54%→19%."),
    ("단일 정책의 이점은 어려운 곳에서", "쉬운 경로는 동급, 위험 전환이 몰린 gauntlet에서 CTE −27%·전환 1/3·시간 절반. 남은 벽은 gait 부호 가족 간 전환."),
]
for i, (t, d) in enumerate(insights):
    r_, c_ = divmod(i, 2)
    x = X0 + c_ * 4.55
    y = 1.3 + r_ * 1.38
    w = 4.35 if i < 6 else CW
    rect(s, x, y, w, 1.25)
    badge(s, x + 0.1, y + 0.12, 0.32, str(i + 1), BLUE if i < 6 else NAVY, size=9)
    add_text(s, x + 0.5, y + 0.08, w - 0.6, 0.3, [{"text": t, "size": 10, "bold": True, "color": NAVY}], margin=0)
    add_text(s, x + 0.5, y + 0.4, w - 0.6, 0.8, [{"text": d, "size": 8.5, "color": TEXT}], margin=0)

# 27. 다음 단계
s = content_slide("다음 단계")
nxt = [("δ=203 진입 대책 (결정 필요)", "① 가족 간 전환용 상태 인식 정렬(관절 속도 부호 기준) ② 선형 명령 낙상 페널티 상향(통합 env 전용) ③ δ=203 도착 쌍 가중 커리큘럼 / 탐색 std 확대"),
       ("대표 체크포인트 선정·정리", "고정 시드 벤치마크로 S1~S3 중 선정 → policies/unified/01~03 정리, 통합 정책 데모 재비교"),
       ("방위 추종 2단계", "웨이포인트 도달 시 yaw 오차 ≥20°면 CW/CCW 회전 후 진행 — 회전→직진 전환 유형 검증, 통합 정책으로 직접 수행"),
       ("δ-보간 연속 조향", "heading ≈ 2δ 가설 검증 — 8-명령 양자화를 넘어 연속 방향 명령으로 (gait provider 확장 지점)"),
       ("지속 학습 (Phase D) · Sim-to-Real", "Progress & Compress(증류+EWC), Kickstarting(교사 KL 정규화) · 마찰 무작위화 재도입, 관측 지연·노이즈, 지형 굴곡")]
for i, (t, d) in enumerate(nxt):
    y = 1.3 + i * 1.08
    rect(s, X0, y, CW, 0.96)
    badge(s, X0 + 0.12, y + 0.31, 0.34, str(i + 1), BLUE, size=9)
    add_text(s, X0 + 0.6, y + 0.08, 2.5, 0.8, [{"text": t, "size": 10, "bold": True, "color": NAVY}], margin=0, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, X0 + 3.15, y + 0.08, CW - 3.3, 0.8, [{"text": d, "size": 9, "color": TEXT}], margin=0, anchor=MSO_ANCHOR.MIDDLE)

# 28. 참고문헌·산출물
s = content_slide("참고문헌·산출물")
rows = [["주제", "대표 문헌", "본 연구와의 대응"],
        ["정책 증류", "Rusu+ Policy Distillation (ICLR'16), Parisotto+ Actor-Mimic (ICLR'16), Merel+ NPMP (ICLR'19)", "10 전문가 → 단일 명령 조건부 정책"],
        ["BC / DAgger", "Ross+ DAgger (AISTATS'11), Laskey+ DART (CoRL'17)", "노이즈 주입 + 학생 상태 라벨링"],
        ["BC→RL 워밍업", "Rajeswaran+ DAPG (RSS'18), Uchendu+ JSRL (ICML'23), Ball+ RLPD (ICML'23)", "critic 사전 회귀·보수적 std"],
        ["다중 보행·전환", "Yang+ MELA (Sci. Robot.'20), Margolis & Agrawal Walk These Ways (CoRL'22)", "보행 조건부 단일 정책"],
        ["뱀 로봇·CPG 위상", "Hirose '93, Tesch+ '09, Ijspeert '08, Song+ GD (ICAE'25)", "serpenoid gait, 위상 정렬"],
        ["지속 학습", "Kirkpatrick+ EWC (PNAS'17), Schwarz+ Progress & Compress (ICML'18), Schmitt+ Kickstarting ('18)", "Phase D 망각 방지"]]
add_table(s, rows, X0, 1.3, CW, 3.2, col_w=[1.4, 5.0, 2.5], size=8)
note(s, X0, 4.55, CW, 0.45, "docs/references_transition_learning.md — 8개 주제 48편, arXiv 초록·출판사·Crossref로 서지정보 검증(검증 실패로 제외한 항목 없음), 파이프라인 구성요소↔문헌 대응표 수록.", size=8.5)
card(s, X0, 5.05, CW, 1.75, "산출물",
     ["policies/unified/00_distilled/ (증류 정책 model.zip + vecnormalize.pkl, DISTILL_REPORT.md) · policies/unified/TRAINING_HISTORY.txt (통합 계보 원장)",
      "training/distill_experts.py · training/path_following.py(--policy unified) · training/configs/ppo_unified_transition_stage{1,2,3}.yaml · horcrux_env/envs/plane_unified_v1.py",
      "runs/path_follow_demo/ (데모 영상·궤적·result.txt) · CLAUDE_CHANGES.md (요청 맥락·변경·수치가 담긴 변경 이력)"], size=8.5)

# 29. 부록 설정
s = content_slide("부록 ① 설정 요약")
rows = [["구분", "항목", "값"],
        ["환경", "보상 계수 (frozen)", "forward 60 · efficiency 3 · healthy 2 · rotation_norm 10 · proj_dist 0 · ctrl 0"],
        ["환경", "종료", "롤 범위 이탈 30스텝(선형) / 60스텝(회전) · 앵커 종료 없음(anchor_terminate false) · 선형 낙상 페널티 2"],
        ["환경", "앵커 근접 보상", "10·max(0, 1−d/0.2) + 포화 비용 50·min(d, 2)"],
        ["환경", "전환 커리큘럼", "1~4회 · dwell 100 · align · 초기 위상 무작위 · horizon 1000 · 90쌍 균등"],
        ["PPO", "Stage 1 / 2 / 3", "lr 1e-4 / 1e-4 / 2e-4 · n_epochs 2 / 3 / 3 · target_kl 0.04 · γ 0.99 · n_steps 512 · batch 512 · 5×512 tanh"],
        ["샘플링", "num_envs / fps", "8 subproc · ≈2,150~2,190 fps · 40M ≈ 5.2 h per stage"],
        ["평가", "eval_freq / 에피소드", "250k · 10 (Stage 1) → 20 (Stage 2·3) 결정론"]]
add_table(s, rows, X0, 1.3, CW, 3.3, col_w=[0.9, 1.9, 6.1], size=8.5)
card(s, X0, 4.8, CW, 2.0, "CLAUDE_CHANGES.md 주요 항목 (2026-09-08 ~ 10)",
     ["위상 정렬 채택·3방식 A/B → 윈도우 매칭 기각 → align+fade 기각 → 정지 제거 진단 정정 → 매끄러움 하이브리드 → result.txt 헤더(+60배 중복 버그 수정)",
      "방위 화살표 렌더 → 전환 학습 파이프라인(env·증류·콜백·YAML) → 증류 완료(v1 실패/v2/DAgger) → Stage 1 착수 → 앵커 근접 보상 설계·재시작 → Stage 1~3 완료 → 통합 정책 데모 모드 → δ=203 진단"], size=8.5)

# 30. 부록 벤치마크 (있으면)
if BENCH:
    s = content_slide("부록 ② 체크포인트 벤치마크")
    rows = [["체크포인트", "리턴 평균 ± sd", "길이", "완주율", "전환 실패(100)", "δ=203 도착 실패"]]
    for n, r in BENCH.items():
        rows.append([n, f"{r['ret']:,.0f} ± {r['ret_sd']:,.0f}", f"{r['eplen']:.0f}", f"{r['survive']:.2f}", f"{r['fail100']:.3f} ({r['n_sw']})", f"{r['fail203']:.2f} ({r['n203']})"])
    add_table(s, rows, X0, 1.3, CW, 2.6, col_w=[1.7, 1.9, 0.8, 0.9, 1.8, 1.8], size=9)
    best = min(BENCH.items(), key=lambda kv: kv[1]["fail100"])
    note(s, X0, 4.05, CW, 0.9, f"동일한 40개 시드(무작위 전환 1~4회, horizon 1000)로 결정론 평가. 리턴은 편차(sd ≈ 1.4~1.7만)에 비해 차이가 작아 동급이며, 전환 관련 지표는 stage를 거치며 단조 개선. 전환 실패율 최저: {best[0]} ({best[1]['fail100']:.3f}, δ=203 {best[1]['fail203']:.2f}).", size=9)
    card(s, X0, 5.05, CW, 1.75, "대표 체크포인트 권고",
         ["S3 final: 전환 후 100스텝 내 실패 0.066(S1 final 0.164의 40%), δ=203 도착 실패 0.06 — 전환 강건성 최우선이면 이 체크포인트",
          "S2 final: 완주율 0.80·에피소드 길이 913으로 생존은 최고, 전환 실패 0.090 — 차선",
          "한 판 경로 데모의 편차(S3 final 사각형 0.447)는 결정론 단일 궤적의 잡음 — 대표 선정은 이 벤치마크 기준"], size=9)

prs.save(OUT)
print("saved", OUT, f"{OUT.stat().st_size/1e6:.1f} MB, slides", len(prs.slides))
