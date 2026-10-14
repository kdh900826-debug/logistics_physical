"""W2-⑨⑩ 스크립트 영역: 활성 쌍 선계산, 대시보드, Top 3, 추가 자료 요청 목록, 보고서 검증.

(설계서 §3.5 precompute_pairs / compute_dashboard / rank_top3 / build_data_request / validate_report)
"""
from __future__ import annotations

import re
from collections import Counter

import yaml

from ..io import load_json, load_yaml, now_iso, save_json, save_text
from ..paths import ENGINE_REFS, input_dir, wf2_dir
from ..schema import Slot, field_def
from .rules import EMOJI

ACTIVE = {"red", "yellow"}


def _active(results):
    return [r for r in results if r["status"] == "triggered" and r["severity_final"] in ACTIVE]


# ── 상관관계 쌍 ─────────────────────────────────────────
def load_correlation_map() -> list[dict]:
    text = (ENGINE_REFS / "correlation_map.md").read_text(encoding="utf-8")
    m = re.search(r"```yaml\s*\n(.*?)```", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}).get("relations", []) if m else []


def precompute_pairs(asset_id: str) -> dict:
    ev = load_json(wf2_dir(asset_id) / "w2_08_risk_evaluation.json")
    act = _active(ev["results"])
    by_rule: dict[str, list] = {}
    for r in act:
        by_rule.setdefault(r["rule_id"], []).append(r["building_id"])
    pairs = []
    for rel in load_correlation_map():
        members = rel["rules"]
        if all(m in by_rule for m in members):
            # 동 내 결합: 모든 멤버가 같은 동에서 활성 (자산 단위 룰은 어느 동과도 결합)
            bsets = [set(by_rule[m]) for m in members]
            per_bld = [b for b in set().union(*bsets) if b is not None and all(b in s or None in s for s in bsets)]
            pairs.append({"relation_id": rel["id"], "rules": members, "converges_to": rel.get("converges_to"),
                          "description": rel.get("description"), "buildings": sorted(per_bld) or ["(동 간)"]})
    data = {"asset_id": asset_id, "created_at": now_iso(), "pairs": pairs}
    save_json(wf2_dir(asset_id) / "w2_09_pairs.json", data)
    return data


# ── 대시보드 ────────────────────────────────────────────
def compute_dashboard(asset_id: str) -> dict:
    out = wf2_dir(asset_id)
    ev = load_json(out / "w2_08_risk_evaluation.json")
    conf = load_json(out / "w2_05_confirmed_spec.json")
    rec = load_json(out / "w2_04_reconciled.json")
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    res = ev["results"]
    trig_or_hold = [r for r in res if r["status"] in ("triggered", "hold")]

    def count(rows, key="severity_final"):
        c = Counter(r[key] for r in rows)
        return {k: c.get(k, 0) for k in ("red", "yellow", "green", "hold")}

    verified = [r for r in trig_or_hold if r["now"]["input_grade"] == "verified" if "now" in r] if trig_or_hold else []
    claimed = [r for r in trig_or_hold if r.get("now", {}).get("input_grade") == "claimed"]
    exit_up = [r for r in res if r.get("severity_exit") and r["severity_exit"] != r["severity_base"]
               and _rank(r["severity_exit"]) > _rank(r["severity_base"])]

    statuses = Counter()
    for b in conf["buildings"]:
        for _, vs in _iter(b):
            statuses[vs[0].get("status")] += 1
    for _, vs in (conf.get("asset") or {}).items():
        statuses[vs[0].get("status")] += 1
    dirs = Counter(e.get("direction") for e in rec["entries"] if e["state"] == "불일치")
    v01 = (ev.get("consistency") or {}).get("v01_items") or []
    dash = {
        "asset_id": asset_id, "asset_name": meta.get("asset_name"), "created_at": now_iso(),
        "mode": "정규" if (out / "w2_03_drawing_specs.json").exists() else "IM 단독",
        "rule_count": ev["rule_count"], "evaluated": len(res),
        "severity": count(trig_or_hold),
        "severity_verified": count(verified), "severity_claimed": count(claimed),
        "not_triggered": sum(1 for r in res if r["status"] == "not_triggered"),
        "exit_escalations": [{"rule_id": r["rule_id"], "building_id": r["building_id"],
                              "now": r["severity_base"], "exit": r["severity_exit"]} for r in exit_up],
        "spec_status": dict(statuses),
        "reconcile_mismatch": {"total": sum(dirs.values()), "overstated": dirs.get("overstated", 0),
                               "conservative": dirs.get("conservative", 0), "neutral": dirs.get("neutral", 0)},
        "v01_overstated": sum(1 for i in v01 if i["direction"] == "overstated"),
        "rejected_adjustments": len(ev.get("rejected_adjustments") or []),
        "holding_years": meta.get("holding_years"),
        "vector_rules": [{"rule_id": r["rule_id"], "building_id": r["building_id"], "severity": r["severity_final"],
                          "inputs": _vector_inputs(r)} for r in trig_or_hold if _vector_inputs(r)],
    }
    save_json(out / "w2_10_dashboard.json", dash)
    return dash


