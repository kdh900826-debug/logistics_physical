# [화성풀필먼트신흥 복합물류센터] 물리적 리스크 분석 보고서

> 분석 모드: 정규 · 기준일: 미입력(실행일 기준) · 보유기간: 미입력(exit 평가 생략)
> 룰셋: ruleset-untagged@2e2d57e · 임계값 검증: 참조 20건 중 verified 20건 · 벤치마크: 미적용 · 입지 조회: 미조회
> 한계: 본 보고서는 IM과 도면 기반의 스크리닝 결과이며 PCA·현장 실사를 대체하지 않는다. ⚪ 판정 보류 항목은 '정상'이 아니라 입력이 확인되지 않아 평가하지 않은 항목이다.

## 0. 요약 대시보드

| 🔴 | 🟡 | 🟢 | ⚪ 판정 보류 | 미발동 |
|---|---|---|---|---|
| 7 | 0 | 16 | 8 | 1 |

- 등급 정책: 단일 등급 — 🔴·🟡 구분 없이 발동은 모두 🔴 (severity_policy.yaml)
- 검증 입력 기준: 🔴 7 · 🟡 0 · 🟢 16 · ⚪ 8 / †IM 기준(주장값 포함): 🔴 0 · 🟡 0 · ⚪ 0
- 보유 중 심각도 상승 예정: 0건
- IM–도면 불일치: 6건 (IM 과장 3 · IM 보수 2 · 방향 없음 1)
- 스펙 확정 현황: 확정(교차) 27 · 확정 30

**우선 확인 Top 3** (정렬: 심각도 → V01 연관 → 상관관계 연결 수 → 카테고리 우선순위)

1. 🔴 **SP05** 램프·차량 접근 제약 [main] — <!-- LLM:top3_1 -->
2. 🔴 **FR04** 저온동 단열재 화재 [main] — <!-- LLM:top3_2 -->
3. 🔴 **FR05** 창고 내부 깊이 과대 (소방대 진입 거리) [main] — <!-- LLM:top3_3 -->

<!-- LLM:summary -->

## 1. 자산 프로파일

### 물류창고 [main]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 기둥 스팬(장변) | 11.0m | 확정(교차) | 건축.pdf · page 41, sheet_no A-205 [근거](output/wf2/hwaseong/crops/building_main_x_column_span_x_m_0.png) |
| 기둥 스팬(단변) | 11.0m | 확정(교차) | 건축.pdf · page 41, sheet_no A-205 [근거](output/wf2/hwaseong/crops/building_main_x_column_span_y_m_0.png) |
| 지상층수 | 4층 | 확정(교차) | 건축.pdf · page 3, sheet_no A-011 [근거](output/wf2/hwaseong/crops/building_main_x_floors_above_0.png) |
| 지하층수 | 1층 | 확정(교차) | 건축.pdf · page 3, sheet_no A-011 [근거](output/wf2/hwaseong/crops/building_main_x_floors_below_0.png) |
| 연면적 | 45,723.76㎡ | 확정(교차) | 건축.pdf · page 3, sheet_no A-011 [근거](output/wf2/hwaseong/crops/building_main_x_gross_floor_area_m2_0.png) |
| 램프 경사 | 10.0% | 확정 | 건축.pdf · page 77, sheet_no A-901 [근거](output/wf2/hwaseong/crops/building_main_x_ramp_slope_pct_0.png) |
| 창고 내부 깊이(하역장 측 벽~반대편 벽) | 96.0m | 확정 | 화성풀필먼트신흥 담보대출[IM]_250313.pdf · page 22 |
| 저온동 단열재 종류 | 우레탄 | 확정 | 건축.pdf · page 87, sheet_no A-1143 [근거](output/wf2/hwaseong/crops/building_main_x_cold_insulation_material_0.png) |
| 준공연도(사용승인) | 2024 | 확정 | 화성풀필먼트신흥 담보대출[IM]_250313.pdf · page 14 |
| 도크 수 | 64 | 확정 | 건축.pdf · page 13, sheet_no A-104 [근거](output/wf2/hwaseong/crops/building_main_x_dock_count_0.png) |
| 방화구획 최대 면적 | 2,878.62㎡ | 확정 | 건축.pdf · page 24, sheet_no A-124 [근거](output/wf2/hwaseong/crops/building_main_x_fire_compartment_max_m2_0.png) |
| 램프 형상 | 곡선형 | 확정 | 건축.pdf · page 77, sheet_no A-901 [근거](output/wf2/hwaseong/crops/building_main_x_ramp_form_0.png) |
| 램프 통행 방향 | 양방향 | 확정 | 건축.pdf · page 12, sheet_no A-103 [근거](output/wf2/hwaseong/crops/building_main_x_ramp_type_0.png) |
| 램프 폭 | 9.4m | 확정 | 건축.pdf · page 77, sheet_no A-901 [근거](output/wf2/hwaseong/crops/building_main_x_ramp_width_m_0.png) |
| 스프링클러 형식 | 표준형 | 확정 | 기계소방.pdf · page 3, sheet_no MF-002 [근거](output/wf2/hwaseong/crops/building_main_x_sprinkler_type_0.png) |
| 지형 단차 진입도로로 여러 층 직접 접안 | 있음 | 확정 | 건축.pdf · page 5, sheet_no A-013 [근거](output/wf2/hwaseong/crops/building_main_x_terrain_multi_level_access_0.png) |
| 대형차 최소 회전반경(램프·하역장 동선) | 12.0m | 확정 | 건축.pdf · page 77, sheet_no A-901 [근거](output/wf2/hwaseong/crops/building_main_x_turning_radius_m_0.png) |
| 외벽 패널 심재 | 글라스울 | 확정 | 건축.pdf · page 30, sheet_no A-135 [근거](output/wf2/hwaseong/crops/building_main_x_wall_panel_core_0.png) |
| 저온·냉동 면적 | 8,101.98㎡ | 확정 | 화성풀필먼트신흥 담보대출[IM]_250313.pdf · page 16 |
| 구조형식 | 복합 | 확정 | 화성풀필먼트신흥 담보대출[IM]_250313.pdf · page 14 |
| 저온동 단열재 두께 | 200.0mm | 확정 | 건축.pdf · page 87, sheet_no A-1143 [근거](output/wf2/hwaseong/crops/building_main_x_cold_insulation_thickness_mm_0.png) |

| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |
|---|---|---|---|---|---|
| B1 | 창고 | 13,538.62㎡ | 2.0t/㎡ | 8.2m | 있음 |
| 1F | 창고 | 11,505.21㎡ | 2.039t/㎡ | 8.2m | 있음 |
| 2F | 사무 | 1,664.93㎡ | 0.357t/㎡ | — | — |
| 3F | 창고 | 10,913.05㎡ | 2.039t/㎡ | 8.2m | 있음 |
| 4F | 창고 | 8,101.98㎡ | 2.549t/㎡ | 8.2m | 있음 |

### 단지 공용

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 대지면적 | 29,961.0㎡ | 확정 | 화성풀필먼트신흥 담보대출[IM]_250313.pdf · page 14 |

## 2. 스펙 경쟁력 — 벤치마크 포지셔닝

벤치마크 미적용 — WF1 벤치마크 DB가 아직 없다(구현 3단계).

## 3. IM–도면 정합성

| 항목 | IM 기재 | 도면 | 확정값 | 방향 |
|---|---|---|---|---|
| 대지면적 | 29,961.0㎡ | 29,419.0㎡ | 29,961.0㎡ (확정) | IM 과장 |
| 저온·냉동 면적 (main) | 8,101.98㎡, 8,101.95㎡ | 7,821.34㎡ | 8,101.98㎡ (확정) | 방향 없음 |
| 저온동 단열재 두께 (main) | — | 200.0mm, 150.0mm | 200.0mm (확정) | — |
| 램프 경사 (main) | 9.0%, 10.2% | 10.0% | 10.0% (확정) | IM 과장 |
| 구조형식 (main) | 복합 | 복합, RC | 복합 (확정) | — |
| 창고 내부 깊이(하역장 측 벽~반대편 벽) (main) | 96.0m, 85.0m, 96.0m | 71.0m | 96.0m (확정) | IM 보수 |
| 층 면적 (main 3F) | 10,913.05㎡ | 11,193.66㎡ | 10,913.05㎡ (확정) | IM 보수 |
| 층 면적 (main 4F) | 8,101.98㎡ | 7,821.34㎡ | 8,101.98㎡ (확정) | IM 과장 |
| 층 온도대 (main 4F) | 저온 | 냉동, 저온 | 저온 (확정) | — |

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

- **판정 입력:** cold_insulation_combustibility=난연, cold_ratio=0.177, has_cold=있음
- **추론 근거:** <!-- LLM:basis:FR04@main -->
- **근본 원인:** <!-- LLM:root:FR04@main -->
- **연쇄 리스크:** <!-- LLM:cascade:FR04@main -->
- **DD 확인 포인트:** <!-- LLM:dd:FR04@main -->

### 🔴 FR05. 창고 내부 깊이 과대 (소방대 진입 거리) [main]

- **판정 입력:** warehouse_depth_m=96.0
- **적용 임계값:** warehouse_depth.red=77 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR05@main -->
- **근본 원인:** <!-- LLM:root:FR05@main -->
- **연쇄 리스크:** <!-- LLM:cascade:FR05@main -->
- **DD 확인 포인트:** <!-- LLM:dd:FR05@main -->

