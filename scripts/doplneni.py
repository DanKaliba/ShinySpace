"""Doplnění bodů z „Co chybí“ (kromě 2. kola Senátu).

python -P scripts/doplneni.py <dl_dir> data

a) Demografie 2026: věk po okrscích (grid 2021 × koeficient věkové skupiny MČ, OBY02E), věk a pohlaví po MČ
b) Dělení hlasů MČ × magistrát (stejní voliči, stejný den)
c) Preferenční hlasy pirátské magistrátní kandidátky po čtvrtích Prahy 5
d) Přesuny voličů PS 2025 → KV 2026 (Praha 5 i Praha)
e) Účast: kdo získal z nových voličů
f) Nová výstavba: okrsky s největším přírůstkem voličů
g) Ekologická inference – varianta s IPF po okrscích (entropická metoda Johnstona a Pattieho)
h) Monte Carlo mandátů v Praze 5
i) Srovnání Prahy 5 s ostatními MČ
Spouštět po census.py.
"""
import sys, os, json, re, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ei import fit, bootstrap  # noqa: E402
from jsonio import save  # noqa: E402
from kvdata import Data, composition, stable, MC22, MC26, PSB  # noqa: E402

DL, OUT = sys.argv[1:3]
P5, MAG, SEATS = 500143, 554782, 41
rng = np.random.default_rng(2026)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}
ids = sorted(O)
out = {}


def ci(boot, i, j):
    return round(float(np.percentile(boot[:, i, j], 5)) * 100, 1), round(float(np.percentile(boot[:, i, j], 95)) * 100, 1)


def wavg(v, w):
    v, w = np.asarray(v, float), np.asarray(w, float)
    m = ~np.isnan(v)
    return float((v[m] * w[m]).sum() / w[m].sum())


# ---------------------------------------------------------------- načtení KV a PS (sdílené v kvdata.py)
D = Data(DL)
KV = {y: D.kv(y) for y in (2022, 2026)}
bloc_votes, ps_votes = D.bloc_votes, D.ps_votes


def ei_summary(Xa, Yb, w, focus, nboot):
    B = fit(Xa.values, Yb.values, w)
    bo = bootstrap(Xa.values, Yb.values, w, rng, n=nboot) if nboot else None
    i = list(Xa.columns).index(focus)
    rows = []
    for j, c in enumerate(Yb.columns):
        lo, hi = ci(bo, i, j) if bo is not None else (None, None)
        rows.append(dict(kam=c, pct=round(float(B[i, j]) * 100, 1), p05=lo, p95=hi))
    return B, sorted(rows, key=lambda d: -d['pct'])


MB = [('Piráti', r'^Česká pirátská'), ('SPOLU', r'^SPOLU'), ('STAN', r'^STAROSTOVÉ'), ('PRAHA SOBĚ', r'^PRAHA SOBĚ'), ('ANO', r'^ANO'), ('SEN', r'^SEN '), ('Ostatní', r'.')]
# ---------------------------------------------------------------- a) Demografie 2026
def oby(y):
    a = pd.read_csv(os.path.join(DL, 'csu', f'oby02e_{y}.csv'), dtype=str)
    a = a[a['UZ596H.MOMC'].fillna('') != '']
    a['v'] = a.Hodnota.astype(float)
    return a.pivot_table(index='UZ596H.MOMC', columns=['POHL2', 'VekSkupZakl'], values='v', aggfunc='sum')


A21, A25 = oby(2021), oby(2025)


def shares(A):
    tot = A[('0', 'VEKC')]
    return pd.DataFrame({'obyv': tot, 'v0_14': A[('0', 'VEK014')] / tot * 100, 'v65': A[('0', 'VEK65AV')] / tot * 100, 'zeny': A[('2', 'VEKC')] / tot * 100})


S21, S25 = shares(A21), shares(A25)
K = {g: float(A25.loc[str(P5), ('0', g)] / A21.loc[str(P5), ('0', g)]) for g in ('VEK014', 'VEK1564', 'VEK65AV', 'VEKC')}
for o in ids:
    r = O[o]
    if r.get('cen_obyv') is None or r.get('cen_0_14') is None:
        continue
    n = r['cen_obyv']; a0 = n * r['cen_0_14'] / 100; a65 = n * r['cen_65'] / 100; a15 = n - a0 - a65
    b0, b15, b65 = a0 * K['VEK014'], a15 * K['VEK1564'], a65 * K['VEK65AV']
    tot = b0 + b15 + b65
    r['cen26_obyv'] = round(tot); r['cen26_0_14'] = round(b0 / tot * 100, 1); r['cen26_65'] = round(b65 / tot * 100, 1)
