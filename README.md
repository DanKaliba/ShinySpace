# ShinySpace – Piráti Praha 5, komunální volby 2026

Analýza výsledků Pirátů v komunálních volbách 2026 v Praze a na Praze 5 po volebních okrscích:
srovnání s KV 2022 a PS 2025, SEN a STAN, Senát (obvod 21), kampaňové akce a zápisy do škol.

**Web:** https://dankaliba.github.io/ShinySpace/

## Struktura

| Složka | Co v ní je | Kdo ji mění |
|---|---|---|
| [`zjisteni/`](zjisteni/) | zjištění a metodika v Markdownu – web je zobrazuje přímo | kdokoli z týmu, ručně |
| [`data/`](data/) | vygenerovaná data: `data.json` (web), CSV pro Excel, hranice okrsků | skripty |
| [`scripts/`](scripts/) | stažení zdrojů a výpočet (`download.sh`, `okr.py`, `build.py`, `schools.py`, `psefologie.py`, `rozsireni.py`, `census.py`, `doplneni.py`, `ei.py`) | při změně analýzy |
| [`.claude/skills/`](.claude/skills/) | skill `psefologie-okrsky` pro Claude Code: zdroje, nástrahy a metody této analýzy | když se metoda změní |
| [`web/`](web/) | stránka (HTML, JS, CSS) – čte `../data/` a `../zjisteni/` | při změně vzhledu |

Chceš doplnit zjištění? Uprav `zjisteni/hlavni-zjisteni.md` a commitni. Nová data? Spusť skripty a commitni `data/`.

## Lokální náhled

```bash
python -m http.server 8000      # v kořeni repozitáře
# http://localhost:8000/web/
```

## Přegenerování dat

```bash
bash scripts/download.sh dl                               # volby.gov.cz, Internet Archive, spadovostpraha.cz
python scripts/okr.py volby_source okrsky.json            # volební místnosti a ulice z Okrsky.docx
python scripts/build.py dl volby_source okrsky.json data
python scripts/schools.py dl data
python scripts/psefologie.py dl data                      # volatilita, ENP, mandáty, ekologická inference, Moranovo I (~2 min)
python scripts/rozsireni.py dl data                       # Sankey (P5 + Praha), Senát × Piráti, domovy pro seniory (~15 min)
python scripts/census.py dl data                          # demografie ze sčítání 2021: grid → okrsky, vzdělání po MČ
python scripts/doplneni.py dl data                        # věk 2026, MČ × magistrát, PS 2025 → KV 2026, účast, výstavba, Monte Carlo, srovnání MČ
```

`volby_source/` = interní podklady (kalendář akcí z Notionu, Okrsky.docx, mapování okrsků na čtvrti) – do repozitáře nepatří
(je v `.gitignore`). Web obsahuje jen veřejné akce bez jmen organizátorů. 2. kolo Senátu (16.–17. 10.) zatím v datech není.

Zdroje: ČSÚ – [volby.gov.cz](https://volby.gov.cz/opendata/opendata.htm), systém zápisů MČ Praha 5 (přes Internet Archive),
[spadovostpraha.cz](https://www.spadovostpraha.cz/), podkladové mapy © Esri.
