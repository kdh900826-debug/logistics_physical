"""OCR 키워드 좌표 탐색 (설계서 §3.6). 값 채택에는 쓰지 않는다.

OCR 엔진(Tesseract + kor 언어팩, pytesseract)이 없으면 available=False를 반환하고,
drawing-extractor는 해당 도면 전체 타일을 판독한다.
"""
from __future__ import annotations

import shutil

import fitz

from ..io import load_json, load_yaml
from ..paths import INGEST_REFS, ROOT, wf2_dir


def available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def locate(asset_id: str, sheet_id: str, fields: list[str], dpi: int = 200) -> dict:
    kw = load_yaml(INGEST_REFS / "ocr_keywords.yaml")["keywords"]
    targets = {f: kw.get(f, []) for f in fields}
    idx = load_json(wf2_dir(asset_id) / "w2_03_sheet_index.json")
    sh = next(s for s in idx["sheets"] if s["sheet_id"] == sheet_id)
    page = fitz.open(ROOT / sh["file"])[sh["page"] - 1]
    words = page.get_text("words")
    if words:     # 벡터 PDF: 텍스트 레이어 좌표가 OCR보다 정확하다
        hits = [{"field": f, "word": w[4], "bbox_pt": [round(x, 1) for x in w[:4]], "source": "text_layer"}
                for w in words for f, ks in targets.items() if any(k.lower() in w[4].lower() for k in ks)]
        return {"available": True, "source": "text_layer", "hits": hits}
    if not available():
        return {"available": False, "hits": [], "note": "OCR 엔진 없음 — 전체 타일 판독"}
    import pytesseract
    from PIL import Image

    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    data = pytesseract.image_to_data(img, lang="kor+eng", output_type=pytesseract.Output.DICT)
    scale = 72 / dpi
    hits = []
    for i, word in enumerate(data["text"]):
        w = (word or "").strip()
        if not w:
            continue
        for field, words in targets.items():
            if any(k.lower() in w.lower() for k in words):
                x, y, ww, hh = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                hits.append({"field": field, "word": w,
                             "bbox_pt": [round(x * scale, 1), round(y * scale, 1),
                                         round((x + ww) * scale, 1), round((y + hh) * scale, 1)]})
    return {"available": True, "hits": hits}


def text_search(asset_id: str, pattern: str) -> dict:
    """도면 PDF 전체의 텍스트 레이어에서 정규식 검색 (벡터 PDF만 해당, 스캔 장은 건너뜀).

    판독 전 탐색·'도면 미기재' 재확인용. 결과 좌표는 페이지 pt.
    """
    import re
    rx = re.compile(pattern, re.I)
    hits, no_text = [], []
    for f in sorted((ROOT / "input" / asset_id / "drawings").glob("*.pdf")):
        doc = fitz.open(f)
        rel = f.relative_to(ROOT).as_posix()
        if not any(p.get_text().strip() for p in doc):
            no_text.append(rel)
            continue
        for i, p in enumerate(doc):
            for b in p.get_text("blocks"):
                t = " ".join(b[4].split())
                if rx.search(t):
                    hits.append({"file": rel, "page": i + 1, "bbox_pt": [round(x, 1) for x in b[:4]], "text": t[:300]})
    return {"pattern": pattern, "hits": hits, "scan_only_files": no_text}
