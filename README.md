Weather Likelihood (MVP)
Personalized dashboard using NASA Earth observations to estimate probability of exceeding user-defined thresholds by day-of-year.

Backend: FastAPI + xarray (NASA GES DISC, OPeNDAP/CMR)
Frontend: React + Vite + MapLibre
Notebooks: Validation with Giovanni / Data Rods
Infra: Docker Compose
Compliance
NASA does not endorse any non-U.S. Government entity and is not responsible for information contained on non-U.S. Government websites. For non-U.S. Government websites, users must comply with that site’s data use parameters.

Quick start

See docs/Architecture.md and docs/API.md
Backend dev: cd backend && uvicorn app.main:app --reload
Frontend dev: cd frontend && pnpm dev
Docker: cd infra && docker compose up --build
File: NOTICE.md
NASA does not endorse any non-U.S. Government entity and is not responsible for information contained on non-U.S. Government websites. For non-U.S. Government websites, users must comply with that site’s data use parameters.