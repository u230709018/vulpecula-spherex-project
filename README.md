# SPHEREx Blink

A web tool that shows how a patch of sky changes over time in NASA SPHEREx images.
Enter a Right Ascension and Declination; the tool plays the images of that patch like a
short video so moving objects stand out.

Built for the NASA Space Apps 2026 challenge "Planet X and SPHEREx". First prototype.

## Run

Needs Python 3.10 or newer.

```bash
pip install -r requirements.txt
python -m uvicorn server:app --port 8000
```

Then open http://localhost:8000 and pick a test target or enter coordinates in degrees.
The first load of a position takes about a minute on a slow connection; after that it is
served from the local `cache/` folder.

A view can be shared as a link: `http://localhost:8000/#ra=269.4464&dec=4.7686&fov=180&band=D2`

## How it works

1. **Search.** One query to the IRSA archive (TAP) returns every SPHEREx spectral image
   whose footprint contains the position, with its detector (D1-D6) and observation time.
2. **Partial download.** Each image is a 65 MB FITS file. Instead of downloading it, the
   server reads two small pieces from the public AWS S3 bucket `nasa-irsa-spherex`:
   the header (about 35 kB, holds the sky-to-pixel transform) and only the pixels around
   the target (one small byte range per detector row).
3. **Alignment.** Every exposure has a different orientation. Each cutout is resampled
   onto the same north-up, east-left grid centred on the target, so frames line up
   pixel by pixel.
4. **Display.** The browser subtracts the background, scales each frame by its own noise,
   and plays the frames. Images taken within 30 days of each other are one "visit" and
   can be combined (per-pixel median) into a single cleaner frame.

## Files

- `server.py` - backend: archive search, partial FITS download, alignment.
- `index.html` - the whole user interface.

## Known limits

- Coordinates are decimal degrees only; there is no search by object name.
- Within one detector the wavelength of a source changes from exposure to exposure,
  so brightness in single exposures is not directly comparable.
- Saturated pixels (cores of very bright stars) are missing in the data and show as black.
- Checked on Barnard's Star (motion clearly visible). Other test targets are not yet verified.

## Data

SPHEREx data come from the NASA/IPAC Infrared Science Archive (IRSA).
"This publication makes use of data products from the Spectro-Photometer for the History
of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint
project of the Jet Propulsion Laboratory and the California Institute of Technology, and
is funded by the National Aeronautics and Space Administration."
