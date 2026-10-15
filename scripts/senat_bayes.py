"""Hierarchický bayesovský model 2. kola Senátu pro okrsky obvodu 21 (Praha 5 a část Prahy 13) a srovnání metod zpětným testem.

python -P scripts/senat_bayes.py <dl_dir> data        (spouštět po senat_okrsky.py – používá jeho mezipaměť minulých kol)

Model (jen numpy, Monte Carlo z prediktivního rozdělení):
  přesuny v obvodu   θ_r                          r = zdroj (vítěz 1. kola, druhý, ostatní kandidáti, nevoliči) → (vítěz, druhý, nepřišel)
  přesuny v okrsku   p_ir ~ Dirichlet(κ · θ_r)    okrsek se od obvodu odchyluje, κ = jak málo (vybráno zpětným testem)
  hlasy ve 2. kole   v_i = Σ_r n_ir · p_ir        n_ir = složení okrsku v 1. kole
Dvě varianty prioru pro θ (oba z matic přesunů minulých druhých kol 2008–2024):
  „nezávislý“  každý řádek θ_r ~ Dirichlet(α_r) zvlášť (α metodou momentů) – ignoruje, že řádky spolu v minulosti souvisely,
  „empirický“  θ = celá matice jednoho náhodného minulého kola – zachová vazby mezi řádky (např. vyšší účast obou finalistů naráz).
Před 2. kolem nejsou v obvodu žádná data o přesunech, informace o nich pochází jen z minulých kol; 1. kolo je známé složení okrsků.

Srovnání (každé minulé kolo bez sebe sama): CRPS podílu druhého finalisty v okrscích (nižší = lepší) a pokrytí 80% intervalů.
Stávající metoda = průměrná matice přesunů + posun na celkový výsledek podle jednoho minulého kola + chyba okrsku podle velikosti.
Podrobnosti pro interní report: <dl_dir>/../senat_2kolo/bayes_detail.json.
"""
import sys, os, json, pickle
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402
from senat_data import load  # noqa: E402

DL, OUT = sys.argv[1:3]
H = os.path.join(DL, 'senat_hist')
OBVOD, LEAD, RUN = 21, 'Láska', 'Sáblík'
MC = {500143: 'Praha 5', 539694: 'Praha 13'}
rng = np.random.default_rng(2026)
races = pickle.load(open(os.path.join(H, '_kola_okrsky.pkl'), 'rb'))
Ball = np.array([r['B'] for r in races])
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
SO = data['senat_okrsky']
sd_bin = np.array(SO['chyba_okrsku_sd_logit'])
allw = np.concatenate([(r['d'].a2 + r['d'].b2).values for r in races])
edges = np.quantile(allw, [.2, .4, .6, .8])
ZDROJ, CIL = ['voliči vítěze 1. kola', 'voliči druhého z 1. kola', 'voliči vypadlých kandidátů', 'nevoliči 1. kola'], ['vítěz 1. kola', 'druhý z 1. kola', 'nepřišel']


