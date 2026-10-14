# 룰 후보 — 대형 물류센터 화재 확산·진압 조건 (2026-10-13)

- 상태: **WATCHLIST** (FRC1은 FR05로 승격, FRC2·FRC3은 유지) (지지 딜 1건 < min_support 2, 근거가 사후 결과 문서가 아니라 매각·주선 측 IM의 비교 서술)
- 출처: `[NHIS] 그레이트 원창 물류센터 매입 담보대출_v3.0_20260908.pdf` (NH투자증권 IM v3.0, 2026.09), 인쇄 쪽 34~35(PDF p35~36) 'Ⅳ.6 화재 예방 및 대응 방안'. 표 원출처는 큐브인더스트리얼자산운용
- 사용자 지시: "34~35페이지, 화재 관련 학습해줘"
- 반영: 기존 룰 FR02·FR03의 DD 확인 포인트에 추가(`rules_fire.md`). 아래 후보는 판정 룰로 넣지 않았다 — 새 필드가 필요하고 임계값 근거가 없다.

### 근거 요약 (IM 기재 그대로, 검증 전)

| 항목 | 인천 석남동 물류센터 (화재 발생) | 그레이트 원창 물류센터 (본건) |
|---|---|---|
| 주소 | 인천시 서구 석남동 229-3 | 인천시 서구 원창동 393-53 |
| 연면적 | 299,247.26㎡ (90,523.60평) | 111,959.24㎡ (33,867.67평) |
| 규모 | 지하1층~지상8층(창고층 8개), **2개 동** | 지하1층~지상10층(창고층 8개), 1개 동 |
| 높이 / 창고 내부 깊이 | 79.6m / 약 77m | 87m / 약 53m |
| 도면 표기 | 1동·2동 같은 층에 '발화층' 표시 | — |

IM이 든 **화재 발생 리스크**(석남동 사례):
- 발화·확산: 2개 동이 연결된 대규모 구조라 연기·열 확산 위험이 크다. 복잡한 인랙·메자닌 구조로 스프링클러 살수가 제한될 수 있다.
- 외부 소방 한계: 발화 지점이 고층부면 외부 직접 방수가 어렵다. 건물 내부 깊이가 길어 소방대 내부 진입·진압이 불리하다.

IM이 든 **본건(원창)의 대응** — 매도·주선 측 주장, 도면·현장 확인 전:
- 3면이 도로에 접한 단일 동, 소방차 진입·진출구 분리 순환 동선, 창고 내부 깊이가 짧아 소방대 진입·방수에 유리
- 각 층에서 외부 출구까지 보행거리 100m 이하
- 유수검지장치별 인랙 스프링클러용 분기배관·밸브 설치, 실제 랙·메자닌 계획에 맞춰 인랙 추가
- 준비작동식 스프링클러(분당 80L / 20분 이상), 수원 총 59㎥(옥내소화전 13 + 옥외소화전 14 + 스프링클러 32), 옥내소화전 비상전원 20분 이상
- 배전반·분전반 패치형 자동소화장치, 공기흡입형 감지기, 감지기 위치표시, 비상방송·자탐, 유도등·피난유도선
- 점검·훈련: 자탐·제연·방송 일일·연동점검(연 2회), 직무교육 매월, 비상 훈련 분기, 소방대 협업 연 1회

주의:
- 석남동 화재 사례의 발생일·원인·피해 규모는 이 IM에 없다. 다른 출처 없이 적지 않았다.
- 골든 `seoknam`(인천 석남 물류센터, 석남동 223-41, 단일 동 B1~10F, 148,238㎡)은 **다른 자산**이다.
- 원창 자산의 상온 컨버전(IM p34, 소방설비 부분 수정 포함 평단가 416,568원(E))은 별도 학습 대상이다.

### 후보 목록

각 후보는 새 Core Spec 필드가 필요하다. 임계값은 근거가 없어 비워 두었다(⚪).

## FRC1. 창고 내부 깊이 과대 (소방대 진입 거리)

```yaml
id: FRC1
category: fire
scope: per_building
horizon: now
inputs: [warehouse_depth_m]           # 신규 필드 후보: 외벽(소방 진입면)에서 창고 내부 가장 먼 지점까지 거리
trigger: "true"
severity:
  yellow: "warehouse_depth_m > th.warehouse_depth.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: im_wonchang_2026_p34, deals: [], approved: null}
```
- 관측값: 석남동(화재) 약 77m, 원창 약 53m. 두 값뿐이라 임계값을 제안하지 않는다.
- **2026-10-13 승격(사용자 요청):** 필드 `warehouse_depth_m`와 룰 FR05(`rules_fire.md`)로 반영. 같은 날 사용자가 🔴 77m 이상으로 결정(석남동 화재 사례).

## FRC2. 다동 연결 대규모 구조

```yaml
id: FRC2
category: fire
scope: asset
horizon: now
inputs: [connected_buildings]         # 신규 필드 후보: 같은 층에서 내부로 연결된 창고 동 수
trigger: "true"
severity:
  yellow: "connected_buildings >= 2"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: im_wonchang_2026_p34, deals: [], approved: null}
```
- 기존 FR02(방화구획 최대 면적)는 구획 단위만 본다. 동이 연결돼 연기·열이 옆 동으로 넘어가는 경로는 따로 봐야 한다는 가설.

## FRC3. 소방차 접근면 부족

```yaml
id: FRC3
category: fire
scope: asset
horizon: now
inputs: [fire_access_sides]           # 신규 필드 후보: 소방차가 붙을 수 있는 건물 면 수(도로·소방 활동 공간 접면)
trigger: "true"
severity:
  yellow: "fire_access_sides <= th.fire_access_sides.yellow"
  green:  "otherwise"
on_missing: hold
llm_adjust: up_one
adjust_basis: []
manifest_years: null
provenance: {source: im_wonchang_2026_p34, deals: [], approved: null}
```
- 관측값: 원창 3면(IM 주장). 석남동은 IM에 없음.

FR03 보완 후보(필드 추가 없이 서술·DD로 처리): 임차인 인랙·메자닌 계획 대비 인랙 분기배관·밸브 선반영 여부. → `rules_fire.md` FR03 DD 확인 포인트에 반영함.

고층부 발화 외부 방수 제약: 기존 필드 `floors_above`로 표현할 수 있으나 '외부 방수 가능 높이' 근거가 없어 후보로 만들지 않았다.

### 반례·검증 계획
- 반례 검토 불가: 이 특징을 가진 다른 딜의 사후 결과(화재·보험 조건)가 코퍼스에 없다.
- 승격 조건: 같은 특징(깊이·연결 동·접근면)을 가진 딜 중 화재·보험 인수 조건 악화 사례가 1건 이상 추가되고, 화재 원인 조사 자료(소방청·보험사)로 확산 경로가 확인될 때.
