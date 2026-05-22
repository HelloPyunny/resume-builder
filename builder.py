import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONT = "HYSMyeongJo-Medium"
ACCENT = colors.HexColor("#1F3A5F")
MUTED = colors.HexColor("#5C6B7A")
BORDER = colors.HexColor("#D8DEE6")
SURFACE = colors.HexColor("#F4F6F9")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
PHOTO_W = 108
PHOTO_H = 128

OUTPUT_STEM = "korean_resume_fullpage"
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "resume_data.json"
UPLOAD_DIR = BASE_DIR / "uploads"

pdfmetrics.registerFont(UnicodeCIDFont(FONT))
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "Title",
    parent=styles["Heading1"],
    fontName=FONT,
    fontSize=22,
    leading=26,
    alignment=TA_CENTER,
    textColor=ACCENT,
    spaceAfter=3,
)

subtitle_style = ParagraphStyle(
    "Subtitle",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=10,
    leading=13,
    alignment=TA_CENTER,
    textColor=MUTED,
    spaceAfter=10,
)

label_style = ParagraphStyle(
    "Label",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=9,
    leading=12,
    textColor=ACCENT,
)

value_style = ParagraphStyle(
    "Value",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=9,
    leading=12,
    textColor=colors.black,
)

section_style = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName=FONT,
    fontSize=12,
    leading=15,
    textColor=ACCENT,
    spaceBefore=4,
    spaceAfter=2,
)

bullet_style = ParagraphStyle(
    "Bullet",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=8.4,
    leading=11.5,
    leftIndent=12,
    firstLineIndent=-7,
    spaceAfter=2,
    textColor=colors.black,
)

photo_style = ParagraphStyle(
    "Photo",
    parent=styles["BodyText"],
    fontName=FONT,
    fontSize=9,
    leading=12,
    alignment=TA_CENTER,
    textColor=MUTED,
)


def default_data() -> Dict[str, Any]:
    import json

    default_file = BASE_DIR / "resume_data_default.json"
    with default_file.open(encoding="utf-8") as f:
        return json.load(f)


def load_data() -> Dict[str, Any]:
    if DATA_FILE.exists():
        import json

        with DATA_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return default_data()


def save_data(data: Dict[str, Any]) -> None:
    import json

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_output_path(directory: Path, stem: str = OUTPUT_STEM) -> Path:
    pattern = re.compile(rf"^{re.escape(stem)}_(\d+)\.pdf$")
    max_n = 0
    for path in directory.glob(f"{stem}_*.pdf"):
        match = pattern.match(path.name)
        if match:
            max_n = max(max_n, int(match.group(1)))
    return directory / f"{stem}_{max_n + 1}.pdf"


def resolve_photo_path(photo: Optional[str]) -> Optional[Path]:
    if not photo:
        return None
    path = Path(photo)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path if path.exists() else None


def bullet_paragraph(text: str) -> Paragraph:
    if ": " in text:
        title, body = text.split(": ", 1)
        html = f"<b>{title}</b>: {body}"
    else:
        html = text
    return Paragraph(f"\u2022 {html}", bullet_style)


def section_header(title: str) -> List:
    return [
        Paragraph(title, section_style),
        HRFlowable(
            width="100%",
            thickness=0.8,
            color=ACCENT,
            spaceBefore=0,
            spaceAfter=5,
        ),
    ]


def info_table(rows: List[Tuple[str, str]]) -> Table:
    data = [
        [Paragraph(label, label_style), Paragraph(value, value_style)]
        for label, value in rows
    ]
    label_w = 68
    value_w = CONTENT_W - PHOTO_W - 14 - label_w
    table = Table(data, colWidths=[label_w, value_w])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BACKGROUND", (0, 0), (0, -1), SURFACE),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
                ("LINEBELOW", (0, -1), (-1, -1), 0.6, BORDER),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
            ]
        )
    )
    return table


def photo_block(photo_path: Optional[Path] = None) -> Table:
    if photo_path:
        img = Image(str(photo_path), width=PHOTO_W, height=PHOTO_H)
        cell = img
    else:
        cell = Paragraph("\uc0ac\uc9c4", photo_style)

    table = Table([[cell]], colWidths=[PHOTO_W], rowHeights=[PHOTO_H])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
            ]
        )
    )
    return table


def build_story(data: Dict[str, Any]) -> List:
    story = []
    story.append(Paragraph(data.get("name", ""), title_style))
    story.append(Paragraph(data.get("subtitle", ""), subtitle_style))

    info_rows = [
        (row["label"], row["value"])
        for row in data.get("info_rows", [])
        if row.get("label") or row.get("value")
    ]

    photo_path = resolve_photo_path(data.get("photo"))
    top_table = Table(
        [[photo_block(photo_path), info_table(info_rows)]],
        colWidths=[PHOTO_W + 10, CONTENT_W - PHOTO_W - 10],
    )
    top_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(top_table)
    story.append(Spacer(1, 10))

    for section in data.get("sections", []):
        title = section.get("title", "").strip()
        items = [i.strip() for i in section.get("items", []) if i.strip()]
        if not title:
            continue
        story.extend(section_header(title))
        for item in items:
            story.append(bullet_paragraph(item))
        story.append(Spacer(1, 4))

    return story


def _make_doc(target) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        target,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )


def generate_pdf_bytes(data: Dict[str, Any]) -> bytes:
    """Preview and download must both use this function."""
    buffer = BytesIO()
    doc = _make_doc(buffer)
    doc.build(build_story(data))
    return buffer.getvalue()


def generate_pdf(data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    out = output_path or next_output_path(BASE_DIR)
    out.write_bytes(generate_pdf_bytes(data))
    return out
