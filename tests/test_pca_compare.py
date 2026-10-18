"""실사 대조(pca_compare) 단위 테스트."""
import pytest

from lprisk.paths import INPUT, TESTS
from lprisk.review.pca_compare import _change, _readme, build


def test_change_labels():
    assert _change("red", "red") == "같음"
    assert _change("hold", "red") == "실사 값으로 🔴"
    assert _change("hold", "green") == "실사로 해소"
    assert _change("green", "hold") == "실사 자료 부족"
    assert _change("red", "green") == "실사 기준 하향"
    assert _change("green", "red") == "실사 기준 상향"
    assert _change(None, None) == "같음"


def test_readme_checklist(tmp_path):
    (tmp_path / "README.md").write_text(
        "# x\n\n- 실사(정답) 출처: `a.pdf` (2026)\n\n## 검토 필요\n\n- [ ] **램프 경사**: 10.69 vs 8.76\n- [x] 끝난 항목\n\n## 다음\n- [ ] 다른 절\n",
        encoding="utf-8")
    r = _readme(tmp_path)
    assert r["source"] == "`a.pdf` (2026)"
    assert [t["done"] for t in r["todo"]] == [False, True]
    assert r["todo"][0]["text"].startswith("**램프 경사**")


@pytest.mark.skipif(not ((TESTS / "golden" / "bukhang" / "golden_spec.json").exists()
                         and (INPUT / "bukhang" / "asset_meta.yaml").exists()), reason="bukhang 입력 없음")
def test_build_bukhang():
    d = build("bukhang")
    s = d["summary"]
    assert s["gold_slots"] == sum(s["spec"][k] for k in ("일치", "불일치", "WF2 누락"))
    assert sum(s["verdicts"]["ours"].values()) == sum(s["verdicts"]["pca"].values())
    by = {r["rule_id"]: r for r in d["rules"]}
    assert by["SP05"]["pca"] == "red"            # 실사 램프 곡선 내측 경사 10.69% > 9%
    assert by["SP02"]["ours"] == by["SP02"]["pca"] == "red"