cz = {int(m['kod']): m for m in data['census']['mc']}
mc26 = []
for kod, m in cz.items():
    k = str(kod)
    if k not in S25.index:
        continue
    mc26.append(dict(kod=kod, nazev=m['nazev'], obyv_2021=int(S21.loc[k, 'obyv']), obyv_2026=int(S25.loc[k, 'obyv']), rust=round(float(S25.loc[k, 'obyv'] / S21.loc[k, 'obyv'] - 1) * 100, 1),
                     v0_14_2026=round(float(S25.loc[k, 'v0_14']), 1), v65_2026=round(float(S25.loc[k, 'v65']), 1), zeny_2026=round(float(S25.loc[k, 'zeny']), 1),
                     v65_2021=round(float(S21.loc[k, 'v65']), 1), vs_2021=m['vs'], mag_2026=m['mag_2026'], mag_zmena=m['mag_zmena']))
M26 = pd.DataFrame(mc26)
kor26 = []
for a, al in [('v0_14_2026', 'děti 0–14 (2026)'), ('v65_2026', 'senioři 65+ (2026)'), ('zeny_2026', 'podíl žen (2026)'), ('rust', 'růst obyvatel 2022–26'), ('vs_2021', 'vysokoškoláci (2021)')]:
    for b, bl in [('mag_2026', 'Piráti magistrát 2026'), ('mag_zmena', 'změna 2022→26')]:
        kor26.append(dict(demo=a, demo_label=al, vysledek=b, vysledek_label=bl, r=round(float(M26[a].corr(M26[b])), 2)))
out['demografie_2026'] = dict(koeficienty_p5={k: round(v, 4) for k, v in K.items()}, p5_2021={k: round(float(v), 2) for k, v in S21.loc[str(P5)].items()},
                              p5_2026={k: round(float(v), 2) for k, v in S25.loc[str(P5)].items()}, mc=mc26, korelace_mc=kor26,
                              poznamka='Věk po okrscích 2026 = grid SLDB 2021 × koeficient věkové skupiny Prahy 5 (31. 12. 2025 / 31. 12. 2021, OBY02E). Vzdělání se mezi sčítáními neaktualizuje.')
print('a) K', out['demografie_2026']['koeficienty_p5'])

# ---------------------------------------------------------------- b) dělení hlasů MČ × magistrát (Praha 5, 2026)
vm, tm = bloc_votes(2026, MAG, MB, obec=P5)
vc, tc = bloc_votes(2026, P5, MC26, obec=P5)
keys = [k for k in vm.index if k[1] != 5008]
Xm = vm.loc[keys].div(vm.loc[keys].sum(1), axis=0)
Yc = vc.loc[keys].div(vc.loc[keys].sum(1), axis=0)
w = tc.ODEVZ_OBAL.loc[keys].values
Bs, pir_mag_kam = ei_summary(Xm, Yc, w, 'Piráti', 200)
mag_vol = Xm.mul(tc.ODEVZ_OBAL.loc[keys], axis=0).sum()
jp = list(Yc.columns).index('Piráti')
inflow = Bs[:, jp] * mag_vol.values
out['deleni_mc_mag'] = dict(
    pirati_mag_kam=pir_mag_kam,
    pirati_mc_odkud=sorted([dict(odkud=c, volicu=int(inflow[i]), pct=round(float(inflow[i] / inflow.sum()) * 100, 1)) for i, c in enumerate(Xm.columns)], key=lambda d: -d['volicu']),
    r2=round(float(1 - ((Yc.values - Xm.values @ Bs) ** 2).sum() / ((Yc.values - Yc.values.mean(0)) ** 2).sum()), 3),
)
for o in ids:
    O[o]['mc_minus_mag'] = round(O[o]['mc_2026'] - O[o]['mag_2026'], 2)
