"""Volební analýza Pirátů – Praha a Praha 5 (KV 2022, PS 2025, KV 2026, Senát 2026).

python -P build.py <dl_dir> <volby_source_dir> <okrsky.json> <out_dir>
"""
import sys, os, re, json, math, html, unicodedata
from datetime import date
import pandas as pd
import numpy as np

DL, SRC, OKRJ, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
PIR = '720'
P5 = 500143
MC_SEATS = 41  # zastupitelstvo MČ Praha 5 (kvrzcoco.MANDATY) = počet hlasů jednoho voliče
MAG = 554782


def rd(p, **kw):
    return pd.read_csv(os.path.join(DL, p), low_memory=False, **kw)


def is_pir(slozeni):
    return PIR in str(slozeni).split(',')


# ---------------------------------------------------------------- KV
def load_kv(year):
    if year == 2026:
        t3 = rd('KV2026_data_20261011_csv/csv_od/kvt3.csv')
        hl = rd('KV2026_data_20261011_csv/csv_od/kvhl.csv')
        ros = rd('KV2026reg20261011_csv/csv_od/kvros.csv')
        rk = rd('KV2026reg20261011_csv/csv_od/kvrk.csv')
    else:
        t3 = rd('KV2022_data_20260328_csv/csv_od/kvt3.csv')
        hl = rd('KV2022_data_20260328_csv/csv_od/kvhl.csv')
        ros = rd('KV2022reg20260328_csv/csv_od/kvros.csv')
        rk = rd('KV2022reg20260328_csv/csv_od/kvrk.csv')
        t3 = t3[t3.DATUMVOLEB == 20220923]
        hl = hl[hl.DATUMVOLEB == 20220923]
        ros = ros[ros.DATUMVOLEB == 20220923]
        rk = rk[rk.DATUMVOLEB == 20220923]
    t3 = t3[t3.OKRES == 1100].copy()
    hl = hl[hl.OKRES == 1100].copy()
    ros = ros[ros.OKRES == 1100].copy()
    rk = rk[rk.OKRES == 1100].copy()
    ros['PIR'] = ros.SLOZENI.map(is_pir)
    hl = hl.merge(t3[['ID_OKRSKY', 'KODZASTUP', 'PL_HL_CELK', 'ODEVZ_OBAL', 'VOL_SEZNAM']], on='ID_OKRSKY')
    hl = hl.merge(ros[['KODZASTUP', 'POR_STR_HL', 'VSTRANA', 'ZKRATKAO30', 'NAZEVCELK', 'PIR']], on=['KODZASTUP', 'POR_STR_HL'], how='left')
    return t3, hl, ros, rk


K = {y: load_kv(y) for y in (2022, 2026)}
mc_names = K[2026][2][['KODZASTUP', 'NAZEVZAST']].drop_duplicates().set_index('KODZASTUP').NAZEVZAST.to_dict()
mc_names.pop(MAG, None)


def mag_party_table(y):
    ros = K[y][2]
    m = ros[ros.KODZASTUP == MAG][['POR_STR_HL', 'VSTRANA', 'ZKRATKAO30', 'HLASY_STR', 'PROCHLSTR', 'MAND_STR', 'PIR']]
    return m.sort_values('PROCHLSTR', ascending=False)


def pir_share(hl, t3, kod_filter, by):
    """Podíl Pirátů (pirátská listina) na platných hlasech, agregace podle 'by'."""
    h = hl[kod_filter(hl)]
    t = t3[kod_filter(t3)]
    pv = h[h.PIR == True].groupby(by).POC_HLASU.sum()
    tv = t.groupby(by).PL_HL_CELK.sum()
    return (pv / tv * 100).rename('pir')


# --- PS 2025
ps_t = rd('PS2025data20251005_csv/csv_od/pst4.csv')
ps_p = rd('PS2025data20251005_csv/csv_od/pst4p.csv')
ps_t = ps_t[ps_t.OKRES == 1100]
ps_p = ps_p[ps_p.OKRES == 1100]
PS_PIR_K = 16
ps_pir = ps_p[ps_p.KSTRANA == PS_PIR_K].groupby(['OBEC', 'OKRSEK']).POC_HLASU.sum()
ps_tot = ps_t.groupby(['OBEC', 'OKRSEK']).agg(PL=('PL_HL_CELK', 'sum'), ODEVZ=('ODEVZ_OBAL', 'sum'), VOL=('VOL_SEZNAM', 'sum'))
ps_okr = ps_tot.join(ps_pir.rename('PIRV')).fillna(0)
ps_okr['pir_ps25'] = ps_okr.PIRV / ps_okr.PL * 100
ps_okr['ucast_ps25'] = ps_okr.ODEVZ / ps_okr.VOL * 100

# ---------------------------------------------------------------- Praha – magistrát + MČ
out = {}
mag = {}
for y in (2022, 2026):
    t = mag_party_table(y)
    mag[y] = t
out['mag_parties'] = {
    str(y): [dict(nazev=r.ZKRATKAO30, pct=round(float(r.PROCHLSTR), 2), mandaty=int(r.MAND_STR or 0), hlasy=int(r.HLASY_STR), pir=bool(r.PIR))
             for r in mag[y].itertuples() if r.PROCHLSTR >= 1]
    for y in mag
}

