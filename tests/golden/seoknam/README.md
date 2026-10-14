# seoknam 골든 샘플 (인천 석남 물류센터 / 석남로지스틱스센터)

- 실사(정답) 출처: `인천석남 물류센터 Due Diligence Report(Final)_241114_Update_250408.pdf` (WSP, 241p)
- IM: `20250430_인천 브룩필드 석남로지스틱스센터 담보대출 IM_대주_v1.74_Clean.docx`
- 건물 구성: 단일 동 `main`(창고동, B1~10F, RC+PC, 2023-06-01 사용승인). IM의 East/West Wing은 같은 동 안의 평면 구획이다. 경비실동(5.15평)은 별도 building으로 두지 않았다.
- 파일: `golden_spec.json`(DD 정답) / `golden_im_claims.json`(IM 기재값과 서술형 주장) / `asset_meta.yaml` / `drawing_pages.yaml`(DD 도면 40페이지)
- 단위는 원문대로 전사했다(kN/㎡, mm, 평, kVA). 정규화는 `normalize_units.py`가 한다.

## 골든 값 (DD 기준)

| 필드 | 값 (원 단위) | DD p | IM 값 (다를 때·참고) |
|---|---|---|---|
| site_area_m2 | 26,792.00 ㎡ | 16 | 26,792.0㎡ (동일) |
| truck_yard_depth_m | 13.0 m (하역장, 차로 16.0m) | 38 | 없음 |
| completion_year | 2023 | 16 | 동일 |
| gross_floor_area_m2 | 148,238.05 ㎡ | 16 | 동일 |
| floors_above / below | 10 / 1 | 16 | 동일 |
| structure_type | 복합 (RC+PC) | 16, 120 | 동일 |
| column_span_x/y_m | 11 / 11 m | 38 | 동일 |
| ramp_type | 단방향 (상행·하행 분리) | 33 | "1Way 진출입통로 분리" |
| ramp_slope_pct | 8.2 % (도면) | 27 | 없음 |
| ramp_width_m | 6,500 mm (실측 6,536) | 26 | 없음 |
| freight_elevator_count | 1 (화물용, 운행 1-10(8)) | 170-171 | "화물용 승강기 설치"·도식상 "전층", 대수 없음 |
| wall_panel_core | 글라스울 (THK75/200) | 75, 93 | 없음 |
| fire_compartment_max_m2 | 3,000 ㎡ | 100 (38) | 없음 |
| sprinkler_type | 표준형 (준비작동식, 상향/하향 헤드) | 179, 184 | "전층 스프링쿨러", 형식 없음 |
| cold_insulation_material | 우레탄 (벽·천장 뿜칠) | 7 | 1층 천장 우레탄 추가공사 계획 |
| power_capacity_kw | 7,500 **kVA** | 158 | 없음 |
| transformer_capacity_kva | 7,500 kVA (1,500×5) | 12, 159 | 없음 |

층별 값(B1~10F, 층고는 p77, 면적·용도는 p17, 하중은 p121, 유효고는 p78-79):

| 층 | 용도/온도 | 면적 ㎡ | 하중 kN/㎡ | 유효고 mm (SP 하단 최저) | 층고 m | 트럭 접안 |
|---|---|---|---|---|---|---|
| B1 | 기계 | 1,107.54 | – | – | 6.9 | – |
| 1F | 창고/저온 | 18,534.76 | 25.0 | 7,584 | 10.0 | O |
| 2F | 창고/저온 | 18,451.20 | 25.0 | 7,839 | 10.0 | O |
| 3F | 창고/저온 | 18,451.19 | 25.0 | (미측정) | 10.0 | O |
| 4F | 사무 | 2,470.45 | – | – | 5.4 | – |
| 5F / 6F / 7F | 창고/상온 | 18,451.19 | 20.0 | 8,142 / 8,170 / 8,181 | 10.0 | O |
| 8F | 사무 | 2,472.65 | – | – | 5.2 | – |
| 9F | 창고/상온 | 18,451.19 | 20.0 | 8,158 | 10.0 | O |
| 10F | 창고/상온 | 12,945.50 | 20.0 | 8,140 | **10.2** | O |

