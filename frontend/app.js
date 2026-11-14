/*
 * SPHEREx Time Machine – frontend.
 * Parts of this file were written with the assistance of an AI coding assistant
 * (Claude, Anthropic) and reviewed by the team. See README "Use of AI".
 */
"use strict";

const DETS = ["D1", "D2", "D3", "D4", "D5", "D6"];
const DET_WL = { D1: "0.75–1.1", D2: "1.1–1.6", D3: "1.6–2.4", D4: "2.4–3.8", D5: "3.8–4.4", D6: "4.4–5.0" };
const DET_COLORS = { D1: "#7aa2ff", D2: "#5ad1ff", D3: "#5ef0b0", D4: "#d6e05a", D5: "#ffb547", D6: "#ff6b6b" };
const FEATURES = [
  { lo: 1.30, hi: 1.50, label: "H₂O", kind: "mol" }, { lo: 1.75, hi: 2.05, label: "H₂O", kind: "mol" },
  { lo: 2.60, hi: 2.95, label: "H₂O", kind: "mol" }, { lo: 1.60, hi: 1.75, label: "CH₄", kind: "mol" },
  { lo: 2.15, hi: 2.45, label: "CH₄", kind: "mol" }, { lo: 3.15, hi: 3.55, label: "CH₄ (3.3)", kind: "mol" },
  { lo: 4.20, hi: 4.35, label: "CO₂", kind: "mol" }, { lo: 4.50, hi: 4.80, label: "CO", kind: "mol" },
];
const LINES = [[1.282, "Paβ"], [1.875, "Paα"], [2.166, "Brγ"], [3.30, "PAH"], [4.052, "Brα"]];

const $ = (id) => document.getElementById(id);
const S = {
  result: null, key: null, z: new Map(), epochs: [], cur: 0, playing: true, timer: null,
  mode: "blink", dets: new Set(["D5", "D6"]), display: [], limits: null,
  gaia: null, ast: null, spec: null, specLabel: null, target: null, fov: 5, pending: null,
  auto: null, embed: false,
};

