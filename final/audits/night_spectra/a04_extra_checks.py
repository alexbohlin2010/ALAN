"""Extra invariants (run from final/, stdlib only): raw NaN locations, chronological order and spacing of the selected
spectra, selected spectra per night block, source row-2 ('night id') behaviour, moon up/down among selected spectra,
fields of the outputs that carry no label/unit. Writes results/a04_extra.txt."""
import json, datetime
RAW = "data/raw/spectra/spitschan2016"; D = "data/derived/spectra"; OUT = "audits/night_spectra/results"
A = json.load(open(f"{OUT}/a02_extract.json"))
log = []
P = lambda *a: log.append(" ".join(str(x) for x in a))
fmt = "%d-%b-%Y %H:%M:%S"
for site, code in (("philadelphia", "DRL"), ("cherry_springs", "CSSP")):
    rows = [l.split(",") for l in open(f"{RAW}/{code}_spectra.csv", encoding="ascii").read()[:-1].split("\n")]
    rows[0] = rows[0][:-1] if rows[0][-1] == "" else rows[0]
    C = len(rows[0])
    P(f"[{site}]")
    nanrows = [r + 1 for r in range(5, 566) if any(v == "NaN" for v in rows[r])]
    P(f"  raw: CSV rows containing NaN: {nanrows[0]}..{nanrows[-1]} (= {280 + nanrows[0] - 6}..{280 + nanrows[-1] - 6} nm), "
      f"{len(nanrows)} rows; contiguous {nanrows == list(range(nanrows[0], nanrows[-1] + 1))}")
    allnan_cols = sum(all(rows[r][c] == "NaN" for r in range(5, 566)) for c in range(C))
    allzero_cols = sum(all(rows[r][c] != "NaN" and float(rows[r][c]) == 0 for r in range(5, 566)) for c in range(C))
    P(f"  raw: columns entirely NaN {allnan_cols}; entirely zero {allzero_cols}")
    t_all = [datetime.datetime.strptime(x, fmt) for x in rows[0]]
    P(f"  raw: timestamps strictly increasing in column order: {all(a < b for a, b in zip(t_all, t_all[1:]))}")
    J = json.load(open(f"{D}/{site}.json"))
    ts = [datetime.datetime.strptime(x, fmt) for x in J["timestamp"]]
    P(f"  output: selected timestamps strictly increasing: {all(a < b for a, b in zip(ts, ts[1:]))}")
    # selected timestamp == raw row 1 at source_column (1-based), independent of a02
    P(f"  output: timestamp[i] == raw row 1 at column source_column[i] for all i: "
      f"{all(rows[0][c - 1] == t for c, t in zip(J['source_column'], J['timestamp']))}")
    P(f"  output: solar_elevation_deg all < -18: {all(s < -18 for s in J['solar_elevation_deg'])}; max {max(J['solar_elevation_deg'])}")
    gaps = sorted({b - a for a, b in zip(J["source_column"], J["source_column"][1:])})
    P(f"  output: distinct column steps between consecutive selected spectra: {gaps}")
    # per night block
    sol = [float(v) for v in rows[2]]
    night = [c for c in range(C) if sol[c] < -18]
    blocks = []
    for c in night:
        if blocks and c == blocks[-1][1] + 1: blocks[-1][1] = c
        else: blocks.append([c, c])
    per = [sum(a + 1 <= sc <= b + 1 for sc in J["source_column"]) for a, b in blocks]
    P(f"  night blocks: {len(blocks)}; source columns (1-based) {[[a + 1, b + 1] for a, b in blocks]}; "
      f"spectra per block {[b - a + 1 for a, b in blocks]}; selected per block {per}")
    P(f"  block date spans: {[(rows[0][a], rows[0][b]) for a, b in blocks]}")
    ids = sorted(set(J["night_id"]))
    P(f"  output night_id distinct values: {ids}")
    split = [(rows[1][a], rows[1][b]) for a, b in blocks if rows[1][a] != rows[1][b]]
    P(f"  night blocks whose source row-2 value changes inside the block: {len(split)} {split}")
    lun = J["lunar_elevation_deg"]
    P(f"  selected spectra with lunar elevation > 0: {sum(x > 0 for x in lun)} of {len(lun)}; "
      f"lunar fraction range {min(J['lunar_illuminated_fraction'])}..{max(J['lunar_illuminated_fraction'])}")
    P(f"  zero cells in selected output by wavelength (top 5): "
      f"{sorted(((sum(1 for r in J['irradiance'] if r[j] == 0), 280 + 2 * j) for j in range(281)), reverse=True)[:5]}")
    P(f"  site file has unit / wavelength / source URL / time-zone fields: "
      f"{[k for k in ('unit', 'wavelength_nm', 'source_url', 'timestamp_format') if k in J]}")
    unl = [k for k in J if k not in J["labels"] and k not in ("labels",)]
    P(f"  site-file keys with no entry in 'labels': {unl}")
M = json.load(open(f"{D}/spectra_meta.json"))
P("[spectra_meta] labelled blocks:", [k for k, v in M.items() if isinstance(v, dict) and "label" in v],
  "| has source citation:", "source" in M, "| has source_url:", "source_url" in M)
open(f"{OUT}/a04_extra.txt", "w").write("\n".join(log) + "\n")
print("\n".join(log))
