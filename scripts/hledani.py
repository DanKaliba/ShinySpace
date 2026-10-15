"""Kde hledat hlasy na další mandát Pirátů v Praze 5 (KV 2026).

python -P scripts/hledani.py <dl_dir> data        (spouštět po forenzni.py)

- mandátová hrana: kolik hlasů Pirátům chybí, i když jiná kandidátka ztratí, a po opravě nalezených chyb,
- pořadí okrsků: rozdíl mezi Piráty v MČ a na magistrátu ve stejném okrsku (stejní voliči, stejný den),
  nadbytek neplatných lístků v MČ, hlasů na platný lístek, čas zpracování (dávky volby.gov.cz), nálezy kontroly dat.
Jde o pořadí, kde je největší šance najít chybu při sčítání – ne o důkaz chyby.
"""
import sys, os, json, urllib.request, xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402
from kvdata import Data, P5, MAG  # noqa: E402
from mandaty import allocate, votes_needed  # noqa: E402

DL, OUT = sys.argv[1:3]
D = Data(DL)
t3, hl, ros = D.kv(2026)
rk = D.rd('KV2026reg20261011_csv/csv_od/kvrk.csv')
rk = rk[rk.OKRES == 1100]
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
O = {o['okrsek']: o for o in data['okrsky']}

# ---------------------------------------------------------------- čas zpracování okrsků z dávek volby.gov.cz
DAV = os.path.join(DL, 'davky')
os.makedirs(DAV, exist_ok=True)
NS = '{http://www.volby.cz/kv/}'
cas = {}
i = 1
while True:
    f = os.path.join(DAV, f'd{i:05d}.xml')
    if not os.path.exists(f):
        try:
            b = urllib.request.urlopen(f'https://volby.gov.cz/appdata/kv2026/20261009/odata/okrsky/vysledky_okrsky_{i:05d}.xml', timeout=120).read()
        except Exception:
            break
        open(f, 'wb').write(b)
    root = ET.parse(f).getroot()
    dav = root.find(NS + 'DAVKA')
    for ok in root.iter(NS + 'OKRSEK'):
        if ok.get('CIS_OBEC') == str(P5) and ok.get('KODZASTUP') == str(P5):
            cas[int(ok.get('CIS_OKRSEK'))] = dict(cas=ok.get('DATUM_CAS_ZPRAC'), opakovane=ok.get('OPAKOVANE') != '0', davka=i)
    if dav is not None and dav.get('OKRSKY_ZPRAC') == dav.get('OKRSKY_CELKEM') and dav.get('OKRSKY_DAVKA') == '0':
        break
    i += 1

# ---------------------------------------------------------------- mandátová hrana
r5 = ros[ros.KODZASTUP == P5]
names = r5.set_index('POR_STR_HL').ZKRATKAO30
v = {names[p]: int(h) for p, h in zip(r5.POR_STR_HL, r5.HLASY_STR)}
nc = {names[p]: int((rk[(rk.KODZASTUP == P5) & (rk.POR_STR_HL == p)]).shape[0]) for p in r5.POR_STR_HL}
pir = next(n for n in v if n.startswith('Česká pirátská'))
sen = next(n for n in v if n.startswith('SEN '))
cur = allocate(v, nc, 41)[pir]
adj = {n: (v[n] / nc[n] * 41 if nc[n] < 41 else v[n]) for n in v}
prosly = [n for n in v if adj[n] / sum(adj.values()) * 100 >= 5]  # jen kandidátky nad 5% klauzulí mají nárok na mandát
quot = sorted([(v[n] / d, n, d) for n in prosly for d in range(1, 42)], reverse=True)
okq = [q for q in quot if allocate(v, nc, 41)[q[1]] >= q[2]]
posledni = okq[40] if len(okq) > 40 else okq[-1]
dalsi = [q for q in quot if q not in okq][:3]
need = votes_needed(v, nc, 41, pir, cur + 1)
need_sen = {b: votes_needed(v, nc, 41, pir, cur + 1, {sen: -b}) for b in (500, 1000, 2000, 5000)}
# opravy nalezených chyb v protokolech MČ (překlepy, neúplné řádky) – odhad změny hlasů kandidátek
korekce = {}
for n in data['forenzni']['nalezy']:
    if n['zastupitelstvo'] == 'MČ Praha 5' and n.get('korekce_hlasu') and n.get('listina') in v:
        korekce[n['listina']] = korekce.get(n['listina'], 0) + n['korekce_hlasu']
need_opr = votes_needed(v, nc, 41, pir, cur + 1, korekce)
hrana = dict(mandaty=cur, chybi_hlasu=need, chybi_plnych_volicu=round(need / 41, 1),
             posledni=dict(listina=posledni[1], mandat=posledni[2], podil=round(posledni[0], 1)),
             dalsi_v_poradi=[dict(listina=n, mandat=d, podil=round(q, 1)) for q, n, d in dalsi],
             pri_ztrate_sen={str(k): val for k, val in need_sen.items()}, minimum_pri_ztrate_sen=min(x for x in need_sen.values() if x is not None),
             po_oprave_chyb=need_opr, korekce=korekce)

