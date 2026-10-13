"""Psefologická vrstva pro Prahu 5 (zastupitelstvo MČ, 2022 → 2026).

python -P scripts/psefologie.py <dl_dir> data

Výstup: data/psefologie.json + doplní data/data.json (okrskům volatilitu, ENP, LISA).
Jen numpy/pandas (scipy není potřeba).
"""
import sys, os, json, math
import numpy as np
import pandas as pd

DL, OUT = sys.argv[1:3]
P5, SEATS = 500143, 41
rng = np.random.default_rng(2026)


def rd(p):
    return pd.read_csv(os.path.join(DL, p), low_memory=False)


def load(y):
    if y == 2026:
        t3, hl, ros = rd('KV2026_data_20261011_csv/csv_od/kvt3.csv'), rd('KV2026_data_20261011_csv/csv_od/kvhl.csv'), rd('KV2026reg20261011_csv/csv_od/kvros.csv')
    else:
        t3, hl, ros = rd('KV2022_data_20260328_csv/csv_od/kvt3.csv'), rd('KV2022_data_20260328_csv/csv_od/kvhl.csv'), rd('KV2022reg20260328_csv/csv_od/kvros.csv')
        t3, hl, ros = (d[d.DATUMVOLEB == 20220923] for d in (t3, hl, ros))
    t3 = t3[(t3.OBEC == P5) & (t3.KODZASTUP == P5)].set_index('OKRSEK')
    ids = set(t3.ID_OKRSKY)
    hl = hl[hl.ID_OKRSKY.isin(ids)]
    ros = ros[ros.KODZASTUP == P5].set_index('POR_STR_HL')
    votes = hl.pivot_table(index='OKRSEK', columns='POR_STR_HL', values='POC_HLASU', aggfunc='sum', fill_value=0)
    return t3, votes, ros


# bloky stran srovnatelné mezi roky (ODS a TOP 09 kandidovaly 2022 spolu → jeden pravý blok)
BLOKY = [
    ('Piráti', ['Česká pirátská'], ['Česká pirátská']),
    ('PRAHA 5 SOBĚ', ['PRAHA 5 SOBĚ'], ['PRAHA 5 SOBĚ']),
    ('ODS, TOP 09, KDU', ['SPOLEČNĚ PRO PRAHU 5', 'KDU-ČSL, Zelení'], ['Občanská demokratická', 'TOP Lidovci']),
    ('STAN', ['STAROSTOVÉ'], ['STAROSTOVÉ']),
    ('SEN', ['SEN 21'], ['SEN PRO PRAHU 5']),
    ('ANO', ['ANO 2011'], ['ANO 2011']),
    ('SPD, Motoristé a menší', None, None),  # zbytek
]


def blocks(y):
    t3, votes, ros = load(y)
    names = ros.ZKRATKAO30.to_dict()
    col = {}
    for por, n in names.items():
        b = next((lab for lab, a, c in BLOKY[:-1] if any(n.startswith(k) or k in n for k in (a if y == 2022 else c))), BLOKY[-1][0])
        col[por] = b
    bv = votes.T.groupby(col).sum().T  # hlasy bloků po okrscích
    bv = bv[[b[0] for b in BLOKY]]
    return t3, votes, ros, bv, col


T = {y: blocks(y) for y in (2022, 2026)}
okrsky = sorted(set(T[2022][0].index) & set(T[2026][0].index))
B = [b[0] for b in BLOKY]


def shares(bv):
    return bv.div(bv.sum(axis=1), axis=0) * 100


s22, s26 = shares(T[2022][3]).loc[okrsky], shares(T[2026][3]).loc[okrsky]
out = {}

# ---------------------------------------------------------------- volatilita a ENP
tot22 = T[2022][3].sum() / T[2022][3].sum().sum() * 100
tot26 = T[2026][3].sum() / T[2026][3].sum().sum() * 100
out['bloky'] = [dict(blok=b, p2022=round(float(tot22[b]), 2), p2026=round(float(tot26[b]), 2)) for b in B]
out['pedersen_p5'] = round(float((tot26 - tot22).abs().sum() / 2), 2)
ped_okr = ((s26 - s22).abs().sum(axis=1) / 2)


def enp(v):
    p = np.asarray(v, float); p = p / p.sum()
    return float(1 / (p ** 2).sum())


