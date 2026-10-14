"""도면 2단계 판독 보조 (설계서 §2.3 W2-③, §3.5 classify_sheets / rasterize_tiles / crop_evidence).

1단계: 모든 도면 페이지의 저해상도 썸네일 + 표제란 후보 크롭 → drawing-extractor(하위 모델)가 유형 분류
2단계: 선별된 페이지만 고해상도 타일 → drawing-extractor(상위 모델)가 수치 판독
근거: 판독 좌표 영역을 크롭해 G2 화면·보고서에 쓴다
"""
from __future__ import annotations

from pathlib import Path

import fitz

from ..io import load_json, now_iso, save_json
from ..paths import ROOT, rel, wf2_dir

THUMB_LONG_EDGE = 1100       # 썸네일 장변 픽셀
TITLEBLOCK_FRAC = (0.62, 0.62, 1.0, 1.0)   # 표제란 후보: 우하단 영역 (x0,y0,x1,y1 비율)
DETAIL_DPI = 220
TILE_PX = 1600
TILE_OVERLAP = 160


def _drawing_pages(asset_id: str) -> list[tuple[str, int]]:
    inv = load_json(wf2_dir(asset_id) / "w2_01_inventory.json")
    out = []
    for f in inv["drawings"]:
        if f.get("readable") and f["format"].startswith("pdf"):
            out += [(f["path"], i) for i in range(1, f["pages"] + 1)]
        elif f.get("readable") and f["format"] == "image":
            out.append((f["path"], 1))
    return out


def _open_page(path: str, page_no: int):
    doc = fitz.open(ROOT / path)
    return doc, doc[page_no - 1]


def _sheet_id(path: str, page_no: int) -> str:
    stem = Path(path).stem
    return f"{stem[:32]}_p{page_no:03d}"


def classify_sheets(asset_id: str) -> dict:
    """1단계 입력 생성: 썸네일·표제란 크롭과 빈 분류 인덱스."""
    out = wf2_dir(asset_id)
    tdir = out / "thumbs"
    tdir.mkdir(exist_ok=True)
    sheets = []
    for path, pno in _drawing_pages(asset_id):
        doc, page = _open_page(path, pno)
        r = page.rect
        zoom = THUMB_LONG_EDGE / max(r.width, r.height)
        sid = _sheet_id(path, pno)
        thumb = tdir / f"{sid}.png"
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(thumb)
        x0, y0, x1, y1 = TITLEBLOCK_FRAC
        clip = fitz.Rect(r.x0 + r.width * x0, r.y0 + r.height * y0, r.x0 + r.width * x1, r.y0 + r.height * y1)
        tb = tdir / f"{sid}_titleblock.png"
        page.get_pixmap(matrix=fitz.Matrix(zoom * 2.2, zoom * 2.2), clip=clip).save(tb)
        sheets.append({
            "sheet_id": sid, "file": path, "page": pno,
            "page_size_pt": [round(r.width, 1), round(r.height, 1)],
            "text_hint": " ".join(page.get_text().split())[:300],
            "thumb": rel(thumb), "titleblock": rel(tb),
            # drawing-extractor가 채우는 항목
            "drawing_type": None, "sheet_no": None, "title": None,
            "building_id": None, "floors": [], "readable": None, "note": None,
        })
    idx = {"asset_id": asset_id, "created_at": now_iso(), "sheets": sheets}
    save_json(out / "w2_03_sheet_index.json", idx)
    return idx


