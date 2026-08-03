import os
import glob
import tempfile
import io
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd

from db_storage import init_db, save_parsed_pdf, clear_all_data
from pdf_parser import parse_audit_pdf
from analytics import (
    get_overall_summary,
    get_personal_analytics,
    get_division_analytics,
    get_post_performance,
    get_employee_detail
)
from pdf_generator import generate_pdf_report

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize database schema on startup
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/summary", methods=["GET"])
def api_summary():
    date_filter = request.args.get("date")
    summary = get_overall_summary(date_filter)
    return jsonify(summary)

@app.route("/api/personal", methods=["GET"])
def api_personal():
    date_filter = request.args.get("date")
    divisi_filter = request.args.get("divisi")
    search_query = request.args.get("search")
    data = get_personal_analytics(date_filter, divisi_filter, search_query)
    return jsonify(data)

@app.route("/api/divisions", methods=["GET"])
def api_divisions():
    date_filter = request.args.get("date")
    data = get_division_analytics(date_filter)
    return jsonify(data)

@app.route("/api/posts", methods=["GET"])
def api_posts():
    date_filter = request.args.get("date")
    data = get_post_performance(date_filter)
    return jsonify(data)

@app.route("/api/employee/detail", methods=["GET"])
def api_employee_detail():
    emp_name = request.args.get("name")
    date_filter = request.args.get("date")
    if not emp_name:
        return jsonify({"error": "Employee name required"}), 400
    data = get_employee_detail(emp_name, date_filter)
    return jsonify(data)

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
        
    uploaded_files = request.files.getlist("files")
    saved_count = 0
    errors = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for f in uploaded_files:
            if f.filename and f.filename.endswith(".pdf"):
                temp_path = os.path.join(temp_dir, f.filename)
                f.save(temp_path)
                try:
                    parsed = parse_audit_pdf(temp_path)
                    save_parsed_pdf(parsed)
                    saved_count += 1
                except Exception as e:
                    errors.append(f"{f.filename}: {str(e)}")
                    
    return jsonify({
        "success": True,
        "saved_count": saved_count,
        "errors": errors
    })

@app.route("/api/import-folder", methods=["POST"])
def api_import_folder():
    req_data = request.get_json() or {}
    folder_path = req_data.get("folder_path", r"C:\Users\USER\Documents\Medsos Audit\31-07-2026")
    
    if not os.path.exists(folder_path):
        return jsonify({"error": f"Directory path '{folder_path}' does not exist."}), 400
        
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
    if not pdf_files:
        return jsonify({"error": f"No PDF files found in '{folder_path}'."}), 400
        
    saved_count = 0
    errors = []
    for pdf_path in pdf_files:
        try:
            parsed = parse_audit_pdf(pdf_path)
            save_parsed_pdf(parsed)
            saved_count += 1
        except Exception as e:
            errors.append(f"{os.path.basename(pdf_path)}: {str(e)}")
            
    return jsonify({
        "success": True,
        "folder_path": folder_path,
        "saved_count": saved_count,
        "errors": errors
    })

@app.route("/api/export-excel", methods=["GET"])
def api_export_excel():
    date_filter = request.args.get("date")
    divisi_filter = request.args.get("divisi")
    search_query = request.args.get("search")
    
    personal_data = get_personal_analytics(date_filter, divisi_filter, search_query)
    
    df_data = []
    for idx, emp in enumerate(personal_data, 1):
        df_data.append({
            "No": idx,
            "Nama Pegawai": emp['nama'],
            "Jabatan": emp['jabatan'],
            "Divisi": emp['divisi'],
            "Jumlah Post Audited": emp['total_posts'],
            "IG Like": emp['ig_like'],
            "IG Komen": emp['ig_komen'],
            "IG Share": emp['ig_share'],
            "FB Like": emp['fb_like'],
            "FB Komen": emp['fb_komen'],
            "FB Share": emp['fb_share'],
            "Total Like (IG+FB)": emp['total_like'],
            "Total Komen (IG+FB)": emp['total_komen'],
            "Total Interaksi": emp['total_interaction'],
            "Persentase Kepatuhan Like (%)": emp['like_compliance']
        })
        
    df = pd.DataFrame(df_data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rekap Analisis Personal')
    output.seek(0)
    
    export_filename = f"Rekap_Analisis_Medsos_Personal_{date_filter or 'All'}.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=export_filename
    )

@app.route("/api/export-pdf", methods=["GET"])
def api_export_pdf():
    date_filter = request.args.get("date")
    divisi_filter = request.args.get("divisi")
    search_query = request.args.get("search")
    
    pdf_buffer = generate_pdf_report(date_filter, divisi_filter, search_query)
    export_filename = f"Laporan_Analisis_Medsos_{date_filter or 'All'}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=export_filename
    )

@app.route("/api/clear", methods=["POST"])
def api_clear():
    clear_all_data()
    return jsonify({"success": True, "message": "All data cleared successfully."})

if __name__ == "__main__":
    # Ingest default data folder on start if empty
    summary = get_overall_summary()
    if summary["total_posts"] == 0:
        default_folder = r"C:\Users\USER\Documents\Medsos Audit\31-07-2026"
        if os.path.exists(default_folder):
            print(f"[*] Initializing dataset from '{default_folder}'...")
            pdf_files = glob.glob(os.path.join(default_folder, "*.pdf"))
            for pdf_path in pdf_files:
                try:
                    parsed = parse_audit_pdf(pdf_path)
                    save_parsed_pdf(parsed)
                except Exception as e:
                    print(f"[!] Error reading {pdf_path}: {e}")
            print(f"[OK] Ingested {len(pdf_files)} PDF audit files into database!")
            
    print("=" * 60)
    print("[OK] Social Media Audit & Analytics System running on http://127.0.0.1:5050")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5050, debug=False)
