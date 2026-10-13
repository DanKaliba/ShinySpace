# Piráti Praha 5 – komunální volby 2026

Statický web s analýzou výsledků Pirátů v komunálních volbách 2026 v Praze a na Praze 5 po volebních okrscích
(srovnání s KV 2022 a PS 2025, SEN a STAN, Senát obvod 21, kampaňové akce, zápisy do škol).

Otevření lokálně: `python -m http.server` v této složce a pak http://localhost:8000 (soubor nejde otevřít přímo, data se načítají přes `fetch`).

## Přegenerování dat

```bash
bash scripts/download.sh ../dl                         # volby.gov.cz, Internet Archive, spadovostpraha.cz
python scripts/okr.py <složka volby_source> okrsky.json # volební místnosti a ulice z Okrsky.docx
python scripts/build.py ../dl <složka volby_source> okrsky.json data
python scripts/schools.py ../dl data
```

`volby_source` = interní podklady (kalendář akcí z Notionu, Okrsky.docx, mapování okrsků na čtvrti). Do repozitáře se nedávají;
web obsahuje jen veřejné akce bez jmen organizátorů.

Zdroje: ČSÚ – volby.gov.cz (otevřená data), systém zápisů MČ Praha 5 (přes Internet Archive), spadovostpraha.cz, podkladové mapy © Esri.
