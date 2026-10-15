"""Předpověď 2. kola Senátu v obvodu 21 (Láska × Sáblík) ze dvou modelů nad historickými druhými koly 2008–2024.

python -P scripts/senat_predikce.py <dl_dir> data        (data v <dl_dir>/senat_hist/<rok>, viz download.sh)

A) Historický model: logistická regrese „vyhrál druhý z 1. kola“ ~ náskok vítěze 1. kola (p. b.), všechna druhá kola v ČR.
B) Model přesunů voličů: pro každé minulé druhé kolo ekologická inference po okrscích (kolo 1 → kolo 2):
   kolik voličů obou finalistů přišlo znovu, kam šli voliči vypadlých kandidátů a kolik nevoličů se zapojilo.
   Každý z těchto vzorců se použije na výsledek 1. kola v obvodu 21; podíl vzorců, se kterými vyhraje Sáblík, je pravděpodobnost.
Oba modely se ověřují zpětně (každé minulé druhé kolo se předpoví bez sebe sama).
Model nezná kandidáty ani doporučení vypadlých kandidátů – jen to, jak se druhá kola v ČR obvykle vyvíjejí.
"""
import sys, os, json, re, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ei import fit  # noqa: E402
from jsonio import save  # noqa: E402
from senat_data import YEARS, PRAHA, load, hl  # noqa: E402

DL, OUT = sys.argv[1:3]
H = os.path.join(DL, 'senat_hist')
OBVOD, LEAD, RUN = 21, 'Láska', 'Sáblík'
# obhájce mandátu: „senátor/ka“ v povolání (zachytí i zvolené v doplňovacích volbách) nebo vítěz téhož obvodu před 6 lety
RX_SEN = re.compile(r'\bsenátor(ka)?\b|předsed\w* senátu|místopředsed\w* senátu', re.I)
VITEZ = {}  # (obvod, rok) -> jméno vítěze
OBH_VSE = []  # (rok, obvod, vyhrál v 1. kole, postoupil, vyhrál ve 2. kole) pro každého obhájce


def obhajce(c, ob, y):
    return bool(RX_SEN.search(str(c.POVOLANI))) or VITEZ.get((ob, y - 6)) == f'{c.JMENO} {c.PRIJMENI}'.lower()


def matrix(t5, obvod, a, b):
    """Okrskové složení kol 1 a 2 (podíly zapsaných voličů) pro finalisty a (vítěz 1. kola) a b."""
    t = t5[t5.OBVOD == obvod]
    k = ['OBEC', 'OKRSEK']
    m = t[t.KOLO == 1].merge(t[t.KOLO == 2], on=k, suffixes=('_1', '_2'))
    m = m[(m.VOL_SEZNAM_1 >= 50) & (m.VOL_SEZNAM_2 >= 50)]
    r1 = m.VOL_SEZNAM_1.astype(float)
    a1 = m[f'HLASY_{a:02d}_1'].fillna(0)
    b1 = m[f'HLASY_{b:02d}_1'].fillna(0)
    c1 = m.PL_HL_CELK_1 - a1 - b1
    X = np.c_[a1, b1, c1, r1 - m.PL_HL_CELK_1] / r1.values[:, None]
    r2 = m.VOL_SEZNAM_2.astype(float)
    a2, b2 = m[f'HLASY_{a:02d}_2'].fillna(0), m[f'HLASY_{b:02d}_2'].fillna(0)
    Y = np.c_[a2, b2, r2 - a2 - b2] / r2.values[:, None]
    return X, Y, r1.values