mc_rows = []
for kod, name in sorted(mc_names.items(), key=lambda x: x[1]):
    row = dict(kod=int(kod), nazev=name)
    for y in (2022, 2026):
        t3, hl, ros, rk = K[y]
        # magistrát v území MČ (OBEC = MČ)
        tm = t3[(t3.KODZASTUP == MAG) & (t3.OBEC == kod)]
        hm = hl[(hl.KODZASTUP == MAG) & (hl.OBEC == kod)]
        if len(tm):
            row[f'mag_{y}'] = round(float(hm[hm.PIR == True].POC_HLASU.sum() / tm.PL_HL_CELK.sum() * 100), 2)
            row[f'ucast_{y}'] = round(float(tm.ODEVZ_OBAL.sum() / tm.VOL_SEZNAM.sum() * 100), 2)
            row[f'volici_{y}'] = int(tm.VOL_SEZNAM.sum())
        r = ros[(ros.KODZASTUP == kod) & (ros.PIR == True)]
        if len(r):
            r = r.sort_values('PROCHLSTR', ascending=False).iloc[0]
            row[f'mc_{y}'] = round(float(r.PROCHLSTR), 2)
            row[f'mc_mand_{y}'] = int(r.MAND_STR or 0)
            row[f'mc_list_{y}'] = r.ZKRATKAO30
            row[f'mc_samostatne_{y}'] = str(r.SLOZENI) == PIR
    ps = ps_okr.loc[kod] if kod in ps_okr.index.get_level_values(0) else None
    if ps is not None:
        row['ps25'] = round(float(ps.PIRV.sum() / ps.PL.sum() * 100), 2)
    mc_rows.append(row)
out['mc'] = mc_rows

# Praha celkem PS25
pt = ps_okr.sum()
out['praha_ps25'] = round(float(pt.PIRV / pt.PL * 100), 2)
for y in (2022, 2026):
    t3 = K[y][0]
    tm = t3[t3.KODZASTUP == MAG]
    out[f'praha_ucast_{y}'] = round(float(tm.ODEVZ_OBAL.sum() / tm.VOL_SEZNAM.sum() * 100), 2)

# ---------------------------------------------------------------- Praha 5 – strany v MČ
p5p = {}
for y in (2022, 2026):
    ros = K[y][2]
    r = ros[ros.KODZASTUP == P5].sort_values('PROCHLSTR', ascending=False)
    p5p[str(y)] = [dict(nazev=x.ZKRATKAO30, vstrana=int(x.VSTRANA), pct=round(float(x.PROCHLSTR), 2), mandaty=int(x.MAND_STR or 0),
                        hlasy=int(x.HLASY_STR), pir=bool(x.PIR)) for x in r.itertuples()]
out['p5_parties'] = p5p

# ---------------------------------------------------------------- Praha 5 – okrsky
okj = json.load(open(OKRJ, encoding='utf8'))
CT = {
    'Malvazinky': [5024, 5025, 5026, 5039, 5040, 5041, 5042, 5043],
    'Barrandov': list(range(5066, 5082)),
    'Jinonice': [5060, 5061, 5062, 5063],
    'Radlice': [5020, 5021, 5022, 5023],
    'Hlubočepy': [5064, 5065],
    'Smíchov': list(range(5001, 5020)) + list(range(5027, 5033)),
    'Hřebenka': [5033, 5034, 5035, 5036, 5037, 5038],
    'Košíře': [5044, 5045] + list(range(5048, 5060)),
    'Motol': [5046, 5047],  # doplněno podle Okrsky.docx (MŠ Kudrnova, Praha 5-Motol)
}
okr2ct = {o: c for c, l in CT.items() for o in l}
assert len(okr2ct) == 81, len(okr2ct)

rows = {}
for o in range(5001, 5082):
    rows[o] = dict(okrsek=o, ctvrt=okr2ct[o], mistnost=okj[str(o)]['mistnost'], adresa=okj[str(o)]['adresa'].split(',')[0])

for y in (2022, 2026):
    t3, hl, ros, rk = K[y]
    for kod, tag in ((P5, 'mc'), (MAG, 'mag')):
        t = t3[(t3.OBEC == P5) & (t3.KODZASTUP == kod)].set_index('OKRSEK')
        h = hl[(hl.OBEC == P5) & (hl.KODZASTUP == kod)]
        pv = h[h.PIR == True].groupby('OKRSEK').POC_HLASU.sum()
        allp = h.groupby(['OKRSEK', 'ZKRATKAO30']).POC_HLASU.sum().reset_index()
        for o in rows:
            if o not in t.index:
                continue
            tt = t.loc[o]
            rows[o][f'{tag}_{y}'] = round(float(pv.get(o, 0) / tt.PL_HL_CELK * 100), 2)
            if tag == 'mc':
                rows[o][f'volici_{y}'] = int(tt.VOL_SEZNAM)
                rows[o][f'odevzdano_{y}'] = int(tt.ODEVZ_OBAL)
                rows[o][f'ucast_{y}'] = round(float(tt.ODEVZ_OBAL / tt.VOL_SEZNAM * 100), 2)
                a = allp[allp.OKRSEK == o].sort_values('POC_HLASU', ascending=False)
                rows[o][f'vitez_{y}'] = a.iloc[0].ZKRATKAO30
                rows[o][f'vitez_pct_{y}'] = round(float(a.iloc[0].POC_HLASU / tt.PL_HL_CELK * 100), 2)
                # pořadí Pirátů v okrsku
                names = a.ZKRATKAO30.tolist()
                pirname = ros[(ros.KODZASTUP == P5) & (ros.PIR == True)].ZKRATKAO30.iloc[0]
                rows[o][f'mc_poradi_{y}'] = names.index(pirname) + 1 if pirname in names else None
                # "voličské ekvivalenty" = pirátské hlasy / počet mandátů (41 v Praze 5)
                rows[o][f'mc_volici_pir_{y}'] = round(float(pv.get(o, 0) / MC_SEATS), 1)

