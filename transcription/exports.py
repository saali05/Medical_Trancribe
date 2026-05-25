import io
import qrcode
import qrcode.image.pil
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, BaseDocTemplate, PageTemplate,
    Frame, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from django.http import HttpResponse

# ── Colors (matching the design) ─────────────────────────────────────────────
NAVY        = colors.HexColor('#1a3a6b')
NAVY_DARK   = colors.HexColor('#0f2347')
NAVY_LIGHT  = colors.HexColor('#e8eef7')
BLUE_MID    = colors.HexColor('#2563a8')
WHITE       = colors.white
LIGHT_GRAY  = colors.HexColor('#f4f6fb')
MID_GRAY    = colors.HexColor('#6b7280')
DARK_TEXT   = colors.HexColor('#1a1a2e')
BORDER      = colors.HexColor('#c5d3e8')
GOLD        = colors.HexColor('#d4af37')


def _make_qr(text, size=22):
    """Generate a QR code image and return as ReportLab Image."""
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a3a6b", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return Image(buf, width=size*mm, height=size*mm)


def _draw_page(c, doc):
    """Draw header, footer and decorative elements on every page."""
    w, h = A4

    # ── Top white header area ─────────────────────────────────────────────────
    c.setFillColor(WHITE)
    c.rect(0, h - 38*mm, w, 38*mm, fill=1, stroke=0)

    # Thin navy line under header
    c.setFillColor(NAVY)
    c.rect(0, h - 39.5*mm, w, 1.5*mm, fill=1, stroke=0)

    # Caduceus / logo area (navy square)
    c.setFillColor(NAVY)
    c.roundRect(12*mm, h - 34*mm, 18*mm, 18*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(21*mm, h - 24*mm, "+")

    # DocAI title
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(33*mm, h - 22*mm, "DocAI")
    c.setFillColor(BLUE_MID)
    c.setFont("Helvetica", 9)
    c.drawString(33*mm, h - 27*mm, "AI-Powered Medical Documentation")

    # Doctor info (right side)
    doctor_name = getattr(doc, 'doctor_name', 'Doctor')
    doctor_qual = getattr(doc, 'doctor_qual', 'MBBS, MD (Medicine)')
    doctor_reg  = getattr(doc, 'doctor_reg',  'Reg. No.: N/A')
    hospital    = getattr(doc, 'hospital',    '')

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(w - 12*mm, h - 18*mm, doctor_name.upper())
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK_TEXT)
    c.drawRightString(w - 12*mm, h - 23*mm, doctor_qual)
    c.drawRightString(w - 12*mm, h - 28*mm, "Attending Physician")
    c.drawRightString(w - 12*mm, h - 33*mm, doctor_reg)

    # ── Section title banner ──────────────────────────────────────────────────
    c.setFillColor(WHITE)
    c.rect(0, h - 49*mm, w, 9*mm, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.rect(10*mm, h - 48.5*mm, w - 20*mm, 7.5*mm, fill=0, stroke=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w/2, h - 45*mm, "CLINICAL PRESCRIPTION & SUMMARY")

    # Decorative dashes around title
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    c.line(14*mm, h - 44*mm, 55*mm, h - 44*mm)
    c.line(w - 55*mm, h - 44*mm, w - 14*mm, h - 44*mm)

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_y = 8*mm
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.5)
    c.line(10*mm, footer_y + 5*mm, w - 10*mm, footer_y + 5*mm)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(12*mm, footer_y + 2*mm, hospital or "DocAI Medical Center")

    c.setFillColor(MID_GRAY)
    c.setFont("Helvetica", 7)
    c.drawRightString(w - 12*mm, footer_y + 2*mm,
                      f"www.docai.health  |  Page {doc.page}")


class PremiumTemplate(BaseDocTemplate):
    def __init__(self, buffer, doctor_name="Doctor", doctor_qual="",
                 doctor_reg="", hospital="", **kwargs):
        super().__init__(buffer, **kwargs)
        self.doctor_name = doctor_name
        self.doctor_qual = doctor_qual
        self.doctor_reg  = doctor_reg
        self.hospital    = hospital
        frame = Frame(
            10*mm, 18*mm,
            A4[0] - 20*mm, A4[1] - 72*mm,
            leftPadding=0, rightPadding=0,
            topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(
            id='premium', frames=[frame], onPage=_draw_page
        )])


