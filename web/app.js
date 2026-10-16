'use strict';
/* Piráti Praha 5 – volby 2026. Data: data/data.json (generuje build.py). */

const $ = (s) => document.querySelector(s);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const nf = (v, d = 1) => (v == null || isNaN(v) ? '–' : Number(v).toLocaleString('cs-CZ', { minimumFractionDigits: d, maximumFractionDigits: d }));
const pct = (v, d = 1) => (v == null ? '–' : nf(v, d) + ' %');
const pp = (v, d = 1) => (v == null ? '–' : (v > 0 ? '+' : v < 0 ? '−' : '±') + nf(Math.abs(v), d) + ' p. b.');
const pr = (v, d = 1) => (v == null ? '–' : (v > 0 ? '+' : v < 0 ? '−' : '±') + nf(Math.abs(v), d) + ' %');
const int = (v) => (v == null ? '–' : Math.round(v).toLocaleString('cs-CZ'));
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const sgnCls = (v) => (v < 0 ? 'down' : v > 0 ? 'up' : '');

const BLUE = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#104281'];
const ORANGE = ['#fbd9c8', '#f6b393', '#f08b5f', '#eb6834', '#c4501f', '#8f3814'];
const DIV = ['#b8322f', '#dc5f55', '#ec958b', '#f5c6c0', '#e1e0d9', '#6da7ec'];
const TYPES = ['Stánek / stan', 'Rozdávání letáků', 'SWAP', 'Debata', 'Roznos do schránek', 'Komunitní akce'];
const typeColor = (t) => css('--s' + (TYPES.indexOf(t) + 1));