for y in (2022, 2026):
    t3, votes, ros, bv, col = T[y]
    out[f'enp_hlasy_{y}'] = round(enp(votes.sum()), 2)  # po jednotlivých listinách
    out[f'enp_mandaty_{y}'] = round(enp(ros.MAND_STR.fillna(0)), 2)
enp_okr = {y: T[y][1].loc[okrsky].apply(enp, axis=1) for y in (2022, 2026)}

# ---------------------------------------------------------------- mandáty: D'Hondt s 5% klauzulí
def dhondt(votes, seats, thr_ok):
    q = [(v / d, p) for p, v in votes.items() if thr_ok[p] for d in range(1, seats + 1)]
    q.sort(key=lambda x: -x[0])
    won = {p: 0 for p in votes}
    for _, p in q[:seats]:
        won[p] += 1
    dhondt.last_party = q[seats - 1][1]
    return won, q[seats - 1][0], q[seats][0]


t3, votes, ros, bv, col = T[2026]
tv = votes.sum()
total = tv.sum()
official = ros.MAND_STR.fillna(0).astype(int).to_dict()
# klauzule: zkusí se pevných 5 % a varianta s vyšší klauzulí pro koalice (počet stran bez NK = kód 080);
# použije se ta, která reprodukuje oficiální mandáty
npart = {p: len([c for c in str(ros.SLOZENI[p]).split(',') if c != '080']) for p in tv.index}
varianty = {'5 % pro všechny': {p: 5 for p in tv.index},
            'koalice 10/15/20 %': {p: (5 if npart[p] <= 1 else {2: 10, 3: 15}.get(npart[p], 20)) for p in tv.index}}
for nazev_var, klauz in varianty.items():
    thr = {p: tv[p] / total * 100 >= klauz[p] for p in tv.index}
    won, last_q, next_q = dhondt(tv.to_dict(), SEATS, thr)
    if all(won[p] == official[p] for p in won):
        break
out['klauzule'] = nazev_var
out['dhondt_shoda'] = all(won[p] == official[p] for p in won)
pir = next(p for p, n in ros.ZKRATKAO30.items() if n.startswith('Česká pirátská'))
# kolik hlasů chybělo na 4. mandát (ostatní beze změny): podíl Pirátů / 4 musí přebít poslední přidělený podíl
need = last_q * 4 - tv[pir]
out['mandaty'] = dict(
    oficialni={ros.ZKRATKAO30[p]: int(official[p]) for p in tv.index if official[p]},
    piráti_hlasy=int(tv[pir]),
    posledni_podil=round(float(last_q), 1),
    posledni_mandat=f"{ros.ZKRATKAO30[dhondt.last_party]} ({official[dhondt.last_party]}. mandát)",
    chybelo_na_4_mandat_hlasu=int(math.ceil(need)),
    chybelo_na_4_mandat_volicu=int(math.ceil(need / SEATS)),
    rezerva_3_mandatu_volicu=int((tv[pir] / 3 - next_q) * 3 // SEATS) if tv[pir] / 3 > next_q else 0,
)
# kolik voličů bylo potřeba na 6 mandátů z roku 2022
out['mandaty']['na_6_mandatu_volicu'] = int(math.ceil((last_q * 6 - tv[pir]) / SEATS))

# ---------------------------------------------------------------- plošný vs. poměrný pokles
p22, p26 = s22['Piráti'], s26['Piráti']
uni = p22 + (p26.mean() - p22.mean())
prop = p22 * (p26.mean() / p22.mean())
out['swing'] = dict(
    rmse_plosny=round(float(np.sqrt(((p26 - uni) ** 2).mean())), 2),
    rmse_pomerny=round(float(np.sqrt(((p26 - prop) ** 2).mean())), 2),
    pomer=round(float(p26.mean() / p22.mean()), 3),
    korelace_2022_2026=round(float(p22.corr(p26)), 3),
)

# ---------------------------------------------------------------- ekologická inference přesunů (Goodman s omezeními)
# jednotky: okrsky bez 5008 (adresa úřadu, zkreslená účast); kategorie = podíl na zapsaných voličích
EXCL = [5008]
units = [o for o in okrsky if o not in EXCL]


def composition(y):
    t3, votes, ros, bv, col = T[y]
    reg = t3.VOL_SEZNAM.loc[units].astype(float)
    ballots = t3.ODEVZ_OBAL.loc[units].astype(float)
    # hlasy bloku přepočtené na voliče: podíl bloku na platných hlasech × odevzdané obálky
    sh = bv.loc[units].div(bv.loc[units].sum(axis=1), axis=0)
    X = sh.mul(ballots, axis=0)
    X['Nevoliči'] = reg - ballots
    return X.div(reg, axis=0), reg


X22, reg22 = composition(2022)
X26, reg26 = composition(2026)
cats = list(X22.columns)


def proj_simplex(v):
    u = np.sort(v)[::-1]; css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(v) + 1) > (css - 1))[0][-1]
    th = (css[rho] - 1) / (rho + 1)
    return np.maximum(v - th, 0)