def lg(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def sg(z):
    return 1 / (1 + np.exp(-z))


def counts(d):
    return np.c_[d.a1, d.b1, d.c1, d.reg1 - d.valid1].astype(float)


def dir_mom(rows):
    rows = np.clip(np.asarray(rows, float), 1e-3, None)
    rows = rows / rows.sum(1, keepdims=True)
    m, v = rows.mean(0), rows.var(0, ddof=1)
    return m * max(np.median(m * (1 - m) / np.maximum(v, 1e-9) - 1), 0.5)


def theta_nezavisly(Bs, S):
    alpha = np.stack([dir_mom(Bs[:, k]) for k in range(4)])
    th = rng.gamma(np.broadcast_to(alpha, (S, 4, 3)))
    return th / th.sum(-1, keepdims=True)


def theta_empiricky(Bs, S):
    th = np.clip(Bs[rng.integers(0, len(Bs), S)], 1e-4, None)
    return th / th.sum(-1, keepdims=True)


def sim_bayes(n, theta, kappa):
    """n (I, 4) složení okrsků, theta (S, 4, 3); vrací podíl druhého finalisty a hlasy finalistů (S, I)."""
    g = rng.gamma(kappa * theta[:, None] + 1e-6, size=(theta.shape[0], n.shape[0], 4, 3))
    p = g / g.sum(-1, keepdims=True)
    v = np.einsum('ir,sirc->sic', n, p)
    return v[..., 1] / np.maximum(v[..., 0] + v[..., 1], 1e-9), v[..., 0] + v[..., 1]


def shift_to(z, w, target):
    lo, hi = -10.0, 10.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if np.average(sg(z + mid), weights=w) < target else (lo, mid)
    return z + (lo + hi) / 2


def sim_stavajici(n, Bs, S):
    v = n @ Bs.mean(0)
    hl = v[:, 0] + v[:, 1]
    z0 = lg(v[:, 1] / np.maximum(hl, 1e-9))
    sd = sd_bin[np.searchsorted(edges, hl)]
    tot = n.sum(0)
    out = []
    for k in rng.integers(0, len(Bs), S):
        vv = tot @ Bs[k]
        out.append(sg(shift_to(z0, hl, vv[1] / (vv[0] + vv[1])) + rng.normal(0, sd)))
    return np.array(out), np.broadcast_to(hl, (S, len(hl)))


def crps(sims, y, w):
    s, y = sims[:200] * 100, y * 100
    t1 = np.abs(s - y).mean(0)
    t2 = np.abs(s[:, None, :] - s[None, :, :]).mean((0, 1)) / 2
    return float(np.average(t1 - t2, weights=w))


def cover(sims, y, w):
    lo, hi = np.percentile(sims, 10, axis=0), np.percentile(sims, 90, axis=0)
    return float(np.average((y >= lo) & (y <= hi), weights=w))


# ---------------------------------------------------------------- zpětný test
KAPPAS = [30, 100, 300, 1000]
VAR = {'nezavisly': theta_nezavisly, 'empiricky': theta_empiricky}
S = 200
half = np.arange(len(races)) % 2
score = {(v, k): [] for v in VAR for k in KAPPAS}
base = []
for i, r in enumerate(races):
    d = r['d']
    n = counts(d)
    y = (d.b2 / (d.a2 + d.b2)).values
    w = (d.a2 + d.b2).values
    others = np.delete(Ball, i, axis=0)
    for v, thf in VAR.items():
        th = thf(others, S)
        for k in KAPPAS:
            sb, _ = sim_bayes(n, th, k)
            score[(v, k)].append((crps(sb, y, w), cover(sb, y, w)))
    ss, _ = sim_stavajici(n, others, S)
    base.append((crps(ss, y, w), cover(ss, y, w)))
    if i % 40 == 0:
        print('kolo', i, '/', len(races), flush=True)
praha = np.array([r['praha'] for r in races])


def summ(rows, mask=None):
    rr = [x for j, x in enumerate(rows) if mask is None or mask[j]]
    return dict(crps=round(float(np.mean([x[0] for x in rr])), 2), pokryti_80=round(float(np.mean([x[1] for x in rr])) * 100, 1), kol=len(rr))


best_k, cv = {}, {}
for v in VAR:  # κ vybrané na jedné polovině kol, hodnocené na druhé
    bk = {h: min(KAPPAS, key=lambda k: np.mean([score[(v, k)][j][0] for j in range(len(races)) if half[j] == h])) for h in (0, 1)}
    cv[v] = [score[(v, bk[1 - half[j]])][j] for j in range(len(races))]
    best_k[v] = min(KAPPAS, key=lambda k: np.mean([x[0] for x in score[(v, k)]]))
metody = {'stavajici': base, 'bayes_nezavisly': cv['nezavisly'], 'bayes_empiricky': cv['empiricky']}
test = {m: dict(vse=summ(rows), praha=summ(rows, praha)) for m, rows in metody.items()}
lepsi = min(test, key=lambda m: test[m]['vse']['crps'])
print('zpětný test', json.dumps(test, ensure_ascii=False), '| κ', best_k, '| lepší:', lepsi, flush=True)

# ---------------------------------------------------------------- 2026: celý obvod 21
rk26 = load(os.path.join(DL, 'SE2026reg20261011_csv'), 'serk')
t26 = load(os.path.join(DL, 'SE2026data20261011_csv'), 'set5')
g = rk26[rk26.OBVOD == OBVOD]
ca, cb = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0]), int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
t = t26[(t26.OBVOD == OBVOD) & (t26.KOLO == 1) & (t26.VOL_SEZNAM > 0)]
a1, b1 = t[f'HLASY_{ca:02d}'].fillna(0).values, t[f'HLASY_{cb:02d}'].fillna(0).values
n = np.c_[a1, b1, t.PL_HL_CELK.values - a1 - b1, t.VOL_SEZNAM.values - t.PL_HL_CELK.values].astype(float)
okr, obec = t.OKRSEK.values.astype(int), t.OBEC.values.astype(int)
def wq(x, w, q):
    """Vážený kvantil podél osy 0 (x: S nebo S×I, w: S)."""
    x = np.asarray(x, float)
    o = np.argsort(x, axis=0)
    xs = np.take_along_axis(x, o, 0)
    cw = np.cumsum(w[o], axis=0) / w.sum()
    k = np.minimum((cw < q).sum(0), len(w) - 1)
    return xs[k] if x.ndim == 1 else xs[k, np.arange(x.shape[1])]


