"""W2-⑪ 최종 검토 응답 처리: 승인 → FINAL·코퍼스 편입 / 코멘트 → 재진입 라우팅 (설계서 §2.3 W2-⑪)."""
from __future__ import annotations

import shutil

from .. import session
from ..io import load_json, load_yaml, now_iso, save_json, save_yaml
from ..paths import KB, input_dir, wf2_dir

REENTRY = {"spec": ("W2-⑤", "AWAITING_CONFIRMATION", 0),
           "severity": ("W2-⑧", "EVALUATED", 1),
           "wording": ("W2-⑩", "REPORT_DRAFT", 2)}


def finalize(asset_id: str) -> dict:
    out = wf2_dir(asset_id)
    resp = load_json(out / "w2_11_review_response.json")
    st = session.load(asset_id)
    if resp.get("approved"):
        rep = out / f"{asset_id}_logistics_risk_report.md"
        final = out / f"{asset_id}_logistics_risk_report_final.md"
        shutil.copy(rep, final)
        from .report_html import render as render_html
        html = render_html(asset_id, final=True)
        result = {"state": "FINAL", "report": final.name, "report_html": html.name}
        if resp.get("corpus_include"):
            dst = KB / "corpus" / "inbox" / asset_id
            (dst / "im").mkdir(parents=True, exist_ok=True)
            for f in (input_dir(asset_id) / "im").glob("*"):
                shutil.copy(f, dst / "im" / f.name)
            shutil.copy(out / "w2_05_confirmed_spec.json", dst / "confirmed_spec.json")
            meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
            save_yaml(dst / "deal_meta.yaml", {
                "deal_id": None, "asset_name": meta.get("asset_name"), "source": "wf2_final",
                "wf2_asset_id": asset_id, "ruleset_version": st.get("ruleset_version"),
                "invested": None, "investment_date": None, "outcome_observation_until": None})
            result["corpus_inbox"] = str(dst.relative_to(KB.parent))
        session.transition(asset_id, "FINAL", "G3 승인", final_report=final.name, final_report_html=html.name)
        return result

    comments = resp.get("comments") or []
    if not comments:
        raise RuntimeError("승인도 코멘트도 없는 응답")
    step, state, _ = min((REENTRY[c["type"]] for c in comments), key=lambda x: x[2])
    revs = st.get("revisions") or []
    revs.append({"at": now_iso(), "reason": "; ".join(f"[{c['target']}] {c['text']}" for c in comments)[:500],
                 "reentry": step})
    session.transition(asset_id, state, f"G3 피드백 → {step}", revisions=revs)
    save_json(out / "w2_11_feedback_routing.json", {"reentry": step, "comments": comments})
    return {"state": state, "reentry": step, "comments": len(comments)}