// ---------------------------------------------------------------- helpers
const fmt = (x, d = 2) => (x == null || !isFinite(x) ? "–" : Number(x).toFixed(d));
function sexa(deg, isRa) {
  let v = isRa ? deg / 15 : Math.abs(deg);
  const a = Math.floor(v), b = Math.floor((v - a) * 60), c = ((v - a) * 60 - b) * 60;
  const s = `${String(a).padStart(2, "0")}:${String(b).padStart(2, "0")}:${c.toFixed(isRa ? 2 : 1).padStart(isRa ? 5 : 4, "0")}`;
  return isRa ? s : (deg < 0 ? "−" : "+") + s;
}
function parseCoords(text) {
  const t = text.trim().replace(/[hdms°′″'"]/g, " ").replace(/,/g, " ").replace(/\s+/g, " ");
  const parts = t.split(" ");
  if (parts.length === 2 && parts.every((p) => /^[-+]?\d+(\.\d+)?$/.test(p))) {
    return { ra: +parts[0], dec: +parts[1] };
  }
  const sx = text.trim().match(/^(\d{1,2})[: h](\d{1,2})[: m](\d{1,2}(?:\.\d+)?)s?\s*,?\s*([-+]?\d{1,2})[: d°](\d{1,2})[: m′'](\d{1,2}(?:\.\d+)?)/);
  if (sx) {
    if ([sx[2], sx[3], sx[5], sx[6]].some((v) => +v >= 60)) return { ra: NaN, dec: NaN };   // minutes/seconds must be < 60
    const ra = 15 * (+sx[1] + sx[2] / 60 + sx[3] / 3600);
    const sgn = sx[4].startsWith("-") ? -1 : 1;
    const dec = sgn * (Math.abs(+sx[4]) + sx[5] / 60 + sx[6] / 3600);
    return { ra, dec };
  }
  return null;
}
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) {
    const d = (await r.json().catch(() => ({}))).detail;
    throw new Error(Array.isArray(d) ? d.map((x) => `${(x.loc || []).slice(-1)[0]}: ${x.msg}`).join("; ") : d || r.statusText);
  }
  return r.json();
}
function percentile(sorted, p) {
  if (!sorted.length) return 0;
  const i = Math.min(sorted.length - 1, Math.max(0, Math.round((p / 100) * (sorted.length - 1))));
  return sorted[i];
}
function decodeF32(b64) {
  const bin = atob(b64), buf = new ArrayBuffer(bin.length), u8 = new Uint8Array(buf);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return new Float32Array(buf);
}

// ---------------------------------------------------------------- WCS (TAN)
const D2R = Math.PI / 180;
function world2pix(ra, dec) {
  const g = S.result.grid, a0 = g.crval[0] * D2R, d0 = g.crval[1] * D2R;
  const a = ra * D2R, d = dec * D2R;
  const cosc = Math.sin(d0) * Math.sin(d) + Math.cos(d0) * Math.cos(d) * Math.cos(a - a0);
  const xi = (Math.cos(d) * Math.sin(a - a0)) / cosc / D2R;
  const eta = (Math.cos(d0) * Math.sin(d) - Math.sin(d0) * Math.cos(d) * Math.cos(a - a0)) / cosc / D2R;
  return [g.crpix[0] + xi / g.cdelt[0] - 1, g.crpix[1] + eta / g.cdelt[1] - 1]; // 0-based
}
function pix2world(x, y) {
  const g = S.result.grid, a0 = g.crval[0] * D2R, d0 = g.crval[1] * D2R;
  const xi = (x + 1 - g.crpix[0]) * g.cdelt[0] * D2R, eta = (y + 1 - g.crpix[1]) * g.cdelt[1] * D2R;
  const den = Math.cos(d0) - eta * Math.sin(d0);
  const ra = (a0 + Math.atan2(xi, den)) / D2R;
  const dec = Math.atan2(Math.sin(d0) + eta * Math.cos(d0), Math.hypot(xi, den)) / D2R;
  return [(ra + 360) % 360, dec];
}

// ---------------------------------------------------------------- frames
function normaliseFrames() {
  S.z.clear();
  for (const f of S.result.frames) {
    const a = decodeF32(f.data);
    const fin = Array.from(a).filter(Number.isFinite).sort((p, q) => p - q);
    const med = percentile(fin, 50);
    const mad = percentile(fin.map((v) => Math.abs(v - med)).sort((p, q) => p - q), 50) * 1.4826 || 1;
    const z = new Float32Array(a.length);
    for (let i = 0; i < a.length; i++) z[i] = (a[i] - med) / mad;
    S.z.set(`${f.epoch}|${f.det}`, z);
  }
}
function composite(ep, dets) {
  const [ny, nx] = S.result.grid.shape, out = new Float32Array(nx * ny), cnt = new Uint8Array(nx * ny);
  let any = false;
  for (const d of dets) {
    const z = S.z.get(`${ep}|${d}`);
    if (!z) continue;
    any = true;
    for (let i = 0; i < z.length; i++) if (Number.isFinite(z[i])) { out[i] += z[i]; cnt[i]++; }
  }
  for (let i = 0; i < out.length; i++) out[i] = cnt[i] ? out[i] / Math.sqrt(cnt[i]) : NaN;
  return any ? out : null;
}
function medianOthers(arrs, skip) {
  const n = arrs[0].length, out = new Float32Array(n), tmp = [];
  for (let i = 0; i < n; i++) {
    tmp.length = 0;
    arrs.forEach((a, k) => { if (k !== skip && a && Number.isFinite(a[i])) tmp.push(a[i]); });
    tmp.sort((p, q) => p - q);
    out[i] = tmp.length ? tmp[tmp.length >> 1] : NaN;
  }
  return out;
}
function rebuildDisplay() {
  if (!S.result) return;
  const eps = S.epochs.map((e) => e.epoch);
  const dets = [...S.dets];
  if (S.mode === "color") {
    const ch = [["D5", "D6"], ["D3", "D4"], ["D1", "D2"]];
    S.display = eps.map((ep) => ch.map((c) => composite(ep, c)));
  } else if (S.mode === "cdiff") {
    S.display = eps.map((ep) => {
      const a = composite(ep, ["D5", "D6"]), b = composite(ep, ["D4"]);
      if (!a || !b) return [null];
      const o = new Float32Array(a.length);
      for (let i = 0; i < a.length; i++) o[i] = a[i] - b[i];
      return [o];
    });
  } else {
    const base = eps.map((ep) => composite(ep, dets));
    if (S.mode === "stack") {
      const valid = base.filter(Boolean);
      const st = valid.length ? medianOthers(valid, -1) : null;
      S.display = base.map(() => [st]);
    } else if (S.mode === "diff") {
      S.display = base.map((a, k) => {
        if (!a) return [null];
        const m = medianOthers(base, k), o = new Float32Array(a.length);
        for (let i = 0; i < a.length; i++) o[i] = a[i] - m[i];
        return [o];
      });
    } else S.display = base.map((a) => [a]);
  }
  S.auto = $("ovAuto").checked ? detectChanges() : null;
  computeLimits();
  render();
}

// ---------------------------------------------------------------- automatic change detection
// Thresholds tuned on the five demo fields: at 5 sigma, quiet fields showed up to 3 noise hits per visit.
const DETECT_SIGMA = 7;        // a flagged pixel must exceed the noise of the difference image by this much
const DETECT_FRACTION = 0.35;  // ...and be a large fraction of the source itself (rejects small residuals of steady stars)
/* Flag places where one visit is much brighter than the median of the other visits: a source that
   moved in, or a star that brightened. Returns, per visit, up to 5 hits {x, y, ra, dec, snr}.
   These are hints for the eye, not discoveries: confirm by blinking and checking the flags. */
function detectChanges() {
  if (!S.result || isMoving()) return null;
  const [ny, nx] = S.result.grid.shape;
  const base = S.epochs.map((e) => composite(e.epoch, [...S.dets]));
  const valid = base.map((a, k) => (a ? k : -1)).filter((k) => k >= 0);
  const out = S.epochs.map(() => []);
  if (valid.length < 3) return out;
  const arrs = valid.map((k) => base[k]);
  valid.forEach((k, j) => {
    const a = arrs[j], m = medianOthers(arrs, j), d = new Float32Array(a.length);
    for (let i = 0; i < a.length; i++) d[i] = a[i] - m[i];
    const abs = Array.from(d).filter(Number.isFinite).map(Math.abs).sort((p, q) => p - q);
    const sigma = 1.4826 * percentile(abs, 50) || 1;
    const hits = [];
    for (let y = 2; y < ny - 2; y++) for (let x = 2; x < nx - 2; x++) {
      const i = y * nx + x, v = d[i];
      if (!(v > DETECT_SIGMA * sigma) || !(v > DETECT_FRACTION * a[i])) continue;
      let peak = true, support = false;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue;
        const w = d[i + dy * nx + dx];
        if (w > v) peak = false;
        if (w > 0.4 * v) support = true;   // starlight spills into a neighbouring pixel; a cosmic-ray hit does not
      }
      if (peak && support) { const [ra, dec] = pix2world(x, y); hits.push({ x, y, ra, dec, snr: v / sigma }); }
    }
    // strongest first; drop hits within 5 px of a stronger one (the halo of a bright star gives several)
    const kept = [];
    for (const h of hits.sort((p, q) => q.snr - p.snr))
      if (kept.length < 5 && !kept.some((g) => Math.hypot(g.x - h.x, g.y - h.y) < 5)) kept.push(h);
    out[k] = kept;
  });
  return out;
}
function gaiaNear(ra, dec) {   // is a Gaia star within 4″ at the current visit? null = Gaia not loaded
  if (!S.gaia || !S.gaia.provider) return null;
  const cosd = Math.cos(dec * D2R);
  return S.gaia.sources.some((s) => { const p = s.positions[S.cur]; return p && Math.hypot((p[0] - ra) * cosd, p[1] - dec) * 3600 < 4; });
}
function computeLimits() {
  const lo = +$("lo").value, hi = +$("hi").value, sym = S.mode === "diff" || S.mode === "cdiff";
  const nch = S.display[0]?.length || 1;
  S.limits = [];
  for (let c = 0; c < nch; c++) {
    const vals = [];
    for (const d of S.display) {
      const a = d[c];
      if (!a) continue;
      for (let i = 0; i < a.length; i += 3) if (Number.isFinite(a[i])) vals.push(sym ? Math.abs(a[i]) : a[i]);
    }
    vals.sort((p, q) => p - q);
    S.limits.push(sym ? [-percentile(vals, hi), percentile(vals, hi)] : [percentile(vals, lo), percentile(vals, hi)]);
  }
}
function stretch(v, [a, b], k) {
  if (!Number.isFinite(v)) return NaN;
  let x = (v - a) / (b - a || 1);
  x = Math.min(1, Math.max(0, x));
  return k > 0 ? Math.asinh(k * x) / Math.asinh(k) : x;
}

// ---------------------------------------------------------------- rendering
const off = document.createElement("canvas");
function render() {
  const cv = $("img"), ctx = cv.getContext("2d");
  ctx.fillStyle = "#05080d";
  ctx.fillRect(0, 0, cv.width, cv.height);
  if (!S.result || !S.display.length) return drawOverlay();
  const [ny, nx] = S.result.grid.shape, chans = S.display[S.cur];
  off.width = nx; off.height = ny;
  const octx = off.getContext("2d"), img = octx.createImageData(nx, ny);
  const k = +$("asinh").value, inv = $("invert").checked, sym = S.mode === "diff" || S.mode === "cdiff";
  const kk = sym ? 0 : k;
  for (let y = 0; y < ny; y++) {
    for (let x = 0; x < nx; x++) {
      const src = y * nx + x, dst = ((ny - 1 - y) * nx + x) * 4;
      if (chans.length === 3) {
        for (let c = 0; c < 3; c++) {
          const a = chans[c];
          let v = a ? stretch(a[src], S.limits[c], kk) : 0;
          if (!Number.isFinite(v)) v = 0;
          img.data[dst + c] = Math.round(255 * v);   // colour is never inverted (would swap hues)
        }
      } else {
        let v = chans[0] ? stretch(chans[0][src], S.limits[0], kk) : NaN;
        if (!Number.isFinite(v)) { img.data[dst] = 40; img.data[dst + 1] = 20; img.data[dst + 2] = 30; img.data[dst + 3] = 255; continue; }
        const g = Math.round(255 * (inv ? 1 - v : v));
        img.data[dst] = img.data[dst + 1] = img.data[dst + 2] = g;
      }
      img.data[dst + 3] = 255;
    }
  }
  octx.putImageData(img, 0, 0);
  const v = view();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, v.sx, v.sy, v.sw, v.sw, 0, 0, cv.width, cv.height);
  const e = S.epochs[S.cur];
  if (isMoving()) {
    $("epochLabel").textContent = S.mode === "stack"
      ? `Stack of ${S.epochs.length} frames (shift-and-add on the object)`
      : `${e.date_start} UT · ${e.dets[0]} · ${e.geo_au != null ? e.geo_au.toFixed(2) + " au from Earth" : ""}${e.vmag != null ? " · V≈" + e.vmag.toFixed(1) : ""}`;
  } else {
    $("epochLabel").textContent = S.mode === "stack" ? `Stack of all ${S.epochs.length} visits`
      : `${e.date_start}${e.date_end !== e.date_start ? " → " + e.date_end.slice(5) : ""} · ${e.n_images} images · ${S.mode === "color" ? "colour" : S.mode === "cdiff" ? "D5+D6 − D4" : [...S.dets].join("+")}${S.mode === "diff" ? " − median" : ""}`;
  }
  document.querySelectorAll(".timeline button").forEach((b, i) => b.classList.toggle("cur", i === S.cur));
  const hits = (S.auto && S.auto[S.cur]) || [];
  $("autoNote").hidden = !S.auto;
  if (S.auto) {
    const noGaia = hits.filter((h) => gaiaNear(h.ra, h.dec) === false).length;
    $("autoNote").textContent = S.epochs.length < 3 ? "Auto-detect needs at least 3 visits."
      : `Auto-detect: ${hits.length} change${hits.length === 1 ? "" : "s"} flagged in this visit${hits.length ? `, ${noGaia} with no Gaia star` : ""}. Hints only – confirm by blinking.`;
  }
  drawOverlay();
}
function view() {
  const [ny, nx] = S.result.grid.shape, zoom = +$("zoom").value, sw = nx / zoom;
  return { sx: (nx - sw) / 2, sy: (ny - sw) / 2, sw, scale: $("img").width / sw, nx, ny };
}
function toCanvas(x, y) {
  const v = view();
  return [(x + 0.5 - v.sx) * v.scale, (v.ny - 1 - y + 0.5 - v.sy) * v.scale];
}
function fromCanvas(cx, cy) {
  const v = view();
  return [cx / v.scale + v.sx - 0.5, v.ny - 1 - (cy / v.scale + v.sy - 0.5)];
}
function drawOverlay() {
  const cv = $("overlay"), ctx = cv.getContext("2d");
  ctx.clearRect(0, 0, cv.width, cv.height);
  if (!S.result) return;
  const v = view(), px = v.scale;
  if ($("ovBorder").checked && S.cur === 0) {
    ctx.setLineDash([10, 6]); ctx.strokeStyle = "#ffb547"; ctx.lineWidth = 4;
    ctx.strokeRect(2, 2, cv.width - 4, cv.height - 4); ctx.setLineDash([]);
  }
  if (isMoving()) {   // frames are centred on the object: just mark the centre
    if ($("ovTarget").checked) {
      const c = $("overlay").width / 2, r = Math.max(10, px * 2.2);
      ctx.strokeStyle = "#c58cff"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(c, c, r, 0, 2 * Math.PI); ctx.stroke();
    }
    return;
  }
  if ($("ovGaia").checked && S.gaia) {
    for (const s of S.gaia.sources) {
      const p = s.positions[S.cur];
      const fast = s.pm_total && s.pm_total > 150;
      if (!p || (!fast && s.g != null && s.g > 18)) continue;   // declutter: SPHEREx single visits reach ~G 18
      const [x, y] = toCanvas(...world2pix(p[0], p[1]));
      ctx.strokeStyle = fast ? "#ff6bd6" : "rgba(57,217,138,.7)"; ctx.lineWidth = fast ? 2 : 1;
      ctx.beginPath(); ctx.arc(x, y, fast ? Math.max(6, px * 1.6) : Math.max(2.5, px * 0.55), 0, 2 * Math.PI); ctx.stroke();
      if (fast) { // arrow = motion over 5 years
        const q = s.positions[S.cur], ddeg = (s.pmdec * 5) / 3.6e6, rdeg = (s.pmra * 5) / 3.6e6 / Math.cos(q[1] * D2R);
        const [x2, y2] = toCanvas(...world2pix(q[0] + rdeg, q[1] + ddeg));
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
      }
    }
  }
  if ($("ovAst").checked && S.ast) {
    const list = S.ast[S.cur]?.objects || [];
    ctx.font = "12px system-ui"; ctx.fillStyle = "#ffd25a"; ctx.strokeStyle = "#ffd25a"; ctx.lineWidth = 1.5;
    for (const o of list) {
      const [x, y] = toCanvas(...world2pix(o.ra, o.dec)), r = Math.max(6, px * 1.3);
      ctx.beginPath(); ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath(); ctx.stroke();
      ctx.fillText(o.name.split(" (")[0], x + r + 2, y - 2);
    }
  }
  if ($("ovTarget").checked && S.target) {
    const pts = S.epochs.map((e) => toCanvas(...world2pix(e.target_ra, e.target_dec)));
    ctx.strokeStyle = "rgba(79,179,255,.6)"; ctx.lineWidth = 1.5;
    ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
    pts.forEach(([x, y], i) => { ctx.fillStyle = i === S.cur ? "#4fb3ff" : "rgba(79,179,255,.5)"; ctx.beginPath(); ctx.arc(x, y, 2.5, 0, 7); ctx.fill(); });
    const [x, y] = pts[S.cur], r = Math.max(9, px * 2.2);
    ctx.strokeStyle = "#4fb3ff"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.stroke();
  }
  if (S.auto) {   // automatic hints: pink boxes, solid when no Gaia star sits there
    ctx.font = "11px system-ui";
    for (const h of S.auto[S.cur] || []) {
      const [x, y] = toCanvas(h.x, h.y), r = Math.max(10, px * 1.8), noGaia = gaiaNear(h.ra, h.dec) === false;
      ctx.strokeStyle = ctx.fillStyle = "#ff6bd6"; ctx.lineWidth = noGaia ? 2.5 : 1.5;
      ctx.setLineDash(noGaia ? [] : [4, 3]); ctx.strokeRect(x - r, y - r, 2 * r, 2 * r); ctx.setLineDash([]);
      ctx.fillText(`${h.snr.toFixed(0)}σ${noGaia ? " · no Gaia" : ""}`, x + r + 3, y + 4);
    }
  }
  ctx.strokeStyle = "#ffd25a"; ctx.lineWidth = 1.5;   // saved candidates: small yellow squares
  for (const c of loadCands()) {
    const [x, y] = toCanvas(...world2pix(c.ra, c.dec));
    if (x > 0 && y > 0 && x < cv.width && y < cv.height) ctx.strokeRect(x - 7, y - 7, 14, 14);
  }
  if (S.specLabel && S.specLabel.ra != null) {
    const [x, y] = toCanvas(...world2pix(S.specLabel.ra, S.specLabel.dec));
    ctx.strokeStyle = "#ffb547"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(x - 10, y); ctx.lineTo(x - 4, y); ctx.moveTo(x + 4, y); ctx.lineTo(x + 10, y);
    ctx.moveTo(x, y - 10); ctx.lineTo(x, y - 4); ctx.moveTo(x, y + 4); ctx.lineTo(x, y + 10); ctx.stroke();
  }
}

