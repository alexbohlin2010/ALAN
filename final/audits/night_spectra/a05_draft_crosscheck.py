"""Third-party cross-check (run from final/, stdlib only, read-only outside audits/): spectra_meta.json says the
selection "reproduces" the draft Linda/visual tests/spatial/philadelphia-spectral-space/scripts/preprocess.ts. That draft
lives only in the main checkout (not in this worktree). Compare its committed output (public/data/manifest.json and the
Float32 .bin matrices, written 2026-09-27) with the audited outputs: selected source indices, timestamps, display limits,
and every irradiance cell after rounding the output value to float32. Writes results/a05_draft_crosscheck.txt."""
import json, struct, os
DRAFT = "/Users/lindaxiangyideng/Documents/GitHub/ALAN/Linda/visual tests/spatial/philadelphia-spectral-space/public/data"
D = "data/derived/spectra"; OUT = "audits/night_spectra/results"
log = []
P = lambda *a: log.append(" ".join(str(x) for x in a))
if not os.path.isdir(DRAFT):
    P("draft output folder not found:", DRAFT)
else:
    m = json.load(open(f"{DRAFT}/manifest.json"))
    M = json.load(open(f"{D}/spectra_meta.json"))
    P("draft manifest generatedAt:", m["generatedAt"], "| unit:", m["unit"], "| stride:", m["wavelengthStepNm"])
    P("draft wavelengthNm == output wavelength_nm:", m["wavelengthNm"] == M["wavelength_nm"])
    P("draft floor/ceil:", m["irradianceFloorLog10"], m["irradianceCeilLog10"], "| output:",
      M["display_limits_log10"]["floor"], M["display_limits_log10"]["ceil"])
    for site, did in (("philadelphia", "philadelphia"), ("cherry_springs", "cherry-springs")):
        s = m["sites"][did]; J = json.load(open(f"{D}/{site}.json"))
        P(f"[{site}] draft keys: {sorted(s.keys())}")
        si = s.get("sourceIndices")
        P("  draft sourceIndices (0-based) + 1 == output source_column:", [i + 1 for i in si] == J["source_column"])
        P("  draft timestamps == output timestamp:", s.get("timestamps") == J["timestamp"])
        raw = open(f"{DRAFT}/{s['binaryFile']}", "rb").read()
        vals = struct.unpack(f"<{len(raw) // 4}f", raw)
        P("  draft matrix length:", len(vals), "== 240*281:", len(vals) == 240 * 281)
        f32 = lambda x: struct.unpack("<f", struct.pack("<f", x))[0]
        eq = sum(f32(J["irradiance"][i][j]) == vals[i * 281 + j] for i in range(240) for j in range(281))
        P(f"  irradiance cells equal after float32 rounding of output: {eq} / {240 * 281}")
        for k in ("zeroCells", "nanCells", "finitePositiveCells"):
            P(f"  draft {k}: {s.get(k)}")
    lp = [v for v in (m["sites"][x].get("log10Percentiles") for x in m["sites"]) if v]
    P("draft log10Percentiles found per site:", lp[:1])
open(f"{OUT}/a05_draft_crosscheck.txt", "w").write("\n".join(log) + "\n")
print("\n".join(log))
