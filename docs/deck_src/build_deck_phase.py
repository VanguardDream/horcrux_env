"""전환 위상 선택의 수학적 근거 — 발표 덱 (사용자 템플릿, 쉬운 문장).

원칙: 한 문장에 한 가지 내용. 기호(→, ·, /) 대신 말로 푼다. 수식은 꼭 필요한 두 개만 쓰고 말로 다시 풀어 준다.
그림: docs/figures/phase_selection/*.png (make_phase_figures.py)
실험: runs/moving_state_bank/eval_phase_rules.json (규칙 4개 비교), eval_phase_rules_all.json (후보 위상 전부)
"""
import json
import sys
from pathlib import Path

import numpy as np
from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path("/home/bong/projects/horcrux_env")
FIG = ROOT / "docs/figures/phase_selection"
TEMPLATE = ROOT / "docs" / "PPT샘플.pptx"
OUT = ROOT / "docs" / "Horcrux_phase_selection_math_2026-09.pptx"
EXP_PATH = ROOT / "runs/moving_state_bank/eval_phase_rules.json"
EXP_ALL_PATH = ROOT / "runs/moving_state_bank/eval_phase_rules_all.json"
EXP = json.load(open(EXP_PATH)) if EXP_PATH.exists() else None
EXP_ALL = json.load(open(EXP_ALL_PATH)) if EXP_ALL_PATH.exists() else None
EXP_SM_PATH = ROOT / "runs/moving_state_bank/eval_phase_rules_signmom.json"
EXP_SM = json.load(open(EXP_SM_PATH)) if EXP_SM_PATH.exists() else None
INFO = json.load(open(FIG / "figure_info.json")) if (FIG / "figure_info.json").exists() else {}

NAVY, BLUE = "203864", "2E75B6"
CARD, CARD_LINE = "EEF3FA", "C7D3E3"
TEXT, SUB, CAP = "262626", "595959", "8A8A8A"
ORANGE, GREEN, RED = "E97132", "196B24", "C0392B"
WHITE = "FFFFFF"
FONT = "맑은 고딕"
DATE = "20260911"
TOPIC = "전환 위상 선택의 근거"
X0, X1, Y0, Y1 = 0.55, 9.45, 1.25, 6.85
CW = X1 - X0
RULE_KO = {"k0": "위상 0 재시작", "sign": "부호 정렬 (현행)", "near": "가장 가까운 점 (분산)", "kin": "운동 에너지", "signmom": "부호 정렬 + 운동량"}

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


def formula(slide, x, y, w, h, text, size=13, sub=None):
    """수식 상자: 남색 바탕에 흰 글씨, 아래에 말 풀이."""
    rect(slide, x, y, w, h, NAVY, None)
    add_text(slide, x + 0.15, y + 0.06, w - 0.3, h - 0.12, [{"text": text, "size": size, "bold": True, "color": WHITE, "align": PP_ALIGN.CENTER}],
             anchor=MSO_ANCHOR.MIDDLE, margin=0)


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
    # 접두어가 한글이라 글자당 폭이 넓다 — 오른쪽 아이콘(약 7.7인치)과 겹치지 않도록 길이별로 줄인다
    _style_run(r, 16 if len(full) <= 31 else (14 if len(full) <= 34 else (12.5 if len(full) <= 38 else 11.5)), True, NAVY)
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


def add_table(slide, rows, x, y, w, h, col_w=None, size=9, header=True, first_col_center=False):
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
            p.alignment = PP_ALIGN.LEFT if (j == 0 and not first_col_center) else PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(val)
            is_head = header and i == 0
            _style_run(r, size + (0.5 if is_head else 0), is_head, WHITE if is_head else TEXT)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(NAVY if is_head else (CARD if i % 2 == 0 else WHITE))
    return tbl


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


def fig(name):
    p = FIG / f"{name}.png"
    return p if p.exists() else None


# ------------------------------------------------------------------ 실험 수치 정리
def exp_summary():
    """규칙별 평균 실패 비율(목표 평균), 목표별 표, 거리-실패 관계, 오라클."""
    out = {}
    if EXP:
        rules, targets = EXP["rules"], EXP["targets"]
        out["rules"], out["targets"] = rules, targets
        out["per_target"] = {t: {r: EXP["summary"][t][r]["mean"] for r in rules} for t in targets}
        out["mean"] = {r: float(np.mean([EXP["summary"][t][r]["mean"] for t in targets])) for r in rules}
        rec = EXP["records"]
        J = np.array([r["j_var"] for r in rec], dtype=float)
        F = np.array([r["fail"] for r in rec], dtype=float)
        ok = np.isfinite(J)
        q = np.quantile(J[ok], [0.1, 0.2, 0.8])
        out["fail_lowest10"] = float(F[ok & (J <= q[0])].mean())
        out["fail_low"] = float(F[ok & (J <= q[1])].mean())
        out["fail_high"] = float(F[ok & (J >= q[2])].mean())
        out["n"] = int(ok.sum())
        out["n_states"] = len({(r["target"], r["source"], r["state"]) for r in rec})
        out["corr"] = float(np.corrcoef(J[ok], F[ok])[0, 1])
        if EXP_SM:
            r = "signmom"
            out["rules"] = rules + [r]
            for t in targets:
                out["per_target"][t][r] = EXP_SM["summary"][t][r]["mean"]
            out["mean"][r] = float(np.mean([EXP_SM["summary"][t][r]["mean"] for t in targets]))
    if EXP_ALL:
        rec = EXP_ALL["records"]
        by_state = {}
        for r in rec:
            by_state.setdefault((r["target"], r["source"], r["state"]), []).append(r)
        oracle, best_fixed = {}, {}
        for t in EXP_ALL["targets"]:
            keys = [k for k in by_state if k[0] == t]
            oracle[t] = float(np.mean([all(r["fail"] for r in by_state[k]) for k in keys]))          # 어떤 위상도 안 되는 비율
            # 위상마다(열 기준) 고정 규칙으로 썼을 때 가장 좋은 열의 실패율
            cols = sorted({r["col"] for k in keys for r in by_state[k]})
            best_fixed[t] = min(float(np.mean([r["fail"] for k in keys for r in by_state[k] if r["col"] == c])) for c in cols)
        out["oracle"] = oracle
        out["best_fixed"] = best_fixed
        out["oracle_mean"] = float(np.mean(list(oracle.values())))
        out["n_all"] = len(rec)
        J = np.array([r["j_var"] for r in rec], dtype=float)
        F = np.array([r["fail"] for r in rec], dtype=float)
        ok = np.isfinite(J)
        q = np.quantile(J[ok], [0.2, 0.8])
        out["all_fail_low"], out["all_fail_high"] = float(F[ok & (J <= q[0])].mean()), float(F[ok & (J >= q[1])].mean())
    return out


