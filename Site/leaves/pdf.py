"""Versioned Bulgarian PDF layout with embedded Cyrillic fonts."""

import datetime
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@lru_cache(maxsize=1)
def register_fonts() -> None:
    directory = Path(__file__).parent / "fonts"
    pdfmetrics.registerFont(TTFont("LeaveBody", str(directory / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("LeaveBold", str(directory / "DejaVuSans-Bold.ttf")))


def render_annual_request(document) -> bytes:
    if document.template_version != "bg-annual-request-v1":
        raise ValueError("Unsupported document template version")
    register_fonts()
    data = document.snapshot
    output = BytesIO()
    body = ParagraphStyle("Body", fontName="LeaveBody", fontSize=10, leading=16, spaceAfter=9)
    heading = ParagraphStyle("Heading", parent=body, fontName="LeaveBold", fontSize=21, leading=27)
    label = ParagraphStyle("Label", parent=body, fontSize=8, textColor=colors.HexColor("#52646F"))
    reference = f"FR-LR-{document.leave_id}-{str(document.pk)[:8]}"

    def p(text, style=body):
        return Paragraph(escape(str(text)), style)

    def date(value):
        return datetime.date.fromisoformat(value).strftime("%d.%m.%Y")

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("LeaveBody", 7)
        canvas.setFillColor(colors.HexColor("#52646F"))
        canvas.drawString(48, 35, f"{reference}  |  {document.template_version}")
        canvas.drawRightString(A4[0] - 48, 35, f"Страница {doc.page}")
        canvas.restoreState()

    rows = [
        [p("До", label), p(f"{data['addressee']} на {data['employer_name']}")],
        [p("ЕИК", label), p(data["employer_eik"])],
        [p("Документ", label), p(reference)],
        [p("Дата на съставяне", label), p(date(data["prepared_date"]))],
        [p("Три имена", label), p(data["employee_name"])],
        [p("Служебен номер", label), p(data["personnel_number"])],
        [p("Длъжност", label), p(data["job_title"])],
    ]
    details = Table(rows, colWidths=[120, A4[0] - 216], hAlign="LEFT")
    details.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    # Escape all data as plain text; neither employee names nor template context
    # can inject ReportLab markup or external resources.
    text = render_to_string(
        "leaves/documents/bg_annual_request_v1.txt",
        {
            "start_date": date(data["start_date"]),
            "end_date": date(data["end_date"]),
            "working_days": data["working_days"],
        },
    ).strip()
    story = [
        p("ЗАЯВЛЕНИЕ", heading),
        p("за ползване на платен годишен отпуск"),
        Spacer(1, 20),
        details,
        Spacer(1, 22),
        p(
            f"{date(data['start_date'])} - {date(data['end_date'])}  |  "
            f"{data['working_days']} работни дни"
        ),
        Spacer(1, 14),
        p(text),
        Spacer(1, 30),
        KeepTogether(
            [
                p("Подпис на служителя:", label),
                Spacer(1, 40),
                p(data["employee_name"]),
            ]
        ),
    ]
    SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=48,
        bottomMargin=65,
        title="Заявление за платен годишен отпуск",
        author=data["employee_name"],
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