def fit(X, Y, w, iters=6000):
    X, Y = np.asarray(X), np.asarray(Y)
    W = np.sqrt(w / w.mean())[:, None]
    Xw, Yw = X * W, Y * W
    k = X.shape[1]
    Bm = np.tile(Y.mean(0), (k, 1))
    L = np.linalg.norm(Xw.T @ Xw, 2)
    step = 1 / L
    for _ in range(iters):
        G = Xw.T @ (Xw @ Bm - Yw)
        Bm = np.apply_along_axis(proj_simplex, 1, Bm - step * G)
    return Bm


w = reg22.values
Bhat = fit(X22.values, X26.values, w)
boot = []
for _ in range(200):
    idx = rng.integers(0, len(units), len(units))
    boot.append(fit(X22.values[idx], X26.values[idx], w[idx], iters=2500))
boot = np.array(boot)
lo, hi = np.percentile(boot, 5, axis=0), np.percentile(boot, 95, axis=0)
# celkový počet voličů v přesunu (v osobách) = podíl × velikost kategorie 2022
size22 = (X22.mul(reg22, axis=0)).sum()
out['ei'] = dict(
    kategorie_2022=cats, kategorie_2026=list(X26.columns),
    matice=[[round(float(v) * 100, 1) for v in row] for row in Bhat],
    p05=[[round(float(v) * 100, 1) for v in row] for row in lo],
    p95=[[round(float(v) * 100, 1) for v in row] for row in hi],
    velikost_2022={c: int(size22[c]) for c in cats},
    okrsku=len(units), vynechano=EXCL,
)
i = cats.index('Piráti')
out['ei']['pirati_2022_kam'] = sorted([dict(kam=c, pct=round(float(Bhat[i, j]) * 100, 1), p05=round(float(lo[i, j]) * 100, 1), p95=round(float(hi[i, j]) * 100, 1),
                                            volicu=int(Bhat[i, j] * size22['Piráti'])) for j, c in enumerate(X26.columns)], key=lambda d: -d['pct'])
j = list(X26.columns).index('Piráti')
inflow = Bhat[:, j] * size22.values
out['ei']['pirati_2026_odkud'] = sorted([dict(odkud=c, volicu=int(inflow[k]), pct=round(float(inflow[k] / inflow.sum()) * 100, 1)) for k, c in enumerate(cats)], key=lambda d: -d['volicu'])
pred = X22.values @ Bhat
out['ei']['r2_pirati_2026'] = round(float(1 - ((X26['Piráti'] - pred[:, j]) ** 2).sum() / ((X26['Piráti'] - X26['Piráti'].mean()) ** 2).sum()), 3)

# citlivost: jen voliči (bez kategorie nevoličů, podíly v rámci odevzdaných hlasů)
V22 = X22.drop(columns='Nevoliči'); V22 = V22.div(V22.sum(1), axis=0)
V26 = X26.drop(columns='Nevoliči'); V26 = V26.div(V26.sum(1), axis=0)
Bv = fit(V22.values, V26.values, w)
bv_boot = np.array([fit(V22.values[ix], V26.values[ix], w[ix], iters=2500) for ix in (rng.integers(0, len(units), len(units)) for _ in range(200))])
iv = list(V22.columns).index('Piráti')
out['ei']['jen_volici_pirati_2022_kam'] = sorted([dict(kam=c, pct=round(float(Bv[iv, k]) * 100, 1), p05=round(float(np.percentile(bv_boot[:, iv, k], 5)) * 100, 1),
                                                       p95=round(float(np.percentile(bv_boot[:, iv, k], 95)) * 100, 1)) for k, c in enumerate(V26.columns)], key=lambda d: -d['pct'])

