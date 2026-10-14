# A. 연식 기반 룰 (v1 이식·조정) — 10건

공통: `scope: per_building`, `horizon: both` (현재 연식과 보유기간 말 연식으로 각각 평가).
임계값은 `thresholds.yaml`의 `aging.*` 키를 쓴다. 연식 기준값은 v1 오피스 엔진에서 옮겨 온 것이라 물류센터 근거로 다시 검증해야 한다.

## G01. 배관 노후

```yaml
id: G01
category: aging
scope: per_building
horizon: both
inputs: [building_age, has_cold]
trigger: "true"
severity:
  red:    "building_age >= th.aging_piping.red"
  yellow: "building_age >= th.aging_piping.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 급수·소화·냉매 배관의 부식과 이음부 열화가 연식에 비례해 진행된다. 저온동은 결로로 외부 부식이 빠르다.
- **연쇄 리스크:**
  - → 재무: 배관 교체·보수 CAPEX, 누수 피해 복구비
  - → 임대차: 누수로 인한 화물 손상 클레임, 임차인 운영 중단
  - → 법률: 소화배관 누수 시 소방 점검 지적
- **DD 확인 포인트:**
  - 배관 교체 이력과 누수 보수 기록
  - 저온동 결로 배관 보온 상태
  - 소화배관 압력 유지 상태(충압펌프 기동 빈도)

## G02. 수변전설비 노후

```yaml
id: G02
category: aging
scope: per_building
horizon: both
inputs: [building_age, cold_ratio]
trigger: "true"
severity:
  red:    "building_age >= th.aging_substation.red"
  yellow: "building_age >= th.aging_substation.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 변압기·차단기·보호계전기의 절연 열화. 저온 비율이 높으면 상시 부하가 커서 열화가 빠르고 증설 여유가 작다.
- **연쇄 리스크:**
  - → 재무: 변압기·배전반 교체 CAPEX
  - → 임대차: 정전 시 저온 화물 손상, 임차인 전력 증설 요구 대응 불가
  - → 법률: 전기안전 정기검사 지적
- **DD 확인 포인트:**
  - 변압기 제조연도·절연유 분석 결과
  - 수전 용량 대비 최대수요전력(부하 여유율)
  - 임차인 전용 증설 설비의 소유·원상복구 조건
  - 전용 변압기(스노우멜팅·냉동) 부하율과 증설 여유 — 사례: 송온리 1센터 스노우멜팅 전용 500kVA 부하율 95% 초과(golden songon1)

## G03. 화물용 승강기·수직반송기 노후

```yaml
id: G03
category: aging
scope: per_building
horizon: both
inputs: [building_age, freight_elevator_count, vrc_count, handling_type]
trigger: "freight_elevator_count > 0 or vrc_count > 0"
severity:
  red:    "building_age >= th.aging_elevator.red"
  yellow: "building_age >= th.aging_elevator.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 권상기·제어반·로프의 마모. 다층 승강기형은 수직 동선이 승강기에 집중되어 고장 시 층 전체 운영이 멈춘다.
- **연쇄 리스크:**
  - → 재무: 제어반·권상기 교체(현대화) CAPEX
  - → 임대차: 상층부 임대 경쟁력 저하, 처리량 병목
  - → 법률: 승강기 안전검사 불합격 시 운행 정지
- **DD 확인 포인트:**
  - 승강기·수직반송기 제조연도와 정밀안전검사 결과
  - 유지보수 계약과 고장 이력
  - 수직반송기 소유(임차인 설치 여부)
  - 화물용 승강기가 없으면 임차인이 승객용을 화물용으로 쓰는지, 고장 이력 — 사례: 송온리 1센터(golden songon1)

## G04. 비상발전기 신뢰성

```yaml
id: G04
category: aging
scope: per_building
horizon: both
inputs: [building_age, has_cold]
trigger: "true"
severity:
  red:    "building_age >= th.aging_generator.red"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 발전기 기동 신뢰성 저하와 용량 부족. 저온동은 정전 시 냉동설비가 멈추면 화물 손상으로 바로 이어진다(저온동이면 LLM 상향 검토). 연면적 기준 적용 대상 판단은 출처가 없어 제거했다 — 물류센터는 소방 비상전원 대상인 경우가 대부분이다.
- **연쇄 리스크:**
  - → 재무: 발전기 교체·증설 CAPEX
  - → 임대차: 정전 시 저온 화물 손상 배상, 임차인 이탈
  - → 법률: 소방·비상전원 기준 미달 지적
- **DD 확인 포인트:**
  - 발전기 용량과 냉동설비 비상부하 포함 여부
  - 부하 운전 시험 기록
  - 임차인 자체 발전기 유무

## G05. 스프링클러·제연 노후

