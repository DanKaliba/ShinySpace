"""Kontrola dat a přepočet mandátů (inspirováno auditem volebnianalyza.suchan.cz).

python -P scripts/forenzni.py <dl_dir> data

1) Okrsky Prahy 5 (MČ i magistrát, KV 2026): obálky, nulové neplatné lístky, opravené zápisy, deficit strany proti sousedním
   okrskům (chybějící balík lístků), překlepy a neúplné řádky v preferenčních hlasech, Benfordův test 2. číslice.
2) Přepočet mandátů ve všech 57 MČ a na magistrátu podle zákona (5% klauzule s přepočtem pro neúplné kandidátky,
   D'Hondt, strop počtem kandidátů) a ověření proti oficiálním mandátům.
3) Preferenční pravidlo (10 % nad průměr na kandidáta) – ověření pořadí zvolených na všech listinách Prahy 5.
4) Rozhodující marže: kolik hlasů chybělo pirátským kandidátkám na další mandát a jaká byla rezerva; nejmenší marže celého
   zastupitelstva Prahy 5 (srovnání s auditem suchan.cz: 251 hlasů).
"""
import sys, os, json, math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402
from kvdata import Data, P5, MAG  # noqa: E402
from mandaty import allocate, margins  # noqa: E402

DL, OUT = sys.argv[1:3]
rng = np.random.default_rng(2026)
D = Data(DL)
t3, hl, ros = D.kv(2026)
rk = D.rd('KV2026reg20261011_csv/csv_od/kvrk.csv')
rk = rk[rk.OKRES == 1100]
coco = D.rd('KV2026reg20261011_csv/csv_od/kvrzcoco.csv').drop_duplicates('KODZASTUP').set_index('KODZASTUP').MANDATY
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}
ids = sorted(O)
URL = 'https://volby.gov.cz/app/kv2026/cs/20261009/results/!__0_1100_1100_500143___{o}'
URLJ = 'https://volby.gov.cz/appdata/kv2026/20261009/vysled/okrsek/1100/500143_{o}.json'
ZAST = {P5: 'MČ Praha 5', MAG: 'magistrát'}
nalezy = []


def nalez(typ, o, kod, subjekt, detail, jistota, vliv='bez vlivu na mandáty', listina=None, korekce=None, do_skore=True):
    nalezy.append(dict(typ=typ, okrsek=int(o), ctvrt=O[o]['ctvrt'], zastupitelstvo=ZAST[kod], subjekt=subjekt, detail=detail, jistota=jistota, vliv=vliv, do_skore=do_skore,
                       listina=listina, korekce_hlasu=None if korekce is None else int(round(korekce)),
                       url=URL.format(o=o), json=URLJ.format(o=o)))


# ---------------------------------------------------------------- 1) okrsky Prahy 5
T = {kod: t3[(t3.OBEC == P5) & (t3.KODZASTUP == kod)].set_index('OKRSEK') for kod in (P5, MAG)}
for kod, t in T.items():
    for o, r in t.iterrows():
        d = int(r.VYD_OBALKY - r.ODEVZ_OBAL)
        if d >= 20:
            nalez('Rozdíl vydaných a odevzdaných obálek', o, kod, f'{d} obálek', f'vydáno {int(r.VYD_OBALKY)}, odevzdáno {int(r.ODEVZ_OBAL)}: voliči převzali obálku, která v urně chybí', 'střední')
        if d < 0:
            nalez('Víc odevzdaných obálek než vydaných', o, kod, f'{-d} obálek', f'vydáno {int(r.VYD_OBALKY)}, odevzdáno {int(r.ODEVZ_OBAL)}', 'vysoká')
        if r.OPRAVA and int(r.OPRAVA) > 0:
            nalez('Opravený zápis', o, kod, 'zápis', f'okrsková komise zápis během zpracování opravila (OPRAVA = {int(r.OPRAVA)})', 'informativní')