def _styles():
    s = getSampleStyleSheet()
    return {
        'info_label': ParagraphStyle('IL',
            fontSize=8, fontName='Helvetica-Bold',
            textColor=NAVY),
        'info_value': ParagraphStyle('IV',
            fontSize=9, fontName='Helvetica',
            textColor=DARK_TEXT),
        'section_header': ParagraphStyle('SHD',
            fontSize=9, fontName='Helvetica-Bold',
            textColor=WHITE, alignment=TA_CENTER),
        'field_label': ParagraphStyle('FL',
            fontSize=9, fontName='Helvetica-Bold',
            textColor=NAVY, leading=13),
        'field_value': ParagraphStyle('FV',
            fontSize=9, fontName='Helvetica',
            textColor=DARK_TEXT, leading=13),
        'not_mentioned': ParagraphStyle('NM',
            fontSize=8, fontName='Helvetica-Oblique',
            textColor=MID_GRAY),
        'footer_label': ParagraphStyle('FTL',
            fontSize=8, fontName='Helvetica-Bold',
            textColor=NAVY),
        'footer_value': ParagraphStyle('FTV',
            fontSize=8, fontName='Helvetica',
            textColor=DARK_TEXT),
        'advice_item': ParagraphStyle('AI',
            fontSize=8, fontName='Helvetica',
            textColor=DARK_TEXT, leading=13),
        'notes': ParagraphStyle('NT',
            fontSize=8, fontName='Helvetica',
            textColor=DARK_TEXT, leading=12),
        'disclaimer': ParagraphStyle('DS',
            fontSize=7, fontName='Helvetica-Oblique',
            textColor=MID_GRAY, alignment=TA_CENTER),
    }


def _val(value, s):
    if value and value.strip() and value.strip().lower() != "not mentioned":
        return Paragraph(value, s['field_value'])
    return Paragraph("—", s['not_mentioned'])


def _icon_label(icon_text, label, s):
    """Label with inline icon character."""
    return Paragraph(f"{icon_text}  <b>{label}</b>", s['field_label'])


