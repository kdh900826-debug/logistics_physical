"""W2-④ 교차 대조 (설계서 §2.3 W2-④).

- 동·층 슬롯 단위로 IM 주장값과 도면 값(블라인드/힌트)을 구간 비교
- 블라인드 도면값이 IM과 허용오차 내 일치 → 확정(교차) 자동 확정
- 불일치 방향(IM 과장/보수) 판정, 힌트 재판독 요청 목록 생성
- G2 확인 항목(w2_04_confirmation_items.json) 생성
"""
from __future__ import annotations

from functools import lru_cache

from ..io import load_json, load_yaml, now_iso, save_json
from ..paths import SCHEMA_REFS, input_dir, rel, wf2_dir
from ..schema import ASSET_BUILDING, Slot, evaluated_building_ids, field_def, iter_slots, load_schema, put
from .normalize import normalize_record
from .validate import validate_record


@lru_cache(maxsize=1)
def tolerance_table() -> dict:
    return load_yaml(SCHEMA_REFS / "tolerance.yaml")


def tolerance(field: str, base_value: float) -> float:
    t = tolerance_table()
    fd = field_def(field)
    spec = (t.get("fields") or {}).get(field) or (t.get("defaults_by_unit") or {}).get(fd.get("unit"), {"abs": 0, "rel": 0})
    return max(spec.get("abs", 0), spec.get("rel", 0) * abs(base_value))


def im_interval(field: str, v: dict) -> tuple[float, float]:
    """IM 값의 허용 구간. precision 반영 (설계서 W2-④ 표)."""
    x = v["value"]
    tol = tolerance(field, x)
    prec = v.get("precision") or "exact"
    if prec in ("approx", "rounded"):
        tol = max(tol, v.get("precision_halfwidth") or 0)
    if prec == "lower_bound":
        return (x - tol, float("inf"))
    if prec == "upper_bound":
        return (float("-inf"), x + tol)
    return (x - tol, x + tol)


def matches(field: str, im_v: dict, other: dict) -> bool:
    t = field_def(field)["type"]
    a, b = im_v.get("value"), other.get("value")
    if a is None or b is None:
        return False
    if t in ("number", "int"):
        lo, hi = im_interval(field, im_v)
        return lo <= b <= hi
    if t == "text":
        return str(a).replace(" ", "") == str(b).replace(" ", "")
    return a == b


def direction(field: str, im_value, other_value) -> str:
    """IM 값이 상대 값보다 매도자에게 유리한지: overstated | conservative | neutral."""
    fd = field_def(field)
    fav = fd.get("favorable", "none")
    t = fd["type"]
    if im_value is None or other_value is None or im_value == other_value:
        return "neutral"
    if t == "enum":
        order = (load_schema().get("favor_order") or {}).get(fd["enum"])
        if not order or im_value not in order or other_value not in order:
            return "neutral"
        return "overstated" if order.index(im_value) < order.index(other_value) else "conservative"
    if fav == "none":
        return "neutral"
    if t == "bool":
        better = (im_value is True) if fav == "higher" else (im_value is False)
        return "overstated" if better else "conservative"
    if t in ("number", "int"):
        higher = im_value > other_value
        return "overstated" if (higher == (fav == "higher")) else "conservative"
    return "neutral"


def _expand_asset_level(rec: dict, building_ids: list[str]) -> dict:
    """IM이 동 구분 없이 자산 단위(_asset)로 적은 값을 각 동 슬롯으로 펼친다."""
    out = {}
    for slot, values in iter_slots(rec):
        if slot.building_id == ASSET_BUILDING:
            for bid in building_ids:
                vs = [dict(v, granularity="asset") for v in values]
                out.setdefault(Slot(slot.level, bid, slot.floor, slot.field), []).extend(vs)
        else:
            out.setdefault(slot, []).extend(values)
    return out