S = exp_summary()
picks = INFO.get("picks") or {}

# ============================================================================= 1. 표지
s = prs.slides.add_slide(L_COVER)
for ph in s.placeholders:
    idx = ph.placeholder_format.idx
    tf = ph.text_frame
    tf.clear()
    r = tf.paragraphs[0].add_run()
    if idx == 0:
        r.text = "전환 위상 선택의 수학적 근거"
        _style_run(r, 30, True, NAVY)
    elif idx == 1:
        r.text = "다른 gait로 움직이던 몸을 새 gait로 바꿀 때 어느 위상에서 시작해야 하는지를, 수학과 실험으로 따져 본 기록입니다. 2026년 9월 11일."
        _style_run(r, 12, False, SUB)
add_text(s, 3.31, 6.95, 3.38, 0.4, [{"text": "지능로봇시스템연구실", "size": 11, "color": SUB, "align": PP_ALIGN.CENTER}], margin=0)

# ============================================================================= 2. 한 장 요약
s = content_slide("한 장 요약")
card(s, X0, Y0, 4.6, 1.55, "원리는 한 줄입니다",
     ["전환은 지금 몸 상태를 목표 gait의 주기 궤도 위로 옮기는 일입니다.",
      "옮기는 거리가 짧을수록 목표 gait가 흔들림을 흡수하기 쉽습니다."], size=9.5)
card(s, X0, Y0 + 1.7, 4.6, 1.75, "지금 규칙은 이 원리의 거친 근사입니다",
     ["부호 정렬은 토크 방향이 뒤집히는 관절 수만 셉니다.",
      "실제 몸 상태, 각도의 크기, 속도는 보지 않습니다.",
      "집안을 건너는 전환에서는 어떤 위상을 골라도 부호를 다 맞출 수 없다는 것을 증명할 수 있습니다."], size=9.5)
card(s, X0, Y0 + 3.6, 4.6, 1.95, "제안과 확인",
     ["관절 각도와 각속도를 함께 보고 궤도에서 가장 가까운 점을 고르는 규칙을 제안했습니다.",
      "학습 없이 규칙만 바꿔서 실험했습니다. 가장 단순한 가중치는 부호 정렬을 넘지 못했습니다. 숫자는 뒤에 그대로 적었습니다.",
      "그런데 후보 위상을 전부 시도해 보니 거의 모든 상태에 살아남는 위상이 있었습니다. 다음 과제는 그 위상을 상태에서 찾는 규칙을 데이터로 배우는 것입니다."], size=9.5)
if fig("F8a_schematic_basin"):
    ox, oy, bw, bh = fit_image(s, fig("F8a_schematic_basin"), X0 + 4.8, Y0, 4.1, 4.6)
    caption(s, X0 + 4.8, oy + bh + 0.05, 4.1, "목표 gait의 궤도와 흡인 영역, 그리고 지금 상태에서 궤도 위의 점을 고르는 그림입니다.")

# ============================================================================= 3. 토크가 만들어지는 방식
s = content_slide("토크가 만들어지는 방식")
if fig("F1_serpenoid_sign"):
    ox, oy, bw, bh = fit_image(s, fig("F1_serpenoid_sign"), X0, Y0, 5.35, 3.6)
    caption(s, X0, oy + bh + 0.05, 5.35, "forward gait의 관절 1과 관절 2입니다. 주황 계단이 모션 벡터이고, 초록 점선은 각도 부호를 뒤집은 것입니다. 둘이 같습니다.")
card(s, X0 + 5.5, Y0, CW - 5.5, 3.95, "코드로 확인한 사실",
     ["기준 궤적은 Hirose의 서펜오이드입니다. 홀수 관절은 세로 파동이고, 짝수 관절은 가로 파동에 위상차 δ가 더해집니다.",
      "모션 벡터는 기준 각도를 시간으로 두 번 미분한 값의 부호입니다.",
      "사인파는 두 번 미분하면 자기 자신에 음수를 곱한 것이 됩니다. 그래서 모션 벡터는 기준 각도 부호의 반대입니다.",
      "관절은 토크 모터입니다. 토크는 정책이 정한 크기에 모션 벡터를 곱한 값입니다.",
      "즉 정책은 얼마나 세게만 정하고, 어느 쪽으로는 gait가 정합니다."], size=9)
card(s, X0, Y0 + 4.15, CW, 1.4, "그래서 전환은 토크 방향 패턴을 통째로 바꾸는 일입니다",
     ["gait를 바꾸는 순간, 열네 개 관절의 토크 방향이 새 gait의 패턴으로 한꺼번에 바뀝니다.",
      "정책은 크기만 조절할 수 있으니, 새 패턴이 지금 몸 상태와 맞지 않으면 정책이 할 수 있는 일은 힘을 줄이는 것뿐입니다."], size=9)
notes(s, "gait_v2.py 103행(서펜오이드), 135행(두 번 미분의 부호), horcrux_p.xml의 motor 액추에이터, plane_v3.py 408행(토크 = 행동 × 모션 벡터).")

