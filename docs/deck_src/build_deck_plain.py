"""연구 정리 덱 — 사용자 템플릿 위에, 소리 내어 읽기 쉬운 문장으로 전면 재작성 (2026-09-11).

원칙: 한 문장에 한 가지 내용. 기호(→, ·, /) 대신 말로 푼다. 숫자는 꼭 필요한 것만.
수치 출처: results/ 아래 결과 JSON(2026-10-20부터 git 추적), 그 전 수치는 CLAUDE_CHANGES.md, TRAINING_HISTORY.txt, MOVING_INIT_CAMPAIGN.txt에서 옮긴 것
"""
import glob
import json
import sys
from pathlib import Path

import imageio
import numpy as np
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
POSTERS.mkdir(parents=True, exist_ok=True)   # 처음 실행하는 데이터 폴더에서도 포스터를 만들 수 있게 (2026-10-20)
TEMPLATE = ROOT / "docs" / "PPT샘플.pptx"
OUT = ROOT / "docs" / "Horcrux_transition_research_2026-09_template.pptx"
CURVES = json.load(open(SC / "curves.json"))
BENCH = json.load(open(SC / "bench_ckpts.json")) if (SC / "bench_ckpts.json").exists() else None


def load_eval(label):
    p = ROOT / "results/moving_state_bank" / f"eval_{label}.json"
    return json.load(open(p))["results"] if p.exists() else None


EVALS = {k: load_eval(k) for k in ("baseline_iter1", "iter1_final", "iter1_best", "iter2_final", "iter2_best", "iter3_final", "iter3_best", "iter4_final")}


def load_phase(label):
    """시작 위상 규칙 비교 평가(eval_phase_rules_*.json) → {목표: {규칙: 평균 실패}}"""
    p = ROOT / "results/moving_state_bank" / f"eval_phase_rules{('_' + label) if label else ''}.json"
    if not p.exists():
        return {}
    d = json.load(open(p))
    return {t: {r: v["mean"] for r, v in rules.items()} for t, rules in d["summary"].items()}


PHASE = {k: load_phase(k) for k in ("", "lat", "iter3_final", "iter4_final", "iter4_best")}


def phase_val(label, target, rule):
    v = PHASE.get(label, {}).get(target, {}).get(rule)
    return "-" if v is None else f"{v:.3f}"


def find_demo(kind, suffix, unified=False):
    pat = f"2026*_{kind}_unified_{suffix}" if unified else f"2026*_{kind}_{suffix}"
    hits = sorted(glob.glob(str(ROOT / "runs/path_follow_demo" / pat)))
    return Path(hits[-1]) if hits else None


def parse_demo(folder):
    import re
    if folder is None or not (folder / "result.txt").exists():
        return None
    txt = (folder / "result.txt").read_text(encoding="utf-8")
    err = re.search(r"평균 ([\d.]+) m / 최대 ([\d.]+) m", txt)
    sw = re.search(r"명령 전환 (\d+)회 \| 주행 (\d+) 스텝 \(([\d.]+) s\)", txt)
    if not err or not sw:
        return None
    return dict(err=float(err.group(1)), err_max=float(err.group(2)), switches=int(sw.group(1)), steps=int(sw.group(2)),
                sec=float(sw.group(3)), done="완주=True" in txt)

NAVY, BLUE = "203864", "2E75B6"
CARD, CARD_LINE = "EEF3FA", "C7D3E3"
TEXT, SUB, CAP = "262626", "595959", "8A8A8A"
ORANGE, GREEN, RED, TEAL = "E97132", "196B24", "C0392B", "156082"
WHITE = "FFFFFF"
FONT = "맑은 고딕"
DATE = "20260911"
TOPIC = "gait 전환 학습"
X0, X1, Y0, Y1 = 0.55, 9.45, 1.25, 6.85
CW = X1 - X0
SHOW = ROOT / "runs/policy_showcase/20260910-111945_S3final"
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
    "show_tour": SHOW / "command_tour.mp4",
    "show_close_ok": SHOW / "closeup_forward_to_diag_fr.mp4",
    "show_close_fail": SHOW / "closeup_backward_to_diag_bl.mp4",
    "show_path_gauntlet": SHOW / "path_gauntlet.mp4",
    "show_path_star": SHOW / "path_star.mp4",
    "show_path_square": SHOW / "path_square.mp4",
}
# 인계 시작 학습 영상 (iteration 2, CoM 추적 카메라) — 가장 최근 클립
_iter2_vids = sorted(glob.glob(str(ROOT / "runs/ppo_plane_forward_moving_init_iter2/*/videos/*.mp4")))
if _iter2_vids:
    VIDEOS["iter2_forward_train"] = Path(_iter2_vids[-1])
# 정리된 통합 계보 경로가 바뀌었으면 stage1 영상 경로 보정
if not VIDEOS["stage1_train"].exists():
    alt = sorted(glob.glob(str(ROOT / "policies/unified/01_transition_stage1/videos/*.mp4")))
    if alt:
        VIDEOS["stage1_train"] = Path(alt[-1])
FIGS = {"experts_star_traj": ROOT / "runs/path_follow_demo/20260909-105200_star/trajectory.png"}


def ensure_poster(key):
    p = POSTERS / f"{key}.png"
    if not p.exists():
        r = imageio.get_reader(str(VIDEOS[key]))
        n = r.count_frames()
        imageio.imwrite(p, r.get_data(int(n * 0.6)))
        r.close()
    return p


prs = Presentation(str(TEMPLATE))
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
        etree.SubElement(rPr, qn("a:ea")).set("typeface", FONT)


def _bullet(para, level=0, char="▪", color=BLUE):
    pPr = para._p.get_or_add_pPr()
    indent = 0.16
    pPr.set("marL", str(Emu(Inches(indent * (level + 1)))))
    pPr.set("indent", str(-Emu(Inches(indent))))
    bu = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(bu, qn("a:srgbClr")).set("val", color)
    etree.SubElement(pPr, qn("a:buChar")).set("char", char)


def add_text(slide, x, y, w, h, paras, size=10, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, margin=0.04, space_after=2, line_spacing=1.06):
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
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
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


def card(slide, x, y, w, h, header, bullets, size=9.5, fill=CARD, line=CARD_LINE, header_color=NAVY, text_color=TEXT, bullet_color=BLUE, header_size=11):
    rect(slide, x, y, w, h, fill, line)
    add_text(slide, x + 0.12, y + 0.07, w - 0.24, 0.3, [{"text": header, "size": header_size, "bold": True, "color": header_color}], margin=0)
    add_text(slide, x + 0.12, y + 0.36, w - 0.24, h - 0.4,
             [{"text": b, "size": size, "color": text_color, "bullet": True, "bullet_color": bullet_color, "space_after": 3} if isinstance(b, str) else b for b in bullets], margin=0)


def intent_result(slide, x, y, w, h, intent, result, split=0.42, size=9.5):
    ih = h * split - 0.06
    card(slide, x, y, w, ih, "무엇을 알고 싶었나", intent, size=size)
    ry, rh = y + ih + 0.1, h - ih - 0.1
    card(slide, x, ry, w, rh, "무엇을 알게 됐나", result, size=size, fill=NAVY, line=None, header_color=WHITE, text_color=WHITE, bullet_color="9DC3E6")


def label(slide, x, y, w, text, size=11):
    add_text(slide, x, y, w, 0.3, [{"text": text, "size": size, "bold": True, "color": NAVY}], margin=0)


def caption(slide, x, y, w, text):
    add_text(slide, x, y, w, 0.28, [{"text": text, "size": 8.5, "color": CAP}], margin=0)


def note(slide, x, y, w, h, text, size=9.5):
    add_text(slide, x, y, w, h, [{"text": text, "size": size, "color": SUB}], margin=0)


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
    tf = s.shapes.title.text_frame
    tf.clear()
    r = tf.paragraphs[0].add_run()
    full = f"{TOPIC} ({DATE}) ― {sub}"
    r.text = full
    _style_run(r, 16 if len(full) <= 34 else (14 if len(full) <= 38 else 12.5), True, NAVY)
    return s


def section_slide(title, body):
    s = prs.slides.add_slide(L_SECTION)
    for ph in s.placeholders:
        idx = ph.placeholder_format.idx
        if idx in (0, 1):
            tf = ph.text_frame
            tf.clear()
            r = tf.paragraphs[0].add_run()
            r.text = title if idx == 0 else body
            _style_run(r, 26 if idx == 0 else 12, idx == 0, WHITE if idx == 0 else "DCE6F2")
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
    h = h or w * 9 / 16
    rect(slide, x - 0.03, y - 0.03, w + 0.06, h + 0.06, "D9E2F0", None, radius=0.02)
    slide.shapes.add_movie(str(VIDEOS[key]), Inches(x), Inches(y), Inches(w), Inches(h), poster_frame_image=str(ensure_poster(key)), mime_type="video/mp4")
    if cap:
        caption(slide, x, y + h + 0.05, w, "▶ " + cap)
    return y + h + (0.33 if cap else 0.05)


def add_table(slide, rows, x, y, w, h, col_w=None, size=9, header=True):
    nr, nc = len(rows), len(rows[0])
    tbl = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h)).table
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


def line_chart(slide, series, x, y, w, h, title=None, colors=None, xtitle="학습 스텝 (백만)", legend=True, ymin=None, ymax=None, fmt=None):
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

# ============================================================================= 1. 표지
s = prs.slides.add_slide(L_COVER)
for ph in s.placeholders:
    idx = ph.placeholder_format.idx
    tf = ph.text_frame
    tf.clear()
    r = tf.paragraphs[0].add_run()
    if idx == 0:
        r.text = "뱀 로봇의 경로 추종과 gait 전환 학습"
        _style_run(r, 30, True, NAVY)
    elif idx == 1:
        r.text = "전문가 정책 열 개에서 출발해, 전환을 스스로 다루는 정책까지 만들어 온 과정입니다. 2026년 9월 8일부터 11일까지의 기록입니다."
        _style_run(r, 12, False, SUB)
add_text(s, 3.31, 6.95, 3.38, 0.4, [{"text": "지능로봇시스템연구실", "size": 11, "color": SUB, "align": PP_ALIGN.CENTER}], margin=0)

# 2. 흐름
s = content_slide("연구 흐름 요약")
flow = [
    ("전문가 정책 열 개", "여덟 방향으로 걷는 정책과, 제자리에서 도는 정책 두 개를 각각 따로 학습해 두었습니다."),
    ("경로 추종 시연", "웨이포인트를 따라가며 전문가를 바꿔 끼우는 방식으로, 네모와 별 모양 경로를 완주했습니다."),
    ("전환 문제 발견", "후진과 우측 정책이 이상해 보였는데, 실제 원인은 gait를 바꾸는 순간의 위상 충돌이었습니다."),
    ("전환 방법 탐구", "페이드를 써 보고, 위상 정렬을 찾았고, 위험한 쌍에만 부드럽게 섞는 방식으로 정리했습니다."),
    ("방향 화살표 표시", "웨이포인트가 원하는 방향과 로봇이 실제로 향한 방향을 화살표로 그려 비교했습니다."),
    ("전문가 증류", "전문가 열 개의 행동을 정책 하나에 옮겨 담았습니다. 열 개 중 아홉 개는 전문가와 같은 수준입니다."),
    ("전환 학습", "무작위로 명령이 바뀌는 환경에서 정책 하나를 세 단계 더 학습했습니다."),
    ("전문가 이어 학습", "전문가가 움직이던 상태에서 시작하도록 파일럿 네 번을 돌렸습니다. 학습보다 시작 위상 규칙이 더 큰 차이를 만들었습니다."),
]
step_cards(s, X0, 1.3, CW, flow, cols=4, card_h=1.62, size=8.5)
card(s, X0, 4.85, CW, 1.15, "이 연구의 한 줄 요약",
     ["우리 로봇은 방향을 gait가 정하고, 힘의 세기는 정책이 정합니다. 그래서 전환이 어려운 이유는 gait의 부호가 갑자기 바뀌기 때문입니다.",
      "먼저 위상 정렬로 그 충격을 줄였고, 다음에는 정책이 전환을 스스로 다루도록 학습시켰습니다."], size=9.5)
note(s, X0, 6.1, CW, 0.7, "이 자료의 숫자는 모두 기록 파일에서 가져왔습니다. 영상은 슬라이드에 들어 있어서 누르면 재생됩니다.", size=9)

