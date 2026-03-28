"""
PDF Export
==========
Export BRD to professional PDF format.

Uses reportlab for PDF generation with custom templates.
Falls back to HTML-based export if reportlab not available.
"""

import io
import html
from datetime import datetime
from typing import Optional


def _check_reportlab():
    """Check if reportlab is available."""
    try:
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        return True
    except ImportError:
        return False


def export_to_pdf(brd_data: dict, output_path: Optional[str] = None) -> bytes:
    """
    Export BRD data to PDF format.
    
    Args:
        brd_data: The BRD extraction result dictionary
        output_path: Optional file path to save PDF (if None, returns bytes)
        
    Returns:
        PDF content as bytes
    """
    if _check_reportlab():
        return _export_with_reportlab(brd_data, output_path)
    else:
        return _export_html_fallback(brd_data, output_path)


def _export_with_reportlab(brd_data: dict, output_path: Optional[str] = None) -> bytes:
    """Export using reportlab library."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'BRDTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        textColor=colors.HexColor('#1a365d'),
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=20,
        textColor=colors.HexColor('#2d3748'),
        borderWidth=1,
        borderColor=colors.HexColor('#e2e8f0'),
        borderPadding=5,
    )
    
    body_style = ParagraphStyle(
        'BRDBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )
    
    story = []
    
    # Title
    project_name = brd_data.get('project_name', 'Business Requirements Document')
    story.append(Paragraph(project_name, title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 20))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", section_style))
    fr_count = len(brd_data.get('functional_reqs', []))
    nfr_count = len(brd_data.get('nfrs', []))
    stakeholder_count = len(brd_data.get('stakeholders', []))
    decision_count = len(brd_data.get('decisions', []))
    completeness = brd_data.get('completeness_score', 0) * 100
    
    summary_text = f"""
    This document contains {fr_count} functional requirements, {nfr_count} non-functional requirements,
    {stakeholder_count} identified stakeholders, and {decision_count} recorded decisions.
    Document completeness score: {completeness:.0f}%
    """
    story.append(Paragraph(summary_text.strip(), body_style))
    story.append(Spacer(1, 15))
    
    # Functional Requirements
    frs = brd_data.get('functional_reqs', [])
    if frs:
        story.append(Paragraph("Functional Requirements", section_style))
        
        table_data = [['ID', 'Requirement', 'Priority', 'MoSCoW', 'Confidence']]
        for req in frs:
            table_data.append([
                req.get('id', ''),
                Paragraph(req.get('text', '')[:100], body_style),
                str(req.get('priority', '')),
                req.get('moscow', ''),
                f"{req.get('confidence', 0):.0%}",
            ])
        
        table = Table(table_data, colWidths=[0.7*inch, 3.5*inch, 0.6*inch, 0.7*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Non-Functional Requirements
    nfrs = brd_data.get('nfrs', [])
    if nfrs:
        story.append(Paragraph("Non-Functional Requirements", section_style))
        
        table_data = [['ID', 'Requirement', 'Category', 'Confidence']]
        for req in nfrs:
            table_data.append([
                req.get('id', ''),
                Paragraph(req.get('text', '')[:120], body_style),
                req.get('category', ''),
                f"{req.get('confidence', 0):.0%}",
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 4*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Stakeholders
    stakeholders = brd_data.get('stakeholders', [])
    if stakeholders:
        story.append(Paragraph("Stakeholders", section_style))
        
        table_data = [['Name', 'Role', 'Influence', 'Mentions']]
        for sh in stakeholders:
            table_data.append([
                sh.get('name', ''),
                sh.get('role', ''),
                f"{sh.get('influence_score', 0):.0%}",
                str(sh.get('mentioned_count', 0)),
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
    
    # Decisions
    decisions = brd_data.get('decisions', [])
    if decisions:
        story.append(Paragraph("Key Decisions", section_style))
        
        for dec in decisions:
            story.append(Paragraph(f"<b>{dec.get('id', '')}:</b> {dec.get('text', '')}", body_style))
            if dec.get('rationale'):
                story.append(Paragraph(f"<i>Rationale: {dec.get('rationale')}</i>", body_style))
            story.append(Spacer(1, 6))
    
    # Scope
    scope = brd_data.get('scope', {})
    if any(scope.values()):
        story.append(Paragraph("Scope", section_style))
        
        if scope.get('in_scope'):
            story.append(Paragraph("<b>In Scope:</b>", body_style))
            for item in scope['in_scope']:
                story.append(Paragraph(f"• {item}", body_style))
        
        if scope.get('out_of_scope'):
            story.append(Paragraph("<b>Out of Scope:</b>", body_style))
            for item in scope['out_of_scope']:
                story.append(Paragraph(f"• {item}", body_style))
        
        if scope.get('assumptions'):
            story.append(Paragraph("<b>Assumptions:</b>", body_style))
            for item in scope['assumptions']:
                story.append(Paragraph(f"• {item}", body_style))
    
    # Gaps (if any)
    gaps = brd_data.get('gaps', [])
    if gaps:
        story.append(Paragraph("Identified Gaps", section_style))
        for gap in gaps:
            severity = gap.get('severity', 'medium')
            color = '#e53e3e' if severity == 'critical' else '#dd6b20' if severity == 'high' else '#718096'
            story.append(Paragraph(
                f"<font color='{color}'>[{severity.upper()}]</font> {gap.get('gap', '')}",
                body_style
            ))
            if gap.get('suggestion'):
                story.append(Paragraph(f"<i>Suggestion: {gap.get('suggestion')}</i>", body_style))
    
    # Dynamic Domain Sections (ApexBRD+)
    domain_data = brd_data.get('domain_data', {})
    if domain_data and domain_data.get('sections'):
        domain_name = brd_data.get('domain', 'Industrial').capitalize()
        story.append(Paragraph(f"{domain_name} Domain Extraction", section_style))
        
        for section_title, items in domain_data['sections'].items():
            if not items:
                continue
                
            story.append(Paragraph(section_title, ParagraphStyle(
                'SubSection', parent=body_style, fontSize=12, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5
            )))
            
            for item in items:
                title = item.get('title') or item.get('name') or item.get('objective', 'Requirement')
                desc = item.get('description') or item.get('requirement') or item.get('specification', '')
                priority = item.get('priority', '')
                
                p_text = f"<b>{title}</b>"
                if priority:
                    p_text += f" <font color='#4a5568'>[{priority}]</font>"
                
                story.append(Paragraph(p_text, body_style))
                if desc:
                    story.append(Paragraph(desc, ParagraphStyle('ItemDesc', parent=body_style, leftIndent=20)))
                
                if item.get('mitigation'):
                    story.append(Paragraph(f"<i>Mitigation: {item.get('mitigation')}</i>", ParagraphStyle('Mitigation', parent=body_style, leftIndent=20, textColor=colors.HexColor('#af2b21'))))
                    
                story.append(Spacer(1, 4))
        
        # Domain scores
        scores = domain_data.get('domain_scores', {})
        if scores:
            story.append(Spacer(1, 10))
            story.append(Paragraph("Domain Performance Metrics", ParagraphStyle('ScoreHeader', parent=body_style, fontSize=11, fontName='Helvetica-Bold')))
            
            for s_name, s_val in scores.items():
                val = s_val.get('value', 0) if isinstance(s_val, dict) else s_val
                rat = s_val.get('rationale', '') if isinstance(s_val, dict) else ''
                story.append(Paragraph(f"• {s_name.replace('_', ' ').title()}: {val:.1%} - {rat}", body_style))

    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
    
    return pdf_bytes


def _export_html_fallback(brd_data: dict, output_path: Optional[str] = None) -> bytes:
    """Fallback export using HTML (can be printed to PDF by browser)."""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Business Requirements Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a365d; border-bottom: 2px solid #4a5568; padding-bottom: 10px; }}
        h2 {{ color: #2d3748; background: #f7fafc; padding: 10px; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th {{ background: #4a5568; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border: 1px solid #e2e8f0; }}
        tr:nth-child(even) {{ background: #f7fafc; }}
        .critical {{ color: #e53e3e; font-weight: bold; }}
        .high {{ color: #dd6b20; }}
        .meta {{ color: #718096; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{html.escape(brd_data.get('project_name', 'Business Requirements Document'))}</h1>
    <p class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    
    <h2>Executive Summary</h2>
    <p>
        This document contains <strong>{len(brd_data.get('functional_reqs', []))}</strong> functional requirements,
        <strong>{len(brd_data.get('nfrs', []))}</strong> non-functional requirements,
        <strong>{len(brd_data.get('stakeholders', []))}</strong> stakeholders, and
        <strong>{len(brd_data.get('decisions', []))}</strong> decisions.
    </p>
    <p>Completeness Score: <strong>{brd_data.get('completeness_score', 0) * 100:.0f}%</strong></p>
"""
    
    # Functional Requirements
    frs = brd_data.get('functional_reqs', [])
    if frs:
        html_content += """
    <h2>Functional Requirements</h2>
    <table>
        <tr><th>ID</th><th>Requirement</th><th>Priority</th><th>MoSCoW</th><th>Confidence</th></tr>
"""
        for req in frs:
            html_content += f"""
        <tr>
            <td>{html.escape(req.get('id', ''))}</td>
            <td>{html.escape(req.get('text', ''))}</td>
            <td>{req.get('priority', '')}</td>
            <td>{html.escape(req.get('moscow', ''))}</td>
            <td>{req.get('confidence', 0):.0%}</td>
        </tr>
"""
        html_content += "    </table>\n"
    
    # NFRs
    nfrs = brd_data.get('nfrs', [])
    if nfrs:
        html_content += """
    <h2>Non-Functional Requirements</h2>
    <table>
        <tr><th>ID</th><th>Requirement</th><th>Category</th><th>Confidence</th></tr>
"""
        for req in nfrs:
            html_content += f"""
        <tr>
            <td>{html.escape(req.get('id', ''))}</td>
            <td>{html.escape(req.get('text', ''))}</td>
            <td>{html.escape(req.get('category', ''))}</td>
            <td>{req.get('confidence', 0):.0%}</td>
        </tr>
"""
        html_content += "    </table>\n"
    
    # Stakeholders
    stakeholders = brd_data.get('stakeholders', [])
    if stakeholders:
        html_content += """
    <h2>Stakeholders</h2>
    <table>
        <tr><th>Name</th><th>Role</th><th>Influence</th><th>Mentions</th></tr>
"""
        for sh in stakeholders:
            html_content += f"""
        <tr>
            <td>{html.escape(sh.get('name', ''))}</td>
            <td>{html.escape(sh.get('role', ''))}</td>
            <td>{sh.get('influence_score', 0):.0%}</td>
            <td>{sh.get('mentioned_count', 0)}</td>
        </tr>
"""
        html_content += "    </table>\n"
    
    # Decisions
    decisions = brd_data.get('decisions', [])
    if decisions:
        html_content += "    <h2>Key Decisions</h2>\n"
        for dec in decisions:
            html_content += f"    <p><strong>{html.escape(dec.get('id', ''))}:</strong> {html.escape(dec.get('text', ''))}</p>\n"
            if dec.get('rationale'):
                html_content += f"    <p><em>Rationale: {html.escape(dec.get('rationale'))}</em></p>\n"
    
    html_content += """
</body>
</html>
"""
    
    content_bytes = html_content.encode('utf-8')
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(content_bytes)
    
    return content_bytes


if __name__ == "__main__":
    # Test export
    test_data = {
        "project_name": "Test BRD Export",
        "functional_reqs": [
            {"id": "FR-001", "text": "User authentication via SSO", "priority": 1, "moscow": "Must", "confidence": 0.95},
            {"id": "FR-002", "text": "Payment processing with Stripe", "priority": 1, "moscow": "Must", "confidence": 0.90},
        ],
        "nfrs": [
            {"id": "NFR-001", "text": "Response time under 200ms", "category": "Performance", "confidence": 0.88},
        ],
        "stakeholders": [
            {"name": "John Smith", "role": "Product Manager", "influence_score": 0.9, "mentioned_count": 5},
        ],
        "decisions": [
            {"id": "DEC-001", "text": "Use PostgreSQL for database", "rationale": "Better JSON support"},
        ],
        "completeness_score": 0.85,
    }
    
    print(f"reportlab available: {_check_reportlab()}")
    
    pdf_bytes = export_to_pdf(test_data)
    print(f"Generated PDF: {len(pdf_bytes)} bytes")
