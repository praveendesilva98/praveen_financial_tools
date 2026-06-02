// app.js — Shared utilities for Praveen's Financial Tools

// ── Format helpers ────────────────────────────────────────────────────────
function fmtM(v) {
  const a = Math.abs(v), s = v < 0 ? '-' : '';
  if (a >= 1e6) return s + '€' + (a / 1e6).toFixed(2) + 'M';
  if (a >= 1e3) return s + '€' + Math.round(a / 1000) + 'K';
  return s + '€' + Math.round(a);
}
function fmtPct(v, d=1) { return (v * 100).toFixed(d) + '%'; }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

// ── Chart constants ───────────────────────────────────────────────────────
const GC = 'rgba(255,255,255,0.04)';
const TC = { color: '#50506a', font: { family: 'DM Mono, monospace', size: 9 } };

// ── Chart registry ────────────────────────────────────────────────────────
const _charts = {};
function killChart(id) {
  if (_charts[id]) { _charts[id].destroy(); delete _charts[id]; }
}
function regChart(id, instance) { _charts[id] = instance; return instance; }

// ── Percentile ────────────────────────────────────────────────────────────
function pctile(sorted, p) {
  const i = Math.floor((p / 100) * sorted.length);
  return sorted[Math.min(i, sorted.length - 1)];
}

// ── Box-Muller normal random ──────────────────────────────────────────────
function gauss() {
  let u = 0, v = 0;
  while (!u) u = Math.random();
  while (!v) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// ── Pill toggle helper ────────────────────────────────────────────────────
function setPill(groupEl, clickedEl, callback) {
  groupEl.querySelectorAll('.pill').forEach(p => p.classList.remove('on'));
  clickedEl.classList.add('on');
  if (callback) callback(clickedEl.dataset.value);
}

// ── Toggle group helper ───────────────────────────────────────────────────
function setTgl(groupEl, val) {
  groupEl.querySelectorAll('.tgl').forEach(t => {
    t.classList.toggle('on', t.dataset.value === val);
  });
}

// ── Progress helper ───────────────────────────────────────────────────────
function setProgress(barEl, pct) {
  barEl.style.width = Math.round(pct * 100) + '%';
}

// ── Score color ───────────────────────────────────────────────────────────
function scoreColor(s) {
  return s >= 72 ? 'var(--green2)' : s >= 50 ? 'var(--amber2)' : 'var(--red2)';
}
