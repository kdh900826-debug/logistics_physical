"""벡터 좌표 측정(램프 내측 반경) — 합성 A3 도면으로 검증."""
import math

import fitz

from lprisk.doc_ingest import vector_measure as vm


def _ramp_pdf(path, inner_pt=37.3, outer_pt=70.0, n=60):
    doc = fitz.open()
    page = doc.new_page(width=1191, height=842)               # A3 가로
    cx, cy = 600, 400
    page.insert_text((900, 800), "축척 : 1/1,200(A3)", fontname="korea")
    page.insert_text((cx - 6, cy + 9), "W.P", fontsize=6)
    page.draw_circle((cx, cy), 2.1)
    for i in range(n):                                        # 위쪽 반원 빗금
        a = math.pi * (i + 0.5) / n
        page.draw_line((cx + inner_pt * math.cos(a), cy - inner_pt * math.sin(a)),
                       (cx + outer_pt * math.cos(a), cy - outer_pt * math.sin(a)))
    doc.save(path)


def test_ramp_radius_from_hatch(tmp_path, monkeypatch):
    pdf = tmp_path / "ramp.pdf"
    _ramp_pdf(pdf)
    monkeypatch.setattr(vm, "ROOT", tmp_path)
    monkeypatch.setattr(vm, "wf2_dir", lambda a: tmp_path)
    r = vm.ramp_radius("t", "ramp.pdf", 1)
    assert abs(r["scale_mm_per_pt"] - 423.33) < 0.01
    assert r["suggested"]["value"] == round(37.3 * 0.42333, 1)   # 15.8m
    assert r["suggested"]["precision"] == "approx" and r["method"] == "vector"


def test_ramp_radius_needs_scale(tmp_path, monkeypatch):
    doc = fitz.open(); doc.new_page(width=1191, height=842); doc.save(tmp_path / "x.pdf")
    monkeypatch.setattr(vm, "ROOT", tmp_path)
    monkeypatch.setattr(vm, "wf2_dir", lambda a: tmp_path)
    assert "error" in vm.ramp_radius("t", "x.pdf", 1)


def _yard_pdf(path):
    """도크면 x=100(세로선), 접안 구간 y=100~300. 경계: y=100~200은 x=180→160 사선, y=200~300은 곡선(x 최소 150 부근)."""
    doc = fitz.open()
    page = doc.new_page(width=1191, height=842)
    page.insert_text((900, 800), "축척 : 1/1,200(A3)", fontname="korea")
    page.draw_line((100, 50), (100, 350))                                   # 도크면
    page.draw_line((180, 100), (160, 200))                                  # 사선 연석
    sh = page.new_shape()
    sh.draw_bezier((160, 200), (140, 233), (140, 266), (160, 300))         # 곡선 연석(x 최소 = 145)
    sh.finish(); sh.commit()
    doc.save(path)


def test_depth_min_over_frontage(tmp_path, monkeypatch):
    pdf = tmp_path / "yard.pdf"
    _yard_pdf(pdf)
    monkeypatch.setattr(vm, "ROOT", tmp_path)
    monkeypatch.setattr(vm, "wf2_dir", lambda a: tmp_path)
    k = 0.42333
    r = vm.depth_min("t", "yard.pdf", 1, "100,200", "100,100", "100,300", "170,150;145,250", name="y")
    assert r["d1"]["mode"] == "min_over_frontage" and r["d1"]["coverage"] >= 0.98
    assert abs(r["distance_m"] - round(45 * k, 2)) <= 0.05          # 곡선 최저점 x≈145 → 45pt
    assert abs(r["d1"]["max_m"] - round(80 * k, 2)) <= 0.05         # 사선 시작 x=180 → 80pt
    r = vm.depth_min("t", "yard.pdf", 1, "100,200", "100,100", "100,180", "170,150", name="y2")
    assert abs(r["distance_m"] - round(64 * k, 2)) <= 0.05          # 구간 끝(y=180)에서 사선 x=164 → 64pt
    r = vm.depth_min("t", "yard.pdf", 1, "100,200", "100,100", "100,300", "170,150", name="y3")
    assert r["d1"]["coverage"] < 0.6 and "덮음" in r["note"]        # 곡선 경로를 안 줬음
