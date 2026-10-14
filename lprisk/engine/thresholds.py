"""thresholds.yaml 해석: default + segment override, verified 검사 (설계서 §3.7)."""
from __future__ import annotations

from functools import lru_cache

from ..io import load_yaml
from ..paths import ENGINE_REFS
from .expr import Missing


@lru_cache(maxsize=1)
def load_thresholds() -> dict:
    p = ENGINE_REFS / "thresholds.yaml"
    data = load_yaml(p) if p.exists() else {}
    return {k: v for k, v in (data or {}).items() if isinstance(v, dict) and ("default" in v or "overrides" in v)}


class ThresholdResolver:
    """th.<group>.<key> 참조를 동 세그먼트에 맞춰 해석하고, 사용 기록을 남긴다."""

    def __init__(self, segment: dict, table: dict | None = None):
        self.segment = segment or {}
        self.table = table if table is not None else load_thresholds()
        self.used: dict[str, dict] = {}

    def __call__(self, path: str):
        group, _, key = path.partition(".")
        g = self.table.get(group)
        if g is None:
            raise Missing(f"th.{path}", "임계값 미정")
        entry, seg_label = None, "default"
        for ov in g.get("overrides") or []:
            cond = ov.get("when") or {}
            if cond and all(self.segment.get(k) == v for k, v in cond.items()) and key in ov:
                entry, seg_label = ov[key], ",".join(f"{k}={v}" for k, v in cond.items())
                break
        if entry is None:
            entry = (g.get("default") or {}).get(key)
        if entry is None or entry.get("value") is None:
            raise Missing(f"th.{path}", "임계값 미정")
        self.used[path] = {"key": path, "value": entry["value"], "segment": seg_label,
                           "source": entry.get("source"), "verified": bool(entry.get("verified"))}
        if not entry.get("verified"):
            raise Missing(f"th.{path}", "기준값 미검증")
        return entry["value"]
