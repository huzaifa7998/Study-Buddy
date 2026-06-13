import os, json, sqlite3, hashlib
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import jwt

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'studybuddy-riphah-secret-change-in-production')
CORS(app)

DB_FILE  = 'studybuddy.db'
AV_CYCLE = ['av1', 'av2', 'av3', 'av4', 'av5']

# ── DEPARTMENT → SEMESTER → SUBJECTS MAP ─────────────────────────────────────
DEPT_SUBJECTS = {
    "BSCS": {
        "Semester 2 (FA25)": ["Digital Logic Design","Object-Oriented Programming","Pre-Calculus II","Expository Writing","Probability & Statistics","Calculus & Analytic Geometry","Understanding Quran II","Islamic Studies"],
        "Semester 4 (FA24)": ["Computer Architecture","Software Engineering","Linear Algebra","Web Programming","Analysis of Algorithms","Problem Solving II","Computer Construction","Introduction to History & Society"],
        "Semester 5 (SP24)": ["Mobile Application Development","Human Computer Interaction & Graphics","Theory of Automata & Formal Languages","Operating Systems","Group Project","Technical & Business Writing"],
        "Semester 6 (FA23)": ["Cloud Computing","Artificial Intelligence","Advanced Database Management Systems","Computer Networks","Computer Construction"]
    },
    "BSSE": {
        "Semester 2 (FA25)": ["Digital Logic Design","Object-Oriented Programming","Pre-Calculus II","Expository Writing","Probability & Statistics","Calculus & Analytic Geometry","Understanding Quran II","Islamic Studies"],
        "Semester 4 (FA24)": ["Analysis of Algorithms","Software Requirements Engineering","Web Programming","Linear Algebra","Computer Organization & Assembly Language","Problem Solving II","Introduction to History & Society"],
        "Semester 5 (SP24)": ["Mobile Application Development","Parallel & Distributed Computing","Operating Systems","Software Construction & Development","Group Project","Technical & Business Writing"],
        "Semester 6 (FA23)": ["Software Quality Engineering","Software Construction & Configuration Management","Software Design & Architecture","Computer Networks","Artificial Intelligence"]
    },
    "BSIT": {
        "Semester 2 (FA25)": ["Digital Logic Design","Object-Oriented Programming","Pre-Calculus II","Expository Writing","Probability & Statistics","Calculus & Analytic Geometry","Understanding Quran II","Islamic Studies"],
        "Semester 4 (FA24)": ["Database Systems","Web Programming","Information Security","Operating Systems","Problem Solving II","Introduction to History & Society"]
    },
    "BSAI": {
        "Semester 2 (FA25)": ["Digital Logic Design","Object-Oriented Programming","Pre-Calculus II","Expository Writing","Probability & Statistics","Calculus & Analytic Geometry","Islamic Studies"],
        "Semester 4 (FA24)": ["Database Systems","Analysis of Algorithms","Linear Algebra","Machine Learning","Problem Solving II","Introduction to History & Society"]
    },
    "BSGV": {
        "Semester 2 (FA25)": ["Object-Oriented Programming","Expository Writing","Calculus & Analytic Geometry","Discrete Structures","Understanding Quran II","Islamic Studies"],
        "Semester 4 (FA24)": ["Database Systems","Computer Graphics","3D Modeling & Animation","Problem Solving II","Introduction to History & Society","Technical & Business Writing"]
    },
    "BSEng": {
        "Semester 2 (FA25)": ["Expository Writing","Introduction to Linguistics","Text & Quantitative Reasoning","Environmental Sciences","Understanding Quran II","Pak Studies"],
        "Semester 4 (FA24)": ["Phonetics & Phonology","Romantic Poetry","Semantics & Pragmatics","Morphology & Syntax","Family Life","Classical Drama"],
        "Semester 6 (FA23)": ["Second Language Acquisition","Diaspora Studies","Mass Communication & Print Media","Sociolinguistics","Practical Life in English","Research Methods","Entrepreneurship"]
    },
    "BBA": {
        "Semester 1 (SP26)": ["Functional English","Everyday Science","Business Math & Statistics","Principles of Microeconomics","Applications of ICT","Understanding Quran I"],
        "Semester 2 (FA25)": ["FA&R I","Human Psychology & Philosophy","Logic & Critical Thinking","Pak Economic & Constitutional Environment","Principles of Macroeconomics","Expository Writing","Understanding Quran II"],
        "Semester 3 (SP25)": ["FA&R II","Principles of Marketing","Principles of Management","Entrepreneurship","Pakistan Economy","Ideology & Constitution of Pakistan"],
        "Semester 4 (FA24)": ["Business Finance","Business & Corporate Law","Cost Accounting","HRM","Pakistan Economy","Pak Studies"],
        "Semester 6 (FA23)": ["CSR & Ethics in Management","Business Taxation","Leadership & Management I","Information Systems & Business Analytics","Research Methods"]
    },
    "DPT": {
        "Semester 1 (SP26)": ["Anatomy I","Physiology I","Kinesiology I","Cell Biology","Human Psychology","Functional English","Understanding Quran I"],
        "Semester 2 (FA25)": ["Anatomy II","Physiology II","Kinesiology II","Quran Recitation I","Expository Writing","Islamic Studies"],
        "Semester 3 (SP25)": ["Anatomy III","Physiology III","Bioethics & Evidence I","Quran Recitation II","Principles of Biochemistry","Therapeutic Modalities & Orthopaedic Surgery"],
        "Semester 4 (FA24)": ["Anatomy IV","Bioethics & Evidence II","Biochemistry II","Quran Recitation II","Health & Wellness","Microbiology & Genetics","Intro to Basic Translation of Quran"]
    },
    "PharmD": {
        "Semester 2 (FA25)": ["Organic Chemistry II","Physiology II","Anatomy & Histology","Physical Pharmacy II","Biochemistry II","Islamic Studies"],
        "Semester 4 (FA24)": ["Dosage Form Sciences","Microbiology","Pharmacognosy I","Pharmacology & Therapeutics I","Biostatistics","Pharmaceutical Sciences"],
        "Semester 6 (FA23)": ["Pharmacy Practice II","Pharmacology & Therapeutics II","Pharmaceutical Analysis","Pharmacognosy II","Understanding Quran II","Pharmacy Practice III"]
    },
    "BSN": {
        "Semester 2 (FA25)": ["Anatomy & Physiology II","Applied Nutrition","Fundamentals of Nursing II","Theoretical Basis of Nursing","Islamic Studies","QR-I","Understanding Quran II","Intro to Basic Translation of Quran"]
    },
    "MLT": {
        "Semester 2 (FA25)": ["Physiology I","Expository Writing","QR-I","Understanding Quran II","Pak Studies"],
        "Semester 4 (FA24)": ["General Microbiology","Histology & Cytology I","Haematology I","Immunology & Serology","Medical Instrumentation","Biochemistry II"]
    },
    "HND": {
        "Semester 2 (FA25)": ["Human Anatomy","Human Physiology","QR-II","Expository Writing","Understanding Quran II","Pak Studies"],
        "Semester 4 (FA24)": ["Anatomy of Nervous System","Nutrition Transition through Life Cycle","Menu Planning & Management","Food & Drug Law","General Pathology"]
    },
    "FST": {
        "Semester 2 (FA25)": ["Food & Human Nutrition","Cell Biology","QR-II","Expository Writing","Understanding Quran II","Pak Studies"],
        "Semester 4 (FA24)": ["Food Analysis & Vegetable Processing","Food Safety & Quality Management","Dairy Technology","Bakery & Pastry Technology","Post-Harvest Losses & Drying"]
    }
}


