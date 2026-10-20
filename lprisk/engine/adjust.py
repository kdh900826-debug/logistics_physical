"""W2-⑧ (d) LLM 조정 검증·병합 (설계서 §3.5 validate_adjustments, §1.8-8).

입력: w2_08_base.json (스크립트 판정) + w2_08_llm.json (risk-evaluator 서술·조정 제안)
출력: w2_08_risk_evaluation.json

조정 규칙:
- 상향: llm_adjust ∈ {up_one, up_or_confirmed_down}, 1단계, 근거 필수
- 하향: llm_adjust ∈ {down_confirmed_only, up_or_confirmed_down}, 1단계,
        근거는 G2에서 '확정'된 이력(claim)만. IM 주장 기반 하향은 무효
- ⚪·미발동 룰은 조정 불가
"""
from __future__ import annotations

from ..io import load_json, now_iso, save_json
from ..paths import wf2_dir
from .rules import load_rules, single_grade

UP = {"green": "yellow", "yellow": "red"}
DOWN = {"red": "yellow", "yellow": "green"}
UP_SINGLE = {"green": "red"}          # severity_policy.yaml single_grade: 🟡 없음
DOWN_SINGLE = {"red": "green"}


def check_adjustment(adj: dict, base: dict, rule: dict, confirmed_claims: dict, single: bool = False) -> str | None:
    """위반 사유를 반환 (None이면 유효)."""
    up, down = (UP_SINGLE, DOWN_SINGLE) if single else (UP, DOWN)
    if base["status"] != "triggered" or base["severity_base"] not in ("red", "yellow", "green"):
        return "발동하지 않았거나 판정 보류된 룰은 조정 불가"
    allowed = rule["llm_adjust"]
    if not adj.get("reason") or not adj.get("basis"):
        return "조정 사유·근거 누락"
    if adj["direction"] == "up":
        if allowed not in ("up_one", "up_or_confirmed_down"):
            return f"상향 불허 (llm_adjust={allowed})"
        if base["severity_base"] not in up:
            return "🔴는 더 올릴 수 없음"
        return None
    if adj["direction"] == "down":
        if allowed not in ("down_confirmed_only", "up_or_confirmed_down"):
            return f"하향 불허 (llm_adjust={allowed})"
        if base["severity_base"] not in down:
            return "🟢는 더 내릴 수 없음"
        hist = [b for b in adj["basis"] if b.get("type") == "confirmed_history"]
        if not hist or len(hist) != len(adj["basis"]):
            return "하향 근거는 G2 확정 이력(confirmed_history)만 허용 — IM 주장 기반 하향 금지"
        if not set(rule.get("adjust_basis") or []) & {"replacement_history", "confirmed_history"}:
            return "룰의 adjust_basis가 이력 기반 하향을 허용하지 않음"
        for b in hist:
            if confirmed_claims.get(b.get("ref")) != "확정":
                return f"근거 이력 {b.get('ref')}가 G2에서 확정되지 않음"
        return None
    return f"알 수 없는 방향 {adj.get('direction')}"


def run(asset_id: str) -> dict:
    out_dir = wf2_dir(asset_id)
    base = load_json(out_dir / "w2_08_base.json")
    llm = load_json(out_dir / "w2_08_llm.json")
    conf = load_json(out_dir / "w2_05_confirmed_spec.json")
    claims = {c["claim_id"]: c.get("status") for c in conf.get("claims") or []}
    rules = {r["id"]: r for r in load_rules()["rules"]}
    single = bool(base.get("single_grade")) or single_grade()
    llm_map = {(x["rule_id"], x.get("building_id")): x for x in llm.get("results", [])}

    merged, rejected, uncovered = [], [], []
    for b in base["results"]:
        key = (b["rule_id"], b["building_id"])
        rule = rules[b["rule_id"]]
        x = llm_map.get(key)
        r = dict(b)
        r["severity_final"] = b["severity_base"]
        r["adjustment"] = None
        nar = rule["narrative"]
        r.update(root_cause=nar.get("root_cause"), cascade_risks=nar.get("cascade"),
                 dd_checkpoints=list(nar.get("dd_checkpoints") or []), inference_basis=None, reset_note=None,
                 dd_on_green=bool(rule.get("dd_on_green")))
        if x:
            for k in ("inference_basis", "root_cause", "cascade_risks", "reset_note"):
                if x.get(k):
                    r[k] = x[k]
            if x.get("dd_checkpoints"):
                r["dd_checkpoints"] = x["dd_checkpoints"]
            adj = x.get("adjustment")
            if adj:
                why = check_adjustment(adj, b, rule, claims, single)
                if why:
                    rejected.append({"rule_id": b["rule_id"], "building_id": b["building_id"], "reason": why, "proposal": adj})
                else:
                    r["adjustment"] = adj
                    up, down = (UP_SINGLE, DOWN_SINGLE) if single else (UP, DOWN)
                    r["severity_final"] = (up if adj["direction"] == "up" else down)[b["severity_base"]]
        elif b["status"] in ("triggered", "hold"):
            uncovered.append(f"{b['rule_id']}@{b['building_id']}")
        merged.append(r)

    data = {"asset_id": asset_id, "created_at": now_iso(), "rule_count": base["rule_count"],
            "consistency": base.get("consistency"), "results": merged,
            "rejected_adjustments": rejected, "uncovered": uncovered}
    save_json(out_dir / "w2_08_risk_evaluation.json", data)
    return {"rejected": rejected, "uncovered": uncovered}
