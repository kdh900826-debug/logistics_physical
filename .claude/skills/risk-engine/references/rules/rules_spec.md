# B. 스펙 기반 룰 (도면) — 7건

공통: `scope: per_building`, 층별 필드는 창고 용도 층만(`warehouse_floors.*`). 벤치마크 위치는 `benchmark_field`로 지정해 `benchmark_context`에 넣는다(B01 흡수).

## SP01. 바닥하중 미달

```yaml
id: SP01
category: spec
scope: per_building
floor_filter: warehouse
horizon: now
inputs: [warehouse_floors.floor_load_tpm2]
trigger: "true"
severity:
  red:    "warehouse_floors.floor_load_tpm2.min < th.floor_load.red"
  yellow: "warehouse_floors.floor_load_tpm2.min < th.floor_load.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: floor_load_tpm2
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 설계하중이 낮으면 고단 랙·중량 화물·지게차 운용이 제한된다. 보강은 사실상 불가능하다.
- **연쇄 리스크:**
  - → 재무: 임대료 할인, 공실 기간 증가
  - → 임대차: 중량물 임차인 유치 불가, 임차인 업종 제한
- **DD 확인 포인트:**
  - 구조일반사항 설계하중표의 층별 값
  - 미달 층의 면적 비중과 현재 적재 하중
  - 바닥 균열·처짐 흔적

## SP02. 유효층고 미달

```yaml
id: SP02
category: spec
scope: per_building
floor_filter: warehouse
horizon: now
inputs: [warehouse_floors.clear_height_m]
trigger: "true"
severity:
  red:    "min_below(warehouse_floors.clear_height_m, th.clear_height.red)"
  yellow: "min_below(warehouse_floors.clear_height_m, th.clear_height.yellow)"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: clear_height_m
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 유효층고가 낮으면 랙 단수가 줄어 보관 효율이 떨어진다. 이 룰은 **유효층고(바닥에서 천정·보·스프링클러 배관 하단까지)** 를 비교한다. 층고(FL~FL)가 아니다 — 시장 자료의 '층고 10m'를 그대로 기준으로 쓰지 않는다.
- **측정 기준(basis)과 상한값:** 유효층고 값마다 측정 기준(`basis`: 배관 하단·천장 하단·보 하단·슬래브 하단)을 기록한다. 보·슬래브 하단은 배관·덕트를 반영하지 않으므로 실제 유효층고의 **상한**(`precision: upper_bound`)이다. `min_below`는 층 값을 구간으로 보고 판정한다(2026-10-18 사용자 결정):
  - 어느 창고층이든 상한(또는 확정값)이 기준 미만 → 🔴 확정
  - 상한만 있는 층이 기준 이상 → ⚪ "상한값만 있음 — 배관 하단 확인 필요" (공제폭을 빼서 추정하지 않는다)
  - IM의 '유효고 n m 이상'(lower_bound)은 적힌 값으로 비교한다 — 기준 미만이면 🔴(원칙 5: '이상' 표기로 심각도를 낮추지 않는다. 화성 IM '8.2m 이상' → 🔴 유지)
  - 저온창고 유닛쿨러(배관) 하단은 국부 제약이라 유효층고 기준으로 쓰지 않는다 — note·DD 포인트로만 남긴다
  - 사례: 북항(golden bukhang p68) 도면 보 하단 8.55m인데 실측 배관 하단 8.025m(기준층), 9F 7.852m — 보 하단과 배관 하단 차이 약 0.5m
- **연쇄 리스크:**
  - → 재무: 평당 보관량 감소에 따른 임대료 경쟁력 저하
  - → 임대차: 자동화·고단 랙 임차인 유치 제약
- **DD 확인 포인트:**
  - 단면도 층고와 보·배관 하단 실측 유효고 — 도면 값이 보 하단 기준이면 스프링클러·덕트·조명 배관 하단 실측 확인
  - 저온창고 유닛쿨러(배관) 하단 높이와 그 아래 랙 배치 제약(북항: 유닛쿨러 배관 하단 6.3~6.5m)
  - 스프링클러 헤드 하단 이격 확보 여부
  - 층별 편차(저층 vs 상층)

