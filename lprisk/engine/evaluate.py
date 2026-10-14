"""W2-⑧ (a) 룰 트리거·기본 심각도 판정 (설계서 §2.3 W2-⑧, §3.5 evaluate_rules).

- 동별(scope: per_building) / 자산 단위(scope: asset) 평가
- horizon: both → 현재 연식과 exit 연식으로 두 번 평가
- 입력 미확인·기준값 미검증 → ⚪(hold)
- 일부 창고층 미확인인데 결과가 🟢 → ⚪
- 주장값 입력으로 나온 🟢 → ⚪ (§1.8-10)
"""
from __future__ import annotations

import copy

from ..io import load_json, now_iso, save_json
from ..paths import wf2_dir
from .expr import Evaluator, Missing, variables
from .rules import SEVERITY_ORDER, load_rules, single_grade
from .thresholds import ThresholdResolver


def _resolver(vars_: dict, touched: set):
    def resolve(path: str):
        touched.add(path)
        if path not in vars_:
            raise Missing(path, "변수 없음(프로파일 미산출)")
        v = vars_[path]
        if v is None:
            raise Missing(path)
        return v
    return resolve


def _eval_once(rule: dict, ctx: dict, segment: dict) -> dict:
    vars_ = ctx["vars"]
    touched: set[str] = set()
    th = ThresholdResolver(segment)
    ev = Evaluator(_resolver(vars_, touched), th)
    res = {"status": None, "severity": None, "hold_reason": None, "missing_inputs": []}

    def hold(m: Missing):
        res.update(status="hold", severity="hold", hold_reason=m.reason)
        path = m.path
        res["missing_inputs"] = sorted(set((ctx.get("missing") or {}).get(path, []) or [path]))

    try:
        trig = ev.eval(rule["trigger"])
    except Missing as m:
        hold(m)
        trig = None
    if trig is False:
        res["status"] = "not_triggered"
    elif trig is True:
        res["status"] = "triggered"
        skipped, evaluated = [], 0
        for sev in SEVERITY_ORDER:
            expr = rule["severity"].get(sev)
            if expr is None:
                continue
            if expr == "otherwise":
                res["severity"] = sev
                break
            try:
                if ev.eval(expr):
                    res["severity"] = sev
                    break
                evaluated += 1
            except Missing as m:
                if m.reason == "임계값 미정":     # 정의되지 않은 등급은 건너뛴다 (thresholds.yaml에 키 없음)
                    skipped.append(sev)
                    continue
                hold(m)                           # 더 높은 심각도를 배제할 수 없음
                break
        res["levels_skipped"] = skipped
        if res["severity"] is None and res["status"] == "triggered":
            res["severity"] = "green"
        if res["severity"] == "green" and skipped and evaluated == 0:
            res.update(status="hold", severity="hold", hold_reason="임계값 미정",
                       missing_inputs=[f"thresholds.yaml: {rule['id']} {'/'.join(skipped)}"])

    inputs = set()
    for e in [rule["trigger"]] + [v for v in rule["severity"].values() if v != "otherwise"]:
        inputs |= variables(e)
    grades = {p: (ctx.get("grades") or {}).get(p) for p in touched}
    claimed = sorted(p for p, g in grades.items() if g == "claimed")
    res["input_grade"] = "claimed" if claimed else "verified"
    res["claimed_inputs"] = claimed

    if res["severity"] == "green":
        partial = [p for p in inputs if p.startswith("warehouse_floors.")]
        for p in partial:
            base = ".".join(p.split(".")[:2])
            mc = vars_.get(base + ".missing_count")
            if mc:
                res.update(status="hold", severity="hold", hold_reason="일부 창고층 미확인",
                           missing_inputs=(ctx.get("missing") or {}).get(base, []))
                break
    if res["severity"] == "green" and claimed:
        res.update(status="hold", severity="hold", hold_reason="주장값 기반 🟢 격하(†IM 기준)")
    res["thresholds"] = list(th.used.values())
    res["facts"] = {p: vars_.get(p) for p in sorted(touched) if not isinstance(vars_.get(p), list) or len(vars_.get(p)) < 30}
    res["fact_deps"] = {p: (ctx.get("deps") or {}).get(p, []) for p in sorted(touched)}
    vec = set(ctx.get("vector_slots") or [])
    res["vector_inputs"] = sorted({s for d in res["fact_deps"].values() for s in d if s in vec})
    return res


