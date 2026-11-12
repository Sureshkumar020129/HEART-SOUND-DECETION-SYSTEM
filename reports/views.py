"""Reports: PDF generation and download."""
import io
import logging
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from heart_analysis.models import AnalysisRecord

logger = logging.getLogger(__name__)


@login_required
def download_report(request, pk):
    """Generate and serve a PDF report for the given analysis."""
    analysis = get_object_or_404(AnalysisRecord, pk=pk, user=request.user)

    if analysis.status not in ('completed', 'model_unavailable'):
        raise Http404("Report not available for this analysis status.")

    prediction = getattr(analysis, 'prediction', None)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Heart Sound Analysis Report — {analysis.id}",
    )

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle('Title', parent=styles['Title'],
                                  fontSize=20, spaceAfter=12, textColor=colors.HexColor('#1a365d'))
    heading_style = ParagraphStyle('Heading2', parent=styles['Heading2'],
                                    fontSize=13, textColor=colors.HexColor('#2b6cb0'), spaceAfter=6)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                   fontSize=10, leading=14, spaceAfter=4)
    disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'],
                                       fontSize=9, leading=12, textColor=colors.HexColor('#c53030'),
                                       backColor=colors.HexColor('#fff5f5'),
                                       borderPadding=(6, 6, 6, 6))
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')

    story = []

    # Header
    story.append(Paragraph("HeartSound AI", ParagraphStyle('Logo', parent=styles['Title'],
                                                             fontSize=14, textColor=colors.HexColor('#2b6cb0'))))
    story.append(Paragraph("Heart Sound Analysis Report", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2b6cb0')))
    story.append(Spacer(1, 0.5*cm))

    # Analysis metadata
    story.append(Paragraph("Analysis Information", heading_style))
    meta_data = [
        ['Analysis ID:', str(analysis.id)],
        ['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M UTC')],
        ['Analysis Date:', analysis.created_at.strftime('%Y-%m-%d %H:%M UTC')],
        ['Status:', analysis.get_status_display()],
        ['Original File:', analysis.recording.original_filename or 'Browser Recording'],
        ['Recording Duration:', f"{analysis.recording.duration_seconds:.2f}s" if analysis.recording.duration_seconds else 'N/A'],
        ['Sample Rate:', f"{analysis.recording.sample_rate} Hz" if analysis.recording.sample_rate else 'N/A'],
    ]
    if analysis.processing_duration_ms:
        meta_data.append(['Processing Time:', f"{analysis.processing_duration_ms} ms"])

    table = Table(meta_data, colWidths=[5*cm, 12*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2d3748')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#ebf8ff')]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#bee3f8')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    # Prediction Results
    story.append(Paragraph("Model Classification", heading_style))
    if prediction:
        result_color = {
            'normal': colors.HexColor('#276749'),
            'abnormal': colors.HexColor('#c53030'),
            'uncertain': colors.HexColor('#744210'),
            'model_unavailable': colors.HexColor('#2d3748'),
        }.get(prediction.classification, colors.HexColor('#2d3748'))

        result_data = [
            ['Model Name:', prediction.model_name],
            ['Model Version:', prediction.model_version],
            ['Classification:', prediction.classification.upper()],
        ]
        if prediction.confidence_score is not None:
            result_data.append(['Confidence Score:', f"{prediction.confidence_score:.1%}"])
        if prediction.raw_scores:
            for cls, score in prediction.raw_scores.items():
                result_data.append([f'  P({cls}):', f"{score:.4f}"])

        result_table = Table(result_data, colWidths=[5*cm, 12*cm])
        result_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (1, 2), (1, 2), result_color),
            ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 2), (1, 2), 12),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(result_table)
    else:
        story.append(Paragraph("No prediction result available for this analysis.", normal_style))

    story.append(Spacer(1, 0.5*cm))

    # Analysis error (if any)
    if analysis.error_message:
        story.append(Paragraph("Processing Notes", heading_style))
        story.append(Paragraph(analysis.error_message[:1000], normal_style))
        story.append(Spacer(1, 0.3*cm))

    # Medical disclaimer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#fc8181')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("⚠ Important Medical Disclaimer", heading_style))
    disclaimer_text = (
        prediction.disclaimer if prediction else
        "This report is produced by a research machine-learning system and is NOT a clinical diagnosis. "
        "Always consult a qualified healthcare professional for medical evaluation."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    story.append(Spacer(1, 0.3*cm))

    # Next steps
    story.append(Paragraph("Recommended Next Steps", heading_style))
    next_steps = [
        "• Consult a qualified cardiologist or general practitioner for professional auscultation.",
        "• If you experience chest pain, shortness of breath, or fainting, seek emergency care immediately.",
        "• This tool is intended for educational and research screening purposes only.",
        "• Do not make any changes to medication or treatment based on this report.",
    ]
    for step in next_steps:
        story.append(Paragraph(step, normal_style))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Generated by HeartSound AI v{getattr(settings, 'SITE_VERSION', '1.0.0')} "
        f"| {timezone.now().strftime('%Y-%m-%d %H:%M UTC')} | Research Use Only",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#718096'), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="heartsound_report_{analysis.id}.pdf"'
    return response