def shrn(SH, VO, w=None):
    w = np.ones(len(SH)) if w is None else w
    ob = (SH * VO).sum(1) / VO.sum(1)
    P = SH * 100
    med, lo, hi = wq(P, w, .5), wq(P, w, .1), wq(P, w, .9)
    win = (w[:, None] * (P > 50)).sum(0) / w.sum()
    uc = wq(VO / n.sum(1)[None] * 100, w, .5)
    return dict(p_obvod=round(float((w * (ob > 0.5)).sum() / w.sum() * 100), 1),
                obvod=dict(median=round(float(wq(ob, w, .5)) * 100, 1), p10=round(float(wq(ob, w, .1)) * 100, 1), p90=round(float(wq(ob, w, .9)) * 100, 1)),
                hist=np.histogram(ob * 100, bins=np.arange(20, 72, 2), weights=w / w.mean())[0].round().astype(int).tolist(),
                okrsky={int(o): dict(sablik=round(float(med[j]), 1), p10=round(float(lo[j]), 1), p90=round(float(hi[j]), 1),
                                     p=round(float(win[j] * 100), 0), ucast=round(float(uc[j]), 1)) for j, o in enumerate(okr)})


vysl, SIM = {}, {}
for m in metody:
    if m == 'stavajici':
        sims = [sim_stavajici(n, Ball, 400) for _ in range(10)]
    else:
        v = m.split('_')[1]
        sims = [sim_bayes(n, VAR[v](Ball, 400), best_k[v]) for _ in range(10)]
    SIM[m] = (np.vstack([s[0] for s in sims]), np.vstack([s[1] for s in sims]))
    vysl[m] = shrn(*SIM[m])
    print(m, 'P(Sáblík vyhraje obvod) =', vysl[m]['p_obvod'], '% | obvod medián', vysl[m]['obvod']['median'], flush=True)
# empirický prior převážený na model A1 (náskok + obhajoba mandátu): simulace, ve kterých Sáblík vyhraje obvod,
# dostanou takovou váhu, aby jejich podíl odpovídal pravděpodobnosti z A1; rozložení mezi okrsky a vazby mezi nimi zůstanou
pA1 = data['senat_predikce']['obhajoba']['model_a1']['p'] / 100
SH, VO = SIM['bayes_empiricky']
won = ((SH * VO).sum(1) / VO.sum(1)) > 0.5
p0 = won.mean()
wA1 = np.where(won, pA1 / p0, (1 - pA1) / (1 - p0))
vysl['bayes_empiricky_a1'] = shrn(SH, VO, wA1)
print('bayes_empiricky_a1 P(Sáblík vyhraje obvod) =', vysl['bayes_empiricky_a1']['p_obvod'], '% | obvod medián', vysl['bayes_empiricky_a1']['obvod']['median'], flush=True)
FINAL = 'bayes_empiricky_a1'