zero = [o for o in ids if T[P5].loc[o, 'PLAT_LISTKY'] == T[P5].loc[o, 'ODEVZ_OBAL'] and T[MAG].loc[o, 'PLAT_LISTKY'] == T[MAG].loc[o, 'ODEVZ_OBAL']]
inval = {kod: 1 - T[kod].PLAT_LISTKY.sum() / T[kod].ODEVZ_OBAL.sum() for kod in T}
for o in zero:
    n = int(T[P5].loc[o, 'ODEVZ_OBAL'])
    p = (1 - inval[P5]) ** n * (1 - inval[MAG]) ** n
    nalez('Nulový počet neplatných lístků na obou lístcích', o, P5, f'{n} obálek',
          f'platných lístků = odevzdaných obálek v MČ i na magistrátu; při neplatnosti {inval[P5] * 100:.1f} % (MČ) a {inval[MAG] * 100:.1f} % (magistrát) je pravděpodobnost {p:.1e}', 'vysoká')

# sousedé podle těžišť okrsků
xy = np.array([[O[o]['lon'] * math.cos(math.radians(50.07)), O[o]['lat']] for o in ids])
Dm = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1))
NB = {o: [ids[j] for j in np.argsort(Dm[i])[1:7]] for i, o in enumerate(ids)}

for kod in (P5, MAG):
    t = T[kod]
    h = hl[hl.ID_OKRSKY.isin(set(t.ID_OKRSKY))].drop(columns=['OKRSEK'], errors='ignore').merge(t.reset_index()[['ID_OKRSKY', 'OKRSEK']], on='ID_OKRSKY')
    names = ros[ros.KODZASTUP == kod].set_index('POR_STR_HL').ZKRATKAO30
    ncand = rk[rk.KODZASTUP == kod].groupby('POR_STR_HL').size()
    seats = int(coco[kod])
    # hlasů na platný lístek (okrsek bez balíku lístků jedné strany má podezřele málo)
    hpl = (t.PL_HL_CELK / t.PLAT_LISTKY)
    share = h.pivot_table(index='OKRSEK', columns='POR_STR_HL', values='POC_HLASU', aggfunc='sum', fill_value=0).div(t.PL_HL_CELK, axis=0)
    for o in ids:
        nb = [n for n in NB[o] if n != 5008]
        if o == 5008:  # adresa úřadu – jiné složení voličů, srovnání se sousedy nedává smysl
            continue
        zh = (hpl[o] - hpl[nb].median()) / ((hpl[nb] - hpl[nb].median()).abs().median() * 1.4826 + 0.5)
        chybi_celkem = max(hpl[nb].median() - hpl[o], 0) * t.loc[o, 'PLAT_LISTKY']  # hlasů, které okrsku chybí proti sousedům
        for p in share.columns:
            med = share.loc[nb, p].median()
            mad = (share.loc[nb, p] - med).abs().median() * 1.4826 + 0.004
            z = (share.loc[o, p] - med) / mad
            deficit = (med - share.loc[o, p]) * t.loc[o, 'PL_HL_CELK']
            listku = deficit / max(ncand.get(p, seats), 1)  # přibližně lístků „s křížkem u strany“
            shoda = min(deficit, chybi_celkem) / max(deficit, chybi_celkem) if deficit > 0 and chybi_celkem > 0 else 0
            # buď výrazný deficit strany, nebo středně výrazný + současně málo hlasů na lístek a oba deficity si odpovídají
            if med > 0.03 and listku >= 15 and (z < -4 or (z < -2 and zh < -3 and shoda > 0.5)):
                nalez('Deficit strany proti sousedním okrskům (možný chybějící balík lístků)', o, kod, names[p],
                      f'podíl {share.loc[o, p] * 100:.1f} % proti mediánu sousedů {med * 100:.1f} % (robustní z = {z:.1f}); chybí řádově {deficit:,.0f} hlasů, tj. asi {listku:.0f} lístků; '
                      f'hlasů na lístek {hpl[o]:.1f} proti {hpl[nb].median():.1f} u sousedů (z = {zh:.1f}); shoda obou deficitů {shoda * 100:.0f} %'.replace(',', ' '),
                      'vysoká' if (zh < -3 and shoda > 0.5) else 'střední', 'chybí hlasy strany; ovlivní preferenční hlasy, na mandáty má vliv jen výjimečně')
        # kandidáti: překlepy (vložená/vypadlá číslice) a neúplně opsané řádky
        for p, g in h[h.OKRSEK == o].groupby('POR_STR_HL'):
            n = int(ncand.get(p, 0))
            if n == 0:
                continue
            v = g[[f'HLASY_{i:02d}' for i in range(1, n + 1)]].iloc[0].values.astype(float)
            med = np.median(v)
            if med < 8:
                continue
            for i, x in enumerate(v):
                if x >= 6 * med and abs(x / 10 - med) < 0.6 * med:
                    nalez('Překlep v hlasech kandidáta (vložená číslice)', o, kod, f'{names[p]}, kandidát č. {i + 1}', f'{int(x)} hlasů proti mediánu listiny {med:.0f}', 'vysoká', 'ovlivní pořadí preferenčních hlasů', names[p], round(x / 10) - x)
                elif 0 < x <= med / 6 and abs(x * 10 - med) < 0.6 * med:
                    nalez('Překlep v hlasech kandidáta (vypadlá číslice)', o, kod, f'{names[p]}, kandidát č. {i + 1}', f'{int(x)} hlasů proti mediánu listiny {med:.0f}', 'vysoká', 'ovlivní pořadí preferenčních hlasů', names[p], med - x)
            zeros = np.nonzero(v == 0)[0]
            if len(zeros) >= 2 and zeros[0] < n - 1 and np.all(v[zeros[0]:] == 0) and med >= 10:
                nalez('Neúplně opsané řádky kandidátů', o, kod, names[p], f'kandidáti č. {zeros[0] + 1}–{n} mají 0 hlasů, předchozí kolem {med:.0f}', 'vysoká', 'ovlivní preferenční hlasy', names[p], med * (n - zeros[0]))

