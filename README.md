# SPHEREx Time Machine

**Blink the infrared sky. Spot what moves. Read its spectrum.**

**Live tool: https://spherex-time-machine.onrender.com** (free hosting: the first visit after a quiet period can take ~1 minute to wake up).

Try: [WISE 0855 difference](https://spherex-time-machine.onrender.com/#target=wise0855&mode=diff&dets=D5,D6) · [Barnard's Star](https://spherex-time-machine.onrender.com/#target=barnard&dets=D2,D3) · [R Draconis light curve](https://spherex-time-machine.onrender.com/#target=r_dra) · [Interstellar comet 3I/ATLAS](https://spherex-time-machine.onrender.com/#object=3I&fov=4&mode=stack)

A public web tool for the NASA Space Apps Challenge 2026 *"Planet X and SPHEREx"*. Enter a sky position or an object name, and the tool shows a series of NASA SPHEREx images of that patch of sky like a short movie, making moving and variable objects easy to see. Click anywhere to get an on-the-fly 0.75–5 µm spectrum.

## Features

- **Blink** SPHEREx images of any position, one frame per visit (DR1 + QR3 + deep fields, queried live from NASA/IPAC IRSA, so newly released data appears automatically).
- **Six detector arrays** selectable individually or combined; frames are co-added per visit and detector for signal-to-noise.
- **Difference mode**: each visit minus the median of the other visits. Static stars cancel; movers leave a dipole.
- **False-colour mode** (blue = D1+D2, green = D3+D4, red = D5+D6) and **D6−D4 mode**: cold brown dwarfs are bright at 4.5 µm but dark in the 3.3 µm methane band.
- **Proper-motion aware**: named targets are propagated to the SPHEREx epochs. High-proper-motion stars (Barnard's Star moved 4.4′ since J2000; WISE 0855 sits ~2′ from its catalogue position) are found automatically, and the predicted track is drawn on the images.
- **On-the-fly spectrum and light curve** at the target or at any clicked position, coloured by visit, with molecular bands (H₂O, CH₄, CO₂, CO) and emission lines marked.
- **Overlays**: Gaia DR3 (propagated to each visit from J2016.0, fast movers drawn with motion arrows), known asteroids and comets (JPL Small-Body Identification), target track.
- **"No Gaia counterpart" badge**: a moving source invisible to Gaia is too cold for optical light – the classic brown-dwarf signature used by citizen scientists.
- **Data-quality notes** from SPHEREx pixel flags (ghosts, streaks, cosmic rays, persistence) at the measured position; frames with heavy transient contamination are skipped.
- **Shareable/embeddable URLs**: every setting lives in the URL, e.g. `/#target=wise0855&mode=diff&dets=D5,D6` or `/#ra=269.452&dec=4.693&pmra=-802&pmdec=10362&fov=8`.
- **Links out**: WiseView (13 years of WISE), SIMBAD, CADC SSOIS (other telescopes at this position), Legacy Survey, IRSA SPHEREx Data Explorer.
- Keyboard: Space play/pause · ← → step · B/D/C modes · I invert · + − zoom.

## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install astropy astroquery numpy reproject fastapi uvicorn
.venv/bin/uvicorn main:app --app-dir backend --port 8000
# open http://localhost:8000
```

Optional – pre-compute the demo targets so they load instantly:

```bash
.venv/bin/python scripts/warm_cache.py 5
```

## How it works

```
Browser (vanilla JS, canvas, Plotly)          FastAPI backend (Python)
  blink / difference / colour rendering  <--   /api/frames   IRSA TAP -> cutouts -> clean -> reproject -> co-add
  stretch, invert, zoom (instant)              /api/spectrum aperture photometry on every image
  WCS (TAN) for overlays & clicks              /api/gaia     ESA Gaia archive (MAST fallback)
  URL state, keyboard                          /api/asteroids JPL sb_ident
                                               /api/resolve  built-in targets, CDS Sesame
                                               disk cache of cutouts and results
```

- Images: SPHEREx Level-2 spectral images (DR1 + QR3) via the IRSA TAP service (`spherex.artifact`/`spherex.plane`) and the IRSA cutout service.
- Cleaning: zodiacal light model (ZODI extension) subtracted; pixels with bad FLAGS bits masked (Explanatory Supplement Table 16); per-image background removed.
- Alignment: every cutout reprojected onto a common north-up TAN grid (6.15″ pixels) with `reproject`.
- Co-addition: one inverse-variance–weighted frame per (visit, detector); the browser normalises and combines detectors on the fly.
- Spectrum: each SPHEREx pixel has its own wavelength (linear variable filter); per-image aperture photometry (r = 2 px, local annulus background) at the target position for that image's date gives one spectral point per image.

## Data and resources

**NASA:** SPHEREx DR1 (DOI 10.26131/IRSA678) and QR3 (DOI 10.26131/IRSA662) spectral images via NASA/IPAC IRSA; SPHEREx Explanatory Supplement; IRSA SPHEREx tutorial notebooks; IRSA MOST; JPL Small-Body Identification API; WiseView (inspiration).
**Space agency partners:** ESA Gaia DR3; Canadian Space Agency NEOSSat tutorial and Canadian Astronomy Data Centre (SSOIS, DSS).
**Other:** CDS Sesame name resolver; astropy, astroquery, reproject, FastAPI, Plotly.js.

### Acknowledgements

This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration. This research has made use of the NASA/IPAC Infrared Science Archive, which is funded by NASA and operated by the California Institute of Technology. This work has made use of data from the European Space Agency (ESA) mission Gaia, processed by the Gaia Data Processing and Analysis Consortium. This research used the facilities of the Canadian Astronomy Data Centre operated by the National Research Council of Canada with the support of the Canadian Space Agency.

This is not an official NASA product and does not imply endorsement by NASA, JPL, Caltech, ESA or CSA.

## Use of AI (Super Intelligence) tools

As required by the NASA Space Apps rules, we disclose that an AI coding assistant (Claude, by Anthropic) was used during the hackathon to help survey the challenge resources and to draft parts of the code (backend pipeline, API server and frontend). Files containing AI-assisted code say so in their header comment. The team chose the challenge, made the design decisions, and reviewed, tested and is responsible for all code and results. No AI-generated images, audio or video are used.

## License

MIT (see LICENSE). Third-party data remain subject to their providers' terms.
