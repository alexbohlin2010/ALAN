# Handoff: EOG version (2015 v2.1 vs 2025 v2.2) sensitivity of the story figures

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` "Story, step 38" (background: steps 36–37). Read `RULES.md` first.

## What was done
- New diagnostic script `pipeline/story/03_version_sensitivity.py` → `data/derived/story/version_sensitivity_2015_2025.json` (`inferred`, unaudited). It does not replace the published figures in `radiance_change_2015_2025.json` / `country_change_2015_2025.json`, and no story text was changed.
- Variants: (a) current > 0, (b) lit in both years, (c) same fixed floor both years (0.653 / 1 / 2 / 3), (d) per-1° local floor. (a) reproduces the published figures exactly. The results table is in the AI_LOG entry.
- EOG docs (sub-agent search, sources in AI_LOG): per-pixel multiyear DR threshold; v2.2 changed months counted, DR calculation and satellite mix; no documented threshold change; no EOG guidance on comparing across versions; years ≤ 2021 exist only as v2.1.

## Facts
- Radiance change keeps its sign under every variant for global (+30 to +44%), India (+72 to +128%) and Ukraine (−22 to −44%).
- Iceland changes sign: +106% at > 0, −17% on pixels lit in both years, −14% at > 3.
- Global lit-area change ranges from +25% (> 0) to +83% (> 0.653).
- Median per-1° smallest positive value is higher in 2025 than in 2015 everywhere except at high latitude (Iceland 1.07 → 0.51).

## Decisions made by humans
- None yet. Options were given in chat; the human decides.

## Open
- Which option to take for the story figures (see chat / AI_LOG step 38).
- RULES §3 audit of 03 if its numbers are used in the story.

## Addendum (step 39)
- Human chose option 3. France is back in the story (Intro, Statistic, India, France, Ukraine); Iceland is in `retired`. The "Statistic" step no longer gives the lit-area figure.
- France under the version check: −38% to −48% radiance in every variant.
- Open: the human is open to a different country with a light-related policy and a notable visualization (not searched yet); whether to keep the Kyba 2017 lit-area sentence in the Statistic note; §3 audit of 03.

## Addendum (step 40)
- Human: a new case-study country can have a light-pollution law or a recent light-expansion initiative ("how countries are expanding light into natural areas").
- `pipeline/story/04_country_screen.py` → `data/derived/story/country_screen_2015_2025.csv`: every country × variants a/b/c2/c3/d, with a same-sign flag (unaudited, screening only).
- Candidates found (sources in AI_LOG step 40 / chat) and their screen results are in AI_LOG step 40. Human to choose; nothing in the story changed.

## Addendum (step 41)
- Human: two case-study countries only, India and Côte d'Ivoire. France and Ukraine are in `retired` (with Iceland). Côte d'Ivoire +227% (02_country_change.py; +116 to +247% under all version variants); PRONER source read by the agent (documented).
- Statistic step: no camera move, no sweep (stays at the intro view).
- Open: what the Statistic step does next (human: "then can figure out what to do next"); Côte d'Ivoire camera framing (card covers the Abidjan coast); Côte d'Ivoire text is a DRAFT; §3 audits of 02 (rerun), 03, 04.
