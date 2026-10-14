"""W2-① 입력 접수: 파일 인벤토리·형식 감지·스캔 판정 (설계서 §2.3 W2-①, §3.6)."""
from __future__ import annotations

from pathlib import Path

import fitz

from ..io import load_yaml, now_iso, save_json
from ..paths import input_dir, rel, wf2_dir

SCAN_CHARS_PER_PAGE = 200      # 페이지 텍스트 레이어 문자 수가 이보다 적으면 스캔 페이지로 본다
SCAN_PAGE_RATIO = 0.5          # 스캔 페이지 비율이 이 이상이면 파일 전체를 스캔으로 분류
TILE_PX = 1600                 # rasterize_tiles 기본 타일 크기 (판독 비용 추정용)
DETAIL_DPI = 200

EXT_FORMAT = {".pptx": "pptx", ".docx": "docx", ".dxf": "dxf", ".dwg": "dwg",
              ".png": "image", ".jpg": "image", ".jpeg": "image", ".tif": "image", ".tiff": "image"}


def _pdf_info(path: Path) -> dict:
    doc = fitz.open(path)
    pages = []
    for i, p in enumerate(doc):
        chars = len(p.get_text().strip())
        w_mm, h_mm = p.rect.width / 72 * 25.4, p.rect.height / 72 * 25.4
        tiles = max(1, round(p.rect.width / 72 * DETAIL_DPI / TILE_PX)) * max(1, round(p.rect.height / 72 * DETAIL_DPI / TILE_PX))
        pages.append({"page": i + 1, "text_chars": chars, "scan": chars < SCAN_CHARS_PER_PAGE,
                      "size_mm": [round(w_mm), round(h_mm)], "est_tiles": tiles})
    scan_ratio = sum(p["scan"] for p in pages) / max(1, len(pages))
    return {"format": "pdf_scan" if scan_ratio >= SCAN_PAGE_RATIO else "pdf_vector",
            "pages": len(pages), "scan_page_ratio": round(scan_ratio, 2), "page_info": pages,
            "est_tiles": sum(p["est_tiles"] for p in pages if p["scan"])}


def describe(path: Path) -> dict:
    ext = path.suffix.lower()
    entry = {"path": rel(path), "name": path.name, "bytes": path.stat().st_size}
    if ext == ".pdf":
        try:
            entry.update(_pdf_info(path))
            entry["readable"] = True
        except Exception as e:  # 손상·암호화
            entry.update({"format": "pdf", "readable": False, "error": str(e)})
    elif ext in EXT_FORMAT:
        entry.update({"format": EXT_FORMAT[ext], "readable": True})
    else:
        entry.update({"format": "unknown", "readable": False})
    return entry


def run(asset_id: str) -> dict:
    base = input_dir(asset_id)
    meta_path = base / "asset_meta.yaml"
    meta = load_yaml(meta_path) if meta_path.exists() else None

    im_files = [describe(p) for p in sorted((base / "im").glob("*")) if p.is_file()]
    dwg_files = [describe(p) for p in sorted((base / "drawings").glob("*")) if p.is_file()]

    escalations = []
    readable_im = [f for f in im_files if f.get("readable") and f["format"] in ("pdf_vector", "pdf_scan", "pptx", "docx")]
    if not readable_im:
        escalations.append({"code": "NO_IM", "message": "판독 가능한 IM이 없습니다. 진행 불가."})
    if not dwg_files:
        escalations.append({"code": "NO_DRAWINGS", "message": "도면이 없습니다. IM 단독 모드로 진행할지 확인이 필요합니다."})
    dwg_only = [f for f in dwg_files if f["format"] == "dwg"]
    if meta is None:
        escalations.append({"code": "NO_ASSET_META", "message": "asset_meta.yaml이 없습니다."})
    else:
        for k in ("asset_id", "address", "buildings"):
            if not meta.get(k):
                escalations.append({"code": "ASSET_META_FIELD", "message": f"asset_meta.yaml 필수 항목 누락: {k}"})

    inv = {
        "asset_id": asset_id,
        "created_at": now_iso(),
        "im": im_files,
        "drawings": dwg_files,
        "dwg_requests": [{"file": f["path"], "request": "벡터 PDF 출력본 요청"} for f in dwg_only],
        "mode": "정규" if any(f["format"] != "dwg" for f in dwg_files) else "IM 단독(확인 필요)",
        "est_vision_tiles": sum(f.get("est_tiles", 0) for f in dwg_files),
        "escalations": escalations,
    }
    save_json(wf2_dir(asset_id) / "w2_01_inventory.json", inv)
    return inv
