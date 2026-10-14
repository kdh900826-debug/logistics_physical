"""임계값·법규 시행일 확인표 (설계서 §3.7, §4.1 U1·U2).

리뷰 서버 `/thresholds` 화면의 데이터를 만들고, 사용자 결정을 YAML에 반영한다.
반영은 ruamel.yaml 왕복(round-trip)으로 해서 주석·순서를 보존한다.
확정한 항목에는 verified: true, verified_by: user, verified_at을 남긴다.
"""
from __future__ import annotations

import re
from collections import defaultdict

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from ..io import load_yaml, now_iso, save_json
from ..paths import ENGINE_REFS, KB, RULES_DIR, SCHEMA_REFS

TH_PATH = ENGINE_REFS / "thresholds.yaml"
REG_PATH = ENGINE_REFS / "regulation_timeline.yaml"
PROFILE_PATH = SCHEMA_REFS / "profile_config.yaml"

LEVEL_KO = {"red": "🔴", "yellow": "🟡", "gfa": "적용 연면적", "cold_ratio_red": "🔴 저온 비율"}
GROUP_KO = {
    "floor_load": ("바닥 설계하중", "t/㎡"), "clear_height": ("유효층고(천정·보·배관 하단)", "m"), "column_span": ("기둥 스팬", "m"),
    "dock_density": ("연면적 1만평당 도크 수", "대/1만평"), "ramp_slope": ("램프 경사", "%"), "ramp_width": ("램프 폭", "m"),
    "truck_yard_depth": ("트럭야드 깊이", "m"), "turning_radius": ("대형차 최소 회전반경", "m"),
    "fire_compartment_area": ("방화구획 최대 면적", "㎡"),
    "sprinkler_esfr_clear_height": ("천장형 스프링클러 한계 천장고", "m"), "cold_fire": ("저온동 단열재 화재", "비율"),
    "warehouse_depth": ("창고 내부 깊이(소방대 진입 거리)", "m"),
    "flood_depth": ("홍수 예상 침수심", "m"), "v02_unconfirmed_ratio": ("핵심 스펙 미확인 비율", "비율"),
    "aging_piping": ("배관 노후", "년"), "aging_substation": ("수변전설비 노후", "년"), "aging_elevator": ("승강기 노후", "년"),
    "aging_generator": ("비상발전기", "년 / ㎡"), "aging_fire_system": ("소화설비 노후", "년"), "aging_roof": ("지붕 방수", "년"),
    "aging_pavement": ("야드·램프 포장", "년"), "aging_compliance": ("법규 적합성", "년"), "aging_capex": ("CapEx 종합", "년"),
    "cold_refrigeration_age": ("냉동설비 연식", "년"), "cold_insulation_age": ("저온 단열 패널 연식", "년"),
}
POLICY_GROUPS = {"v02_unconfirmed_ratio"}
# unresolved 기록의 옛 키 이름 → 현재 그룹
ALIASES = {"aging_pavement": ["yard_pavement_age"], "aging_generator": ["backup_generator_gfa"]}   # 외부 출처가 있을 수 없는 내부 정책값


def _yaml():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def rule_usage() -> dict[str, list[str]]:
    """'group.level' → 그 임계값을 쓰는 룰 ID 목록."""
    use = defaultdict(set)
    for p in RULES_DIR.glob("rules_*.md"):
        rid = None
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^id:\s*(\w+)", line)
            if m:
                rid = m.group(1)
            for k in re.findall(r"th\.([a-z_0-9]+\.[a-z_]+)", line):
                use[k].add(rid)
    return {k: sorted(v) for k, v in use.items()}


def _direction(g: dict) -> str:
    return {"lower_is_worse": "값이 이보다 낮으면 발동", "higher_is_worse": "값이 이보다 높으면 발동"}.get(g.get("direction"), "")


