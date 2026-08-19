import os
import io
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

from analytics import (
    get_overall_summary,
    get_personal_analytics,
    get_division_analytics,
    get_post_performance
)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header line & title (pages > 1)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, 810, 559, 810)
            self.drawString(36, 815, "Laporan Analisis Interaksi Media Sosial Pegawai - Kanwil Kementerian Hukum Kepri")
        
        # Footer line & page numbers

        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, 40, 559, 40)
        
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M WIB")
        self.drawString(36, 28, f"Dicetak otomatis pada: {timestamp}")
        self.drawRightString(559, 28, f"Halaman {self._pageNumber} dari {page_count}")
        self.restoreState()


def generate_top_employees_chart(personal_data):
    top10 = personal_data[:10]
    if not top10:
        return None
        
    names = [emp['nama'][:18] + '...' if len(emp['nama']) > 18 else emp['nama'] for emp in reversed(top10)]
    likes = [emp['total_like'] for emp in reversed(top10)]
    komens = [emp['total_komen'] for emp in reversed(top10)]
    
    fig, ax = plt.subplots(figsize=(7.5, 3.5), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')
    
    y_pos = range(len(names))
    
    p1 = ax.barh(y_pos, likes, color='#6366f1', height=0.55, label='Total Like (IG+FB)')
    p2 = ax.barh(y_pos, komens, left=likes, color='#f59e0b', height=0.55, label='Total Komen (IG+FB)')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=8, fontweight='bold', color='#1e293b')
    ax.set_xlabel('Jumlah Interaksi (Like + Komen)', fontsize=9, fontweight='bold', color='#475569')
    ax.set_title('Top 10 Pegawai Interaksi Tertinggi', fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.legend(loc='lower right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=8)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_division_chart(division_data):
    if not division_data:
        return None
        
    divs = [d['divisi'].replace('DIVISI: ', '').replace('BAGIAN ', '') for d in division_data]
    likes = [d['total_like'] for d in division_data]
    komens = [d['total_komen'] for d in division_data]
    
    fig, ax = plt.subplots(figsize=(7.5, 3.2), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')
    
    import numpy as np
    x = np.arange(len(divs))
    width = 0.35
    
    rects1 = ax.bar(x - width/2, likes, width, label='Total Like', color='#4f46e5')
    rects2 = ax.bar(x + width/2, komens, width, label='Total Komen', color='#10b981')
    
    ax.set_ylabel('Jumlah Interaksi', fontsize=9, fontweight='bold', color='#475569')
    ax.set_title('Perbandingan Interaksi Per Divisi', fontsize=11, fontweight='bold', color='#0f172a', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(divs, rotation=15, ha='right', fontsize=8, fontweight='bold', color='#1e293b')
    ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=8)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.yaxis.grid(True, linestyle='--', alpha=0.5, color='#cbd5e1')
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_pdf_report(date_filter=None, divisi_filter=None, search_query=None):
    summary = get_overall_summary(date_filter)
    personal_data = get_personal_analytics(date_filter, divisi_filter, search_query)
    division_data = get_division_analytics(date_filter)
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        alignment=TA_CENTER
    )
    
    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#4338ca'),
        alignment=TA_CENTER
    )
    
    style_meta = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )
    
    style_section = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=12,
        spaceAfter=6
    )

    style_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    
    style_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )

    style_cell_header = ParagraphStyle(
        'TableHeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    story = []
    
    # Header Banner Block
    story.append(Paragraph("LAPORAN REKAPITULASI &amp; ANALISIS INTERAKSI MEDIA SOSIAL PEGAWAI", style_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("KANTOR WILAYAH KEMENTERIAN HUKUM KEPULAUAN RIAU", style_subtitle))
    story.append(Spacer(1, 4))

    
    date_str = f"Periode Audit: {date_filter}" if date_filter else "Periode Audit: Seluruh Batch"
    div_str = f" | Divisi: {divisi_filter}" if divisi_filter else ""
    story.append(Paragraph(f"{date_str}{div_str}", style_meta))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=12))
    
    # KPI Summary Cards Table
    kpi_data = [
        [
            Paragraph("<b>POST AUDITED</b>", ParagraphStyle('K1', parent=style_meta, textColor=colors.HexColor('#475569'))),
            Paragraph("<b>PEGAWAI TERDATA</b>", ParagraphStyle('K2', parent=style_meta, textColor=colors.HexColor('#475569'))),
            Paragraph("<b>TOTAL LIKES</b>", ParagraphStyle('K3', parent=style_meta, textColor=colors.HexColor('#475569'))),
            Paragraph("<b>TOTAL KOMEN</b>", ParagraphStyle('K4', parent=style_meta, textColor=colors.HexColor('#475569'))),
            Paragraph("<b>GRAND TOTAL</b>", ParagraphStyle('K5', parent=style_meta, textColor=colors.HexColor('#475569')))
        ],
        [
            Paragraph(f"<font size=13 color='#0f172a'><b>{summary['total_posts']}</b></font>", ParagraphStyle('V1', alignment=TA_CENTER)),
            Paragraph(f"<font size=13 color='#0f172a'><b>{summary['total_employees']}</b></font>", ParagraphStyle('V2', alignment=TA_CENTER)),
            Paragraph(f"<font size=13 color='#e11d48'><b>{summary['total_like']}</b></font><br/><font size=7 color='#64748b'>IG:{summary['total_ig_like']} FB:{summary['total_fb_like']}</font>", ParagraphStyle('V3', alignment=TA_CENTER)),
            Paragraph(f"<font size=13 color='#d97706'><b>{summary['total_komen']}</b></font><br/><font size=7 color='#64748b'>IG:{summary['total_ig_komen']} FB:{summary['total_fb_komen']}</font>", ParagraphStyle('V4', alignment=TA_CENTER)),
            Paragraph(f"<font size=13 color='#4338ca'><b>{summary['grand_total']}</b></font>", ParagraphStyle('V5', alignment=TA_CENTER))
        ]
    ]
    
    kpi_table = Table(kpi_data, colWidths=[104]*5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))
    
    # Section: Visual Charts
    story.append(Paragraph("1. Grafis Visualisasi Analisis Interaksi", style_section))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    
    buf_top_chart = generate_top_employees_chart(personal_data)
    buf_div_chart = generate_division_chart(division_data)
    
    charts_row = []
    if buf_top_chart:
        img1 = Image(buf_top_chart, width=255, height=125)
        charts_row.append(img1)
    if buf_div_chart:
        img2 = Image(buf_div_chart, width=255, height=125)
        charts_row.append(img2)
        
    if charts_row:
        chart_table = Table([charts_row], colWidths=[260, 260])
        chart_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(chart_table)
        story.append(Spacer(1, 14))
        
    # Section: Division Table Breakdown
    story.append(Paragraph("2. Rekapitulasi Performa Per Divisi", style_section))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    
    div_table_headers = [
        Paragraph("<b>NAMA DIVISI</b>", style_cell_header),
        Paragraph("<b>PEGAWAI</b>", style_cell_header),
        Paragraph("<b>TOTAL LIKE</b>", style_cell_header),
        Paragraph("<b>TOTAL KOMEN</b>", style_cell_header),
        Paragraph("<b>GRAND TOTAL</b>", style_cell_header)
    ]
    
    div_table_rows = [div_table_headers]
    for d in division_data:
        div_table_rows.append([
            Paragraph(f"<b>{d['divisi']}</b>", style_cell),
            Paragraph(str(d['total_pegawai']), ParagraphStyle('C1', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#e11d48'><b>{d['total_like']}</b></font>", ParagraphStyle('C2', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#d97706'><b>{d['total_komen']}</b></font>", ParagraphStyle('C3', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#4338ca'><b>{d['total_interaction']}</b></font>", ParagraphStyle('C4', parent=style_cell, alignment=TA_CENTER))
        ])
        
    div_table = Table(div_table_rows, colWidths=[200, 80, 80, 80, 80])
    div_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#312e81')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(div_table)
    story.append(Spacer(1, 14))
    
    # Section: Personal Data Table
    story.append(Paragraph("3. Detail Kuantitas Interaksi Personal Pegawai", style_section))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    
    pers_table_headers = [
        Paragraph("<b>NO</b>", style_cell_header),
        Paragraph("<b>NAMA PEGAWAI / JABATAN</b>", style_cell_header),
        Paragraph("<b>IG (L / K)</b>", style_cell_header),
        Paragraph("<b>FB (L / K)</b>", style_cell_header),
        Paragraph("<b>TOT LIKE</b>", style_cell_header),
        Paragraph("<b>TOT KOMEN</b>", style_cell_header),
        Paragraph("<b>GRAND TOTAL</b>", style_cell_header)
    ]
    
    pers_table_rows = [pers_table_headers]
    for idx, emp in enumerate(personal_data, 1):
        nama_p = f"<b>{emp['nama']}</b><br/><font size=7 color='#64748b'>{emp['jabatan'] or ''}</font>"
        ig_p = f"<font color='#e11d48'>{emp['ig_like']}</font> / <font color='#d97706'>{emp['ig_komen']}</font>"
        fb_p = f"<font color='#e11d48'>{emp['fb_like']}</font> / <font color='#d97706'>{emp['fb_komen']}</font>"
        
        pers_table_rows.append([
            Paragraph(str(idx), ParagraphStyle('CN', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(nama_p, style_cell),
            Paragraph(ig_p, ParagraphStyle('CIG', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(fb_p, ParagraphStyle('CFB', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#e11d48'><b>{emp['total_like']}</b></font>", ParagraphStyle('CTL', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#d97706'><b>{emp['total_komen']}</b></font>", ParagraphStyle('CTK', parent=style_cell, alignment=TA_CENTER)),
            Paragraph(f"<font color='#4338ca'><b>{emp['total_interaction']}</b></font>", ParagraphStyle('CGT', parent=style_cell, alignment=TA_CENTER))
        ])
        
    pers_table = Table(pers_table_rows, colWidths=[24, 218, 70, 70, 46, 46, 46])
    pers_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1b4b')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(pers_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer
