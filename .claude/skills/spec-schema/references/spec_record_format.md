# 스펙 레코드 포맷

IM 주장값(`w2_02_im_claims.json`), 도면 추출값(`w2_03_drawing_specs.json`), 확정 스펙(`w2_05_confirmed_spec.json`), 골든 정답(`tests/golden/{asset}/golden_spec.json`)은 모두 같은 골격을 쓴다. 필드 정의는 `core_spec_schema.yaml`을 따른다.

## 골격

```json
{
  "asset_id": "cheongna",
  "record_type": "im_claims | drawing_specs | confirmed | golden_spec | golden_im_claims",
  "created_at": "2026-10-13T12:00:00+09:00",
  "asset":     { "<asset 필드 id>": [ValueObj, ...] },
  "buildings": [
    {
      "building_id": "main",
      "label": "청라로지스틱스센터",
      "phase": "원준공",
      "fields": { "<building 필드 id>": [ValueObj, ...] },
      "floors": [
        { "floor": "1F", "fields": { "use": [ValueObj], "floor_load_tpm2": [ValueObj] } }
      ]
    }
  ],
  "claims":  [ClaimObj, ...],
  "missing": [MissingObj, ...]
}
```

- 필드 값은 **항상 리스트**다. 추출 단계에서는 후보가 여럿일 수 있다(상충 기재 → 전부 기록, `conflict: true`). 확정 스펙·골든은 원소 1개다.
- `building_id`는 `asset_meta.yaml`의 `buildings[].id`를 쓴다. IM이 동 구분 없이 자산 단위로만 적었으면 `building_id: "_asset"`인 가상 building에 넣는다(`granularity: asset`).
- 층 라벨은 `B1`, `1F`, `2F`, …, `RF`, `M1F`(메자닌)로 정규화한다.
- 값을 찾지 못한 필드는 넣지 않는다(null 금지). 도면 추출에서는 대신 `missing`에 사유를 남긴다.

## ValueObj

```json
{
  "value": 1.5,
  "unit": "t/m2",
  "raw_text": "적재하중 1.5톤/㎡ 이상",
  "precision": "lower_bound",
  "source_doc": "input/cheongna/im/IM_Cheongna....pdf",
  "source_locator": { "page": 12, "sheet_no": null, "bbox": null, "crop": null },
  "method": "im_text",
  "confidence": "medium",
  "source_grade": "IM주장",
  "status": null,
  "conflict": false,
  "note": null
}
```

| 키 | 규칙 |
|----|------|
| value | 문서에 **적힌 값을 그대로 전사**. 계산·보간·추정 금지. 단위 환산은 `normalize_units.py`가 한다(전사 단계에서는 원 단위 유지 가능, `unit`에 원 단위 기재) |
| raw_text | 근거가 된 원문 구절(짧게) |
| precision | exact / approx('약') / lower_bound('이상') / upper_bound('이하') / rounded('약 3만평'처럼 반올림 단위) |
| source_locator.page | 1부터 시작하는 PDF 페이지 번호(DOCX는 문단 번호 또는 표 번호를 `para`/`table`로) |
| source_locator.bbox | 도면 판독 시 페이지 좌표 [x0,y0,x1,y1] (pt) |
| method | im_text / vision / vision_hinted / script / dxf / public_api / user / vector (벡터 PDF 좌표 측정 — 도면에 치수로 적힌 값이 아니라 선·원호 좌표로 잰 값. 사용자가 지시한 경우만 쓰고, 이 값으로 판정한 룰은 보고서에 📐벡터 측정으로 표시된다) |
| confidence | method별 기본값은 스크립트가 부여. 추출자는 근거가 약하면 낮출 수만 있음 |
| basis | (clear_height_m만) 측정 기준 — 배관 하단 / 천장 하단 / 보 하단 / 슬래브 하단. 보·슬래브 하단은 정규화에서 `precision: upper_bound`(실제 유효층고의 상한)가 된다 |

## ClaimObj (IM 서술형 주장)

```json
{ "type": "renovation | marketing | ownership | other",
  "building_id": "main", "field": "renovation_history",
  "text": "2024년 4~6층 대수선(쿠팡)", "quote": "원문 인용", "year": 2024,
  "source_doc": "...", "source_locator": {"page": 31} }
```

## MissingObj (도면 추출)

```json
{ "level": "floor", "building_id": "main", "floor": "3F", "field": "floor_load_tpm2",
  "missing_reason": "도면없음 | 미기재 | 판독불가", "searched": ["구조일반사항", "평면도"], "note": "..." }
```

## 골든 정답 추가 규칙

- `golden_spec.json`: 실사(PCA/DD) 보고서에서 확인한 값. `method: "user"`, `source_grade: "확정"`, `status: "확정"`. `source_doc`은 실사 보고서, `page`는 근거 페이지.
- `golden_im_claims.json`: IM에 실제로 적힌 값(정답 IM 추출 결과). im-analyst 정확도 측정용.
- 두 파일의 차이가 곧 V01(IM–실제 불일치) 테스트 케이스다.
- 실사 보고서에 없는 필드는 넣지 않는다. 사용자가 검토하며 추가·수정한다.
