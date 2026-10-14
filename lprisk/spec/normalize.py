"""단위 정규화·precision 반폭 산출·method별 기본 confidence (설계서 §3.5 normalize_units)."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ..schema import field_def, iter_slots

PYEONG_M2 = 3.305785
G = 9.80665

# (정규화 단위) → {원 단위 표기: 배수}
UNIT_FACTORS = {
    "t/m2": {"t/m2": 1, "t/㎡": 1, "톤/㎡": 1, "톤/m2": 1, "ton/m2": 1, "tf/m2": 1, "tf/㎡": 1,
             "kg/m2": 0.001, "kg/㎡": 0.001, "kgf/m2": 0.001, "kgf/㎡": 0.001,
             "kn/m2": 1 / G, "kn/㎡": 1 / G, "kpa": 1 / G},
    "m2": {"m2": 1, "㎡": 1, "평": PYEONG_M2, "py": PYEONG_M2},
    "m": {"m": 1, "mm": 0.001, "cm": 0.01},
    "mm": {"mm": 1, "m": 1000, "cm": 10, "t": 1},       # 단열재 THK 표기 't'
    "pct": {"pct": 1, "%": 1},
    "kW": {"kw": 1, "mw": 1000},
    "kVA": {"kva": 1, "mva": 1000},
    "t": {"t": 1, "ton": 1, "톤": 1, "kg": 0.001},
    "year": {"year": 1, "년": 1},
    "ea": {"ea": 1, "개": 1, "대": 1, "기": 1, "개소": 1},
    "floor": {"floor": 1, "층": 1},
}

DEFAULT_CONFIDENCE = {"dxf": "high", "script": "medium", "im_text": "medium", "vision": "low",
                      "vision_hinted": "low", "public_api": "high", "user": "high"}
CONF_RANK = {"low": 0, "medium": 1, "high": 2}


def _unit_key(u: str | None) -> str:
    return (u or "").strip().replace(" ", "").lower()


def _to_number(v) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.replace(",", "").strip()
        m = re.fullmatch(r"1\s*[/:]\s*([0-9.]+)", s)          # 램프 경사 '1/8', '1:8'
        if m:
            return 100.0 / float(m.group(1))
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _last_digit_unit(raw) -> float:
    """원 값 표기의 마지막 유효 자리 단위. 1.5→0.1, 30000→10000, 10→1."""
    try:
        d = Decimal(str(raw).replace(",", ""))
    except InvalidOperation:
        return 0.0
    d = d.normalize()
    exp = d.as_tuple().exponent
    return float(Decimal(1).scaleb(exp))


def normalize_value(field: str, v: dict) -> dict:
    """ValueObj 하나를 스키마 단위로 정규화. 원 값은 raw_value/raw_unit에 보존. flags에 이상 표시."""
    fd = field_def(field)
    out = dict(v)
    flags = list(out.get("flags") or [])
    t = fd["type"]
    if out.get("method") and not out.get("confidence"):
        out["confidence"] = DEFAULT_CONFIDENCE.get(out["method"], "low")
    elif out.get("method") in DEFAULT_CONFIDENCE:
        # 추출자는 confidence를 낮출 수만 있다
        cap = DEFAULT_CONFIDENCE[out["method"]]
        if CONF_RANK.get(out.get("confidence"), 0) > CONF_RANK[cap]:
            out["confidence"] = cap

    if t in ("number", "int"):
        target = fd.get("unit")
        if "raw_value" not in out:
            out["raw_value"], out["raw_unit"] = out.get("value"), out.get("unit")
        num = _to_number(out["raw_value"])
        if num is None:
            flags.append("value_not_numeric")
        else:
            src_unit = _unit_key(out.get("raw_unit") or target)
            # 램프 경사 '1/8' 표기는 이미 % 로 환산됨
            if isinstance(out["raw_value"], str) and re.fullmatch(r"1\s*[/:]\s*[0-9.]+", out["raw_value"].strip()):
                src_unit = "pct"
            factors = {_unit_key(k): f for k, f in UNIT_FACTORS.get(target, {target: 1}).items()}
            factors.setdefault(_unit_key(target), 1)
            if src_unit not in factors:
                flags.append(f"unit_unknown:{out.get('raw_unit')}")
                out["value"] = None
            else:
                f = factors[src_unit]
                val = num * f
                out["value"] = int(round(val)) if t == "int" else round(val, 4)
                out["unit"] = target
                prec = out.get("precision") or "exact"
                if prec in ("approx", "rounded"):
                    out["precision_halfwidth"] = round(_last_digit_unit(out["raw_value"]) / 2 * f, 4)
                rng = fd.get("range")
                if rng and out["value"] is not None and not (rng[0] <= out["value"] <= rng[1]):
                    flags.append("range_out")
    elif t == "enum":
        from ..schema import enum_values
        if out.get("value") not in (enum_values(field) or []):
            flags.append(f"enum_invalid:{out.get('value')}")
    elif t == "bool":
        if not isinstance(out.get("value"), bool):
            flags.append("bool_invalid")
    out["flags"] = sorted(set(flags))
    return out


def normalize_record(record: dict) -> dict:
    for slot, values in iter_slots(record):
        if field_def(slot.field)["type"] == "list":
            continue
        values[:] = [normalize_value(slot.field, v) for v in values]
    return record