## SP03. 기둥 스팬·랙 효율

```yaml
id: SP03
category: spec
scope: per_building
horizon: now
inputs: [column_span_x_m, column_span_y_m]
trigger: "true"
severity:
  yellow: "column_span_x_m < th.column_span.yellow or column_span_y_m < th.column_span.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: column_span_x_m
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 기둥 간격이 좁으면 표준 랙·통로 배치가 맞지 않아 손실 면적이 생긴다.
- **연쇄 리스크:**
  - → 재무: 유효 보관 면적 감소
  - → 임대차: 임차인 레이아웃 제약
- **DD 확인 포인트:**
  - 구조 그리드 치수와 표준 랙 배치 시뮬레이션
  - 하역장 구간 기둥 간섭

## SP04. 도크 부족

```yaml
id: SP04
category: spec
scope: per_building
horizon: now
inputs: [dock_density]
trigger: "true"
severity:
  red:    "dock_density < th.dock_density.red"
  yellow: "dock_density < th.dock_density.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: dock_density
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 연면적 대비 도크 수가 적으면 입출고 처리량이 제한된다.
- **연쇄 리스크:**
  - → 재무: 회전형(택배·이커머스) 임차인 대상 경쟁력 저하
  - → 임대차: 피크 시간 대기 차량 증가, 임차인 불만
- **DD 확인 포인트:**
  - 도크·도크레벨러 실제 수량과 배치
  - 층별 접안 가능 대수
  - 도크 증설 가능 구간

## SP05. 램프·차량 접근 제약

```yaml
id: SP05
category: spec
scope: per_building
horizon: now
inputs: [ramp_type, ramp_form, ramp_slope_pct, ramp_width_m, floors_without_direct_access, floors_above]
trigger: "floors_above > 1 and (ramp_type != '없음' or ramp_slope_pct != null)"   # 옥외 대지 경사로 경사가 확인되면 램프 통행 표기가 없어도 판정(2026-10-21)
severity:
  red:    "ramp_slope_pct > th.ramp_slope.red or ramp_width_m < th.ramp_width.red"
  yellow: "count(floors_without_direct_access) > 0"     # 램프 경사·폭은 🔴 단일 등급(2026-10-13 사용자 결정)
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: ramp_slope_pct
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 램프 경사가 급하거나 폭이 좁으면 대형 화물차 통행 속도·안전이 떨어지고, 직접접안이 안 되는 층은 수직반송에 의존한다.
- **연쇄 리스크:**
  - → 재무: 상층부 임대료 할인
  - → 임대차: 동절기 결빙·사고 리스크, 대형차 운용 제약
  - → 법률: 차량 사고 시 시설 책임
- **DD 확인 포인트:**
  - 램프 실측 경사·폭(곡선부 포함)
  - 40FT 컨테이너·세미트레일러 출차 회전: 하역장 주차 위치에서 출차 램프까지 한 번에 진입 가능한지(도면 회전반경 표기, 현장 주차 위치가 준공도면과 같은지), 곡선구간 교행 가능 폭 — 사례: 이천 송온리 B2 램프 폭 4m·최좌측 40FT 1회 진입 불가(golden songon p40)
  - 램프→하역장 진입 동선상 기둥 간섭: 램프 출구에서 하역장으로 꺾는 구간에 기둥이 있으면 40FT가 한 번에 들어가지 못하고 반대차선을 침범한다 — 대안(기둥보호대·안내원·대형차 다른 층 유도)과 그 층 임차인 차량 구성 확인. 사례: 송온리 1센터 2층(golden songon1 p21)
  - 층별 직접접안 가능 여부
  - 램프 결빙 방지(열선) 설비
  - 옥외 대지 경사로(지형 단차 진입도로로 야드에 붙는 자산): 건물 램프와 같이 판정한다(2026-10-20 사용자 지시). 지붕 없는 경사로라 겨울철 결빙이 직접 온다 — 열선(로드히팅) 설치 구간, 제설 장비·제설제 운용 계획, 적재 트레일러 등판·제동 사고 이력, 9% 초과 구간의 길이와 곡선부 겹침. 사례: 와이드크릭 군량리B 대지 경사로 S=-15.0%·10.0%, 양평리 s=10.0%·9.51%

## SP06. 트럭야드 협소

```yaml
id: SP06
category: spec
scope: per_building
horizon: now
inputs: [truck_yard_depth_m]
trigger: "true"
severity:
  red:    "truck_yard_depth_m < th.truck_yard_depth.red"
  yellow: "truck_yard_depth_m < th.truck_yard_depth.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: truck_yard_depth_m
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 야드 깊이가 대형 트레일러 회전·후진 접안에 필요한 거리보다 짧다.
- **입력 정의:** 실내 하역장은 단지 값 `truck_yard_depth_m`(접안 구획 깊이, 🔴 13m). 옥외 야드(지형접안형 등 층별 야드)는 층별 `yard_depth_m`(차로 포함 야드 전체 깊이) 최솟값이고 세그먼트 `yard_type: 옥외` 임계값(접안 세미트레일러 16.7m + 통행 1차로 3.25m = 19.95m)을 쓴다 — 하역 중에도 그 뒤로 차량이 지나갈 수 있어야 한다(2026-10-20 사용자 지시).
- **연쇄 리스크:**
  - → 재무: 대형차 임차인 유치 제약
  - → 임대차: 접안 지연, 단지 내 정체
