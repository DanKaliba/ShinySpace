"""Rozšíření analýzy: Senát × výsledky Pirátů, Sankey přesunů (Praha 5 i Praha), okrsky s domovy pro seniory.

python -P scripts/rozsireni.py <dl_dir> data

Vstupy navíc proti build.py: dl/rpss/rpss.json (registr sociálních služeb MPSV),
dl/spad/addr_2026.bin (adresní body se souřadnicemi). Spouštět po psefologie.py.
"""
import sys, os, json, math, re
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ei import fit, bootstrap  # noqa: E402

DL, OUT = sys.argv[1:3]
P5, MAG = 500143, 554782
rng = np.random.default_rng(2026)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}
ids = sorted(O)


def rd(p):
    return pd.read_csv(os.path.join(DL, p), low_memory=False)


def pct_ci(boot, i, j):
    return round(float(np.percentile(boot[:, i, j], 5)) * 100, 1), round(float(np.percentile(boot[:, i, j], 95)) * 100, 1)


out = {}

# ---------------------------------------------------------------- 1. Senát obvod 21 × výsledky Pirátů
se = rd('SE2026data20261011_csv/csv_od/set5.csv')
serk = rd('SE2026reg20261011_csv/csv_od/serk.csv')
se = se[(se.OBEC == P5) & (se.KOLO == 1)].set_index('OKRSEK').loc[ids]
kand = serk[serk.OBVOD == 21].sort_values('CKAND')
K = {int(r.CKAND): f'{r.JMENO} {r.PRIJMENI}' for r in kand.itertuples()}
Ysen = pd.DataFrame({c: se[f'HLASY_{c:02d}'] / se.PL_HL_CELK for c in K}, index=ids)

df = pd.DataFrame(data['okrsky']).set_index('okrsek').loc[ids]
korel = []
for c, jm in K.items():
    s = Ysen[c] * 100
    korel.append(dict(c=c, jmeno=jm, navrh=kand.set_index('CKAND').NAZEV_VS[c][:60],
                      pct_p5=round(float((se[f'HLASY_{c:02d}'].sum() / se.PL_HL_CELK.sum()) * 100), 2),
                      r_pirati_mc=round(float(s.corr(df.mc_2026)), 2), r_pirati_mag=round(float(s.corr(df.mag_2026)), 2),
                      r_pirati_zmena=round(float(s.corr(df.mc_delta)), 2), r_pirati_ps25=round(float(s.corr(df.ps_2025)), 2),
                      r_sen=round(float(s.corr(df.sen_2026)), 2), r_stan=round(float(s.corr(df.stan_2026)), 2)))
out['senat_korelace'] = korel

# dělení hlasů: bloky stran v MČ (stejný den, stejní voliči) → senátní kandidáti
BL = [('Piráti', r'^Česká pirátská'), ('PRAHA 5 SOBĚ', r'^PRAHA 5 SOBĚ'), ('ODS, TOP 09, KDU', r'^Občanská demokratická|^TOP Lidovci'),
      ('STAN', r'^STAROSTOVÉ'), ('SEN', r'^SEN '), ('ANO', r'^ANO'), ('SPD, Motoristé a menší', r'.')]


def bloc_of(name):
    return next(b for b, rx in BL if re.search(rx, name))


X = pd.DataFrame([{b: 0.0 for b, _ in BL} for _ in ids], index=ids)
for o in ids:
    for n, v in O[o]['strany_2026'].items():
        X.loc[o, bloc_of(n)] += v / 100
X = X.div(X.sum(1), axis=0)
units = [o for o in ids if o != 5008]
w = se.PL_HL_CELK.loc[units].values
Bs = fit(X.loc[units].values, Ysen.loc[units].values, w)
bs_boot = bootstrap(X.loc[units].values, Ysen.loc[units].values, w, rng, n=200)
blocs, cands = [b for b, _ in BL], list(K)
out['senat_deleni'] = dict(
    bloky=blocs, kandidati=[K[c] for c in cands],
    matice=[[round(float(v) * 100, 1) for v in row] for row in Bs],
    pirati=[dict(kandidat=K[c], pct=round(float(Bs[0, j]) * 100, 1), p05=pct_ci(bs_boot, 0, j)[0], p95=pct_ci(bs_boot, 0, j)[1]) for j, c in enumerate(cands)],
    r2=round(float(1 - ((Ysen.loc[units].values - X.loc[units].values @ Bs) ** 2).sum() / ((Ysen.loc[units].values - Ysen.loc[units].values.mean(0)) ** 2).sum()), 3),
)
# kolik Šarapatkových hlasů v Praze 5 pochází od pirátských voličů (odhad)
sar = next(c for c, j in K.items() if 'Šarapatka' in j)
js = cands.index(sar)
mc_vol = X.loc[units].mul(se.PL_HL_CELK.loc[units], axis=0).sum()  # voliči bloků (přibližně = senátní platné hlasy)
from_bl = {b: float(Bs[i, js] * mc_vol[b]) for i, b in enumerate(blocs)}
tot = sum(from_bl.values())
out['sarapatka_odkud'] = sorted([dict(blok=b, volicu=int(v), pct=round(v / tot * 100, 1)) for b, v in from_bl.items()], key=lambda d: -d['volicu'])
for o in ids:
    O[o]['senat_sarapatka'] = round(float(Ysen.loc[o, sar] * 100), 2)