/* ---------- tooltip ---------- */
const tip = $('#tip');
function showTip(html, ev) {
  tip.innerHTML = html; tip.hidden = false;
  const x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  const y = Math.min(ev.clientY + 14, window.innerHeight - tip.offsetHeight - 8);
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
const hideTip = () => { tip.hidden = true; };

/* ---------- SVG helpers ---------- */
const NS = 'http://www.w3.org/2000/svg';
function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function svgRoot(container, w, h) {
  container.innerHTML = '';
  const s = el('svg', { viewBox: `0 0 ${w} ${h}`, width: w, role: 'img' });
  container.appendChild(s);
  return s;
}
function hover(node, html) {
  node.addEventListener('mousemove', (e) => showTip(html, e));
  node.addEventListener('mouseleave', hideTip);
}

/* Tabulková alternativa ke grafu (přístupnost, kopírování čísel) */
function tableToggle(container, headers, rows) {
  const d = document.createElement('details');
  d.className = 'tbl';
  d.innerHTML = `<summary>Zobrazit jako tabulku</summary><div class="tablewrap"><table class="data"><thead><tr>${headers.map((h) => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  container.appendChild(d);
}
const stripHtml = (s) => String(s ?? '').replace(/<br\s*\/?>/g, ' · ').replace(/<[^>]+>/g, '');

/* Dumbbell: rows [{label, a, b, hi, extra}] – a = dřívější, b = pozdější. */
function dumbbell(container, rows, opts = {}) {
  dumbbellSvg(container, rows, opts);
  const { la = '2022', lb = '2026', extraLabel } = opts;
  tableToggle(container, ['', la, lb, ...(extraLabel ? [extraLabel] : [])], rows.map((r) => [r.label, pct(r.a), pct(r.b), ...(extraLabel ? [r.extra ?? ''] : [])]));
}
function dumbbellSvg(container, rows, { la = '2022', lb = '2026', max, extraLabel } = {}) {
  const W = 560, rowH = 30, L = 170, R = extraLabel ? 70 : 24, T = 26;
  const H = T + rows.length * rowH + 22;
  const s = svgRoot(container, W, H);
  max = max || Math.ceil(Math.max(...rows.flatMap((r) => [r.a || 0, r.b || 0])) / 5) * 5;
  const x = (v) => L + (v / max) * (W - L - R);
  for (let t = 0; t <= max; t += max > 30 ? 10 : 5) {
    el('line', { x1: x(t), x2: x(t), y1: T - 6, y2: H - 20, class: 'grid' }, s);
    el('text', { x: x(t), y: H - 6, 'text-anchor': 'middle' }, s).textContent = t + ' %';
  }
  // legenda
  const lg = el('g', {}, s);
  el('circle', { cx: L, cy: 10, r: 5, fill: 'none', stroke: css('--ink-2'), 'stroke-width': 2 }, lg);
  el('text', { x: L + 10, y: 14 }, lg).textContent = la;
  el('circle', { cx: L + 60, cy: 10, r: 5, fill: css('--ink') }, lg);
  el('text', { x: L + 70, y: 14 }, lg).textContent = lb;
  if (extraLabel) el('text', { x: W - 4, y: 14, 'text-anchor': 'end' }, s).textContent = extraLabel;
  rows.forEach((r, i) => {
    const y = T + i * rowH + rowH / 2;
    const ink = r.hi ? css('--ink') : css('--muted');
    const g = el('g', {}, s);
    el('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: 'transparent' }, g);
    const t = el('text', { x: L - 10, y: y + 4, 'text-anchor': 'end', class: r.hi ? 'lbl' : '' }, g);
    t.textContent = r.label; if (r.hi) t.setAttribute('font-weight', '650');
    if (r.a != null && r.b != null) el('line', { x1: x(r.a), x2: x(r.b), y1: y, y2: y, stroke: r.hi ? css('--ink') : css('--gray-mark'), 'stroke-width': 2 }, g);
    if (r.a != null) el('circle', { cx: x(r.a), cy: y, r: 5, fill: css('--surface'), stroke: ink, 'stroke-width': 2 }, g);
    if (r.b != null) el('circle', { cx: x(r.b), cy: y, r: 6, fill: r.hi ? css('--ink') : css('--muted'), stroke: css('--surface'), 'stroke-width': 2 }, g);
    if (r.hi || r.lab) {
      const v = r.b ?? r.a;
      const right = r.b != null && r.a != null && r.b < r.a;
      el('text', { x: x(v) + (right ? -10 : 10), y: y + 4, 'text-anchor': right ? 'end' : 'start', class: 'lbl' }, g).textContent = nf(v);
    }
    if (extraLabel) el('text', { x: W - 4, y: y + 4, 'text-anchor': 'end' }, g).textContent = r.extra ?? '';
    hover(g, `<b>${esc(r.label)}</b><br>${la}: ${pct(r.a, 2)}${r.ma != null ? ` (${r.ma} mand.)` : ''}<br>${lb}: ${pct(r.b, 2)}${r.mb != null ? ` (${r.mb} mand.)` : ''}` +
      (r.a != null && r.b != null ? `<br>změna: ${pp(r.b - r.a, 2)}` : '') + (r.tipx || ''));
  });
}

/* Horizontální sloupce: rows [{label, v, hi, note}] */
function bars(container, rows, opts = {}) {
  barsSvg(container, rows, opts);
  if (!opts.noTable) tableToggle(container, ['', 'hodnota'], rows.map((r) => [r.label, r.txt ?? nf(r.v, opts.d ?? 1) + (opts.unit ?? ' %')]));
}
function barsSvg(container, rows, { max, unit = ' %', d = 1 } = {}) {
  const W = Math.max(280, Math.min(560, container.clientWidth || 560)), rowH = W < 400 ? 22 : 30, L = Math.min(200, Math.round(W * 0.42)), R = 56, T = 6;
  const H = T + rows.length * rowH + 6;
  const s = svgRoot(container, W, H);
  max = max || Math.max(...rows.map((r) => r.v));
  const x = (v) => (v / max) * (W - L - R);
  rows.forEach((r, i) => {
    const y = T + i * rowH;
    const g = el('g', {}, s);
    el('rect', { x: 0, y, width: W, height: rowH, fill: 'transparent' }, g);
    const t = el('text', { x: L - 10, y: y + rowH / 2 + 4, 'text-anchor': 'end', class: r.hi ? 'lbl' : '' }, g);
    t.textContent = r.label; if (r.hi) t.setAttribute('font-weight', '650');
    const w = Math.max(2, x(r.v));
    el('path', { d: `M${L},${y + 5} h${w - 4} a4,4 0 0 1 4,4 v${rowH - 18} a4,4 0 0 1 -4,4 h${-(w - 4)} z`, fill: r.color || (r.hi ? css('--ink') : css('--gray-mark')) }, g);
    el('text', { x: L + w + 6, y: y + rowH / 2 + 4, class: 'lbl' }, g).textContent = r.txt ?? nf(r.v, d) + unit;
    hover(g, `<b>${esc(r.label)}</b><br>${nf(r.v, 2)}${unit}${r.note ? '<br>' + r.note : ''}`);
  });
}

/* Bodový graf: points [{x, y, label, series}] */
function scatter(container, pts, opts = {}) {
  scatterSvg(container, pts, opts);
  tableToggle(container, ['bod', opts.xl, opts.yl], pts.map((p) => [stripHtml(p.tip || p.label), nf(p.x, 2), nf(p.y, 2)]));
}
function scatterSvg(container, pts, { xl, yl, series, zeroY = false, zeroX = false, fit = false } = {}) {
  const W = 560, H = 380, L = 48, R = 16, T = 16, B = 44;
  const s = svgRoot(container, W, H);
  const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
  const nice = (a, b) => { const r = b - a, st = r > 20 ? 5 : r > 8 ? 2 : r > 3 ? 1 : r > 1.2 ? 0.5 : 0.25; return [Math.floor(a / st) * st, Math.ceil(b / st) * st, st]; };
  const [x0, x1, xst] = nice(Math.min(zeroX ? 0 : Infinity, ...xs), Math.max(...xs));
  const [y0, y1, yst] = nice(Math.min(...ys, zeroY ? 0 : Infinity), Math.max(...ys, zeroY ? 0 : -Infinity));
  const X = (v) => L + ((v - x0) / (x1 - x0 || 1)) * (W - L - R);
  const Y = (v) => H - B - ((v - y0) / (y1 - y0 || 1)) * (H - T - B);
  for (let v = y0; v <= y1 + 1e-9; v += yst) {
    el('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: Math.abs(v) < 1e-9 ? 'axis' : 'grid' }, s);
    el('text', { x: L - 6, y: Y(v) + 4, 'text-anchor': 'end' }, s).textContent = nf(v, yst < 1 ? 2 : 0);
  }
  for (let v = x0; v <= x1 + 1e-9; v += xst) {
    el('line', { x1: X(v), x2: X(v), y1: T, y2: H - B, class: 'grid' }, s);
    el('text', { x: X(v), y: H - B + 16, 'text-anchor': 'middle' }, s).textContent = nf(v, xst < 1 ? 2 : 0);
  }
  el('text', { x: (L + W - R) / 2, y: H - 6, 'text-anchor': 'middle' }, s).textContent = xl;
  const yt = el('text', { x: 12, y: (T + H - B) / 2, 'text-anchor': 'middle', transform: `rotate(-90 12 ${(T + H - B) / 2})` }, s);
  yt.textContent = yl;
  const ser = series || [{ key: undefined, color: css('--s1') }];
  if (fit) {
    ser.forEach((sr) => {
      const P = pts.filter((p) => p.series === sr.key);
      const n = P.length, mx = P.reduce((a, p) => a + p.x, 0) / n, my = P.reduce((a, p) => a + p.y, 0) / n;
      const b = P.reduce((a, p) => a + (p.x - mx) * (p.y - my), 0) / P.reduce((a, p) => a + (p.x - mx) ** 2, 0);
      const lo = Math.min(...P.map((p) => p.x)), hi = Math.max(...P.map((p) => p.x));
      el('line', { x1: X(lo), x2: X(hi), y1: Y(my + b * (lo - mx)), y2: Y(my + b * (hi - mx)), stroke: sr.color, 'stroke-width': 2, opacity: 0.8 }, s);
    });
  }
  pts.forEach((p) => {
    const sr = ser.find((q) => q.key === p.series) || ser[0];
    const c = el('circle', { cx: X(p.x), cy: Y(p.y), r: 5, fill: sr.color, stroke: css('--surface'), 'stroke-width': 2, 'fill-opacity': 0.85 }, s);
    const hit = el('circle', { cx: X(p.x), cy: Y(p.y), r: 10, fill: 'transparent' }, s);
    hover(hit, p.tip || esc(p.label));
    if (p.onclick) { hit.style.cursor = 'pointer'; hit.addEventListener('click', p.onclick); }
  });
}

/* Skládané sloupce po týdnech */
function weekBars(container, weeks) {
  const W = 560, H = 260, L = 30, R = 8, T = 10, B = 40;
  const s = svgRoot(container, W, H);
  const max = Math.max(...weeks.map((w) => w.total));
  const bw = (W - L - R) / weeks.length;
  const Y = (v) => H - B - (v / max) * (H - T - B);
  for (let v = 0; v <= max; v += 2) {
    el('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: v ? 'grid' : 'axis' }, s);
    el('text', { x: L - 6, y: Y(v) + 4, 'text-anchor': 'end' }, s).textContent = v;
  }
  weeks.forEach((w, i) => {
    const x = L + i * bw + 1;
    let acc = 0;
    const g = el('g', {}, s);
    el('rect', { x, y: T, width: bw - 2, height: H - T - B, fill: 'transparent' }, g);
    TYPES.forEach((t) => {
      const n = w.byType[t] || 0;
      if (!n) return;
      const y1 = Y(acc + n), y0 = Y(acc);
      el('rect', { x, y: y1 + (acc ? 0 : 0), width: Math.max(1, bw - 2), height: Math.max(0, y0 - y1 - 1), fill: typeColor(t), rx: 1.5 }, g);
      acc += n;
    });
    if (w.label) el('text', { x: x + bw / 2, y: H - B + 16, 'text-anchor': 'middle' }, s).textContent = w.label;
    hover(g, `<b>Týden od ${w.from}</b><br>` + TYPES.filter((t) => w.byType[t]).map((t) => `${t}: ${w.byType[t]}`).join('<br>') + `<br><b>celkem ${w.total}</b>`);
  });
  el('line', { x1: L, x2: W - R, y1: H - B, y2: H - B, class: 'axis' }, s);
}

/* Sankey: cats (stejné kategorie vlevo i vpravo), size = velikost kategorií 2022 (osoby), M = matice přesunů (řádky 2022) */
const CAT_COLOR = [[/^Piráti/, '--ink'], [/SOBĚ/, '--s4'], [/^ODS|^SPOLU/, '--s1'], [/^STAN/, '--s5'], [/^SEN/, '--s3'], [/^ANO/, '--s7'], [/^SPD|^Ostatní|^Motoristé/, '--s2'], [/^Nevoliči/, '--gray-mark']];
const catColor = (c) => css((CAT_COLOR.find(([rx]) => rx.test(c)) || [0, '--muted'])[1]);
function sankey(container, { cats, catsR, size, M, nonvoters = false }) {
  catsR = catsR || cats;
  const W = 760, H = 460, NW = 14, GAP = 10, LW = 170;
  // bez zaškrtnutí se skryje jen tok "nevolil ani jednou" (jinak by přebil celý diagram); příchody a odchody nevoličů zůstávají
  const idx = cats.map((c, i) => i), jdx = catsR.map((c, j) => j);
  const f = idx.map((i) => jdx.map((j) => (!nonvoters && cats[i] === 'Nevoliči' && catsR[j] === 'Nevoliči' ? 0 : size[cats[i]] * M[i][j])));
  const Lt = f.map((r) => r.reduce((a, b) => a + b, 0)), Rt = jdx.map((_, j) => f.reduce((a, r) => a + r[j], 0));
  const T = Lt.reduce((a, b) => a + b, 0), k = (H - 20 - GAP * (Math.max(idx.length, jdx.length) - 1)) / T;
  const s = svgRoot(container, W, H), x0 = LW, x1 = W - LW - NW;
  const ly = [], ry = [];
  let y = 10; Lt.forEach((v) => { ly.push(y); y += v * k + GAP; });
  y = 10; Rt.forEach((v) => { ry.push(y); y += v * k + GAP; });
  const lOff = [...ly], rOff = [...ry];
  const links = el('g', {}, s);
  idx.forEach((_, a) => jdx.forEach((__, b) => {
    const v = f[a][b], h = v * k;
    const ys = lOff[a], yt = rOff[b]; lOff[a] += h; rOff[b] += h;
    if (v < T * 0.002) return;
    const mx = (x0 + NW + x1) / 2, src = cats[idx[a]], tgt = catsR[jdx[b]];
    const pir = /^Piráti/.test(src) || /^Piráti/.test(tgt);
    const p = el('path', { d: `M${x0 + NW},${ys} C${mx},${ys} ${mx},${yt} ${x1},${yt} L${x1},${yt + h} C${mx},${yt + h} ${mx},${ys + h} ${x0 + NW},${ys + h} Z`,
      fill: catColor(src), 'fill-opacity': pir ? 0.55 : 0.22 }, links);
    hover(p, `<b>${esc(src)} → ${esc(tgt)}</b><br>≈ ${int(v)} voličů<br>${nf(v / Lt[a] * 100, 0)} % voličů ${esc(src)}${tgt === 'Nevoliči' || src === 'Nevoliči' ? '<br><i>toky z/do nevoličů jsou nejméně jistý odhad</i>' : ''}`);
  }));
  const node = (x, yy, h, c, n, left) => {
    if (n < 1) return; // prázdný uzel (např. nevoliči bez toků) nekreslit
    el('rect', { x, y: yy, width: NW, height: Math.max(1, h), rx: 2, fill: catColor(c) }, s);
    const t = el('text', { x: left ? x - 6 : x + NW + 6, y: yy + Math.max(h, 12) / 2 + 4, 'text-anchor': left ? 'end' : 'start', class: 'lbl' }, s);
    t.textContent = `${c === 'Nevoliči' ? (left ? 'Nevolili (dříve)' : 'Nevolili (nyní)') : c} · ${int(n)}`;
    if (/^Piráti/.test(c)) t.setAttribute('font-weight', '650');
  };
  idx.forEach((i, a) => node(x0, ly[a], Lt[a] * k, cats[i], Lt[a], true));
  jdx.forEach((j, b) => node(x1, ry[b], Rt[b] * k, catsR[j], Rt[b], false));
  el('text', { x: x0 + NW / 2, y: H - 2, 'text-anchor': 'middle' }, s).textContent = '';
}

/* ---------- tabulky ---------- */
function table(elm, cols, rows, { sort, desc = true, onRow, rowClass } = {}) {
  let sk = sort, sd = desc;
  function render() {
    const R = [...rows];
    if (sk) R.sort((a, b) => {
      const c = cols.find((q) => q.k === sk), va = c.sv ? c.sv(a) : a[sk], vb = c.sv ? c.sv(b) : b[sk];
      if (va == null) return 1; if (vb == null) return -1;
      return (typeof va === 'string' ? va.localeCompare(vb, 'cs') : va - vb) * (sd ? -1 : 1);
    });
    elm.innerHTML = '<thead><tr>' + cols.map((c) => `<th class="${c.n ? 'n' : ''}" data-k="${c.k}" ${sk === c.k ? `aria-sort="${sd ? 'descending' : 'ascending'}"` : ''} title="${esc(c.title || '')}">${c.label}</th>`).join('') + '</tr></thead><tbody>' +
      R.map((r, i) => `<tr data-i="${rows.indexOf(r)}" class="${onRow ? 'click ' : ''}${rowClass ? rowClass(r) : ''}">` + cols.map((c) => `<td class="${c.n ? 'n' : ''} ${c.cls || ''}">${c.f ? c.f(r) : esc(r[c.k])}</td>`).join('') + '</tr>').join('') + '</tbody>';
    if (elm.classList.contains('sortable')) elm.querySelectorAll('th').forEach((th) => th.addEventListener('click', () => {
      const k = th.dataset.k; if (sk === k) sd = !sd; else { sk = k; sd = !!cols.find((c) => c.k === k).n; } render();
    }));
    if (onRow) elm.querySelectorAll('tbody tr').forEach((tr) => tr.addEventListener('click', () => onRow(rows[+tr.dataset.i])));
  }
  render();
  return { set(newRows) { rows = newRows; render(); } };
}

/* ---------- mapy ---------- */
function tiles(map) {
  const dark = matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme !== 'light';
  const base = dark ? 'World_Dark_Gray_Base' : 'World_Light_Gray_Base';
  const ref = dark ? 'World_Dark_Gray_Reference' : 'World_Light_Gray_Reference';
  L.tileLayer(`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/${base}/MapServer/tile/{z}/{y}/{x}`, {
    attribution: 'Podklad © Esri, HERE, OpenStreetMap · okrsky © ČSÚ', maxZoom: 16,
  }).addTo(map);
  L.tileLayer(`https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/${ref}/MapServer/tile/{z}/{y}/{x}`, { maxZoom: 16, pane: 'shadowPane' }).addTo(map);
}
const binColor = (v, breaks, ramp) => { if (v == null) return '#999'; let i = 0; while (i < breaks.length && v >= breaks[i]) i++; return ramp[i]; };
function legend(elm, breaks, ramp, fmt) {
  const lab = (i) => i === 0 ? `pod ${fmt(breaks[0])}` : i === breaks.length ? `${fmt(breaks[i - 1])} a víc` : `${fmt(breaks[i - 1])} – ${fmt(breaks[i])}`;
  elm.innerHTML = ramp.map((c, i) => `<span><span class="sw" style="background:${c}"></span>${lab(i)}</span>`).join('');
}

/* ---------- tlačítko „zpět“ u každé sekce (návrat na obsah bez scrollování) ---------- */
document.querySelectorAll('main section[id]').forEach((sec) => {
  if (sec.id === 'tiles') return;
  const a = document.createElement('a');
  a.href = '#top'; a.className = 'back'; a.textContent = '‹ zpět na obsah';
  a.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('top').scrollIntoView({ behavior: 'smooth' }); history.replaceState(null, '', location.pathname); });
  sec.insertBefore(a, sec.firstChild);
});

/* ---------- zjištění z Markdownu (složka zjisteni/) ---------- */
const ZJISTENI = ['hlavni-zjisteni.md', 'metodika.md', 'dalsi-pohledy.md'];
document.querySelectorAll('[data-md]').forEach((elm) => {
  if (!ZJISTENI.includes(elm.dataset.md)) return;
  fetch('../zjisteni/' + elm.dataset.md).then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.status)))).then((md) => {
    elm.innerHTML = window.marked ? marked.parse(md) : `<pre>${esc(md)}</pre>`;
  }).catch((e) => { elm.innerHTML = `<p class="muted">Soubor zjisteni/${esc(elm.dataset.md)} se nepodařilo načíst (${esc(e.message)}).</p>`; });
});

/* ---------- hlavní ---------- */
fetch('../data/data.json?v=20261016d').then((r) => r.json()).then(init).catch((e) => {
  document.querySelector('main').insertAdjacentHTML('afterbegin', `<p class="card">Data se nepodařilo načíst (${esc(e.message)}). Stránku je potřeba otevřít přes web server, ne jako soubor.</p>`);
});

function init(D) {
  const P = D.p5, O = D.okrsky, S = D.stats, RZ = D.rozsireni || {};
  const byO = Object.fromEntries(O.map((o) => [o.okrsek, o]));
  const pub = D.akce.filter((a) => a.typ !== 'Interní' && a.datum >= '2026-01-01');
  const p26 = D.p5_parties['2026'], p22 = D.p5_parties['2022'];
  const find = (arr, rx) => arr.find((p) => rx.test(p.nazev));
  const sen22 = find(p22, /SEN/), sen26 = find(p26, /SEN/);
  const C = Object.fromEntries(D.ctvrti.map((c) => [c.ctvrt, c]));
  const kryl = D.p5_kandidati.find((k) => /Kryl/.test(k.jmeno));
  const mandK = D.p5_kandidati.filter((k) => k.mandat);

  /* tiles */
  const tile = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
  $('#tiles').innerHTML =
    tile('Praha 5 – zastupitelstvo MČ', pct(P.mc_2026, 2), `<b class="down">${pp(P.mc_2026 - P.mc_2022, 2)}</b> · ${P.mc_mand_2026} mandáty z 41 (2022: ${P.mc_mand_2022})`) +
    tile('Praha 5 – hlasy na magistrát', pct(P.mag_2026, 2), `<b class="down">${pp(P.mag_2026 - P.mag_2022, 2)}</b> proti 2022`) +
    tile('Praha – magistrát celkem', pct(D.praha_mag_2026.pct, 2), `<b class="down">${pp(D.praha_mag_2026.pct - D.praha_mag_2022.pct, 2)}</b> · ${D.praha_mag_2026.mandaty} mandátů (2022: ${D.praha_mag_2022.mandaty})`) +
    tile('Účast Praha 5', pct(P.ucast_2026), `<b class="up">${pp(P.ucast_2026 - P.ucast_2022)}</b> · ≈ ${int(P.mc_volici_2026)} pirátských voličů (2022: ${int(P.mc_volici_2022)})`);

  /* Praha */
  $('#praha-note').innerHTML = `Účast v Praze ${pct(D.praha_ucast_2026)} (2022: ${pct(D.praha_ucast_2022)}). Ve sněmovních volbách 2025 měli Piráti v Praze ${pct(D.praha_ps25, 2)}.`;
  const fam = [
    ['STAN', /^STAROSTOVÉ/], ['SPOLU', /^SPOLU/], ['PRAHA SOBĚ', /^PRAHA SOBĚ/], ['ANO', /^ANO/], ['Piráti', /pirátská/i],
    ['SPD a spojenci', /^SPD/], ['Motoristé', /^Motoristé/], ['SEN', /^SEN/],
  ];
  const famRows = (A, B, F) => F.map(([lab, rx]) => {
    const a = A.find((p) => rx.test(p.nazev)), b = B.find((p) => rx.test(p.nazev));
    return { label: lab, a: a?.pct ?? null, b: b?.pct ?? null, ma: a?.mandaty, mb: b?.mandaty, hi: lab === 'Piráti' };
  }).filter((r) => r.a != null || r.b != null).sort((x, y) => (y.b ?? 0) - (x.b ?? 0));
  dumbbell($('#ch-mag'), famRows(D.mag_parties['2022'], D.mag_parties['2026'], fam), { max: 30 });

  const mapPraha = L.map('map-praha', { scrollWheelZoom: false, zoomSnap: 0.25 });
  tiles(mapPraha);
  const brP = [6, 8, 10, 12, 14];
  fetch('../data/okrsky_praha.geojson').then((r) => r.json()).then((g) => {
    const mcName = Object.fromEntries(D.mc.map((m) => [m.kod, m.nazev]));
    const lyr = L.geoJSON(g, {
      style: (f) => ({ fillColor: binColor(f.properties.p26, brP, BLUE), fillOpacity: 0.8, color: css('--surface'), weight: 0.4 }),
      onEachFeature: (f, l) => l.bindTooltip(`<b>${esc(mcName[f.properties.m] || '')}, okrsek ${f.properties.o}</b><br>2026: ${pct(f.properties.p26)}<br>2022: ${pct(f.properties.p22)}`, { sticky: true }),
    }).addTo(mapPraha);
    mapPraha.fitBounds(lyr.getBounds());
  });
  legend($('#lg-praha'), brP, BLUE, (v) => v + ' %');

  table($('#tb-mc'), [
    { k: 'nazev', label: 'Městská část' },
    { k: 'mag_2022', label: 'Mag. 2022', n: 1, f: (r) => pct(r.mag_2022) },
    { k: 'mag_2026', label: 'Mag. 2026', n: 1, f: (r) => pct(r.mag_2026) },
    { k: 'dmag', label: 'Změna', n: 1, sv: (r) => r.mag_2026 - r.mag_2022, f: (r) => `<span class="${sgnCls(r.mag_2026 - r.mag_2022)}">${pp(r.mag_2026 - r.mag_2022)}</span>` },
    { k: 'ps25', label: 'PS 2025', n: 1, f: (r) => pct(r.ps25) },
    { k: 'mc_2022', label: 'MČ 2022', n: 1, f: (r) => r.mc_2022 != null ? `${pct(r.mc_2022)} · ${r.mc_mand_2022}` : '–', title: 'podíl · mandáty' },
    { k: 'mc_2026', label: 'MČ 2026', n: 1, f: (r) => r.mc_2026 != null ? `${pct(r.mc_2026)} · ${r.mc_mand_2026}` : '–', title: 'podíl · mandáty' },
    { k: 'mc_list_2026', label: 'Listina 2026', f: (r) => esc(r.mc_list_2026 || ''), cls: 'wrap' },
  ], D.mc.filter((m) => m.mag_2026 != null), { sort: 'mag_2026', rowClass: (r) => (r.kod === 500143 ? 'hl' : '') });

  /* Praha 5 – strany */
  const famP5 = [
    ['PRAHA 5 SOBĚ', /^PRAHA 5 SOBĚ/], ['ODS (2022 SPOLEČNĚ s TOP 09)', /SPOLEČNĚ PRO PRAHU 5|Občanská demokratická/], ['STAN', /^STAROSTOVÉ/],
    ['SEN (Václav Láska)', /^SEN|SEN 21/], ['ANO', /^ANO/], ['Piráti', /pirátská/i], ['TOP 09 a KDU', /^TOP Lidovci|^KDU-ČSL, Zelení/], ['SPD', /^SPD|^Svoboda a přímá/],
  ];
  dumbbell($('#ch-p5'), famRows(p22, p26, famP5).map((r) => ({ ...r, extra: `${r.ma ?? 0} → ${r.mb ?? 0}` })), { max: 25, extraLabel: 'mandáty' });
  bars($('#ch-p5-trend'), [
    { label: 'KV 2022 – magistrát', v: P.mag_2022, color: css('--gray-mark') },
    { label: 'KV 2022 – MČ Praha 5', v: P.mc_2022, color: css('--gray-mark') },
    { label: 'PS 2025 – sněmovna', v: P.ps_2025, color: css('--gray-mark'), note: `${int(P.ps_2025_hlasy)} hlasů, účast ${pct(P.ucast_ps_2025)}` },
    { label: 'KV 2026 – magistrát', v: P.mag_2026, hi: true },
    { label: 'KV 2026 – MČ Praha 5', v: P.mc_2026, hi: true },
  ], { max: 22 });

  /* Okrsky – mapa */
  const LAYERS = [
    { k: 'mc_2026', label: 'Piráti MČ 2026', br: [5, 7, 9, 11, 13], ramp: BLUE },
    { k: 'mc_delta', label: 'Změna 2022 → 2026', br: [-8, -5, -3, -1, 1], ramp: DIV, fmt: (v) => (v > 0 ? '+' : '') + nf(v, 0) },
    { k: 'mag_2026', label: 'Piráti magistrát 2026', br: [7, 9, 11, 13, 15], ramp: BLUE },
    { k: 'ps_2025', label: 'Piráti sněmovna 2025', br: [15, 18, 21, 24, 27], ramp: BLUE },
    { k: 'sen_2026', label: 'SEN 2026', br: [5, 10, 15, 20, 25], ramp: ORANGE },
    { k: 'stan_2026', label: 'STAN 2026', br: [10, 13, 16, 19, 22], ramp: ORANGE },
    { k: 'laska', label: 'Láska (senát)', br: [20, 25, 30, 35, 40], ramp: ORANGE, get: (o) => o.senat_laska },
    { k: 'senat_sarapatka', label: 'Šarapatka (senát)', br: [12, 16, 20, 24, 28], ramp: ORANGE, get: (o) => o.senat_sarapatka },
    { k: 'ucast_2026', label: 'Účast 2026', br: [35, 42, 48, 54, 60], ramp: BLUE },
    { k: 'zs_uspesnost', label: 'Spádová ZŠ: úspěšnost', br: [65, 75, 85, 92, 98], ramp: BLUE },
    { k: 'cen_0_14', label: 'Děti 0–14 (SLDB)', br: [12, 14, 16, 18, 20], ramp: BLUE },
    { k: 'cen_65', label: 'Senioři 65+ (SLDB)', br: [12, 14, 16, 18, 20], ramp: BLUE },
    { k: 'cen_rust_11_21', label: 'Růst obyvatel 2011–21', br: [-5, 0, 5, 10, 20], ramp: BLUE, fmt: (v) => v + ' %' },
    { k: 'cen26_0_14', label: 'Děti 0–14 (2026)', br: [12, 14, 16, 18, 20], ramp: BLUE },
    { k: 'cen26_65', label: 'Senioři 65+ (2026)', br: [12, 14, 16, 18, 20], ramp: BLUE },
    { k: 'mc_minus_mag', label: 'Piráti MČ − magistrát', br: [-4, -2, -1, 0, 1], ramp: DIV, fmt: (v) => (v > 0 ? '+' : '') + nf(v, 0) },
    { k: 'senat_k2_sablik', label: 'Senát 2. kolo: předpověď', br: [40, 45, 50, 55, 60], ramp: ['#0e7a52', '#1baf7a', '#a3dcc5', '#b5d3f5', '#5a9be6', '#1f5fae'], fmt: (v) => nf(v, 0) + ' %', unit: ' Sáblík (zbytek Láska)' },
    { k: 'hledani_skore', label: '4. mandát: kde hledat', br: [100, 200, 300, 450, 600], ramp: ORANGE, get: (o) => ((D.hledani || {}).okrsky || []).find((r) => r.okrsek === o.okrsek)?.skore, fmt: (v) => v },
    { k: 'pedersen', label: 'Volatilita (Pedersen)', br: [10, 13, 16, 19, 22], ramp: ORANGE, fmt: (v) => v },
    { k: 'akce', label: 'Akce', br: [1, 3, 6, 10, 14], ramp: BLUE, get: (o) => o.akci_kampan_do_700m, fmt: (v) => v, unit: ' akcí do 700 m' },
  ];
  let cur = LAYERS[0], sel = null;
  const val = (o, L) => (L.get ? L.get(o) : o[L.k]);
  const mapP5 = L.map('map-p5', { scrollWheelZoom: false, zoomSnap: 0.25 });
  tiles(mapP5);
  let p5lyr;
  const evLayer = L.layerGroup();
  const byAnchor = {};
  pub.filter((a) => a.okrsek).forEach((a) => (byAnchor[a.okrsek] = byAnchor[a.okrsek] || []).push(a));
  Object.entries(byAnchor).forEach(([o, list]) => {
    const c = byO[o];
    const m = L.circleMarker([c.lat, c.lon], { radius: 4 + Math.sqrt(list.length) * 2.2, color: css('--surface'), weight: 2, fillColor: css('--ink'), fillOpacity: 0.85 });
    const types = {}; list.forEach((a) => (types[a.typ] = (types[a.typ] || 0) + 1));
    m.bindTooltip(`<b>Místo u okrsku ${o}: ${list.length} akcí</b><br>` + Object.entries(types).map(([t, n]) => `${t}: ${n}`).join('<br>') + `<br><span class="muted">${esc([...new Set(list.map((a) => a.misto).filter(Boolean))].slice(0, 3).join(', '))}</span>`);
    m.addTo(evLayer);
  });
  const btns = $('#layer-btns');
  btns.innerHTML = LAYERS.map((L, i) => `<button role="radio" aria-checked="${i === 0}" data-i="${i}">${L.label}</button>`).join('') +
    `<label style="margin-left:8px;font-size:14px"><input type="checkbox" id="ev-toggle"> místa akcí</label>` +
    `<label style="margin-left:8px;font-size:14px"><input type="checkbox" id="dom-toggle"> domovy pro seniory</label>`;
  btns.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
    btns.querySelectorAll('button').forEach((x) => x.setAttribute('aria-checked', 'false'));
    b.setAttribute('aria-checked', 'true'); cur = LAYERS[+b.dataset.i];
    if (cur.k === 'akce') { $('#ev-toggle').checked = true; evLayer.addTo(mapP5); }
    restyle();
  }));
  $('#ev-toggle').addEventListener('change', (e) => (e.target.checked ? evLayer.addTo(mapP5) : evLayer.remove()));
  const domLayer = L.layerGroup();
  ((D.rozsireni || {}).seniori || { domovy: [] }).domovy.forEach((d) => {
    L.marker([d.lat, d.lon], { icon: L.divIcon({ className: '', html: '<div style="width:16px;height:16px;border-radius:4px;background:#e34948;border:2px solid #fff;box-shadow:0 0 0 1px #0006"></div>', iconSize: [16, 16] }) })
      .bindTooltip(`<b>${esc(d.nazev || d.adresa)}</b><br>${esc(d.adresa)} · ${d.kapacita} lůžek<br>okrsek ${d.okrsek}`).addTo(domLayer);
  });
  $('#dom-toggle').addEventListener('change', (e) => (e.target.checked ? domLayer.addTo(mapP5) : domLayer.remove()));
  function styleF(f) {
    const o = byO[f.properties.o];
    return { fillColor: binColor(val(o, cur), cur.br, cur.ramp), fillOpacity: 0.82, color: sel === o.okrsek ? css('--ink') : css('--surface'), weight: sel === o.okrsek ? 3 : 1 };
  }
  function restyle() {
    p5lyr && p5lyr.setStyle(styleF);
    legend($('#lg-p5'), cur.br, cur.ramp, cur.fmt || ((v) => v + ' %'));
    if (cur.k === 'mc_delta') $('#lg-p5').insertAdjacentHTML('beforeend', '<span class="muted">p. b.</span>');
    if (cur.k === 'akce') $('#lg-p5').insertAdjacentHTML('beforeend', '<span class="muted">akcí v kampani do 700 m od okrsku</span>');
  }
  fetch('../data/okrsky_p5.geojson').then((r) => r.json()).then((g) => {
    p5lyr = L.geoJSON(g, {
      style: styleF,
      onEachFeature: (f, l) => {
        const o = byO[f.properties.o];
        l.bindTooltip(() => `<b>Okrsek ${o.okrsek} · ${o.ctvrt}</b><br>${cur.label}: ${cur.k === 'akce' ? val(o, cur) : cur.k === 'mc_delta' ? pp(val(o, cur)) : pct(val(o, cur))}`, { sticky: true });
        l.on('click', () => select(o.okrsek));
      },
    }).addTo(mapP5);
    mapP5.fitBounds(p5lyr.getBounds(), { padding: [10, 10] });
    restyle();
  });
  const SEN_C = D.senat.kandidati;
  function select(n, pan) {
    sel = n; const o = byO[n];
    p5lyr && p5lyr.setStyle(styleF);
    if (pan && p5lyr) p5lyr.eachLayer((l) => l.feature.properties.o === n && mapP5.fitBounds(l.getBounds(), { maxZoom: 15 }));
    const top = Object.entries(o.strany_2026).sort((a, b) => b[1] - a[1]).slice(0, 6);
    $('#okr-detail').innerHTML = `<h3>Okrsek ${o.okrsek} · ${esc(o.ctvrt)}</h3><p class="sub">${esc(o.mistnost)}, ${esc(o.adresa)}</p>
      <dl>
        <dt>Piráti MČ 2022 → 2026</dt><dd>${pct(o.mc_2022)} → <b>${pct(o.mc_2026)}</b></dd>
        <dt>Změna</dt><dd class="${sgnCls(o.mc_delta)}">${pp(o.mc_delta)}</dd>
        <dt>Pořadí Pirátů v okrsku</dt><dd>${o.mc_poradi_2026}. (2022: ${o.mc_poradi_2022}.)</dd>
        <dt>Piráti magistrát 2022 → 2026</dt><dd>${pct(o.mag_2022)} → ${pct(o.mag_2026)}</dd>
        <dt>Piráti sněmovna 2025</dt><dd>${pct(o.ps_2025)}</dd>
        <dt>Voliči / účast 2026</dt><dd>${int(o.volici_2026)} / ${pct(o.ucast_2026)}</dd>
        <dt>Účast 2022</dt><dd>${pct(o.ucast_2022)}</dd>
        <dt>SEN 2022 → 2026</dt><dd>${pct(o.sen_2022)} → ${pct(o.sen_2026)}</dd>
        <dt>STAN 2022 → 2026</dt><dd>${pct(o.stan_2022)} → ${pct(o.stan_2026)}</dd>
        <dt>Senát: Láska / Sáblík</dt><dd>${pct(o.senat_laska)} / ${pct(o.senat_sablik)}</dd>
        <dt>Akcí do 700 m (celkem / kampaň)</dt><dd>${o.akci_do_700m} / ${o.akci_kampan_do_700m}</dd>
        <dt>Volatilita (Pedersen)</dt><dd>${nf(o.pedersen)}</dd>
        <dt>Efektivní počet stran 2022 → 2026</dt><dd>${nf(o.enp_2022)} → ${nf(o.enp_2026)}</dd>
        <dt>SLDB 2021: děti / 65+</dt><dd>${pct(o.cen_0_14)} / ${pct(o.cen_65)}</dd>
        <dt>Růst obyvatel 2011–21</dt><dd>${pct(o.cen_rust_11_21)}</dd>
        <dt>Spádová ZŠ</dt><dd>${esc(o.zs_skola || '–')}</dd>
        <dt>Úspěšnost žádostí 2026 (2025)</dt><dd>${pct(o.zs_uspesnost, 0)} (${pct(o.zs_uspesnost_2025, 0)})</dd>
      </dl>
      <p class="sub"><a href="https://volby.gov.cz/app/kv2026/cs/20261009/results/!__0_1100_1100_500143___${o.okrsek}" target="_blank" rel="noopener">Výsledky okrsku na volby.gov.cz</a> · <a href="https://volby.gov.cz/appdata/kv2026/20261009/vysled/okrsek/1100/500143_${o.okrsek}.json" target="_blank" rel="noopener">data</a></p>
      <p class="sub"><b>Strany 2026 v okrsku</b></p><div id="okr-bars"></div>`;
    bars($('#okr-bars'), top.map(([k, v]) => ({ label: k.length > 26 ? k.slice(0, 25) + '…' : k, v, hi: /pirátská/i.test(k) })), { max: Math.max(30, top[0][1]), noTable: true });
  }

  // tabulka okrsků
  const cts = Object.keys(C);
  $('#f-ctvrt').innerHTML += cts.map((c) => `<option>${c}</option>`).join('');
  const dcol = (k) => ({ k, label: 'Změna', n: 1, f: (r) => `<span class="${sgnCls(r[k])}">${pp(r[k])}</span>` });
  const okrT = table($('#tb-okr'), [
    { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => r.okrsek },
    { k: 'ctvrt', label: 'Čtvrť' },
    { k: 'volici_2026', label: 'Voliči', n: 1, f: (r) => int(r.volici_2026) },
    { k: 'ucast_2026', label: 'Účast', n: 1, f: (r) => pct(r.ucast_2026) },
    { k: 'mc_2022', label: 'MČ 2022', n: 1, f: (r) => pct(r.mc_2022) },
    { k: 'mc_2026', label: 'MČ 2026', n: 1, f: (r) => `<b>${pct(r.mc_2026)}</b>` },
    dcol('mc_delta'),
    { k: 'mag_2026', label: 'Mag. 2026', n: 1, f: (r) => pct(r.mag_2026) },
    { k: 'ps_2025', label: 'PS 2025', n: 1, f: (r) => pct(r.ps_2025) },
    { k: 'sen_2026', label: 'SEN', n: 1, f: (r) => pct(r.sen_2026) },
    { k: 'stan_2026', label: 'STAN', n: 1, f: (r) => pct(r.stan_2026) },
    { k: 'senat_laska', label: 'Láska', n: 1, f: (r) => pct(r.senat_laska) },
    { k: 'vitez_2026', label: 'Vítěz MČ', f: (r) => esc(r.vitez_2026.slice(0, 22)) },
    { k: 'akci_kampan_do_700m', label: 'Akce', n: 1, title: 'akcí v kampani (září–říjen) do 700 m', f: (r) => r.akci_kampan_do_700m },
    { k: 'zs_skola', label: 'Spádová ZŠ', f: (r) => esc(r.zs_skola || '–') },
    { k: 'zs_uspesnost', label: 'ZŠ úspěšnost', n: 1, title: 'úspěšnost žádostí u zápisu 2026 na spádové ZŠ', f: (r) => pct(r.zs_uspesnost, 0) },
  ], O, { sort: 'okrsek', desc: false, onRow: (r) => { select(r.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); } });
  $('#f-ctvrt').addEventListener('change', (e) => okrT.set(e.target.value ? O.filter((o) => o.ctvrt === e.target.value) : O));
  const norm = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  $('#f-ulice').addEventListener('input', (e) => {
    const q = norm(e.target.value.trim());
    if (q.length < 3) { $('#f-ulice-out').innerHTML = ''; okrT.set(O); return; }
    const hit = O.filter((o) => (o.ulice || []).some((u) => norm(u).includes(q)) || norm(o.mistnost + ' ' + o.adresa).includes(q));
    okrT.set(hit);
    $('#f-ulice-out').innerHTML = hit.length ? `nalezeno: ${hit.map((o) => `<a href="#map-p5" data-o="${o.okrsek}">${o.okrsek}</a>`).join(', ')}` : 'nic nenalezeno';
    $('#f-ulice-out').querySelectorAll('a').forEach((a) => a.addEventListener('click', (ev) => { ev.preventDefault(); select(+a.dataset.o, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); }));
  });

  /* Čtvrti */
  const ctRows = [...D.ctvrti].sort((a, b) => b.mc_2026 - a.mc_2026);
  dumbbell($('#ch-ctvrti'), ctRows.map((c) => ({ label: `${c.ctvrt} (${c.okrsku})`, a: c.mc_2022, b: c.mc_2026, hi: true, extra: `${c.akci}`,
    tipx: `<br>magistrát: ${pct(c.mag_2022)} → ${pct(c.mag_2026)}<br>PS 2025: ${pct(c.ps_2025)}<br>akcí 2026: ${c.akci} (září–říjen ${c.akci_zari_rijen})` })), { max: 16, extraLabel: 'akcí' });
  table($('#tb-ctvrti'), [
    { k: 'ctvrt', label: 'Čtvrť' },
    { k: 'volici', label: 'Voliči', n: 1, f: (r) => int(r.volici) },
    { k: 'mc_2022', label: 'MČ 2022', n: 1, f: (r) => pct(r.mc_2022) },
    { k: 'mc_2026', label: 'MČ 2026', n: 1, f: (r) => `<b>${pct(r.mc_2026)}</b>` },
    { k: 'd', label: 'Změna', n: 1, f: (r) => `<span class="${sgnCls(r.mc_2026 - r.mc_2022)}">${pp(r.mc_2026 - r.mc_2022)}</span>` },
    { k: 'mag_2026', label: 'Mag. 2026', n: 1, f: (r) => pct(r.mag_2026) },
    { k: 'ps_2025', label: 'PS 2025', n: 1, f: (r) => pct(r.ps_2025) },
    { k: 'ucast_2026', label: 'Účast', n: 1, f: (r) => pct(r.ucast_2026) },
    { k: 'akci', label: 'Akce 2026', n: 1, f: (r) => r.akci },
    { k: 'akci_zari_rijen', label: 'z toho září–říjen', n: 1, f: (r) => r.akci_zari_rijen },
    { k: 'akci_na_1000_volicu', label: 'Akcí / 1000 voličů', n: 1, f: (r) => nf(r.akci_na_1000_volicu) },
    { k: 'hodin', label: 'Hodin', n: 1, f: (r) => nf(r.hodin, 0) },
    { k: 'ms_zadosti_na_misto', label: 'MŠ žádostí/místo', n: 1, f: (r) => nf(r.ms_zadosti_na_misto, 1) },
    { k: 'ms_uspesnost', label: 'MŠ úspěšnost', n: 1, f: (r) => pct(r.ms_uspesnost, 0) },
    { k: 'zs_uspesnost', label: 'Spádová ZŠ úspěšnost', n: 1, f: (r) => pct(r.zs_uspesnost, 0) },
  ], ctRows);

  /* Školy */
  const SK = D.skoly, sz = SK.souhrn;
  const zsRows = SK.zs_obvody.map((z) => {
    const okl = O.filter((o) => o.zs_obvody[0] && o.zs_obvody[0].obvod === z.obvod);
    const w = okl.reduce((a, o) => a + o.odevzdano_2026, 0);
    return { ...z, okrsky: okl.map((o) => o.okrsek), pir: w ? okl.reduce((a, o) => a + o.mc_2026 * o.odevzdano_2026, 0) / w : null,
      pirD: w ? okl.reduce((a, o) => a + o.mc_delta * o.odevzdano_2026, 0) / w : null, u25: z.r2025 ? z.r2025.uspesnost : null };
  });
  const worstZs = [...zsRows].filter((z) => z.spadove).sort((a, b) => a.uspesnost - b.uspesnost).slice(0, 3);
  $('#skoly-text').innerHTML = `<p><b>Celkem za Prahu 5:</b> do školek se v roce 2026 hlásilo ${int(sz.ms_2026.zadosti)} žádostí na ${int(sz.ms_2026.mista)} míst; nepřijato zůstalo <b>${sz.ms_2026.neprijato} dětí</b> (2025: ${sz.ms_2025.neprijato} dětí, ${int(sz.ms_2025.zadosti)} žádostí). Do 1. tříd ${int(sz.zs_2026.zadosti)} žádostí na ${int(sz.zs_2026.mista)} míst a <b>${sz.zs_2026.neprijato} nepřijatých dětí</b> (2025: ${sz.zs_2025.neprijato}). Tato čísla jsou po dětech; po školách systém ukazuje jen žádosti.</p>
    <p><b>Kde je tlak největší:</b> u školek na Barrandově (${nf(C['Barrandov'].ms_zadosti_na_misto, 1)} žádosti na místo, úspěšnost ${pct(C['Barrandov'].ms_uspesnost, 0)}) a v Košířích (${pct(C['Košíře'].ms_uspesnost, 0)}). U základních škol nejvíc odmítnutých žádostí měly ${worstZs.map((z) => `${esc(z.nazev)} (${pct(z.uspesnost, 0)}, ${z.neprijato} žádostí)`).join(', ')}.</p>
    <p><b>Souvislost s volbami je slabá.</b> Piráti jsou silnější v okrscích, kde je o spádovou ZŠ větší zájem (žádostí na místo vs. Piráti 2026: r = ${nf(SK.stats['zs_zadosti_na_misto~mc_2026'], 2)}). Jde ale spíš o to, kde bydlí mladé rodiny s dětmi, než o reakci na zápis. Se změnou výsledku 2022 → 2026 to nesouvisí (r = ${nf(SK.stats['zs_zadosti_na_misto~mc_delta'], 2)}). Barrandov má nejhorší situaci ve školkách i největší pirátský propad, ale z 9 čtvrtí se vztah spolehlivě určit nedá.</p>`;
  table($('#tb-zs'), [
    { k: 'nazev', label: 'Spádová ZŠ' },
    { k: 'mista', label: 'Místa', n: 1, f: (r) => r.mista }, { k: 'spadove', label: 'Děti ze spádu', n: 1, f: (r) => r.spadove || '–' },
    { k: 'zadosti', label: 'Žádosti', n: 1, f: (r) => r.zadosti }, { k: 'prijato', label: 'Přijato', n: 1, f: (r) => r.prijato },
    { k: 'neprijato', label: 'Nepřijato', n: 1, f: (r) => r.neprijato },
    { k: 'uspesnost', label: 'Úspěšnost 2026', n: 1, f: (r) => `<b>${pct(r.uspesnost, 0)}</b>` },
    { k: 'u25', label: '2025', n: 1, f: (r) => pct(r.u25, 0) },
    { k: 'okr', label: 'Okrsky', n: 1, sv: (r) => r.okrsky.length, f: (r) => (r.okrsky.length ? r.okrsky.length : '–') },
    { k: 'pir', label: 'Piráti 2026', n: 1, f: (r) => pct(r.pir) },
    { k: 'pirD', label: 'Změna', n: 1, f: (r) => (r.pirD == null ? '–' : `<span class="${sgnCls(r.pirD)}">${pp(r.pirD)}</span>`) },
  ], zsRows, { sort: 'uspesnost', desc: false });
  const msRows = [...SK.ms].sort((a, b) => a.uspesnost - b.uspesnost);
  dumbbell($('#ch-ms'), msRows.map((m) => ({ label: m.nazev.replace(/\s*\(.*\)$/, '').replace(/^ZŠ a MŠ Barrandov, Chaplinovo nám\./, 'ZŠ a MŠ Chaplinovo').slice(0, 26), a: m.uspesnost_2025, b: m.uspesnost,
    hi: m.uspesnost < 50, extra: m.ctvrt, tipx: `<br>${esc(m.ctvrt)} · místa ${m.mista}, žádosti ${m.zadosti}, nepřijaté žádosti ${m.neprijato}` })), { la: '2025', lb: '2026', max: 100, extraLabel: 'čtvrť' });
  scatter($('#ch-zs-pir'), O.filter((o) => o.zs_zadosti_na_misto != null).map((o) => ({ x: o.zs_zadosti_na_misto, y: o.mc_2026,
    tip: `<b>Okrsek ${o.okrsek} · ${esc(o.ctvrt)}</b><br>spádová ZŠ: ${esc(o.zs_skola)}<br>žádostí na místo: ${nf(o.zs_zadosti_na_misto, 2)}<br>Piráti 2026: ${pct(o.mc_2026)}` })),
  { xl: 'žádostí na místo ve spádové ZŠ', yl: 'Piráti MČ 2026 (%)', fit: true });

  /* Akce */
  const noCt = pub.filter((a) => !a.ctvrt).length, noAnc = pub.filter((a) => !a.okrsek).length;
  const g = S.skupiny.reduce((m, x) => ((m[x.skupina] = x), m), {});
  const gh = g['hodně akcí (≥3)'], g0 = g['žádná akce'];
  $('#akce-text').innerHTML = `<p>V kalendáři je ${pub.length} veřejných akcí v roce 2026 (bez interních schůzí): ${TYPES.map((t) => `${t.toLowerCase()} ${pub.filter((a) => a.typ === t).length}×`).join(', ')}. ${noCt} akcí nemá čtvrť a ${noAnc} nešlo přiřadit ke konkrétnímu okrsku (debaty a stánky bez uvedeného místa a plošné roznosy do schránek).</p>
    <p><b>Co z dat plyne:</b> akce se soustředily tam, kde byli Piráti už v roce 2022 silnější. Okrsky s 3 a více akcemi v okolí měly v roce 2022 průměrně ${pct(gh.mc_2022)}, okrsky bez akcí ${pct(g0.mc_2022)}. V roce 2026 je pořadí stejné (${pct(gh.mc_2026)} proti ${pct(g0.mc_2026)}), jenže relativní ztráta je v obou skupinách podobná (${nf((1 - gh.mc_2026 / gh.mc_2022) * 100, 0)} % proti ${nf((1 - g0.mc_2026 / g0.mc_2022) * 100, 0)} %). Okrsková data tedy nenaznačují, že by akce brzdily pokles víc tam, kde se konaly. Nedokazují ale ani opak: stánky na Andělu nebo u metra oslovují hlavně lidi, kteří tam jen projíždějí, a o volbě se podle povolebních průzkumů velká část pirátských voličů rozhoduje až v posledním týdnu.</p>`;
  // týdny
  const monday = (s) => { const d = new Date(s + 'T12:00:00'); const w = (d.getDay() + 6) % 7; d.setDate(d.getDate() - w); return d; };
  const wk = {};
  pub.forEach((a) => { const m = monday(a.datum).toISOString().slice(0, 10); (wk[m] = wk[m] || { byType: {}, total: 0 }); wk[m].byType[a.typ] = (wk[m].byType[a.typ] || 0) + 1; wk[m].total++; });
  const first = monday(pub[0].datum), last = monday(pub[pub.length - 1].datum), weeks = [];
  for (let d = new Date(first); d <= last; d.setDate(d.getDate() + 7)) {
    const k = d.toISOString().slice(0, 10), w = wk[k] || { byType: {}, total: 0 };
    weeks.push({ ...w, from: d.toLocaleDateString('cs-CZ', { day: 'numeric', month: 'numeric' }), label: d.getDate() <= 7 ? d.toLocaleDateString('cs-CZ', { month: 'short' }) : '' });
  }
  weekBars($('#ch-weeks'), weeks);
  $('#lg-weeks').innerHTML = TYPES.map((t) => `<span><span class="sw" style="background:${typeColor(t)}"></span>${t}</span>`).join('');
  scatter($('#ch-scatter-akce'), O.map((o) => ({ x: o.akci_kampan_do_700m, y: o.mc_delta, label: o.okrsek,
    tip: `<b>Okrsek ${o.okrsek} · ${esc(o.ctvrt)}</b><br>akcí do 700 m: ${o.akci_kampan_do_700m}<br>Piráti: ${pct(o.mc_2022)} → ${pct(o.mc_2026)} (${pp(o.mc_delta)})`,
    onclick: () => { select(o.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); } })),
  { xl: 'akcí v kampani do 700 m', yl: 'změna Pirátů MČ (p. b.)', fit: true, zeroY: true, zeroX: true });
  table($('#tb-skupiny'), [
    { k: 'skupina', label: 'Okrsky' }, { k: 'okrsku', label: 'Počet', n: 1, f: (r) => r.okrsku },
    { k: 'mc_2022', label: 'Piráti MČ 2022', n: 1, f: (r) => pct(r.mc_2022) }, { k: 'mc_2026', label: 'Piráti MČ 2026', n: 1, f: (r) => pct(r.mc_2026) },
    { k: 'rel', label: 'Relativní změna', n: 1, f: (r) => `<span class="down">−${nf((1 - r.mc_2026 / r.mc_2022) * 100, 0)} %</span>` },
    { k: 'ps_2025', label: 'PS 2025 (průměr)', n: 1, f: (r) => pct(r.ps_2025) }, { k: 'ucast_delta', label: 'Změna účasti', n: 1, f: (r) => pp(r.ucast_delta) },
  ], ['hodně akcí (≥3)', 'pár akcí (1–2)', 'žádná akce'].map((k) => g[k]));
  const MA = S.mc_vs_mag_akce, mz = (o) => o.mc_delta - o.mag_delta, sgn = (v) => `<span class="${sgnCls(v)}">${pp(v)}</span>`;
  const akO = O.filter((o) => o.akci_v_okrsku > 0), oo = (k) => O.find((o) => o.okrsek === k);
  const arb = oo(5004), and = oo(5011), zv = oo(5057), zv2 = oo(5056);
  const zs = O.map(mz).sort((x, y) => y - x), medZ = (zs[(zs.length - 1) >> 1] + zs[zs.length >> 1]) / 2, rank = (o) => zs.indexOf(mz(o)) + 1;
  $('#akce-mag').innerHTML = `<p><b>Čistší srovnání: MČ proti magistrátu.</b> Ve stejném okrsku volí stejní lidé ve stejný den dvakrát: do MČ a na magistrát. Pětková kampaň by se proto měla projevit hlavně v tom, o kolik méně ztratila kandidátka do MČ než magistrátní. Celopražský propad značky se tím odečte. Okrsky, kde akce přímo byly (${MA.s_akci.okrsku}), mají tento místní efekt ${pp(MA.s_akci.median)} (medián), okrsky bez akce (${MA.bez_akci.okrsku}) ${pp(MA.bez_akci.median)}; rozdíl není průkazný (permutační test p = ${nf(MA.p, 2)}) a s počtem akcí v okolí 700 m nesouvisí (r = ${nf(MA.r_kampan_700m, 2).replace('-', '−')}). Okrsky s akcemi navíc ztratily v MČ o něco víc (medián ${pp(MA.s_akci.mc_delta)} proti ${pp(MA.bez_akci.mc_delta)}), protože akce byly hlavně tam, kde byli Piráti v roce 2022 silní.</p>
    <p><b>Jednotlivá místa:</b> na Arbesově náměstí (okrsek 5004, ${arb.akci_v_okrsku} akcí včetně smíchovských SWAPů) Piráti v MČ téměř neztratili (${pct(arb.mc_2022)} → ${pct(arb.mc_2026)}), přestože na magistrátu tam stejní voliči ubrali ${pp(arb.mag_delta).replace('−', '')}; místní efekt ${pp(mz(arb))} je ${rank(arb)}. nejvyšší z ${O.length} okrsků (typická hodnota ${pp(medZ)}), okrsek je ale malý (${arb.odevzdano_2026} obálek). U Anděla (5011, ${and.akci_v_okrsku} akcí) je místní efekt jen ${pp(mz(and))}, tedy pod typickou hodnotou – stánek u metra oslovuje hlavně lidi, kteří tam jen projíždějí. U Zvonu (5057) Piráti vyrostli z ${pct(zv.mc_2022)} na ${pct(zv.mc_2026)}, ale rostli tam i na magistrátu (${pp(zv.mag_delta)}), takže místní efekt (${pp(mz(zv))}) je běžný (sousední 5056 ve stejné volební místnosti navíc v MČ spadl o ${pp(zv2.mc_delta).replace('−', '')}). Jednotlivá místa jsou tip, kde akce mohly fungovat; statisticky se od náhody odlišit nedají.</p>`;
  if (D.doplneni && D.doplneni.srovnani_mc) {
    const SMC = D.doplneni.srovnani_mc, L = SMC.mc.filter((m) => m.srovnatelne), P5 = SMC.p5, rng = (k) => `${pr(Math.max(...L.map((m) => m[k])), 0)} až ${pr(Math.min(...L.map((m) => m[k])), 0)}`;
    const lepsi = L.filter((m) => !m.p5 && m.rezidual > P5.rezidual).sort((a, b) => b.rezidual - a.rezidual);
    $('#akce-mc').innerHTML = `<p><b>Proč to neznamená, že akce nefungovaly.</b> Okrskové srovnání se ptá jen na to, jestli dopadla líp místa, kde akce byly, než místa, kde nebyly. Efekt, který zasáhne celou Prahu 5 stejně, v něm vidět není: stánek na Andělu nebo na Arbesáku oslovuje lidi z celé městské části a k tomu se přidávají sociální sítě, letáky a viditelnost kandidátů. Takový efekt zvedne všechny okrsky stejně a uvnitř Prahy 5 nezanechá žádný rozdíl. Ukázat ho může jen srovnání s jinými městskými částmi.</p>
      <p><b>Srovnání s ostatními MČ:</b> pod vlastní značkou (sami nebo s nezávislými kandidáty) šli Piráti v obou volbách v ${L.length} srovnatelných městských částech. Místní kandidátka ve všech ztratila méně než magistrátní ve stejné MČ (místní ${rng('rel_mc')}, magistrátní ${rng('rel_mag')}), jde tedy o obecný jev, ne o zvláštnost Prahy 5. Kde Piráti víc ztratili na magistrátu, ztratili víc i místně. Podle propadu na magistrátu se na Praze 5 dal čekat pokles místní kandidátky ${pr(P5.ocekavano, 0)}, skutečnost je ${pr(P5.rel_mc, 0)}, tedy o ${nf(P5.rezidual)} p. b. lépe. Praha 5 je tak na ${P5.poradi}. místě mezi ${P5.z_kolika} MČ${lepsi.length ? `; ještě víc nad očekáváním dopadly ${lepsi.map((m) => `${esc(m.nazev)} (${pp(m.rezidual)})`).join(' a ')}` : ''}. Výsledek je slučitelný s efektem kampaně na celé Praze 5, ale je v mezích běžného rozptylu mezi MČ (z = ${nf(P5.z, 2)}). S ${L.length} městskými částmi nejde kampaň oddělit od vlivu kandidátů nebo od náhody. <a href="#d-mc">Podrobné srovnání MČ</a>.</p>`;
  }
  table($('#tb-akce-okrsky'), [
    { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => `<b>${r.okrsek}</b><br><span class="muted">${esc(r.ctvrt)}</span>` },
    { k: 'akci_v_okrsku', label: 'Akcí v okrsku', n: 1, f: (r) => r.akci_v_okrsku },
    { k: 'mista', label: 'Místa', cls: 'wrap', sv: (r) => r.akci_v_okrsku, f: (r) => esc([...new Set(pub.filter((a) => a.okrsek === r.okrsek).map((a) => a.misto).filter(Boolean))].slice(0, 3).join(', ') || '–') },
    { k: 'mc', label: 'Piráti MČ 2022 → 2026', n: 1, sv: (r) => r.mc_2026, f: (r) => `${pct(r.mc_2022)} → ${pct(r.mc_2026)}` },
    { k: 'mc_delta', label: 'Změna MČ', n: 1, f: (r) => sgn(r.mc_delta) },
    { k: 'mag_delta', label: 'Změna magistrát', n: 1, f: (r) => sgn(r.mag_delta) },
    { k: 'mz', label: 'Místní efekt', n: 1, sv: mz, f: (r) => `<b>${sgn(mz(r))}</b>` },
    { k: 'odevzdano_2026', label: 'Obálek 2026', n: 1, f: (r) => int(r.odevzdano_2026) },
  ], akO, { sort: 'akci_v_okrsku', desc: true, onRow: (r) => { select(r.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); } });
  table($('#tb-akce'), [
    { k: 'datum', label: 'Datum', f: (r) => new Date(r.datum + 'T12:00:00').toLocaleDateString('cs-CZ') },
    { k: 'typ', label: 'Typ' }, { k: 'ctvrt', label: 'Čtvrť', f: (r) => esc(r.ctvrt || '–') }, { k: 'misto', label: 'Místo', f: (r) => esc(r.misto || '–') },
    { k: 'od', label: 'Čas', f: (r) => (r.od ? `${r.od}${r.do ? '–' + r.do : ''}` : '') }, { k: 'nazev', label: 'Akce', cls: 'wrap' },
  ], pub, { sort: 'datum' });

  /* Konkurence */
  $('#konk-text').innerHTML = `<p>SEN PRO PRAHU 5 (s podporou senátora Lásky a Společnosti na ochranu Prokopského údolí) získal ${pct(sen26.pct, 2)} a ${sen26.mandaty} mandátů (2022: ${pct(sen22.pct, 2)}, ${sen22.mandaty}). Piráti a SEN mají silná místa jinde: korelace jejich výsledků po okrscích je záporná (2026: r = ${nf(S['mc_2026~sen_2026'], 2)}, 2022: r = ${nf(S['mc_2022~sen_2022'], 2)}). SEN je nejsilnější na Barrandově a v Jinonicích (kolem 16 %), Piráti na Smíchově, v Radlicích a na Hřebenkách.</p>
    <p>Pirátům klesl výsledek v ${S.pir_down} okrscích a v ${S.pir_down_sen_up} z nich SEN zároveň rostl. Velikost pirátské ztráty ale s růstem SENu nesouvisí (r = ${nf(S['mc_delta~sen_delta'], 2)}). Stejně je to u Starostů (r = ${nf(S['mc_delta~stan_delta'], 2)}), kteří rostli prakticky všude. Přesun voličů tedy z okrskových dat přímo vyčíst nejde (to by chtělo povolební průzkum nebo panel). Data ale ukazují, že SEN nebral Pirátům víc tam, kde je sám silný.</p>`;
  scatter($('#ch-sen'), O.map((o) => ({ x: o.sen_2026, y: o.mc_2026, tip: `<b>Okrsek ${o.okrsek} · ${esc(o.ctvrt)}</b><br>SEN: ${pct(o.sen_2026)}<br>Piráti: ${pct(o.mc_2026)}` })),
    { xl: 'SEN PRO PRAHU 5 (% hlasů)', yl: 'Piráti (% hlasů)', fit: true, zeroX: true });
  const pts = O.flatMap((o) => [
    { x: o.sen_2026 - o.sen_2022, y: o.mc_delta, series: 'SEN', tip: `<b>Okrsek ${o.okrsek}</b><br>SEN: ${pp(o.sen_2026 - o.sen_2022)}<br>Piráti: ${pp(o.mc_delta)}` },
    { x: o.stan_2026 - o.stan_2022, y: o.mc_delta, series: 'STAN', tip: `<b>Okrsek ${o.okrsek}</b><br>STAN: ${pp(o.stan_2026 - o.stan_2022)}<br>Piráti: ${pp(o.mc_delta)}` },
  ]);
  const ser2 = [{ key: 'SEN', color: css('--s2') }, { key: 'STAN', color: css('--s1') }];
  scatter($('#ch-delta-konk'), pts, { xl: 'změna konkurenta (p. b.)', yl: 'změna Pirátů (p. b.)', series: ser2, fit: true });
  $('#lg-delta-konk').innerHTML = ser2.map((s) => `<span><span class="sw dot" style="background:${s.color}"></span>${s.key}</span>`).join('') + '<span class="muted">čára = lineární trend</span>';

  /* Psefologie */
  const PS = D.psefologie, M = PS.mandaty;
  const tile2 = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
  $('#pse-tiles').innerHTML =
    tile2('Na 4. mandát chybělo', `${int(M.chybelo_na_4_mandat_hlasu)} hlasů`, `≈ ${M.chybelo_na_4_mandat_volicu} voličů s plným hlasováním · poslední mandát: ${esc(M.posledni_mandat.replace(/ s podporou.*\(/, ' ('))}`) +
    tile2('Volatilita Praha 5 (Pedersen)', nf(PS.pedersen_p5), `bloky stran 2022 → 2026; v okrscích ${nf(PS.pedersen_okrsky.min)}–${nf(PS.pedersen_okrsky.max)}`) +
    tile2('Efektivní počet stran', `${nf(PS.enp_hlasy_2022)} → ${nf(PS.enp_hlasy_2026)}`, `podle hlasů; podle mandátů ${nf(PS.enp_mandaty_2022)} → ${nf(PS.enp_mandaty_2026)}`) +
    tile2('Prostorové shlukování změny', `I = ${nf(PS.moran['piráti_zmena'][0], 2)}`, `Moranovo I, p = ${nf(PS.moran['piráti_zmena'][1], 2)} – změna je prostorově náhodná`);
  const top = PS.ei.pirati_2022_kam.filter((r) => r.kam !== 'Piráti').slice(0, 3);
  const pir26 = PS.ei.pirati_2026_odkud.reduce((s, r) => s + r.volicu, 0), fromNV = PS.ei.pirati_2026_odkud.find((r) => r.odkud === 'Nevoliči');
  const keep = PS.ei.pirati_2022_kam.find((r) => r.kam === 'Piráti'), keepV = PS.ei.jen_volici_pirati_2022_kam.find((r) => r.kam === 'Piráti');
  $('#pse-text').innerHTML = `<p><b>Mandáty:</b> přepočet D'Hondtovou metodou (klauzule: ${esc(PS.klauzule)}) přesně odpovídá oficiálnímu výsledku${PS.dhondt_shoda ? '' : ' (POZOR: neodpovídá)'}. Pirátům chybělo na další mandát ${int(M.chybelo_na_4_mandat_hlasu)} hlasů, tedy asi ${M.chybelo_na_4_mandat_volicu} voličů, kteří by dali všechny své hlasy Pirátům. Poslední mandát připadl kandidátce ${esc(M.posledni_mandat.replace(/ s podporou[^(]*/, ' '))}. Na udržení 6 mandátů z roku 2022 by bylo potřeba ještě zhruba ${int(M.na_6_mandatu_volicu)} voličů (simulace přepočtu – Piráti by museli vytlačit tři cizí mandáty). Třetí mandát měli Piráti jistý s rezervou asi ${int(M.rezerva_3_mandatu_volicu)} voličů.</p>
    <p><b>Plošný, nebo poměrný pokles?</b> Poměrný model (každý okrsek ztratil stejný podíl, ${nf((1 - PS.swing.pomer) * 100, 0)} %) sedí lépe než plošný (všude stejně procentních bodů): chyba ${nf(PS.swing.rmse_pomerny, 2)} proti ${nf(PS.swing.rmse_plosny, 2)} p. b. Piráti ztratili nejvíc tam, kde měli nejvíc. Změna se prostorově neshlukuje (Moranovo I = ${nf(PS.moran['piráti_zmena'][0], 2)}, p = ${nf(PS.moran['piráti_zmena'][1], 2)}), zatímco SEN je silně soustředěný (I = ${nf(PS.moran.sen_2026[0], 2)}). Z 81 lokálních testů (LISA) ${PS.lisa_fdr_vyznamnych ? `zůstalo po korekci na vícenásobné testování (FDR) ${PS.lisa_fdr_vyznamnych} významných` : 'nezůstal po korekci na vícenásobné testování (FDR) žádný významný shluk'}.</p>
    <p><b>Kam odešli voliči?</b> Pirátský výsledek klesl zhruba o ${nf((1 - pir26 / PS.ei.velikost_2022['Piráti']) * 100, 0)} %, ale za tím je velká výměna voličů: podle ekologické inference z rozdílů mezi okrsky volilo Piráty znovu jen asi ${nf(keep.pct, 0)}–${nf(keepV.pct, 0)} % jejich voličů z roku 2022 a zbytek dnešního výsledku tvoří noví voliči (hlavně lidé, kteří v roce 2022 nevolili – podle modelu ${nf(fromNV.pct, 0)} % dnešních pirátských voličů). Hrubé toky tato metoda spíš nadsazuje (nerozliší výměnu voličů od čistého přesunu a toky k nevoličům a od nich nejsou spolehlivě určitelné), skutečné udržení bude nejspíš vyšší. Nejvíc odchodů míří k bloku ODS, TOP 09 a KDU (${nf(top[0].pct, 0)} %, interval ${nf(top[0].p05, 0)}–${nf(top[0].p95, 0)} %), dál k ${top.slice(1).map((r) => `${esc(r.kam)} (${nf(r.pct, 0)} %)`).join(' a ')}. Odhad pro STAN je nejistý (0–${nf(PS.ei.pirati_2022_kam.find((r) => r.kam === 'STAN').p95, 0)} %). Model vysvětluje jen ${nf(PS.ei.r2_pirati_2026 * 100, 0)} % rozdílů pirátského výsledku mezi okrsky, takže jde o orientační odhad: intervaly jsou široké a kategorie se překrývají.</p>`;
  const vMap = Object.fromEntries(PS.ei.jen_volici_pirati_2022_kam.map((r) => [r.kam, r]));
  table($('#tb-ei'), [
    { k: 'kam', label: 'Kam (2026)' },
    { k: 'pct', label: 'Odhad', n: 1, f: (r) => `<b>${nf(r.pct, 0)} %</b>` },
    { k: 'int', label: '90% interval', n: 1, f: (r) => `${nf(r.p05, 0)}–${nf(r.p95, 0)} %` },
    { k: 'volicu', label: '≈ voličů', n: 1, f: (r) => int(r.volicu) },
    { k: 'v', label: 'Jen voliči', n: 1, f: (r) => (vMap[r.kam] ? `${nf(vMap[r.kam].pct, 0)} % (${nf(vMap[r.kam].p05, 0)}–${nf(vMap[r.kam].p95, 0)})` : '–') },
  ], PS.ei.pirati_2022_kam);
  if (RZ.sankey_p5) {
    let skView = 'p5';
    // vysvětlivka pod Sankey: metoda, Piráti s intervaly, co znamená uzel nevoličů
    const skNote = (q, intro, odkdy) => {
      const rows = q.pirati_kam_shrink || q.pirati_kam;
      const nev = rows.find((r) => r.kam === 'Nevoliči');
      const lam = q.lambda_;
      return `<p>${intro} Voliči Pirátů (${odkdy}): ${rows.filter((r) => r.pct >= 1).map((r) => `${esc(r.kam === 'Nevoliči' ? 'nepřišli' : r.kam)} ${nf(r.pct, 0)} %${r.p05 != null ? ` (${nf(r.p05, 0)}–${nf(r.p95, 0)})` : ''}`).join(', ')}.</p>
        <p><b>Uzel „Nevolili (nyní)“</b> = odhad lidí, kteří ${odkdy === '2022' ? 'v roce 2022' : 've sněmovních volbách 2025'} volili a letos ne. Z okrskových součtů jde spolehlivě určit jen <i>čistý</i> pohyb – kolik lidí přibylo nebo ubylo. Skutečná výměna voličů (část lidí odešla, jiní místo nich přišli) je větší a model ji vidí jen částečně.${nev ? ` U Pirátů je odhad odchodu k nevoličům ${nf(nev.pct, 0)} % (bootstrap ${nf(nev.p05, 0)}–${nf(nev.p95, 0)} %)${(q.citlivost || []).length ? `; když model mírně „smrštíme“ k neutrálnímu výchozímu bodu, vyjde ${q.citlivost.map((c) => `${nf(c.do_nevolicu['Piráti'], 0)} % (přesnost horší o ${nf(c.cv_horsi_o, 0)} %)`).join(' a ')}. Data tedy připouštějí zhruba ${nf(Math.min(nev.pct, ...q.citlivost.map((c) => c.do_nevolicu['Piráti'])), 0)}–${nf(Math.max(nev.p95, ...q.citlivost.map((c) => c.do_nevolicu['Piráti'])), 0)} % a přesně to nerozliší` : ''}.` : ''}</p>
        <p class="small">${lam != null ? (lam > 0 ? `Metoda: Goodmanova regrese se smrštěním k neutrálnímu výchozímu bodu (síla λ = ${String(lam).replace('.', ',')} zvolená křížovou validací přes okrsky).` : 'Metoda: Goodmanova regrese. Smrštění k neutrálnímu výchozímu bodu jsme testovali křížovou validací přes okrsky; nezvolila ho (každé smrštění zhoršuje předpověď vynechaných okrsků). Nuly u toků do nevoličů proto nejsou přeučení, ale znamenají, že tyto toky data neurčují – proto citlivostní rozpětí výše.') : ''} Tloušťka pruhu = odhadovaný počet voličů; jde o odhad z agregátů okrsků, ne o data o jednotlivcích.</p>`;
    };
    const drawSk = () => {
      const DP = (D.doplneni || {}).ps25_kv26;
      if ((skView === 'ps5' || skView === 'psp') && DP) {
        const q = skView === 'ps5' ? DP.p5 : DP.praha;
        sankey($('#ch-sankey'), { cats: q.kategorie_ps, catsR: q.kategorie_kv, size: q.velikost_ps, M: q.matice_shrink || q.matice, nonvoters: $('#sk-nev').checked });
        $('#sk-note').innerHTML = skNote(q, `Sněmovní volby 2025 → zastupitelstvo Prahy 5 2026, ${int(q.okrsku)} okrsků. Účast ve sněmovních volbách byla mnohem vyšší, proto velký tok do nevoličů; odhad mezi různými typy voleb je méně spolehlivý než mezi dvěma komunálními volbami.`, 'PS 2025');
        return;
      }
      const sk = skView === 'p5' ? RZ.sankey_p5 : RZ.sankey_praha;
      sankey($('#ch-sankey'), { cats: sk.kategorie, size: sk.velikost_2022, M: sk.matice_shrink || sk.matice, nonvoters: $('#sk-nev').checked });
      $('#sk-note').innerHTML = skNote(sk, skView === 'p5' ? `Praha 5, zastupitelstvo MČ, ${sk.okrsku} okrsků.` : `Celá Praha, zastupitelstvo hl. m. Prahy, ${int(sk.okrsku)} okrsků se stabilními hranicemi.`, '2022');
    };
    $('#sk-ctrl').querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
      $('#sk-ctrl').querySelectorAll('button').forEach((x) => x.setAttribute('aria-checked', 'false'));
      b.setAttribute('aria-checked', 'true'); skView = b.dataset.v; drawSk();
    }));
    $('#sk-nev').addEventListener('change', drawSk);
    drawSk();
  }
  dumbbell($('#ch-bloky'), PS.bloky.map((b) => ({ label: b.blok, a: b.p2022, b: b.p2026, hi: b.blok === 'Piráti', lab: true })).sort((x, y) => y.b - x.b), { max: 30 });

  /* Senát */
  const sarK = D.senat.kandidati.find((k) => /Šarapatka/.test(k.jmeno));
  $('#senat-text').innerHTML = `<p>V okrscích Prahy 5 byla účast v 1. kole ${pct(D.senat.ucast_p5)}. <b>Piráti podpořili Zdeňka Šarapatku</b> (navržen hnutím „Zlu se neustupuje“), který skončil třetí s ${pct(sarK.pct)} a do 2. kola nepostoupil. Václav Láska je zároveň tváří kandidátky SEN, tedy přímého konkurenta Pirátů v MČ. V ostatních pražských obvodech podpořili Piráti v obvodu 27 koaličního kandidáta Jiřího Padevěta.</p>`;
  bars($('#ch-senat'), [...D.senat.kandidati].sort((a, b) => b.pct - a.pct).map((k) => ({ label: k.jmeno, v: k.pct, hi: k.postup, note: `${esc(k.navrh)}<br>Praha 5: ${pct(D.senat.p5_pct[k.c])}${k.postup ? '<br><b>postup do 2. kola</b>' : ''}` })), { max: 40 });
  table($('#tb-senat-praha'), [
    { k: 'obvod', label: 'Obvod', n: 1, f: (r) => r.obvod }, { k: 'jmeno', label: 'Kandidát', f: (r) => `${esc(r.jmeno)}${r.pir ? ' <b>(s Piráty)</b>' : ''}` },
    { k: 'pct', label: '1. kolo', n: 1, f: (r) => pct(r.pct, 2) }, { k: 'postup', label: '', f: (r) => (r.postup ? '2. kolo' : '') },
  ], D.senat.ostatni_praha.filter((r) => r.pct >= 5));

  /* Předpověď 2. kola */
  if (D.senat_predikce) {
    const SP = D.senat_predikce, MA = SP.model_a, MB = SP.model_b, HI = SP.historie, OV = SP.overeni, VZ = MB.vzorce;
    const t6 = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
    const OBH = SP.obhajoba, A1 = OBH.model_a1, SG = OBH.skupiny.find((g) => g.situace === 'vítěz 1. kola obhajuje'), OV1 = OBH.overeni;
    $('#senpred-tiles').innerHTML =
      t6('Šance Sáblíka (výsledná předpověď)', pct(A1.p, 0), `model A1: náskok ${pp(SP.naskok_pb)} + Láska obhajuje mandát · 90% interval ${nf(A1.p05, 0)}–${nf(A1.p95, 0)} %`) +
      t6('Bez zohlednění obhajoby', `${pct(MA.p, 0)} / ${pct(MB.p, 0)}`, `model A (jen náskok) / model B (přesuny voličů)`) +
      t6('Když vede obhájce mandátu', `${SG.druhy_vyhral} z ${SG.kol}`, `druhých kol ${HI.roky} vyhrál druhý z 1. kola (${pct(SG.pct, 0)}; bez obhájce ${pct(OBH.skupiny.find((g) => g.situace === 'nikdo neobhajuje').pct, 0)})`) +
      t6('Bod zvratu', pct(MB.potreba_z_ostatnich.median, 0), `voličů vypadlých kandidátů, kteří přijdou, by musel získat Sáblík (medián; obvykle jich přijde ${pct(VZ.ostatni_k_vitezi + VZ.ostatni_k_druhemu, 0)})`);
    $('#senpred-text').innerHTML = `<p>Václav Láska vede po 1. kole o ${int(SP.k1.laska - SP.k1.sablik)} hlasů (${pp(SP.naskok_pb)}) a obhajuje mandát (senátorem za obvod 21 je od roku 2014). Šanci Radka Sáblíka odhadujeme modely postavenými na všech ${HI.druhych_kol} druhých kolech senátních voleb ${HI.roky} (z toho ${HI.praha} v Praze). Druhý z 1. kola v nich vyhrál ${HI.druhy_vyhral}× (${pct(HI.druhy_vyhral_pct, 0)}). Obvod 21 tvoří celá Praha 5 (60 % voličů) a část Prahy 13 (40 %).</p>
      <p><b>Výsledná předpověď – model A1</b> je logistická regrese: pravděpodobnost, že vyhraje druhý z 1. kola, podle náskoku vítěze a podle toho, kdo obhajuje mandát. Vychází <b>${pct(A1.p, 0)}</b> pro Sáblíka (bootstrap, 90% interval ${nf(A1.p05, 0)}–${nf(A1.p95, 0)} %). Obhajoba přitom Láskovi nepomáhá, spíš naopak: když po 1. kole vede obhájce, druhý vyhrává častěji (${SG.druhy_vyhral} z ${SG.kol} kol, ${pct(SG.pct, 0)}), ačkoli obhájci mívají větší náskok (medián ${nf(SG.naskok_median)} p. b.). Po zohlednění náskoku má druhý z 1. kola proti vedoucímu obhájci zhruba ${nf(Math.exp(A1.beta.obhajce_vitez), 1)}× vyšší šanci (p = ${nf(A1.p_hodnota.obhajce_vitez, 2)}) – obhájce má své voliče zmobilizované už v 1. kole, vyzyvatel sjednocuje ty, kdo chtějí změnu. Bez obhajoby by modely dávaly Sáblíkovi ${pct(MA.p, 0)} (model A, jen náskok) a ${pct(MB.p, 0)} (model B, přesuny voličů).</p>
      <p><b>Model B (přesuny voličů)</b> odhaduje v každém minulém druhém kole ekologickou inferencí z okrsků, kolik voličů obou finalistů přišlo znovu, kam šli voliči vypadlých kandidátů a kolik lidí přišlo navíc. Typicky přijde znovu ${pct(VZ.vitez_znovu, 0)} voličů vítěze 1. kola a ${pct(VZ.druhy_znovu, 0)} voličů druhého; z voličů vypadlých kandidátů ${pct(VZ.ostatni_neprisli, 0)} nepřijde, ${pct(VZ.ostatni_k_vitezi, 0)} volí vítěze 1. kola a ${pct(VZ.ostatni_k_druhemu, 0)} druhého. Model B slouží hlavně k rozložení výsledku mezi okrsky (níže).</p>
      <p><b>Ověření na minulých volbách:</b> každé minulé druhé kolo jsme předpověděli bez něj samotného. Brierovo skóre (nižší = lepší): A1 ${nf(OV1.A1.brier, 3)}, A ${nf(OV1.A.brier, 3)}, B ${nf(OV1.B.brier, 3)}, prostý odhad „druhý vyhrává v ${pct(HI.druhy_vyhral_pct, 0)} případů“ ${nf(OV.zakladni.brier, 3)}. A1 je nejlepší; překvapení ale nejsou vzácná.</p>
      <p><b>Co modely nevědí:</b> doporučení vypadlých kandidátů. TOP 09, která spolu s Piráty podporovala Šarapatku (${pct(sarK.pct)}), doporučila pro 2. kolo Sáblíka; Šarapatka sám ani Piráti doporučení nevydali. Vliv doporučení se z minulých kol změřit nedá. Rozhodne hlavně to, kolik Šarapatkových voličů přijde: přichází jich typicky jen asi čtvrtina, takže i kdyby 80 % z nich volilo Sáblíka, šance by se podle modelu B zvýšila jen asi o 14 bodů. Po 2. kole sem doplníme skutečný výsledek a odhad, kam se Šarapatkovi voliči přesunuli.</p>`;
    // A: křivka modelu + skutečný podíl výher druhého po 3 p. b.
    (() => {
      const box = $('#ch-senpred-a'), W = 560, H = 320, L = 48, R = 16, T = 16, B = 44, XM = 30;
      const s = svgRoot(box, W, H), X = (v) => L + (v / XM) * (W - L - R), Y = (v) => H - B - (v / 100) * (H - T - B);
      for (let v = 0; v <= 100; v += 25) { el('line', { x1: L, x2: W - R, y1: Y(v), y2: Y(v), class: v ? 'grid' : 'axis' }, s); el('text', { x: L - 6, y: Y(v) + 4, 'text-anchor': 'end' }, s).textContent = v + ' %'; }
      for (let v = 0; v <= XM; v += 5) el('text', { x: X(v), y: H - B + 16, 'text-anchor': 'middle' }, s).textContent = v;
      el('text', { x: (L + W - R) / 2, y: H - 6, 'text-anchor': 'middle' }, s).textContent = 'náskok vítěze 1. kola (p. b.)';
      const bins = [];
      for (let a = 0; a < XM; a += 3) {
        const P = MA.body.filter((b) => b.naskok >= a && b.naskok < a + 3);
        if (P.length) bins.push({ a, n: P.length, w: P.filter((b) => b.druhy_vyhral).length, P });
      }
      el('path', { d: MA.krivka.filter((k) => k.naskok <= XM).map((k, i) => `${i ? 'L' : 'M'}${X(k.naskok)},${Y(k.p)}`).join(''), fill: 'none', stroke: css('--s1'), 'stroke-width': 2 }, s);
      bins.forEach((b) => {
        const g = el('g', {}, s);
        el('rect', { x: X(b.a), y: T, width: X(3) - X(0), height: H - T - B, fill: 'transparent' }, g);
        el('circle', { cx: X(b.a + 1.5), cy: Y((b.w / b.n) * 100), r: Math.max(4, Math.min(11, 2 + Math.sqrt(b.n) * 1.3)), fill: css('--gray-mark'), stroke: css('--surface'), 'stroke-width': 2 }, g);
        hover(g, `<b>Náskok ${b.a}–${b.a + 3} p. b.</b><br>druhý vyhrál ${b.w} z ${b.n} kol (${pct((b.w / b.n) * 100, 0)})` +
          (b.w ? '<br>' + b.P.filter((p) => p.druhy_vyhral).slice(0, 6).map((p) => esc(p.text)).join('<br>') : ''));
      });
      const g = el('g', {}, s), x0 = X(SP.naskok_pb);
      el('line', { x1: x0, x2: x0, y1: T, y2: H - B, stroke: css('--ink'), 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }, g);
      el('circle', { cx: x0, cy: Y(MA.p), r: 6, fill: css('--ink'), stroke: css('--surface'), 'stroke-width': 2 }, g);
      el('text', { x: x0 + 8, y: T + 12, class: 'lbl' }, g).textContent = `obvod 21 (náskok ${nf(SP.naskok_pb)} p. b.): ${nf(MA.p, 0)} %`;
      hover(g, `<b>Obvod 21</b><br>náskok ${pp(SP.naskok_pb)}<br>šance Sáblíka ${pct(MA.p, 0)} (90% ${nf(MA.p05, 0)}–${nf(MA.p95, 0)} %)`);
      $('#lg-senpred-a').innerHTML = `<span><span class="sw" style="background:${css('--s1')}"></span>model (logistická regrese)</span><span><span class="sw" style="background:${css('--gray-mark')}"></span>skutečný podíl výher druhého (velikost = počet kol)</span>`;
      tableToggle(box, ['náskok (p. b.)', 'kol', 'druhý vyhrál', 'podíl'], bins.map((b) => [`${b.a}–${b.a + 3}`, b.n, b.w, pct((b.w / b.n) * 100, 0)]));
    })();
    // B: histogram výsledků obvodu 21 podle vzorců minulých kol (Sáblík − Láska, p. b.)
    (() => {
      const box = $('#ch-senpred-b'), W = 560, H = 320, L = 40, R = 16, T = 16, B = 44, st = 4;
      const v = MB.simulace.map((x) => x.rozdil), lo = Math.floor(Math.min(...v) / st) * st, hi = Math.ceil(Math.max(...v) / st) * st;
      const bins = [];
      for (let a = lo; a < hi; a += st) bins.push({ a, P: MB.simulace.filter((x) => x.rozdil >= a && x.rozdil < a + st) });
      const mx = Math.max(...bins.map((b) => b.P.length));
      const s = svgRoot(box, W, H), X = (q) => L + ((q - lo) / (hi - lo)) * (W - L - R), Y = (q) => H - B - (q / mx) * (H - T - B);
      for (let q = 0; q <= mx; q += mx > 40 ? 10 : 5) { el('line', { x1: L, x2: W - R, y1: Y(q), y2: Y(q), class: q ? 'grid' : 'axis' }, s); el('text', { x: L - 6, y: Y(q) + 4, 'text-anchor': 'end' }, s).textContent = q; }
      for (let q = Math.ceil(lo / 10) * 10; q <= hi; q += 10) el('text', { x: X(q), y: H - B + 16, 'text-anchor': 'middle' }, s).textContent = q > 0 ? '+' + q : String(q).replace('-', '−');
      el('text', { x: (L + W - R) / 2, y: H - 6, 'text-anchor': 'middle' }, s).textContent = 'Sáblík − Láska ve 2. kole (p. b.)';
      const cS = css('--s1'), cL = css('--s3');
      bins.forEach((b) => {
        if (!b.P.length) return;
        const g = el('g', {}, s), x = X(b.a) + 1, w = X(b.a + st) - X(b.a) - 2, y = Y(b.P.length), h = Y(0) - y;
        el('rect', { x, y: T, width: w, height: H - T - B, fill: 'transparent' }, g);
        el('path', { d: `M${x},${Y(0)} v${-Math.max(0, h - 4)} a4,4 0 0 1 4,-4 h${w - 8} a4,4 0 0 1 4,4 v${Math.max(0, h - 4)} z`, fill: b.a >= 0 ? cS : cL }, g);
        hover(g, `<b>${b.a > 0 ? '+' : ''}${b.a} až ${b.a + st > 0 ? '+' : ''}${b.a + st} p. b.</b><br>${b.P.length} vzorců (${b.a >= 0 ? 'vyhrává Sáblík' : 'vyhrává Láska'})<br>` +
          b.P.slice(0, 5).map((p) => `${p.rok}, obvod ${p.obvod}${p.praha ? ' (Praha)' : ''}`).join('<br>'));
      });
      el('line', { x1: X(0), x2: X(0), y1: T, y2: H - B, stroke: css('--ink'), 'stroke-width': 1.5, 'stroke-dasharray': '4 3' }, s);
      $('#lg-senpred-b').innerHTML = `<span><span class="sw" style="background:${cL}"></span>vyhrává Láska</span><span><span class="sw" style="background:${cS}"></span>vyhrává Sáblík (${pct(MB.p, 0)} vzorců)</span>`;
      tableToggle(box, ['Sáblík − Láska (p. b.)', 'vzorců'], bins.filter((b) => b.P.length).map((b) => [`${b.a} až ${b.a + st}`, b.P.length]));
    })();
  }

  if (D.senat_okrsky) {
    const SO = D.senat_okrsky, OB = SO.obvod_sablik, best = SO.metody.find((m) => m.metoda === SO.metoda), p5o = SO.okrsky.filter((r) => r.p5);
    const ctv = (o) => (O.find((x) => x.okrsek === o) || {}).ctvrt || '';
    const BY = SO.bayes, TB = BY.test.bayes_empiricky.vse, TBP = BY.test.bayes_empiricky.praha, all = SO.okrsky, p13 = all.filter((r) => !r.p5);
    $('#senok-text').innerHTML = `<p><b>Předpověď po okrscích.</b> Rozložení mezi okrsky dává hierarchický bayesovský model: v každé ze 4 000 simulací se vezme celá tabulka přesunů voličů jednoho skutečného minulého druhého kola a každý okrsek se od ní náhodně odchýlí (podle toho, jak se okrsky odchylovaly v minulosti). Simulace jsou pak převážené tak, aby šance Sáblíka na celý obvod odpovídala modelu A1 (${pct(BY.p_obvod.bayes_empiricky_a1, 0)}); bez toho by vycházelo ${pct(BY.p_obvod.bayes_empiricky, 0)}. Podíl Sáblíka v obvodu: medián ${pct(OB.median, 0)}, 80% interval ${nf(OB.p10, 0)}–${nf(OB.p90, 0)} %.</p>
      <p>Metodu jsme vybrali zpětným testem na ${SO.druhych_kol} minulých druhých kolech (každé předpovězeno bez sebe sama): typická chyba předpovězeného rozdělení v okrsku (CRPS) ${nf(TB.crps, 2)} p. b., v Praze ${nf(TBP.crps, 2)}; 80% interval pokryl skutečnost v ${pct(TB.pokryti_80, 0)} okrsků (ideál 80 %). Nebayesovská kontrola (konformní intervaly) i jednodušší metody v tabulce vlevo vycházejí podobně. Podle mediánu by Sáblík vedl v ${p5o.filter((r) => r.sablik > 50).length} z ${p5o.length} okrsků Prahy 5 a v ${p13.filter((r) => r.sablik > 50).length} z ${p13.length} okrsků Prahy 13 – hlavně na Smíchově u Anděla a Arbesova náměstí a na Hřebenkách. Na mapě okrsků Prahy 5 je předpověď jako vrstva „Senát 2. kolo: předpověď“.</p>`;
    table($('#tb-senok-metody'), [
      { k: 'popis', label: 'Metoda', f: (r) => (r.b ? `<b>${esc(r.popis)}</b> (použita)` : esc(r.popis)) },
      { k: 'v', label: 'Zpětný test', n: 1, f: (r) => r.txt },
    ], [{ popis: 'Bayesovský model (empirický prior)', b: 1, v: TB.crps, txt: `CRPS ${nf(TB.crps, 2)} p. b., pokrytí ${pct(TB.pokryti_80, 0)}` },
      { popis: 'Bayes s nezávislým priorem', v: BY.test.bayes_nezavisly.vse.crps, txt: `CRPS ${nf(BY.test.bayes_nezavisly.vse.crps, 2)} p. b., pokrytí ${pct(BY.test.bayes_nezavisly.vse.pokryti_80, 0)}` },
      { popis: 'Průměrné přesuny + chyba podle velikosti okrsku', v: BY.test.stavajici.vse.crps, txt: `CRPS ${nf(BY.test.stavajici.vse.crps, 2)} p. b., pokrytí ${pct(BY.test.stavajici.vse.pokryti_80, 0)}` },
      ...SO.metody.map((m) => ({ popis: m.popis + ' (bodový odhad)', v: m.rmse, txt: `chyba ${nf(m.rmse)} p. b. při známém výsledku obvodu` }))]);
    table($('#tb-senok'), [
      { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => `<b>${r.okrsek}</b><br><span class="muted">${r.p5 ? esc(ctv(r.okrsek)) : 'Praha 13'}</span>` },
      { k: 'k1_sablik_ze_dvou', label: '1. kolo: Sáblík ze dvou', n: 1, f: (r) => pct(r.k1_sablik_ze_dvou, 0) },
      { k: 'sablik', label: 'Předpověď Sáblík', n: 1, f: (r) => `<b>${pct(r.sablik, 0)}</b><br><span class="muted">${nf(r.sablik_p10, 0)}–${nf(r.sablik_p90, 0)} %</span>` },
      { k: 'p_sablik_vyhraje', label: 'Šance, že Sáblík vyhraje okrsek', n: 1, f: (r) => `<span class="${r.p_sablik_vyhraje >= 50 ? 'up' : ''}">${pct(r.p_sablik_vyhraje, 0)}</span>` },
      { k: 'ucast', label: 'Očekávaná účast', n: 1, f: (r) => pct(r.ucast, 0) },
    ], all, { sort: 'sablik', desc: true, onRow: (r) => { if (r.p5) { select(r.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); } } });
  }

  if (RZ.senat_korelace) {
    const sk = [...RZ.senat_korelace].sort((a, b) => b.pct_p5 - a.pct_p5);
    const rc = (v) => `<span class="${v >= 0.3 ? 'up' : v <= -0.3 ? 'down' : ''}">${nf(v, 2)}</span>`;
    table($('#tb-sen-kor'), [
      { k: 'jmeno', label: 'Kandidát', f: (r) => (/Šarapatka/.test(r.jmeno) ? `<b>${esc(r.jmeno)}</b> (podpora Pirátů)` : esc(r.jmeno)) },
      { k: 'pct_p5', label: 'Praha 5', n: 1, f: (r) => pct(r.pct_p5) },
      { k: 'r_pirati_mc', label: 'r Piráti MČ', n: 1, f: (r) => rc(r.r_pirati_mc) },
      { k: 'r_pirati_mag', label: 'r Piráti mag.', n: 1, f: (r) => rc(r.r_pirati_mag) },
      { k: 'r_pirati_zmena', label: 'r změna Pirátů', n: 1, f: (r) => rc(r.r_pirati_zmena) },
      { k: 'r_sen', label: 'r SEN', n: 1, f: (r) => rc(r.r_sen) },
      { k: 'r_stan', label: 'r STAN', n: 1, f: (r) => rc(r.r_stan) },
    ], sk);
    const SD = RZ.senat_deleni;
    table($('#tb-sen-deleni'), [
      { k: 'kandidat', label: 'Voliči Pirátů v MČ → senátor', f: (r) => esc(r.kandidat) },
      { k: 'pct', label: 'Odhad', n: 1, f: (r) => `<b>${nf(r.pct, 0)} %</b>` },
      { k: 'i', label: '90% interval', n: 1, f: (r) => `${nf(r.p05, 0)}–${nf(r.p95, 0)} %` },
    ], [...SD.pirati].sort((a, b) => b.pct - a.pct));
    table($('#tb-sar-odkud'), [
      { k: 'blok', label: 'Hlasy Šarapatky podle volby v MČ', f: (r) => esc(r.blok) },
      { k: 'volicu', label: '≈ voličů', n: 1, f: (r) => int(r.volicu) },
      { k: 'pct', label: 'Podíl', n: 1, f: (r) => `${nf(r.pct, 0)} %` },
    ], RZ.sarapatka_odkud);
    $('#sen-deleni-note').textContent = `Odhad ekologickou inferencí: senátní a obecní volby proběhly ve stejný den, takže v okrsku jde o stejné voliče. Model vysvětluje ${nf(SD.r2 * 100, 0)} % rozdílů ve výsledcích kandidátů mezi okrsky (80 okrsků bez 5008, bootstrap 200×). Bloky: Piráti, PRAHA 5 SOBĚ, ODS + TOP 09 + KDU, STAN, SEN, ANO, ostatní.`;
  }

  /* Demografie (SLDB 2021) */
  if (D.census) {
    const CE = D.census, K = CE.kontrola, PS5 = CE.p5_sldb;
    const tile3 = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
    const kr = (a, b) => CE.korelace_okrsky.find((x) => x.demo === a && x.vysledek === b);
    const mk = (a, b) => CE.korelace_mc.find((x) => x.demo === a && x.vysledek === b);
    const T3 = CE.mc_tercily_vs, lo = T3[0], hi = T3[T3.length - 1];
    $('#demo-tiles').innerHTML =
      tile3('Praha 5 ve sčítání 2021', int(PS5.obyv), `obyvatel · ${pct(PS5.vs, 0)} vysokoškoláků · průměrný věk ${nf(PS5.vek)}`) +
      tile3('Děti × Piráti (okrsky)', `r = ${nf(kr('cen_0_14', 'mc_2026').r, 2)}`, `kde víc dětí, tam slabší Piráti; SEN opačně (r = ${nf(kr('cen_0_14', 'sen_2026').r, 2)})`) +
      tile3('Vzdělání × Piráti (57 MČ)', `${nf(hi.mag_2022 - lo.mag_2022)} → ${nf(hi.mag_2026 - lo.mag_2026)} p. b.`, 'náskok v nejvzdělanějších MČ proti nejméně vzdělaným, 2022 → 2026') +
      tile3('Kontrola gridu', `${nf(K.v65_odhad)} %`, `podíl 65+ z okrsků vs. ${nf(K.v65_sldb)} % oficiálně; obyvatel ${int(K.obyv_odhad)} vs. ${int(K.obyv_sldb)}`);
    $('#demo-text').innerHTML = `<p><b>Okrsky Prahy 5.</b> Piráti jsou slabší tam, kde žije víc dětí (r = ${nf(kr('cen_0_14', 'mc_2026').r, 2)}) a seniorů (r = ${nf(kr('cen_65', 'mc_2026').r, 2)}). Rodinné okrsky zároveň ztratily víc i po zohlednění výsledku z roku 2022 (regrese: děti t = ${nf(CE.regrese.zmena.koef.cen_0_14.t, 1)}, senioři t = ${nf(CE.regrese.zmena.koef.cen_65.t, 1)}, růst obyvatel t = ${nf(CE.regrese.zmena.koef.cen_rust_11_21.t, 1)}). SEN je naopak nejsilnější v rodinných okrscích (Barrandov). Šarapatka i STAN mají vyšší podíl tam, kde je víc neobydlených bytů (centrum Smíchova), SEN tam slabší. Nová výstavba 2011–2021 s výsledkem Pirátů nesouvisí.</p>
      <p><b>Celá Praha po MČ.</b> V roce 2022 byli Piráti na magistrát silní hlavně ve vzdělaných MČ (r = ${nf(mk('vs', 'mag_2022').r, 2)}), v roce 2026 je vztah slabší (r = ${nf(mk('vs', 'mag_2026').r, 2)}). V nejvzdělanější třetině MČ klesli z ${pct(hi.mag_2022)} na ${pct(hi.mag_2026)}, v nejméně vzdělané z ${pct(lo.mag_2022)} na ${pct(lo.mag_2026)}. Relativně ztratili všude podobně (${nf((1 - lo.mag_2026 / lo.mag_2022) * 100, 0)} % a ${nf((1 - hi.mag_2026 / hi.mag_2022) * 100, 0)} %), ale náskok mezi vzdělanými voliči skoro zmizel. To sedí s přesunem k STAN a PRAHA SOBĚ, které oslovují stejné voliče.</p>
      <p class="small">Metoda: 1km grid SLDB 2021 (ČSÚ, Statistický atlas) rozdělený do okrsků podle adresních bodů; vzdělání na úrovni okrsků v gridu není, proto je jen po MČ. Postup převzatý z projektu census-demografie-cz-sk; roční přepočet gridu tu nic nepřidá, protože Praha 5 má jeden koeficient růstu.</p>`;
    const vys = ['mc_2026', 'mc_delta', 'ps_2025', 'ucast_2026', 'sen_2026', 'stan_2026', 'ano_2026', 'senat_sarapatka'];
    const demos = [...new Set(CE.korelace_okrsky.map((x) => x.demo))];
    const rcell = (x) => `<span class="${x.r >= 0.3 ? 'up' : x.r <= -0.3 ? 'down' : ''}">${x.fdr ? '<b>' : ''}${nf(x.r, 2)}${x.fdr ? '</b>' : ''}</span>`;
    table($('#tb-demo-kor'), [
      { k: 'demo_label', label: 'Demografie' },
      ...vys.map((v) => ({ k: v, label: CE.korelace_okrsky.find((x) => x.vysledek === v).vysledek_label, n: 1, f: (r) => rcell(kr(r.demo, v)) })),
    ], demos.map((d) => ({ demo: d, demo_label: CE.korelace_okrsky.find((x) => x.demo === d).demo_label })));
    scatter($('#ch-demo-deti'), O.filter((o) => o.okrsek !== 5008 && o.cen_0_14 != null).map((o) => ({ x: o.cen_0_14, y: o.mc_2026, series: o.ctvrt === 'Barrandov' ? 'B' : 'O',
      tip: `<b>Okrsek ${o.okrsek} · ${esc(o.ctvrt)}</b><br>děti 0–14: ${pct(o.cen_0_14)} · 65+: ${pct(o.cen_65)}<br>Piráti 2026: ${pct(o.mc_2026)} · SEN: ${pct(o.sen_2026)}` })),
    { xl: 'podíl dětí 0–14 let (SLDB 2021, %)', yl: 'Piráti MČ 2026 (%)', series: [{ key: 'O', color: css('--s1') }, { key: 'B', color: css('--s2') }], fit: false });
    const mcPts = CE.mc.flatMap((m) => [
      { x: m.vs, y: m.mag_2022, series: '2022', tip: `<b>${esc(m.nazev)}</b><br>VŠ: ${pct(m.vs)}<br>Piráti 2022: ${pct(m.mag_2022)}` },
      { x: m.vs, y: m.mag_2026, series: '2026', tip: `<b>${esc(m.nazev)}</b><br>VŠ: ${pct(m.vs)}<br>Piráti 2026: ${pct(m.mag_2026)}` },
    ]);
    const s2 = [{ key: '2022', color: css('--gray-mark') }, { key: '2026', color: css('--s1') }];
    scatter($('#ch-demo-vs'), mcPts, { xl: 'vysokoškoláci 25+ (%)', yl: 'Piráti na magistrát (%)', series: s2, fit: true, zeroY: true });
    $('#lg-demo-vs').innerHTML = '<span><span class="sw dot" style="background:' + css('--gray-mark') + '"></span>2022</span><span><span class="sw dot" style="background:' + css('--s1') + '"></span>2026</span><span class="muted">čára = lineární trend</span>';
    table($('#tb-demo-terc'), [
      { k: 'skupina', label: 'Třetina MČ' }, { k: 'vs', label: 'VŠ', n: 1, f: (r) => pct(r.vs) },
      { k: 'mag_2022', label: 'Piráti 2022', n: 1, f: (r) => pct(r.mag_2022) }, { k: 'mag_2026', label: 'Piráti 2026', n: 1, f: (r) => `<b>${pct(r.mag_2026)}</b>` },
      { k: 'rel', label: 'Relativní změna', n: 1, f: (r) => `<span class="down">−${nf((1 - r.mag_2026 / r.mag_2022) * 100, 0)} %</span>` },
    ], T3);
    table($('#tb-demo-mckor'), [
      { k: 'demo_label', label: 'MČ: ukazatel' },
      ...['mag_2022', 'mag_2026', 'mag_zmena', 'ps25'].map((v) => ({ k: v, label: CE.korelace_mc.find((x) => x.vysledek === v).vysledek_label, n: 1,
        f: (r) => { const x = mk(r.demo, v); return `<span class="${x.p < 0.01 ? (x.r > 0 ? 'up' : 'down') : 'muted'}">${nf(x.r, 2)}</span>`; } })),
    ], [...new Set(CE.korelace_mc.map((x) => x.demo))].map((d) => ({ demo: d, demo_label: CE.korelace_mc.find((x) => x.demo === d).demo_label })));
  }

  /* Kontrola dat */
  if (D.forenzni) {
    const F = D.forenzni, RP = F.reprodukce, PM = F.p5_marze;
    const tile4 = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
    const cnt = (j) => F.nalezy.filter((n) => n.jistota === j).length;
    $('#kon-tiles').innerHTML =
      tile4('Přepočet mandátů', `${RP.shoda} / ${RP.zastupitelstev}`, 'zastupitelstev Prahy (57 MČ + magistrát) sedí na oficiální výsledek') +
      tile4('Rozhodující marže Prahy 5', `${int(PM.hlasu)} hlasů`, `≈ ${nf(PM.volicu)} plných voličů · ${esc(PM.listina.replace(/ s podporou.*/, ''))} ${esc(PM.zmena)}`) +
      tile4('Preferenční pravidlo', F.preference_shoda['10'] && !F.preference_shoda['5'] ? '10 %' : '?', '10% hranice sedí na všechny kandidátky, 5% ne') +
      tile4('Nálezy v okrscích P5', String(F.nalezy.length), `${cnt('vysoká')} vysoká jistota · ${cnt('střední')} střední · ${cnt('informativní')} informativní`);
    $('#kon-text').innerHTML = `<p>Nezávisle jsme přepočítali mandáty podle zákona (5% klauzule s přepočtem pro neúplné kandidátky, D'Hondt, 10% preferenční pravidlo) a prošli okrsky Prahy 5 testy, které používá audit <a href="https://volebnianalyza.suchan.cz/kv/praha/index.html">volebnianalyza.suchan.cz</a>. Výsledky se shodují: rozhodující marže zastupitelstva Prahy 5 vychází ${int(PM.hlasu)} hlasů (audit: ${PM.suchan}) a našli jsme i tytéž okrsky s chybami (nulové neplatné lístky 5004, 5019, 5067; překlep 5036; chybějící balík lístků STAN v 5019; rozdíl obálek 5081). <b>Žádný nález nemění mandáty</b> – ani v zastupitelstvu Prahy 5, ani na magistrátu (chybějící hlasy STAN v okrsku 5019 jsou řádově 2 000, na změnu mandátu by bylo potřeba přes 44 000). Chyby se týkají hlavně preferenčních hlasů jednotlivých kandidátů.</p>`;
    {
      const nul = F.nalezy.filter((n) => n.typ === 'Nulový počet hlasů kandidátky'), vy = F.nalezy.filter((n) => n.typ === 'Nízké využití hlasů na lístku');
      $('#kon-text').insertAdjacentHTML('beforeend', `<p><b>Testy podle analýzy <a href="https://www.mahdalova-skop.cz/clanek/volby-cr-2026-10-12-anomalie-ve-vysledcich" target="_blank" rel="noopener">Mahdalové a Škopa</a>:</b> doplnili jsme jejich test nulových hlasů kandidátky (strana má v okrsku 0 hlasů, ačkoli by podle Prahy 5 čekala aspoň 100) a test využití hlasů (okrsek, kde voliči využili o 12 a víc bodů méně hlasů než medián). ` +
        (nul.length ? `Nulové hlasy: ${nul.map((n) => `${n.okrsek} ${esc(n.subjekt.replace(/ s podp.*/, ''))} (${esc(n.zastupitelstvo)})`).join(', ')}. ` : 'Nulové hlasy: nic. ') +
        `Jejich jediný nález na Praze 5 – SPD s nulou v okrsku 5004 – vidíme na obou lístcích, do MČ i na magistrát, takže jde spíš o skutečný výsledek malého okrsku než o chybu. ` +
        (vy.length ? `Nízké využití hlasů: ${vy.map((n) => `${n.okrsek} (${esc(n.zastupitelstvo)}, ${esc(n.subjekt)})`).join(', ')} – potvrzuje náš nález chybějícího balíku lístků v tomtéž okrsku. ` : 'Nízké využití hlasů: nic. ') +
        `Na lístku do MČ Prahy 5 žádný okrsek nevybočuje. Tyto nálezy se do pořadí „kde hledat hlasy na 4. mandát“ nezapočítávají podruhé.</p>`);
    }
    const dots = { 'vysoká': '●●●', 'střední': '●●', 'informativní': '●' };
    table($('#tb-kon-nalezy'), [
      { k: 'jistota', label: 'Jistota', f: (r) => `<span title="${esc(r.jistota)}">${dots[r.jistota] || ''}</span>` },
      { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => `${r.okrsek}<br><span class="muted">${esc(r.ctvrt)}</span>` },
      { k: 'zastupitelstvo', label: 'Hlasování' }, { k: 'typ', label: 'Nález', cls: 'wrap' }, { k: 'subjekt', label: 'Subjekt', cls: 'wrap' },
      { k: 'detail', label: 'Detail', cls: 'wrap', f: (r) => `${esc(r.detail)}<br><span class="muted">${esc(r.vliv)}</span>` },
      { k: 'url', label: 'Ověřit', f: (r) => `<a href="${r.url}" target="_blank" rel="noopener">volby.gov.cz</a><br><a href="${r.json}" target="_blank" rel="noopener">data</a>` },
    ], F.nalezy);
    table($('#tb-kon-marze'), [
      { k: 'nazev', label: 'MČ' }, { k: 'listina', label: 'Kandidátka', cls: 'wrap' }, { k: 'mandaty', label: 'Mandáty', n: 1, f: (r) => `${r.mandaty} z ${r.mandatu_celkem}` },
      { k: 'chybelo_hlasu', label: 'Chybělo na další', n: 1, sv: (r) => r.chybelo_volicu, f: (r) => `${int(r.chybelo_hlasu)}<br><span class="muted">${nf(r.chybelo_volicu)} plných voličů</span>` },
      { k: 'rezerva_hlasu', label: 'Rezerva', n: 1, sv: (r) => r.rezerva_volicu, f: (r) => `${int(r.rezerva_hlasu)}<br><span class="muted">${nf(r.rezerva_volicu)} plných voličů</span>` },
    ], F.marze_pirati, { sort: 'chybelo_hlasu', desc: false, rowClass: (r) => (r.kod === 500143 ? 'hl' : '') });
    table($('#tb-kon-benford'), [
      { k: 'z', label: 'Hlasování' }, { k: 'n', label: 'Počet hodnot', n: 1, f: (r) => int(r.n) }, { k: 'chi2', label: 'χ²', n: 1, f: (r) => nf(r.chi2, 1) }, { k: 'p', label: 'p', n: 1, f: (r) => nf(r.p, 3) },
    ], Object.entries(F.benford).map(([z, v]) => ({ z, ...v })));
    $('#kon-benford-note').textContent = 'Benfordův test 2. číslice je jen hrubý ukazatel. V MČ (41 hlasů na voliče) data Benfordovu rozdělení odpovídají. Na magistrátu (65 hlasů na voliče) se od něj odchylují, to je ale u vícehlasých lístků očekávané: hlasy stran jsou přibližně násobky počtu lístků, a druhá číslice proto Benfordovo rozdělení mít nemusí. Nejde o známku manipulace; audit suchan.cz proto používá i další testy (Klimek, Kobak, Beber–Scacco), všechny v normě.';
  }

  /* Kuriozity */
  if (D.kuriozity) {
    const rn = (v) => nf(v, 2).replace('-', '−'), K = D.kuriozity, PA = K.parita, TI = K.titul, CA = K.cas, pv = K.povolani;
    const pir = pv.find((r) => r.strana === 'Piráti'), ano = pv.find((r) => r.strana === 'ANO');
    $('#kur-text').innerHTML = `<p>Všechna čísla v této sekci jsou spočítaná správně z dat ČSÚ. Jen z nich neplyne skoro nic – nebo něco úplně jiného, než napovídá titulek. Je to taky ukázka toho, proč korelace (dvě věci jdou spolu) neznamená příčinu (jedna způsobuje druhou), a proč se z výsledků okrsků nedá usuzovat na jednotlivé voliče (<a href="#metodika">ekologická chyba</a>). Pod každým grafem je vysvětlení, co se za ním skutečně skrývá.</p>`;
    // 1) IT × důchodci
    (() => {
      const box = $('#ch-kur-povolani'), W = 560, rowH = 30, L = 100, R = 60, T = 6, H = T + pv.length * rowH + 22, mx = Math.max(...pv.flatMap((r) => [r.it, r.duchodci]));
      const s = svgRoot(box, W, H), X = (v) => L + (v / mx) * (W - L - R), c1 = css('--s1'), c2 = css('--s4');
      for (let v = 0; v <= mx; v += 5) { el('line', { x1: X(v), x2: X(v), y1: T, y2: H - 18, class: 'grid' }, s); el('text', { x: X(v), y: H - 4, 'text-anchor': 'middle' }, s).textContent = v + ' %'; }
      pv.forEach((r, i) => {
        const y = T + i * rowH, g = el('g', {}, s);
        el('rect', { x: 0, y, width: W, height: rowH, fill: 'transparent' }, g);
        el('text', { x: L - 8, y: y + rowH / 2 + 4, 'text-anchor': 'end', class: r.strana === 'Piráti' ? 'lbl' : '' }, g).textContent = r.strana;
        [[r.it, c1, 4], [r.duchodci, c2, 15]].forEach(([v, c, dy]) => {
          el('rect', { x: L, y: y + dy, width: Math.max(2, X(v) - L), height: 10, rx: 3, fill: c }, g);
          el('text', { x: X(v) + 5, y: y + dy + 9 }, g).textContent = nf(v) + ' %';
        });
        hover(g, `<b>${esc(r.strana)}</b> – ${int(r.kandidatu)} kandidátů do MČ<br>IT / programátoři: ${pct(r.it)}<br>důchodci: ${pct(r.duchodci)}<br>medián věku: ${nf(r.vek, 0)} let`);
      });
      $('#lg-kur-povolani').innerHTML = `<span><span class="sw" style="background:${c1}"></span>IT, programátoři, vývojáři, data</span><span><span class="sw" style="background:${c2}"></span>důchodci</span>`;
      tableToggle(box, ['strana', 'kandidátů', 'IT', 'důchodci', 'medián věku'], pv.map((r) => [r.strana, r.kandidatu, pct(r.it), pct(r.duchodci), nf(r.vek, 0)]));
      $('#kur-povolani-note').innerHTML = `Na pirátské kandidátce je ${nf(pir.it / pir.duchodci, 0)}× víc lidí z IT než důchodců, u ANO je to ${nf(ano.duchodci / ano.it, 0)}× naopak. Tady je rozdíl skutečný – jen o voličích neříká nic: kandidátky skládají strany, ne voliči. Podle povolání, které kandidáti sami uvedli (${int(pv.reduce((a, r) => a + r.kandidatu, 0))} kandidátů, „IT“ = programátor, vývojář, software, data, digitalizace).`;
    })();
    // 2) sudé × liché
    bars($('#ch-kur-parita'), [{ label: `sudé okrsky (${PA.sudych})`, v: PA.sude, hi: true }, { label: `liché okrsky (${PA.lichych})`, v: PA.liche }], { max: 10, d: 2 });
    $('#kur-parita-note').innerHTML = `V sudých okrscích mají Piráti o ${nf(PA.rozdil, 2)} p. b. víc. Kdyby čísla okrsků přidělil někdo náhodně, vyšel by stejně velký nebo větší rozdíl v ${nf(PA.p * 100, 0)} % případů (permutační test) – je to čistá náhoda. Takhle vypadá „zjištění“, které by v dostatečně velké tabulce našel každý.`;
    // 3) typ místnosti
    bars($('#ch-kur-mistnost'), K.mistnost.map((r) => ({ label: `${r.typ.replace(/ \(.*\)$/, '')} (${r.okrsku})`, v: r.pirati, hi: r.zmena >= 0, txt: `${nf(r.pirati)} % (${pp(r.zmena)})`, note: `změna proti 2022: ${pp(r.zmena)} · ${r.okrsku} okrsků` })), { max: 15, noTable: false });
    $('#kur-mistnost-note').innerHTML = `V okrscích, kde se volí na gymnáziu nebo v ZUŠ, Piráti neztratili; kde se volí v mateřské škole, ztratili ${nf(-K.mistnost.find((r) => r.typ === 'mateřská škola').zmena)} procentního bodu. Gymnázia a ZUŠ jsou ale jen 2–3 okrsky (v ZUŠ na Popelce volí i okrsek U Zvonu, kde Piráti vyrostli) – a místnost se vybírá podle toho, co v okrsku stojí, ne naopak. Volit chodí lidé z ulic okolo, ne žáci.`;
    // 4) čas sečtení
    scatter($('#ch-kur-cas'), CA.body.map((b) => ({ x: b.hodin, y: b.pirati, tip: `<b>Okrsek ${b.okrsek} · ${esc(b.ctvrt)}</b><br>sečteno ${nf(b.hodin, 1)} h po uzavření místností<br>Piráti ${pct(b.pirati)} · ${int(b.obalky)} obálek` })),
      { xl: 'hodin od uzavření volebních místností (10. 10. 14:00)', yl: 'Piráti MČ 2026 (%)', fit: true });
    $('#kur-cas-note').innerHTML = `Čím dřív byl okrsek sečtený, tím víc tam měli Piráti (r = ${rn(CA.r_pirati)}). Skutečný důvod: velké okrsky se sčítají déle (r = ${rn(CA.r_obalky)} mezi časem a počtem obálek) a Piráti mají ve velkých okrscích méně (r = ${rn(CA.r_pirati_obalky)}). Komise nikomu nenadržuje – jen přepočítat několik set obálek trvá déle než sto.`;
    // 5) titul
    bars($('#ch-kur-titul'), [{ label: 's titulem před jménem', v: TI.s_titulem * 100, hi: true, txt: nf(TI.s_titulem * 100, 1) }, { label: 'bez titulu', v: TI.bez_titulu * 100, txt: nf(TI.bez_titulu * 100, 1) }], { max: 110, unit: '' });
    $('#kur-titul-note').innerHTML = `Kandidáti s titulem dostali o ${nf(TI.rozdil_pct, 1)} % víc preferenčních hlasů než kandidáti bez titulu, vždy měřeno proti průměru vlastní kandidátky (titul má ${int(TI.s_titulem_n)} z ${int(TI.kandidatu)} kandidátů). Část efektu jde na vrub toho, že lidé s titulem bývají na kandidátce výš (pořadí s hlasy souvisí: r = ${rn(TI.r_poradi)}); po zohlednění pořadí zbývá rozdíl asi ${nf(TI.rozdil_po_poradi * 100, 1)} bodu na stupnici, kde 100 = průměr kandidátky. Délka příjmení naopak nehraje žádnou roli (r = ${rn(TI.r_delka)}) – pro všechny Nováky a Procházky je to dobrá zpráva.`;
  }

  /* Kde hledat hlasy na 4. mandát */
  if (D.hledani) {
    const HL = D.hledani, HR = HL.hrana, nm = (s) => esc(String(s).replace(/ s podporou.*/, ''));
    const t5 = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
    const lastT = HL.posledni_cas ? new Date(HL.posledni_cas) : null;
    $('#hl-tiles').innerHTML =
      t5('Pirátům chybí na 4. mandát', `${int(HR.chybi_hlasu)} hlasů`, `≈ ${Math.ceil(HR.chybi_plnych_volicu)} voličů, kteří by dali Pirátům všech 41 hlasů`) +
      t5('Pořadí podílů kolem 41. mandátu', `${int(HR.posledni.podil)}`, `${nm(HR.posledni.listina)} (${HR.posledni.mandat}. mandát) · pak ${HR.dalsi_v_poradi.slice(0, 2).map((d) => `${nm(d.listina)} ${int(d.podil)}`).join(', ')}`) +
      t5('Kdyby SEN přišel o hlasy', `min. ${int(HR.minimum_pri_ztrate_sen)}`, `hlasů Pirátům navíc – mandát by nejdřív připadl ${nm(HR.dalsi_v_poradi[0].listina)}`) +
      t5('Poslední sečtený okrsek', `${HL.posledni_okrsek}`, lastT ? `zpracován ${lastT.getDate()}. ${lastT.getMonth() + 1}. v ${lastT.toTimeString().slice(0, 5)}` : '');
    const top = HL.okrsky.filter((r) => !r.zvlastni).slice(0, 6);
    $('#hl-text').innerHTML = `<p>Na 4. mandát chybělo Pirátům ${int(HR.chybi_hlasu)} hlasů. Poslední mandát drží ${nm(HR.posledni.listina)} (${HR.posledni.mandat}.), těsně za ním je ${nm(HR.dalsi_v_poradi[0].listina)} (${HR.dalsi_v_poradi[0].mandat}. podíl) a teprve potom Piráti. Pokud by se našly hlasy navíc pro Piráty, stačí ${int(HR.chybi_hlasu)}; pokud by SEN o hlasy přišel, mandát by nejdřív připadl ${nm(HR.dalsi_v_poradi[0].listina)} a Piráti by stejně potřebovali aspoň ${int(HR.minimum_pri_ztrate_sen)}. Oprava chyb, které už jsme v protokolech našli (překlepy a neúplně opsané řádky u jiných kandidátek), by Pirátům potřebu zvýšila na ${int(HR.po_oprave_chyb)}.</p>
      <p><b>Kde je největší šance najít chybu:</b> nejsilnějším signálem je rozdíl mezi pirátským výsledkem v MČ a na magistrátu ve stejném okrsku – volili stejní lidé ve stejný den, takže výrazně nižší výsledek v MČ může znamenat chybu při sčítání (například chybějící balík lístků). Dalšími signály jsou neplatné lístky nad průměr, pozdní zpracování a chyby nalezené kontrolou dat. Nejvýš vychází ${top.map((r) => `<b>${r.okrsek}</b> ${esc(r.ctvrt)}`).join(', ')}.</p>
      <p><b>Co to není:</b> rozdíly mezi MČ a magistrátem jsou z velké části běžné – část lidí volí Piráty jen na magistrát. Seznam je pořadí, kde se vyplatí hledat, ne důkaz chyby nebo pochybení komise. Výsledek voleb může změnit jen soud na návrh podaný do 10 dnů od vyhlášení výsledků; postup je dobré ověřit s právníkem. Zápisy okrskových komisí uchovává úřad MČ.</p>`;
    table($('#tb-hledani'), [
      { k: 'poradi', label: '#', n: 1, f: (r) => r.poradi },
      { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => `<b>${r.okrsek}</b><br><span class="muted">${esc(r.ctvrt)}</span>` },
      { k: 'cas', label: 'Zpracováno', f: (r) => (r.cas ? new Date(r.cas).toLocaleString('cs-CZ', { day: 'numeric', month: 'numeric', hour: '2-digit', minute: '2-digit' }) : '–') },
      { k: 'pir_mc', label: 'Piráti MČ / mag.', n: 1, f: (r) => `${pct(r.pir_mc)} / ${pct(r.pir_mag)}` },
      { k: 'deficit', label: 'Chybí proti očekávání', n: 1, f: (r) => `<span class="${r.deficit > 150 ? 'down' : ''}">${int(r.deficit)}</span><br><span class="muted">${int(r.skutecnost)} z ${int(r.ocekavano)}</span>` },
      { k: 'neplatne_mc', label: 'Neplatné MČ / mag.', n: 1, f: (r) => `${r.neplatne_mc} / ${r.neplatne_mag}` },
      { k: 'duvody', label: 'Proč hledat', cls: 'wrap', sv: (r) => r.duvody.length, f: (r) => (r.duvody.length ? r.duvody.map(esc).join('<br>') : '<span class="muted">nic nápadného</span>') },
      { k: 'skore', label: 'Skóre', n: 1, f: (r) => int(r.skore) },
      { k: 'url', label: 'Protokol', f: (r) => `<a href="https://volby.gov.cz/app/kv2026/cs/20261009/results/!__0_1100_1100_500143___${r.okrsek}" target="_blank" rel="noopener">volby.gov.cz</a>` },
    ], HL.okrsky, { sort: 'poradi', desc: false, onRow: (r) => { select(r.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); }, rowClass: (r) => (r.poradi <= 6 ? 'hl' : '') });
  }

  /* Doplňující analýzy */
  if (D.doplneni) {
    const DP = D.doplneni, DV = DP.demografie_2026;
    const p21 = DV.p5_2021, p26 = DV.p5_2026, kor = (a, b) => DV.korelace_mc.find((x) => x.demo === a && x.vysledek === b).r;
    $('#d-vek-text').innerHTML = `<p>Věk a pohlaví se po městských částech aktualizují každý rok (ČSÚ, sada OBY02E), vzdělání jen při sčítání. Praha 5 měla k 31. 12. 2021 ${int(p21.obyv)} obyvatel a k 1. 1. 2026 ${int(p26.obyv)} (${pr((p26.obyv / p21.obyv - 1) * 100)}). Podíl dětí ${pct(p21.v0_14)} → ${pct(p26.v0_14)}, seniorů ${pct(p21.v65)} → ${pct(p26.v65)}, žen ${pct(p21.zeny)} → ${pct(p26.zeny)}. Věk po okrscích pro rok 2026 je dopočítaný tvou metodou koeficientu po věkových skupinách (grid 2021 × změna skupiny v Praze 5; děti ×${nf(DV.koeficienty_p5.VEK014, 3)}, 15–64 ×${nf(DV.koeficienty_p5.VEK1564, 3)}, 65+ ×${nf(DV.koeficienty_p5.VEK65AV, 3)}), v mapě okrsků jako vrstvy „Děti 0–14 (2026)“ a „Senioři 65+ (2026)“. Pořadí okrsků se tím nemění, protože celá Praha 5 má jeden koeficient na skupinu.</p>
      <p>Po MČ: Piráti na magistrát 2026 × podíl dětí r = ${nf(kor('v0_14_2026', 'mag_2026'), 2)}, × senioři r = ${nf(kor('v65_2026', 'mag_2026'), 2)}, × podíl žen r = ${nf(kor('zeny_2026', 'mag_2026'), 2)}, × vysokoškoláci (2021) r = ${nf(kor('vs_2021', 'mag_2026'), 2)}, × růst obyvatel 2022–26 r = ${nf(kor('rust', 'mag_2026'), 2)}.</p>`;
    table($('#tb-d-vek'), [
      { k: 'nazev', label: 'MČ' }, { k: 'obyv_2026', label: 'Obyvatelé 2026', n: 1, f: (r) => int(r.obyv_2026) }, { k: 'rust', label: 'Růst od 2022', n: 1, f: (r) => pr(r.rust) },
      { k: 'v0_14_2026', label: 'Děti 0–14', n: 1, f: (r) => pct(r.v0_14_2026) }, { k: 'v65_2026', label: '65+', n: 1, f: (r) => pct(r.v65_2026) },
      { k: 'zeny_2026', label: 'Ženy', n: 1, f: (r) => pct(r.zeny_2026) }, { k: 'vs_2021', label: 'VŠ (2021)', n: 1, f: (r) => pct(r.vs_2021) },
      { k: 'mag_2026', label: 'Piráti mag. 2026', n: 1, f: (r) => pct(r.mag_2026) },
    ], DV.mc, { sort: 'mag_2026', rowClass: (r) => (r.kod === 500143 ? 'hl' : '') });

    const SP = DP.deleni_mc_mag, keepMc = SP.pirati_mag_kam.find((r) => r.kam === 'Piráti');
    $('#d-split-text').innerHTML = `<p>Na Praze 5 měli Piráti v MČ v průměru o ${nf(Math.abs(SP.rozdil.prumer))} p. b. ${SP.rozdil.prumer < 0 ? 'méně' : 'víc'} než na magistrát. Podle odhadu z okrsků volilo pirátskou kandidátku v MČ asi ${nf(keepMc.pct, 0)} % voličů pirátské magistrátní kandidátky (interval ${nf(keepMc.p05, 0)}–${nf(keepMc.p95, 0)} %); zbytek dal hlasy v MČ hlavně ${SP.pirati_mag_kam.filter((r) => r.kam !== 'Piráti').slice(0, 2).map((r) => `${esc(r.kam)} (${nf(r.pct, 0)} %)`).join(' a ')}. „Místní tým“ je silnější než „značka“ hlavně tam, kde je rozdíl kladný: ${SP.rozdil.nejvic_mc.slice(0, 3).map((r) => `${r.okrsek} ${esc(r.ctvrt)} (${pp(r.rozdil)})`).join(', ')}. V mapě okrsků vrstva „Piráti MČ − magistrát“.</p>`;
    table($('#tb-d-split'), [
      { k: 'kam', label: 'Volba v MČ' }, { k: 'pct', label: 'Odhad', n: 1, f: (r) => `<b>${nf(r.pct, 0)} %</b>` },
      { k: 'i', label: '90% interval', n: 1, f: (r) => `${nf(r.p05, 0)}–${nf(r.p95, 0)} %` },
    ], SP.pirati_mag_kam);
    const pomer = D.ctvrti.map((c) => ({ label: c.ctvrt, a: c.mc_2022 / c.mag_2022 * 100, b: c.mc_2026 / c.mag_2026 * 100, hi: true,
      tipx: `<br>MČ ${pct(c.mc_2022)} → ${pct(c.mc_2026)}<br>magistrát ${pct(c.mag_2022)} → ${pct(c.mag_2026)}` })).sort((x, y) => y.b - x.b);
    pomer.push({ label: 'Praha 5 celkem', a: P.mc_2022 / P.mag_2022 * 100, b: P.mc_2026 / P.mag_2026 * 100, hi: true, tipx: `<br>MČ ${pct(P.mc_2022)} → ${pct(P.mc_2026)}<br>magistrát ${pct(P.mag_2022)} → ${pct(P.mag_2026)}` });
    dumbbell($('#ch-d-split'), pomer, { la: '2022', lb: '2026', max: 100 });
    $('#ch-d-split').insertAdjacentHTML('beforeend', `<p class="small">100 % = Piráti mají v MČ stejný podíl jako na magistrátu. V roce 2022 měla místní kandidátka ${nf(P.mc_2022 / P.mag_2022 * 100, 0)} % magistrátního výsledku, letos ${nf(P.mc_2026 / P.mag_2026 * 100, 0)} %. Zlepšení je hlavně tím, že magistrátní kandidátka propadla víc (−${nf((1 - P.mag_2026 / P.mag_2022) * 100, 0)} %) než místní (−${nf((1 - P.mc_2026 / P.mc_2022) * 100, 0)} %). Část rozdílu dělají místní konkurenti, kteří na magistrátu nejsou nebo jsou slabí (SEN PRO PRAHU 5, PRAHA 5 SOBĚ).</p>`);

    const CTS2 = Object.keys(DP.pref_magistrat[0].index_ctvrti);
    table($('#tb-d-pref'), [
      { k: 'poradi', label: '#', n: 1, f: (r) => r.poradi }, { k: 'jmeno', label: 'Kandidát' }, { k: 'hlasy_p5', label: 'Hlasy P5', n: 1, f: (r) => int(r.hlasy_p5) },
      ...CTS2.map((c) => ({ k: 'i_' + c, label: c, n: 1, sv: (r) => r.index_ctvrti[c], f: (r) => { const v = r.index_ctvrti[c]; return v >= 105 ? `<b class="up">${v}</b>` : v <= 95 ? `<span class="down">${v}</span>` : v; } })),
      { k: 'max_okrsek', label: 'Nejsilnější okrsek', n: 1, f: (r) => `${r.max_okrsek} (${nf(r.max_index, 0)})` },
    ], DP.pref_magistrat, { sort: 'poradi', desc: false });

    const UC = DP.ucast, nv5 = UC.nevolici_2022_p5, nvp = UC.nevolici_2022_praha;
    $('#d-ucast-text').innerHTML = `<p>Účast stoupla na Praze 5 z ${pct(UC.p5_2022)} na ${pct(UC.p5_2026)}, v Praze z ${pct(UC.praha_2022)} na ${pct(UC.praha_2026)}. <b>S Piráty změna účasti nesouvisí:</b> v okrscích, kde účast víc stoupla, se pirátský výsledek neměnil jinak než jinde (r = ${nf(UC.korelace_zmena_ucasti['Piráti'], 2)}); mírně z vyšší účasti těžilo ANO (r = ${nf(UC.korelace_zmena_ucasti['ANO'], 2)}), STAN a SEN spíš naopak.</p>
      <p><b>Kdo nepřišel:</b> ze sněmovních voličů Pirátů 2025 letos na Praze 5 podle odhadu nevolilo asi ${nf(UC.pirati_ps25_nevolili_p5.pct, 0)} % (interval ${nf(UC.pirati_ps25_nevolili_p5.p05, 0)}–${nf(UC.pirati_ps25_nevolili_p5.p95, 0)} %). Účast byla v komunálních volbách o čtvrtinu nižší než ve sněmovních, takže demobilizace je velká u všech; u Pirátů je ale hlavním kanálem ztráty proti loňsku – víc než přeběhy.</p>
      <p class="small">Tabulka vlevo ukazuje odhad, ke komu šli lidé, kteří v roce 2022 nevolili a letos přišli. Toky z a do nevoličů jsou v ekologické inferenci nejméně spolehlivé (velká kategorie, malé změny) – berte je jako orientační. Pražský model PS 2025 → magistrát 2026 jsme z Sankey diagramu vyřadili: vycházel nevěrohodně (Pirátům by zůstala 3 % sněmovních voličů při 9,4 % na magistrátu), což je typický projev ekologické chyby.</p>`;
    table($('#tb-d-nevol'), [
      { k: 'kam', label: 'Kam', f: (r) => esc(r.kam) }, { k: 'p5', label: 'Praha 5', n: 1, f: (r) => `${nf(r.pct, 0)} %` },
      { k: 'praha', label: 'Praha', n: 1, f: (r) => { const x = nvp.kam.find((y) => y.kam === r.kam || (r.kam === 'ODS, TOP 09, KDU' && y.kam === 'SPOLU')); return x ? `${nf(x.pct, 0)} %` : '–'; } },
    ], nv5.kam);
    const DM = (DP.ps25_kv26 || {}).doma;
    if (DM) {
      const g = (s) => DM.find((r) => r.strana === s) || {};
      const ms = (s) => g(s).ms_praha;
      $('#d-doma-text').innerHTML = `<p>Komunální volby mají mnohem nižší účast než sněmovní (Praha 5 letos ${pct(UC.p5_2026)}), takže velká část voličů roku 2025 letos prostě nepřišla. Odhad z okrsků ukazuje, že doma zůstali hlavně voliči Pirátů (Praha 5 ${pct(g('Piráti').p5.pct, 0)}, Praha ${pct(g('Piráti').praha.pct, 0)}), ANO (${pct(g('ANO').p5.pct, 0)} / ${pct(g('ANO').praha.pct, 0)}) a SPD a menších stran, zatímco voliči SPOLU přišli skoro všichni (${pct(g('SPOLU').p5.pct, 0)} / ${pct(g('SPOLU').praha.pct, 0)}).</p>
        <p><b>Srovnání s nezávislou analýzou:</b> <a href="${DP.ps25_kv26.doma_zdroj}" target="_blank" rel="noopener">Mahdalová & Škop</a> odhadli totéž pro 22 měst a senátních obvodů dvěma metodami. V Praze jim vyšlo, že doma zůstalo ${nf(ms('Piráti')[0], 0)}–${nf(ms('Piráti')[1], 0)} % pirátských voličů, ${nf(ms('ANO')[0], 0)}–${nf(ms('ANO')[1], 0)} % voličů ANO a ${nf(ms('SPD')[0], 0)}–${nf(ms('SPD')[1], 0)} % voličů SPD; u SPOLU byl medián přes všech 22 míst ${g('SPOLU').ms_median22} %. Naše pražské odhady leží uvnitř jejich rozsahů, obě analýzy se tedy shodují: <b>hlavním kanálem pirátského propadu je nevolení</b>, ne přechod k jiné straně. Kdo z pirátských voličů roku 2025 přišel a volil jinak, šel podle obou analýz hlavně k Praha sobě / PRAHA 5 SOBĚ.</p>
        <p class="small">Toky od nevoličů a k nevoličům jsou v ekologické inferenci nejméně spolehlivé a u malých stran (Piráti, SPD) jsou intervaly široké; Mahdalová & Škop upozorňují na totéž. Na Praze 5 je odhad z ${DP.ps25_kv26.p5.okrsku} okrsků, v Praze z ${int(DP.ps25_kv26.praha.okrsku)}.</p>`;
      (() => {
        const box = $('#ch-d-doma'), rows = DM.filter((r) => r.strana !== 'Ostatní'), W = 560, rowH = 40, L = 100, R = 20, T = 8, H = T + rows.length * rowH + 30;
        const s = svgRoot(box, W, H), X = (v) => L + (v / 100) * (W - L - R);
        for (let v = 0; v <= 100; v += 25) { el('line', { x1: X(v), x2: X(v), y1: T, y2: H - 24, class: v ? 'grid' : 'axis' }, s); el('text', { x: X(v), y: H - 8, 'text-anchor': 'middle' }, s).textContent = v + ' %'; }
        const C5 = css('--ink'), CP = css('--s1'), CM = css('--gray-mark');
        rows.forEach((r, i) => {
          const y = T + i * rowH + rowH / 2, g = el('g', {}, s);
          el('rect', { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: 'transparent' }, g);
          el('text', { x: L - 10, y: y + 4, 'text-anchor': 'end', class: r.strana === 'Piráti' ? 'lbl' : '' }, g).textContent = r.strana;
          if (r.ms_median22 != null && !r.ms_praha) el('line', { x1: X(r.ms_median22), x2: X(r.ms_median22), y1: y - 13, y2: y + 13, stroke: CM, 'stroke-width': 3 }, g);
          if (r.ms_praha) el('rect', { x: X(r.ms_praha[0]), y: y - 13, width: Math.max(2, X(r.ms_praha[1]) - X(r.ms_praha[0])), height: 26, rx: 4, fill: CM, opacity: 0.35 }, g);
          [[r.p5, C5, -6], [r.praha, CP, 6]].forEach(([d, c, dy]) => {
            if (!d) return;
            el('line', { x1: X(d.p05), x2: X(d.p95), y1: y + dy, y2: y + dy, stroke: c, 'stroke-width': 2 }, g);
            el('circle', { cx: X(d.pct), cy: y + dy, r: 5, fill: c, stroke: css('--surface'), 'stroke-width': 2 }, g);
          });
          hover(g, `<b>${esc(r.strana)}</b> – voliči 2025, kteří v roce 2026 nevolili<br>Praha 5: ${pct(r.p5.pct, 0)} (${nf(r.p5.p05, 0)}–${nf(r.p5.p95, 0)} %), asi ${int(r.p5.volicu)} voličů 2025` +
            (r.praha ? `<br>Praha: ${pct(r.praha.pct, 0)} (${nf(r.praha.p05, 0)}–${nf(r.praha.p95, 0)} %)` : '') +
            (r.ms_praha ? `<br>Mahdalová & Škop, Praha: ${nf(r.ms_praha[0], 0)}–${nf(r.ms_praha[1], 0)} %` : '') + (r.ms_median22 != null ? `<br>Mahdalová & Škop, medián 22 míst: ${r.ms_median22} %` : ''));
        });
        $('#lg-d-doma').innerHTML = `<span><span class="sw" style="background:${C5}"></span>Praha 5 (náš odhad)</span><span><span class="sw" style="background:${CP}"></span>Praha (náš odhad, magistrát)</span><span><span class="sw" style="background:${CM};opacity:.5"></span>Mahdalová & Škop: rozsah v Praze (pás) nebo medián 22 míst (čárka)</span>`;
        tableToggle(box, ['strana', 'Praha 5', 'Praha', 'Mahdalová & Škop (Praha)'], rows.map((r) => [r.strana, `${nf(r.p5.pct, 0)} % (${nf(r.p5.p05, 0)}–${nf(r.p5.p95, 0)})`,
          r.praha ? `${nf(r.praha.pct, 0)} % (${nf(r.praha.p05, 0)}–${nf(r.praha.p95, 0)})` : '–', r.ms_praha ? `${nf(r.ms_praha[0], 0)}–${nf(r.ms_praha[1], 0)} %` : (r.ms_median22 != null ? `medián 22 míst ${r.ms_median22} %` : '–')]));
      })();
    }
    table($('#tb-d-ucastkor'), [{ k: 'strana', label: 'Strana' }, { k: 'r', label: 'r (změna účasti × změna podílu)', n: 1, f: (r) => nf(r.r, 2) }],
      Object.entries(UC.korelace_zmena_ucasti).map(([strana, r]) => ({ strana, r })));

    const VY = DP.vystavba, t = VY.p5_top, rs = VY.p5_ostatni, pn = VY.praha_nove;
    $('#d-vystavba-text').innerHTML = `<p>Deset okrsků Prahy 5 s největším přírůstkem voličů od roku 2022 (${pr(t.rust_volicu, 0)} proti ${pr(rs.rust_volicu)} jinde) volilo Piráty ${pct(t.pirati_2026)} (ostatní okrsky ${pct(rs.pirati_2026)}), STAN ${pct(t.stan_2026)} (${pct(rs.stan_2026)}), SEN ${pct(t.sen_2026)} (${pct(rs.sen_2026)}); účast ${pct(t.ucast_2026)} (${pct(rs.ucast_2026)}). Vztah růstu voličů a změny Pirátů r = ${nf(VY.korelace_rust_pirati_zmena, 2)}. V celé Praze má ${pn.okrsku} okrsků přírůstek voličů 15–100 %: Piráti tam ${pct(pn.pirati_2026)} na magistrát (jinde ${pct(pn.pirati_2026_ostatni)}), účast ${pct(pn.ucast_nove)} (${pct(pn.ucast_ostatni)}).</p>`;
    table($('#tb-d-vystavba'), [
      { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => r.okrsek }, { k: 'ctvrt', label: 'Čtvrť' }, { k: 'rust_volicu', label: 'Přírůstek voličů', n: 1, f: (r) => pr(r.rust_volicu) },
      { k: 'pirati_2026', label: 'Piráti 2026', n: 1, f: (r) => pct(r.pirati_2026) }, { k: 'pirati_zmena', label: 'Změna', n: 1, f: (r) => `<span class="${sgnCls(r.pirati_zmena)}">${pp(r.pirati_zmena)}</span>` },
      { k: 'ucast_2026', label: 'Účast', n: 1, f: (r) => pct(r.ucast_2026) },
    ], VY.p5_okrsky);

    const SM = DP.srovnani_mc;
    const SR = SM.mc.filter((m) => m.srovnatelne), lep = SR.filter((m) => m.rezidual > 0 && !m.p5).sort((a, b) => b.rezidual - a.rezidual);
    $('#d-mc-text').innerHTML = `<p>Piráti měli kandidátku do MČ v roce 2022 i 2026 ve ${SM.p5.vsech_mc} městských částech. Srovnatelných je ${SM.srovnatelnych}: tam, kde šli Piráti v obou volbách pod vlastní značkou – sami, nebo s nezávislými kandidáty (i na Praze 5 kandidují nezávislí na pirátské kandidátce) – a MČ má aspoň 5 000 voličů. Koalice (Piráti + Praha sobě, Zelení, STAN, KDU-ČSL…) jsou v tabulce také, počítané jako blok Pirátů a partnerů v obou volbách i na magistrátu; kde se ale složení koalice mezi volbami změnilo, srovnání s magistrátem férové není.</p>
      <p>Ve všech ${SM.srovnatelnych} srovnatelných MČ ztratila místní kandidátka méně než magistrátní. Kde Piráti víc ztratili na magistrátu, ztratili víc i místně (r = ${nf(SM.model.r, 2)}). Podle propadu na magistrátu se na Praze 5 čekala změna ${pr(SM.p5.ocekavano)}, skutečnost je ${pr(SM.p5.rel_mc)}, tedy o ${nf(Math.abs(SM.p5.rezidual), 1)} p. b. ${SM.p5.rezidual >= 0 ? 'lépe' : 'hůř'} – ${SM.p5.poradi}. místo z ${SM.p5.z_kolika} (${nf(Math.abs(SM.p5.z), 1)} směrodatné odchylky, ${Math.abs(SM.p5.z) < 1 ? 'v rámci běžného rozptylu' : 'výraznější odchylka'}). Nad očekáváním dopadly také ${lep.map((m) => `${esc(m.nazev)} (${pp(m.rezidual)})`).join(', ')}.</p>`;
    scatter($('#ch-d-mc'), SR.map((m) => ({ x: m.rel_mag, y: m.rel_mc, series: m.p5 ? 'P5' : 'MČ', tip: `<b>${esc(m.nazev)}</b><br>MČ: ${pct(m.mc_2022)} → ${pct(m.mc_2026)} (${pr(m.rel_mc)})<br>magistrát: ${pr(m.rel_mag)}<br>lépe/hůř než očekávání: ${pp(m.rezidual)}` })),
      { xl: 'relativní změna na magistrát (%)', yl: 'relativní změna listiny v MČ (%)', series: [{ key: 'MČ', color: css('--gray-mark') }, { key: 'P5', color: css('--s8') }], fit: false });
    table($('#tb-d-mc'), [
      { k: 'nazev', label: 'MČ', f: (r) => `${esc(r.nazev)}<br><span class="muted">${esc(r.typ_2022 === r.typ_2026 ? r.typ_2026 : r.typ_2022 + ' → ' + r.typ_2026)}</span>` },
      { k: 'mc', label: 'MČ 2022 → 2026', n: 1, f: (r) => `${pct(r.mc_2022)} → ${pct(r.mc_2026)}` },
      { k: 'rel_mc', label: 'Změna v MČ', n: 1, f: (r) => pr(r.rel_mc) }, { k: 'rel_mag', label: 'Změna na magistrátu', n: 1, f: (r) => pr(r.rel_mag) },
      { k: 'ocekavano', label: 'Očekávaná změna v MČ', n: 1, title: 'podle propadu na magistrátu v téže MČ', f: (r) => pr(r.ocekavano) },
      { k: 'rezidual', label: 'Lépe / hůř než očekávání', n: 1, f: (r) => (r.srovnatelne ? `<span class="${sgnCls(r.rezidual)}">${pp(r.rezidual)}</span>` : `<span class="muted">${pp(r.rezidual)}<br>${esc(r.proc_ne)}</span>`) },
    ], [...SM.mc].sort((a, b) => (b.srovnatelne - a.srovnatelne) || (b.rezidual - a.rezidual)), { rowClass: (r) => (r.p5 ? 'hl' : '') });

    const MC = DP.monte_carlo, pd4 = (d) => Object.entries(d).filter(([k]) => +k >= 4).reduce((a, [, v]) => a + v, 0);
    $('#d-mandaty-text').innerHTML = `<p>Oficiálně ${MC.oficialne} mandáty, na další chybělo ${int(D.psefologie.mandaty.chybelo_na_4_mandat_hlasu)} hlasů. Kdyby se hlasy všech stran náhodně pohnuly o ±1 % (relativně), měli by Piráti 4 a víc mandátů v ${nf(pd4(MC.sum_1_procento.pirati), 0)} % simulací; při ±2 % v ${nf(pd4(MC.sum_2_procenta.pirati), 0)} %. Při náhodném přeskupení okrsků (bootstrap, odpovídá jiné geografické účasti) v ${nf(pd4(MC.bootstrap_okrsku.pirati), 0)} %. Další mandát tedy nebyl daleko – rozhodovaly desítky voličů (${D.psefologie.mandaty.chybelo_na_4_mandat_volicu} „plných“).</p>`;
    const simRows = ['sum_1_procento', 'sum_2_procenta', 'bootstrap_okrsku'].flatMap((key) => ['pirati', 'sen'].map((p) => ({ scen: { sum_1_procento: 'šum ±1 %', sum_2_procenta: 'šum ±2 %', bootstrap_okrsku: 'bootstrap okrsků' }[key], p: p === 'pirati' ? 'Piráti' : 'SEN', d: MC[key][p] })));
    const allK = [...new Set(simRows.flatMap((r) => Object.keys(r.d).map(Number)))].sort((a, b) => a - b);
    table($('#tb-d-mc-sim'), [{ k: 'scen', label: 'Scénář' }, { k: 'p', label: 'Strana' }, ...allK.map((kk) => ({ k: 'm' + kk, label: `${kk} mand.`, n: 1, f: (r) => (r.d[kk] ? `${nf(r.d[kk], 0)} %` : '–') }))], simRows);

    const EV = DP.ei_varianty;
    $('#d-ei-text').innerHTML = `<p>Goodmanova regrese odhaduje jednu matici přesunů pro všechny okrsky. Varianta s IPF (entropická metoda Johnstona a Pattieho) ji použije jako výchozí bod a v každém okrsku ji dorovná tak, aby přesně seděla na výsledky okrsku v obou volbách. Kde se obě metody shodují, je odhad robustnější.</p>`;
    const eiRows = [];
    [['p5', 'Praha 5 (MČ)'], ['praha', 'Praha (magistrát)']].forEach(([k, lab]) => EV[k].kategorie.forEach((c, j) => eiRows.push({ uzemi: lab, kam: c, g: EV[k].goodman[j], i: EV[k].ipf[j] })));
    table($('#tb-d-ei'), [{ k: 'uzemi', label: 'Území' }, { k: 'kam', label: 'Kam (2026)' }, { k: 'g', label: 'Goodman', n: 1, f: (r) => `${nf(r.g, 0)} %` }, { k: 'i', label: 'IPF po okrscích', n: 1, f: (r) => `${nf(r.i, 0)} %` }],
      eiRows.filter((r) => r.g >= 1 || r.i >= 1));
  }

  /* Senioři */
  if (RZ.seniori) {
    const SN = RZ.seniori, big = SN.domovy[0];
    const isD = (k) => k === 'mc_delta';
    const cell = (v, ref, k) => (v == null ? '–' : `${isD(k) ? pp(v) : pct(v)}${ref != null && !isD(k) ? ` <span class="${v - ref > 1 ? 'up' : v - ref < -1 ? 'down' : 'muted'}">(${v - ref >= 0 ? '+' : '−'}${nf(Math.abs(v - ref), 1)})</span>` : ''}`);
    $('#seniori-text').innerHTML = `<p>Na Praze 5 jsou podle registru MPSV ${SN.domovy.length} pobytová zařízení pro seniory. Volební vliv může mít hlavně <b>${esc(big.nazev)}</b> (${esc(big.adresa)}, ${big.kapacita} lůžek) v okrsku ${big.okrsek} (${esc(big.ctvrt)}): lůžka odpovídají až ${nf(big.podil_kapacity, 0)} % zapsaných voličů okrsku. Tam měli Piráti ${pct(big.okrsek_hodnoty.mc_2026)} (sousední okrsky ${pct(big.sousede_hodnoty.mc_2026)}), ANO ${pct(big.okrsek_hodnoty.ano_2026)} (sousedé ${pct(big.sousede_hodnoty.ano_2026)}) a účast byla ${pct(big.okrsek_hodnoty.ucast_2026)} (sousedé ${pct(big.sousede_hodnoty.ucast_2026)}). Ve sněmovních volbách 2025 tam měli Piráti ${pct(big.okrsek_hodnoty.ps_2025)} proti ${pct(big.sousede_hodnoty.ps_2025)} v okolí.</p>
      <p>Ostatní zařízení jsou malá (odlehčovací služby na krátkodobé pobyty, 8 lůžek domova se zvláštním režimem) a výsledek okrsku znatelně ovlivnit nemohou; rozdíl proti sousedům je u nich spíš vlastnost čtvrti než domova. Data o tom, jak volili přímo klienti domovů (přenosná volební schránka), nejsou veřejná.</p>`;
    table($('#tb-seniori'), [
      { k: 'nazev', label: 'Zařízení', f: (r) => `<b>${esc(r.nazev || r.adresa)}</b><br><span class="muted">${esc(r.adresa)} · ${Object.entries(r.sluzby).map(([k, v]) => `${k} ${v}`).join(', ')}</span>`, cls: 'wrap' },
      { k: 'okrsek', label: 'Okrsek', n: 1, f: (r) => `${r.okrsek}<br><span class="muted">${esc(r.ctvrt)}</span>` },
      { k: 'podil_kapacity', label: 'Lůžka / voliči', n: 1, f: (r) => `${r.kapacita} / ${int(r.volici)}<br><span class="muted">${nf(r.podil_kapacity, 0)} %</span>` },
      ...SN.metriky.map((m) => ({ k: m.k, label: m.label, n: 1, sv: (r) => r.okrsek_hodnoty[m.k],
        f: (r) => `${cell(r.okrsek_hodnoty[m.k], r.sousede_hodnoty[m.k], m.k)}<br><span class="muted">okolí ${isD(m.k) ? pp(r.sousede_hodnoty[m.k]) : pct(r.sousede_hodnoty[m.k])} · P5 ${isD(m.k) ? pp(SN.p5[m.k]) : pct(SN.p5[m.k])}</span>` })),
    ], SN.domovy);
  }

  /* Kandidáti */
  $('#kand-text').innerHTML = `<p>V komunálních volbách většina voličů dává hlas celé listině, takže preferenční hlasy kandidátů se liší jen o desítky až stovky. Přednost před pořadím dostane kandidát, který má aspoň o 10 % víc hlasů, než je průměr na kandidáta listiny (zde ${int(P.mc_hlasy_2026 / D.p5_kandidati.length * 1.1)} hlasů; 10% hranici jsme ověřili přepočtem všech kandidátek Prahy 5). Mandát získali ${mandK.map((k) => `${esc(k.jmeno)} (${k.poradi}.)`).join(', ')}. ${kryl ? `${esc(kryl.jmeno)}, jednatel Spolku na ochranu Barrandova, přeskočil z 6. místa: na Barrandově dostal o ${nf(kryl.index_ctvrti.Barrandov - 100, 0)} % víc preferencí, než je jeho průměr.` : ''}</p>`;
  const CTS = Object.keys(D.p5_kandidati[0].index_ctvrti);
  table($('#tb-kand'), [
    { k: 'poradi', label: '#', n: 1, f: (r) => r.poradi }, { k: 'jmeno', label: 'Kandidát', f: (r) => `${r.mandat ? '<b>' : ''}${esc(r.jmeno)}${r.mandat ? '</b>' : ''}` },
    { k: 'vek', label: 'Věk', n: 1, f: (r) => r.vek }, { k: 'hlasy', label: 'Hlasy', n: 1, f: (r) => int(r.hlasy) }, { k: 'pct', label: '% listiny', n: 1, f: (r) => nf(r.pct, 2) },
    { k: 'mandat', label: 'Mandát', sv: (r) => (r.mandat ? 1 : 0), f: (r) => (r.mandat ? `✓ ${r.poradi_mand}.` : r.poradi_nahr ? `${r.poradi_nahr}. náhr.` : '') },
    ...CTS.map((c) => ({ k: 'i_' + c, label: c, n: 1, sv: (r) => r.index_ctvrti[c], f: (r) => { const v = r.index_ctvrti[c]; return v >= 110 ? `<b class="up">${v}</b>` : v <= 90 ? `<span class="down">${v}</span>` : v; } })),
  ], D.p5_kandidati, { sort: 'poradi', desc: false });
  table($('#tb-debaty'), [
    { k: 'jmeno', label: 'Host' }, { k: 'ctvrt', label: 'Debata', f: (r) => `${esc(r.ctvrt)} (${esc(r.datum)})` },
    { k: 'index_v_ctvrti', label: 'Index v čtvrti', n: 1, f: (r) => (r.na_kandidatce ? nf(r.index_v_ctvrti, 0) : 'nekandiduje') },
    { k: 'poradi_ctvrti', label: 'Pořadí čtvrti', n: 1, f: (r) => (r.na_kandidatce ? `${r.poradi_ctvrti}. z 9` : '') },
  ], D.debaty);
  table($('#tb-magk'), [
    { k: 'poradi', label: '#', n: 1, f: (r) => r.poradi }, { k: 'jmeno', label: 'Kandidát', f: (r) => `${r.mandat ? '<b>' : ''}${esc(r.jmeno)}${r.mandat ? '</b>' : ''}` },
    { k: 'hlasy', label: 'Hlasy Praha', n: 1, f: (r) => int(r.hlasy) }, { k: 'hlasy_p5', label: 'Hlasy Praha 5', n: 1, f: (r) => int(r.hlasy_p5) },
    { k: 'mandat', label: 'Mandát', f: (r) => (r.mandat ? '✓' : '') },
  ], D.mag_kandidati.slice(0, 15));


  select(5011);
  // odkaz na sekci (#psefologie apod.) funguje i po dokreslení obsahu
  if (location.hash && document.querySelector(location.hash)) setTimeout(() => document.querySelector(location.hash).scrollIntoView(), 300);
}