for o in rows:
    if (P5, o) in ps_okr.index:
        r = ps_okr.loc[(P5, o)]
        rows[o]['ps_2025'] = round(float(r.pir_ps25), 2)
        rows[o]['ucast_ps_2025'] = round(float(r.ucast_ps25), 2)

# Strany v okrscích 2026 (MČ) – podíly všech hlavních listin
t3, hl, ros, rk = K[2026]
h = hl[(hl.OBEC == P5) & (hl.KODZASTUP == P5)]
t = t3[(t3.OBEC == P5) & (t3.KODZASTUP == P5)].set_index('OKRSEK').PL_HL_CELK
shares = h.groupby(['OKRSEK', 'ZKRATKAO30']).POC_HLASU.sum().unstack(fill_value=0).div(t, axis=0) * 100
for o in rows:
    rows[o]['strany_2026'] = {k: round(float(v), 2) for k, v in shares.loc[o].items()}

# Konkurenti v MČ: SEN (Láska), STAN, PRAHA 5 SOBĚ, ODS/SPOLEČNĚ, TOP/KDU – podíly po okrscích 2022 a 2026
COMP = {'sen': r'^SEN|SEN 21', 'stan': r'^STAROSTOVÉ', 'p5sobe': r'^PRAHA 5 SOBĚ', 'ano': r'^ANO'}
for y in (2022, 2026):
    t3, hl, ros, rk = K[y]
    t = t3[(t3.OBEC == P5) & (t3.KODZASTUP == P5)].set_index('OKRSEK').PL_HL_CELK
    h = hl[(hl.OBEC == P5) & (hl.KODZASTUP == P5)]
    for key, rx in COMP.items():
        m = h[h.ZKRATKAO30.str.contains(rx, regex=True, na=False)]
        s = m.groupby('OKRSEK').POC_HLASU.sum() / t * 100
        for o in rows:
            rows[o][f'{key}_{y}'] = round(float(s.get(o, 0)), 2)
out['konkurent_nazvy'] = {str(y): {key: sorted(K[y][2][(K[y][2].KODZASTUP == P5) & K[y][2].ZKRATKAO30.str.contains(rx, regex=True, na=False)].ZKRATKAO30.unique().tolist())
                                   for key, rx in COMP.items()} for y in (2022, 2026)}

# ---------------------------------------------------------------- Senát 2026 – obvod 21
se = rd('SE2026data20261011_csv/csv_od/set5.csv')
serk = rd('SE2026reg20261011_csv/csv_od/serk.csv')
se5 = se[(se.OBEC == P5) & (se.KOLO == 1)].set_index('OKRSEK')
c21 = serk[serk.OBVOD == 21].sort_values('CKAND')
out['senat'] = dict(
    obvod=21,
    kandidati=[dict(c=int(r.CKAND), jmeno=f'{r.JMENO} {r.PRIJMENI}', navrh=r.NAZEV_VS[:90], pct=float(r.PROC_K1), hlasy=int(r.HLASY_K1),
                    postup=int(r.ZVOLEN_K1) == 2) for r in c21.itertuples()],
    ostatni_praha=[dict(obvod=int(r.OBVOD), jmeno=f'{r.JMENO} {r.PRIJMENI}', navrh=r.NAZEV_VS[:110], pct=float(r.PROC_K1), postup=int(r.ZVOLEN_K1) == 2,
                        pir='irát' in r.NAZEV_VS)
                   for r in serk[serk.OBVOD.isin([24, 27])].sort_values(['OBVOD', 'PROC_K1'], ascending=[True, False]).itertuples()],
)
se_p5 = se[(se.OBEC == P5) & (se.KOLO == 1)]
out['senat']['ucast_p5'] = round(float(se_p5.ODEVZ_OBAL.sum() / se_p5.VOL_SEZNAM.sum() * 100), 2)
p5tot = se_p5.PL_HL_CELK.sum()
out['senat']['p5_pct'] = {int(r.CKAND): round(float(se_p5[f'HLASY_{int(r.CKAND):02d}'].sum() / p5tot * 100), 2) for r in c21.itertuples()}
for o in rows:
    r = se5.loc[o]
    rows[o]['senat'] = {int(c): round(float(r[f'HLASY_{int(c):02d}'] / r.PL_HL_CELK * 100), 2) for c in c21.CKAND}
    rows[o]['senat_ucast'] = round(float(r.ODEVZ_OBAL / r.VOL_SEZNAM * 100), 2)