# ============================================================================= 4. 지금 규칙이 하는 일
s = content_slide("지금 규칙이 하는 일")
formula(s, X0, Y0, CW, 0.8, "c* = argmax over c of  ⟨ m_S , M_T[:, c] ⟩  =  (같은 부호 수) − (다른 부호 수)", size=13)
note(s, X0, Y0 + 0.88, CW, 0.6,
     "m_S 는 지금 실행 중인 출발 gait의 모션 벡터입니다. M_T 는 목표 gait의 모션 행렬이고, 열 하나가 위상 하나입니다. 내적이 가장 큰 열, 즉 부호가 가장 많이 같은 위상을 고릅니다. 역재생 gait는 열 번호에 마이너스를 붙여 시작합니다.", size=9.5)
card(s, X0, Y0 + 1.6, 4.35, 3.9, "이 규칙이 보는 것",
     ["출발 gait의 기준 신호 부호 열네 개입니다.",
      "목표 gait의 후보 위상마다 기준 신호 부호 열네 개입니다.",
      "즉 토크 방향이 뒤집히는 관절의 개수를 가장 적게 만드는 위상을 고릅니다.",
      "같은 집안 안에서는 열세 개나 열네 개가 맞으므로 잘 작동합니다. 실제로 전환 실패가 크게 줄었습니다."], size=9.5)
card(s, X0 + 4.55, Y0 + 1.6, CW - 4.55, 3.9, "이 규칙이 못 보는 것 세 가지",
     ["첫째, 실제 몸 상태를 보지 않습니다. 기준 신호만 봅니다. 몸이 기준보다 늦거나 눌려 있어도 모릅니다.",
      "둘째, 크기를 보지 않고 부호만 봅니다. 각도가 0에 가까운 관절은 뒤집어도 싸고, 끝까지 꺾인 관절은 비쌉니다. 이 차이를 모릅니다.",
      "셋째, 속도를 전혀 보지 않습니다. 운동량이 있는 관절을 반대로 밀면 충격이 생기는데, 이 순간을 피할 수 없습니다.",
      "이 세 가지가 집안을 건너는 전환에서 그대로 드러납니다."], size=9.5, fill=NAVY, line=None, header_color=WHITE, text_color=WHITE, bullet_color="9DC3E6")

# ============================================================================= 5. 집안을 건너면 왜 안 되나 (증명)
s = content_slide("집안을 건너면 왜 안 되나")
if fig("F2_delta180"):
    ox, oy, bw, bh = fit_image(s, fig("F2_delta180"), X0, Y0, CW, 3.15)
    caption(s, X0, oy + bh + 0.03, CW, "왼쪽: left와 right의 기준 파동입니다. 오른쪽: forward의 한 패턴을 두 목표 gait의 모든 위상과 비교한 부호 일치입니다.")
card(s, X0, Y0 + 3.55, 4.35, 2.0, "증명은 세 문장입니다",
     ["여덟 방향 gait는 시간 파라미터가 모두 40이라서 세로 파동과 가로 파동이 같은 속도로 흐릅니다.",
      "δ에 180도를 더하면 가로 관절의 기준 신호는 모든 시각에 정확히 부호가 뒤집힙니다. 사인에 180도를 더하면 부호가 반대가 되기 때문입니다. 세로 관절은 그대로입니다.",
      "그래서 세로 관절 부호를 모두 맞추는 위상에서는 가로 관절 부호가 모두 어긋납니다. 어떤 위상을 골라도 둘 다 맞출 수 없습니다."], size=9)
card(s, X0 + 4.55, Y0 + 3.55, CW - 4.55, 2.0, "숫자로 보면",
     ["같은 집안 안에서는 열네 개 중 열두 개에서 열네 개까지 맞습니다.",
      "집안을 건너면 평균 다섯에서 여섯에 막힙니다. 이 값은 다음 장의 표에 있습니다.",
      "left와 right, diag_fl과 diag_fr는 정확히 180도 차이입니다. forward와 diag_fr는 203도 차이라서 거의 같은 상황입니다."], size=9)
notes(s, "증명: sin(x + δ + π) = −sin(x + δ). 시간 파라미터가 같으므로(40, 40) 위상 이동 k가 세로와 가로 파동에 똑같이 적용되어 두 파동을 따로 맞출 수 없다.")

# ============================================================================= 6. 집안이 눈에 보입니다 (표)
s = content_slide("집안이 눈에 보입니다")
if fig("F3_agreement_heatmap"):
    ox, oy, bw, bh = fit_image(s, fig("F3_agreement_heatmap"), X0, Y0, 5.0, 5.4)
card(s, X0 + 5.2, Y0, CW - 5.2, 2.55, "표 읽는 법",
     ["출발 gait의 패턴 하나하나에 대해, 목표 gait의 모든 위상 가운데 부호 일치가 가장 큰 값을 구하고 평균했습니다.",
      "열네 개면 전부 같고, 0이면 반은 같고 반은 다른 것입니다.",
      "짙은 정사각형 두 개가 집안 A와 집안 B입니다. 집안 안은 열둘 이상이고, 집안 사이는 다섯에서 여섯입니다."], size=9)
card(s, X0 + 5.2, Y0 + 2.7, CW - 5.2, 2.85, "실험 결과와 맞아떨어집니다",
     ["전환 실패가 집중된 쌍은 모두 집안을 건너는 쌍이었습니다. diag_fr로 갈 때와 diag_bl로 갈 때가 그렇습니다.",
      "같은 집안 안에서는 위상 정렬만으로 실패가 거의 0이 됐습니다.",
      "회전 gait 두 개는 집안 A에 가까운 쪽과 집안 B에 가까운 쪽으로 나뉩니다. ccw는 A쪽이고 cw는 B쪽입니다."], size=9, fill=NAVY, line=None, header_color=WHITE, text_color=WHITE, bullet_color="9DC3E6")

# ============================================================================= 7. 물리적인 뜻
s = content_slide("물리적인 뜻")
if fig("F4_robot_joints"):
    ox, oy, bw, bh = fit_image(s, fig("F4_robot_joints"), X0, Y0, 5.3, 3.0)
    caption(s, X0, oy + bh + 0.05, 5.3, "forward로 움직이던 순간의 몸입니다. 파란 번호가 세로 파동 관절이고, 주황 번호가 가로 파동 관절입니다.")
