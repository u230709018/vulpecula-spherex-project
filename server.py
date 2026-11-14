"""SPHEREx blink viewer - backend.

Run:  py -m uvicorn server:app --port 8000
Open: http://localhost:8000
"""
import hashlib
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
from astropy.io import fits
from astropy.wcs import WCS
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse

HERE = Path(__file__).parent
CACHE = HERE / "cache"
(CACHE / "hdr").mkdir(parents=True, exist_ok=True)
(CACHE / "cut").mkdir(parents=True, exist_ok=True)
(CACHE / "search").mkdir(parents=True, exist_ok=True)

TAP = "https://irsa.ipac.caltech.edu/TAP/sync"
S3 = "https://nasa-irsa-spherex.s3.amazonaws.com/"
OUT_SCALE = 3.0  # arcsec per output pixel (SPHEREx native is ~6.15)
HEADER_BYTES = 34560  # headers seen so far end at 25920-28800 bytes

app = FastAPI()
POOL = ThreadPoolExecutor(16)
_local = threading.local()


def http_get(url, start=None, end=None):
    """GET with keep-alive per thread, optional byte range, 3 attempts."""
    if not hasattr(_local, "session"):
        _local.session = requests.Session()
    headers = {"Range": f"bytes={start}-{end}"} if start is not None else {}
    for attempt in range(3):
        try:
            r = _local.session.get(url, headers=headers, timeout=(10, 60))
            r.raise_for_status()
            return r
        except requests.RequestException:
            if attempt == 2:
                raise


def sha(text):
    return hashlib.sha1(text.encode()).hexdigest()


def s3_url(uri):
    return S3 + uri.removeprefix("ibe/data/spherex/")


@app.get("/")
def index():
    return FileResponse(HERE / "index.html")


@app.get("/api/search")
def search(ra: float, dec: float):
    """All SPHEREx spectral images whose footprint contains the position."""
    # The archive query is slow and sometimes times out, so keep each answer for a day.
    f = CACHE / "search" / (sha(f"{ra}|{dec}") + ".json")
    if f.exists() and time.time() - f.stat().st_mtime < 86400:
        return json.loads(f.read_text())
    query = (
        "SELECT a.uri, p.energy_bandpassname, p.time_bounds_lower "
        "FROM spherex.artifact a JOIN spherex.plane p ON a.planeid = p.planeid "
        f"WHERE CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly) = 1 "
        "AND a.uri LIKE '%/level2/%'"
    )
    text = http_get(f"{TAP}?FORMAT=csv&QUERY={quote(query)}").text
    rows = [line.split(",") for line in text.strip().splitlines()[1:]]
    out = [{"uri": u, "band": b[-2:], "mjd": float(t)} for u, b, t in rows]
    out.sort(key=lambda r: r["mjd"])
    f.write_text(json.dumps(out))
    return out


def load_wcs(uri):
    """Read only the FITS headers of an image (first ~35 kB) and build its WCS.

    Returns (wcs, byte offset of the image data, NAXIS1, NAXIS2).
    The image is the first extension, stored as uncompressed big-endian float32.
    """
    f = CACHE / "hdr" / (sha(uri) + ".bin")
    if f.exists():
        raw = f.read_bytes()
    else:
        raw = http_get(s3_url(uri), 0, HEADER_BYTES - 1).content
        f.write_bytes(raw)
    primary = fits.Header.fromstring(raw)
    primary_len = len(primary.tostring())
    hdr = fits.Header.fromstring(raw[primary_len:])
    offset = primary_len + len(hdr.tostring())
    if offset > HEADER_BYTES:
        raise RuntimeError(f"FITS header longer than {HEADER_BYTES} bytes: {uri}")
    return WCS(hdr, naxis=2), offset, hdr["NAXIS1"], hdr["NAXIS2"]


def cutout(uri, ra, dec, fov):
    """North-up, east-left cutout centred on (ra, dec); None if off the detector."""
    wcs, offset, nx, ny = load_wcs(uri)

    # Sky coordinates of every output pixel: tangent plane centred on the target.
    n = int(round(fov / OUT_SCALE))
    t = (n / 2 - 0.5 - np.arange(n)) * np.radians(OUT_SCALE / 3600)
    xi, eta = np.meshgrid(t, t)  # xi: east (to the left), eta: north (up)
    d0 = np.radians(dec)
    den = np.cos(d0) - eta * np.sin(d0)
    sky_ra = ra + np.degrees(np.arctan2(xi, den))
    sky_dec = np.degrees(np.arctan2(np.sin(d0) + eta * np.cos(d0), np.hypot(xi, den)))

    # Where those sky positions fall on this detector image.
    x, y = wcs.all_world2pix(sky_ra, sky_dec, 0)
    x0, x1 = int(np.floor(x.min())), int(np.floor(x.max())) + 2
    y0, y1 = int(np.floor(y.min())), int(np.floor(y.max())) + 2
    if x0 < 0 or y0 < 0 or x1 > nx or y1 > ny:
        return None

    # Download only the needed pixels: one small byte range per detector row.
    url = s3_url(uri)

    def row(j):
        start = offset + 4 * (j * nx + x0)
        return np.frombuffer(http_get(url, start, start + 4 * (x1 - x0) - 1).content, ">f4")

    block = np.array(list(POOL.map(row, range(y0, y1))))

    # Bilinear interpolation onto the output grid.
    fx, fy = x - x0, y - y0
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    wx, wy = fx - ix, fy - iy
    return (
        block[iy, ix] * (1 - wx) * (1 - wy)
        + block[iy, ix + 1] * wx * (1 - wy)
        + block[iy + 1, ix] * (1 - wx) * wy
        + block[iy + 1, ix + 1] * wx * wy
    )


@app.get("/api/cutout")
def api_cutout(uri: str, ra: float, dec: float, fov: float = 120):
    """Raw little-endian float32 n*n pixels (MJy/sr); empty body if off detector."""
    if not re.fullmatch(r"ibe/data/spherex/[\w./-]+\.fits", uri) or ".." in uri:
        raise HTTPException(400, "Bad uri")
    fov = min(max(fov, 30), 600)
    f = CACHE / "cut" / (sha(f"{uri}|{ra}|{dec}|{fov}") + ".f32")
    if f.exists():
        data = f.read_bytes()
    else:
        img = cutout(uri, ra, dec, fov)
        data = b"" if img is None else img.astype("<f4").tobytes()
        f.write_bytes(data)
    return Response(data, media_type="application/octet-stream")