# ---------------------------------------------------------------- Kandidáti Pirátů Praha 5 (MČ) – preferenční hlasy
def cand_table(y, kod):
    t3, hl, ros, rk = K[y]
    por = int(ros[(ros.KODZASTUP == kod) & (ros.PIR == True)].POR_STR_HL.iloc[0])
    c = rk[(rk.KODZASTUP == kod) & (rk.POR_STR_HL == por)].sort_values('PORCISLO')
    return por, c


por26, c26 = cand_table(2026, P5)
h = hl[(hl.OBEC == P5) & (hl.KODZASTUP == P5) & (hl.POR_STR_HL == por26)].copy()
h['ctvrt'] = h.OKRSEK.map(okr2ct)
cands = []
ct_party = h.groupby('ctvrt').POC_HLASU.sum()
n_c = len(c26)
for r in c26.itertuples():
    col = f'HLASY_{int(r.PORCISLO):02d}'
    byct = h.groupby('ctvrt')[col].sum()
    # index preference: podíl kandidáta na hlasech listiny v čtvrti / podíl v celé MČ
    tot_share = h[col].sum() / h.POC_HLASU.sum()
    idx = {k: round(float((byct[k] / ct_party[k]) / tot_share * 100), 0) if tot_share > 0 else None for k in byct.index}
    cands.append(dict(poradi=int(r.PORCISLO), jmeno=f'{r.TITULPRED + " " if isinstance(r.TITULPRED, str) and r.TITULPRED else ""}{r.JMENO} {r.PRIJMENI}'.strip(),
                      vek=int(r.VEK), povolani=r.POVOLANI, hlasy=int(r.POCHLASU), pct=float(r.POCPROCVSE), mandat=r.MANDAT == 'A',
                      poradi_mand=int(r.PORADIMAND) if r.PORADIMAND else 0, poradi_nahr=int(r.PORADINAHR) if r.PORADINAHR else 0,
                      index_ctvrti=idx))
out['p5_kandidati'] = cands
out['p5_kandidati_2022'] = [dict(poradi=int(r.PORCISLO), jmeno=f'{r.JMENO} {r.PRIJMENI}', hlasy=int(r.POCHLASU), pct=float(r.POCPROCVSE), mandat=r.MANDAT == 'A')
                            for r in cand_table(2022, P5)[1].itertuples()]

# magistrátní kandidátka Pirátů – celopražsky + v Praze 5
pm, cm = cand_table(2026, MAG)
hm = hl[(hl.KODZASTUP == MAG) & (hl.POR_STR_HL == pm)]
hm5 = hm[hm.OBEC == P5]
out['mag_kandidati'] = [dict(poradi=int(r.PORCISLO), jmeno=f'{r.JMENO} {r.PRIJMENI}', hlasy=int(r.POCHLASU), pct=float(r.POCPROCVSE), mandat=r.MANDAT == 'A',
                             hlasy_p5=int(hm5[f'HLASY_{int(r.PORCISLO):02d}'].sum()),
                             pct_p5=round(float(hm5[f'HLASY_{int(r.PORCISLO):02d}'].sum() / hm5.POC_HLASU.sum() * 100 * 65 / 65), 2))
                        for r in cm.itertuples() if int(r.PORCISLO) <= 30]

# debaty "Na rovinu s …" – index preferencí hostujícího kandidáta magistrátní kandidátky v čtvrti debaty
hm5 = hm5.assign(ctvrt=hm5.OKRSEK.map(okr2ct))
HOSTS = [('Tereza', 'Nislerová', 'Motol', '11. 5.'), ('Adam', 'Zábranský', 'Jinonice', '20. 4.'), ('Magdalena', 'Valdmanová', 'Jinonice', '7. 4.'),
         ('Olga', 'Richterová', 'Hřebenka', '8. 6.'), ('Katerina', 'Demetrashvili', 'Barrandov', '28. 4.')]
deb = []
ct_tot = hm5.groupby('ctvrt').POC_HLASU.sum()
for jm, pr, ct, dt in HOSTS:
    r = cm[(cm.PRIJMENI == pr)]
    if not len(r):
        deb.append(dict(jmeno=f'{jm} {pr}', ctvrt=ct, datum=dt, na_kandidatce=False))
        continue
    col = f'HLASY_{int(r.iloc[0].PORCISLO):02d}'
    s = hm5.groupby('ctvrt')[col].sum() / ct_tot
    base = hm5[col].sum() / hm5.POC_HLASU.sum()
    idx = (s / base * 100).round(1)
    deb.append(dict(jmeno=f'{jm} {pr}', ctvrt=ct, datum=dt, na_kandidatce=True, poradi=int(r.iloc[0].PORCISLO),
                    index_v_ctvrti=float(idx[ct]), index_max=float(idx.max()), ctvrt_max=idx.idxmax(),
                    poradi_ctvrti=int((idx > idx[ct]).sum() + 1)))
out['debaty'] = deb