# 3. 배경 ①
s = content_slide("배경 ① 기본 개념과 학습 방법")
rect(s, X0, 1.3, 4.3, 2.35)
add_text(s, X0 + 0.12, 1.37, 4.0, 0.3, [{"text": "gait 분해 방식이란", "size": 11, "bold": True, "color": NAVY}], margin=0)
bx = X0 + 0.15
for lab, col, txt in [("정책", BLUE, "관절마다 힘의 세기를 정합니다"), ("×", None, ""), ("gait", NAVY, "관절마다 힘의 방향, 즉 부호를 정합니다"), ("=", None, ""), ("토크", TEAL, "둘을 곱한 값이 실제 명령입니다")]:
    if col is None:
        add_text(s, bx, 2.05, 0.3, 0.5, [{"text": lab, "size": 16, "bold": True, "color": CAP, "align": PP_ALIGN.CENTER}], margin=0)
        bx += 0.3
        continue
    rect(s, bx, 1.75, 1.1, 1.05, col, None)
    add_text(s, bx, 1.8, 1.1, 0.3, [{"text": lab, "size": 9, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    add_text(s, bx, 2.1, 1.1, 0.65, [{"text": txt, "size": 8, "color": WHITE, "align": PP_ALIGN.CENTER}], margin=0)
    bx += 1.15
note(s, X0 + 0.12, 2.9, 4.05, 0.7, "그래서 gait를 바꾸는 순간에 부호가 뒤집히면 로봇이 흔들립니다. 이것이 전환 문제의 뿌리입니다.", size=9)
card(s, 5.05, 1.3, 4.4, 2.35, "학습을 이어 가는 세 단계 방법",
     ["첫 단계는 학습률 1e-4에 에포크 2로 시작합니다. 정책이 거의 안 바뀌면 다음 단계로 갑니다.",
      "둘째 단계는 에포크를 3으로 올립니다. 정책이 너무 많이 바뀌면 다음 단계로 갑니다.",
      "셋째 단계는 학습률을 절반으로 줄입니다. 이 방법은 정책 열 개에서 모두 잘 맞았습니다."], size=9)
card(s, X0, 3.85, CW, 2.9, "제자리 회전 정책은 이렇게 만들었습니다",
     ["빠르게 도는 것보다 일정한 속도로 도는 것을 더 중요하게 보상했습니다.",
      "시작 위치에서 20센티미터 넘게 벗어난 상태가 60스텝 이어지면 실패로 처리했습니다.",
      "넘어지면 큰 벌점을 주고, 먼 미래까지 보도록 할인율을 0.99로 두었습니다.",
      "정책이 보는 정보는 센서 값과 gait의 부호, 그리고 명령입니다. 모두 합쳐 97개 숫자입니다."], size=9.5)

# 4. 배경 ②
s = content_slide("배경 ② 전문가 정책 열 개")
rows = [["명령", "방향", "gait 각도", "명령", "방향", "gait 각도"],
        ["forward", "앞으로", "0", "backward", "뒤로", "0, 거꾸로 재생"],
        ["left", "왼쪽으로", "45", "diag_bl", "뒤쪽 왼쪽 대각선", "203, 거꾸로 재생"],
        ["right", "오른쪽으로", "225", "diag_br", "뒤쪽 오른쪽 대각선", "23, 거꾸로 재생"],
        ["diag_fl", "앞쪽 왼쪽 대각선", "23", "ccw", "반시계 회전", "315"],
        ["diag_fr", "앞쪽 오른쪽 대각선", "203", "cw", "시계 회전", "135"]]
label(s, X0, 1.3, CW, "열 가지 명령과 각 명령에 쓰는 gait")
add_table(s, rows, X0, 1.65, CW, 2.2, col_w=[1.2, 1.7, 1.55, 1.2, 1.7, 1.55], size=9)
card(s, X0, 4.05, 4.35, 2.7, "gait 사이의 규칙",
     ["좌우를 거울처럼 뒤집으려면 각도에 180도를 더하면 됩니다.",
      "뒤로 가는 gait는 앞으로 가는 gait를 시간 순서만 거꾸로 재생한 것입니다.",
      "시계 회전과 반시계 회전도 서로 거울 관계입니다."], size=9.5)
card(s, 5.1, 4.05, 4.35, 2.7, "전문가들의 실력",
     ["걷는 정책 여덟 개는 초당 0.45미터에서 0.68미터 사이로 움직이고, 넘어지지 않습니다.",
      "회전 정책 두 개는 초당 약 0.6라디안으로 돌고, 시작점에서 최대 25센티미터까지만 벗어납니다.",
      "가장 느린 정책은 앞쪽 오른쪽 대각선입니다. 뒤에서 이 정책이 전환에 약하다는 이야기가 나옵니다."], size=9.5)

# 5. 간지
section_slide("Part 1. 경로 추종 시연과 전환 방법", "전문가 열 개를 바꿔 끼우며 네모와 별을 그려 보고, 전환이 왜 어려운지 알아본 과정입니다.")

# 6. 시연 설계
s = content_slide("경로 추종 시연")
yb = add_video(s, "experts_square", X0, 1.3, 4.6, cap="네모 경로를 도는 영상입니다. 초록 화살표가 목표 방향입니다.")
card(s, 5.35, 1.3, 4.1, 2.75, "어떻게 만들었나",
     ["로봇은 다음 웨이포인트가 어느 쪽에 있는지 보고, 여덟 방향 중 가장 가까운 명령을 고릅니다.",
      "명령은 25스텝마다 다시 정합니다. 목표에 35센티미터 안으로 오면 다음 점으로 넘어갑니다.",
      "카메라는 로봇의 무게중심을 따라가고, 지나온 길은 빨간 점으로 남깁니다."], size=9)
intent_result(s, X0, yb + 0.05, 4.6, 6.8 - yb - 0.05,
              ["전문가 열 개와 간단한 추종기만으로 계획한 경로를 따라갈 수 있는지 보고 싶었습니다."],
              ["네모 경로는 평균 19센티미터 오차로 완주했습니다. 전환은 다섯 번이었습니다.",
               "별 경로도 평균 33센티미터 오차로 완주했습니다."], split=0.36, size=9)
card(s, 5.35, 4.2, 4.1, 2.6, "결과 파일은 어디에 있나",
     ["runs 폴더 아래 path_follow_demo에 시각별로 폴더가 생깁니다.",
      "폴더마다 영상, 궤적 그림, 그리고 어떤 실험이었는지 적은 result.txt가 있습니다."], size=9)

# 7. 문제 발견
s = content_slide("문제 발견: 정책이 아니라 전환이 원인")
rows = [["무엇을 했나", "결과"],
        ["후진 정책과 우측 정책을 각각 따로 돌려 봤습니다.", "방향 오차가 1.5도 안쪽이라 정책은 정상이었습니다."],
        ["56가지 전환 쌍을 모두 시험했습니다.", "12쌍에서 로봇이 뒤집혔습니다. 거울 관계인 쌍이 가장 심했습니다."],
        ["새 gait를 항상 처음 위상에서 시작해 봤습니다.", "12쌍 중 9쌍이 해결됐고, 3쌍이 남았습니다."],
        ["남은 세 쌍을 살펴봤습니다.", "뒤로 가는 gait에서 앞으로 가는 gait로 바뀌는 쌍이었습니다. 오차가 152도, 61도, 156도였습니다."]]
add_table(s, rows, X0, 1.3, CW, 2.3, col_w=[3.8, 5.1], size=9)
card(s, X0, 3.8, 4.35, 3.0, "왜 이 쌍들이 위험한가",
     ["뒤로 가는 gait는 앞으로 가는 gait를 거꾸로 재생한 것입니다. 그래서 바꾸는 순간 여러 관절의 힘 방향이 한꺼번에 뒤집힙니다.",
      "몸은 아직 이전 움직임의 관성을 갖고 있어서, 힘 방향이 갑자기 바뀌면 그대로 뒤집힙니다."], size=9)
intent_result(s, 5.1, 3.8, 4.35, 3.0,
              ["정책이 잘못된 것인지, 전환 방법이 잘못된 것인지 가려내고 싶었습니다."],
              ["정책은 문제가 없었습니다. 문제는 gait를 바꾸는 순간을 다루는 방법이었습니다.",
               "전환 문제는 두 gait의 위상과 부호를 맞추는 문제로 다시 정의했습니다."], split=0.4, size=9)

# 8. 방법 ①
s = content_slide("전환 방법 ① 페이드")
yb = add_video(s, "fade_bl_to_right_fade_1p25s", X0, 1.3, 4.4, cap="힘을 줄였다가 gait를 바꾸고 다시 올리는 페이드 영상입니다.")
rows = [["방법", "결과"],
        ["두 정책의 행동을 섞기", "오히려 나빠졌습니다. 옛 정책이 새 gait 위에서 엉뚱한 힘을 냈기 때문입니다."],
        ["힘을 줄이고, 멈추고, 바꾸고, 다시 올리기", "위험한 세 쌍이 정상으로 돌아왔습니다."],
        ["멈추는 시간을 길게 (2.75초)", "15번 중 12번만 성공했습니다."],
        ["멈추는 시간을 짧게 (1.25초)", "15번 모두 성공했습니다. 이 값을 골랐습니다."],
        ["모든 전환에 페이드 적용", "네모 경로 오차가 0.19미터에서 0.83미터로 나빠졌습니다."]]
add_table(s, rows, 5.15, 1.3, 4.3, 2.75, col_w=[1.7, 2.6], size=8.5)
intent_result(s, X0, 4.25, CW, 2.55,
              ["두 정책의 행동을 섞으면 전환이 부드러워질지 보고 싶었습니다. 안 되면 힘을 줄여서 바꾸는 방법을 시험하려 했습니다."],
              ["행동을 섞는 방법은 실패했습니다. 섞어야 할 것은 행동이 아니라 gait의 위상이었습니다.",
               "페이드는 위험한 쌍에는 효과가 있지만, 시간이 걸리고 안전한 쌍에는 손해였습니다."], split=0.38)

# 9. 방법 ②
s = content_slide("전환 방법 ② 위상 정렬")
y2 = add_video(s, "align_hard", X0, 1.3, 3.9, cap="처음 위상에서 시작한 경우입니다. 로봇이 뒤집힙니다.")
add_video(s, "align_align", X0, y2 + 0.05, 3.9, cap="가장 닮은 위상에서 시작한 경우입니다. 오차가 1도입니다.")
card(s, 4.65, 1.3, 4.8, 2.35, "위상 정렬은 이런 방법입니다",
     ["새 gait는 한 주기 안에 여러 위상을 갖고, 위상마다 관절 부호 패턴이 다릅니다.",
      "지금 로봇이 쓰고 있는 부호 패턴과 가장 많이 겹치는 위상을 찾아서, 거기서 새 gait를 시작합니다.",
      "겹치는 정도는 관절 열네 개 중 부호가 같은 개수에서 다른 개수를 뺀 값으로 잽니다.",
      "거꾸로 재생하는 gait는 위상 번호의 부호를 뒤집어야 합니다. 이것은 나중에 찾은 버그였습니다."], size=9)
intent_result(s, 4.65, 3.8, 4.8, 3.0,
              ["부호를 맞춰 시작하면 기다리는 시간 없이 전환할 수 있는지 보고 싶었습니다."],
              ["위험한 세 쌍의 오차가 152도, 61도, 156도에서 1도, 0.5도, 3도로 줄었습니다. 기다림도 없습니다.",
               "다만 모든 전환에 쓰면 네모 경로가 나빠졌습니다. 전문가들이 처음 위상에서만 학습했기 때문입니다.",
               "그래서 위험한 쌍에만 씁니다."], split=0.3, size=9)

# 10. A/B 비교
s = content_slide("세 가지 방법 비교와 버린 아이디어")
bar_chart(s, ["네모", "별", "gauntlet"], [("그냥 바꾸기", [0.193, 0.742, 0.485]), ("페이드", [0.193, 0.497, 0.301]), ("위상 정렬", [0.193, 0.433, 0.472])],
          X0, 1.3, 4.4, 2.7, title="경로별 평균 오차 (미터). 낮을수록 좋습니다.", colors=[RED, ORANGE, BLUE], fmt="0.000")
bar_chart(s, ["bl→right", "bl→diag_fr", "br→diag_fl"], [("그냥 바꾸기", [152.5, 61.4, 155.7]), ("위상 정렬", [1.0, 0.5, 3.1])],
          5.15, 1.3, 4.3, 2.7, title="위험한 세 쌍의 방향 오차 (도)", colors=[RED, BLUE], fmt="0.0")
rows = [["버린 아이디어", "왜 버렸나"],
        ["이전 여러 스텝의 부호를 함께 맞추기", "한 스텝만 맞추는 것이 이미 충분했고, 여러 스텝을 맞추면 오히려 안전한 쌍이 무너졌습니다."],
        ["위상 정렬과 페이드를 같이 쓰기", "멈추는 동안 몸이 움직여서 정렬해 둔 위상이 어긋났습니다. 한 쌍이 76도나 틀어졌습니다."],
        ["멈춤 없이 페이드만 얹기", "무너지지는 않았지만 위상 정렬 하나만 쓴 것보다 나아지지 않았습니다."]]
add_table(s, rows, X0, 4.15, CW, 1.9, col_w=[2.6, 6.3], size=8.5)
note(s, X0, 6.1, CW, 0.7, "네모 경로는 위험한 쌍이 나오지 않아 세 방법이 같습니다. 별에서는 위상 정렬이, gauntlet에서는 페이드가 조금 더 좋았습니다. 둘 다 그냥 바꾸는 것보다는 훨씬 낫습니다.", size=9)

# 11. 매끄러움 ①
s = content_slide("매끄러움 ① 흔들림을 재는 방법")
y2 = add_video(s, "smooth_align_only", X0, 1.3, 3.9, cap="위상 정렬만 쓴 경우입니다. 충격 값이 155입니다.")
add_video(s, "smooth_align_xfade", X0, y2 + 0.05, 3.9, cap="위상 정렬에 짧은 섞기를 더한 경우입니다. 충격 값이 57입니다.")
rows = [["방법", "방향 오차", "헤딩 흔들림", "충격"],
        ["그냥 바꾸기", "123도", "165", "119"], ["위상 정렬", "1.6도", "120", "142"],
        ["정렬 + 토크 필터", "1.0도", "144", "151"], ["정렬 + 짧은 섞기", "0.9도", "99", "89"],
        ["정렬 + 정책 섞기", "1.2도", "141", "116"]]
add_table(s, rows, 4.65, 1.3, 4.8, 2.4, col_w=[1.9, 0.9, 1.0, 1.0], size=8.5)
card(s, 4.65, 3.85, 4.8, 2.95, "무엇을 알게 됐나",
     ["흔들림은 속도 변화, 방향 변화, 그리고 머리의 가속도 충격으로 쟀습니다.",
      "위상 정렬은 뒤집힘은 막지만 충격은 남깁니다.",
      "위상 정렬 뒤에 두 정책의 행동을 열두 스텝 동안 섞으면 충격이 가장 작아지고, 방향 오차도 그대로 좋습니다.",
      "안전한 쌍에 이런 섞기를 쓰면 오히려 나빠집니다. 그래서 위험한 쌍에만 씁니다."], size=9)

# 12. 매끄러움 ②
s = content_slide("매끄러움 ② 최종 방법")
bar_chart(s, ["네모", "별", "gauntlet"], [("위상 정렬만", [0.193, 0.433, 0.472]), ("위상 정렬 + 짧은 섞기", [0.193, 0.334, 0.345])],
          X0, 1.3, 4.4, 2.8, title="경로별 평균 오차 (미터)", colors=[NAVY, BLUE], fmt="0.000")
card(s, 5.15, 1.3, 4.3, 2.8, "최종으로 고른 방법",
     ["안전한 쌍은 새 gait를 처음 위상에서 바로 시작합니다.",
      "위험한 세 쌍은 위상을 정렬한 다음, 열두 스텝 동안 두 정책의 행동을 섞습니다.",
      "위상 정렬은 뒤집힘을 막고, 섞기는 남은 충격을 줄입니다. 역할이 나뉘어 있습니다."], size=9)
intent_result(s, X0, 4.3, CW, 2.5,
              ["뒤집히지 않는 것과 부드러운 것을 동시에 잡을 수 있는지 보고 싶었습니다."],
              ["한 쌍에서 충격 값이 155에서 57로 줄었습니다. 63퍼센트 감소입니다.",
               "경로 오차도 좋아졌습니다. 별은 0.43에서 0.33미터로, gauntlet은 0.47에서 0.35미터로 줄었습니다."], split=0.36)

# 13. 방향 화살표
s = content_slide("방향 화살표 표시")
y2 = add_video(s, "experts_star", X0, 1.3, 4.4, cap="별 경로입니다. 초록은 목표 방향, 파랑은 로봇이 향한 방향입니다.")
fit_image(s, FIGS["experts_star_traj"], X0, y2 + 0.05, 4.4, 2.35)
card(s, 5.15, 1.3, 4.3, 2.55, "무엇을 바꿨나",
     ["웨이포인트마다 목표 방향을 정했습니다. 기본값은 다음 점을 향하는 방향입니다.",
      "영상에서 웨이포인트를 공 대신 화살표로 그렸습니다. 로봇 위에도 파란 화살표를 그렸습니다.",
      "경로 추종 결과 숫자는 그대로입니다. 그림만 바꾼 것을 확인했습니다."], size=9)
intent_result(s, 5.15, 4.0, 4.3, 2.8,
              ["지금의 추종 방식이 로봇의 몸 방향을 전혀 다루지 않는다는 점을 눈으로 보이고 싶었습니다."],
              ["파란 화살표는 늘 같은 쪽을 보고, 초록 화살표는 모서리마다 90도씩 돕니다. 차이가 한눈에 보입니다.",
               "회전 정책을 경로 추종에 넣는 일은 다음 단계로 미루고, 먼저 전환 학습으로 넘어갔습니다."], split=0.38, size=9)

# 14. 간지
section_slide("Part 2. 전환을 스스로 다루는 정책 만들기", "전문가 열 개를 정책 하나에 옮겨 담고, 명령이 무작위로 바뀌는 환경에서 더 학습한 과정입니다.")

# 15. 설계 결정
s = content_slide("전환 학습을 시작하며 정한 것")
rows = [["무엇을 정했나", "고를 수 있던 것", "무엇을 골랐고 왜 골랐나"],
        ["출발점", "앞으로 가는 전문가 하나에서 시작할지, 열 개를 먼저 합칠지", "열 개를 먼저 합쳤습니다. 그래야 강화학습이 전환만 배우면 되기 때문입니다. 합치는 일은 답이 있는 회귀라서 몇 분이면 됩니다."],
        ["전환 방법", "처음 위상, 위상 정렬, 둘을 섞기", "위상 정렬을 골랐습니다. 물리적으로 가장 매끄럽고, 정책이 이 시작에 익숙해지면 약점이 사라집니다."],
        ["할인율", "0.95 또는 0.99", "0.99를 골랐습니다. 전환하고 100스텝 뒤에 넘어지는 일을 정책이 내다보려면 긴 시야가 필요합니다."],
        ["학습 설정", "검증된 첫 단계 값", "학습률 1e-4, 에포크 2, KL 한도 0.04, 4천만 스텝입니다."]]
add_table(s, rows, X0, 1.3, CW, 3.7, col_w=[1.4, 2.6, 4.9], size=8.5)
card(s, X0, 5.2, CW, 1.6, "설명 방식에 대한 피드백",
     ["처음에는 선택지만 나열해서 설명이 비약된다는 지적을 받았습니다. 그 뒤로는 각 선택지의 뜻과 비용과 위험을 풀어서 설명한 다음 결정했습니다."], size=9)

# 16. 증류 파이프라인
s = content_slide("전문가 열 개를 정책 하나로 합치기")
steps = [("모으기", "전문가 열 개를 각자 명령으로 돌리면서, 그때 본 것과 한 행동을 기록합니다."),
         ("정규화 통일", "전문가마다 달랐던 입력 정규화 값을 하나로 합칩니다."),
         ("따라 하기 학습", "새 정책이 전문가의 행동을 그대로 따라 하도록 학습합니다. 가치 함수도 미리 맞춰 둡니다."),
         ("보정", "새 정책을 직접 돌려 보고, 가 본 상태마다 전문가라면 어떻게 했을지 라벨을 붙여 다시 학습합니다."),
         ("검증", "명령마다 새 정책과 전문가를 열 판씩 비교합니다."),
         ("저장", "학습을 이어 갈 수 있는 형식으로 저장합니다. 모델과 정규화 값은 항상 같이 다닙니다.")]
step_cards(s, X0, 1.3, CW, steps, cols=3, card_h=1.55, size=8.5)
intent_result(s, X0, 4.65, CW, 2.15,
              ["강화학습을 시작하기 전에, 열 가지 명령을 이미 할 줄 아는 출발점을 만들고 싶었습니다."],
              ["처음에는 전문가의 정확한 행동만 기록했더니, 절반의 명령에서 새 정책이 넘어졌습니다. 조금만 벗어난 상태를 본 적이 없었기 때문입니다.",
               "전문가에 일부러 노이즈를 섞어 돌리고, 보정 단계를 네 번 넣자 열 개 중 아홉 개가 전문가 수준이 됐습니다."], split=0.34)

# 17. 증류 결과
s = content_slide("합친 정책의 실력")
v1 = [0.42, -0.08, -0.19, 0.54, -0.30, 0.48, 0.69, 0.80, 1.09, 0.23]
fin = [1.00, 0.98, 0.99, 0.98, 1.00, 0.95, 1.00, 1.00, 1.01, 0.60]
bar_chart(s, cmds, [("첫 시도", v1), ("최종", fin)], X0, 1.3, CW, 2.75, title="전문가 점수를 1로 봤을 때 새 정책의 점수", colors=[RED, BLUE], fmt="0.00", ymin=-0.4, ymax=1.2, label_size=6.5)
note(s, X0, 4.05, CW, 0.3, "첫 시도의 diag_fr는 실제로는 뒤로 갔습니다. 그림에서는 -0.3으로 잘라 그렸습니다.", size=8.5)
card(s, X0, 4.4, 4.35, 2.4, "시계 회전만 0.6인 이유",
     ["도는 속도는 정상인데, 시작점에서 천천히 밀려나다가 729스텝에 실패 판정을 받습니다.",
      "행동에 작은 노이즈만 줘도 여덟 번 중 다섯 번은 끝까지 버팁니다. 아슬아슬한 경계에 있는 것입니다.",
      "전문가의 기록에는 밀려났을 때 돌아오는 행동이 없어서, 따라 하기만으로는 못 배웁니다. 강화학습에서 고치기로 했습니다."], size=8.5)
intent_result(s, 5.1, 4.4, 4.35, 2.4,
              ["새 정책이 전문가의 90퍼센트 이상인지, 더 자주 넘어지지는 않는지 확인하고 싶었습니다."],
              ["열 개 중 아홉 개가 0.95에서 1.01 사이입니다. 넘어지는 일도 없습니다.",
               "데이터는 모두 180만 개를 썼고, 만드는 데 약 9분이 걸렸습니다."], split=0.32, size=8.5)

# 18. 전환 커리큘럼 환경
s = content_slide("명령이 무작위로 바뀌는 학습 환경")
rect(s, X0, 1.3, CW, 1.45)
add_text(s, X0 + 0.12, 1.36, 8.6, 0.3, [{"text": "한 에피소드는 이렇게 흘러갑니다 (1000스텝, 50초)", "size": 10.5, "bold": True, "color": NAVY}], margin=0)
tx, tw = X0 + 0.2, CW - 0.4
rect(s, tx, 1.95, tw, 0.2, "E1E6EC", None, rounded=False)
for a, b, lab, col in [(0, 0.28, "forward", NAVY), (0.28, 0.55, "diag_bl", TEAL), (0.55, 0.82, "ccw", ORANGE), (0.82, 1.0, "right", BLUE)]:
    rect(s, tx + a * tw, 1.95, (b - a) * tw, 0.2, col, None, rounded=False)
    add_text(s, tx + a * tw, 2.17, (b - a) * tw, 0.25, [{"text": lab, "size": 8, "color": TEXT, "align": PP_ALIGN.CENTER}], margin=0)
for a in (0.28, 0.55, 0.82):
    badge(s, tx + a * tw - 0.1, 1.78, 0.2, "↕", RED, size=8)
note(s, X0 + 0.12, 2.42, 8.6, 0.3, "빨간 표시가 명령이 바뀌는 순간입니다. 한 에피소드에 한 번에서 네 번 바뀌고, 최소 100스텝은 같은 명령을 유지합니다.", size=8.5)
rows = [["항목", "내용"],
        ["다음 명령", "지금 명령을 뺀 나머지 아홉 개에서 똑같은 확률로 고릅니다. 전환 쌍은 모두 90가지입니다."],
        ["바뀌는 시점", "물리 계산이 끝난 뒤, 정책에게 관측을 주기 전에 바꿉니다. 그래서 정책은 바뀐 gait를 바로 봅니다."],
        ["시작 위상", "에피소드가 시작할 때 gait 위상도 무작위로 정합니다. 전환 순간의 몸 상태가 다양해집니다."],
        ["확인한 것", "전문가로 40판을 돌려 보니 전환이 50번 일어났고, 위상 정렬은 모두 정확했습니다. 전문가는 27판에서 전환 직후 넘어졌습니다."]]
add_table(s, rows, X0, 2.9, CW, 2.2, col_w=[1.4, 7.5], size=8.5)
card(s, X0, 5.25, CW, 1.55, "시험하다 찾은 실수 두 가지",
     ["환경 인자 이름을 max_episode_steps로 지으면 gym이 가로채서 환경에 전달되지 않습니다. 이름을 episode_horizon으로 바꿨습니다.",
      "거꾸로 재생하는 gait의 위상 정렬에서 부호를 안 뒤집는 버그가 있었습니다. 위험한 세 쌍이 모두 앞으로 가는 gait라 그동안 드러나지 않았습니다."], size=9)

# 19. 앵커 문제 ①
s = content_slide("첫 학습에서 만난 문제 ① 회전 진입")
rows = [["무엇을 쟀나 (회전으로 전환한 24번)", "값"],
        ["100스텝 안에 실패한 비율", "54퍼센트입니다. 걷기로 전환할 때는 9퍼센트입니다."],
        ["전환 직전 속도", "초당 0.44미터입니다."],
        ["전환 뒤 시작점에서 벗어난 거리", "평균 0.37미터입니다. 88퍼센트가 0.2미터를 넘었습니다."],
        ["60스텝 뒤에 기준점을 다시 잡으면", "벗어난 거리가 0.04미터로 줄고, 0.2미터를 넘는 경우가 없습니다."]]
add_table(s, rows, X0, 1.3, CW, 2.0, col_w=[4.4, 4.5], size=9)
card(s, X0, 3.5, 4.35, 3.3, "무슨 일이 일어났나",
     ["회전으로 바뀌는 순간 기준점이 찍히는데, 몸은 아직 미끄러지고 있습니다. 관성만으로 0.2미터를 넘습니다.",
      "회전 gait는 미끄러짐을 멈추거나 되돌아오지 못합니다. 그래서 60스텝 규칙에 걸려 실패합니다.",
      "이건 정책이 고칠 수 없는 규칙 문제입니다. 게다가 정책이 평소에 천천히 걷도록 잘못 배울 위험도 있습니다."], size=9)
intent_result(s, 5.1, 3.5, 4.35, 3.0,
              ["회전으로 전환할 때 자꾸 실패하는 것이 정책 탓인지 규칙 탓인지 가려내고 싶었습니다."],
              ["규칙 탓이었습니다. 처음에는 기준점을 조금 늦게 잡자고 제안했습니다.",
               "그런데 실패 대신 기준점 가까이 있으면 점수를 더 주자는 제안을 받았고, 그 방식이 더 좋았습니다."], split=0.32, size=9)

# 20. 앵커 문제 ②
s = content_slide("첫 학습에서 만난 문제 ② 새 보상 설계")
rows2 = [["기준점과의 거리", "가까이 있어서 받는 점수", "멀어서 받는 벌점", "한 스텝 합계"],
         ["0미터", "+10", "0", "+35"], ["0.1미터", "+5", "-5", "+25"], ["0.2미터", "0", "-10", "+15"],
         ["0.4미터 (관성으로 밀린 평균)", "0", "-20", "+5"], ["0.55미터 이상", "0", "-27 이하", "마이너스"]]
add_table(s, rows2, X0, 1.3, 4.4, 2.3, col_w=[1.6, 1.0, 0.9, 0.9], size=9)
note(s, X0, 3.65, 4.4, 0.7, "합계는 목표 속도로 돌 때 받는 점수 25를 더한 값입니다. 실패 판정은 없앴고, 멀어질수록 깎는 벌점은 그대로 두었습니다.", size=8.5)
card(s, 5.15, 1.3, 4.3, 3.05, "설계할 때 지킨 원칙",
     ["가까울수록 점수가 올라가고, 아주 멀어져도 벌점이 무한히 커지지는 않게 했습니다.",
      "가까이 있는 점수 10은 도는 점수 22.5보다 작게 두었습니다. 그래야 가만히 있는 것이 도는 것보다 유리해지지 않습니다.",
      "밀려난 거리를 줄이면 점수가 오르니, 정책이 부드럽게 진입하는 법을 배울 이유가 생깁니다."], size=9)
intent_result(s, X0, 4.5, CW, 2.3,
              ["실패 판정을 점수로 바꿨을 때 계산이 맞는지, 부작용은 없는지 확인하고 싶었습니다."],
              ["점수는 설계한 대로 나왔습니다. 회전으로 전환할 때 실패하는 비율이 54퍼센트에서 19퍼센트로 줄었습니다. 남은 것은 넘어지는 경우입니다.",
               "기본 설정으로 만든 환경은 예전과 똑같이 동작하는 것도 확인했습니다. 첫 학습은 멈추고 다시 시작했습니다."], split=0.34)

# 21. Stage 1 결과
s = content_slide("첫 단계 학습 결과 (4천만 스텝)")
line_chart(s, [("평가 점수", CURVES["s1_eval"]), ("학습 중 점수 (이동평균)", CURVES["s1_ep_rew"])], X0, 1.3, 3.0, 2.2, title="점수", colors=[BLUE, NAVY], fmt="#,##0")
line_chart(s, [("가치 함수가 설명하는 비율", CURVES["s1_ev"])], 3.5, 1.3, 2.95, 2.2, title="가치 함수의 정확도", colors=[TEAL], ymin=-0.2, ymax=1.0, legend=False)
line_chart(s, [("전환 뒤 100스텝 안에 실패한 비율", CURVES["s1_fail"])], 6.5, 1.3, 2.95, 2.2, title="전환 실패율 (이동평균)", colors=[RED], ymin=0, ymax=0.5, legend=False)
f0, f1 = CURVES["s0_fail_to"], CURVES["s1_fail_to"]
bar_chart(s, cmds, [("첫 시도 (실패 판정 규칙)", [round(f0[c], 3) for c in cmds]), ("첫 단계 끝 (새 보상)", [round(f1[c], 3) for c in cmds])],
          X0, 3.6, 5.3, 3.2, title="어떤 명령으로 바뀔 때 실패하는가 (100스텝 안 실패 비율)", colors=[RED, BLUE], fmt="0.00", ymax=0.8, label_size=6.5)
intent_result(s, 6.0, 3.6, 3.45, 3.2,
              ["합쳐 둔 정책이 무너지지 않는지, 전환 실력이 붙는지 보고 싶었습니다."],
              ["무너지지 않았습니다. 학습 중 점수는 마이너스 1만 6천에서 플러스 1만 3천으로 올랐습니다.",
               "회전으로 바뀔 때 실패하던 문제가 사라졌습니다. 이제는 diag_fr와 diag_bl로 바뀔 때만 셋 중 하나꼴로 실패합니다."], split=0.26, size=8.5)

# 22. Stage 2·3
s = content_slide("둘째와 셋째 단계 결과")
line_chart(s, [("둘째 단계 평가", CURVES["s2_eval"]), ("셋째 단계 평가", CURVES["s3_eval"]), ("둘째 단계 학습 중", CURVES["s2_ep_rew"]), ("셋째 단계 학습 중", CURVES["s3_ep_rew"])],
           X0, 1.3, 4.4, 2.6, title="점수 (누적 스텝)", colors=[BLUE, ORANGE, NAVY, "8E44AD"], fmt="#,##0")
line_chart(s, [("둘째 단계", CURVES["s2_kl"]), ("셋째 단계", CURVES["s3_kl"])], 5.15, 1.3, 4.3, 2.6, title="정책이 한 번에 얼마나 바뀌는가 (KL, 한도 0.04)", colors=[BLUE, ORANGE], ymin=0, fmt="0.000")
f2, f3 = CURVES["s2_fail_to"], CURVES["s3_fail_to"]
bar_chart(s, cmds, [("둘째 단계 끝", [round(f2[c], 3) for c in cmds]), ("셋째 단계 끝", [round(f3[c], 3) for c in cmds])],
          X0, 4.0, 5.3, 2.8, title="어떤 명령으로 바뀔 때 실패하는가", colors=[BLUE, ORANGE], fmt="0.00", ymax=0.5, label_size=6.5)
card(s, 6.0, 4.0, 3.45, 2.8, "요약",
     ["둘째 단계에서는 에포크를 3으로 올렸지만 정책이 거의 바뀌지 않았습니다.",
      "셋째 단계에서 학습률을 두 배로 올리자 정책이 움직이기 시작했습니다.",
      "점수는 크게 오르지 않았지만, diag_bl로 바뀔 때 실패하는 비율이 0.35에서 0.12로 줄었습니다."], size=9)

# 23. 정체 원인
s = content_slide("왜 더 좋아지지 않았나")
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
label(s, X0, 1.3, CW, "위상을 맞춰도 부호가 몇 개나 같아질 수 있는가 (14가 전부 같음)")
add_table(s, rows, X0, 1.62, CW, 2.85, col_w=[1.1] + [0.78] * 10, size=7.5)
card(s, X0, 4.6, 4.35, 2.2, "gait가 두 집안으로 나뉩니다",
     ["앞으로, 뒤로, 왼쪽, 그리고 대각선 두 개가 한 집안입니다. 오른쪽과 나머지 대각선 두 개가 다른 집안입니다.",
      "같은 집안끼리는 부호가 거의 다 맞습니다. 집안을 건너면 어느 위상에서 시작해도 관절 아홉 개쯤이 뒤집힙니다."], size=8.5)
card(s, 5.1, 4.6, 4.35, 2.2, "실험으로 확인한 것",
     ["diag_fr로 바뀔 때는 20스텝만 힘을 빼고 있으면 거의 넘어지지 않습니다. 정책이 그 방법을 못 배웠을 뿐입니다.",
      "diag_bl로 바뀔 때는 힘을 빼도 넘어집니다. 위상 정렬이 고른 시작 위상 자체가 나쁜 경우입니다."], size=8.5)

# 24~25. 통합 정책 경로 추종
s = content_slide("합친 정책 하나로 경로 따라가기 ①")
vw = 2.85
add_video(s, "unified_square", X0, 1.3, vw, cap="네모: 오차 0.18미터, 전환 8번, 37초")
add_video(s, "unified_star", X0 + vw + 0.17, 1.3, vw, cap="별: 오차 0.34미터, 전환 15번, 59초")
add_video(s, "unified_gauntlet", X0 + 2 * (vw + 0.17), 1.3, vw, cap="gauntlet: 오차 0.25미터, 전환 13번, 59초")
card(s, X0, 3.35, CW, 1.4, "어떻게 돌렸나",
     ["정책 하나가 모든 명령을 맡습니다. 명령이 바뀌면 학습 때와 똑같이 위상을 정렬하고, 정책은 바뀐 gait를 바로 봅니다.",
      "두 정책의 행동을 섞는 단계는 없습니다. 전환을 다루는 일은 이제 정책의 몫입니다."], size=9)
intent_result(s, X0, 4.9, CW, 1.9,
              ["전환을 배운 정책이 전문가를 바꿔 끼우던 방식보다 나은지 같은 경로에서 비교하고 싶었습니다."],
              ["위험한 전환이 몰린 gauntlet에서 오차가 27퍼센트 줄고, 전환 횟수는 3분의 1, 시간은 절반이 됐습니다.",
               "네모와 별은 오차가 비슷하지만 시간이 더 걸렸습니다. 전환 직후에 속도가 줄기 때문입니다."], split=0.36, size=9)

s = content_slide("합친 정책 하나로 경로 따라가기 ②")
bar_chart(s, ["네모", "별", "gauntlet"], [("전문가 바꿔 끼우기", [0.193, 0.334, 0.345]), ("합친 정책", [0.180, 0.343, 0.253])],
          X0, 1.3, 4.4, 2.5, title="평균 오차 (미터)", colors=[NAVY, BLUE], fmt="0.000")
bar_chart(s, ["네모", "별", "gauntlet"], [("전문가 바꿔 끼우기", [20.0, 42.5, 128.8]), ("합친 정책", [37.5, 58.8, 58.8])],
          5.15, 1.3, 4.3, 2.5, title="완주 시간 (초)", colors=[NAVY, BLUE], fmt="0.0")
rows = [["어떤 정책", "네모", "별", "gauntlet", "평균 오차", "총 시간"],
        ["전문가 바꿔 끼우기", "0.193 / 20초", "0.334 / 43초", "0.345 / 129초", "0.291", "192초"],
        ["첫 단계 끝", "0.180 / 38초", "0.343 / 59초", "0.253 / 59초", "0.259", "155초"],
        ["둘째 단계 최고", "0.321 / 30초", "0.273 / 46초", "0.219 / 70초", "0.271", "146초"],
        ["둘째 단계 끝", "0.164 / 21초", "0.280 / 40초", "0.408 / 86초", "0.284", "147초"],
        ["셋째 단계 최고", "0.211 / 19초", "0.472 / 125초", "0.298 / 49초", "0.327", "193초"],
        ["셋째 단계 끝", "0.447 / 50초", "0.306 / 61초", "0.223 / 33초", "0.325", "144초"]]
add_table(s, rows, X0, 3.95, CW, 2.1, col_w=[2.0, 1.45, 1.45, 1.45, 1.25, 1.3], size=8)
note(s, X0, 6.1, CW, 0.7, "한 경로를 한 번씩만 돈 결과라서, 전환 한 번의 실패가 평균을 크게 흔듭니다. 어떤 정책이 나은지는 뒤에 나오는 40판 벤치마크로 정했습니다.", size=8.5)

# 26~28. 정책 시각화
s = content_slide("시각화 ① 열 가지 명령 차례로")
yb = add_video(s, "show_tour", X0, 1.3, 4.6, cap="열 가지 명령을 6초씩 차례로 바꿔 가며 돌린 영상입니다.")
rows = [["구간", "명령", "불안정했던 스텝 수 (120 중)"],
        ["1, 3, 4, 5", "forward, right, diag_br, backward", "0"],
        ["2", "diag_fr", "12"],
        ["6", "diag_bl", "24"],
        ["7", "left", "0"],
        ["8", "diag_fl (앞 구간의 여파)", "63"],
        ["9, 10", "ccw, cw", "0"]]
add_table(s, rows, 5.35, 1.3, 4.1, 2.7, col_w=[0.9, 2.0, 1.2], size=8.5)
card(s, 5.35, 4.15, 4.1, 2.65, "화면에 나오는 정보",
     ["왼쪽 위에는 지금 명령과 전환한 뒤 지난 시간이 나옵니다. 동그라미 안 화살표는 목표 방향입니다.",
      "왼쪽 아래 막대는 정책이 관절 열네 개에 주는 힘의 세기입니다.",
      "바닥의 노란 상자는 명령이 바뀐 자리이고, 파란 화살표는 로봇이 향한 방향입니다."], size=8.5)
intent_result(s, X0, yb + 0.05, 4.6, 6.8 - yb - 0.05,
              ["정책 하나가 열 가지 명령과 그 사이 전환을 어떻게 해내는지 한 번에 보고 싶었습니다."],
              ["열 구간 중 여덟 구간은 깨끗합니다. diag_fr와 diag_bl로 바뀔 때만 흔들렸습니다. 벤치마크와 같은 결과입니다."], split=0.36, size=8.5)

s = content_slide("시각화 ② 전환 느리게 보기")
y2 = add_video(s, "show_close_ok", X0, 1.3, 4.4, cap="forward에서 diag_fr로. 150스텝 동안 안정했습니다.")
add_video(s, "show_close_fail", X0, y2 + 0.05, 4.4, cap="backward에서 diag_bl로. 61스텝 동안 불안정했습니다.")
card(s, 5.15, 1.3, 4.3, 2.65, "힘의 막대를 보면",
     ["성공한 경우에는 전환 직후 몇 스텝 동안 힘을 낮췄다가 새 리듬에 맞춰 다시 올립니다. 학습된 부드러운 진입입니다.",
      "실패한 경우에는 힘을 조절해도 몸이 뒤집힙니다. 시작 위상 자체가 나쁜 경우입니다.",
      "나머지 세 쌍은 모두 안정했습니다."], size=8.5)
intent_result(s, 5.15, 4.1, 4.3, 2.7,
              ["위험한 전환에서 정책이 실제로 무엇을 하는지 절반 속도로 보고 싶었습니다."],
              ["diag_fr로 가는 전환은 힘 조절로 풀리는 유형이고, diag_bl로 가는 전환은 시작 위상을 고쳐야 하는 유형입니다.",
               "그래서 다음 과제로 집안을 건너는 전환의 시작 위상 규칙 개선을 올려 두었습니다."], split=0.34, size=8.5)

s = content_slide("시각화 ③ 경로 따라가기")
add_video(s, "show_path_square", X0, 1.3, vw, cap="네모: 오차 0.34미터, 전환 24번, 91초")
add_video(s, "show_path_star", X0 + vw + 0.17, 1.3, vw, cap="별: 오차 0.31미터, 전환 13번, 61초")
add_video(s, "show_path_gauntlet", X0 + 2 * (vw + 0.17), 1.3, vw, cap="gauntlet: 오차 0.22미터, 전환 7번, 33초")
rows = [["경로", "전문가 바꿔 끼우기", "합친 정책, 첫 단계 끝", "합친 정책, 셋째 단계 끝"],
        ["네모", "0.193미터 / 5번 / 20초", "0.180 / 8번 / 38초", "0.341 / 24번 / 91초"],
        ["별", "0.334 / 10번 / 43초", "0.343 / 15번 / 59초", "0.306 / 13번 / 61초"],
        ["gauntlet", "0.345 / 34번 / 129초", "0.253 / 13번 / 59초", "0.223 / 7번 / 33초"]]
add_table(s, rows, X0, 3.4, CW, 1.55, col_w=[1.3, 2.6, 2.5, 2.5], size=8.5)
intent_result(s, X0, 5.1, CW, 1.7,
              ["대표로 고른 정책으로 세 경로를 다시 돌려 기준과 비교하고 싶었습니다."],
              ["gauntlet과 별은 좋아졌습니다. gauntlet은 전환 7번, 33초로 전문가 방식의 4분의 1 시간입니다. 네모는 전환 한 번의 흔들림 때문에 시간이 늘었습니다."], split=0.4, size=8.5)

# 29. 배운 것
s = content_slide("배운 것 일곱 가지")
insights = [
    ("전환의 본질은 부호 맞추기", "방향은 gait가 정합니다. 전환이 실패하는 이유는 정책이 아니라, 두 gait의 위상과 부호가 부딪히기 때문입니다."),
    ("위상 정렬이 페이드보다 낫다", "원인을 없애면 기다릴 필요가 없습니다. 페이드는 증상만 줄이고, 정렬 위에 얹으면 오히려 방해가 됩니다."),
    ("위험한 쌍에만 쓴다", "전문가는 처음 위상에서만 학습했습니다. 그래서 정렬과 섞기는 위험한 쌍에만 쓰고, 안전한 쌍은 그냥 바꿉니다."),
    ("안 되는 것도 기록한다", "여러 스텝 맞추기, 정렬과 페이드 섞기, 모든 전환에 페이드 쓰기는 실험으로 버렸고, 이유를 적어 두었습니다."),
    ("합치는 일은 빠르지만 함정이 있다", "전문가의 정확한 행동만 기록하면 새 정책은 조금만 벗어나도 넘어집니다. 노이즈와 보정이 필요했습니다."),
    ("규칙이 물리를 이길 수 없다", "미끄러지는 몸을 실패로 처벌하면 잘못 배웁니다. 점수로 바꾸자 실패가 54퍼센트에서 19퍼센트로 줄었습니다."),
    ("정책 하나의 장점은 어려운 곳에서 드러난다", "쉬운 경로는 비슷하지만, 위험한 전환이 몰린 경로에서 오차와 시간이 크게 줄었습니다. 남은 벽은 gait 집안을 건너는 전환입니다."),
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

# ============================================================================= Part 3. 전문가 이어 학습
section_slide("Part 3. 전문가를 움직이는 상태에서 다시 학습하기", "전문가가 정지 상태가 아니라, 다른 정책이 움직이던 상태에서 시작하도록 이어 학습한 과정입니다. 2026년 9월 10일부터 11일까지입니다.")

# P3-1 왜 시작했나
s = content_slide("이어 학습 ① 왜 시작했나")
card(s, X0, 1.3, 4.35, 2.6, "문제의식",
     ["전문가는 늘 멈춘 자세에서, 처음 위상으로 학습을 시작했습니다.",
      "그런데 실제로 전환이 일어나는 순간에는 로봇이 이미 다른 gait로 움직이고 있습니다.",
      "그 상태는 전문가가 한 번도 본 적이 없는 상태입니다. 그래서 전환 직후에 자주 넘어집니다."], size=9)
card(s, 5.1, 1.3, 4.35, 2.6, "해결 방향",
     ["에피소드의 절반은 다른 정책이 움직이던 상태에서 시작하게 합니다. 시작하는 순간 새 gait로 위상을 맞춰 바꿉니다.",
      "나머지 절반은 예전처럼 멈춘 자세에서 시작합니다. 그래야 평소 걷는 실력이 떨어지지 않습니다.",
      "은행에 상태를 많이 모아 두고, 학습이 끝나면 은행을 다시 만들어 반복합니다."], size=9)
rows = [["용어", "뜻"],
        ["인계 시작", "다른 정책이 움직이던 몸 상태를 그대로 물려받아 에피소드를 시작하는 것입니다."],
        ["위상 정렬 전환", "새 gait를 지금 부호와 가장 닮은 위상에서 시작하는 것입니다. 지금 쓰는 전환 방법입니다."],
        ["상태 은행", "인계 시작에 쓸 몸 상태를 미리 모아 둔 파일입니다. 출발 명령마다 2만 개, 모두 22만 개입니다."]]
add_table(s, rows, X0, 4.1, CW, 1.6, col_w=[1.5, 7.4], size=9)
note(s, X0, 5.85, CW, 0.9, "이 방식은 DeepMimic에서 쓴 참조 상태 초기화와 같은 계열입니다. 학습 분포와 실제 전환 순간의 분포를 같게 만드는 것이 핵심입니다.", size=9)

# P3-2 만든 것
s = content_slide("이어 학습 ② 새로 만든 것")
steps = [("상태 은행 만들기", "전문가 열 개를 돌리면서 매 스텝의 몸 상태를 저장합니다. 노이즈를 섞은 롤아웃, 전환 뒤의 상태, 합친 정책의 상태도 넣었습니다."),
         ("인계 시작 환경", "기존 환경의 보상과 판정은 그대로 두고, 시작만 절반 확률로 은행 상태에서 하도록 만들었습니다. 이름은 plane-moving-init-v0입니다."),
         ("평가 도구", "멈춘 자세에서 걷는 실력과, 아홉 가지 출발에서 들어올 때 100스텝 안에 넘어지는 비율을 재는 스크립트입니다."),
         ("학습 설정 파일", "세 전문가용으로 설정 파일을 만들었습니다. 각 전문가의 마지막 모델에서 이어서 학습합니다."),
         ("기록 항목 추가", "정지 시작과 인계 시작을 나누어 점수와 실패율을 텐서보드에 남기도록 콜백을 고쳤습니다."),
         ("녹화 카메라 수정", "학습 중 저장하는 영상에서 로봇이 화면 밖으로 나가는 문제를 고쳤습니다. 이제 카메라가 로봇을 따라갑니다.")]
step_cards(s, X0, 1.3, CW, steps, cols=3, card_h=1.75, size=8.5)
if "iter2_forward_train" in VIDEOS:
    yb = add_video(s, "iter2_forward_train", X0, 5.05, 3.1, cap="두 번째 파일럿의 학습 영상입니다. 카메라가 로봇을 따라갑니다.")
card(s, 3.85, 5.05, 5.6, 1.75, "시험으로 확인한 것",
     ["인계 시작 비율은 0.53으로 설정값 0.5에 맞았고, 절단 규칙과 관측도 정상이었습니다.",
      "기존 diag_fr 전문가는 인계 시작 32번 중 10번을 100스텝 안에 넘어졌습니다. 멈춘 자세에서는 한 번도 안 넘어졌습니다. 배울 것이 분명히 있었습니다."], size=8.5)

# P3-3 파일럿 1 결과
def eval_row(name, key, field):
    e = EVALS.get(key)
    if not e or name not in e:
        return "-"
    return f"{e[name]['entry_fail_mean']:.3f}" if field == "fail" else f"{e[name]['rest']['speed']:.3f}"

s = content_slide("이어 학습 ③ 첫 파일럿 결과")
rows = [["전문가", "멈춘 자세에서 걷는 속도 (전 → 후)", "전환 뒤 100스텝 안 실패 비율: 기준 → 학습 뒤 (final) → (best)"]]
for name in ("diag_fr", "diag_bl", "forward"):
    rows.append([name, f"{eval_row(name, 'baseline_iter1', 'speed')} → {eval_row(name, 'iter1_final', 'speed')} 미터/초",
                 f"{eval_row(name, 'baseline_iter1', 'fail')} → {eval_row(name, 'iter1_final', 'fail')} → {eval_row(name, 'iter1_best', 'fail')}"])
add_table(s, rows, X0, 1.3, CW, 1.6, col_w=[1.2, 3.2, 4.5], size=9)
card(s, X0, 3.05, 4.35, 3.75, "무엇을 알게 됐나",
     ["평소 걷는 실력은 세 전문가 모두 그대로였습니다. 정지 시작을 섞은 효과입니다.",
      "그런데 전환 뒤에 넘어지는 비율은 거의 줄지 않았습니다. 학습 중에 오른 점수는 넘어지지 않은 경우의 주행이 좋아진 것이었습니다.",
      "새 diag_fr 전문가에게 전환 직후 20스텝 동안 힘을 빼게 하면, left에서 들어올 때 실패가 0.6에서 0으로 줄었습니다. 피할 수 있는데 못 배운 것입니다."], size=9)
card(s, 5.1, 3.05, 4.35, 3.75, "왜 못 배웠나",
     ["넘어질 때 받는 벌점이 2점뿐이었습니다. 게다가 할인율 0.95라 20스텝 뒤는 거의 보지 않습니다.",
      "그래서 잠깐 힘을 빼고 버티는 것과, 바로 달리다 넘어지는 것의 기대 점수가 비슷했습니다. 배울 이유가 없었습니다.",
      "diag_bl로 들어오는 경우는 힘을 빼도 넘어집니다. 이건 시작 위상 규칙을 고쳐야 하는 별개의 문제입니다."], size=9)

# P3-4 결함 발견
s = content_slide("이어 학습 ④ 찾아낸 결함과 수정")
card(s, X0, 1.3, CW, 2.2, "낙상 벌점이 한 번도 적용된 적이 없었습니다",
     ["벌점을 200으로 올려 시험해 보니, 넘어지는 스텝의 벌점이 여전히 0이었습니다.",
      "원인은 기존 환경이 실패 판정을 한 스텝에 두 번 확인하는 데 있었습니다. 보상을 계산할 때는 아직 실패 전이고, 그 직후에 에피소드가 끝납니다.",
      "그래서 지금까지의 전문가 열 개는 넘어져도 벌점 2점조차 받은 적이 없었습니다. 실패 판정도 설정의 절반인 약 15스텝 만에 났습니다."], size=9)
card(s, X0, 3.65, 4.35, 3.15, "어떻게 고쳤나",
     ["기존 환경 파일은 손대지 않았습니다. 예전 정책들의 의미를 지키기 위해서입니다.",
      "인계 시작 환경의 step 함수에서, 에피소드가 끝나는 스텝에 벌점을 한 번 얹도록 보정했습니다.",
      "실패 판정이 나는 시점은 예전과 똑같이 두었습니다."], size=9)
card(s, 5.1, 3.65, 4.35, 3.15, "확인한 것",
     ["무작위로 움직여 넘어지게 해 보니, 끝나는 스텝의 벌점이 정확히 마이너스 200이었습니다. 기본 설정에서는 마이너스 2였습니다.",
      "이 결함은 첫 파일럿에서 전환 실패가 줄지 않은 직접 원인이기도 합니다."], size=9)

# P3-5 iteration 2
s = content_slide("이어 학습 ⑤ 두 번째 파일럿")
rows = [["항목", "첫 파일럿", "두 번째 파일럿"],
        ["시작 모델", "각 전문가의 셋째 단계 모델", "첫 파일럿의 마지막 모델"],
        ["넘어질 때 벌점", "2 (실제로는 적용 안 됨)", "200 (끝나는 스텝에 한 번)"],
        ["학습률", "1e-4", "5e-5 (첫 파일럿에서 정책이 너무 많이 바뀌어서)"],
        ["나머지", "인계 시작 50퍼센트, 위상 정렬 80퍼센트, 2천8백만 스텝", "같음"]]
add_table(s, rows, X0, 1.3, CW, 1.9, col_w=[1.5, 3.5, 3.9], size=9)
rows = [["전문가", "멈춘 자세에서 걷는 속도 (기준 → 두 번째 뒤)", "전환 뒤 실패 비율: 기준 → 첫 파일럿 → 두 번째 (final) → (best)"]]
for name in ("diag_fr", "diag_bl", "forward"):
    rows.append([name, f"{eval_row(name, 'baseline_iter1', 'speed')} → {eval_row(name, 'iter2_final', 'speed')} 미터/초",
                 f"{eval_row(name, 'baseline_iter1', 'fail')} → {eval_row(name, 'iter1_final', 'fail')} → {eval_row(name, 'iter2_final', 'fail')} → {eval_row(name, 'iter2_best', 'fail')}"])
add_table(s, rows, X0, 3.35, CW, 1.6, col_w=[1.2, 3.2, 4.5], size=9)
card(s, X0, 5.1, CW, 1.85, "판정",
     ["걷는 실력은 그대로 유지됐고 벌점도 제대로 적용됐지만, 전환 뒤 실패 비율은 두 번째 파일럿에서도 줄지 않았습니다.",
      "행동에 무작위를 섞어 평가해도 결과는 비슷했습니다. 평균 행동이 아슬아슬해서 생기는 문제가 아니라, 정책이 아직 그 상황을 배우지 못한 것입니다.",
      "즉 벌점을 올리는 것만으로는 부족했습니다. 다음 수정 후보는 다음 단계 슬라이드에 적었습니다."], size=9)

# P3-6 바뀐 파일
s = content_slide("이어 학습 ⑥ 바뀐 파일 목록")
rows = [["파일", "무엇을 했나"],
        ["horcrux_env/envs/plane_moving_init_v1.py", "인계 시작 환경입니다. 새로 만들었고, 끝나는 스텝의 벌점 보정도 여기 있습니다."],
        ["horcrux_env/__init__.py, envs/__init__.py", "새 환경을 plane-moving-init-v0 이름으로 등록했습니다."],
        ["training/build_moving_state_bank.py", "상태 은행을 만드는 스크립트입니다. 새로 만들었습니다."],
        ["training/eval_expert_transitions.py", "걷는 실력과 전환 실패율을 재는 평가 스크립트입니다. 새로 만들었습니다."],
        ["training/callbacks/info_metrics.py", "정지 시작과 인계 시작을 나누어 기록하는 항목을 더했습니다."],
        ["training/callbacks/video_recorder.py, train.py", "학습 녹화 카메라가 로봇을 따라가도록 고쳤습니다."],
        ["training/path_following.py", "경로 시연에서 특정 전문가를 새 모델로 바꿔 끼우는 옵션을 더했습니다."],
        ["training/configs/ppo_plane_*_moving_init_iter1.yaml, iter2.yaml", "세 전문가의 파일럿 설정 두 벌입니다."],
        ["policies/path_tracking/MOVING_INIT_CAMPAIGN.txt", "이 캠페인의 기록 원장입니다. 은행, 기준선, 결과, 진단을 적어 둡니다."]]
add_table(s, rows, X0, 1.3, CW, 4.6, col_w=[3.6, 5.3], size=8.5)
note(s, X0, 6.0, CW, 0.8, "모든 변경은 CLAUDE_CHANGES.md에도 날짜와 이유와 함께 적혀 있습니다. 예전 정책 파일과 기존 환경 파일은 바꾸지 않았습니다.", size=9)

# P3-7 세 번째 파일럿
s = content_slide("이어 학습 ⑦ 세 번째 파일럿")
rows = [["항목", "세 번째 파일럿 (2026년 9월 11일)"],
        ["시작 모델", "원본인 셋째 단계 최종 모델. 두 번의 파일럿이 효과가 없어서 처음부터 다시 시작했습니다."],
        ["새로 넣은 보상 항", "기울기 벌점과 기운 채로 세게 밀기 벌점, 각각 20점. 몸통이 15도 넘게 기울 때만 붙고, 인계 시작 에피소드에만 적용했습니다."],
        ["나머지", "넘어질 때 벌점 200, 학습률 1e-4, 인계 시작 50퍼센트, 위상 정렬 80퍼센트, 2천8백만 스텝"]]
add_table(s, rows, X0, 1.3, CW, 1.6, col_w=[1.6, 7.3], size=9)
rows = [["전문가", "멈춘 자세에서 걷는 속도 (기준 → 세 번째 뒤)", "전환 뒤 실패 비율: 기준 → 세 번째 (final) → (best)"]]
for name in ("diag_fr", "diag_bl", "forward"):
    rows.append([name, f"{eval_row(name, 'baseline_iter1', 'speed')} → {eval_row(name, 'iter3_final', 'speed')} 미터/초",
                 f"{eval_row(name, 'baseline_iter1', 'fail')} → {eval_row(name, 'iter3_final', 'fail')} → {eval_row(name, 'iter3_best', 'fail')}"])
add_table(s, rows, X0, 3.05, CW, 1.5, col_w=[1.2, 3.4, 4.3], size=9)
card(s, X0, 4.7, CW, 2.15, "무엇을 알게 됐나",
     ["학습 내내 벌점의 크기가 처음 값 그대로였습니다. 매 스텝 신호를 줬는데도 정책이 그 벌점을 피하는 행동을 찾지 못했다는 뜻입니다.",
      "forward만 0.167에서 0.117로 줄었고, diag_fr와 diag_bl은 그대로였습니다. 멈춘 자세 주행 점수는 2에서 4퍼센트 내려갔습니다.",
      "그래서 힘의 크기를 조절하는 것으로는 이 출발 상태를 구하기 어렵다고 보고, 출발 상태 자체를 바꾸는 쪽으로 방향을 돌렸습니다."], size=9)

# P3-8 시작 위상 규칙의 발견
s = content_slide("이어 학습 ⑧ 시작 위상 규칙의 발견")
_f3 = ROOT / "docs/figures/phase_selection/F3_agreement_heatmap.png"
if _f3.exists():
    ox, oy, bw, bh = fit_image(s, _f3, X0, 1.3, 4.1, 3.6)
    caption(s, X0, oy + bh + 0.03, 4.1, "위상을 맞춰도 부호가 몇 개나 같아지는지를 gait 쌍마다 그린 표입니다. 짙은 네모 두 개가 두 집안입니다.")
card(s, X0 + 4.3, 1.3, CW - 4.3, 3.95, "무엇을 찾았나",
     ["부호 열네 개를 두 묶음으로 나눴습니다. 홀수 관절은 세로 파동이고 땅에 닿는 마디를 정합니다. 짝수 관절은 가로 파동이고 미는 방향을 정합니다.",
      "집안을 건너는 전환에서는 둘을 동시에 맞출 수 없습니다. 후보 위상을 전부 시도한 기록으로 보니, 가로를 맞춘 위상은 0.86이 살아남고 세로를 맞춘 위상은 0.38만 살아남았습니다.",
      "그래서 가로를 먼저 맞추고, 같으면 세로로 정하는 규칙을 만들었습니다. 코드 몇 줄이고 학습이 없습니다.",
      "뜻은 이렇습니다. 집안을 건널 때는 미는 방향을 잇고 땅에 닿는 마디를 바꾸는 쪽이, 그 반대보다 안전합니다."], size=9)
card(s, X0, 5.4, CW, 1.45, "확인한 것",
     ["대표 전문가 여덟 개를 같은 1,440개 상태에서 평가하니, 진입 실패가 평균 0.231에서 0.158로 줄었습니다. 여덟 목표 모두 줄었고, 집안을 건너는 전환은 0.34에서 0.22로 줄었으며 같은 집안은 그대로였습니다.",
      "수학적 근거와 실험은 별도 덱 docs/Horcrux_phase_selection_math_2026-09.pptx에 정리했습니다. 규칙 함수는 horcrux_env/envs/phase_align.py에 있습니다."], size=9)

# P3-9 네 번째 파일럿
s = content_slide("이어 학습 ⑨ 네 번째 파일럿")
rows = [["항목", "네 번째 파일럿 (2026년 9월 12일)"],
        ["시작 모델", "원본인 셋째 단계 최종 모델"],
        ["바꾼 것", "인계 시작의 위상 규칙을 가로 먼저로 바꿨습니다. 80퍼센트는 이 규칙, 20퍼센트는 무작위 위상입니다."],
        ["뺀 것", "세 번째 파일럿의 벌점 항 두 개. 효과가 없었고 주행 점수를 깎았기 때문입니다."],
        ["나머지", "넘어질 때 벌점 200, 학습률 1e-4, 인계 시작 50퍼센트, 2천8백만 스텝"]]
add_table(s, rows, X0, 1.3, CW, 1.75, col_w=[1.6, 7.3], size=9)
rows = [["전문가", "걷는 속도 (기준 → 네 번째 뒤)", "새 규칙으로 잰 실패: 원본 → 네 번째 (final) → (best)", "지금 규칙으로 잰 실패: 기준 → 네 번째"]]
for name in ("diag_fr", "diag_bl", "forward"):
    rows.append([name, f"{eval_row(name, 'baseline_iter1', 'speed')} → {eval_row(name, 'iter4_final', 'speed')}",
                 f"{phase_val('lat', name, 'lat')} → {phase_val('iter4_final', name, 'lat')} → {phase_val('iter4_best', name, 'lat')}",
                 f"{eval_row(name, 'baseline_iter1', 'fail')} → {eval_row(name, 'iter4_final', 'fail')}"])
add_table(s, rows, X0, 3.2, CW, 1.5, col_w=[1.1, 2.2, 3.3, 2.3], size=8.5)
card(s, X0, 4.85, CW, 2.0, "무엇을 알게 됐나",
     ["멈춘 자세 주행은 완전히 유지됐습니다. 벌점 항을 뺀 덕에 점수 하락이 없었고 오히려 조금 올랐습니다.",
      "새 규칙으로 잰 실패는 diag_bl이 0.161에서 0.122로 4분의 1 줄었고, forward는 조금 줄었으며, diag_fr는 그대로였습니다. 목표에는 셋 다 못 미쳤습니다.",
      "남은 실패가 어디 있는지는 분명해졌습니다. diag_bl은 선형 출발 다섯 개에서 실패가 0이 됐고, 남은 것은 역재생 출발과 회전 출발입니다. forward도 남은 것은 거의 회전 출발입니다."], size=9)

# P3-10 네 번의 파일럿 종합
s = content_slide("이어 학습 ⑩ 네 번의 파일럿 종합")
rows = [["파일럿", "바꾼 것", "diag_fr", "diag_bl", "forward", "주행", "한 줄 판정"],
        ["기준 (원본)", "지금 규칙으로 평가", eval_row("diag_fr", "baseline_iter1", "fail"), eval_row("diag_bl", "baseline_iter1", "fail"), eval_row("forward", "baseline_iter1", "fail"), "기준", "출발선입니다."],
        ["첫 번째", "인계 시작 절반 섞기", eval_row("diag_fr", "iter1_final", "fail"), eval_row("diag_bl", "iter1_final", "fail"), eval_row("forward", "iter1_final", "fail"), "유지", "주행은 지켰지만 실패는 그대로였습니다."],
        ["두 번째", "벌점 200, 학습률 낮춤", eval_row("diag_fr", "iter2_final", "fail"), eval_row("diag_bl", "iter2_final", "fail"), eval_row("forward", "iter2_final", "fail"), "유지", "벌점을 올려도 같았습니다."],
        ["세 번째", "기울기 벌점 두 항, 원본 시작", eval_row("diag_fr", "iter3_final", "fail"), eval_row("diag_bl", "iter3_final", "fail"), eval_row("forward", "iter3_final", "fail"), "2~4% 하락", "벌점을 피하는 행동을 못 찾았습니다."],
        ["규칙만 (학습 없음)", "시작 위상 가로 먼저", phase_val("lat", "diag_fr", "lat"), phase_val("lat", "diag_bl", "lat"), phase_val("lat", "forward", "lat"), "그대로", "학습 없이 가장 크게 줄었습니다."],
        ["네 번째", "규칙 + 원본 시작 학습", phase_val("iter4_final", "diag_fr", "lat"), phase_val("iter4_final", "diag_bl", "lat"), phase_val("iter4_final", "forward", "lat"), "유지", "diag_bl과 forward만 조금 더 줄었습니다."]]
add_table(s, rows, X0, 1.3, CW, 2.75, col_w=[1.35, 2.05, 0.85, 0.85, 0.85, 0.95, 2.0], size=8.5)
note(s, X0, 4.1, CW, 0.45, "위 네 줄은 지금 규칙(부호 정렬)으로 잰 값이고, 아래 두 줄은 새 규칙(가로 먼저)으로 잰 값입니다. 같은 은행 상태 스무 개씩, 출발 아홉 개입니다.", size=8.5)
card(s, X0, 4.6, CW, 2.25, "얻은 것 세 가지",
     ["학습을 네 번 바꿔서 얻은 것보다, 시작 위상 규칙 하나를 바꿔서 얻은 것이 훨씬 큽니다. 규칙은 어떤 모델에도 그대로 붙습니다.",
      "지금까지의 실패 원인은 정책의 실력이 아니라, 정책이 구할 수 없는 출발 상태를 우리가 만들어 주고 있었던 것입니다.",
      "그래서 전문가 이어 학습은 여기서 멈춥니다. 남은 실패는 회전 출발과 diag_fr의 forward, left 출발에 몰려 있어서, 그쪽은 따로 다룹니다."], size=9)

# P3-11 경로 추종 재실험 v2 ① 결과 표 (2026-09-13, 결함 수정 + 반복 조건)
def v2_runs(suffix, kind, unified=False):
    import re as _re
    pat = f"2026*_{kind}_unified_v2_{suffix}_r*" if unified else f"2026*_{kind}_v2_{suffix}_r*"
    out = {}
    for h in sorted(glob.glob(str(ROOT / "runs/path_follow_demo" / pat))):
        r = parse_demo(Path(h))
        if r:
            m = _re.search(r"시드 (\d+)", (Path(h) / "result.txt").read_text(encoding="utf-8"))
            out[int(m.group(1)) if m else len(out)] = r
    return out


COMBOS = [("A_sign", "원본 전문가, 지금 규칙", False), ("B_lat3", "원본 전문가, 새 규칙을 위험한 세 쌍에만", False),
          ("C_latall", "원본 전문가, 새 규칙을 모든 전환에", False), ("D_iter4_latall", "네 번째 파일럿 전문가, 새 규칙을 모든 전환에", False),
          ("U_sign", "합친 정책, 지금 규칙", True), ("U_lat", "합친 정책, 새 규칙", True)]


def v2_paired(a, b, kind):
    from math import comb as _comb
    ua = next(u for s_, _, u in COMBOS if s_ == a)
    ub = next(u for s_, _, u in COMBOS if s_ == b)
    ra, rb = v2_runs(a, kind, ua), v2_runs(b, kind, ub)
    seeds = sorted(set(ra) & set(rb))
    if not seeds:
        return None
    d = np.array([ra[s_]["err"] - rb[s_]["err"] for s_ in seeds])
    w, l = int((d < -1e-9).sum()), int((d > 1e-9).sum())
    t = len(seeds) - w - l
    n, k = w + l, min(w, l)
    p = min(1.0, 2 * sum(_comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return dict(w=w, t=t, l=l, d=float(d.mean()), p=p)


s = content_slide("경로 추종 재실험 ① 결과")
note(s, X0, 1.3, CW, 0.75, "어제 비교의 결함 세 곳을 고치고 다시 했습니다. 시드로 정한 난수로 시작 관절 각도에 0.03라디안 안팎의 잡음을 주고 경로를 8도 안팎으로 돌려서, 같은 시드면 모든 조합이 같은 조건을 받게 했습니다. 조합 여섯 개, 경로 세 개, 반복 열 번, 모두 180번입니다. 영상은 따로 세 번 찍었습니다.", size=9)
rows = [["조합", "네모", "별", "장애물"]]
for suf, label, uni in COMBOS:
    cells = []
    for kind in ("square", "star", "gauntlet"):
        rs = list(v2_runs(suf, kind, uni).values())
        if not rs:
            cells.append("-")
            continue
        errs = np.array([r["err"] for r in rs])
        done = sum(r["done"] for r in rs)
        cells.append(f"완주 {done}/{len(rs)}, 오차 {errs.mean():.2f}±{errs.std():.2f} m, {np.mean([r['sec'] for r in rs]):.0f}초")
    rows.append([label] + cells)
add_table(s, rows, X0, 2.1, CW, 2.2, col_w=[3.1, 1.95, 1.95, 1.9], size=8.5)
vy = 4.5
for i, (suf, cap_txt) in enumerate((("A_sign", "장애물, 원본 전문가, 지금 규칙 (시드 1)"), ("C_latall", "장애물, 원본 전문가, 새 규칙 전부 (시드 1)"), ("U_lat", "장애물, 합친 정책, 새 규칙 (시드 1)"))):
    f = find_demo("gauntlet", f"v2_{suf}_video", unified=(suf in ("U_sign", "U_lat")))
    if f and (f / "path_demo.mp4").exists():
        VIDEOS[f"demo_{suf}"] = f / "path_demo.mp4"
        add_video(s, f"demo_{suf}", X0 + 0.15 + i * 3.0, vy, 2.6, cap=cap_txt)
note(s, X0, 6.45, CW, 0.4, "오차는 매 스텝 경로까지의 거리를 평균한 값이고, 완주는 웨이포인트를 모두 지난 횟수입니다. 시간이 길어지면 전환도 오차도 같이 늘기 때문에 세 값은 한 현상의 세 얼굴입니다.", size=8.5)

# P3-12 경로 추종 재실험 v2 ② 짝지은 비교
s = content_slide("경로 추종 재실험 ② 짝지은 비교")
pairs = [("C_latall", "A_sign", "새 규칙 전부 vs 지금 규칙 (원본 전문가)"), ("B_lat3", "A_sign", "새 규칙 위험 세 쌍만 vs 지금 규칙"),
         ("D_iter4_latall", "C_latall", "네 번째 파일럿 vs 원본 (둘 다 새 규칙 전부)"), ("U_lat", "U_sign", "합친 정책: 새 규칙 vs 지금 규칙"),
         ("U_lat", "C_latall", "합친 정책 새 규칙 vs 전문가 새 규칙 전부"), ("U_lat", "A_sign", "합친 정책 새 규칙 vs 전문가 지금 규칙")]
rows = [["비교 (앞 조합이 이긴 횟수 / 비김 / 진 횟수, 오차 차이, p)", "네모", "별", "장애물"]]
for a, b, label in pairs:
    cells = []
    for kind in ("square", "star", "gauntlet"):
        r = v2_paired(a, b, kind)
        cells.append("-" if r is None else f"{r['w']}/{r['t']}/{r['l']}, {r['d']:+.2f} m, p={r['p']:.2f}")
    rows.append([label] + cells)
add_table(s, rows, X0, 1.3, CW, 2.3, col_w=[3.5, 1.8, 1.8, 1.8], size=8.5)
card(s, X0, 3.8, CW, 3.05, "판정 (검토 에이전트의 확인을 거친 문장)",
     ["합친 정책에 새 규칙을 쓴 조합이 오차와 시간 모두 가장 좋았습니다. 다른 다섯 조합과 30쌍씩 비교해 모두 이겼습니다. 이긴 횟수는 22에서 24이고 p는 0.016 이하입니다. 다만 경로와 시드별로 항상 1등은 아니어서 30칸 중 16칸입니다.",
      "규칙만 바꿔 얻은 것은 합친 정책 안에서 평균 0.08미터입니다. 전문가 대비 우위 0.19미터에는 합친 정책의 학습이 함께 들어 있습니다.",
      "전문가에 새 규칙을 모든 전환에 쓰면 장애물에서는 좋아지는 쪽이고 네모에서는 나빠지는 쪽이라, 세 경로를 합치면 이득이 없습니다. 위험한 세 쌍에만 쓰는 것은 그 쌍이 모두 같은 집안이라 차이가 나기 어렵습니다.",
      "네 번째 파일럿 전문가의 이득은 찾지 못했습니다. 열 번으로는 0.1미터 안쪽 차이를 잡을 수 없습니다.",
      "한계입니다. 여러 비교를 한꺼번에 했으므로 보정하면 남는 결과는 합친 정책의 네모 10대 0 하나입니다. 회전각 표본이 양수 쪽에 치우쳤고, 새 규칙은 가로 우선과 표 가운데 열 고르기 두 가지가 함께 바뀐 것이라 어느 쪽 효과인지 모릅니다. 명령 기록을 저장하지 않아 실제 전환 구성은 확인하지 못했습니다."], size=8.5)

# P3-13 커맨더 실험 v3 (갱신 주기 × 도착 판정)
V3 = json.load(open(ROOT / "results/path_follow_demo/v3_summary.json")) if (ROOT / "results/path_follow_demo/v3_summary.json").exists() else None
s = content_slide("경로 추종 재실험 ③ 갱신 주기")
note(s, X0, 1.3, CW, 0.6, "갱신 주기가 너무 길다는 지적을 검증했습니다. 합친 정책과 새 규칙으로 고정하고, 주기 25, 10, 5, 2, 1스텝과 도착 판정 두 가지(원, 수직면)를 조합해 경로 세 개, 시드 열 개로 270번 돌렸습니다. 기준은 지금 설정인 주기 25스텝과 원 판정입니다.", size=9)
if V3:
    rows = [["변형", "네모 (오차 / 최대 / 시간)", "별", "장애물", "기준 대비 30쌍"]]
    labels = {"P25_circ": "주기 25, 원 (지금)", "P25_plane": "주기 25, 수직면", "P10_circ": "주기 10, 원", "P10_plane": "주기 10, 수직면", "P5_circ": "주기 5, 원", "P5_plane": "주기 5, 수직면",
              "P2_circ": "주기 2 (0.1초), 원", "P2_plane": "주기 2 (0.1초), 수직면", "P1_plane": "주기 1 (매 스텝), 수직면"}
    for v, lab in labels.items():
        cells = []
        for kind in ("square", "star", "gauntlet"):
            d = V3["summary"].get(f"{v}/{kind}")
            cells.append("-" if not d else f"{d['err']:.2f} / {d['err_max']:.2f} m / {d['sec']:.0f}초")
        if v == "P25_circ":
            cells.append("기준")
        else:
            W = sum(V3["paired"][f"{v}/{k}"]["w"] for k in ("square", "star", "gauntlet"))
            T = sum(V3["paired"][f"{v}/{k}"]["t"] for k in ("square", "star", "gauntlet"))
            L = sum(V3["paired"][f"{v}/{k}"]["l"] for k in ("square", "star", "gauntlet"))
            cells.append(f"이김 {W} / 비김 {T} / 짐 {L}")
        rows.append([lab] + cells)
    add_table(s, rows, X0, 1.95, CW, 2.75, col_w=[2.0, 2.0, 1.8, 1.8, 1.3], size=8)
card(s, X0, 4.85, CW, 2.0, "판정 (검토 에이전트의 재계산을 거친 문장)",
     ["기준 설정의 큰 오차는 코너 오버슛이 아니라, 판정 순간 사이에 도착 원을 지나쳐 놓친 뒤 0.85미터 동결을 벗어나서야 되돌아오는 데서 났습니다. 기준의 최대 오차 30개 중 23개가 이 경우였습니다. 주기를 줄이면 이 놓침이 150개 중 24개에서 1~4개로, 수직면 판정을 켜면 구간 중간에 되돌아간 전환이 네모 18에서 2, 별 41에서 4, 장애물 36에서 1로 줄었습니다.",
      "주기 5나 10에 수직면 판정을 합치면 평균 오차가 0.29에서 0.32미터에서 0.16에서 0.21미터로, 최대 오차가 1.0에서 1.3미터에서 0.5에서 0.8미터로 줄었습니다. 주기를 0.1초나 매 스텝으로 더 줄여도 평균 오차와 시간은 같고, 구간 중간 전환만 30퍼센트 늡니다. 매 스텝 판단은 큰 실패가 가장 적었습니다(최대 오차 0.8미터 초과가 30번 중 1번).",
      "남은 최대 오차(중앙값 0.47미터)의 3분의 2는 구간을 따라가며 옆으로 쌓인 오차이고 3분의 1은 코너 직후 흔들림입니다. 옆 오차는 이웃한 두 명령을 번갈아 내는 동안 커져서 여덟 방향 양자화가 의심되지만, 몸통 방향을 기록하지 않아 보행 편향과 가르지 못했습니다. 수직면 판정은 웨이포인트를 옆으로 지나가도 도착으로 치므로 끝점 오차가 커질 수 있습니다."], size=8)

# ---------------------------------------------------------------------------
# 자율 캠페인 (2026-09-14 저녁): 다양한 경로 검증, 커맨더 최적화, Stage 4 비교
# 데이터: results/path_validation/*.json (validate_paths.py), results/unified_bench/*.json (bench_unified_ckpts.py)
# ---------------------------------------------------------------------------
VAL_DIR = ROOT / "results/path_validation"
PATH_KO = {"square": "네모", "star": "별", "gauntlet": "장애물", "zigzag": "지그재그", "scurve": "S자", "octagon": "팔각형",
           "serpentine": "굽이길", "uturn": "유턴", "random": "무작위"}
VAL_KINDS = list(PATH_KO)


def val_load(tag):
    p = VAL_DIR / f"{tag}.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def _sign_p(w, l):
    from math import comb as _comb
    n, k = w + l, min(w, l)
    return min(1.0, 2 * sum(_comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def val_paired(a, b, field="err", kinds=None, tol=1e-9):
    """a가 b보다 작은(좋은) 쌍 수 / 비김 / 큰 쌍 수, 평균 차이, 부호 검정 p. 경로·시드로 짝지음."""
    ra = {(r["kind"], r["seed"]): r for r in a["records"]}
    rb = {(r["kind"], r["seed"]): r for r in b["records"]}
    keys = sorted(set(ra) & set(rb))
    if kinds:
        keys = [k for k in keys if k[0] in kinds]
    d = np.array([ra[k][field] - rb[k][field] for k in keys]) if keys else np.zeros(0)
    w, l = int((d < -tol).sum()), int((d > tol).sum())
    return dict(w=w, t=len(d) - w - l, l=l, d=float(d.mean()) if len(d) else 0.0, p=_sign_p(w, l), n=len(d))


def val_kind_counts(a, b, field="err", tol=1e-3):
    """경로별 평균으로 a가 나아진 경로 수 / 비슷 / 나빠진 경로 수."""
    imp = same = worse = 0
    for k in VAL_KINDS:
        if k in a["summary"] and k in b["summary"]:
            dd = a["summary"][k][field] - b["summary"][k][field]
            imp += dd < -tol
            worse += dd > tol
            same += abs(dd) <= tol
    return imp, same, worse


def val_cell(a, b, kinds=None):
    r = val_paired(a, b, "err", kinds)
    if r["n"] == 0:
        return "-"
    return f"{r['w']}/{r['t']}/{r['l']}, {r['d']:+.3f} m, p={r['p']:.3f}" if r["p"] >= 0.001 else f"{r['w']}/{r['t']}/{r['l']}, {r['d']:+.3f} m, p<.001"


BASE_NEW = val_load("tune_f045_h34")       # S3 final + lat + 새 기본값(주기 5, 수직면, 동결 0.45)
BASE_OLD = val_load("s3_lat_base")         # 동결 0.85 (탐색 전 기본값)
# 판정 문장은 검토 에이전트의 확인을 거친 뒤 여기서 채운다 (결과가 없을 때는 자리표시 문장).
LA_JUDGE_TEXT = [
    "앞보기 점을 겨냥하면 오차가 줄고 시간이 늘어나는 맞바꿈이 생깁니다. 시험한 0.35미터부터 0.8미터 사이에서는 거리를 줄일수록 오차가 더 줄고 시간이 더 늘었습니다. 큰 실패도 6번에서 3, 2, 1, 0번으로 함께 줄었습니다. 그림의 극적인 개선은 앞보기 0.5미터 단독의 사례입니다.",
    "불감대 변형은 오차 17퍼센트, 최대 오차 18퍼센트가 줄고 큰 실패가 6번에서 2번이며 아홉 경로 모두 오차가 줄었습니다. 시간은 평균 3.8초, 10퍼센트 늘었습니다. 부호 검정으로는 확정하지 못했지만 비용이 없다는 뜻은 아닙니다. 장애물은 18초, 굽이길은 10초 늘었습니다. 앞보기 0.65미터와는 어느 지표로도 차이를 찾지 못했습니다.",
    "기본값은 바꾸지 않았습니다. 사전 규칙에는 시간 조건이 없어서 불감대 변형은 규칙을 채우지만, 시간이 느는 변형이라 사용자 결정으로 남겼습니다. 정확도를 가장 앞에 두면 앞보기 0.35미터가 제일 좋습니다. 중간을 고르면 0.65미터입니다.",
    "한계입니다. 앞보기라는 생각을 이 90번 주행의 큰 오차를 보고 만들었고 같은 경로와 시드로 채점했으므로 이득이 실제보다 좋게 나왔을 수 있습니다. 홀름 보정을 하면 0.35, 0.5, 불감대 변형만 남고 0.65는 탈락합니다. 정책 하나, 경로 크기 2미터, 갱신 주기 0.25초에서만 시험했습니다."]
S4_JUDGE_TEXT = [
    "넷째 단계의 이득도 손해도 확인되지 않았습니다. 새 규칙에서는 넷째 단계가 모든 집계에서 조금 앞서지만, 같은 시드끼리 짝지으면 어느 항목도 우연과 구분되지 않습니다. 점수는 22판 이김 18판 짐이고, 평균 점수 차이의 절반 이상은 시드 하나에서 나왔습니다.",
    "지금 규칙에서는 넘어진 판이 40판 중 10판으로 둘이 같고 완주율도 같습니다. 다만 전환 직후 낙상이 76번 중 8번 대 5번으로 조금 늘었고, 늘어난 몫은 모두 전진 오른쪽 대각과 후진 왼쪽 대각으로 바꾼 직후입니다. 새 규칙에 맞춰진 탓인지는 이 표본으로 판단할 수 없습니다.",
    "경로 추종에서는 차이를 확인하지 못했습니다. 90쌍에서 41 이김 47 짐이고, 시간과 전환 횟수도 같고, 완주는 둘 다 90번 모두입니다. 셋째 단계 쪽은 넷째 단계와 같은 스크립트로 다시 돌려 확인했습니다.",
    "셋째 단계에 새 규칙을 쓰면 벤치마크가 나빠진다는 출발 전제도 확인된 것이 아닙니다. 짝지으면 새 규칙만 넘어진 판 6, 지금 규칙만 넘어진 판 4입니다. 40판으로는 실패율 0.03 차이를 가릴 힘이 없고, 잡으려면 약 700판이 필요합니다.",
    "바꿀 근거가 없으므로 대표 모델은 셋째 단계 마지막 모델을 그대로 둡니다. 함께 쓸 규칙은 정해야 합니다. 경로 추종이 목적이면 새 규칙(시간 16퍼센트 단축), 벤치마크 재현이면 지금 규칙입니다. 넷째 단계 결과는 runs 폴더에 두고 정리는 승인 뒤에 합니다."]

# C-1 다양한 경로 검증 ① 아홉 경로와 기준 결과
s = content_slide("경로 검증 ① 아홉 경로")
note(s, X0, 1.3, CW, 0.6, "네모, 별, 장애물 셋에 여섯 경로를 더했습니다. 지그재그는 63도 꺾임, S자는 완만한 굽이, 팔각형은 45도 꺾임 여덟 번, 굽이길은 직각 되돌기, 유턴은 168도 되돌기, 무작위는 시드마다 다른 여섯 점입니다. 시작 관절 잡음 0.03라디안과 경로 회전 8도는 이전과 같습니다.", size=9)
fig_grid = ROOT / "docs/figures/path_validation/paths_grid.png"
if fig_grid.exists():
    fit_image(s, fig_grid, X0, 1.95, 4.3, 4.6)
if BASE_NEW:
    rows = [["경로", "완주", "오차 평균±편차", "최대", "시간", "전환"]]
    for k in VAL_KINDS:
        d = BASE_NEW["summary"].get(k)
        if d:
            rows.append([PATH_KO[k], f"{d['done']}/{d['n']}", f"{d['err']:.3f}±{d['err_sd']:.3f} m", f"{d['err_max']:.2f} m", f"{d['sec']:.0f}초", f"{d['sw']:.0f}회"])
    add_table(s, rows, X0 + 4.5, 1.95, CW - 4.5, 3.4, col_w=[0.85, 0.6, 1.35, 0.7, 0.55, 0.55], size=8)
    note(s, X0 + 4.5, 5.45, CW - 4.5, 1.2, "합친 정책(셋째 단계 마지막 모델)에 새 규칙과 커맨더 새 기본값(갱신 0.25초, 수직면 판정, 동결 0.45미터)을 쓴 결과입니다. 경로마다 시드 열 개, 모두 90번이고 모두 끝까지 갔습니다. 다만 도착 판정은 웨이포인트 옆을 지나가도 인정하는 방식이고, 90번 중 2번은 웨이포인트를 0.35미터 밖으로 지나쳤습니다. 오차는 매 스텝 경로까지 거리의 평균이고, 최대는 열 번의 최대 오차 평균입니다. 개별 주행의 평균 오차는 0.06미터에서 0.46미터까지 벌어집니다.", size=8)

# C-2 다양한 경로 검증 ② 정책·규칙 비교 (같은 시드끼리 짝지음)
S3_SIGN = val_load("s3_sign_f045")
EXP_LAT = val_load("experts_latall_f045")
s = content_slide("경로 검증 ② 정책과 규칙")
note(s, X0, 1.3, CW, 0.5, "같은 커맨더 기본값에서 정책과 규칙만 바꿔 같은 시드끼리 90쌍을 짝지었습니다. 칸은 앞 조합이 이긴 횟수 / 비김 / 진 횟수, 평균 오차 차이, 부호 검정 p입니다.", size=9)
rows = [["비교 (앞 조합 기준)", "90쌍 전체", "네모·별·장애물 30쌍", "새 경로 여섯 60쌍", "경로별 +/=/−", "완주"]]
cmp_list = [("합친 정책 새 규칙 vs 합친 정책 지금 규칙", BASE_NEW, S3_SIGN),
            ("합친 정책 새 규칙 vs 원본 전문가 새 규칙 전부", BASE_NEW, EXP_LAT)]
for lab, a, b in cmp_list:
    if a and b:
        i, sm, w = val_kind_counts(a, b)
        rows.append([lab, val_cell(a, b), val_cell(a, b, ("square", "star", "gauntlet")), val_cell(a, b, ("zigzag", "scurve", "octagon", "serpentine", "uturn", "random")),
                     f"{i}/{sm}/{w}", f"{sum(r['done'] for r in a['records'])}/{len(a['records'])} 대 {sum(r['done'] for r in b['records'])}/{len(b['records'])}"])
    else:
        rows.append([lab, "-", "-", "-", "-", "-"])
add_table(s, rows, X0, 1.85, CW, 1.25, col_w=[2.6, 1.55, 1.55, 1.55, 0.85, 0.8], size=8)
if S3_SIGN and EXP_LAT and BASE_NEW:
    rows = [["경로", "합친 정책 새 규칙", "합친 정책 지금 규칙", "원본 전문가 새 규칙 전부"]]
    for k in VAL_KINDS:
        cells = [PATH_KO[k]]
        for dd in (BASE_NEW, S3_SIGN, EXP_LAT):
            d = dd["summary"].get(k)
            cells.append("-" if not d else f"{d['done']}/{d['n']} 완주, {d['err']:.3f} m, {d['sec']:.0f}초, 전환 {d['sw']:.0f}회")
        rows.append(cells)
    add_table(s, rows, X0, 3.2, CW, 2.0, col_w=[1.1, 2.6, 2.6, 2.6], size=7)
RULE_JUDGE_TEXT = [
    "새 규칙은 합친 정책의 오차를 줄이지 않았습니다. 90쌍 중 44 이김, 1 비김, 45 짐이고 최대 오차도 40 대 45입니다. 대신 주행 시간이 16퍼센트 짧습니다. 전환 수도 19퍼센트 적지만 대부분은 주행이 짧아져 판단 기회가 줄어든 결과입니다. 새 규칙에서 로봇은 주행 내내 8퍼센트 빠르게 움직이고 덜 헤맵니다. 왜 그런지는 아직 모릅니다.",
    "어제 옛 커맨더에서 경로 세 개로 얻은 0.08미터 차이는 새 조건에서 재현되지 않았습니다. 그 결과는 처음부터 약했고, 조건이 한꺼번에 여럿 바뀌어 어느 변화 때문인지는 가릴 수 없습니다.",
    "합친 정책은 원본 전문가 열 개보다 오차가 작습니다. 56 이김, 34 짐이고 보통 주행에서는 0.02미터쯤, 평균으로는 0.07미터 줄었습니다. 평균이 큰 것은 전문가 쪽의 큰 실패 때문입니다. 최대 오차 0.8미터 초과가 6번 대 28번입니다. 유턴 한 경로는 오히려 18퍼센트 나빠졌습니다. 오차 차이의 p 0.026은 여러 조합을 함께 비교한 보정을 넘지 못합니다. 완주는 둘 다 90번 모두입니다."]
card(s, X0, 5.3, CW, 1.55, "판정 (검토 에이전트의 확인을 거친 문장)", RULE_JUDGE_TEXT, size=7.5)

# C-3 커맨더 최적화 ① 동결 반지름·히스테리시스
s = content_slide("커맨더 최적화 ① 동결 반지름")
note(s, X0, 1.3, CW, 0.6, "합친 정책과 새 규칙, 갱신 0.25초, 수직면 판정으로 고정하고 근접 동결 반지름과 히스테리시스 각도를 바꿔 아홉 경로, 시드 열 개로 90쌍씩 기준(동결 0.85미터, 히스테리시스 34도)과 짝지었습니다.", size=9)
variants = [("tune_f060_h34", "동결 0.60"), ("tune_f045_h34", "동결 0.45 (채택)"), ("tune_f035_h34", "동결 0.35"), ("tune_f085_h25", "히스테리시스 25도"),
            ("tune_f085_h45", "히스테리시스 45도"), ("tune_f060_h25", "동결 0.60 + 25도"), ("tune_f045_h30", "동결 0.45 + 30도")]
rows = [["변형", "평균 오차 (이김/비김/짐, 차이, p)", "최대 오차", "시간", "경로별 나아짐/비슷/나빠짐", "완주"]]
if BASE_OLD:
    for tag, lab in variants:
        v = val_load(tag)
        if not v:
            continue
        rm = val_paired(v, BASE_OLD, "err_max")
        rt = val_paired(v, BASE_OLD, "sec")
        i, sm, w = val_kind_counts(v, BASE_OLD)
        rows.append([lab, val_cell(v, BASE_OLD), f"{rm['w']}/{rm['t']}/{rm['l']}", f"{rt['w']}/{rt['t']}/{rt['l']}", f"{i}/{sm}/{w}", f"{sum(r['done'] for r in v['records'])}/{len(v['records'])}"])
add_table(s, rows, X0, 1.95, CW, 2.7, col_w=[1.7, 2.6, 1.0, 0.9, 1.7, 1.0], size=8)
card(s, X0, 4.8, CW, 2.05, "판정 (검토 에이전트의 확인을 거친 문장)",
     ["동결 반지름을 0.85에서 0.45미터로 줄이면 평균 오차가 90쌍 중 50쌍에서 줄고 20쌍은 같고 20쌍은 늘었습니다. 평균 0.024미터 개선이고 p는 0.001보다 작습니다. 아홉 경로 중 일곱이 나아지고 나빠진 경로는 없으며 시간은 달라지지 않았습니다. 미리 정한 채택 기준을 채워 기본값으로 삼았습니다.",
      "0.35는 0.45와 차이가 없었습니다. 히스테리시스를 25도나 30도로 줄이면 전환이 늘어 시간이 나빠지고, 45도로 늘리면 오차가 나빠집니다.",
      "이 표는 정책 하나(합친 정책)와 경로 크기 2미터에서 얻은 것입니다. 다른 정책이나 더 큰 경로에서는 다시 확인해야 합니다."], size=8.5)

# C-4 커맨더 최적화 ② 앞보기 점
s = content_slide("커맨더 최적화 ② 앞보기 점")
note(s, X0, 1.3, CW, 0.7, "남은 큰 오차가 어디서 나는지 90번의 궤적을 다시 봤습니다. 최대 오차가 0.6미터를 넘은 22번 중 20번이 마지막 코너를 지나고 3초 넘게 흐른 뒤, 구간 중간에서 났습니다. 웨이포인트를 겨냥하면 34도 히스테리시스가 남은 거리에 비례한 옆 오차를 허용하므로, 선분 위 가까운 점을 겨냥하는 앞보기를 시험했습니다. 다만 실제 옆 오차는 이 허용치보다 두세 배 크고, 로봇이 명령한 방향에서 34도 넘게 벗어나 움직인 시간이 전체의 15퍼센트입니다. 남은 오차는 겨냥 방식과 보행의 방향 오차가 함께 만든 것입니다.", size=8.5)
LA = [("la035", "앞보기 0.35 m"), ("la050", "앞보기 0.5 m"), ("la065", "앞보기 0.65 m"), ("la080", "앞보기 0.8 m"), ("la050_db025", "앞보기 0.5 m + 불감대 0.25 m")]
la_dirs = sorted(glob.glob(str(ROOT / "runs/path_follow_demo/2026*_zigzag_unified_la_smoke")))
if len(la_dirs) >= 3:
    fit_image(s, Path(la_dirs[0]) / "trajectory.png", X0, 2.05, 4.35, 1.55)
    fit_image(s, Path(la_dirs[2]) / "trajectory.png", X0 + 4.55, 2.05, 4.35, 1.55)
    caption(s, X0, 3.62, CW, "지그재그 시드 7. 왼쪽은 웨이포인트 겨냥(최대 오차 1.48미터, 56초), 오른쪽은 앞보기 0.5미터(최대 0.27미터, 29초)입니다. 불감대는 옆 오차가 문턱을 넘을 때만 앞보기 점을 겨냥하는 변형입니다. 큰 실패는 최대 오차 0.8미터 초과 횟수(변형 대 기준)입니다.")
rows = [["변형 (기준: 웨이포인트 겨냥, 90쌍)", "평균 오차 (이김/비김/짐, 차이, p)", "최대 오차", "시간", "전환 수", "경로별 +/=/−", "큰 실패", "완주"]]
if BASE_NEW:
    big_b = sum(r["err_max"] > 0.8 for r in BASE_NEW["records"])
    for tag, lab in LA:
        v = val_load(tag)
        if not v:
            continue
        rm = val_paired(v, BASE_NEW, "err_max")
        rt = val_paired(v, BASE_NEW, "sec")
        rs = val_paired(v, BASE_NEW, "sw")
        i, sm, w = val_kind_counts(v, BASE_NEW)
        rows.append([lab, val_cell(v, BASE_NEW), f"{rm['w']}/{rm['t']}/{rm['l']}", f"{rt['w']}/{rt['t']}/{rt['l']}", f"{rs['w']}/{rs['t']}/{rs['l']}", f"{i}/{sm}/{w}",
                     f"{sum(r['err_max'] > 0.8 for r in v['records'])} 대 {big_b}", f"{sum(r['done'] for r in v['records'])}/{len(v['records'])}"])
add_table(s, rows, X0, 3.98, CW, 1.3, col_w=[2.1, 2.05, 0.85, 0.75, 0.75, 0.85, 1.0, 0.55], size=7.5)
card(s, X0, 5.33, CW, 1.52, "판정 (검토 에이전트의 확인을 거친 문장)", LA_JUDGE_TEXT, size=7.5)

# C-5 Stage 4 이어 학습 (lat 규칙으로 학습) — 결과 파일이 있을 때만
BENCH4 = {}
for rule in ("sign", "lat"):
    p = ROOT / "results/unified_bench" / f"s3s4_{rule}.json"
    if p.exists():
        BENCH4[rule] = json.load(open(p, encoding="utf-8"))["results"]
S4_VAL = val_load("s4_lat")
if BENCH4 or S4_VAL:
    s = content_slide("합친 정책 넷째 단계")
    note(s, X0, 1.3, CW, 0.6, "셋째 단계 마지막 모델에서 이어서, 전환 시작 위상 규칙만 새 규칙(가로 먼저)으로 바꾸고 4천만 스텝을 더 학습했습니다. 학습률 2e-4, 에포크 3, KL 한도 0.04은 셋째 단계와 같습니다. 셋째 단계는 지금 규칙으로 학습했고 새 규칙으로 잰 벤치마크가 조금 나빠 보였기 때문에, 그 틈이 메워지는지를 판정 항목으로 삼았습니다. 검토 결과 그 틈 자체가 40판 잡음 안이었습니다. 학습 중 잰 전환 뒤 실패율(확률 정책)은 0.061에서 0.049로 내려갔고, 그 하락은 학습의 마지막 30퍼센트에서만 났습니다.", size=8.5)
    if BENCH4:
        rows = [["고정 시드 40판", "규칙", "점수 평균 ± 편차", "완주 비율", "전환 뒤 100스텝 안 낙상", "대각 두 방향(diag_fr, diag_bl)으로 바꾼 직후 낙상"]]
        for rule in ("sign", "lat"):
            for n, r in BENCH4.get(rule, {}).items():
                rows.append([n, "지금 규칙" if rule == "sign" else "새 규칙", f"{r['ret']:,.0f} ± {r['ret_sd']:,.0f}", f"{r['survive']:.2f}", f"{r['fail100']:.3f} ({r['n_sw']}회 중)", f"{r['fail203']:.2f} ({r['n203']}회 중)"])
        add_table(s, rows, X0, 2.0, CW, 1.8, col_w=[1.2, 0.9, 1.6, 0.9, 1.8, 2.5], size=8)
    if S4_VAL and BASE_NEW:
        rows = [["경로 추종 (같은 시드 짝지음)", "90쌍 전체", "네모·별·장애물", "새 경로 여섯", "최대 오차", "시간", "경로별", "완주"]]
        r_all = val_cell(S4_VAL, BASE_NEW)
        rm = val_paired(S4_VAL, BASE_NEW, "err_max")
        rt = val_paired(S4_VAL, BASE_NEW, "sec")
        i, sm, w = val_kind_counts(S4_VAL, BASE_NEW)
        rows.append(["넷째 단계 vs 셋째 단계 (둘 다 새 규칙, 새 기본값)", r_all, val_cell(S4_VAL, BASE_NEW, ("square", "star", "gauntlet")),
                     val_cell(S4_VAL, BASE_NEW, ("zigzag", "scurve", "octagon", "serpentine", "uturn", "random")), f"{rm['w']}/{rm['t']}/{rm['l']}", f"{rt['w']}/{rt['t']}/{rt['l']}", f"{i}/{sm}/{w}",
                     f"{sum(r['done'] for r in S4_VAL['records'])}/{len(S4_VAL['records'])} 대 {sum(r['done'] for r in BASE_NEW['records'])}/{len(BASE_NEW['records'])}"])
        add_table(s, rows, X0, 3.9, CW, 0.85, col_w=[2.3, 1.3, 1.2, 1.2, 0.7, 0.6, 0.7, 0.9], size=7.5)
    card(s, X0, 4.85, CW, 2.0, "판정 (검토 에이전트의 확인을 거친 문장)", S4_JUDGE_TEXT, size=7.5)

# 다음 단계
s = content_slide("다음 단계")
nxt = [("경로 추종 커맨더", "기본값은 갱신 0.25초, 수직면 판정, 동결 반지름 0.45미터입니다. 선분 위 앞보기 점은 오차와 시간의 맞바꿈이라 사용자 결정을 기다립니다. 정확도를 앞에 두면 0.35미터, 중간이면 0.65미터입니다. 남겨 둔 경로와 시드로 다시 채점하고, 경로 크기 1미터와 3미터에서도 확인해야 합니다."),
       ("대표 모델과 함께 쓸 규칙", "대표 모델은 셋째 단계 마지막 모델입니다. 넷째 단계는 이득도 손해도 확인되지 않아 runs 폴더에 둡니다. 함께 쓸 전환 규칙은 정해야 합니다. 경로 추종이 목적이면 새 규칙이 시간을 16퍼센트 줄이고, 벤치마크 재현이 목적이면 지금 규칙입니다."),
       ("새 규칙이 왜 빠른지 찾기", "새 규칙에서 로봇은 주행 내내 8퍼센트 빠르고 덜 헤맵니다. 원인은 모릅니다. 전환 시점의 위상과 몸통 자세를 기록해 비교하고, 규칙의 두 변화(가로 먼저, 가운데 열 고르기)를 따로 켜 봅니다. 벤치마크는 전환 단위 기록을 남기고 판 수를 늘려야 합니다."),
       ("회전에서 선형으로 바뀌는 전환", "남은 실패는 대부분 회전 출발입니다. 회전 중에는 몸이 돌고 있으니, 짧게 힘을 빼서 회전을 죽인 뒤 바꾸는 규칙을 평가 스크립트에서 먼저 시험합니다. 전문가 이어 학습은 네 번의 파일럿에서 이득이 작아 멈췄습니다."),
       ("실제 로봇을 향한 준비", "마찰을 무작위로 바꾸고, 센서 지연과 노이즈에 강하게 만들고, 굴곡진 바닥에서도 시험합니다. 궤적 기록에 몸통 방향을 넣어 남은 오차 중 커맨더 몫과 보행 몫을 나눕니다.")]
for i, (t, d) in enumerate(nxt):
    y = 1.3 + i * 1.08
    rect(s, X0, y, CW, 0.96)
    badge(s, X0 + 0.12, y + 0.31, 0.34, str(i + 1), BLUE, size=9)
    add_text(s, X0 + 0.6, y + 0.08, 2.6, 0.8, [{"text": t, "size": 10, "bold": True, "color": NAVY}], margin=0, anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, X0 + 3.25, y + 0.08, CW - 3.4, 0.8, [{"text": d, "size": 9, "color": TEXT}], margin=0, anchor=MSO_ANCHOR.MIDDLE)

# 참고문헌·산출물
s = content_slide("참고문헌과 결과물 위치")
rows = [["주제", "대표 논문", "우리 연구와 어떻게 이어지나"],
        ["정책 합치기", "Rusu 외, Policy Distillation (ICLR 2016) / Parisotto 외, Actor-Mimic (ICLR 2016)", "전문가 열 개를 정책 하나로 옮기는 방법입니다."],
        ["따라 하기 학습의 보정", "Ross 외, DAgger (AISTATS 2011) / Laskey 외, DART (CoRL 2017)", "노이즈를 섞고, 학생이 간 상태에 라벨을 붙이는 방법입니다."],
        ["따라 하기에서 강화학습으로", "Rajeswaran 외, DAPG (RSS 2018) / Uchendu 외, JSRL (ICML 2023)", "가치 함수를 미리 맞추고 조심스럽게 시작하는 이유입니다."],
        ["여러 보행을 다루는 다리 로봇", "Yang 외, MELA (Science Robotics 2020) / Margolis & Agrawal (CoRL 2022)", "보행 조건부 정책과 전환 커리큘럼의 근거입니다."],
        ["뱀 로봇과 진동 위상", "Hirose (1993) / Tesch 외 (2009) / Ijspeert (2008) / Song 외, ICAE 2025", "serpenoid gait와 위상 정렬의 배경입니다."],
        ["잊지 않는 학습", "Kirkpatrick 외, EWC (PNAS 2017) / Schwarz 외, Progress & Compress (ICML 2018)", "새 작업을 더할 때 옛 실력을 지키는 방법입니다."]]
add_table(s, rows, X0, 1.3, CW, 3.2, col_w=[1.6, 4.6, 2.7], size=8)
note(s, X0, 4.55, CW, 0.45, "문헌 목록은 docs/references_transition_learning.md에 있습니다. 48편 모두 서지 정보를 확인했습니다.", size=8.5)
card(s, X0, 5.05, CW, 1.75, "결과물은 여기에 있습니다",
     ["합친 정책 계보는 policies/unified 폴더에 있습니다. 대표 모델은 03_transition_stage3의 final_model.zip과 vecnormalize.pkl입니다.",
      "전문가 이어 학습 결과는 runs 폴더의 ppo_plane_*_moving_init_iter1부터 iter4에 있고, 정리하면 policies/path_tracking 아래 04_부터 07_로 옮깁니다.",
      "시작 위상 규칙 함수는 horcrux_env/envs/phase_align.py에 있고, 수학 근거는 docs/Horcrux_phase_selection_math_2026-09.pptx에 있습니다.",
      "넷째 단계 run은 runs/ppo_unified_transition_stage4에 있고, 정리하면 policies/unified/04_transition_stage4로 옮깁니다. 경로 검증 결과는 results/path_validation(git 추적), 검증 드라이버는 training/validate_paths.py, 체크포인트 벤치마크는 training/bench_unified_ckpts.py입니다.",
      "시연 영상은 runs/path_follow_demo와 runs/policy_showcase에 있습니다. 변경 이력은 CLAUDE_CHANGES.md입니다."], size=8)

# 부록 설정
s = content_slide("부록 ① 학습 설정 요약")
rows = [["구분", "항목", "값"],
        ["환경", "보상 계수", "앞으로 가는 보상 60, 효율 3, 건강 2, 자세 흐트러짐 벌점 10"],
        ["환경", "실패 판정", "몸이 롤 방향으로 기울어진 상태가 걷기는 30스텝, 회전은 60스텝 이어지면 실패입니다."],
        ["환경 (합친 정책)", "회전 기준점", "실패 판정 대신 가까이 있으면 점수를 줍니다. 최대 10점입니다."],
        ["환경 (합친 정책)", "전환 커리큘럼", "한 에피소드에 1번에서 4번, 최소 100스텝 간격, 위상 정렬, 시작 위상 무작위, 1000스텝 절단"],
        ["환경 (전문가 이어 학습)", "인계 시작", "인계 시작 50퍼센트, 위상 정렬 80퍼센트, 인계 에피소드 1000스텝, 두 번째 파일럿부터 낙상 벌점 200"],
        ["환경 (전문가 이어 학습)", "세 번째와 네 번째 파일럿", "세 번째는 기울기 벌점 20과 기운 채로 세게 밀기 벌점 20을 인계 에피소드에만 더했습니다. 네 번째는 그 항을 빼고 시작 위상 규칙을 가로 먼저로 바꿨습니다."],
        ["PPO", "합친 정책 세 단계", "학습률 1e-4, 1e-4, 2e-4. 에포크 2, 3, 3. KL 한도 0.04. 할인율 0.99. 각 4천만 스텝"],
        ["PPO", "전문가 파일럿", "학습률 1e-4 다음 5e-5. 에포크 2. 할인율 0.95. 각 2천8백만 스텝"],
        ["속도", "학습 속도", "혼자 돌리면 초당 약 2천2백 스텝, 셋을 같이 돌리면 각각 약 1천2백 스텝입니다."]]
add_table(s, rows, X0, 1.3, CW, 4.3, col_w=[1.6, 1.5, 5.8], size=8.5)

# 부록 벤치마크
if BENCH:
    s = content_slide("부록 ② 체크포인트 비교")
    rows = [["체크포인트", "점수 평균 ± 편차", "에피소드 길이", "완주 비율", "전환 뒤 실패 비율", "diag_fr, diag_bl로 갈 때 실패"]]
    for n, r in BENCH.items():
        rows.append([n, f"{r['ret']:,.0f} ± {r['ret_sd']:,.0f}", f"{r['eplen']:.0f}", f"{r['survive']:.2f}", f"{r['fail100']:.3f}", f"{r['fail203']:.2f}"])
    add_table(s, rows, X0, 1.3, CW, 2.6, col_w=[1.6, 1.9, 1.1, 1.0, 1.5, 1.8], size=9)
    card(s, X0, 4.1, CW, 2.4, "어떻게 읽나",
         ["같은 40판을 모든 체크포인트에 똑같이 돌렸습니다. 점수 차이는 편차보다 작아서 다 비슷합니다.",
          "전환 뒤 실패 비율은 단계를 거칠수록 줄었습니다. 첫 단계 끝이 0.164, 셋째 단계 끝이 0.066입니다.",
          "그래서 셋째 단계의 마지막 모델을 대표로 골랐습니다. 완주 비율이 가장 높은 둘째 단계 마지막 모델이 그다음입니다."], size=9)

prs.save(OUT)
print("saved", OUT, f"{OUT.stat().st_size/1e6:.1f} MB, slides", len(prs.slides))
