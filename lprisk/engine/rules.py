"""룰 파일 로드·검증 (설계서 §3.5 load_rules, §3.7 룰 포맷).

룰 파일: rules/rules_*.md. 룰마다 `## [ID]. 제목` 헤더 + ```yaml 블록 + 서술(근본 원인·연쇄 리스크·DD 포인트).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..paths import ENGINE_REFS, RULES_DIR
from .expr import ExprError, parse, variables

REQUIRED = ["id", "category", "scope", "inputs", "trigger", "severity", "on_missing", "llm_adjust"]
CATEGORIES = {"aging", "spec", "fire", "cold", "location", "consistency", "benchmark"}
SCOPES = {"per_building", "asset"}
HORIZONS = {"now", "exit", "both"}
ADJUST = {"none", "up_one", "down_confirmed_only", "up_or_confirmed_down"}
SEVERITY_ORDER = ["red", "yellow", "green"]
EMOJI = {"red": "🔴", "yellow": "🟡", "green": "🟢", "hold": "⚪", None: "—"}


def single_grade() -> bool:
    """severity_policy.yaml의 single_grade — True면 🟡를 🔴로 합친다."""
    p = ENGINE_REFS / "severity_policy.yaml"
    if not p.exists():
        return False
    return bool((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("single_grade"))

_HEADER = re.compile(r"^##\s+(?:\[)?([A-Z]+[0-9]+)(?:\])?\.\s*(.+?)\s*$", re.M)
_YAML = re.compile(r"```yaml\s*\n(.*?)```", re.S)


def _parse_narrative(text: str) -> dict:
    """서술 블록 → {root_cause, cascade:{financial,lease,legal}, dd_checkpoints:[...]}."""
    out = {"root_cause": None, "cascade": {}, "dd_checkpoints": [], "notes": []}
    section = None
    keymap = {"재무": "financial", "임대차": "lease", "법률": "legal", "운영": "operation"}
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^-\s*\*\*(.+?):\*\*\s*(.*)$", s)
        if m:
            title, rest = m.group(1), m.group(2).strip()
            if "근본 원인" in title:
                section = "root"
                out["root_cause"] = rest or None
            elif "연쇄" in title:
                section = "cascade"
            elif "DD" in title:
                section = "dd"
            else:
                section = "notes"
                out["notes"].append(f"{title}: {rest}")
            continue
        m = re.match(r"^-\s*→\s*(\S+?):\s*(.*)$", s)
        if m and section == "cascade":
            out["cascade"][keymap.get(m.group(1), m.group(1))] = m.group(2).strip()
            continue
        m = re.match(r"^-\s+(.*)$", s)
        if m and section == "dd":
            out["dd_checkpoints"].append(m.group(1).strip())
        elif section == "root" and out["root_cause"] is not None:
            out["root_cause"] += " " + s
    return out


def parse_rule_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    heads = list(_HEADER.finditer(text))
    rules = []
    for i, h in enumerate(heads):
        body = text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        m = _YAML.search(body)
        if not m:
            raise ValueError(f"{path.name} {h.group(1)}: yaml 블록 없음")
        spec = yaml.safe_load(m.group(1))
        spec["title"] = h.group(2)
        spec["file"] = path.name
        spec["narrative"] = _parse_narrative(body[m.end():])
        rules.append(spec)
    return rules


def validate_rule(r: dict) -> list[str]:
    errs = []
    rid = r.get("id", "?")
    for k in REQUIRED:
        if k not in r:
            errs.append(f"{rid}: 필수 키 누락 {k}")
    if errs:
        return errs
    if r["category"] not in CATEGORIES:
        errs.append(f"{rid}: category 오류 {r['category']}")
    if r["scope"] not in SCOPES:
        errs.append(f"{rid}: scope 오류 {r['scope']}")
    if r.get("horizon", "now") not in HORIZONS:
        errs.append(f"{rid}: horizon 오류")
    if r["llm_adjust"] not in ADJUST:
        errs.append(f"{rid}: llm_adjust 오류 {r['llm_adjust']}")
    if "im_claim" in (r.get("adjust_basis") or []):
        errs.append(f"{rid}: adjust_basis에 im_claim 지정 불가 (§1.8-8)")
    if r["on_missing"] != "hold":
        errs.append(f"{rid}: on_missing은 hold만 허용")
    sev = r["severity"]
    if not isinstance(sev, dict) or not set(sev) <= set(SEVERITY_ORDER) or not sev:
        errs.append(f"{rid}: severity는 red/yellow/green 키만")
    exprs = [r["trigger"]] + [v for v in sev.values() if v != "otherwise"]
    used = set()
    for e in exprs:
        try:
            parse(e)
            used |= variables(e)
        except ExprError as ex:
            errs.append(f"{rid}: {ex}")
    declared = set(r["inputs"] or [])
    undeclared = {u for u in used if not any(u == d or u.startswith(d + ".") or d.startswith(u + ".") for d in declared)}
    if undeclared:
        errs.append(f"{rid}: inputs에 선언되지 않은 변수 {sorted(undeclared)}")
    return errs


def load_rules(rules_dir: Path = RULES_DIR) -> dict:
    rules, errors, seen = [], [], set()
    for path in sorted(rules_dir.glob("rules_*.md")):
        try:
            for r in parse_rule_file(path):
                errors += validate_rule(r)
                if r.get("id") in seen:
                    errors.append(f"{r['id']}: 중복 ID")
                seen.add(r.get("id"))
                rules.append(r)
        except Exception as e:
            errors.append(f"{path.name}: {e}")
    return {"rules": rules, "errors": errors, "count": len(rules)}
