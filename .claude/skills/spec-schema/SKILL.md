---
name: spec-schema
description: Core Spec 스키마(동·층 구조)와 스펙 레코드 형식, 단위 정규화·검증, IM–도면 교차 대조(자동 확정·방향·판정 민감도), G2 확인 반영, 동별 프로파일. WF2 W2-②~⑥에서 쓴다.
---

# spec-schema

코드: `lprisk/spec/`, `lprisk/schema.py`

| 명령 | 설계서 스크립트 | 산출물 |
|---|---|---|
| `validate im\|drawing` | validate_spec.py + normalize_units.py | 검증 결과(errors/flags) |
| `reconcile` | reconcile_sources.py + compute_sensitivity.py + build_confirmation_sheet.py | `w2_04_reconciled.json`, `w2_04_confirmation_items.json`, `w2_04_hint_requests.json`, `w2_04_confirmation_sheet.md` |
| `apply-confirmation` | apply_confirmation.py | `w2_05_confirmed_spec.json`, `kb/extraction_log.csv`. 확인 항목 외에 **미발견 필드(`unresolved_missing`)도 `decisions`에 `correct`로 값을 줄 수 있다** — 도면 재확인값이면 `source_doc`·`source_locator`·`raw_text`·`method`(`vision`·`vector`)·`precision`을 함께 준다 |
| `profile` | build_profile.py | `w2_06_profile.json` |

참조 파일 (`references/`):
- `core_spec_schema.yaml` — 필드 정의, enum, 유리 방향(favor_order)
- `spec_record_format.md` — ValueObj·ClaimObj·MissingObj 형식
- `field_extraction_guide.md` — 필드별 탐색 순서·함정 (도크 수·트럭야드·지형 단차·기둥 간섭·램프 방향·회전반경 기준은 2026-10-14 bangchori 재확인에서 정함)
- `method: vector` — 벡터 PDF 좌표로 잰 값(도면 표기 아님). 프로파일이 `vector_slots`로 모으고, 그 값을 쓴 판정은 보고서에 📐벡터 측정으로 표시된다
- `tolerance.yaml` — 허용오차(abs/rel) — **수치 미확정(U13)**
- `profile_config.yaml` — 연식 구간, 온도대 분류, 패널 가연성 매핑
