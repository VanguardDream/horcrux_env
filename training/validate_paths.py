"""다양한 웨이포인트 경로로 경로 추종 성능을 검증하고, 두 설정을 같은 시드끼리 짝지어 비교한다 (2026-09-14).

run 모드: 정책·규칙·커맨더 설정 하나로 경로 목록 × 시드를 돌려(path_following.py 서브프로세스, 영상 없음)
          result.txt를 모아 results/path_validation/<tag>.json 으로 저장한다 (git 추적, 2026-10-20 runs/에서 이동).
compare 모드: JSON 두 개를 경로·시드로 짝지어 평균 오차·최대 오차·시간·전환·완주를 비교한다(부호 검정).

사용:
  python training/validate_paths.py run --tag s3_lat --policy unified --model ... --vecnorm ... --align-rule lat
  python training/validate_paths.py compare results/path_validation/s3_lat.json results/path_validation/s4_lat.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
DEFAULT_PATHS = ["square", "star", "gauntlet", "zigzag", "scurve", "octagon", "serpentine", "uturn", "random"]
PATH_KO = {"square": "네모", "star": "별", "gauntlet": "장애물", "zigzag": "지그재그", "scurve": "S자", "octagon": "팔각형",
           "serpentine": "굽이길", "uturn": "유턴", "random": "무작위", "line": "직선"}


def parse_result(folder: Path) -> dict | None:
    f = folder / "result.txt"
    if not f.exists():
        return None
    t = f.read_text(encoding="utf-8")
    e = re.search(r"평균 ([\d.]+) m / 최대 ([\d.]+) m", t)
    s = re.search(r"명령 전환 (\d+)회 \| 주행 (\d+) 스텝 \(([\d.]+) s\)", t)
    wp = re.search(r"웨이포인트 (\d+)/(\d+)", t)
    miss = re.search(r"판정 원 밖 통과 (\d+)/(\d+)", t)
    back = re.search(r"되돌아간 전환 (\d+)회", t)
    if not (e and s and wp):
        return None
    return dict(err=float(e.group(1)), err_max=float(e.group(2)), sw=int(s.group(1)), steps=int(s.group(2)), sec=float(s.group(3)),
                done="완주=True" in t, wp=int(wp.group(1)), wp_total=int(wp.group(2)),
                miss=int(miss.group(1)) if miss else None, back=int(back.group(1)) if back else None, folder=str(folder))


def run_mode(a) -> None:
    out_dir = ROOT / "results/path_validation"   # 결과 JSON은 git 추적 폴더에 (CLAUDE.md "연구 기록")
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    t0 = time.time()
    for kind in a.paths:
        for seed in range(1, a.seeds + 1):
            suffix = f"_val_{a.tag}_{kind}_r{seed}"
            cmd = [PY, str(ROOT / "training/path_following.py"), "--path", kind, "--seed", str(seed), "--no-video",
                   "--start-noise", str(a.start_noise), "--path-rotate-deg", str(a.path_rotate_deg), "--scale", str(a.scale),
                   "--max-steps", str(a.max_steps), "--policy", a.policy, "--align-rule", a.align_rule, "--tag-suffix", suffix]
            if a.policy == "unified":
                cmd += ["--model", a.model, "--vecnorm", a.vecnorm]
            if a.align_all:
                cmd.append("--align-all")
            for o in a.expert_override:
                cmd += ["--expert-override", o]
            cmd += a.extra
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            m = re.search(r"산출물: (\S+)", proc.stdout)
            rec = parse_result(Path(m.group(1))) if m else None
            if rec is None:
                print(f"[실패] {kind} 시드 {seed}: {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else '결과 없음'}", flush=True)
                continue
            rec.update(kind=kind, seed=seed)
            records.append(rec)
            print(f"{kind:9s} r{seed:<2d} 오차 {rec['err']:.3f} 최대 {rec['err_max']:.2f} {rec['sec']:5.1f}s 전환 {rec['sw']:2d} 완주 {rec['wp']}/{rec['wp_total']}", flush=True)
    summary = {}
    for kind in a.paths:
        rs = [r for r in records if r["kind"] == kind]
        if rs:
            summary[kind] = dict(n=len(rs), done=sum(r["done"] for r in rs), err=float(np.mean([r["err"] for r in rs])),
                                 err_sd=float(np.std([r["err"] for r in rs])), err_max=float(np.mean([r["err_max"] for r in rs])),
                                 sec=float(np.mean([r["sec"] for r in rs])), sw=float(np.mean([r["sw"] for r in rs])))
    out = out_dir / f"{a.tag}.json"
    json.dump(dict(tag=a.tag, args={k: v for k, v in vars(a).items() if k != "func"}, summary=summary, records=records,
                   elapsed_sec=time.time() - t0), open(out, "w"), ensure_ascii=False, indent=1, default=str)
    print("\n| 경로 | 완주 | 평균 오차 | 최대 오차 | 시간 | 전환 |")
    print("|---|---|---|---|---|---|")
    for kind, d in summary.items():
        print(f"| {PATH_KO.get(kind, kind)} | {d['done']}/{d['n']} | {d['err']:.3f}±{d['err_sd']:.3f} | {d['err_max']:.2f} | {d['sec']:.0f}초 | {d['sw']:.0f} |")
    print(f"저장: {out} ({(time.time() - t0) / 60:.1f}분)")


def sign_p(w: int, l: int) -> float:
    n, k = w + l, min(w, l)
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def compare_mode(a) -> None:
    A, B = json.load(open(a.a)), json.load(open(a.b))
    ra = {(r["kind"], r["seed"]): r for r in A["records"]}
    rb = {(r["kind"], r["seed"]): r for r in B["records"]}
    kinds = [k for k in DEFAULT_PATHS + sorted({k for k, _ in ra}) if k in {k for k, _ in ra}]
    kinds = list(dict.fromkeys(kinds))
    print(f"## {A['tag']} (A) vs {B['tag']} (B) — 같은 경로·시드 짝지음. 이김 = A가 작음")
    print("| 경로 | 쌍 | 평균 오차 이김/비김/짐 (Δ, p) | 최대 오차 이김/짐 | 시간 이김/짐 | 완주 A/B | 평균 오차 A → B |")
    print("|---|---|---|---|---|---|---|")
    tot = dict(w=0, t=0, l=0, d=[], mw=0, ml=0, tw=0, tl=0)
    result = {}
    for kind in kinds:
        keys = sorted(k for k in ra if k[0] == kind and k in rb)
        if not keys:
            continue
        d = np.array([ra[k]["err"] - rb[k]["err"] for k in keys])
        dm = np.array([ra[k]["err_max"] - rb[k]["err_max"] for k in keys])
        dt = np.array([ra[k]["sec"] - rb[k]["sec"] for k in keys])
        w, l = int((d < -1e-9).sum()), int((d > 1e-9).sum()); t = len(keys) - w - l
        mw, ml = int((dm < -1e-9).sum()), int((dm > 1e-9).sum()); tw, tl = int((dt < -1e-9).sum()), int((dt > 1e-9).sum())
        da, db = sum(ra[k]["done"] for k in keys), sum(rb[k]["done"] for k in keys)
        ea, eb = np.mean([ra[k]["err"] for k in keys]), np.mean([rb[k]["err"] for k in keys])
        result[kind] = dict(n=len(keys), w=w, t=t, l=l, d=float(d.mean()), p=sign_p(w, l), mw=mw, ml=ml, tw=tw, tl=tl, done_a=da, done_b=db, err_a=float(ea), err_b=float(eb))
        print(f"| {PATH_KO.get(kind, kind)} | {len(keys)} | {w}/{t}/{l} ({d.mean():+.3f}, p={sign_p(w, l):.2f}) | {mw}/{ml} | {tw}/{tl} | {da}/{db} | {ea:.3f} → {eb:.3f} |")
        tot["w"] += w; tot["t"] += t; tot["l"] += l; tot["d"] += list(d); tot["mw"] += mw; tot["ml"] += ml; tot["tw"] += tw; tot["tl"] += tl
    if tot["d"]:
        print(f"| 합산 | {len(tot['d'])} | {tot['w']}/{tot['t']}/{tot['l']} ({np.mean(tot['d']):+.3f}, p={sign_p(tot['w'], tot['l']):.3f}) | {tot['mw']}/{tot['ml']} | {tot['tw']}/{tot['tl']} | | |")
    if a.out:
        json.dump(dict(a=A["tag"], b=B["tag"], per_path=result, total=dict(w=tot["w"], t=tot["t"], l=tot["l"], d=float(np.mean(tot["d"])) if tot["d"] else None,
                       p=sign_p(tot["w"], tot["l"]), mw=tot["mw"], ml=tot["ml"], tw=tot["tw"], tl=tot["tl"])), open(a.out, "w"), ensure_ascii=False, indent=1)
        print("저장:", a.out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    r = sub.add_parser("run")
    r.add_argument("--tag", required=True)
    r.add_argument("--paths", nargs="+", default=DEFAULT_PATHS)
    r.add_argument("--seeds", type=int, default=10)
    r.add_argument("--policy", choices=("experts", "unified"), default="unified")
    r.add_argument("--model", default=str(ROOT / "policies/unified/03_transition_stage3/final_model.zip"))
    r.add_argument("--vecnorm", default=str(ROOT / "policies/unified/03_transition_stage3/vecnormalize.pkl"))
    r.add_argument("--align-rule", choices=("sign", "lat"), default="lat")
    r.add_argument("--align-all", action="store_true")
    r.add_argument("--expert-override", action="append", default=[])
    r.add_argument("--start-noise", type=float, default=0.03)
    r.add_argument("--path-rotate-deg", type=float, default=8.0)
    r.add_argument("--scale", type=float, default=2.0)
    r.add_argument("--max-steps", type=int, default=6000)
    r.add_argument("extra", nargs="*", help="path_following.py에 그대로 넘길 추가 인자 (예: --control-period 10)")
    r.set_defaults(func=run_mode)
    c = sub.add_parser("compare")
    c.add_argument("a"); c.add_argument("b"); c.add_argument("--out", default=None)
    c.set_defaults(func=compare_mode)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