def build_items() -> dict:
    th = load_yaml(TH_PATH) or {}
    regs = load_yaml(REG_PATH) or {}
    usage = rule_usage()
    unresolved = {u["key"]: u for u in th.get("unresolved") or []}
    items, present = [], set()
    for group, g in th.items():
        if not isinstance(g, dict) or not ("default" in g or "overrides" in g):
            continue
        name, unit = GROUP_KO.get(group, (group, g.get("unit", "")))
        blocks = [("기본", "default", None, g.get("default") or {})]
        blocks += [(", ".join(f"{k}={v}" for k, v in (ov.get("when") or {}).items()), "override", i, ov)
                   for i, ov in enumerate(g.get("overrides") or [])]
        for scope_label, scope, idx, block in blocks:
            for level, e in block.items():
                if level == "when" or not isinstance(e, dict):
                    continue
                key = f"{group}.{level}"
                present.add(key) if scope == "default" else None
                items.append({
                    "id": f"th:{group}:{scope}:{idx if idx is not None else ''}:{level}", "kind": "threshold",
                    "group": group, "name": name, "unit": unit, "level": level, "level_label": LEVEL_KO.get(level, level),
                    "scope": scope_label, "value": e.get("value"), "source": e.get("source"), "note": e.get("note"),
                    "verified": bool(e.get("verified")), "direction": _direction(g),
                    "rules": usage.get(key, []), "policy": group in POLICY_GROUPS,
                })
    missing = []
    for key, rules in sorted(usage.items()):
        if key in present:
            continue
        group, level = key.split(".", 1)
        name, unit = GROUP_KO.get(group, (group, ""))
        aliases = {group, *ALIASES.get(group, [])}
        hint = next((u for k, u in unresolved.items() if k.split(".")[0].split(" ")[0] in aliases), None)
        # 같은 그룹에 다른 등급이 이미 있으면 이 등급은 선택 사항(없으면 그 등급만 건너뜀)
        optional = any(k.startswith(group + ".") for k in present)
        missing.append({"id": f"missing:{key}", "kind": "missing", "group": group, "name": name, "unit": unit,
                        "optional": optional,
                        "level": level, "level_label": LEVEL_KO.get(level, level), "rules": rules,
                        "policy": group in POLICY_GROUPS,
                        "searched": (hint or {}).get("searched"), "finding": (hint or {}).get("finding")})
    reg_items = [{"id": f"reg:{r['id']}", "kind": "regulation", **{k: r.get(k) for k in
                  ("title", "law", "effective_date", "effective_date_basis", "applies_to", "summary", "source_url", "rule_refs")},
                  "reg_id": r["id"], "verified": bool(r.get("verified"))} for r in regs.get("regulations") or []]
    prof = load_yaml(PROFILE_PATH)
    policy = [{"id": "profile:temp_zone_classification", "kind": "profile", "name": "온도대 분류 (저온·냉동 면적 비율)",
               "values": prof["temp_zone_classification"],
               "note": "cold_ratio < ambient_max → 상온, ≥ cold_min → 저온, 그 사이 복합. Claude 임시값 — 시장 정의 없음",
               "verified": bool(prof.get("temp_zone_classification_verified"))}]
    # 골든 사례: 두 자산의 실제 값과 '초안 전부 확정' 가정 판정
    from .threshold_calibration import columns, examples, golden_profiles, simulate
    gp = golden_profiles()
    for it in items + missing:
        it["examples"] = examples(it["group"], it["level"], gp)
    try:
        sim = simulate(gp)
    except Exception as e:      # 화면은 계속 보여준다
        sim = {"_error": str(e)}
    return {"thresholds": items, "missing": missing, "regulations": reg_items, "policy": policy,
            "unresolved_regulations": regs.get("unresolved") or [], "simulation": sim,
            "golden_assets": dict(columns(gp))}


def _num(v):
    if v in (None, ""):
        return None
    try:
        f = float(str(v).replace(",", ""))
        return int(f) if f.is_integer() else f
    except ValueError:
        raise ValueError(f"숫자가 아닌 값: {v}")


