# 리스크 상관관계 맵

W2-⑨에서 `precompute_pairs.py`가 아래 관계 중 구성 룰이 모두 활성(🔴·🟡)인 것만 뽑고, risk-evaluator가 자산 맥락으로 해석한다.
맵에 없는 연쇄는 보고서 부록 B '미검증 제안'으로만 쓰며, G1에서 승인되면 여기에 추가한다.

```yaml
relations:
  - id: R01
    rules: [FR01, FR02]
    converges_to: 화재 손실 확대·보험 조건 악화
    description: 가연성 패널 심재와 대면적 방화구획이 겹치면 연소 확대 범위와 최대 추정 손실이 커진다.
  - id: R02
    rules: [FR01, FR03]
    converges_to: 화재 손실 확대·보험 조건 악화
    description: 가연성 패널 + 고층고 대비 부적합 스프링클러는 초기 진압 실패와 전층 확대로 이어진다.
  - id: R03
    rules: [FR02, FR03]
    converges_to: 화재 손실 확대·보험 조건 악화
    description: 대면적 구획에서 스프링클러가 제어하지 못하면 손실이 구획 전체로 번진다.
  - id: R04
    rules: [FR04, CL01]
    converges_to: 저온동 화재·운영 중단
    description: 가연성 단열재와 노후 냉동설비(전기 화재·냉매)가 같은 공간에 있다.
  - id: R05
    rules: [G02, G04]
    converges_to: 정전 시 저온 화물 손상
    description: 노후 수변전설비와 비상발전기 신뢰성 부족이 겹치면 정전 대응이 불가능하다.
  - id: R06
    rules: [G04, CL01]
    converges_to: 정전 시 저온 화물 손상
    description: 비상전원 부족 상태에서 냉동설비가 멈추면 화물 손상 배상으로 이어진다.
  - id: R07
    rules: [SP05, G07]
    converges_to: 램프·야드 보수 CAPEX 반복
    description: 급경사·협폭 램프는 대형차 제동 하중이 커서 포장 열화가 빨라진다.
  - id: R08
    rules: [SP07, G03]
    converges_to: 상층부 처리량 병목·공실
    description: 수직반송 의존 구조에서 승강기가 노후하면 상층부 운영이 멈춘다.
  - id: R09
    rules: [SP01, SP02]
    converges_to: 임대 경쟁력 저하
    description: 하중과 유효층고가 함께 낮으면 고단 랙 임차인을 유치할 수 없다.
  - id: R10
    rules: [SP04, SP06]
    converges_to: 입출고 처리량 제약
    description: 도크 부족과 협소한 야드가 겹치면 피크 시간 대기가 길어진다.
  - id: R11
    rules: [LC01, CL02]
    converges_to: 저온동 바닥 손상
    description: 침수 위험 지반과 동상 방지 설비 부재가 겹치면 저온동 바닥 손상이 커진다.
  - id: R12
    rules: [LC02, SP01]
    converges_to: 바닥 침하·균열
    description: 연약지반에서 고하중 바닥은 부동침하와 균열이 생기기 쉽다.
  - id: R13
    rules: [LC02, G07]
    converges_to: 램프·야드 보수 CAPEX 반복
    description: 연약지반 위 야드·램프는 침하로 포장 열화가 빨라진다.
  - id: R14
    rules: [V01, SP01]
    converges_to: 가격 근거 하향
    description: IM 과장이 하중 판정을 바꿨다면 가격 가정 자체를 다시 봐야 한다.
  - id: R15
    rules: [G06, CL03]
    converges_to: 누수·결로 복합 손상
    description: 지붕 누수와 저온동 단열 열화가 겹치면 결빙·화물 손상이 커진다.
```
