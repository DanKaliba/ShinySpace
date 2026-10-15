"""Předpověď 2. kola Senátu po okrscích (obvod 21, Láska × Sáblík) a výběr metody zpětným testem.

python -P scripts/senat_okrsky.py <dl_dir> data        (spouštět po senat_predikce.py)

Předpověď se skládá ze dvou částí:
1) celkový výsledek obvodu – vzorce přesunů voličů z minulých druhých kol (model B v senat_predikce.py),
2) rozložení mezi okrsky – metoda vybraná zpětným testem na všech druhých kolech 2008–2024:
   M1 poměr finalistů v 1. kole, M2 průměrná matice přesunů minulých kol použitá na každý okrsek,
   M3 regrese (logit podílu ve 2. kole ~ logit poměru finalistů, podíl vypadlých kandidátů, účast, s pevným efektem kola).
   Ve zpětném testu se každé kolo předpovídá bez sebe sama a předpověď se posune tak, aby souhlasil skutečný celkový výsledek;
   chyba tak měří jen to, jak dobře metoda rozloží výsledek mezi okrsky.
Nejistota okrsku = nejistota celkového výsledku (rozptyl vzorců přesunů) + chyba okrsku ze zpětného testu (podle velikosti okrsku).
"""
import sys, os, json, pickle
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ei import fit  # noqa: E402
from jsonio import save  # noqa: E402
from senat_data import YEARS, PRAHA, load  # noqa: E402

DL, OUT = sys.argv[1:3]
H = os.path.join(DL, 'senat_hist')
OBVOD, LEAD, RUN, P5 = 21, 'Láska', 'Sáblík', 500143
rng = np.random.default_rng(2026)


