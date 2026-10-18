"""유효층고 측정 기준(basis)과 상·하한 판정 (SP02, 2026-10-18 사용자 결정).

보·슬래브 하단 = 배관 미반영 → 실제 유효층고의 상한. 상한이 기준 미만이면 🔴, 기준 이상이면 ⚪(추정 공제 없음).
"""
import pytest

from lprisk.engine import evaluate as ev_mod
from lprisk.engine.expr import Evaluator, Missing
from lprisk.engine.rules import load_rules
from lprisk.engine.thresholds import ThresholdResolver
from lprisk.spec.normalize import normalize_value
from lprisk.spec.validate import validate_record

K = "warehouse_floors.clear_height_m"


def fl(floor, value, precision="exact", basis=None):
    return {"floor": floor, "value": value, "area": 100, "precision": precision, "basis": basis,
            "slot": f"floor|main|{floor}|clear_height_m"}


def ev(series):
    def resolve(p):
        if p != K or series is None:
            raise Missing(p)
        return series
    return Evaluator(resolve, ThresholdResolver({}, {}))


def test_min_below_intervals():
    f = "min_below(warehouse_floors.clear_height_m, 8.5)"
    assert ev([fl("3F", 9.0), fl("9F", 8.35)]).eval(f) is True                          # 확정값 미달
    assert ev([fl("3F", 9.0), fl("4F", 8.6)]).eval(f) is False                          # 전부 확정 이상
    assert ev([fl("3F", 8.55, "upper_bound", "보 하단"), fl("9F", 8.35, "upper_bound", "보 하단")]).eval(f) is True
    with pytest.raises(Missing) as e:                                                    # 상한만 있고 기준 이상
        ev([fl("3F", 8.55, "upper_bound", "보 하단"), fl("4F", 9.0)]).eval(f)
    assert "상한값만" in e.value.reason and e.value.inputs == ["floor|main|3F|clear_height_m"]
    assert ev([fl("1F", 8.2, "lower_bound")]).eval(f) is True       # IM '8.2m 이상' — 적힌 값으로 비교(원칙 5)
    assert ev([fl("1F", 8.6, "lower_bound")]).eval(f) is False
    with pytest.raises(Missing):                                                         # 값 없는 층
        ev([fl("3F", 9.0), {"floor": "4F", "value": None, "area": 100}]).eval(f)
    assert ev([fl("3F", 8.0), {"floor": "4F", "value": None, "area": 100}]).eval(f) is True


def test_sp02_rule_hold_lists_upper_bound_floors(monkeypatch):
    sp02 = next(r for r in load_rules()["rules"] if r["id"] == "SP02")
    monkeypatch.setattr(ev_mod, "ThresholdResolver", lambda seg: ThresholdResolver(
        seg, {"clear_height": {"default": {"yellow": {"value": 8.5, "verified": True}}}}))
    def ctx(series):
        return {"building_id": "main", "vars": {K: series, K + ".missing_count": 0}, "grades": {K: "verified"},
                "deps": {}, "missing": {}}
    r = ev_mod.evaluate_context(sp02, ctx([fl("3F", 8.55, "upper_bound", "보 하단")]), {})
    assert r["severity_base"] == "hold" and r["now"]["missing_inputs"] == ["floor|main|3F|clear_height_m"]
    r = ev_mod.evaluate_context(sp02, ctx([fl("3F", 8.55, "upper_bound", "보 하단"), fl("9F", 8.35, "upper_bound", "보 하단")]), {})
    assert r["severity_base"] == "yellow"
    r = ev_mod.evaluate_context(sp02, ctx([fl("3F", 8.6, basis="배관 하단")]), {})
    assert r["severity_base"] == "green"


def test_normalize_basis_sets_upper_bound():
    v = normalize_value("clear_height_m", {"value": 8550, "unit": "mm", "basis": "보 하단", "method": "vision"})
    assert (v["value"], v["precision"]) == (8.55, "upper_bound")
    v = normalize_value("clear_height_m", {"value": 8.025, "unit": "m", "basis": "배관 하단", "method": "vision"})
    assert (v.get("precision") or "exact") == "exact"
    v = normalize_value("clear_height_m", {"value": 8.2, "unit": "m", "basis": "보 하단", "precision": "lower_bound",
                                           "method": "im_text"})
    assert v["precision"] == "lower_bound"          # 원문이 '이상'이면 그대로 둔다


def test_validate_basis_enum():
    def rec(field, basis):
        return {"asset": {}, "buildings": [{"building_id": "main", "fields": {}, "floors": [{"floor": "3F", "fields": {
            field: [{"value": 8.5, "unit": "m", "basis": basis, "source_doc": "x.pdf", "source_locator": {"page": 1},
                     "method": "vision"}]}}]}]}
    assert validate_record(rec("clear_height_m", "배관 하단"))["ok"]
    assert not validate_record(rec("clear_height_m", "유닛쿨러 하단"))["ok"]
    assert not validate_record(rec("floor_height_m", "보 하단"))["ok"]       # basis 없는 필드
