"""
End-to-end job: target -> SPHEREx frames (per epoch x detector) + spectrum + light curve.

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict

import numpy as np
from astropy.time import Time

import catalogs as cat
import spherex_core as sx

RESULTS_DIR = sx.ROOT / "data" / "results"
_CUTOUT_LRU: "OrderedDict[str, list[sx.Cutout]]" = OrderedDict()
_LRU_LOCK = threading.Lock()
PIPELINE_VERSION = 5
PREVIEW_PER_CELL = 3   # images per (visit, detector) in a preview; 3 still allows a median


def job_key(p: dict) -> str:
    sig = json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in sorted(p.items())}
                     | {"v": PIPELINE_VERSION})
    return hashlib.sha1(sig.encode()).hexdigest()[:16]


def frames_key(p: dict) -> str:
    """Cache key of a sky-position job. `preview`, `start` and `end` only enter the key when set,
    so the keys of full results (including the pre-computed demo targets) are the same as before
    these options existed."""
    return job_key({k: v for k, v in p.items() if k != "name" and (k not in ("preview", "start", "end") or v)})


def cached_result(key: str) -> dict | None:
    f = RESULTS_DIR / f"{key}.json"
    return json.loads(f.read_text()) if f.exists() else None


def result_from_cached_full(p: dict) -> dict | None:
    """A date range on a field whose full result without dates is already stored: answer from
    that result instead of asking the archive again (it can be slow or down, and the stored demo
    targets should keep working then). Done by visit: a visit that overlaps the range is kept
    whole. Returns None if there is no stored full result."""
    full = cached_result(frames_key(p | {"start": None, "end": None, "preview": False}))
    if not full:
        return None
    lo, hi = p.get("start") or "0000", p.get("end") or "9999"        # ISO dates compare as text
    keep = {e["epoch"] for e in full["epochs"] if e["date_end"] >= lo and e["date_start"] <= hi}
    if not keep:
        raise RuntimeError(f"No SPHEREx images of this position in the chosen dates. The images here "
                           f"run from {full['epochs'][0]['date_start']} to {full['epochs'][-1]['date_end']}.")
    res = full | {k: [x for x in full[k] if x["epoch"] in keep]
                  for k in ("epochs", "frames", "images", "points", "lightcurve")}
    res["key"] = frames_key(p | {"preview": False})
    res["stats"] = full["stats"] | {"n_total": sum(e["n_available"] for e in res["epochs"]),
                                    "n_downloaded": len(res["images"]), "n_used": len(res["images"]),
                                    "rejected": {"failed": 0, "transient": 0}, "seconds": 0.0}
    (RESULTS_DIR / f"{res['key']}.json").write_text(json.dumps(res))
    return res


def _remember(key: str, cutouts: list[sx.Cutout]):
    with _LRU_LOCK:
        _CUTOUT_LRU[key] = cutouts
        _CUTOUT_LRU.move_to_end(key)
        while len(_CUTOUT_LRU) > 4:
            _CUTOUT_LRU.popitem(last=False)


def cutouts_for(key: str, params: dict) -> list[sx.Cutout]:
    """Cutouts of a finished job (memory, else re-read from the disk cache)."""
    with _LRU_LOCK:
        if key in _CUTOUT_LRU:
            return _CUTOUT_LRU[key]
    res = cached_result(key)
    if not res:
        return []
    ra0, dec0, size = res["grid"]["crval"][0], res["grid"]["crval"][1], res["fov_arcmin"] / 60
    cutouts = []
    for im in res["images"]:
        rec = sx.ImageRecord(uri=im["uri"], mjd=im["mjd"], det=im["det"], epoch=im["epoch"])
        path = sx.fetch_cutout(sx.cutout_url(rec, ra0, dec0, size))
        c = sx.load_cutout(rec, path) if path else None
        if c is not None:
            cutouts.append(c)
    _remember(key, cutouts)
    return cutouts


def target_track(p: dict, mjds: list[float]) -> list[tuple[float, float]]:
    return [cat.propagate(p["ra"], p["dec"], p.get("pmra", 0), p.get("pmdec", 0),
                          p.get("ref_epoch", 2000.0), cat.mjd_to_jyear(m)) for m in mjds]


def spectrum_and_lightcurve(cutouts, positions_by_epoch=None, ra=None, dec=None) -> dict:
    """Photometry at a fixed (ra, dec) or at a moving target position per epoch."""
    pts = []
    for c in cutouts:
        if positions_by_epoch is not None:
            r, d = positions_by_epoch[c.rec.epoch]
        else:
            r, d = ra, dec
        ph = sx.photometry_at(c, r, d)
        if ph is not None:
            pts.append(ph)
    pts.sort(key=lambda q: (q["wavelength_um"] or 0))
    # light curve: robust median per (epoch, detector)
    lc = []
    cells: dict = {}
    for q in pts:
        if q["good"]:
            cells.setdefault((q["epoch"], q["det"]), []).append(q)
    for (ep, det), qs in sorted(cells.items()):
        f = np.array([q["flux_mjy"] for q in qs])
        lc.append({"epoch": ep, "det": det, "mjd": float(np.mean([q["mjd"] for q in qs])),
                   "flux_mjy": float(np.median(f)),
                   "err_mjy": float(1.253 * np.std(f) / np.sqrt(len(f))) if len(f) > 1 else None,
                   "n": len(qs)})
    return {"points": pts, "lightcurve": lc}


def run_frames_job(p: dict, progress) -> dict:
    """p: ra, dec, pmra, pmdec, ref_epoch, fov_arcmin, max_per_cell, budget, name, preview, start, end."""
    t0 = time.time()
    key = frames_key(p)
    size_deg = p["fov_arcmin"] / 60.0

    # Centre the field on the target's position in the middle of the SPHEREx data range.
    progress("query", 0, 1, "Searching the SPHEREx archive (IRSA)...")
    ra_mid, dec_mid = cat.propagate(p["ra"], p["dec"], p.get("pmra", 0), p.get("pmdec", 0),
                                    p.get("ref_epoch", 2000.0), 2025.9)
    records = sx.find_images(ra_mid, dec_mid)
    if not records:
        raise RuntimeError("No SPHEREx images cover this position yet.")
    if p.get("start") or p.get("end"):
        # Optional date range (YYYY-MM-DD, end date included). Applied to the archive listing,
        # so images outside the range are never downloaded.
        lo = Time(p["start"]).mjd if p.get("start") else -np.inf
        hi = Time(p["end"]).mjd + 1 if p.get("end") else np.inf
        first, last = (Time(m, format="mjd").iso[:10] for m in (records[0].mjd, records[-1].mjd))
        records = [r for r in records if lo <= r.mjd < hi]
        if not records:
            raise RuntimeError(f"No SPHEREx images of this position in the chosen dates. "
                               f"The images here run from {first} to {last}.")
    epochs = sx.group_epochs(records)
    n_total = len(records)
    chosen = sx.budget_select(records, p.get("max_per_cell", 8), p.get("budget", 260))
    if p.get("preview"):
        # Quick first look: fewer images per (visit, detector). Picked from the full selection,
        # so the full job that follows finds these cutouts already on disk.
        chosen = sx.budget_select(chosen, PREVIEW_PER_CELL, p.get("budget", 260))
    progress("query", 1, 1, f"{n_total} images in {len(epochs)} visits; downloading {len(chosen)}")

    paths = sx.fetch_all(chosen, ra_mid, dec_mid, size_deg,
                         progress=lambda i, n: progress("download", i, n, f"Downloading cutouts {i}/{n}"))

    progress("process", 0, 1, "Cleaning images (zodiacal light, bad pixels)...")
    cutouts, rejected = [], {"failed": 0, "transient": 0}
    for rec in chosen:
        path = paths.get(rec.uri)
        c = sx.load_cutout(rec, path) if path else None
        if c is None:
            rejected["failed"] += 1
        elif c.n_transient > sx.MAX_TRANSIENT_PIXELS:
            rejected["transient"] += 1
        else:
            cutouts.append(c)
    if not cutouts:
        raise RuntimeError("All cutouts failed to download; IRSA may be overloaded. Try again shortly.")
    _remember(key, cutouts)

    progress("process", 0, 1, "Aligning images on a common north-up grid...")
    grid, shape = sx.make_grid(ra_mid, dec_mid, size_deg)
    frames = sx.build_frames(cutouts, grid, shape)

    used_epochs = sorted({c.rec.epoch for c in cutouts})
    ep_meta = []
    for ep in used_epochs:
        cs = [c for c in cutouts if c.rec.epoch == ep]
        mjds = [c.rec.mjd for c in cs]
        ep_meta.append({"epoch": ep, "mjd": float(np.mean(mjds)),
                        "jyear": cat.mjd_to_jyear(float(np.mean(mjds))),
                        "date_start": Time(min(mjds), format="mjd").iso[:10],
                        "date_end": Time(max(mjds), format="mjd").iso[:10],
                        "n_images": len(cs),
                        "n_available": sum(1 for r in records if r.epoch == ep),
                        "dets": sorted({c.rec.det for c in cs})})
    track = target_track(p, [e["mjd"] for e in ep_meta])
    pos_by_epoch = {e["epoch"]: t for e, t in zip(ep_meta, track)}

    progress("process", 1, 1, "Measuring the spectrum and light curve...")
    phot = spectrum_and_lightcurve(cutouts, positions_by_epoch=pos_by_epoch)

    result = {
        "key": key, "preview": bool(p.get("preview")), "name": p.get("name"), "target": {k: p.get(k) for k in ("ra", "dec", "pmra", "pmdec", "ref_epoch")},
        "fov_arcmin": p["fov_arcmin"],
        "grid": {"crval": [ra_mid, dec_mid], "crpix": list(grid.wcs.crpix), "cdelt": list(grid.wcs.cdelt),
                 "shape": list(shape)},
        "epochs": [e | {"target_ra": t[0], "target_dec": t[1]} for e, t in zip(ep_meta, track)],
        "frames": [{"epoch": ep, "det": det, "n": n, "data": sx.b64f32(arr)}
                   for (ep, det), (arr, n) in sorted(frames.items())],
        "images": [{"uri": c.rec.uri, "mjd": c.rec.mjd, "det": c.rec.det, "epoch": c.rec.epoch,
                    "obs_id": c.rec.obs_id} for c in cutouts],
        "stats": {"n_total": n_total, "n_downloaded": len(chosen), "n_used": len(cutouts),
                  "rejected": rejected, "seconds": round(time.time() - t0, 1)},
        **phot,
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / f"{key}.json").write_text(json.dumps(result))
    return result
