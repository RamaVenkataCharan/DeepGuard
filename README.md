# DeepGuard

DeepGuard is an end-to-end predictive analytics and crop risk assessment platform combining Flask, Celery, React (Vite + Tailwind CSS), and Machine Learning inference.

Refer to [PROJECT_OVERVIEW.md](file:///c:/Users/ramav/Documents/DeepGuard/PROJECT_OVERVIEW.md) for full project architecture, implementation status, and feature roadmap.

## Quick Start

### Backend & Database
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python seed.py
python wsgi.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup
```bash
docker-compose up --build
```
