"""G2 응답 반영 — 미발견 필드(unresolved_missing) 정정."""
import json

import pytest
import yaml

from lprisk.spec import confirmation as cf


def _setup(tmp_path, monkeypatch, decisions):
    (tmp_path / "in").mkdir(); (tmp_path / "out").mkdir()
    (tmp_path / "in" / "asset_meta.yaml").write_text(
        yaml.safe_dump({"asset_id": "t", "buildings": [{"id": "main", "name": "m"}]}, allow_unicode=True), encoding="utf-8")
    ci = {"items": [], "reference_items": [], "auto_confirmed": [], "claims": [],
          "unresolved_missing": [{"level": "building", "building_id": "main", "field": "turning_radius_m",
                                  "missing_reason": "미기재"}]}
    (tmp_path / "out" / "w2_04_confirmation_items.json").write_text(json.dumps(ci), encoding="utf-8")
    resp = {"decisions": decisions, "bulk": "rest_unconfirmed"}
    (tmp_path / "out" / "w2_05_user_response.json").write_text(json.dumps(resp, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(cf, "wf2_dir", lambda a: tmp_path / "out")
    monkeypatch.setattr(cf, "input_dir", lambda a: tmp_path / "in")
    monkeypatch.setattr(cf, "KB", tmp_path)


def test_missing_field_correct_keeps_source(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, {"building|main|-|turning_radius_m": {
        "action": "correct", "value": 15.8, "reason": "채팅", "method": "vector", "precision": "approx",
        "source_doc": "input/t/drawings/A-400.pdf", "source_locator": {"page": 1, "sheet_no": "A-401"}}})
    cf.run("t")
    rec = json.loads((tmp_path / "out" / "w2_05_confirmed_spec.json").read_text(encoding="utf-8"))
    b = next(b for b in rec["buildings"] if b["building_id"] == "main")
    v = b["fields"]["turning_radius_m"][0]
    assert (v["value"], v["method"], v["status"], v["source_locator"]["sheet_no"]) == (15.8, "vector", "확정", "A-401")


def test_unknown_slot_rejected(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, {"building|main|-|dock_count": {"action": "correct", "value": 1}})
    with pytest.raises(ValueError):
        cf.run("t")
