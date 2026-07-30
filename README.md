# DeepGuard

Professional, production-ready README for the DeepGuard project — an ML-powered monitoring, prediction, alerting and reporting platform.


## Overview
DeepGuard combines ML-driven risk predictions with a dashboard, alerting pipeline and reporting engine. It provides a Flask + Celery backend that serves REST APIs, a React + Vite single-page frontend, and an ML workspace for training and inference. DeepGuard is intended for teams that need to integrate predictive analytics (weather and customer risk) into operational workflows.


## Key features
- JWT-based authentication and role-aware APIs
- Customer management and profiling endpoints
- ML prediction endpoints (batch and on-demand) backed by model artifacts under ml/
- Background processing with Celery for long-running tasks (predictions, report generation, alerting)
- PDF report generation (ReportLab) and alerting pipeline
- OpenAPI documentation via Flask-Smorest
- Docker + docker-compose for local development and production variants


## Architecture & stack
- Languages: Python (backend, ML) and JavaScript (frontend)
- Backend: Flask 3.x, Flask-Smorest (OpenAPI), Flask-SQLAlchemy
- Background jobs: Celery (Redis broker/result backend)
- Database: MySQL / compatible (PyMySQL) — configured via environment
- Frontend: React + Vite, Tailwind CSS
- ML: Python scripts and pipelines in ml/ for training and inference


## Repository layout
```text
.
├─ .env.example             # Example environment variables
├─ Makefile                 # Developer tasks
├─ docker-compose.yml       # Local compose (backend, frontend, redis, db)
├─ docker-compose.prod.yml  # Production compose
├─ backend/                 # Flask backend service
│  ├─ app/                  # Flask app factory, blueprints, models, services
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ seed.py               # Demo data seeding
├─ frontend/                # React + Vite SPA
│  ├─ package.json
│  └─ src/                  # Frontend source
├─ ml/                      # ML training, inference, models and configs
└─ infra/                   # Deployment and infra helpers
```


## Quickstart (recommended)
The easiest way to run the full stack locally is Docker Compose.

1. Clone and prepare environment
```bash
git clone https://github.com/RamaVenkataCharan/DeepGuard.git
cd DeepGuard
cp .env.example .env
# Edit .env to set DB credentials, broker URLs and secrets
```

2. Start services
```bash
docker-compose up --build
```
This starts the backend API, the frontend dev server (or static build depending on compose), Redis (for Celery) and the database.

3. Optional: run Celery workers (if not started by compose)
```bash
# from project root
celery -A backend.app.extensions.celery worker --loglevel=info
```

4. Access the app
- Frontend: http://localhost:3000 (or the port defined in docker-compose)
- API: http://localhost:5000
- OpenAPI / API docs: available when the backend runs (Flask-Smorest provides interactive docs)


## Development (backend)
Use a Python virtual environment for backend development.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# set FLASK_ENV=development and other env vars
python backend/seed.py   # seed demo data
# Run local dev server (or gunicorn for production-like server)
gunicorn --bind 0.0.0.0:5000 backend.wsgi:app
# or
flask run --host=0.0.0.0 --port=5000
```

Run tests
```bash
cd backend
pytest
```


## Development (frontend)
```bash
cd frontend
npm install
npm run dev
# build for production
npm run build
```


## Machine learning (ml/)
- Dependencies for experiments and training are in ml/requirements.txt
- Training scripts, model checkpointing and inference helpers are under ml/training and ml/inference
- Trained artifacts should be stored under ml/models (or a configured artifact store). The backend predictions endpoints load models from a configured path.

Example (pseudo):
```bash
cd ml
python training/train.py --config config.yaml --out ml/models/latest
```


## Configuration
Copy and edit .env.example. Key environment variables you should configure:
- FLASK_ENV=development|production
- DATABASE_URL (or MYSQL_HOST/USER/PASSWORD/NAME)
- CELERY_BROKER_URL (e.g., redis://redis:6379/0)
- CELERY_RESULT_BACKEND (e.g., redis://redis:6379/1)
- SECRET_KEY / JWT_SECRET_KEY
- MAIL_*/THIRD_PARTY_API_KEYS used by integrations

The backend loads configuration from backend/app/config.py and maps FLASK_ENV to a concrete configuration object.


## API surface (high-level)
The application exposes several blueprints in backend/app/api/:
- auth.py — login, register, token management (JWT)
- customers.py — CRUD for customer entities
- predictions.py — submit prediction requests, query results
- alerts.py — create/acknowledge alerts and subscriptions
- reports.py — generate and download PDF reports
- dashboard.py, weather.py — supporting endpoints for the frontend

When the backend is running, an OpenAPI (Swagger) interface is available via Flask-Smorest to inspect schemas and try endpoints.


## Operational notes
- Celery tasks run with the Flask app context — inspect backend/app/__init__.py and backend/app/extensions.py for wiring.
- Use Alembic for migrations if you modify models (alembic is listed in backend/requirements.txt).
- Report generation uses ReportLab (PDF) — heavy tasks should be run via Celery.


## Contributing
- Use feature branches and open Pull Requests with meaningful descriptions.
- Add/maintain tests in backend/tests and ml/tests when relevant.
- Document ML experiments and model formats in ml/README.md if adding models.


## License
If this repository does not already include a LICENSE file, add one before releasing. Common choices: MIT, Apache-2.0.


## Contact / Support
For questions or to propose changes, open an issue or PR in this repository.


---

This README was generated and tailored for the DeepGuard repository to provide a professional, actionable project overview and developer guide.