d = pd.DataFrame(data['okrsky']).set_index('okrsek')
out['deleni_mc_mag']['rozdil'] = dict(prumer=round(float(np.average(d.mc_minus_mag, weights=d.odevzdano_2026)), 2),
                                      nejvic_mc=[dict(okrsek=int(o), ctvrt=d.ctvrt[o], rozdil=float(d.mc_minus_mag[o])) for o in d.mc_minus_mag.nlargest(5).index],
                                      nejvic_mag=[dict(okrsek=int(o), ctvrt=d.ctvrt[o], rozdil=float(d.mc_minus_mag[o])) for o in d.mc_minus_mag.nsmallest(5).index],
                                      ctvrti={c: round(wavg(g.mc_minus_mag, g.odevzdano_2026), 2) for c, g in d.groupby('ctvrt')})
print('b)', pir_mag_kam[:4])

# ---------------------------------------------------------------- c) preferenční hlasy magistrátní kandidátky Pirátů po čtvrtích Prahy 5
t3, hl, ros = KV[2026]
rk = D.rd('KV2026reg20261011_csv/csv_od/kvrk.csv')
por = int(ros[(ros.KODZASTUP == MAG) & ros.ZKRATKAO30.str.startswith('Česká pirátská')].POR_STR_HL.iloc[0])
tP = t3[(t3.KODZASTUP == MAG) & (t3.OBEC == P5)][['ID_OKRSKY', 'OKRSEK']]
hP = hl[(hl.POR_STR_HL == por)].drop(columns=['OKRSEK'], errors='ignore').merge(tP, on='ID_OKRSKY')
hP['ctvrt'] = hP.OKRSEK.map(lambda o: O[o]['ctvrt'])
cand = rk[(rk.KODZASTUP == MAG) & (rk.POR_STR_HL == por)].sort_values('PORCISLO').head(15)
ctot = hP.groupby('ctvrt').POC_HLASU.sum()
pref = []
for r in cand.itertuples():
    col = f'HLASY_{int(r.PORCISLO):02d}'
    base = hP[col].sum() / hP.POC_HLASU.sum()
    idx = (hP.groupby('ctvrt')[col].sum() / ctot / base * 100).round(0)
    ok = hP.groupby('OKRSEK')[col].sum() / hP.groupby('OKRSEK').POC_HLASU.sum() / base * 100
    pref.append(dict(poradi=int(r.PORCISLO), jmeno=f'{r.JMENO} {r.PRIJMENI}', hlasy_p5=int(hP[col].sum()), index_ctvrti={k: float(v) for k, v in idx.items()},
                     max_okrsek=int(ok.idxmax()), max_index=round(float(ok.max()), 0)))
out['pref_magistrat'] = pref
print('c)', [(p['jmeno'], max(p['index_ctvrti'].items(), key=lambda x: x[1])) for p in pref[:5]])

# ---------------------------------------------------------------- d) PS 2025 → KV 2026
vps, tps = ps_votes(PSB, obec=P5)
k5 = stable(tps, tc).intersection(vps.index)
k5 = [k for k in k5 if k[1] != 5008]
Xps = composition(vps, tps, k5)
Ymc = composition(vc, tc, k5)
B_ps5, ps5_kam = ei_summary(Xps, Ymc, tps.VOL_SEZNAM.loc[k5].values, 'Piráti', 200)
size_ps5 = Xps.mul(tps.VOL_SEZNAM.loc[k5], axis=0).sum()
# Praha: PS → magistrát
vpa, tpa = ps_votes(PSB)
vma, tma = bloc_votes(2026, MAG, MB)
kp = stable(tpa, tma).intersection(vpa.index).intersection(vma.index)
Xpa, Yma = composition(vpa, tpa, kp), composition(vma, tma, kp)
B_psp, psp_kam = ei_summary(Xpa, Yma, tpa.VOL_SEZNAM.loc[kp].values, 'Piráti', 60)
size_psp = Xpa.mul(tpa.VOL_SEZNAM.loc[kp], axis=0).sum()
out['ps25_kv26'] = dict(
    p5=dict(okrsku=len(k5), kategorie_ps=list(Xps.columns), kategorie_kv=list(Ymc.columns), matice=[[round(float(v), 4) for v in r] for r in B_ps5],
            velikost_ps={c: int(v) for c, v in size_ps5.items()}, pirati_kam=ps5_kam),
    praha=dict(okrsku=len(kp), kategorie_ps=list(Xpa.columns), kategorie_kv=list(Yma.columns), matice=[[round(float(v), 4) for v in r] for r in B_psp],
               velikost_ps={c: int(v) for c, v in size_psp.items()}, pirati_kam=psp_kam),
)
print('d) P5', ps5_kam[:4], '\n   Praha', psp_kam[:4])