def _iter(b):
    for f, vs in (b.get("fields") or {}).items():
        if field_def(f)["type"] != "list":
            yield f, vs
    for fl in b.get("floors") or []:
        for f, vs in (fl.get("fields") or {}).items():
            yield f, vs


def _vector_inputs(r) -> list[str]:
    return sorted({s for h in ("now", "exit") if r.get(h) for s in r[h].get("vector_inputs") or []})


def _rank(sev):
    return {"green": 0, "yellow": 1, "red": 2}.get(sev, -1)


# ── Top 3 ───────────────────────────────────────────────
def rank_top3(asset_id: str) -> dict:
    out = wf2_dir(asset_id)
    ev = load_json(out / "w2_08_risk_evaluation.json")
    pairs = load_json(out / "w2_09_pairs.json")["pairs"] if (out / "w2_09_pairs.json").exists() else []
    cfg = load_yaml(ENGINE_REFS / "report_config.yaml")
    prio = cfg["category_priority"]
    v01_slots = {i["slot"].split("|")[-1] for i in ((ev.get("consistency") or {}).get("v01_items") or [])}
    links = Counter(rid for p in pairs for rid in p["rules"])

    def v01_related(r):
        return any(any(f in p for f in v01_slots) for p in (r.get("now") or {}).get("facts", {}))

    cands = _active(ev["results"])
    keyed = sorted(cands, key=lambda r: (-_rank(r["severity_final"]), not v01_related(r), -links.get(r["rule_id"], 0),
                                         prio.index(r["category"]) if r["category"] in prio else 99,
                                         r["rule_id"], r["building_id"] or ""))
    top = [{"rank": i + 1, "rule_id": r["rule_id"], "building_id": r["building_id"], "title": r["title"],
            "severity": r["severity_final"], "v01_related": v01_related(r), "links": links.get(r["rule_id"], 0),
            "category": r["category"], "vector_inputs": _vector_inputs(r)} for i, r in enumerate(keyed[:3])]
    data = {"asset_id": asset_id, "sort_keys": ["severity", "v01_related", "correlation_links", "category_priority", "rule_id"],
            "top3": top}
    save_json(out / "w2_10_top3.json", data)
    return data


# ── 추가 자료 요청 목록 ─────────────────────────────────
REQUEST_TEXT = {
    "도면없음": "해당 도면 제공 요청",
    "미기재": "현장 실사·PCA에서 확인 필요 (도면에 기재 없음)",
    "판독불가": "고해상도 스캔 또는 원본(벡터 PDF) 재요청",
    None: "자료 요청 또는 현장 확인 필요",
}


def build_data_request(asset_id: str) -> str:
    out = wf2_dir(asset_id)
    ev = load_json(out / "w2_08_risk_evaluation.json")
    conf = load_json(out / "w2_05_confirmed_spec.json")
    inv = load_json(out / "w2_01_inventory.json")
    meta = load_yaml(input_dir(asset_id) / "asset_meta.yaml")
    miss_by_slot = {Slot(m["level"], m.get("building_id"), m.get("floor"), m["field"]).key: m for m in conf.get("missing") or []}
    impact: dict[str, set] = {}
    for r in ev["results"]:
        if r["severity_final"] == "hold":
            for p in (r.get("now") or r.get("exit") or {}).get("missing_inputs") or []:
                impact.setdefault(p, set()).add(r["rule_id"])
    rows = []
    for slot_key, rules in sorted(impact.items()):
        if "|" not in slot_key:
            reason, what = None, slot_key
        else:
            s = Slot.from_key(slot_key)
            m = miss_by_slot.get(slot_key) or {}
            reason = m.get("missing_reason")
            what = s.label()
            dtypes = ", ".join(m.get("searched") or field_def(s.field).get("drawing_types") or [])
            what += f" — 관련 도면: {dtypes}" if dtypes else ""
        rows.append((reason, what, sorted(rules)))
    lines = [f"# 추가 자료 요청 목록 — {meta.get('asset_name', asset_id)}", "",
             f"> 생성: {now_iso()} · 판정 보류(⚪) 룰의 미확인 입력 기준", "",
             "| 구분 | 요청 자료 / 확인 항목 | 필요 사유 | 영향 룰 |", "|---|---|---|---|"]
    for reason, what, rules in sorted(rows, key=lambda x: (str(x[0]), x[1])):
        lines.append(f"| {reason or '미확인'} | {what} | {REQUEST_TEXT.get(reason, REQUEST_TEXT[None])} | {', '.join(rules)} |")
    for d in inv.get("dwg_requests") or []:
        lines.append(f"| 형식 | {d['file']} | DWG는 처리하지 않음 — {d['request']} | — |")
    text = "\n".join(lines) + "\n"
    save_text(out / f"{asset_id}_data_request.md", text)
    return text