def _build_pdf(buffer, patient_name, record_id, created_at, fields,
               doctor_name="Doctor", doctor_qual="MBBS, MD (Medicine)",
               doctor_reg="", hospital="", patient_age="",
               patient_gender="", patient_contact=""):

    doc = PremiumTemplate(
        buffer,
        doctor_name=doctor_name,
        doctor_qual=doctor_qual,
        doctor_reg=doctor_reg,
        hospital=hospital,
        pagesize=A4,
        rightMargin=10*mm, leftMargin=10*mm,
        topMargin=52*mm, bottomMargin=20*mm,
    )

    s = _styles()
    W = A4[0] - 20*mm
    story = []

    # ── Patient Info Box ──────────────────────────────────────────────────────
    info_rows = [
        [
            Paragraph("👤  PATIENT NAME", s['info_label']),
            Paragraph(f":  {patient_name}", s['info_value']),
            Paragraph("🗒  RECORD NUMBER", s['info_label']),
            Paragraph(f":  {record_id:05d}", s['info_value']),
        ],
        [
            Paragraph("📅  AGE / GENDER", s['info_label']),
            Paragraph(f":  {patient_age or '—'} / {patient_gender or '—'}", s['info_value']),
            Paragraph("📅  DATE", s['info_label']),
            Paragraph(f":  {created_at.strftime('%d %b %Y')}", s['info_value']),
        ],
        [
            Paragraph("📞  CONTACT", s['info_label']),
            Paragraph(f":  {patient_contact or '—'}", s['info_value']),
            Paragraph("🕐  TIME", s['info_label']),
            Paragraph(f":  {created_at.strftime('%I:%M %p')}", s['info_value']),
        ],
    ]

    col_w = [38*mm, 52*mm, 38*mm, 52*mm]
    info_tbl = Table(info_rows, colWidths=col_w)
    info_tbl.setStyle(TableStyle([
        ('BOX',          (0, 0), (-1, -1), 1, NAVY),
        ('INNERGRID',    (0, 0), (-1, -1), 0.3, BORDER),
        ('BACKGROUND',   (0, 0), (-1, -1), LIGHT_GRAY),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Clinical Summary Header ───────────────────────────────────────────────
    header_tbl = Table(
        [[Paragraph("CLINICAL SUMMARY", s['section_header'])]],
        colWidths=[W]
    )
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), NAVY),
        ('TOPPADDING',   (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
    ]))
    story.append(header_tbl)

    # ── Clinical Fields ───────────────────────────────────────────────────────
    icons = {
        "Chief Complaint":      "👤",
        "History":              "📋",
        "Present Illness":      "📋",
        "Examination":          "🩺",
        "Tests":                "🔬",
        "Diagnosis":            "Rx",
        "Prescription":         "💊",
        "Treatment Plan":       "📝",
        "Follow Up":            "📅",
        "Vitals":               "❤",
        "Past Medical History": "📋",
    }

    col_label = 45*mm
    col_value = W - col_label

    for label, value in fields.items():
        safe = value[:500] + '...' if value and len(value) > 500 else value
        icon = icons.get(label, "•")
        row = [[_icon_label(icon, label.upper(), s), _val(safe, s)]]
        tbl = Table(row, colWidths=[col_label, col_value])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (0, 0), NAVY_LIGHT),
            ('BACKGROUND',    (1, 0), (1, 0), WHITE),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 8),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
            ('LINEBELOW',     (0, 0), (-1, -1), 0.5, BORDER),
            ('BOX',           (0, 0), (-1, -1), 0.5, BORDER),
            ('LINEAFTER',     (0, 0), (0, -1), 0.5, NAVY),
        ]))
        story.append(tbl)

    story.append(Spacer(1, 4*mm))

    # ── Notes Box ────────────────────────────────────────────────────────────
    notes_row = [[
        Paragraph("🗒", s['field_label']),
        Paragraph(
            "<b>NOTES</b><br/>"
            "This document was generated by DocAI using AI transcription and is intended "
            "for clinical reference only. Please verify all information with the treating physician.",
            s['notes']
        )
    ]]
    notes_tbl = Table(notes_row, colWidths=[10*mm, W - 10*mm])
    notes_tbl.setStyle(TableStyle([
        ('BOX',          (0, 0), (-1, -1), 0.8, NAVY),
        ('BACKGROUND',   (0, 0), (-1, -1), NAVY_LIGHT),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 8),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    story.append(notes_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Bottom 3-column: Advice | Signature | QR ─────────────────────────────
    # Advice
    advice_items = [
        "Take medications as prescribed.",
        "Drink plenty of fluids and rest.",
        "Avoid cold exposure and spicy food.",
        "Seek immediate medical attention if symptoms worsen.",
    ]
    advice_content = [
        Paragraph("<b>DOCTOR'S ADVICE</b>", s['footer_label']),
        Spacer(1, 2*mm),
    ] + [Paragraph(f"• {item}", s['advice_item']) for item in advice_items]

    # Signature block
    sig_content = [
        Paragraph("<b>DOCTOR'S SIGNATURE</b>", s['footer_label']),
        Spacer(1, 8*mm),
        Paragraph("<i>_______________________</i>", s['notes']),
        Spacer(1, 2*mm),
        Paragraph(f"<b>{doctor_name}</b>", s['footer_label']),
        Paragraph(doctor_qual, s['footer_value']),
        Paragraph("Attending Physician", s['footer_value']),
        Paragraph(doctor_reg, s['footer_value']),
    ]

    # QR code
    qr_label = f"DocAI Record #{record_id:05d} | {patient_name} | {created_at.strftime('%d %b %Y')}"
    try:
        qr_img = _make_qr(qr_label, size=24)
        qr_content = [
            qr_img,
            Spacer(1, 2*mm),
            Paragraph("Scan to Verify", s['footer_value']),
            Paragraph(f"Record #{record_id:05d}", s['footer_value']),
        ]
    except Exception:
        qr_content = [Paragraph(f"Record #{record_id:05d}", s['footer_value'])]

    bottom_col_w = [W * 0.40, W * 0.35, W * 0.25]

    def _wrap(items):
        rows = [[item] for item in items]
        t = Table(rows, colWidths=[bottom_col_w[0]])
        t.setStyle(TableStyle([
            ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING',  (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING',   (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
        ]))
        return t

    bottom_data = [[
        Table([[item] for item in advice_content],
              colWidths=[bottom_col_w[0]],
              style=[('VALIGN',(0,0),(-1,-1),'TOP'),
                     ('TOPPADDING',(0,0),(-1,-1),1),
                     ('BOTTOMPADDING',(0,0),(-1,-1),1),
                     ('LEFTPADDING',(0,0),(-1,-1),0),
                     ('RIGHTPADDING',(0,0),(-1,-1),0)]),
        Table([[item] for item in sig_content],
              colWidths=[bottom_col_w[1]],
              style=[('VALIGN',(0,0),(-1,-1),'TOP'),
                     ('TOPPADDING',(0,0),(-1,-1),1),
                     ('BOTTOMPADDING',(0,0),(-1,-1),1),
                     ('LEFTPADDING',(0,0),(-1,-1),0),
                     ('RIGHTPADDING',(0,0),(-1,-1),0)]),
        Table([[item] for item in qr_content],
              colWidths=[bottom_col_w[2]],
              style=[('VALIGN',(0,0),(-1,-1),'TOP'),
                     ('ALIGN',(0,0),(-1,-1),'CENTER'),
                     ('TOPPADDING',(0,0),(-1,-1),1),
                     ('BOTTOMPADDING',(0,0),(-1,-1),1),
                     ('LEFTPADDING',(0,0),(-1,-1),0),
                     ('RIGHTPADDING',(0,0),(-1,-1),0)]),
    ]]

    bottom_tbl = Table(bottom_data, colWidths=bottom_col_w)
    bottom_tbl.setStyle(TableStyle([
        ('BOX',         (0, 0), (-1, -1), 0.8, NAVY),
        ('LINEBEFORE',  (1, 0), (1, -1), 0.5, BORDER),
        ('LINEBEFORE',  (2, 0), (2, -1), 0.5, BORDER),
        ('VALIGN',      (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',  (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0,0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',(0, 0), (-1, -1), 8),
        ('BACKGROUND',  (0, 0), (-1, -1), LIGHT_GRAY),
    ]))
    story.append(bottom_tbl)

    doc.build(story)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf(doc):
    try:
        user = doc.transcript.audio.doctor
        doctor_name = f"Dr. {user.get_full_name() or user.username}"
    except Exception:
        doctor_name = "Doctor"

    buf = io.BytesIO()
    _build_pdf(
        buffer=buf,
        patient_name=doc.patient_name or "Unknown Patient",
        record_id=doc.pk,
        created_at=doc.created_at,
        doctor_name=doctor_name,
        patient_age=transcription.patient_age or '',
        patient_gender=transcription.patient_gender or '',
        patient_contact=transcription.patient_contact or '',
        fields={
            "Chief Complaint": doc.chief_complaint,
            "History":         doc.history,
            "Examination":     doc.examination,
            "Diagnosis":       doc.diagnosis,
            "Prescription":    doc.prescription,
            "Treatment Plan":  doc.treatment_plan,
            "Follow Up":       doc.follow_up,
        },
    )
    buf.seek(0)
    return buf.read()


def export_transcription_pdf(transcription, user=None):
    """Transcription -> HttpResponse PDF download."""
    if user:
        doctor_name = f"Dr. {user.get_full_name() or user.username}"
    else:
        doctor_name = "Doctor"

    buf = io.BytesIO()
    _build_pdf(
        buffer=buf,
        patient_name=transcription.patient_name or "Unknown Patient",
        record_id=transcription.id,
        created_at=transcription.created_at,
        doctor_name=doctor_name,
        # ↓↓↓ THESE 3 LINES ARE MISSING — ADD THEM ↓↓↓
        patient_age=transcription.patient_age or '',
        patient_gender=transcription.patient_gender or '',
        patient_contact=transcription.patient_contact or '',
        fields={
            "Chief Complaint":      transcription.chief_complaint,
            "Present Illness":      transcription.present_illness,
            "Diagnosis":            transcription.diagnosis,
            "Prescription":         transcription.prescription,
            "Treatment Plan":       transcription.treatment_plan,
            "Follow Up":            transcription.follow_up,
            "Vitals":               transcription.vitals,
            "Past Medical History": transcription.past_medical_history,
        },
    )
    buf.seek(0)

    patient  = (transcription.patient_name or "patient").replace(" ", "_").lower()
    date_str = transcription.created_at.strftime("%Y%m%d")
    filename = f"DocAI_{patient}_{date_str}_{transcription.id:05d}.pdf"
    response = HttpResponse(buf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response