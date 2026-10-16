# [이천 송온리 우석 물류센터] 물리적 리스크 분석 보고서

> 분석 모드: 정규 · 기준일: 미입력(실행일 기준) · 보유기간: 미입력(exit 평가 생략)
> 룰셋: ruleset-untagged@338c97e · 임계값 검증: 참조 9건 중 verified 9건 · 벤치마크: 미적용 · 입지 조회: 미조회
> 한계: 본 보고서는 IM과 도면 기반의 스크리닝 결과이며 PCA·현장 실사를 대체하지 않는다. ⚪ 판정 보류 항목은 '정상'이 아니라 입력이 확인되지 않아 평가하지 않은 항목이다.

## 0. 요약 대시보드

| 🔴 | 🟡 | 🟢 | ⚪ 판정 보류 | 미발동 |
|---|---|---|---|---|
| 5 | 0 | 6 | 19 | 2 |

- 등급 정책: 단일 등급 — 🔴·🟡 구분 없이 발동은 모두 🔴 (severity_policy.yaml)
- 검증 입력 기준: 🔴 5 · 🟡 0 · 🟢 6 · ⚪ 19 / †IM 기준(주장값 포함): 🔴 0 · 🟡 0 · ⚪ 0
- 보유 중 심각도 상승 예정: 0건
- IM–도면 불일치: 0건 (IM 과장 0 · IM 보수 0 · 방향 없음 0)
- 스펙 확정 현황: 확정 49

**우선 확인 Top 3** (정렬: 심각도 → V01 연관 → 상관관계 연결 수 → 카테고리 우선순위)

1. 🔴 **FR01** 패널 심재 가연성 [main] — <!-- LLM:top3_1 -->
2. 🔴 **FR04** 저온동 단열재 화재 [main] — <!-- LLM:top3_2 -->
3. 🔴 **SP02** 유효층고 미달 [main] — <!-- LLM:top3_3 -->

<!-- LLM:summary -->

## 1. 자산 프로파일

### 가동 (창고동) [main]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 냉동설비 형식 | 반밀폐형 스크류식(수냉식) CDU + 유닛쿨러, R-404A | 확정 | 8-1설비-냉동.pdf · page 3, sheet_no MR-002 [근거](output/wf2/songon1/crops/building_main_x_refrigeration_system_0.png) |
| 저온동 단열재 종류 | 우레탄 | 확정 | 1-1.건축.pdf · page 98, sheet_no A-511 [근거](output/wf2/songon1/crops/building_main_x_cold_insulation_material_0.png) |
| 기둥 스팬(장변) | 11.0m | 확정 | 1-1.건축.pdf · page 6, sheet_no A-102 [근거](output/wf2/songon1/crops/building_main_x_column_span_x_m_0.png) |
| 기둥 스팬(단변) | 11.0m | 확정 | 1-1.건축.pdf · page 62, sheet_no A-401 [근거](output/wf2/songon1/crops/building_main_x_column_span_y_m_0.png) |
| 도크 수 | 106 | 확정 | 1-1.건축.pdf · page 54, sheet_no A-201 [근거](output/wf2/songon1/crops/building_main_x_dock_count_0.png) |
| 방화구획 최대 면적 | 2,961.78㎡ | 확정 | 1-1.건축.pdf · page 19, sheet_no A-124 [근거](output/wf2/songon1/crops/building_main_x_fire_compartment_max_m2_0.png) |
| 지상층수 | 3층 | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_main_x_floors_above_0.png) |
| 지하층수 | 2층 | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_main_x_floors_below_0.png) |
| 연면적 | 54,982.92㎡ | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_main_x_gross_floor_area_m2_0.png) |
| 램프 형상 | 곡선형 | 확정 | 1-1.건축.pdf · page 77, sheet_no A-441 [근거](output/wf2/songon1/crops/building_main_x_ramp_form_0.png) |
| 램프 통행 방향 | 양방향 | 확정 | 1-1.건축.pdf · page 77, sheet_no A-441 [근거](output/wf2/songon1/crops/building_main_x_ramp_type_0.png) |
| 램프 폭 | 9.6m | 확정 | 1-1.건축.pdf · page 77, sheet_no A-441 [근거](output/wf2/songon1/crops/building_main_x_ramp_width_m_0.png) |
| 냉매 종류 | 프레온계열 | 확정 | 8-1설비-냉동.pdf · page 5, sheet_no MR-004 [근거](output/wf2/songon1/crops/building_main_x_refrigerant_0.png) |
| 지붕 패널 심재 | EPS | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_main_x_roof_panel_core_0.png) |
| 스프링클러 형식 | 표준형 | 확정 | 7-1.설비-기계소방.pdf · page 6, sheet_no MF-101 [근거](output/wf2/songon1/crops/building_main_x_sprinkler_type_0.png) |
| 구조형식 | 복합 | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_main_x_structure_type_0.png) |
| 지형 단차 진입도로로 여러 층 직접 접안 | 있음 | 확정 | 1-1.건축.pdf · page 7, sheet_no A-103 [근거](output/wf2/songon1/crops/building_main_x_terrain_multi_level_access_0.png) |
| 외벽 패널 심재 | EPS | 확정 | 1-1.건축.pdf · page 98, sheet_no A-511 [근거](output/wf2/songon1/crops/building_main_x_wall_panel_core_0.png) |
| 창고 내부 깊이(하역장 측 벽~반대편 벽) | 31.0m | 확정 | 1-1.건축.pdf · page 62, sheet_no A-401 [근거](output/wf2/songon1/crops/building_main_x_warehouse_depth_m_0.png) |
| 램프 경사 | 10.0% | 확정 | 1-1.건축.pdf · page 79, sheet_no A-443 [근거](output/wf2/songon1/crops/building_main_x_ramp_slope_pct_0.png) |
| 저온동 단열재 두께 | 170.0mm | 확정 | 1-1.건축.pdf · page 98, sheet_no A-511 [근거](output/wf2/songon1/crops/building_main_x_cold_insulation_thickness_mm_0.png) |

| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |
|---|---|---|---|---|---|
| B2 | 창고 | 18,920.13㎡ | — | — | 있음 |
| B1 | 기타 | 2,185.29㎡ | — | — | — |
| 1F | 창고 | 11,692.23㎡ | — | — | 있음 |
| 2F | 창고 | 12,678.64㎡ | — | — | 있음 |
| 3F | 창고 | 9,506.63㎡ | — | 8.0m | 있음 |

### 나동 (경비동) [guard]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 지상층수 | 1층 | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_guard_x_floors_above_0.png) |
| 연면적 | 12.0㎡ | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/building_guard_x_gross_floor_area_m2_0.png) |

| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |
|---|---|---|---|---|---|
| 1F | 기타 | — | — | — | — |

### 단지 공용

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 대지면적 | 29,587.0㎡ | 확정 | 1-1.건축.pdf · page 5, sheet_no A-101 [근거](output/wf2/songon1/crops/asset_x_x_site_area_m2_0.png) |
| 트럭야드 깊이 | 11.0m | 확정 | 1-1.건축.pdf · page 62, sheet_no A-401 [근거](output/wf2/songon1/crops/asset_x_x_truck_yard_depth_m_0.png) |

## 2. 스펙 경쟁력 — 벤치마크 포지셔닝

벤치마크 미적용 — WF1 벤치마크 DB가 아직 없다(구현 3단계).

## 3. IM–도면 정합성

| 항목 | IM 기재 | 도면 | 확정값 | 방향 |
|---|---|---|---|---|
| 저온동 단열재 두께 (main) | — | 170.0mm, 150.0mm | 170.0mm (확정) | — |
| 램프 경사 (main) | — | 10.0%, 9.091% | 10.0% (확정) | — |

<!-- LLM:consistency -->

## 4. 입지 리스크

입지 조회 미실행 — 입지 룰(LC)은 구현 2단계에서 추가된다.

## 5. 리스크 평가 결과

### 🔴 FR01. 패널 심재 가연성 [main]

- **판정 입력:** panel_combustibility=가연, roof_panel_combustibility=가연
- **추론 근거:** <!-- LLM:basis:FR01@main -->
- **근본 원인:** <!-- LLM:root:FR01@main -->
- **연쇄 리스크:** <!-- LLM:cascade:FR01@main -->
- **DD 확인 포인트:** <!-- LLM:dd:FR01@main -->

