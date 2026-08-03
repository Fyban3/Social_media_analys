import re
import os
import pdfplumber

def parse_audit_pdf(file_path):
    """
    Parses a single Social Media Audit PDF file.
    Returns metadata and list of employee interactions.
    """
    filename = os.path.basename(file_path)
    post_title = filename.replace('Rekap_', '').replace('.pdf', '').strip()
    
    audit_date = ""
    total_pegawai = 0
    ig_url = ""
    fb_url = ""
    employees = []
    
    current_divisi = "LAINNYA"
    
    with pdfplumber.open(file_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            if page_idx == 0:
                m_date = re.search(r'TANGGAL AUDIT:\s*(\d{4}-\d{2}-\d{2})', text)
                if m_date:
                    audit_date = m_date.group(1)
                    
                m_tot = re.search(r'TOTAL PEGAWAI:\s*(\d+)', text)
                if m_tot:
                    total_pegawai = int(m_tot.group(1))
                    
                m_ig = re.search(r'TARGET IG POST:\s*(\S+)', text)
                if m_ig:
                    ig_url = m_ig.group(1)
                    
                m_fb = re.search(r'TARGET FB POST:\s*(\S+)', text)
                if m_fb:
                    fb_url = m_fb.group(1)

            tables = page.extract_tables()
            for t in tables:
                for row in t:
                    if not row:
                        continue
                    
                    row_str = ' '.join([str(cell) for cell in row if cell])
                    
                    # Check division row header
                    if 'DIVISI:' in row_str:
                        current_divisi = row_str.replace('DIVISI:', '').strip()
                        continue
                    
                    # Check if row is an employee data row (starts with integer NO)
                    if row[0] and str(row[0]).strip().isdigit():
                        no = str(row[0]).strip()
                        nama = str(row[1]).replace('\n', ' ').strip() if len(row) > 1 and row[1] else ''
                        jabatan = str(row[2]).replace('\n', ' ').strip() if len(row) > 2 and row[2] else ''
                        
                        # Interaction columns
                        # row[3] = IG Like, row[4] = IG Komen, row[5] = IG Share
                        # row[6] = FB Like, row[7] = FB Komen, row[8] = FB Share
                        ig_like = str(row[3]).strip() if len(row) > 3 and row[3] else '-'
                        ig_komen = str(row[4]).strip() if len(row) > 4 and row[4] else '-'
                        ig_share = str(row[5]).strip() if len(row) > 5 and row[5] else '-'
                        
                        fb_like = str(row[6]).strip() if len(row) > 6 and row[6] else '-'
                        fb_komen = str(row[7]).strip() if len(row) > 7 and row[7] else '-'
                        fb_share = str(row[8]).strip() if len(row) > 8 and row[8] else '-'
                        
                        employees.append({
                            "no": no,
                            "nama": nama,
                            "jabatan": jabatan,
                            "divisi": current_divisi,
                            "ig_like": ig_like,
                            "ig_komen": ig_komen,
                            "ig_share": ig_share,
                            "fb_like": fb_like,
                            "fb_komen": fb_komen,
                            "fb_share": fb_share
                        })

    return {
        "filename": filename,
        "post_title": post_title,
        "audit_date": audit_date,
        "total_pegawai": total_pegawai,
        "ig_url": ig_url,
        "fb_url": fb_url,
        "employees": employees
    }
