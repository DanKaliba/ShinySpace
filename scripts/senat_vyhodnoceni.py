"""Vyhodnocení předpovědi 2. kola Senátu v obvodu 21 (Láska × Sáblík) po skutečném výsledku 16.–17. 10. 2026.

python -P scripts/senat_vyhodnoceni.py <dl_dir> data        (spouštět po senat_bayes.py; data 2. kola v <dl_dir>/SE2026data20261017_csv)

Srovnává výslednou okrskovou předpověď (Bayes + obhajoba) a naivní odhad „jako 1. kolo“ (podíl Sáblíka mezi finalisty v 1. kole)
se skutečností: chyba, systematický posun, pokrytí 80% intervalů, správný vítěz okrsku, Brierovo skóre šance na výhru okrsku.
Do data['okrsky'] (Praha 5) doplní skutečný podíl Sáblíka a rozdíl předpovědi pro mapu.
"""
import sys, os, json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402
from senat_data import load  # noqa: E402
from ei import fit, bootstrap  # noqa: E402

DL, OUT = sys.argv[1:3]
OBVOD, LEAD, RUN = 21, 'Láska', 'Sáblík'
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
SO, SP = data['senat_okrsky'], data['senat_predikce']
rk = load(os.path.join(DL, 'SE2026reg20261017_csv'), 'serk')
g = rk[rk.OBVOD == OBVOD]
ca, cb = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0]), int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
t = load(os.path.join(DL, 'SE2026data20261017_csv'), 'set5')
t1 = t[(t.OBVOD == OBVOD) & (t.KOLO == 1)].set_index('OKRSEK')
t2 = t[(t.OBVOD == OBVOD) & (t.KOLO == 2)].set_index('OKRSEK')
ctv = {o['okrsek']: o['ctvrt'] for o in data['okrsky']}

rows = []
for o in SO['okrsky']:
    k = o['okrsek']
    if k not in t2.index:
        continue
    r = t2.loc[k]
    a, b = float(r[f'HLASY_{ca:02d}']), float(r[f'HLASY_{cb:02d}'])
    if a + b == 0:
        continue
    r1 = t1.loc[k]
    rows.append(dict(okrsek=int(k), mc='Praha 5' if o['p5'] else 'Praha 13', ctvrt=ctv.get(k, ''), laska=int(a), sablik_hlasy=int(b), hlasu=int(a + b),
                     skutecnost=round(b / (a + b) * 100, 2), ucast=round(float(r.ODEVZ_OBAL / r.VOL_SEZNAM * 100), 2),
                     predpoved=o['sablik'], p10=o['sablik_p10'], p90=o['sablik_p90'], p=o['p_sablik_vyhraje'], ucast_pred=o['ucast'], k1=o['k1_sablik_ze_dvou'],
                     sarapatka_k1=round(float(r1.HLASY_02 / r1.PL_HL_CELK * 100), 2), broz_k1=round(float(r1.HLASY_01 / r1.PL_HL_CELK * 100), 2)))
R = pd.DataFrame(rows)
R['chyba'] = R.predpoved - R.skutecnost


def hodnot(X, col, p=None, lo=None, hi=None):
    e = X[col] - X.skutecnost
    out = dict(okrsku=len(X), mae=round(float(e.abs().mean()), 2), posun=round(float(np.average(e, weights=X.hlasu)), 2),
               r=round(float(X[col].corr(X.skutecnost)), 3), vitez_ok=round(float(((X[col] > 50) == (X.skutecnost > 50)).mean()) * 100, 1))
    if p:
        out['brier'] = round(float(((X[p] / 100 - (X.skutecnost > 50)) ** 2).mean()), 3)
    if lo:
        out['pokryti_80'] = round(float(((X.skutecnost >= X[lo]) & (X.skutecnost <= X[hi])).mean()) * 100, 1)
    return out


celk = {}
for nazev, X in (('vse', R), ('praha5', R[R.mc == 'Praha 5']), ('praha13', R[R.mc == 'Praha 13'])):
    celk[nazev] = dict(model=hodnot(X, 'predpoved', 'p', 'p10', 'p90'), naivni=hodnot(X, 'k1'))
