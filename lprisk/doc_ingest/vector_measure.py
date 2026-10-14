"""벡터 PDF 좌표 측정 — 램프 곡선부 내측 반경 (turning_radius_m 보조, method: vector).

도면에 R 치수가 적혀 있지 않을 때만 쓴다. 적힌 값이 아니라 선·원호 좌표로 잰 값이므로
판독 기록은 `method: "vector"`, `precision: "approx"`로 남기고 보고서에는 📐벡터 측정으로 표시된다.

방법 (bangchori A-401, 2026-10-14):
1. 축척: 페이지의 '1/N(A3)' 표기와 용지 크기로 mm/pt를 구한다(1pt = 25.4/72 mm × N). 없으면 --scale 필요.
2. 원 중심: 'W.P'·'Center' 라벨 옆의 작은 원 표식 중심.
3. 내측 반경: 중심에서 뻗는 차로면 빗금(방사선)의 안쪽 끝 반경 최빈값 = 차로면 내측 원호(연석).
   같은 중심의 원호(베지어)도 함께 나열해 교차 확인한다.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import fitz

from ..io import save_json
from ..paths import ROOT, wf2_dir

PAPER = {"A3": (1191, 842), "A1": (2384, 1684), "A2": (1684, 1191), "A0": (3370, 2384)}


def _scale(page: fitz.Page) -> tuple[float | None, str | None]:
    w, h = sorted((page.rect.width, page.rect.height), reverse=True)
    paper = next((k for k, (pw, ph) in PAPER.items() if abs(w - pw) < 8 and abs(h - ph) < 8), None)
    text = page.get_text()
    pat = rf"1\s*/\s*([\d,]+)\s*\(\s*{paper}\s*\)" if paper else None
    m = re.search(pat, text) if pat else None
    if not m:
        return None, None
    n = int(m.group(1).replace(",", ""))
    return 25.4 / 72 * n, f"{m.group(0)} · 용지 {paper}"


def _centers(page: fitz.Page, drawings: list, label_re: str) -> list[dict]:
    labels = [w for w in page.get_text("words") if re.match(label_re, w[4], re.I)]
    out = []
    for dr in drawings:
        r = dr["rect"]
        if not (2.5 < r.width < 6.5 and abs(r.width - r.height) < 0.6 and any(it[0] == "c" for it in dr["items"])):
            continue
        c = ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
        lab = next((w for w in labels if math.hypot((w[0] + w[2]) / 2 - c[0], (w[1] + w[3]) / 2 - c[1]) < 15), None)
        if lab and not any(math.hypot(c[0] - o["center_pt"][0], c[1] - o["center_pt"][1]) < 0.6 for o in out):
            out.append({"center_pt": [round(c[0], 2), round(c[1], 2)], "label": lab[4]})
    return out


def _fit_circle(pts):
    n = len(pts)
    sx = sum(p[0] for p in pts) / n
    sy = sum(p[1] for p in pts) / n
    u = [(p[0] - sx, p[1] - sy) for p in pts]
    suu = sum(a * a for a, _ in u); svv = sum(b * b for _, b in u); suv = sum(a * b for a, b in u)
    suuu = sum(a ** 3 for a, _ in u); svvv = sum(b ** 3 for _, b in u)
    suvv = sum(a * b * b for a, b in u); svuu = sum(b * a * a for a, b in u)
    det = suu * svv - suv * suv
    if abs(det) < 1e-9:
        return None
    uc = (0.5 * (suuu + suvv) * svv - 0.5 * (svvv + svuu) * suv) / det
    vc = (0.5 * (svvv + svuu) * suu - 0.5 * (suuu + suvv) * suv) / det
    cx, cy = uc + sx, vc + sy
    r = math.sqrt(uc * uc + vc * vc + (suu + svv) / n)
    res = max(abs(math.hypot(p[0] - cx, p[1] - cy) - r) for p in pts)
    return cx, cy, r, res


def _bezier(P, t):
    return ((1 - t) ** 3 * P[0].x + 3 * (1 - t) ** 2 * t * P[1].x + 3 * (1 - t) * t * t * P[2].x + t ** 3 * P[3].x,
            (1 - t) ** 3 * P[0].y + 3 * (1 - t) ** 2 * t * P[1].y + 3 * (1 - t) * t * t * P[2].y + t ** 3 * P[3].y)


def ramp_radius(asset_id: str, file: str, page_no: int, scale: float | None = None,
                label_re: str = r"^(W\.?P|Center)", reach_pt: float = 120, min_lines: int = 10) -> dict:
    """원 중심(W.P 등)마다 차로면 내측 반경을 잰다. 결과는 output/wf2/{a}/vector_measure_*.json."""
    doc = fitz.open(ROOT / file)
    page = doc[page_no - 1]
    scale_src = "사용자 지정(--scale)"
    if scale is None:
        scale, scale_src = _scale(page)
        if scale is None:
            return {"error": "축척 표기('1/N(A3)' 등)를 찾지 못함 — --scale <mm/pt>로 지정"}
    k = scale / 1000                                       # pt → m
    drawings = page.get_drawings()
    lines = [(it[1], it[2]) for dr in drawings for it in dr["items"] if it[0] == "l"]
    curves = [it[1:5] for dr in drawings for it in dr["items"] if it[0] == "c"]
    centers = _centers(page, drawings, label_re)
    for c in centers:
        cx, cy = c["center_pt"]
        inner = Counter()
        for a, b in lines:
            if max(abs(a.x - cx), abs(b.x - cx), abs(a.y - cy), abs(b.y - cy)) > reach_pt:
                continue
            vx, vy = b.x - a.x, b.y - a.y
            L = math.hypot(vx, vy)
            mx, my = (a.x + b.x) / 2 - cx, (a.y + b.y) / 2 - cy
            M = math.hypot(mx, my)
            if L < 2 or M < 1:
                continue
            ra, rb = math.hypot(a.x - cx, a.y - cy), math.hypot(b.x - cx, b.y - cy)
            if abs(vx * mx + vy * my) / (L * M) > 0.995 and abs(ra - rb) > 2:
                inner[round(min(ra, rb) * k, 1)] += 1
        arcs = set()
        for P in curves:
            if math.hypot(P[3].x - P[0].x, P[3].y - P[0].y) < 2:
                continue
            f = _fit_circle([_bezier(P, t / 6) for t in range(7)])
            if f and f[3] < 0.05 and math.hypot(f[0] - cx, f[1] - cy) < 0.6 and f[2] * k > 3:
                arcs.add(round(f[2] * k, 2))
        mode = inner.most_common(1)
        c["inner_edge_m"] = mode[0][0] if mode and mode[0][1] >= min_lines else None
        c["inner_edge_lines"] = mode[0][1] if mode else 0
        c["radial_lines"] = sum(inner.values())
        c["arcs_m"] = sorted(arcs)
    got = [c for c in centers if c["inner_edge_m"] is not None]
    best = min(got, key=lambda c: c["inner_edge_m"]) if got else None
    result = {"file": file, "page": page_no, "scale_mm_per_pt": round(scale, 2), "scale_source": scale_src,
              "method": "vector", "centers": centers}
    if best:
        cx, cy = best["center_pt"]
        R = best["inner_edge_m"] / k
        result["suggested"] = {
            "field": "turning_radius_m", "value": best["inner_edge_m"], "unit": "m", "precision": "approx",
            "bbox": [round(cx - R * 1.4, 1), round(cy - R * 1.4, 1), round(cx + R * 1.4, 1), round(cy + R * 1.4, 1)],
            "range_m": [min(c["inner_edge_m"] for c in got), max(c["inner_edge_m"] for c in got)],
            "note": (f"벡터 좌표 측정: {best['label']} 중심~차로면 내측 원호(빗금 {best['inner_edge_lines']}개 시작 반경). "
                     f"축척 {scale:.1f}mm/pt({scale_src}). 중심 {len(got)}곳 범위 "
                     f"{min(c['inner_edge_m'] for c in got)}~{max(c['inner_edge_m'] for c in got)}m. "
                     "도면 R 표기 아님 · 램프 곡선부 내측 반경(차량 회전 궤적·출차부 R 아님)")}
    else:
        result["suggested"] = None
    save_json(wf2_dir(asset_id) / f"vector_measure_{Path(file).stem}_p{page_no}.json", result)
    return result
