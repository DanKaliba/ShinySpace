"""Kuriozity: datově správné, ale k ničemu (nebo skoro k ničemu) užitečné srovnání. Pro zasmání a jako ukázka, že korelace není příčina.

python -P scripts/kuriozity.py <dl_dir> data        (spouštět po hledani.py – používá čas zpracování okrsků)

1) povolání kandidátů v pražských MČ podle stran (IT × důchodci), 2) sudé × liché okrsky Prahy 5,
3) typ volební místnosti, 4) čas sečtení okrsku × výsledek Pirátů, 5) titul a délka příjmení × preferenční hlasy.
"""
import sys, os, json
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402
from kvdata import Data  # noqa: E402

DL, OUT = sys.argv[1:3]
rng = np.random.default_rng(2026)
D = Data(DL)
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = pd.DataFrame(data['okrsky']).set_index('okrsek')
out = {}

# ---------------------------------------------------------------- 1) povolání kandidátů (všechny kandidátky do MČ v Praze, KV 2026)
rk = D.rd('KV2026reg20261011_csv/csv_od/kvrk.csv')
rk = rk[rk.OKRES == 1100]
ros = D.kv(2026)[2]
m = rk.merge(ros[ros.OKRES == 1100][['KODZASTUP', 'POR_STR_HL', 'SLOZENI']], on=['KODZASTUP', 'POR_STR_HL'])
STRANY = [('720', 'Piráti'), ('768', 'ANO'), ('166', 'STAN'), ('053', 'ODS'), ('721', 'TOP 09'), ('1180', 'Praha sobě'), ('1114', 'SPD'), ('1178', 'Motoristé')]
m['strana'] = m.SLOZENI.map(lambda sl: next((n for c, n in STRANY if c in str(sl).split(',')), None))
m = m[m.strana.notna()]
P = m.POVOLANI.astype(str).str.lower()
m['it'] = P.str.contains(r'program|vývojář|developer|\bit\b|softwar|datov|data |analytik dat|digitaliz', regex=True)
m['duchodce'] = P.str.contains('důchod')
g = m.groupby('strana').agg(kandidatu=('it', 'size'), it=('it', 'mean'), duchodci=('duchodce', 'mean'), vek=('VEK', 'median'))
out['povolani'] = [dict(strana=s, kandidatu=int(r.kandidatu), it=round(float(r.it) * 100, 1), duchodci=round(float(r.duchodci) * 100, 1), vek=float(r.vek))
                   for s, r in g.sort_values('it', ascending=False).iterrows()]

# ---------------------------------------------------------------- 2) sudé × liché okrsky Prahy 5 (permutační test)
lich = (O.index % 2 == 1)
y = O.mc_2026.values
d_obs = y[~lich].mean() - y[lich].mean()
perm = np.array([(lambda s: y[~s].mean() - y[s].mean())(rng.permutation(lich)) for _ in range(20000)])
out['parita'] = dict(sude=round(float(y[~lich].mean()), 2), liche=round(float(y[lich].mean()), 2), rozdil=round(float(d_obs), 2),
                     p=round(float((np.abs(perm) >= abs(d_obs)).mean()), 2), sudych=int((~lich).sum()), lichych=int(lich.sum()))

# ---------------------------------------------------------------- 3) typ volební místnosti


def typ(mst):
    s = str(mst).lower()
    for k, v in (('mateřsk', 'mateřská škola'), ('umělecká', 'základní umělecká škola'), ('základní', 'základní škola'), ('gymn', 'gymnázium / střední škola'),
                 ('střední', 'gymnázium / střední škola'), ('sociálního zabezpečení', 'správa sociálního zabezpečení'), ('úřad', 'úřad městské části')):
        if k in s:
            return v
    return 'ostatní (vysoká škola, komunitní centrum…)'


O['typ_mistnosti'] = O.mistnost.map(typ)
t = O.groupby('typ_mistnosti').agg(okrsku=('mc_2026', 'size'), pirati=('mc_2026', 'mean'), zmena=('mc_delta', 'mean'))
out['mistnost'] = [dict(typ=k, okrsku=int(r.okrsku), pirati=round(float(r.pirati), 1), zmena=round(float(r.zmena), 1)) for k, r in t.sort_values('pirati', ascending=False).iterrows()]

# ---------------------------------------------------------------- 4) čas sečtení okrsku (dávky volby.gov.cz) × Piráti
H = pd.DataFrame(data['hledani']['okrsky']).set_index('okrsek')
H['t'] = pd.to_datetime(H.cas)
start = pd.Timestamp('2026-10-10 14:00:00')  # uzavření volebních místností
x = H.join(O[['mc_2026', 'odevzdano_2026', 'ctvrt']], rsuffix='_o')
x['hodin'] = (x.t - start).dt.total_seconds() / 3600
out['cas'] = dict(r_pirati=round(float(x.hodin.corr(x.mc_2026)), 2), r_obalky=round(float(x.hodin.corr(x.odevzdano_2026)), 2),
                  r_pirati_obalky=round(float(x.odevzdano_2026.corr(x.mc_2026)), 2),
                  body=[dict(okrsek=int(o), hodin=round(float(r.hodin), 2), pirati=round(float(r.mc_2026), 2), obalky=int(r.odevzdano_2026), ctvrt=str(r.ctvrt))
                        for o, r in x.iterrows() if pd.notna(r.hodin)])

# ---------------------------------------------------------------- 5) titul a délka příjmení × preferenční hlasy (relativně k průměru vlastní kandidátky)
rk['rel'] = rk.POCHLASU / rk.groupby(['KODZASTUP', 'POR_STR_HL']).POCHLASU.transform('mean')
rk = rk[np.isfinite(rk.rel)]
rk['titul'] = rk.TITULPRED.fillna('').astype(str).str.strip().str.len() > 0
a, b = rk[rk.titul].rel.values, rk[~rk.titul].rel.values
boot = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(2000)]
# kontrola: titul i pořadí na kandidátce (tituly bývají výš) – rozdíl po zohlednění pořadí
rk['por_bin'] = pd.qcut(rk.PORCISLO, 10, labels=False, duplicates='drop')
po = rk.groupby('por_bin').apply(lambda g_: g_[g_.titul].rel.mean() - g_[~g_.titul].rel.mean()).mean()
rk['delka'] = rk.PRIJMENI.astype(str).str.len()
out['titul'] = dict(s_titulem=round(float(a.mean()), 3), bez_titulu=round(float(b.mean()), 3), rozdil_pct=round(float(a.mean() / b.mean() - 1) * 100, 1),
                    p05=round(float(np.percentile(boot, 5)), 3), p95=round(float(np.percentile(boot, 95)), 3), kandidatu=int(len(rk)), s_titulem_n=int(len(a)),
                    rozdil_po_poradi=round(float(po), 3), r_delka=round(float(rk.delka.corr(rk.rel)), 3), r_poradi=round(float(rk.PORCISLO.corr(rk.rel)), 2))

data['kuriozity'] = out
save(data, os.path.join(OUT, 'data.json'))
print(json.dumps({k: v for k, v in out.items() if k != 'cas'}, ensure_ascii=False, indent=1)[:2500])
print({k: v for k, v in out['cas'].items() if k != 'body'})