# ---------------------------------------------------------------- Kalendář akcí
cal_file = [f for f in os.listdir(SRC) if f.endswith('.htm')][0]
raw = open(os.path.join(SRC, cal_file), encoding='utf8').read()
body = re.sub(r'<script.*?</script>|<style.*?</style>', '', raw, flags=re.S)
txt = html.unescape(re.sub(r'<[^>]+>', '\n', body))
L = [l.strip() for l in txt.split('\n') if l.strip()]
start = L.index('Všechny akce') + 1
end = len(L) - 1 - L[::-1].index('Všechny akce')
L = L[start:end]
MONTHS = {m: i for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 1)}
date_re = re.compile(r'^(?:(%s) (\d{1,2}), (\d{4})|Last (Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday))(?: (\d{1,2}:\d{2}))?(?: → (?:(?:%s) \d{1,2}, \d{4} ?)?(\d{1,2}:\d{2})?)?$' % ('|'.join(MONTHS), '|'.join(MONTHS)))
events = []
i = 0
while i < len(L):
    if i + 1 < len(L) and L[i + 1] in ('Přihlásit se',) or (i + 2 < len(L) and L[i + 2] == 'Přihlásit se' and L[i + 1] in ('1', '(nepřihlašujte se)')):
        title = L[i]
        j = i + 1
        while j < len(L) and L[j] != 'Přihlásit se':
            j += 1
        j += 1
        ev = dict(title=title, dline=None, place=None)
        # další řádky do příštího titulku
        k = j
        block = []
        while k < len(L) and not (k + 1 < len(L) and L[k + 1] == 'Přihlásit se') and not (k + 2 < len(L) and L[k + 2] == 'Přihlásit se' and L[k + 1] in ('1', '(nepřihlašujte se)')):
            block.append(L[k])
            k += 1
        for b in block:
            if date_re.match(b) and ev['dline'] is None:
                ev['dline'] = b
            elif ev['place'] is None and ev['dline'] is not None and len(b) > 2 and b not in ('Anonymous', 'We') and not re.match(r'^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]$', b):
                # místo je řádek hned po datu (jméno organizátora následuje za iniciálou)
                ev['place'] = b
        # odfiltrovat jméno organizátora omylem zachycené jako místo
        idx = block.index(ev['place']) if ev['place'] in block else -1
        if idx > 0 and re.match(r'^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]$', block[idx - 1]):
            ev['place'] = None
        ev['_block'] = block
        events.append(ev)
        i = k
    else:
        i += 1

ORGANIZERS = set()
for e in events:
    b = e['_block']
    for a, nxt in zip(b, b[1:]):
        if re.match(r'^[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]$', a):
            ORGANIZERS.add(nxt)
# jména bez iniciály (Tomáš Bederka, Filip Karel, Anonymous) – poslední řádek bloku, který není místo ani datum
for e in events:
    if e['place'] and (e['place'] in ORGANIZERS or e['place'] in ('Tomáš Bederka', 'Filip Karel', 'Anonymous')):
        e['place'] = None

TODAY = date(2026, 10, 13)  # export kalendáře: "Last Wednesday" = 7. 10. 2026 apod.
WD = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def parse_date(e):
    t = e['title']
    m = date_re.match(e['dline'] or '')
    d = t_from = t_to = None
    if m:
        if m.group(1):
            d = date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
        t_from, t_to = m.group(5), m.group(6)
    tm = re.search(r'\((\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})?', t)
    if d is None and tm:
        d = date(int(tm.group(3) or 2026), int(tm.group(2)), int(tm.group(1)))
    if d is None and m and m.group(4):
        # "Last Wednesday" relativně k exportu (týden před 13. 10. 2026)
        wd = WD.index(m.group(4))
        delta = (TODAY.weekday() - wd) % 7 or 7
        d = date.fromordinal(TODAY.toordinal() - delta)
    return d, t_from, t_to


CT_KEYS = [
    ('Barrandov', ['Barrandov', 'Barandov', 'Chaplinovo', 'Tilleho', 'Trnkovo', 'Olgy Scheinpflugové']),
    ('Smíchov', ['Smíchov', 'Arbes', 'Anděl', 'Knížecí', 'Svatého Filipa', 'Nádražní', 'Císařská louka', 'Cindu']),
    ('Košíře', ['Košíř', 'U Zvonu', 'Klamovk', 'Kavalir', 'Husov', 'U Tenisu']),
    ('Jinonice', ['Jinonic', 'Butovic', 'Walterovo']),
    ('Radlice', ['Radlic', 'Na Pláni', 'Křížová', 'Laurová']),
    ('Malvazinky', ['Malvazink', 'Na Vinici']),
    ('Hřebenka', ['Hřebenk']),
    ('Motol', ['Motol', 'Kudrnova', 'Zahradníčkova']),
]
# kotevní okrsek místa akce (podle seznamu ulic v Okrsky.docx); None = jen čtvrť
ANCHOR = [
    ('Chaplinovo', 5071), ('Tilleho', 5075), ('Trnkovo', 5080), ('Arbes', 5004), ('Svatého Filipa', 5004),
    ('Anděl', 5011), ('Knížecí', 5016), ('Nádražní', 5010), ('Kavalír', 5049), ('Klamovk', 5050), ('Husov', 5030),
    ('U Tenisu', 5051), ('Jinonic', 5061), ('Walterovo', 5061), ('Na Pláni', 5024), ('Park na Pláni', 5024), ('Křížová', 5023), ('Laurová', 5022),
    ('Škola Radlice', 5021), ('Kudrnova', 5046), ('Zahradníčkova', 5047),
]


