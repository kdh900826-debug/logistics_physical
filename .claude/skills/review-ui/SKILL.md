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
| `/pca/{a}` — 실사 대조: WF2 판정 ↔ 실사 값 판정(골든 값으로 같은 룰셋 재평가), 스펙 슬롯 일치·불일치·누락, 룰별 실사 소견, 룰이 못 잡은 결함, 골든 검토 항목. `tests/golden/{a}/golden_spec.json`이 있을 때만 | — (읽기 전용. `python -m lprisk pca-compare {a}` → `pca_comparison.json`) |
| `/thresholds` — 임계값·법규 시행일·분류 정의 확인표(확정/값 수정/보류, 값 없는 항목 입력) | `thresholds.yaml`·`regulation_timeline.yaml`·`profile_config.yaml` 직접 수정(주석 보존), `kb/threshold_review_log.json` |

G3 처리: `python -m lprisk finalize {a}` → FINAL(최종본 `.md` + 단독 HTML `{a}_logistics_risk_report_final.html`, 코퍼스 편입 체크 시 `kb/corpus/inbox/{a}/`) 또는 재진입 지점. HTML만 다시 만들 때는 `python -m lprisk render-html {a}` (`--draft`: 초안).
실사 대조의 원문 페이지 링크는 실사 PDF를 `input/{a}/dd/`에 두면 열린다(골든 `source_doc` 파일명으로 찾음). 입력 폴더가 없는 자산은 골든의 `asset_meta.yaml`을 쓰고 V01·V02는 ⚪로 둔다.
G2 후보 중 `method: vector`는 📐벡터 측정 칩으로 표시된다(도면 표기값과 구분).
'판정 민감' 배지는 정렬에만 쓰고, 값별 심각도는 화면에 보여주지 않는다(역방향 편향 방지).
