---
name: risk-engine
description: 물류센터 리스크 룰 로드·제한 문법 평가(동별·현재/exit·⚪ 판정), V01/V02 정합성, LLM 조정 검증, 상관관계 쌍, 대시보드·Top 3·자료 요청 목록, 보고서 골격 렌더링·검증. WF2 W2-⑧~⑩에서 쓴다.
---

# risk-engine

코드: `lprisk/engine/`

| 명령 | 설계서 스크립트 | 산출물 |
|---|---|---|
| `load-rules` | load_rules.py | 룰 수·오류 |
| `evaluate` | evaluate_rules.py (+consistency) | `w2_08_base.json` |
| `merge-evaluation` | validate_adjustments.py | `w2_08_risk_evaluation.json` |
| `pairs` | precompute_pairs.py | `w2_09_pairs.json` |
| `report-data` | compute_dashboard.py + rank_top3.py + build_data_request.py | `w2_10_dashboard.json`, `w2_10_top3.json`, `{a}_data_request.md` |
| `render-report` | (보고서 골격) | `{a}_report_skeleton.md` |
| `validate-report` | validate_report.py | 섹션·건수·Top 3·수치 대조, 서술 표식 잔존 |

참조 (`references/`):
- `rules/rules_*.md` — 룰 28건(A 연식 10, B 스펙 7, C 화재 4, D 저온 4, E 정합성·벤치마크 3)
- `thresholds.yaml` — **전 항목 verified: false (사용자 확인 필요)**. 키가 없는 등급은 건너뛰고, 정의된 등급이 하나도 없으면 ⚪
- `severity_policy.yaml` — `single_grade: true`(2026-10-14 사용자 결정)면 🔴·🟡 구분 없이 발동은 모두 🔴. 룰의 red/yellow 식은 유지하고 evaluate가 결과에서 🟡를 🔴로 합친다(`merged_from` 기록). LLM 조정 1단계 = 🟢↔🔴. 임계값 보정(threshold_calibration)만 원 등급을 쓴다
- `regulation_timeline.yaml` — 법규 시행일 (verified: false)
- `correlation_map.md`, `report_config.yaml`

📐벡터 측정: 룰 결과 `now/exit.vector_inputs`에 벡터 좌표 측정 슬롯(`method: vector`)이 들어가면 대시보드 `vector_rules`·Top 3 `vector_inputs`에 기록되고, 보고서는 §0 "📐벡터 측정값 사용 판정" 줄, §1 상태 열, §5 카드 머리말·"📐벡터 측정 입력" 줄로 표시한다(†IM 기준과 같은 방식). 등급은 바꾸지 않는다.

조건식 규칙: `x == null`/`x != null`은 명시적 null 검사다. 항상 적용되는 룰의 trigger는 `"true"`로 두고, 입력 미확인은 심각도 식에서 ⚪가 되게 한다.
