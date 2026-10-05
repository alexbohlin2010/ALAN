"""Share of the Philadelphia night spectra that falls in an amber band, unweighted and weighted by response curves.

Run from final/:  python3 pipeline/spectra/03_amber_share.py      (stdlib only)
Input:  data/derived/spectra/philadelphia.json, spectra_meta.json (pipeline/spectra/01_night_spectra.py)
        data/raw/receptors/linda_draft/development-placeholders.json (read-only; SHA-256 checked against
        data/raw/receptors/MANIFEST.csv). Curves resampled with the rule of pipeline/spectra/02_species_curves.py
        (imported, not copied), so they match species_curves.json; CIE photopic V(λ) is read from the same raw file
        (it is in Linda's file but was left out of species_curves.json, human decision round 7j).
Output: data/derived/spectra/amber_share.json
Requested by the human (AI_LOG "Species perceptions" step 1): what share of the Philadelphia spectrum, weighted by
each curve, falls in an amber band. Numbers for the human's decision only; not shown on screen.

Rule (deterministic): for each of the 240 selected Philadelphia spectra S(λ) (W m⁻² nm⁻¹, 2 nm grid, null cells = 0;
there are none) and each curve R(λ) (peak 1, energy basis as in the app's S × R):
  share = Σ_{λ in band} S(λ) R(λ) / Σ_{λ in denominator} S(λ) R(λ)   (Riemann sums, 2 nm steps; the step cancels)
Weighted: denominator = the whole grid 280–840 nm (each curve is 0 outside its range).
Unweighted (R = 1): denominators 380–780 nm (CIE visible range) and 280–840 nm (whole grid).
Flat spectrum (S = 1, the curve alone): shows how much of each share comes from the curve rather than the light.
Reported: median and min / max over the 240 per-spectrum shares, and the share of the summed spectrum.
Bands (grid points lo ≤ λ ≤ hi):
  570–615 nm  documented: Spitschan et al. 2016, Results (City), "broader peak in the wavelength range 570–615 nm
              ... consistent with the emission spectra of artificial lights"; the band used on Two measured nights.
  604–622 nm  agent choice for a sensitivity check only: 613.41 nm (Owens & Lewis 2021 amber LED peak) ± ~9 nm on the
              2 nm grid. The paper gives no bandwidth, so this band has no source.
Labels (RULES 2.3): shares weighted by CIE curves and unweighted shares `inferred` (this rule; inputs measured
irradiance and documented CIE samples as copied in Linda's file). Shares weighted by the firefly curve: no label,
the curve is provisional (human, round 7j), so the share inherits that status.
"""
import csv
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/receptors/linda_draft/development-placeholders.json'
MANIFEST = ROOT / 'data/raw/receptors/MANIFEST.csv'
META = ROOT / 'data/derived/spectra/spectra_meta.json'
SITE = ROOT / 'data/derived/spectra/philadelphia.json'
OUT = ROOT / 'data/derived/spectra/amber_share.json'

spec = importlib.util.spec_from_file_location('species_curves', ROOT / 'pipeline/spectra/02_species_curves.py')
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

CURVES = {   # species id → receptor id in the raw file; label of the weighted share
    'human-photopic-v': ('human-photopic', 'inferred'),
    'human-scotopic-v': ('human-scotopic', 'inferred'),
    'firefly-yellow': ('big-dipper-firefly', None),
}
BANDS = {'570-615': (570, 615), '604-622': (604, 622)}


def share(s, r, wl, band, den=(280, 840)):
    num = sum(a * b for a, b, w in zip(s, r, wl) if band[0] <= w <= band[1])
    tot = sum(a * b for a, b, w in zip(s, r, wl) if den[0] <= w <= den[1])
    return num / tot if tot > 0 else None


def summary(spectra, r, wl, band, den=(280, 840)):
    per = [x for x in (share(s, r, wl, band, den) for s in spectra) if x is not None]
    summed = [sum(col) for col in zip(*spectra)]
    return {'median': round(statistics.median(per), 4), 'min': round(min(per), 4), 'max': round(max(per), 4),
            'summed_spectrum': round(share(summed, r, wl, band, den), 4), 'n': len(per)}


def main():
    got = sc.sha256(RAW)
    if got != sc.manifest_sha('linda_draft/development-placeholders.json'):
        raise SystemExit(f'SHA-256 mismatch for {RAW}')
    wl = json.loads(META.read_text())['wavelength_nm']
    site = json.loads(SITE.read_text())
    spectra = [[v if v is not None and v > 0 else 0.0 for v in row] for row in site['irradiance']]
    raw = {s['id']: s for s in json.loads(RAW.read_text())['species']}
    curves = {rid: sc.resample(next(r for r in raw[sid]['receptors'] if r['id'] == rid), wl)
              for rid, (sid, _) in CURVES.items()}
    ones, flat = [1.0] * len(wl), [[1.0] * len(wl)]
    out = {'description': 'Share of the Philadelphia night spectra in an amber band (see the script docstring).',
           'script': 'pipeline/spectra/03_amber_share.py', 'site_file': str(SITE.relative_to(ROOT)),
           'site_sha256': hashlib.sha256(SITE.read_bytes()).hexdigest(), 'curves_file': str(RAW.relative_to(ROOT)),
           'curves_sha256': got, 'basis': 'energy (W m⁻² nm⁻¹ × response), as in the app',
           'bands_nm': {k: list(v) for k, v in BANDS.items()},
           'band_sources': {'570-615': 'documented: Spitschan et al. 2016 Results (City), doi:10.1038/srep26756',
                            '604-622': 'agent choice, sensitivity only (613.41 nm ± ~9 nm; no source for a bandwidth)'},
           'results': {}}
    for b, band in BANDS.items():
        res = {'unweighted_of_380_780': {**summary(spectra, ones, wl, band, (380, 780)), 'label': 'inferred'},
               'unweighted_of_280_840': {**summary(spectra, ones, wl, band), 'label': 'inferred'}}
        for rid, (_, label) in CURVES.items():
            res[f'weighted_{rid}'] = {**summary(spectra, curves[rid], wl, band), 'label': label,
                                      **({} if label else {'status': 'provisional curve (human, round 7j); no label'})}
            res[f'flat_spectrum_{rid}'] = {'share': round(share(flat[0], curves[rid], wl, band), 4), 'label': label}
        out['results'][b] = res
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for b, res in out['results'].items():
        print(f'band {b} nm')
        for k, v in res.items():
            print(f'  {k:34s}', {x: v[x] for x in v if x not in ('label', 'status', 'n')})
    print(f'{OUT.relative_to(ROOT)} written')


if __name__ == '__main__':
    main()
