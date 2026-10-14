"""골든 샘플 준비·채점 (설계서 §3.12-10).

골든 = 실사(PCA/DD) 보고서로 확인한 정답 스펙(golden_spec.json) + IM 기재값 정답(golden_im_claims.json).
원본 도면 세트가 없으므로 실사 보고서에 수록된 도면 페이지를 '스캔 도면' 입력으로 쓴다.
"""
from __future__ import annotations

import shutil

import fitz

from .io import load_json, load_yaml, now_iso, save_json, save_text
from .paths import ROOT, TESTS, input_dir, wf2_dir
from .schema import ASSET_BUILDING, Slot, evaluated_building_ids, field_def, iter_slots
from .spec.normalize import normalize_record
from .spec.reconcile import matches


def golden_dir(asset_id: str):
    return TESTS / "golden" / asset_id


def prepare(asset_id: str) -> dict:
    g = golden_dir(asset_id)
    inp = input_dir(asset_id)
    (inp / "drawings").mkdir(parents=True, exist_ok=True)
    meta_dst = inp / "asset_meta.yaml"
    if not meta_dst.exists():
        shutil.copy(g / "asset_meta.yaml", meta_dst)
    dp = load_yaml(g / "drawing_pages.yaml")
    src = ROOT / dp["source_doc"]
    pages = sorted({d["page"] for d in (dp.get("drawings") or dp.get("pages") or [])})
    out_pdf = inp / "drawings" / f"{asset_id}_실사보고서_수록도면.pdf"
    doc = fitz.open(src)
    new = fitz.open()
    for p in pages:
        new.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
    new.save(out_pdf)
    # 추적용: 입력 PDF 페이지 → 원본 보고서 페이지 (drawing-extractor에는 주지 않음)
    save_json(g / "drawing_page_map.json", {"input_pdf": out_pdf.name, "source_doc": dp["source_doc"],
                                            "map": {i + 1: p for i, p in enumerate(pages)}})
    return {"asset_meta": str(meta_dst.relative_to(ROOT)), "drawings_pdf": str(out_pdf.relative_to(ROOT)),
            "pages": len(pages)}


def _slots(rec: dict, bids: list[str]) -> dict[Slot, list]:
    out = {}
    for s, vs in iter_slots(rec):
        if field_def(s.field)["type"] == "list":
            continue
        targets = bids if s.building_id == ASSET_BUILDING else [s.building_id]
        for b in targets:
            key = Slot(s.level, b if s.level != "asset" else None, s.floor, s.field)
            out.setdefault(key, []).extend(v for v in vs if v.get("value") is not None)
    return out


def check(asset_id: str, target: str = "im") -> dict:
    g = golden_dir(asset_id)
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    bids = evaluated_building_ids(meta)
    gold_name, out_name = {"im": ("golden_im_claims.json", "w2_02_im_claims.json"),
                           "drawing": ("golden_spec.json", "w2_03_drawing_specs.json"),
                           "confirmed": ("golden_spec.json", "w2_05_confirmed_spec.json")}[target]
    gold = _slots(normalize_record(load_json(g / gold_name)), bids)
    got = _slots(normalize_record(load_json(wf2_dir(asset_id) / out_name)), bids)
    if target == "drawing":
        # 도면 채점은 도면에서 읽을 수 있는 필드만 대상으로 한다 (스키마 drawing_types 보유 필드)
        gold = {s: v for s, v in gold.items() if field_def(s.field).get("drawing_types")}
    rows, correct, wrong, missed = [], 0, 0, 0
    for s, gv in sorted(gold.items(), key=lambda x: x[0].key):
        if not gv:
            continue
        ov = got.get(s) or []
        gold_v = dict(gv[0], precision=gv[0].get("precision") or "exact")
        if not ov:
            missed += 1
            rows.append({"slot": s.key, "gold": gold_v["value"], "got": None, "result": "누락"})
            continue
        golds = [gold_v] + [dict(gold_v, value=a, precision="exact") for a in gold_v.get("accept_also") or []]
        ok = any(matches(s.field, gv_, o) or matches(s.field, dict(o, precision=o.get("precision") or "exact"), gv_)
                 for gv_ in golds for o in ov)
        correct += ok
        wrong += (not ok)
        rows.append({"slot": s.key, "gold": gold_v["value"], "got": [o["value"] for o in ov],
                     "result": "정답" if ok else "오답"})
    extra = sorted(s.key for s in got if s not in gold)
    n = len([r for r in rows])
    summary = {"asset_id": asset_id, "target": target, "checked_at": now_iso(), "gold_slots": n,
               "correct": correct, "wrong": wrong, "missed": missed, "extra_slots": len(extra)}
    save_json(wf2_dir(asset_id) / f"golden_check_{target}.json", {"summary": summary, "rows": rows, "extra": extra})
    lines = [f"# 골든 채점 — {asset_id} / {target}", "",
             f"정답 {correct} · 오답 {wrong} · 누락 {missed} (골든 슬롯 {n}) · 골든에 없는 추출 {len(extra)}", "",
             "| 슬롯 | 정답 | 추출 | 결과 |", "|---|---|---|---|"]
    lines += [f"| {r['slot']} | {r['gold']} | {r['got']} | {r['result']} |" for r in rows if r["result"] != "정답"]
    save_text(wf2_dir(asset_id) / f"golden_check_{target}.md", "\n".join(lines) + "\n")
    return summary
