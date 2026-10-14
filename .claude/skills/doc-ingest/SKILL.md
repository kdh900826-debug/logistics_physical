---
name: doc-ingest
description: 물류센터 IM·도면 파일 형식 처리 — 인벤토리·스캔 판정, IM 텍스트·표 추출(PDF/PPTX/DOCX), 도면 썸네일·표제란 분류 입력, 고해상도 타일, OCR 키워드 위치, 근거 크롭. WF2 W2-①~③에서 쓴다.
---

# doc-ingest

코드: `lprisk/doc_ingest/` · 실행: `python -m lprisk <명령> <asset_id>`

| 명령 | 설계서 스크립트 | 산출물 |
|---|---|---|
| `intake` | detect_format.py | `w2_01_inventory.json`, `session_state.json` |
| `extract-im-text` | extract_pdf_text.py / extract_pptx.py (+DOCX) | `w2_02_im_text.json`, `pages/*.png`(스캔 페이지) |
| `classify-sheets` | classify_sheets.py | `w2_03_sheet_index.json`, `thumbs/` |
| `tiles <sheet_id> [--dpi]` | rasterize_tiles.py | `tiles/<sheet_id>/r{row}c{col}.png`, `tiles.json` |
| `ocr <sheet_id> --fields a,b` | ocr_locate.py | 키워드 좌표. 벡터 PDF는 텍스트 레이어로 찾는다(`source: text_layer`), 스캔 장은 Tesseract(없으면 `available: false`) |
| `text-search --pattern <정규식>` | ocr_locate.text_search | 도면 PDF 전체 텍스트 레이어 검색(파일·페이지·좌표). 판독 전 탐색과 '도면 미기재' 재확인에 쓴다. 스캔 전용 파일은 `scan_only_files` |
| `vector-radius --file <PDF> --page <n> [--scale mm/pt]` | vector_measure.py | 램프 원 중심(W.P 등)~차로면 내측 원호 반경(벡터 좌표 측정). `vector_measure_*.json`의 `suggested`를 `method: vector`로 기록 → G2·보고서 📐 표시 |
| `crop --file --page --bbox --name` / `crop-all` | crop_evidence.py | `crops/*.png`, `source_locator.crop` |

참조: `references/drawing_types.md`(분류 기준), `references/ocr_keywords.yaml`.
DWG는 처리하지 않는다 — 인벤토리의 `dwg_requests`로 "벡터 PDF 출력본 요청".
