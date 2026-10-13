---
name: psefologie-okrsky
description: Analýza českých voleb po volebních okrscích z otevřených dat ČSÚ (volby.gov.cz) – komunální (KV), magistrát, Senát, Sněmovna. Použij, když se počítají výsledky stran po okrscích nebo čtvrtích, srovnání mezi volbami, volatilita (Pedersen), efektivní počet stran, přepočet mandátů D'Hondtem, kolik hlasů chybělo na mandát, přesuny voličů (ekologická inference), prostorové shluky (Moranovo I, LISA) nebo vztah výsledků ke kampani, školám či demografii. Nepoužívej pro průzkumy veřejného mínění ani pro zahraniční volby.
---

# Psefologie po okrscích (Česko)

Referenční implementace: `scripts/build.py`, `scripts/schools.py`, `scripts/psefologie.py` v repozitáři ShinySpace.
Vše jde jen s numpy + pandas (scipy/geopandas nejsou potřeba).

## 1. Data – odkud a jak spojovat

- Stránka voleb: `https://volby.gov.cz/opendata/<kv2026|kv2022|se2026|ps2025>/<id>_opendata.htm`; zip balíky
  `KV2026_data_<datum>_csv.zip` (výsledky okrsků), `KV2026reg<datum>_csv.zip` (registry), `KV2026ciselniky…`.
  Starší volby mají novější stav dat (KV 2022 → `KV2022_data_20260328_csv.zip`) a **obsahují i dodatečné volby** –
  filtruj `DATUMVOLEB == 20220923`.
- KV soubory (`csv_od/`): `kvt3` = okrsek × zastupitelstvo (voliči `VOL_SEZNAM`, obálky `ODEVZ_OBAL`, platné hlasy `PL_HL_CELK`,
  `KODZASTUP`); `kvhl` = hlasy listin (`POR_STR_HL`, `POC_HLASU`, preferenční `HLASY_01…`); `kvros` = listiny (`ZKRATKAO30`,
  `SLOZENI`, `PROCHLSTR`, `MAND_STR`); `kvrk` = kandidáti; `kvrzcoco` = zastupitelstva (**`MANDATY`**).
  Spojení: `kvhl.ID_OKRSKY → kvt3.ID_OKRSKY` (ID je okrsek × zastupitelstvo), listina `(KODZASTUP, POR_STR_HL) → kvros`.
- Praha: `OKRES == 1100`, magistrát `KODZASTUP == 554782` (`TYPZASTUP 1`), městská část `TYPZASTUP 2`, `OBEC` = kód MČ
  (Praha 5 = 500143). Okrsky Prahy 5 jsou 5001–5081.
- Strana v koalici: kódy v `SLOZENI` odděl čárkou a porovnávej celé kódy (Piráti `720`; `"1720"` není Piráti!). `080` = nezávislí kandidáti.
- Senát: `set5.csv` (okrsky, `OBVOD`, `KOLO`, `HLASY_<CKAND>`), `serk.csv` (kandidáti, `NAZEV_VS`). Sněmovna: `pst4.csv` + `pst4p.csv`
  (`KSTRANA` z `psrkl.csv`).
- Hranice okrsků: `opendata/kv2022/geo/vol_okrsky_2022g100.geojson` (WGS84, vlastnosti `CISLO`, `MOMC`, `OBEC`). Novější soubor
  nemusí být; ověř stabilitu okrsků porovnáním čísel a počtu voličů mezi roky.
- Školy (Praha 5): systém zápisů `zapisdoms-praha5.praha.eu` / `zapisdozs-praha5.praha.eu` (po skončení roku jen přes Internet Archive,
  CDX API `web.archive.org/cdx/search/cdx?url=…&from=2026`); spádové obvody ZŠ s polohou adres `spadovostpraha.cz/data/addresses/<rok>`
  + mapování obvod → škola v `__NEXT_DATA__` stránky `spadovostpraha.cz/<rok>`.

## 2. Nástrahy (všechny se už staly)

1. **Počet mandátů ber z `kvrzcoco.MANDATY`, nikdy z hlavy.** Praha 5 má 41, ne 45. Volič má v KV tolik hlasů, kolik je mandátů
   → „voliči“ ≈ hlasy ÷ mandáty (jen orientačně, lidé hlasy dělí).
