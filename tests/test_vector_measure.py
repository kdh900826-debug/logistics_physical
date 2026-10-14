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