# Testy podle DataTimes / Mahdalová & Škop (12. 10. 2026): nulové hlasy kandidátky a nízké využití hlasů.
# do_skore=False: potvrzují nebo doplňují jiné nálezy, do pořadí „kde hledat“ se nezapočítávají podruhé.
SH, NM = {}, {}
for kod in (P5, MAG):
    t = T[kod]
    h = hl[hl.ID_OKRSKY.isin(set(t.ID_OKRSKY))].drop(columns=['OKRSEK'], errors='ignore').merge(t.reset_index()[['ID_OKRSKY', 'OKRSEK']], on='ID_OKRSKY')
    NM[kod] = ros[ros.KODZASTUP == kod].set_index('POR_STR_HL').ZKRATKAO30
    SH[kod] = h.pivot_table(index='OKRSEK', columns='POR_STR_HL', values='POC_HLASU', aggfunc='sum').reindex(index=ids, columns=NM[kod].index).fillna(0)
for kod in (P5, MAG):
    t, piv, other = T[kod], SH[kod], MAG if kod == P5 else P5
    podil = piv.sum() / t.PL_HL_CELK.sum()
    for o in ids:
        for p in piv.columns:
            exp = podil[p] * t.loc[o, 'PL_HL_CELK']
            if piv.loc[o, p] == 0 and podil[p] >= 0.02 and exp >= 100:
                nm = NM[kod][p]
                po = NM[other][NM[other].str[:3] == nm[:3]].index
                obe = len(po) > 0 and SH[other].loc[o, po].sum() == 0
                nalez('Nulový počet hlasů kandidátky', o, kod, nm,
                      f'0 hlasů, podle podílu v Praze 5 ({podil[p] * 100:.1f} %) by se čekalo asi {exp:.0f}; '
                      + ('nulu má tato strana ve stejném okrsku i na druhém lístku, takže jde spíš o skutečný výsledek (malý okrsek, pár voličů této strany)' if obe else 'na druhém lístku tu strana hlasy má – stojí za kontrolu zápisu'),
                      'informativní' if obe else 'střední', do_skore=False)
                nalezy[-1]['detail'] = nalezy[-1]['detail'].replace('.', ',')
    seats = int(coco[kod])
    vyuz = t.PL_HL_CELK / (t.PLAT_LISTKY * seats) * 100
    med = vyuz[t.PLAT_LISTKY >= 50].median()
    for o in ids:
        if t.loc[o, 'PLAT_LISTKY'] >= 50 and vyuz[o] < med - 12:
            chybi = (med - vyuz[o]) / 100 * t.loc[o, 'PLAT_LISTKY'] * seats
            nalez('Nízké využití hlasů na lístku', o, kod, f'{vyuz[o]:.1f} % hlasů'.replace('.', ','),
                  f'voliči využili {vyuz[o]:.1f} % z možných {seats} hlasů na lístek proti mediánu Prahy 5 {med:.1f} %; proti mediánu chybí asi {chybi:,.0f} hlasů'.replace(',', ' ').replace('.', ','),
                  'střední', 'chybí hlasy; ovlivní preferenční hlasy, na mandáty má vliv jen výjimečně', do_skore=False)