def rasterize_tiles(asset_id: str, sheet_id: str, dpi: int = DETAIL_DPI) -> list[dict]:
    """2단계: 한 장을 고해상도로 래스터화해 겹침 있는 타일로 자른다.

    반환 타일마다 페이지 좌표(pt) bbox를 기록하므로, 판독 결과의 좌표를 페이지 좌표로 되돌릴 수 있다.
    """
    idx = load_json(wf2_dir(asset_id) / "w2_03_sheet_index.json")
    sh = next(s for s in idx["sheets"] if s["sheet_id"] == sheet_id)
    doc, page = _open_page(sh["file"], sh["page"])
    tdir = wf2_dir(asset_id) / "tiles" / sheet_id
    tdir.mkdir(parents=True, exist_ok=True)
    scale = dpi / 72
    W, H = page.rect.width * scale, page.rect.height * scale
    step = TILE_PX - TILE_OVERLAP
    tiles = []
    ty = 0
    row = 0
    while ty < H:
        tx, col = 0, 0
        while tx < W:
            x1, y1 = min(tx + TILE_PX, W), min(ty + TILE_PX, H)
            clip = fitz.Rect(tx / scale, ty / scale, x1 / scale, y1 / scale)
            fn = tdir / f"r{row}c{col}.png"
            page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip).save(fn)
            tiles.append({"tile": rel(fn), "row": row, "col": col,
                          "bbox_pt": [round(clip.x0, 1), round(clip.y0, 1), round(clip.x1, 1), round(clip.y1, 1)]})
            if x1 >= W:
                break
            tx += step
            col += 1
        if ty + TILE_PX >= H:
            break
        ty += step
        row += 1
    save_json(tdir / "tiles.json", {"sheet_id": sheet_id, "dpi": dpi, "tiles": tiles})
    return tiles


def tile_to_page_bbox(tile_bbox_pt: list[float], tile_px: tuple[int, int], frac_box: list[float]) -> list[float]:
    """타일 내 비율 좌표(0~1) → 페이지 좌표(pt)."""
    x0, y0, x1, y1 = tile_bbox_pt
    w, h = x1 - x0, y1 - y0
    fx0, fy0, fx1, fy1 = frac_box
    return [round(x0 + w * fx0, 1), round(y0 + h * fy0, 1), round(x0 + w * fx1, 1), round(y0 + h * fy1, 1)]


def crop_evidence(asset_id: str, file: str, page_no: int, bbox_pt: list[float], name: str,
                  pad_pt: float = 18, dpi: int = 200) -> str:
    """판독 근거 영역 크롭 (여백 포함). 반환: 프로젝트 상대 경로."""
    doc, page = _open_page(file, page_no)
    r = fitz.Rect(*bbox_pt)
    r = fitz.Rect(r.x0 - pad_pt, r.y0 - pad_pt, r.x1 + pad_pt, r.y1 + pad_pt) & page.rect
    cdir = wf2_dir(asset_id) / "crops"
    cdir.mkdir(exist_ok=True)
    fn = cdir / f"{name}.png"
    page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), clip=r).save(fn)
    return rel(fn)


def crop_all(asset_id: str) -> int:
    """drawing_specs의 모든 값에 bbox가 있으면 크롭을 만들어 source_locator.crop을 채운다."""
    from ..schema import iter_slots
    path = wf2_dir(asset_id) / "w2_03_drawing_specs.json"
    rec = load_json(path)
    n = 0
    for slot, values in iter_slots(rec):
        for i, v in enumerate(values):
            loc = v.get("source_locator") or {}
            if not loc.get("bbox") and loc.get("tile") and loc.get("tile_box"):
                # 판독자는 타일 내 비율 좌표만 적는다 → 페이지 좌표로 환산
                tj = load_json(ROOT / Path(loc["tile"]).parent / "tiles.json")
                t = next((x for x in tj["tiles"] if x["tile"] == loc["tile"]), None)
                if t:
                    loc["bbox"] = tile_to_page_bbox(t["bbox_pt"], (0, 0), loc["tile_box"])
            if loc.get("bbox") and loc.get("page") and not loc.get("crop"):
                name = f"{slot.key.replace('|', '_')}_{i}".replace("-", "x")
                loc["crop"] = crop_evidence(asset_id, v["source_doc"], loc["page"], loc["bbox"], name)
                v["source_locator"] = loc
                n += 1
    save_json(path, rec)
    return n
