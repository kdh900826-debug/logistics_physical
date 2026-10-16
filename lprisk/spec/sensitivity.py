"""판정 민감도 (설계서 §2.3 W2-④ (e), compute_sensitivity).

후보값마다 룰 심각도가 달라지는지만 계산해 G2 정렬용 sensitive 플래그로 남긴다.
어떤 값이 어떤 심각도인지는 저장하지 않는다(역방향 편향 방지, §2.3 W2-⑤).
"""
from __future__ import annotations

import copy

from ..schema import Slot, empty_record, put
from .profile import build_profile, load_location


def cand_to_value(c: dict, status: str, source_grade: str | None = None) -> dict:
    return {"value": c["value"], "unit": c.get("unit"), "raw_text": c.get("raw_text"),
            "precision": c.get("precision"), "source_doc": c.get("source_doc"),
            "source_locator": c.get("locator") or {}, "method": c.get("method"),
            "confidence": c.get("confidence"),
            "source_grade": source_grade or ("IM주장" if c["origin"] == "im" else "확정"),
            "status": status}


def provisional_record(asset_id: str, ci: dict, meta: dict) -> dict:
    rec = empty_record(asset_id, "provisional", meta["buildings"])
    for it in ci["auto_confirmed"]:
        c = next(c for c in it["candidates"] if c["cand_id"] == it["adopted"])
        put(rec, Slot.from_key(it["slot"]), [cand_to_value(c, "확정(교차)")])
    for it in ci["items"] + ci["reference_items"]:
        cands = it["candidates"]
        pick = next((c for c in cands if c["origin"] == "drawing"), None) or cands[0]
        put(rec, Slot.from_key(it["slot"]), [cand_to_value(pick, "주장값" if pick["origin"] == "im" else "확정")])
    return rec


def _signature(results: list[dict]) -> dict:
    return {(r["rule_id"], r["building_id"]): (r["severity_base"], r.get("severity_exit")) for r in results}


def mark_sensitivity(asset_id: str, ci: dict, meta: dict) -> None:
    from ..engine.evaluate import evaluate_profile
    from ..engine.rules import load_rules
    loaded = load_rules()
    rules = [r for r in loaded["rules"] if r["category"] != "consistency"]
    if not rules:
        return
    loc = load_location(asset_id)
    base_rec = provisional_record(asset_id, ci, meta)
    # 미발견 필드마다 그 값이 없어서 판정 보류되는 룰 (G2에서 따로 짚기용)
    holds: dict[str, set] = {}
    for r in evaluate_profile(build_profile(base_rec, meta, loc), rules):
        for h in (r.get("now"), r.get("exit")):
            if not h or h.get("severity") != "hold":
                continue
            # '일부 창고층 미확인' 보류는 missing_inputs가 비어 올 수 있어 fact_deps 슬롯으로 대신한다
            keys = h.get("missing_inputs") or [k for ks in (h.get("fact_deps") or {}).values() for k in ks]
            for k in keys:
                holds.setdefault(k, set()).add(r["rule_id"])
    for m in ci.get("unresolved_missing") or []:
        m["blocks_rules"] = sorted(holds.get(m.get("slot"), ()))
    for it in ci["items"]:
        values = {repr(c["value"]) for c in it["candidates"]}
        if len(values) < 2:
            continue
        sigs = []
        for c in it["candidates"]:
            rec = copy.deepcopy(base_rec)
            put(rec, Slot.from_key(it["slot"]), [cand_to_value(c, "확정", "확정")])
            sigs.append(_signature(evaluate_profile(build_profile(rec, meta, loc), rules)))
        it["sensitive"] = any(s != sigs[0] for s in sigs[1:])
