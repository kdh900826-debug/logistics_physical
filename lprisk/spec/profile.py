"""W2-⑥ 프로파일 생성: 동별 파생 변수 (설계서 §2.3 W2-⑥). 기본값 적용 없음.

각 변수는 값과 함께 등급(verified | claimed)과 의존 슬롯을 가진다.
- 확정·확정(교차) 값만 쓰면 verified, 주장값이 하나라도 섞이면 claimed
- 의존 입력이 하나라도 미확인이면 값은 None (의존 필드 기록)
"""
from __future__ import annotations

from datetime import date

from ..io import load_yaml, now_iso, save_json
from ..paths import ENGINE_REFS, SCHEMA_REFS, input_dir, wf2_dir
from ..schema import ASSET_BUILDING, Slot, fields_at, iter_slots

VERIFIED_STATUS = {"확정", "확정(교차)"}


class Var:
    __slots__ = ("value", "grade", "deps", "missing")

    def __init__(self, value, grade, deps, missing=()):
        self.value, self.grade, self.deps, self.missing = value, grade, list(deps), list(missing)


def _combine(fn, *vars_: Var, deps_extra=()):
    deps = [d for v in vars_ for d in v.deps] + list(deps_extra)
    missing = [m for v in vars_ for m in v.missing]
    if any(v.value is None for v in vars_):
        return Var(None, None, deps, missing or deps)
    grade = "claimed" if any(v.grade == "claimed" for v in vars_) else "verified"
    return Var(fn(*[v.value for v in vars_]), grade, deps, missing)


def _confirmed_var(values: list | None, slot: Slot) -> Var:
    if not values:
        return Var(None, None, [slot.key], [slot.key])
    v = values[0]
    st = v.get("status")
    if st in VERIFIED_STATUS:
        return Var(v.get("value"), "verified", [slot.key])
    if st == "주장값":
        return Var(v.get("value"), "claimed", [slot.key])
    return Var(None, None, [slot.key], [slot.key])


def profile_config() -> dict:
    return load_yaml(SCHEMA_REFS / "profile_config.yaml")


def _reg_flags(completion: Var, regs: list[dict]) -> dict[str, Var]:
    out = {}
    for r in regs:
        key = f"regulation_flags.{r['id']}"
        eff = r.get("effective_date")
        if not r.get("verified") or not eff:
            out[key] = Var(None, None, completion.deps, [f"regulation:{r['id']}(미검증)"])
            continue
        if completion.value is None:
            out[key] = Var(None, None, completion.deps, completion.missing)
            continue
        eff_year = int(str(eff)[:4])
        y = int(completion.value)
        val = True if y < eff_year else False if y > eff_year else None  # 같은 해는 준공일 미상으로 판정 불가
        out[key] = Var(val, completion.grade if val is not None else None, completion.deps,
                       [] if val is not None else [f"{completion.deps[0]}(준공월 필요)"])
    return out


