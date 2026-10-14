"""WF2 세션 상태 (설계서 §2.1). output/wf2/{asset}/session_state.json."""
from __future__ import annotations

import subprocess

from .io import load_json, now_iso, save_json
from .paths import ROOT, wf2_dir

STATES = ["INTAKE", "EXTRACTING", "RECONCILED", "AWAITING_CONFIRMATION", "PROFILED", "EVALUATED",
          "REPORT_DRAFT", "AWAITING_REVIEW", "FINAL", "HALTED"]


def ruleset_version() -> str:
    """현재 룰셋 버전 = 최신 ruleset-* 태그 (+ 커밋 해시, 미커밋 변경 표시)."""
    def git(*args):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        return r.stdout.strip() if r.returncode == 0 else ""
    tag = git("describe", "--tags", "--match", "ruleset-*", "--abbrev=0")
    head = git("rev-parse", "--short", "HEAD")
    dirty = git("status", "--porcelain", "--", ".claude/skills/risk-engine/references")
    v = tag or "ruleset-untagged"
    if head:
        v += f"@{head}"
    if dirty:
        v += "+uncommitted"
    return v


def path(asset_id: str):
    return wf2_dir(asset_id) / "session_state.json"


def load(asset_id: str) -> dict:
    p = path(asset_id)
    return load_json(p) if p.exists() else {}


def init(asset_id: str, mode: str) -> dict:
    st = {"asset_id": asset_id, "state": "INTAKE", "mode": mode, "ruleset_version": ruleset_version(),
          "created_at": now_iso(), "history": [{"at": now_iso(), "state": "INTAKE"}], "halt_reason": None,
          "revisions": []}
    save_json(path(asset_id), st)
    return st


def transition(asset_id: str, state: str, note: str | None = None, **extra) -> dict:
    assert state in STATES, state
    st = load(asset_id) or init(asset_id, "정규")
    st["state"] = state
    st["history"].append({"at": now_iso(), "state": state, "note": note})
    if state == "HALTED":
        st["halt_reason"] = note
    st.update(extra)
    save_json(path(asset_id), st)
    return st