# ---------------------------------------------------------------- prostorová autokorelace (Moranovo I, k=6 nejbližších)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}
ids = [o for o in okrsky]
xy = np.array([[O[o]['lon'] * math.cos(math.radians(50.07)), O[o]['lat']] for o in ids])
D = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1))
K = 6
Wm = np.zeros_like(D)
for a in range(len(ids)):
    nn = np.argsort(D[a])[1:K + 1]
    Wm[a, nn] = 1
Wm = Wm / Wm.sum(1, keepdims=True)


def moran(z, perms=999):
    z = np.asarray(z, float); z = z - z.mean()
    I = (len(z) / Wm.sum()) * (z @ Wm @ z) / (z @ z)
    sims = np.array([(lambda p: (len(p) / Wm.sum()) * (p @ Wm @ p) / (p @ p))(rng.permutation(z)) for _ in range(perms)])
    p = (np.sum(sims >= I) + 1) / (perms + 1)
    return round(float(I), 3), round(float(p), 3)


def lisa(z, perms=999):
    z = np.asarray(z, float); z = (z - z.mean()) / z.std()
    lag = Wm @ z
    Ii = z * lag
    res = []
    for a in range(len(z)):
        others = np.delete(np.arange(len(z)), a)
        nn = np.nonzero(Wm[a])[0]
        sims = np.array([z[a] * z[rng.choice(others, len(nn), replace=False)].mean() for _ in range(perms)])
        p = (np.sum(np.abs(sims) >= abs(Ii[a])) + 1) / (perms + 1)
        typ = 'ns' if p > 0.05 else ('HH' if z[a] > 0 and lag[a] > 0 else 'LL' if z[a] < 0 and lag[a] < 0 else 'HL' if z[a] > 0 else 'LH')
        res.append((typ, round(float(p), 3)))
    return res


dmc = np.array([O[o]['mc_delta'] for o in ids])
out['moran'] = {
    'piráti_2026': moran([O[o]['mc_2026'] for o in ids]),
    'piráti_zmena': moran(dmc),
    'sen_2026': moran([O[o]['sen_2026'] for o in ids]),
    'stan_zmena': moran([O[o]['stan_2026'] - O[o]['stan_2022'] for o in ids]),
    'k_sousedu': K,
}
L = lisa(dmc)
for o, (typ, p), pe, e22, e26 in zip(ids, L, ped_okr.loc[ids], enp_okr[2022].loc[ids], enp_okr[2026].loc[ids]):
    O[o]['lisa_zmena'] = typ
    O[o]['lisa_p'] = p
    O[o]['pedersen'] = round(float(pe), 1)
    O[o]['enp_2022'] = round(float(e22), 2)
    O[o]['enp_2026'] = round(float(e26), 2)
out['lisa_pocty'] = pd.Series([t for t, _ in L]).value_counts().to_dict()
# Benjamini–Hochberg (FDR 5 %) přes 81 lokálních testů
pv = np.array([p for _, p in L]); order = np.argsort(pv); m = len(pv)
passed = pv[order] <= 0.05 * np.arange(1, m + 1) / m
k_bh = int(np.max(np.nonzero(passed)[0]) + 1) if passed.any() else 0
out['lisa_fdr_vyznamnych'] = k_bh
for o in ids:
    O[o]['lisa_fdr'] = bool(k_bh and O[o]['lisa_p'] <= pv[order][k_bh - 1])
out['pedersen_okrsky'] = dict(min=round(float(ped_okr.min()), 1), median=round(float(ped_okr.median()), 1), max=round(float(ped_okr.max()), 1))

data['psefologie'] = out
json.dump(data, open(os.path.join(OUT, 'data.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
json.dump(out, open(os.path.join(OUT, 'psefologie.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'ei'}, ensure_ascii=False, indent=1))
print('EI piráti 2022 →', out['ei']['pirati_2022_kam'])
print('EI piráti 2026 ←', out['ei']['pirati_2026_odkud'])
print('EI R2', out['ei']['r2_pirati_2026'])
print('EI jen voliči', out['ei']['jen_volici_pirati_2022_kam'])
print(pd.DataFrame(out['ei']['matice'], index=cats, columns=list(X26.columns)).to_string())
