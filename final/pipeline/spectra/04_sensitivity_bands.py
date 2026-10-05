"""Peak and half-maximum band of the two curves compared on Species perceptions (human night, firefly).

Run from final/:  python3 pipeline/spectra/04_sensitivity_bands.py      (stdlib only)
Input:  data/raw/receptors/linda_draft/development-placeholders.json (read-only; SHA-256 checked against
        data/raw/receptors/MANIFEST.csv), data/derived/spectra/species_curves.json and spectra_meta.json (2 nm grid;
        pipeline/spectra/02_species_curves.py, 01_night_spectra.py)
Output: data/derived/spectra/sensitivity_bands.json
Requested by the human (AI_LOG "Species perceptions" step 10): reproduce in the repo the facts "scotopic V′(λ) peaks at
506 nm, half-max band 454–548 nm; firefly peaks at 564 nm, half-max band 530–600 nm", which came from a check not in
the repo, as candidate definitions of the "Human sensitivity" / "Firefly sensitivity" blocks on Two measured nights.

Curves: human-scotopic-v (CIE 2019 scotopic V′(λ), 1 nm samples as copied in Linda's file) and firefly-yellow
(Photinus pyralis female behavioural action spectrum, Lall & Worthy 2000 as cited there; 5 nm samples,
'measured-peaks-modeled-shape'). Both peak-normalised to 1 in the source: they say where each species responds, not
how strongly one responds compared with the other.

Rule (deterministic), computed twice: (a) on the source samples; (b) on the 2 nm grid of species_curves.json (what the
app draws).
  peak      = wavelength of the largest response (first one if tied)
  half-max  = the outermost wavelengths where the curve crosses 0.5 × peak, by linear interpolation between the two
              neighbouring samples ('interpolated'), and the first / last sample with response ≥ 0.5 ('samples ≥ 0.5')
Values rounded to 0.1 nm.
Labels (RULES 2.3): human night values `inferred` (this rule; input documented CIE 2019 samples as copied in Linda's
file, not yet compared against the CIE table). Firefly values: no label, the curve is provisional (human, round 7j);
the stated peak 565 nm is `documented` in the source file as Lall & Worthy 2000 (not checked against the paper).
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/receptors/linda_draft/development-placeholders.json'
CURVES = ROOT / 'data/derived/spectra/species_curves.json'
OUT = ROOT / 'data/derived/spectra/sensitivity_bands.json'

spec = importlib.util.spec_from_file_location('species_curves', ROOT / 'pipeline/spectra/02_species_curves.py')
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

WHICH = {'human-scotopic-v': 'inferred', 'firefly-yellow': None}


def band(wl, r):
    top = max(r)
    i = r.index(top)
    half = top / 2
    above = [k for k, v in enumerate(r) if v >= half]
    lo_k, hi_k = above[0], above[-1]

    def cross(a, b):   # linear interpolation of the 0.5 crossing between sample indices a and b
        return wl[a] + (half - r[a]) * (wl[b] - wl[a]) / (r[b] - r[a])
    lo = cross(lo_k - 1, lo_k) if lo_k > 0 else None
    hi = cross(hi_k, hi_k + 1) if hi_k + 1 < len(r) else None
    return {'peak_nm': wl[i], 'half_max_interpolated_nm': [round(lo, 1) if lo else None, round(hi, 1) if hi else None],
            'half_max_samples_ge_0_5_nm': [wl[lo_k], wl[hi_k]], 'sample_step_nm': wl[1] - wl[0]}


def main():
    got = sc.sha256(RAW)
    if got != sc.manifest_sha('linda_draft/development-placeholders.json'):
        raise SystemExit(f'SHA-256 mismatch for {RAW}')
    raw = {r['id']: r for s in json.loads(RAW.read_text())['species'] for r in s['receptors']}
    grid = json.loads(CURVES.read_text())
    on_grid = {r['id']: r['response'] for s in grid['species'] for r in s['receptors']}
    out = {'description': 'Peak and half-maximum band of human night (CIE scotopic V′(λ)) and the firefly curve.',
           'script': 'pipeline/spectra/04_sensitivity_bands.py', 'curves_file': str(RAW.relative_to(ROOT)),
           'curves_sha256': got, 'grid_file': str(CURVES.relative_to(ROOT)), 'units': 'nm, wavelength in air',
           'normalization': 'each curve peak-normalised to 1 in the source', 'curves': {}}
    for rid, label in WHICH.items():
        s = sorted(raw[rid]['samples'], key=lambda x: x['wavelengthNm'])
        res = {'source_samples': band([x['wavelengthNm'] for x in s], [x['response'] for x in s]),
               'app_grid_2nm': band(grid['wavelength_nm'], on_grid[rid]),
               'stated_peak_nm_in_source': raw[rid].get('peakNm'), 'label': label}
        if not label:
            res['status'] = 'provisional curve (human, round 7j); no label'
        out['curves'][rid] = res
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for rid, res in out['curves'].items():
        print(rid, f"(stated peak {res['stated_peak_nm_in_source']})")
        for k in ('source_samples', 'app_grid_2nm'):
            print(f'  {k:15s}', res[k])
    print(f'{OUT.relative_to(ROOT)} written')


if __name__ == '__main__':
    main()
