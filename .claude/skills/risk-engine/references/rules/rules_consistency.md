# E. 정합성·벤치마크 룰 — 3건

`scope: asset`. 입력 변수는 `lprisk/engine/consistency.py`가 만든다.

## V01. IM–도면 스펙 불일치

```yaml
id: V01
category: consistency
scope: asset
horizon: now
inputs: [v01.discrepancy_count, v01.overstated_count, v01.overstated_sensitive_count]
trigger: "v01.discrepancy_count > 0"
severity:
  red:    "v01.overstated_sensitive_count > 0"
  yellow: "v01.overstated_count > 0"
  green:  "otherwise"
on_missing: hold
llm_adjust: none
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 매도측 IM이 실제(도면·확정값)보다 유리한 스펙을 적었다. 다른 룰의 판정을 바꾸는 과장이면 IM 전체의 신뢰도와 가격 근거가 흔들린다.
- **연쇄 리스크:**
  - → 재무: IM 기준 가격·임대료 가정의 하향 조정
  - → 임대차: 임차인 요구 스펙 미충족 발견 시 분쟁
  - → 법률: 매매계약 진술·보장 조항 근거
- **DD 확인 포인트:**
  - 불일치 항목별 매도측 소명 요청
  - 진술·보장 조항에 핵심 스펙 명시
  - 판정을 바꾼 항목의 현장 실측

## V02. 핵심 스펙 미확인

```yaml
id: V02
category: consistency
scope: asset
horizon: now
inputs: [v02.unconfirmed_ratio]
trigger: "true"
severity:
  red:    "v02.unconfirmed_ratio >= th.v02_unconfirmed_ratio.red"
  yellow: "v02.unconfirmed_ratio >= th.v02_unconfirmed_ratio.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: none
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 룰 판정에 필요한 핵심 스펙이 상당 부분 확인되지 않아 스크리닝 결과의 커버리지가 낮다.
- **연쇄 리스크:**
  - → 재무: 미확인 항목의 잠재 CAPEX가 가격에 반영되지 않음
- **DD 확인 포인트:**
  - 추가 자료 요청 목록의 도면·자료 확보
  - 확보 불가 항목의 현장 실사 범위 포함

## B01. 동급 대비 스펙 열위

```yaml
id: B01
category: benchmark
scope: asset
horizon: now
inputs: [benchmark_available, benchmark.unruled_inferior_count]
trigger: "benchmark_available == true"
severity:
  yellow: "benchmark.unruled_inferior_count > 0"
  green:  "otherwise"
on_missing: hold
llm_adjust: none
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 절대 임계 룰이 없는 필드에서 동급 세그먼트 대비 하위 구간에 있다. 절대 임계 룰이 있는 필드의 벤치마크 위치는 해당 룰의 맥락으로만 표시한다(이중 집계 방지).
- **연쇄 리스크:**
  - → 재무: 임대료 경쟁력 열위
  - → 임대차: 재임대 시 공실 기간 증가
- **DD 확인 포인트:**
  - 열위 필드의 임차인 수요 영향
  - 비교 세그먼트의 표본 수와 판정 방식
