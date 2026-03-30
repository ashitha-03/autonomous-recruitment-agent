"""
backend/services/pdf_generator.py
Generates professional PDF for Job Descriptions using ReportLab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import io


def generate_jd_pdf(jd: dict) -> bytes:
    """
    Generates a professional PDF for a Job Description.
    Returns PDF as bytes.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    # ── Colors ────────────────────────────────────────────────────────────────
    navy = HexColor('#0f1e3c')
    gold = HexColor('#f0c040')
    green = HexColor('#16a34a')
    blue = HexColor('#3b82f6')
    light_gray = HexColor('#f8fafc')
    dark_gray = HexColor('#374151')
    mid_gray = HexColor('#64748b')

    # ── Styles ─────────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=white,
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        fontName='Helvetica',
        fontSize=11,
        textColor=HexColor('#cbd5e1'),
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=navy,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=10,
        textColor=dark_gray,
        spaceAfter=4,
        leading=16,
        alignment=TA_JUSTIFY,
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        fontName='Helvetica',
        fontSize=10,
        textColor=dark_gray,
        spaceAfter=3,
        leftIndent=10,
        leading=15,
    )

    tag_style = ParagraphStyle(
        'Tag',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=green,
        alignment=TA_CENTER,
    )

    # ── Content ────────────────────────────────────────────────────────────────
    elements = []

    # Header banner
    header_data = [[
        Paragraph(jd.get('role_title', 'Job Description'), title_style),
    ]]
    header_table = Table(header_data, colWidths=[170*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), navy),
        ('PADDING', (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', [8]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # Subtitle info row
    dept = jd.get('department', '')
    company = jd.get('company_name', 'Our Company')
    subtitle_data = [[
        Paragraph(f"<b>{company}</b> • {dept}", subtitle_style),
    ]]
    subtitle_table = Table(subtitle_data, colWidths=[170*mm])
    subtitle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#1e3a6e')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(subtitle_table)
    elements.append(Spacer(1, 6*mm))

    # Info chips row
    chips_data = []
    chips = [
        ('📍', jd.get('location') or 'Location TBD'),
        ('💼', jd.get('employment_type') or 'Full-time'),
        ('🏠', jd.get('work_mode') or 'Hybrid'),
        ('⏱', f"{jd.get('experience_years', 0)}+ years"),
        ('💰', jd.get('salary_range') or 'Competitive'),
    ]

    chip_cells = []
    for icon, text in chips:
        chip_cells.append(
            Paragraph(f"{icon} {text}", ParagraphStyle(
                'Chip', fontName='Helvetica', fontSize=9,
                textColor=navy, alignment=TA_CENTER
            ))
        )

    chips_table = Table([chip_cells], colWidths=[34*mm]*5)
    chips_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0f4ff')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elements.append(chips_table)
    elements.append(Spacer(1, 6*mm))

    # Divider
    elements.append(HRFlowable(width="100%", thickness=2, color=gold))
    elements.append(Spacer(1, 4*mm))

    # Summary
    if jd.get('summary'):
        elements.append(Paragraph("About the Role", section_heading))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e2e8f0')))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(jd['summary'], body_style))
        elements.append(Spacer(1, 4*mm))

    # Responsibilities
    responsibilities = jd.get('responsibilities', '')
    if responsibilities:
        resp_list = [r.strip() for r in responsibilities.split(' | ') if r.strip()]
        if resp_list:
            elements.append(Paragraph("Key Responsibilities", section_heading))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=gold))
            elements.append(Spacer(1, 3*mm))
            for resp in resp_list:
                elements.append(Paragraph(f"▸  {resp}", bullet_style))
            elements.append(Spacer(1, 4*mm))

    # Required Skills
    required_skills = jd.get('required_skills', '')
    if required_skills:
        skills_list = [s.strip() for s in required_skills.split(',') if s.strip()]
        if skills_list:
            elements.append(Paragraph("Required Skills", section_heading))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=gold))
            elements.append(Spacer(1, 3*mm))

            # Skills in tag format
            cols = 4
            rows = [skills_list[i:i+cols] for i in range(0, len(skills_list), cols)]
            for row in rows:
                while len(row) < cols:
                    row.append('')
                skill_cells = []
                for skill in row:
                    if skill:
                        skill_cells.append(
                            Paragraph(f"✓ {skill}", ParagraphStyle(
                                'Skill', fontName='Helvetica-Bold', fontSize=9,
                                textColor=green, alignment=TA_CENTER
                            ))
                        )
                    else:
                        skill_cells.append(Paragraph('', body_style))

                skill_table = Table([skill_cells], colWidths=[42.5*mm]*cols)
                skill_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0fdf4')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#86efac')),
                    ('ROUNDEDCORNERS', [4]),
                ]))
                elements.append(skill_table)
                elements.append(Spacer(1, 2*mm))
            elements.append(Spacer(1, 4*mm))

    # Preferred Skills
    preferred_skills = jd.get('preferred_skills', '')
    if preferred_skills:
        pref_list = [s.strip() for s in preferred_skills.split(',') if s.strip()]
        if pref_list:
            elements.append(Paragraph("Nice to Have", section_heading))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#e2e8f0')))
            elements.append(Spacer(1, 3*mm))

            cols = 4
            rows = [pref_list[i:i+cols] for i in range(0, len(pref_list), cols)]
            for row in rows:
                while len(row) < cols:
                    row.append('')
                pref_cells = []
                for skill in row:
                    if skill:
                        pref_cells.append(
                            Paragraph(f"+ {skill}", ParagraphStyle(
                                'Pref', fontName='Helvetica', fontSize=9,
                                textColor=blue, alignment=TA_CENTER
                            ))
                        )
                    else:
                        pref_cells.append(Paragraph('', body_style))

                pref_table = Table([pref_cells], colWidths=[42.5*mm]*cols)
                pref_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0f4ff')),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#bfdbfe')),
                ]))
                elements.append(pref_table)
                elements.append(Spacer(1, 2*mm))
            elements.append(Spacer(1, 4*mm))

    # Footer
    elements.append(HRFlowable(width="100%", thickness=1, color=navy))
    elements.append(Spacer(1, 3*mm))

    footer_data = [[
        Paragraph(
            f"Generated by <b>RecruitAI</b> — Autonomous Recruitment Agent | "
            f"Posted: {jd.get('created_at', '')[:10] if jd.get('created_at') else 'Recently'}",
            ParagraphStyle('Footer', fontName='Helvetica', fontSize=8,
                          textColor=mid_gray, alignment=TA_CENTER)
        )
    ]]
    elements.append(Table(footer_data, colWidths=[170*mm]))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()