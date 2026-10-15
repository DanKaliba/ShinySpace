"""Volební noc 2. kola Senátu (obvod 21): průběžný poměrový odhad konečného výsledku ze sečtených okrsků.

python -P scripts/senat_noc.py <dl_dir> <out_dir> --test        zpětný test na minulých druhých kolech (2008–2024)
python -P scripts/senat_noc.py <dl_dir> <out_dir> --live [s]    stahuje volby.gov.cz každých s sekund (výchozí 90) a píše <out_dir>/noc.html
python -P scripts/senat_noc.py <dl_dir> <out_dir> --jednou      jedno stažení a přepočet (např. pro kontrolu)

Metody (nebayesovské):
  posun   – v každé MČ (vrstvě) se spočítá, o kolik se podíl Sáblíka mezi finalisty ve sečtených okrscích posunul proti 1. kolu
            (vážený průměr) a poměr hlasů 2. kola k platným hlasům 1. kola; obojí se přenese na nesečtené okrsky téže MČ
            (bez sečtených okrsků v MČ se použije celkový posun),
  regrese – hlasy finalistů ve 2. kole ~ hlasy Lásky, Sáblíka a ostatních v 1. kole (nezáporné koeficienty, sečtené okrsky),
            od 15 sečtených okrsků.
Interval a šance na výhru: bootstrap sečtených okrsků (v rámci MČ). Sečtené okrsky nejsou náhodný vzorek (malé okrsky bývají
sečtené dřív), proto se posun počítá po MČ a vážený velikostí; zpětný test simuluje pořadí sčítání „malé okrsky dřív“.
"""
import sys, os, json, time, pickle, urllib.request, datetime as dt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from senat_data import load  # noqa: E402

DL, OUT, MODE = sys.argv[1], sys.argv[2], sys.argv[3]
PERIOD = int(sys.argv[4]) if len(sys.argv) > 4 else 90
OBVOD, LEAD, RUN = 21, 'Láska', 'Sáblík'
MC = {500143: 'Praha 5', 539694: 'Praha 13'}
API = 'https://volby.gov.cz/appdata/senat/20261009/vysled/okrsek/21/{obec}_{okrsek}.json'
rng = np.random.default_rng(2026)
os.makedirs(OUT, exist_ok=True)


def nnls(X, y):
    """Nezáporné nejmenší čtverce pro pár proměnných: přesně, přes všechny podmnožiny aktivních proměnných."""
    best, bb = np.inf, np.zeros(X.shape[1])
    for mask in range(1, 2 ** X.shape[1]):
        idx = [k for k in range(X.shape[1]) if mask >> k & 1]
        b, *_ = np.linalg.lstsq(X[:, idx], y, rcond=None)
        if (b >= 0).all():
            full = np.zeros(X.shape[1]); full[idx] = b
            e = float(((X @ full - y) ** 2).sum())
            if e < best:
                best, bb = e, full
    return bb


