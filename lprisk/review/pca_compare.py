"""실사 대조 — WF2 결과와 물리실사(PCA/TDD) 골든을 나란히 (리뷰 서버 /pca/{a}, `python -m lprisk pca-compare {a}`).

- 스펙: 확정 스펙(없으면 도면 판독)과 골든 슬롯별로 일치·불일치·WF2 누락·실사 미기재를 가른다.
- 판정: 골든 값을 확정 스펙으로 넣고 같은 룰셋으로 프로파일·룰 평가를 다시 돌린 '실사 값 판정'을 WF2 판정과 룰별로 맞댄다.
- 소견: findings.yaml(룰별 실사 소견)을 룰에 붙이고, 결함 소견이 있는데 두 판정 모두 🔴가 아닌 룰을 '룰이 못 잡은 결함'으로 모은다.
화면·기록용이며 WF2 산출물(w2_*)은 바꾸지 않는다. 실사 원문 PDF는 input/{a}/dd/ 에 두면 페이지 링크가 열린다.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..engine.consistency import consistency_vars
from ..engine.evaluate import evaluate_profile
from ..engine.rules import load_rules
from ..golden import _slots, golden_dir, slot_matches
from ..io import load_json, load_yaml, now_iso, save_json
from ..paths import input_dir, rel, wf2_dir
from ..schema import Slot, evaluated_building_ids, field_def, floor_sort_key
from ..spec.normalize import normalize_record
from ..spec.profile import build_profile, load_location

SEV_RANK = {"red": 0, "yellow": 1, "green": 2, "hold": 3, None: 4}
LEVEL_RANK = {"asset": 0, "building": 1, "floor": 2}
CHANGE_ORDER = ["실사 값으로 🔴", "실사 기준 상향", "실사로 해소", "실사 기준 하향", "실사 자료 부족", "같음", "WF2 미평가"]


def _sev(r: dict | None) -> str | None:
    """룰 결과의 최종 심각도. 미발동은 None."""
    if not r or r.get("status") == "not_triggered":
        return None
    return r.get("severity_final") or r.get("severity_base")


def _change(ours: str | None, pca: str | None) -> str:
    if ours == pca:
        return "같음"
    if ours == "hold":
        return "실사 값으로 🔴" if pca == "red" else "실사로 해소"
    if pca == "hold":
        return "실사 자료 부족"
    return "실사 기준 상향" if SEV_RANK[pca] < SEV_RANK[ours] else "실사 기준 하향"


def _slot_label(key: str) -> str:
    return Slot.from_key(key).label() if key.count("|") == 3 else key


def _dd_doc(asset_id: str, name: str | None) -> str | None:
    """골든 출처 문서명 → input/{a}/dd/ 아래 실제 파일(있을 때만)."""
    if not name:
        return None
    p = input_dir(asset_id) / "dd" / Path(name).name
    return rel(p) if p.exists() else None


def _slot_sort(s: Slot) -> tuple:
    return (LEVEL_RANK[s.level], s.building_id or "", floor_sort_key(s.floor) if s.floor else (-1,), s.field)


def _ours_view(v: dict) -> dict:
    loc = v.get("source_locator") or v.get("locator") or {}
    return {"value": v.get("value"), "unit": v.get("unit"), "raw_text": v.get("raw_text"), "method": v.get("method"),
            "status": v.get("status"), "doc": v.get("source_doc"), "page": loc.get("page"),
            "sheet_no": loc.get("sheet_no"), "crop": loc.get("crop") or v.get("crop"), "flags": v.get("flags") or [],
            "note": v.get("note"), "precision": v.get("precision"), "basis": v.get("basis")}


def _gold_view(asset_id: str, v: dict) -> dict:
    loc = v.get("source_locator") or {}
    return {"value": v.get("value"), "unit": v.get("unit"), "raw_text": v.get("raw_text"), "page": loc.get("page"),
            "doc": _dd_doc(asset_id, v.get("source_doc")), "doc_name": v.get("source_doc"),
            "confidence": v.get("confidence"), "accept_also": v.get("accept_also") or [], "note": v.get("note"),
            "precision": v.get("precision"), "basis": v.get("basis")}


def _rule_inputs(results: list[dict]) -> dict[str, set[str]]:
    """스펙 슬롯 → 그 슬롯을 판정 입력으로 쓴(또는 기다리는) 룰."""
    out: dict[str, set[str]] = {}
    for r in results:
        for h in (r.get("now"), r.get("exit")):
            if not h:
                continue
            keys = [k for ks in (h.get("fact_deps") or {}).values() for k in ks] + list(h.get("missing_inputs") or [])
            for k in keys:
                if k.count("|") == 3:
                    out.setdefault(k, set()).add(r["rule_id"])
    return out


def _spec_rows(asset_id: str, gold_rec: dict, ours_rec: dict, bids: list[str], rule_map: dict) -> list[dict]:
    gold, ours = _slots(gold_rec, bids), _slots(ours_rec, bids)
    rows = []
    for s in sorted(set(gold) | set(ours), key=_slot_sort):
        gv, ov = gold.get(s) or [], ours.get(s) or []
        if not gv and not ov:
            continue
        if gv and ov:
            result = "일치" if slot_matches(s.field, gv[0], ov) else "불일치"
        else:
            result = "WF2 누락" if gv else "실사 미기재"
        rows.append({"slot": s.key, "label": s.label(), "field": s.field, "floor": s.floor,
                     "unit": field_def(s.field).get("unit"), "result": result,
                     "rule_input": bool(rule_map.get(s.key)), "rules": sorted(rule_map.get(s.key) or []),
                     "ours": _ours_view(ov[0]) if ov else None, "gold": _gold_view(asset_id, gv[0]) if gv else None})
    rank = {"불일치": 0, "WF2 누락": 1, "일치": 2, "실사 미기재": 3}
    rows.sort(key=lambda r: (rank[r["result"]], not r["rule_input"]))     # 안정 정렬: 같은 묶음 안은 슬롯 순서
    return rows


def _pca_results(asset_id: str, gold_rec: dict, meta: dict, rules: list[dict]) -> list[dict]:
    """골든 값을 확정 스펙으로 두고 같은 룰셋으로 다시 평가 (파일에 쓰지 않음)."""
    rec = dict(gold_rec, asset_id=asset_id)
    prof = build_profile(rec, meta, load_location(asset_id))
    try:
        extra = consistency_vars(asset_id, prof, rules)
    except FileNotFoundError:          # 입력 폴더가 없는 자산(골든만 남은 경우) — V01·V02는 ⚪
        extra = {}
    return evaluate_profile(prof, rules, extra)


def _hold_view(r: dict | None) -> dict | None:
    h = (r or {}).get("now") or (r or {}).get("exit")
    if not h or h.get("severity") != "hold":
        return None
    return {"reason": h.get("hold_reason"), "inputs": [_slot_label(k) for k in h.get("missing_inputs") or []]}


def _scalar(v):
    if isinstance(v, (list, dict)):
        return None if len(str(v)) > 120 else v
    return v


def _facts_diff(ours: dict | None, pca: dict | None) -> list[dict]:
    fo = ((ours or {}).get("now") or (ours or {}).get("exit") or {}).get("facts") or {}
    fp = ((pca or {}).get("now") or (pca or {}).get("exit") or {}).get("facts") or {}
    rows = []
    for k in sorted(set(fo) | set(fp)):
        a, b = _scalar(fo.get(k)), _scalar(fp.get(k))
        rows.append({"var": k, "ours": a, "pca": b, "diff": a != b})
    return rows


def _thresholds(*results: dict | None) -> list[dict]:
    """두 판정이 비교에 쓴 임계값 (key 기준 중복 제거)."""
    seen = {}
    for r in results:
        for h in ((r or {}).get("now"), (r or {}).get("exit")):
            for th in (h or {}).get("thresholds") or []:
                seen.setdefault(th["key"], {"key": th["key"], "value": th.get("value"), "segment": th.get("segment"),
                                            "verified": th.get("verified")})
    return list(seen.values())


def _findings(asset_id: str, g: Path) -> tuple[dict[str, list], str | None]:
    p = g / "findings.yaml"
    if not p.exists():
        return {}, None
    raw = p.read_text(encoding="utf-8")
    m = re.search(r"^#\s*source_doc:\s*(.+?)(?:\s{2,}|\s*\(|$)", raw, re.M)
    doc = _dd_doc(asset_id, m.group(1).strip()) if m else None
    out = {}
    for rid, items in ((load_yaml(p) or {}).get("findings") or {}).items():
        out[rid] = [{"text": f.get("text"), "page": f.get("page"), "severity": f.get("severity_hint") or "경미"}
                    for f in items or []]
    return out, doc


def _readme(g: Path) -> dict:
    """골든 README에서 출처 한 줄과 '검토 필요' 체크리스트."""
    p = g / "README.md"
    if not p.exists():
        return {"source": None, "todo": []}
    text = p.read_text(encoding="utf-8")
    m = re.search(r"^- 실사\(정답\) 출처:\s*(.+)$", text, re.M)
    sec = re.search(r"^## 검토 필요\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    todo = []
    for line in (sec.group(1) if sec else "").splitlines():
        t = re.match(r"^- \[( |x)\]\s*(.+)$", line.strip())
        if t:
            todo.append({"done": t.group(1) == "x", "text": t.group(2)})
    return {"source": m.group(1).strip() if m else None, "todo": todo}


def build(asset_id: str, save: bool = False) -> dict:
    g = golden_dir(asset_id)
    if not (g / "golden_spec.json").exists():
        raise FileNotFoundError(f"골든 없음: tests/golden/{asset_id}/golden_spec.json")
    out = wf2_dir(asset_id)
    meta_path = input_dir(asset_id) / "asset_meta.yaml"
    meta = load_yaml(meta_path if meta_path.exists() else g / "asset_meta.yaml")
    bids = evaluated_building_ids(meta)
    gold_rec = normalize_record(load_json(g / "golden_spec.json"))
    ours_name = "w2_05_confirmed_spec.json" if (out / "w2_05_confirmed_spec.json").exists() else "w2_03_drawing_specs.json"
    ours_rec = normalize_record(load_json(out / ours_name))

    loaded = load_rules()
    if loaded["errors"]:
        raise RuntimeError("룰 파일 오류:\n" + "\n".join(loaded["errors"]))
    rules = loaded["rules"]
    titles = {r["id"]: r["title"] for r in rules}
    ev_path = out / "w2_08_risk_evaluation.json"
    ours_res = load_json(ev_path)["results"] if ev_path.exists() else []
    pca_res = _pca_results(asset_id, gold_rec, meta, rules)

    spec = _spec_rows(asset_id, gold_rec, ours_rec, bids, _rule_inputs(ours_res + pca_res))
    findings, findings_doc = _findings(asset_id, g)

    wf2_evaluated = bool(ours_res)
    ours_by = {(r["rule_id"], r.get("building_id")): r for r in ours_res}
    pca_by = {(r["rule_id"], r.get("building_id")): r for r in pca_res}
    rule_rows, seen = [], set()
    for key in list(ours_by) + [k for k in pca_by if k not in ours_by]:
        r, p = ours_by.get(key), pca_by.get(key)
        base = r or p
        seen.add(key[0])
        so, sp = _sev(r), _sev(p)
        fs = findings.get(key[0], [])
        defects = sum(f["severity"] == "결함" for f in fs)
        rule_rows.append({
            "rule_id": key[0], "title": base["title"], "category": base["category"], "building_id": key[1],
            "ours": so, "pca": sp, "change": _change(so, sp) if wf2_evaluated else "WF2 미평가",
            "ours_hold": _hold_view(r) if so == "hold" else None, "pca_hold": _hold_view(p) if sp == "hold" else None,
            "facts": _facts_diff(r, p), "thresholds": _thresholds(r, p), "root_cause": (r or {}).get("root_cause"),
            "findings": fs, "defects": defects,
            "uncaught": defects > 0 and so != "red" and sp != "red"})
    for rid, fs in findings.items():                 # 평가 결과에 없는 룰(룰셋 밖)의 소견
        if rid not in seen:
            rule_rows.append({"rule_id": rid, "title": titles.get(rid, "(룰셋에 없음)"), "category": None,
                              "building_id": None, "ours": None, "pca": None, "change": "같음",
                              "ours_hold": None, "pca_hold": None, "facts": [], "thresholds": [], "root_cause": None, "findings": fs,
                              "defects": sum(f["severity"] == "결함" for f in fs),
                              "uncaught": any(f["severity"] == "결함" for f in fs)})
    rule_rows.sort(key=lambda x: (CHANGE_ORDER.index(x["change"]), SEV_RANK[x["pca"]], x["rule_id"]))

    def counts(key):
        c = {"red": 0, "yellow": 0, "green": 0, "hold": 0, None: 0}
        for x in rule_rows:
            if x["category"] is not None:
                c[x[key]] += 1
        return {"red": c["red"], "yellow": c["yellow"], "green": c["green"], "hold": c["hold"], "none": c[None]}

    spec_counts = {k: sum(r["result"] == k for r in spec) for k in ("일치", "불일치", "WF2 누락", "실사 미기재")}
    all_f = [f for fs in findings.values() for f in fs]
    uncaught = [{"rule_id": x["rule_id"], "title": x["title"], "ours": x["ours"], "pca": x["pca"],
                 "items": [f for f in x["findings"] if f["severity"] == "결함"]} for x in rule_rows if x["uncaught"]]
    st_path = out / "session_state.json"
    data = {
        "asset_id": asset_id, "created_at": now_iso(), "asset_name": meta.get("asset_name"),
        "ours_source": ours_name, "wf2_evaluated": wf2_evaluated, "wf2_state": load_json(st_path).get("state") if st_path.exists() else None,
        "golden": _readme(g), "findings_doc": findings_doc,
        "summary": {
            "verdicts": {"ours": counts("ours"), "pca": counts("pca")},
            "changes": {k: sum(x["change"] == k for x in rule_rows if x["category"] is not None) for k in CHANGE_ORDER},
            "changed": sum(x["change"] not in ("같음", "WF2 미평가") for x in rule_rows if x["category"] is not None),
            "spec": spec_counts, "gold_slots": sum(r["gold"] is not None for r in spec),
            "findings": {k: sum(f["severity"] == k for f in all_f) for k in ("결함", "경미", "양호")},
            "uncaught_defects": sum(len(u["items"]) for u in uncaught),
        },
        "rules": rule_rows, "spec": spec, "uncaught": uncaught,
    }
    if save:
        save_json(out / "pca_comparison.json", data)
    return data


def run(asset_id: str) -> dict:
    d = build(asset_id, save=True)
    return {"saved": f"output/wf2/{asset_id}/pca_comparison.json", **d["summary"],
            "view": f"http://127.0.0.1:8765/pca/{asset_id}"}