# Benford – 2. číslice hlasů stran v okrscích (hlasy ≥ 10)
BEN2 = np.array([sum(math.log10(1 + 1 / (10 * k + d)) for k in range(1, 10)) for d in range(10)])
benford = {}
for kod in (P5, MAG):
    v = hl[hl.ID_OKRSKY.isin(set(T[kod].ID_OKRSKY))].POC_HLASU.values
    v = v[v >= 10]
    d2 = np.array([int(str(int(x))[1]) for x in v])
    obs = np.bincount(d2, minlength=10)
    exp = BEN2 * len(d2)
    chi = float(((obs - exp) ** 2 / exp).sum())
    sims = rng.multinomial(len(d2), BEN2, size=20000)
    chis = (((sims - exp) ** 2) / exp).sum(1)
    benford[ZAST[kod]] = dict(n=int(len(d2)), chi2=round(chi, 2), p=round(float((chis >= chi).mean()), 3),
                              pozorovano=[round(float(x) * 100, 1) for x in obs / len(d2)], ocekavano=[round(float(x) * 100, 1) for x in BEN2])

# ---------------------------------------------------------------- 2) přepočet mandátů (všechny MČ + magistrát)
repro = []
mar = []
for kod in sorted(ros.KODZASTUP.unique()):
    r = ros[ros.KODZASTUP == kod]
    seats = int(coco[kod])
    votes = dict(zip(r.POR_STR_HL, r.HLASY_STR.astype(int)))
    nc = rk[rk.KODZASTUP == kod].groupby('POR_STR_HL').size().to_dict()
    nc = {p: int(nc.get(p, seats)) for p in votes}
    s = allocate(votes, nc, seats)
    off = dict(zip(r.POR_STR_HL, r.MAND_STR.fillna(0).astype(int)))
    shoda = all(s[p] == off[p] for p in votes)
    repro.append(dict(kod=int(kod), nazev=r.NAZEVZAST.iloc[0], mandatu=seats, shoda=bool(shoda)))
    for p in r[r.SLOZENI.astype(str).str.split(',').map(lambda x: '720' in x)].POR_STR_HL:
        base, plus, minus = margins(votes, nc, seats, p)
        mar.append(dict(kod=int(kod), nazev=r.NAZEVZAST.iloc[0], listina=r.set_index('POR_STR_HL').ZKRATKAO30[p], mandatu_celkem=seats, mandaty=int(base),
                        oficialne=int(off[p]), chybelo_hlasu=int(plus), chybelo_volicu=round(plus / seats, 1), rezerva_hlasu=int(minus), rezerva_volicu=round(minus / seats, 1)))