card(s, X0 + 5.5, Y0, CW - 5.5, 3.35, "두 파동의 역할이 다릅니다",
     ["세로 파동은 몸을 위아래로 굽혀서 어느 마디가 땅에 닿을지를 정합니다.",
      "가로 파동은 몸을 좌우로 굽혀서 닿은 마디가 어느 쪽으로 밀지를 정합니다.",
      "두 파동의 시간 차이 δ가 미는 방향, 곧 진행 방향을 정합니다."], size=9.5)
card(s, X0, Y0 + 3.6, CW, 1.95, "집안을 건너면 무슨 일이 생기나",
     ["집안을 건너면 같은 마디가 반대 방향으로 밀게 됩니다. 그런데 몸은 아직 옛 방향의 운동량을 가지고 있습니다.",
      "마찰력이 뒤집히고 운동량은 남아 있으니 몸통 축을 도는 모멘트가 생깁니다. 그래서 롤로 넘어집니다.",
      "따라서 가로 관절이 잠깐 멈추는 순간, 곧 속도가 0에 가까운 순간에 뒤집어야 충격이 작습니다. 이 순간을 고르려면 속도를 봐야 합니다."], size=9.5)

# ============================================================================= 8. 제안하는 규칙의 수식
s = content_slide("제안하는 규칙")
formula(s, X0, Y0, CW, 0.95, "J(k) = (θ − θ̄ₖ)ᵀ W (θ − θ̄ₖ) + (v − v̄ₖ)ᵀ V (v − v̄ₖ),      k* = argmin over k of J(k)", size=13)
note(s, X0, Y0 + 1.03, CW, 0.75,
     "θ 는 지금 관절 각도이고 v 는 지금 관절 각속도입니다. θ̄ₖ 와 v̄ₖ 는 목표 gait가 위상 k 에서 평소에 갖는 평균 각도와 평균 각속도입니다. "
     "W 와 V 는 무엇을 더 중요하게 볼지 정하는 가중치입니다. 각도 차이와 속도 차이를 더해서 가장 작은 위상을 고릅니다.", size=9.5)
card(s, X0, Y0 + 1.9, 4.35, 3.65, "궤도 표는 이렇게 만듭니다",
     ["목표 gait의 전문가를 정지 상태에서 굴린 상태 은행을 씁니다. 이미 있는 데이터입니다.",
      "은행의 각 상태에는 그때의 모션 벡터가 함께 적혀 있습니다. 같은 모션 벡터를 가진 상태끼리 묶어서 관절 각도와 각속도의 평균을 냅니다.",
      "gait 하나에 서로 다른 모션 벡터는 열한 개쯤입니다. 그래서 표는 gait마다 열한 줄, 스물여덟 개 숫자입니다.",
      "전환 순간에는 후보 위상 열한 개에 대해 J를 계산하고 가장 작은 것을 고릅니다. 곱셈 몇백 번이라 비용은 없습니다."], size=9)
card(s, X0 + 4.55, Y0 + 1.9, CW - 4.55, 3.65, "왜 측정값을 쓰나",
     ["기준 신호 대신 실제로 잰 각도와 속도를 씁니다. 몸이 기준보다 늦게 따라오는 것과 땅에 눌리는 효과가 표에 그대로 들어갑니다.",
      "부호 대신 크기를 씁니다. 0 근처의 관절은 싸게 뒤집고, 끝까지 꺾인 관절은 비싸게 칩니다.",
      "속도를 함께 봅니다. 운동량이 남은 관절을 반대로 미는 위상은 거리가 커져서 피하게 됩니다.",
      "역재생 gait의 별도 처리도 사라집니다. 표를 실제 열 번호로 찾기 때문에 규칙이 하나로 통일됩니다."], size=9)

# ============================================================================= 9. 궤도 위에서 고르기 (실제 데이터)
s = content_slide("실제 데이터로 본 궤도")
if fig("F5_phase_portrait"):
    ox, oy, bw, bh = fit_image(s, fig("F5_phase_portrait"), X0, Y0, CW, 2.95)
    caption(s, X0, oy + bh + 0.03, CW, "forward로 움직이던 몸 하나를 diag_fr로 바꿀 때입니다. 회색 점은 diag_fr 전문가의 상태 구름이고, 진한 선은 패턴별 평균을 위상 순서로 이은 주기 궤도입니다.")
pick_txt = ""
if picks:
    js, jn = picks.get("sign", {}).get("j_var"), picks.get("near", {}).get("j_var")
    if js is not None and jn is not None:
        pick_txt = f"이 예에서 부호 정렬이 고른 점의 거리는 {js:.0f}이고, 가장 가까운 점의 거리는 {jn:.0f}입니다."
card(s, X0, Y0 + 3.35, 4.35, 2.2, "그림 읽는 법",
     ["가로축은 관절 각도이고 세로축은 관절 각속도입니다. 한 관절의 움직임이 궤도 위를 도는 점으로 보입니다.",
      "빨간 점이 지금 몸 상태입니다. 주황 네모는 부호 정렬이 고른 궤도 위의 점이고, 초록 네모는 가장 가까운 점입니다.",
      "오른쪽 그림은 후보 위상마다 잰 거리 J입니다. 골짜기의 바닥이 제안 규칙의 선택입니다."], size=9)
card(s, X0 + 4.55, Y0 + 3.35, CW - 4.55, 2.2, "이 그림에서 알 수 있는 것",
     [pick_txt or "두 규칙이 고르는 점이 다를 수 있습니다.",
      "거리 J는 위상에 따라 몇 배씩 달라집니다. 즉 위상 선택은 실제로 큰 차이를 만드는 결정입니다.",
      "궤도가 상태 구름의 한가운데를 지나므로, 표의 평균값이 목표 gait의 평소 움직임을 잘 대표합니다."], size=9)

