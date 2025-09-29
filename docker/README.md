# Dockerised Repro Environment

This container image captures the minimal toolchain required to run `make repro`
(benchmarks, Bullet holdout, BAO validation, SOTA rebuild). Usage:

```bash
# Build once (tagged "gravitation-repro")
docker build -t gravitation-repro -f docker/Dockerfile .

# Mount the repo and execute the reproducibility check
docker run --rm -it \
  -v "$(pwd)":/workspace \
  -w /workspace \
  gravitation-repro \
  bash -lc "make repro"
```

The Dockerfile installs the runtime dependencies declared in `requirements.txt`
and the dev extras from `requirements-dev.txt`. CLASS (via `classy==3.3.2.0`),
scipy, astropy, and FFTW/OpenBLAS toolchain support are all baked in so the
pipeline is deterministic.
