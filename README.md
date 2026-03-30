# 🤖 Autonomous Recruitment & Hiring Agent

An AI-powered recruitment pipeline using **Google Workspace + Vertex AI**.

---

## 📁 Project Structure

```
autonomous-recruitment-agent/
├── backend/                  # FastAPI Python backend
│   ├── main.py               # App entry point
│   ├── routers/
│   │   ├── jd.py             # Job Description routes
│   │   ├── resume.py         # Resume upload & parsing routes
│   │   └── candidates.py     # Candidate scoring & listing routes
│   ├── services/
│   │   ├── jd_generator.py   # AI JD generation via Vertex AI
│   │   ├── resume_parser.py  # PDF/DOCX resume parsing
│   │   ├── scorer.py         # Vertex AI candidate scoring
│   │   ├── sheets.py         # Google Sheets integration
│   │   ├── gmail.py          # Gmail API email sender
│   │   ├── calendar.py       # Google Calendar scheduling
│   │   └── linkedin.py       # LinkedIn scraping (Apify)
│   ├── models/
│   │   └── schemas.py        # Pydantic data models
│   └── utils/
│       └── auth.py           # Google OAuth / Service Account
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page-level components
│   │   └── services/         # API call helpers
│   └── public/
├── config/
│   ├── credentials.json      # Google Service Account key (DO NOT COMMIT)
│   └── settings.py           # Central config (env vars)
├── scripts/
│   └── setup_sheets.py       # One-time Google Sheet setup
├── .env.example              # Environment variable template
├── requirements.txt
└── docker-compose.yml
```

---

## 🚀 Week 1 Deliverables

- [x] Project structure & environment setup
- [x] AI Job Description Generator (Vertex AI)
- [x] Resume upload endpoint + PDF/DOCX parsing
- [x] Google Sheets candidate storage
- [x] Vertex AI resume ↔ JD scoring
- [x] LinkedIn profile scraper (via Apify)
- [x] React frontend scaffold

---

## ⚙️ Setup Instructions

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd autonomous-recruitment-agent

# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in all values in .env
```

### 3. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable these APIs:
   - Vertex AI API
   - Google Sheets API
   - Gmail API
   - Google Calendar API
   - Google Drive API
3. Create a **Service Account** → Download `credentials.json` → place in `config/`
4. For Gmail/Calendar (needs user OAuth): create OAuth 2.0 credentials

### 4. Run the Sheet Setup Script

```bash
python scripts/setup_sheets.py
```

### 5. Start Development Servers

```bash
# Terminal 1 - Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm start
```

---

## 🔑 Environment Variables

See `.env.example` for all required variables.