# ============================================================================= 10. 가중치와 지금 규칙의 자리
s = content_slide("가중치 세 가지")
rows = [["가중치를 정하는 법", "무엇을 재는가", "장점과 주의"],
        ["궤도의 흔들림 폭으로 나눕니다", "각 관절이 평소에 흔들리는 폭을 1로 놓고 잰 거리입니다. 통계에서 마할라노비스 거리라고 부릅니다.", "설명이 쉽고 단위 문제가 없습니다. 모든 관절을 같은 무게로 봅니다."],
        ["질량 행렬을 씁니다", "V에 로봇의 질량 행렬을 넣으면 속도 항이 운동 에너지가 됩니다. 목표 궤도로 옮기는 데 드는 에너지입니다.", "물리적으로 가장 깔끔합니다. MuJoCo에서 한 줄로 얻습니다. 위치 항은 따로 정해야 합니다."],
        ["데이터로 배웁니다", "진입 성공과 실패 기록으로 가중치를 학습합니다. 실패를 잘 가르는 방향이 저절로 커집니다.", "실제로 넘어지는 원인을 반영합니다. 데이터가 필요하고 해석은 조금 어려워집니다."]]
add_table(s, rows, X0, Y0, CW, 2.6, col_w=[2.2, 3.5, 3.2], size=9)
card(s, X0, Y0 + 2.8, CW, 2.75, "부호 정렬은 이 규칙의 0차 근사입니다",
     ["측정값 대신 기준 신호를 쓰고, 크기 대신 부호만 남기고, V를 0으로 두면 지금 규칙이 됩니다.",
      "그래서 논문에는 부호 정렬을 제안 규칙의 가장 거친 근사로 소개하고, 제안 규칙을 그 일반화로 소개할 수 있습니다.",
      "역재생 gait에 쓰던 열 번호 부호 반전 처리도 일반 규칙 안에 자연스럽게 들어갑니다.",
      "가중치를 어떻게 정하든 원리는 같습니다. 목표 궤도에서 가장 가까운 점을 고릅니다."], size=9.5)

# ============================================================================= 11. 왜 가장 가까운 점인가
s = content_slide("왜 가장 가까운 점인가")
if fig("F8a_schematic_basin"):
    ox, oy, bw, bh = fit_image(s, fig("F8a_schematic_basin"), X0, Y0, 4.3, 4.3)
    caption(s, X0, oy + bh + 0.05, 4.3, "도식입니다. 진한 선이 목표 gait의 주기 궤도이고, 옅은 띠가 돌아올 수 있는 영역입니다.")
card(s, X0 + 4.5, Y0, CW - 4.5, 5.55, "이론적인 뒷받침",
     ["전문가 정책과 gait가 합쳐지면 안정한 주기 궤도, 곧 극한 주기 궤도가 됩니다. 작은 흔들림이 있어도 돌아온다는 것은 실험으로 이미 보고 있습니다.",
      "돌아오는 영역을 흡인 영역이라고 부릅니다. 전환은 상태를 목표 궤도 기준으로 갑자기 점프시키는 일입니다. 점프한 곳이 흡인 영역 안이면 살고, 밖이면 넘어집니다.",
      "흡인 영역의 경계는 28차원이라 직접 계산할 수 없습니다. 하지만 궤도에서 가까울수록 안에 있을 확률이 높습니다. 그래서 거리를 줄이는 것이 살아남을 확률을 높이는 대리 목표가 됩니다.",
      "진동자 이론에는 궤도 밖의 점에도 결국 어느 위상으로 수렴하는지가 정해져 있다는 결과가 있습니다. 점근 위상, 또는 등위상선이라고 부릅니다. 가장 가까운 점을 고르는 규칙은 이 점근 위상을 가까운 범위에서 근사하는 것입니다.",
      "애니메이션 분야의 모션 그래프도 같은 규칙을 씁니다. 자세와 속도의 거리가 작은 순간에만 동작을 이어 붙입니다."], size=9)

# ============================================================================= 12. 강화학습으로 보면
s = content_slide("강화학습으로 보면")
if fig("F8b_schematic_initiation"):
    ox, oy, bw, bh = fit_image(s, fig("F8b_schematic_initiation"), X0, Y0, 4.6, 2.9)
    caption(s, X0, oy + bh + 0.05, 4.6, "왼쪽이 출발 gait의 궤도이고 오른쪽이 목표 gait의 궤도입니다. 옅은 영역이 시작 집합입니다.")
card(s, X0 + 4.8, Y0, CW - 4.8, 3.2, "시작 집합이라는 말로 정리됩니다",
     ["스킬마다 그 스킬을 안전하게 시작할 수 있는 상태의 집합이 있습니다. 시작 집합이라고 부릅니다. 흡인 영역의 강화학습 이름입니다.",
      "인계 시작 학습은 시작 집합을 넓히는 일입니다. 위상 규칙은 시작 집합 안에 들어가는 점을 고르는 일입니다.",
      "둘은 서로를 보완합니다. 논문의 이야기 한 줄로 쓰기 좋습니다."], size=9)
card(s, X0, Y0 + 3.4, CW, 2.15, "보상을 바꿔서 이어 학습할 때 조심할 점 (질문에 대한 답)",
     ["가치 함수가 옛 보상에 맞춰져 있어서 처음 몇 번의 갱신에서 이득 추정이 치우칩니다. 학습률을 낮추고 신뢰 영역 한도를 그대로 두면 한 번에 무너지지는 않습니다.",
      "새 보상만 챙기는 쪽으로 샐 수 있습니다. 항은 작게, 인계 시작 환경에만 넣고, 정지 시작 에피소드는 그대로 둡니다.",
      "시간 기준 조건은 정책이 볼 수 없습니다. 거리 J처럼 상태 기준으로 정의하면 정책이 볼 수 있고 평소 주행에서는 저절로 사라집니다.",
      "새 항은 나중에 0으로 줄여서 원래 보상으로 돌아옵니다. 퍼텐셜 기반이 아닌 보상은 최적 정책을 바꾸기 때문입니다."], size=8.5)