# ---------------------------------------------------------------- 2. Sankey Praha – magistrát 2022 → 2026 (všechny pražské okrsky)
MB = [('Piráti', r'^Česká pirátská'), ('SPOLU', r'^SPOLU'), ('STAN', r'^STAROSTOVÉ'), ('PRAHA SOBĚ', r'^PRAHA SOBĚ'), ('ANO', r'^ANO'), ('Ostatní', r'.')]


def mag(y):
    if y == 2026:
        t3, hl, ros = rd('KV2026_data_20261011_csv/csv_od/kvt3.csv'), rd('KV2026_data_20261011_csv/csv_od/kvhl.csv'), rd('KV2026reg20261011_csv/csv_od/kvros.csv')
    else:
        t3, hl, ros = rd('KV2022_data_20260328_csv/csv_od/kvt3.csv'), rd('KV2022_data_20260328_csv/csv_od/kvhl.csv'), rd('KV2022reg20260328_csv/csv_od/kvros.csv')
        t3, hl, ros = (d[d.DATUMVOLEB == 20220923] for d in (t3, hl, ros))
    t3 = t3[t3.KODZASTUP == MAG]
    hl = hl[hl.ID_OKRSKY.isin(set(t3.ID_OKRSKY))].merge(t3[['ID_OKRSKY', 'OBEC', 'OKRSEK']].rename(columns={'OBEC': 'OB', 'OKRSEK': 'OK'}), on='ID_OKRSKY')
    names = ros[ros.KODZASTUP == MAG].set_index('POR_STR_HL').ZKRATKAO30
    hl['blok'] = hl.POR_STR_HL.map(lambda p: next(b for b, rx in MB if re.search(rx, names[p])))
    v = hl.pivot_table(index=['OB', 'OK'], columns='blok', values='POC_HLASU', aggfunc='sum', fill_value=0)[[b for b, _ in MB]]
    t = t3.groupby(['OBEC', 'OKRSEK'])[['VOL_SEZNAM', 'ODEVZ_OBAL']].sum()
    t.index.names = ['OB', 'OK']
    return v, t


v22, t22 = mag(2022)
v26, t26 = mag(2026)
keys = v22.index.intersection(v26.index)
r = (t26.VOL_SEZNAM / t22.VOL_SEZNAM).reindex(keys)
u22 = (t22.ODEVZ_OBAL / t22.VOL_SEZNAM).reindex(keys)
keys = keys[(r > 0.8) & (r < 1.25) & (t22.VOL_SEZNAM.reindex(keys) >= 150) & (u22 > 0.15)]  # stabilní okrsky, bez "úředních"


def comp(v, t):
    sh = v.loc[keys].div(v.loc[keys].sum(1), axis=0)
    Xc = sh.mul(t.ODEVZ_OBAL.loc[keys], axis=0)
    Xc['Nevoliči'] = t.VOL_SEZNAM.loc[keys] - t.ODEVZ_OBAL.loc[keys]
    return Xc.div(t.VOL_SEZNAM.loc[keys], axis=0)


Xp, Yp = comp(v22, t22), comp(v26, t26)
wp = t22.VOL_SEZNAM.loc[keys].values
Bp = fit(Xp.values, Yp.values, wp)
bp_boot = bootstrap(Xp.values, Yp.values, wp, rng, n=100)
size_p = (Xp.mul(t22.VOL_SEZNAM.loc[keys], axis=0)).sum()
cat_p = list(Xp.columns)
ip = cat_p.index('Piráti')
out['sankey_praha'] = dict(
    kategorie=cat_p, velikost_2022={c: int(size_p[c]) for c in cat_p},
    velikost_2026={c: int(v) for c, v in (Yp.mul(t26.VOL_SEZNAM.loc[keys], axis=0)).sum().items()},
    matice=[[round(float(v), 4) for v in row] for row in Bp], okrsku=len(keys),
    pirati_kam=sorted([dict(kam=c, pct=round(float(Bp[ip, j]) * 100, 1), p05=pct_ci(bp_boot, ip, j)[0], p95=pct_ci(bp_boot, ip, j)[1],
                            volicu=int(Bp[ip, j] * size_p['Piráti'])) for j, c in enumerate(cat_p)], key=lambda d: -d['pct']),
)
pse = data['psefologie']['ei']
out['sankey_p5'] = dict(kategorie=pse['kategorie_2022'], velikost_2022=pse['velikost_2022'],
                        matice=[[v / 100 for v in row] for row in pse['matice']], okrsku=pse['okrsku'])

