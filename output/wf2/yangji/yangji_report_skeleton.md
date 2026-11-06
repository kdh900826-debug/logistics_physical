# [아레나스 양지 물류센터] 물리적 리스크 분석 보고서

> 분석 모드: 정규 · 기준일: 미입력(실행일 기준) · 보유기간: 미입력(exit 평가 생략)
> 룰셋: ruleset-untagged@aa1c5f0 · 임계값 검증: 참조 19건 중 verified 19건 · 벤치마크: 미적용 · 입지 조회: 미조회
> 한계: 본 보고서는 IM과 도면 기반의 스크리닝 결과이며 PCA·현장 실사를 대체하지 않는다. ⚪ 판정 보류 항목은 '정상'이 아니라 입력이 확인되지 않아 평가하지 않은 항목이다.

## 0. 요약 대시보드

| 🔴 | 🟡 | 🟢 | ⚪ 판정 보류 | 미발동 |
|---|---|---|---|---|
| 4 | 0 | 15 | 7 | 7 |

- 등급 정책: 단일 등급 — 🔴·🟡 구분 없이 발동은 모두 🔴 (severity_policy.yaml)
- 검증 입력 기준: 🔴 4 · 🟡 0 · 🟢 15 · ⚪ 7 / †IM 기준(주장값 포함): 🔴 0 · 🟡 0 · ⚪ 0
- 보유 중 심각도 상승 예정: 0건
- IM–도면 불일치: 3건 (IM 과장 1 · IM 보수 0 · 방향 없음 2)
- 스펙 확정 현황: 확정(교차) 27 · 주장값 2 · 확정 54

**우선 확인 Top 3** (정렬: 심각도 → V01 연관 → 상관관계 연결 수 → 카테고리 우선순위)

1. 🔴 **SP02** 유효층고 미달 [main] — <!-- LLM:top3_1 -->
2. 🔴 **SP05** 램프·차량 접근 제약 [main] — <!-- LLM:top3_2 -->
3. 🔴 **SP06** 트럭야드 협소 [main] — <!-- LLM:top3_3 -->

<!-- LLM:summary -->

## 1. 자산 프로파일

### 물류센터 (양지유통업무설비창고A) [main]

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 지상층수 | 10층 | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 1 [근거](output/wf2/yangji/crops/building_main_x_floors_above_0.png) |
| 지하층수 | 2층 | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 1 [근거](output/wf2/yangji/crops/building_main_x_floors_below_0.png) |
| 램프 형상 | 직선형 | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_ramp_form_0.png) |
| 램프 통행 방향 | 단방향 | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_ramp_type_0.png) |
| 화물용 승강기 용량 | 5.0t | 주장값 | 임대차계약서_세부약정서_기타합의서_발췌.pdf · page 1 |
| 변압기 총용량 | 11,000.0kVA | 주장값 | [아레나스양지] IM_260728.pdf · page 9 |
| 램프 경사 | 10.0% | 확정 | [아레나스양지] IM_260728.pdf · page 14 |
| 기둥 스팬(장변) | 11.0m | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_column_span_x_m_0.png) |
| 기둥 스팬(단변) | 11.0m | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_column_span_y_m_0.png) |
| 준공연도(사용승인) | 2019 | 확정 | [아레나스양지] IM_260728.pdf · page 9 |
| 화물용 승강기 대수 | 4 | 확정 | [아레나스양지] IM_260728.pdf · page 9 |
| 지형 단차 진입도로로 여러 층 직접 접안 | 있음 | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_terrain_multi_level_access_0.png) |
| 수직반송기 대수 | 4 | 확정 | 임대차계약서_세부약정서_기타합의서_발췌.pdf · page 1 |
| 창고 내부 깊이(하역장 측 벽~반대편 벽) | 66.0m | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/building_main_x_warehouse_depth_m_0.png) |
| 도크 수 | 747 | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 20 [근거](output/wf2/yangji/crops/building_main_x_dock_count_1.png) |
| 연면적 | 346,364.8㎡ | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 1 [근거](output/wf2/yangji/crops/building_main_x_gross_floor_area_m2_0.png) |
| 램프 폭 | 8.6m | 확정 | [아레나스양지] IM_260728.pdf · page 9 |
| 스프링클러 형식 | 혼합 | 확정 | 임대차계약서_세부약정서_기타합의서_발췌.pdf · page 2 |
| 구조형식 | 복합 | 확정 | 임대차계약서_별첨도면_추출본.pdf · page 1 [근거](output/wf2/yangji/crops/building_main_x_structure_type_0.png) |

| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |
|---|---|---|---|---|---|
| B2 | 창고 | 67,178.81㎡ | — | ≤9.2m (보 하단) | 있음 |
| B1 | 주차 | 8,192.64㎡ | — | — | — |
| 1F | 창고 | 53,125.1㎡ | 2.5t/㎡ | 8.2m | 있음 |
| 2F | 사무 | 2,786.54㎡ | — | — | — |
| 3F | 창고 | 51,372.11㎡ | 2.5t/㎡ | 8.2m | 있음 |
| 4F | 사무 | 1,769.57㎡ | — | — | — |
| 5F | 창고 | 50,213.85㎡ | 2.5t/㎡ | 8.2m | 있음 |
| 6F | 사무 | 1,769.57㎡ | — | — | — |
| 7F | 창고 | 52,223.04㎡ | 2.5t/㎡ | 8.2m | 있음 |
| 8F | 사무 | 1,769.57㎡ | — | — | — |
| 9F | 창고 | 54,187.29㎡ | 2.5t/㎡ | 12.2m | 있음 |
| 10F | 사무 | 1,776.71㎡ | — | — | — |

**하역장·야드** (하역장 하부 = 위층 야드 데크 아래 구역. 층 대표 유효층고는 일반 구역 값)

| 층 | 접안 구획 폭×깊이 | 야드 깊이 | 하역장 하부 층고 / 유효층고 | 하역장 하부 면적 (층 면적 대비) |
|---|---|---|---|---|
| B2 | 3.2m × 9.0m | — | — / — | — |
| 1F | 3.2m × 13.0m | — | — / — | — |
| 3F | 3.2m × 13.0m | — | — / — | — |
| 5F | 3.2m × 13.0m | — | — / — | — |
| 7F | 3.2m × 13.0m | — | — / — | — |
| 9F | 3.2m × 13.0m | — | — / — | — |

### 단지 공용

| 항목 | 값 | 상태 | 출처 |
|---|---|---|---|
| 대지면적 | 93,741.0㎡ | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 1 [근거](output/wf2/yangji/crops/asset_x_x_site_area_m2_0.png) |
| 트럭야드 깊이 | 13.0m | 확정(교차) | 임대차계약서_별첨도면_추출본.pdf · page 4, sheet_no A-0303 [근거](output/wf2/yangji/crops/asset_x_x_truck_yard_depth_m_0.png) |

## 2. 스펙 경쟁력 — 벤치마크 포지셔닝

벤치마크 미적용 — WF1 벤치마크 DB가 아직 없다(구현 3단계).

## 3. IM–도면 정합성

| 항목 | IM 기재 | 도면 | 확정값 | 방향 |
|---|---|---|---|---|
| 도크 수 (main) | — | 764, 747 | 747 (확정) | — |
| 연면적 (main) | 349,722.27㎡, 349,722.27㎡ | 346,364.8㎡, 346,364.8㎡ | 346,364.8㎡ (확정) | IM 과장 |
| 구조형식 (main) | SRC, SRC | 복합 | 복합 (확정) | 방향 없음 |
| 층 용도 (main B1) | 사무 | 주차 | 주차 (확정) | 방향 없음 |

<!-- LLM:consistency -->

## 4. 입지 리스크

입지 조회 미실행 — 입지 룰(LC)은 구현 2단계에서 추가된다.

## 5. 리스크 평가 결과

### 🔴 SP02. 유효층고 미달 [main]

- **판정 입력:** warehouse_floors.clear_height_m=[1F 8.2; 3F 8.2; 5F 8.2; 7F 8.2; B2 ≤9.2 (보 하단); 9F 12.2]
- **적용 임계값:** clear_height.yellow=8.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP02@main -->
- **근본 원인:** <!-- LLM:root:SP02@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP02@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP02@main -->

### 🔴 SP05. 램프·차량 접근 제약 [main]

- **판정 입력:** floors_above=10, ramp_slope_pct=10.0, ramp_type=단방향, ramp_width_m=8.6
- **적용 임계값:** ramp_slope.red=9 (default, 검증); ramp_width.red=6.5 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP05@main -->
- **근본 원인:** <!-- LLM:root:SP05@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP05@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP05@main -->

### 🔴 SP06. 트럭야드 협소 [main]