- **DD 확인 포인트:**
  - 도크 전면 야드 깊이 실측
  - 대기 차량 공간과 진출입 동선
  - 옥외 야드: 접안 차량 뒤 통행 차로가 실제로 비어 있는지(야드 내 대기·불법 주차, 반대편 주차 구획 사용 실태), 후진 접안 회전 궤적(기준 미반영)
  - 실내 하역주차장(지하층 등)의 대형차 회전 궤적: 주차 구획별로 40FT 차량이 출차할 수 있는지(golden songon p40)

## SP08. 대형차 회전반경 부족

```yaml
id: SP08
category: spec
scope: per_building
horizon: now
inputs: [turning_radius_m]
trigger: "true"
severity:
  red:    "turning_radius_m < th.turning_radius.red"
  yellow: "turning_radius_m < th.turning_radius.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
benchmark_field: turning_radius_m
provenance: {source: golden_songon, deals: [], approved: null}
```

- **근본 원인:** 램프 곡선부나 하역장→출차 램프 진입부의 회전반경이 대형차(세미트레일러·40FT 컨테이너)의 최소 회전반경에 못 미치거나 여유가 없으면, 차량이 한 번에 돌지 못해 후진·재진입이 필요하다. 주차 위치가 준공도면과 다르면 실제 여유는 도면보다 더 작다.
- **연쇄 리스크:**
  - → 재무: 대형차(컨테이너) 임차인 유치 제약, 동선 개선 공사비
  - → 임대차: 출차 지연·정체, 주차 구획 축소로 운영 차질
  - → 법률: 회전 중 충돌 사고 시 시설 책임
- **DD 확인 포인트:**
  - 도면 R 표기(램프 곡선부, 하역장 출차부)와 현장 주차 위치 일치 여부
  - 40FT 컨테이너·세미트레일러 회전 궤적 검토(AutoTURN 등) 결과
  - 저온층 상온 전환 시 대형차 운행 가능 여부 — 사례: 이천 송온리 B2 R-12M, 최좌측 40FT 1회 진입 불가(golden songon p40)

## SP09. 하역 동선 기둥 간섭

```yaml
id: SP09
category: spec
scope: per_building
horizon: now
inputs: [floors_with_dock_column_conflict]
trigger: "true"
severity:
  yellow: "count(floors_with_dock_column_conflict) > 0"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: golden_songon1, deals: [], approved: null}
```

