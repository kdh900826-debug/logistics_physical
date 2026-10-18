"""로컬 리뷰 서버 — G2 스펙 확인 / G3 최종 검토 / 보고서 열람 (설계서 §2.3 W2-⑤⑪, §2.5).

    python -m lprisk review [--port 8765] [--no-browser]

localhost 전용. 제출 결과는 산출물 폴더에 JSON으로 직접 저장하고, 오케스트레이터는 그 파일로 게이트 통과를 판단한다.
"""
from __future__ import annotations

import io
import re
import webbrowser
from pathlib import Path

import fitz
from flask import Flask, abort, jsonify, render_template, request, send_file
from markupsafe import Markup

from ..io import load_json, load_yaml, now_iso, save_json
from ..paths import INPUT, OUTPUT, ROOT, TESTS, input_dir, wf2_dir

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
app.json.ensure_ascii = False

SERVE_ROOTS = [OUTPUT.resolve(), INPUT.resolve()]

_URL = re.compile(r"https?://[^\s|;)]+")
app.jinja_env.filters["regex_urls"] = lambda s: _URL.findall(s or "")
app.jinja_env.globals["SEV"] = {"red": "🔴", "yellow": "🟡", "green": "🟢", "hold": "⚪", "none": "—"}
app.jinja_env.globals["SEVTXT"] = {"red": "발동", "yellow": "주의", "green": "양호", "hold": "보류", "none": "미발동"}
app.jinja_env.filters["md_inline"] = lambda s: Markup(re.sub(r"^<p>|</p>$", "", _md_html(s or "").strip()))
app.jinja_env.filters["strip_urls"] = lambda s: re.sub(r"\s*\|?\s*" + _URL.pattern, "", s or "").strip(" |;")


def _safe(rel_path: str) -> Path:
    p = (ROOT / rel_path).resolve()
    if not any(str(p).startswith(str(r)) for r in SERVE_ROOTS + [ROOT.resolve()]) or not p.exists():
        abort(404)
    if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".pdf", ".docx", ".pptx"):
        abort(403)
    return p


@app.get("/")
def index():
    assets = []
    for d in sorted((OUTPUT / "wf2").glob("*")):
        st = d / "session_state.json"
        if st.exists():
            s = load_json(st)
            assets.append({"asset_id": d.name, "state": s.get("state"), "mode": s.get("mode"),
                           "pca": (TESTS / "golden" / d.name / "golden_spec.json").exists()})
    return render_template("index.html", assets=assets)


@app.get("/file")
def file():
    return send_file(_safe(request.args["path"]))


@app.get("/render")
def render_page():
    """원문 페이지 렌더링 (IM·도면 PDF). 근거 확인용."""
    p = _safe(request.args["path"])
    page = int(request.args.get("page", 1))
    dpi = min(int(request.args.get("dpi", 110)), 200)
    if p.suffix.lower() != ".pdf":
        abort(400)
    doc = fitz.open(p)
    if not 1 <= page <= len(doc):
        abort(404)
    png = doc[page - 1].get_pixmap(dpi=dpi).tobytes("png")
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.get("/g2/<asset_id>")
def g2(asset_id):
    out = wf2_dir(asset_id)
    p = out / "w2_04_confirmation_items.json"
    if not p.exists():
        abort(404)
    ci = load_json(p)
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    done = (out / "w2_05_user_response.json").exists()
    inv = out / "w2_01_inventory.json"
    docs = [d["path"] for d in load_json(inv).get("drawings", [])] if inv.exists() else []
    return render_template("g2.html", ci=ci, meta=meta, asset_id=asset_id, done=done, docs=docs)


@app.post("/api/g2/<asset_id>")
def g2_submit(asset_id):
    data = request.get_json(force=True)
    out = wf2_dir(asset_id)
    ci = load_json(out / "w2_04_confirmation_items.json")
    pending = [it["slot"] for it in ci["items"] if it["slot"] not in (data.get("decisions") or {})]
    if pending and data.get("bulk") != "rest_unconfirmed":
        return jsonify({"ok": False, "error": f"미결정 항목 {len(pending)}건", "pending": pending}), 400
    for slot, d in (data.get("decisions") or {}).items():
        if d.get("action") == "correct" and (d.get("value") in (None, "") or not d.get("reason")):
            return jsonify({"ok": False, "error": f"{slot}: 정정 값과 사유를 모두 입력하세요"}), 400
    data["submitted_at"] = now_iso()
    save_json(out / "w2_05_user_response.json", data)
    return jsonify({"ok": True, "saved": f"output/wf2/{asset_id}/w2_05_user_response.json"})


