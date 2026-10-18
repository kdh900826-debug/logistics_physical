"""스펙 레코드 검증 (설계서 §3.5 validate_spec, §1.8-3 출처 필수).

errors: 스키마 위반 — 재시도 대상
flags:  값 이상(범위 이탈·단위 불명 등) — 검토 큐/G2로 넘김
"""
from __future__ import annotations

import re

from ..schema import ASSET_BUILDING, field_def, iter_slots, load_schema

ALLOWED = load_schema()["value_meta"]


def validate_record(record: dict, building_ids: list[str] | None = None) -> dict:
    errors, flags = [], []
    fields = load_schema()["fields"]
    floor_re = re.compile(load_schema()["floor_label_pattern"])
    for slot, values in iter_slots(record):
        where = slot.key
        if slot.field not in fields:
            errors.append(f"{where}: 스키마에 없는 필드")
            continue
        fd = fields[slot.field]
        if fd["level"] != slot.level:
            errors.append(f"{where}: level 불일치 (스키마 {fd['level']})")
        if building_ids is not None and slot.building_id not in (None, ASSET_BUILDING, *building_ids):
            errors.append(f"{where}: asset_meta에 없는 building_id")
        if slot.floor is not None and not floor_re.match(slot.floor):
            errors.append(f"{where}: 층 라벨 형식 오류 '{slot.floor}'")
        if not isinstance(values, list) or not values:
            errors.append(f"{where}: 값은 비어있지 않은 리스트여야 함")
            continue
        if fd["type"] == "list":
            continue
        for i, v in enumerate(values):
            tag = f"{where}[{i}]"
            if "value" not in v or v["value"] is None and "unit_unknown" not in " ".join(v.get("flags", [])):
                errors.append(f"{tag}: value 없음 (값이 없으면 필드를 넣지 말 것)")
            if not v.get("source_doc") or not v.get("source_locator"):
                errors.append(f"{tag}: 출처(source_doc/source_locator) 없음")
            if v.get("method") not in ALLOWED["method"]:
                errors.append(f"{tag}: method 값 오류 {v.get('method')}")
            if v.get("precision") and v["precision"] not in ALLOWED["precision"]:
                errors.append(f"{tag}: precision 값 오류 {v.get('precision')}")
            if v.get("basis") is not None:
                bdef = fd.get("basis")
                allowed = load_schema()["enums"].get(bdef["enum"], []) if bdef else []
                if v["basis"] not in allowed:
                    errors.append(f"{tag}: basis 값 오류 {v.get('basis')} (허용: {', '.join(allowed) or '이 필드는 basis 없음'})")
            for fl in v.get("flags") or []:
                flags.append({"slot": where, "index": i, "flag": fl, "value": v.get("value")})
    for m in record.get("missing") or []:
        if m.get("missing_reason") not in ALLOWED["missing_reason"]:
            errors.append(f"missing {m.get('field')}: missing_reason 오류 {m.get('missing_reason')}")
    for c in record.get("claims") or []:
        if not c.get("quote") or not c.get("source_locator"):
            errors.append(f"claim '{c.get('text', '')[:20]}': 원문 인용·출처 없음")
    return {"ok": not errors, "errors": errors, "flags": flags}
