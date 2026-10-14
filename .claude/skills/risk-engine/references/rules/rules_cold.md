# D. 저온 특화 룰 — 4건

공통: 저온·냉동 면적이 있는 동(`has_cold == true`)에서만 발동한다.

## CL01. 냉동설비·냉매 리스크

```yaml
id: CL01
category: cold
scope: per_building
horizon: both
inputs: [has_cold, refrigerant, building_age]
trigger: "has_cold == true"
severity:
  red:    "refrigerant == '암모니아' or building_age >= th.cold_refrigeration_age.red"
  yellow: "refrigerant == '프레온계열' or building_age >= th.cold_refrigeration_age.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 암모니아는 누출 시 독성·폭발 위험과 안전관리 의무가 크고, 프레온 계열(R-22, R-404A 등)은 감축 규제로 냉매 수급·교체 부담이 있다. 압축기·응축기는 연식에 따라 효율이 떨어진다.
- **연쇄 리스크:**
  - → 재무: 냉매 전환·설비 교체 CAPEX, 전력비 증가
  - → 임대차: 냉동설비 고장 시 화물 손상 배상
  - → 법률: 고압가스·화학물질 안전관리 의무
- **DD 확인 포인트:**
  - 냉동기 형식·냉매 종류와 고압가스 허가·검사 이력
  - 냉동설비 소유(임대인/임차인)와 교체 책임
  - 압축기 운전시간·오버홀 이력

## CL02. 바닥 동상

```yaml
id: CL02
category: cold
scope: per_building
horizon: now
inputs: [has_cold, cold_floor_heave_protection]
trigger: "has_cold == true"
severity:
  red:    "cold_floor_heave_protection == false"
  green:  "otherwise"
on_missing: hold
llm_adjust: none
adjust_basis: []
manifest_years: 5
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 냉동창고 바닥 아래 지반이 얼면 융기(동상)로 바닥이 들뜨고 균열이 생긴다. 바닥 히팅·환기 배관 같은 방지 설비가 필요하다.
- **연쇄 리스크:**
  - → 재무: 바닥 철거·재시공 CAPEX(운영 중단 동반)
  - → 임대차: 랙 기울어짐·지게차 운행 장애
- **DD 확인 포인트:**
  - 바닥 상세도의 동상 방지 설비(히팅 코일·환기관)
  - 설비 작동 상태와 바닥 레벨 측정 결과

## CL03. 단열 패널 열화·결로

```yaml
id: CL03
category: cold
scope: per_building
horizon: both
inputs: [has_cold, building_age, cold_insulation_material]
trigger: "has_cold == true"
severity:
  red:    "building_age >= th.cold_insulation_age.red"
  yellow: "building_age >= th.cold_insulation_age.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_or_confirmed_down
adjust_basis: [replacement_history]
manifest_years: 3
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 단열 패널 이음부 실링이 열화하면 결로·결빙과 냉기 손실이 생긴다.
- **연쇄 리스크:**
  - → 재무: 패널 보수·교체 CAPEX, 전력비 증가
  - → 임대차: 온도 유지 실패로 화물 품질 클레임
- **DD 확인 포인트:**
  - 패널 이음부 결로·결빙 흔적
  - 도어·도크씰 기밀 상태

## CL04. 온도대 전환 유연성

```yaml
id: CL04
category: cold
scope: per_building
horizon: now
inputs: [has_cold, cold_ratio, refrigerant]
trigger: "has_cold == true"
severity:
  yellow: "refrigerant == null"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** IM이 '저온↔상온 전환 가능'을 주장해도 냉동설비·단열·바닥 동상 방지 근거가 도면에서 확인되지 않으면 전환 비용과 기간을 알 수 없다. 이 룰은 설비 근거 확인 여부만 기계적으로 보고, IM 서술형 주장은 risk-evaluator가 근거와 대조해 서술한다.
- **연쇄 리스크:**
  - → 재무: 전환 공사비(설비 철거·신설), 전환 기간 공실
  - → 임대차: 저온 임차인 이탈 시 대체 임차인 범위 제한
