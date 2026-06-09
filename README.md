# Study Buddy Matcher — Riphah BSSE-FA'25

Built by the vibe coding group (Huzaifa, Ayesha Ahmad, Farah Sajid, Hafsa Mustafa, Saira Bano)
Submitted to Sir Ghulam Murtaza

## Setup & Run

### 1. Install dependencies (one time only)
```bash
pip install flask flask-cors pyjwt
```

### 2. Start the server
```bash
python app.py
```

### 3. Open the app
Go to: http://localhost:5000

---

## Features
- **Auth** — Register / login with JWT tokens (30-day sessions)
- **Profile** — 3-step form: basic info → subjects & schedule → study style
- **Matching** — Algorithm: subjects 50% + schedule 30% + style 20%
- **Chat** — Real-time polling every 3 seconds, schedule session via chat
- **Sessions** — Log, rate, and track study sessions with stats & bar chart

## File structure
```
studybuddy/
├── app.py          ← Flask backend (SQLite + JWT)
├── index.html      ← Full frontend (single HTML file)
├── requirements.txt
└── studybuddy.db   ← Created automatically on first run
```