// ---------------------------------------------------------------- playback
function step(d) { if (!S.epochs.length) return; S.cur = (S.cur + d + S.epochs.length) % S.epochs.length; render(); }
function play(on) {
  S.playing = on; $("playBtn").textContent = on ? "⏸" : "▶︎";
  clearTimeout(S.timer);
  const tick = () => { if (!S.playing) return; step(1); S.timer = setTimeout(tick, +$("speed").value); };
  if (on) S.timer = setTimeout(tick, +$("speed").value);
}

// ---------------------------------------------------------------- loading
function showProgress(on, msg, frac) {
  $("progress").hidden = !on;
  if (msg) $("progressMsg").textContent = msg;
  if (frac != null) $("progressBar").style.width = `${Math.round(frac * 100)}%`;
}
/* Optional date range from the search bar, as request fields (empty boxes are left out). */
function dateRange() {
  const d = {};
  if ($("from").value) d.start = $("from").value;
  if ($("to").value) d.end = $("to").value;
  return d;
}
async function loadTarget(t, fov) {
  S.target = t; S.fov = fov; S.gaia = null; S.ast = null; S.spec = null; S.specLabel = null;
  $("ovAst").checked = false; $("candidates").hidden = true;
  $("empty").hidden = true; $("targetName").textContent = t.name || `${sexa(t.ra, true)} ${sexa(t.dec)}`;
  const pm = Math.hypot(t.pmra || 0, t.pmdec || 0);
  $("targetInfo").textContent = `${t.kind ? t.kind + " · " : ""}RA ${sexa(t.ra, true)} Dec ${sexa(t.dec)} (epoch ${t.ref_epoch || 2000})${pm > 50 ? ` · moves ${(pm / 1000).toFixed(2)}″/yr` : ""}`;
  setHash();
  const body = { ra: t.ra, dec: t.dec, pmra: t.pmra || 0, pmdec: t.pmdec || 0, ref_epoch: t.ref_epoch || 2000,
                 fov_arcmin: fov, max_per_cell: 8, budget: 260, name: t.name || null, ...dateRange() };
  // Ask for a quick preview first; the server answers with the full result if it already has it.
  runJob("/api/frames", { ...body, preview: true }, "Could not load this field.", body);
}
async function loadObject(name, fov) {
  S.target = { name, sso: true, pmra: 0, pmdec: 0 }; S.fov = Math.min(fov || 4, 15); setFovOption(S.fov);
  S.gaia = null; S.ast = null; S.spec = null; S.specLabel = null; $("ovAst").checked = false;
  $("empty").hidden = true; $("candidates").hidden = true;
  $("targetName").textContent = name;
  $("targetInfo").textContent = "Solar System object · frames centred on the object (stars stream past)";
  setHash();
  const body = { name, fov_arcmin: S.fov, max_frames: 40 };
  if (name === "3I") Object.assign(body, { start: "2025-08-01", end: "2025-12-31" });  // demo: SPHEREx's two 3I/ATLAS campaigns
  Object.assign(body, dateRange());
  runJob("/api/moving", body, "Could not track this object.");
}
/* Start a job (or get its cached result) and poll until it is done. Returns the result,
   or null when the user has loaded something else in the meantime. */
