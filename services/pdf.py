"""PDF writer for the report.

make_pdf(report, question="", out_dir="storage/reports") -> path or None

Takes the Report (a dict or a Pydantic model) and builds a PDF for readers who are not experts:
a title block, the sections (sections that need review
carry a visible label, not only a colour), each chart placed next to the section that discusses it
with a plain-language explanation, and an evidence appendix with clickable source links.
It never raises: on any failure it prints the reason and returns None.

The PDF uses a standard font, so characters outside Latin-1 are replaced (the rupee sign is written "INR").
"""
import os
import re
from datetime import date
from typing import Optional
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

BLUE = colors.HexColor("#2F5597")
AMBER = colors.HexColor("#9C5700")
GREY = colors.HexColor("#595959")
FOOTER = "AI-generated draft - needs consultant review"
def _text(value) -> str:
    """Safe text for a standard PDF font."""
    s = str(value if value is not None else "").replace("₹", "INR ")
    return s.encode("cp1252", errors="replace").decode("cp1252")


def _p(value) -> str:
    return escape(_text(value))


def _as_dict(report) -> dict:
    if isinstance(report, dict):
        return report
    dump = getattr(report, "model_dump", None)
    return dump() if callable(dump) else {}


def _link(url: str, fallback: str) -> str:
    """Clickable site name for the appendix."""
    if not url:
        return _p(fallback)
    host = urlparse(url).netloc.replace("www.", "") or fallback
    return '<a href="%s" color="#2F5597">%s</a>' % (escape(url, {'"': "&quot;"}), _p(host))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, FOOTER)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, "Page %d" % doc.page)
    canvas.restoreState()


def _chart_image(path: str, width_cm: float = 13.5):
    """The picture at its own proportions."""
    w, h = ImageReader(path).getSize()
    return Image(path, width=width_cm * cm, height=width_cm * cm * h / w)


