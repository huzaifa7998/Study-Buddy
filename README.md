<div align="center">

# 📚 StudyBuddy
### Smart Study Partner Matching for Riphah International University

**A department-aware web application that connects students with compatible study partners — same class, same vibe.**

![Platform](https://img.shields.io/badge/Platform-PythonAnywhere-3776AB?style=flat-square&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-brightgreen?style=flat-square)
![University](https://img.shields.io/badge/University-Riphah%20International-blue?style=flat-square)
![Team](https://img.shields.io/badge/Team-BSSE--FA'25-orange?style=flat-square)

**[🌐 Live Demo →](https://huzaifa7998.pythonanywhere.com/)**

</div>

---

## Overview

StudyBuddy eliminates the hassle of finding study partners through random WhatsApp blasts and disorganized group chats. Instead, it uses a weighted compatibility algorithm to match students based on shared subjects, schedule overlap, and study style — scoped strictly within the same department and semester for relevant, focused connections.

Built by the **BSSE-FA'25 team** at Riphah International University Sahiwal and submitted to Sir Ghulam Murtaza.

---

## Features

### Smart Profile Builder
A guided three-step profile wizard that captures:
- Department and semester (used to scope all matches)
- Enrolled subjects (auto-populated based on department + semester selection)
- Preferred study days and time slots
- Study style preference — Solo Focused, Small Group, or Open Discussion
- An optional personal note for your profile

### Compatibility Matching
The matching engine compares your profile against every other student in your department and semester and produces a compatibility score out of 100.

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Shared Subjects | 50% | Core predictor — you can only study together what you're both enrolled in |
| Schedule Overlap | 30% | Ensures matches are practically meetable |
| Study Style | 20% | Aligns working preferences to avoid friction |

### Department Gating
Students can only connect with others from the **same department and semester**. This keeps every match relevant and prevents noise from unrelated cohorts.

Supported departments:

| Code | Program |
|------|---------|
| BSCS | Computer Science |
| BSSE | Software Engineering |
| BSIT | Information Technology |
| BSAI | Artificial Intelligence |
| BSGV | Game Development |
| BSEng | English |
| BBA | Business Administration |
| DPT | Physical Therapy |
| PharmD | Pharmacy |
| BSN | Nursing |
| MLT | Medical Lab Technology |
| HND | Health & Nutrition Dietetics |
| FST | Food Science & Technology |

### Real-Time Chat
Direct in-app messaging between matched students — no need to exchange personal contacts to get started.

### Session Tracker
Log completed study sessions with:
- Study partner name
- Subject covered
- Date
- Productivity rating (starred)

The tracker surfaces your total sessions, average rating, and top subject over time so you can identify what's working.

---

## How It Works

```
1. Create Account       Register with your name, email, and password
        ↓
2. Build Profile        Select department → semester → subjects → schedule → style
        ↓
3. Get Matched          Algorithm scores you against all students in your cohort
        ↓
4. Browse & Connect     View top compatible buddies sorted by score
        ↓
5. Chat & Study         Message partners directly inside the app
        ↓
6. Log Sessions         Record what you studied and rate the session
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python (hosted on PythonAnywhere) |
| Frontend | HTML, CSS, JavaScript |
| Deployment | [PythonAnywhere](https://www.pythonanywhere.com/) |

---

## Deployment

The application is live at:

```
https://huzaifa7998.pythonanywhere.com/
```

Hosted on PythonAnywhere. No local installation is required to use the app — simply visit the link and create an account.

### Running Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/studybuddy.git
   cd studybuddy
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   python manage.py runserver     # Django
   # or
   python app.py                  # Flask
   ```

4. Open `http://localhost:8000` in your browser.

> Update this section with the exact framework and run command for your project.

---

## Project Structure

```
studybuddy/
│
├── app/                    # Core application logic
│   ├── models/             # User, Profile, Match, Session, Message models
│   ├── views/              # Route handlers / view functions
│   ├── matching/           # Compatibility scoring algorithm
│   └── templates/          # HTML templates
│
├── static/                 # CSS, JavaScript, assets
│
├── requirements.txt        # Python dependencies
└── README.md
```

> Update this tree to reflect your actual directory layout.

---

## Roadmap

- [ ] Email verification on account creation
- [ ] Push notifications for new matches and messages
- [ ] Study group support (3+ members)
- [ ] Public profile pages with shareable links
- [ ] Mobile-responsive PWA version
- [ ] Admin dashboard for university staff
- [ ] Export session history as PDF

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

---

## Team

Built by the **BSSE-FA'25** cohort at **Riphah International University, Sahiwal Campus**.  
Submitted to **Sir Ghulam Murtaza**.

---

## License

This project is open source. You are free to use, modify, and distribute it with attribution.
