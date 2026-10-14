"""Core Spec 스키마 로드와 스펙 레코드 순회 (설계서 §1.5, spec_record_format.md)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterator

from .io import load_yaml
from .paths import SCHEMA_REFS

ASSET_BUILDING = "_asset"  # IM이 동 구분 없이 자산 단위로 기재한 값을 담는 가상 building


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return load_yaml(SCHEMA_REFS / "core_spec_schema.yaml")


def field_def(field: str) -> dict:
    fields = load_schema()["fields"]
    if field not in fields:
        raise KeyError(f"스키마에 없는 필드: {field}")
    return fields[field]


def fields_at(level: str) -> list[str]:
    return [k for k, v in load_schema()["fields"].items() if v["level"] == level]


def enum_values(field: str) -> list[str] | None:
    d = field_def(field)
    if d["type"] != "enum":
        return None
    return load_schema()["enums"][d["enum"]]


_FLOOR_PATTERNS = [
    (re.compile(r"^\s*(?:지하|B)\s*([1-9])\s*(?:층|F)?\s*$", re.I), lambda m: f"B{m.group(1)}"),
    (re.compile(r"^\s*(?:지상)?\s*([1-9][0-9]?)\s*(?:층|F)\s*$", re.I), lambda m: f"{int(m.group(1))}F"),
    (re.compile(r"^\s*(?:메자닌|M)\s*([1-9][0-9]?)\s*(?:층|F)?\s*$", re.I), lambda m: f"M{int(m.group(1))}F"),
    (re.compile(r"^\s*(?:지붕|옥상|R|RF|PH|옥탑)\s*(?:층|F)?\s*$", re.I), lambda m: "RF"),
]


def normalize_floor(label: str) -> str | None:
    """'지상 3층', '3F', 'B1', '지하1층' → '3F', 'B1'. 해석 불가면 None."""
    if label is None:
        return None
    s = str(label).strip()
    for pat, fn in _FLOOR_PATTERNS:
        m = pat.match(s)
        if m:
            return fn(m)
    return None


def floor_sort_key(label: str) -> tuple:
    if label.startswith("B"):
        return (0, -int(label[1:]))
    if label.startswith("M"):
        return (1, int(label[1:-1]), 1)
    if label == "RF":
        return (2, 999)
    return (1, int(label[:-1]), 0)


@dataclass(frozen=True)
class Slot:
    """스펙 값의 위치. 대조·확정·평가의 공통 키."""
    level: str          # asset | building | floor
    building_id: str | None
    floor: str | None
    field: str

    @property
    def key(self) -> str:
        parts = [self.level, self.building_id or "-", self.floor or "-", self.field]
        return "|".join(parts)

    @classmethod
    def from_key(cls, key: str) -> "Slot":
        level, b, f, field = key.split("|")
        return cls(level, None if b == "-" else b, None if f == "-" else f, field)

    def label(self) -> str:
        name = field_def(self.field).get("label", self.field)
        where = []
        if self.building_id and self.building_id != ASSET_BUILDING:
            where.append(self.building_id)
        if self.floor:
            where.append(self.floor)
        return f"{name} ({' '.join(where)})" if where else name


def iter_slots(record: dict) -> Iterator[tuple[Slot, list]]:
    """스펙 레코드의 모든 (Slot, 값 리스트)."""
    for field, values in (record.get("asset") or {}).items():
        yield Slot("asset", None, None, field), values
    for b in record.get("buildings") or []:
        bid = b["building_id"]
        for field, values in (b.get("fields") or {}).items():
            yield Slot("building", bid, None, field), values
        for fl in b.get("floors") or []:
            for field, values in (fl.get("fields") or {}).items():
                yield Slot("floor", bid, fl["floor"], field), values


def empty_record(asset_id: str, record_type: str, buildings: list[dict]) -> dict:
    return {
        "asset_id": asset_id,
        "record_type": record_type,
        "asset": {},
        "buildings": [
            {"building_id": b["id"], "label": b.get("name", b["id"]), "phase": b.get("phase", "원준공"),
             "fields": {}, "floors": []}
            for b in buildings
        ],
        "claims": [],
        "missing": [],
    }


def put(record: dict, slot: Slot, values: list) -> None:
    """레코드의 slot 위치에 값 리스트를 넣는다 (building·floor가 없으면 만든다)."""
    if slot.level == "asset":
        record.setdefault("asset", {})[slot.field] = values
        return
    blds = record.setdefault("buildings", [])
    b = next((x for x in blds if x["building_id"] == slot.building_id), None)
    if b is None:
        b = {"building_id": slot.building_id, "label": slot.building_id, "phase": "원준공", "fields": {}, "floors": []}
        blds.append(b)
    if slot.level == "building":
        b.setdefault("fields", {})[slot.field] = values
        return
    fl = next((x for x in b.setdefault("floors", []) if x["floor"] == slot.floor), None)
    if fl is None:
        fl = {"floor": slot.floor, "fields": {}}
        b["floors"].append(fl)
        b["floors"].sort(key=lambda x: floor_sort_key(x["floor"]))
    fl.setdefault("fields", {})[slot.field] = values


def get(record: dict, slot: Slot) -> list | None:
    for s, v in iter_slots(record):
        if s == slot:
            return v
    return None


def evaluated_building_ids(meta: dict) -> list[str]:
    """룰 평가·자산 단위 값 전개 대상 동 (role: 부속 제외)."""
    return [b["id"] for b in meta["buildings"] if b.get("role") != "부속"]
