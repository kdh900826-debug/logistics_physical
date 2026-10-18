# Logistics Physical Risk Agent — 오케스트레이터

준공·운영 중인 물류센터(매입·담보대출 심사)의 물리적 리스크를 IM과 도면으로 스크리닝한다. 설계 원본은 `logistics_physical_risk_agent_design.md`(v2.1)다. **결과는 스크리닝 수준이며 PCA·현장 실사를 대체하지 않는다.**

현재 구현 범위는 **1단계(WF2 정규 모드)**다. 입지(LC)·DXF는 2단계, WF1 벤치마크는 3단계, 룰 학습·G1은 4단계에서 추가된다.

## 핵심 원칙
1. **수치 생성 금지:** 임계값 비교·집계·파생 변수·Top 3 정렬·자동 확정은 모두 `python -m lprisk` 스크립트가 한다. LLM은 적힌 값을 전사하고 서술만 한다. 도면에 표기 없는 치수를 벡터 PDF 좌표로 잴 때는 스크립트(`vector-radius`)만 쓰고 `method: vector`로 남긴다 — 그 값을 쓴 판정은 G2·보고서에 **📐벡터 측정**으로 따로 표시된다.
2. **추정 금지:** 미확인 필드는 기본값으로 채우지 않는다. 그 필드를 쓰는 룰은 ⚪ 판정 보류다.
3. **출처 필수:** 모든 스펙 값은 문서·페이지(도면은 타일 좌표)를 가진다.
4. **사람 게이트는 정지점:** G2(스펙 확인)·G3(최종 검토)는 리뷰 서버 제출 파일이 생기기 전에는 넘어가지 않는다.
5. **매도자 유리 방향 비대칭:** IM 주장으로 심각도를 낮추지 않는다. 하향은 G2에서 확정된 이력만.
6. **추출 독립성:** drawing-extractor(blind)에 IM·`w2_02_*` 경로를 넘기지 않는다.
7. **미검증 기준값:** `thresholds.yaml`·`regulation_timeline.yaml`의 `verified: false` 항목에 의존하는 룰은 ⚪다. 사용자가 확인한 항목만 `verified: true`로 바꾼다(Claude가 임의로 바꾸지 않는다). 확인은 리뷰 서버 `/thresholds` 화면에서 하며, 제출 즉시 YAML에 반영되고 이력은 `kb/threshold_review_log.json`에 남는다.

## 모드 판별
- "분석", "WF2", 자산 id 언급 → WF2. `input/{asset_id}/`에 `im/`, `drawings/`, `asset_meta.yaml`이 있어야 한다.
- "학습", "IM 추가", "코퍼스" → WF1. **아직 미구현(3·4단계)** 이라고 알린다.

## WF2 실행 절차
사용자가 "분석 시작"을 지시하면 G2까지 멈추지 않고 진행한다. 각 단계 결과 JSON의 `error`를 확인하고, 실패하면 아래 실패 처리를 따른다.