### 🔴 FR04. 저온동 단열재 화재 [main]

- **판정 입력:** cold_insulation_combustibility=난연, cold_ratio=—, has_cold=있음
- **추론 근거:** <!-- LLM:basis:FR04@main -->
- **근본 원인:** <!-- LLM:root:FR04@main -->
- **연쇄 리스크:** <!-- LLM:cascade:FR04@main -->
- **DD 확인 포인트:** <!-- LLM:dd:FR04@main -->

### 🔴 SP02. 유효층고 미달 [main]

- **판정 입력:** warehouse_floors.clear_height_m.min=8.0
- **적용 임계값:** clear_height.yellow=8.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP02@main -->
- **근본 원인:** <!-- LLM:root:SP02@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP02@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP02@main -->

### 🔴 SP05. 램프·차량 접근 제약 [main]

- **판정 입력:** floors_above=3, ramp_slope_pct=10.0, ramp_type=양방향, ramp_width_m=9.6
- **적용 임계값:** ramp_slope.red=9 (default, 검증); ramp_width.red=7.5 (ramp_type=양방향, 검증)
- **추론 근거:** <!-- LLM:basis:SP05@main -->
- **근본 원인:** <!-- LLM:root:SP05@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP05@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP05@main -->

### 🔴 SP06. 트럭야드 협소 [main]

- **판정 입력:** truck_yard_depth_m=11.0
- **적용 임계값:** truck_yard_depth.red=13 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP06@main -->
- **근본 원인:** <!-- LLM:root:SP06@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP06@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP06@main -->

### 🟢 CL04. 온도대 전환 유연성 [main]

- **판정 입력:** has_cold=있음, refrigerant=프레온계열
- **추론 근거:** <!-- LLM:basis:CL04@main -->

### 🟢 FR02. 방화구획 대면적 [main]

- **판정 입력:** fire_compartment_max_m2=2,961.78
- **적용 임계값:** fire_compartment_area.yellow=3000 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR02@main -->

### 🟢 FR05. 창고 내부 깊이 과대 (소방대 진입 거리) [main]

- **판정 입력:** warehouse_depth_m=31.0
- **적용 임계값:** warehouse_depth.red=77 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR05@main -->

### 🟢 SP03. 기둥 스팬·랙 효율 [main]

- **판정 입력:** column_span_x_m=11.0, column_span_y_m=11.0
- **적용 임계값:** column_span.yellow=11.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP03@main -->

### 🟢 SP04. 도크 부족 [main]

- **판정 입력:** dock_density=63.7
- **적용 임계값:** dock_density.red=50 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP04@main -->

### 🟢 SP07. 수직반송 의존 [main]

- **판정 입력:** handling_type=다층 램프형
- **추론 근거:** <!-- LLM:basis:SP07@main -->

### ⚪ CL01. 냉동설비·냉매 리스크 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—, has_cold=있음, refrigerant=프레온계열
- **DD 확인 포인트:** 미확인 입력 확보; 냉동설비(CDU·유닛쿨러·냉각탑) 소유(임대인/임차인)와 교체 책임 — 도면으로 확인 불가; 실제 충전 냉매 종류(R-404A 외 R-22 표기 계통 유무); 고압가스 허가·정기검사 이력; 압축기 운전시간·오버홀 이력; 사용승인일 확보(연식 입력)

### ⚪ CL02. 바닥 동상 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 저온동 바닥 동상 방지 설비 (main)
- **판정 입력:** cold_floor_heave_protection=—, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; B2·1F 냉동창고 바닥의 동상 방지 설비(히팅 코일·통기관) 유무 — 냉동 전문 도면(8-1 설비-냉동)·시공 자료 확인; 설비 작동 상태와 바닥 레벨 측정 결과; B2 바닥 균열·융기 흔적

### ⚪ CL03. 단열 패널 열화·결로 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 냉동창고 벽·천장 이음부 결로·결빙 흔적; 냉동창고 도어·도크씰 기밀 상태

