FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install -U pip && pip install -r requirements.txt -r requirements-dev.txt || true

COPY . .

# Build static site (mkdocs) and SOTA; skip failures for optional tools
RUN bash -lc "python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt && PYTHONPATH=. .venv/bin/python scripts/build_state_of_the_art.py || true && mkdocs build --strict || true"

EXPOSE 8000
CMD ["bash","-lc","USE_TLS=0 bash scripts/start_web.sh && tail -f /dev/null"]