# skutečné přesuny voličů mezi koly (Goodmanova regrese s omezeními po okrscích obvodu, bootstrap 200×)
m = t1.reset_index().merge(t2.reset_index(), on=['OBEC', 'OKRSEK'], suffixes=('_1', '_2'))
m = m[(m.VOL_SEZNAM_1 >= 50) & (m.VOL_SEZNAM_2 >= 50)]
r1, r2 = m.VOL_SEZNAM_1.astype(float).values, m.VOL_SEZNAM_2.astype(float).values
sar, bro = 2, 1  # Šarapatka, Brož (číslo kandidáta)
G = {LEAD: m[f'HLASY_{ca:02d}_1'], RUN: m[f'HLASY_{cb:02d}_1'], 'Šarapatka': m[f'HLASY_{sar:02d}_1'], 'Brož (ANO)': m[f'HLASY_{bro:02d}_1']}
G['Ostatní (SPD, KSČM, Přísaha)'] = m.PL_HL_CELK_1 - sum(G.values())
G['Nevoliči'] = m.VOL_SEZNAM_1 - m.PL_HL_CELK_1
Xk = np.column_stack([v.astype(float).values for v in G.values()]) / r1[:, None]
a2, b2 = m[f'HLASY_{ca:02d}_2'].astype(float).values, m[f'HLASY_{cb:02d}_2'].astype(float).values
Yk = np.c_[a2, b2, r2 - a2 - b2] / r2[:, None]
Bk = fit(Xk, Yk, r1)
bo = bootstrap(Xk, Yk, r1, np.random.default_rng(2026), n=200)
K2 = [LEAD, RUN, 'Nevoliči']
presuny = dict(kategorie_k1=list(G), kategorie_k2=K2, velikost={k: int(v.sum()) for k, v in G.items()}, okrsku=int(len(m)),
               matice=[[round(float(x), 4) for x in r] for r in Bk],
               p05=[[round(float(x), 4) for x in r] for r in np.percentile(bo, 5, axis=0)], p95=[[round(float(x), 4) for x in r] for r in np.percentile(bo, 95, axis=0)])
A, B = int(R.laska.sum()), int(R.sablik_hlasy.sum())
k1_obvod = SP['k1']['sablik'] / (SP['k1']['laska'] + SP['k1']['sablik']) * 100
X_ = np.c_[np.ones(len(R)), R.sarapatka_k1, R.broz_k1]
b_, *_ = np.linalg.lstsq(X_, R.skutecnost - R.k1, rcond=None)
data['senat_vysledek'] = dict(
    laska=A, sablik=B, sablik_pct=round(B / (A + B) * 100, 2), ucast=round(float(t2.ODEVZ_OBAL.sum() / t2.VOL_SEZNAM.sum() * 100), 2),
    k1_sablik_ze_dvou=round(k1_obvod, 2), predpoved=dict(obvod=SO['obvod_sablik'], p_a1=SP['obhajoba']['model_a1']['p'], p_a=SP['model_a']['p'], p_b=SP['model_b']['p'],
                                                         ucast=SP['model_b']['ucast_median']),
    okrsky_hodnoceni=celk,
    sablik_vyhral=dict(praha5=int(((R.mc == 'Praha 5') & (R.skutecnost > 50)).sum()), praha13=int(((R.mc == 'Praha 13') & (R.skutecnost > 50)).sum())),
    predpoved_vede=dict(praha5=int(((R.mc == 'Praha 5') & (R.predpoved > 50)).sum()), praha13=int(((R.mc == 'Praha 13') & (R.predpoved > 50)).sum())),
    posun_ctvrti=R[R.mc == 'Praha 5'].groupby('ctvrt').apply(lambda x: round(float(np.average(x.chyba, weights=x.hlasu)), 2)).sort_values().to_dict(),
    zisk_vypadli=dict(sarapatka=round(float(b_[1]), 2), broz=round(float(b_[2]), 2), r_chyba_sarapatka=round(float(R.chyba.corr(R.sarapatka_k1)), 2)),
    ucast_posun=round(float((R.ucast_pred - R.ucast).mean()), 2),
    presuny=presuny,
    okrsky=R.round(2).to_dict('records'))
by = R.set_index('okrsek')
for o in data['okrsky']:
    if o['okrsek'] in by.index:
        o['senat_k2_skutecnost'] = float(by.loc[o['okrsek'], 'skutecnost'])
        o['senat_k2_rozdil'] = round(float(by.loc[o['okrsek'], 'chyba']), 2)
save(data, os.path.join(OUT, 'data.json'))
V = data['senat_vysledek']
print({k: v for k, v in V.items() if k not in ('okrsky', 'okrsky_hodnoceni')})
print(json.dumps(V['okrsky_hodnoceni'], ensure_ascii=False))
for k, r in zip(presuny['kategorie_k1'], presuny['matice']):
    print(f'  {k:30s}', [round(x * 100, 1) for x in r], presuny['velikost'][k])