def classify(t):
    tl = t.lower()
    if 'napiš sem' in tl:
        return None
    if any(k in tl for k in ('schůze', 'školení', 'fundraising', 'sraz nováčků', 'setkání mediálu')):
        return 'Interní'
    if 'zahájení pirátské kampaně' in tl:
        return 'Interní'
    if 'debata' in tl:
        return 'Debata'
    if 'swap' in tl:
        return 'SWAP'
    if 'roznos' in tl and 'rozdávání' not in tl:
        return 'Roznos do schránek'
    if any(k in tl for k in ('úklid', 'ukliď', 'grilování', 'aukce', 'zahájení kampaně')):
        return 'Komunitní akce'
    if 'stan' in tl or 'stánek' in tl:
        return 'Stánek / stan'
    if 'rozdávání' in tl or 'rozádávání' in tl or 'prague: anděl' in tl:
        return 'Rozdávání letáků'
    return 'Jiné'


ev_out = []
for e in events:
    typ = classify(e['title'])
    if typ is None:
        continue
    d, tf, tt = parse_date(e)
    hay = e['title'] + ' ' + (e['place'] or '')
    ct = next((c for c, ks in CT_KEYS if any(k.lower() in e['title'].lower() for k in ks)), None)
    if ct is None:
        ct = next((c for c, ks in CT_KEYS if any(k.lower() in hay.lower() for k in ks)), None)
    anc = next((o for k, o in ANCHOR if k.lower() in (e['place'] or '').lower()), None) or next((o for k, o in ANCHOR if k.lower() in e['title'].lower()), None)
    hrs = None
    if tf and tt:
        a = int(tf.split(':')[0]) * 60 + int(tf.split(':')[1])
        b = int(tt.split(':')[0]) * 60 + int(tt.split(':')[1])
        hrs = round((b - a) / 60, 2) if b > a else None
    title = re.sub(r',—,-$', '', e['title']).strip()
    title = re.sub(r'\s*\(1\)$', '', title)
    place = e['place']
    if place:
        place = re.sub(r',? ?\d{3} \d{2} Prague, Czechia$|, Prague, Czechia$', '', place).strip()
    if typ == 'Interní' or (ct is None and typ != 'Debata'):
        ct_final = ct
    else:
        ct_final = ct
    ev_out.append(dict(datum=d.isoformat() if d else None, nazev=title, typ=typ, ctvrt=ct_final, misto=place, od=tf, do=tt, hodin=hrs, okrsek=anc,
                       volebni_den=bool(d and d in (date(2026, 10, 9), date(2026, 10, 10)))))
ev_out.sort(key=lambda x: x['datum'] or '')
ev_out = [e for e in ev_out if e['typ'] != 'Interní']  # interní schůze, školení a fundraising se nepublikují
out['akce'] = ev_out

# ---------------------------------------------------------------- Agregace podle čtvrtí
pub = [e for e in ev_out if e['typ'] != 'Interní' and e['datum'] and e['datum'] >= '2026-01-01']
ct_rows = []
for c, okl in CT.items():
    R = [rows[o] for o in okl]
    def wavg(key, w='odevzdano_2026'):
        num = sum(r[key] * r[w] for r in R if r.get(key) is not None)
        den = sum(r[w] for r in R if r.get(key) is not None)
        return round(num / den, 2) if den else None
    t3, hl, ros, rk = K[2026]
    def ct_share(y, kod):
        t3, hl, ros, rk = K[y]
        t = t3[(t3.OBEC == P5) & (t3.KODZASTUP == kod) & (t3.OKRSEK.isin(okl))]
        h = hl[(hl.OBEC == P5) & (hl.KODZASTUP == kod) & (hl.OKRSEK.isin(okl)) & (hl.PIR == True)]
        return round(float(h.POC_HLASU.sum() / t.PL_HL_CELK.sum() * 100), 2), round(float(t.ODEVZ_OBAL.sum() / t.VOL_SEZNAM.sum() * 100), 2), int(t.VOL_SEZNAM.sum())
    mc22, u22, v22 = ct_share(2022, P5)
    mc26, u26, v26 = ct_share(2026, P5)
    mg22, _, _ = ct_share(2022, MAG)
    mg26, _, _ = ct_share(2026, MAG)
    psv = ps_okr.loc[[(P5, o) for o in okl]]
    E = [e for e in pub if e['ctvrt'] == c]
    Ec = [e for e in E if e['datum'] >= '2026-09-01']
    ct_rows.append(dict(ctvrt=c, okrsku=len(okl), volici=v26, mc_2022=mc22, mc_2026=mc26, mag_2022=mg22, mag_2026=mg26,
                        ps_2025=round(float(psv.PIRV.sum() / psv.PL.sum() * 100), 2), ucast_2022=u22, ucast_2026=u26,
                        akci=len(E), akci_zari_rijen=len(Ec), akci_na_1000_volicu=round(len(E) / v26 * 1000, 2),
                        hodin=round(sum(e['hodin'] or 0 for e in E), 1),
                        typy={t: sum(1 for e in E if e['typ'] == t) for t in sorted(set(e['typ'] for e in pub))}))
out['ctvrti'] = ct_rows