def projekce(d, sec, nboot=300):
    """d: okrsky s a1, b1, c1, valid1, vrstva (+ a2, b2 u sečtených); sec: maska sečtených. Vrací odhady podílu druhého finalisty."""
    sec = np.asarray(sec, bool)
    codes, strat = np.unique(d.vrstva.astype(str).values, return_inverse=True)
    K = len(codes)
    a1, b1, c1, v1 = (d[c].values.astype(float) for c in ('a1', 'b1', 'c1', 'valid1'))
    a2, b2 = d.a2.values.astype(float), d.b2.values.astype(float)
    h1 = b1 / np.maximum(a1 + b1, 1)
    ci, ui = np.flatnonzero(sec), np.flatnonzero(~sec)
    act_a, act_b = a2[ci].sum(), b2[ci].sum()
    w_all = a2 + b2
    sh2 = np.where(sec, b2 / np.maximum(w_all, 1), 0)

    def posun(ix):
        w, st = w_all[ix], strat[ix]
        dw = np.bincount(st, w * (sh2[ix] - h1[ix]), K)
        ws = np.bincount(st, w, K)
        vs = np.bincount(st, v1[ix], K)
        d_tot = dw.sum() / max(ws.sum(), 1e-9)
        r_tot = ws.sum() / max(vs.sum(), 1e-9)
        dk = np.where(ws > 0, dw / np.maximum(ws, 1e-9), d_tot)
        rk = np.where(ws > 0, ws / np.maximum(vs, 1e-9), r_tot)
        hl = v1[ui] * rk[strat[ui]]
        s_ = np.clip(h1[ui] + dk[strat[ui]], 0, 1)
        pa, pb = (hl * (1 - s_)).sum(), (hl * s_).sum()
        return (act_b + pb) / max(act_a + act_b + pa + pb, 1), act_a + act_b + pa + pb

    Xall = np.c_[a1, b1, c1]

    def regrese(ix):
        ba, bb = nnls(Xall[ix], a2[ix]), nnls(Xall[ix], b2[ix])
        pa, pb = float((Xall[ui] @ ba).sum()), float((Xall[ui] @ bb).sum())
        return (act_b + pb) / max(act_a + act_b + pa + pb, 1), act_a + act_b + pa + pb

    groups = [ci[strat[ci] == k] for k in range(K) if (strat[ci] == k).any()]
    out = {}
    metody = {'posun': posun}
    if len(ci) >= 15:
        metody['regrese'] = regrese
    for m, f in metody.items():
        est, hl = f(ci)
        boots = np.array([f(np.concatenate([rng.choice(g_, len(g_)) for g_ in groups]))[0] for _ in range(nboot if len(ui) else 0)]) if len(ui) else np.array([est])
        out[m] = dict(podil=float(est), p10=float(np.percentile(boots, 10)), p90=float(np.percentile(boots, 90)),
                      sance=float((boots > 0.5).mean()), hlasu=float(hl))
    return out