- **근본 원인:** 램프 출구에서 하역장으로 꺾는 동선에 기둥이 있으면 40FT 트레일러 같은 대형차가 한 번에 들어가지 못하고 반대차선을 침범한다. 구조 기둥이라 사후 개선이 어렵고, 운영(안내원·기둥보호대·대형차 다른 층 유도)으로만 대응한다.
- **연쇄 리스크:**
  - → 재무: 해당 층 대형차 임차인 유치 제약, 임대료 할인
  - → 임대차: 진출입 지연·정체, 다른 층으로 유도하면 층별 운영 제약
  - → 법률: 기둥·차량 충돌 사고 시 시설 책임
- **DD 확인 포인트:**
  - 간섭 층의 하역장 진입·진출구 평면과 대형차 회전 궤적
  - 그 층 임차인의 차량 구성(40FT·세미트레일러 비중)과 대체 동선(다른 층 유도) 가능 여부
  - 기둥보호대·유도 설비 설치 여부
- **LLM 상향 기준:** 간섭 층이 대형차 주 하역층이거나 대체 동선이 없으면 🔴 검토. 사례: 송온리 1센터 2층(golden songon1 p21, p61)

## SP07. 수직반송 의존

```yaml
id: SP07
category: spec
scope: per_building
horizon: now
inputs: [handling_type]
trigger: "true"
severity:
  yellow: "handling_type == '다층 승강기형'"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: engine_v1, deals: [], approved: null}
```

- **근본 원인:** 다층 승강기형은 상층부 입출고가 승강기·수직반송기 처리 용량에 묶인다.
- **연쇄 리스크:**
  - → 재무: 상층부 임대료 할인, 공실 장기화
  - → 임대차: 승강기 고장 시 층 단위 운영 중단
- **DD 확인 포인트:**
  - 승강기·수직반송기 대수·용량 대비 층 면적
  - 피크 시간 처리량 실적

## SP10. 창고 상부 데크 야드·램프 (하부·접합부 누수)

```yaml
id: SP10
category: spec
scope: per_building
horizon: now
inputs: [floors_with_under_yard, floors_with_under_ramp]
trigger: "count(floors_with_under_yard) > 0 or count(floors_with_under_ramp) > 0"
severity:
  green:  "otherwise"      # 등급 없이 실사 포인트만 표시(dd_on_green). 등급 부여는 사용자 결정 사항
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
dd_on_green: true
provenance: {source: user_2026-10-20, deals: [widecreek_gunryang_a, widecreek_gunryang_b, widecreek_yangpyeong, songon], approved: null, note: "2026-11-11 램프 접합·하부 창고 추가(송온리 2센터 사후 누수)"}
```

- **근본 원인:** 차량이 다니는 슬래브(위층 야드 데크, 건물 램프)가 창고 위에 얹히거나 창고 외벽·지붕에 붙으면, 차량 반복 하중·제동, 방수층 손상, 배수 구배·드레인 불량, 램프-건물 접합부 후레싱·판넬 이음부 틈이 겹쳐 아래·옆 창고로 누수가 생기기 쉽다. 경사지 다층 지형접안형은 위층 야드가 아래층 창고 위에 얹히고, 다층 램프형은 램프 구조체가 창고 위를 지나거나 외벽에 붙는다. 데크를 받치는 보·슬래브가 깊어 하부 구역의 유효층고도 일반 구역보다 낮다.
- **연쇄 리스크:**
  - → 재무: 데크·램프 방수 재시공·균열 보수 CAPEX(보수 중 야드·램프 일부 폐쇄), 하부 창고 차수판·물받이 같은 임시 조치 반복
  - → 임대차: 하부 창고 누수로 화물 손상 클레임, 하부 구역 랙 단수 제약, 자동화 설비(로봇·컨베이어) 운행 차질
  - → 법률: 하자담보 기간 내 누수 하자 청구 시한, 시공사가 하자를 처리하지 못하면 하자보수보증 청구