def _g3_evidence(out: Path, cards: list[dict]) -> dict:
    """룰 카드별 판정 입력값의 근거 (확정 스펙 값·출처·크롭). 키: rule_id@building_id."""
    from ..schema import Slot, iter_slots
    p = out / "w2_05_confirmed_spec.json"
    confirmed = {s.key: vs for s, vs in iter_slots(load_json(p))} if p.exists() else {}
    ev = {}
    for r in cards:
        rows, seen = [], set()
        for h in (r.get("now"), r.get("exit")):
            if not h:
                continue
            missing = set(h.get("missing_inputs") or [])
            deps = [k for ks in (h.get("fact_deps") or {}).values() for k in ks] + sorted(missing)
            for key in deps:
                if key in seen:
                    continue
                seen.add(key)
                if key.count("|") != 3:      # asset_meta 입력·임계값 등 스펙 슬롯이 아닌 의존
                    rows.append({"slot": key, "label": key, "v": None, "loc": {}, "crop": None, "missing": True})
                    continue
                vals =[v for v in confirmed.get(key, []) if v.get("value") is not None]
                v = vals[0] if vals else None
                loc = (v or {}).get("source_locator") or {}
                rows.append({"slot": key, "label": Slot.from_key(key).label(), "v": v, "loc": loc,
                             "crop": loc.get("crop"), "missing": v is None})
        ev[f"{r['rule_id']}@{r.get('building_id') or ''}"] = rows
    return ev


@app.get("/g3/<asset_id>")
def g3(asset_id):
    out = wf2_dir(asset_id)
    ev = load_json(out / "w2_08_risk_evaluation.json")
    report = next(out.glob(f"{asset_id}_logistics_risk_report*.md"), None)
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    order = {"red": 0, "yellow": 1, "green": 2, "hold": 3}
    cards = sorted([r for r in ev["results"] if r["status"] in ("triggered", "hold")],
                   key=lambda r: (order[r["severity_final"]], r["rule_id"]))
    return render_template("g3.html", asset_id=asset_id, meta=meta, cards=cards,
                           evidence=_g3_evidence(out, cards),
                           report_html=_md_html(report.read_text(encoding="utf-8")) if report else None,
                           done=(out / "w2_11_review_response.json").exists())


@app.post("/api/g3/<asset_id>")
def g3_submit(asset_id):
    data = request.get_json(force=True)
    for c in data.get("comments") or []:
        if c.get("type") not in ("spec", "severity", "wording"):
            return jsonify({"ok": False, "error": "코멘트마다 유형(스펙 정정/심각도 이견/문구 수정)을 고르세요"}), 400
    if data.get("approved") and data.get("comments"):
        return jsonify({"ok": False, "error": "승인과 수정 요청을 동시에 보낼 수 없습니다"}), 400
    data["submitted_at"] = now_iso()
    save_json(wf2_dir(asset_id) / "w2_11_review_response.json", data)
    return jsonify({"ok": True})


@app.get("/thresholds")
def thresholds():
    from ..engine.threshold_review import build_items
    return render_template("thresholds.html", d=build_items())


@app.post("/api/thresholds")
def thresholds_submit():
    from ..engine.threshold_review import apply
    try:
        r = apply((request.get_json(force=True) or {}).get("decisions") or {})
    except (ValueError, KeyError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, **r})


@app.get("/pca/<asset_id>")
def pca(asset_id):
    """실사 대조: WF2 결과 ↔ 물리실사 골든 (tests/golden/{a}/)."""
    from ..golden import golden_dir
    from .pca_compare import build
    if not (golden_dir(asset_id) / "golden_spec.json").exists():
        abort(404)
    return render_template("pca.html", asset_id=asset_id, d=build(asset_id))


@app.get("/report/<asset_id>")
def report(asset_id):
    out = wf2_dir(asset_id)
    p = next(out.glob(f"{asset_id}_logistics_risk_report*.md"), None) or out / f"{asset_id}_report_skeleton.md"
    if not p.exists():
        abort(404)
    return render_template("report.html", asset_id=asset_id, title=p.name, html=_md_html(p.read_text(encoding="utf-8")),
                           pca=(TESTS / "golden" / asset_id / "golden_spec.json").exists())


def _md_html(text: str) -> str:
    import markdown
    html = markdown.markdown(text, extensions=["tables"])
    # 산출물 상대 경로 링크(크롭 등)를 /file 경유로
    return re.sub(r'href="(output/[^"]+)"', lambda m: f'href="/file?path={m.group(1)}" target="_blank"', html)


def serve(port: int = 8765, open_browser: bool = True):
    url = f"http://127.0.0.1:{port}/"
    if open_browser:
        webbrowser.open(url)
    app.run(host="127.0.0.1", port=port, debug=False)
