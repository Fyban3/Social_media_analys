from db_storage import get_db

def get_overall_summary(date_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    if date_filter:
        where_clause = "WHERE p.audit_date = ?"
        params.append(date_filter)
        
    # Total Posts audited
    cursor.execute(f"SELECT COUNT(*) as count FROM posts p {where_clause}", params)
    total_posts = cursor.fetchone()['count']
    
    # Total unique employees recorded
    cursor.execute(f"SELECT COUNT(DISTINCT i.nama) as count FROM interactions i JOIN posts p ON i.post_id = p.id {where_clause}", params)
    total_employees = cursor.fetchone()['count']
    
    # Total Interactions
    query_counts = f"""
        SELECT 
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) as total_ig_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) as total_ig_komen,
            SUM(CASE WHEN i.ig_share = 'SUDAH' THEN 1 ELSE 0 END) as total_ig_share,
            SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as total_fb_like,
            SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as total_fb_komen,
            SUM(CASE WHEN i.fb_share = 'SUDAH' THEN 1 ELSE 0 END) as total_fb_share
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
    """
    cursor.execute(query_counts, params)
    row = cursor.fetchone()
    
    ig_like = row['total_ig_like'] or 0
    ig_komen = row['total_ig_komen'] or 0
    ig_share = row['total_ig_share'] or 0
    fb_like = row['total_fb_like'] or 0
    fb_komen = row['total_fb_komen'] or 0
    fb_share = row['total_fb_share'] or 0
    
    total_like = ig_like + fb_like
    total_komen = ig_komen + fb_komen
    total_share = ig_share + fb_share
    grand_total = total_like + total_komen + total_share
    
    # Get available dates
    cursor.execute("SELECT DISTINCT audit_date FROM posts ORDER BY audit_date DESC")
    available_dates = [r['audit_date'] for r in cursor.fetchall() if r['audit_date']]
    
    conn.close()
    
    return {
        "total_posts": total_posts,
        "total_employees": total_employees,
        "total_ig_like": ig_like,
        "total_ig_komen": ig_komen,
        "total_ig_share": ig_share,
        "total_fb_like": fb_like,
        "total_fb_komen": fb_komen,
        "total_fb_share": fb_share,
        "total_like": total_like,
        "total_komen": total_komen,
        "total_share": total_share,
        "grand_total": grand_total,
        "available_dates": available_dates
    }

def get_personal_analytics(date_filter=None, divisi_filter=None, search_query=None):
    """
    Returns personal quantity of Likes, Comments, Shares, and compliance per employee.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    where_conditions = []
    params = []
    
    if date_filter:
        where_conditions.append("p.audit_date = ?")
        params.append(date_filter)
        
    if divisi_filter:
        where_conditions.append("i.divisi = ?")
        params.append(divisi_filter)
        
    if search_query:
        where_conditions.append("(i.nama LIKE ? OR i.jabatan LIKE ?)")
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    query = f"""
        SELECT 
            i.nama,
            MAX(i.jabatan) as jabatan,
            MAX(i.divisi) as divisi,
            COUNT(DISTINCT i.post_id) as total_audited_posts,
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) as ig_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) as ig_komen,
            SUM(CASE WHEN i.ig_share = 'SUDAH' THEN 1 ELSE 0 END) as ig_share,
            SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as fb_like,
            SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as fb_komen,
            SUM(CASE WHEN i.fb_share = 'SUDAH' THEN 1 ELSE 0 END) as fb_share
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
        GROUP BY i.nama
        ORDER BY (SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) + 
                  SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) +
                  SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) + 
                  SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END)) DESC, i.nama ASC
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    result = []
    for r in rows:
        total_posts = r['total_audited_posts']
        t_ig_like = r['ig_like']
        t_ig_komen = r['ig_komen']
        t_ig_share = r['ig_share']
        t_fb_like = r['fb_like']
        t_fb_komen = r['fb_komen']
        t_fb_share = r['fb_share']
        
        tot_like = t_ig_like + t_fb_like
        tot_komen = t_ig_komen + t_fb_komen
        tot_share = t_ig_share + t_fb_share
        tot_interaction = tot_like + tot_komen + tot_share
        
        max_likes_possible = total_posts * 2
        like_compliance = round((tot_like / max_likes_possible * 100), 1) if max_likes_possible > 0 else 0
        
        result.append({
            "nama": r['nama'],
            "jabatan": r['jabatan'],
            "divisi": r['divisi'],
            "total_posts": total_posts,
            "ig_like": t_ig_like,
            "ig_komen": t_ig_komen,
            "ig_share": t_ig_share,
            "fb_like": t_fb_like,
            "fb_komen": t_fb_komen,
            "fb_share": t_fb_share,
            "total_like": tot_like,
            "total_komen": tot_komen,
            "total_share": tot_share,
            "total_interaction": tot_interaction,
            "like_compliance": like_compliance
        })
        
    conn.close()
    return result

