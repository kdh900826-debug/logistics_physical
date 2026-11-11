"""스크립트 영역 단위 테스트 (설계서 §3.12-10 룰 경계값 테스트)."""
import pytest

from lprisk.engine import evaluate as ev_mod
from lprisk.engine.adjust import check_adjustment
from lprisk.engine.expr import Evaluator, ExprError, Missing, parse, variables
from lprisk.engine.thresholds import ThresholdResolver
from lprisk.spec.normalize import normalize_value
from lprisk.spec.reconcile import direction, matches


# ── 제한 문법 ──────────────────────────────────────────
def ev(vars_, th=None):
    def resolve(p):
        if p not in vars_ or vars_[p] is None:
            raise Missing(p)
        return vars_[p]
    return Evaluator(resolve, ThresholdResolver({}, th or {}))


def test_expr_rejects_unsafe_syntax():
    for bad in ["__import__('os')", "a + 1", "x[0]", "lambda: 1", "open('f')"]:
        with pytest.raises(ExprError):
            parse(bad)


def test_expr_kleene_logic():
    e = ev({"a": 5, "b": None})
    assert e.eval("a > 3 or b > 1") is True          # 참이 하나면 참
    assert e.eval("a > 9 and b > 1") is False         # 거짓이 하나면 거짓
    with pytest.raises(Missing):
        e.eval("a > 9 or b > 1")                      # 판단 불가
    assert e.eval("b == null") is True


def test_expr_area_share_and_floors():
    series = [{"floor": "1F", "value": 2.0, "area": 100}, {"floor": "2F", "value": 1.2, "area": 300}]
    e = ev({"s": series})
    assert e.eval("area_share_below(s, 1.5) > 0.7") is True
    assert e.eval("count(floors_below(s, 1.5)) == 1") is True


def test_variables_excludes_thresholds():
    assert variables("a.b.min < th.floor_load.red and c != null") == {"a.b.min", "c"}


# ── 정규화 ────────────────────────────────────────────
def test_normalize_units():
    v = normalize_value("floor_load_tpm2", {"value": 20, "unit": "kN/㎡", "method": "vision"})
    assert v["value"] == pytest.approx(2.0394, abs=1e-3) and v["unit"] == "t/m2"
    v = normalize_value("gross_floor_area_m2", {"value": "30,000", "unit": "평", "precision": "rounded", "method": "im_text"})
    assert v["value"] == pytest.approx(99173.55, abs=0.1)
    assert v["precision_halfwidth"] == pytest.approx(5000 * 3.305785, rel=1e-6)   # 만 평 단위 반올림
    v = normalize_value("ramp_slope_pct", {"value": "1/8", "unit": None, "method": "im_text"})
    assert v["value"] == 12.5
    v = normalize_value("power_capacity_kw", {"value": 7500, "unit": "kVA", "method": "im_text"})
    assert v["value"] is None and any(f.startswith("unit_unknown") for f in v["flags"])   # kVA는 kW로 환산하지 않음


def test_confidence_cannot_be_raised():
    v = normalize_value("clear_height_m", {"value": 10, "unit": "m", "method": "vision", "confidence": "high"})
    assert v["confidence"] == "low"


# ── 대조 ──────────────────────────────────────────────
def test_precision_intervals():
    im = {"value": 1.5, "precision": "lower_bound"}
    assert matches("floor_load_tpm2", im, {"value": 2.0})
    assert not matches("floor_load_tpm2", im, {"value": 1.2})
    im = {"value": 7.5, "precision": "upper_bound"}
    assert not matches("ramp_slope_pct", im, {"value": 8.52})
    im = normalize_value("clear_height_m", {"value": 10, "unit": "m", "precision": "approx", "method": "im_text"})
    assert matches("clear_height_m", im, {"value": 9.6})          # '약 10m' → ±0.5


def test_direction():
    assert direction("ramp_slope_pct", 7.5, 8.52) == "overstated"   # 경사는 낮을수록 유리
    assert direction("floor_load_tpm2", 1.5, 2.0) == "conservative"
    assert direction("wall_panel_core", "글라스울", "EPS") == "overstated"
    assert direction("cold_floor_heave_protection", True, False) == "overstated"


# ── 룰 판정 ────────────────────────────────────────────
RULE = {"id": "T01", "title": "t", "category": "spec", "scope": "per_building", "horizon": "now",
        "inputs": ["warehouse_floors.floor_load_tpm2"],
        "trigger": "warehouse_floors.floor_load_tpm2.min != null",
        "severity": {"red": "warehouse_floors.floor_load_tpm2.min < th.floor_load.red",
                     "yellow": "warehouse_floors.floor_load_tpm2.min < th.floor_load.yellow",
                     "green": "otherwise"},
        "on_missing": "hold", "llm_adjust": "up_one"}