# ── 보고서 검증 ─────────────────────────────────────────
REQUIRED_SECTIONS = ["## 0. 요약 대시보드", "## 1. 자산 프로파일", "## 2. 스펙 경쟁력", "## 3. IM–도면 정합성",
                     "## 4. 입지 리스크", "## 5. 리스크 평가 결과", "## 6. 리스크 상관관계", "## 7. DD 체크리스트",
                     "## 부록 A", "## 부록 B", "## 갱신 이력"]


def validate_report(asset_id: str) -> dict:
    out = wf2_dir(asset_id)
    draft = out / f"{asset_id}_logistics_risk_report.md"      # 초안 우선 (_final·백업 파일이 같은 패턴에 걸림)
    path = draft if draft.exists() else next(out.glob(f"{asset_id}_logistics_risk_report*.md"), None)
    errs = []
    if path is None:
        return {"ok": False, "errors": ["보고서 파일 없음"]}
    text = path.read_text(encoding="utf-8")
    left = re.findall(r"<!-- LLM:([^ ]+) -->", text)
    if left:
        errs.append(f"채워지지 않은 서술 표식 {len(left)}개: {left[:8]}")
    for s in REQUIRED_SECTIONS:
        if s not in text:
            errs.append(f"필수 섹션 누락: {s}")
    dash = load_json(out / "w2_10_dashboard.json")
    ev = load_json(out / "w2_08_risk_evaluation.json")
    sec5 = text.split("## 5. 리스크 평가 결과", 1)[-1].split("## 6.", 1)[0]
    cards = re.findall(r"^###\s+(🔴|🟡|🟢|⚪)\s+([A-Z]+[0-9]+)", sec5, re.M)
    c = Counter(e for e, _ in cards)
    for sev, emo in (("red", "🔴"), ("yellow", "🟡"), ("green", "🟢"), ("hold", "⚪")):
        if c.get(emo, 0) != dash["severity"][sev]:
            errs.append(f"§5 {emo} 카드 수 {c.get(emo, 0)} ≠ 대시보드 {dash['severity'][sev]}")
    top = load_json(out / "w2_10_top3.json")["top3"]
    sec0 = text.split("## 0. 요약 대시보드", 1)[-1].split("## 1.", 1)[0]
    for t in top:
        if t["rule_id"] not in sec0:
            errs.append(f"Top 3 {t['rule_id']}가 §0에 없음")
    # 보고서의 숫자가 스크립트 산출물에 존재하는지 (서술 수치 생성 금지 §1.8-1)
    known = _known_numbers(out)
    plain = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text)    # 렌더러 천 단위 쉼표(_fmt) 제거
    stray = sorted({n for n in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])", plain)
                    if _num(n) not in known and len(n.replace(".", "")) >= 2})
    if stray:
        errs.append(f"스크립트 산출물에 없는 수치 {len(stray)}개: {stray[:15]}")
    return {"ok": not errs, "errors": errs, "report": path.name}


def _num(s):
    try:
        f = float(s)
        return round(f, 4)
    except ValueError:
        return None


def _known_numbers(out) -> set:
    nums = set()
    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            nums.add(round(float(x), 4))
            nums.add(round(float(x), 3))     # report_render._fmt 반올림 표기
        elif isinstance(x, str):
            for n in re.findall(r"\d+(?:\.\d+)?", re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", x)):
                nums.add(round(float(n), 4))
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(k); walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    for name in ("w2_01_inventory.json", "w2_02_im_claims.json", "w2_03_drawing_specs.json", "w2_04_reconciled.json",
                 "w2_05_confirmed_spec.json", "w2_06_profile.json", "w2_07_benchmark_position.json",
                 "w2_08_risk_evaluation.json", "w2_09_correlations.json", "w2_09_pairs.json", "w2_10_dashboard.json",
                 "w2_10_top3.json", "w2_01b_location.json", "session_state.json"):
        p = out / name
        if p.exists():
            walk(load_json(p))
    for i in range(0, 13):          # 섹션 번호·순위 등 구조용 작은 정수
        nums.add(float(i))
    return nums