| 단계 | 실행 | 상태 |
|---|---|---|
| W2-① 접수 | `python -m lprisk intake {a}` → `escalations` 확인. `NO_DRAWINGS`면 IM 단독 모드 진행 여부를 사용자에게 묻는다. `NO_IM`·`ASSET_META*`는 진행 불가로 에스컬레이션 | INTAKE |
| W2-② IM 텍스트 | `python -m lprisk extract-im-text {a}` | EXTRACTING |
| W2-② IM 주장값 | `im-analyst` 호출 (mode target, asset_id) | |
| W2-③ 1단계 분류 | `python -m lprisk classify-sheets {a}` → `drawing-classifier` 호출 | |
| W2-③ 2단계 판독 | `drawing-extractor` 호출 (mode **blind**). IM 경로를 프롬프트에 넣지 않는다 | |
| W2-④ 대조 | `python -m lprisk reconcile {a}` → `hint_requests > 0`이면 `drawing-extractor`(mode **hinted**) 호출 후 `reconcile` 한 번 더 | RECONCILED |
| **G2** | 리뷰 서버를 띄우고(아래) 채팅에 URL과 요약(확인 필요 n / 자동 확정 m / 서술형 주장 k / **미발견 룰 입력 u**)을 출력하고 **멈춘다**. u > 0이면 `w2_04_confirmation_items.json`의 `unresolved_missing` 중 `rule_input: true`를 `필드(층) — 보류되는 룰(blocks_rules)` 목록으로 따로 짚는다 | AWAITING_CONFIRMATION |
| W2-⑤ 반영 | 사용자가 "계속" → `output/wf2/{a}/w2_05_user_response.json` 존재 확인 → `python -m lprisk apply-confirmation {a}` | PROFILED |
| W2-⑥ 프로파일 | `python -m lprisk profile {a}` | |
| W2-⑦ 벤치마크 | 1단계 미구현 — 스킵(보고서에 "벤치마크 미적용") | |
| W2-⑧ 룰 평가 | `python -m lprisk evaluate {a}` → `risk-evaluator`(phase evaluate) — 내부에서 `merge-evaluation` 실행 | EVALUATED |
| W2-⑨ 상관관계 | `python -m lprisk pairs {a}` → `risk-evaluator`(phase correlate) | |
| W2-⑩ 보고서 | `risk-evaluator`(phase report) — `report-data`·`render-report`·`validate-report` 포함 | REPORT_DRAFT |
| **G3** | 리뷰 서버 `/g3/{a}` URL 안내 후 **멈춘다** | `python -m lprisk transition {a} AWAITING_REVIEW` |
| W2-⑪ | 사용자가 "계속" → `w2_11_review_response.json` 확인 → `python -m lprisk finalize {a}` (승인 시 최종본 `{a}_logistics_risk_report_final.md`와 **HTML `…_final.html`** 을 함께 만든다) → 사용자에게 HTML 경로를 안내 | FINAL 또는 재진입 |

### 리뷰 서버
- 기동: 포트 8765가 비어 있으면 `python -m lprisk review --no-browser` 를 백그라운드로 실행한다. 이미 떠 있으면 재사용한다.
- 화면: `http://127.0.0.1:8765/g2/{a}`, `/g3/{a}`, `/report/{a}`, `/pca/{a}`(실사 대조 — 골든이 있을 때)
- 사용자가 채팅으로 값을 알려 주면(예: "3층 하중은 1.2t") 그 내용을 `w2_05_user_response.json`의 `decisions`에 `{"action": "correct", "value": ..., "reason": "채팅 지시"}`로 반영해도 된다. 도면 판독값을 확정하라는 지시면 `{"action": "cand", "cand_id": "drawing:0"}`. 일괄 지시("나머지 미확인")는 `"bulk": "rest_unconfirmed"`.
- 일괄 지시("전부 도면 값 채택", "나머지 미확인")는 **확인 항목에만** 적용된다. 미발견 룰 입력 필드는 그대로 ⚪로 남으므로, 일괄 지시를 반영할 때 그 목록(필드·층·보류 룰·탐색 도면)을 채팅에 다시 보여 주고 "이 필드는 미확인으로 남는다"고 알린다. 사용자가 그중 값을 주거나 도면 재확인을 요청하면 아래 절차대로 처리한다.
- G2 확인 항목이 아닌 **미발견 필드**(`w2_04_confirmation_items.json`의 `unresolved_missing`)도 `decisions`에 `correct`로 넣을 수 있다. 도면 재확인으로 찾은 값이면 `source_doc`·`source_locator`(page·sheet_no)·`raw_text`·`method`(`vision` 또는 `vector`)·`precision`을 함께 넣어 출처를 남긴다. 판독 파일(`w2_03_drawing_specs.json`)을 손으로 고치지 않는다.

### 도면 재확인 요청 ("도면에서 확인 불가한지 다시 봐 줘")
1. 해당 필드의 `w2_03_drawing_specs.json` `missing[].searched`와 `w2_03_sheet_index.json`을 대조해 **안 본 시트**를 찾는다(타일이 없는 시트 = 안 본 시트).
2. `python -m lprisk text-search {a} --pattern "..."`으로 벡터 PDF 텍스트를 검색하고, 안 본 시트를 렌더링해 확인한다. 필드 기준은 `field_extraction_guide.md`.
   - 도크 수(`dock_count`) 점검은 `field_extraction_guide.md` '도크 수 접안 검증' 절차를 따른다. 층별 평면도에서 화물주차 구획이 창고 벽에 닿는지 확대해 보고, 단순 야드·옥상 화물주차는 뺀다. 결과는 층별 `표 n / 접안 확인 n / 제외 n(사유)` 표로 답한다.
