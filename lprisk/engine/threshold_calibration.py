"""임계값 확인표용 골든 사례 (설계서 §3.12-10 골든 샘플 활용).

골든 정답(실사 보고서로 확인한 스펙)으로 프로파일을 만들고,
- 임계값마다 두 자산의 실제 값과 현재 값 기준 발동 여부
- 초안 임계값을 '전부 확정했다고 가정'했을 때의 룰별 판정
을 계산한다. 화면 표시용이며 thresholds.yaml을 바꾸지 않는다.
"""
from __future__ import annotations

import copy

from ..io import load_json, load_yaml
from ..paths import TESTS
from ..spec.normalize import normalize_record
from ..spec.profile import build_profile, load_regulations
from . import evaluate as ev_mod
from .rules import load_rules
from .thresholds import ThresholdResolver, load_thresholds

SHORT_NAMES = {"cheongna": "청라", "seoknam": "석남", "icheon": "이천", "songon": "송온2", "songon1": "송온1", "hyeonbang": "현방",
               "bukhang": "북항"}


def golden_assets() -> dict[str, str]:
    """tests/golden/*/golden_spec.json 이 있는 자산 → 짧은 이름."""
    out = {}
    for d in sorted((TESTS / "golden").glob("*/golden_spec.json")):
        a = d.parent.name
        if not (d.parent / "asset_meta.yaml").exists():      # 작성 중인 골든은 건너뜀
            continue
        meta = load_yaml(d.parent / "asset_meta.yaml")
        out[a] = SHORT_NAMES.get(a, meta.get("asset_name", a))
    return out

# 임계값 그룹 → (비교 변수, 방향, 표시 이름). 방향: lower = 값이 임계보다 낮으면 발동
GROUP_VAR = {
    "floor_load": ("warehouse_floors.floor_load_tpm2.min", "lower", "창고층 최소 설계하중"),
    "clear_height": ("warehouse_floors.clear_height_m.min", "lower", "창고층 최소 유효층고"),
    "column_span": ("column_span_min", "lower", "기둥 스팬(짧은 쪽)"),
    "dock_density": ("dock_density", "lower", "연면적 1만평당 도크 수"),
    "ramp_slope": ("ramp_slope_pct", "higher", "램프 경사"),
    "ramp_width": ("ramp_width_m", "lower", "램프 폭"),
    "truck_yard_depth": ("truck_yard_depth_m", "lower", "트럭야드 깊이"),
    "turning_radius": ("turning_radius_m", "lower", "대형차 최소 회전반경"),
    "fire_compartment_area": ("fire_compartment_max_m2", "higher", "방화구획 최대 면적"),
    "warehouse_depth": ("warehouse_depth_m", "higher", "창고 내부 깊이"),
    "sprinkler_esfr_clear_height": ("warehouse_floors.clear_height_m.max", "higher", "창고층 최대 유효층고"),
    "flood_depth": ("flood_depth_m", "higher", "예상 침수심"),
    "cold_fire": ("cold_ratio", "higher", "저온 비율"),
    "v02_unconfirmed_ratio": (None, "higher", "핵심 스펙 미확인 비율"),
}
AGE_GROUPS = ("aging_", "cold_refrigeration_age", "cold_insulation_age")


def _var_for(group: str, level: str):
    if group == "aging_generator" and level == "gfa":
        return "gross_floor_area_m2", "higher_eq", "연면적"
    if group.startswith(AGE_GROUPS):
        return "building_age", "higher_eq", "건물 연식(현재)"   # 연식 룰은 '이상'으로 발동
    return GROUP_VAR.get(group, (None, "higher", group))


def golden_profiles() -> dict:
    out = {}
    regs = load_regulations()
    for a, name in golden_assets().items():
        g = TESTS / "golden" / a
        if not (g / "golden_spec.json").exists():
            continue
        rec = normalize_record(load_json(g / "golden_spec.json"))
        meta = load_yaml(g / "asset_meta.yaml")
        prof = build_profile(rec, meta, {"asset": {}}, regs=regs)
        for b in prof["buildings"]:
            v = b["vars"]
            xs = [x for x in (v.get("column_span_x_m"), v.get("column_span_y_m")) if x is not None]
            v["column_span_min"] = min(xs) if xs else None
            b["grades"]["column_span_min"] = "verified" if xs else None
        out[a] = {"name": name, "profile": prof, "meta": meta}
    return out


