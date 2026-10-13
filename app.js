'use strict';
/* Piráti Praha 5 – volby 2026. Data: data/data.json (generuje build.py). */

const $ = (s) => document.querySelector(s);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const nf = (v, d = 1) => (v == null || isNaN(v) ? '–' : Number(v).toLocaleString('cs-CZ', { minimumFractionDigits: d, maximumFractionDigits: d }));
const pct = (v, d = 1) => (v == null ? '–' : nf(v, d) + ' %');
const pp = (v, d = 1) => (v == null ? '–' : (v > 0 ? '+' : v < 0 ? '−' : '±') + nf(Math.abs(v), d) + ' p. b.');
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

/* Dumbbell: rows [{label, a, b, hi, extra}] – a = dřívější, b = pozdější. */
function dumbbell(container, rows, { la = '2022', lb = '2026', max, extraLabel } = {}) {
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
function bars(container, rows, { max, unit = ' %', d = 1 } = {}) {
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
    el('text', { x: L + w + 6, y: y + rowH / 2 + 4, class: 'lbl' }, g).textContent = nf(r.v, d) + unit;
    hover(g, `<b>${esc(r.label)}</b><br>${nf(r.v, 2)}${unit}${r.note ? '<br>' + r.note : ''}`);
  });
}

/* Bodový graf: points [{x, y, label, series}] */
function scatter(container, pts, { xl, yl, series, zeroY = false, zeroX = false, fit = false } = {}) {
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

/* ---------- hlavní ---------- */
fetch('data/data.json').then((r) => r.json()).then(init).catch((e) => {
  document.querySelector('main').insertAdjacentHTML('afterbegin', `<p class="card">Data se nepodařilo načíst (${esc(e.message)}). Stránku je potřeba otevřít přes web server, ne jako soubor.</p>`);
});

function init(D) {
  const P = D.p5, O = D.okrsky, S = D.stats;
  const byO = Object.fromEntries(O.map((o) => [o.okrsek, o]));
  const pub = D.akce.filter((a) => a.typ !== 'Interní' && a.datum >= '2026-01-01');
  const kamp = pub.filter((a) => a.datum >= '2026-09-01');
  const down = O.filter((o) => o.mc_delta < 0).length;
  const mcDown = D.mc.filter((m) => m.mag_2026 < m.mag_2022).length;
  const relMc = (P.mc_2026 / P.mc_2022 - 1) * 100, relMag = (P.mag_2026 / P.mag_2022 - 1) * 100;
  const p26 = D.p5_parties['2026'], p22 = D.p5_parties['2022'];
  const find = (arr, rx) => arr.find((p) => rx.test(p.nazev));
  const stan22 = find(p22, /^STAROSTOVÉ/), stan26 = find(p26, /^STAROSTOVÉ/), sen22 = find(p22, /SEN/), sen26 = find(p26, /SEN/);
  const magStan = (y) => D.mag_parties[y].find((p) => /^STAROSTOVÉ/.test(p.nazev));
  const ups = O.filter((o) => o.mc_delta > 0).sort((a, b) => b.mc_delta - a.mc_delta);
  const worst = [...O].sort((a, b) => a.mc_delta - b.mc_delta).slice(0, 3);
  const C = Object.fromEntries(D.ctvrti.map((c) => [c.ctvrt, c]));
  const kryl = D.p5_kandidati.find((k) => /Kryl/.test(k.jmeno));
  const mandK = D.p5_kandidati.filter((k) => k.mandat);
  const lask = D.senat.kandidati.find((k) => /Láska/.test(k.jmeno)), sab = D.senat.kandidati.find((k) => /Sáblík/.test(k.jmeno));

  /* tiles */
  const tile = (k, v, d) => `<div class="tile"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
  $('#tiles').innerHTML =
    tile('Praha 5 – zastupitelstvo MČ', pct(P.mc_2026, 2), `<b class="down">${pp(P.mc_2026 - P.mc_2022, 2)}</b> · ${P.mc_mand_2026} mandáty z 45 (2022: ${P.mc_mand_2022})`) +
    tile('Praha 5 – hlasy na magistrát', pct(P.mag_2026, 2), `<b class="down">${pp(P.mag_2026 - P.mag_2022, 2)}</b> proti 2022`) +
    tile('Praha – magistrát celkem', pct(D.praha_mag_2026.pct, 2), `<b class="down">${pp(D.praha_mag_2026.pct - D.praha_mag_2022.pct, 2)}</b> · ${D.praha_mag_2026.mandaty} mandátů (2022: ${D.praha_mag_2022.mandaty})`) +
    tile('Účast Praha 5', pct(P.ucast_2026), `<b class="up">${pp(P.ucast_2026 - P.ucast_2022)}</b> · ≈ ${int(P.mc_volici_2026)} pirátských voličů (2022: ${int(P.mc_volici_2022)})`);

  /* findings */
  $('#findings').innerHTML = [
    `<b>Praha 5: z 11,74 % na ${nf(P.mc_2026, 2)} %, ze 6 na ${P.mc_mand_2026} mandáty.</b> Hlasy Pirátů odpovídají zhruba ${int(P.mc_volici_2026)} voličům místo ${int(P.mc_volici_2022)} (−${nf((1 - P.mc_volici_2026 / P.mc_volici_2022) * 100, 0)} %), přestože účast stoupla o ${nf(P.ucast_2026 - P.ucast_2022)} p. b.`,
    `<b>Propad je celopražský, ne pětkový.</b> Na magistrát Piráti klesli v Praze ze ${nf(D.praha_mag_2022.pct, 2)} % na ${nf(D.praha_mag_2026.pct, 2)} % (${D.praha_mag_2022.mandaty} → ${D.praha_mag_2026.mandaty} mandátů) a ztratili ve všech ${mcDown} městských částech. Praha 5 je s ${nf(P.mag_2026, 2)} % na magistrát mírně nad pražským průměrem.`,
    `<b>Místní kandidátka ztratila méně než magistrátní.</b> Na Praze 5 přišla listina do MČ o ${nf(-relMc, 0)} % svého výsledku, magistrátní o ${nf(-relMag, 0)} %. Rozdíl mezi oběma hlasováními se zúžil z ${nf(P.mag_2022 - P.mc_2022)} na ${nf(P.mag_2026 - P.mc_2026)} p. b.`,
    `<b>Největší přírůstek mají Starostové, ne SEN.</b> STAN na Praze 5 vyrostl z ${nf(stan22.pct, 2)} na ${nf(stan26.pct, 2)} % (na magistrát z ${nf(magStan('2022').pct)} na ${nf(magStan('2026').pct)} %). SEN Václava Lásky přidal jen ${pp(sen26.pct - sen22.pct, 2)} (na ${nf(sen26.pct, 2)} %, ${sen26.mandaty} mandátů). V okrscích změna Pirátů nesouvisí se změnou STAN (r = ${nf(S['mc_delta~stan_delta'], 2)}) ani SEN (r = ${nf(S['mc_delta~sen_delta'], 2)}), takže pokles byl plošný a okrsková data neřeknou, ke komu voliči odešli.`,
    `<b>Ztráta v ${down} z 81 okrsků, nejvíc tam, kde byli Piráti nejsilnější</b> (korelace výsledku 2022 a změny r = ${nf(S['mc_2022~mc_delta'], 2)}). Nejhůř: ${worst.map((o) => `${o.okrsek} ${o.ctvrt} (${pp(o.mc_delta)})`).join(', ')}. Růst v ${ups.length} okrscích, výrazně jen ${ups[0].okrsek} v Košířích (${pp(ups[0].mc_delta)}).`,
    `<b>Akce se v okrskových výsledcích neprojevily.</b> ${pub.length} veřejných akcí, z toho ${kamp.length} v září a říjnu. Barrandov měl nejvíc akcí (${C['Barrandov'].akci}) a zároveň největší pokles mezi velkými čtvrtěmi (${nf(C['Barrandov'].mc_2022)} → ${nf(C['Barrandov'].mc_2026)} %). Mezi počtem akcí v okolí a změnou výsledku není vztah (r = ${nf(S['akci_kampan_do_700m~mc_delta'], 2)}, po kontrole výchozí úrovně t = ${nf(S.ols_mc_delta.akci_kampan_do_700m.t, 2)}).`,
    `<b>Školy:</b> do školek nebylo v roce 2026 přijato ${D.skoly.souhrn.ms_2026.neprijato} dětí (2025: ${D.skoly.souhrn.ms_2025.neprijato}), do 1. tříd ${D.skoly.souhrn.zs_2026.neprijato}. Nejhorší je situace ve školkách na Barrandově (úspěšnost žádostí ${pct(C['Barrandov'].ms_uspesnost, 0)}) a v Košířích (${pct(C['Košíře'].ms_uspesnost, 0)}). Piráti jsou silnější tam, kde je o spádovou ZŠ větší zájem, ale se změnou výsledku to nesouvisí.`,
    `<b>Preferenční hlasy:</b> mandáty mají ${mandK.map((k) => k.jmeno.replace(/^(Ing\.|Mgr\.|PhDr\.|MUDr\.)\s/, '')).join(', ')}. ${kryl ? `${kryl.jmeno.replace(/^Ing\.\s/, '')} postoupil ze 6. místa díky Barrandovu (index ${nf(kryl.index_ctvrti.Barrandov, 0)}).` : ''} Debaty „Na rovinu“ v preferencích hostů stopu nenechaly.`,
    `<b>Senát, obvod 21:</b> Piráti neměli kandidáta. Do 2. kola (16.–17. 10.) jdou ${lask.jmeno} (${pct(lask.pct)}) a ${sab.jmeno} (${pct(sab.pct)}). Láska je silný tam, kde i SEN (r = ${nf(S['sen_2026~laska'], 2)}), s Piráty mírně proti sobě (r = ${nf(S['mc_2026~laska'], 2)}).`,
  ].map((t) => `<li>${t}</li>`).join('');

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
  fetch('data/okrsky_praha.geojson').then((r) => r.json()).then((g) => {
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
    { k: 'laska', label: 'Láska (senát)', br: [20, 25, 30, 35, 40], ramp: ORANGE, get: (o) => o.senat['3'] },
    { k: 'ucast_2026', label: 'Účast 2026', br: [35, 42, 48, 54, 60], ramp: BLUE },
    { k: 'zs_uspesnost', label: 'Spádová ZŠ: úspěšnost', br: [65, 75, 85, 92, 98], ramp: BLUE },
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
    `<label style="margin-left:8px;font-size:14px"><input type="checkbox" id="ev-toggle"> místa akcí</label>`;
  btns.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
    btns.querySelectorAll('button').forEach((x) => x.setAttribute('aria-checked', 'false'));
    b.setAttribute('aria-checked', 'true'); cur = LAYERS[+b.dataset.i];
    if (cur.k === 'akce') { $('#ev-toggle').checked = true; evLayer.addTo(mapP5); }
    restyle();
  }));
  $('#ev-toggle').addEventListener('change', (e) => (e.target.checked ? evLayer.addTo(mapP5) : evLayer.remove()));
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
  fetch('data/okrsky_p5.geojson').then((r) => r.json()).then((g) => {
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
        <dt>Senát: Láska / Sáblík</dt><dd>${pct(o.senat['3'])} / ${pct(o.senat['6'])}</dd>
        <dt>Akcí do 700 m (celkem / kampaň)</dt><dd>${o.akci_do_700m} / ${o.akci_kampan_do_700m}</dd>
        <dt>Spádová ZŠ</dt><dd>${esc(o.zs_skola || '–')}</dd>
        <dt>Úspěšnost žádostí 2026 (2025)</dt><dd>${pct(o.zs_uspesnost, 0)} (${pct(o.zs_uspesnost_2025, 0)})</dd>
      </dl>
      <p class="sub"><b>Strany 2026 v okrsku</b></p><div id="okr-bars"></div>`;
    bars($('#okr-bars'), top.map(([k, v]) => ({ label: k.length > 26 ? k.slice(0, 25) + '…' : k, v, hi: /pirátská/i.test(k) })), { max: Math.max(30, top[0][1]) });
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
    { k: 'laska', label: 'Láska', n: 1, sv: (r) => r.senat['3'], f: (r) => pct(r.senat['3']) },
    { k: 'vitez_2026', label: 'Vítěz MČ', f: (r) => esc(r.vitez_2026.slice(0, 22)) },
    { k: 'akci_kampan_do_700m', label: 'Akce', n: 1, title: 'akcí v kampani (září–říjen) do 700 m', f: (r) => r.akci_kampan_do_700m },
    { k: 'zs_skola', label: 'Spádová ZŠ', f: (r) => esc(r.zs_skola || '–') },
    { k: 'zs_uspesnost', label: 'ZŠ úspěšnost', n: 1, title: 'úspěšnost žádostí u zápisu 2026 na spádové ZŠ', f: (r) => pct(r.zs_uspesnost, 0) },
  ], O, { sort: 'okrsek', desc: false, onRow: (r) => { select(r.okrsek, true); $('#map-p5').scrollIntoView({ behavior: 'smooth', block: 'center' }); } });
  $('#f-ctvrt').addEventListener('change', (e) => okrT.set(e.target.value ? O.filter((o) => o.ctvrt === e.target.value) : O));

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
  $('#akce-text').innerHTML = `<p>V kalendáři je ${pub.length} veřejných akcí v roce 2026 (bez interních schůzí): ${TYPES.map((t) => `${t.toLowerCase()} ${pub.filter((a) => a.typ === t).length}×`).join(', ')}. ${noCt} akcí nemá čtvrť a ${noAnc} nešlo přiřadit ke konkrétnímu okrsku, například „u Alberta“ na Malvazinkách nebo „U Zvonu“ v Košířích.</p>
    <p><b>Co z dat plyne:</b> akce se soustředily tam, kde byli Piráti už v roce 2022 silnější. Okrsky s 3 a více akcemi v okolí měly v roce 2022 průměrně ${pct(gh.mc_2022)}, okrsky bez akcí ${pct(g0.mc_2022)}. V roce 2026 je pořadí stejné (${pct(gh.mc_2026)} proti ${pct(g0.mc_2026)}), jenže relativní ztráta je v obou skupinách podobná (${nf((1 - gh.mc_2026 / gh.mc_2022) * 100, 0)} % proti ${nf((1 - g0.mc_2026 / g0.mc_2022) * 100, 0)} %). Okrsková data tedy nenaznačují, že by akce pokles brzdily. Nedokazují ale ani opak: stánky na Andělu nebo u metra oslovují hlavně lidi, kteří tam jen projíždějí, a o volbě se podle povolebních průzkumů velká část pirátských voličů rozhoduje až v posledním týdnu.</p>`;
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

  /* Senát */
  $('#senat-text').innerHTML = `<p>V okrscích Prahy 5 byla účast v 1. kole ${pct(D.senat.ucast_p5)}. Piráti vlastního kandidáta neměli; Václav Láska je zároveň tváří kandidátky SEN, tedy přímého konkurenta Pirátů v MČ. V ostatních pražských obvodech podpořili Piráti v obvodu 27 koaličního kandidáta Jiřího Padevěta.</p>`;
  bars($('#ch-senat'), [...D.senat.kandidati].sort((a, b) => b.pct - a.pct).map((k) => ({ label: k.jmeno, v: k.pct, hi: k.postup, note: `${esc(k.navrh)}<br>Praha 5: ${pct(D.senat.p5_pct[k.c])}${k.postup ? '<br><b>postup do 2. kola</b>' : ''}` })), { max: 40 });
  table($('#tb-senat-praha'), [
    { k: 'obvod', label: 'Obvod', n: 1, f: (r) => r.obvod }, { k: 'jmeno', label: 'Kandidát', f: (r) => `${esc(r.jmeno)}${r.pir ? ' <b>(s Piráty)</b>' : ''}` },
    { k: 'pct', label: '1. kolo', n: 1, f: (r) => pct(r.pct, 2) }, { k: 'postup', label: '', f: (r) => (r.postup ? '2. kolo' : '') },
  ], D.senat.ostatni_praha.filter((r) => r.pct >= 5));

  /* Kandidáti */
  $('#kand-text').innerHTML = `<p>V komunálních volbách většina voličů dává hlas celé listině, takže preferenční hlasy kandidátů se liší jen o desítky až stovky. Přednost před pořadím dostane kandidát, který má aspoň o 5 % víc hlasů, než je průměr na kandidáta listiny (zde ${int(P.mc_hlasy_2026 / D.p5_kandidati.length * 1.05)} hlasů). Mandát získali ${mandK.map((k) => `${esc(k.jmeno)} (${k.poradi}.)`).join(', ')}. ${kryl ? `${esc(kryl.jmeno)}, jednatel Spolku na ochranu Barrandova, přeskočil z 6. místa: na Barrandově dostal o ${nf(kryl.index_ctvrti.Barrandov - 100, 0)} % víc preferencí, než je jeho průměr.` : ''}</p>`;
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

  const o = S.ols_mc_delta;
  $('#ols').textContent = `Výsledek: R² = ${nf(S.ols_r2, 2)}; akce b = ${nf(o.akci_kampan_do_700m.b, 2)} (t = ${nf(o.akci_kampan_do_700m.t, 2)}), výsledek 2022 b = ${nf(o.mc_2022.b, 2)} (t = ${nf(o.mc_2022.t, 1)}), Δ účasti t = ${nf(o.ucast_delta.t, 2)}, Δ SEN t = ${nf(o.sen_delta.t, 2)}. Změnu vysvětluje hlavně výchozí úroveň (návrat k průměru); akce nic.`;

  select(5011);
}