def ctx(minv, missing_count=0, grade="verified"):
    k = "warehouse_floors.floor_load_tpm2"
    return {"building_id": "main", "vars": {k + ".min": minv, k + ".missing_count": missing_count},
            "grades": {k + ".min": grade}, "deps": {}, "missing": {}}


@pytest.fixture
def table(monkeypatch):
    def use(t):
        monkeypatch.setattr(ev_mod, "ThresholdResolver", lambda seg: ThresholdResolver(seg, t))
    return use


def T(red=None, yellow=None, verified=True):
    d = {}
    if red is not None:
        d["red"] = {"value": red, "verified": verified}
    if yellow is not None:
        d["yellow"] = {"value": yellow, "verified": verified}
    return {"floor_load": {"default": d}}


def test_severity_boundaries(table):
    table(T(1.2, 1.5))
    assert ev_mod.evaluate_context(RULE, ctx(1.1), {})["severity_base"] == "red"
    assert ev_mod.evaluate_context(RULE, ctx(1.2), {})["severity_base"] == "yellow"   # 경계값: 미만만 발동
    assert ev_mod.evaluate_context(RULE, ctx(1.5), {})["severity_base"] == "green"


def test_unverified_threshold_holds(table):
    table(T(1.2, 1.5, verified=False))
    r = ev_mod.evaluate_context(RULE, ctx(2.0), {})
    assert r["severity_base"] == "hold" and r["now"]["hold_reason"] == "기준값 미검증"


def test_undefined_level_is_skipped(table):
    table(T(red=None, yellow=1.5))
    assert ev_mod.evaluate_context(RULE, ctx(1.3), {})["severity_base"] == "yellow"
    assert ev_mod.evaluate_context(RULE, ctx(2.0), {})["severity_base"] == "green"
    table({"floor_load": {"default": {}}})
    assert ev_mod.evaluate_context(RULE, ctx(2.0), {})["severity_base"] == "hold"     # 정의된 등급이 하나도 없음


def test_partial_floors_and_claimed_green_hold(table):
    table(T(1.2, 1.5))
    assert ev_mod.evaluate_context(RULE, ctx(2.0, missing_count=1), {})["severity_base"] == "hold"
    assert ev_mod.evaluate_context(RULE, ctx(1.0, missing_count=1), {})["severity_base"] == "red"   # 나쁜 값은 이미 확인
    r = ev_mod.evaluate_context(RULE, ctx(2.0, grade="claimed"), {})
    assert r["severity_base"] == "hold" and "주장값" in r["now"]["hold_reason"]


def test_vector_inputs_marked(table):
    """벡터 좌표 측정 슬롯(method: vector)을 쓴 판정은 vector_inputs로 표시된다 — 보고서 📐 표시 근거."""
    table(T(1.2, 1.5))
    c = ctx(2.0)
    k = "warehouse_floors.floor_load_tpm2.min"
    c["deps"] = {k: ["floor|main|1F|floor_load_tpm2"]}
    assert ev_mod.evaluate_context(RULE, c, {})["now"]["vector_inputs"] == []
    c["vector_slots"] = ["floor|main|1F|floor_load_tpm2"]
    r = ev_mod.evaluate_context(RULE, c, {})
    assert r["severity_base"] == "green" and r["now"]["vector_inputs"] == ["floor|main|1F|floor_load_tpm2"]


def test_horizon_both_uses_exit_age(table):
    table({"aging_roof": {"default": {"yellow": {"value": 8, "verified": True}}}})
    rule = {"id": "G06", "title": "t", "category": "aging", "scope": "per_building", "horizon": "both",
            "inputs": ["building_age"], "trigger": "building_age != null",
            "severity": {"yellow": "building_age >= th.aging_roof.yellow", "green": "otherwise"},
            "on_missing": "hold", "llm_adjust": "up_one"}
    c = {"building_id": "main", "vars": {"building_age": 4, "exit_age": 11}, "grades": {}, "deps": {}, "missing": {}}
    r = ev_mod.evaluate_context(rule, c, {})
    assert (r["severity_base"], r["severity_exit"]) == ("green", "yellow")