- **판정 입력:** truck_yard_depth_m=13.0
- **적용 임계값:** truck_yard_depth.red=13 (default, 검증)
- **LLM 조정:** 🟢 → 🔴 (상향)
- **추론 근거:** <!-- LLM:basis:SP06@main -->
- **근본 원인:** <!-- LLM:root:SP06@main -->
- **연쇄 리스크:** <!-- LLM:cascade:SP06@main -->
- **DD 확인 포인트:** <!-- LLM:dd:SP06@main -->

### 🔴 V01. IM–도면 스펙 불일치

- **판정 입력:** v01.discrepancy_count=3, v01.overstated_count=1, v01.overstated_sensitive_count=0
- **추론 근거:** <!-- LLM:basis:V01@None -->
- **근본 원인:** <!-- LLM:root:V01@None -->
- **연쇄 리스크:** <!-- LLM:cascade:V01@None -->
- **DD 확인 포인트:** <!-- LLM:dd:V01@None -->

### 🟢 FR03. 스프링클러 형식 부적합 [main]

- **판정 입력:** sprinkler_type=혼합, warehouse_floors.clear_height_m.max=12.2
- **적용 임계값:** sprinkler_esfr_clear_height.red=13.7 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR03@main -->

### 🟢 FR05. 창고 내부 깊이 과대 (소방대 진입 거리) [main]

- **판정 입력:** warehouse_depth_m=66.0
- **적용 임계값:** warehouse_depth.red=77 (default, 검증)
- **추론 근거:** <!-- LLM:basis:FR05@main -->

### 🟢 G01. 배관 노후 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_piping.red=30 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G01@main -->

### 🟢 G02. 수변전설비 노후 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_substation.red=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G02@main -->

### 🟢 G03. 화물용 승강기·수직반송기 노후 [main]

- **판정 입력:** building_age=7, freight_elevator_count=4, vrc_count=4
- **적용 임계값:** aging_elevator.red=15 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G03@main -->

### 🟢 G04. 비상발전기 신뢰성 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_generator.red=30 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G04@main -->

### 🟢 G05. 스프링클러·제연 노후 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_fire_system.red=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G05@main -->

### 🟢 G06. 지붕 방수·배수 열화 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_roof.red=15 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G06@main -->

### 🟢 G07. 야드·램프 포장 열화 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_pavement.red=20 (default, 검증); aging_pavement.yellow=10 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G07@main -->

### 🟢 G08. 석면 함유 가능성 [main]

- **판정 입력:** regulation_flags.asbestos_total_ban_2009=없음
- **추론 근거:** <!-- LLM:basis:G08@main -->

### 🟢 G09. 법규 적합성·용도변경 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_compliance.yellow=20 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G09@main -->

### 🟢 G10. CapEx 종합 [main]

- **판정 입력:** building_age=7
- **적용 임계값:** aging_capex.yellow=15 (default, 검증)
- **보유기간 말:** 🟢 → ⚪
- **추론 근거:** <!-- LLM:basis:G10@main -->

### 🟢 SP03. 기둥 스팬·랙 효율 [main]

- **판정 입력:** column_span_x_m=11.0, column_span_y_m=11.0
- **적용 임계값:** column_span.yellow=11.0 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP03@main -->

### 🟢 SP04. 도크 부족 [main]

- **판정 입력:** dock_density=71.3
- **적용 임계값:** dock_density.red=50 (default, 검증)
- **추론 근거:** <!-- LLM:basis:SP04@main -->

### 🟢 SP07. 수직반송 의존 [main]

- **판정 입력:** handling_type=다층 램프형
- **추론 근거:** <!-- LLM:basis:SP07@main -->

### ⚪ FR01. 패널 심재 가연성 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 외벽 패널 심재 (main)
- **판정 입력:** panel_combustibility=—, roof_panel_combustibility=—
- **DD 확인 포인트:** 미확인 입력 확보; 외벽·지붕 판넬 심재 시험성적서·납품서; 대수선(2024 B2, 2026 1F·B2)에서 새로 설치한 방화벽체 판넬 심재 성능; 보험사 리스크 서베이 결과

### ⚪ FR02. 방화구획 대면적 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 방화구획 최대 면적 (main)
- **판정 입력:** fire_compartment_max_m2=—
- **DD 확인 포인트:** 미확인 입력 확보; 방화계획도의 층별 구획 면적과 방화셔터·스크린 위치(현행, 대수선 반영본); B2 스크린 방화셔터 7개소 작동 시험·장애물 적치 여부; IM '자동화 구간 드렌처' 주장의 설치 위치·작동 시험 증빙; 단일 동 길이(IM 주장 265.2m)·10개 층 구조에서 소방차 접근 면 수와 고층부 외부 방수 가능 범위