def get_division_analytics(date_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    if date_filter:
        where_clause = "WHERE p.audit_date = ?"
        params.append(date_filter)
        
    query = f"""
        SELECT 
            i.divisi,
            COUNT(DISTINCT i.nama) as total_pegawai,
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) as ig_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) as ig_komen,
            SUM(CASE WHEN i.ig_share = 'SUDAH' THEN 1 ELSE 0 END) as ig_share,
            SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as fb_like,
            SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as fb_komen,
            SUM(CASE WHEN i.fb_share = 'SUDAH' THEN 1 ELSE 0 END) as fb_share,
            (SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END)) as total_like,
            (SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END)) as total_komen,
            (SUM(CASE WHEN i.ig_share = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_share = 'SUDAH' THEN 1 ELSE 0 END)) as total_share
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
        GROUP BY i.divisi
        ORDER BY (SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END)) DESC
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    divisions = []
    for r in rows:
        divisions.append({
            "divisi": r['divisi'],
            "total_pegawai": r['total_pegawai'],
            "total_like": r['total_like'],
            "total_komen": r['total_komen'],
            "total_share": r['total_share'],
            "total_interaction": r['total_like'] + r['total_komen'] + r['total_share']
        })
        
    conn.close()
    return divisions

def get_post_performance(date_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    
    where_clause = ""
    params = []
    if date_filter:
        where_clause = "WHERE p.audit_date = ?"
        params.append(date_filter)
        
    query = f"""
        SELECT 
            p.id,
            p.filename,
            p.post_title,
            p.ig_title,
            p.fb_title,
            p.audit_date,
            p.export_time,
            p.total_pegawai,
            p.ig_url,
            p.fb_url,
            COUNT(i.id) as record_count,
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) as ig_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) as ig_komen,
            SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as fb_like,
            SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as fb_komen
        FROM posts p
        LEFT JOIN interactions i ON i.post_id = p.id
        {where_clause}
        GROUP BY p.id
        ORDER BY p.audit_date DESC, p.id DESC
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    posts = []
    for r in rows:
        tot_peg = r['total_pegawai'] or 75
        ig_l = r['ig_like'] or 0
        ig_k = r['ig_komen'] or 0
        fb_l = r['fb_like'] or 0
        fb_k = r['fb_komen'] or 0
        tot_l = ig_l + fb_l
        tot_k = ig_k + fb_k
        tot_i = tot_l + tot_k
        
        # Compliance percentage for this post
        max_likes = tot_peg * 2
        compliance = round((tot_l / max_likes * 100), 1) if max_likes > 0 else 0
        
        posts.append({
            "id": r['id'],
            "filename": r['filename'],
            "title": r['post_title'],
            "ig_title": r['ig_title'] or r['post_title'],
            "fb_title": r['fb_title'] or r['post_title'],
            "date": r['audit_date'],
            "export_time": r['export_time'] or "-",
            "total_pegawai": tot_peg,
            "ig_url": r['ig_url'],
            "fb_url": r['fb_url'],
            "ig_like": ig_l,
            "ig_komen": ig_k,
            "fb_like": fb_l,
            "fb_komen": fb_k,
            "total_like": tot_l,
            "total_komen": tot_k,
            "total_interaction": tot_i,
            "compliance": compliance
        })
        
    conn.close()
    return posts