async function fetchResult(path, body, token, onProgress) {
  let r = await api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  while (r.status === "running") {
    await new Promise((res) => setTimeout(res, 1500));
    if (S.pending !== token) return null;
    const j = await api(`/api/jobs/${r.job_id}`);
    onProgress(j);
    if (j.status === "error") { const e = new Error(j.message); e.candidates = j.candidates; throw e; }
    if (j.status === "done") r = { status: "done", result_key: j.result_key };
  }
  const res = await api(`/api/result/${r.result_key}`);
  return S.pending === token ? res : null;
}
/* After a preview is on screen: load the full-quality result in the background and swap it in. */
async function upgradeToFull(fullBody, token) {
  const say = (text) => { const el = $("previewBadge"); if (el) el.textContent = text; };
  try {
    const res = await fetchResult("/api/frames", fullBody, token, (j) =>
      say(`Quick preview · full quality: ${j.stage === "download" ? `${j.done}/${j.total} images` : "processing"}…`));
    if (res) onResult(res, true);
  } catch {
    say("Quick preview only – the full-quality load failed, reload to retry");
  }
}
async function runJob(path, body, failMsg, fullBody) {
  showProgress(true, "Contacting the SPHEREx archive…", 0.02);
  const token = Symbol(); S.pending = token;
  try {
    const res = await fetchResult(path, body, token, (j) => showProgress(true, j.message,
      j.stage === "download" ? 0.1 + 0.75 * (j.done / Math.max(1, j.total)) : j.stage === "process" ? 0.9 : 0.05));
    if (!res) return;
    onResult(res);
    if (res.preview && fullBody) upgradeToFull(fullBody, token);
  } catch (err) {
    showProgress(false);
    $("empty").hidden = false;
    $("empty").innerHTML = `<p><b>${failMsg}</b><br>${err.message}</p>`;
    if (err.candidates) {
      const box = $("candidates");
      box.hidden = false;
      box.innerHTML = "Did you mean: " + err.candidates.map((c) => `<button data-n="${c.naif}" class="sso">${c.name} <span class="k">${c.type}</span></button>`).join("");
      box.querySelectorAll("button").forEach((b) => (b.onclick = () => loadObject(b.dataset.n, +$("fov").value)));
    }
  }
}
const isMoving = () => S.result && S.result.mode === "moving";
function onResult(res, keepView) {   // keepView: a full result replacing its preview – stay on the same visit
  const cur = S.cur, playing = S.playing;
  S.result = res; S.key = res.key; S.epochs = res.epochs; S.cur = keepView ? Math.min(cur, res.epochs.length - 1) : 0;
  if (res.mode === "moving") {
    S.dets = new Set(DETS);                 // each frame is a single detector image
    if (S.mode === "diff" || S.mode === "cdiff") S.mode = "blink";
    document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.mode === S.mode));
    $("targetName").textContent = res.name;
  }
  ["ovGaia", "ovAst"].forEach((id) => ($(id).disabled = res.mode === "moving"));
  normaliseFrames();
  buildTimeline(); buildDetButtons(); rebuildDisplay();
  showProgress(false);
  S.spec = { points: res.points, lightcurve: res.lightcurve };
  S.specLabel = { name: "target", ra: null, dec: null };
  $("specTitle").textContent = "Spectrum at target"; $("specReset").hidden = true;
  plotSpectrum(); plotLightcurve(); buildBadges(); buildWarnings(); buildLinks();
  if (!isMoving()) fetchGaia();
  if (!keepView) updateContext();
  play(keepView ? playing : true);
}
function buildTimeline() {
  const tl = $("timeline"); tl.innerHTML = "";
  S.epochs.forEach((e, i) => {
    const b = document.createElement("button");
    b.innerHTML = `${e.date_start}<span class="n">${e.n_images}</span>`;
    b.title = `${e.date_start} → ${e.date_end}: ${e.n_images} of ${e.n_available} images used (${e.dets.join(" ")})`;
    b.onclick = () => { play(false); S.cur = i; render(); };
    tl.appendChild(b);
  });
}
function buildDetButtons() {
  const box = $("dets"); box.innerHTML = "";
  const present = new Set(S.result.frames.map((f) => f.det));
  DETS.forEach((d) => {
    const b = document.createElement("button");
    b.innerHTML = `${d}<span class="wl">${DET_WL[d]}µm</span>`;
    b.classList.toggle("on", S.dets.has(d));
    b.disabled = !present.has(d);
    b.title = `Detector ${d} (${DET_WL[d]} µm). Shift-click to select only this one.`;
    b.onclick = (ev) => {
      if (ev.shiftKey) S.dets = new Set([d]);
      else if (S.dets.has(d) && S.dets.size > 1) S.dets.delete(d); else S.dets.add(d);
      buildDetButtons(); setHash(); rebuildDisplay();
    };
    box.appendChild(b);
  });
}
function buildBadges() {
  const r = S.result, b = [];
  if (isMoving()) {
    const days = (S.epochs.at(-1).mjd - S.epochs[0].mjd);
    b.push(`<span class="badge info">${r.stats.n_total} SPHEREx images of this object · showing ${r.stats.n_used} · ${days.toFixed(0)} days</span>`);
    const e = parseFloat(r.orbit?.eccentricity);
    if (e > 1) b.push(`<span class="badge warn">Hyperbolic orbit (e = ${e.toFixed(2)}): interstellar visitor</span>`);
    else if (e >= 0) b.push(`<span class="badge">Orbit e = ${e.toFixed(2)}${r.orbit.semimajor_axis ? `, a = ${(+r.orbit.semimajor_axis).toFixed(2)} au` : ""}</span>`);
    b.push(`<span class="badge">Ephemeris: JPL Horizons via IRSA MOST</span>`);
    $("badges").innerHTML = b.join("");
    return;
  }
  const span = S.epochs.length > 1 ? (S.epochs.at(-1).mjd - S.epochs[0].mjd) / 365.25 : 0;
  if (r.preview) b.push(`<span class="badge warn" id="previewBadge" title="Shown first so you are not kept waiting: up to 3 images per visit and detector, so it is noisier and the spectrum has fewer points. The full version replaces it automatically.">Quick preview · full quality loading…</span>`);
  b.push(`<span class="badge info">${r.stats.n_used} images · ${S.epochs.length} visits · ${span.toFixed(1)} yr</span>`);
  if (r.stats.n_total > r.stats.n_downloaded)
    b.push(`<span class="badge" title="To stay fast, up to 8 images per visit and detector are used">${r.stats.n_total} images in archive${r.stats.n_total > 1000 ? " (deep field)" : ""}</span>`);
  const pm = Math.hypot(S.target.pmra || 0, S.target.pmdec || 0);
  if (pm > 500) b.push(`<span class="badge warn">High proper motion: ${(pm / 1000).toFixed(1)}″/yr → ${(pm / 1000 * span / 6.15).toFixed(1)} px over the data</span>`);
  const latest = S.epochs.map((e) => e.date_end).sort().at(-1);
  b.push(`<span class="badge" title="Date of the newest SPHEREx image used for this field. Fields are queried live from the archive on first load and then kept; see the README for refreshing after a data release.">Latest image: ${latest}</span>`);
  b.push(`<span class="badge" id="gaiaBadge">Gaia: checking…</span>`);
  b.push(`<span class="badge" id="pmBadge"></span>`);
  $("badges").innerHTML = b.join("");
  showMotionBadge();
}
function buildWarnings() {
  const items = [], pts = S.spec.points;
  const sat = pts.filter((p) => p.saturated).length;
  if (pts.length && sat / pts.length > 0.3) {
    const wings = pts.filter((p) => p.method === "wings").length;
    items.push(`<b>Target is saturated</b> in ${sat} of ${pts.length} images (too bright for SPHEREx single exposures). ` +
      (wings ? `Fluxes are measured on the unsaturated PSF wings, so the <b>light curve is reliable in relative terms</b> (compare within one detector); the spectrum shape is only approximate.`
             : `Its motion is still visible, but its spectrum and light curve are not reliable.`));
    $("badges").insertAdjacentHTML("beforeend", `<span class="badge warn">Saturated in SPHEREx</span>`);
  }
  const art = {};
  pts.forEach((p) => p.artifact.forEach((a) => (art[a] = (art[a] || 0) + 1)));
  const arts = Object.entries(art).sort((a, b) => b[1] - a[1]);
  if (arts.length) items.push(`Artifact flags at the target in ${arts.map(([k, n]) => `${n}× ${k}`).join(", ")} measurements – treat those points with care.`);
  const rej = S.result.stats.rejected;
  if (rej.transient) items.push(`${rej.transient} frame(s) skipped: heavy cosmic-ray/transient contamination.`);
  if (rej.failed) items.push(`${rej.failed} cutout(s) could not be downloaded from IRSA (network or archive load).`);
  const bad = pts.filter((p) => !p.good).length;
  if (bad) items.push(`${bad} of ${pts.length} spectral points have masked pixels at the source position (shown hollow).`);
  $("warnCard").hidden = !items.length;
  $("warnings").innerHTML = items.map((x) => `<li>${x}</li>`).join("");
}
function buildLinks() {
  if (isMoving()) {
    const n = encodeURIComponent(S.target.name.replace(/:NID$/, "")), d0 = S.epochs[0].date_start.slice(0, 10).replace(/-/g, "+"),
      d1 = S.epochs.at(-1).date_start.slice(0, 10).replace(/-/g, "+");
    const L = [
      ["Same object in other telescopes (CADC SSOIS)", `https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/ssois/results.html?lang=en&object=${n}&search=bynameall&epoch1=${d0}&epoch2=${d1}&eellipse=&eunits=arcseconds&extres=no&xyres=no`],
      ["JPL Small-Body Database", `https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=${n}`],
      ["IRSA Moving Object Search Tool", "https://irsa.ipac.caltech.edu/applications/MOST/"],
    ];
    $("links").innerHTML = L.map(([t, u]) => `<a href="${u}" target="_blank" rel="noopener">${t} ↗</a>`).join("");
    return;
  }
  const ra = S.result.grid.crval[0], dec = S.result.grid.crval[1], fov = S.fov;
  const L = [
    ["Open in WiseView (13 yr of WISE)", `https://byw.tools/wiseview#ra=${ra.toFixed(6)}&dec=${dec.toFixed(6)}&size=${Math.round(fov * 60)}&band=3&speed=500&minbright=-50.0000&maxbright=500.0000&window=0.5&diff_window=1&linear=1&color=&zoom=9&border=0&gaia=0&invert=1&maxdyr=0&scandir=0&neowise=0&diff=0&outer_epochs=0&unique_window=1&smooth_scan=0&shift=0&pmra=0&pmdec=0&synth_a=0&synth_b=0`],
    ["SIMBAD", `https://simbad.cds.unistra.fr/simbad/sim-coo?Coord=${ra.toFixed(5)}%20${dec.toFixed(5)}&Radius=1&Radius.unit=arcmin`],
    ["Other telescopes here (CADC SSOIS)", `https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/cadcbin/ssos/fixedssos.pl?pos=${ra.toFixed(5)},${dec.toFixed(5)}`],
    ["Legacy Survey viewer", `https://www.legacysurvey.org/viewer?ra=${ra.toFixed(5)}&dec=${dec.toFixed(5)}&layer=unwise-neo7&zoom=13`],
    ["IRSA SPHEREx Data Explorer", "https://irsa.ipac.caltech.edu/applications/spherex/"],
  ];
  $("links").innerHTML = L.map(([t, u]) => `<a href="${u}" target="_blank" rel="noopener">${t} ↗</a>`).join("");
}
async function fetchGaia() {
  const r = S.result, rad = (S.fov / 60) * 0.75;
  try {
    S.gaia = await api(`/api/gaia?ra=${r.grid.crval[0]}&dec=${r.grid.crval[1]}&radius_deg=${rad.toFixed(4)}&jyears=${S.epochs.map((e) => e.jyear.toFixed(3)).join(",")}`);
  } catch { S.gaia = null; }
  const el = $("gaiaBadge");
  if (!el) return;
  if (!S.gaia || !S.gaia.provider) { el.textContent = "Gaia: unavailable"; return; }
  // Does any Gaia source sit on the target at the first epoch?
  const e0 = S.epochs[0], cosd = Math.cos(e0.target_dec * D2R);
  const match = S.gaia.sources.find((s) => {
    const p = s.positions[0];
    return Math.hypot((p[0] - e0.target_ra) * cosd, p[1] - e0.target_dec) * 3600 < 4;
  });
  if (match) {
    el.className = "badge good";
    el.textContent = `Gaia match: G=${fmt(match.g, 1)}${match.pm_total ? `, pm ${fmt(match.pm_total / 1000, 2)}″/yr` : ""}`;
  } else {
    el.className = "badge warn";
    el.textContent = "No Gaia counterpart – invisible in optical light";
  }
  render();   // also refreshes the auto-detect note, which counts hits without a Gaia star
}
async function fetchAsteroids() {
  const r = S.result;
  $("ovAst").disabled = true;
  try {
    S.ast = await api(`/api/asteroids?ra=${r.grid.crval[0]}&dec=${r.grid.crval[1]}&half_width_deg=${(S.fov / 120).toFixed(4)}&mjds=${S.epochs.map((e) => e.mjd.toFixed(4)).join(",")}`);
  } catch { S.ast = null; }
  $("ovAst").disabled = false;
  drawOverlay();
}

