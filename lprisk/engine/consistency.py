"""V01(IM–확정값 불일치: 방향 × 파급)·V02(핵심 스펙 미확인) 입력 변수 산출 (설계서 §3.8 E).

V01: IM 주장값과 G2 확정값을 비교한다(허용오차·정밀도 반영).
  - overstated: IM이 매도자에게 유리하게 과장
  - sensitive : IM 값을 넣었을 때 다른 룰의 심각도가 확정값 기준과 달라짐
V02: 룰 입력 필드(동 단위) 중 확정되지 않은 비율
"""
from __future__ import annotations

import copy

from ..io import load_json, load_yaml
from ..paths import input_dir, wf2_dir
from ..schema import ASSET_BUILDING, Slot, evaluated_building_ids, field_def, fields_at, iter_slots, put
from ..spec.profile import build_profile, load_location
from ..spec.reconcile import direction, matches

VERIFIED = {"확정", "확정(교차)"}


def _signature(results):
    return {(r["rule_id"], r["building_id"]): (r["severity_base"], r.get("severity_exit")) for r in results}


def consistency_vars(asset_id: str, profile: dict, rules: list[dict]) -> dict:
    from .evaluate import evaluate_profile
    out_dir = wf2_dir(asset_id)
    conf = load_json(out_dir / "w2_05_confirmed_spec.json")
    im = load_json(out_dir / "w2_02_im_claims.json")
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    bids = evaluated_building_ids(meta)
    loc = load_location(asset_id)
    base_rules = [r for r in rules if r["category"] != "consistency"]
    base_sig = _signature(evaluate_profile(profile, base_rules))

    conf_slots = {s: v[0] for s, v in iter_slots(conf) if v}
    im_slots: dict[Slot, list] = {}
    for s, vals in iter_slots(im):
        targets = bids if s.building_id == ASSET_BUILDING else [s.building_id]
        for b in targets:
            im_slots.setdefault(Slot(s.level, b, s.floor, s.field), []).extend(vals)

    items = []
    for s, ivs in im_slots.items():
        fd = field_def(s.field)
        if fd["type"] == "list":
            continue
        cv = conf_slots.get(s)
        if not cv or cv.get("status") not in VERIFIED or cv.get("value") is None:
            continue
        if cv.get("method") == "im_text":      # 확정값이 IM 자체에서 온 경우 비교 무의미
            continue
        ivs = [v for v in ivs if v.get("value") is not None]
        if not ivs or all(matches(s.field, iv, cv) for iv in ivs):
            continue
        iv = next(v for v in ivs if not matches(s.field, v, cv))
        d = direction(s.field, iv["value"], cv["value"])
        sensitive = False
        if d == "overstated":
            alt = copy.deepcopy(conf)
            put(alt, s, [dict(cv, value=iv["value"])])
            sig = _signature(evaluate_profile(build_profile(alt, meta, loc), base_rules))
            changed = sorted({k[0] for k in sig if sig[k] != base_sig.get(k)})
            sensitive = bool(changed)
        else:
            changed = []
        items.append({"slot": s.key, "label": s.label(), "im_value": iv["value"], "im_raw": iv.get("raw_text"),
                      "im_page": (iv.get("source_locator") or {}), "confirmed_value": cv["value"],
                      "unit": cv.get("unit"), "direction": d, "sensitive": sensitive, "affected_rules": changed})

    # V02: 동 단위 룰 입력 필드의 미확인 비율 (공공데이터 필드 제외)
    rule_fields = [f for f in fields_at("building") if field_def(f).get("rule_input") and field_def(f)["type"] != "list"]
    total = unconf = 0
    unconf_list = []
    cold_only = {"refrigerant", "cold_floor_heave_protection", "cold_insulation_material"}
    ramp_only = {"ramp_slope_pct", "ramp_width_m"}
    pvars = {pb["building_id"]: pb["vars"] for pb in profile["buildings"]}
    for b in bids:
        pv = pvars.get(b, {})
        for f in rule_fields:
            if f in cold_only and pv.get("has_cold") is False:
                continue
            if f in ramp_only and pv.get("ramp_type") == "없음":
                continue
            total += 1
            cv = conf_slots.get(Slot("building", b, None, f))
            if not cv or cv.get("status") not in VERIFIED | {"주장값"}:
                unconf += 1
                unconf_list.append(Slot("building", b, None, f).key)

    over = [i for i in items if i["direction"] == "overstated"]
    vars_ = {
        "v01.discrepancy_count": len(items),
        "v01.overstated_count": len(over),
        "v01.overstated_sensitive_count": sum(1 for i in over if i["sensitive"]),
        "v01.conservative_count": sum(1 for i in items if i["direction"] == "conservative"),
        "v02.unconfirmed_ratio": round(unconf / total, 4) if total else None,
        "v02.unconfirmed_count": unconf,
        # 벤치마크(3단계)가 없으면 B01은 미발동 (설계서 §3.8 E)
        "benchmark_available": (out_dir / "w2_07_benchmark_position.json").exists(),
        "benchmark.unruled_inferior_count": None,
    }
    return {"vars": vars_, "grades": {k: "verified" for k in vars_},
            "detail": {"v01_items": items, "v02_unconfirmed": unconf_list, "v02_total": total}}