# ============================================================================= 13. 구현 세 수준
s = content_slide("구현 방법 세 수준")
rows = [["방법", "무엇이 필요한가", "장점", "주의할 점"],
        ["거리 기반", "궤도 표와 가중치입니다. 은행에서 바로 만듭니다.", "설명이 쉽고 학습이 필요 없습니다. 계산 비용이 없습니다.", "가중치를 사람이 고릅니다. 실제 실패 원인과 다를 수 있습니다."],
        ["분류기 기반", "은행 상태와 진입 성공 여부 기록입니다. 이미 있습니다.", "시작 집합을 데이터로 직접 추정합니다. 실제 원인을 반영합니다.", "데이터가 없는 gait 쌍에는 약합니다. 해석이 조금 어렵습니다."],
        ["가치 함수 기반", "목표 전문가의 critic입니다. 추가 모델이 없습니다.", "정책이 스스로 자신 있는 위상을 고릅니다. 학습과 같이 좋아집니다.", "인계 상태가 학습 분포 안에 있어야 믿을 수 있습니다. 인계 시작 학습 뒤에 유효합니다."]]
add_table(s, rows, X0, Y0, CW, 2.8, col_w=[1.5, 2.6, 2.4, 2.4], size=9)
card(s, X0, Y0 + 3.0, CW, 2.55, "추천하는 순서",
     ["먼저 거리 기반으로 원리가 맞는지 확인합니다. 학습 없이 규칙만 바꿔 평가하면 몇 분이면 됩니다. 이 덱의 실험이 그것입니다.",
      "다음으로 후보 위상을 전부 시도한 기록으로 분류기를 학습합니다. 어떤 위상도 안 되는 진입과, 위상만 잘 고르면 되는 진입을 가릅니다.",
      "인계 시작 학습을 거친 뒤에는 가치 함수 기반을 비교군으로 둡니다.",
      "규칙은 경로 추종 시연의 전환 블록과 통합 정책 환경의 위상 정렬에 같은 자리로 꽂힙니다."], size=9.5)

# ============================================================================= 14. 실험 ① 규칙 비교
s = content_slide("실험 ① 규칙 비교")
if S.get("rules"):
    rules, targets = S["rules"], S["targets"]
    rows = [["목표 gait"] + [RULE_KO.get(r, r) for r in rules]]
    for t in targets:
        rows.append([t] + [f"{S['per_target'][t][r]:.2f}" for r in rules])
    rows.append(["평균"] + [f"{S['mean'][r]:.3f}" for r in rules])
    add_table(s, rows, X0, Y0, 4.6, 0.32 * len(rows), col_w=[1.2] + [3.4 / len(rules)] * len(rules), size=8.5)
    if fig("F7_rule_comparison"):
        ox, oy, bw, bh = fit_image(s, fig("F7_rule_comparison"), X0 + 4.8, Y0, CW - 4.8, 2.9)
    best = min(S["mean"], key=S["mean"].get)
    sign_m, near_m, k0_m = S["mean"].get("sign"), S["mean"].get("near"), S["mean"].get("k0")
    mean_txt = ", ".join(f"{RULE_KO[r]} {S['mean'][r]:.3f}" for r in rules)
    n_states = S["n_states"]
    lines = [f"같은 은행 상태 {n_states:,}개에 대해 시작 위상 규칙만 바꿔서 150스텝 안에 넘어지는지 봤습니다. 전문가는 지금 대표 모델 그대로입니다.",
             f"평균 실패 비율은 {mean_txt} 입니다."]
    sm_m = S["mean"].get("signmom")
    if sm_m is not None and sign_m is not None:
        if sm_m < sign_m - 0.02:
            lines.append(f"부호 정렬의 동점을 운동량으로 가르는 규칙은 실패를 {sign_m - sm_m:.3f}만큼 더 줄였습니다.")
        elif abs(sm_m - sign_m) <= 0.02:
            lines.append("부호 정렬의 동점을 운동량으로 가르는 규칙은 부호 정렬과 차이가 잡음 범위였습니다.")
        else:
            lines.append(f"부호 정렬의 동점을 운동량으로 가르는 규칙은 부호 정렬보다 {sm_m - sign_m:.3f}만큼 나빴습니다.")
    if near_m is not None and sign_m is not None:
        if near_m < sign_m - 0.02:
            lines.append(f"가장 가까운 점 규칙이 부호 정렬보다 실패를 {sign_m - near_m:.3f}만큼 줄였습니다.")
        elif abs(near_m - sign_m) <= 0.02:
            lines.append("가장 가까운 점 규칙과 부호 정렬의 차이는 잡음 범위 안이었습니다. 이 가중치로는 개선이 없었습니다.")
        else:
            lines.append(f"가장 가까운 점 규칙이 부호 정렬보다 오히려 {near_m - sign_m:.3f}만큼 나빴습니다. 이 가중치는 실패 원인을 제대로 재지 못한 것입니다.")
    if k0_m is not None and k0_m <= min(v for r, v in S["mean"].items() if r != "k0"):
        lines.append("위상 0 재시작이 가장 낮았습니다. 전문가가 정지 상태의 위상 0에서만 시작하도록 학습됐기 때문에, 시작 집합이 위상 0 근처에 몰려 있다고 읽힙니다.")
    lines.append(f"가장 좋은 규칙은 {RULE_KO.get(best, best)}였습니다.")
    card(s, X0, Y0 + max(0.32 * len(rows), 2.9) + 0.25, CW, Y1 - (Y0 + max(0.32 * len(rows), 2.9) + 0.25), "읽는 법과 판정", lines, size=9)
else:
    card(s, X0, Y0, CW, 2.0, "실험 결과 대기", ["규칙 비교 실험이 아직 끝나지 않았습니다."], size=9.5)

# ============================================================================= 15. 실험 ② 거리와 실패, 오라클
s = content_slide("실험 ② 거리와 실패")
if fig("F6_distance_vs_failure"):
    ox, oy, bw, bh = fit_image(s, fig("F6_distance_vs_failure"), X0, Y0, 4.6, 2.75)
    caption(s, X0, oy + bh + 0.03, 4.6, "진입 순간의 거리 J를 열 구간으로 나누고, 구간마다 넘어진 비율을 찍었습니다.")