# ---------------------------------------------------------------- zpětný test
if MODE == '--test':
    races = pickle.load(open(os.path.join(DL, 'senat_hist', '_kola_okrsky.pkl'), 'rb'))
    PODILY = [0.05, 0.1, 0.2, 0.3, 0.5]
    rows = []
    for i, r in enumerate(races):
        d = r['d'].copy().reset_index(drop=True)
        d['vrstva'] = d.OBEC
        truth = d.b2.sum() / (d.a2 + d.b2).sum()
        # pořadí sčítání: malé okrsky dřív (s náhodou)
        order = np.argsort(d.reg1.values * rng.lognormal(0, 0.5, len(d)))
        for p in PODILY:
            k = max(1, int(round(p * len(d))))
            sec = np.zeros(len(d), bool); sec[order[:k]] = True
            pr = projekce(d, sec, nboot=60)
            for m, v in pr.items():
                rows.append(dict(kolo=i, rok=r['rok'], obvod=r['obvod'], praha=r['praha'], podil_secteno=p, metoda=m,
                                 chyba=(v['podil'] - truth) * 100, v_intervalu=v['p10'] <= truth <= v['p90'], vitez_ok=(v['podil'] > 0.5) == (truth > 0.5),
                                 sance=v['sance'], skutecne_druhy=truth > 0.5))
        if i % 40 == 0:
            print('kolo', i, '/', len(races), flush=True)
    T = pd.DataFrame(rows)
    T['brier'] = (T.sance - T.skutecne_druhy.astype(float)) ** 2
    S = T.groupby(['metoda', 'podil_secteno']).agg(kol=('chyba', 'size'), chyba_median=('chyba', lambda x: np.median(np.abs(x))), chyba_90=('chyba', lambda x: np.percentile(np.abs(x), 90)),
                                                   pokryti_80=('v_intervalu', 'mean'), vitez_spravne=('vitez_ok', 'mean'), brier=('brier', 'mean')).reset_index()
    Sp = T[T.praha].groupby(['metoda', 'podil_secteno']).agg(kol=('chyba', 'size'), chyba_median=('chyba', lambda x: np.median(np.abs(x))), vitez_spravne=('vitez_ok', 'mean')).reset_index()
    S.to_csv(os.path.join(OUT, 'test_noc.csv'), index=False, encoding='utf-8-sig', sep=';')
    chyby = {m: {str(p): T[(T.metoda == m) & (T.podil_secteno == p)].chyba.round(3).tolist() for p in PODILY} for m in T.metoda.unique()}
    json.dump(dict(vse=S.round(4).to_dict('records'), praha=Sp.round(4).to_dict('records'), chyby=chyby), open(os.path.join(OUT, 'test_noc.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    pd.set_option('display.width', 200)
    print(S.round(3).to_string()); print('Praha'); print(Sp.round(3).to_string())
    sys.exit()

# ---------------------------------------------------------------- volební noc
t26 = load(os.path.join(DL, 'SE2026data20261011_csv'), 'set5')
rk26 = load(os.path.join(DL, 'SE2026reg20261011_csv'), 'serk')
g = rk26[rk26.OBVOD == OBVOD]
ca, cb = int(g[g.PRIJMENI == LEAD].CKAND.iloc[0]), int(g[g.PRIJMENI == RUN].CKAND.iloc[0])
t = t26[(t26.OBVOD == OBVOD) & (t26.KOLO == 1)].copy()
base = pd.DataFrame({'obec': t.OBEC.astype(int).values, 'okrsek': t.OKRSEK.astype(int).values, 'reg1': t.VOL_SEZNAM.values.astype(float),
                     'valid1': t.PL_HL_CELK.values.astype(float), 'a1': t[f'HLASY_{ca:02d}'].fillna(0).values.astype(float),
                     'b1': t[f'HLASY_{cb:02d}'].fillna(0).values.astype(float)})
base['c1'] = base.valid1 - base.a1 - base.b1
base['vrstva'] = base.obec.map(MC)
pred_path = os.path.join(OUT, '..', 'bayes_detail.json')
PRED = {o['okrsek']: o['bayes_empiricky_a1'] for o in json.load(open(pred_path, encoding='utf8'))['okrsky']} if os.path.exists(pred_path) else {}
HIST = os.path.join(OUT, 'historie.json')
hist = json.load(open(HIST, encoding='utf8')) if os.path.exists(HIST) else []
RAW = os.path.join(OUT, 'raw'); os.makedirs(RAW, exist_ok=True)


TEST = os.path.join(OUT, 'test_noc.json')
CHYBY = json.load(open(TEST, encoding='utf8')).get('chyby', {}) if os.path.exists(TEST) else {}


def kalibruj(pr, podil_secteno):
    """Interval a šance ze skutečných chyb odhadu v minulých kolech při podobném podílu sečtených okrsků (bootstrap je příliš úzký)."""
    for m, v in pr.items():
        ch = CHYBY.get(m)
        if not ch:
            continue
        p = min(ch, key=lambda k: abs(float(k) - podil_secteno))
        E = np.array(ch[p])
        if len(E) < 20:
            continue
        est = v['podil'] * 100
        v.update(p10=(est - np.percentile(E, 90)) / 100, p90=(est - np.percentile(E, 10)) / 100, sance=float(np.mean(est - E > 50)), kalibrace=f'chyby {len(E)} minulých kol při {float(p) * 100:.0f} % sečtených')
    return pr


def stahni(obec, okrsek):
    """Vrátí (hlasy Láska, hlasy Sáblík, odevzdané obálky) za 2. kolo, nebo None, pokud okrsek ještě není sečtený."""
    try:
        j = json.loads(urllib.request.urlopen(API.format(obec=obec, okrsek=okrsek), timeout=30).read().decode('utf8'))
    except Exception:
        return None
    json.dump(j, open(os.path.join(RAW, f'{obec}_{okrsek}.json'), 'w', encoding='utf8'), ensure_ascii=False)
    k2 = [p for p in j.get('prehled', []) if p and p[0] == 2]
    if not k2:
        return None
    hl = {}
    for v in j.get('vysledky', []):
        if v[0] in (ca, cb) and v[7] is not None:
            hl[v[0]] = v[7]
    if len(hl) < 2:
        return None
    return hl[ca], hl[cb], k2[0][5] if len(k2[0]) > 5 else None


def html(d, sec, pr, stamp):
    c = d[sec]
    act_a, act_b = int(c.a2.sum()), int(c.b2.sum())
    rows = []
    for _, r in c.sort_values('okrsek').iterrows():
        sh = r.b2 / max(r.a2 + r.b2, 1) * 100
        p = PRED.get(int(r.okrsek))
        rows.append(f"<tr><td>{int(r.okrsek)}</td><td>{r.vrstva}</td><td>{int(r.a2)}</td><td>{int(r.b2)}</td><td><b>{sh:.0f} %</b></td><td>{r.b1 / max(r.a1 + r.b1, 1) * 100:.0f} %</td>"
                    + (f"<td>{p['sablik']:.0f} % ({p['p10']:.0f}–{p['p90']:.0f})</td><td class='{'up' if sh > p['p90'] else 'down' if sh < p['p10'] else ''}'>{sh - p['sablik']:+.0f}</td>" if p else '<td>–</td><td>–</td>') + '</tr>')
    mt = ''.join(f"<div class='tile'><div class='k'>Odhad konečného výsledku – {m}</div><div class='v'>Sáblík {v['podil'] * 100:.1f} %</div>"
                 f"<div class='d'>80% interval {v['p10'] * 100:.1f}–{v['p90'] * 100:.1f} % · šance Sáblíka {v['sance'] * 100:.0f} %</div></div>" for m, v in pr.items())
    hrows = ''.join(f"<tr><td>{h['cas'][11:16]}</td><td>{h['secteno']}</td><td>{h['sablik_aktualne']:.1f} %</td>" + ''.join(f"<td>{h.get(m, {}).get('podil', float('nan')) * 100:.1f} %</td>" for m in ('posun', 'regrese')) + '</tr>' for h in hist[::-1])
    return f"""<!doctype html><html lang="cs"><head><meta charset="utf-8"><meta http-equiv="refresh" content="60"><title>Senát 2. kolo – volební noc</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;margin:0;background:#f8f8f6;color:#1d1d1b}}main{{max-width:1000px;margin:0 auto;padding:20px 16px}}.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}}
.tile{{background:#fff;border:1px solid #e6e6e1;border-radius:10px;padding:14px}}.k{{color:#55554f;font-size:13px}}.v{{font-size:26px;font-weight:650}}.d{{color:#8a8a83;font-size:13px}}table{{border-collapse:collapse;width:100%;font-size:13.5px;background:#fff}}
td,th{{padding:4px 8px;border-bottom:1px solid #e6e6e1;text-align:right}}td:first-child,th:first-child{{text-align:left}}.up{{color:#2a78d6;font-weight:600}}.down{{color:#1b8f63;font-weight:600}}h2{{font-size:18px;margin:26px 0 8px}}</style></head><body><main>
<h1>Senát 2. kolo, obvod 21 – volební noc</h1><p>Aktualizováno {stamp} · stránka se obnovuje každou minutu · sečteno <b>{int(sec.sum())} z {len(d)}</b> okrsků
(Praha 5: {int((sec & (d.vrstva == 'Praha 5')).sum())}/81, Praha 13: {int((sec & (d.vrstva == 'Praha 13')).sum())}/58)</p>
<div class="tiles"><div class="tile"><div class="k">Sečteno zatím</div><div class="v">Láska {act_a} : Sáblík {act_b}</div><div class="d">Sáblík {act_b / max(act_a + act_b, 1) * 100:.1f} % sečtených hlasů</div></div>{mt}</div>
<p style="color:#55554f;font-size:13px">Odhad = sečtené hlasy + nesečtené okrsky dopočtené podle posunu proti 1. kolu v téže MČ (posun), případně regresí na výsledky 1. kola (regrese, od 15 okrsků). Interval a šance: podle skutečných chyb tohoto odhadu v minulých druhých kolech při stejném podílu sečtených okrsků (zpětný test). První sečtené okrsky bývají malé – v prvních minutách berte odhad s rezervou (viz zpětný test).</p>
<h2>Vývoj odhadu</h2><table><tr><th>čas</th><th>sečteno</th><th>Sáblík sečteno</th><th>odhad – posun</th><th>odhad – regrese</th></tr>{hrows}</table>
<h2>Sečtené okrsky × předpověď (Bayes + obhajoba)</h2><table><tr><th>okrsek</th><th>MČ</th><th>Láska</th><th>Sáblík</th><th>Sáblík %</th><th>1. kolo (ze dvou)</th><th>předpověď (80% int.)</th><th>rozdíl p. b.</th></tr>{''.join(rows)}</table>
<p style="color:#55554f;font-size:13px">Modře = Sáblík nad 80% intervalem předpovědi, zeleně = pod ním.</p></main></body></html>"""


def kolo():
    d = base.copy()
    d['a2'] = np.nan; d['b2'] = np.nan
    for i, r in d.iterrows():
        v = stahni(int(r.obec), int(r.okrsek))
        if v:
            d.loc[i, 'a2'], d.loc[i, 'b2'] = v[0], v[1]
    sec = d.a2.notna()
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if sec.sum() == 0:
        open(os.path.join(OUT, 'noc.html'), 'w', encoding='utf8').write(f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="60"><p>{stamp}: zatím žádný sečtený okrsek 2. kola.</p>')
        print(stamp, 'nic sečteno', flush=True)
        return 0
    pr = kalibruj(projekce(d, sec), sec.sum() / len(d))
    act = d[sec].b2.sum() / (d[sec].a2 + d[sec].b2).sum() * 100
    hist.append(dict(cas=stamp, secteno=int(sec.sum()), sablik_aktualne=float(act), **pr))
    json.dump(hist, open(HIST, 'w', encoding='utf8'), ensure_ascii=False)
    open(os.path.join(OUT, 'noc.html'), 'w', encoding='utf8').write(html(d, sec, pr, stamp))
    print(stamp, f'sečteno {int(sec.sum())}/{len(d)}', {m: f"{v['podil'] * 100:.1f} % ({v['p10'] * 100:.1f}–{v['p90'] * 100:.1f}), šance {v['sance'] * 100:.0f} %" for m, v in pr.items()}, flush=True)
    return int(sec.sum())


if MODE == '--simulace':  # zkouška stránky na minulém pražském kole (2024, obvod 26), sečteno 30 % okrsků od nejmenších
    races = pickle.load(open(os.path.join(DL, 'senat_hist', '_kola_okrsky.pkl'), 'rb'))
    r = next(x for x in races if x['rok'] == 2024 and x['obvod'] == 26)
    d = r['d'].rename(columns={'OBEC': 'obec', 'OKRSEK': 'okrsek'}).reset_index(drop=True)
    d['vrstva'] = d.obec.astype(str)
    sec = pd.Series(False, index=d.index); sec[np.argsort(d.reg1.values)[: int(0.3 * len(d))]] = True
    pr = kalibruj(projekce(d, sec), sec.sum() / len(d))
    hist = [dict(cas='2024-09-28 14:20:00', secteno=int(sec.sum()), sablik_aktualne=float(d[sec].b2.sum() / (d[sec].a2 + d[sec].b2).sum() * 100), **pr)]
    PRED = {}
    open(os.path.join(OUT, 'noc_simulace.html'), 'w', encoding='utf8').write(html(d, sec, pr, 'SIMULACE 2024, obvod 26'))
    print('skutečnost', round(d.b2.sum() / (d.a2 + d.b2).sum() * 100, 1), {m: round(v['podil'] * 100, 1) for m, v in pr.items()})
elif MODE == '--jednou':
    kolo()
else:
    while True:
        n = kolo()
        if n == len(base):
            print('sečteno vše', flush=True)
            break
        time.sleep(PERIOD)