def apply(decisions: dict) -> dict:
    """decisions = {"<item id>": {"action": "verify"|"edit"|"hold"|"set", "value":..., "source":..., "comment":...}}"""
    y = _yaml()
    th = y.load(TH_PATH.read_text(encoding="utf-8"))
    regs = y.load(REG_PATH.read_text(encoding="utf-8"))
    stamp = now_iso()
    changed = []
    for iid, d in decisions.items():
        act = d.get("action")
        if act in (None, "", "hold"):
            continue
        kind = iid.split(":", 1)[0]
        if kind == "th":
            _, group, scope, idx, level = iid.split(":")
            block = th[group]["default"] if scope == "default" else th[group]["overrides"][int(idx)]
            e = block[level]
            if act == "edit":
                old = e.get("value")
                e["value"] = _num(d.get("value"))
                if d.get("source"):
                    e["source"] = d["source"]
                e["note"] = f"{e.get('note') or ''} / {stamp[:10]} 사용자 수정: {old} → {e['value']}. {d.get('comment') or ''}".strip(" /")
            e["verified"] = True
            e["verified_by"] = "user"
            e["verified_at"] = stamp
            if d.get("comment") and act == "verify":
                e["note"] = f"{e.get('note') or ''} / 확인 메모: {d['comment']}".strip(" /")
            changed.append(iid)
        elif kind == "missing" and act == "set":
            key = iid.split(":", 1)[1]
            group, level = key.split(".", 1)
            val = _num(d.get("value"))
            if val is None or not d.get("source"):
                raise ValueError(f"{key}: 값과 출처(또는 '내부 정책' 근거)를 모두 입력하세요")
            g = th.get(group)
            if g is None:
                g = CommentedMap([("default", CommentedMap()), ("overrides", [])])
                th.insert(len([k for k in th if k != "unresolved"]), group, g)
            g.setdefault("default", CommentedMap())
            g["default"][level] = CommentedMap([("value", val), ("source", d["source"]), ("verified", True),
                                                ("verified_by", "user"), ("verified_at", stamp)])
            if d.get("comment"):
                g["default"][level]["note"] = d["comment"]
            changed.append(iid)
        elif kind == "reg":
            rid = iid.split(":", 1)[1]
            r = next(x for x in regs["regulations"] if x["id"] == rid)
            if act == "edit" and d.get("value"):
                r["effective_date"] = str(d["value"])
            if d.get("source"):
                r["source_url"] = d["source"]
            r["verified"] = True
            r["verified_by"] = "user"
            r["verified_at"] = stamp
            if d.get("comment"):
                r["summary"] = f"{r.get('summary') or ''} / 확인 메모: {d['comment']}".strip(" /")
            changed.append(iid)
        elif kind == "profile":
            prof = y.load(PROFILE_PATH.read_text(encoding="utf-8"))
            tz = prof["temp_zone_classification"]
            if act == "edit":
                tz["ambient_max"] = _num(d.get("ambient_max", tz["ambient_max"]))
                tz["cold_min"] = _num(d.get("cold_min", tz["cold_min"]))
            prof["temp_zone_classification_verified"] = True
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                y.dump(prof, f)
            changed.append(iid)
    with open(TH_PATH, "w", encoding="utf-8") as f:
        y.dump(th, f)
    with open(REG_PATH, "w", encoding="utf-8") as f:
        y.dump(regs, f)
    from .thresholds import load_thresholds
    load_thresholds.cache_clear()
    log = KB / "threshold_review_log.json"
    from ..io import load_json
    hist = load_json(log) if log.exists() else []
    hist.append({"at": stamp, "changed": changed, "decisions": {k: v for k, v in decisions.items() if k in changed}})
    save_json(log, hist)
    return {"changed": len(changed), "items": changed}
