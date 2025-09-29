# Reproducible environment for `make repro`
FROM mcr.microsoft.com/devcontainers/python:1-3.11

# System packages needed for classy/scipy/astropy builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gfortran build-essential cmake pkg-config \
    libfftw3-dev libopenblas-dev liblapack-dev \
    git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Optional: bring the repo in at runtime via mount. Provide default entrypoint.
CMD ["bash"]