# nejmenší rozhodující marže celého zastupitelstva Prahy 5 (kterákoli strana, +/−)
r5 = ros[ros.KODZASTUP == P5]
v5 = dict(zip(r5.POR_STR_HL, r5.HLASY_STR.astype(int)))
nc5 = {p: int(rk[(rk.KODZASTUP == P5) & (rk.POR_STR_HL == p)].shape[0]) for p in v5}
mm = []
for p in v5:
    if v5[p] < 0.03 * sum(v5.values()):
        continue
    base, plus, minus = margins(v5, nc5, 41, p)
    mm.append((plus, p, '+1 mandát')); mm.append((minus + 1, p, '−1 mandát'))
best = min(mm)
p5marze = dict(hlasu=int(best[0]), volicu=round(best[0] / 41, 1), listina=r5.set_index('POR_STR_HL').ZKRATKAO30[best[1]], zmena=best[2], suchan=251)

# ---------------------------------------------------------------- 3) preferenční pravidlo (Praha 5)
pref = []
for p, g in rk[rk.KODZASTUP == P5].groupby('POR_STR_HL'):
    seats_p = int(r5.set_index('POR_STR_HL').MAND_STR.fillna(0)[p])
    if seats_p == 0:
        continue
    avg = v5[p] / len(g)
    for prah in (0.05, 0.10):
        pr = g[g.POCHLASU >= avg * (1 + prah)].sort_values('POCHLASU', ascending=False).PORCISLO.tolist()
        rest = [c for c in g.sort_values('PORCISLO').PORCISLO if c not in pr]
        zvol = set((pr + rest)[:seats_p])
        off = set(g[g.MANDAT == 'A'].PORCISLO)
        pref.append(dict(listina=r5.set_index('POR_STR_HL').ZKRATKAO30[p], mandaty=seats_p, prah=int(prah * 100), shoda=zvol == off,
                         prumer=round(avg), hranice=round(avg * (1 + prah))))
pref_ok = {pr: all(x['shoda'] for x in pref if x['prah'] == pr) for pr in (5, 10)}

nal = sorted(nalezy, key=lambda x: ({'vysoká': 0, 'střední': 1, 'informativní': 2}[x['jistota']], x['okrsek']))
data['forenzni'] = dict(nalezy=nal, benford=benford, reprodukce=dict(zastupitelstev=len(repro), shoda=sum(x['shoda'] for x in repro), neshody=[x for x in repro if not x['shoda']]),
                        marze_pirati=sorted(mar, key=lambda x: x['chybelo_hlasu']), p5_marze=p5marze, preference=pref, preference_shoda=pref_ok,
                        neplatne_pct={ZAST[k]: round(v * 100, 2) for k, v in inval.items()})
save(data, os.path.join(OUT, 'data.json'))
print('nálezů', len(nal)); [print(' ', n['jistota'], n['okrsek'], n['zastupitelstvo'], n['typ'], '|', n['subjekt'], '|', n['detail'][:110]) for n in nal]
print('benford', {k: (v['chi2'], v['p']) for k, v in benford.items()})
print('reprodukce', data['forenzni']['reprodukce']['shoda'], '/', len(repro), data['forenzni']['reprodukce']['neshody'][:5])
print('P5 marže', p5marze)
print('preference', pref_ok, [(x['listina'][:20], x['prah'], x['shoda']) for x in pref])
print('pirátské marže', [(m['nazev'], m['mandaty'], m['oficialne'], m['chybelo_hlasu'], m['rezerva_hlasu']) for m in sorted(mar, key=lambda x: x['chybelo_hlasu'])[:10]])