def build_building(bid: str, label: str, slots: dict[Slot, list], asset_vars: dict[str, Var],
                   meta: dict, cfg: dict, regs: list[dict], confirmed_claims: list[dict],
                   claimed_claims: list[dict]) -> dict:
    V: dict[str, Var] = dict(asset_vars)
    for f in fields_at("building"):
        s = Slot("building", bid, None, f)
        V[f] = _confirmed_var(slots.get(s), s)

    # ── 연식 ──
    ref_year = int(str(meta.get("analysis_date") or date.today().isoformat())[:4])
    V["building_age"] = _combine(lambda y: ref_year - int(y), V["completion_year"])
    hold = meta.get("holding_years")
    close_year = int(str(meta.get("closing_date") or meta.get("analysis_date") or date.today().isoformat())[:4])
    if hold is None:
        V["exit_age"] = Var(None, None, ["asset_meta.holding_years"], ["asset_meta.holding_years(미입력)"])
    else:
        V["exit_age"] = _combine(lambda y: close_year + int(hold) - int(y), V["completion_year"])
    bands = cfg["age_bands"]
    def band(a):
        for b in bands:
            if a < b["lt"]:
                return b["label"]
        return bands[-1]["label"]
    V["age_band"] = _combine(band, V["building_age"])

    # ── 저온 ──
    if V["cold_ratio_pct"].value is not None:
        V["cold_ratio"] = _combine(lambda p: round(p / 100, 4), V["cold_ratio_pct"])
    else:
        V["cold_ratio"] = _combine(lambda c, g: round(c / g, 4) if g else None, V["cold_area_m2"], V["gross_floor_area_m2"])
    tz = cfg["temp_zone_classification"]
    V["temp_zone"] = _combine(lambda r: "상온" if r < tz["ambient_max"] else "저온" if r >= tz["cold_min"] else "복합", V["cold_ratio"])
    V["has_cold"] = _combine(lambda r: r > 0, V["cold_ratio"])

    # ── 하역·동선 ──
    # 연면적 1만평당 도크 수(대) — 낮을수록 도크 부족. 1평 = 400/121 ㎡
    V["dock_density"] = _combine(lambda g, d: round(d / (g * 121 / 400) * 10000, 1) if g else None,
                                 V["gross_floor_area_m2"], V["dock_count"])
    # 하역 방식: 단층 / 다층 램프형(건물 램프) / 다층 지형접안형(지형 단차 진입도로로 여러 층 직접 접안) / 다층 승강기형
    fa, rt, ta = V["floors_above"], V["ramp_type"], V["terrain_multi_level_access"]
    if fa.value == 1:
        V["handling_type"] = _combine(lambda _: "단층", fa)
    elif rt.value in ("단방향", "양방향"):
        V["handling_type"] = _combine(lambda *_: "다층 램프형", fa, rt)
    elif ta.value is True:
        V["handling_type"] = _combine(lambda *_: "다층 지형접안형", fa, ta)
    elif rt.value == "없음" and ta.value is False:
        V["handling_type"] = _combine(lambda *_: "다층 승강기형", fa, rt, ta)
    else:   # 층수·램프·지형 접안 중 확인 안 된 것이 있으면 판정 보류
        V["handling_type"] = Var(None, None, fa.deps + rt.deps + ta.deps,
                                 [m for x in (fa, rt, ta) if x.value is None for m in (x.missing or x.deps)])

    # ── 외피 ──
    comb = cfg["panel_combustibility"]
    V["panel_combustibility"] = _combine(lambda c: comb.get(c), V["wall_panel_core"])
    V["roof_panel_combustibility"] = _combine(lambda c: comb.get(c), V["roof_panel_core"])
    V["cold_insulation_combustibility"] = _combine(lambda c: comb.get(c), V["cold_insulation_material"])

    # ── 층별 (창고층) ──
    floors = sorted({s.floor for s in slots if s.level == "floor" and s.building_id == bid})
    def fvar(fl, f):
        s = Slot("floor", bid, fl, f)
        return _confirmed_var(slots.get(s), s)
    uses = {fl: fvar(fl, "use") for fl in floors}
    # 트럭야드 깊이(SP06): 단지 값(실내 하역장 접안 구획 깊이, 2026-10-14)이 없으면 층별 야드 전체 깊이(yard_depth_m,
    # 차로 포함)의 최솟값 — 옥외 야드 자산(2026-10-20 사용자 지시: 접안 중에도 그 뒤로 차량이 지나갈 수 있어야 함).
    # 기준이 달라 세그먼트 yard_type=옥외로 표시하고 임계값 override(접안 차량 길이 + 통행 차로)를 쓴다
    yard_type = None
    if V["truck_yard_depth_m"].value is None:
        known = [y for y in (fvar(fl, "yard_depth_m") for fl in floors) if y.value is not None]
        if known:
            best = min(known, key=lambda y: y.value)
            V["truck_yard_depth_m"] = Var(best.value, "claimed" if any(y.grade == "claimed" for y in known) else "verified",
                                          [d for y in known for d in y.deps])
            yard_type = "옥외"
    # 저온 비율을 모르더라도 층별 온도대가 확인돼 있으면 저온동 유무는 판정할 수 있다
    if V["has_cold"].value is None and floors:
        temps = {fl: fvar(fl, "temp") for fl in floors}
        cold = [t for t in temps.values() if t.value in ("저온", "냉동", "혼합")]
        known = [t for t in temps.values() if t.value is not None]
        if cold:
            V["has_cold"] = Var(True, "claimed" if any(t.grade == "claimed" for t in cold) else "verified",
                                [d for t in cold for d in t.deps])
        else:
            whf = [fl for fl in floors if uses[fl].value == "창고"]
            if whf and all(temps[fl].value == "상온" for fl in whf):   # 창고층 전부 상온으로 확인
                V["has_cold"] = Var(False, "claimed" if any(temps[fl].grade == "claimed" for fl in whf) else "verified",
                                    [d for fl in whf for d in temps[fl].deps])
    wh = [fl for fl, u in uses.items() if u.value == "창고"]
    unknown_use = [fl for fl, u in uses.items() if u.value is None]
    V["warehouse_floors"] = Var(wh if wh else None, "claimed" if any(uses[f].grade == "claimed" for f in wh) else "verified",
                                [Slot("floor", bid, f, "use").key for f in floors],
                                [Slot("floor", bid, f, "use").key for f in unknown_use] if not wh else [])
    for f in ("floor_load_tpm2", "clear_height_m", "direct_truck_access"):
        if not wh:
            V[f"warehouse_floors.{f}"] = Var(None, None, [], [f"{bid}: 창고 용도 층 미확인"])
            for agg in ("min", "max", "missing_count"):
                V[f"warehouse_floors.{f}.{agg}"] = Var(None, None, [], [f"{bid}: 창고 용도 층 미확인"])
            continue
        series, deps, miss, grades = [], [], [], set()
        for fl in wh:
            v, a = fvar(fl, f), fvar(fl, "area_m2")
            deps += v.deps + a.deps
            if v.value is None:
                miss += v.missing
            else:
                grades.add(v.grade)
            item = {"floor": fl, "value": v.value, "area": a.value}
            if v.value is not None:      # 측정 기준·정밀도 — 상·하한 값은 룰 함수(min_below)가 구간으로 다룬다
                raw = (slots.get(Slot("floor", bid, fl, f)) or [{}])[0]
                item.update(precision=raw.get("precision") or "exact", basis=raw.get("basis"),
                            slot=Slot("floor", bid, fl, f).key)
            series.append(item)
        known = [s["value"] for s in series if s["value"] is not None]
        g = "claimed" if "claimed" in grades else "verified"
        V[f"warehouse_floors.{f}"] = Var(series, g, deps, miss)
        V[f"warehouse_floors.{f}.missing_count"] = Var(len(miss), "verified", deps)
        if known and f != "direct_truck_access":
            V[f"warehouse_floors.{f}.min"] = Var(min(known), g, deps, miss)
            V[f"warehouse_floors.{f}.max"] = Var(max(known), g, deps, miss)
        else:
            V[f"warehouse_floors.{f}.min"] = Var(None, None, deps, miss or deps)
            V[f"warehouse_floors.{f}.max"] = Var(None, None, deps, miss or deps)
    if wh:
        da = V["warehouse_floors.direct_truck_access"]
        no_access = [s["floor"] for s in (da.value or []) if s["value"] is False]
        V["floors_without_direct_access"] = Var(no_access, da.grade, da.deps, da.missing)
        # 기둥 간섭: 간섭 층이 하나라도 확인되면 그 목록, 없는데 미확인 층이 남으면 None(판정 보류)
        series, deps, miss, grades = [], [], [], set()
        for fl in wh:
            v = fvar(fl, "dock_route_column_conflict")
            deps += v.deps
            if v.value is None:
                miss += v.missing
            else:
                grades.add(v.grade)
                series.append((fl, v.value))
        hit = [fl for fl, val in series if val is True]
        g = "claimed" if "claimed" in grades else "verified"
        V["floors_with_dock_column_conflict"] = Var(hit if (hit or not miss) else None, g if (hit or not miss) else None, deps, miss)

    # 창고 상부 데크 야드(SP10): 하역장 하부 값(층고·유효층고·면적)이 하나라도 있는 층. 없으면 빈 목록(미발동) —
    # 하부 구역이 없다는 확인과 기재 없음을 구분할 수 없으므로 보류하지 않는다
    uy = [(fl, f) for fl in floors for f in ("under_yard_area_m2", "under_yard_clear_height_m", "under_yard_floor_height_m")]
    uy_vars = {(fl, f): fvar(fl, f) for fl, f in uy}
    V["floors_with_under_yard"] = Var(sorted({fl for (fl, _), v in uy_vars.items() if v.value is not None}, key=floors.index),
                                      "verified", [k for (fl, f), v in uy_vars.items() if v.value is not None
                                                   for k in v.deps])

    V.update(_reg_flags(V["completion_year"], regs))

    # ── 이력 (리스크 리셋 근거) ──
    V["confirmed_renovation_items"] = Var([c.get("item") or c.get("text") for c in confirmed_claims], "verified", [])
    V["claimed_renovation_items"] = Var([c.get("item") or c.get("text") for c in claimed_claims], "claimed", [])

    seg = {"temp_zone": V["temp_zone"].value, "handling_type": V["handling_type"].value,
           "ramp_type": V["ramp_type"].value, "ramp_form": V["ramp_form"].value, "yard_type": yard_type}
    return {
        "building_id": bid, "label": label, "segment": seg,
        "vars": {k: v.value for k, v in V.items()},
        "grades": {k: v.grade for k, v in V.items()},
        "deps": {k: v.deps for k, v in V.items()},
        "missing": {k: v.missing for k, v in V.items() if v.value is None},
    }


