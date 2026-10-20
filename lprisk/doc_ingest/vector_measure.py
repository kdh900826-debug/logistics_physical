"""벡터 PDF 좌표 측정 (method: vector).

도면에 치수가 적혀 있지 않을 때만 쓴다. 적힌 값이 아니라 선·원호 좌표로 잰 값이므로
판독 기록은 `method: "vector"`, `precision: "approx"`로 남기고 보고서에는 📐벡터 측정으로 표시된다.

1) ramp_radius — 램프 곡선부 내측 반경 (turning_radius_m 보조, bangchori A-401, 2026-10-14)
   1. 축척: 페이지의 '1/N(A3)'·'A3:1/N' 표기와 용지 크기로 mm/pt를 구한다(1pt = 25.4/72 mm × N). 없으면 --scale 필요.
   2. 원 중심: 'W.P'·'Center' 라벨 옆의 작은 원 표식 중심.
   3. 내측 반경: 중심에서 뻗는 차로면 빗금(방사선)의 안쪽 끝 반경 최빈값 = 차로면 내측 원호(연석).
      같은 중심의 원호(베지어)도 함께 나열해 교차 확인한다.

2) lines_near / distance — 두 선 사이 직선거리·사각 구역 면적 (접안 구획·야드 깊이·하역장 하부 면적, 2026-10-20)
   판독자는 재고 싶은 두 선 위(또는 가까이)의 점을 준다. 스크립트가 각 점을 가장 가까운 벡터 선분에 붙이고
   (snap), 두 선분이 평행하면 선 사이 수직거리, 아니면 붙은 두 점 사이 거리를 잰다. 거리 두 쌍을 주면
   (서로 직각일 때) 사각 구역 면적 = 거리1 × 거리2. 좌표는 PDF 원본(회전 전) pt — get_text('words')·
   get_drawings()와 같은 좌표계다. 축척은 같은 페이지의 기둥 그리드 치수(예: 11,000)를 먼저 재서 확인한다.

3) depth_min — 야드 깊이 최솟값 (yard_depth_m, 2026-10-20 사용자 지시 '최솟값 기준')
   도크면 직선에서 반대편 경계(사선·곡선 연석, 주차 구획선)까지의 수직거리를 접안 구간(첫~끝 구획) 전체에서 재고
   최솟값을 값으로 낸다. 경계가 곡선(베지어)이면 선분으로 펼친다. 최댓값·덮음 비율(coverage)도 남긴다.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import fitz

from ..io import save_json
from ..paths import ROOT, rel, wf2_dir

PAPER = {"A3": (1191, 842), "A1": (2384, 1684), "A2": (1684, 1191), "A0": (3370, 2384)}


def _scale(page: fitz.Page) -> tuple[float | None, str | None]:
    w, h = sorted((page.rect.width, page.rect.height), reverse=True)
    paper = next((k for k, (pw, ph) in PAPER.items() if abs(w - pw) < 8 and abs(h - ph) < 8), None)
    text = page.get_text()
    m = None
    if paper:   # '1/800(A3)' (DiJ 표제란) 또는 'SCALE = A3:1/800' (가우건축 표제란)
        m = (re.search(rf"1\s*/\s*([\d,]+)\s*\(\s*{paper}\s*\)", text)
             or re.search(rf"{paper}\s*:\s*1\s*/\s*([\d,]+)", text))
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


# ── 직선거리·사각 면적 (2026-10-20) ─────────────────────────────────

def _page_scale(page: fitz.Page, scale: float | None) -> tuple[float | None, str | None]:
    if scale is not None:
        return scale, "사용자 지정(--scale)"
    return _scale(page)


def _segments(page: fitz.Page, min_len: float = 2.0) -> list[tuple[float, float, float, float]]:
    segs = []
    for dr in page.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                a, b = it[1], it[2]
                segs.append((a.x, a.y, b.x, b.y))
            elif it[0] == "re":
                r = it[1]
                segs += [(r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                         (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0)]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll]
                segs += [(pts[i].x, pts[i].y, pts[(i + 1) % 4].x, pts[(i + 1) % 4].y) for i in range(4)]
    return [s for s in segs if math.hypot(s[2] - s[0], s[3] - s[1]) >= min_len]


def _foot(s, p):
    """점 p에서 선분 s로 내린 수선의 발과 거리."""
    x0, y0, x1, y1 = s
    vx, vy = x1 - x0, y1 - y0
    L2 = vx * vx + vy * vy
    t = max(0.0, min(1.0, ((p[0] - x0) * vx + (p[1] - y0) * vy) / L2))
    fx, fy = x0 + t * vx, y0 + t * vy
    return (fx, fy), math.hypot(p[0] - fx, p[1] - fy)


def _angle(s) -> float:
    return math.degrees(math.atan2(s[3] - s[1], s[2] - s[0])) % 180


def _line_dist(s, p) -> float:
    """점 p에서 선분 s를 연장한 직선까지 거리."""
    x0, y0, x1, y1 = s
    return abs((x1 - x0) * (y0 - p[1]) - (x0 - p[0]) * (y1 - y0)) / math.hypot(x1 - x0, y1 - y0)


def _snap(segs, p, tol):
    best = None
    for s in segs:
        f, d = _foot(s, p)
        if d <= tol and (best is None or d < best[2] or (abs(d - best[2]) < 1e-6 and
                                                          math.hypot(s[2] - s[0], s[3] - s[1]) > math.hypot(best[0][2] - best[0][0], best[0][3] - best[0][1]))):
            best = (s, f, d)
    return best


def _seg_json(s, k):
    return {"pt": [round(v, 2) for v in s], "length_m": round(math.hypot(s[2] - s[0], s[3] - s[1]) * k, 2),
            "angle_deg": round(_angle(s), 1)}


def _parse_pt(v) -> tuple[float, float]:
    x, y = (float(t) for t in str(v).split(","))
    return x, y


def lines_near(asset_id: str, file: str, page_no: int, at: str, radius: float = 15.0,
               scale: float | None = None, limit: int = 25) -> dict:
    """점 주변 벡터 선분과 단어 목록 — distance에 줄 점을 고르는 용도."""
    page = fitz.open(ROOT / file)[page_no - 1]
    sc, src = _page_scale(page, scale)
    k = (sc or 0) / 1000
    p = _parse_pt(at)
    rows = []
    for s in _segments(page):
        f, d = _foot(s, p)
        if d <= radius:
            rows.append({**_seg_json(s, k), "dist_pt": round(d, 2), "foot": [round(f[0], 2), round(f[1], 2)]})
    rows.sort(key=lambda r: (r["dist_pt"], -r["length_m"]))
    words = [{"text": w[4], "pt": [round(w[0], 1), round(w[1], 1), round(w[2], 1), round(w[3], 1)]}
             for w in page.get_text("words")
             if math.hypot((w[0] + w[2]) / 2 - p[0], (w[1] + w[3]) / 2 - p[1]) <= radius * 3]
    return {"file": file, "page": page_no, "at": list(p), "scale_mm_per_pt": round(sc, 2) if sc else None,
            "scale_source": src, "coord": "PDF 원본(회전 전) pt", "lines": rows[:limit], "words": words[:limit]}


def _measure_pair(segs, a, b, tol, k):
    sa, sb = _snap(segs, a, tol), _snap(segs, b, tol)
    if not sa or not sb:
        miss = [n for n, s in (("a", sa), ("b", sb)) if not s]
        return {"error": f"점 {','.join(miss)} 주변 {tol}pt 안에 벡터 선분 없음 — lines-near로 좌표 확인"}
    da = abs(_angle(sa[0]) - _angle(sb[0]))
    da = min(da, 180 - da)
    if da <= 2.0:
        d_pt = (_line_dist(sb[0], sa[1]) + _line_dist(sa[0], sb[1])) / 2
        mode = "parallel"     # 평행한 두 선 사이 수직거리
    else:
        d_pt = math.hypot(sa[1][0] - sb[1][0], sa[1][1] - sb[1][1])
        mode = "point"        # 선이 평행하지 않음 — 붙은 두 점 사이 거리
    return {"mode": mode, "distance_m": round(d_pt * k, 2), "distance_pt": round(d_pt, 2),
            "angle_diff_deg": round(da, 1), "seg_a": _seg_json(sa[0], k), "seg_b": _seg_json(sb[0], k),
            "snap_pt": [[round(v, 2) for v in sa[1]], [round(v, 2) for v in sb[1]]],
            "snap_dist_pt": [round(sa[2], 2), round(sb[2], 2)], "dir_deg": round(_angle(sa[0]), 1)}


def _overlay(asset_id: str, page: fitz.Page, segs_hi: list, bbox, name: str, dpi: int = 200) -> tuple[str, list]:
    """측정에 쓴 선분을 붉게 표시한 근거 크롭. 반환: (경로, 화면 좌표 bbox)."""
    from PIL import Image, ImageDraw
    rm = page.rotation_matrix
    r = fitz.Rect(*bbox) * rm
    r.normalize()
    clip = fitz.Rect(r.x0 - 18, r.y0 - 18, r.x1 + 18, r.y1 + 18) & page.rect
    z = dpi / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(z, z), clip=clip)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    dr = ImageDraw.Draw(img)
    for s in segs_hi:
        p0, p1 = fitz.Point(s[0], s[1]) * rm, fitz.Point(s[2], s[3]) * rm
        dr.line([((p0.x - clip.x0) * z, (p0.y - clip.y0) * z), ((p1.x - clip.x0) * z, (p1.y - clip.y0) * z)],
                fill=(230, 0, 0), width=4)
    cdir = wf2_dir(asset_id) / "crops"
    cdir.mkdir(exist_ok=True)
    fn = cdir / f"vector_{name}.png"
    img.save(fn)
    return rel(fn), [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)]


def distance(asset_id: str, file: str, page_no: int, a: str, b: str, c: str | None = None, d: str | None = None,
             scale: float | None = None, name: str = "measure", snap: float = 6.0) -> dict:
    """두 선 사이 거리(a–b). c–d를 더 주면 두 번째 거리와 사각 구역 면적(거리1 × 거리2)."""
    page = fitz.open(ROOT / file)[page_no - 1]
    sc, src = _page_scale(page, scale)
    if sc is None:
        return {"error": "축척 표기('1/N(A3)'·'A3:1/N')를 찾지 못함 — --scale <mm/pt>로 지정"}
    k = sc / 1000
    segs = _segments(page)
    m1 = _measure_pair(segs, _parse_pt(a), _parse_pt(b), snap, k)
    if "error" in m1:
        return m1
    result = {"file": file, "page": page_no, "name": name, "method": "vector", "precision": "approx",
              "scale_mm_per_pt": round(sc, 2), "scale_source": src, "coord": "PDF 원본(회전 전) pt", "d1": m1}
    hi = [tuple(m1["seg_a"]["pt"]), tuple(m1["seg_b"]["pt"])]
    pts = m1["snap_pt"]
    if c and d:
        m2 = _measure_pair(segs, _parse_pt(c), _parse_pt(d), snap, k)
        if "error" in m2:
            return m2
        result["d2"] = m2
        hi += [tuple(m2["seg_a"]["pt"]), tuple(m2["seg_b"]["pt"])]
        pts = pts + m2["snap_pt"]
        perp = abs(abs(m1["dir_deg"] - m2["dir_deg"]) - 90) <= 2.0
        if m1["mode"] == m2["mode"] == "parallel" and perp:
            result["area_m2"] = round(m1["distance_m"] * m2["distance_m"], 1)
        else:
            result["area_note"] = "두 거리가 서로 직각인 평행선 쌍이 아니라 면적을 계산하지 않음"
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    result["overlay"], result["bbox"] = _overlay(asset_id, page, hi, bbox, name)
    result["bbox_raw"] = [round(v, 1) for v in bbox]
    note = f"벡터 좌표 측정: 선 사이 {'수직' if m1['mode'] == 'parallel' else '점 간'}거리 {m1['distance_m']}m"
    if "d2" in result:
        note += f" × {result['d2']['distance_m']}m"
        if "area_m2" in result:
            note += f" = {result['area_m2']}㎡"
    note += f". 축척 {sc:.1f}mm/pt({src}). 도면 치수 표기 아님"
    result["note"] = note
    save_json(wf2_dir(asset_id) / f"vector_distance_{name}.json", result)
    return result


def _path_segments(page: fitz.Page, pieces: int = 16) -> list[tuple[int, tuple]]:
    """(경로 번호, 선분) — 직선·사각형·사변형과 베지어 곡선(pieces개 선분으로 펼침). 곡선 연석·야드 경계용."""
    out = []
    for pid, dr in enumerate(page.get_drawings()):
        for it in dr["items"]:
            if it[0] == "l":
                out.append((pid, (it[1].x, it[1].y, it[2].x, it[2].y)))
            elif it[0] == "re":
                r = it[1]
                out += [(pid, s) for s in ((r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                                            (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0))]
            elif it[0] == "qu":
                q = it[1]
                pts = [q.ul, q.ur, q.lr, q.ll]
                out += [(pid, (pts[i].x, pts[i].y, pts[(i + 1) % 4].x, pts[(i + 1) % 4].y)) for i in range(4)]
            elif it[0] == "c":
                pts = [_bezier(it[1:5], i / pieces) for i in range(pieces + 1)]
                out += [(pid, (*pts[i], *pts[i + 1])) for i in range(pieces)]
    return [(pid, s) for pid, s in out if math.hypot(s[2] - s[0], s[3] - s[1]) > 1e-6]


def depth_min(asset_id: str, file: str, page_no: int, a: str, frm: str, to: str, b: str,
              scale: float | None = None, name: str = "measure", snap: float = 6.0) -> dict:
    """도크면 직선(a)에서 반대편 경계(b — 사선·곡선 가능)까지 수직거리의 최솟값을 접안 구간(frm~to) 전체에서 잰다.

    야드 깊이 최솟값 기준(2026-10-20 사용자 지시). b는 ';'로 여러 점 — 점마다 가장 가까운 선분이 속한 벡터 경로
    (연석·옹벽·주차 구획선)를 통째로 경계로 쓴다(곡선은 선분으로 펼침). 경계를 접안 구간 투영 범위로 잘라
    잘린 선분 끝점마다 도크면까지 거리를 재고 최솟값·최댓값을 낸다. 경계가 접안 구간을 다 덮지 못하면 coverage<1.
    """
    page = fitz.open(ROOT / file)[page_no - 1]
    sc, src = _page_scale(page, scale)
    if sc is None:
        return {"error": "축척 표기('1/N(A3)'·'A3:1/N')를 찾지 못함 — --scale <mm/pt>로 지정"}
    k = sc / 1000
    sa = _snap(_segments(page), _parse_pt(a), snap)
    if not sa:
        return {"error": f"점 a 주변 {snap}pt 안에 벡터 선분 없음 — vector-lines로 좌표 확인"}
    A = sa[0]
    L = math.hypot(A[2] - A[0], A[3] - A[1])
    ux, uy = (A[2] - A[0]) / L, (A[3] - A[1]) / L
    nx, ny = -uy, ux
    proj = lambda p: (p[0] - A[0]) * ux + (p[1] - A[1]) * uy
    off = lambda p: (p[0] - A[0]) * nx + (p[1] - A[1]) * ny
    t0, t1 = sorted((proj(_parse_pt(frm)), proj(_parse_pt(to))))
    psegs = _path_segments(page)
    bpts = [_parse_pt(x) for x in str(b).split(";") if x.strip()]
    pids = set()
    for p in bpts:
        best = min(((pid, s, _foot(s, p)[1]) for pid, s in psegs if s != A), key=lambda r: r[2], default=None)
        if not best or best[2] > snap:
            return {"error": f"경계 점 {p} 주변 {snap}pt 안에 벡터 선분 없음 — vector-lines로 좌표 확인"}
        pids.add(best[0])
    side = 1 if sum(off(p) for p in bpts) > 0 else -1
    samples, used, spans = [], [], []
    for pid, s in psegs:
        if pid not in pids:
            continue
        p0, p1 = (s[0], s[1]), (s[2], s[3])
        q0, q1 = proj(p0), proj(p1)
        lo, hi = max(min(q0, q1), t0), min(max(q0, q1), t1)
        if hi < lo or abs(q1 - q0) < 1e-9 and not (t0 <= q0 <= t1):
            continue
        clip = []
        for q in ((lo, hi) if abs(q1 - q0) > 1e-9 else (q0,)):
            r = 0.0 if abs(q1 - q0) < 1e-9 else (q - q0) / (q1 - q0)
            clip.append((p0[0] + r * (p1[0] - p0[0]), p0[1] + r * (p1[1] - p0[1])))
        for p in clip:
            d = off(p) * side
            if d > 0:
                samples.append((d, p))
        used.append(s)
        spans.append((lo, hi))
    if not samples:
        return {"error": "경계 경로가 접안 구간(frm~to) 투영 범위에 없음 — b 점·frm/to 확인"}
    spans.sort()
    cov, cur = 0.0, None
    for lo, hi in spans:                     # 투영 구간 합집합 길이 → 접안 구간 덮음 비율
        if cur is None or lo > cur[1]:
            cov += (cur[1] - cur[0]) if cur else 0
            cur = [lo, hi]
        else:
            cur[1] = max(cur[1], hi)
    cov += cur[1] - cur[0]
    coverage = round(cov / (t1 - t0), 3) if t1 > t0 else None
    dmin, pmin = min(samples, key=lambda r: r[0])
    dmax, _ = max(samples, key=lambda r: r[0])
    foot = (pmin[0] - side * dmin * nx, pmin[1] - side * dmin * ny)
    result = {"file": file, "page": page_no, "name": name, "method": "vector", "precision": "approx",
              "scale_mm_per_pt": round(sc, 2), "scale_source": src, "coord": "PDF 원본(회전 전) pt",
              "d1": {"mode": "min_over_frontage", "distance_m": round(dmin * k, 2), "distance_pt": round(dmin, 2),
                     "max_m": round(dmax * k, 2), "frontage_m": round((t1 - t0) * k, 2), "coverage": coverage,
                     "seg_a": _seg_json(A, k), "boundary_paths": len(pids), "boundary_segments": len(used),
                     "min_at": [round(pmin[0], 2), round(pmin[1], 2)], "foot_on_a": [round(foot[0], 2), round(foot[1], 2)]},
              "distance_m": round(dmin * k, 2)}
    fa = (A[0] + ux * t0, A[1] + uy * t0, A[0] + ux * t1, A[1] + uy * t1)
    hi_segs = [fa] + used + [(foot[0], foot[1], pmin[0], pmin[1])]
    xs = [fa[0], fa[2], pmin[0], foot[0]] + [v for s in used for v in (s[0], s[2])]
    ys = [fa[1], fa[3], pmin[1], foot[1]] + [v for s in used for v in (s[1], s[3])]
    bbox = [min(xs), min(ys), max(xs), max(ys)]
    result["overlay"], result["bbox"] = _overlay(asset_id, page, hi_segs, bbox, name)
    result["bbox_raw"] = [round(v, 1) for v in bbox]
    note = (f"벡터 좌표 측정: 접안 구간 {result['d1']['frontage_m']}m 전체에서 도크면~경계 수직거리 최솟값 "
            f"{result['distance_m']}m (최대 {result['d1']['max_m']}m). 축척 {sc:.1f}mm/pt({src}). 도면 치수 표기 아님")
    if coverage is not None and coverage < 0.98:
        note += f". 경계가 접안 구간의 {coverage * 100:.0f}%만 덮음 — 나머지 구간 경계 점(b) 추가 필요"
    result["note"] = note
    save_json(wf2_dir(asset_id) / f"vector_distance_{name}.json", result)
    return result


def area_sum(asset_id: str, names: str) -> dict:
    """distance로 잰 직사각형 여러 개(이름 목록)의 면적 합계 — ㄱ자 등 비직사각형 구역용."""
    from ..io import load_json
    parts = []
    for n in [x.strip() for x in names.split(",") if x.strip()]:
        p = wf2_dir(asset_id) / f"vector_distance_{n}.json"
        if not p.exists():
            return {"error": f"측정 결과 없음: {p.name}"}
        r = load_json(p)
        if r.get("area_m2") is None:
            return {"error": f"{n}: 면적이 없는 측정(두 쌍 직각 측정이 아님)"}
        parts.append({"name": n, "area_m2": r["area_m2"], "page": r["page"], "bbox": r["bbox"], "overlay": r["overlay"]})
    total = round(sum(p["area_m2"] for p in parts), 1)
    return {"method": "vector", "precision": "approx", "area_m2": total, "parts": parts,
            "note": "벡터 좌표 측정 직사각형 합계: " + " + ".join(f"{p['name']} {p['area_m2']}㎡" for p in parts)
                    + f" = {total}㎡. 도면 치수 표기 아님"}
