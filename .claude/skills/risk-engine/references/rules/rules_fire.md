# C. 화재 룰 (물류센터 핵심) — 4건

법규 시행일 비교는 `regulation_flags.<id>`를 쓴다. `regulation_timeline.yaml`의 해당 항목이 `verified: false`면 그 변수는 null이 되어 ⚪이다.

## FR01. 패널 심재 가연성

```yaml
id: FR01
category: fire
scope: per_building
horizon: now
inputs: [panel_combustibility, roof_panel_combustibility]
trigger: "true"
severity:
  red:    "panel_combustibility == '가연' or roof_panel_combustibility == '가연'"
  yellow: "panel_combustibility == '난연' or roof_panel_combustibility == '난연'"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** EPS 등 가연성 심재 샌드위치 패널은 화재 시 급격한 연소 확대와 유독가스를 낳는다. 물류센터 대형 화재의 반복 원인이다.
- **연쇄 리스크:**
  - → 재무: 화재보험료 상승·인수 거절, 전손 리스크
  - → 임대차: 화재 시 장기 운영 중단, 임차인 이탈
  - → 법률: 마감재 기준 강화 이전 준공분의 개선 요구 가능성
- **DD 확인 포인트:**
  - 외벽·지붕 패널 심재 시험성적서·납품서
  - 부분 교체 여부(증축·보수 구간 심재 혼재)
  - 보험사 리스크 서베이 결과

## FR02. 방화구획 대면적

```yaml
id: FR02
category: fire
scope: per_building
horizon: now
inputs: [fire_compartment_max_m2]
trigger: "true"
severity:
  red:    "fire_compartment_max_m2 > th.fire_compartment_area.red"
  yellow: "fire_compartment_max_m2 > th.fire_compartment_area.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 방화구획이 크면 화재가 한 구획 안에서 크게 번진다. 창고 특례 등으로 대면적 구획이 허용된 경우가 많다.
- **연쇄 리스크:**
  - → 재무: 최대 추정 손실(PML) 증가, 보험 조건 악화
  - → 임대차: 복수 임차인 동시 피해
- **DD 확인 포인트:**
  - 방화계획도의 구획 면적과 방화셔터 위치
  - 방화셔터 작동 시험·장애물 적치 여부
  - 구획 변경(대수선) 시 인허가 반영 여부
  - 화재 확산·진압 조건(구획 면적만으로 안 보이는 요인): 여러 동이 연결된 대규모 구조인지, 창고 내부 깊이(외벽에서 가장 먼 지점까지 — 소방대 내부 진입 거리), 소방차가 접근할 수 있는 면 수와 진입·진출 분리 순환 동선, 발화 지점이 고층부면 외부 직접 방수가 어려운 층수, 피난 보행거리 — 사례: 인천 석남동 쿠팡 물류센터 화재(2개 동 연결, 지하1~지상8층, 창고 내부 깊이 약 77m)를 비교한 원창 IM 분석(kb/rule_candidates/20261013_fire_wonchang_candidates.md). 골든 seoknam(석남동 223-41)과는 다른 자산

## FR03. 스프링클러 형식 부적합

```yaml
id: FR03
category: fire
scope: per_building
floor_filter: warehouse
horizon: now
inputs: [sprinkler_type, warehouse_floors.clear_height_m]
trigger: "true"
severity:
  red:    "sprinkler_type in ['표준형', '준비작동식'] and warehouse_floors.clear_height_m.max > th.sprinkler_esfr_clear_height.red"
  yellow: "sprinkler_type == '혼합' and warehouse_floors.clear_height_m.max > th.sprinkler_esfr_clear_height.red"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 높은 층고에 고단 적재를 하면서 표준형 헤드만 설치하면 랙 상부 화재를 제어하지 못한다.
- **연쇄 리스크:**
  - → 재무: 보험 인수 조건 악화, 랙 인랙 추가 설치 CAPEX
  - → 임대차: 적재 높이 제한으로 보관 효율 저하
  - → 법률: 창고시설 화재안전기준 부적합 지적
- **DD 확인 포인트:**
  - 헤드 종류(ESFR·표준형·랙 인랙)와 설치 높이
  - 실제 적재 높이와 상품 등급
  - 수원·펌프 용량이 ESFR 기준을 충족하는지
  - 임차인 파렛트랙·메자닌 계획 대비 살수 제한: 복잡한 인랙·메자닌 구조는 천장 헤드 살수를 막는다. 유수검지장치별 인랙용 분기배관·밸브가 미리 반영돼 있는지, 메자닌 하부 헤드 추가 계획이 있는지(원창 IM은 '선반영'을 주장 — 도면·시공 확인 전까지 주장값)
  - 준공 후 소방 점검 지적: 출입문 개방 시 살수장애, 공기흡입형 감지기·덕트가 헤드 살수 반경을 가림(golden songon1 incidents)

## FR05. 창고 내부 깊이 과대 (소방대 진입 거리)

```yaml
id: FR05
category: fire
scope: per_building
horizon: now
inputs: [warehouse_depth_m]
trigger: "true"
severity:
  red:    "warehouse_depth_m >= th.warehouse_depth.red"      # 기준 사례(석남동 화재 약 77m) 자체가 걸리도록 이상(>=)
  yellow: "warehouse_depth_m >= th.warehouse_depth.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: im_wonchang_2026_p34, deals: [], approved: null}