// ---------------------------------------------------------------- candidates (kept in this browser)
const CAND_KEY = "sxtm.candidates";
function loadCands() { try { return JSON.parse(localStorage.getItem(CAND_KEY)) || []; } catch { return []; } }
function saveCands(list) {
  try { localStorage.setItem(CAND_KEY, JSON.stringify(list)); } catch { /* storage blocked: list lasts until reload */ }
  renderCands(); drawOverlay();
}
/* Save the clicked position (or, with nothing clicked, the target) of the visit on screen. */
function addCandidate() {
  if (!S.result || isMoving()) return;
  const e = S.epochs[S.cur], clicked = S.specLabel && S.specLabel.ra != null;
  const ra = clicked ? S.specLabel.ra : e.target_ra, dec = clicked ? S.specLabel.dec : e.target_dec;
  const g = gaiaNear(ra, dec);
  const h = new URLSearchParams({ ra: ra.toFixed(6), dec: dec.toFixed(6), fov: S.fov, mode: S.mode, dets: [...S.dets].join(","), name: "Candidate" });
  saveCands([...loadCands(), { ra, dec, field: S.target.name || "", date: e.date_start, mode: S.mode, dets: [...S.dets].join("+"),
    gaia: g == null ? "unknown" : g ? "yes" : "no", link: `${location.origin}${location.pathname}#${h}`, saved: new Date().toISOString() }]);
}
function renderCands() {
  const list = loadCands();
  $("candCount").textContent = list.length ? `(${list.length})` : "";
  $("candCsv").disabled = !list.length;
  $("candList").innerHTML = list.length
    ? list.map((c, i) => `<li><a href="${esc(c.link)}" title="Open a view centred on this position">${sexa(c.ra, true)} ${sexa(c.dec)}</a>
        <button class="ghost small" data-i="${i}" title="Remove">✕</button><br>
        <span class="muted">${esc(c.field || "field")} · ${esc(c.date)} · ${esc(c.dets)} · Gaia star: ${esc(c.gaia)}</span></li>`).join("")
    : `<li class="muted">Nothing saved yet. Click a source on the image, then “Save as candidate”.</li>`;
  $("candList").querySelectorAll("button").forEach((b) => (b.onclick = () => { const l = loadCands(); l.splice(+b.dataset.i, 1); saveCands(l); }));
}
function downloadCands() {
  const cols = ["ra_deg", "dec_deg", "ra_hms", "dec_dms", "field", "visit_date", "mode", "detectors", "gaia_star_within_4arcsec", "link", "saved_utc"];
  const rows = loadCands().map((c) => [c.ra.toFixed(6), c.dec.toFixed(6), sexa(c.ra, true), sexa(c.dec).replace("−", "-"),
    c.field, c.date, c.mode, c.dets, c.gaia, c.link, c.saved]);
  const csv = [cols, ...rows].map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); a.download = "spherex-candidates.csv"; a.click();
  URL.revokeObjectURL(a.href);
}

// ---------------------------------------------------------------- sharing and embedding
function viewUrl(embed) {
  const h = new URLSearchParams(location.hash.slice(1));
  if (embed) h.set("embed", "1"); else h.delete("embed");
  return `${location.origin}${location.pathname}#${h}`;
}
function share(text, btn) {   // show the text ready to copy, and copy it when the browser allows
  const box = $("shareBox"), label = btn.textContent;
  box.hidden = false; box.value = text; box.select();
  navigator.clipboard?.writeText(text).then(() => { btn.textContent = "Copied ✓"; setTimeout(() => (btn.textContent = label), 1500); }).catch(() => {});
}

// ---------------------------------------------------------------- measured proper motion
/* Centroid the target in every visit (near its predicted position) and fit a straight line in
   time. SPHEREx astrometry is good to <0.3", so even ~1-pixel motions over a year are measurable. */
function measureMotion() {
  if (!S.result || isMoving() || S.epochs.length < 3) return null;
  const [ny, nx] = S.result.grid.shape, pix = Math.abs(S.result.grid.cdelt[0]) * 3600;
  const dets = S.dets.size ? [...S.dets] : DETS;
  const pts = [];
  // Saturated stars have flat/masked cores: centroid the symmetric PSF wings in a wider box.
  const satFrac = S.result.points.length ? S.result.points.filter((p) => p.saturated).length / S.result.points.length : 0;
  const hb = satFrac > 0.3 ? 4 : 2;
  for (const e of S.epochs) {
    const img = composite(e.epoch, dets);
    if (!img) continue;
    const [px, py] = world2pix(e.target_ra, e.target_dec);
    let best = -Infinity, bx = 0, by = 0;
    for (let y = Math.round(py) - 3; y <= Math.round(py) + 3; y++)
      for (let x = Math.round(px) - 3; x <= Math.round(px) + 3; x++) {
        if (x < 2 || y < 2 || x >= nx - 2 || y >= ny - 2) continue;
        const v = img[y * nx + x];
        if (Number.isFinite(v) && v > best) { best = v; bx = x; by = y; }
      }
    if (!(best > 3)) continue;           // need a >3-sigma detection
    if (hb > 2) { bx = Math.round(px); by = Math.round(py); }   // wide box centred on the prediction
    let sw = 0, sx = 0, sy = 0;
    for (let y = by - hb; y <= by + hb; y++)
      for (let x = bx - hb; x <= bx + hb; x++) {
        if (x < 0 || y < 0 || x >= nx || y >= ny) continue;
        const v = img[y * nx + x];
        if (Number.isFinite(v) && v > 0) { sw += v; sx += v * x; sy += v * y; }
      }
    if (sw > 0) pts.push({ t: e.jyear, x: sx / sw, y: sy / sw });
  }
  if (pts.length < 3) return null;
  const fit = (key) => {
    const n = pts.length, mt = pts.reduce((a, p) => a + p.t, 0) / n, mv = pts.reduce((a, p) => a + p[key], 0) / n;
    let sxx = 0, sxy = 0;
    pts.forEach((p) => { sxx += (p.t - mt) ** 2; sxy += (p.t - mt) * (p[key] - mv); });
    const b = sxy / sxx, res = pts.reduce((a, p) => a + (p[key] - mv - b * (p.t - mt)) ** 2, 0);
    return { slope: b, err: Math.sqrt(res / Math.max(1, n - 2) / sxx) };
  };
  const fx = fit("x"), fy = fit("y");
  // grid x grows westward (cdelt1 < 0): +x = -RA direction
  const pmra = -fx.slope * pix, pmdec = fy.slope * pix;
  const err = Math.hypot(fx.err, fy.err) * pix / Math.SQRT2;
  return { pmra, pmdec, total: Math.hypot(pmra, pmdec), err: Math.max(err, 0.3 / (S.epochs.at(-1).jyear - S.epochs[0].jyear)),
           n: pts.length, span: pts.at(-1).t - pts[0].t };
}
function showMotionBadge() {
  const m = measureMotion(), el = $("pmBadge");
  if (!el) return;
  if (!m) { el.remove(); return; }
  const cat = Math.hypot(S.target.pmra || 0, S.target.pmdec || 0) / 1000;
  const sig = m.total / m.err;
  el.className = "badge " + (sig > 3 ? "good" : "");
  el.title = `Centroid fit over ${m.n} visits spanning ${m.span.toFixed(2)} yr: μα* = ${m.pmra.toFixed(2)}″/yr, μδ = ${m.pmdec.toFixed(2)}″/yr`;
  el.textContent = sig > 3
    ? `Measured by SPHEREx: ${m.total.toFixed(1)} ± ${m.err.toFixed(1)}″/yr${cat > 0.05 ? ` (catalogue ${cat.toFixed(1)}″/yr)` : " – moving!"}`
    : `Measured by SPHEREx: no significant motion (< ${(3 * m.err).toFixed(1)}″/yr)`;
}

// ---------------------------------------------------------------- Aladin sky context
let aladin = null, aladinReady = null;
function ensureAladin() {
  if (aladinReady) return aladinReady;
  aladinReady = new Promise((resolve) => {
    const start = () => {
      if (!window.A) return setTimeout(start, 300);
      A.init.then(() => {
        aladin = A.aladin("#aladin", { survey: $("survey").value, fov: 0.2, projection: "TAN",
          showReticle: false, showLayersControl: false, showGotoControl: false, showFrame: false,
          showFullscreenControl: true, showCooGridControl: false, showSimbadPointerControl: true });
        resolve(aladin);
      }).catch(() => resolve(null));
    };
    start();
  });
  return aladinReady;
}
function propagateJs(t, jyear) {
  const dt = jyear - (t.ref_epoch || 2000);
  const dec = t.dec + ((t.pmdec || 0) * dt) / 3.6e6;
  return [t.ra + ((t.pmra || 0) * dt) / 3.6e6 / Math.cos(t.dec * D2R), dec];
}
async function updateContext() {
  $("contextCard").hidden = false;
  const al = await ensureAladin();
  if (!al || !S.result) return;
  const [ny, nx] = S.result.grid.shape, c = S.result.grid.crval;
  al.removeLayers?.();
  if (isMoving()) {
    const pts = S.epochs.map((e) => [e.target_ra, e.target_dec]);
    const ras = pts.map((p) => p[0]), decs = pts.map((p) => p[1]);
    const mid = pts[Math.floor(pts.length / 2)];
    const span = Math.max(Math.max(...decs) - Math.min(...decs), (Math.max(...ras) - Math.min(...ras)) * Math.cos(mid[1] * D2R));
    al.gotoRaDec(mid[0], mid[1]); al.setFoV(Math.min(180, Math.max(0.5, span * 1.3)));
    const tr = A.graphicOverlay({ color: "#c58cff", lineWidth: 2, name: "Object path" });
    al.addOverlay(tr); tr.add(A.polyline(pts));
    const marks = A.catalog({ name: "Frames", sourceSize: 8, color: "#c58cff", displayLabel: true, labelColumn: "label", labelColor: "#e2c8ff" });
    al.addCatalog(marks);
    marks.addSources(S.epochs.map((e, i) => A.source(e.target_ra, e.target_dec,
      { label: i === 0 || i === S.epochs.length - 1 || S.epochs[i].date_start.slice(0, 7) !== S.epochs[i - 1].date_start.slice(0, 7) ? e.date_start.slice(0, 10) : "" })));
    $("contextNote").textContent = `Purple: path of ${S.result.name} across the sky at the times SPHEREx imaged it (${S.epochs[0].date_start.slice(0, 10)} → ${S.epochs.at(-1).date_start.slice(0, 10)}). Powered by Aladin Lite (CDS).`;
    return;
  }
  al.gotoRaDec(c[0], c[1]);
  al.setFoV((S.fov / 60) * 1.8);
  const fp = A.graphicOverlay({ color: "#4fb3ff", lineWidth: 2, name: "SPHEREx field" });
  al.addOverlay(fp);
  const corners = [[-0.5, -0.5], [nx - 0.5, -0.5], [nx - 0.5, ny - 0.5], [-0.5, ny - 0.5]].map(([x, y]) => pix2world(x, y));
  fp.add(A.polygon(corners));
  const t = S.target, pm = Math.hypot(t.pmra || 0, t.pmdec || 0);
  if (pm > 100) {
    const track = A.graphicOverlay({ color: "#ffb547", lineWidth: 2, name: "Proper-motion track" });
    al.addOverlay(track);
    const pts = [];
    for (let y = 1950; y <= 2030; y += 2) pts.push(propagateJs(t, y));
    track.add(A.polyline(pts));
    const marks = A.catalog({ name: "Epochs", sourceSize: 12, shape: "circle", color: "#ffb547",
      displayLabel: true, labelColumn: "label", labelColor: "#ffd28a", labelFont: "12px sans-serif" });
    al.addCatalog(marks);
    const e0 = S.epochs[0], e1 = S.epochs.at(-1);
    const stops = [[1953, "1953 POSS-I"], [1993, "1993 DSS2"], [2016, "2016 Gaia"],
                   [e1.jyear, `${e0.date_start.slice(0, 4)}–${e1.date_start.slice(0, 4)} SPHEREx`]];
    marks.addSources(stops.map(([y, label]) => { const [ra, dec] = propagateJs(t, y); return A.source(ra, dec, { label }); }));
    const moved = (pm / 1000) * (e1.jyear - 1953) / 60;
    $("contextNote").textContent = `Orange track: ${t.name || "target"} moved ${moved.toFixed(1)}′ since the 1953 Palomar plates (${(pm / 1000).toFixed(2)}″/yr). Switch the background to compare decades. Blue square: the SPHEREx field above. Powered by Aladin Lite (CDS).`;
    if (moved * 60 > S.fov * 60 * 0.6) al.setFoV(Math.max((S.fov / 60) * 1.8, (moved / 60) * 1.4));
  } else {
    $("contextNote").textContent = "Blue square: the SPHEREx field shown above. Use the background menu to compare with other surveys. Powered by Aladin Lite (CDS).";
  }
}

