"""Konformní intervaly pro okrsky obvodu 21 – nebayesovská kontrola bayesovského modelu 2. kola Senátu.

python -P scripts/senat_konform.py <dl_dir> <out_json>        (spouštět po senat_okrsky.py a senat_bayes.py)

Střed: průměrná matice přesunů minulých druhých kol použitá na každý okrsek, posunutá na medián celkového výsledku obvodu
podle matic jednotlivých minulých kol (stejně jako „stávající metoda“, bez znalosti skutečného výsledku).
Šířka: konformní predikce – normované chyby (logit skutečnosti − logit středu) / σ(velikost okrsku) ze všech minulých kol;
80% interval = střed ± 80. percentil |chyby|, rozdělení pro šanci na výhru = střed + empirické chyby. Žádný předpoklad o tvaru rozdělení.
Zpětný test: kolo se vyhodnotí s chybami jen z ostatních kol (každé kolo má stejnou váhu).
"""
import sys, os, json, pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from senat_data import load  # noqa: E402

DL, OUTJ = sys.argv[1:3]
OBVOD, LEAD, RUN = 21, 'Láska', 'Sáblík'
MC = {500143: 'Praha 5', 539694: 'Praha 13'}
rng = np.random.default_rng(2026)
races = pickle.load(open(os.path.join(DL, 'senat_hist', '_kola_okrsky.pkl'), 'rb'))
Ball = np.array([r['B'] for r in races])


def lg(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def sg(z):
    return 1 / (1 + np.exp(-z))


def counts(d):
    return np.c_[d.a1, d.b1, d.c1, d.reg1 - d.valid1].astype(float)


def shift_to(z, w, target):
    lo, hi = -10.0, 10.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if np.average(sg(z + mid), weights=w) < target else (lo, mid)
    return z + (lo + hi) / 2


def stred(n, Bs):
    v = n @ Bs.mean(0)
    hl = v[:, 0] + v[:, 1]
    z0 = lg(v[:, 1] / np.maximum(hl, 1e-9))
    tot = n.sum(0)
    s = [(tot @ B)[1] / ((tot @ B)[0] + (tot @ B)[1]) for B in Bs]
    return shift_to(z0, hl, float(np.median(s))), hl


# σ podle velikosti okrsku: pětiny počtu hlasů pro finalisty, robustní směrodatná odchylka chyby (MAD) v každé pětině
allw = np.concatenate([(r['d'].a2 + r['d'].b2).values for r in races])
edges = np.quantile(allw, [.2, .4, .6, .8])
E, Ew, RID, SIG = [], [], [], []
cent = []
for i, r in enumerate(races):
    d = r['d']
    others = np.delete(Ball, i, axis=0)
    zc, hl = stred(counts(d), others)
    y = lg((d.b2 / (d.a2 + d.b2)).values)
    cent.append((zc, hl, y, (d.a2 + d.b2).values))
    E.append(y - zc); RID.append(np.full(len(y), i)); SIG.append(np.searchsorted(edges, hl))
E, RID, SIG = np.concatenate(E), np.concatenate(RID), np.concatenate(SIG)
Ew = np.concatenate([np.full(len(c[2]), 1 / len(c[2])) for c in cent])  # každé kolo stejnou váhou
sig = np.array([1.4826 * np.median(np.abs(E[SIG == b] - np.median(E[SIG == b]))) for b in range(5)])
Z = E / sig[SIG]


def wquant(x, w, q):
    o = np.argsort(x)
    cw = np.cumsum(w[o]) / w.sum()
    return x[o][min(np.searchsorted(cw, q), len(x) - 1)]


def crps(s, y, w):
    s, y = s[:200] * 100, y * 100
    return float(np.average(np.abs(s - y).mean(0) - np.abs(s[:, None, :] - s[None, :, :]).mean((0, 1)) / 2, weights=w))


cov, crp, wid = [], [], []
for i, (zc, hl, y, w) in enumerate(cent):
    m = RID != i
    q = wquant(np.abs(Z[m]), Ew[m], 0.8)
    s_ = sig[np.searchsorted(edges, hl)]
    lo, hi = sg(zc - q * s_), sg(zc + q * s_)
    yy = sg(y)
    cov.append(float(np.average((yy >= lo) & (yy <= hi), weights=w)))
    wid.append(float(np.average(hi - lo, weights=w)) * 100)
    zs = rng.choice(Z[m], 200, p=Ew[m] / Ew[m].sum())
    crp.append(crps(sg(zc[None] + zs[:, None] * s_[None]), yy, w))
    if i % 60 == 0:
        print('kolo', i, flush=True)
praha = np.array([r['praha'] for r in races])
test = dict(vse=dict(crps=round(float(np.mean(crp)), 2), pokryti_80=round(float(np.mean(cov)) * 100, 1), sirka_80=round(float(np.mean(wid)), 1)),
            praha=dict(crps=round(float(np.mean(np.array(crp)[praha])), 2), pokryti_80=round(float(np.mean(np.array(cov)[praha])) * 100, 1), sirka_80=round(float(np.mean(np.array(wid)[praha])), 1)))
print('zpětný test konformní', test, flush=True)

# ---------------------------------------------------------------- 2026
rk26 = load(os.path.join(DL, 'SE2026reg20261011_csv'), 'serk')
t26 = load(os.path.join(DL, 'SE2026data20261011_csv'), 'set5')
g = rk26[rk26.OBVOD == OBVOD]
ca, cb = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0]), int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
t = t26[(t26.OBVOD == OBVOD) & (t26.KOLO == 1) & (t26.VOL_SEZNAM > 0)]
a1, b1 = t[f'HLASY_{ca:02d}'].fillna(0).values, t[f'HLASY_{cb:02d}'].fillna(0).values
n = np.c_[a1, b1, t.PL_HL_CELK.values - a1 - b1, t.VOL_SEZNAM.values - t.PL_HL_CELK.values].astype(float)
zc, hl = stred(n, Ball)
s_ = sig[np.searchsorted(edges, hl)]
q = wquant(np.abs(Z), Ew, 0.8)
zs = rng.choice(Z, 4000, p=Ew / Ew.sum())
P = sg(zc[None] + zs[:, None] * s_[None]) * 100
okr = [dict(okrsek=int(o), mc=MC.get(int(b), str(b)), sablik=round(float(sg(zc[j]) * 100), 1), p10=round(float(sg(zc[j] - q * s_[j]) * 100), 1),
            p90=round(float(sg(zc[j] + q * s_[j]) * 100), 1), p=round(float((P[:, j] > 50).mean() * 100), 0))
       for j, (o, b) in enumerate(zip(t.OKRSEK.values, t.OBEC.values))]
json.dump(dict(test=test, q80=round(float(q), 3), sigma=[round(float(x), 3) for x in sig], okrsky=okr), open(OUTJ, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('P5 Sáblík vede (střed):', sum(o['sablik'] > 50 for o in okr if o['mc'] == 'Praha 5'), flush=True)