# ---------------------------------------------------------------- historická druhá kola
races = []
for y in YEARS:
    base = os.path.join(H, str(y))
    rk, t5 = load(base, 'serk'), load(base, 'set5')
    for ob, g in rk.groupby('OBVOD'):
        z = g[(g.ZVOLEN_K1.fillna(0) == 1) | (g.ZVOLEN_K2.fillna(0) == 1)]  # 1 = zvolen, 2 = postup do 2. kola
        if len(z):
            VITEZ[(int(ob), y)] = f'{z.iloc[0].JMENO} {z.iloc[0].PRIJMENI}'.lower()
        for c in g.itertuples():
            if obhajce(c, int(ob), y):
                OBH_VSE.append((y, int(ob), c.ZVOLEN_K1 == 1, c.ZVOLEN_K1 == 2, c.ZVOLEN_K2 == 1))
        f = g[g.HLASY_K2.fillna(0) > 0]
        if len(f) != 2:
            continue
        f = f.sort_values('HLASY_K1', ascending=False)
        a, b = f.iloc[0], f.iloc[1]
        tot1 = g.HLASY_K1.sum()
        X, Y, w = matrix(t5, ob, int(a.CKAND), int(b.CKAND))
        if len(X) < 20:
            continue
        B = fit(X, Y, w, iters=3000)
        t1 = t5[(t5.OBVOD == ob) & (t5.KOLO == 1)]
        a1, b1 = float(hl(t1, a.CKAND).sum()), float(hl(t1, b.CKAND).sum())
        x1 = np.array([a1, b1, float(t1.PL_HL_CELK.sum()) - a1 - b1, float((t1.VOL_SEZNAM - t1.PL_HL_CELK).sum())])
        races.append(dict(rok=y, obvod=int(ob), praha=int(ob) in PRAHA,
                          vitez_k1=f'{a.JMENO} {a.PRIJMENI}', druhy_k1=f'{b.JMENO} {b.PRIJMENI}',
                          a_pct=round(float(a.HLASY_K1 / tot1 * 100), 2), b_pct=round(float(b.HLASY_K1 / tot1 * 100), 2),
                          ostatni_pct=round(float((tot1 - a.HLASY_K1 - b.HLASY_K1) / tot1 * 100), 2),
                          a_k2=int(a.HLASY_K2), b_k2=int(b.HLASY_K2), druhy_vyhral=bool(b.HLASY_K2 > a.HLASY_K2),
                          okrsku=len(X), B=B, x1=x1, obh_a=obhajce(a, int(ob), y), obh_b=obhajce(b, int(ob), y)))
R = pd.DataFrame(races)
R['naskok'] = R.a_pct - R.b_pct
print('druhých kol', len(R), 'z toho Praha', int(R.praha.sum()), '| druhý z 1. kola vyhrál', int(R.druhy_vyhral.sum()))


# ---------------------------------------------------------------- A) logistická regrese
def logit_fit(x, y, iters=50):
    Xd = np.c_[np.ones(len(x)), x]
    beta = np.zeros(Xd.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xd @ beta))
        W = p * (1 - p) + 1e-9
        beta += np.linalg.solve(Xd.T @ (Xd * W[:, None]), Xd.T @ (y - p))
    return beta


def logit_p(beta, x):
    x = np.asarray(x, float)
    return 1 / (1 + np.exp(-(beta[0] + (x @ beta[1:] if len(beta) > 2 else beta[1] * x))))


# ---------------------------------------------------------------- obvod 21, 1. kolo 2026
rk26 = load(os.path.join(DL, 'SE2026reg20261011_csv'), 'serk')
t26 = load(os.path.join(DL, 'SE2026data20261011_csv'), 'set5')
g = rk26[rk26.OBVOD == OBVOD]
ca = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0])
cb = int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
t = t26[(t26.OBVOD == OBVOD) & (t26.KOLO == 1)]
A1, B1 = float(hl(t, ca).sum()), float(hl(t, cb).sum())
reg, valid = float(t.VOL_SEZNAM.sum()), float(t.PL_HL_CELK.sum())
x21 = np.array([A1, B1, valid - A1 - B1, reg - valid])
naskok = (A1 - B1) / valid * 100
print(f'obvod 21: {LEAD} {A1:.0f}, {RUN} {B1:.0f}, náskok {naskok:.2f} p. b., zapsaných {reg:.0f}')

