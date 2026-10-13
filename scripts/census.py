"""Demografie ze Sčítání 2021 (ČSÚ, Statistický atlas) × výsledky voleb.

python -P scripts/census.py <dl_dir> data

1) Okrsky Prahy 5: 1km grid SLDB 2021 (věk, byty, změna 2011→2021, vyjížďka) rozpočítaný do okrsků
   dasymetricky podle adresních bodů (všechny pražské adresy, takže buňky na hranici Prahy 5 se dělí správně).
2) 57 pražských MČ: ukazatele SLDB 2021 za ZÚJ (vzdělání, věk, narození v zahraničí) × Piráti na magistrát.

Stažení vstupů (dl/census/*.geojson, dl/census/praha_zuj.json) – viz scripts/download.sh.
Postup převzat z projektu census-demografie-cz-sk (grid SLDB 2021, EPSG:3035 → zde WGS84 z ArcGIS služby ČSÚ).
"""
import sys, os, json, re
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402

DL, OUT = sys.argv[1:3]
C = os.path.join(DL, 'census')
rng = np.random.default_rng(2026)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}

# ---------------------------------------------------------------- 1. grid → okrsky
LAYERS = {
    'sldb2021_obyvatelstvo': {'gis131620000': 'obyv', 'gis131620011': 'v0_14', 'gis131620012': 'v15_64', 'gis131620013': 'v65'},
    'byty': {'gis326070001': 'byty', 'gis326070002': 'byty_obydl', 'gis326070003': 'byty_neobydl'},
    'srovnani_sldb': {'gis243162002': 'zmena_obyv_11_21', 'gis242607002': 'zmena_byty_11_21'},
    'vyjizdka': {'gis174119001': 'vyjizdka', 'gis174119006': 'vyjizdka_prace', 'gis174119011': 'vyjizdka_skola'},
}
cells, geom = {}, {}
for lay, fields in LAYERS.items():
    for f in json.load(open(os.path.join(C, f'{lay}.geojson'), encoding='utf8'))['features']:
        p = f['properties']
        rec = cells.setdefault(p['kod'], {})
        for k, v in fields.items():
            rec[v] = float(p.get(k) or 0)
        geom[p['kod']] = np.array(f['geometry']['coordinates'][0])
cell_ids = list(cells)


