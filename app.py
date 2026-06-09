import os, json, sqlite3, hashlib
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
import jwt

app = Flask(__name__, static_folder='.')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'studybuddy-riphah-secret-change-in-production')
CORS(app)

DB_FILE   = 'studybuddy.db'
AV_CYCLE  = ['av1', 'av2', 'av3', 'av4', 'av5']

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

def q(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows

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
    program       TEXT    DEFAULT 'BSSE-FA''25',
    semester      TEXT    DEFAULT 'Second',
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
    d = dict(row)
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
    def parse(x):
        try:
            return set(x if isinstance(x, list) else json.loads(x or '[]'))
        except Exception:
            return set()

    s1, s2 = parse(me['subjects']), parse(them['subjects'])
    shared_s = s1 & s2
    score = (len(shared_s) / len(s1)) * 50 if shared_s and s1 else 0

    d1, d2 = parse(me['days']), parse(them['days'])
    shared_d = d1 & d2
    if shared_d and d1:
        score += (len(shared_d) / len(d1)) * 15

    t1, t2 = parse(me['times']), parse(them['times'])
    shared_t = t1 & t2
    if shared_t and t1:
        score += (len(shared_t) / len(t1)) * 15

    if me.get('style') == them.get('style'):
        score += 20

    return round(min(score, 99))


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
        SET name=?, campus=?, program=?, semester=?,
            subjects=?, days=?, times=?, style=?, note=?, profile_done=1
        WHERE id=?
    ''', (
        d.get('name'),
        d.get('campus', 'Riphah International University'),
        d.get('program', "BSSE-FA'25"),
        d.get('semester', 'Second'),
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


# ── MATCHES ───────────────────────────────────────────────────────────────────
@app.route('/api/matches')
@require_auth
def get_matches():
    me_row = q('SELECT * FROM users WHERE id=?', (g.uid,), one=True)
    others = q('SELECT * FROM users WHERE id!=? AND profile_done=1', (g.uid,))
    results = []
    for u in others:
        sc = calc_score(me_row, u)
        if sc > 0:
            ud = fmt_user(u)
            ud['score'] = sc
            ud['cms']   = u['program']
            results.append(ud)
    results.sort(key=lambda x: x['score'], reverse=True)
    return jsonify(results[:10])


# ── CONVERSATIONS ─────────────────────────────────────────────────────────────
@app.route('/api/conversations')
@require_auth
def conversations():
    uid  = g.uid
    rows = q('''
        SELECT m.*,
            CASE WHEN m.sender_id=? THEN m.receiver_id ELSE m.sender_id END AS contact_id,
            u2.name    AS contact_name,
            u2.program AS contact_program
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
    return jsonify([dict(r) for r in rows])


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
    return jsonify([dict(r) for r in rows])


@app.route('/api/messages', methods=['POST'])
@require_auth
def send_message():
    d   = request.json or {}
    rid = d.get('receiver_id')
    txt = (d.get('text') or '').strip()
    if not rid or not txt:
        return jsonify(error='receiver_id and text required'), 400
    db = get_db()
    db.execute('INSERT INTO messages (sender_id,receiver_id,text) VALUES (?,?,?)',
               (g.uid, rid, txt))
    db.commit()
    row = q('SELECT * FROM messages WHERE rowid=last_insert_rowid()', one=True)
    return jsonify(dict(row)), 201


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
    return jsonify([dict(r) for r in rows])


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
    return jsonify(incoming=[dict(r) for r in incoming],
                   outgoing=[dict(r) for r in outgoing])


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
    students    = q('SELECT COUNT(*) AS c FROM users', one=True)['c']
    profiled    = q('SELECT COUNT(*) AS c FROM users WHERE profile_done=1', one=True)['c']
    sessions_n  = q('SELECT COUNT(*) AS c FROM study_sessions', one=True)['c']
    matches_n   = q("""
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
    rows = q('SELECT id, name, program, semester FROM users WHERE id!=?', (g.uid,))
    return jsonify([dict(r) for r in rows])


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print('\n' + '='*50)
    print("  StudyBuddy — Riphah BSSE-FA'25")
    print('  Running at  →  http://localhost:5000')
    print('='*50 + '\n')
    app.run(debug=True, port=5000)