def test_sp08_turning_radius_only_holds_itself(table):
    """회전반경은 SP08 단독 룰 — 미확인이어도 SP05(램프)는 영향받지 않는다."""
    from lprisk.engine.rules import load_rules
    loaded = load_rules()
    assert loaded["errors"] == []
    rules = {r["id"]: r for r in loaded["rules"]}
    sp08 = rules["SP08"]
    assert "turning_radius_m" not in str(rules["SP05"]["severity"])
    table({"turning_radius": {"default": {"red": {"value": 12.0, "verified": True},
                                          "yellow": {"value": 12.5, "verified": True}}}})
    def c(r):
        return {"building_id": "main", "vars": {"turning_radius_m": r}, "grades": {}, "deps": {}, "missing": {}}
    assert ev_mod.evaluate_context(sp08, c(11.5), {})["severity_base"] == "red"
    assert ev_mod.evaluate_context(sp08, c(12.0), {})["severity_base"] == "yellow"   # 송온 R-12M
    assert ev_mod.evaluate_context(sp08, c(12.5), {})["severity_base"] == "green"    # 석남 R12,500
    assert ev_mod.evaluate_context(sp08, c(None), {})["severity_base"] == "hold"


def test_sp09_column_conflict_kleene():
    """간섭 층이 하나라도 확인되면 🟡, 없는데 미확인 층이 남으면 ⚪ (추정 금지)."""
    from lprisk.engine.rules import load_rules
    sp09 = {r["id"]: r for r in load_rules()["rules"]}["SP09"]
    def c(v):
        return {"building_id": "main", "vars": {"floors_with_dock_column_conflict": v}, "grades": {}, "deps": {}, "missing": {}}
    assert ev_mod.evaluate_context(sp09, c(["2F"]), {})["severity_base"] == "yellow"
    assert ev_mod.evaluate_context(sp09, c([]), {})["severity_base"] == "green"
    assert ev_mod.evaluate_context(sp09, c(None), {})["severity_base"] == "hold"


def test_fr05_warehouse_depth(table):
    """창고 내부 깊이: 기준값이 없으면 ⚪, 있으면 초과 시 발동."""
    from lprisk.engine.rules import load_rules
    fr05 = {r["id"]: r for r in load_rules()["rules"]}["FR05"]
    def c(d):
        return {"building_id": "main", "vars": {"warehouse_depth_m": d}, "grades": {}, "deps": {}, "missing": {}}
    table({})
    assert ev_mod.evaluate_context(fr05, c(77), {})["severity_base"] == "hold"        # 임계값 미정
    table({"warehouse_depth": {"default": {"red": {"value": 77, "verified": True}}}})   # 사용자 결정 🔴 단일
    assert ev_mod.evaluate_context(fr05, c(77), {})["severity_base"] == "red"         # 석남동(화재) 77m — 이상(>=)이라 걸림
    assert ev_mod.evaluate_context(fr05, c(76.9), {})["severity_base"] == "green"
    assert ev_mod.evaluate_context(fr05, c(53), {})["severity_base"] == "green"       # 원창 53m
    assert ev_mod.evaluate_context(fr05, c(None), {})["severity_base"] == "hold"


def test_fr06_ohd_sprinkler_gap():
    """OHD 하부 살수장애: 확인되면 🟡, 보강 확인되면 🟢, 미기재면 ⚪."""
    from lprisk.engine.rules import load_rules
    fr06 = {r["id"]: r for r in load_rules()["rules"]}["FR06"]
    def c(v):
        return {"building_id": "main", "vars": {"ohd_sprinkler_gap": v}, "grades": {}, "deps": {}, "missing": {}}
    assert ev_mod.evaluate_context(fr06, c(True), {})["severity_base"] == "yellow"
    assert ev_mod.evaluate_context(fr06, c(False), {})["severity_base"] == "green"
    assert ev_mod.evaluate_context(fr06, c(None), {})["severity_base"] == "hold"


def test_handling_type_terrain_access():
    """지형 단차 접안: 램프 없음 + 지형 접안 → 다층 지형접안형, 램프가 있으면 램프형 우선 (골든 회귀)."""
    from lprisk.engine.threshold_calibration import golden_profiles
    gp = golden_profiles()
    ht = {(a, b["building_id"]): b["vars"].get("handling_type") for a, g in gp.items() for b in g["profile"]["buildings"]}
    assert ht[("hyeonbang", "bldg_a")] == "다층 지형접안형"
    assert ht[("icheon", "main")] == "다층 램프형"        # 지형 접안 + 램프 → 램프형


# ── LLM 조정 검증 ──────────────────────────────────────
BASE = {"status": "triggered", "severity_base": "yellow"}