def load_regulations() -> list[dict]:
    regs_path = ENGINE_REFS / "regulation_timeline.yaml"
    return (load_yaml(regs_path) or {}).get("regulations", []) if regs_path.exists() else []


def load_location(asset_id: str) -> dict:
    from ..io import load_json
    p = wf2_dir(asset_id) / "w2_01b_location.json"
    return load_json(p) if p.exists() else {"asset": {}}


def run(asset_id: str) -> dict:
    from ..io import load_json
    out_dir = wf2_dir(asset_id)
    conf = load_json(out_dir / "w2_05_confirmed_spec.json")
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    prof = build_profile(conf, meta, load_location(asset_id))
    save_json(out_dir / "w2_06_profile.json", prof)
    return prof


def build_profile(conf: dict, meta: dict, loc: dict, regs: list[dict] | None = None) -> dict:
    cfg = profile_config()
    regs = load_regulations() if regs is None else regs
    asset_id = conf["asset_id"]
    slots = {s: v for s, v in iter_slots(conf)}
    asset_vars: dict[str, Var] = {}
    for f in fields_at("asset"):
        s = Slot("asset", None, None, f)
        values = slots.get(s) or (loc.get("asset") or {}).get(f)
        asset_vars[f] = _confirmed_var(values, s)

    claims = conf.get("claims") or []
    buildings = []
    # 부속 동(공작물주차장 등, asset_meta에서 role: 부속)은 물류센터 룰 평가 대상에서 제외
    ancillary = {b["id"] for b in meta.get("buildings", []) if b.get("role") == "부속"}
    for b in conf["buildings"]:
        if b["building_id"] == ASSET_BUILDING or b["building_id"] in ancillary:
            continue
        bid = b["building_id"]
        mine = [c for c in claims if c.get("type") == "renovation" and c.get("building_id") in (bid, ASSET_BUILDING, None)]
        buildings.append(build_building(
            bid, b.get("label", bid), slots, asset_vars, meta, cfg, regs,
            [c for c in mine if c.get("status") == "확정"],
            [c for c in mine if c.get("status") != "확정"]))
    # 벡터 좌표 측정값(도면 표기값 아님): 이 슬롯을 쓴 판정은 보고서에 📐 표시
    vector_slots = sorted(s.key for s, vs in slots.items()
                          if vs and vs[0].get("method") == "vector" and vs[0].get("status") in VERIFIED_STATUS)
    return {"asset_id": asset_id, "created_at": now_iso(),
            "analysis_date": meta.get("analysis_date"), "holding_years": meta.get("holding_years"),
            "vector_slots": vector_slots, "buildings": buildings}
