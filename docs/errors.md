# Error Log

## [2026-04-25] Task 5 — kaleido hangs indefinitely on Windows (Stage 3 smoke test)

**Symptom:** `python -m src.signal_engine.cli` (and any `fig.write_image()` call) hung
indefinitely — no output, no error, no timeout. Background processes ran for 5–10 minutes
with no PNGs produced.

**Root cause:** kaleido 0.2.x uses a headless Chromium subprocess for PNG rendering.
On Windows, the Python ↔ subprocess pipe communication deadlocks: Chromium starts but
never sends the ready signal back over stdout, so `_ensure_kaleido()` blocks forever.
This is a known Windows-specific bug in the kaleido 0.2.x release series.

**Diagnosis steps:**
1. Confirmed kaleido executable exists and starts (`kaleido.cmd --help` returned JSON response).
2. Confirmed scope creates without error (`PlotlyScope()` succeeded).
3. Confirmed the hang is in the first `write_image` call, not import time.
4. Identified pipe deadlock as root cause from kaleido issue tracker behaviour.

**Fix:** Downgrade to `kaleido==0.1.0post1`, which uses a different (non-Chromium) rendering
path. The `fig.write_image()` API is identical — no code changes needed, only the package
version.

```
pip install kaleido==0.1.0post1
```

`requirements.txt` updated from `kaleido==0.2.1` → `kaleido==0.1.0post1` in commit b9f5f3c.

**Affected environment:** Windows 11, Python 3.9, kaleido 0.2.1, plotly 5.22.0.