def test_adjust_down_requires_confirmed_history():
    rule = {"llm_adjust": "up_or_confirmed_down", "adjust_basis": ["replacement_history"]}
    im_based = {"direction": "down", "reason": "IM에 재시공 주장", "basis": [{"type": "im_claim", "ref": "claim:0"}]}
    assert "IM 주장" in check_adjustment(im_based, BASE, rule, {"claim:0": "미확인"})
    hist = {"direction": "down", "reason": "확정된 교체", "basis": [{"type": "confirmed_history", "ref": "claim:0"}]}
    assert check_adjustment(hist, BASE, rule, {"claim:0": "미확인"}) is not None
    assert check_adjustment(hist, BASE, rule, {"claim:0": "확정"}) is None


def test_adjust_up_rules():
    up = {"direction": "up", "reason": "연약지반", "basis": [{"type": "location", "ref": "soft_ground"}]}
    assert check_adjustment(up, BASE, {"llm_adjust": "up_one"}, {}) is None
    assert check_adjustment(up, BASE, {"llm_adjust": "none"}, {}) is not None
    assert check_adjustment(up, {"status": "hold", "severity_base": "hold"}, {"llm_adjust": "up_one"}, {}) is not None


# ── 단일 등급 정책 (severity_policy.yaml single_grade) ──────────
def test_single_grade_merges_yellow(table):
    table(T(red=1.0, yellow=1.5))
    prof = {"buildings": [dict(ctx(1.3), segment={})]}
    raw = ev_mod.evaluate_profile(prof, [RULE], single=False)[0]
    merged = ev_mod.evaluate_profile(prof, [RULE], single=True)[0]
    assert raw["severity_base"] == "yellow"
    assert merged["severity_base"] == "red" and merged["merged_from"] == {"severity_base": "yellow"}
    low = {"buildings": [dict(ctx(0.8), segment={})]}
    assert ev_mod.evaluate_profile(low, [RULE], single=True)[0]["severity_base"] == "red"


def test_single_grade_adjust_steps():
    up = {"direction": "up", "reason": "연약지반", "basis": [{"type": "location", "ref": "soft_ground"}]}
    green = {"status": "triggered", "severity_base": "green"}
    red = {"status": "triggered", "severity_base": "red"}
    assert check_adjustment(up, green, {"llm_adjust": "up_one"}, {}, single=True) is None
    assert check_adjustment(up, red, {"llm_adjust": "up_one"}, {}, single=True) is not None


# ── 최종 보고서 HTML ──────────────────────────────────
def test_report_html_relative_links():
    from lprisk.paths import ROOT
    from lprisk.review.report_html import md_to_html
    html = md_to_html("| a |\n|---|\n| [근거](output/wf2/x/crops/c.png) |", ROOT / "output" / "wf2" / "x")
    assert "<table>" in html and 'href="crops/c.png"' in html


def test_outdoor_yard_override():
    """SP06: 옥외 야드(yard_type=옥외)는 접안 차량 + 통행 차로 기준 override를 쓴다 (2026-10-20)."""
    t = {"truck_yard_depth": {"default": {"red": {"value": 13, "verified": True}},
                              "overrides": [{"when": {"yard_type": "옥외"}, "red": {"value": 19.95, "verified": True}}]}}
    assert ThresholdResolver({}, t)("truck_yard_depth.red") == 13
    assert ThresholdResolver({"yard_type": None}, t)("truck_yard_depth.red") == 13
    assert ThresholdResolver({"yard_type": "옥외"}, t)("truck_yard_depth.red") == 19.95


def test_sp10_sp11_dd_rules():
    """SP10 램프 접합·하부 창고 / SP11 상온창고 기계 환기 부재: 등급 없이 DD 포인트(dd_on_green) (2026-11-11)."""
    from lprisk.engine.rules import load_rules
    rules = {r["id"]: r for r in load_rules()["rules"]}
    sp10, sp11 = rules["SP10"], rules["SP11"]
    assert sp10.get("dd_on_green") and sp11.get("dd_on_green")
    def c(**v):
        return {"building_id": "main", "vars": v, "grades": {}, "deps": {}, "missing": {}}
    r = ev_mod.evaluate_context(sp10, c(floors_with_under_yard=[], floors_with_under_ramp=["1F"]), {})
    assert (r["status"], r["severity_base"]) == ("triggered", "green")
    r = ev_mod.evaluate_context(sp10, c(floors_with_under_yard=[], floors_with_under_ramp=[]), {})
    assert r["status"] == "not_triggered"
    assert ev_mod.evaluate_context(sp11, c(floors_without_mech_ventilation=["1F"]), {})["status"] == "triggered"
    assert ev_mod.evaluate_context(sp11, c(floors_without_mech_ventilation=[]), {})["status"] == "not_triggered"
    assert ev_mod.evaluate_context(sp11, c(floors_without_mech_ventilation=None), {})["severity_base"] == "hold"