2. `PROCHLSTR` je z přepočteného základu (neúplné kandidátky) – podíly spočtené z okrsků se mohou o desetiny lišit. Uveď to.
3. **Přepočet mandátů vždy ověř proti `MAND_STR`.** KV 2026 Praha 5 reprodukuje D'Hondt (dělitelé 1, 2, 3…) s 5% klauzulí pro všechny
   listiny (koalice TOP+KDU prošla s 5,85 %). Klauzuli neodhaduj ze zákona z paměti – vyzkoušej varianty a vezmi tu, co sedí.
4. Okrsek na adrese úřadu (Praha 5: 5008) má stovky „úředních“ trvalých pobytů → účast ~8 %. Z modelů účasti a z ekologické
   inference ho vyřaď, v podílech stran nech.
5. Koalice se mezi volbami mění (2022 SPOLEČNĚ = ODS+TOP, 2026 ODS zvlášť, TOP s KDU) → pro volatilitu a přesuny slučuj do bloků.
6. Mapové podklady CARTO teď chtějí API klíč (vodoznak). Bez klíče: Esri `Canvas/World_Light_Gray_Base` a `World_Dark_Gray_Base`.
7. Kalendář/podklady strany jsou interní – na veřejný web jen veřejné akce, bez jmen organizátorů a interních schůzí.

## 3. Metody

- **Volatilita (Pedersen):** `½ Σ |p_2026 − p_2022|` na blocích stran; celkem i po okrscích.
- **Efektivní počet stran (Laakso–Taagepera):** `1 / Σ p²` z hlasů i z mandátů.
- **Mandátové hrany:** kolik hlasů chybělo na další mandát = `poslední přidělený podíl × (n+1) − hlasy strany`; řekni, kdo poslední mandát drží.
  Rezerva = o kolik hlasů mohla strana přijít bez ztráty mandátu.
- **Plošný vs. poměrný swing:** porovnej RMSE modelů `p22 + Δ̄` a `p22 × poměr`. Pokud vyhrává poměrný, ztráty jsou úměrné síle.
- **Ekologická inference (přesuny voličů):** Goodmanova regrese s omezeními – kategorie = podíl na zapsaných voličích (strany přepočtené
  na voliče + nevoliči), matice přesunů s řádky na simplexu (projekce gradientu), váhy = počet voličů, bootstrap okrsků (≥ 200×) pro
  90% intervaly, citlivostní varianta „jen voliči“. Reportuj R² pro cílovou stranu a široké intervaly; je to orientační odhad (ekologický klam).
- **Prostorová autokorelace:** Moranovo I s k = 6 nejbližšími těžišti (řádkově standardizované), 999 permutací; LISA s podmíněnou
  permutací a **korekcí FDR (Benjamini–Hochberg)** – bez ní vyjde ~5 % falešných shluků. Zmiň okrajový efekt a MAUP.
- **Vztah k akcím/školám/demografii:** jen asociace. Akce nejsou rozmístěné náhodně (míří do silných míst), proto kontroluj výchozí
  úroveň (výsledek minulých voleb) a návrat k průměru; ukaž všechny specifikace, ne jen tu nejlepší. Ze 9 čtvrtí nic neusuzuj.
- **Odlehlé okrsky:** robustní z-skóre přes MAD > 3,5; hlavní výsledky ukaž s nimi i bez nich.

## 4. Kontrola před odevzdáním

- Každé číslo v textu dohledatelné ve výstupu skriptu; čísla psaná ručně do Markdownu po přegenerování dat přepočítat.
- Mandáty sedí na oficiální výsledek; počty okrsků sedí (Praha 5: 81).
- Ke každé korelaci velikost efektu a n; u mnoha testů korekce na vícenásobné testování.
- Neutrální jazyk: popisuj, nedoporučuj; řekni, kde data nestačí (kauzalita, přesuny voličů).
- Web vykreslit (headless Chrome `--dump-dom` / `--screenshot`) a zkontrolovat, že se všechny sekce naplnily.