# ---------------------------------------------------------------- 3. Domovy pro seniory (registr MPSV) → okrsky
rp = json.load(open(os.path.join(DL, 'rpss', 'rpss.json'), encoding='utf8'))['polozky']
pts = {}
for area in json.load(open(os.path.join(DL, 'spad', 'addr_2026.bin'), encoding='utf8'))['municipalities']['500143']['areas']:
    for p in area:
        m = re.match(r'(.+?) (\d+)(?:/(\w+))?,', p['address'])
        if m:
            pts[(m.group(1), m.group(2))] = (p['lng'], p['lat'])
geo = json.load(open(os.path.join(OUT, 'okrsky_p5.geojson'), encoding='utf8'))
polys = [(f['properties']['o'], [np.array(p[0]) for p in (f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']])]) for f in geo['features']]


def pip(x, y, ring):
    xs, ys = ring[:, 0], ring[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    return (((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / (yj - ys + 1e-15) + xs)).sum() % 2 == 1


def okrsek_of(lng, lat):
    return next((o for o, rs in polys if any(pip(lng, lat, r) for r in rs)), None)


DRUH = {'8': 'odlehčovací pobytová služba', '13': 'domov pro seniory', '14': 'domov se zvláštním režimem'}
zar = {}
for it in rp:
    if it.get('datumPoskytovaniDo'):
        continue
    druh = it['druhSocialniSluzby']['id'].split('/')[-1]
    cs = {c['cilovaSkupina']['id'].split('/')[-1] for c in it.get('ciloveSkupiny') or []}
    pob = [f for f in it.get('formy') or [] if f['forma']['id'].endswith('/pob')]
    if not pob or not (druh in ('13', '14') or (druh == '8' and '24' in cs)):
        continue
    cap = sum(k['pocet'] for f in pob for k in (f.get('kapacity') or []) if k.get('pocet'))
    for z in it.get('zarizeni') or []:
        a = (z or {}).get('adresa') or {}
        if (a.get('obec') or {}).get('id') != 'Obec/554782' or not str(a.get('psc', '')).startswith(('150', '152', '158')):
            continue
        ul, cd = (a.get('ulice') or {}).get('nazev'), str(a.get('cisloDomovni'))
        pos = pts.get((ul, cd))
        key = (ul, cd)
        rec = zar.setdefault(key, dict(adresa=f"{ul} {cd}/{a.get('cisloOrientacni')}", nazev=(z.get('nazev') or '').strip(),
                                       poskytovatel=(it.get('poskytovatel') or {}).get('nazev'), sluzby={}, lon=pos[0] if pos else None,
                                       lat=pos[1] if pos else None, okrsek=okrsek_of(*pos) if pos else None))
        rec['sluzby'][DRUH[druh]] = max(rec['sluzby'].get(DRUH[druh], 0), cap)
# sousedé (k=6) pro srovnání okolí
xy = np.array([[O[o]['lon'] * math.cos(math.radians(50.07)), O[o]['lat']] for o in ids])
Dm = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1))
METR = [('mc_2026', 'Piráti MČ 2026'), ('mc_delta', 'Piráti změna'), ('ano_2026', 'ANO'), ('stan_2026', 'STAN'), ('sen_2026', 'SEN'),
        ('ucast_2026', 'Účast'), ('ps_2025', 'Piráti PS 2025')]
p5avg = {k: float(np.average(df[k], weights=df.volici_2026 if k == 'ucast_2026' else df.odevzdano_2026)) for k, _ in METR}  # účast vážit voliči
dom = []
for rec in zar.values():
    o = rec['okrsek']
    if o is None:
        continue
    i = ids.index(o)
    nn = [ids[j] for j in np.argsort(Dm[i])[1:7]]
    kap = sum(rec['sluzby'].values())
    dom.append(dict(**{k: v for k, v in rec.items() if k not in ('sluzby',)}, sluzby=rec['sluzby'], kapacita=kap,
                    ctvrt=O[o]['ctvrt'], volici=O[o]['volici_2026'], podil_kapacity=round(kap / O[o]['volici_2026'] * 100, 1),
                    okrsek_hodnoty={k: O[o][k] for k, _ in METR}, sousede=nn,
                    sousede_hodnoty={k: round(float(np.mean([O[n][k] for n in nn])), 2) for k, _ in METR}))
out['seniori'] = dict(domovy=sorted(dom, key=lambda d: -d['kapacita']), p5={k: round(v, 2) for k, v in p5avg.items()},
                      metriky=[dict(k=k, label=l) for k, l in METR])
for d_ in dom:
    O[d_['okrsek']]['domov_seniory'] = d_['nazev'] or d_['adresa']

data['rozsireni'] = out
json.dump(data, open(os.path.join(OUT, 'data.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps({k: v for k, v in out.items() if k not in ('sankey_praha', 'sankey_p5')}, ensure_ascii=False, indent=1)[:6000])
print('Praha okrsků', len(keys), 'piráti kam', out['sankey_praha']['pirati_kam'])