- **DD 확인 포인트:**
  - 전환 이력·계획(공사비, 인허가)
  - 전환 대상 구역의 냉동설비·단열·바닥 상세
  - 전환 이력의 흔적: 냉동↔상온 변경 시 바닥 마감 두께가 달라 창고와 ELEV홀·전실·도크 경계에 단차가 생긴다(경사로 등 보완 필요). 골조 완료 후 변경된 층이 있는지, 수전·냉동설비 용량도 같이 줄었는지 확인 — 사례: 송온리 1센터 2층 단차·수전 4,000→3,500kW(golden songon1 p19, p48)
  - 냉동 하역장의 기둥 간격·동선: 냉동층은 소형 냉동차(최대 5톤) 기준이라, 상온 전환 후 대형차가 기둥 사이를 통과하기 어려울 수 있다(golden songon1 p14)
  - 전환 후 차량 구성 변화: 저온층으로 쓸 때는 40FT 컨테이너 운행이 없어 드러나지 않던 램프 폭·회전반경 제약이 상온 전환 후 40FT 컨테이너 운행에서 드러난다(golden songon p40 — B2 상온 운영 시 40FT 출차 제한)
  - 냉동(영하) → 냉장·상온 전환 시 소방·환기 신설 비용: 냉동창고는 영하라 스프링클러·옥내소화전이 면제돼 없는 경우가 많다. 전환하면 새로 설치해야 한다 — 사례: 송온리 1센터 B2·1F 냉동→냉장 소방·환기 추가공사 공급가 20.5억원(약 6.7만원/㎡, golden songon1 incidents.yaml)
  - 임대차·인수인계서의 전환 관련 하자 책임: 임차인이 저온층을 상온으로 쓰다가 다시 냉동·냉장으로 바꿀 때 단열 크랙 등 하자를 임대인이 책임지는 조항(원상복구 면제 포함)이 있는지 — 사례: 송온리 1센터 인수인계확인서(2022.05)
  - 전환 인허가 경로와 기간: 해체심의 인허가 + 대수선 인허가(대수선 통상 1개월, 보완·조건부 시 총 6주 이내), 철거 심의 1개월 병행, 착공필증 1개월 이내. 매입 전 진행하려면 현 소유자 동의 필요. 업체 선정부터 착공까지 약 7개월 사례(원창 IM) — `conversion_cases.yaml`
  - 전환 공사비 시장 범위(저온→상온): 30만 ~ 52만원/평(전환 대상 창고면적 기준, 예비비 별도, 6개 센터). 소방설비 전면 교체 여부·기둥 단열 마감 철거 여부·챔버 구획 유지 여부가 차이를 만든다 — 대상 자산 견적의 범위 포함 여부를 확인(`conversion_cases.yaml`)
  - 전환 견적 검토: 인허가(대수선·해체) 분리, 폐기물 처리비, 판넬·방화셔터·OHD 수량, 바닥 마감 중복, 이미 철거된 장비 철거비, 간접비 요율 — `conversion_cases.yaml` estimate_review_checklist. 사례: 상봉리 B1 견적 12.87억 → 실사 검토 7.32억(57%), 수정 견적 11.47억(소방 포함, 약 39.5만원/평)
  - 전환 뒤 효과·설계: 저온 전용 변압기 휴지와 계약전력 하향(상봉리 2,900→1,900kVA), 저온·상온 바닥 마감이 같은 설계인지(같으면 단차·바닥 재시공 없음) — 공사 범위는 원창 IM 5단계(사전진단→설계변경→철거→건축·설비 재시공→소방 보강·시운전)
  - 부분 전환이면 남는 저온층과 새 상온층 경계의 열교·결로 대책(천정·바닥 추가 방열)이 견적에 있는지 — 사례: 석남 SNK A구간 1~3층 상온화 견적에 1층 천정 추가 방열 100T 5.1억(직접공사비의 약 15%)
  - 방화구획선 이동(하역장 방화셔터 ↔ 도크 저온 OHD 맞교체, OHD 철거부 상부 방화벽)과 시공사 견적·사업주 직발주(설계·인허가·감리·전기·소방) 범위 분리 — 석남 SNK 직발주분 8.7억(전체 49.78억의 약 17%). `conversion_cases.yaml`
