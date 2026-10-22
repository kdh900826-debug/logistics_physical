"""W2-⑤ 사람 응답 반영 → 확정 스펙 (설계서 §2.3 W2-⑤, §3.5 apply_confirmation).

응답 파일 w2_05_user_response.json (리뷰 서버가 저장):
{
  "decisions":  {"<slot>": {"action": "cand", "cand_id": "drawing:0"}
                           | {"action": "claim", "cand_id": "im:0"}          # 주장값 유지
                           | {"action": "correct", "value": 1.2, "reason": "..."}
                           | {"action": "unconfirmed", "reason": "..."}},
  "overrides":  {"<slot>": <위와 같은 형식>},   # 자동 확정·참고 항목을 뒤집을 때
  # 도면·IM 어디에도 없던 필드(unresolved_missing)도 decisions에 "correct"로 값을 줄 수 있다.
  # 도면 재확인으로 찾은 값이면 출처를 함께 준다:
  #   {"action": "correct", "value": 193, "reason": "...", "source_doc": "input/.../A-021.pdf",
  #    "source_locator": {"page": 1, "sheet_no": "A-021"}, "raw_text": "...", "method": "vision" | "vector",
  #    "precision": "approx"}
  # 유효층고(clear_height_m)는 측정 기준 "basis"(배관 하단|천장 하단|보 하단|슬래브 하단)를 함께 준다 — 보·슬래브 하단은 상한
  "claims":     {"claim:0": "확정" | "미확인"},
  "bulk":       "rest_unconfirmed" | null,
  "submitted_at": "..."
}
"""
from __future__ import annotations

import csv
from pathlib import Path

from ..io import load_json, load_yaml, now_iso, save_json
from ..paths import KB, input_dir, wf2_dir
from ..schema import Slot, empty_record, field_def, put
from .sensitivity import cand_to_value

LOG_COLUMNS = ["logged_at", "asset_id", "slot", "field", "drawing_type", "method", "confidence",
               "drawing_value", "final_value", "final_status", "action", "reason"]


def _drawing_type(asset_id: str, cand: dict) -> str | None:
    p = wf2_dir(asset_id) / "w2_03_sheet_index.json"
    if not p.exists():
        return None
    page = (cand.get("locator") or {}).get("page")
    for sh in load_json(p)["sheets"]:
        if Path(sh["file"]).name == Path(cand.get("source_doc") or "").name and sh["page"] == page:
            return sh.get("drawing_type")
    return None


def _decide(it: dict, d: dict) -> dict:
    cands = {c["cand_id"]: c for c in it["candidates"]}
    act = d.get("action")
    if act == "cand":
        c = cands[d["cand_id"]]
        v = cand_to_value(c, "확정", "확정")
        if c["origin"] == "im":
            v["note"] = "G2에서 IM 값 채택"
        return v
    if act == "claim":
        c = cands.get(d.get("cand_id") or "im:0")
        if not c or c["origin"] != "im":
            raise ValueError(f"{it['slot']}: 주장값 유지는 IM 후보에만 가능")
        return cand_to_value(c, "주장값", "IM주장")
    if act == "correct":
        # 출처를 함께 주면(도면 재확인값) 그 출처를 남기고, 없으면 사용자 정정으로 기록
        # basis(유효층고 측정 기준)가 상한 기준(보·슬래브 하단)이면 precision은 upper_bound
        bdef = field_def(it["field"]).get("basis") or {}
        prec = d.get("precision") or ("upper_bound" if d.get("basis") in (bdef.get("upper_bound") or []) else "exact")
        return {"value": d["value"], "unit": field_def(it["field"]).get("unit"), "raw_text": d.get("raw_text"),
                **({"basis": d["basis"]} if d.get("basis") else {}),
                "precision": prec, "source_doc": d.get("source_doc") or "G2 사용자 정정",
                "source_locator": d.get("source_locator") or {"g2": it["slot"]},
                "method": d.get("method") or "user", "confidence": "high", "source_grade": "확정", "status": "확정",
                "note": d.get("reason")}
    if act == "unconfirmed":
        return {"value": None, "status": "미확인", "source_doc": "G2", "source_locator": {"g2": it["slot"]},
                "method": "user", "missing_reason": it.get("missing_reason"), "note": d.get("reason")}
    raise ValueError(f"{it['slot']}: 알 수 없는 action {act}")


