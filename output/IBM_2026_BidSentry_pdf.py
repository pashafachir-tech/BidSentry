from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = ROOT / ".codex-build" / "presentation" / "renders"


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble the rendered 16:9 BidSentry pitch slides into a PDF.")
    parser.add_argument("--stem", default="IBM_2026_BidSentry_v3", help="output filename stem")
    args = parser.parse_args()
    images = sorted(RENDER_DIR.glob("slide-[0-9][0-9].png"))
    if len(images) != 10:
        raise SystemExit(f"Expected 10 slide renders in {RENDER_DIR}; found {len(images)}.")
    output_dir = ROOT / "output" / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{args.stem}.pdf"
    page_w, page_h = 13.3333333333 * inch, 7.5 * inch
    pdf = canvas.Canvas(str(target), pagesize=(page_w, page_h), pageCompression=1)
    pdf.setTitle("BidSentry AI | IBM SkillsBuild 2026")
    pdf.setAuthor("Tim BidSentry AI")
    pdf.setSubject("Pitch deck 16:9; seluruh demo memakai data sintetis")
    for image in images:
        pdf.drawImage(str(image), 0, 0, width=page_w, height=page_h, preserveAspectRatio=False, anchor="c", mask="auto")
        pdf.showPage()
    pdf.save()
    print(f"Created {target} with {len(images)} landscape 16:9 pages")


if __name__ == "__main__":
    main()