"""Study highlight sets for the Studies / Fireflies steps (ladder plan, phase 2; AI_LOG "Story review" steps 7–8): which located studies measured a behaviour effect, and which are firefly / glow-worm studies.

Run from final/:  python3 pipeline/impacts/10_study_highlights.py
Input:  data/derived/impacts/effects.json    (04_effects.py; Czarnecka et al. 2025 Data S1 records, located studies)
        data/derived/impacts/studies.json    (01_studies.py; species and titles as in Data S1)
Output: data/derived/impacts/study_highlights.json

Rules (deterministic; both sets `inferred`):
- Located studies = the study_ids that have records in effects.json (the 207 studies on the globe).
- behaviour: located studies with at least one record whose `category` is "Behaviour" (Data S1 category, as copied).
- fireflies: located studies whose Data S1 species list names a species of the genus Photinus or Lampyris (the two
  genera the repo's firefly sources name: Owens & Lewis 2021, Photinus obscurellus "fireflies"; Kivelä et al. 2023,
  Lampyris noctiluca "glow-worm"), or whose Data S1 title contains "firefl", "Lampyridae" or "glow-worm"
  (case-insensitive). Other firefly genera are not searched for (no source in the repo lists them).
No values are changed; the output lists study ids only, with the counts.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

D = Path('data/derived/impacts')
GENERA = ('Photinus', 'Lampyris')
TITLE_WORDS = ('firefl', 'lampyridae', 'glow-worm')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    eff_path, st_path = D / 'effects.json', D / 'studies.json'
    effects = json.loads(eff_path.read_text())['effects']
    studies = {s['study_id']: s for s in json.loads(st_path.read_text())['studies']}
    located = sorted({e['study_id'] for e in effects})
    behaviour = sorted({e['study_id'] for e in effects if e['category'] == 'Behaviour'})

    def is_firefly(sid):
        s = studies[sid]
        title = ' '.join(s['title']).lower()
        return any(n.split(' ')[0] in GENERA for n in s['species']) or any(w in title for w in TITLE_WORDS)

    fireflies = [sid for sid in located if is_firefly(sid)]
    out = {
        'meta': {
            'inputs': {str(eff_path): sha(eff_path), str(st_path): sha(st_path)},
            'script': 'pipeline/impacts/10_study_highlights.py',
            'created': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'located_studies': len(located),
            'audit': 'Not yet audited (RULES section 3).',
        },
        'sets': {
            'behaviour': {'label': 'inferred', 'n': len(behaviour), 'study_ids': behaviour,
                          'rule': 'located studies with >= 1 effects.json record whose category is "Behaviour"'},
            'fireflies': {'label': 'inferred', 'n': len(fireflies), 'study_ids': fireflies,
                          'rule': f'species genus in {list(GENERA)} or title contains {list(TITLE_WORDS)} (case-insensitive)'},
        },
    }
    (D / 'study_highlights.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(len(located), 'located;', len(behaviour), 'behaviour;', len(fireflies), 'fireflies:', fireflies)


if __name__ == '__main__':
    main()