def get_post_detail(post_id):
    """
    Returns complete post metadata and full 75-employee matrix for a specific post.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    if not post:
        conn.close()
        return None
        
    cursor.execute("""
        SELECT emp_no, nama, jabatan, divisi, ig_like, ig_komen, fb_like, fb_komen
        FROM interactions
        WHERE post_id = ?
        ORDER BY id ASC
    """, (post_id,))
    rows = cursor.fetchall()
    
    employees = []
    grouped_by_divisi = {}
    
    ig_like_sudah = 0
    ig_komen_sudah = 0
    fb_like_sudah = 0
    fb_komen_sudah = 0
    
    for r in rows:
        item = {
            "no": r['emp_no'],
            "nama": r['nama'],
            "jabatan": r['jabatan'],
            "divisi": r['divisi'],
            "ig_like": r['ig_like'] or '-',
            "ig_komen": r['ig_komen'] or '-',
            "fb_like": r['fb_like'] or '-',
            "fb_komen": r['fb_komen'] or '-'
        }
        employees.append(item)
        
        div = r['divisi'] or 'LAINNYA'
        if div not in grouped_by_divisi:
            grouped_by_divisi[div] = []
        grouped_by_divisi[div].append(item)
        
        if item['ig_like'] == 'SUDAH': ig_like_sudah += 1
        if item['ig_komen'] == 'SUDAH': ig_komen_sudah += 1
        if item['fb_like'] == 'SUDAH': fb_like_sudah += 1
        if item['fb_komen'] == 'SUDAH': fb_komen_sudah += 1
        
    tot_peg = post['total_pegawai'] or len(employees)
    tot_like = ig_like_sudah + fb_like_sudah
    tot_komen = ig_komen_sudah + fb_komen_sudah
    
    res = {
        "id": post['id'],
        "filename": post['filename'],
        "post_title": post['post_title'],
        "ig_title": post['ig_title'] or post['post_title'],
        "fb_title": post['fb_title'] or post['post_title'],
        "audit_date": post['audit_date'],
        "export_time": post['export_time'] or "-",
        "total_pegawai": tot_peg,
        "ig_url": post['ig_url'] or "-",
        "fb_url": post['fb_url'] or "-",
        "stats": {
            "ig_like": ig_like_sudah,
            "ig_komen": ig_komen_sudah,
            "fb_like": fb_like_sudah,
            "fb_komen": fb_komen_sudah,
            "total_like": tot_like,
            "total_komen": tot_komen,
            "total_interaction": tot_like + tot_komen,
            "ig_like_pct": round((ig_like_sudah / tot_peg * 100), 1) if tot_peg > 0 else 0,
            "fb_like_pct": round((fb_like_sudah / tot_peg * 100), 1) if tot_peg > 0 else 0
        },
        "employees": employees,
        "grouped_by_divisi": grouped_by_divisi
    }
    conn.close()
    return res

def get_employee_detail(emp_name, date_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    
    where_conditions = ["i.nama = ?"]
    params = [emp_name]
    
    if date_filter:
        where_conditions.append("p.audit_date = ?")
        params.append(date_filter)
        
    where_clause = "WHERE " + " AND ".join(where_conditions)
    
    query = f"""
        SELECT 
            p.id as post_id,
            p.post_title,
            p.audit_date,
            p.export_time,
            p.ig_url,
            p.fb_url,
            i.jabatan,
            i.divisi,
            i.ig_like,
            i.ig_komen,
            i.fb_like,
            i.fb_komen
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
        ORDER BY p.audit_date DESC, p.id DESC
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    posts_detail = []
    jabatan = ""
    divisi = ""
    
    for r in rows:
        if not jabatan:
            jabatan = r['jabatan']
            divisi = r['divisi']
            
        posts_detail.append({
            "post_id": r['post_id'],
            "title": r['post_title'],
            "date": r['audit_date'],
            "export_time": r['export_time'] or "-",
            "ig_url": r['ig_url'],
            "fb_url": r['fb_url'],
            "ig_like": r['ig_like'],
            "ig_komen": r['ig_komen'],
            "fb_like": r['fb_like'],
            "fb_komen": r['fb_komen']
        })
        
    conn.close()
    return {
        "nama": emp_name,
        "jabatan": jabatan,
        "divisi": divisi,
        "posts": posts_detail
    }