# ---------------------------------------------------------------- okrsky
T = {k: t3[(t3.OBEC == P5) & (t3.KODZASTUP == k)].set_index('OKRSEK') for k in (P5, MAG)}


def share(kod, prefix):
    t = T[kod]
    h = hl[hl.ID_OKRSKY.isin(set(t.ID_OKRSKY))].drop(columns=['OKRSEK'], errors='ignore').merge(t.reset_index()[['ID_OKRSKY', 'OKRSEK']], on='ID_OKRSKY')
    nm = ros[ros.KODZASTUP == kod].set_index('POR_STR_HL').ZKRATKAO30
    por = next(p for p in nm.index if nm[p].startswith(prefix))
    return h[h.POR_STR_HL == por].set_index('OKRSEK').POC_HLASU


pm, pa = share(P5, 'Česká pirátská'), share(MAG, 'Česká pirátská')
df = pd.DataFrame(index=sorted(O))
df['pir_mc'] = pm
df['sh_mc'] = pm / T[P5].PL_HL_CELK
df['sh_mag'] = pa / T[MAG].PL_HL_CELK
ratio = df.sh_mc / df.sh_mag
med = ratio.drop(5008).median()
mad = (ratio.drop(5008) - med).abs().median() * 1.4826
df['z'] = (ratio - med) / mad
df['ocek'] = df.sh_mag * med * T[P5].PL_HL_CELK
df['deficit'] = df.ocek - df.pir_mc
obal = T[P5].ODEVZ_OBAL
nepl = obal - T[P5].PLAT_LISTKY
rate = nepl.sum() / obal.sum()
df['neplatne_mc'] = nepl
df['neplatne_mag'] = obal - T[MAG].PLAT_LISTKY
df['neplatne_navic'] = nepl - obal * rate
df['hlasu_na_listek'] = T[P5].PL_HL_CELK / T[P5].PLAT_LISTKY
df['obalky_rozdil'] = T[P5].VYD_OBALKY - T[P5].ODEVZ_OBAL
nal = {}
for n in data['forenzni']['nalezy']:
    if n.get('do_skore', True):
        nal.setdefault(n['okrsek'], []).append(n['typ'])
casy = pd.Series({o: pd.to_datetime(cas[o]['cas']) for o in cas})
pozde = set(casy.sort_values().index[-5:])
rows = []
for o in df.index:
    r = df.loc[o]
    duvody = []
    if r.deficit >= 150 and o != 5008:
        duvody.append(f'Piráti v MČ o {r.deficit:.0f} hlasů níž, než odpovídá magistrátu')
    if r.neplatne_navic >= 8:
        duvody.append(f'{int(r.neplatne_mc)} neplatných lístků v MČ (o {r.neplatne_navic:.0f} víc než průměr)')
    if r.neplatne_mc > 2 * max(r.neplatne_mag, 1) and r.neplatne_mc >= 10:
        duvody.append(f'neplatných v MČ {int(r.neplatne_mc)} proti {int(r.neplatne_mag)} na magistrátu')
    if o in pozde:
        duvody.append(f'zpracováno pozdě ({casy[o].day}. {casy[o].month}. {casy[o]:%H:%M})')
    if r.obalky_rozdil >= 10:
        duvody.append(f'{int(r.obalky_rozdil)} vydaných obálek chybí v urně')
    for t in sorted(set(nal.get(o, []))):
        duvody.append('kontrola dat: ' + t.lower())
    skore = max(r.deficit, 0) + 20 * max(r.neplatne_navic, 0) + 150 * len(set(nal.get(o, []))) + (150 if o in pozde else 0)
    rows.append(dict(okrsek=int(o), ctvrt=O[o]['ctvrt'], mistnost=O[o]['mistnost'], cas=cas.get(o, {}).get('cas'),
                     pir_mc=round(float(r.sh_mc) * 100, 2), pir_mag=round(float(r.sh_mag) * 100, 2), pomer=round(float(ratio[o]), 2), z=round(float(r.z), 2),
                     ocekavano=int(round(r.ocek)), skutecnost=int(r.pir_mc), deficit=int(round(r.deficit)), neplatne_mc=int(r.neplatne_mc), neplatne_mag=int(r.neplatne_mag),
                     neplatne_navic=round(float(r.neplatne_navic), 1), hlasu_na_listek=round(float(r.hlasu_na_listek), 2), obalky_rozdil=int(r.obalky_rozdil),
                     duvody=duvody, skore=round(float(skore)), zvlastni=o == 5008))
rows.sort(key=lambda x: -x['skore'])
for i, r in enumerate(rows, 1):
    r['poradi'] = i
data['hledani'] = dict(hrana=hrana, okrsky=rows, pomer_median=round(float(med), 3), neplatne_mc_pct=round(float(rate) * 100, 2),
                       posledni_okrsek=max(cas.items(), key=lambda kv: kv[1]['cas'])[0] if cas else None,
                       posledni_cas=max(x['cas'] for x in cas.values()) if cas else None)
save(data, os.path.join(OUT, 'data.json'))
print('hrana', json.dumps(hrana, ensure_ascii=False))
for r in rows[:12]:
    print(r['poradi'], r['okrsek'], r['ctvrt'], r['skore'], r['deficit'], r['cas'], '|', '; '.join(r['duvody']))