def pip(x, y, ring):
    xs, ys = ring[:, 0], ring[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    return (((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / (yj - ys + 1e-15) + xs)).sum() % 2 == 1


bb = {k: (g[:, 0].min(), g[:, 0].max(), g[:, 1].min(), g[:, 1].max()) for k, g in geom.items()}


def cell_of(x, y):
    for k, b in bb.items():
        if b[0] <= x <= b[1] and b[2] <= y <= b[3] and pip(x, y, geom[k]):
            return k
    return None


okg = json.load(open(os.path.join(OUT, 'okrsky_p5.geojson'), encoding='utf8'))
polys = [(f['properties']['o'], [np.array(p[0]) for p in (f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']])]) for f in okg['features']]
obb = {o: (min(r[:, 0].min() for r in rs), max(r[:, 0].max() for r in rs), min(r[:, 1].min() for r in rs), max(r[:, 1].max() for r in rs)) for o, rs in polys}
X0, X1 = min(b[0] for b in bb.values()), max(b[1] for b in bb.values())
Y0, Y1 = min(b[2] for b in bb.values()), max(b[3] for b in bb.values())


def okrsek_of(x, y):
    for o, rs in polys:
        b = obb[o]
        if b[0] <= x <= b[1] and b[2] <= y <= b[3] and any(pip(x, y, r) for r in rs):
            return o
    return None


# všechny pražské adresní body (unikátní) v rozsahu stažených buněk
mun = json.load(open(os.path.join(DL, 'spad', 'addr_2026.bin'), encoding='utf8'))['municipalities']
pts = {}
for m in mun.values():
    for area in m['areas']:
        for p in area:
            pts[p['address']] = (p['lng'], p['lat'])
    for p in m.get('unmappedPoints') or []:
        pts[p['address']] = (p['lng'], p['lat'])
cnt_cell, cnt_cell_ok = {}, {}
for x, y in pts.values():
    if not (X0 <= x <= X1 and Y0 <= y <= Y1):
        continue
    k = cell_of(x, y)
    if k is None:
        continue
    cnt_cell[k] = cnt_cell.get(k, 0) + 1
    o = okrsek_of(x, y)
    if o is not None:
        cnt_cell_ok[(k, o)] = cnt_cell_ok.get((k, o), 0) + 1

VARS = ['obyv', 'v0_14', 'v15_64', 'v65', 'byty', 'byty_obydl', 'byty_neobydl', 'zmena_obyv_11_21', 'zmena_byty_11_21', 'vyjizdka']
alloc = {o: {v: 0.0 for v in VARS} for o in O}
for (k, o), n in cnt_cell_ok.items():
    w = n / cnt_cell[k]
    for v in VARS:
        alloc[o][v] += cells[k].get(v, 0) * w
okr_cen = []
for o, a in alloc.items():
    ob = a['obyv']
    rec = dict(
        cen_obyv=round(ob),
        cen_65=round(a['v65'] / ob * 100, 1) if ob else None,
        cen_0_14=round(a['v0_14'] / ob * 100, 1) if ob else None,
        cen_rust_11_21=round(a['zmena_obyv_11_21'] / (ob - a['zmena_obyv_11_21']) * 100, 1) if ob - a['zmena_obyv_11_21'] > 0 else None,
        cen_byty_neobydl=round(a['byty_neobydl'] / a['byty'] * 100, 1) if a['byty'] else None,
        cen_obyv_na_byt=round(ob / a['byty_obydl'], 2) if a['byty_obydl'] else None,
        cen_vyjizdka=round(a['vyjizdka'] / ob * 100, 1) if ob else None,
        cen_volici_na_obyv=round(O[o]['volici_2026'] / ob * 100, 1) if ob else None,
    )
    O[o].update(rec)
    okr_cen.append(dict(okrsek=o, **rec))

zuj = json.load(open(os.path.join(C, 'p5_zuj.json'), encoding='utf8'))['features'][0]['attributes']
check = dict(obyv_odhad=round(sum(a['obyv'] for a in alloc.values())), obyv_sldb=int(zuj['gis131620000']),
             v65_odhad=round(sum(a['v65'] for a in alloc.values()) / sum(a['obyv'] for a in alloc.values()) * 100, 1), v65_sldb=round(zuj['gis141190005'], 1),
             v0_14_odhad=round(sum(a['v0_14'] for a in alloc.values()) / sum(a['obyv'] for a in alloc.values()) * 100, 1), v0_14_sldb=round(zuj['gis141190003'], 1),
             bunek=len({k for k, _ in cnt_cell_ok}), adres_p5=sum(cnt_cell_ok.values()))
df = pd.DataFrame(data['okrsky']).set_index('okrsek')
check['r_volici_vs_obyv'] = round(float(df.volici_2026.drop(5008).corr(df.cen_obyv.drop(5008))), 3)

# korelace (okrsky) – permutační p a Benjamini–Hochberg; pozor: 1km grid vyhlazuje, sousední okrsky sdílí buňky
DEMO = [('cen_65', 'podíl 65+'), ('cen_0_14', 'podíl dětí 0–14'), ('cen_rust_11_21', 'růst obyvatel 2011–21'),
        ('cen_obyv_na_byt', 'obyvatel na obydlený byt'), ('cen_byty_neobydl', 'neobydlené byty'), ('cen_volici_na_obyv', 'voliči / obyvatelé')]
VYS = [('mc_2026', 'Piráti MČ 2026'), ('mc_delta', 'Piráti změna'), ('ps_2025', 'Piráti PS 2025'), ('ucast_2026', 'účast 2026'),
       ('ano_2026', 'ANO'), ('stan_2026', 'STAN'), ('sen_2026', 'SEN'), ('senat_sarapatka', 'Šarapatka')]
d2 = df.drop(index=[5008])  # adresa úřadu: voliči i účast zkreslené


def perm_p(x, y, n=1999):
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = np.corrcoef(x, y)[0, 1]
    sims = np.array([np.corrcoef(x, rng.permutation(y))[0, 1] for _ in range(n)])
    return r, (np.sum(np.abs(sims) >= abs(r)) + 1) / (n + 1)


kor = []
for a, al in DEMO:
    for b, bl in VYS:
        s = d2[[a, b]].dropna()
        r, p = perm_p(s[a], s[b])
        kor.append(dict(demo=a, demo_label=al, vysledek=b, vysledek_label=bl, r=round(float(r), 2), p=round(float(p), 4), n=len(s)))
ps = np.array([k['p'] for k in kor]); order = np.argsort(ps); m = len(ps)
ok = ps[order] <= 0.05 * np.arange(1, m + 1) / m
kmax = int(np.max(np.nonzero(ok)[0]) + 1) if ok.any() else 0
thr = ps[order][kmax - 1] if kmax else -1
for k in kor:
    k['fdr'] = bool(k['p'] <= thr)

# regrese: změna Pirátů ~ výsledek 2022 + věk + děti + růst (standardizované)
cols = ['mc_2022', 'cen_65', 'cen_0_14', 'cen_rust_11_21']
R = d2[cols + ['mc_delta', 'mc_2026']].dropna()


def ols(y, Xc):
    X = (R[Xc] - R[Xc].mean()) / R[Xc].std()
    X.insert(0, 'const', 1.0)
    b, *_ = np.linalg.lstsq(X.values, R[y].values, rcond=None)
    res = R[y].values - X.values @ b
    s2 = res @ res / (len(R) - X.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.values.T @ X.values)))
    r2 = 1 - (res @ res) / ((R[y] - R[y].mean()) @ (R[y] - R[y].mean()))
    return dict(r2=round(float(r2), 3), koef={c: dict(b=round(float(bi), 2), t=round(float(bi / si), 2)) for c, bi, si in zip(X.columns, b, se)})


reg = dict(zmena=ols('mc_delta', cols), uroven_2026=ols('mc_2026', ['cen_65', 'cen_0_14', 'cen_rust_11_21']))

# ---------------------------------------------------------------- 2. pražské MČ (ZÚJ): vzdělání a věk × Piráti na magistrát
zj = json.load(open(os.path.join(C, 'praha_zuj.json'), encoding='utf8'))['features']
Z = {int(f['attributes']['kod']): f['attributes'] for f in zj}
mc_rows = []
for m_ in data['mc']:
    a = Z.get(m_['kod'])
    if not a or m_.get('mag_2026') is None:
        continue
    mc_rows.append(dict(kod=m_['kod'], nazev=m_['nazev'], obyv=a['gis131620000'], vs=a['gis141190014'], v65=a['gis141190005'], v0_14=a['gis141190003'],
                        vek=a['gis124070001'], zahr=round(a['gis131620071'] / a['gis131620000'] * 100, 1) if a['gis131620000'] else None,
                        mag_2022=m_['mag_2022'], mag_2026=m_['mag_2026'], mag_zmena=round(m_['mag_2026'] - m_['mag_2022'], 2), ps25=m_.get('ps25')))
M = pd.DataFrame(mc_rows)
w = M.obyv
mc_kor = []
for a, al in [('vs', 'vysokoškoláci (25+)'), ('vek', 'průměrný věk'), ('v65', 'podíl 65+'), ('v0_14', 'podíl 0–14'), ('zahr', 'narození v zahraničí')]:
    for b, bl in [('mag_2026', 'Piráti magistrát 2026'), ('mag_2022', 'Piráti magistrát 2022'), ('mag_zmena', 'změna 2022→26'), ('ps25', 'Piráti PS 2025')]:
        s = M[[a, b]].dropna()
        r, p = perm_p(s[a], s[b])
        mc_kor.append(dict(demo=a, demo_label=al, vysledek=b, vysledek_label=bl, r=round(float(r), 2), p=round(float(p), 4), n=len(s)))
# relativní ztráta podle vzdělání (tercily MČ váženo obyvateli)
M['tercil_vs'] = pd.qcut(M.vs, 3, labels=['nejméně VŠ', 'střed', 'nejvíc VŠ'])
terc = [dict(skupina=str(k), mc=int(len(g)), vs=round(float(np.average(g.vs, weights=g.obyv)), 1), mag_2022=round(float(np.average(g.mag_2022, weights=g.obyv)), 2),
             mag_2026=round(float(np.average(g.mag_2026, weights=g.obyv)), 2)) for k, g in M.groupby('tercil_vs', observed=True)]

out = dict(kontrola=check, korelace_okrsky=kor, fdr_vyznamnych=int(kmax), regrese=reg, okrsky=okr_cen,
           mc=mc_rows, korelace_mc=mc_kor, mc_tercily_vs=terc,
           p5_sldb=dict(obyv=int(zuj['gis131620000']), vs=round(zuj['gis141190014'], 1), v65=round(zuj['gis141190005'], 1), v0_14=round(zuj['gis141190003'], 1),
                        vek=round(zuj['gis124070001'], 1)))
data['census'] = out
save(data, os.path.join(OUT, 'data.json'))
pd.DataFrame(okr_cen).to_csv(os.path.join(OUT, 'okrsky_demografie_sldb2021.csv'), index=False, encoding='utf-8-sig', sep=';', decimal=',')
print(json.dumps(check, ensure_ascii=False))
print('FDR', kmax); print(pd.DataFrame(kor).pivot(index='demo_label', columns='vysledek_label', values='r').to_string())
print(json.dumps(reg, ensure_ascii=False))
print(pd.DataFrame(mc_kor).pivot(index='demo_label', columns='vysledek_label', values='r').to_string())
print(pd.DataFrame(mc_kor)[['demo', 'vysledek', 'r', 'p']].to_string())
print(terc)
