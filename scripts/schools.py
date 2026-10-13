"""Zápisy do MŠ a 1. tříd ZŠ na Praze 5 (2025, 2026) + spádové obvody ZŠ → volební okrsky.

python -P schools.py <dl_dir> <out_dir>   (doplní data.json o klíč "skoly" a okrskům přidá ukazatele spádové ZŠ)
"""
import sys, os, re, json, html
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsonio import save  # noqa: E402

DL, OUT = sys.argv[1:3]
WB = os.path.join(DL, 'zapis', 'wb')
SP = os.path.join(DL, 'spad')


def parse_table(path):
    t = open(path, encoding='utf8').read()
    txt = html.unescape(re.sub(r'<[^>]+>', '\n', t))
    L = [l.strip() for l in txt.split('\n') if l.strip()]
    i = L.index('Průběžné výsledky') + 1
    L = L[i:]
    rows = []
    k = 0
    while k < len(L):
        if L[k].startswith('Děti ze spádové oblasti'):
            # zpětně: místa, adresa, název
            j = k - 1
            places = []
            while re.fullmatch(r'\d+|/', L[j]):
                if L[j] != '/':
                    places.insert(0, int(L[j]))
                j -= 1
            adresa = L[j]
            nazev = L[j - 1]
            rec = dict(nazev=nazev, adresa=adresa, mista=sum(places), mista_detail=places)
            m = k
            while m < len(L) and m < k + 12:
                lab = L[m]
                if lab.endswith(':') and m + 1 < len(L) and re.fullmatch(r'\d+', L[m + 1]):
                    key = {'Děti ze spádové oblasti:': 'spadove', 'Podaných žádostí:': 'zadosti', 'Přijatých dětí:': 'prijato', 'Přijatých žáků:': 'prijato',
                           'Nepřijatých dětí:': 'neprijato', 'Nepřijatých žáků:': 'neprijato', 'Přerušených řízení:': 'preruseno'}.get(lab)
                    if key:
                        rec[key] = int(L[m + 1])
                m += 1
            rows.append(rec)
            k += 10
        else:
            k += 1
    # souhrn nahoře
    head = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    head = re.sub(r'\s+', ' ', head)
    s = {}
    for lab, key in (('Vypsaných volných míst', 'mista'), ('Podaných žádostí', 'zadosti'), ('Přijatých dětí', 'prijato'), ('Přijatých žáků', 'prijato'),
                     ('Nepřijatých dětí', 'neprijato'), ('Nepřijatých žáků', 'neprijato')):
        m = re.search(lab + r':\s*(\d+)', head)
        if m and key not in s:
            s[key] = int(m.group(1))
    return rows, s


skoly = {}
for typ in ('ms', 'zs'):
    for y in (2025, 2026):
        rows, s = parse_table(os.path.join(WB, f'{typ}_{y}.html'))
        skoly[f'{typ}_{y}'] = dict(skoly=rows, souhrn=s)
        print(typ, y, len(rows), s, sum(r.get('prijato', 0) for r in rows), sum(r.get('neprijato', 0) for r in rows))

# ---------------------------------------------------------------- spádové obvody ZŠ 2026 → okrsky
page = open(os.path.join(SP, 'p2026.html'), encoding='utf8').read()
nd = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S).group(1))
mun = [m for m in nd['props']['pageProps']['data']['municipalities'] if m['code'] == 500143][0]
area_school = [a['schools'] for a in mun['areas']]
addr = json.load(open(os.path.join(SP, 'addr_2026.bin'), encoding='utf8'))['municipalities']['500143']['areas']
assert len(addr) == len(area_school)

geo = json.load(open(os.path.join(OUT, 'okrsky_p5.geojson'), encoding='utf8'))


