FROM mambaorg/micromamba:1.5
COPY ../backend/env.yml /tmp/env.yml
RUN micromamba create -n app -f /tmp/env.yml && micromamba clean --all --yes
SHELL ["bash", "-lc"]
WORKDIR /app
COPY ../backend/app /app/app
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["bash", "-lc", "micromamba run -n app uvicorn app.main:app --host 0.0.0.0 --port 8000"]