rng = np.random.default_rng(2026)
x, yv = R.naskok.values, R.druhy_vyhral.values.astype(float)
beta = logit_fit(x, yv)
pA = float(logit_p(beta, naskok))
boot = []
for _ in range(2000):
    ix = rng.integers(0, len(R), len(R))
    boot.append(float(logit_p(logit_fit(x[ix], yv[ix]), naskok)))
pA_lo, pA_hi = np.percentile(boot, [5, 95])
loo_A = np.array([logit_p(logit_fit(np.delete(x, i), np.delete(yv, i)), x[i]) for i in range(len(R))])
pod = R[(R.naskok >= naskok - 3) & (R.naskok <= naskok + 3)]
print(f'A: P({RUN}) = {pA:.3f} (90% {pA_lo:.3f}–{pA_hi:.3f}); podobný náskok ±3 p. b.: {int(pod.druhy_vyhral.sum())}/{len(pod)}')


# ---------------------------------------------------------------- B) model přesunů voličů (analogie minulých druhých kol)
def apply(B, xv):
    v = xv @ B
    return v[0], v[1]


sim = []
for r in races:
    a2, b2 = apply(r['B'], x21)
    sim.append(dict(rok=r['rok'], obvod=r['obvod'], praha=r['praha'], laska=a2, sablik=b2,
                    rozdil_pct=(b2 - a2) / (a2 + b2) * 100, ucast=(a2 + b2) / reg * 100))
S = pd.DataFrame(sim)
# bod zvratu: jaký podíl voličů vypadlých kandidátů, kteří ve 2. kole přijdou, musí dostat Sáblík (ostatní toky podle daného kola)
f_need = []
for r in races:
    Bm = r['B']
    fa = x21[0] * Bm[0, 0] + x21[1] * Bm[1, 0] + x21[3] * Bm[3, 0]
    fb = x21[0] * Bm[0, 1] + x21[1] * Bm[1, 1] + x21[3] * Bm[3, 1]
    c = x21[2] * (Bm[2, 0] + Bm[2, 1])
    f_need.append((fa - fb + c) / (2 * c) if c > 0 else np.nan)
f_need = np.array(f_need)
pB = float((S.sablik > S.laska).mean())
pB_praha = float((S[S.praha].sablik > S[S.praha].laska).mean())
# zpětné ověření B: každé druhé kolo předpovězeno vzorci ostatních kol z jeho skutečného 1. kola
loo_B = []
for i, r in enumerate(races):
    votes = [apply(o['B'], r['x1']) for j, o in enumerate(races) if j != i]
    loo_B.append(float(np.mean([b > a for a, b in votes])))
loo_B = np.array(loo_B)


def score(p):
    return dict(brier=round(float(np.mean((p - yv) ** 2)), 4), presnost=round(float(np.mean((p > 0.5) == (yv == 1)) * 100), 1))


base_rate = float(yv.mean())

# ---------------------------------------------------------------- obhajoba mandátu (A1: náskok + obhájce vítěz / druhý; B: jen kola se stejnou situací)
oa, ob_ = R.obh_a.values.astype(float), R.obh_b.values.astype(float)
X1 = np.c_[x, oa, ob_]
o21a = obhajce(g[g.PRIJMENI == LEAD].iloc[0], OBVOD, 2026)
o21b = obhajce(g[g.PRIJMENI == RUN].iloc[0], OBVOD, 2026)
x21_1 = np.array([naskok, float(o21a), float(o21b)])
beta1 = logit_fit(X1, yv)
Xd1 = np.c_[np.ones(len(X1)), X1]
pp1 = 1 / (1 + np.exp(-Xd1 @ beta1))
se1 = np.sqrt(np.diag(np.linalg.inv(Xd1.T @ (Xd1 * (pp1 * (1 - pp1))[:, None]))))
pval1 = [math.erfc(abs(b_ / s_) / math.sqrt(2)) for b_, s_ in zip(beta1, se1)]
pA1 = float(logit_p(beta1, x21_1[None])[0])
boot1 = []
for _ in range(2000):
    ix = rng.integers(0, len(R), len(R))
    boot1.append(float(logit_p(logit_fit(X1[ix], yv[ix]), x21_1[None])[0]))