### ⚪ FR06. 오버헤드도어 하부 살수장애 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 오버헤드도어 하부 스프링클러 살수장애(헤드 미설치) (main)
- **판정 입력:** ohd_sprinkler_gap=—
- **DD 확인 포인트:** 미확인 입력 확보; 소방 평면도에서 층별 OHD 하부(문 안쪽) 헤드 유무와 도어 개방 시 간섭; 준공 후 소방 점검·CJ대한통운 Fire Audit 지적과 보완 여부(층별); Berth 구간 프리액션 설비(IM 주장)의 배관·헤드 배치 증빙

### ⚪ SP01. 바닥하중 미달 [main]

- **판정 보류 사유:** 일부 창고층 미확인 — 미확인 입력: —
- **판정 입력:** warehouse_floors.floor_load_tpm2.min=2.5
- **적용 임계값:** floor_load.red=1.5 (default, 검증)
- **DD 확인 포인트:** 미확인 입력 확보; 구조일반사항 설계하중표의 B2 포함 층별 값; 매입IM '2.0~2.5t/㎡' 하한 2.0이 적용되는 층·구역; 2025 메자닌(중2층 적층랙)과 2026 스파이럴 컨베이어 설치 구역의 구조 검토서; 바닥 균열·처짐 흔적

### ⚪ SP08. 대형차 회전반경 부족 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 대형차 최소 회전반경(램프·하역장 동선) (main)
- **판정 입력:** turning_radius_m=—
- **DD 확인 포인트:** 미확인 입력 확보; 램프 곡선부·하역장 출차부 R 표기가 있는 준공 평면도 확보; 40FT·세미트레일러 회전 궤적 검토(AutoTURN 등) 결과; 현장 주차 위치가 2023 주차계획(2안)과 같은지

### ⚪ SP09. 하역 동선 기둥 간섭 [main]

- **판정 보류 사유:** 입력 미확인 — 미확인 입력: 램프→하역장 동선 기둥 간섭(대형차) (main 1F), 램프→하역장 동선 기둥 간섭(대형차) (main 3F), 램프→하역장 동선 기둥 간섭(대형차) (main 5F), 램프→하역장 동선 기둥 간섭(대형차) (main 7F), 램프→하역장 동선 기둥 간섭(대형차) (main 9F), 램프→하역장 동선 기둥 간섭(대형차) (main B2)
- **판정 입력:** floors_with_dock_column_conflict=—
- **DD 확인 포인트:** 미확인 입력 확보; 층별 램프 출구→하역장 진입부 평면과 40FT 회전 궤적; CJ대한통운·B2 임차인의 차량 구성(40FT·세미트레일러 비중); 기둥보호대·유도 설비 설치 여부

### ⚪ V02. 핵심 스펙 미확인

- **판정 보류 사유:** 임계값 미정 — 미확인 입력: thresholds.yaml: V02 red/yellow
- **판정 입력:** v02.unconfirmed_ratio=0.37
- **DD 확인 포인트:** 미확인 입력 확보; 정식 준공 도면 세트(구조일반사항 설계하중표, 단면도, 재료마감표, 소방 평면도, 단선결선도) 확보; 확보 불가 항목(패널 심재, OHD 하부 헤드, 방화구획 면적)은 현장 실사 범위에 포함; V02 임계값 검증 후 재판정

## 6. 리스크 상관관계

- 상관관계 맵에 정의된 관계 중 양쪽이 모두 활성인 쌍이 없다.

## 7. DD 체크리스트

판정 보류(⚪) 항목을 먼저, 미확인 사유별로 묶었다. 자료 요청은 `yangji_data_request.md` 참조.

<!-- LLM:dd_checklist -->

## 부록 A. 필드별 추출 근거

§1 표의 출처 열과 `w2_05_confirmed_spec.json` 참조. 도면 판독값은 [근거] 링크로 크롭 이미지를 연다.

## 부록 B. 미검증 연쇄 제안

- ['SP02', 'SP05']: <!-- LLM:proposal:0 -->

## 갱신 이력

| 일시 | 변경 사유 | 재진입 지점 |
|---|---|---|
| — | 초안 | — |