// ---------------------------------------------------------------- charts
const PLOT_LAYOUT = {
  paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#cfd8e8", size: 11 },
  margin: { l: 50, r: 10, t: 10, b: 40 }, showlegend: true, legend: { orientation: "h", y: -0.25, font: { size: 10 } },
  xaxis: { gridcolor: "#24304a", zerolinecolor: "#24304a" }, yaxis: { gridcolor: "#24304a", zerolinecolor: "#24304a" },
};
const EPOCH_COLORS = ["#4fb3ff", "#ffb547", "#39d98a", "#ff6b6b", "#c58cff", "#5ef0e0", "#f0e05e", "#ff8fc7"];
function plotSpectrum() {
  if (!window.Plotly || !S.spec) return;
  const pts = S.spec.points.filter((p) => p.wavelength_um);
  const traces = [];
  if (S.epochs.length > 8) {   // many visits (e.g. moving objects): one trace, colour = date
    const g = pts.filter((p) => p.good);
    traces.push({ x: g.map((p) => p.wavelength_um), y: g.map((p) => p.flux_mjy), mode: "markers", type: "scatter", name: "measurements",
      text: g.map((p) => mjdToDate(p.mjd)),
      marker: { size: 6, color: g.map((p) => p.mjd), colorscale: "Viridis", showscale: false },
      error_y: { type: "data", array: g.map((p) => p.err_mjy || 0), visible: true, thickness: 1, width: 0, color: "rgba(200,210,230,.35)" },
      hovertemplate: "%{x:.3f} µm<br>%{y:.3f} mJy<br>%{text}<extra></extra>" });
  }
  S.epochs.forEach((e, k) => {
    if (S.epochs.length > 8) return;
    const g = pts.filter((p) => p.epoch === e.epoch && p.good);
    if (!g.length) return;
    traces.push({ x: g.map((p) => p.wavelength_um), y: g.map((p) => p.flux_mjy), mode: "markers", type: "scatter",
      name: e.date_start, marker: { size: 6, color: EPOCH_COLORS[k % EPOCH_COLORS.length] },
      error_y: { type: "data", array: g.map((p) => p.err_mjy || 0), visible: true, thickness: 1, width: 0, color: "rgba(200,210,230,.35)" },
      hovertemplate: "%{x:.3f} µm<br>%{y:.3f} mJy<br>" + e.date_start + "<extra></extra>" });
  });
  const bad = pts.filter((p) => !p.good);
  if (bad.length) traces.push({ x: bad.map((p) => p.wavelength_um), y: bad.map((p) => p.flux_mjy), mode: "markers", type: "scatter",
    name: "flagged", marker: { size: 6, color: "rgba(0,0,0,0)", line: { color: "#8e9bb3", width: 1 } }, hoverinfo: "skip" });
  const shapes = FEATURES.map((f) => ({ type: "rect", xref: "x", yref: "paper", x0: f.lo, x1: f.hi, y0: 0, y1: 1,
    fillcolor: "rgba(79,179,255,.07)", line: { width: 0 } }));
  const ann = FEATURES.map((f) => ({ x: (f.lo + f.hi) / 2, y: 1, xref: "x", yref: "paper", text: f.label, showarrow: false,
    font: { size: 9, color: "#7f9cc8" }, yanchor: "bottom" }));
  LINES.forEach(([w, t]) => { shapes.push({ type: "line", xref: "x", yref: "paper", x0: w, x1: w, y0: 0, y1: 0.92, line: { color: "rgba(255,181,71,.35)", dash: "dot", width: 1 } });
    ann.push({ x: w, y: 0.92, xref: "x", yref: "paper", text: t, showarrow: false, font: { size: 8, color: "#c9a35e" }, yanchor: "bottom" }); });
  const goodPts = pts.filter((p) => p.good);
  const ys = (goodPts.length >= 5 ? goodPts : pts).map((p) => p.flux_mjy).sort((a, b) => a - b);
  const y0 = percentile(ys, 3), y1 = percentile(ys, 97), pad = Math.max(0.15 * (y1 - y0), 0.05 * Math.abs(y1) || 0.05);
  Plotly.react("specPlot", traces, { ...PLOT_LAYOUT, shapes, annotations: ann,
    xaxis: { ...PLOT_LAYOUT.xaxis, title: "Wavelength (µm)", range: [0.7, 5.05] },
    yaxis: { ...PLOT_LAYOUT.yaxis, title: "Flux density (mJy)", range: ys.length ? [y0 - pad, y1 + pad * 1.6] : undefined } },
    { displayModeBar: false, responsive: true });
}
function plotLightcurve() {
  if (!window.Plotly || !S.spec) return;
  const lc = S.spec.lightcurve, traces = [];
  DETS.forEach((d) => {
    const g = lc.filter((r) => r.det === d);
    if (g.length < 2) return;
    const med = [...g.map((r) => r.flux_mjy)].sort((a, b) => a - b)[g.length >> 1] || 1;
    const norm = Math.abs(med) > 1e-6 ? med : 1;
    traces.push({ x: g.map((r) => mjdToDate(r.mjd)), y: g.map((r) => r.flux_mjy / norm), mode: "lines+markers", type: "scatter", name: d,
      line: { color: DET_COLORS[d], width: 1.5 }, marker: { size: 7 },
      error_y: { type: "data", array: g.map((r) => (r.err_mjy || 0) / Math.abs(norm)), visible: true, thickness: 1, width: 0 },
      hovertemplate: `${d}: %{y:.2f}× median<br>%{x}<extra></extra>` });
  });
  Plotly.react("lcPlot", traces, { ...PLOT_LAYOUT, xaxis: { ...PLOT_LAYOUT.xaxis, type: "date" },
    yaxis: { ...PLOT_LAYOUT.yaxis, title: "Flux / median", type: lcLog() ? "log" : "linear" } }, { displayModeBar: false, responsive: true });
}
function lcLog() {   // large-amplitude variables (e.g. Miras) read better on a log axis
  const lc = S.spec?.lightcurve || [];
  return DETS.some((d) => {
    const f = lc.filter((r) => r.det === d && r.flux_mjy > 0).map((r) => r.flux_mjy);
    return f.length > 2 && Math.max(...f) / Math.min(...f) > 4;
  });
}
function mjdToDate(m) { return new Date((m - 40587) * 86400000).toISOString().slice(0, 10); }