def _cand(origin: str, v: dict, i: int) -> dict:
    loc = v.get("source_locator") or {}
    return {"cand_id": f"{origin}:{i}", "origin": origin, "value": v.get("value"), "unit": v.get("unit"),
            "raw_text": v.get("raw_text"), "precision": v.get("precision"), "source_doc": v.get("source_doc"),
            "locator": loc, "crop": loc.get("crop"), "method": v.get("method"), "confidence": v.get("confidence"),
            "flags": v.get("flags", []), "granularity": v.get("granularity")}


def _consistent(field: str, values: list[dict]) -> bool:
    if len(values) <= 1:
        return True
    base = dict(values[0], precision="exact")
    return all(matches(field, base, v) for v in values[1:])


def run(asset_id: str) -> dict:
    out_dir = wf2_dir(asset_id)
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    bids = [b["id"] for b in meta["buildings"]]
    ebids = evaluated_building_ids(meta)

    im_path, dr_path = out_dir / "w2_02_im_claims.json", out_dir / "w2_03_drawing_specs.json"
    im = normalize_record(load_json(im_path))
    save_json(im_path, im)
    dr = None
    if dr_path.exists():
        dr = normalize_record(load_json(dr_path))
        save_json(dr_path, dr)

    checks = {"im": validate_record(im, bids), "drawing": validate_record(dr, bids) if dr else None}
    if not checks["im"]["ok"] or (dr and not checks["drawing"]["ok"]):
        save_json(out_dir / "w2_04_validation_errors.json", checks)
        raise RuntimeError("스펙 레코드 검증 실패 — w2_04_validation_errors.json 참조")

    im_slots = _expand_asset_level(im, ebids)
    dr_slots = _expand_asset_level(dr, ebids) if dr else {}
    missing = {}
    for m in (dr or {}).get("missing") or []:
        s = Slot(m["level"], m.get("building_id"), m.get("floor"), m["field"])
        missing[s.key] = m

    all_slots = sorted(set(im_slots) | set(dr_slots), key=lambda s: s.key)
    reconciled, items, reference, auto, hint_requests = [], [], [], [], []
    for s in all_slots:
        fd = field_def(s.field)
        if fd["type"] == "list":
            continue
        im_v = [v for v in im_slots.get(s, []) if v.get("value") is not None]
        dr_all = [v for v in dr_slots.get(s, []) if v.get("value") is not None]
        blind = [v for v in dr_all if v.get("method") != "vision_hinted"]
        hinted = [v for v in dr_all if v.get("method") == "vision_hinted"]
        entry = {"slot": s.key, "label": s.label(), "level": s.level, "building_id": s.building_id,
                 "floor": s.floor, "field": s.field, "rule_input": bool(fd.get("rule_input")),
                 "favorable": fd.get("favorable"), "im": im_v, "drawing": blind, "hinted": hinted,
                 "missing_reason": (missing.get(s.key) or {}).get("missing_reason"),
                 "direction": None, "state": None, "auto_status": None}

        if not im_v and not blind:
            entry["state"] = "양쪽없음"
        elif im_v and not blind:
            entry["state"] = "IM만"
        elif blind and not im_v:
            entry["state"] = "도면만" if _consistent(s.field, blind) else "도면상충"
        elif not _consistent(s.field, blind):
            entry["state"] = "도면상충"
        elif all(matches(s.field, iv, blind[0]) for iv in im_v):
            entry["state"] = "일치"
            entry["auto_status"] = "확정(교차)"
        else:
            entry["state"] = "불일치"
            dirs = {direction(s.field, iv["value"], blind[0]["value"]) for iv in im_v}
            entry["direction"] = "overstated" if "overstated" in dirs else "conservative" if "conservative" in dirs else "neutral"
            # IM 후보끼리 이미 상충하면 도면 재판독으로 풀리지 않는다 → 바로 G2
            if not hinted and _consistent(s.field, im_v):
                hint_requests.append({"slot": s.key, "label": entry["label"], "field": s.field,
                                      "building_id": s.building_id, "floor": s.floor,
                                      "im_value": im_v[0]["value"], "unit": im_v[0].get("unit"),
                                      "im_raw_text": im_v[0].get("raw_text"),
                                      "drawing_locator": blind[0].get("source_locator"),
                                      "drawing_doc": blind[0].get("source_doc")})
        reconciled.append(entry)

        cands = [_cand("im", v, i) for i, v in enumerate(im_v)] + \
                [_cand("drawing", v, i) for i, v in enumerate(blind)] + \
                [_cand("hinted", v, i) for i, v in enumerate(hinted)]
        item = {"slot": s.key, "label": entry["label"], "level": s.level, "building_id": s.building_id,
                "floor": s.floor, "field": s.field, "unit": fd.get("unit"), "rule_input": entry["rule_input"],
                "state": entry["state"], "direction": entry["direction"], "missing_reason": entry["missing_reason"],
                "candidates": cands, "sensitive": None, "default_action": None}
        if entry["state"] == "일치":
            auto.append(dict(item, adopted="drawing:0"))
        elif entry["state"] == "양쪽없음":
            continue
        elif s.building_id not in ebids and s.level != "asset":     # 부속 동: 참고 항목
            item["default_action"] = "claim" if entry["state"] == "IM만" else "drawing:0"
            reference.append(item)
        elif entry["rule_input"] or entry["state"] in ("불일치", "도면상충") or hinted:
            items.append(item)
        else:
            item["default_action"] = "claim" if entry["state"] == "IM만" else "drawing:0"
            reference.append(item)

    # 도면에서 미발견인데 IM에도 없는 룰 입력 필드 → 미확인 사유를 G2 화면에 참고 표시
    unresolved = [m for k, m in missing.items() if k not in {e["slot"] for e in reconciled}]

    claims = []
    for i, c in enumerate(im.get("claims") or []):
        claims.append(dict(c, claim_id=f"claim:{i}"))

    loc_path = out_dir / "w2_01b_location.json"
    loc = load_json(loc_path) if loc_path.exists() else None

    from .sensitivity import mark_sensitivity
    conf_items = {"asset_id": asset_id, "created_at": now_iso(), "mode": "정규" if dr else "IM 단독",
                  "items": items, "reference_items": reference, "auto_confirmed": auto,
                  "claims": claims, "unresolved_missing": unresolved, "location": loc,
                  "summary": {"needs_review": len(items), "auto_confirmed": len(auto),
                              "reference": len(reference), "claims": len(claims),
                              "hint_requests": len(hint_requests)}}
    try:
        mark_sensitivity(asset_id, conf_items, meta)
    except Exception as e:   # 룰·임계값 미비 시에도 대조 결과는 낸다
        conf_items["sensitivity_error"] = str(e)
    order = {True: 0, None: 1, False: 2}
    conf_items["items"].sort(key=lambda it: (order[it["sensitive"]], not it["rule_input"], it["slot"]))

    save_json(out_dir / "w2_04_reconciled.json", {"asset_id": asset_id, "created_at": now_iso(),
                                                  "entries": reconciled, "validation": checks})
    save_json(out_dir / "w2_04_hint_requests.json", {"asset_id": asset_id, "requests": hint_requests})
    save_json(out_dir / "w2_04_confirmation_items.json", conf_items)
    _write_sheet_md(out_dir, conf_items)
    return conf_items


def _write_sheet_md(out_dir, ci: dict) -> None:
    from ..io import save_text
    s = ci["summary"]
    lines = [f"# 스펙 확인 시트 — {ci['asset_id']}", "",
             f"> 모드: {ci['mode']} · 확인 필요 {s['needs_review']}건 · 자동 확정 {s['auto_confirmed']}건 · "
             f"참고 {s['reference']}건 · 서술형 주장 {s['claims']}건", "",
             "확인은 리뷰 서버 G2 화면에서 한다. 이 파일은 보관용 요약이다.", "",
             "| 슬롯 | 상태 | 방향 | 후보값 |", "|---|---|---|---|"]
    for it in ci["items"]:
        cands = " / ".join(f"{c['origin']}={c['value']}" for c in it["candidates"])
        lines.append(f"| {it['label']} | {it['state']} | {it['direction'] or ''} | {cands} |")
    save_text(out_dir / "w2_04_confirmation_sheet.md", "\n".join(lines) + "\n")