def lg(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def sg(z):
    return 1 / (1 + np.exp(-z))


def okrsky(t5, obvod, a, b, kola=(1, 2)):
    t = t5[t5.OBVOD == obvod]
    k = ['OBEC', 'OKRSEK']
    m = t[t.KOLO == 1]
    if 2 in kola:
        m = m.merge(t[t.KOLO == 2], on=k, suffixes=('_1', '_2'))
        m = m[(m.VOL_SEZNAM_1 >= 50) & (m.VOL_SEZNAM_2 >= 50)]
    else:
        m = m.add_suffix('_1').rename(columns={'OBEC_1': 'OBEC', 'OKRSEK_1': 'OKRSEK'})
    d = pd.DataFrame({'OBEC': m.OBEC.values, 'OKRSEK': m.OKRSEK.values,
                      'reg1': m.VOL_SEZNAM_1.astype(float).values, 'valid1': m.PL_HL_CELK_1.astype(float).values,
                      'a1': m[f'HLASY_{a:02d}_1'].fillna(0).astype(float).values, 'b1': m[f'HLASY_{b:02d}_1'].fillna(0).astype(float).values})
    d['c1'] = d.valid1 - d.a1 - d.b1
    if 2 in kola:
        d['reg2'] = m.VOL_SEZNAM_2.astype(float).values
        d['a2'] = m[f'HLASY_{a:02d}_2'].fillna(0).astype(float).values
        d['b2'] = m[f'HLASY_{b:02d}_2'].fillna(0).astype(float).values
    return d


def features(d):
    h = d.b1 / (d.a1 + d.b1).clip(lower=1)
    L = lg(h.values)
    c = (d.c1 / d.valid1.clip(lower=1)).values
    t1 = (d.valid1 / d.reg1).values
    return np.c_[L, c, t1, L * c, L * t1]


def X_of(d):
    return np.c_[d.a1, d.b1, d.c1, d.reg1 - d.valid1] / d.reg1.values[:, None]


def shift_to(z, w, target):
    """Posun logitů tak, aby vážený průměrný podíl byl target."""
    lo, hi = -10.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if np.average(sg(z + mid), weights=w) < target else (lo, mid)
    return z + (lo + hi) / 2


# ---------------------------------------------------------------- historie
races = []
for y in YEARS:
    base = os.path.join(H, str(y))
    rk, t5 = load(base, 'serk'), load(base, 'set5')
    for ob, g in rk.groupby('OBVOD'):
        f = g[g.HLASY_K2.fillna(0) > 0]
        if len(f) != 2:
            continue
        f = f.sort_values('HLASY_K1', ascending=False)
        d = okrsky(t5, ob, int(f.iloc[0].CKAND), int(f.iloc[1].CKAND))
        d = d[(d.a2 + d.b2) > 0]
        if len(d) < 20:
            continue
        Y = np.c_[d.a2, d.b2, d.reg2 - d.a2 - d.b2] / d.reg2.values[:, None]
        races.append(dict(rok=y, obvod=int(ob), praha=int(ob) in PRAHA, d=d.reset_index(drop=True), B=fit(X_of(d), Y, d.reg1.values, iters=3000)))
print('druhých kol', len(races))
with open(os.path.join(H, '_kola_okrsky.pkl'), 'wb') as fh:  # mezipaměť pro senat_bayes.py
    pickle.dump([{k: r[k] for k in ('rok', 'obvod', 'praha', 'd', 'B')} for r in races], fh)

# M3: regrese s pevným efektem kola (odečtení vážených průměrů v rámci kola)
for r in races:
    d = r['d']
    r['F'] = features(d)
    r['y'] = lg((d.b2 / (d.a2 + d.b2)).values)
    r['w'] = (d.a2 + d.b2).values
    r['wv'] = d.valid1.values


def fit_m3(idx):
    Fs, ys, ws = [], [], []
    for i in idx:
        r = races[i]
        w = r['w']
        Fs.append(r['F'] - np.average(r['F'], axis=0, weights=w))
        ys.append(r['y'] - np.average(r['y'], weights=w))
        ws.append(w)
    F, yv, w = np.vstack(Fs), np.concatenate(ys), np.concatenate(ws)
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(F * sw[:, None], yv * sw, rcond=None)
    return beta


beta_all = fit_m3(range(len(races)))
Bmean_all = np.mean([r['B'] for r in races], axis=0)
METODY = {'M1': 'poměr finalistů v 1. kole', 'M2': 'přesuny voličů (průměrná matice minulých kol)', 'M3': 'regrese z minulých kol'}

# ---------------------------------------------------------------- zpětný test (každé kolo bez sebe sama, posun na skutečný celkový výsledek)
res = {m: dict(se=0.0, ae=0.0, w=0.0, ok=0, n=0) for m in METODY}
resid = []  # (počet hlasů, reziduum logitu) pro vybranou metodu
folds = rng.permutation(len(races)) % 10  # M3: 10násobná křížová validace po kolech (rychlejší než LOO, stejný princip)
beta_cv = {k: fit_m3([i for i in range(len(races)) if folds[i] != k]) for k in range(10)}
sum_B = np.sum([r['B'] for r in races], axis=0)
for i, r in enumerate(races):
    d = r['d']
    s_true = (d.b2 / (d.a2 + d.b2)).values
    target = d.b2.sum() / (d.a2 + d.b2).sum()
    Bm = (sum_B - r['B']) / (len(races) - 1)
    v = X_of(d) * d.reg1.values[:, None] @ Bm
    z = {'M1': r['F'][:, 0],
         'M2': lg(v[:, 1] / np.clip(v[:, 0] + v[:, 1], 1e-9, None)),
         'M3': r['F'] @ beta_cv[folds[i]]}
    for m, zz in z.items():
        p = sg(shift_to(zz, r['wv'], target))
        e = (p - s_true) * 100
        res[m]['se'] += float((r['w'] * e ** 2).sum()); res[m]['ae'] += float((r['w'] * np.abs(e)).sum()); res[m]['w'] += float(r['w'].sum())
        res[m]['ok'] += int(((p > 0.5) == (s_true > 0.5)).sum()); res[m]['n'] += len(p)
        if m == 'M3':
            resid.append(np.c_[r['w'], lg(s_true) - shift_to(zz, r['wv'], target)])
test = [dict(metoda=m, popis=METODY[m], rmse=round((x['se'] / x['w']) ** 0.5, 2), mae=round(x['ae'] / x['w'], 2), vitez_okrsku=round(x['ok'] / x['n'] * 100, 1)) for m, x in res.items()]
best = min(test, key=lambda x: x['rmse'])['metoda']
print('zpětný test', test, '→', best)

# chyba okrsku podle velikosti (směrodatná odchylka rezidua logitu v pěti skupinách podle počtu hlasů)
if best != 'M3':
    resid = []
    for i, r in enumerate(races):
        d = r['d']
        Bm = (sum_B - r['B']) / (len(races) - 1)
        v = X_of(d) * d.reg1.values[:, None] @ Bm
        zz = r['F'][:, 0] if best == 'M1' else lg(v[:, 1] / np.clip(v[:, 0] + v[:, 1], 1e-9, None))
        target = d.b2.sum() / (d.a2 + d.b2).sum()
        resid.append(np.c_[r['w'], lg((d.b2 / (d.a2 + d.b2)).values) - shift_to(zz, r['wv'], target)])
RS = np.vstack(resid)
edges = np.quantile(RS[:, 0], [0, .2, .4, .6, .8, 1])
sd_bin = [float(np.std(RS[(RS[:, 0] >= lo) & (RS[:, 0] <= hi), 1])) for lo, hi in zip(edges[:-1], edges[1:])]


def sd_for(n):
    return np.array([sd_bin[min(np.searchsorted(edges[1:-1], x), 4)] for x in n])


# ---------------------------------------------------------------- obvod 21, 2026
rk26 = load(os.path.join(DL, 'SE2026reg20261011_csv'), 'serk')
t26 = load(os.path.join(DL, 'SE2026data20261011_csv'), 'set5')
g = rk26[rk26.OBVOD == OBVOD]
ca, cb = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0]), int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
d = okrsky(t26, OBVOD, ca, cb, kola=(1,))
d = d[d.reg1 > 0].reset_index(drop=True)
F = features(d)
Xd = X_of(d) * d.reg1.values[:, None]
v = Xd @ Bmean_all
z0 = {'M1': F[:, 0], 'M2': lg(v[:, 1] / np.clip(v[:, 0] + v[:, 1], 1e-9, None)), 'M3': F @ beta_all}[best]
hlasu = v[:, 0] + v[:, 1]  # očekávaný počet platných hlasů pro finalisty (průměrná matice)
sd = sd_for(hlasu)
# celkový výsledek: každý vzorec přesunů z minulých kol → podíl Sáblíka v obvodu; k němu náhodná chyba okrsku
tot = Xd.sum(0)
shares = []
for r in races:
    vv = tot @ r['B']
    shares.append(vv[1] / (vv[0] + vv[1]))
