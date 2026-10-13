"""Export okrskové tabulky Prahy 5 do CSV pro Excel – spouštět jako poslední krok (obsahuje všechny ukazatele).

python -P scripts/export_csv.py data
"""
import sys, os, json
import pandas as pd

OUT = sys.argv[1]
data = json.load(open(os.path.join(OUT, 'data.json'), encoding='utf8'))
kand = {str(k['c']): k['jmeno'].split()[-1] for k in data['senat']['kandidati']}
rows = []
for o in data['okrsky']:
    r = {k: v for k, v in o.items() if not isinstance(v, (dict, list))}
    for c, v in (o.get('senat') or {}).items():
        r[f'senat_{kand.get(str(c), c)}'] = v
    for k, v in (o.get('strany_2026') or {}).items():
        r[f'mc2026_{k[:40]}'] = v
    rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'okrsky_praha5.csv'), index=False, encoding='utf-8-sig', sep=';', decimal=',')
print('okrsky_praha5.csv', len(rows), 'řádků,', len(rows[0]), 'sloupců')
