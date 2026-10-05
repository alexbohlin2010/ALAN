"""Amber band (570-615 nm) night irradiance, Philadelphia vs Cherry Springs, for the "Two measured nights" text.

Run from final/:  python3 pipeline/spectra/03_amber_band_ratio.py      (stdlib only)
Input:  data/derived/spectra/philadelphia.json, cherry_springs.json, spectra_meta.json
        (pipeline/spectra/01_night_spectra.py: 240 selected night spectra per site, 280..840 nm at 2 nm, W m^-2 nm^-1)
Output: data/derived/spectra/amber_band_ratio.json

Human decisions (AI_LOG "Amber highlight" steps 2-3): band shading on the Philadelphia half; text (placement not decided)
"In amber light (570–615 nm), Philadelphia's night sky is about 150 times brighter than Cherry Springs, a dark sky park."
Band: 570-615 nm, documented in Spitschan et al. 2016 (Sci Rep 6: 26756), Results, City night spectra: "The broader
peak in the wavelength range 570–615 nm is also consistent with the emission spectra of artificial lights."

Rule (inferred, RULES 2.3):
- per spectrum: band irradiance = sum of value x 2 nm over grid wavelengths 570 <= w <= 615 (23 values, 570..614 nm; rectangle rule
  on the 2 nm grid; zeros kept; nulls skipped and counted);
- per site: median of the 240 band irradiances (statistics.median);
- ratio = Philadelphia median / Cherry Springs median;
- display = ratio rounded to 2 significant figures.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECTRA = ROOT / 'data/derived/spectra'
OUT = SPECTRA / 'amber_band_ratio.json'
LO, HI, STEP = 570, 615, 2
SITES = ['philadelphia', 'cherry_springs']


def main():
    meta = json.loads((SPECTRA / 'spectra_meta.json').read_text())
    wl = meta['wavelength_nm']
    if meta['wavelength_step_nm'] != STEP:
        raise SystemExit('unexpected wavelength step')
    idx = [i for i, w in enumerate(wl) if LO <= w <= HI]
    sites = {}
    for s in SITES:
        doc = json.loads((SPECTRA / f'{s}.json').read_text())
        band, nulls = [], 0
        for row in doc['irradiance']:
            if len(row) != len(wl):
                raise SystemExit(f'{s}: row length differs from wavelength grid')
            vals = [row[i] for i in idx]
            nulls += sum(v is None for v in vals)
            band.append(sum(v * STEP for v in vals if v is not None))
        sites[s] = {'place': doc['place'], 'n_spectra': len(band), 'null_values_skipped': nulls,
                    'median_band_irradiance_W_m2': statistics.median(band),
                    'min_band_irradiance_W_m2': min(band), 'max_band_irradiance_W_m2': max(band),
                    'selected_date_range': doc['selected_date_range']}
    ratio = sites['philadelphia']['median_band_irradiance_W_m2'] / sites['cherry_springs']['median_band_irradiance_W_m2']
    out = {
        'label': 'inferred',
        'rule': __doc__.split('Rule (inferred, RULES 2.3):\n', 1)[1].strip(),
        'inputs': ['data/derived/spectra/philadelphia.json', 'data/derived/spectra/cherry_springs.json',
                   'data/derived/spectra/spectra_meta.json'],
        'band_nm': [LO, HI], 'band_grid_nm': [wl[i] for i in idx],
        'band_source': 'Spitschan et al. 2016, Sci Rep 6: 26756, doi:10.1038/srep26756, Results (City night spectra)',
        'unit': 'W m^-2 (band-integrated downwelling irradiance)',
        'sites': sites,
        'ratio_philadelphia_to_cherry_springs': ratio,
        'ratio_display': float(f'{ratio:.2g}'),
        'script': 'pipeline/spectra/03_amber_band_ratio.py',
        'audit': 'pending (RULES 3)',
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False) + '\n')
    print(f"medians: {sites['philadelphia']['median_band_irradiance_W_m2']:.4g} / "
          f"{sites['cherry_springs']['median_band_irradiance_W_m2']:.4g} W m^-2; ratio {ratio:.4g} -> {out['ratio_display']:g}")


if __name__ == '__main__':
    main()
