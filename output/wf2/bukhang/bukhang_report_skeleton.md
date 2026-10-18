# [그레이트원창 북항물류센터] 물리적 리스크 분석 보고서

> 분석 모드: 정규 · 기준일: 미입력(실행일 기준) · 보유기간: 미입력(exit 평가 생략)
> 룰셋: ruleset-untagged@7fb5838 · 임계값 검증: 참조 9건 중 verified 9건 · 벤치마크: 미적용 · 입지 조회: 미조회
> 한계: 본 보고서는 IM과 도면 기반의 스크리닝 결과이며 PCA·현장 실사를 대체하지 않는다. ⚪ 판정 보류 항목은 '정상'이 아니라 입력이 확인되지 않아 평가하지 않은 항목이다.

## 0. 요약 대시보드

| 🔴 | 🟡 | 🟢 | ⚪ 판정 보류 | 미발동 |
|---|---|---|---|---|
| 3 | 0 | 8 | 19 | 2 |

- 등급 정책: 단일 등급 — 🔴·🟡 구분 없이 발동은 모두 🔴 (severity_policy.yaml)
- 검증 입력 기준: 🔴 3 · 🟡 0 · 🟢 8 · ⚪ 19 / †IM 기준(주장값 포함): 🔴 0 · 🟡 0 · ⚪ 0
- 보유 중 심각도 상승 예정: 0건
- IM–도면 불일치: 0건 (IM 과장 0 · IM 보수 0 · 방향 없음 0)
- 스펙 확정 현황: 확정 81

**우선 확인 Top 3** (정렬: 심각도 → V01 연관 → 상관관계 연결 수 → 카테고리 우선순위)

1. 🔴 **FR04** 저온동 단열재 화재 [main] — <!-- LLM:top3_1 -->
2. 🔴 **CL04** 온도대 전환 유연성 [main] — <!-- LLM:top3_2 -->
3. 🔴 **SP02** 유효층고 미달 [main] — <!-- LLM:top3_3 -->

<!-- LLM:summary -->

## 1. 자산 프로파일

### 물류센터 (주건축물) [main]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 저온동 단열재 두께 | 150.0mm | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 45, sheet_no A-181 [근거](output/wf2/bukhang/crops/building_main_x_cold_insulation_thickness_mm_0.png) |
| 저온동 단열재 종류 | 우레탄 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 45, sheet_no A-181 [근거](output/wf2/bukhang/crops/building_main_x_cold_insulation_material_0.png) |
| 기둥 스팬(장변) | 11.0m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 96, sheet_no A-302 [근거](output/wf2/bukhang/crops/building_main_x_column_span_x_m_0.png) |
| 기둥 스팬(단변) | 11.0m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 96, sheet_no A-302 [근거](output/wf2/bukhang/crops/building_main_x_column_span_y_m_0.png) |
| 도크 수 | 192 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 22, sheet_no A-131 [근거](output/wf2/bukhang/crops/building_main_x_dock_count_0.png) |
| 도크레벨러 수 | 16 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 188, sheet_no A-731 [근거](output/wf2/bukhang/crops/building_main_x_dock_leveler_count_0.png) |
| 방화구획 최대 면적 | 1,925.27㎡ | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 29, sheet_no A-152 [근거](output/wf2/bukhang/crops/building_main_x_fire_compartment_max_m2_0.png) |
| 지상층수 | 10층 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/building_main_x_floors_above_0.png) |
| 지하층수 | 1층 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/building_main_x_floors_below_0.png) |
| 화물용 승강기 대수 | 0 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 26, sheet_no A-141 [근거](output/wf2/bukhang/crops/building_main_x_freight_elevator_count_0.png) |
| 연면적 | 111,934.06㎡ | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/building_main_x_gross_floor_area_m2_0.png) |
| 램프 형상 | 나선형 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 98, sheet_no A-304 [근거](output/wf2/bukhang/crops/building_main_x_ramp_form_0.png) |
| 램프 통행 방향 | 양방향 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 23, sheet_no A-132 [근거](output/wf2/bukhang/crops/building_main_x_ramp_type_0.png) |
| 램프 폭 | 14.0m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 13, sheet_no A-108 [근거](output/wf2/bukhang/crops/building_main_x_ramp_width_m_0.png) |
| 구조형식 | 복합 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/building_main_x_structure_type_0.png) |
| 지형 단차 진입도로로 여러 층 직접 접안 | 없음 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 10, sheet_no A-105 [근거](output/wf2/bukhang/crops/building_main_x_terrain_multi_level_access_0.png) |
| 대형차 최소 회전반경(램프·하역장 동선) | 12.0m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 13, sheet_no A-108 [근거](output/wf2/bukhang/crops/building_main_x_turning_radius_m_0.png) |
| 외벽 패널 심재 | 글라스울 | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 107, sheet_no A-321 [근거](output/wf2/bukhang/crops/building_main_x_wall_panel_core_0.png) |
| 창고 내부 깊이(하역장 측 벽~반대편 벽) | 53.6m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 171, sheet_no A-601 [근거](output/wf2/bukhang/crops/building_main_x_warehouse_depth_m_0.png) |

| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |
|---|---|---|---|---|---|
| B1 | 기계 | 1,377.11㎡ | — | — | — |
| 1F | 창고 | 13,343.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 2F | 사무 | 2,036.97㎡ | — | 2.4m | — |
| 3F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 4F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 5F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 6F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 7F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 8F | 창고 | 13,316.91㎡ | — | ≤8.55m (보 하단) | 있음 |
| 9F | 창고 | 13,316.91㎡ | — | ≤8.35m (보 하단) | 있음 |
| 10F | 사무 | 1,982.88㎡ | — | — | — |

### 경비동 (부속건축물) [guard]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 연면적 | 25.18㎡ | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/building_guard_x_gross_floor_area_m2_0.png) |

### 단지 공용

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 대지면적 | 27,351.5㎡ | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 6, sheet_no A-101 [근거](output/wf2/bukhang/crops/asset_x_x_site_area_m2_0.png) |
| 트럭야드 깊이 | 13.0m | 확정 | 건축도면 - 인천 서구 그레이트원창 북항물류센터_2 · page 178, sheet_no A-702 [근거](output/wf2/bukhang/crops/asset_x_x_truck_yard_depth_m_0.png) |

## 2. 스펙 경쟁력 — 벤치마크 포지셔닝

벤치마크 미적용 — WF1 벤치마크 DB가 아직 없다(구현 3단계).

## 3. IM–도면 정합성

| 항목 | IM 기재 | 도면 | 확정값 | 방향 |
|---|---|---|---|---|
| 불일치 없음 | | | | |

<!-- LLM:consistency -->

## 4. 입지 리스크

입지 조회 미실행 — 입지 룰(LC)은 구현 2단계에서 추가된다.

## 5. 리스크 평가 결과

### 🔴 CL04. 온도대 전환 유연성 [main]

- **판정 입력:** has_cold=있음, refrigerant=—
- **추론 근거:** <!-- LLM:basis:CL04@main -->
- **근본 원인:** <!-- LLM:root:CL04@main -->
- **연쇄 리스크:** <!-- LLM:cascade:CL04@main -->
- **DD 확인 포인트:** <!-- LLM:dd:CL04@main -->

### 🔴 FR04. 저온동 단열재 화재 [main]

- **판정 입력:** cold_insulation_combustibility=난연, cold_ratio=—, has_cold=있음
- **추론 근거:** <!-- LLM:basis:FR04@main -->
- **근본 원인:** <!-- LLM:root:FR04@main -->
- **연쇄 리스크:** <!-- LLM:cascade:FR04@main -->
- **DD 확인 포인트:** <!-- LLM:dd:FR04@main -->

### 🔴 SP02. 유효층고 미달 [main]

- **판정 입력:** warehouse_floors.clear_height_m=[9F ≤8.35 (보 하단); 1F ≤8.55 (보 하단); 3F ≤8.55 (보 하단); 4F ≤8.55 (보 하단); 5F ≤8.55 (보 하단); 6F ≤8.55 (보 하단); 7F ≤8.55 (보 하단); 8F ≤8.55 (보 하단)]
- **적용 임계값:** clear_height.yellow=8.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP02@main -->
- **근본 원인:** <!-- LLM:root:SP02@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP02@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP02@main -->

### 🟢 FR02. 방화구획 대면적 [main]

- **판정 입력:** fire_compartment_max_m2=1,925.27
- **적용 임계값:** fire_compartment_area.yellow=3000 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR02@main -->

### 🟢 FR03. 스프링클러 형식 부적합 [main]

- **판정 입력:** sprinkler_type=—, warehouse_floors.clear_height_m.max=8.55
- **적용 임계값:** sprinkler_esfr_clear_height.red=13.7 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR03@main -->

### 🟢 FR05. 창고 내부 깊이 과대 (소방대 진입 거리) [main]

- **판정 입력:** warehouse_depth_m=53.6
- **적용 임계값:** warehouse_depth.red=77 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR05@main -->

### 🟢 SP03. 기둥 스팬·랙 효율 [main]

- **판정 입력:** column_span_x_m=11.0, column_span_y_m=11.0
- **적용 임계값:** column_span.yellow=11.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP03@main -->

### 🟢 SP04. 도크 부족 [main]