# ---------------------------------------------------------------- e) účast
rows = pd.DataFrame(data['okrsky']).set_index('okrsek').drop(index=5008)
rows['ucast_d'] = rows.ucast_2026 - rows.ucast_2022
uc = {}
for k_, lab in [('mc_delta', 'Piráti'), ('stan', 'STAN'), ('sen', 'SEN'), ('p5sobe', 'PRAHA 5 SOBĚ'), ('ano', 'ANO')]:
    dv = rows.mc_delta if k_ == 'mc_delta' else rows[f'{k_}_2026'] - rows[f'{k_}_2022']
    uc[lab] = round(float(rows.ucast_d.corr(dv)), 2)
sk_p5, sk_pr = data['rozsireni']['sankey_p5'], data['rozsireni']['sankey_praha']


def nonvoter_flows(sk):
    cats = sk['kategorie']; i = cats.index('Nevoliči'); M = np.array(sk['matice']); size = sk['velikost_2022']['Nevoliči']
    flows = {c: M[i, j] * size for j, c in enumerate(cats) if c != 'Nevoliči'}
    tot = sum(flows.values())
    return dict(prislo_volit=int(tot), podil_nevolicu=round(tot / size * 100, 1), kam=sorted([dict(kam=c, volicu=int(v), pct=round(v / tot * 100, 1)) for c, v in flows.items()], key=lambda x: -x['volicu']))


ps_pir_nevol = next(r for r in ps5_kam if r['kam'] == 'Nevoliči')
psp_pir_nevol = next(r for r in psp_kam if r['kam'] == 'Nevoliči')
out['ucast'] = dict(p5_2022=data['p5']['ucast_2022'], p5_2026=data['p5']['ucast_2026'], praha_2022=data['praha_ucast_2022'], praha_2026=data['praha_ucast_2026'],
                    korelace_zmena_ucasti=uc, nevolici_2022_p5=nonvoter_flows(sk_p5), nevolici_2022_praha=nonvoter_flows(sk_pr),
                    pirati_ps25_nevolili_p5=ps_pir_nevol, pirati_ps25_nevolili_praha=psp_pir_nevol,
                    nejvic_rust=[dict(okrsek=int(o), ctvrt=rows.ctvrt[o], zmena=round(float(rows.ucast_d[o]), 1)) for o in rows.ucast_d.nlargest(5).index])
print('e)', uc, out['ucast']['nevolici_2022_p5']['kam'][:3])

# ---------------------------------------------------------------- f) nová výstavba
rows['rust_volicu'] = (rows.volici_2026 / rows.volici_2022 - 1) * 100
top = rows.rust_volicu.nlargest(10).index
rest = rows.index.difference(top)


def grp(ix):
    g = rows.loc[ix]
    return dict(okrsku=len(ix), rust_volicu=round(float(g.volici_2026.sum() / g.volici_2022.sum() - 1) * 100, 1),
                pirati_2022=round(wavg(g.mc_2022, g.odevzdano_2022), 2), pirati_2026=round(wavg(g.mc_2026, g.odevzdano_2026), 2),
                stan_2026=round(wavg(g.stan_2026, g.odevzdano_2026), 2), sen_2026=round(wavg(g.sen_2026, g.odevzdano_2026), 2),
                ano_2026=round(wavg(g.ano_2026, g.odevzdano_2026), 2), ucast_2026=round(float(g.odevzdano_2026.sum() / g.volici_2026.sum() * 100), 1),
                rust_obyv_11_21=round(wavg(g.cen_rust_11_21, g.cen_obyv), 1))


