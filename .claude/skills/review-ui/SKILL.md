---
name: review-ui
description: 사람 게이트용 로컬 리뷰 서버(G2 스펙 확인, G3 최종 검토, 보고서 HTML 열람). 제출 결과를 산출물 폴더에 JSON으로 저장한다.
---

# review-ui

코드: `lprisk/review/` · 실행: `python -m lprisk review [--port 8765] [--no-browser]`

| 화면 | 저장 파일 |
|---|---|
| `/g2/{a}` — 필드 카드(IM 원문·도면 크롭 병치), 서술형 주장 확정, 자동 확정 뒤집기, 일괄 미확인 | `w2_05_user_response.json` |
| `/g3/{a}` — 룰·섹션별 코멘트 + 유형(스펙/심각도/문구), 승인, 코퍼스 편입 | `w2_11_review_response.json` |
| `/report/{a}` — 보고서 HTML 뷰 | — |
| `/thresholds` — 임계값·법규 시행일·분류 정의 확인표(확정/값 수정/보류, 값 없는 항목 입력) | `thresholds.yaml`·`regulation_timeline.yaml`·`profile_config.yaml` 직접 수정(주석 보존), `kb/threshold_review_log.json` |

G3 처리: `python -m lprisk finalize {a}` → FINAL(최종본 `.md` + 단독 HTML `{a}_logistics_risk_report_final.html`, 코퍼스 편입 체크 시 `kb/corpus/inbox/{a}/`) 또는 재진입 지점. HTML만 다시 만들 때는 `python -m lprisk render-html {a}` (`--draft`: 초안).
G2 후보 중 `method: vector`는 📐벡터 측정 칩으로 표시된다(도면 표기값과 구분).
'판정 민감' 배지는 정렬에만 쓰고, 값별 심각도는 화면에 보여주지 않는다(역방향 편향 방지).
