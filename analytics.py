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
        
        # Max possible interactions per post = 6 (3 IG, 3 FB)
        # Or compliance based on likes + comments
        max_likes_possible = total_posts * 2 # 1 IG + 1 FB
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
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as total_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as total_komen,
            SUM(CASE WHEN i.ig_share = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_share = 'SUDAH' THEN 1 ELSE 0 END) as total_share
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
        GROUP BY i.divisi
        ORDER BY total_like DESC
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
            p.post_title,
            p.audit_date,
            p.ig_url,
            p.fb_url,
            SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) as ig_like,
            SUM(CASE WHEN i.ig_komen = 'SUDAH' THEN 1 ELSE 0 END) as ig_komen,
            SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END) as fb_like,
            SUM(CASE WHEN i.fb_komen = 'SUDAH' THEN 1 ELSE 0 END) as fb_komen
        FROM posts p
        LEFT JOIN interactions i ON i.post_id = p.id
        {where_clause}
        GROUP BY p.id
        ORDER BY (SUM(CASE WHEN i.ig_like = 'SUDAH' THEN 1 ELSE 0 END) + SUM(CASE WHEN i.fb_like = 'SUDAH' THEN 1 ELSE 0 END)) DESC
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    posts = []
    for r in rows:
        posts.append({
            "id": r['id'],
            "title": r['post_title'],
            "date": r['audit_date'],
            "ig_url": r['ig_url'],
            "fb_url": r['fb_url'],
            "ig_like": r['ig_like'] or 0,
            "ig_komen": r['ig_komen'] or 0,
            "fb_like": r['fb_like'] or 0,
            "fb_komen": r['fb_komen'] or 0,
            "total_like": (r['ig_like'] or 0) + (r['fb_like'] or 0),
            "total_komen": (r['ig_komen'] or 0) + (r['fb_komen'] or 0)
        })
        
    conn.close()
    return posts

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
            p.post_title,
            p.audit_date,
            p.ig_url,
            p.fb_url,
            i.jabatan,
            i.divisi,
            i.ig_like,
            i.ig_komen,
            i.ig_share,
            i.fb_like,
            i.fb_komen,
            i.fb_share
        FROM interactions i
        JOIN posts p ON i.post_id = p.id
        {where_clause}
        ORDER BY p.audit_date DESC, p.id ASC
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
            "title": r['post_title'],
            "date": r['audit_date'],
            "ig_url": r['ig_url'],
            "fb_url": r['fb_url'],
            "ig_like": r['ig_like'],
            "ig_komen": r['ig_komen'],
            "ig_share": r['ig_share'],
            "fb_like": r['fb_like'],
            "fb_komen": r['fb_komen'],
            "fb_share": r['fb_share']
        })
        
    conn.close()
    return {
        "nama": emp_name,
        "jabatan": jabatan,
        "divisi": divisi,
        "posts": posts_detail
    }