- **판정 입력:** dock_density=56.7
- **적용 임계값:** dock_density.red=50 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP04@main -->

### 🟢 SP06. 트럭야드 협소 [main]

- **판정 입력:** truck_yard_depth_m=13.0
- **적용 임계값:** truck_yard_depth.red=13 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP06@main -->

### 🟢 SP07. 수직반송 의존 [main]

- **판정 입력:** handling_type=다층 램프형
- **추론 근거:** <!-- LLM:basis:SP07@main -->

### 🟢 SP08. 대형차 회전반경 부족 [main]

- **판정 입력:** turning_radius_m=12.0
- **적용 임계값:** turning_radius.red=12.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP08@main -->

### ⚪ CL01. 냉동설비·냉매 리스크 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 냉매 종류 (main)
- **판정 입력:** building_age=—, has_cold=있음, refrigerant=—
- **DD 확인 포인트:** 미확인 입력 확보; 냉동기 형식·냉매 종류(기계 냉동도면 또는 고압가스 허가증) — ⚪ 해소; 냉동설비 소유(임대인/임차인)와 교체·원상복구 책임; 냉동기계실(2F·3~9F)별 압축기 운전시간·오버홀 이력; 사용승인일 확인 — building_age 산정

### ⚪ CL02. 바닥 동상 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 저온동 바닥 동상 방지 설비 (main)
- **판정 입력:** cold_floor_heave_protection=—, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; 1F 저온창고 바닥 상세(구조·기계)의 동상 방지 히팅·환기관 유무 — ⚪ 해소; 1F 바닥 하부가 지반인 범위(B1 상부 여부); 1F 바닥 레벨 측정·균열 조사 결과

### ⚪ CL03. 단열 패널 열화·결로 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 외벽·천장 우레탄 뿜칠면 균열·박리·결로 흔적; 도크 OHD·도크씰·방열문 기밀 상태; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ FR01. 패널 심재 가연성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 지붕 패널 심재 (main)
- **판정 입력:** panel_combustibility=불연, roof_panel_combustibility=—
- **DD 확인 포인트:** 미확인 입력 확보; 지붕 구성이 RC 슬래브뿐이고 샌드위치 패널 구간(사무동 지붕·캐노피 등)이 없는지 확인 — G2에서 확정하면 ⚪ 해소; 외벽 글라스울 패널 시험성적서·납품서; 증축·보수 구간 심재 혼재 여부

### ⚪ FR06. 오버헤드도어 하부 살수장애 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 오버헤드도어 하부 스프링클러 살수장애(헤드 미설치) (main)
- **판정 입력:** ohd_sprinkler_gap=—
- **DD 확인 포인트:** 미확인 입력 확보; 소방 평면도의 OHD 하부(문 안쪽) 헤드 유무 — ⚪ 해소; 준공 후 소방 점검·임차인 Fire Audit 지적과 보완 여부(층별); 저온 도크·유니트쿨러 주변 미경계구역(드라이펜던트 헤드)

### ⚪ G01. 배관 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일(건축물대장) 확인 — building_age 산정으로 ⚪ 해소; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소; 기계(위생·소화·냉매) 배관 도면 확보 — 이번 PDF는 건축도면만 수록; 저온창고 구간 배관 보온 상태·결로 흔적과 누수 이력

### ⚪ G02. 수변전설비 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 수전 계약전력·변압기 구성(단선결선도) 확보와 최대수요전력 대비 여유율; 저온 전용 변압기 유무와 부하율; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G03. 화물용 승강기·수직반송기 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 수직반송기 대수 (main)
- **판정 입력:** freight_elevator_count=0, vrc_count=—
- **DD 확인 포인트:** 미확인 입력 확보; 수직반송기 유무·대수 — 없으면 G2에서 0으로 확정해 ⚪ 해소; 수직반송기 소유(vrc_owner)와 원상복구 조건; 비상용 승강기 6대의 화물 운반 겸용 여부와 고장 이력

### ⚪ G04. 비상발전기 신뢰성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 비상발전기 용량과 부하 범위(소방 전용 / 냉동 부하 포함); 부하운전 시험 기록·연료 보유량; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G05. 스프링클러·제연 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 소방(스프링클러·제연) 도면 확보 — 층별 헤드 형식·면제 구역; 최근 소방 종합정밀점검 결과와 지적 보완 여부; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G06. 지붕 방수·배수 열화 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 옥상주차장 방수층 종류·보수 이력과 배수 드레인(열선 포함) 상태; 9F 저온창고 천장 누수·결빙 흔적; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G07. 야드·램프 포장 열화 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 램프·화물주차장 바닥 균열·신축이음부 상태와 보수 이력; 램프 열선(결빙 방지) 설비 유무; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G08. 석면 함유 가능성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** regulation_flags.asbestos_total_ban_2009=—
- **DD 확인 포인트:** 미확인 입력 확보; 건축물대장 사용승인일 확인 — ⚪ 해소

