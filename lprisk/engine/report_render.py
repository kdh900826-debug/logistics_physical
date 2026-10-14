"""W2-⑩ 보고서 골격 렌더링 (설계서 §1.6, §2.3 W2-⑩).

수치·표·건수·Top 3·룰 카드 머리말은 모두 스크립트가 쓴다. LLM(risk-evaluator)은
`<!-- LLM:키 -->` 표식 자리에 서술만 채운다. validate_report가 표식 잔존 여부를 검사한다.
"""
from __future__ import annotations

from ..io import load_json, load_yaml, save_text
from ..paths import ENGINE_REFS, input_dir, wf2_dir
from ..schema import ASSET_BUILDING, Slot, field_def, floor_sort_key, iter_slots
from .rules import EMOJI, single_grade

ORDER = {"red": 0, "yellow": 1, "green": 2, "hold": 3}
GRADE_MARK = {"claimed": " †IM 기준", "verified": ""}
VECTOR_MARK = " 📐벡터 측정"     # 도면 치수 표기값이 아니라 벡터 PDF 좌표로 잰 값(method: vector)이 판정 입력


def _vmark(v: dict) -> str:
    return VECTOR_MARK if v.get("method") == "vector" else ""


def _fmt(v, unit=None):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "있음" if v else "없음"
    if unit == "year" and isinstance(v, (int, float)):
        return str(int(v))
    if isinstance(v, float):
        v = round(v, 3)
    u = {"m2": "㎡", "t/m2": "t/㎡", "pct": "%", "year": "", "ea": "", "floor": "층"}.get(unit, unit or "")
    return f"{v:,}{u}" if isinstance(v, (int, float)) else f"{v}{u}"


def _src(v: dict) -> str:
    loc = v.get("source_locator") or {}
    doc = (v.get("source_doc") or "").split("/")[-1]
    where = ", ".join(f"{k} {loc[k]}" for k in ("page", "slide", "para", "table", "sheet_no") if loc.get(k))
    crop = f" [근거]({loc['crop']})" if loc.get("crop") else ""
    return f"{doc[:28]}{' · ' + where if where else ''}{crop}"


