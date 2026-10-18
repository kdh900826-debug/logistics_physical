"""룰 조건식 제한 문법 평가기 (설계서 §3.7). `eval` 미사용.

허용: 비교(== != < <= > >= in, not in), and/or/not, 숫자·문자열·불리언·null·리스트 리터럴,
점 표기 변수(building_age, warehouse_floors.floor_load_tpm2.min), th. 임계값 참조,
화이트리스트 함수(area_share_below, area_share_above, floors_below, floors_above, count, any_of, min_below).

미확인 값은 3치 논리로 다룬다: 비교에 null 값이 들어가면 Missing. and/or는 Kleene 규칙.
단, `x == null` / `x != null`은 명시적 null 검사로 보고 미확인을 None으로 판정한다.
따라서 '입력이 있어야 평가'라는 뜻으로 trigger에 `x != null`을 쓰지 않는다(입력 미확인이 미발동이 됨).
항상 적용되는 룰은 trigger "true"로 두고, 심각도 식에서 미확인이 나오면 ⚪가 된다.
"""
from __future__ import annotations

import ast
from typing import Callable

LITERALS = {"null": None, "true": True, "false": False}


class Missing(Exception):
    """입력 미확인 — 룰은 ⚪ 판정 보류."""
    def __init__(self, path: str, reason: str = "입력 미확인", inputs: list[str] | None = None):
        super().__init__(path)
        self.path, self.reason = path, reason
        self.inputs = inputs          # 보류 원인 슬롯을 직접 지정할 때 (없으면 프로파일 missing 맵에서 찾음)


class ExprError(Exception):
    """문법 위반 — 룰 파일 오류 (load_rules에서 걸러야 함)."""


_ALLOWED = (ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not, ast.USub, ast.Compare,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Name, ast.Load,
            ast.Attribute, ast.Constant, ast.List, ast.Tuple, ast.Call)

FUNCS = {"area_share_below", "area_share_above", "floors_below", "floors_above", "count", "any_of", "min_below"}


