"""Recheck2 q05: is spectra_meta.json `source_column_note` correct? Reads the raw CSVs (read only, own split on ',')
and checks, for every selected spectrum, that CSV column `source_column` (1-based) holds the output's timestamp,
night id, solar / lunar elevation, lunar fraction (rows 1-5) and irradiance at row 6 + (w - 280), all as text.
Also checks that a 0-based reading would not match, and that CSV column 1 is a spectrum (row 1 field 1 is a
timestamp, no header column). Writes results/q05_source_column_note.txt."""
import json, re
R = "audits/night_spectra/recheck2_2026-10-04/results"
meta = json.load(open("data/derived/spectra/spectra_meta.json"), parse_float=str, parse_int=str)
L = [f"note: {meta['source_column_note']!r}"]
wl = [int(w) for w in meta["wavelength_nm"]]
TS = re.compile(r"\d\d-[A-Z][a-z]{2}-\d{4} \d\d:\d\d:\d\d")
for site, fn in (("philadelphia", "DRL_spectra.csv"), ("cherry_springs", "CSSP_spectra.csv")):
    raw = open(f"data/raw/spectra/spitschan2016/{fn}", "rb").read().decode("utf-8")
    assert "\r" not in raw and '"' not in raw
    rows = [ln.split(",") for ln in raw.rstrip("\n").split("\n")]  # rows[r-1][c-1] = CSV row r, column c (1-based)
    d = json.load(open(f"data/derived/spectra/{site}.json"), parse_float=str, parse_int=str)
    def col(c, r): return rows[r - 1][c - 1]
    m1 = {k: 0 for k in ("timestamp", "night_id", "solar", "lunar_el", "lunar_frac", "irradiance_cells")}
    m0_ts = 0
    for i, c in enumerate(int(x) for x in d["source_column"]):
        m1["timestamp"] += col(c, 1) == d["timestamp"][i]
        m1["night_id"] += col(c, 2) == d["night_id"][i]
        m1["solar"] += col(c, 3) == d["solar_elevation_deg"][i]
        m1["lunar_el"] += col(c, 4) == d["lunar_elevation_deg"][i]
        m1["lunar_frac"] += col(c, 5) == d["lunar_illuminated_fraction"][i]
        m1["irradiance_cells"] += sum(col(c, 6 + (w - 280)) == d["irradiance"][i][k] for k, w in enumerate(wl))
        m0_ts += rows[0][c] == d["timestamp"][i]  # 0-based reading: column index c
    L.append(f"== {site} ({fn}): {len(rows)} CSV rows, {len(rows[0])} fields in row 1 "
             f"(last field {rows[0][-1]!r}); CSV row 1 column 1 = {rows[0][0]!r} "
             f"({'timestamp' if TS.fullmatch(rows[0][0]) else 'NOT a timestamp'})")
    L.append(f"  1-based matches: " + ", ".join(f"{k} {v}" for k, v in m1.items()) + f" (of 240; cells of {240*281})")
    L.append(f"  0-based reading timestamp matches: {m0_ts}/240")
    for i in (0, 1, 120, 239):
        c = int(d["source_column"][i])
        L.append(f"  example spectrum {i}: source_column {c}; CSV row1 col {c} = {col(c,1)!r}; output timestamp "
                 f"{d['timestamp'][i]!r}; CSV row {6+(500-280)} (500 nm) col {c} = {col(c, 226)!r}; output "
                 f"{d['irradiance'][i][wl.index(500)]!r}")
open(f"{R}/q05_source_column_note.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