def run(asset_id: str) -> dict:
    out_dir = wf2_dir(asset_id)
    ci = load_json(out_dir / "w2_04_confirmation_items.json")
    resp = load_json(out_dir / "w2_05_user_response.json")
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    decisions, overrides = resp.get("decisions") or {}, resp.get("overrides") or {}
    rec = empty_record(asset_id, "confirmed", meta["buildings"])
    log_rows, undecided = [], []

    def log(it, final, action, reason=None):
        if reason == "일괄 미확인 처리":       # 판독 정확도와 무관한 일괄 처리는 기록하지 않음
            return
        for c in it["candidates"]:
            if c["origin"] in ("drawing", "hinted") and c.get("method", "").startswith("vision"):
                if final.get("value") != c["value"] or action == "unconfirmed":
                    log_rows.append({"logged_at": now_iso(), "asset_id": asset_id, "slot": it["slot"],
                                     "field": it["field"], "drawing_type": _drawing_type(asset_id, c),
                                     "method": c["method"], "confidence": c.get("confidence"),
                                     "drawing_value": c["value"], "final_value": final.get("value"),
                                     "final_status": final.get("status"), "action": action, "reason": reason})

    for it in ci["auto_confirmed"]:
        if it["slot"] in overrides:
            d = overrides[it["slot"]]
            v = _decide(it, d)
            log(it, v, "override_auto:" + d["action"], d.get("reason"))
        else:
            c = next(c for c in it["candidates"] if c["cand_id"] == it["adopted"])
            v = cand_to_value(c, "확정(교차)", "확정")
        put(rec, Slot.from_key(it["slot"]), [v])

    for it in ci["reference_items"]:
        d = overrides.get(it["slot"]) or decisions.get(it["slot"])
        if d is None:
            act = it["default_action"]
            d = {"action": "claim", "cand_id": "im:0"} if act == "claim" else {"action": "cand", "cand_id": act}
        put(rec, Slot.from_key(it["slot"]), [_decide(it, d)])

    for it in ci["items"]:
        d = decisions.get(it["slot"])
        if d is None:
            if resp.get("bulk") == "rest_unconfirmed":
                d = {"action": "unconfirmed", "reason": "일괄 미확인 처리"}
            else:
                undecided.append(it["slot"])
                continue
        v = _decide(it, d)
        log(it, v, d["action"], d.get("reason") or d.get("note"))
        put(rec, Slot.from_key(it["slot"]), [v])

    if undecided:
        raise RuntimeError(f"미결정 확인 항목 {len(undecided)}건: {undecided[:5]} …")

    # 미발견 필드에 대한 정정(채팅 지시·도면 재확인) — 확인 항목이 아니므로 correct만 허용
    handled = {it["slot"] for it in ci["items"] + ci["reference_items"] + ci["auto_confirmed"]}
    missing_slots = {Slot(m.get("level") or ("floor" if m.get("floor") else "building" if m.get("building_id") else "asset"),
                          m.get("building_id"), m.get("floor"), m["field"]).key: m
                     for m in ci.get("unresolved_missing") or []}
    for slot, d in decisions.items():
        if slot in handled:
            continue
        if slot not in missing_slots:
            raise ValueError(f"{slot}: 확인 항목에도 미발견 목록에도 없는 슬롯")
        if d.get("action") != "correct":
            raise ValueError(f"{slot}: 미발견 필드는 correct(값 지정)만 가능")
        m = missing_slots[slot]
        it = {"slot": slot, "field": m["field"], "candidates": [], "missing_reason": m.get("missing_reason")}
        put(rec, Slot.from_key(slot), [_decide(it, d)])

    claims_dec = resp.get("claims") or {}
    for c in ci["claims"]:
        st = claims_dec.get(c["claim_id"], "미확인")
        rec["claims"].append(dict(c, status=st))
    dr_path = out_dir / "w2_03_drawing_specs.json"
    if dr_path.exists():
        rec["missing"] = load_json(dr_path).get("missing") or []
    rec["confirmed_at"] = resp.get("submitted_at") or now_iso()
    save_json(out_dir / "w2_05_confirmed_spec.json", rec)

    path = KB / "extraction_log.csv"
    if log_rows and path.exists():
        # 재진입(G3 → W2-⑤)으로 같은 결정을 다시 반영할 때 이미 기록된 정정은 다시 쓰지 않는다(logged_at 제외 비교)
        with open(path, encoding="utf-8-sig", newline="") as f:
            seen = {tuple(r.get(c) or "" for c in LOG_COLUMNS[1:]) for r in csv.DictReader(f)}
        log_rows = [r for r in log_rows if tuple("" if r[c] is None else str(r[c]) for c in LOG_COLUMNS[1:]) not in seen]
    if log_rows:
        new = not path.exists()
        with open(path, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LOG_COLUMNS)
            if new:
                w.writeheader()
            w.writerows(log_rows)
    from collections import Counter
    from ..schema import iter_slots
    st = Counter(vs[0].get("status") for _, vs in iter_slots(rec) if vs)
    return {"status_counts": dict(st), "claims_confirmed": sum(1 for c in rec["claims"] if c["status"] == "확정"),
            "log_rows": len(log_rows)}