# Praha: okrsky, kde přibylo voličů o 15–100 % (stejné číslo okrsku 2022 i 2026)
_, t22m = bloc_votes(2022, MAG, MB)
v26m, t26m = vma, tma
kk = t22m.index.intersection(t26m.index)
gr = (t26m.VOL_SEZNAM.loc[kk] / t22m.VOL_SEZNAM.loc[kk] - 1) * 100
newp = kk[(gr > 15) & (gr < 100)]
out['vystavba'] = dict(
    p5_top=grp(top), p5_ostatni=grp(rest),
    p5_okrsky=[dict(okrsek=int(o), ctvrt=rows.ctvrt[o], rust_volicu=round(float(rows.rust_volicu[o]), 1), pirati_2026=float(rows.mc_2026[o]), pirati_zmena=float(rows.mc_delta[o]),
                    ucast_2026=float(rows.ucast_2026[o])) for o in top],
    korelace_rust_pirati_zmena=round(float(rows.rust_volicu.corr(rows.mc_delta)), 2),
    praha_nove=dict(okrsku=int(len(newp)), pirati_2026=round(float((v26m.loc[newp, 'Piráti'].sum() / v26m.loc[newp].sum().sum()) * 100), 2),
                    pirati_2026_ostatni=round(float((v26m.drop(index=newp)['Piráti'].sum() / v26m.drop(index=newp).sum().sum()) * 100), 2),
                    ucast_nove=round(float(t26m.ODEVZ_OBAL.loc[newp].sum() / t26m.VOL_SEZNAM.loc[newp].sum() * 100), 1),
                    ucast_ostatni=round(float(t26m.drop(index=newp).ODEVZ_OBAL.sum() / t26m.drop(index=newp).VOL_SEZNAM.sum() * 100), 1)),
)
print('f)', out['vystavba']['p5_top'], out['vystavba']['p5_ostatni'], out['vystavba']['praha_nove'])

# ---------------------------------------------------------------- g) EI varianta: IPF po okrscích (Johnston–Pattie)
def ipf_ei(Xa, Yb, N, B, iters=200):
    tot = np.zeros_like(B)
    for u in range(len(Xa)):
        r, c = Xa[u] * N[u], Yb[u] * N[u]
        T = r[:, None] * B + 1e-9
        for _ in range(iters):
            T *= (r / np.maximum(T.sum(1), 1e-12))[:, None]
            T *= (c / np.maximum(T.sum(0), 1e-12))[None, :]
        tot += T
    return tot / tot.sum(1, keepdims=True)


v22c, t22c = bloc_votes(2022, P5, MC22, obec=P5)
kj = [k for k in v22c.index.intersection(vc.index) if k[1] != 5008]
X22, Y26 = composition(v22c, t22c, kj), composition(vc, tc, kj)
N = tc.VOL_SEZNAM.loc[kj].values.astype(float)
Bg = fit(X22.values, Y26.values, t22c.VOL_SEZNAM.loc[kj].values)
Bj = ipf_ei(X22.values, Y26.values, N, Bg)
ip = list(X22.columns).index('Piráti')
out['ei_varianty'] = dict(
    p5=dict(kategorie=list(Y26.columns), goodman=[round(float(v) * 100, 1) for v in Bg[ip]], ipf=[round(float(v) * 100, 1) for v in Bj[ip]]),
    praha=None,
)
# Praha magistrát 2022 → 2026 (stejné bloky jako Sankey)
skp = data['rozsireni']['sankey_praha']
MBp = [('Piráti', r'^Česká pirátská'), ('SPOLU', r'^SPOLU'), ('STAN', r'^STAROSTOVÉ'), ('PRAHA SOBĚ', r'^PRAHA SOBĚ'), ('ANO', r'^ANO'), ('Ostatní', r'.')]
va22, ta22 = bloc_votes(2022, MAG, MBp)
va26, ta26 = bloc_votes(2026, MAG, MBp)
kq = stable(ta22, ta26)
Xq, Yq = composition(va22, ta22, kq), composition(va26, ta26, kq)
Bq = np.array(skp['matice'])
Bqj = ipf_ei(Xq.values, Yq.values, ta26.VOL_SEZNAM.loc[kq].values.astype(float), Bq, iters=100)
iq = list(Xq.columns).index('Piráti')
out['ei_varianty']['praha'] = dict(kategorie=list(Yq.columns), goodman=[round(float(v) * 100, 1) for v in Bq[iq]], ipf=[round(float(v) * 100, 1) for v in Bqj[iq]])
print('g)', out['ei_varianty'])

