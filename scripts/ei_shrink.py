"""Přesuny voličů se smrštěním k neutrálnímu výchozímu bodu (místo krajních 0 % a 100 % Goodmanova odhadu).

python -P scripts/ei_shrink.py <dl_dir> data [--jen-citlivost]

Pro tři pohledy Sankey diagramu (Praha 5 KV 2022 → 2026, Praha magistrát 2022 → 2026, Praha 5 PS 2025 → KV 2026):
- síla smrštění λ se volí 5násobnou křížovou validací přes okrsky (2 opakování),
- výchozí bod B0 = „bez informace“: každá kategorie se rozdělí podle celkového složení cílových voleb,
- intervaly bootstrapem okrsků se zvoleným λ.
Výsledek se zapíše do data.json (rozsireni.sankey_* a doplneni.ps25_kv26.p5 → klíče matice_shrink, lambda, …).
Spouštět po doplneni.py.
"""
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ei import fit, fit_shrink, neutral_prior, cv_lambda, bootstrap  # noqa: E402
from kvdata import Data, composition, stable, P5, MAG, MC22, MC26, MAGB, PSB  # noqa: E402

DL, OUT = sys.argv[1:3]
JEN_CITLIVOST = '--jen-citlivost' in sys.argv
rng = np.random.default_rng(2026)
D = Data(DL)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
GRID = [0, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3]


def citlivost(X, Y, w, cverr):
    """Jak se mění odchody k nevoličům při mírném smrštění (CV chyba horší o méně než 5 % a 15 %)."""
    best = min(cverr.values())
    out = []
    for lam in (0.003, 0.01):
        B = fit_shrink(X.values, Y.values, w, lam, neutral_prior(X.values, Y.values, w))
        jn, ip = list(Y.columns).index('Nevoliči'), list(X.columns).index('Piráti')
        out.append(dict(lam=lam, cv_horsi_o=round((cverr[str(lam)] / best - 1) * 100, 1),
                        do_nevolicu={c: round(float(B[i, jn]) * 100, 1) for i, c in enumerate(X.columns) if c != 'Nevoliči'},
                        pirati={c: round(float(B[ip, j]) * 100, 1) for j, c in enumerate(Y.columns)}))
    return out


def run(name, X, Y, w, size_rows, nboot, prev=None):
    if JEN_CITLIVOST and prev and 'cv_chyba' in prev:
        return dict(citlivost=citlivost(X, Y, w, prev['cv_chyba']))
    lam, cverr = cv_lambda(X.values, Y.values, w, GRID, rng)
    B0 = neutral_prior(X.values, Y.values, w)
    Bg = fit(X.values, Y.values, w)
    Bs = fit_shrink(X.values, Y.values, w, lam, B0) if lam > 0 else Bg
    bo = bootstrap(X.values, Y.values, w, rng, n=nboot, lam=lam if lam > 0 else None, B0=B0)
    rows, cols = list(X.columns), list(Y.columns)
    ip = rows.index('Piráti')
    res = dict(
        lambda_=lam, cv_chyba=cverr, okrsku=len(X),
        matice_shrink=[[round(float(v), 4) for v in r] for r in Bs],
        pirati_kam_shrink=sorted([dict(kam=c, pct=round(float(Bs[ip, j]) * 100, 1), p05=round(float(np.percentile(bo[:, ip, j], 5)) * 100, 1),
                                       p95=round(float(np.percentile(bo[:, ip, j], 95)) * 100, 1), goodman=round(float(Bg[ip, j]) * 100, 1),
                                       volicu=int(Bs[ip, j] * size_rows['Piráti'])) for j, c in enumerate(cols)], key=lambda d: -d['pct']),
    )
    res['citlivost'] = citlivost(X, Y, w, cverr)
    if 'Nevoliči' in cols:
        jn = cols.index('Nevoliči')
        res['do_nevolicu_shrink'] = {r: round(float(Bs[i, jn]) * 100, 1) for i, r in enumerate(rows) if r != 'Nevoliči'}
        res['do_nevolicu_goodman'] = {r: round(float(Bg[i, jn]) * 100, 1) for i, r in enumerate(rows) if r != 'Nevoliči'}
    print(name, 'λ =', lam, '| Piráti →', [(d['kam'], d['pct'], d['goodman']) for d in res['pirati_kam_shrink']])
    if 'do_nevolicu_shrink' in res:
        print('   do nevoličů (shrink):', res['do_nevolicu_shrink'])
    return res


# 1) Praha 5, zastupitelstvo MČ 2022 → 2026
v22, t22 = D.bloc_votes(2022, P5, MC22, obec=P5)
v26, t26 = D.bloc_votes(2026, P5, MC26, obec=P5)
k5 = [k for k in v22.index.intersection(v26.index) if k[1] != 5008]
X, Y = composition(v22, t22, k5), composition(v26, t26, k5)
r1 = run('P5 KV', X, Y, t22.VOL_SEZNAM.loc[k5].values.astype(float), X.mul(t22.VOL_SEZNAM.loc[k5], axis=0).sum(), 200, data['rozsireni']['sankey_p5'])
data['rozsireni']['sankey_p5'].update(r1)

# 2) Praha, magistrát 2022 → 2026
m22, s22 = D.bloc_votes(2022, MAG, MAGB)
m26, s26 = D.bloc_votes(2026, MAG, MAGB)
kp = stable(s22, s26)
Xp, Yp = composition(m22, s22, kp), composition(m26, s26, kp)
r2 = run('Praha mag', Xp, Yp, s22.VOL_SEZNAM.loc[kp].values.astype(float), Xp.mul(s22.VOL_SEZNAM.loc[kp], axis=0).sum(), 60, data['rozsireni']['sankey_praha'])
data['rozsireni']['sankey_praha'].update(r2)

# 3) Praha 5, PS 2025 → MČ 2026
vps, tps = D.ps_votes(PSB, obec=P5)
kq = [k for k in stable(tps, t26).intersection(vps.index) if k[1] != 5008]
Xq, Yq = composition(vps, tps, kq), composition(v26, t26, kq)
r3 = run('P5 PS→KV', Xq, Yq, tps.VOL_SEZNAM.loc[kq].values.astype(float), Xq.mul(tps.VOL_SEZNAM.loc[kq], axis=0).sum(), 200, data['doplneni']['ps25_kv26']['p5'])
r3.update(kategorie_ps=list(Xq.columns), kategorie_kv=list(Yq.columns))
data['doplneni']['ps25_kv26']['p5'].update(r3)

json.dump(data, open(os.path.join(OUT, 'data.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('OK')