def make_pdf(report, question: str = "", out_dir: str = "storage/reports") -> Optional[str]:
    try:
        rep = _as_dict(report)
        if not rep.get("sections"):
            return None                      # nothing to print
        os.makedirs(out_dir, exist_ok=True)
        job = re.sub(r"[^A-Za-z0-9_.-]", "_", str(rep.get("job_id", "job_demo"))) or "job_demo"
        path = os.path.join(out_dir, job + ".pdf")

        base = getSampleStyleSheet()
        title = ParagraphStyle("T", parent=base["Title"], textColor=BLUE, fontSize=22, alignment=0)
        heading = ParagraphStyle("H", parent=base["Heading2"], textColor=BLUE, spaceBefore=14, spaceAfter=4, keepWithNext=1)
        sub = ParagraphStyle("Sub", parent=base["BodyText"], fontSize=10.5, leading=14, spaceBefore=4,
                             spaceAfter=2, fontName="Helvetica-Bold", keepWithNext=1)
        body = ParagraphStyle("B", parent=base["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)
        bullet = ParagraphStyle("Bul", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=4)
        review = ParagraphStyle("R", parent=body, textColor=AMBER)
        review_bullet = ParagraphStyle("RB", parent=bullet, textColor=AMBER)
        small = ParagraphStyle("S", parent=base["BodyText"], fontSize=8, leading=10)
        figure = ParagraphStyle("F", parent=base["BodyText"], fontSize=9, leading=12, textColor=GREY, spaceAfter=3)
        fig_title = ParagraphStyle("FT", parent=base["BodyText"], fontSize=10, leading=13, spaceBefore=6, spaceAfter=2,
                                   fontName="Helvetica-Bold", textColor=BLUE, keepWithNext=1)
        insight = ParagraphStyle("FI", parent=base["BodyText"], fontSize=9.5, leading=13, spaceAfter=4, keepWithNext=1)
        source = ParagraphStyle("FS", parent=base["BodyText"], fontSize=8, leading=10, textColor=GREY, spaceBefore=2, spaceAfter=10)

        story = [Paragraph("Market Research Brief", title)]
        if question:
            story.append(Paragraph(_p(question), body))
        story += [Paragraph("Generated on %s" % date.today().strftime("%d %B %Y"), small), Spacer(1, 8)]

        notes = [w for w in rep.get("warnings", []) if str(w).strip()]
        if notes:
            banner = Table([[[Paragraph("<b>Limited version of this report</b>", small)] +
                             [Paragraph("\u2022 " + _p(w), small) for w in notes]]], colWidths=[17 * cm])
            banner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF2CC")),
                                        ("BOX", (0, 0), (-1, -1), 0.6, AMBER),
                                        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            story += [banner, Spacer(1, 6)]

        charts = [c for c in rep.get("charts", []) if c.get("png_path") and os.path.exists(c["png_path"])]
        placed, figure_no = set(), [0]

        def chart_block(c):
            """Figure title, one insight sentence, the picture, then the source line, kept together."""
            figure_no[0] += 1
            lines = [x for x in str(c.get("description", "")).split("\n") if x.strip()]
            note = next((x for x in lines if x.startswith(("Source", "Sources"))), "")
            sentence = " ".join(x for x in lines if x != note)
            parts = [Paragraph("Figure %d: %s" % (figure_no[0], _p(c.get("title", ""))), fig_title)]
            if sentence:
                parts.append(Paragraph(_p(sentence), insight))
            parts.append(_chart_image(c["png_path"]))
            if note:
                parts.append(Paragraph(_p(note), source))
            else:
                parts.append(Spacer(1, 10))
            return [KeepTogether(parts)]

        for sec in rep.get("sections", []):
            needs = bool(sec.get("needs_review"))
            name = _p(sec.get("title", ""))
            tag = ' <font color="#9C5700" size="9">- needs human review</font>' if needs else ""
            story.append(Paragraph(name + tag, heading))
            keyterms = sec.get("title") == "Glossary"
            for para in str(sec.get("content", "")).split("\n"):
                para = para.strip()
                if not para:
                    continue
                if para.startswith("\u2022"):
                    text = para.lstrip("\u2022 ").strip()
                    if keyterms and " \u2013 " in text:
                        term, meaning = text.split(" \u2013 ", 1)
                        shown = "<b>%s</b> \u2013 %s" % (_p(term), _p(meaning))
                    else:
                        shown = _p(text)
                    story.append(Paragraph(shown, review_bullet if needs else bullet, bulletText="\u2022"))
                elif para.endswith(":") and len(para) < 30:
                    story.append(Paragraph(_p(para), sub))
                else:
                    story.append(Paragraph(_p(para), review if needs else body))
            for i, c in enumerate(charts):
                if c.get("section") == sec.get("title") and i not in placed:
                    story.extend(chart_block(c))
                    placed.add(i)

        rest = [c for i, c in enumerate(charts) if i not in placed]
        if rest:
            story.append(Paragraph("Charts", heading))
            for c in rest:
                story.extend(chart_block(c))

        appendix = rep.get("evidence_appendix", [])
        if appendix:
            story.append(CondPageBreak(6 * cm))
            story.append(Paragraph("Evidence Appendix", heading))
            story.append(Paragraph("Each row is a statement cited or listed in this report. The Status column shows whether it was confirmed or still needs review. Click the site name to open the source page.", figure))
            head = [Paragraph("<b>%s</b>" % h, small) for h in ("ID", "Statement", "Source", "Date", "Confidence", "Status")]
            rows = [head]
            for a in appendix:
                rows.append([
                    Paragraph(_p(a.get("id", "")), small),
                    Paragraph(_p(a.get("claim", "")), small),
                    Paragraph(_link(a.get("source_url", ""), a.get("source", "")), small),
                    Paragraph(_p(a.get("date", "")), small),
                    Paragraph("%.2f" % float(a.get("confidence") or 0), small),
                    Paragraph({"accepted": "Confirmed", "needs_review": "Needs review"}.get(a.get("status", ""), _p(a.get("status", ""))), small),
                ])
            table = Table(rows, colWidths=[1.0 * cm, 5.3 * cm, 4.5 * cm, 1.9 * cm, 2.0 * cm, 2.3 * cm], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBF7")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(table)

        doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm, title="Market Research Brief")
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return path
    except Exception as e:
        print(f"[pdf] failed: {type(e).__name__}: {e}")
        return None