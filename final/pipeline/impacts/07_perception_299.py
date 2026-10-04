"""Study 299: each LED spectrum weighted by the P. scintillans sensitivity ("perception" layer).

Run from final/:  .venv/bin/python pipeline/impacts/07_perception_299.py
Input:  data/derived/impacts/spectra_299.json (06_spectra_299.py; inferred from Fig. 1 vectors)
Output: data/derived/impacts/perception_299.json

Human decision (AI_LOG "Impacts task", step 78): show a perception layer = lamp spectrum x animal
sensitivity, label `inferred` (rule: product at each nm).

Rules (all deterministic):
- At every whole nm where both the LED curve and the P. scintillans curve have a sample, value =
  LED value x sensitivity value (both as read from Fig. 1: relative intensity, relative sensitivity).
  Negative zeros from the extraction are taken as 0.
- Where the LED has a sample but the sensitivity curve does not (the figure plots P. scintillans only
  from 350 to 675 nm), the value is null: sensitivity there is not shown in the source, so it is unknown,
  not zero. The count of null cells per lamp is written out.
- No normalisation, smoothing or summing. Units: relative (product of two relative scales); only the
  shape and the comparison between lamps at the same intensity are meaningful. Fig. 1 standardises the
  area under each LED curve (photons), so all five lamps are on one scale (caption, documented).
"""
import json
from pathlib import Path

SRC = Path('data/derived/impacts/spectra_299.json')
OUT = Path('data/derived/impacts/perception_299.json')
LAMPS = ['cool_white', 'warm_white', 'blue', 'amber', 'red']


def main():
    src = json.loads(SRC.read_text())
    sens = {nm: max(0.0, v) for nm, v in src['curves']['p_scintillans']['samples']}
    out = {}
    for lamp in LAMPS:
        samples, empty = [], 0
        for nm, v in src['curves'][lamp]['samples']:
            if nm in sens:
                samples.append([nm, round(max(0.0, v) * sens[nm], 5)])
            else:
                samples.append([nm, None])
                empty += 1
        out[lamp] = {'n': len(samples), 'n_null': empty, 'samples': samples}
        print(f'{lamp:11s} {len(samples)} samples, {empty} null (no sensitivity value)')
    doc = {
        'study_id': '299',
        'label': 'inferred',
        'rule': 'LED value x P. scintillans sensitivity at each whole nm; null where the sensitivity curve has '
                'no sample (pipeline/impacts/07_perception_299.py)',
        'inputs': str(SRC) + ' (inferred from Owens & Lewis 2021 Fig. 1, doi:10.1111/icad.12487)',
        'units': {'wavelength': 'nm', 'value': 'relative (product of relative intensity and relative sensitivity)'},
        'sensitivity_range_nm': [min(sens), max(sens)],
        'curves': out,
    }
    OUT.write_text(json.dumps(doc, indent=1))


if __name__ == '__main__':
    main()