loo_A1 = np.array([logit_p(logit_fit(np.delete(X1, i, 0), np.delete(yv, i)), X1[i][None])[0] for i in range(len(R))])
# stejná situace jako obvod 21 (vítěz 1. kola obhajuje, druhý ne)
same = (oa == o21a) & (ob_ == o21b)
pB_obh = float((S[same].sablik > S[same].laska).mean())
loo_B1 = []
for i, r in enumerate(races):
    m = [j for j in range(len(races)) if j != i and oa[j] == oa[i] and ob_[j] == ob_[i]]
    m = m if len(m) >= 10 else [j for j in range(len(races)) if j != i]
    loo_B1.append(float(np.mean([b > a for a, b in (apply(races[j]['B'], r['x1']) for j in m)])))
loo_B1 = np.array(loo_B1)
ll = lambda p: round(float(-np.mean(yv * np.log(np.clip(p, 1e-6, 1)) + (1 - yv) * np.log(np.clip(1 - p, 1e-6, 1)))), 4)
skup = []
for (a_, b_), nm in (((1, 0), 'vítěz 1. kola obhajuje'), ((0, 1), 'druhý z 1. kola obhajuje'), ((0, 0), 'nikdo neobhajuje'), ((1, 1), 'oba senátoři')):
    mm = (oa == a_) & (ob_ == b_)
    skup.append(dict(situace=nm, kol=int(mm.sum()), druhy_vyhral=int(yv[mm].sum()), pct=round(float(yv[mm].mean()) * 100, 1) if mm.any() else None,
                     naskok_median=round(float(np.median(x[mm])), 1) if mm.any() else None))
obhajoba = dict(laska_obhajuje=bool(o21a), sablik_obhajuje=bool(o21b), skupiny=skup,
                model_a1=dict(p=round(pA1 * 100, 1), p05=round(float(np.percentile(boot1, 5)) * 100, 1), p95=round(float(np.percentile(boot1, 95)) * 100, 1),
                              beta=dict(zip(['konstanta', 'naskok', 'obhajce_vitez', 'obhajce_druhy'], [round(float(b_), 3) for b_ in beta1])),
                              se=dict(zip(['konstanta', 'naskok', 'obhajce_vitez', 'obhajce_druhy'], [round(float(s_), 3) for s_ in se1])),
                              p_hodnota=dict(zip(['konstanta', 'naskok', 'obhajce_vitez', 'obhajce_druhy'], [round(float(q), 4) for q in pval1]))),
                obhajci_celkem=dict(kandidovalo=len(OBH_VSE), vyhrali_v_1_kole=int(sum(o[2] for o in OBH_VSE)), ve_2_kole=int(sum(o[3] for o in OBH_VSE)),
                                    vyhrali_ve_2_kole=int(sum(o[3] and o[4] for o in OBH_VSE))),
                model_b1=dict(p=round(pB_obh * 100, 1), kol=int(same.sum())),
                overeni={'A': dict(brier=round(float(np.mean((loo_A - yv) ** 2)), 4), logloss=ll(loo_A)),
                         'A1': dict(brier=round(float(np.mean((loo_A1 - yv) ** 2)), 4), logloss=ll(loo_A1)),
                         'B': dict(brier=round(float(np.mean((loo_B - yv) ** 2)), 4), logloss=ll(loo_B)),
                         'B1': dict(brier=round(float(np.mean((loo_B1 - yv) ** 2)), 4), logloss=ll(loo_B1))})