IM 층별 값: 면적은 평 단위(1F 5,601.62평은 경비실 제외, 5.15평 별도)이고, 층고는 "10m 층고계획"으로 일괄 기재돼 있다. 10F는 DD 10.2m와 다르다.

## IM과 DD 불일치 (V01 후보)

1. **주차 위치**: IM은 "일반주차는 지하에 별도 구획"이라고 적었다(table 8 row 3). DD에서 여객주차는 지상1층 램프 하부 2개소이고(p33), B1은 기계·전기실이다. IM의 table 9 row 2("승용차 공간 1층 배치")와도 서로 맞지 않는다.
2. **상온전환 공사비**: IM은 5,250백만원이다(para 100, table 23). DD Capex에서 Conversion은 5,000,200,000원이다(p230). 기타 CAPEX 1,354/308백만원은 DD와 일치한다.
3. **층고**: IM은 "10m 층고"로 일괄 기재했지만 DD에서 10F는 10.2m, 4F는 5.4m, 8F는 5.2m다.
4. **화물용 승강기**: IM 도식에는 "전층 화물용 승강기 설치"로 되어 있다. DD에는 화물용 1대, 운행구간 1-10(8)으로 나온다(8개 층만 정차).
5. **저온 표현**: IM은 "1~3F 냉동·냉장"(table 65)이라고 적었고, DD는 "저온창고"로만 기재한다.
6. **DD로 확인되지 않는 IM 주장**: 도크씰·도크레벨러(수량 없음), 전층 지게차 램프, 9층 옥상정원(DD는 "옥상층" 조경으로 기재).

## 검토 필요

- [ ] `clear_height_m`: DD는 다점 실측값만 준다. "SP 배관하단 최저값" 규칙이 맞는지(보 하단 값을 쓸지) 확인이 필요하다. 3F 창고와 4F·8F 사무실(2,371~2,602mm)은 넣지 않았다.
- [ ] `floor_load_tpm2`: "상온창고/저온창고" 항목을 층에 대응시켰다. 4F·8F는 사무실 5.0과 미표기 행 7.0이 섞여 있어 넣지 않았다.
- [ ] `truck_yard_depth_m` = 하역장 13.0m: 다층 램프형에서 이 필드에 무엇을 넣을지(13.0 / 16.0 / 13+16) 정의가 필요하다.
- [ ] `ramp_type` = 단방향: 상행·하행 램프가 분리돼 각각 1way다. enum 해석(단방향인지 양방향인지)을 확인해야 한다.
- [ ] `sprinkler_type` = 표준형: DD에는 ESFR 언급이 없다. 준비작동식·상향식 헤드라는 기재를 enum으로 옮긴 분류다.
- [ ] `power_capacity_kw`: DD 원문은 7,500kVA다. kW 필드에 kVA 단위로 넣었으므로 정규화 규칙 확인이 필요하다.
- [ ] `cold_insulation_material` = 우레탄은 벽·천장 기준이다. 저온층 바닥은 비드법보온판(EPS)이다(p97). 두께는 부위별로 달라 넣지 않았다.
- [ ] DD에 없어 넣지 않은 필드: dock_count, dock_leveler_count, vrc_count, freight_elevator_capacity_t, roof_panel_core(RC 슬래브 지붕), solar_installed, refrigerant, refrigeration_system, cold_floor_heave_protection, cold_area_m2, cold_ratio_pct, 소유 4종(refrigeration/dock/rack/vrc_owner), renovation_history(DD는 2023 신축, p230에 Conversion CAPEX만 있음). 냉동냉장설비 실사 보고서는 별첨이라 받지 못했다.
- [ ] IM 측 `cold_area_m2`는 임대면적(평) 두 값이 상충한다(table 18 11,694.10 / table 20 12,418.17). `conflict: true`로 둘 다 기록했다.
- [ ] `direct_truck_access`(IM)는 내부동선 도식 이미지(table 9 row 2)에서 읽은 값이다.
- [ ] DD 내부 불일치(스키마 외): 기초가 "지내력 기초"(p16)인지 "파일 기초"(p9, p120)인지 다르다. 파일 지지력은 kN/ea(p9)와 kPa(p116)로 단위가 다르다. 건폐율·용적률이 69.91/349.59(p16)와 69.94/349.73(p114)로 다르다. p1-2 텍스트 레이어에 다른 자산명("용인 기흥 Fresh Bag 물류센터")이 남아 있다.