// ---------------------------------------------------------------- interaction
function setHash() {
  if (!S.target) return;
  const t = S.target, h = new URLSearchParams();
  if (t.sso) h.set("object", t.name);
  else if (t.id) h.set("target", t.id);
  else { h.set("ra", t.ra.toFixed(6)); h.set("dec", t.dec.toFixed(6)); if (t.pmra) h.set("pmra", t.pmra); if (t.pmdec) h.set("pmdec", t.pmdec); if (t.ref_epoch && t.ref_epoch !== 2000) h.set("epoch", t.ref_epoch); if (t.name) h.set("name", t.name); }
  if ($("from").value) h.set("from", $("from").value);
  if ($("to").value) h.set("to", $("to").value);
  h.set("fov", S.fov); h.set("mode", S.mode); h.set("dets", [...S.dets].join(","));
  h.set("speed", $("speed").value); if (!$("invert").checked) h.set("invert", "0"); if (+$("zoom").value !== 1) h.set("zoom", $("zoom").value);
  if (S.embed) h.set("embed", "1");
  history.replaceState(null, "", "#" + h.toString());
  $("openFull").href = viewUrl(false);
}
function setMode(m) {
  S.mode = m; document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.mode === m));
  setHash(); rebuildDisplay();
}
const esc = (s) => String(s).replace(/[&<>"']/g, (ch) => `&#${ch.charCodeAt(0)};`);
/* A rejected search: say what is wrong and show the accepted formats as clickable examples. */
function inputHelp(message) {
  S.pending = null; showProgress(false);
  const ex = [["269.452 4.693", "decimal degrees"], ["08:55:10.8 -07:14:42", "hours and degrees"],
              ["Barnard's Star", "a name known to SIMBAD"], ["M 31", "catalogue name"]];
  $("empty").hidden = false;
  $("empty").innerHTML = `<p><b>${esc(message)}</b></p>
    <p class="small">Accepted input (click an example to try it):</p>
    <p class="examples">${ex.map(([q, what]) => `<button type="button" data-q="${esc(q)}">${esc(q)}<span class="k">${what}</span></button>`).join("")}</p>
    <p class="small">RA runs from 0° to 360° (or 0h to 24h), Dec from −90° to +90°.<br>
    Names follow SIMBAD spelling, e.g. <i>WISE J085510.83-071442.5</i>. Asteroids and comets: switch the menu to “Solar System object”.</p>`;
  $("empty").querySelectorAll("button[data-q]").forEach((b) => (b.onclick = () => { $("q").value = b.dataset.q; submitQuery(b.dataset.q); }));
}
async function submitQuery(text) {
  const fov = +$("fov").value;
  if ($("qmode").value === "sso") return loadObject(text, fov);
  const c = parseCoords(text);
  if (c) {
    if (Number.isNaN(c.ra)) return inputHelp("Minutes and seconds in a position must be below 60.");
    if (!(c.ra >= 0 && c.ra < 360 && Math.abs(c.dec) <= 90))
      return inputHelp(`These coordinates are outside the sky: RA ${fmt(c.ra, 3)}°, Dec ${fmt(c.dec, 3)}°.`);
    return loadTarget({ name: null, ra: c.ra, dec: c.dec, pmra: 0, pmdec: 0, ref_epoch: 2000 }, fov);
  }
  if (!/[a-z]/i.test(text)) return inputHelp(`“${text}” is not a complete position: give both RA and Dec.`);
  try {
    const r = await api(`/api/resolve?q=${encodeURIComponent(text)}`);
    loadTarget(r, fov);
  } catch (err) {
    inputHelp(err.message);
  }
}
function setFovOption(v) {
  if (!(v >= 1 && v <= 20)) return;
  const sel = $("fov");
  if (![...sel.options].some((o) => +o.value === v)) {
    const o = document.createElement("option"); o.value = v; o.textContent = `${v}′`;
    sel.appendChild(o);
    [...sel.options].sort((a, b) => a.value - b.value).forEach((x) => sel.appendChild(x));
  }
  sel.value = String(v);
}
async function initFromHash(targets) {
  const h = new URLSearchParams(location.hash.slice(1));
  S.embed = h.get("embed") === "1";            // embed=1: viewer only, for <iframe> use on other sites
  document.body.classList.toggle("embed", S.embed);
  if (h.get("fov")) setFovOption(+h.get("fov"));
  for (const k of ["from", "to"]) if (/^\d{4}-\d{2}-\d{2}$/.test(h.get(k) || "")) $(k).value = h.get(k);
  if (h.get("mode")) S.mode = h.get("mode");
  if (h.get("dets")) S.dets = new Set(h.get("dets").split(",").filter((d) => DETS.includes(d)));
  if (h.get("speed")) $("speed").value = h.get("speed");
  if (h.get("invert") === "0") $("invert").checked = false;
  if (h.get("zoom")) $("zoom").value = h.get("zoom");
  document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("on", b.dataset.mode === S.mode));
  const fov = +$("fov").value;
  if (h.get("object")) { $("qmode").value = "sso"; return loadObject(h.get("object"), fov); }
  if (h.get("target")) {
    const t = targets.find((x) => x.id === h.get("target"));
    if (t) return loadTarget(t, fov);
  }
  if (h.get("ra") && h.get("dec")) {
    return loadTarget({ name: h.get("name"), ra: +h.get("ra"), dec: +h.get("dec"), pmra: +(h.get("pmra") || 0),
      pmdec: +(h.get("pmdec") || 0), ref_epoch: +(h.get("epoch") || 2000) }, fov);
  }
}

async function main() {
  let targets = [];
  try { targets = await api("/api/targets"); } catch { /* offline */ }
  $("demos").innerHTML = targets.map((t) => `<button data-id="${t.id}" title="${t.note}">${t.name}<span class="k">${t.kind}</span></button>`).join("")
    + `<button class="sso" data-obj="3I" title="Interstellar comet 3I/ATLAS, imaged by SPHEREx in Aug and Dec 2025">3I/ATLAS<span class="k">interstellar comet</span></button>`;
  $("demos").querySelector("[data-obj]").onclick = () => { $("qmode").value = "sso"; loadObject("3I", 4); };
  $("demos").querySelectorAll("button[data-id]").forEach((b) => (b.onclick = () => {
    $("qmode").value = "sky";
    const t = targets.find((x) => x.id === b.dataset.id);
    if (t.id === "wise0855" || t.id === "eps_ind_b") { S.dets = new Set(["D5", "D6"]); }
    else if (t.id === "barnard") { S.dets = new Set(["D2", "D3"]); }
    else { S.dets = new Set(DETS); }
    loadTarget(t, +$("fov").value);
  }));
  $("searchForm").onsubmit = (e) => { e.preventDefault(); if ($("q").value.trim()) submitQuery($("q").value.trim()); };
  $("playBtn").onclick = () => play(!S.playing);
  $("prevBtn").onclick = () => { play(false); step(-1); };
  $("nextBtn").onclick = () => { play(false); step(1); };
  document.querySelectorAll(".mode").forEach((b) => (b.onclick = () => setMode(b.dataset.mode)));
  ["lo", "hi"].forEach((id) => ($(id).oninput = () => { computeLimits(); render(); }));
  ["asinh", "invert"].forEach((id) => ($(id).oninput = () => { render(); setHash(); }));
  $("zoom").oninput = () => { render(); setHash(); };
  $("speed").oninput = () => setHash();
  ["ovTarget", "ovGaia", "ovBorder"].forEach((id) => ($(id).onchange = drawOverlay));
  $("ovAuto").onchange = () => { S.auto = $("ovAuto").checked ? detectChanges() : null; render(); };
  $("candAdd").onclick = addCandidate;
  $("candCsv").onclick = downloadCands;
  $("copyLink").onclick = () => share(viewUrl(false), $("copyLink"));
  $("copyEmbed").onclick = () => share(`<iframe src="${viewUrl(true)}" width="600" height="760" style="border:0" loading="lazy" title="SPHEREx Time Machine"></iframe>`, $("copyEmbed"));
  renderCands();
  window.addEventListener("hashchange", () => initFromHash(targets));   // opening a saved candidate link
  $("survey").onchange = async () => {
    const al = await ensureAladin();
    if (!al) return;
    (al.setBaseImageLayer || al.setImageSurvey).call(al, $("survey").value);
  };
  $("ovAst").onchange = () => { if ($("ovAst").checked && !S.ast && S.result) fetchAsteroids(); else drawOverlay(); };
  $("specReset").onclick = () => {
    S.spec = { points: S.result.points, lightcurve: S.result.lightcurve }; S.specLabel = { name: "target" };
    $("specTitle").textContent = "Spectrum at target"; $("specReset").hidden = true; plotSpectrum(); plotLightcurve(); drawOverlay();
  };
  const ov = $("overlay");
  ov.addEventListener("mousemove", (ev) => {
    if (!S.result) return;
    const r = ov.getBoundingClientRect(), cx = ((ev.clientX - r.left) / r.width) * ov.width, cy = ((ev.clientY - r.top) / r.height) * ov.height;
    const [x, y] = fromCanvas(cx, cy), [ra, dec] = pix2world(x, y);
    $("readout").textContent = isMoving() ? "object-centred frame" : `${sexa(ra, true)} ${sexa(dec)}`;
  });
  ov.addEventListener("click", async (ev) => {
    if (!S.result || isMoving()) return;
    const r = ov.getBoundingClientRect(), cx = ((ev.clientX - r.left) / r.width) * ov.width, cy = ((ev.clientY - r.top) / r.height) * ov.height;
    const [ra, dec] = pix2world(...fromCanvas(cx, cy));
    S.specLabel = { ra, dec }; drawOverlay();
    $("specTitle").textContent = `Spectrum at ${sexa(ra, true)} ${sexa(dec)} …`;
    try {
      S.spec = await api(`/api/spectrum/${S.key}?ra=${ra}&dec=${dec}`);
      $("specTitle").textContent = `Spectrum at ${sexa(ra, true)} ${sexa(dec)}`;
      $("specReset").hidden = false; plotSpectrum(); plotLightcurve();
    } catch (err) { $("specTitle").textContent = `Spectrum: ${err.message}`; }
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.target.matches("input[type=text], select")) return;
    const k = ev.key.toLowerCase();
    if (k === " ") { ev.preventDefault(); play(!S.playing); }
    else if (k === "arrowleft") { play(false); step(-1); }
    else if (k === "arrowright") { play(false); step(1); }
    else if (k === "b") setMode("blink"); else if (k === "d") setMode("diff"); else if (k === "c") setMode("color");
    else if (k === "s") setMode("stack");
    else if (k === "i") { $("invert").checked = !$("invert").checked; render(); setHash(); }
    else if (k === "+" || k === "=") { $("zoom").value = Math.min(4, +$("zoom").value + 0.25); render(); }
    else if (k === "-") { $("zoom").value = Math.max(1, +$("zoom").value - 0.25); render(); }
  });
  window.addEventListener("load", () => { if (S.spec) { plotSpectrum(); plotLightcurve(); } });
  await initFromHash(targets);
}
main();
