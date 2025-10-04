Backend (FastAPI) for Weather Likelihood

Prereqs

Mambaforge/Conda on Windows
Earthdata Login and %USERPROFILE%.netrc
Run

mamba env create -f env.yml
mamba activate weather
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000