lines = []
if S.get("n"):
    lo, hi = S["fail_low"], S["fail_high"]
    lines.append(f"거리가 짧은 쪽 20퍼센트에서는 실패가 {lo:.2f}이고, 먼 쪽 20퍼센트에서는 {hi:.2f}입니다. 상관계수는 {S['corr']:.2f}입니다.")
    lines.append(f"가장 가까운 10퍼센트 진입만 보면 실패가 {S['fail_lowest10']:.2f}로 낮습니다. 이 진입은 대부분 같은 집안 안의 전환입니다. 그 너머에서는 거리와 실패의 관계가 사라집니다.")
    if hi - lo > 0.1:
        lines.append("거리가 멀수록 실패가 늘어납니다. 원리가 데이터에서 확인됩니다.")
    else:
        lines.append("이 가중치로 잰 거리는 실패를 잘 가르지 못했습니다. 원리가 틀렸다기보다, 무엇을 재야 하는지를 이 가중치가 놓친 것입니다. 해석은 다음 장에 적었습니다.")
if S.get("oracle"):
    om = S["oracle_mean"]
    lines.append(f"후보 위상을 전부 시도해 봤습니다. 어떤 위상을 골라도 넘어지는 상태는 평균 {om:.2f}뿐입니다. 거의 모든 상태에 살아남는 위상이 하나 이상 있습니다.")
    lines.append("다만 이것이 곧 규칙으로 고를 수 있다는 뜻은 아닙니다. 위상별 결과가 상태에서 예측되는지는 다음 장의 지도로 봅니다.")
card(s, X0 + 4.8, Y0, CW - 4.8, 3.1, "읽는 법과 판정", lines or ["실험 결과가 아직 없습니다."], size=8.5)
if S.get("oracle"):
    rows = [["목표 gait", "부호 정렬 실패", "고정 위상 중 최선", "어떤 위상도 안 됨"]]
    for t in EXP_ALL["targets"]:
        sign_v = S["per_target"].get(t, {}).get("sign") if S.get("per_target") else None
        rows.append([t, f"{sign_v:.2f}" if sign_v is not None else "-", f"{S['best_fixed'][t]:.2f}", f"{S['oracle'][t]:.2f}"])
    add_table(s, rows, X0, Y0 + 3.3, CW, 0.215 * len(rows), col_w=[1.6, 2.4, 2.4, 2.5], size=8)
    note(s, X0, Y0 + 3.3 + 0.215 * len(rows) + 0.05, CW, 0.4,
         "고정 위상 중 최선은 열 하나를 모든 상태에 똑같이 썼을 때 가장 좋은 값입니다. 어떤 위상도 안 됨은 후보를 다 시도해도 전부 넘어진 상태의 비율입니다. 출발 9개, 상태 10개씩입니다.", size=8)

# ============================================================================= 15a. 실험 ③ 위상별 결과 지도
s = content_slide("실험 ③ 위상별 결과 지도")
R = INFO.get("raster") or {}
if fig("F9_phase_raster"):
    ox, oy, bw, bh = fit_image(s, fig("F9_phase_raster"), X0, Y0, CW, 3.55)
lines = ["행 하나가 은행 상태 하나이고, 열 하나가 후보 위상 하나입니다. 빨간 칸은 그 위상에서 시작하면 150스텝 안에 넘어진다는 뜻입니다."]
if R:
    surv = ", ".join(f"{t} {v['survive_frac']:.0%}" for t, v in R.items())
    runs = float(np.mean([v["runs"] for v in R.values()]))
    runs_sh = float(np.mean([v["runs_shuffled"] for v in R.values()]))
    lines.append(f"살아남는 칸의 비율은 {surv}입니다. 어떤 위상도 안 되는 행은 1에서 2퍼센트뿐입니다.")
    lines.append(f"빨간 칸은 흩어져 있지 않고 이웃한 위상끼리 뭉쳐 있습니다. 한 행의 빨간 덩어리 수는 평균 {runs:.1f}개인데, 같은 칸을 무작위로 섞으면 {runs_sh:.1f}개가 됩니다. 즉 상태마다 안전한 위상 창이 있습니다.")
lines.append("창의 위치가 상태마다 다르기 때문에 고정 위상 하나로는 안 되고, 상태를 보고 창을 찾는 규칙이 필요합니다. 부호 정렬은 그 창을 부분적으로만 맞춥니다.")
if S.get("n_all"):
    lines.append(f"이 지도가 곧 학습 데이터입니다. 상태와 위상을 넣으면 살아남을지 답하는 분류기를 여기서 학습할 수 있습니다. 여덟 목표에 대해 기록이 {S['n_all']:,}개 있습니다.")
card(s, X0, Y0 + 3.7, CW, Y1 - (Y0 + 3.7), "지도 읽는 법과 판정", lines, size=8.5)

# ============================================================================= 15b. 결과 해석과 수정된 제안
s = content_slide("결과 해석과 수정된 제안")
sm_line = ""
if S.get("mean", {}).get("signmom") is not None:
    sm_line = f" 실제로 이 규칙의 평균 실패는 {S['mean']['signmom']:.3f}이고, 부호 정렬은 {S['mean']['sign']:.3f}입니다."
card(s, X0, Y0, 4.35, 2.7, "왜 부호 정렬이 이겼나",
     ["관절은 방향만 정해 주는 토크 모터입니다. 그래서 토크 방향이 이어지는 것이 상태 거리보다 먼저입니다. 방향이 뒤집힌 관절은 그 순간부터 반대로 밀리기 때문입니다.",
      "거리는 스물여덟 개 숫자를 똑같이 더합니다. 넘어지는 원인은 몇 개 관절의 충돌인데, 그 신호가 나머지 숫자에 묻힙니다.",
      "아주 가까운 진입, 곧 같은 집안 안의 전환만 거리로도 안전하게 골라졌습니다. 거리가 조금이라도 멀어지면 거리는 더 이상 실패를 가르지 못했습니다."], size=9)