def rings(g):
    return [p[0] for p in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']])]


polys = [(f['properties']['o'], [np.array(r) for r in rings(f['geometry'])]) for f in geo['features']]


def pip(x, y, ring):
    xs, ys = ring[:, 0], ring[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    c = ((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / (yj - ys + 1e-15) + xs)
    return c.sum() % 2 == 1


bbox = {o: (min(r[:, 0].min() for r in rs), max(r[:, 0].max() for r in rs), min(r[:, 1].min() for r in rs), max(r[:, 1].max() for r in rs)) for o, rs in polys}


def okrsek_of(lng, lat):
    for o, rs in polys:
        b = bbox[o]
        if b[0] <= lng <= b[1] and b[2] <= lat <= b[3] and any(pip(lng, lat, r) for r in rs):
            return o
    return None


# klíč obvodu: sdílené obvody (stejná množina adres) sloučit
obvody = {}
for i, pts in enumerate(addr):
    key = frozenset(p['address'] for p in pts)
    names = [s['name'] for s in area_school[i]]
    if key in obvody:
        obvody[key]['skoly'] += names
    else:
        obvody[key] = dict(skoly=names, body=pts)
counts = {}  # (okrsek, obvod_idx) -> adres
ob_list = list(obvody.values())
for j, ob in enumerate(ob_list):
    for p in ob['body']:
        o = okrsek_of(p['lng'], p['lat'])
        if o:
            counts[(o, j)] = counts.get((o, j), 0) + 1
print('obvodů', len(ob_list), 'přiřazeno adres', sum(counts.values()))


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower().replace('č', 'c').replace('ř', 'r').replace('š', 's').replace('ž', 'z').replace('ý', 'y').replace('á', 'a').replace('í', 'i').replace('é', 'e').replace('ě', 'e').replace('ú', 'u').replace('ů', 'u').replace('ň', 'n').replace('ť', 't').replace('ď', 'd').replace('ó', 'o'))


def match_school(name, rows):
    # podle čísla popisného / ulice v názvu
    n = norm(name)
    best = None
    for r in rows:
        a = norm(r['adresa'].split(',')[0])
        street = re.sub(r'\d.*', '', a)
        nums = re.findall(r'\d+', r['adresa'].split(',')[0])
        if street and street in n and all(x in name for x in nums[:1]):
            best = r
    return best


zs26 = skoly['zs_2026']['skoly']
zs25 = {r['nazev']: r for r in skoly['zs_2025']['skoly']}
ob_out = []
for j, ob in enumerate(ob_list):
    rs = [match_school(n, zs26) for n in ob['skoly']]
    assert all(rs), (ob['skoly'], rs)
    agg = {k: sum(r.get(k, 0) for r in rs) for k in ('mista', 'zadosti', 'prijato', 'neprijato')}
    # spádové děti jsou u sdíleného obvodu stejné číslo u obou škol → nesčítat
    agg['spadove'] = max(r.get('spadove', 0) for r in rs)
    r25 = [zs25.get(r['nazev']) for r in rs]
    agg25 = {k: sum((x or {}).get(k, 0) for x in r25) for k in ('mista', 'zadosti', 'prijato', 'neprijato')} if all(r25) else None
    if agg25:
        agg25['spadove'] = max(x.get('spadove', 0) for x in r25)
    lab = ' + '.join(re.sub(r'^.*?Praha 5 ?- ?[^,]+, ', '', r['nazev']).split(',')[0] for r in rs)
    lab = lab.replace('příspěvková organizace', '').strip()
    ob_out.append(dict(obvod=j, skoly=[r['nazev'] for r in rs], nazev=lab, **agg, r2025=agg25,
                       adres=len(ob['body'])))
for ob in ob_out:
    d = ob['prijato'] + ob['neprijato']
    ob['uspesnost'] = round(ob['prijato'] / d * 100, 1) if d else None
    ob['mista_na_spadove'] = round(ob['mista'] / ob['spadove'], 2) if ob['spadove'] else None
    ob['zadosti_na_misto'] = round(ob['zadosti'] / ob['mista'], 2) if ob['mista'] else None
    r = ob['r2025']
    if r:
        d = r['prijato'] + r['neprijato']
        r['uspesnost'] = round(r['prijato'] / d * 100, 1) if d else None
        r['mista_na_spadove'] = round(r['mista'] / r['spadove'], 2) if r['spadove'] else None

data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
okr = {o['okrsek']: o for o in data['okrsky']}
for o in okr.values():
    tot = sum(v for (oo, j), v in counts.items() if oo == o['okrsek'])
    parts = sorted([(j, v) for (oo, j), v in counts.items() if oo == o['okrsek']], key=lambda x: -x[1])
    o['zs_obvody'] = [dict(obvod=j, podil=round(v / tot, 3)) for j, v in parts] if tot else []
    real = [(j, v) for j, v in parts if ob_out[j]['spadove'] > 0]
    rt = sum(v for _, v in real)
    def w(key):
        vals = [(ob_out[j].get(key), v) for j, v in real if ob_out[j].get(key) is not None]
        s = sum(v for _, v in vals)
        return round(sum(x * v for x, v in vals) / s, 2) if s else None
    o['zs_skola'] = ob_out[real[0][0]]['nazev'] if real else None
    o['zs_uspesnost'] = w('uspesnost')
    o['zs_mista_na_spadove'] = w('mista_na_spadove')
    o['zs_zadosti_na_misto'] = w('zadosti_na_misto')
    vals25 = [(ob_out[j]['r2025']['uspesnost'], v) for j, v in real if ob_out[j]['r2025'] and ob_out[j]['r2025']['uspesnost'] is not None]
    s25 = sum(v for _, v in vals25)
    o['zs_uspesnost_2025'] = round(sum(x * v for x, v in vals25) / s25, 2) if s25 else None

# MŠ: celá Praha 5 je jeden spádový obvod → ukazatele po školách, poloha podle adresy (z adresních bodů spádovosti)
allpts = {}
for pts in addr:
    for p in pts:
        allpts[norm(p['address'].split(',')[0])] = (p['lng'], p['lat'])
ms_out = []
ms25 = {r['nazev']: r for r in skoly['ms_2025']['skoly']}
# Řádky, kde systém uvádí jen odloučené pracoviště: (název, adresa pro polohu)
MS_FIX = {
    'OP Naskové 1214/5': ('MŠ Slunéčko (Beníškové, Naskové, Pod Lipkami)', 'Naskové 1214'),
    'Chaplinovo nám. 1/615': ('ZŠ a MŠ Barrandov, Chaplinovo nám. (MŠ Renoirova 648)', 'Renoirova 648'),
    'Podbělohorská 2185': ('MŠ Podbělohorská 2185 (U Nesypky)', 'Podbělohorská 2185'),
    'Trojdílná 1117': ('MŠ Duha, Trojdílná 1117 (speciální třídy)', 'Trojdílná 1117'),
    'MŠ Peškova 963': ('FZŠ a MŠ Barrandov II (Peškova 963, Záhorského 887)', 'Peškova 963'),
}


def ms_label(r):
    if r['nazev'] in MS_FIX:
        return MS_FIX[r['nazev']]
    n = r['nazev']
    m = re.search(r'Praha 5 ?- ?([^,]+), ([^,]+?)(?:, příspěvková|$)', n)
    if 'Pohoda' in n:
        return 'MŠ Pohoda, Lohniského 851', 'Lohniského 851'
    if m:
        street = re.sub(r'(\d+)/(\d+)', r'\1/\2', m.group(2).strip())
        pre = 'ZŠ a MŠ' if n.startswith(('Základní', 'Tyršova', 'Fakultní')) else 'MŠ'
        lab = f'{pre} {street}'
        if 'Tyršova' in n:
            lab += f' ({r["adresa"]})'
        if 'Pedagogické fakulty' in n:
            lab = f'FZŠ a MŠ PedF UK ({r["adresa"]})'
        a = r['adresa'].split(',')[0] if 'Praha 5' not in r['adresa'].split(',')[0] else street
        if 'Radlice' in r['adresa']:
            a = 'Radlická 115'
        return lab, a
    return n, r['adresa']


for r in skoly['ms_2026']['skoly']:
    lab, a = ms_label(r)
    a = re.sub(r'(\d+)/(\d+)', lambda m: m.group(1) if int(m.group(1)) > int(m.group(2)) else m.group(2), a)  # č.p. = větší číslo
    nums = re.findall(r'\d+', a)
    street = re.sub(r'\s*\d.*', '', a).strip()
    cand = [k for k in allpts if k.startswith(norm(street)) and all(n in k for n in nums)]
    pos = allpts[cand[0]] if cand else None
    o = okrsek_of(*pos) if pos else None
    d = r.get('prijato', 0) + r.get('neprijato', 0)
    p25 = ms25.get(r['nazev'])
    d25 = (p25.get('prijato', 0) + p25.get('neprijato', 0)) if p25 else 0
    ms_out.append(dict(nazev=lab, adresa=r['adresa'], mista=r['mista'], zadosti=r.get('zadosti'), prijato=r.get('prijato'), neprijato=r.get('neprijato'),
                       uspesnost=round(r.get('prijato', 0) / d * 100, 1) if d else None, okrsek=o, ctvrt=okr[o]['ctvrt'] if o else None,
                       lon=pos[0] if pos else None, lat=pos[1] if pos else None,
                       uspesnost_2025=round(p25.get('prijato', 0) / d25 * 100, 1) if d25 else None, neprijato_2025=p25.get('neprijato') if p25 else None))
print('MŠ bez polohy:', [m['adresa'] for m in ms_out if not m['okrsek']])

# po čtvrtích: MŠ (podle polohy školky) a ZŠ (podle spádových obvodů okrsků, váženo voliči)
ct_rows = []
for c in sorted({o['ctvrt'] for o in okr.values()}):
    M = [m for m in ms_out if m['ctvrt'] == c]
    mm = {k: sum(m[k] or 0 for m in M) for k in ('mista', 'zadosti', 'prijato', 'neprijato')}
    d = mm['prijato'] + mm['neprijato']
    O = [o for o in okr.values() if o['ctvrt'] == c and o.get('zs_uspesnost') is not None]
    wv = sum(o['volici_2026'] for o in O)
    ct_rows.append(dict(ctvrt=c, ms_skol=len(M), ms_mista=mm['mista'], ms_zadosti=mm['zadosti'], ms_prijato=mm['prijato'], ms_neprijato=mm['neprijato'],
                        ms_uspesnost=round(mm['prijato'] / d * 100, 1) if d else None,
                        ms_zadosti_na_misto=round(mm['zadosti'] / mm['mista'], 2) if mm['mista'] else None,
                        zs_uspesnost=round(sum(o['zs_uspesnost'] * o['volici_2026'] for o in O) / wv, 1) if wv else None,
                        zs_skoly=sorted({o['zs_skola'] for o in O})))
ctv = {c['ctvrt']: c for c in data['ctvrti']}
for r in ct_rows:
    ctv[r['ctvrt']].update({k: v for k, v in r.items() if k != 'ctvrt'})
cdf = pd.DataFrame(data['ctvrti'])
cdf['mc_d'] = cdf.mc_2026 - cdf.mc_2022

# poloha ZŠ
for ob in ob_out:
    ob['pozice'] = []
    for i, schs in enumerate(area_school):
        for s in schs:
            if s['name'] in ob['skoly'] or any(norm(s['name'])[:40] == norm(n)[:40] for n in ob['skoly']):
                ob['pozice'].append(dict(lat=s['position']['lat'], lon=s['position']['lng']))

# souvislost s výsledky Pirátů
df = pd.DataFrame(data['okrsky'])
st = {}
for a in ('zs_uspesnost', 'zs_mista_na_spadove', 'zs_zadosti_na_misto'):
    for b in ('mc_2026', 'mc_delta', 'ucast_2026', 'sen_2026', 'stan_2026'):
        s = df[[a, b]].dropna()
        st[f'{a}~{b}'] = round(float(s[a].corr(s[b])), 3)
for a in ('ms_uspesnost', 'zs_uspesnost'):
    for b in ('mc_2026', 'mc_d'):
        s = cdf[[a, b]].dropna()
        st[f'ctvrti:{a}~{b}'] = round(float(s[a].corr(s[b])), 3)
data['skoly'] = dict(zs_obvody=ob_out, ms=ms_out, souhrn={k: v['souhrn'] for k, v in skoly.items()}, stats=st,
                     zs_2026_vse=skoly['zs_2026']['skoly'], zs_2025_vse=skoly['zs_2025']['skoly'])
save(data, os.path.join(OUT, 'data.json'))
for ob in ob_out:
    print(ob['nazev'][:40], ob['mista'], ob['spadove'], ob['zadosti'], ob['prijato'], ob['neprijato'], ob['uspesnost'], ob['mista_na_spadove'], (ob['r2025'] or {}).get('uspesnost'))
print(json.dumps(st, ensure_ascii=False))
print(df.groupby('zs_skola').okrsek.apply(list).to_string())

# CSV pro Excel: okrsky (+ spádová ZŠ) a školy
zs = pd.DataFrame([{k: v for k, v in o.items() if k not in ('r2025', 'pozice', 'skoly')} | {'uspesnost_2025': (o['r2025'] or {}).get('uspesnost')} for o in ob_out])
zs.to_csv(os.path.join(OUT, 'zapisy_zs_2026.csv'), index=False, encoding='utf-8-sig', sep=';', decimal=',')
pd.DataFrame(ms_out).to_csv(os.path.join(OUT, 'zapisy_ms_2026.csv'), index=False, encoding='utf-8-sig', sep=';', decimal=',')
print('CSV OK')