# ---------------------------------------------------------------- Okrsky: blízkost akcí
geo = json.load(open(os.path.join(DL, 'geo/kv2022_geo_vol_okrsky_2022g100.geojson'), encoding='utf8'))


def centroid(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    A = cx = cy = 0
    for poly in polys:
        ring = poly[0]
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            c = x0 * y1 - x1 * y0
            A += c; cx += (x0 + x1) * c; cy += (y0 + y1) * c
    A /= 2
    return (cx / (6 * A), cy / (6 * A)) if A else tuple(np.mean(polys[0][0], axis=0))


p5_feats = [f for f in geo['features'] if f['properties']['MOMC'] == str(P5)]
cent = {int(f['properties']['CISLO']): centroid(f['geometry']) for f in p5_feats}


def dist_km(a, b):
    dx = (a[0] - b[0]) * 111.32 * math.cos(math.radians(50.07))
    dy = (a[1] - b[1]) * 110.57
    return math.hypot(dx, dy)


anchored = [e for e in pub if e['okrsek']]
for o, r in rows.items():
    r['lon'], r['lat'] = round(cent[o][0], 5), round(cent[o][1], 5)
    ds = [dist_km(cent[o], cent[e['okrsek']]) for e in anchored]
    r['akci_do_700m'] = sum(1 for d in ds if d <= 0.7)
    r['akci_kampan_do_700m'] = sum(1 for d, e in zip(ds, anchored) if d <= 0.7 and e['datum'] >= '2026-09-01')
    r['vzdalenost_akce_km'] = round(min(ds), 2) if ds else None
    for k in ('mc', 'mag'):
        if r.get(f'{k}_2026') is not None and r.get(f'{k}_2022') is not None:
            r[f'{k}_delta'] = round(r[f'{k}_2026'] - r[f'{k}_2022'], 2)
    if r.get('ps_2025') is not None:
        r['mc_vs_ps'] = round(r['mc_2026'] - r['ps_2025'], 2)
    r['ucast_delta'] = round(r['ucast_2026'] - r['ucast_2022'], 2)
out['okrsky'] = [rows[o] for o in sorted(rows)]

# ---------------------------------------------------------------- statistiky: akce vs. výsledek
df = pd.DataFrame(out['okrsky'])
stats = {}
for x in ('akci_do_700m', 'akci_kampan_do_700m', 'vzdalenost_akce_km'):
    for yv in ('mc_delta', 'mag_delta', 'mc_vs_ps', 'ucast_delta'):
        s = df[[x, yv]].dropna()
        stats[f'{x}~{yv}'] = round(float(s[x].corr(s[yv])), 3)
df['laska'] = [r['senat'][3] for r in out['okrsky']]
df['sen_delta'] = df.sen_2026 - df.sen_2022
df['stan_delta'] = df.stan_2026 - df.stan_2022
stats['mc_delta~stan_delta'] = round(float(df.mc_delta.corr(df.stan_delta)), 3)
stats['mc_2022~mc_delta'] = round(float(df.mc_2022.corr(df.mc_delta)), 3)
for a, b in (('mc_delta', 'sen_delta'), ('mc_2026', 'sen_2026'), ('mc_2022', 'sen_2022'), ('mc_2026', 'laska'), ('mc_delta', 'laska'),
             ('mc_2026', 'stan_2026'), ('mc_2026', 'p5sobe_2026'), ('mc_2026', 'ps_2025'), ('mc_2026', 'mag_2026'), ('sen_2026', 'laska')):
    stats[f'{a}~{b}'] = round(float(df[a].corr(df[b])), 3)
# Kolik okrsků: Piráti ztratili a SEN získal
stats['pir_down_sen_up'] = int(((df.mc_delta < 0) & (df.sen_delta > 0)).sum())
stats['pir_down'] = int((df.mc_delta < 0).sum())
# regrese: Δ MČ ~ akce + Δ účasti + výchozí úroveň 2022 (kontrola)
X = df[['akci_kampan_do_700m', 'ucast_delta', 'mc_2022', 'sen_delta']].astype(float)
X = (X - X.mean()) / X.std()
X.insert(0, 'const', 1.0)
yv = df.mc_delta.astype(float)
beta, *_ = np.linalg.lstsq(X.values, yv.values, rcond=None)
res = yv.values - X.values @ beta
sig2 = res @ res / (len(yv) - X.shape[1])
se_b = np.sqrt(np.diag(sig2 * np.linalg.inv(X.values.T @ X.values)))
stats['ols_mc_delta'] = {n: dict(b=round(float(b), 3), se=round(float(s), 3), t=round(float(b / s), 2)) for n, b, s in zip(X.columns, beta, se_b)}
stats['ols_r2'] = round(float(1 - (res @ res) / ((yv - yv.mean()) @ (yv - yv.mean()))), 3)
# skupiny: okrsky s ≥3 akcemi kampaně v okolí 700 m vs bez
g = df.assign(grp=np.where(df.akci_kampan_do_700m >= 3, 'hodně akcí (≥3)', np.where(df.akci_kampan_do_700m >= 1, 'pár akcí (1–2)', 'žádná akce')))
stats['skupiny'] = [dict(skupina=k, okrsku=int(len(v)), mc_2022=round(float((v.mc_2022 * v.odevzdano_2022).sum() / v.odevzdano_2022.sum()), 2),
                         mc_2026=round(float((v.mc_2026 * v.odevzdano_2026).sum() / v.odevzdano_2026.sum()), 2),
                         ps_2025=round(float(v.ps_2025.mean()), 2), ucast_delta=round(float(v.ucast_delta.mean()), 2))
                    for k, v in g.groupby('grp')]
out['stats'] = stats

# ---------------------------------------------------------------- souhrn Praha 5
t3, hl, ros, rk = K[2026]
summ = {}
for y in (2022, 2026):
    t3, hl, ros, rk = K[y]
    t = t3[(t3.OBEC == P5) & (t3.KODZASTUP == P5)]
    summ[f'ucast_{y}'] = round(float(t.ODEVZ_OBAL.sum() / t.VOL_SEZNAM.sum() * 100), 2)
    summ[f'volici_{y}'] = int(t.VOL_SEZNAM.sum())
    summ[f'odevzdano_{y}'] = int(t.ODEVZ_OBAL.sum())
    r = ros[(ros.KODZASTUP == P5) & (ros.PIR == True)].iloc[0]
    summ[f'mc_{y}'] = float(r.PROCHLSTR); summ[f'mc_mand_{y}'] = int(r.MAND_STR); summ[f'mc_hlasy_{y}'] = int(r.HLASY_STR)
    summ[f'mc_volici_{y}'] = round(r.HLASY_STR / MC_SEATS)
    tm = t3[(t3.OBEC == P5) & (t3.KODZASTUP == MAG)]
    hm = hl[(hl.OBEC == P5) & (hl.KODZASTUP == MAG) & (hl.PIR == True)]
    summ[f'mag_{y}'] = round(float(hm.POC_HLASU.sum() / tm.PL_HL_CELK.sum() * 100), 2)
ps5 = ps_okr.loc[P5]
summ['ps_2025'] = round(float(ps5.PIRV.sum() / ps5.PL.sum() * 100), 2)
summ['ps_2025_hlasy'] = int(ps5.PIRV.sum())
summ['ucast_ps_2025'] = round(float(ps5.ODEVZ.sum() / ps5.VOL.sum() * 100), 2)
out['p5'] = summ
for y in (2022, 2026):
    r = mag[y][mag[y].PIR == True].iloc[0]
    out[f'praha_mag_{y}'] = dict(pct=float(r.PROCHLSTR), mandaty=int(r.MAND_STR), hlasy=int(r.HLASY_STR))

# ---------------------------------------------------------------- geo výstupy
gp5 = dict(type='FeatureCollection', features=[dict(type='Feature', geometry=f['geometry'], properties={'o': int(f['properties']['CISLO'])}) for f in p5_feats])
json.dump(gp5, open(os.path.join(OUT, 'okrsky_p5.geojson'), 'w', encoding='utf8'), separators=(',', ':'))

# Praha – okrsky magistrát (podíl Pirátů 2026, Δ proti 2022)
mg = {}
for y in (2022, 2026):
    t3, hl, ros, rk = K[y]
    t = t3[t3.KODZASTUP == MAG].groupby(['OBEC', 'OKRSEK']).PL_HL_CELK.sum()
    h = hl[(hl.KODZASTUP == MAG) & (hl.PIR == True)].groupby(['OBEC', 'OKRSEK']).POC_HLASU.sum()
    mg[y] = (h / t * 100)
pr_feats = []
for f in geo['features']:
    p = f['properties']
    if p['OBEC'] != str(MAG):
        continue
    key = (int(p['MOMC']), int(p['CISLO']))
    v26 = mg[2026].get(key); v22 = mg[2022].get(key)
    if v26 is None or (isinstance(v26, float) and math.isnan(v26)):
        continue
    def rnd(g):
        if g['type'] == 'Polygon':
            return dict(type='Polygon', coordinates=[[[round(x, 4), round(y, 4)] for x, y in ring] for ring in g['coordinates']])
        return dict(type='MultiPolygon', coordinates=[[[[round(x, 4), round(y, 4)] for x, y in ring] for ring in poly] for poly in g['coordinates']])
    pr_feats.append(dict(type='Feature', geometry=rnd(f['geometry']),
                         properties=dict(m=int(p['MOMC']), o=int(p['CISLO']), p26=round(float(v26), 1), p22=round(float(v22), 1) if v22 is not None and not math.isnan(v22) else None)))
json.dump(dict(type='FeatureCollection', features=pr_feats), open(os.path.join(OUT, 'okrsky_praha.geojson'), 'w', encoding='utf8'), separators=(',', ':'))

json.dump(out, open(os.path.join(OUT, 'data.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

# CSV po okrscích (pro Excel)
flat = df.drop(columns=['strany_2026', 'senat']).copy()
for c in c21.itertuples():
    flat[f'senat_{c.PRIJMENI}'] = [r['senat'][int(c.CKAND)] for r in out['okrsky']]
flat.to_csv(os.path.join(OUT, 'okrsky_praha5.csv'), index=False, encoding='utf-8-sig', sep=';', decimal=',')
pd.DataFrame(ev_out).to_csv(os.path.join(OUT, 'akce.csv'), index=False, encoding='utf-8-sig', sep=';')
print('OK', len(ev_out), 'akcí;', len(pr_feats), 'pražských okrsků')
