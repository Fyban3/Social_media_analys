import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "audit_data.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Table for Audited Posts (Files)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            post_title TEXT,
            ig_title TEXT,
            fb_title TEXT,
            audit_date TEXT,
            export_time TEXT,
            total_pegawai INTEGER,
            ig_url TEXT,
            fb_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if columns exist (for migration)
    cursor.execute("PRAGMA table_info(posts)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'ig_title' not in columns:
        cursor.execute("ALTER TABLE posts ADD COLUMN ig_title TEXT")
    if 'fb_title' not in columns:
        cursor.execute("ALTER TABLE posts ADD COLUMN fb_title TEXT")
    if 'export_time' not in columns:
        cursor.execute("ALTER TABLE posts ADD COLUMN export_time TEXT")
    
    # Table for Individual Employee Interactions per Post
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            emp_no TEXT,
            nama TEXT,
            jabatan TEXT,
            divisi TEXT,
            ig_like TEXT,
            ig_komen TEXT,
            ig_share TEXT,
            fb_like TEXT,
            fb_komen TEXT,
            fb_share TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def save_parsed_pdf(parsed_data):
    conn = get_db()
    cursor = conn.cursor()
    
    filename = parsed_data['filename']
    
    # Delete old entry if exists (re-upload / overwrite)
    cursor.execute("SELECT id FROM posts WHERE filename = ?", (filename,))
    existing = cursor.fetchone()
    if existing:
        post_id = existing['id']
        cursor.execute("DELETE FROM interactions WHERE post_id = ?", (post_id,))
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        
    cursor.execute('''
        INSERT INTO posts (filename, post_title, ig_title, fb_title, audit_date, export_time, total_pegawai, ig_url, fb_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        filename,
        parsed_data.get('post_title', ''),
        parsed_data.get('ig_title', ''),
        parsed_data.get('fb_title', ''),
        parsed_data.get('audit_date', ''),
        parsed_data.get('export_time', ''),
        parsed_data.get('total_pegawai', 75),
        parsed_data.get('ig_url', ''),
        parsed_data.get('fb_url', '')
    ))
    
    post_id = cursor.lastrowid
    
    interactions_data = []
    for emp in parsed_data.get('employees', []):
        interactions_data.append((
            post_id,
            emp.get('no', ''),
            emp.get('nama', ''),
            emp.get('jabatan', ''),
            emp.get('divisi', ''),
            emp.get('ig_like', '-'),
            emp.get('ig_komen', '-'),
            emp.get('ig_share', '-'),
            emp.get('fb_like', '-'),
            emp.get('fb_komen', '-'),
            emp.get('fb_share', '-')
        ))
        
    cursor.executemany('''
        INSERT INTO interactions (post_id, emp_no, nama, jabatan, divisi, ig_like, ig_komen, ig_share, fb_like, fb_komen, fb_share)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', interactions_data)
    
    conn.commit()
    conn.close()
    return post_id

def clear_all_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interactions")
    cursor.execute("DELETE FROM posts")
    conn.commit()
    conn.close()