shares = np.array(shares)
draws = []
for s_obv in shares:
    zc = shift_to(z0, hlasu, s_obv)
    for _ in range(20):
        draws.append(sg(zc + rng.normal(0, sd)))
P = np.array(draws) * 100
med = np.median(P, axis=0)
lo, hi = np.percentile(P, 10, axis=0), np.percentile(P, 90, axis=0)
pwin = (P > 50).mean(0) * 100
ucast = np.clip(hlasu / d.reg1.values * 100, 0, 100)

rows = []
for i, rr in d.iterrows():
    rows.append(dict(obec=int(rr.OBEC), okrsek=int(rr.OKRSEK), p5=int(rr.OBEC) == P5, zapsanych=int(rr.reg1),
                     k1_laska=int(rr.a1), k1_sablik=int(rr.b1), k1_ostatni=int(rr.c1),
                     k1_sablik_ze_dvou=round(float(rr.b1 / max(rr.a1 + rr.b1, 1) * 100), 1),
                     sablik=round(float(med[i]), 1), sablik_p10=round(float(lo[i]), 1), sablik_p90=round(float(hi[i]), 1),
                     p_sablik_vyhraje=round(float(pwin[i]), 0), ucast=round(float(ucast[i]), 1)))
p5r = [r for r in rows if r['p5']]
print('P5 okrsků', len(p5r), '| Sáblík vede (medián) v', sum(r['sablik'] > 50 for r in p5r), '| obvod medián', round(float(np.median(shares)) * 100, 1))

data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
data['senat_okrsky'] = dict(
    obvod=OBVOD, metoda=best, metody=test, druhych_kol=len(races),
    obvod_sablik=dict(median=round(float(np.median(shares)) * 100, 1), p10=round(float(np.percentile(shares, 10)) * 100, 1), p90=round(float(np.percentile(shares, 90)) * 100, 1)),
    regrese=dict(zip(['logit_pomer', 'podil_ostatnich', 'ucast_k1', 'logit_pomer_x_ostatni', 'logit_pomer_x_ucast'], [round(float(b), 3) for b in beta_all])),
    chyba_okrsku_sd_logit=[round(x, 3) for x in sd_bin],
    okrsky=rows,
    mimo_p5=dict(okrsku=len(rows) - len(p5r), zapsanych=int(sum(r['zapsanych'] for r in rows if not r['p5']))),
)
for o in data['okrsky']:
    r = next((x for x in p5r if x['okrsek'] == o['okrsek']), None)
    if r:
        o['senat_k2_sablik'], o['senat_k2_p'] = r['sablik'], r['p_sablik_vyhraje']
save(data, os.path.join(OUT, 'data.json'))
