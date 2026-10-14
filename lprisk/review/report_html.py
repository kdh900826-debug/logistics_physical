"""보고서 MD → 단독 HTML 파일 (W2-⑪ 최종본, 수동 재생성 `python -m lprisk render-html {a}`).

리뷰 서버 /report 화면과 같은 변환(markdown + tables)·스타일(base.html)을 쓰고,
산출물 경로 링크(크롭 등)는 HTML 파일 위치 기준 상대 경로로 바꿔 폴더째 열람할 수 있게 한다.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..paths import ROOT, wf2_dir

TEMPLATES = Path(__file__).parent / "templates"


def md_to_html(text: str, base_dir: Path) -> str:
    import markdown
    html = markdown.markdown(text, extensions=["tables"])

    def rel(m):
        target = (ROOT / m.group(1)).resolve()
        return f'href="{Path(os.path.relpath(target, base_dir)).as_posix()}" target="_blank"'
    return re.sub(r'href="((?:output|input)/[^"]+)"', rel, html)


def render(asset_id: str, final: bool = True) -> Path:
    out = wf2_dir(asset_id)
    name = f"{asset_id}_logistics_risk_report{'_final' if final else ''}"
    md = out / f"{name}.md"
    if not md.exists():
        raise FileNotFoundError(f"{md.name} 없음")
    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=True)
    page = env.get_template("report_file.html").render(
        asset_id=asset_id, title=md.name.removesuffix(".md"),
        html=md_to_html(md.read_text(encoding="utf-8"), out))
    dst = out / f"{name}.html"
    dst.write_text(page, encoding="utf-8")
    return dst
