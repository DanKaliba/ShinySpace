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