def test_sp12_open_ramp_snow_melting():
    """SP12 오픈 램프 스노우멜팅: 램프·대지 경사로가 있고 오픈 구간이 있을 때만 발동, 설비 없으면 🟡 (2026-11-11)."""
    from lprisk.engine.rules import load_rules
    sp12 = {r["id"]: r for r in load_rules()["rules"]}["SP12"]
    assert sp12.get("dd_on_green")
    def c(**v):
        base = dict(floors_above=3, ramp_type="양방향", ramp_slope_pct=None, terrain_multi_level_access=False,
                    ramp_open_section=True, ramp_snow_melting=None)
        base.update(v)
        return {"building_id": "main", "vars": base, "grades": {}, "deps": {}, "missing": {}}
    def run(**v):
        r = ev_mod.evaluate_context(sp12, c(**v), {})
        return r["status"], r["severity_base"]
    assert run(ramp_snow_melting=False) == ("triggered", "yellow")
    assert run(ramp_snow_melting=True) == ("triggered", "green")
    assert run() == ("hold", "hold")                                       # 설비 미확인
    assert run(ramp_open_section=False)[0] == "not_triggered"              # 지붕 덮인 램프
    assert run(ramp_type="없음")[0] == "not_triggered"                     # 램프·대지 경사로 없음
    assert run(ramp_type="없음", ramp_slope_pct=12.0, ramp_snow_melting=False) == ("triggered", "yellow")  # 옥외 대지 경사로
    assert run(ramp_open_section=None)[0] == "hold"                        # 오픈 여부 미확인
    assert run(ramp_type="없음", terrain_multi_level_access=True, ramp_snow_melting=False)[1] == "yellow"  # 지형접안 진입도로
    assert run(floors_above=1, ramp_open_section=None)[0] == "not_triggered"   # 단층은 ⚪ 노이즈 없이 미발동


def test_sp13_access_road_unverified_threshold_holds():
    """SP13 단지 진입로: 🔴 기준(7.5m)이 사용자 확인 전(verified: false)이라 값이 있어도 ⚪ — 원칙 7."""
    from lprisk.engine.rules import load_rules
    from lprisk.engine.thresholds import load_thresholds
    sp13 = {r["id"]: r for r in load_rules()["rules"]}["SP13"]
    assert sp13["scope"] == "asset" and sp13.get("dd_on_green")
    ctx = {"building_id": None, "vars": {"access_road_width_m": 6.0}, "grades": {}, "deps": {}, "missing": {}}
    r = ev_mod.evaluate_context(sp13, ctx, {})
    th = load_thresholds()["access_road_width"]["default"]["red"]
    if th.get("verified"):
        assert r["severity_base"] == ("red" if 6.0 < th["value"] else "green")
    else:
        assert (r["severity_base"], r["now"]["hold_reason"]) == ("hold", "기준값 미검증")
    ctx["vars"]["access_road_width_m"] = None
    assert ev_mod.evaluate_context(sp13, ctx, {})["severity_base"] == "hold"


def test_golden_snow_melting_values():
    """골든: 북항 오픈 램프+스노우멜팅(DD p22) → SP12 🟢, 청라·송온1은 스노우멜팅만 기재 → 오픈 여부 미확인."""
    from lprisk.engine.threshold_calibration import golden_profiles
    gp = golden_profiles()
    def v(a):
        return {b["building_id"]: b["vars"] for b in gp[a]["profile"]["buildings"]}["main"]
    assert (v("bukhang")["ramp_open_section"], v("bukhang")["ramp_snow_melting"]) == (True, True)
    assert v("cheongna")["ramp_snow_melting"] is True and v("cheongna")["ramp_open_section"] is None
    assert v("songon1")["ramp_snow_melting"] is True

def test_profile_under_ramp_and_ventilation():
    """골든 송온2: 램프 접합 1F·2F(DD p42), 기계 환기 없는 상온창고 1F~3F(DD p60). B2 저온층은 환기 판정 제외."""
    from lprisk.engine.threshold_calibration import golden_profiles
    gp = golden_profiles()
    v = {b["building_id"]: b["vars"] for b in gp["songon"]["profile"]["buildings"]}["main"]
    assert v["floors_with_under_ramp"] == ["1F", "2F"]
    assert v["floors_without_mech_ventilation"] == ["1F", "2F", "3F"]
    # 환기 값이 없는 골든(송온1)은 상온 창고층이 미확인으로 남아 판정 보류
    v1 = {b["building_id"]: b["vars"] for b in gp["songon1"]["profile"]["buildings"]}["main"]
    assert v1["floors_with_under_ramp"] == []
