"""Načítání okrskových výsledků KV a PS pro Prahu (otevřená data ČSÚ) a skládání bloků stran."""
import os, re
import pandas as pd

P5, MAG = 500143, 554782


class Data:
    def __init__(self, dl):
        self.dl = dl
        self._kv = {}

    def rd(self, p):
        return pd.read_csv(os.path.join(self.dl, p), low_memory=False)

    def kv(self, y):
        if y not in self._kv:
            if y == 2026:
                t3, hl, ros = self.rd('KV2026_data_20261011_csv/csv_od/kvt3.csv'), self.rd('KV2026_data_20261011_csv/csv_od/kvhl.csv'), self.rd('KV2026reg20261011_csv/csv_od/kvros.csv')
            else:
                t3, hl, ros = self.rd('KV2022_data_20260328_csv/csv_od/kvt3.csv'), self.rd('KV2022_data_20260328_csv/csv_od/kvhl.csv'), self.rd('KV2022reg20260328_csv/csv_od/kvros.csv')
                t3, hl, ros = (d[d.DATUMVOLEB == 20220923] for d in (t3, hl, ros))
            t3 = t3[t3.OKRES == 1100]
            self._kv[y] = (t3, hl[hl.ID_OKRSKY.isin(set(t3.ID_OKRSKY))], ros[ros.OKRES == 1100])
        return self._kv[y]

    def bloc_votes(self, y, kod, blocs, obec=None):
        """Hlasy bloků a voliči/obálky po okrscích (index OBEC, OKRSEK) pro zastupitelstvo `kod`."""
        t3, hl, ros = self.kv(y)
        t = t3[t3.KODZASTUP == kod]
        if obec:
            t = t[t.OBEC == obec]
        h = hl[hl.ID_OKRSKY.isin(set(t.ID_OKRSKY))].drop(columns=['OBEC', 'OKRSEK'], errors='ignore').merge(t[['ID_OKRSKY', 'OBEC', 'OKRSEK']], on='ID_OKRSKY')
        names = ros[ros.KODZASTUP == kod].set_index('POR_STR_HL').ZKRATKAO30
        h = h.assign(blok=h.POR_STR_HL.map(lambda p: next(b for b, rx in blocs if re.search(rx, names[p]))))
        v = h.pivot_table(index=['OBEC', 'OKRSEK'], columns='blok', values='POC_HLASU', aggfunc='sum', fill_value=0).reindex(columns=[b for b, _ in blocs], fill_value=0)
        return v, t.groupby(['OBEC', 'OKRSEK'])[['VOL_SEZNAM', 'ODEVZ_OBAL']].sum()

    def ps_votes(self, blocs, obec=None):
        t, p = self.rd('PS2025data20251005_csv/csv_od/pst4.csv'), self.rd('PS2025data20251005_csv/csv_od/pst4p.csv')
        k = self.rd('PS2025reg20251005_csv/csv_od/psrkl.csv').set_index('KSTRANA').ZKRATKAK30
        t, p = t[t.OKRES == 1100], p[p.OKRES == 1100]
        if obec:
            t, p = t[t.OBEC == obec], p[p.OBEC == obec]
        p = p.assign(blok=p.KSTRANA.map(lambda s: next(b for b, rx in blocs if re.search(rx, str(k.get(s, ''))))))
        v = p.pivot_table(index=['OBEC', 'OKRSEK'], columns='blok', values='POC_HLASU', aggfunc='sum', fill_value=0).reindex(columns=[b for b, _ in blocs], fill_value=0)
        return v, t.groupby(['OBEC', 'OKRSEK'])[['VOL_SEZNAM', 'ODEVZ_OBAL']].sum()


def composition(v, tt, keys):
    """Podíly kategorií na zapsaných voličích: bloky (přepočtené na voliče) + nevoliči."""
    sh = v.loc[keys].div(v.loc[keys].sum(axis=1), axis=0)
    X = sh.mul(tt.ODEVZ_OBAL.loc[keys], axis=0)
    X['Nevoliči'] = tt.VOL_SEZNAM.loc[keys] - tt.ODEVZ_OBAL.loc[keys]
    return X.div(tt.VOL_SEZNAM.loc[keys], axis=0)


def stable(t_a, t_b, lo=0.8, hi=1.25, minreg=150):
    """Okrsky se stejným číslem a podobným počtem voličů v obou volbách, bez „úředních“ okrsků."""
    keys = t_a.index.intersection(t_b.index)
    r = t_b.VOL_SEZNAM.reindex(keys) / t_a.VOL_SEZNAM.reindex(keys)
    ua = t_a.ODEVZ_OBAL.reindex(keys) / t_a.VOL_SEZNAM.reindex(keys)
    ub = t_b.ODEVZ_OBAL.reindex(keys) / t_b.VOL_SEZNAM.reindex(keys)
    return keys[(r > lo) & (r < hi) & (t_a.VOL_SEZNAM.reindex(keys) >= minreg) & (ua > 0.15) & (ub > 0.10)]


MC22 = [('Piráti', r'^Česká pirátská'), ('PRAHA 5 SOBĚ', r'^PRAHA 5 SOBĚ'), ('ODS, TOP 09, KDU', r'^SPOLEČNĚ PRO PRAHU 5|^KDU-ČSL, Zelení'), ('STAN', r'^STAROSTOVÉ'),
        ('SEN', r'SEN 21'), ('ANO', r'^ANO'), ('SPD, Motoristé a menší', r'.')]
MC26 = [('Piráti', r'^Česká pirátská'), ('PRAHA 5 SOBĚ', r'^PRAHA 5 SOBĚ'), ('ODS, TOP 09, KDU', r'^Občanská demokratická|^TOP Lidovci'), ('STAN', r'^STAROSTOVÉ'),
        ('SEN', r'^SEN '), ('ANO', r'^ANO'), ('SPD, Motoristé a menší', r'.')]
MAGB = [('Piráti', r'^Česká pirátská'), ('SPOLU', r'^SPOLU'), ('STAN', r'^STAROSTOVÉ'), ('PRAHA SOBĚ', r'^PRAHA SOBĚ'), ('ANO', r'^ANO'), ('Ostatní', r'.')]
PSB = [('Piráti', r'pirátská'), ('SPOLU', r'^SPOLU'), ('STAN', r'^STAROSTOVÉ'), ('ANO', r'^ANO'), ('SPD', r'SPD'), ('Motoristé', r'^Motoristé'), ('Ostatní', r'.')]