### ⚪ G09. 법규 적합성·용도변경 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 건축물대장 위반건축물 표기·용도 변경 이력; 온도대 전환 시 대수선 인허가에서 요구될 현행 기준 항목; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ G10. CapEx 종합 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확인 — ⚪ 해소; 설비별(냉동·수변전·소방·승강기) 장기수선계획과 교체 이력; 설비 소유 구분(냉동설비·도크설비·랙·수직반송기 모두 미확인) — 임대인 CAPEX 범위 확정; 보유기간(holding_years) 입력 — 매각 시점 판정 ⚪ 해소

### ⚪ SP01. 바닥하중 미달 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 바닥 설계하중 (main 1F), 바닥 설계하중 (main 3F), 바닥 설계하중 (main 4F), 바닥 설계하중 (main 5F), 바닥 설계하중 (main 6F), 바닥 설계하중 (main 7F), 바닥 설계하중 (main 8F), 바닥 설계하중 (main 9F)
- **판정 입력:** warehouse_floors.floor_load_tpm2.min=—
- **DD 확인 포인트:** 미확인 입력 확보; 구조일반사항 설계하중표의 층별 값(구조도면 확보) — ⚪ 해소; 1F(지반 위)와 3F~9F(슬래브) 하중 차이; 바닥 균열·처짐 흔적

### ⚪ SP05. 램프·차량 접근 제약 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 램프 경사 (main)
- **판정 입력:** floors_above=10, ramp_slope_pct=—, ramp_type=양방향, ramp_width_m=14.0
- **적용 임계값:** ramp_width.red=7.5 (ramp_type=양방향, 검증)
- **DD 확인 포인트:** 미확인 입력 확보; 램프 상세도(A-1201~A-1208) 확보 — 직선·곡선부 경사로 ⚪ 해소; 곡선부 회전반경과 40FT·세미트레일러 교행 가능 여부; 램프 열선(결빙 방지) 설비

### ⚪ SP09. 하역 동선 기둥 간섭 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 램프→하역장 동선 기둥 간섭(대형차) (main 3F), 램프→하역장 동선 기둥 간섭(대형차) (main 4F), 램프→하역장 동선 기둥 간섭(대형차) (main 5F), 램프→하역장 동선 기둥 간섭(대형차) (main 6F), 램프→하역장 동선 기둥 간섭(대형차) (main 7F), 램프→하역장 동선 기둥 간섭(대형차) (main 8F), 램프→하역장 동선 기둥 간섭(대형차) (main 9F)
- **판정 입력:** floors_with_dock_column_conflict=—
- **DD 확인 포인트:** 미확인 입력 확보; 3F~9F 램프 착지부→차로 진입부의 40FT 회전 궤적(Y8 기둥·CORE#1 간섭 여부) — ⚪ 해소; 층별 임차인 차량 구성(40FT·세미트레일러 비중); 기둥보호대·유도 설비 설치 여부

### ⚪ V02. 핵심 스펙 미확인

- **판정 보류 사유:** 임계값 미정 — 미확인 입력: thresholds.yaml: V02 red/yellow
- **판정 입력:** v02.unconfirmed_ratio=0.4
- **DD 확인 포인트:** 미확인 입력 확보; 구조·기계(냉동·소화)·전기 도면과 건축물대장 확보 — 미확인 12개 중 대부분 해소; IM 또는 매도자 자료로 저온 면적·설비 소유 구분 확인; V02 임계값 결정(리뷰 서버 /thresholds)

## 6. 리스크 상관관계

- 상관관계 맵에 정의된 관계 중 양쪽이 모두 활성인 쌍이 없다.

## 7. DD 체크리스트

판정 보류(⚪) 항목을 먼저, 미확인 사유별로 묶었다. 자료 요청은 `bukhang_data_request.md` 참조.

<!-- LLM:dd_checklist -->

## 부록 A. 필드별 추출 근거

§1 표의 출처 열과 `w2_05_confirmed_spec.json` 참조. 도면 판독값은 [근거] 링크로 크롭 이미지를 연다.

## 부록 B. 미검증 연쇄 제안

- 없음

## 갱신 이력

| 일시 | 변경 사유 | 재진입 지점 |
|---|---|---|
| 2026-10-18T18:52:53+09:00 | [유효층고 clear_height_m (main 1F·3F~9F)] 측정 기준 보 하단(A-601 확대단면도-1, p171) 반영 — 배관 미반영 상한값. 값은 그대로 — 채팅 지시 | W2-⑤ |