def evaluate_context(rule: dict, ctx: dict, segment: dict) -> dict:
    """한 컨텍스트(동 또는 자산)에서 룰 평가. horizon both면 now/exit 둘 다."""
    horizon = rule.get("horizon", "now")
    out = {"rule_id": rule["id"], "title": rule["title"], "category": rule["category"],
           "building_id": ctx.get("building_id"), "horizon": horizon}
    if horizon in ("now", "both"):
        out["now"] = _eval_once(rule, ctx, segment)
    if horizon in ("exit", "both"):
        ectx = copy.copy(ctx)
        ectx["vars"] = dict(ctx["vars"])
        ectx["vars"]["building_age"] = ctx["vars"].get("exit_age")
        ectx["grades"] = dict(ctx.get("grades") or {})
        ectx["grades"]["building_age"] = (ctx.get("grades") or {}).get("exit_age")
        ectx["missing"] = dict(ctx.get("missing") or {})
        ectx["missing"]["building_age"] = (ctx.get("missing") or {}).get("exit_age", ["asset_meta.holding_years"])
        out["exit"] = _eval_once(rule, ectx, segment)
    primary = out.get("now") or out.get("exit")
    out.update(status=primary["status"], severity_base=primary["severity"],
               severity_exit=(out.get("exit") or {}).get("severity") if horizon == "both" else None)
    return out


def asset_context(profile: dict, extra: dict) -> dict:
    """자산 단위 룰 컨텍스트: 첫 동의 자산 공용 변수 + 정합성(v01/v02) 변수."""
    from ..schema import fields_at
    b0 = profile["buildings"][0] if profile["buildings"] else {"vars": {}, "grades": {}, "deps": {}, "missing": {}}
    keys = set(fields_at("asset"))
    vars_ = {k: v for k, v in b0["vars"].items() if k in keys}
    grades = {k: v for k, v in b0["grades"].items() if k in keys}
    vars_.update(extra.get("vars", {}))
    grades.update(extra.get("grades", {}))
    return {"building_id": None, "vars": vars_, "grades": grades, "vector_slots": profile.get("vector_slots") or [],
            "deps": {k: v for k, v in b0["deps"].items() if k in keys},
            "missing": {k: v for k, v in b0["missing"].items() if k in keys}}


def evaluate_profile(profile: dict, rules: list[dict], extra_asset_vars: dict | None = None,
                     only: set[str] | None = None, single: bool | None = None) -> list[dict]:
    """single: 🟡→🔴 단일 등급 적용 여부. None이면 severity_policy.yaml을 따른다."""
    results = []
    actx = asset_context(profile, extra_asset_vars or {})
    for r in rules:
        if only and r["id"] not in only:
            continue
        if r["scope"] == "asset":
            seg = profile["buildings"][0]["segment"] if profile["buildings"] else {}
            results.append(evaluate_context(r, actx, seg))
        else:
            for b in profile["buildings"]:
                ctx = {"building_id": b["building_id"], "vars": b["vars"], "grades": b["grades"],
                       "deps": b["deps"], "missing": b["missing"], "vector_slots": profile.get("vector_slots") or []}
                results.append(evaluate_context(r, ctx, b["segment"]))
    if single_grade() if single is None else single:
        for r in results:
            merge_yellow(r)
    return results


def merge_yellow(r: dict) -> dict:
    """단일 등급 정책: 🟡 판정을 🔴로 합치고 원래 등급을 merged_from에 남긴다."""
    for part in (r.get("now"), r.get("exit")):
        if part and part.get("severity") == "yellow":
            part.update(severity="red", merged_from="yellow")
    for k in ("severity_base", "severity_exit"):
        if r.get(k) == "yellow":
            r[k] = "red"
            r.setdefault("merged_from", {})[k] = "yellow"
    return r


def run(asset_id: str) -> dict:
    from .consistency import consistency_vars
    out_dir = wf2_dir(asset_id)
    profile = load_json(out_dir / "w2_06_profile.json")
    loaded = load_rules()
    if loaded["errors"]:
        raise RuntimeError("룰 파일 오류:\n" + "\n".join(loaded["errors"]))
    rules = loaded["rules"]
    extra = consistency_vars(asset_id, profile, rules)
    single = single_grade()
    results = evaluate_profile(profile, rules, extra, single=single)
    data = {"asset_id": asset_id, "created_at": now_iso(), "rule_count": len(rules), "single_grade": single,
            "consistency": extra.get("detail"), "results": results}
    save_json(out_dir / "w2_08_base.json", data)
    return data
