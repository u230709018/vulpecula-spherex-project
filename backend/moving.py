"""
Solar System object mode: find SPHEREx images of an asteroid/comet with IRSA MOST
(Moving Object Search Tool) and build object-centred frames + its spectrum.

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
from __future__ import annotations

import hashlib

import json
import re
import time
import urllib.parse
import urllib.request

import numpy as np
from astropy.table import Table
from astropy.time import Time

import catalogs as cat
import pipeline as pl
import spherex_core as sx

MOST_URL = "https://irsa.ipac.caltech.edu/cgi-bin/MOST/nph-most"
MISSION_START = "2025-04-20"


class AmbiguousName(Exception):
    def __init__(self, candidates):
        super().__init__("Several objects match this name; pick one.")
        self.candidates = candidates


def most_query(name: str, start: str, end: str) -> Table:
    """Run IRSA MOST for SPHEREx. `name` may be a name/number or a NAIF ID ('20000004:NID')."""
    params = {"catalog": "spherex", "obs_begin": start.replace("-", " "), "obs_end": end.replace("-", " "),
              "output_mode": "Brief"}
    if name.endswith(":NID"):
        params |= {"input_type": "naifid_input", "obj_naifid": name[:-4]}
    else:
        params |= {"input_type": "name_input", "obj_name": name}
    url = MOST_URL + "?" + urllib.parse.urlencode(params)
    cache = pl.RESULTS_DIR / f"most_{hashlib.sha1(url.encode()).hexdigest()[:12]}.tbl"
    if cache.exists():
        txt = cache.read_text()
    else:
        with urllib.request.urlopen(urllib.request.Request(url, headers=cat.UA), timeout=240) as r:
            txt = r.read().decode("utf-8", "replace")
    if "Multiple matches" in txt or "Object Name Error" in txt:
        cands = re.findall(r"^\s*(.+?), Object Type=(\w+), NAIF ID=(\d+)", txt, re.M)
        if cands:
            raise AmbiguousName([{"name": n.strip(), "type": t, "naif": f"{i}:NID"} for n, t, i in cands])
        raise RuntimeError("MOST could not resolve this object name.")
    lines = [l for l in txt.splitlines() if l.startswith(("|", "\\")) or l.strip()[:1].isdigit() or l.startswith(" ")]
    tab = Table.read("\n".join(lines), format="ascii.ipac")
    pl.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(txt)
    meta = {}
    for m in re.finditer(r'^\\(\w+)\s*=\s*"([^"]*)"', txt, re.M):
        meta[m.group(1)] = m.group(2).strip()
    tab.meta["most"] = meta
    return tab


def _uri(u: str) -> str:
    return re.sub(r"^https?://irsa\.ipac\.caltech\.edu/", "", u.strip())


def _det(u: str) -> str:
    m = re.search(r"_\d+D(\d)_spx", u)
    return f"D{m.group(1)}" if m else "D?"


def run_moving_job(p: dict, progress) -> dict:
    """p: name, start, end, fov_arcmin, max_frames."""
    t0 = time.time()
    key = "mv_" + pl.job_key({k: v for k, v in p.items()})
    progress("query", 0, 1, f"Computing the orbit of {p['name']} and searching SPHEREx images (IRSA MOST)...")
    tab = most_query(p["name"], p.get("start") or MISSION_START, p.get("end") or Time.now().iso[:10])
    if len(tab) == 0:
        raise RuntimeError("SPHEREx has not observed this object in the selected period.")
    rows = sorted(({"uri": _uri(str(r["uri"])), "mjd": float(r["mjd_start"]), "ra": float(r["ra_obj"]),
                    "dec": float(r["dec_obj"]), "vmag": float(r["vmag"]) if r["vmag"] is not np.ma.masked else None,
                    "geo": float(r["geo_dist"]), "sun": float(r["sun_dist"])}
                   for r in tab), key=lambda q: q["mjd"])
    n_all = len(rows)
    if n_all > p["max_frames"]:
        idx = np.linspace(0, n_all - 1, p["max_frames"]).round().astype(int)
        rows = [rows[i] for i in sorted(set(idx))]
    size = p["fov_arcmin"] / 60.0
    recs = [sx.ImageRecord(uri=q["uri"], mjd=q["mjd"], det=_det(q["uri"]), epoch=i) for i, q in enumerate(rows)]
    urls = [sx.cutout_url(r, q["ra"], q["dec"], size) for r, q in zip(recs, rows)]
    progress("query", 1, 1, f"{n_all} SPHEREx images contain {p['name']}; downloading {len(recs)}")
    from concurrent.futures import ThreadPoolExecutor
    paths = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, path in enumerate(pool.map(sx.fetch_cutout, urls), 1):
            paths.append(path)
            progress("download", i, len(urls), f"Downloading cutouts {i}/{len(urls)}")

    progress("process", 0, 1, "Centring every frame on the moving object...")
    frames, ep_meta, cutouts, pos = [], [], [], {}
    shape = None
    for r, q, path in zip(recs, rows, paths):
        c = sx.load_cutout(r, path) if path else None
        if c is None or c.n_transient > sx.MAX_TRANSIENT_PIXELS:
            continue
        grid, shape = sx.make_grid(q["ra"], q["dec"], size)
        fr = sx.build_frames([c], grid, shape)[(r.epoch, r.det)][0]
        k = len(ep_meta)
        r.epoch = k
        c.rec.epoch = k
        cutouts.append(c)
        pos[k] = (q["ra"], q["dec"])
        frames.append({"epoch": k, "det": r.det, "n": 1, "data": sx.b64f32(fr)})
        d = Time(q["mjd"], format="mjd").iso
        ep_meta.append({"epoch": k, "mjd": q["mjd"], "jyear": cat.mjd_to_jyear(q["mjd"]),
                        "date_start": d[:16], "date_end": d[:16], "n_images": 1, "n_available": 1, "dets": [r.det],
                        "target_ra": q["ra"], "target_dec": q["dec"], "vmag": q["vmag"],
                        "geo_au": q["geo"], "sun_au": q["sun"]})
    if not frames:
        raise RuntimeError("Cutouts could not be downloaded; IRSA may be overloaded. Try again shortly.")
    progress("process", 1, 1, "Measuring the object's spectrum...")
    phot = pl.spectrum_and_lightcurve(cutouts, positions_by_epoch=pos)
    g0, _ = sx.make_grid(ep_meta[0]["target_ra"], ep_meta[0]["target_dec"], size)
    meta = tab.meta.get("most", {})
    result = {
        "key": key, "mode": "moving", "name": meta.get("object_name") or p["name"],
        "target": {"ra": ep_meta[0]["target_ra"], "dec": ep_meta[0]["target_dec"], "pmra": 0, "pmdec": 0, "ref_epoch": 2000},
        "fov_arcmin": p["fov_arcmin"],
        "grid": {"crval": list(g0.wcs.crval), "crpix": list(g0.wcs.crpix), "cdelt": list(g0.wcs.cdelt), "shape": list(shape)},
        "epochs": ep_meta, "frames": frames,
        "images": [{"uri": c.rec.uri, "mjd": c.rec.mjd, "det": c.rec.det, "epoch": c.rec.epoch, "obs_id": c.rec.obs_id}
                   for c in cutouts],
        "orbit": {k: meta.get(k) for k in ("object_name", "eccentricity", "inclination", "perihelion_distance",
                                           "semimajor_axis", "perihelion_time") if meta.get(k)},
        "stats": {"n_total": n_all, "n_downloaded": len(recs), "n_used": len(cutouts),
                  "rejected": {"failed": len(recs) - len(cutouts), "transient": 0}, "seconds": round(time.time() - t0, 1)},
        **phot,
    }
    (pl.RESULTS_DIR / f"{key}.json").write_text(json.dumps(result))
    return result