- **DD 확인 포인트:**
  - [데크 야드] 방수층 사양과 보호층(보호 콘크리트·아스팔트), 신축이음·트렌치·루프드레인 위치와 바로 아래 창고 천장의 누수 흔적
  - [데크 야드] 데크 설계 차량하중(예: DB-24)과 포장 균열·처짐, 제설제 사용에 따른 방수층·철근 부식
  - [데크 야드] 하역장 하부 구역 유효층고 실측과 그 구역 랙 배치·단수(층 대표 유효층고와 별도로 판단)
  - [램프] 램프 접합·하부 창고 구역(그리드 위치)의 천장·기둥 상부 누수 흔적, 램프 난간 후레싱·이중벽·판넬 이음부 코킹, 램프 상부 선홈통·거터 위치 — 사례: 송온리 2센터 1층 램프 하부(Y7~8열) 기둥 상부 누수가 준공 후 2년 넘게 재발해 자동화 구역 상부에 차수판을 두 번 설치했다(golden songon incidents.yaml, DD p42가 램프 난간 후레싱 누수를 미리 지적)
  - [공통] 누수 사고·하자 처리 이력(준공 후 첫 장마·첫 겨울), 같은 부위 재발 여부 — 하자·누수 펀치리스트가 있으면 데크·램프 하부 구역 항목을 대조
  - [공통] 하부 구역 임차인 용도(자동화 설비·고가 화물)와 차수판·물받이 같은 임시 조치 여부

## SP11. 상온창고 기계 환기 부재 (곰팡이·고온다습)

```yaml
id: SP11
category: spec
scope: per_building
horizon: now
inputs: [floors_without_mech_ventilation]
trigger: "count(floors_without_mech_ventilation) > 0"
severity:
  green:  "otherwise"      # 등급 없이 실사 포인트만 표시(dd_on_green). 등급 부여는 사용자 결정 사항
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
dd_on_green: true
provenance: {source: user_2026-11-11, deals: [songon], approved: null}
```

- **근본 원인:** 상온창고는 급배기팬·유인팬 같은 기계 환기 없이 자연 환기에만 기대는 경우가 많다. 대공간에 공기가 정체되면 여름철 고온다습과 결로로 적재 화물(신발·의류·종이 포장 등)에 곰팡이가 생기고 근무 환경이 나빠진다. 지하층·외기 접촉이 적은 층·저온층과 맞닿은 층이 더 취약하다.
- **연쇄 리스크:**
  - → 재무: 제습기·실링팬·급배기팬 추가 CAPEX, 전력 증설 필요 여부
  - → 임대차: 화물 곰팡이 손상 클레임(원인이 건물인지 유통 과정인지 다툼), 임차인 자체 설비 설치 요청, 재임대 시 화주 기피
  - → 법률: 임대인 시설 하자인지 임차인 보관 관리 책임인지 계약상 경계
- **DD 확인 포인트:**
  - 기계설비 도면(환기 계통도·장비일람표)에서 창고 구역 급배기팬·기류유인팬·전열교환기 유무와 환기 횟수 설계값. 냉동기계실·전기실 등 실별 환기팬은 창고 환기로 보지 않는다
  - 매매계약·설계변경 조건에 상온창고 제습·환기가 있었는데 준공에서 빠졌는지 — 사례: 송온리 2센터는 매매계약 2차 변경 조건에 하이브리드 창고의 상온용 제습·환기(급배기팬·기류유인팬) 설계가 있었으나, DD(p60)가 상온창고·사무실 기계 환기 미반영(추가 약 1.4억 원)을 지적했다. 운영 2년 차에 1층 임차인 화물 곰팡이 클레임이 나와 제습기 11대 설치를 검토했고, 2층 임차인은 고온다습 때문에 실링팬을 자체 설치했다(golden songon incidents.yaml)
  - 운영 중 화물 곰팡이·결로 클레임 이력, 임차인이 자체 설치한 제습기·실링팬과 그 소유·원상복구 조건
  - 여름철 창고 내부 온습도 기록(BMS·임차인 계측), 제습·환기 설비 추가 견적과 수전 여유