ctv = {o['okrsek']: o['ctvrt'] for o in data['okrsky']}
th = theta_nezavisly(Ball, 4000)
prior_detail = [dict(zdroj=ZDROJ[r], **{CIL[c]: dict(nezavisly=dict(prumer=round(float(th[:, r, c].mean()) * 100, 1), p05=round(float(np.percentile(th[:, r, c], 5)) * 100, 1), p95=round(float(np.percentile(th[:, r, c], 95)) * 100, 1)),
                                                 empiricky=dict(prumer=round(float(Ball[:, r, c].mean()) * 100, 1), p05=round(float(np.percentile(Ball[:, r, c], 5)) * 100, 1), p95=round(float(np.percentile(Ball[:, r, c], 95)) * 100, 1)))
                                     for c in range(3)}) for r in range(4)]
# vazba mezi řádky v minulých kolech (proč na nezávislém prioru záleží): korelace účasti voličů obou finalistů
kor = float(np.corrcoef(1 - Ball[:, 0, 2], 1 - Ball[:, 1, 2])[0, 1])
DET = os.path.join(DL, '..', 'senat_2kolo')
os.makedirs(DET, exist_ok=True)
json.dump(dict(vytvoreno='2026-10-15', kappa=best_k, test=test, lepsi=lepsi, finalni=FINAL, p_a1=round(pA1 * 100, 1), overeni_obvod=data['senat_predikce']['obhajoba']['overeni'], obhajoba_skupiny=data['senat_predikce']['obhajoba']['skupiny'], model_a1=data['senat_predikce']['obhajoba']['model_a1'], prior=prior_detail, korelace_ucasti_finalistu=round(kor, 2),
               kappa_detail=[dict(varianta=v, kappa=k, crps=round(float(np.mean([x[0] for x in score[(v, k)]])), 3), pokryti_80=round(float(np.mean([x[1] for x in score[(v, k)]])) * 100, 1)) for v in VAR for k in KAPPAS],
               kola=[dict(rok=int(r['rok']), obvod=int(r['obvod']), praha=bool(r['praha']), okrsku=len(r['d']),
                          **{f'crps_{m}': round(metody[m][i][0], 3) for m in metody}, **{f'pokryti_{m}': round(metody[m][i][1] * 100, 1) for m in metody}) for i, r in enumerate(races)],
               p_obvod_modelA=data['senat_predikce']['model_a']['p'], p_obvod_modelB=data['senat_predikce']['model_b']['p'],
               obvod={m: {k: vysl[m][k] for k in ('p_obvod', 'obvod', 'hist')} for m in vysl}, hist_od=20, hist_krok=2,
               okrsky=[dict(okrsek=int(o), mc=MC.get(int(b), str(b)), ctvrt=ctv.get(int(o), ''), k1=dict(laska=int(n[j, 0]), sablik=int(n[j, 1]), ostatni=int(n[j, 2]), zapsanych=int(n[j].sum())),
                            k1_ze_dvou=round(float(n[j, 1] / max(n[j, 0] + n[j, 1], 1) * 100), 1), **{m: vysl[m]['okrsky'][int(o)] for m in vysl}) for j, (o, b) in enumerate(zip(okr, obec))]),
          open(os.path.join(DET, 'bayes_detail.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- web: předpověď okrsků z metody s nejlepším CRPS
SO['bayes'] = dict(test=test, lepsi=lepsi, finalni=FINAL, p_a1=round(pA1 * 100, 1), kappa=best_k, p_obvod={m: vysl[m]['p_obvod'] for m in vysl}, obvod={m: vysl[m]['obvod'] for m in vysl})
best = vysl[FINAL]['okrsky']
for r in SO['okrsky']:
    if r['okrsek'] in best:
        b = best[r['okrsek']]
        r.update(sablik=b['sablik'], sablik_p10=b['p10'], sablik_p90=b['p90'], p_sablik_vyhraje=b['p'], ucast=b['ucast'], mc=MC.get(r['obec'], str(r['obec'])))
SO['metoda_okrsky'] = FINAL
SO['obvod_sablik'] = vysl[FINAL]['obvod']
for o in data['okrsky']:
    if o['okrsek'] in best:
        o['senat_k2_sablik'], o['senat_k2_p'] = best[o['okrsek']]['sablik'], best[o['okrsek']]['p']
save(data, os.path.join(OUT, 'data.json'))
