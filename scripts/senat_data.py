"""Načítání otevřených dat senátních voleb (volby.cz, 2008–2026): XML i CSV, starší i novější formát."""
import io, os, glob
import xml.etree.ElementTree as ET
import pandas as pd

YEARS = [2008, 2010, 2012, 2014, 2016, 2018, 2020, 2022, 2024]
PRAHA = {17, 19, 20, 21, 22, 23, 24, 25, 26, 27}


def read(path):
    if path.endswith('.xml'):
        return pd.DataFrame([{c.tag.split('}')[1]: c.text for c in r} for r in ET.parse(path).getroot()])
    raw = open(path, 'rb').read()
    try:
        txt = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        txt = raw.decode('cp1250')
    head = txt.split('\n', 1)[0]
    return pd.read_csv(io.StringIO(txt), sep=';' if head.count(';') > head.count(',') else ',', dtype=str)


def load(base, name):
    c = [p for p in glob.glob(os.path.join(base, '**', name + '.*'), recursive=True) if p.endswith(('.csv', '.xml'))]
    c.sort(key=lambda p: ('csv_od' not in p, p.endswith('.xml')))
    df = read(c[0])
    for col in df.columns:
        if col not in ('JMENO', 'PRIJMENI', 'TITULPRED', 'TITULZA', 'POVOLANI', 'BYDLISTEN', 'NAZEV_VS', 'PLATNOST'):
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def hl(df, c):
    return df[f'HLASY_{int(c):02d}'].fillna(0).astype(float)
