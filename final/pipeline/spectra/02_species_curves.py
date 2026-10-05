"""Species response curves on the night-spectra wavelength grid, for the "Species perceptions" step.

Run from final/:  python3 pipeline/spectra/02_species_curves.py      (stdlib only)
Input:  data/raw/receptors/linda_draft/development-placeholders.json (read-only; SHA-256 checked against
        data/raw/receptors/MANIFEST.csv before it is read)
        data/derived/spectra/spectra_meta.json (wavelength grid, 280..840 nm at 2 nm; pipeline/spectra/01_night_spectra.py)
Output: data/derived/spectra/species_curves.json

Human decisions (AI_LOG "Firefly tabs review" round 7j):
- Species: human night (CIE 2019 V'(lambda) only; no human day curve) and the five animals with their own published
  peaks in Linda's file: rock pigeon, Carolina sphinx, Big Dipper firefly (Photinus pyralis), bronze ground beetle,
  bobolink. Left out: human day, saw-whet owl (development placeholder), waved sphinx (Manduca proxy).
- Human day (CIE 2019 photopic V(lambda)) was added in AI_LOG "Species perceptions" step 4 and removed again in step 11
  (human: "remove photopic"); the Firefly | Human step uses human night, and the Explore draft cycles the six species.
- CIE curve copied from Linda's file (not downloaded from CIE).
- Animal curves: provisional. Linda's file marks them 'measured-peaks-modeled-shape' (published peaks, modeled shape;
  no method given). The human states the full curves are available online and will be identified later; they are
  not to be labelled 'estimated'. They carry no RULES label here, only the status note below.

Rule (same as the draft's interpolateSamples, Linda/.../src/science/receptors.ts): for each receptor, samples sorted
by wavelength; on each grid wavelength w: 0 outside the receptor's wavelengthRangeNm; inside it, the first / last
sample's response below / above the sampled span; otherwise linear interpolation between the two neighbouring
samples. Responses are written unrounded (Python float repr). Every other field is copied as written in the source.

Labels (RULES 2.3): human night responses `inferred` (rule above, from the CIE 2019 V'(lambda) samples as copied in
Linda's file, `documented` there with DOI 10.25039/CIE.DS.gr6w4b5g; not yet compared against the CIE table).
Animal responses: no label (human decision, round 7j); `status` = provisional note. Names, ids, sources and
display channels are copied text, not values.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/receptors/linda_draft/development-placeholders.json'
MANIFEST = ROOT / 'data/raw/receptors/MANIFEST.csv'
META = ROOT / 'data/derived/spectra/spectra_meta.json'
OUT = ROOT / 'data/derived/spectra/species_curves.json'

KEEP = ['human-scotopic', 'rock-pigeon', 'carolina-sphinx', 'big-dipper-firefly', 'bronze-ground-beetle', 'bobolink']
PROVISIONAL = ("provisional: curve copied from Linda's development-placeholders.json (marked there "
               "'measured-peaks-modeled-shape'); peaks as cited there; full-curve source to be identified "
               "(human, AI_LOG Firefly tabs review round 7j). No RULES label.")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_sha(name):
    with MANIFEST.open(newline='') as f:
        for row in csv.DictReader(f):
            if row['path'] == name:
                return row['sha256']
    raise SystemExit(f'{name} not in {MANIFEST}')


def resample(receptor, grid):
    samples = sorted(receptor['samples'], key=lambda s: s['wavelengthNm'])
    if len(samples) < 2:
        raise SystemExit(f"{receptor['id']}: fewer than two samples")
    lo, hi = receptor['wavelengthRangeNm']
    out = []
    for w in grid:
        if w < lo or w > hi:
            out.append(0.0)
        elif w <= samples[0]['wavelengthNm']:
            out.append(samples[0]['response'])
        elif w >= samples[-1]['wavelengthNm']:
            out.append(samples[-1]['response'])
        else:
            j = next(k for k in range(1, len(samples)) if samples[k]['wavelengthNm'] >= w)
            a, b = samples[j - 1], samples[j]
            t = (w - a['wavelengthNm']) / (b['wavelengthNm'] - a['wavelengthNm'])
            out.append(a['response'] + (b['response'] - a['response']) * t)
    return out


def main():
    got, want = sha256(RAW), manifest_sha('linda_draft/development-placeholders.json')
    if got != want:
        raise SystemExit(f'SHA-256 mismatch for {RAW}: {got} != MANIFEST {want}')
    src = json.loads(RAW.read_text())
    grid = json.loads(META.read_text())['wavelength_nm']
    by_id = {s['id']: s for s in src['species']}
    species = []
    for sid in KEEP:
        s = by_id[sid]
        human = sid in ('human-scotopic', 'human-photopic')
        species.append({
            'id': s['id'], 'name': s['name'], 'scientific_name': s['scientificName'],
            'site_ids_in_source': s['siteIds'], 'evidence_level_in_source': s['evidenceLevel'],
            'receptors': [{
                'id': r['id'], 'name': r['name'], 'display_channel': r['displayChannel'],
                'peak_nm': r.get('peakNm'), 'range_nm': r['wavelengthRangeNm'],
                'source': r['source'], 'curve_status_in_source': r['curveStatus'],
                'label': 'inferred' if human else None,
                'status': None if human else PROVISIONAL,
                'response': resample(r, grid),
            } for r in s['receptors']],
        })
    doc = {
        'description': 'Species response curves resampled to the night-spectra grid (Species perceptions step).',
        'source_file': str(RAW.relative_to(ROOT)), 'source_sha256': got,
        'grid_file': str(META.relative_to(ROOT)),
        'wavelength_nm': grid,
        'normalization': 'as in the source: peak normalized to 1',
        'rule': 'linear interpolation onto wavelength_nm; 0 outside range_nm; end samples held inside range_nm',
        'labels': {'human-scotopic': 'inferred (from documented CIE 2019 V′(λ) samples as copied in the source file)',
                   'animals': 'none (provisional, human decision round 7j); see each receptor status'},
        'species': species,
    }
    text = json.dumps(doc, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    json.loads(text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))   # strict re-parse
    OUT.write_text(text)
    n = sum(len(s['receptors']) for s in species)
    print(f'{OUT.relative_to(ROOT)}: {len(species)} species, {n} receptors, {len(grid)} wavelengths, '
          f'{OUT.stat().st_size} bytes; source sha256 {got[:12]}… OK')


if __name__ == '__main__':
    main()