def parse(src: str) -> ast.Expression:
    try:
        tree = ast.parse(src.strip(), mode="eval")
    except SyntaxError as e:
        raise ExprError(f"구문 오류: {src!r} ({e.msg})")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ExprError(f"허용되지 않은 문법 {type(node).__name__}: {src!r}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS or node.keywords:
                raise ExprError(f"허용되지 않은 함수 호출: {src!r}")
    return tree


def dotted(node) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def variables(src: str) -> set[str]:
    """식이 참조하는 변수 경로 (th. 제외). load_rules의 inputs 검증용."""
    out = set()
    for node in ast.walk(parse(src)):
        if isinstance(node, (ast.Attribute, ast.Name)):
            p = dotted(node)
            if p and p not in LITERALS and p != "th" and not p.startswith("th.") and p not in FUNCS:
                out.add(p)
    # 하위 경로(a.b)만 남기고 상위 접두(a)는 제거
    return {p for p in out if not any(q != p and q.startswith(p + ".") for q in out)}


def _min_below(series: list[dict], x, path: str) -> bool:
    """층 시리즈의 (실제) 최솟값이 x 미만인가 — 상한값(upper_bound)을 구간으로 본다.

    upper_bound = 그 값 이하(예: 유효층고 '보 하단' — 배관 미반영). 어느 층이든 값(상한 포함)이 x 미만이면 참(확정).
    상한만 있는 층이 x 이상이면 실제 값이 x 미만일 수 있으므로 Missing(판정 보류) — 공제폭을 빼서 추정하지 않는다.
    lower_bound(IM '8.2m 이상' 등)는 적힌 값으로 비교한다 — 매도자 유리 방향 비대칭(원칙 5): '이상' 표기로 심각도를 낮추지 않는다.
    """
    if any(s.get("value") is not None and s["value"] < x for s in series):
        return True
    unknown = [s for s in series if s.get("value") is None]
    upper = [s for s in series if s.get("value") is not None and s.get("precision") == "upper_bound"]
    if upper:
        fl = ", ".join(f"{s['floor']} {s['value']}" + (f"({s['basis']})" if s.get("basis") else "") for s in upper)
        raise Missing(path, f"상한값만 있음 — {fl}: 실제 값이 이보다 낮을 수 있어 기준 이상으로 확정 못 함",
                      [s["slot"] for s in upper if s.get("slot")] or None)
    if unknown:
        raise Missing(path)
    return False


class Evaluator:
    def __init__(self, resolve: Callable[[str], object], resolve_th: Callable[[str], object]):
        self.resolve, self.resolve_th = resolve, resolve_th

    def eval(self, src: str):
        return self._ev(parse(src).body)

    def _value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.List, ast.Tuple)):
            return [self._value(e) for e in node.elts]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            v = self._value(node.operand)
            if v is None:
                raise Missing("-", "입력 미확인")
            return -v
        if isinstance(node, (ast.Name, ast.Attribute)):
            p = dotted(node)
            if p in LITERALS:
                return LITERALS[p]
            if p.startswith("th."):
                return self.resolve_th(p[3:])
            return self.resolve(p)
        if isinstance(node, ast.Call):
            return self._call(node)
        return self._ev(node)

    def _lenient(self, node):
        try:
            return self._value(node)
        except Missing:
            return None

    def _call(self, node: ast.Call):
        name = node.func.id
        args = [self._value(a) for a in node.args]
        if name == "count":
            if args[0] is None:
                raise Missing(dotted(node.args[0]) or "count")
            return len(args[0])
        if name == "any_of":
            return any(bool(x) for x in (args[0] or []))
        series, x = args
        path = dotted(node.args[0]) or name
        if series is None or x is None:
            raise Missing(path)
        if name == "min_below":
            return _min_below(series, x, path)
        known = [s for s in series if s.get("value") is not None]
        if name in ("floors_below", "floors_above"):
            cmp = (lambda v: v < x) if name == "floors_below" else (lambda v: v > x)
            return [s["floor"] for s in known if cmp(s["value"])]
        # area_share_*: 해당 층 면적 합 / 창고층 면적 합. 면적이 하나라도 미확인이면 Missing
        if any(s.get("area") is None for s in series):
            raise Missing(path + ".area", "층 면적 미확인")
        total = sum(s["area"] for s in series)
        if total <= 0:
            raise Missing(path + ".area", "층 면적 미확인")
        cmp = (lambda v: v < x) if name == "area_share_below" else (lambda v: v > x)
        return sum(s["area"] for s in known if cmp(s["value"])) / total

    def _ev(self, node):
        if isinstance(node, ast.BoolOp):
            results, missing = [], None
            for v in node.values:
                try:
                    results.append(bool(self._ev(v)))
                except Missing as m:
                    missing = missing or m
            if isinstance(node.op, ast.And):
                if False in results:
                    return False
            else:
                if True in results:
                    return True
            if missing:
                raise missing
            return isinstance(node.op, ast.And)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._ev(node.operand)
        if isinstance(node, ast.Compare):
            # `x == null` / `x != null`은 명시적 null 검사: 미확인 값을 None으로 보고 판정한다
            null_check = len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)) and                 any(dotted(n) == "null" for n in (node.left, node.comparators[0]))
            left = self._lenient(node.left) if null_check else self._value(node.left)
            lnode = node.left
            for op, rnode in zip(node.ops, node.comparators):
                right = self._lenient(rnode) if null_check else self._value(rnode)
                if isinstance(op, (ast.Eq, ast.NotEq)) and (left is None or right is None):
                    res = (left is right) if isinstance(op, ast.Eq) else (left is not right)
                else:
                    for side, n in ((left, lnode), (right, rnode)):
                        if side is None:
                            raise Missing(dotted(n) or "?")
                    if isinstance(op, ast.Lt): res = left < right
                    elif isinstance(op, ast.LtE): res = left <= right
                    elif isinstance(op, ast.Gt): res = left > right
                    elif isinstance(op, ast.GtE): res = left >= right
                    elif isinstance(op, ast.In): res = left in right
                    elif isinstance(op, ast.NotIn): res = left not in right
                    else: res = left == right if isinstance(op, ast.Eq) else left != right
                if not res:
                    return False
                left, lnode = right, rnode
            return True
        v = self._value(node)
        if v is None:
            raise Missing(dotted(node) or "?")
        return bool(v)
