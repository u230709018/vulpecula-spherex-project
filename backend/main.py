"""
FastAPI server for the SPHEREx time-machine web tool.

Run:  .venv/bin/uvicorn main:app --app-dir backend --port 8000

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
from __future__ import annotations

import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import catalogs as cat
import moving as mv
import pipeline as pl
import spherex_core as sx

app = FastAPI(title="SPHEREx Time Machine API")
app.add_middleware(GZipMiddleware, minimum_size=2000)
FRONTEND = sx.ROOT / "frontend"

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
EXECUTOR = ThreadPoolExecutor(max_workers=2)


class FramesRequest(BaseModel):
    ra: float
    dec: float
    pmra: float = 0.0
    pmdec: float = 0.0
    ref_epoch: float = 2000.0
    fov_arcmin: float = Field(5.0, ge=1.0, le=20.0)
    max_per_cell: int = Field(8, ge=2, le=40)
    budget: int = Field(260, ge=20, le=1200)
    name: str | None = None
    start: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")   # only images from this date on
    end: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")     # ... and up to this date (inclusive)
    preview: bool = False             # quick first look with fewer images; see pipeline.PREVIEW_PER_CELL


class MovingRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    start: str | None = None          # YYYY-MM-DD
    end: str | None = None
    fov_arcmin: float = Field(4.0, ge=1.0, le=15.0)
    max_frames: int = Field(40, ge=4, le=120)


def _set(job_id, **kw):
    with JOBS_LOCK:
        JOBS[job_id].update(kw)


def _run(job_id: str, params: dict, fn=None):
    def progress(stage, i, n, msg):
        _set(job_id, stage=stage, done=i, total=n, message=msg)
    try:
        res = (fn or pl.run_frames_job)(params, progress)
        _set(job_id, status="done", result_key=res["key"], message="Done")
    except mv.AmbiguousName as err:
        _set(job_id, status="error", message=str(err), candidates=err.candidates)
    except Exception as err:
        traceback.print_exc()
        _set(job_id, status="error", message=str(err))


@app.get("/api/targets")
def targets():
    return [{k: t[k] for k in ("id", "name", "ra", "dec", "pmra", "pmdec", "ref_epoch", "kind", "note")}
            for t in cat.TARGETS]


@app.get("/api/resolve")
def resolve(q: str = Query(..., min_length=1)):
    try:
        r = cat.resolve(q)
    except cat.ResolverDown:
        raise HTTPException(503, "The name services (SIMBAD, CDS Sesame) cannot be reached right now. "
                                 "Please enter coordinates instead.")
    if r is None:
        raise HTTPException(404, f"No object called '{q}' was found in SIMBAD or CDS Sesame.")
    return r


@app.post("/api/frames")
def frames(req: FramesRequest):
    params = req.model_dump()
    # A finished full-quality result always wins, also when only a preview was asked for.
    for key in (pl.frames_key(params | {"preview": False}), pl.frames_key(params)):
        if pl.cached_result(key):
            return {"status": "done", "result_key": key}
    if params["start"] or params["end"]:
        # Date range on a field that is already stored without dates: no need to ask the archive.
        try:
            res = pl.result_from_cached_full(params)
        except RuntimeError as err:
            raise HTTPException(404, str(err))
        if res:
            return {"status": "done", "result_key": res["key"]}
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "running", "stage": "queued", "done": 0, "total": 1,
                        "message": "Queued...", "params": params}
    EXECUTOR.submit(_run, job_id, params)
    return {"status": "running", "job_id": job_id}


@app.post("/api/moving")
def moving(req: MovingRequest):
    params = req.model_dump()
    key = "mv_" + pl.job_key(params)
    if pl.cached_result(key):
        return {"status": "done", "result_key": key}
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "running", "stage": "queued", "done": 0, "total": 1,
                        "message": "Queued...", "params": params}
    EXECUTOR.submit(_run, job_id, params, mv.run_moving_job)
    return {"status": "running", "job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    with JOBS_LOCK:
        j = JOBS.get(job_id)
        if not j:
            raise HTTPException(404, "Unknown job")
        return {k: v for k, v in j.items() if k != "params"}


@app.get("/api/result/{key}")
def result(key: str):
    r = pl.cached_result(key)
    if not r:
        raise HTTPException(404, "Result not found")
    return JSONResponse(r)


@app.get("/api/spectrum/{key}")
def spectrum(key: str, ra: float, dec: float):
    """Spectrum + light curve at any position inside an already loaded field."""
    cutouts = pl.cutouts_for(key, {})
    if not cutouts:
        raise HTTPException(404, "Field not loaded")
    return pl.spectrum_and_lightcurve(cutouts, ra=ra, dec=dec)


@app.get("/api/gaia")
def gaia(ra: float, dec: float, radius_deg: float = Query(..., gt=0, le=0.3),
         jyears: str = Query(...)):
    return cat.gaia_sources(ra, dec, radius_deg, [float(x) for x in jyears.split(",")])


@app.get("/api/asteroids")
def asteroids(ra: float, dec: float, half_width_deg: float = Query(..., gt=0, le=0.3),
              mjds: str = Query(...)):
    out = []
    for m in [float(x) for x in mjds.split(",")][:24]:
        try:
            out.append({"mjd": m, "objects": cat.known_small_bodies(ra, dec, half_width_deg, m)})
        except Exception as err:
            out.append({"mjd": m, "objects": [], "error": str(err)[:200]})
    return out


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="static")