3. 필드마다 "확인 불가 맞음 / 확인 가능(근거 시트) / 해석 필요"로 답하고, **값 확정은 사용자에게 맡긴다**. 표기 없는 R은 `vector-radius`로 잴 수 있다고만 안내하고, 사용자가 원하면 실행한다.
4. 사용자가 확정하면 아래 재진입 절차로 반영한다.

### 재진입 (G3 피드백)
`finalize`가 돌려준 `reentry`대로 다시 시작한다.
G3 화면 대신 채팅으로 정정 지시를 받았거나 이미 FINAL인 보고서를 고칠 때는, 기존 `w2_11_review_response.json`을 `.prev.json`으로 밀고(이미 있으면 `.prev2`, `.prev3`… 순으로 한 칸씩 민다) `{"approved": false, "comments": [{"type": "spec"|"severity"|"wording", "target": "<슬롯·룰>", "text": "<내용> — 채팅 지시"}]}`를 쓴 뒤 `python -m lprisk finalize {a}`를 실행한다 — 갱신 이력에 기록되고 재진입 상태로 바뀐다. `w2_05_user_response.json`도 같은 방식으로 백업한 뒤 이전 decisions를 유지한 채 새 결정을 더한다.
- `W2-⑤` 스펙 정정 → `reconcile`부터 다시(기존 응답 파일은 `w2_05_user_response.prev.json`으로 이름 변경 후 G2)
- `W2-⑧` 심각도 이견 → `evaluate`부터 (risk-evaluator에 코멘트 전달)
- `W2-⑩` 문구 수정 → `risk-evaluator`(phase report)에 코멘트 전달
보고서 하단 "갱신 이력"은 스크립트가 세션의 `revisions`로 채운다.

### 세션 재개
`python -m lprisk status {a}`의 `state`를 보고 마지막 완료 단계 다음부터 이어 간다. 산출물 파일이 이미 있으면 그 단계를 다시 하지 않는다(사용자가 다시 하라고 하면 예외).

## 실패 처리
- 스크립트 오류(`error` 키): 원인이 입력 형식이면 해당 에이전트에 오류 메시지를 주고 1회 재시도. 그래도 실패하면 `python -m lprisk transition {a} HALTED --note "<사유>"` 후 사용자에게 보고.
- 서브에이전트 산출물이 validate를 통과하지 못하면 최대 2회 재시도.
- `reconcile`이 `w2_04_validation_errors.json`을 남기면 오류 목록을 해당 에이전트에 넘겨 수정하게 한다.

## 파일 경로 규약
- 입력: `input/{asset_id}/im/`, `input/{asset_id}/drawings/`, `input/{asset_id}/asset_meta.yaml`
- 산출물: `output/wf2/{asset_id}/w2_XX_*.json`, `{asset_id}_logistics_risk_report.md`, 최종본 `{asset_id}_logistics_risk_report_final.md`·`.html`(HTML 재생성: `python -m lprisk render-html {a}`, 초안은 `--draft`), `{asset_id}_data_request.md`, `crops/`, `tiles/`
- 설정: `.claude/skills/*/references/` (스키마·허용오차·룰·임계값·법규·상관관계 맵)
- 누적: `kb/` (정정 로그 `kb/extraction_log.csv`, 코퍼스 inbox)

## 골든 샘플 (회귀 테스트)
- `tests/golden/{cheongna,seoknam,icheon,songon,songon1,hyeonbang}/` — 실사 보고서 기반 정답(`golden_spec.json`)과 IM 기재 정답(`golden_im_claims.json`). 사용자 검토 전 초안.
- `python -m lprisk prepare-golden {a}` — 실사 보고서 수록 도면을 `input/{a}/drawings/`로 추출
- `python -m lprisk golden-check {a} --target im|drawing|confirmed` — 채점 결과 `output/wf2/{a}/golden_check_*.md`
- 실사 대조: 사용자가 실사(PCA/TDD) 보고서와 비교를 요청하면 보고서를 `tests/golden/{a}/`(golden_spec.json·findings.yaml·README.md·asset_meta.yaml, songon1 형식)로 옮기고 원문 PDF를 `input/{a}/dd/`에 둔 뒤 `python -m lprisk pca-compare {a}`를 실행하고 리뷰 서버 `/pca/{a}` URL을 안내한다. 실사 값 판정은 화면용 재평가이며 WF2 산출물을 바꾸지 않는다 — 보고서에 반영하려면 재진입 절차를 따른다
- 단위 테스트: `python -m pytest -q`