### ⚪ FR03. 스프링클러 형식 부적합 [main]

- **판정 보류 사유:** 일부 창고층 미확인 — 미확인 입력: —
- **판정 입력:** sprinkler_type=표준형, warehouse_floors.clear_height_m.max=8.0
- **적용 임계값:** sprinkler_esfr_clear_height.red=13.7 (default, 검증)
- **DD 확인 포인트:** 미확인 입력 확보; B2·1F·2F 창고 유효고(보·배관·헤드 하단) 실측 — 도면은 층고(B2 9.2, 1F 8.85, 2F 9.15)만 표기; 실제 적재 높이·상품 등급과 랙 구성; 임차인 파렛트랙·메자닌 계획 대비 인랙 분기배관 반영 여부; 냉동창고 준비작동식 계통의 헤드 배치와 유니트쿨러 주변 미경계구역

### ⚪ FR06. 오버헤드도어 하부 살수장애 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 오버헤드도어 하부 스프링클러 살수장애(헤드 미설치) (main)
- **판정 입력:** ohd_sprinkler_gap=—
- **DD 확인 포인트:** 미확인 입력 확보; 층별 OHD 하부(문 안쪽) 헤드 유무와 개방 시 간섭; 준공 후 소방 점검·임차인 Fire Audit의 OHD 살수장애 지적과 보완 여부; 냉동창고 출입문·유니트쿨러 주변 드라이펜던트 헤드 배치

### ⚪ G01. 배관 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 건축물대장 사용승인일 확보(연식 산정 입력) — 도면 표제란 2021.09는 설계일; asset_meta에 보유기간(holding_years) 입력 — exit 판정 보류 해소; 냉동창고(B2·1F) 냉매·소화배관 보온 상태와 결로 부식 흔적; 냉동설비·냉매배관 소유(임대인/임차인) 확인; 배관 누수 보수 기록과 충압펌프 기동 빈도

### ⚪ G02. 수변전설비 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 한전 계약전력(수전용량)과 최대수요전력 실적 — 도면에 수전용량 표기 없음; 냉동냉장 전용 TR#1·TR#2와 SMP용 TR#3의 부하율·증설 여유; 변압기 제조연도·절연유 분석 결과; 임차인 증설 전기설비의 소유·원상복구 조건

### ⚪ G03. 화물용 승강기·수직반송기 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 화물용 승강기 대수 (main)
- **판정 입력:** freight_elevator_count=—, vrc_count=—
- **DD 확인 포인트:** 미확인 입력 확보; 승강기 대장(화물용·승용 구분)과 수직반송기 설치 여부 — 도면은 승용 EV(16P) 1대만 표기; 전기소방 결선도 'P-ELEV' 항목이 어떤 승강기인지 확인; 수직반송기가 있다면 임차인 설치 여부와 원상복구 조건; 승용 EV의 화물 운반 사용 여부와 고장 이력

### ⚪ G04. 비상발전기 신뢰성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 비상발전기 용량과 냉동설비(CDU·유닛쿨러) 비상부하 포함 여부; 부하 운전 시험 기록; 임차인 자체 발전기 유무와 소유

### ⚪ G05. 스프링클러·제연 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 최근 소방 종합정밀점검·임차인 Fire Audit 지적사항과 시정 여부; 냉동창고 준비작동식(프리액션) 밸브·감지기 연동 시험 기록; 제연설비 작동 시험 기록

### ⚪ G06. 지붕 방수·배수 열화 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 운영 중 누수 사고보고서·하자 처리 내역과 같은 부위 재발 여부; 2F 지붕 위 3F 출하장 구간과 램프-건물 접합부 방수·후레싱 상태; 거터·선홈통 결빙 대책(열선, 오버플로 배수); 태양광 설치 여부와 소유·임대 계약 조건 — 지붕평면도에 표기 없음

### ⚪ G07. 야드·램프 포장 열화 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일 확보(연식 입력); 램프 곡선부·직선부 바닥 균열·박리와 신축이음·배수 상태; 서·동측 대지 경사로와 옹벽·성토부 면접부 부등침하, 측구 균열; 하자보수 기간 잔여 여부

