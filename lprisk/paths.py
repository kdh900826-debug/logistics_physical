"""프로젝트 경로 규약 (설계서 §3.1)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"

SCHEMA_REFS = SKILLS / "spec-schema" / "references"
INGEST_REFS = SKILLS / "doc-ingest" / "references"
ENGINE_REFS = SKILLS / "risk-engine" / "references"
RULES_DIR = ENGINE_REFS / "rules"
LOCATION_REFS = SKILLS / "location" / "references"

KB = ROOT / "kb"
INPUT = ROOT / "input"
OUTPUT = ROOT / "output"
TESTS = ROOT / "tests"


def input_dir(asset_id: str) -> Path:
    return INPUT / asset_id


def wf2_dir(asset_id: str) -> Path:
    d = OUTPUT / "wf2" / asset_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def rel(p: Path | str) -> str:
    """프로젝트 루트 기준 상대 경로 (출처 표기·JSON 저장용, 슬래시 통일)."""
    p = Path(p).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()