def render(asset_id: str) -> str:
    out = wf2_dir(asset_id)
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    st = load_json(out / "session_state.json")
    dash = load_json(out / "w2_10_dashboard.json")
    top = load_json(out / "w2_10_top3.json")["top3"]
    ev = load_json(out / "w2_08_risk_evaluation.json")
    conf = load_json(out / "w2_05_confirmed_spec.json")
    rec = load_json(out / "w2_04_reconciled.json")
    pairs = load_json(out / "w2_09_pairs.json")["pairs"]
    corr = load_json(out / "w2_09_correlations.json") if (out / "w2_09_correlations.json").exists() else {}
    loc = load_json(out / "w2_01b_location.json") if (out / "w2_01b_location.json").exists() else None
    bench = out / "w2_07_benchmark_position.json"
    cfg = load_yaml(ENGINE_REFS / "report_config.yaml")
    sev = dash["severity"]
    name = meta.get("asset_name", asset_id)
    th_all = [t for r in ev["results"] for h in ("now", "exit") if r.get(h) for t in r[h].get("thresholds", [])]
    th_ver = sum(1 for t in th_all if t["verified"])
    L = [f"# [{name}] 물리적 리스크 분석 보고서", "",
         f"> 분석 모드: {dash['mode']} · 기준일: {meta.get('analysis_date') or '미입력(실행일 기준)'} · "
         f"보유기간: {str(meta['holding_years']) + '년' if meta.get('holding_years') else '미입력(exit 평가 생략)'}",
         f"> 룰셋: {st.get('ruleset_version')} · 임계값 검증: 참조 {len(th_all)}건 중 verified {th_ver}건 · "
         f"벤치마크: {'적용' if bench.exists() else '미적용'} · 입지 조회: {(loc or {}).get('queried_at', '미조회')}",
         f"> 한계: {cfg['limitation']}", ""]

    conf_slots = {s.key: vs[0] for s, vs in iter_slots(conf) if vs}

    # §0
    L += ["## 0. 요약 대시보드", "",
          "| 🔴 | 🟡 | 🟢 | ⚪ 판정 보류 | 미발동 |", "|---|---|---|---|---|",
          f"| {sev['red']} | {sev['yellow']} | {sev['green']} | {sev['hold']} | {dash['not_triggered']} |", "",
          *(["- 등급 정책: 단일 등급 — 🔴·🟡 구분 없이 발동은 모두 🔴 (severity_policy.yaml)"] if single_grade() else []),
          f"- 검증 입력 기준: 🔴 {dash['severity_verified']['red']} · 🟡 {dash['severity_verified']['yellow']} · "
          f"🟢 {dash['severity_verified']['green']} · ⚪ {dash['severity_verified']['hold']} / "
          f"†IM 기준(주장값 포함): 🔴 {dash['severity_claimed']['red']} · 🟡 {dash['severity_claimed']['yellow']} · "
          f"⚪ {dash['severity_claimed']['hold']}",
          f"- 보유 중 심각도 상승 예정: {len(dash['exit_escalations'])}건"
          + ("" if not dash["exit_escalations"] else " — " + ", ".join(
              f"{e['rule_id']}({e['building_id']}) {EMOJI[e['now']]}→{EMOJI[e['exit']]}" for e in dash["exit_escalations"])),
          f"- IM–도면 불일치: {dash['reconcile_mismatch']['total']}건 (IM 과장 {dash['reconcile_mismatch']['overstated']} · "
          f"IM 보수 {dash['reconcile_mismatch']['conservative']} · 방향 없음 {dash['reconcile_mismatch']['neutral']})",
          "- 스펙 확정 현황: " + " · ".join(f"{k} {v}" for k, v in dash["spec_status"].items()),
          *([f"- 📐벡터 측정값 사용 판정: {len(dash['vector_rules'])}건 — " + ", ".join(
              f"{EMOJI[v['severity']]} {v['rule_id']}{'(' + v['building_id'] + ')' if v['building_id'] else ''}"
              for v in dash["vector_rules"]) + " (도면에 치수로 적힌 값이 아니라 벡터 PDF 좌표로 잰 값을 입력으로 씀)"]
            if dash.get("vector_rules") else []), "",
          "**우선 확인 Top 3** (정렬: 심각도 → V01 연관 → 상관관계 연결 수 → 카테고리 우선순위)", ""]
    if top:
        for t in top:
            L.append(f"{t['rank']}. {EMOJI[t['severity']]} **{t['rule_id']}** {t['title']}"
                     f"{' [' + t['building_id'] + ']' if t['building_id'] else ''}{VECTOR_MARK if t.get('vector_inputs') else ''}"
                     f" — <!-- LLM:top3_{t['rank']} -->")
    else:
        L.append("- 활성(🔴·🟡) 리스크 없음")
    L += ["", "<!-- LLM:summary -->", ""]

    # §1 프로파일
    L += ["## 1. 자산 프로파일", ""]
    for b in conf["buildings"]:
        if b["building_id"] == ASSET_BUILDING:
            continue
        L += [f"### {b.get('label', b['building_id'])} [{b['building_id']}]", "",
              "| 항목 | 값 | 상태 | 출처 |", "|---|---|---|---|"]
        for f, vs in (b.get("fields") or {}).items():
            fd = field_def(f)
            if fd["type"] == "list":
                continue
            v = vs[0]
            L.append(f"| {fd['label']} | {_fmt(v.get('value'), v.get('unit'))} | {v.get('status')}{_vmark(v)} | {_src(v)} |")
        if b.get("floors"):
            L += ["", "| 층 | 용도 | 면적 | 설계하중 | 유효층고 | 직접접안 |", "|---|---|---|---|---|---|"]
            for fl in sorted(b["floors"], key=lambda x: floor_sort_key(x["floor"])):
                g = lambda k: (fl["fields"].get(k) or [{}])[0]
                def cell(k):
                    v = g(k)
                    mark = "" if v.get("status") in ("확정", "확정(교차)", None) else f" ({v.get('status')})"
                    return _fmt(v.get("value"), v.get("unit")) + mark + _vmark(v)
                L.append(f"| {fl['floor']} | {cell('use')} | {cell('area_m2')} | {cell('floor_load_tpm2')} | "
                         f"{cell('clear_height_m')} | {cell('direct_truck_access')} |")
        L.append("")
    if conf.get("asset"):
        L += ["### 단지 공용", "", "| 항목 | 값 | 상태 | 출처 |", "|---|---|---|---|"]
        for f, vs in conf["asset"].items():
            v = vs[0]
            L.append(f"| {field_def(f)['label']} | {_fmt(v.get('value'), v.get('unit'))} | {v.get('status')}{_vmark(v)} | {_src(v)} |")
        L.append("")

    # §2 벤치마크
    L += ["## 2. 스펙 경쟁력 — 벤치마크 포지셔닝", ""]
    if bench.exists():
        L += ["<!-- LLM:benchmark -->", ""]
    else:
        L += ["벤치마크 미적용 — WF1 벤치마크 DB가 아직 없다(구현 3단계).", ""]

    # §3 정합성
    L += ["## 3. IM–도면 정합성", "", "| 항목 | IM 기재 | 도면 | 확정값 | 방향 |", "|---|---|---|---|---|"]
    mism = [e for e in rec["entries"] if e["state"] in ("불일치", "도면상충")]
    dir_ko = {"overstated": "IM 과장", "conservative": "IM 보수", "neutral": "방향 없음", None: "—"}
    for e in mism:
        cv = conf_slots.get(e["slot"], {})
        L.append(f"| {e['label']} | {', '.join(_fmt(v['value'], v.get('unit')) for v in e['im']) or '—'} | "
                 f"{', '.join(_fmt(v['value'], v.get('unit')) for v in e['drawing']) or '—'} | "
                 f"{_fmt(cv.get('value'), cv.get('unit'))} ({cv.get('status', '—')}) | {dir_ko[e['direction']]} |")
    if not mism:
        L.append("| 불일치 없음 | | | | |")
    L += ["", "<!-- LLM:consistency -->", ""]

    # §4 입지
    L += ["## 4. 입지 리스크", ""]
    if loc:
        L += ["<!-- LLM:location -->", ""]
    else:
        L += ["입지 조회 미실행 — 입지 룰(LC)은 구현 2단계에서 추가된다.", ""]

    # §5 룰 카드
    L += ["## 5. 리스크 평가 결과", ""]
    shown = [r for r in ev["results"] if r["status"] in ("triggered", "hold")]
    shown.sort(key=lambda r: (ORDER[r["severity_final"]], r["rule_id"], r["building_id"] or ""))
    for r in shown:
        n = r.get("now") or r.get("exit")
        tag = f" [{r['building_id']}]" if r["building_id"] else ""
        grade = GRADE_MARK.get(n.get("input_grade"), "")
        vec = sorted({s for h in ("now", "exit") if r.get(h) for s in r[h].get("vector_inputs") or []})
        L += [f"### {EMOJI[r['severity_final']]} {r['rule_id']}. {r['title']}{tag}{grade}{VECTOR_MARK if vec else ''}", ""]
        for s in vec:
            v = conf_slots.get(s, {})
            L.append(f"- **📐벡터 측정 입력:** {_slot_label(s)} = {_fmt(v.get('value'), v.get('unit'))} — {_src(v)} "
                     "(도면에 치수로 적힌 값이 아니라 벡터 PDF 좌표로 잰 값)")
        if r["severity_final"] == "hold":
            L.append(f"- **판정 보류 사유:** {n['hold_reason']} — 미확인 입력: "
                     + (", ".join(_slot_label(p) for p in n["missing_inputs"]) or "—"))
        facts = ", ".join(f"{k}={_fmt(v)}" for k, v in n["facts"].items() if not isinstance(v, (list, dict)))
        L.append(f"- **판정 입력:** {facts or '—'}")
        if n.get("thresholds"):
            L.append("- **적용 임계값:** " + "; ".join(
                f"{t['key']}={t['value']} ({t['segment']}, {'검증' if t['verified'] else '미검증'})" for t in n["thresholds"]))
        if r.get("severity_exit") and r["severity_exit"] != r["severity_base"]:
            L.append(f"- **보유기간 말:** {EMOJI[r['severity_base']]} → {EMOJI[r['severity_exit']]}")
        if r.get("adjustment"):
            a = r["adjustment"]
            L.append(f"- **LLM 조정:** {EMOJI[r['severity_base']]} → {EMOJI[r['severity_final']]} ({'상향' if a['direction'] == 'up' else '하향'})")
        key = f"{r['rule_id']}@{r['building_id']}"
        if r["severity_final"] == "hold":
            # 판정 보류: 서술 없이 룰 기본 DD 포인트만 (미확인 입력 확인이 우선)
            dd = r.get("dd_checkpoints") or []
            L += ["- **DD 확인 포인트:** 미확인 입력 확보" + ("; " + "; ".join(dd) if dd else ""), ""]
        elif r["severity_final"] == "green":
            L += [f"- **추론 근거:** <!-- LLM:basis:{key} -->", ""]
        else:
            L += [f"- **추론 근거:** <!-- LLM:basis:{key} -->",
                  f"- **근본 원인:** <!-- LLM:root:{key} -->",
                  f"- **연쇄 리스크:** <!-- LLM:cascade:{key} -->",
                  f"- **DD 확인 포인트:** <!-- LLM:dd:{key} -->", ""]

    # §6 상관관계
    L += ["## 6. 리스크 상관관계", ""]
    if pairs:
        for p in pairs:
            L.append(f"- **{p['relation_id']}** {' + '.join(p['rules'])} → {p['converges_to']} — <!-- LLM:pair:{p['relation_id']} -->")
    else:
        L.append("- 상관관계 맵에 정의된 관계 중 양쪽이 모두 활성인 쌍이 없다.")
    L.append("")

    # §7 DD 체크리스트
    L += ["## 7. DD 체크리스트", "", "판정 보류(⚪) 항목을 먼저, 미확인 사유별로 묶었다. 자료 요청은 "
          f"`{asset_id}_data_request.md` 참조.", "", "<!-- LLM:dd_checklist -->", ""]

    # 부록
    L += ["## 부록 A. 필드별 추출 근거", "", "§1 표의 출처 열과 `w2_05_confirmed_spec.json` 참조. 도면 판독값은 [근거] 링크로 크롭 이미지를 연다.", ""]
    L += ["## 부록 B. 미검증 연쇄 제안", ""]
    props = corr.get("proposals") or []
    L += ([f"- {p.get('rules')}: <!-- LLM:proposal:{i} -->" for i, p in enumerate(props)] or
          ["- 없음"]) + [""]
    L += ["## 갱신 이력", "", "| 일시 | 변경 사유 | 재진입 지점 |", "|---|---|---|"]
    for rv in st.get("revisions") or []:
        L.append(f"| {rv['at']} | {rv['reason']} | {rv['reentry']} |")
    if not st.get("revisions"):
        L.append("| — | 초안 | — |")
    text = "\n".join(L) + "\n"
    save_text(out / f"{asset_id}_report_skeleton.md", text)
    return text


def _slot_label(p: str) -> str:
    if "|" in p:
        try:
            return Slot.from_key(p).label()
        except Exception:
            return p
    return p