### 🔴 SP02. 유효층고 미달 [main]

- **판정 입력:** warehouse_floors.clear_height_m.min=8.2
- **적용 임계값:** clear_height.yellow=8.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP02@main -->
- **근본 원인:** <!-- LLM:root:SP02@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP02@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP02@main -->

### 🔴 SP04. 도크 부족 [main]

- **판정 입력:** dock_density=46.3
- **적용 임계값:** dock_density.red=50 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP04@main -->
- **근본 원인:** <!-- LLM:root:SP04@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP04@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP04@main -->

### 🔴 SP05. 램프·차량 접근 제약 [main]

- **판정 입력:** floors_above=4, ramp_slope_pct=10.0, ramp_type=양방향, ramp_width_m=9.4
- **적용 임계값:** ramp_slope.red=9 (default, 검증); ramp_width.red=7.5 (ramp_type=양방향, 검증)
- **추론 근거:** <!-- LLM:basis:SP05@main -->
- **근본 원인:** <!-- LLM:root:SP05@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP05@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP05@main -->

### 🔴 V01. IM–도면 스펙 불일치

- **판정 입력:** v01.discrepancy_count=1, v01.overstated_sensitive_count=1
- **추론 근거:** <!-- LLM:basis:V01@None -->
- **근본 원인:** <!-- LLM:root:V01@None -->
- **연쇄 리스크:** <!-- LLM:cascade:V01@None -->
- **DD 확인 포인트:** <!-- LLM:dd:V01@None -->

### 🟢 FR02. 방화구획 대면적 [main]

- **판정 입력:** fire_compartment_max_m2=2,878.62
- **적용 임계값:** fire_compartment_area.yellow=3000 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR02@main -->

### 🟢 FR03. 스프링클러 형식 부적합 [main]

- **판정 입력:** sprinkler_type=표준형, warehouse_floors.clear_height_m.max=8.2
- **적용 임계값:** sprinkler_esfr_clear_height.red=13.7 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR03@main -->

### 🟢 G01. 배관 노후 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_piping.red=30 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G01@main -->

### 🟢 G02. 수변전설비 노후 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_substation.red=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G02@main -->

### 🟢 G04. 비상발전기 신뢰성 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_generator.red=30 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G04@main -->

### 🟢 G05. 스프링클러·제연 노후 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_fire_system.red=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G05@main -->

### 🟢 G06. 지붕 방수·배수 열화 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_roof.red=15 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G06@main -->

### 🟢 G07. 야드·램프 포장 열화 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_pavement.red=20 (default, 검증); aging_pavement.yellow=10 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G07@main -->

### 🟢 G08. 석면 함유 가능성 [main]

- **판정 입력:** regulation_flags.asbestos_total_ban_2009=없음
- **추론 근거:** <!-- LLM:basis:G08@main -->

### 🟢 G09. 법규 적합성·용도변경 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_compliance.yellow=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G09@main -->

### 🟢 G10. CapEx 종합 [main]

- **판정 입력:** building_age=2
- **적용 임계값:** aging_capex.yellow=15 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G10@main -->

### 🟢 SP01. 바닥하중 미달 [main]

- **판정 입력:** warehouse_floors.floor_load_tpm2.min=2.0
- **적용 임계값:** floor_load.red=1.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP01@main -->

### 🟢 SP03. 기둥 스팬·랙 효율 [main]

- **판정 입력:** column_span_x_m=11.0, column_span_y_m=11.0
- **적용 임계값:** column_span.yellow=11.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP03@main -->

### 🟢 SP07. 수직반송 의존 [main]

- **판정 입력:** handling_type=다층 램프형
- **추론 근거:** <!-- LLM:basis:SP07@main -->

### 🟢 SP08. 대형차 회전반경 부족 [main]

- **판정 입력:** turning_radius_m=12.0
- **적용 임계값:** turning_radius.red=12.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP08@main -->

### 🟢 SP09. 하역 동선 기둥 간섭 [main]

- **판정 입력:** —
- **추론 근거:** <!-- LLM:basis:SP09@main -->

### ⚪ CL01. 냉동설비·냉매 리스크 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 냉매 종류 (main)
- **판정 입력:** building_age=2, has_cold=있음, refrigerant=—
- **적용 임계값:** cold_refrigeration_age.red=15 (default, 검증)
- **DD 확인 포인트:** 미확인 입력 확보; 냉동기 형식·냉매 종류·용량과 고압가스 허가·검사 이력(냉동설비 준공도서 또는 임차인 설치 도서); 냉동설비 소유(refrigeration_owner)와 교체·철거·원상복구 책임(임대차계약서); 압축기 운전시간·오버홀 이력