def load_findings() -> dict[str, dict]:
    """tests/golden/{a}/findings.yaml + incidents.yaml → {asset: {rule_id: [{text, page, severity_hint, source?}]}}

    incidents.yaml(운영 중 사고 이력)는 룰별로 펼쳐 `source: '사고 YYYY-MM-DD'`를 달아 붙인다.
    """
    out = {}
    for a in golden_assets():
        p = TESTS / "golden" / a / "findings.yaml"
        fnd = {k: list(v or []) for k, v in (((load_yaml(p) or {}).get("findings") or {}) if p.exists() else {}).items()}
        ip = TESTS / "golden" / a / "incidents.yaml"
        for inc in ((load_yaml(ip) or {}).get("incidents") or []) if ip.exists() else []:
            entry = {"text": f"{inc.get('category', '')}: {inc.get('cause', '')}", "page": None,
                     "severity_hint": inc.get("severity_hint"), "source": f"{inc.get('type') or '사고'} {inc.get('date')}",
                     "dd_flagged": inc.get("dd_flagged")}
            for rid in inc.get("rules") or []:
                fnd.setdefault(rid, []).append(entry)
        out[a] = fnd
    return out


def mismatch(severity: str | None, findings: list[dict]) -> str | None:
    """엔진 판정과 실사 소견이 어긋나는지 (보정 신호)."""
    hints = {f.get("severity_hint") for f in findings or []}
    if severity == "green" and "결함" in hints:
        where = {"사후 이력" if f.get("source") else "실사" for f in findings if f.get("severity_hint") == "결함"}
        return "판정이 낮을 수 있음 — " + "·".join(sorted(where, reverse=True)) + "에서 결함"
    if severity in ("red", "yellow") and hints and hints <= {"양호"}:
        return "판정이 높을 수 있음 — 실사에서 양호"
    return None


def _bname(g: dict, b: dict) -> str:
    """동이 하나면 자산 이름, 여럿이면 '이천 A동'처럼."""
    if len(g["profile"]["buildings"]) == 1:
        return g["name"]
    return f"{g['name']} {b.get('label') or b['building_id']}"


def columns(gp: dict) -> list[tuple[str, str]]:
    return [(f"{a}|{b['building_id']}", _bname(g, b)) for a, g in gp.items() for b in g["profile"]["buildings"]]


def examples(group: str, level: str, gp: dict) -> list[dict]:
    var, direction, label = _var_for(group, level)
    rows = []
    for a, g in gp.items():
        for b in g["profile"]["buildings"]:
            val = b["vars"].get(var) if var else None
            extra = ""
            if group.startswith("cold_") and b["vars"].get("has_cold") is False:
                extra = "저온동 없음 — 룰 미적용"
            if group == "sprinkler_esfr_clear_height":
                extra = f"스프링클러 {b['vars'].get('sprinkler_type') or '미확인'}"
            rows.append({"asset": a, "name": _bname(g, b), "var_label": label, "value": val, "direction": direction,
                         "extra": extra, "segment": b["segment"]})
    return rows


def simulate(gp: dict) -> dict:
    """초안 임계값·법규를 전부 확정했다고 가정한 룰별 판정."""
    table = copy.deepcopy(load_thresholds())
    for g in table.values():
        for blk in [g.get("default") or {}] + list(g.get("overrides") or []):
            for k, e in blk.items():
                if isinstance(e, dict) and "value" in e:
                    e["verified"] = True
    regs = [dict(r, verified=True) for r in load_regulations()]
    rules = [r for r in load_rules()["rules"] if r["category"] not in ("consistency", "benchmark")]
    orig = ev_mod.ThresholdResolver
    ev_mod.ThresholdResolver = lambda seg: ThresholdResolver(seg, table)
    try:
        res = {}
        for a, g in gp.items():
            rec = normalize_record(load_json(TESTS / "golden" / a / "golden_spec.json"))
            prof = build_profile(rec, g["meta"], {"asset": {}}, regs=regs)
            for r in ev_mod.evaluate_profile(prof, rules, single=False):   # 등급별 기준값 보정이라 원 등급 유지
                n = r.get("now") or r.get("exit")
                res.setdefault(r["rule_id"], {"title": r["title"]})[f"{a}|{r['building_id']}"] = {
                    "severity": r["severity_base"], "reason": n.get("hold_reason"),
                    "missing": [m.split("|")[-1] if "|" in m else m for m in (n.get("missing_inputs") or [])][:3]}
    finally:
        ev_mod.ThresholdResolver = orig
    fnd = load_findings()
    for rid, row in res.items():
        for key, cell in row.items():
            if key == "title":
                continue
            a = key.split("|")[0]
            cell["findings"] = fnd.get(a, {}).get(rid, [])
            cell["mismatch"] = mismatch(cell["severity"], cell["findings"])
    return res