```yaml
id: G05
category: aging
scope: per_building
horizon: both
inputs: [building_age]
trigger: "true"
severity:
  red:    "building_age >= th.aging_fire_system.red"
  yellow: "building_age >= th.aging_fire_system.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 소화배관 부식, 헤드·밸브 작동 불량, 제연 댐퍼 고착.
- **연쇄 리스크:**
  - → 재무: 소화설비 보수 CAPEX, 화재보험료 상승
  - → 임대차: 화재 시 운영 중단
  - → 법률: 소방 종합정밀점검 지적·시정명령
- **DD 확인 포인트:**
  - 최근 종합정밀점검 지적사항과 시정 여부
  - 헤드 교체 이력, 배관 부식 상태
  - 제연설비 작동 시험 기록
  - 준공 직후 소방 종합정밀점검·임차인 Fire Audit 지적(스프링클러 배관 누수, 감지기 불량, 출입문 개방 시 살수장애) — 사례: 송온리 1센터 준공 2개월 점검 지적 40건(golden songon1)

## G06. 지붕 방수·배수 열화

```yaml
id: G06
category: aging
scope: per_building
horizon: both
inputs: [building_age, solar_installed, roof_area_m2]
trigger: "true"
severity:
  red:    "building_age >= th.aging_roof.red"
  yellow: "building_age >= th.aging_roof.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 2
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 대면적 평지붕은 방수층 열화와 배수 불량이 누수로 이어지기 쉽다. 태양광이 있으면 방수 보수 때 패널 철거가 필요하다.
- **연쇄 리스크:**
  - → 재무: 방수 재시공 CAPEX(태양광 철거·재설치 포함)
  - → 임대차: 누수로 인한 화물 손상, 임차인 클레임
  - → 법률: 지붕 태양광 임대차(제3자 소유) 시 철거 협의
- **DD 확인 포인트:**
  - 방수 재시공 이력(IM 주장은 증빙 확인 후에만 반영)
  - 누수 흔적과 루프드레인 상태
  - 운영 중 누수 사고보고서·하자 처리 내역(특히 준공 후 첫 겨울·첫 장마). 같은 부위 재발 여부
  - 거터·선홈통 결빙 대책(열선, 오버플로·우회 배수, 우수관 고정)과 램프-건물 접합부·판넬 이음부 후레싱 — 사례: 송온리 2센터는 준공 후 약 7개월 사이 누수 사고 4건(첫 겨울 선홈통 결빙 역류·램프 판넬 누수 2건, 장마철 램프 기둥·판넬 누수 2건 — 보수 후에도 재발, golden songon incidents.yaml). 모두 DD가 미리 지적한 부위
  - 태양광 소유·임대 계약 조건(철거·복구 책임)

## G07. 야드·램프 포장 열화

```yaml
id: G07
category: aging
scope: per_building
horizon: both
inputs: [building_age, ramp_type, ramp_slope_pct]
trigger: "true"
severity:
  red:    "building_age >= th.aging_pavement.red"
  yellow: "building_age >= th.aging_pavement.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 2
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 대형 화물차 반복 하중과 제동으로 하역장·주행로·램프 바닥 콘크리트가 균열·박리된다. 램프 경사가 크면 더 빠르다.
- **연쇄 리스크:**
  - → 재무: 바닥 보수·재포장 CAPEX
  - → 임대차: 보수 중 동선 차단으로 운영 차질
  - → 법률: 차량 사고 시 시설 관리 책임
- **DD 확인 포인트:**
  - 하역장·램프 바닥 균열과 박리 범위
  - 램프 신축이음·배수 상태
  - 보수 이력과 하자보수 기간 잔여 여부
  - 지형 단차 접안 부지(다층 지형접안형): 옹벽·지하구조물과 성토 지반 면접부의 부등침하, 측구 균열로 빗물이 포장 하부로 들어가 침하가 반복되는지, 진입도로 경사·결빙 — 사례: 현방 A동 4층 남측 주차장(golden hyeonbang p9)

## G08. 석면 함유 가능성

```yaml
id: G08
category: aging
scope: per_building
horizon: now
inputs: [completion_year, regulation_flags.asbestos_total_ban_2009]
trigger: "true"
severity:
  red:    "regulation_flags.asbestos_total_ban_2009 == true"
  green:  "otherwise"
on_missing: hold
llm_adjust: none
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 석면 사용 전면 금지(regulation_timeline `asbestos_total_ban_2009`) 이전에 준공된 건물은 마감재·단열재에 석면이 남아 있을 수 있다.
- **연쇄 리스크:**
  - → 재무: 석면 조사·해체 비용
  - → 임대차: 리모델링 시 공사 기간 증가
  - → 법률: 석면안전관리법상 조사·관리 의무
- **DD 확인 포인트:**
  - 석면 조사 보고서 유무
  - 석면 함유 자재 위치와 관리 상태

## G09. 법규 적합성·용도변경

```yaml
id: G09
category: aging
scope: per_building
horizon: both
inputs: [building_age]
trigger: "true"
severity:
  yellow: "building_age >= th.aging_compliance.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 준공 후 강화된 소방·건축 기준과 현황의 차이, 용도변경(창고↔공장, 저온↔상온 전환) 과정의 인허가 누락.
- **연쇄 리스크:**
  - → 재무: 기준 충족 보강 공사비
  - → 임대차: 용도 제한으로 임차인 업종 제약
  - → 법률: 위반건축물 등재, 이행강제금
- **DD 확인 포인트:**
  - 건축물대장 위반 사항과 용도
  - 대수선·용도변경 허가 이력(전환 공사 포함)
  - 소방 완공필증과 현황 일치 여부

## G10. CapEx 종합

```yaml
id: G10
category: aging
scope: per_building
horizon: both
inputs: [building_age]
trigger: "true"
severity:
  red:    "building_age >= th.aging_capex.red"
  yellow: "building_age >= th.aging_capex.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 주요 설비의 내용연수가 비슷한 시기에 도래해 CAPEX가 한꺼번에 몰린다.
- **연쇄 리스크:**
  - → 재무: 보유기간 중 CAPEX 집중, 배당 재원 감소
  - → 임대차: 대규모 교체 공사 중 운영 차질
- **DD 확인 포인트:**
  - PCA 장기 CAPEX 계획표(연도별)
  - 설비별 내용연수 도래 시점
  - 매도인 하자보수 보증 잔여 기간