## 정리 메모 (Claude, 2026-10-13)
- `power_capacity_kw`(수전 용량 7,500kVA)는 단위가 kVA라 kW 필드에서 뺐다. 같은 값이 `transformer_capacity_kva`에 있다(field_extraction_guide: kVA는 변압기 필드).

## 골든 수정 이력 (2026-10-13, 원문 재대조)

| 항목 | 변경 | 근거 |
|---|---|---|
| `golden_spec` 방화구획 최대 면적 3,000㎡ | precision `exact` → `upper_bound` | DD p38 "3,000㎡ 기준으로 방화구획", p100 "3,000m2 마다 구획" — 실제 최대 면적이 아니라 구획 상한. 도면 판독 2,966.75㎡는 이 범위 안 |
| `golden_spec` 3F·7F 층고 10.0m | **유지**, note 추가 | DD p17·p77 "3층 10.0m, 4층 5.4m". 4F·8F는 코어부 메자닌이라 단면도 코어 구간 치수(4.6/5.4, 4.8/5.2)와 다름. 창고 공간 층고는 10.0m |
| `golden_spec` 램프 폭 6.5m | **유지**, 7.5m도 정답 인정(`accept_also`) | DD p26 도면 6,500mm·실측 6,536mm vs p70 교통계획도 범례 "1차로 7.5m" — DD 내부 상충 |
| `golden_spec` 램프 형상 | `ramp_form: 나선형` 추가 | 스키마 분리(ramp_type=방향, ramp_form=형상). DD p70 교통계획도 이미지에 양 끝 타원형 연속 램프 |
| `golden_im_claims` 표 번호 | 0부터 → 1부터 | 추출 도구(`w2_02_im_text.json`) 번호 체계에 맞춤 |
| `golden_im_claims` 층별 층고 8개 층 | 삭제 | IM "10m 층고계획"은 층을 특정하지 않은 일괄 기재 → 추출 가이드 규칙 7에 따라 claim으로만 |
| `golden_im_claims` B1 용도 | "주차" 후보 추가, `conflict: true` | IM 내부 상충: 층별 면적표(table 8 중첩표) "기계전기실" vs table 9 "일반주차는 지하에 별도 구획" |
| 층별 면적·용도, 화물차 동선(직접접안), 램프 단방향 | **유지** | IM에 실제로 있음(table 8 중첩표, table 10 동선 도식 이미지). 1차 IM 추출이 놓친 것은 DOCX 추출 도구 버그(중첩 표·이미지 미추출) 때문이며 도구를 고침 |

## 상온 전환 견적 (`incidents.yaml`, 2026-10-14 추가)

- 2024-10-11 ㈜극동플러스 '인천석남동SNK물류센터 대수선공사(1안)' — A동(구간) 1·2·3층 상온화. 시공 41.08억(VAT 별도) + 사업주 직발주 8.70억 = 49.78억(산출값). 실사 p230 ALT1 50.0억과 근접.
- 핵심: 1층 천정 추가 방열 100T 5.1억(남는 저온층과의 열교 결로 대책), 하역장 방화셔터 ↔ 도크 저온 OHD 맞교체, 대수선 인허가 2개월 + 공사 약 4개월.
- 상세 항목은 `.claude/skills/risk-engine/references/conversion_cases.yaml`.