```

- **근본 원인:** 창고 내부가 깊으면 소방대가 외벽에서 발화 지점까지 들어가는 거리가 길어 내부 진입·진압이 불리하고, 외부 방수가 닿지 않는 구역이 넓어진다. 여러 동이 연결되거나 고층부에서 발화하면 더 불리하다.
- **연쇄 리스크:**
  - → 재무: 최대 추정 손실(PML) 증가, 화재보험 인수 조건 악화
  - → 임대차: 화재 시 장기 운영 중단, 복수 임차인 동시 피해
  - → 법률: 화재 원인·확산 책임 분쟁
- **DD 확인 포인트:**
  - 창고층 평면의 내부 깊이(하역장 측 벽~반대편 벽, 하역장 제외)와 소방대 진입구(외벽 개구부·비상용 진입창) 위치
  - 소방차가 붙을 수 있는 면 수와 진입·진출 분리 동선, 고층부 외부 방수 가능 범위
  - 여러 동이 같은 층에서 연결돼 있는지(연기·열 확산 경로)
- **사례:** 인천 석남동 쿠팡 물류센터 화재 — 2개 동 연결, 창고 내부 깊이 약 77m. 비교 자산 원창 약 53m(IM 주장). 원창 IM p34(kb/rule_candidates/20261013_fire_wonchang_candidates.md). 골든 seoknam과는 다른 자산

## FR06. 오버헤드도어 하부 살수장애

```yaml
id: FR06
category: fire
scope: per_building
horizon: now
inputs: [ohd_sprinkler_gap]
trigger: "true"
severity:
  yellow: "ohd_sprinkler_gap == true"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: golden_hyeonbang_seoknam_songon, deals: [], approved: null}
```

- **근본 원인:** 하역장·출하장 오버헤드도어를 열면 감긴 도어(또는 수평 레일 위 도어 패널)가 천장 스프링클러 헤드 아래를 가려 문 주변 바닥까지 물이 닿지 않는다. 하역장은 화물·팔레트·차량이 몰리는 곳이라 초기 진압이 안 되면 창고 안으로 번진다. 도어를 열어 둔 채 운영하는 시간이 길수록 노출된다.
- **연쇄 리스크:**
  - → 재무: 하역장 발화 시 손실 확대, 보험 서베이 지적·조건 악화. 보완 비용은 대개 작다(하향식·측벽식·드라이펜던트 헤드 추가)
  - → 임대차: 임차인 소방 점검(Fire Audit) 지적 → 임대인 보완 요구
  - → 법률: 소방 종합정밀점검 지적사항
- **DD 확인 포인트:**
  - 소방 평면도에서 OHD 하부(문 안쪽) 헤드 유무, 실제 도어 개방 시 헤드와의 간섭
  - 준공 후 소방 점검·임차인 Fire Audit 지적과 보완 여부(층별)
  - 냉동창고 출입문·유니트쿨러 주변 미경계구역(드라이펜던트 헤드)
- **사례:** 골든 5곳 중 4곳에서 같은 지적 — 현방 A·B동(p15, p100), 석남(p184-185), 송온2(p65, p84, p95), 송온1(2021-12 임차인 소방 정밀점검, incidents). 청라는 출하장 OHD 부분 헤드 추가 사진(p282)
- **LLM 상향 기준:** 하역장이 크고 도어 수가 많거나, 상온 대형 하역장(라지드롭·ESFR 천장형만)인데 보강 계획이 없으면 🔴 검토

## FR04. 저온동 단열재 화재

```yaml
id: FR04
category: fire
scope: per_building
horizon: now
inputs: [has_cold, cold_insulation_combustibility, cold_ratio]
trigger: "has_cold == true"
severity:
  red:    "cold_insulation_combustibility == '가연' and cold_ratio >= th.cold_fire.cold_ratio_red"
  yellow: "cold_insulation_combustibility in ['가연', '난연']"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: mapping_v1, deals: [], approved: null}
```

- **근본 원인:** 저온창고 단열재(우레탄·EPS)는 두께가 두꺼워 화재 하중이 크고, 시공 중 화재(용접) 사례가 많다.
- **연쇄 리스크:**
  - → 재무: 저온동 전손 리스크, 보험료 상승
  - → 임대차: 저온 임차인 운영 중단
- **DD 확인 포인트:**
  - 저온동 단열재 종류·두께와 난연 성능 시험서
  - 화기 작업 관리 절차