print('obhajoba', json.dumps(obhajoba, ensure_ascii=False))
val = dict(A=score(loo_A), B=score(loo_B), zakladni=score(np.full(len(yv), base_rate)), druhych_kol=len(R))
print('B: P =', round(pB, 3), 'bod zvratu', np.round(np.nanpercentile(f_need, [25, 50, 75]), 3), 'Praha', round(pB_praha, 3), '| ověření', val)

# ---------------------------------------------------------------- výstup
par = np.array([r['B'] for r in races])  # kola × [A1, B1, ostatní, nevoliči] × [A2, B2, nepřišli]
med = lambda v: round(float(np.median(v)) * 100, 1)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
data['senat_predikce'] = dict(
    obvod=OBVOD, vitez_k1=LEAD, druhy_k1=RUN, naskok_pb=round(naskok, 2),
    k1=dict(laska=int(A1), sablik=int(B1), ostatni=int(valid - A1 - B1), nevolici=int(reg - valid), zapsanych=int(reg)),
    historie=dict(druhych_kol=len(R), praha=int(R.praha.sum()), druhy_vyhral=int(R.druhy_vyhral.sum()),
                  druhy_vyhral_pct=round(base_rate * 100, 1), roky=f'{min(YEARS)}–{max(YEARS)}',
                  podobny_naskok=dict(od=round(naskok - 3, 1), do=round(naskok + 3, 1), kol=len(pod), druhy_vyhral=int(pod.druhy_vyhral.sum())),
                  praha_druhy_vyhral=int(R[R.praha].druhy_vyhral.sum())),
    model_a=dict(p=round(pA * 100, 1), p05=round(float(pA_lo) * 100, 1), p95=round(float(pA_hi) * 100, 1),
                 beta=[round(float(b), 4) for b in beta],
                 krivka=[dict(naskok=float(n), p=round(float(logit_p(beta, n)) * 100, 1)) for n in np.arange(0, 30.5, 0.5)],
                 body=[dict(naskok=round(float(r.naskok), 2), druhy_vyhral=bool(r.druhy_vyhral), obh_a=bool(r.obh_a), obh_b=bool(r.obh_b), rok=int(r.rok), obvod=int(r.obvod), praha=bool(r.praha),
                            text=f'{r.rok}, obvod {r.obvod}: {r.vitez_k1} {r.a_pct:.1f} % × {r.druhy_k1} {r.b_pct:.1f} %') for r in R.itertuples()]),
    model_b=dict(p=round(pB * 100, 1), p_praha=round(pB_praha * 100, 1), kol_praha=int(S.praha.sum()),
                 rozdil_median=round(float(S.rozdil_pct.median()), 1), rozdil_p05=round(float(S.rozdil_pct.quantile(0.05)), 1), rozdil_p95=round(float(S.rozdil_pct.quantile(0.95)), 1),
                 ucast_median=round(float(S.ucast.median()), 1),
                 potreba_z_ostatnich=dict(median=round(float(np.nanmedian(f_need)) * 100, 1), p25=round(float(np.nanpercentile(f_need, 25)) * 100, 1), p75=round(float(np.nanpercentile(f_need, 75)) * 100, 1)),
                 vzorce=dict(vitez_znovu=med(par[:, 0, 0]), druhy_znovu=med(par[:, 1, 1]),
                             ostatni_k_vitezi=med(par[:, 2, 0]), ostatni_k_druhemu=med(par[:, 2, 1]), ostatni_neprisli=med(par[:, 2, 2]),
                             nevolici_prisli=med(par[:, 3, 0] + par[:, 3, 1])),
                 simulace=[dict(rok=int(s.rok), obvod=int(s.obvod), praha=bool(s.praha), rozdil=round(float(s.rozdil_pct), 2), ucast=round(float(s.ucast), 1)) for s in S.itertuples()]),
    overeni=val,
    obhajoba=obhajoba,
)
save(data, os.path.join(OUT, 'data.json'))
