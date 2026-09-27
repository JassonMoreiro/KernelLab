from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "relatorio_tecnico.md"
OUTPUT = ROOT / "docs" / "relatorio_tecnico.pdf"


def inline_markup(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='ReportMono'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"&lt;(https?://[^&]+)&gt;", r"<link href='\1' color='#146B68'>\1</link>", text)
    return text


def table_rows(lines: list[str]) -> list[list[str]]:
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def build_story(markdown: str, styles: dict) -> list:
    lines = markdown.splitlines()
    story = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("|"):
            block = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index].strip())
                index += 1
            rows = table_rows(block)
            if rows:
                data = [[Paragraph(inline_markup(cell), styles["table_header"] if row_index == 0 else styles["table_cell"])
                         for cell in row] for row_index, row in enumerate(rows)]
                widths = [(A4[0] - 36 * mm) / len(rows[0])] * len(rows[0])
                table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174A52")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#AAB8BC")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F5F4")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.extend([table, Spacer(1, 7)])
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            story.append(Paragraph(inline_markup(heading.group(2)), styles[f"h{level}"]))
            story.append(Spacer(1, 3))
        elif line.startswith("> "):
            story.append(Paragraph(inline_markup(line[2:]), styles["quote"]))
        elif line.startswith("- "):
            story.append(Paragraph(inline_markup(line[2:]), styles["bullet"], bulletText="-"))
        elif re.match(r"^\d+\.\s", line):
            story.append(Paragraph(inline_markup(re.sub(r"^\d+\.\s", "", line)), styles["bullet"], bulletText="•"))
        else:
            paragraph = [line]
            index += 1
            while index < len(lines):
                following = lines[index].strip()
                if (not following or following.startswith(("#", "|", "> ", "- "))
                        or re.match(r"^\d+\.\s", following)):
                    break
                paragraph.append(following)
                index += 1
            story.append(Paragraph(inline_markup(" ".join(paragraph)), styles["body"]))
            story.append(Spacer(1, 5))
            continue
        index += 1
    return story


def add_page_chrome(canvas, document) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#C6D2D2"))
    canvas.line(18 * mm, 15 * mm, width - 18 * mm, 15 * mm)
    canvas.setFont("ReportSans", 8)
    canvas.setFillColor(colors.HexColor("#52666A"))
    canvas.drawString(18 * mm, 10 * mm, "KernelLab | Relatório técnico — MedControl")
    canvas.drawRightString(width - 18 * mm, 10 * mm, str(document.page))
    canvas.restoreState()


def main() -> None:
    from reportlab import Version
    from reportlab.pdfbase.ttfonts import TTFError

    fonts = Path(__import__("reportlab").__file__).resolve().parent / "fonts"
    try:
        pdfmetrics.registerFont(TTFont("ReportSans", str(fonts / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(fonts / "VeraBd.ttf")))
        pdfmetrics.registerFont(TTFont("ReportMono", str(fonts / "Vera.ttf")))
    except (OSError, TTFError) as error:
        raise RuntimeError(f"Não foi possível carregar as fontes incluídas no ReportLab {Version}") from error

    base = getSampleStyleSheet()
    styles = {
        "h1": ParagraphStyle("ReportTitle", parent=base["Title"], fontName="ReportSans-Bold",
                              fontSize=20, leading=25, textColor=colors.HexColor("#174A52"),
                              alignment=TA_LEFT, spaceAfter=10),
        "h2": ParagraphStyle("Section", parent=base["Heading2"], fontName="ReportSans-Bold",
                              fontSize=14, leading=18, textColor=colors.HexColor("#174A52"),
                              spaceBefore=10, spaceAfter=6),
        "h3": ParagraphStyle("Subsection", parent=base["Heading3"], fontName="ReportSans-Bold",
                              fontSize=11, leading=14, textColor=colors.HexColor("#146B68"),
                              spaceBefore=7, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="ReportSans",
                               fontSize=9.3, leading=13.4, alignment=TA_LEFT,
                               textColor=colors.HexColor("#202B2E")),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="ReportSans",
                                 fontSize=9.3, leading=13.4, leftIndent=12, firstLineIndent=0,
                                 textColor=colors.HexColor("#202B2E"), spaceAfter=3),
        "quote": ParagraphStyle("Quote", parent=base["BodyText"], fontName="ReportSans-Bold",
                                fontSize=9.2, leading=13, leftIndent=9, borderColor=colors.HexColor("#D2A84A"),
                                borderWidth=2, borderPadding=7, backColor=colors.HexColor("#F5F4EC"),
                                textColor=colors.HexColor("#354448"), spaceAfter=8),
        "table_header": ParagraphStyle("TableHeader", fontName="ReportSans-Bold", fontSize=7.6,
                                       leading=9.5, textColor=colors.white),
        "table_cell": ParagraphStyle("TableCell", fontName="ReportSans", fontSize=7.6,
                                     leading=9.5, textColor=colors.HexColor("#202B2E")),
    }
    frame = Frame(18 * mm, 20 * mm, A4[0] - 36 * mm, A4[1] - 36 * mm,
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
    document = BaseDocTemplate(str(OUTPUT), pagesize=A4, title="KernelLab — Relatório Técnico MedControl",
                               author="Equipe KernelLab", subject="Sistemas Operacionais")
    document.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=add_page_chrome)])
    document.build(build_story(SOURCE.read_text(encoding="utf-8"), styles))
    print(f"PDF gerado: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()