# ── DATABASE ──────────────────────────────────────────────────────────────────
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

# ── THE KEY FIX: q() always returns plain dicts, never raw sqlite3.Row objects ──
def q(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    rv = [dict(row) for row in rows]
    return (rv[0] if rv else None) if one else rv

def run(sql, args=()):
    db = get_db()
    db.execute(sql, args)
    db.commit()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    campus        TEXT    DEFAULT 'Riphah International University',
    department    TEXT    DEFAULT '',
    program       TEXT    DEFAULT '',
    semester      TEXT    DEFAULT '',
    subjects      TEXT    DEFAULT '[]',
    days          TEXT    DEFAULT '[]',
    times         TEXT    DEFAULT '[]',
    style         TEXT    DEFAULT 'solo',
    note          TEXT    DEFAULT '',
    profile_done  INTEGER DEFAULT 0,
    created_at    TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id   INTEGER NOT NULL REFERENCES users(id),
    receiver_id INTEGER NOT NULL REFERENCES users(id),
    text        TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now')),
    read_at     TEXT
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    partner_id  INTEGER NOT NULL REFERENCES users(id),
    subject     TEXT    NOT NULL,
    date        TEXT    NOT NULL,
    rating      INTEGER DEFAULT 0,
    notes       TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS study_requests (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id         INTEGER NOT NULL REFERENCES users(id),
    receiver_id       INTEGER NOT NULL REFERENCES users(id),
    subject           TEXT    NOT NULL,
    proposed_datetime TEXT    DEFAULT '',
    message           TEXT    DEFAULT '',
    status            TEXT    DEFAULT 'pending',
    created_at        TEXT    DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_msg_s ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_msg_r ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_ses_u ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_req_r ON study_requests(receiver_id, status);
    """)

    # ── MIGRATE: add department column to existing DBs ────────────────────────
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if 'department' not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN department TEXT DEFAULT ''")
    conn.commit()
    conn.close()


# ── AUTH HELPERS ──────────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token(uid):
    return jwt.encode(
        {'uid': uid, 'exp': datetime.now(timezone.utc) + timedelta(days=30)},
        app.config['SECRET_KEY'], algorithm='HS256'
    )

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth  = request.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else auth
        if not token:
            return jsonify(error='Unauthorized'), 401
        try:
            data  = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            g.uid = data['uid']
        except Exception:
            return jsonify(error='Invalid or expired token'), 401
        return f(*args, **kwargs)
    return wrapper

def fmt_user(row):
    # row is already a dict because q() converts everything
    d = dict(row) if not isinstance(row, dict) else row
    for field in ('subjects', 'days', 'times'):
        v = d.get(field)
        try:
            d[field] = json.loads(v) if v else []
        except Exception:
            d[field] = []
    d.pop('password_hash', None)
    parts = (d.get('name') or '').split()
    d['initials'] = ''.join(w[0] for w in parts if w).upper()[:2]
    d['avatar']   = AV_CYCLE[(d['id'] - 1) % len(AV_CYCLE)]
    return d


# ── MATCHING ALGORITHM ────────────────────────────────────────────────────────
def calc_score(me, them):
    me_dept = (me.get('department') or '').strip()
    th_dept = (them.get('department') or '').strip()
    me_sem  = (me.get('semester') or '').strip()
    th_sem  = (them.get('semester') or '').strip()

    if me_dept and th_dept and me_dept != th_dept:
        return 0, 'different_department'
    if me_sem and th_sem and me_sem != th_sem:
        return 0, 'different_semester'

    def parse(x):
        try:
            return set(x if isinstance(x, list) else json.loads(x or '[]'))
        except Exception:
            return set()

    s1, s2   = parse(me.get('subjects')), parse(them.get('subjects'))
    shared_s = s1 & s2
    sub_score = 0
    if shared_s:
        from_me   = (len(shared_s) / len(s1)) * 50 if s1 else 0
        from_them = (len(shared_s) / len(s2)) * 50 if s2 else 0
        sub_score = (from_me + from_them) / 2

    d1, d2   = parse(me.get('days')), parse(them.get('days'))
    shared_d = d1 & d2
    day_score = 0
    if shared_d:
        from_me   = (len(shared_d) / len(d1)) * 15 if d1 else 0
        from_them = (len(shared_d) / len(d2)) * 15 if d2 else 0
        day_score = (from_me + from_them) / 2

    t1, t2   = parse(me.get('times')), parse(them.get('times'))
    shared_t = t1 & t2
    time_score = 0
    if shared_t:
        from_me   = (len(shared_t) / len(t1)) * 15 if t1 else 0
        from_them = (len(shared_t) / len(t2)) * 15 if t2 else 0
        time_score = (from_me + from_them) / 2

    style_score = 20 if me.get('style') == them.get('style') else 0

    return round(min(sub_score + day_score + time_score + style_score, 99)), None


# ── SERVE FRONTEND ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    d     = request.json or {}
    name  = d.get('name', '').strip()
    email = d.get('email', '').strip().lower()
    pw    = d.get('password', '')

    if not name or not email or not pw:
        return jsonify(error='Name, email and password are required'), 400
    if len(pw) < 6:
        return jsonify(error='Password must be at least 6 characters'), 400
    if q('SELECT id FROM users WHERE email=?', (email,), one=True):
        return jsonify(error='Email already registered'), 409

    run('INSERT INTO users (name,email,password_hash) VALUES (?,?,?)',
        (name, email, hash_pw(pw)))
    user = q('SELECT * FROM users WHERE email=?', (email,), one=True)
    return jsonify(token=make_token(user['id']), user=fmt_user(user)), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    d     = request.json or {}
    email = d.get('email', '').strip().lower()
    pw    = d.get('password', '')
    user  = q('SELECT * FROM users WHERE email=?', (email,), one=True)
    if not user or user['password_hash'] != hash_pw(pw):
        return jsonify(error='Invalid email or password'), 401
    return jsonify(token=make_token(user['id']), user=fmt_user(user))


@app.route('/api/auth/me')
@require_auth
def me():
    user = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    if not user:
        return jsonify(error='User not found'), 404
    return jsonify(fmt_user(user))


# ── PROFILE ───────────────────────────────────────────────────────────────────
@app.route('/api/profile', methods=['PUT'])
@require_auth
def update_profile():
    d = request.json or {}
    get_db().execute('''
        UPDATE users
        SET name=?, campus=?, department=?, program=?, semester=?,
            subjects=?, days=?, times=?, style=?, note=?, profile_done=1
        WHERE id=?
    ''', (
        d.get('name'),
        d.get('campus', 'Riphah International University'),
        d.get('department', ''),
        d.get('program', ''),
        d.get('semester', ''),
        json.dumps(d.get('subjects', [])),
        json.dumps(d.get('days', [])),
        json.dumps(d.get('times', [])),
        d.get('style', 'solo'),
        d.get('note', ''),
        g.uid
    ))
    get_db().commit()
    user = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    return jsonify(fmt_user(user))


# ── DEPT/SUBJECTS API ─────────────────────────────────────────────────────────
@app.route('/api/departments')
def get_departments():
    """Return full department → semester → subjects map."""
    return jsonify(DEPT_SUBJECTS)


# ── MATCHES ───────────────────────────────────────────────────────────────────
@app.route('/api/matches')
@require_auth
def get_matches():
    me_row = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    others = q('SELECT * FROM users WHERE id!=? AND profile_done=1', (g.uid,))
    results = []
    for u in others:
        sc, reason = calc_score(me_row, u)
        if sc > 0:
            ud = fmt_user(u)
            ud['score'] = sc
            ud['cms']   = u.get('program', '')
            results.append(ud)
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results[:10])


# ── CHECK IF CONNECT IS ALLOWED ───────────────────────────────────────────────
@app.route('/api/can-connect/<int:other_id>')
@require_auth
def can_connect(other_id):
    me_row    = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    other_row = q('SELECT * FROM users WHERE id=?', (other_id,), one=True)
    if not other_row:
        return jsonify(allowed=False, reason='User not found'), 404
    sc, reason = calc_score(me_row, other_row)
    if reason == 'different_department':
        return jsonify(allowed=False, reason='You are in different departments.')
    if reason == 'different_semester':
        return jsonify(allowed=False, reason='You are in different semesters.')
    return jsonify(allowed=True)


# ── CONVERSATIONS ─────────────────────────────────────────────────────────────
@app.route('/api/conversations')
@require_auth
def conversations():
    uid  = g.uid
    rows = q('''
        SELECT m.*,
            CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END AS contact_id,
            u2.name       AS contact_name,
            u2.department AS contact_department,
            u2.program    AS contact_program
        FROM messages m
        JOIN users u2 ON u2.id =
            CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END
        WHERE m.id IN (
            SELECT MAX(id) FROM messages
            WHERE sender_id=? OR receiver_id=?
            GROUP BY CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END
        )
        ORDER BY m.created_at DESC
    ''', (uid, uid, uid, uid, uid))
    return jsonify(rows)


# ── MESSAGES ──────────────────────────────────────────────────────────────────
@app.route('/api/messages')
@require_auth
def get_messages():
    other = request.args.get('with', type=int)
    if not other:
        return jsonify(error='?with=USER_ID required'), 400
    rows = q('''
        SELECT m.*, u.name AS sender_name
        FROM messages m
        JOIN users u ON u.id = m.sender_id
        WHERE (m.sender_id=? AND m.receiver_id=?)
           OR (m.sender_id=? AND m.receiver_id=?)
        ORDER BY m.created_at ASC
    ''', (g.uid, other, other, g.uid))
    get_db().execute('''
        UPDATE messages SET read_at=datetime('now')
        WHERE receiver_id=? AND sender_id=? AND read_at IS NULL
    ''', (g.uid, other))
    get_db().commit()
    return jsonify(rows)


@app.route('/api/messages', methods=['POST'])
@require_auth
def send_message():
    d   = request.json or {}
    rid = d.get('receiver_id')
    txt = (d.get('text') or '').strip()
    if not rid or not txt:
        return jsonify(error='receiver_id and text required'), 400

    # Gate: check department + semester before allowing message
    me_row    = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    other_row = q('SELECT * FROM users WHERE id=?', (rid,), one=True)
    if me_row and other_row and me_row.get('profile_done') and other_row.get('profile_done'):
        _, reason = calc_score(me_row, other_row)
        if reason == 'different_department':
            return jsonify(error='You can only message students in your department.'), 403
        if reason == 'different_semester':
            return jsonify(error='You can only message students in your semester.'), 403

    db = get_db()
    db.execute('INSERT INTO messages (sender_id,receiver_id,text) VALUES (?,?,?)',
               (g.uid, rid, txt))
    db.commit()
    row = q('SELECT * FROM messages WHERE rowid=last_insert_rowid()', one=True)
    return jsonify(row), 201


@app.route('/api/messages/unread')
@require_auth
def unread():
    row = q('SELECT COUNT(*) AS c FROM messages WHERE receiver_id=? AND read_at IS NULL',
            (g.uid,), one=True)
    return jsonify(count=row['c'])


# ── SESSIONS ──────────────────────────────────────────────────────────────────
@app.route('/api/sessions')
@require_auth
def get_sessions():
    rows = q('''
        SELECT s.*, u.name AS partner_name
        FROM study_sessions s
        JOIN users u ON u.id = s.partner_id
        WHERE s.user_id=?
        ORDER BY s.date DESC, s.created_at DESC
    ''', (g.uid,))
    return jsonify(rows)


@app.route('/api/sessions', methods=['POST'])
@require_auth
def add_session():
    d    = request.json or {}
    pid  = d.get('partner_id')
    subj = (d.get('subject') or '').strip()
    date = (d.get('date') or '').strip()
    if not pid or not subj or not date:
        return jsonify(error='partner_id, subject and date required'), 400
    db = get_db()
    db.execute('INSERT INTO study_sessions (user_id,partner_id,subject,date,rating,notes) VALUES (?,?,?,?,?,?)',
               (g.uid, pid, subj, date, int(d.get('rating', 0)), d.get('notes', '')))
    db.commit()
    return jsonify(success=True), 201


@app.route('/api/sessions/<int:sid>', methods=['DELETE'])
@require_auth
def del_session(sid):
    run('DELETE FROM study_sessions WHERE id=? AND user_id=?', (sid, g.uid))
    return jsonify(success=True)


# ── STUDY REQUESTS ────────────────────────────────────────────────────────────
@app.route('/api/requests', methods=['POST'])
@require_auth
def send_request():
    d = request.json or {}
    run('INSERT INTO study_requests (sender_id,receiver_id,subject,proposed_datetime,message) VALUES (?,?,?,?,?)',
        (g.uid, d.get('receiver_id'), d.get('subject', ''),
         d.get('proposed_datetime', ''), d.get('message', '')))
    return jsonify(success=True), 201


@app.route('/api/requests')
@require_auth
def get_requests():
    incoming = q('''
        SELECT r.*, u.name AS sender_name FROM study_requests r
        JOIN users u ON u.id=r.sender_id
        WHERE r.receiver_id=? AND r.status='pending'
        ORDER BY r.created_at DESC
    ''', (g.uid,))
    outgoing = q('''
        SELECT r.*, u.name AS receiver_name FROM study_requests r
        JOIN users u ON u.id=r.receiver_id
        WHERE r.sender_id=?
        ORDER BY r.created_at DESC
    ''', (g.uid,))
    return jsonify(incoming=incoming, outgoing=outgoing)


@app.route('/api/requests/<int:rid>', methods=['PUT'])
@require_auth
def update_request(rid):
    status = (request.json or {}).get('status')
    if status not in ('accepted', 'declined'):
        return jsonify(error='status must be accepted or declined'), 400
    run('UPDATE study_requests SET status=? WHERE id=? AND receiver_id=?',
        (status, rid, g.uid))
    return jsonify(success=True)


# ── STATS ─────────────────────────────────────────────────────────────────────
@app.route('/api/stats')
def stats():
    students   = q('SELECT COUNT(*) AS c FROM users', one=True)['c']
    profiled   = q('SELECT COUNT(*) AS c FROM users WHERE profile_done=1', one=True)['c']
    sessions_n = q('SELECT COUNT(*) AS c FROM study_sessions', one=True)['c']
    matches_n  = q("""
        SELECT COUNT(DISTINCT
            CASE WHEN sender_id < receiver_id
                 THEN sender_id || '_' || receiver_id
                 ELSE receiver_id || '_' || sender_id END) AS c
        FROM messages
    """, one=True)['c']
    return jsonify(
        students=students,
        matches=matches_n,
        sessions=sessions_n,
        profile_pct=round(profiled / max(students, 1) * 100)
    )


@app.route('/api/users')
@require_auth
def list_users():
    rows = q('SELECT id, name, department, program, semester FROM users WHERE id!=?', (g.uid,))
    return jsonify(rows)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print('\n' + '='*50)
    print("  StudyBuddy — Riphah International University")
    print('  Running at  →  http://localhost:5000')
    print('='*50 + '\n')
    app.run(debug=False, port=5000)
