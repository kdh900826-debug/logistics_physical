"""스크립트 단계 CLI. 오케스트레이터(CLAUDE.md)가 호출한다.

    python -m lprisk <명령> <asset_id> [옵션]

결과 요약은 stdout에 JSON 한 덩어리로 출력한다. 실패 시 종료코드 1과 사유.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback


def _print(obj):
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_intake(a):
    from .doc_ingest import detect_format
    from . import session
    inv = detect_format.run(a.asset)
    session.init(a.asset, inv["mode"])
    return {"mode": inv["mode"], "im": [f["name"] for f in inv["im"]],
            "drawings": [(f["name"], f.get("format"), f.get("pages")) for f in inv["drawings"]],
            "est_vision_tiles": inv["est_vision_tiles"], "escalations": inv["escalations"]}


def cmd_extract_im_text(a):
    from .doc_ingest import extract_text
    from .io import load_json
    from .paths import wf2_dir
    inv = load_json(wf2_dir(a.asset) / "w2_01_inventory.json")
    data = extract_text.run(a.asset, inv)
    return {"docs": [{"path": d["path"], "units": len(d["units"]),
                      "scan_units": sum(1 for u in d["units"] if u.get("scan"))} for d in data["docs"]]}


def cmd_classify_sheets(a):
    from .doc_ingest import sheets
    idx = sheets.classify_sheets(a.asset)
    return {"sheets": len(idx["sheets"]), "index": f"output/wf2/{a.asset}/w2_03_sheet_index.json"}


def cmd_tiles(a):
    from .doc_ingest import sheets
    tiles = sheets.rasterize_tiles(a.asset, a.sheet_id, a.dpi)
    return {"sheet_id": a.sheet_id, "tiles": [t["tile"] for t in tiles]}


def cmd_ocr(a):
    from .doc_ingest import ocr_locate
    return ocr_locate.locate(a.asset, a.sheet_id, a.fields.split(","))


def cmd_text_search(a):
    from .doc_ingest import ocr_locate
    return ocr_locate.text_search(a.asset, a.pattern)


def cmd_vector_radius(a):
    from .doc_ingest import vector_measure
    return vector_measure.ramp_radius(a.asset, a.file, a.page, a.scale)


def cmd_vector_lines(a):
    from .doc_ingest import vector_measure
    return vector_measure.lines_near(a.asset, a.file, a.page, a.at, a.radius, a.scale)


def cmd_vector_distance(a):
    from .doc_ingest import vector_measure
    return vector_measure.distance(a.asset, a.file, a.page, a.a, a.b, a.c, a.d, a.scale, a.name, a.snap)


def cmd_vector_depth_min(a):
    from .doc_ingest import vector_measure
    return vector_measure.depth_min(a.asset, a.file, a.page, a.a, getattr(a, "from"), a.to, a.b, a.scale, a.name, a.snap)


def cmd_vector_area_sum(a):
    from .doc_ingest import vector_measure
    return vector_measure.area_sum(a.asset, a.names)


def cmd_crop(a):
    from .doc_ingest import sheets
    p = sheets.crop_evidence(a.asset, a.file, a.page, [float(x) for x in a.bbox.split(",")], a.name)
    return {"crop": p}


def cmd_crop_all(a):
    from .doc_ingest import sheets
    return {"cropped": sheets.crop_all(a.asset)}


def cmd_validate(a):
    from .io import load_json, load_yaml
    from .paths import input_dir, wf2_dir
    from .spec.normalize import normalize_record
    from .spec.validate import validate_record
    meta = load_yaml(input_dir(a.asset) / "asset_meta.yaml")
    name = {"im": "w2_02_im_claims.json", "drawing": "w2_03_drawing_specs.json"}.get(a.which, a.which)
    rec = normalize_record(load_json(wf2_dir(a.asset) / name))
    return validate_record(rec, [b["id"] for b in meta["buildings"]])


def cmd_reconcile(a):
    from .spec import reconcile
    from . import session
    ci = reconcile.run(a.asset)
    session.transition(a.asset, "RECONCILED", f"확인 {ci['summary']['needs_review']} / 자동확정 {ci['summary']['auto_confirmed']}")
    return ci["summary"] | ({"sensitivity_error": ci["sensitivity_error"]} if ci.get("sensitivity_error") else {})


def cmd_apply_confirmation(a):
    from .spec import confirmation
    from . import session
    r = confirmation.run(a.asset)
    session.transition(a.asset, "PROFILED", "G2 반영")
    return r


def cmd_profile(a):
    from .spec import profile
    p = profile.run(a.asset)
    return {"buildings": [{"id": b["building_id"], "segment": b["segment"],
                           "missing_vars": len(b["missing"])} for b in p["buildings"]]}


def cmd_evaluate(a):
    from .engine import evaluate
    d = evaluate.run(a.asset)
    from collections import Counter
    c = Counter((r["status"], r["severity_base"]) for r in d["results"])
    return {"rules": d["rule_count"], "results": len(d["results"]), "breakdown": {f"{k[0]}:{k[1]}": v for k, v in c.items()}}


def cmd_merge_evaluation(a):
    from .engine import adjust
    from . import session
    r = adjust.run(a.asset)
    session.transition(a.asset, "EVALUATED")
    return r


def cmd_pairs(a):
    from .engine import report_data
    return report_data.precompute_pairs(a.asset)


def cmd_report_data(a):
    from .engine import report_data
    dash = report_data.compute_dashboard(a.asset)
    top = report_data.rank_top3(a.asset)
    report_data.build_data_request(a.asset)
    return {"dashboard": dash, "top3": top["top3"]}


def cmd_render_report(a):
    from .engine import report_render
    text = report_render.render(a.asset)
    return {"skeleton": f"output/wf2/{a.asset}/{a.asset}_report_skeleton.md", "llm_markers": text.count("<!-- LLM:")}


def cmd_validate_report(a):
    from .engine import report_data
    from . import session
    r = report_data.validate_report(a.asset)
    if r["ok"]:
        session.transition(a.asset, "REPORT_DRAFT")
    return r


def cmd_load_rules(a):
    from .engine.rules import load_rules
    r = load_rules()
    return {"count": r["count"], "errors": r["errors"], "ids": [x["id"] for x in r["rules"]]}


def cmd_status(a):
    from . import session
    return session.load(a.asset)


def cmd_transition(a):
    from . import session
    return session.transition(a.asset, a.state, a.note)


def cmd_review(a):
    from .review import server
    server.serve(a.port, open_browser=not a.no_browser)


def cmd_prepare_golden(a):
    from .golden import prepare
    return prepare(a.asset)


def cmd_golden_check(a):
    from .golden import check
    return check(a.asset, a.target)


def cmd_pca_compare(a):
    from .review.pca_compare import run
    return run(a.asset)


def cmd_finalize(a):
    from .review.finalize import finalize
    return finalize(a.asset)


def cmd_render_html(a):
    from .review.report_html import render
    return {"html": str(render(a.asset, final=not a.draft).name)}


def main(argv=None):
    p = argparse.ArgumentParser(prog="lprisk")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *extra):
        sp = sub.add_parser(name)
        if name not in ("load-rules", "review"):
            sp.add_argument("asset")
        for args, kw in extra:
            sp.add_argument(*args, **kw)
        sp.set_defaults(fn=fn)

    add("intake", cmd_intake)
    add("extract-im-text", cmd_extract_im_text)
    add("classify-sheets", cmd_classify_sheets)
    add("tiles", cmd_tiles, (("sheet_id",), {}), (("--dpi",), {"type": int, "default": 220}))
    add("ocr", cmd_ocr, (("sheet_id",), {}), (("--fields",), {"required": True}))
    add("crop", cmd_crop, (("--file",), {"required": True}), (("--page",), {"type": int, "required": True}),
        (("--bbox",), {"required": True}), (("--name",), {"required": True}))
    add("crop-all", cmd_crop_all)
    add("text-search", cmd_text_search, (("--pattern",), {"required": True, "help": "정규식"}))
    add("vector-radius", cmd_vector_radius, (("--file",), {"required": True}), (("--page",), {"type": int, "required": True}),
        (("--scale",), {"type": float, "default": None, "help": "mm/pt (축척 표기 자동 인식 실패 시)"}))
    add("vector-lines", cmd_vector_lines, (("--file",), {"required": True}), (("--page",), {"type": int, "required": True}),
        (("--at",), {"required": True, "help": "x,y (PDF 원본 pt)"}), (("--radius",), {"type": float, "default": 15.0}),
        (("--scale",), {"type": float, "default": None}))
    add("vector-distance", cmd_vector_distance, (("--file",), {"required": True}), (("--page",), {"type": int, "required": True}),
        (("--a",), {"required": True, "help": "x,y — 첫 번째 선 위의 점"}), (("--b",), {"required": True, "help": "x,y — 두 번째 선 위의 점"}),
        (("--c",), {"default": None}), (("--d",), {"default": None, "help": "c–d: 두 번째 거리(직각) → 면적"}),
        (("--scale",), {"type": float, "default": None}), (("--name",), {"required": True}),
        (("--snap",), {"type": float, "default": 6.0}))
    add("vector-depth-min", cmd_vector_depth_min, (("--file",), {"required": True}), (("--page",), {"type": int, "required": True}),
        (("--a",), {"required": True, "help": "x,y — 도크면(직선) 위의 점"}),
        (("--from",), {"required": True, "help": "x,y — 접안 구간 한쪽 끝(첫 구획 바깥 선)"}),
        (("--to",), {"required": True, "help": "x,y — 접안 구간 다른 끝"}),
        (("--b",), {"required": True, "help": "x,y[;x,y…] — 반대편 경계(연석·옹벽·주차 구획선) 위의 점. 경로가 여러 개면 ';'"}),
        (("--scale",), {"type": float, "default": None}), (("--name",), {"required": True}),
        (("--snap",), {"type": float, "default": 6.0}))
    add("vector-area-sum", cmd_vector_area_sum, (("--names",), {"required": True, "help": "vector-distance --name 목록(쉼표)"}))
    add("validate", cmd_validate, (("which",), {"help": "im | drawing | 파일명"}))
    add("reconcile", cmd_reconcile)
    add("apply-confirmation", cmd_apply_confirmation)
    add("profile", cmd_profile)
    add("evaluate", cmd_evaluate)
    add("merge-evaluation", cmd_merge_evaluation)
    add("pairs", cmd_pairs)
    add("report-data", cmd_report_data)
    add("render-report", cmd_render_report)
    add("validate-report", cmd_validate_report)
    add("load-rules", cmd_load_rules)
    add("status", cmd_status)
    add("transition", cmd_transition, (("state",), {}), (("--note",), {"default": None}))
    add("review", cmd_review, (("--port",), {"type": int, "default": 8765}), (("--no-browser",), {"action": "store_true"}))
    add("prepare-golden", cmd_prepare_golden)
    add("golden-check", cmd_golden_check, (("--target",), {"choices": ["im", "drawing", "confirmed"], "default": "im"}))
    add("pca-compare", cmd_pca_compare)
    add("finalize", cmd_finalize)
    add("render-html", cmd_render_html, (("--draft",), {"action": "store_true", "help": "초안 보고서(_final 아님)를 변환"}))

    a = p.parse_args(argv)
    try:
        out = a.fn(a)
        if out is not None:
            _print(out)
    except Exception as e:
        _print({"error": str(e), "trace": traceback.format_exc().splitlines()[-6:]})
        sys.exit(1)


if __name__ == "__main__":
    main()