card(s, X0 + 4.55, Y0, CW - 4.55, 2.7, "그래서 무엇을 재야 하나",
     ["부호 충돌을 먼저 세고, 충돌하는 관절이 얼마나 빠른지로 동점을 가르는 규칙이 자연스러운 다음 후보입니다." + sm_line,
      "가중치를 사람이 하나씩 고르는 대신, 후보 위상을 전부 시도한 기록으로 배우는 것이 정직한 방법입니다. 다음 단계에 적었습니다.",
      "어떤 위상을 골라도 넘어지는 상태는 1에서 2퍼센트뿐이었습니다. 실패의 대부분은 위상을 잘 고르면 피할 수 있는 것으로 보입니다. 그래서 규칙을 데이터로 배우는 일이 그만큼 값어치가 있습니다."], size=9)
card(s, X0, Y0 + 2.9, CW, 2.65, "원리는 살아 있습니다",
     ["목표 궤도에서 가까운 점을 고른다는 원리는, 가까움을 어떤 계량으로 재느냐에 달려 있습니다. 이번 실험은 관절 공간의 보통 거리가 그 계량이 아니라는 것을 보였습니다.",
      "부호 정렬 자체가 이 원리의 한 계량입니다. 토크 방향 공간에서 다른 부호의 개수를 세는 해밍 거리입니다. 이 계량이 관절 공간 거리보다 실패를 더 잘 가릅니다.",
      "그래서 논문에는 어떤 계량이 맞는지를 실험으로 정한 과정으로 쓸 수 있습니다. 부정적인 결과도 그대로 적는 것이 이 덱의 원칙입니다."], size=9.5, fill=NAVY, line=None, header_color=WHITE, text_color=WHITE, bullet_color="9DC3E6")

# ============================================================================= 16. 참고문헌
s = content_slide("참고문헌")
rows = [["저자와 연도", "제목과 게재처", "우리 연구와 어떻게 이어지나"],
        ["Hirose 1993", "Biologically Inspired Robots: Snake-Like Locomotors and Manipulators (Oxford University Press)", "gait의 기준 파형인 서펜오이드 곡선입니다."],
        ["Winfree 1980, 2판 2001", "The Geometry of Biological Time (Springer)", "궤도 밖의 점에도 위상을 매기는 점근 위상 개념입니다."],
        ["Guckenheimer 1975", "Isochrons and phaseless sets, Journal of Mathematical Biology 1권 259–273쪽", "등위상선의 존재와 성질을 수학적으로 보였습니다."],
        ["Aoi, Tsuchiya 2005", "Locomotion Control of a Biped Robot Using Nonlinear Oscillators, Autonomous Robots 19권 219–232쪽", "발이 닿는 순간 위상을 되맞춰 보행을 안정화했습니다."],
        ["Westervelt, Grizzle, Koditschek 2003", "Hybrid Zero Dynamics of Planar Biped Walkers, IEEE Transactions on Automatic Control 48권 1호 42–56쪽", "보행을 안정한 주기 궤도로 보는 관점입니다."],
        ["Kovar, Gleicher, Pighin 2002", "Motion Graphs, ACM Transactions on Graphics 21권 3호 473–482쪽 (SIGGRAPH 2002)", "자세와 속도의 거리가 작은 순간에 동작을 이어 붙입니다. gait 라이브러리 전환과 같은 문제입니다."],
        ["Konidaris, Barto 2009", "Skill Discovery in Continuous Reinforcement Learning Domains using Skill Chaining, NIPS 22", "스킬의 시작 집합을 데이터로 배우는 방법입니다."],
        ["Bullo, Lewis 2005", "Geometric Control of Mechanical Systems (Springer, Texts in Applied Mathematics 49)", "질량 행렬을 거리 계량으로 쓰는 근거입니다."]]
add_table(s, rows, X0, Y0, CW, 4.4, col_w=[1.7, 4.3, 2.9], size=8)
note(s, X0, Y0 + 4.55, CW, 0.5, "서지 정보는 2026년 9월 11일에 출판사 페이지와 Crossref로 확인했습니다. 전체 목록은 docs/references_transition_learning.md 9절에 있습니다.", size=8.5)

# ============================================================================= 17. 다음 단계
s = content_slide("다음 단계")
steps = [("위상 규칙을 데이터로 배우기", f"후보 위상 전부를 시도한 기록 {S.get('n_all', 0):,}개로, 상태와 위상을 넣으면 살아남을지 답하는 분류기를 학습합니다. 교차 검증으로 부호 정렬보다 나은지 먼저 확인합니다."),
         ("규칙을 실제 자리에 꽂기", "경로 추종 시연의 전환 블록과 통합 정책 환경의 위상 정렬에 같은 함수로 넣습니다. 옵션으로 두어 부호 정렬과 바로 비교합니다."),
         ("인계 시작 학습과 합치기", "새 규칙으로 고른 위상에서 인계 시작 학습을 다시 돌립니다. 규칙은 시작 집합 안의 점을 고르고, 학습은 시작 집합을 넓힙니다."),
         ("논문 그림으로 정리", "부호 일치 상한 표, 궤도 그림, 거리와 실패 곡선, 규칙 비교 표를 논문 그림으로 다듬습니다. 파일은 docs/figures/phase_selection 에 있습니다.")]
step_cards(s, X0, Y0, CW, steps, 2, 1.55, size=9)
note(s, X0, Y0 + 3.4, CW, 0.9, "이 덱의 실험 스크립트는 training/eval_phase_rules.py 이고, 그림 스크립트와 덱 스크립트는 docs/deck_src 에 있습니다. 결과 파일은 runs/moving_state_bank/eval_phase_rules*.json 입니다.", size=9)

prs.save(OUT)
print("saved", OUT, f"{OUT.stat().st_size/1e6:.1f} MB, slides", len(prs.slides))
print(json.dumps({k: v for k, v in S.items() if k not in ("per_target",)}, ensure_ascii=False, default=str)[:800])