# ---------------------------------------------------------------- h) Monte Carlo mandátů
t3, hl, ros = KV[2026]
t5 = t3[(t3.KODZASTUP == P5) & (t3.OBEC == P5)]
h5 = hl[hl.ID_OKRSKY.isin(set(t5.ID_OKRSKY))].drop(columns=['OKRSEK'], errors='ignore').merge(t5[['ID_OKRSKY', 'OKRSEK']], on='ID_OKRSKY')
VO = h5.pivot_table(index='OKRSEK', columns='POR_STR_HL', values='POC_HLASU', aggfunc='sum', fill_value=0)
names = ros[ros.KODZASTUP == P5].set_index('POR_STR_HL').ZKRATKAO30
pir = next(p for p in VO.columns if names[p].startswith('Česká pirátská'))
sen = next(p for p in VO.columns if names[p].startswith('SEN '))


def seats(v):
    tot = v.sum()
    ok = v / tot >= 0.05
    q = sorted([(v[i] / d, i) for i in range(len(v)) if ok[i] for d in range(1, SEATS + 1)], reverse=True)[:SEATS]
    s = np.zeros(len(v), int)
    for _, i in q:
        s[i] += 1
    return s


base = VO.sum().values.astype(float)
s0 = seats(base)
ip_, is_ = list(VO.columns).index(pir), list(VO.columns).index(sen)
sim_n = 2000
boot_s = np.array([seats(VO.values[rng.integers(0, len(VO), len(VO))].sum(0).astype(float)) for _ in range(sim_n)])
noise_s = np.array([seats(base * (1 + rng.normal(0, 0.02, len(base)))) for _ in range(sim_n)])
noise1 = np.array([seats(base * (1 + rng.normal(0, 0.01, len(base)))) for _ in range(sim_n)])


def dist(arr, i):
    vals, cnt = np.unique(arr[:, i], return_counts=True)
    return {int(v): round(float(c) / len(arr) * 100, 1) for v, c in zip(vals, cnt)}


out['monte_carlo'] = dict(oficialne=int(s0[ip_]), simulaci=sim_n,
                          bootstrap_okrsku=dict(pirati=dist(boot_s, ip_), sen=dist(boot_s, is_)),
                          sum_2_procenta=dict(pirati=dist(noise_s, ip_), sen=dist(noise_s, is_)),
                          sum_1_procento=dict(pirati=dist(noise1, ip_), sen=dist(noise1, is_)))
print('h)', out['monte_carlo'])

# ---------------------------------------------------------------- i) srovnání s ostatními MČ
mc = pd.DataFrame(data['mc'])
mcp = mc[mc.mc_2022.notna() & mc.mc_2026.notna() & (mc.mc_samostatne_2022 == True) & (mc.mc_samostatne_2026 == True)].copy()
mcp['d_mc'] = mcp.mc_2026 - mcp.mc_2022
mcp['d_mag'] = mcp.mag_2026 - mcp.mag_2022
mcp['rel_mc'] = (mcp.mc_2026 / mcp.mc_2022 - 1) * 100
mcp['rel_mag'] = (mcp.mag_2026 / mcp.mag_2022 - 1) * 100
X_ = np.column_stack([np.ones(len(mcp)), mcp.rel_mag.values])
b_, *_ = np.linalg.lstsq(X_, mcp.rel_mc.values, rcond=None)
mcp['ocekavano'] = X_ @ b_
mcp['rezidual'] = mcp.rel_mc - mcp.ocekavano
res_sd = float(mcp.rezidual.std())
p5r = mcp[mcp.kod == P5].iloc[0]
out['srovnani_mc'] = dict(
    mc=[dict(nazev=r.nazev, mc_2022=r.mc_2022, mc_2026=r.mc_2026, rel_mc=round(r.rel_mc, 1), rel_mag=round(r.rel_mag, 1), ocekavano=round(r.ocekavano, 1),
             rezidual=round(r.rezidual, 1), p5=bool(r.kod == P5)) for r in mcp.sort_values('rel_mc').itertuples()],
    p5=dict(rel_mc=round(float(p5r.rel_mc), 1), ocekavano=round(float(p5r.ocekavano), 1), rezidual=round(float(p5r.rezidual), 1), z=round(float(p5r.rezidual / res_sd), 2),
            poradi=int((mcp.rel_mc > p5r.rel_mc).sum() + 1), z_kolika=int(len(mcp))),
    model=dict(b0=round(float(b_[0]), 2), b1=round(float(b_[1]), 2), r=round(float(mcp.rel_mc.corr(mcp.rel_mag)), 2)),
)
print('i)', out['srovnani_mc']['p5'], out['srovnani_mc']['model'])

data['doplneni'] = out
save(data, os.path.join(OUT, 'data.json'))
print('OK')