### ⚪ G08. 석면 함유 가능성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** regulation_flags.asbestos_total_ban_2009=—
- **DD 확인 포인트:** 미확인 입력 확보; 건축물대장 사용승인일 확인; 석면 조사 보고서 유무

### ⚪ G09. 법규 적합성·용도변경 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 건축물대장 용도·위반 사항과 사용승인일; 동별면적표 '변경후' 표기에 해당하는 설계변경·대수선 허가 이력; 소방 완공필증과 현황 일치 여부(냉동·상온 구획 포함)

### ⚪ G10. CapEx 종합 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 준공연도(사용승인) (main)
- **판정 입력:** building_age=—
- **DD 확인 포인트:** 미확인 입력 확보; 사용승인일과 보유기간 입력; PCA 장기 CAPEX 계획표; 냉동설비·수변전·지붕 판넬의 내용연수 도래 시점; 시공사 하자보수 보증 잔여 기간

### ⚪ SP01. 바닥하중 미달 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 바닥 설계하중 (main 1F), 바닥 설계하중 (main 2F), 바닥 설계하중 (main 3F), 바닥 설계하중 (main B2)
- **판정 입력:** warehouse_floors.floor_load_tpm2.min=—
- **DD 확인 포인트:** 미확인 입력 확보; 구조계산서 또는 설계하중표의 층별 바닥 적재하중; S-271 '2.99KN/m2' 표기의 의미(슬래브 항목) 확인; PC 슬래브 층(2F·3F)의 허용 하중과 현재 랙 하중

### ⚪ SP08. 대형차 회전반경 부족 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 대형차 최소 회전반경(램프·하역장 동선) (main)
- **판정 입력:** turning_radius_m=—
- **DD 확인 포인트:** 미확인 입력 확보; 램프 곡선부 R 치수(설계 원도·CAD 또는 현장 실측); 40FT·세미트레일러 회전 궤적 검토(AutoTURN 등) 결과; 현장 주차 위치가 준공도면과 같은지

### ⚪ SP09. 하역 동선 기둥 간섭 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 램프→하역장 동선 기둥 간섭(대형차) (main 1F), 램프→하역장 동선 기둥 간섭(대형차) (main 2F), 램프→하역장 동선 기둥 간섭(대형차) (main 3F), 램프→하역장 동선 기둥 간섭(대형차) (main B2)
- **판정 입력:** floors_with_dock_column_conflict=—
- **DD 확인 포인트:** 미확인 입력 확보; 2F 램프 출구→하역장 진입 구간 Y4열 기둥과 40FT 회전 궤적; 3F 램프 출구→출하장 동선 기둥 위치; 기둥보호대·유도 설비 설치 여부와 층별 임차인 차량 구성

### ⚪ V02. 핵심 스펙 미확인

- **판정 보류 사유:** 임계값 미정 — 미확인 입력: thresholds.yaml: V02 red/yellow
- **판정 입력:** v02.unconfirmed_ratio=0.367
- **DD 확인 포인트:** 미확인 입력 확보; 건축물대장(사용승인일) — 연식 룰 일괄 보류 해소; 냉동·상온 면적 합계표와 한전 계약전력; 도크레벨러·화물용 승강기·수직반송기 설비 대장; 확보 불가 항목은 현장 실사 범위에 포함; V02 임계값 확정(리뷰 서버 /thresholds)

## 6. 리스크 상관관계

- 상관관계 맵에 정의된 관계 중 양쪽이 모두 활성인 쌍이 없다.

## 7. DD 체크리스트

판정 보류(⚪) 항목을 먼저, 미확인 사유별로 묶었다. 자료 요청은 `songon1_data_request.md` 참조.

<!-- LLM:dd_checklist -->

## 부록 A. 필드별 추출 근거

§1 표의 출처 열과 `w2_05_confirmed_spec.json` 참조. 도면 판독값은 [근거] 링크로 크롭 이미지를 연다.

## 부록 B. 미검증 연쇄 제안

- 없음

## 갱신 이력

| 일시 | 변경 사유 | 재진입 지점 |
|---|---|---|
| — | 초안 | — |
