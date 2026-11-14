"""
SPHEREx time-series core.

Pipeline:
  1. find_images()     IRSA TAP: every SPHEREx spectral image covering a sky position
                       (DR1 + QR3 + deep fields, no ingestion lag -> new data appears automatically)
  2. group_epochs()    split observations into visits ("epochs")
  3. budget_select()   cap downloads per (epoch, detector) so deep fields stay fast
  4. fetch_all()       IRSA cutout service (parallel, retried, cached on disk)
  5. load_cutout()     IMAGE - ZODI, mask bad FLAGS bits, quality screening
  6. build_frames()    reproject onto a common north-up grid; one co-add per (epoch, detector)
  7. photometry_at()   aperture photometry at any position -> spectrum + light curve

Parts of this file were written with the assistance of an AI coding assistant
(Claude, Anthropic) and reviewed by the team. See README "Use of AI".
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import logging
import time
import urllib.error
import urllib.request
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS, FITSFixedWarning
from astroquery.ipac.irsa import Irsa
from reproject import reproject_interp

warnings.simplefilter("ignore", FITSFixedWarning)
logging.getLogger("astropy").setLevel(logging.ERROR)

IRSA_BASE = "https://irsa.ipac.caltech.edu/"
ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache"
PIXEL_SCALE_ARCSEC = 6.15
PIX_SR = (PIXEL_SCALE_ARCSEC / 206264.806) ** 2
MJYSR_TO_MJY_PER_PIX = PIX_SR * 1e9          # MJy/sr * sr -> MJy -> mJy
DETECTORS = ["D1", "D2", "D3", "D4", "D5", "D6"]
DETECTOR_BANDS = {"D1": (0.75, 1.09), "D2": (1.10, 1.62), "D3": (1.63, 2.41),
                  "D4": (2.42, 3.82), "D5": (3.83, 4.41), "D6": (4.42, 5.00)}

# FLAGS bits that make a pixel unusable (Explanatory Supplement Table 16).
# SOURCE (bit 21, "known source") is informational and NOT masked.
BAD_FLAGS = {"TRANSIENT", "OVERFLOW", "SUR_ERROR", "NONFUNC", "DICHROIC", "MISSING_DATA",
             "HOT", "COLD", "PHANMISS", "NONLINEAR", "PERSIST", "OUTLIER", "CROSSTALK",
             "GHOST", "GHOST_FPA", "GHOST_EXT", "STREAK", "BLOOM", "SNOWBALL", "HALO",
             "SATELLITE_HALO"}
# Flags worth warning users about when they sit on a candidate (can mimic movers).
ARTIFACT_FLAGS = {"GHOST", "GHOST_FPA", "GHOST_EXT", "STREAK", "CROSSTALK", "PERSIST",
                  "TRANSIENT", "SNOWBALL", "HALO", "BLOOM", "SATELLITE_HALO"}
SATURATION_FLAGS = {"OVERFLOW", "NONLINEAR"}
# For *display* only permanently bad pixels are masked; transients (cosmic rays, halos) are
# removed by the per-visit median when >= 3 images are available, so images stay hole-free.
DISPLAY_BAD_FLAGS = {"NONFUNC", "MISSING_DATA", "HOT", "COLD"}
MAX_TRANSIENT_PIXELS = 300_000   # Explanatory Supplement: frames above this are compromised


@dataclass
class ImageRecord:
    uri: str
    mjd: float
    det: str                  # "D1".."D6"
    epoch: int = -1

    @property
    def obs_id(self) -> str:
        name = self.uri.rsplit("/", 1)[-1]
        return name.replace("level2_", "").split("_spx")[0]


@dataclass
class Cutout:
    rec: ImageRecord
    image: np.ndarray            # MJy/sr, zodi-subtracted, bad pixels = NaN (strict, for photometry)
    display: np.ndarray          # same, only permanently bad pixels masked (for co-added frames)
    variance: np.ndarray
    flags: np.ndarray
    flag_bits: dict              # name -> bit
    wcs: WCS
    hdul_header: fits.Header     # IMAGE header (for spectral WCS)
    wave_table: object = None    # WCS-WAVE HDU (for spectral WCS)
    n_transient: int = 0
    _spec_wcs: WCS | None = field(default=None, repr=False)

    def wavelength_at(self, x: float, y: float) -> float | None:
        try:
            if self._spec_wcs is None:
                hdul = fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(header=self.hdul_header, name="IMAGE"),
                                     self.wave_table])
                self._spec_wcs = WCS(self.hdul_header, fobj=hdul, key="W")
                self._spec_wcs.sip = None
            wl, _bw = self._spec_wcs.pixel_to_world(x, y)
            return float(wl.to_value("um")) if hasattr(wl, "to_value") else float(wl)
        except Exception:
            return None

    def flag_names_at(self, xi: int, yi: int) -> list[str]:
        v = int(self.flags[yi, xi])
        return [n for n, b in self.flag_bits.items() if v & (1 << b)]


# --------------------------------------------------------------------------- #
# 1-3. Query, epochs, download budget
# --------------------------------------------------------------------------- #
def find_images(ra: float, dec: float) -> list[ImageRecord]:
    query = f"""
        SELECT a.uri, p.time_bounds_lower AS tmjd, p.energy_bandpassname AS band
        FROM spherex.artifact a JOIN spherex.plane p ON a.planeid = p.planeid
        WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
        ORDER BY p.time_bounds_lower
    """
    last = None
    for attempt in range(5):  # IRSA occasionally answers 503 under load
        try:
            table = Irsa.query_tap(query).to_table()
            return [ImageRecord(uri=str(r["uri"]), mjd=float(r["tmjd"]),
                                det=str(r["band"]).replace("SPHEREx-", "")) for r in table]
        except Exception as err:
            last = err
            time.sleep(3 * 2 ** attempt)
    raise RuntimeError(f"IRSA TAP query failed: {last}")


def group_epochs(records: list[ImageRecord], gap_days: float = 10.0,
                 max_span_days: float = 40.0) -> list[list[ImageRecord]]:
    """New epoch after a gap > gap_days, or when a visit would exceed max_span_days
    (keeps deep-field monitoring split into a usable light curve)."""
    records = sorted(records, key=lambda r: r.mjd)
    epochs: list[list[ImageRecord]] = []
    for rec in records:
        if (not epochs or rec.mjd - epochs[-1][-1].mjd > gap_days
                or rec.mjd - epochs[-1][0].mjd > max_span_days):
            epochs.append([])
        rec.epoch = len(epochs) - 1
        epochs[-1].append(rec)
    return epochs


def budget_select(records: list[ImageRecord], max_per_cell: int, total_budget: int) -> list[ImageRecord]:
    """Keep at most N images per (epoch, detector), evenly spread in time."""
    cells: dict[tuple[int, str], list[ImageRecord]] = {}
    for r in records:
        cells.setdefault((r.epoch, r.det), []).append(r)
    per_cell = max(2, min(max_per_cell, total_budget // max(1, len(cells))))
    chosen = []
    for recs in cells.values():
        if len(recs) <= per_cell:
            chosen += recs
        else:
            idx = np.linspace(0, len(recs) - 1, per_cell).round().astype(int)
            chosen += [recs[i] for i in sorted(set(idx))]
    return sorted(chosen, key=lambda r: r.mjd)


# --------------------------------------------------------------------------- #
# 4. Cutout download
# --------------------------------------------------------------------------- #
def cutout_url(rec: ImageRecord, ra: float, dec: float, size_deg: float) -> str:
    return f"{IRSA_BASE}{rec.uri}?center={ra:.6f},{dec:.6f}d&size={size_deg:.5f}"


def fetch_cutout(url: str, retries: int = 4) -> Path | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest()[:20] + ".fits")
    if path.exists() and path.stat().st_size > 0:
        return path
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                data = resp.read()
            tmp = path.with_suffix(f".part{attempt}")
            tmp.write_bytes(data)
            tmp.replace(path)
            return path
        except urllib.error.HTTPError as err:
            if err.code in (400, 404, 500):     # 500 = cutout does not overlap the image
                return None
            time.sleep(1.5 * 2 ** attempt)
        except (TimeoutError, urllib.error.URLError, http.client.IncompleteRead,
                http.client.RemoteDisconnected, ConnectionError):
            time.sleep(1.5 * 2 ** attempt)
    return None


def fetch_all(records, ra, dec, size_deg, workers=8, progress=None) -> dict[str, Path | None]:
    out: dict[str, Path | None] = {}
    urls = [(r.uri, cutout_url(r, ra, dec, size_deg)) for r in records]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, (uri, path) in enumerate(zip([u for u, _ in urls], pool.map(fetch_cutout, [u for _, u in urls])), 1):
            out[uri] = path
            if progress:
                progress(i, len(urls))
    return out


# --------------------------------------------------------------------------- #
# 5. Reading
# --------------------------------------------------------------------------- #
def load_cutout(rec: ImageRecord, path: Path) -> Cutout | None:
    try:
        with fits.open(path, memmap=False) as hdul:
            names = [h.name for h in hdul]
            if "IMAGE" not in names:
                return None
            hdr = hdul["IMAGE"].header.copy()
            n_tr = int(hdr.get("L2 N_TRANSIENT", hdr.get("HIERARCH L2 N_TRANSIENT", 0)) or 0)
            image = hdul["IMAGE"].data.astype(np.float32)
            if "ZODI" in names:
                image = image - hdul["ZODI"].data.astype(np.float32)
            var = hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in names else np.full_like(image, np.nan)
            flags = hdul["FLAGS"].data.astype(np.int64) if "FLAGS" in names else np.zeros(image.shape, np.int64)
            fhdr = hdul["FLAGS"].header if "FLAGS" in names else fits.Header()
            bits = {str(fhdr[k]): int(k[4:]) for k in fhdr["MSKN*"]} if "FLAGS" in names else {}
            wave = hdul["WCS-WAVE"].copy() if "WCS-WAVE" in names else None
    except Exception:
        return None
    def mask_of(names):
        m = 0
        for name, b in bits.items():
            if name in names:
                m |= 1 << b
        return m
    display = image.copy()
    display[((flags & mask_of(DISPLAY_BAD_FLAGS)) != 0) | ~np.isfinite(display)] = np.nan
    image[((flags & mask_of(BAD_FLAGS)) != 0) | ~np.isfinite(image)] = np.nan
    return Cutout(rec, image, display, var, flags, bits, WCS(hdr), hdr, wave, n_tr)


# --------------------------------------------------------------------------- #
# 6. Frames on a common grid
# --------------------------------------------------------------------------- #
def make_grid(ra: float, dec: float, size_deg: float, scale_arcsec: float = PIXEL_SCALE_ARCSEC):
    n = int(np.ceil(size_deg * 3600 / scale_arcsec))
    n += (n + 1) % 2
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(n + 1) / 2, (n + 1) / 2]
    w.wcs.cdelt = [-scale_arcsec / 3600, scale_arcsec / 3600]
    return w, (n, n)


def b64f32(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a, dtype="<f4").tobytes()).decode()


def build_frames(cutouts: list[Cutout], grid: WCS, shape) -> dict:
    """One co-add per (epoch, detector) from the lightly-masked display images.
    Background (median) removed per image. With >= 3 images the per-pixel median rejects
    cosmic rays and other transients; otherwise a 1/variance-weighted mean is used."""
    stacks: dict[tuple[int, str], list] = {}
    for c in cutouts:
        img = c.display - np.nanmedian(c.display)
        img_r, _ = reproject_interp((img, c.wcs), grid, shape_out=shape)
        v = float(np.nanmedian(c.variance))
        stacks.setdefault((c.rec.epoch, c.rec.det), []).append((img_r, 1.0 / v if np.isfinite(v) and v > 0 else 1.0))
    frames = {}
    for key, items in stacks.items():
        cube = np.array([a for a, _ in items])
        if len(items) >= 3:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                out = np.nanmedian(cube, axis=0)
        else:
            w = np.array([w for _, w in items])[:, None, None] * np.isfinite(cube)
            den = w.sum(axis=0)
            out = np.where(den > 0, np.nansum(np.nan_to_num(cube) * w, axis=0) / np.where(den > 0, den, 1), np.nan)
        frames[key] = (out.astype(np.float32), len(items))
    return frames


# --------------------------------------------------------------------------- #
# 7. Photometry
# --------------------------------------------------------------------------- #
def photometry_at(c: Cutout, ra: float, dec: float, r_ap: float = 2.0,
                  r_in: float = 4.0, r_out: float = 8.0) -> dict | None:
    x, y = c.wcs.world_to_pixel(SkyCoord(ra, dec, unit="deg"))
    x, y = float(x), float(y)
    ny, nx = c.image.shape
    if not (1 <= x < nx - 1 and 1 <= y < ny - 1):
        return None
    yy, xx = np.mgrid[0:ny, 0:nx]
    rr = np.hypot(xx - x, yy - y)
    ap = rr <= r_ap
    ann = (rr >= r_in) & (rr <= r_out) & np.isfinite(c.image)
    core = rr <= 1.0
    if not np.isfinite(c.image[core]).all() or ann.sum() < 8:
        good = False
    else:
        good = True
    vals = c.image[ann]
    med = np.nanmedian(vals) if vals.size else 0.0
    if vals.size > 10:   # one sigma-clip pass
        s = np.nanstd(vals)
        med = np.nanmedian(vals[np.abs(vals - med) < 3 * s]) if s > 0 else med
    src = c.image[ap]
    n_ap = int(ap.sum())
    flux = (np.nansum(src) - med * n_ap) * MJYSR_TO_MJY_PER_PIX
    err = np.sqrt(np.nansum(c.variance[ap])) * MJYSR_TO_MJY_PER_PIX if np.isfinite(c.variance[ap]).any() else None
    xi, yi = int(round(x)), int(round(y))
    flags = c.flag_names_at(yi=yi, xi=xi)
    core_flags = set()
    for yy_, xx_ in zip(*np.nonzero(core)):
        core_flags.update(c.flag_names_at(yi=int(yy_), xi=int(xx_)))
    saturated = bool(core_flags & SATURATION_FLAGS)
    method = "aperture"
    if saturated:
        # Wing photometry for saturated stars: the unsaturated PSF wings (1.5-5 px) scale with
        # the total flux, so this gives a reliable *relative* light curve (not an absolute flux).
        wing = (rr >= 1.5) & (rr <= 5.0) & np.isfinite(c.display)
        bkg = (rr >= 9.0) & (rr <= 13.0) & np.isfinite(c.display)
        if wing.sum() >= 12 and bkg.sum() >= 20:
            b = np.nanmedian(c.display[bkg])
            flux = (np.nansum(c.display[wing]) - b * wing.sum()) * MJYSR_TO_MJY_PER_PIX
            err = np.sqrt(np.nansum(np.where(np.isfinite(c.variance[wing]), c.variance[wing], 0))) * MJYSR_TO_MJY_PER_PIX
            good, method = True, "wings"
    return {"wavelength_um": c.wavelength_at(x, y), "flux_mjy": float(flux),
            "err_mjy": float(err) if err is not None else None,
            "mjd": c.rec.mjd, "epoch": c.rec.epoch, "det": c.rec.det, "obs_id": c.rec.obs_id,
            "flags": flags, "artifact": sorted(set(flags) & ARTIFACT_FLAGS),
            "saturated": saturated, "method": method, "good": good}