### ⚪ CL02. 바닥 동상 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 저온동 바닥 동상 방지 설비 (main)
- **판정 입력:** cold_floor_heave_protection=—, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; 4F 바닥 방열 상세와 3F 천장 결로 흔적 — 확인 후 동상방지 필드 해당 여부를 G2에 반영(⚪ 해소); 향후 지반층(B1·1F)을 저온으로 쓸 계획이 있다면 동상방지 설비 신설 필요 여부

### ⚪ CL03. 단열 패널 열화·결로 [main]

- **판정 보류 사유:** 임계값 미정 — 미확인 입력: thresholds.yaml: CL03 red/yellow
- **판정 입력:** building_age=2, has_cold=있음
- **DD 확인 포인트:** 미확인 입력 확보; thresholds.yaml CL03 기준값 사용자 확인(리뷰 서버 /thresholds); 방열 뿜칠 균열·결로·결빙 흔적; 방열문·도크씰 기밀 상태

### ⚪ FR01. 패널 심재 가연성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 지붕 패널 심재 (main)
- **판정 입력:** panel_combustibility=불연, roof_panel_combustibility=—
- **DD 확인 포인트:** 미확인 입력 확보; 지붕 구성(PC 슬래브+우레탄 뿜칠)과 옥탑 지붕판넬 심재를 확인해 roof_panel_core를 G2에 확정(⚪ 해소); 외벽 글라스울 패널 납품서·시험성적서; 부분 교체·임차사 추가공사 구간의 심재 혼재 여부; 보험사 리스크 서베이 결과

### ⚪ FR06. 오버헤드도어 하부 살수장애 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 오버헤드도어 하부 스프링클러 살수장애(헤드 미설치) (main)
- **판정 입력:** ohd_sprinkler_gap=—
- **DD 확인 포인트:** 미확인 입력 확보; 소방 평면도에서 OHD·스피드도어 하부(문 안쪽) 헤드 유무와 도어 개방 시 간섭; 준공 후 소방 점검·임차인 Fire Audit 지적과 층별 보완 여부; 4F 냉동창고 출입문·유니트쿨러 주변 드라이펜던트 헤드 설치 여부

### ⚪ G03. 화물용 승강기·수직반송기 노후 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 화물용 승강기 대수 (main)
- **판정 입력:** freight_elevator_count=—, vrc_count=—
- **DD 확인 포인트:** 미확인 입력 확보; 화물용 승강기·수직반송기 유무와 대수 — 없으면 G2에서 0으로 확정해 ⚪ 해소; 수직반송기 소유(vrc_owner)와 원상복구 조건; 비상용 승강기의 화물 운반 전용 여부와 고장 이력; 승강기 정밀안전검사 결과

### ⚪ SP06. 트럭야드 협소 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 트럭야드 깊이
- **판정 입력:** truck_yard_depth_m=—
- **DD 확인 포인트:** 미확인 입력 확보; 층별 도크 전면 야드 깊이 실측; 40FT 트레일러 후진 접안·회차 가능 여부와 대기 공간; B1F YARD(지하층, 램프-2 연결)의 대형차 회전 궤적

### ⚪ V02. 핵심 스펙 미확인

- **판정 보류 사유:** 임계값 미정 — 미확인 입력: thresholds.yaml: V02 red/yellow
- **판정 입력:** v02.unconfirmed_ratio=0.333
- **DD 확인 포인트:** 미확인 입력 확보; thresholds.yaml V02 기준값 사용자 확인(리뷰 서버 /thresholds); 냉동설비 준공도서(임차인 설치분 포함), 소방 준공도서, 수전 계약서, 승강기 대장 요청; 자료로 확보 못 하는 항목은 현장 실사 범위에 포함

## 6. 리스크 상관관계

- 상관관계 맵에 정의된 관계 중 양쪽이 모두 활성인 쌍이 없다.

## 7. DD 체크리스트

판정 보류(⚪) 항목을 먼저, 미확인 사유별로 묶었다. 자료 요청은 `hwaseong_data_request.md` 참조.

<!-- LLM:dd_checklist -->

## 부록 A. 필드별 추출 근거

§1 표의 출처 열과 `w2_05_confirmed_spec.json` 참조. 도면 판독값은 [근거] 링크로 크롭 이미지를 연다.

## 부록 B. 미검증 연쇄 제안

- ['SP04', 'SP05']: <!-- LLM:proposal:0 -->
- ['CL04', 'SP05']: <!-- LLM:proposal:1 -->
- ['FR04', 'CL04']: <!-- LLM:proposal:2 -->
- ['V01', 'SP05']: <!-- LLM:proposal:3 -->

## 갱신 이력

| 일시 | 변경 사유 | 재진입 지점 |
|---|---|---|
| — | 초안 | — |
