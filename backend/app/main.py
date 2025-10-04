from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Weather Likelihood API", version="0.1.0")

app.add_middleware(
CORSMiddleware,
allow_origins=[""], # tighten in prod
allow_methods=[""],
allow_headers=["*"],
)

@app.get("/health")
def health():
return {"status": "ok"}