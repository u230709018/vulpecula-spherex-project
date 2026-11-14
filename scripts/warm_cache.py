"""
Pre-compute (warm the cache for) the built-in demo targets so the demo is instant.

Usage: .venv/bin/python scripts/warm_cache.py [fov_arcmin ...]

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
import catalogs as cat  # noqa: E402
import pipeline as pl   # noqa: E402

fovs = [float(x) for x in sys.argv[1:]] or [5.0]
for t in cat.TARGETS:
    for fov in fovs:
        p = {k: t[k] for k in ("ra", "dec", "pmra", "pmdec", "ref_epoch")} | {
            "fov_arcmin": fov, "max_per_cell": 8, "budget": 260}
        key = pl.job_key(p)
        if pl.cached_result(key):
            print(f"{t['name']} fov={fov}: cached ({key})", flush=True)
            continue
        t0 = time.time()
        try:
            r = pl.run_frames_job(p | {"name": t["name"]}, lambda *a: None)
            print(f"{t['name']} fov={fov}: OK {r['stats']} in {time.time()-t0:.0f}s ({key})", flush=True)
        except Exception as err:
            print(f"{t['name']} fov={fov}: FAILED {err}", flush=True)
