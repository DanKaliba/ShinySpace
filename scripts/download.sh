#!/usr/bin/env bash
# Stáhne zdrojová data do složky dl/ (mimo repozitář). Použito 13. 10. 2026.
set -euo pipefail
D=${1:-dl}; mkdir -p "$D"; cd "$D"
B=https://volby.gov.cz/opendata
for f in kv2026/KV2026_data_20261011_csv kv2026/KV2026reg20261011_csv kv2026/KV2026ciselniky20261011_csv \
         se2026/SE2026data20261011_csv se2026/SE2026reg20261011_csv \
         kv2022/KV2022_data_20260328_csv kv2022/KV2022reg20260328_csv \
         ps2025/PS2025data20251005_csv ps2025/PS2025reg20251005_csv; do
  n=$(basename "$f"); mkdir -p "$n"; curl -sSL -o "$n/$n.zip" "$B/$f.zip"; (cd "$n" && unzip -oq "$n.zip")
done
mkdir -p geo && curl -sSL -o geo/kv2022_geo_vol_okrsky_2022g100.geojson "$B/kv2022/geo/vol_okrsky_2022g100.geojson"
# zápisy do škol (Internet Archive) a spádové obvody ZŠ
mkdir -p zapis/wb spad
curl -sSL -o zapis/wb/ms_2026.html "https://web.archive.org/web/20260517015248id_/https://zapisdoms-praha5.praha.eu/materske-skoly"
curl -sSL -o zapis/wb/ms_2025.html "https://web.archive.org/web/20250621222537id_/https://zapisdoms-praha5.praha.eu/materske-skoly"
curl -sSL -o zapis/wb/zs_2026.html "https://web.archive.org/web/20260519181720id_/https://zapisdozs-praha5.praha.eu/seznam-skol"
curl -sSL -o zapis/wb/zs_2025.html "https://web.archive.org/web/20250710125855id_/https://zapisdozs-praha5.praha.eu/seznam-skol"
curl -sSL -o spad/p2026.html https://www.spadovostpraha.cz/2026
curl -sSL -o spad/addr_2026.bin https://www.spadovostpraha.cz/data/addresses/2026
# registr sociálních služeb MPSV (domovy pro seniory)
mkdir -p rpss && curl -sSL -o rpss/rpss.json https://data.mpsv.cz/od/soubory/rpss/rpss.json
# Sčítání 2021 – Statistický atlas ČSÚ (1km grid přes Prahu 5 a ukazatele za pražské MČ)
mkdir -p census
B=https://geodata.csu.gov.cz/server/rest/services/Hosted
ENV="geometry=14.30,50.00,14.43,50.09&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&returnGeometry=true&f=geojson&outFields=*&where=1%3D1"
for l in sldb2021_obyvatelstvo/FeatureServer/15948 byty/FeatureServer/25948 srovnani_sldb/FeatureServer/245948 vyjizdka/FeatureServer/175948; do
  curl -sSL -o "census/${l%%/*}.geojson" "$B/$l/query?$ENV"
done
curl -sSL -o census/p5_zuj.json "$B/sldb2021_obyvatelstvo/FeatureServer/10051/query?where=kod%3D%27500143%27&outFields=*&returnGeometry=false&f=json"
curl -sSL -o census/praha_zuj.json "$B/sldb2021_obyvatelstvo/FeatureServer/10051/query?where=kod%20LIKE%20%275%25%27%20AND%20nazev%20LIKE%20%27Praha%25%27&outFields=*&returnGeometry=false&f=json"
# ČSÚ DataStat: obyvatelé po MČ podle pohlaví a základních věkových skupin (31. 12.), po rocích kvůli limitu odpovědi
mkdir -p csu
for y in 2021 2025; do
  curl -sSL -o "csu/oby02e_$y.csv" "https://data.csu.gov.cz/api/dotaz/v1/data/sady/OBY02E/vlastni?format=CSV&kodZvlast=true&kodCiselniku=true&CasRB.od=$y&CasRB.do=$y&UZ596H=*&POHL2=*&VekSkupZakl=*&IndicatorType=2406K2"
done

