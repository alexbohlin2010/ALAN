// Story content: the one file to edit for wording, order, camera and timing.
// Read by app/src/story.js. Text: *word* = italic. Times in milliseconds.
//
// camera: { lat, lng, altitude } (altitude in globe radii; smaller = closer)
// fly:    camera flight time to this step
// swipe:  optional divider position, 0 = all 2025 ... 1 = all 2015.
// sweep:  automatic divider sweep across a country after the flight: the divider glides to the
//         right edge during the flight (2015 view), waits `hold`, jumps smoothly to the country's
//         east edge, then sweeps to its west edge over `duration` (2025 view).
//         east/west are approximate mainland longitudes, set by hand for display only.
// figure: large number line on a case-study card (from data/derived/story/country_change_2015_2025.json,
//         label inferred, lit > 0, PROVISIONAL until audited; see figureNote).
// sources: shown under the card. `supports` says what the source states;
//          it is a note for editors and is not displayed.
// rung:   the step's place on the ladder marker (src/story.js, `ladder` below); steps without one hide it.
//
// DRAFT NOTICE: the case-study and caveat sentences below were drafted by an AI agent
// (claude-opus-5-5, 2026-10-03) at the human's request as prototype placeholders.
// Each cites one source for its factual part. The link between the fact and the change in
// lights is the humans' framing; neither the source nor our data shows that cause.

// Not shown: the ladder was removed (human, AI_LOG Impacts firefly-first step 2; main.js no longer passes it); the
// array and the steps' `rung` keys are kept unused.
// Ladder marker (AI_LOG "Story review" steps 7–8): the kind of data a step shows, from the
// satellite view down to an animal's eye. Labels: [PLACEHOLDER] working words, to be written by the humans.
export const ladder = [
  { id: 'space', label: 'Space' },
  { id: 'studies', label: 'Studies' },
  { id: 'animal', label: 'Animal' },
  { id: 'light', label: 'Light' },
  { id: 'eye', label: 'Eye' },
];

export const story = [
  // ── Part 1: intro / context (global illumination) ──────────────────────────
  {
    id: 'intro',
    part: 1,
    kind: 'intro',             // black screen with text; text fades out; lights fade in; then the UI
    text: '*...and then there was light*',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    timing: { textIn: 1000, hold: 1000, textOut: 500, lightsIn: 6000, uiIn: 1500 },
  },
  {
    id: 'statistic',
    part: 1,
    label: 'Dawn',   // human (AI_LOG Impacts firefly-first step 6); was the id ('Statistic')
    rung: 'space',
    kind: 'fact',              // large text on the left of the globe instead of a card
    // Values from pipeline/story/01_radiance_change.py -> data/derived/story/radiance_change_2015_2025.json
    // (label: inferred; lit = > 0, sphere areas, pairwise -1.5 exclusion): radiance +40.99% vs 2015.
    // Lit area (+25.28%) removed by the human (AI_LOG step 39): it ranges +25..+83% depending on the
    // threshold (EOG version difference, 03_version_sensitivity.py). PROVISIONAL: not yet audited (RULES section 3).
    // Wording: human's (AI_LOG step 11: say "ALAN", radiance moved to the footnote).
    // Wording: human (AI_LOG Impacts firefly-first step 5); the 41 % line moved to Ecosystems. Was 'From 2015 to 2025,
    // Artificial Light at Night (ALAN) increased by 41%.' (human, 2026-10-05, copy editing step 3).
    // 'inhabitants' → 'residents', line break before 'and' (human, AI_LOG Experience refinement step 7).
    text: 'The dawn of human nighttime activity is changing the globe,\nand its residents.',
    // Note and sources moved to Ecosystems with the 41 % line (human, AI_LOG Impacts firefly-first step 5).
    // No camera move and no sweep (human, AI_LOG Story step 41: the India/China pan made India feel
    // shown twice). Camera = the intro view, so the globe stays where the intro left it.
    // Was: camera { lat: 25, lng: 72, altitude: 1.6 }, fly 2500, sweep east 122 -> west 68.1.
    camera: { lat: 20, lng: 10, altitude: 2.2 },
  },
  // ── Part 2: light impacts ─────────────────────────────────────────────────
  // Sequence: human (AI_LOG Impacts steps 26–27). The question is the human's wording.
  // DRAFT NOTICE: all other Part 2 text (cards, chart labels in app/src/impacts.js) was drafted by an
  // AI agent (claude-opus-5-5, 2026-10-03) at the human's request as placeholders. Featured studies
  // (165, 005) and the worked example (005-2) were proposed by the agent, refinable.
  // impacts: stage of the Impacts layer (see setStage in app/src/impacts.js).
  {
    id: 'question',
    // Moved from Part 2 (Impacts) to Part 1 (Light), right after Statistic; wording and West Africa camera: human
    // (AI_LOG Copy editing and drafting step 2). Was: 'But how does light impact our ecosystems?', camera lat 20, lng 10, alt 2.2.
    // Camera point and altitude over West Africa: agent choice, display only.
    part: 1,
    rung: 'space',
    kind: 'fact',
    label: 'ALAN',   // human (AI_LOG Impacts firefly-first step 6); was 'Ecosystems'
    // Wording: human (AI_LOG Story flow step 5; "deeper into the night" accepted as framing, no source). Was 'As light
    // is expanding into new territory, what are the impacts on global ecosystems?'
    // Wording: human (AI_LOG Impacts firefly-first step 5): the 41 % line (from Statistic, comma after 2015 dropped as
    // asked) first; the question replaces it when the sweep ends (`reveal`, story.js sweep; as Two measured nights'
    // lines). Was 'As human nighttime activity expands in intensity and coverage, how is the biosphere responding?'
    // (step 2), before that 'As human activity extends deeper into the night, how is the biosphere responding?'
    text: 'From 2015 to 2025, Artificial Light at Night (ALAN) increased by 41%.',
    reveal: ['How is the biosphere responding?'],
    // The question fades in below the 41 % line, which stays; both stay through the flight to Fireflies (human, AI_LOG
    // Experience refinement step 19, option A4; was: the question replaced the line). Fireflies' `carryFrom`.
    revealBelow: true,
    // Note and sources from Statistic (moved with the 41 % line, step 5). Values from
    // pipeline/story/01_radiance_change.py -> data/derived/story/radiance_change_2015_2025.json (inferred; PROVISIONAL,
    // not yet audited, RULES section 3).
    note: 'ALAN: artificial light at night. 41% is the change in total radiance measured by the VIIRS ' +
      'satellite sensor (summed over area). ' +
      'Our calculation from EOG VIIRS annual data (provisional, audit pending). Consistent with ' +
      'published estimates of global growth: about 3.2% a year in 2012–2024 (Güneş et al. 2026); ' +
      'lit area +2.2% a year in 2012–2016 (Kyba et al. 2017). ' +
      'VIIRS cannot see blue light below about 500 nm, where white LEDs emit strongly, ' +
      'so LED lighting is under-counted (Kyba et al. 2023).',
    sources: [
      { label: 'EOG VIIRS Nighttime Lights, annual V2 (Elvidge et al. 2021)',
        url: 'https://doi.org/10.3390/rs13050922',
        supports: 'input data for our calculation (2015 v2.1, 2025 v2.2, average_masked)' },
      { label: 'Güneş et al. 2026, Ann. N.Y. Acad. Sci.', url: 'https://doi.org/10.1111/nyas.70297',
        supports: 'abstract: harmonized VIIRS 2012–2024, 165 countries; global ALAN +3.2%/yr ' +
          '(full text not yet read by the agent)' },
      { label: 'Kyba et al. 2017, Science Advances', url: 'https://doi.org/10.1126/sciadv.1701528',
        supports: 'abstract: lit area expanding 2.2%/yr, existing lit areas brightening 2.2%/yr, 2012–2016 ' +
          '(full text not yet read by the agent)' },
      { label: 'Kyba et al. 2023, Science 379:265', url: 'https://doi.org/10.1126/science.abq7781',
        supports: 'note: satellites recording global radiance are insensitive to wavelengths < 500 nm ' +
          'emitted by white LEDs (as reported in summaries of the paper; paper text not yet read by the agent)' },
    ],
    // Closer, over the Gulf of Guinea coast (Côte d'Ivoire, Ghana, Togo, Benin), less Sahara in view (human, AI_LOG Impacts
    // firefly-first step 3, option W1). Point, altitude and sweep ends: agent choices, display only (tuned in the preview).
    // Was camera lat 10, lng -13, alt 0.9; sweep east 15, west -17.5 (whole West Africa).
    camera: { lat: 8, lng: -5.5, altitude: 0.45 },   // lng -4 -> -5.5: the divider's 2015 label clear of the text (preview check)
    fly: 3000,
    // Divider sweeps over West Africa while the question shows (human, AI_LOG Copy editing and drafting step 3).
    // east/west: approximate West Africa extent (Cameroon border ~15 E, Dakar ~17.5 W), agent choice, display only.
    // Was: swipe: 0, impacts: { view: 'globe', dots: false } (an impacts stage hides the divider, style.css).
    // duration 3500 → 1000 ms (about the Spectra divider's speed) and `start` 0.72 (the divider arrives near the sweep's east
    // end, ~0.71 of the width at 1280 × 800, not the right edge): human, AI_LOG Experience refinement step 6; values: agent choices.
    sweep: { east: 3, west: -8.5, hold: 800, duration: 1000, start: 0.72 },   // Benin's east border ~3 E to Côte d'Ivoire's west ~8.5 W
  },
  // Studies step removed, merged into All effects (human, AI_LOG Impacts firefly-first step 2, option A2): Impacts opens
  // on the firefly; its note and sources moved to All effects' Details. Was: label 'Studies', text 'These 207 published
  // studies measure the impacts of artificial light on biota.', camera lat 20, lng 10, alt 2.2, fly 3000, impacts
  // { view: 'globe', reveal: true, highlight: Behaviour, then Fireflies and glow-worms }.
  // Female response study on the globe (human, AI_LOG Impacts reorder steps 2–4): replaces Black swans; shown like the
  // retired Fireflies (Taipei) step. Point = the Arnold Arboretum collection site printed in Owens & Lewis 2021
  // (impacts.js SITE_POINTS, documented; Boston only, human). Moving on to Female response the point glows and the
  // scene grows out of it (main.js `site`). Card text: agent draft on the human's request ("Reuse Taipei card shape"),
  // from the paper's Methods (data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf).
  // AI_LOG Fireflies step 2 (human): big text like Statistic (kind 'fact'), the human's sentence; note + source behind
  // "Details & sources"; no site point: study 299's own dot is at the Arboretum (02_geocode.py per-study review);
  // Fireflies <-> Female response is a plain cut. Was: title 'Fireflies · Arnold Arboretum, Boston, Massachusetts',
  // text '[DRAFT] Adult *Photinus obscurellus* fireflies were collected here, at the Arnold Arboretum, and at Muster
  // Field in Lincoln, Massachusetts, in June 2018: 22 males and 22 females, in low wet fields next to forest. Males
  // flash patterns of one to three flashes; females answer with single and double flashes.', impacts.site
  // 'owenslewis2021_boston'.
  {
    id: 'female-site',
    part: 2,
    rung: 'animal',
    kind: 'fact',
    label: 'Fireflies',
    text: 'Fireflies generate natural light to communicate in an increasingly lit environment.',   // wording: human
    carryFrom: 'question',   // ALAN's text stays through the 3.5 s flight across the Atlantic (human, AI_LOG Experience refinement step 19, A4)
    // Only the question flies (the 41 % line fades as the flight starts) and it fades as the US Atlantic coast comes in
    // (human, AI_LOG Experience refinement step 25). 2000 ms: the Boston point enters the screen at ~2.0 s of the flight
    // (measured at 1280 × 800); fade 500 ms, then this text fades in.
    carryFade: 2000,
    side: 'right',   // big text on the right, over the dark ocean (human, AI_LOG Fireflies step 4)
    note: 'The point marks the Boston collection site (coordinates as printed in the paper). The other 2018 site, ' +
      'Muster Field, Lincoln (42.42732, −71.31574), is not shown.',
    sources: [
      { label: 'Owens & Lewis 2021, Insect Conserv. Divers., Methods', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'June 2018: 22 male and 22 female adult P. obscurellus collected from Muster Field, Lincoln, MA (42.42732, −71.31574) and the Arnold Arboretum, Boston, MA (42.30469, −71.12099), in low wet fields abutted by forest; males emit patterns of one to three flashes, females respond with single and double flashes' },
    ],
    camera: { lat: 42.30469, lng: -71.12099, altitude: 0.35 },
    fly: 3500,
    swipe: 0,
    // studyLabel: a label under the study's dot: its title and year from studies.json (Data S1), authors as given here
    // (human: short form "Owens & Lewis 2021", AI_LOG Fireflies step 4).
    // only: study 299's dot alone, the others hidden (human, AI_LOG Impacts firefly-first step 2, option B1); flown to
    // straight from Ecosystems over the Atlantic (C1, 3.5 s). Was highlight: Fireflies and glow-worms (from Studies).
    // studyLabel delay: the label fades in after the 3.5 s flight, so it does not cross the menu in flight (human, AI_LOG
    // Impacts firefly-first step 3; delay = fly: agent choice).
    // site 'study:299': moving on, study 299's dot glows and grows and Female response opens out of it (human, AI_LOG
    // Impacts firefly-first step 8, option T2; was a plain cut since AI_LOG Fireflies step 2).
    impacts: { view: 'globe', only: ['299'], site: 'study:299', studyLabel: { id: '299', authors: 'Owens & Lewis', delay: 3500 } },
  },
  {
    id: 'female-response',
    // Big text centred at 42 % of the height instead of 50 %, clear of the spectrum row tags ("red", "amber"; human, AI_LOG
    // Experience refinement step 6). Value: agent choice (style.css --fact-top, landscape only).
    factTop: 0.42,
    part: 2,
    rung: 'animal',
    kind: 'fact',   // big narrative text, no card (human, AI_LOG Fireflies step 5); was a card titled 'Female response'
    side: 'right',   // human, AI_LOG Fireflies step 5
    label: 'Response',   // human (AI_LOG Experience refinement step 17); was 'Female response'
    // The former '[DRAFT] Fireflies' chapter (study 299), moved here from Explore (human, AI_LOG Firefly tabs round 5a);
    // its door from Light type removed (round 5b). Card text: agent draft on the human's request (round 5g), values as in
    // the sources below.
    // Text: the human's sentence (AI_LOG Fireflies step 4, "Replace card text"). Was: '[DRAFT] Courting *Photinus
    // obscurellus* fireflies: a male flashes, a female answers. In the dark 98.7 % of females answered; under bright cool
    // white 10.3 %, dim warm white 11.6 %, dim blue 36.1 %, dim red 48.6 % and bright amber 0 %. Each lamp in turn, with
    // the part of its light a firefly eye takes in (green).'
    // "firefly" added (human, AI_LOG Experience refinement step 17). Was 'ALAN interrupts female responses to mating calls.'
    // ", in a lab environment" (human, AI_LOG Experience refinement step 23). Was '… to mating calls.'
    text: 'ALAN interrupts female firefly responses to mating calls, in a lab environment.',   // wording: human (AI_LOG Fireflies step 8; was 'Light at night ...')
    // The bright amber beat's sentence replaces the big text on that beat instead of a caption below (human, AI_LOG
    // Firefly flow step 14): beat `line: 1` (spectral.js onLine). F1 wording: agent draft chosen by the human (step 4),
    // from Owens & Lewis 2021 (bright amber 0 %; Discussion: a male's chance of locating and mating with a female depends
    // on her response rate, Demary et al. 2005).
    reveal: ['Bright amber light silenced every female. Without her reply, a male cannot find her to mate.'],
    sources: [
      { label: 'Owens & Lewis 2021, Fig. 1 and Methods', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'five LED spectra, area (photons) standardised; P. scintillans sensitivity (Lall et al. 1988); flash peak 567.47 nm (Hall et al. 2016); dim 2.079 × 10^19, bright 2.079 × 10^20 photons cm⁻² s⁻¹' },
      { label: 'Owens & Lewis 2021, Results', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'female response: dark 98.7 %, bright cool white 10.3 %, dim warm white 11.6 %, dim blue 36.1 %, dim red 48.6 %, bright amber 0 %. The other five colour × intensity values are only in Fig. 2b (not shown)' },
    ],
    // Grows out of the Fireflies (Boston) point (human, AI_LOG Impacts reorder steps 2–4). Was camera lat 20, lng 10,
    // alt 2.2, no fly, no site. Altitude 0.04 and fly 2200: as Signal production (agent choices).
    // Slower dive (human, AI_LOG Impacts firefly-first step 8): fly 2200 → 3500 (value: agent choice).
    // No dive (human, AI_LOG Experience refinement step 17: "i don't like the zoom in"): the camera stays at Fireflies'
    // view and the scene opens at once as a circle out of the dot, without scaling (main.js `flat`). Was altitude 0.04,
    // fly 3500.
    camera: { lat: 42.30469, lng: -71.12099, altitude: 0.35 },
    swipe: 0,
    // manual: no auto-advance; a toggle (top right) and ← → step through the beats (human, Firefly transition task step 3).
    // Two beats (human, AI_LOG Firefly flow step 12: options A, i, 48.6): the four other lamps together with the range of
    // their documented values (dark 98.7 % in the label), the female replying on 48.6 % of cycles (the highest of the
    // four, i.e. "at most"); then bright amber. Was six beats: dark 98.7 %, bright cool white 10.3 %, dim warm white
    // 11.6 %, dim blue 36.1 %, dim red 48.6 %, bright amber 0 %. Button word 'other lights' and the label wording:
    // [PLACEHOLDER] agent choices.
    spectral: { chapter: 'fireflies', manual: true, site: 'study:299', beats: [   // was site 'owenslewis2021_boston' (step 8, T2)
      { lamps: ['cool_white', 'warm_white', 'blue', 'red'], button: 'other lights', value: '10.3–48.6 %',
        // `values`: the range splits and each value flies to its lamp's row tag (human, AI_LOG Experience refinement
        // step 17, option A). documented: Owens & Lewis 2021, Results (bright cool white, dim warm white, dim blue, dim red).
        values: { cool_white: '10.3 %', warm_white: '11.6 %', blue: '36.1 %', red: '48.6 %' },
        // Axis label for the values; the grey `label` fades with the range (human wording, AI_LOG Experience refinement step 18).
        valuesLabel: 'female response rates',
        label: 'females answer · bright cool white, dim warm white, dim blue, dim red (dark: 98.7 %)', reply: 0.486 },
      { lamp: 'amber', brighter: true, value: '0 %', label: 'females answer · bright amber (10× photons)', reply: 0,
        // Its sentence is the step's big-text line 1 (`reveal` above), no caption (AI_LOG Firefly flow step 14). Caption
        // was F1 (step 4), before that 'Bright amber lights reduced female response to 0%' (AI_LOG Fireflies steps 6–7).
        line: 1 },
    ] },
  },
  // Dark screen between Female response and Two measured nights, shown like Conclusion (human, AI_LOG Fireflies
  // step 10: new step, look "Like Conclusion", label "Perception"). Camera: Conclusion's whole-globe view.
  // Folded into Spectra as its opening beat in AI_LOG Impacts firefly-first step 6, reinstated in step 7 (human: "an
  // important link from the study --> to spectra"). Label: as before; the step after Spectra is also 'Perception' now
  // (step 6), to be named by the humans.
  {
    id: 'perception',
    part: 2,
    rung: 'animal',
    kind: 'fact',
    label: 'Impact',   // human (AI_LOG Impacts firefly-first step 8); was 'Perception'
    // Question replaces the sentence (human, AI_LOG Firefly flow step 2, option A). Was 'Humans perceive ALAN differently
    // to other parts of the biota.' (human, AI_LOG Fireflies step 10).
    // Wording: human (AI_LOG Impacts firefly-first step 8). Was 'Does our actual lighting environment impact fireflies
    // in the wild?' (Firefly flow step 2).
    // "Outside of the lab," added (human, AI_LOG Experience refinement step 17: Owens & Lewis 2021 is a lab study).
    text: 'Outside of the lab, does ALAN impact fireflies in the wild?',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    dark: true,
    // Plain black, no globe or limb ring (human, AI_LOG Experience refinement step 19); Response fades out, then this
    // fades in, then Spectra (main.js panRun; the sideways pan, option P2, was tried and cancelled by the human).
    black: true,
    guide: true,   // the firefly guide rests here (main.js; ladder plan phase 4, AI_LOG "Story review" steps 7–8)
  },
  // 'One communication problem' (placeholder, round 1) removed (human, AI_LOG Firefly tabs review round 7c).
  {
    id: 'two-nights',
    part: 2,
    rung: 'light',
    label: 'Spectra',   // human (AI_LOG Impacts firefly-first step 6); was 'Two measured nights'
    // Big text on the right instead of the card (human, AI_LOG Firefly flow step 2, option T1; was a card titled
    // 'Two measured nights', AI_LOG "Amber highlight" steps 3-4): first line while the divider shows Cherry Springs,
    // `reveal` lines in its place once it has swept across to Philadelphia (twoNights.js onSweep). Wording: human (first
    // line from "this is the light spectrum measured at a dark sky park, Cherry Springs"). 150x:
    // data/derived/spectra/amber_band_ratio.json (pipeline/spectra/03_amber_band_ratio.py, inferred, audit pending).
    // Details text (`note`): agent draft (method only). Side and swap-in-place: agent choices (as the card).
    // Beats (human, AI_LOG Firefly flow step 4, option S1; a fourth in step 10): ← → and the nav arrows step Cherry Springs (`text`) →
    // Philadelphia (divider sweeps across; `reveal[0]` when it arrives) → firefly wavelength (Firefly window; `reveal[1]`,
    // the firefly-eye line, once it has narrowed) → `reveal[2]`, the study line (window stays). One line at a time (twoNights.js beat, main.js onBeat).
    kind: 'fact',
    side: 'right',
    // The question was this step's opening beat in AI_LOG Impacts firefly-first step 6; back on Perception (step 7).
    // ', PA' added (human, AI_LOG Experience refinement step 3).
    // Was 'This is the light spectrum measured at a dark sky park, Cherry Springs, PA.' (option a, human, AI_LOG
    // Experience refinement step 29).
    text: 'Night light measured at Cherry Springs, PA, a dark sky park.',
    reveal: [
      // ", a dark sky park" removed (human, AI_LOG Firefly flow step 5: redundant with the first line).
      // Was 'In amber light (570–615 nm), Philadelphia’s night sky is about 150 times brighter than Cherry Springs.'
      // (option a, human, AI_LOG Experience refinement step 29; the band moved to Details).
      'In amber light, Philadelphia’s night sky is about 150 times brighter.',
      // Agent draft D2 chosen by the human, on its own beat before the study line (AI_LOG Firefly flow step 10, W1):
      // Lall et al. 1980 (eye peak ~570 nm) and Philadelphia's median spectrum peak (594 nm, checked in step 5, not shown).
      // Human wording (AI_LOG Experience refinement step 17). Was 'A firefly’s eye is most sensitive here, in the yellow,
      // the same band that holds the peak of Philadelphia’s night sky.'
      // Was 'Fireflies are most visually sensitive to the same wavelength band which is most prominent in the Philadelphia
      // night sky.' Option b (human, AI_LOG Experience refinement step 29): keeps only the sourced half (band:
      // sensitivity_bands.json, provisional curve; Lall et al. 1980); the Philadelphia-peak half rested on the step-5
      // one-off check (not scripted).
      'Fireflies see best in this band.',
      // 'Bright amber light silenced female fireflies most (Owens & Lewis 2021).' moved to Species perceptions' text
      // (human, AI_LOG Experience refinement step 3); twoNights.js BEATS 4 → 3.
    ],
    // Rewritten (human, AI_LOG Experience refinement step 29); dates from amber_band_ratio.json selected ranges (was
    // 'July 2014'). Was: 'Night spectra measured in July 2014, 240 per site. 150× = median irradiance in 570–615 nm,
    // Philadelphia ÷ Cherry Springs (the band the authors link to artificial light in the city spectra). Firefly band
    // (530–600 nm): half-maximum of a modelled curve around the female P. pyralis response peak (565 nm; provisional).
    // Recordings from male P. pyralis eyes peak at about 570 nm, fall steeply near 525 nm, and show a second, violet
    // peak near 400 nm.'
    note: '240 night spectra per site, 30 June–19 July 2014 (Spitschan et al. 2016). 150× = Philadelphia ÷ Cherry ' +
      'Springs, median irradiance in the amber band (570–615 nm), the band the authors link to artificial light in the ' +
      'city. Firefly band (530–600 nm, provisional): where a modelled female P. pyralis response curve (peak 565 nm) is ' +
      'above half its maximum. Male P. pyralis eyes peak near 570 nm, drop steeply near 525 nm, and have a second, ' +
      'violet peak near 400 nm.',
    sources: [
      { label: 'Spitschan et al. 2016, Sci. Rep.', url: 'https://doi.org/10.1038/srep26756',
        supports: 'night spectra, Philadelphia (City) and Cherry Springs (Rural), July 2014; 570–615 nm band' },
      { label: 'PA DCNR, Cherry Springs State Park',
        url: 'https://www.pa.gov/agencies/dcnr/recreation/where-to-go/state-parks/find-a-park/cherry-springs-state-park',
        supports: 'declared a Dark Sky Park by DCNR in 2000' },
      { label: 'Cherry Springs IDSP annual report (DarkSky International)',
        url: 'https://darksky.org/app/uploads/2015/04/CherrySprings-IDSP-2017-Annual-Report.pdf',
        supports: 'International Dark Sky Park since 2008, Gold Level' },
      { label: 'Owens & Lewis 2021, Insect Conserv. Divers.', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'bright amber light had the greatest impact on female responses' },
      { label: 'Lall & Worthy 2000, J. Insect Physiol.', url: 'https://doi.org/10.1016/S0022-1910(99)00206-1',
        supports: 'Photinus pyralis female response, peak 565 nm (the modelled firefly curve, provisional)' },
      // Added (human, AI_LOG Firefly flow step 9, option A); raw PDF data/raw/impacts/fireflies/Lall_1980_JCompPhysiol_135_21.pdf.
      { label: 'Lall et al. 1980, J. Comp. Physiol.', url: 'https://doi.org/10.1007/BF00660178',
        supports: 'ERG, ventral sector of dark-adapted male P. pyralis compound eyes, N = 13: peaks ~570 nm (yellow) and ~400 nm ' +
          '(violet, 380–440 nm between subjects); 1.45–1.85 log unit fall in ~25 nm near 525 nm; in tune with the 565 nm flash' },
    ],
    // Globe camera between the two Spitschan sites (midpoint of the printed coordinates; display only), so both glows
    // are in view during the transition from Local firefly (round 7f). Altitude and timing: agent choices.
    camera: { lat: 40.808419, lng: -76.500617, altitude: 0.35 },
    fly: 1600,
    swipe: 0,
    // 3D night spectra, Philadelphia | Cherry Springs (app/src/twoNights.js; data/derived/spectra/, Spitschan et al.
    // 2016; human decisions: handoff 2026-10-04_two-nights-spectra.md, AI_LOG Firefly narrative round 3c).
    nights: true,
    // Sites (impacts.js SITE_POINTS) whose glows open the left / right half, arriving from the step whose impacts.site
    // is the first one (human: "two points, two halves", AI_LOG Firefly tabs review round 7f).
    nightsSites: ['spitschan2016_city', 'spitschan2016_rural'],
  },
  // Species perceptions, firefly only, Philadelphia | Cherry Springs (human, AI_LOG "Story review" step 3): each site's
  // measured night light as the cloud, weighted by the firefly curve; fixed divider, no cycling (twoNights.js,
  // nights: 'pair'; data/derived/spectra/species_curves.json). Was Firefly | Human on Philadelphia only (human, AI_LOG
  // "Species perceptions" steps 1–7), and before that round 7j's cycling view, kept as [DRAFT] Species perceptions in
  // Explore. Animal curves provisional (human: sources to be identified; nothing shown on screen).
  {
    id: 'species-perceptions',
    part: 2,
    rung: 'eye',
    kind: 'fact',   // big narrative text on the right, no card (human, AI_LOG Fireflies step 12)
    side: 'right',
    label: 'Perception',   // human (AI_LOG Impacts firefly-first step 6); was 'Species perceptions'
    // Was a card titled 'Species perceptions': '[PLACEHOLDER] The measured night light of Philadelphia, weighted by
    // each species' spectral sensitivity.'
    // Was 'Fireflies perceive ALAN with their own eyes, not ours.' (human, AI_LOG Fireflies step 12).
    // Was 'Philadelphia’s Artificial Light drowns out the firefly light.' (human, AI_LOG Firefly flow step 2); replaced by
    // Two measured nights' study line, moved here (human, AI_LOG Experience refinement step 3: the old line "a risky
    // non academic claim").
    text: 'Bright amber light silenced female fireflies most (Owens & Lewis 2021).',
    sources: [
      { label: 'Spitschan et al. 2016, Sci. Rep.', url: 'https://doi.org/10.1038/srep26756',
        supports: 'night spectra, Philadelphia (City) and Cherry Springs (Rural), July 2014' },
      // CIE 2019 scotopic V′(λ) source removed with the human side ("Story review" step 3, human: "fix sources").
      { label: 'Lall & Worthy 2000', supports: 'Photinus pyralis female response, peak 565 nm' },
      // With the moved study line (AI_LOG Experience refinement step 3); same entry as Two measured nights.
      { label: 'Owens & Lewis 2021, Insect Conserv. Divers.', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'bright amber light had the greatest impact on female responses' },
    ],
    camera: { lat: 40.808419, lng: -76.500617, altitude: 0.35 },
    swipe: 0,
    nights: 'pair',
  },
  // Firefly counts across the eastern US (human, AI_LOG Firefly flow step 4: "M1 as a new step"): ties up the firefly
  // section before All effects. Sentence: agent draft M1 chosen by the human, from McNeil et al. 2024 (raw PDF:
  // data/raw/impacts/fireflies/McNeil_2024_STOTEN_172329.pdf). Label: [PLACEHOLDER] (the study's citation), to be named
  // by the humans. Visual (the eastern US at night, 2025 view, the Firefly Watch survey extent of their Fig. 1), camera,
  // fly, rung: agent choices. No Impacts layer, so All effects keeps its globe → chart arrival.
  {
    id: 'firefly-counts',
    part: 2,
    rung: 'studies',
    kind: 'fact',
    side: 'right',
    label: 'Firefly Populations',   // human (AI_LOG Impacts firefly-first step 2); was '[PLACEHOLDER] McNeil et al. 2024'
    // Was 'Across the eastern US, fewer fireflies are counted where nights are brighter: one pressure among climate, soil
    // and land cover.' Human wording (AI_LOG Experience refinement steps 29–30; "lower", not "decreasing": the study
    // compares places, not years). `subtext`: smaller, darker line below (human: "focus audience eyes on main story").
    text: 'In the eastern US, firefly counts are lower in areas with more ALAN,',
    subtext: 'one factor alongside climate, soil and others.',
    note: '24,683 Firefly Watch citizen-science surveys, eastern US (east of the 100th meridian), 2008–2016. In random-forest ' +
      'models of 79 predictors, night-time lights ranked 9th overall and 3rd in areas of high climate quality; counts were ' +
      'lower where night-time lights were brighter. Climate and weather were the strongest predictors. The authors note ' +
      'that the effects of light are confounded with those of urbanization.',
    sources: [
      { label: 'McNeil et al. 2024, Sci. Total Environ.', url: 'https://doi.org/10.1016/j.scitotenv.2024.172329',
        supports: 'Firefly Watch, 24,683 surveys 2008–16, eastern US; Table 2: night-time lights (NTL) rank 9 (all data, ' +
          'importance 2.47) and 3 (high climate, 2.51); Fig. 3F: abundance lower at higher night-time lights DN; Discussion: ' +
          'results support the hypothesis that anthropogenic light may harm firefly populations, confounded with urbanization; ' +
          'climate/weather more important than land cover' },
    ],
    // Centre of the Firefly Watch extent (Fig. 1: ~25–49 N, ~100–67 W), display only.
    camera: { lat: 37, lng: -84, altitude: 1.1 },
    fly: 2500,
    // From Perception: no flight, Perception's view fades out onto this view (human, AI_LOG Experience refinement step 18).
    cutFrom: 'species-perceptions',
    swipe: 0,
    noSwipe: true,   // divider and "2025" label hidden: at the left edge they sat over the menu (agent choice)
  },
  {
    id: 'effects',
    part: 2,
    rung: 'studies',
    kind: 'fact',   // big text on the right, card text behind Details (human, AI_LOG Fireflies step 17)
    side: 'right',
    label: 'Studies',   // human (AI_LOG Experience refinement step 4: "Across" twice in a row); was 'All effects'
    // Was title '3,254 effects'. Sentence: agent draft chosen by the human (their "…generally significant" with
    // 'significant' → 'substantial'), AI_LOG Fireflies step 17. Now agent draft A3 with 'widespread' (human, AI_LOG
    // Story flow step 3): effects recorded in all 9 species groups (our grouping of Data S1). Was '…generally substantial.'
    // Wording: human (AI_LOG Impacts firefly-first step 3; "207" moved here from the removed Studies step). Was 'From one
    // firefly to all of life studied: the impacts of artificial light are widespread.'
    // Was 'Across 207 published studies, the impacts of artificial light on biota are widespread.'
    // 'Beyond fireflies, ' added (human, Experience refinement step 7).
    text: 'Beyond fireflies, 207 published studies reveal widespread impacts of artificial light on biota.',   // human (Experience refinement step 4)
    // First three sentences: the removed Studies step's note, verbatim, placed first (human, AI_LOG Impacts firefly-first
    // step 2, A2; order: agent choice).
    note: 'Each dot is one study that compared living things under artificial light at night with the same ' +
      'under natural darkness. These are 207 of the 314 studies gathered in a 2025 meta-analysis: ' +
      'the ones we could place on the map. Colour = the study’s main category. ' +
      'The 207 studies on the globe measured 3,254 effects. Each dot is one, in the lane of what was measured. ' +
      'Further right = a bigger change under light. Only the size of the change is shown, not its direction: ' +
      'for some measures more is harmful, for others less. White line = the median study: each study’s middle ' +
      'effect, then the middle of those. ' +
      // Moved from under the chart, verbatim (human, AI_LOG Experience refinement step 23, D1).
      '|Hedges g| = difference between lit and dark groups ÷ the normal spread between individuals. ' +
      'Log scale; values above 10 sit at the edge. small / medium / large: Cohen (1988) conventions.',
    sources: [
      // From the removed Studies step (A2).
      { label: 'Czarnecka et al. 2025, Global Change Biology', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'sec. 2.1: 314 studies, 4,905 effect sizes; control group under dark night conditions vs light up to 180 lx' },
      { label: 'Czarnecka et al. 2025, sec. 2.5', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'absolute values |g| used for magnitude because opposite effects within a category could cancel out' },
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'study records; locations geocoded by us (02_geocode.py); category and |g| of each effect record; ' +
          'median of study medians computed by us from |g|' },
    ],
    // Hold 2 s (human, AI_LOG Impacts firefly-first step 3, D2; was 500). `globeSpin`: after the fly-out the globe turns
    // slowly and steadily, at the intro's speed, until the step is left (human, step 6: "rotating as it normally would";
    // replaces step 3's 40° turn during the hold, camera lng 50 → `globeTurn` lng 10).
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    globeSpin: true,
    // Arriving from a step without the Impacts layer (Species perceptions): the globe flies out with the study dots,
    // holds `globeHold`, then the records fly into the chart (main.js; human, AI_LOG Fireflies step 14: 2.5 s + 1 s; hold 0.5 s, step 15).
    fly: 2500,
    globeHold: 2000,
    swipe: 0,
    // The firefly example (299-3) shows on arrival and fades at the first callout (human, step 5: "a relic of the previous chapter").
    // Callouts (human, AI_LOG Effect dots and examples steps 4–5): quotes chosen by the human, verbatim from the
    // study's title or abstract (data/derived/impacts/abstracts.json, Crossref); citation 'Author Year' (human). Each
    // arrow press is one beat: the quote replaces the big text, the study is selected and its card opens; past the
    // last one the arrow moves the story. `effect` = the ringed dot (agent choice of record within the study).
    impacts: { view: 'chart', records: true, filter: true, example: '299-3', exampleLabel: 'Fireflies, female response',   // was 005-2 Black swans (human, AI_LOG Impacts reorder step 2)
      // Aphid and wallaby moved to Broader Impacts (human, AI_LOG Effect dots and examples step 6).
      callouts: [
        { effect: '169-1', quote: 'Artificial light at night increases growth and reproductive output in Anolis lizards', cite: 'Thawley & Kolbe 2020', from: 'title' },
      ] },
  },
  // The next two questions and their one-word answers ("Yes", "Not as much as thought") are the human's
  // (AI_LOG Impacts steps 29, 35–36); the rest of each text is a DRAFT placeholder by the agent.
  {
    id: 'intensity',
    part: 2,
    rung: 'studies',
    kind: 'fact',   // human, AI_LOG Fireflies step 17 (was title 'Does light intensity affect biota?', note began 'Yes.')
    side: 'right',
    label: 'Light level',
    text: 'Impacts occur at every light level, even in low light.',   // agent draft chosen by the human (step 17)
    note: '[DRAFT] The same effects, now sorted by how bright the light was. Effects appear at every level, ' +
      'even below 5 lux. The meta-analysis found them mostly not dose-dependent: low light had an impact ' +
      'comparable to moderate and high light. White line = the median study: each study’s middle effect, then the middle of those. ' +
      // Moved from under the chart, verbatim (human, AI_LOG Experience refinement step 23, D1).
      '|Hedges g| = difference between lit and dark groups ÷ the normal spread between individuals. ' +
      'Log scale; values above 10 sit at the edge. small / medium / large: Cohen (1988) conventions.',
    sources: [
      { label: 'Czarnecka et al. 2025, sec. 2.2', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'light levels: low ≤ 5 lx, moderate 5–20 lx, high > 20 lx (from street lighting standards)' },
      { label: 'Czarnecka et al. 2025, sec. 3.1, Fig. 1, sec. 4', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'effects mostly not dose dependent; strong influence of low light levels, comparable to moderate and high' },
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'light level of each effect record (Night_Lx_coded); median of study medians computed by us from |g|' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // Firefly example removed here: unselected once the callouts begin (human, AI_LOG Effect dots and examples step 5).
    // Callouts (human, AI_LOG Effect dots and examples steps 4–5): quotes chosen by the human, verbatim from the
    // study's title or abstract (data/derived/impacts/abstracts.json, Crossref); citation 'Author Year' (human). Each
    // arrow press is one beat: the quote replaces the big text, the study is selected and its card opens; past the
    // last one the arrow moves the story. `effect` = the ringed dot (agent choice of record within the study).
    impacts: { view: 'chart', records: true, filter: true, group: 'band',
      callouts: [
        { effect: '166-1', quote: 'street lights caused a reduction in activity of slow‐flying bats', cite: 'Stone et al. 2012', from: 'abstract' },
      ] },
  },
  {
    id: 'light-type',
    part: 2,
    rung: 'studies',
    kind: 'fact',   // human, AI_LOG Fireflies step 17 (was title 'Does light temperature affect biota?', note began 'Not as much as thought.')
    side: 'right',
    label: 'Light type',
    // Was 'Impacts occur regardless of light type.' (human, AI_LOG Fireflies step 17).
    text: 'Impacts occur across all light types.',   // wording: human (AI_LOG Experience refinement step 29)
    note: '[DRAFT] The same effects, sorted by type of light. Warm white light ' +
      '(below 3000 K) had an impact similar to cool white light, contrary to the common view that warm light is ' +
      'gentler. White light that also emits ultraviolet had the strongest impact. The narrow-spectrum lanes rest ' +
      'on few studies, so read them with caution. ' +
      // Moved from under the chart, verbatim (human, AI_LOG Experience refinement step 23, D1).
      '|Hedges g| = difference between lit and dark groups ÷ the normal spread between individuals. ' +
      'Log scale; values above 10 sit at the edge. small / medium / large: Cohen (1988) conventions.',
    sources: [
      { label: 'Czarnecka et al. 2025, sec. 2.2', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'light types: BS warm < 3000 K, BS cool > 3000 K, BS_UV cool white with UV; NS blue, green, yellow-orange' },
      { label: 'Czarnecka et al. 2025, sec. 3.1, Fig. 1, sec. 4', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'BS warm and BS cool did not differ significantly; BS_UV greatest overall impact; NS comparable to BS warm/cool, few studies, wide intervals' },
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'light type of each effect record (Light_Type_coded); median of study medians computed by us from |g|' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // Door (299-3) removed when the fireflies chapter moved into "Female response" (human, AI_LOG Firefly tabs round 5b).
    // Firefly example removed here (as Light level). Wallaby here (human: "light type will affect someone").
    // Callouts (human, AI_LOG Effect dots and examples steps 4–5): quotes chosen by the human, verbatim from the
    // study's title or abstract (data/derived/impacts/abstracts.json, Crossref); citation 'Author Year' (human). Each
    // arrow press is one beat: the quote replaces the big text, the study is selected and its card opens; past the
    // last one the arrow moves the story. `effect` = the ringed dot (agent choice of record within the study).
    impacts: { view: 'chart', records: true, filter: true, group: 'type',
      callouts: [
        // Wallaby (as it was on Biosphere Response) replaces the seabird: more ringed dots (human, AI_LOG Experience
        // refinement step 26). Was { effect: '308-1', quote: 'Light pollution critically affects fledglings of
        // burrow-nesting seabirds, leading to massive mortality events.', cite: 'Atchoi et al. 2023', from: 'abstract' }.
        { effect: '154-2', quote: 'White LED exposed wallabies had significantly suppressed nocturnal melatonin', cite: 'Dimovski & Robert 2018', from: 'abstract' },
      ] },
  },
  // Broader Impacts (human request, Firefly transition task step 4): filler screen with the human's question;
  // charts, data and sources on ecosystem-level impacts may follow here (not started).
  {
    id: 'broader',
    part: 2,
    rung: 'studies',
    kind: 'fact',
    side: 'right',   // chart layout: circle left, text + key right, size buttons on top (human, AI_LOG Fireflies step 29)
    label: 'Biosphere Response',   // human (AI_LOG Experience refinement step 5); was 'Broader Impacts'
    // Wording: human (AI_LOG Effect dots and examples step 6). Was 'The biosphere is responding to a new nighttime experience.'
    // (human, AI_LOG Fireflies steps 30–32); before that
    // Opening line (human, AI_LOG Experience refinement step 5); the line below moved to open the Conclusion.
    // Back to the equilibrium line, so the circle's thesis is clear (human, AI_LOG Experience refinement step 13); was
    // 'So how is the biosphere responding?' (step 5).
    text: 'Across the biosphere, ALAN is upsetting the equilibrium of natural systems.',
    // previous text: 'Across the biosphere, ALAN is upsetting the equilibrium of natural systems.'; before that 'All classes of biota are simultaneously responding to a new global environment.' (step 17), before that 'So how does this translate to ecosystem level impacts?'
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    fly: 2500,
    swipe: 0,
    // circle: all records gather into one circle of species-group sectors (human, AI_LOG Broader Impacts circle concept
    // steps 3 and 7; impacts.js drawCircle). On the main URL since step 7 (was behind ?broader=circle).
    // Callouts (human, AI_LOG Effect dots and examples steps 4–5): quotes chosen by the human, verbatim from the
    // study's title or abstract (data/derived/impacts/abstracts.json, Crossref); citation 'Author Year' (human). Each
    // arrow press is one beat: the quote replaces the big text, the study is selected and its card opens; past the
    // last one the arrow moves the story. `effect` = the ringed dot (agent choice of record within the study).
    impacts: { view: 'globe', dots: false, circle: true,
      // Aphid, wallaby, then the ecosystem quote (human: impacts "varying across the class groups", step 6; order: agent; last one step 8).
      callouts: [
        // 200-6: adult aphids after 10 days (Data S1 records for this study are mixed; the quote is the authors' summary).
        { effect: '200-6', quote: 'aphid colony growth and aphid maturation were reduced significantly by ALAN treatments', cite: 'Heinen et al. 2022', from: 'abstract' },
        // Wallaby (154-2, Dimovski & Robert 2018) and salmon (112-4, Oppedal et al. 2001) removed: two examples are enough
        // (human, AI_LOG Experience refinement step 23).
        // Was 231-2 Giavi et al. 2020 'Artificial light at night can modify ecosystem functioning beyond the lit area' (title).
        // Now study 106 (110 bird records, so much of the Birds sector is ringed; human, AI_LOG Effect dots and examples step 8).
        // Quote = the study's title in Data S1 (no abstract in Crossref). 106-108: melatonin at night (agent choice).
        { effect: '106-108', quote: 'Artificial light at night affects brain plasticity and melatonin in birds', cite: 'Moaraf et al. 2020', from: 'title' },
        // Fifth (human, AI_LOG Conclusion step 6: q1, no rings): the meta-analysis behind the circle, not one study, so no
        // `effect` (nothing ringed); "Source" links to the paper (`url`). Verbatim, Czarnecka et al. 2025 Introduction
        // (data/raw/impacts/czarnecka2025/Czarnecka_2025_GCB_article.pdf, p. 1; the sentence cites Sanders et al. 2021).
        { quote: 'This anthropogenic intrusion reverberates through biological communities', cite: 'Czarnecka et al. 2025', from: 'article',
          url: 'https://doi.org/10.1111/gcb.70569' },
      ],
      // `release` (human, AI_LOG Experience refinement step 23: M1, T1, H1): one more arrow beat after the last callout;
      // the labels, key and size buttons fade and the dots move freely, bouncing off each other inside the circle
      // (impacts.js). The last quote stays on screen. A display device, not data.
      release: true,
      // Comes in below the quote while the dots move (human: wording (c), placement P1, AI_LOG Experience refinement
      // steps 24–25). Backing read in Czarnecka et al. 2025: ALAN "reverberates through biological communities" (Intro,
      // citing Sanders et al. 2021); species interactions behind "the uncertainty in model estimates" (Discussion).
      releaseLine: 'Together, these impacts interact in uncertain ways.' },
  },
  // Conclusion (human request, step 4): dark screen (dark: true fades the globe out, main.js); call to action in the
  // human's wording, final (human, AI_LOG Broader Impacts circle concept step 10: DRAFT tag removed).
  {
    id: 'conclusion',
    part: 2,
    rung: 'space',
    kind: 'fact',
    label: 'Conclusion',
    // Beats (human, AI_LOG Conclusion step 6): the text on arrival (lights out, hum fades), then each `reveal` line on the
    // next arrow (`beats: true`, main.js). Wording: human's (step 4). Was 'We need ALAN, but do we need it all the time,
    // everywhere?' ('light at night' → 'ALAN', human, AI_LOG Fireflies step 9).
    // Step 6 (human): autoBeat 4000 → 2500 ms; the earth fades to dark from beat 0 (the text was unreadable on the lit
    // globe), so `darkFrom` removed; the hum plays on until the dusk line (`humFrom: 1`); line 0 anchored (main.js).
    // Transition (human, AI_LOG Experience refinement step 5): the circle's dots fade out and 'Across the biosphere …'
    // (moved from Broader Impacts) shows centred on the lit globe; on its own after `autoBeat` ms the dusk line comes in
    // below it while the earth fades to dark and the hum fades (`darkFrom: 1`, `together: [1]`); the next arrow replaces
    // both with the 5b line. autoBeat 4000 ms and the 1 s dot fade: agent choices. main.js setCallout / applyDark.
    // Step 13 (human, option "Conclusion starts at dusk"): the equilibrium line went back to Biosphere Response, so the
    // Conclusion opens on the dusk line (dots fade, earth darkens, hum fades on arrival), then 5b, then responsive
    // lighting; `together`, `autoBeat`, `humFrom` removed, `humOff` back.
    text: "We may be entering the dusk of the biosphere's stability.",
    // Third beat: responsive lighting as the human's design position, citing both papers (human, AI_LOG Conclusion steps 6–7).
    // "may be" → "is" (human, AI_LOG Experience refinement step 24).
    reveal: ['ALAN is necessary for the modern apparatus of human society. But not all the time, everywhere.',
      'Responsive lighting can restrict ALAN to an optimal time, place, and set of environmental conditions.'],
    beats: true,
    // Note: AGENT DRAFT (claude-opus-5-5, AI_LOG Conclusion step 7), stating only what the two sources say; Bolliger et al.
    // 2020 from its title only (paper not read; reference from Czarnecka et al. 2025).
    note: 'Czarnecka et al. (2025) conclude that ALAN use should be restricted to the minimum necessary. They name ' +
      'restricting where light falls as one of the most effective strategies, with dimmers, motion sensors and timers ' +
      'as possible complementary measures. Bolliger et al. (2020) studied the effects of traffic-regulated street ' +
      'lighting on nocturnal insect abundance and bat activity.',
    sources: [
      { label: 'Czarnecka et al. 2025, Global Change Biology 31: e70569', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'Conclusions: "ALAN use should be restricted to the minimum necessary"; restricting the spatial extent of ' +
          'illumination among the most effective strategies; dimmers, motion sensors and timers may provide additional, ' +
          'complementary benefits (citing Bolliger et al. 2020). Read from data/raw/impacts/czarnecka2025.' },
      { label: 'Bolliger et al. 2020, Basic and Applied Ecology 47: 44–56', url: 'https://doi.org/10.1016/j.baae.2020.06.003',
        supports: 'Title: "Effects of Traffic-Regulated Street Lighting on Nocturnal Insect Abundance and Bat Activity". ' +
          'Reference from Czarnecka et al. 2025; the paper itself not read.' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    dark: true,
    humOff: true,
    // humOff (hum out on arrival; human, AI_LOG Copy editing step 11) replaced: the hum fades with the dark at beat 1
    // (human, AI_LOG Experience refinement step 5; main.js applyDark).
  },
  // ── Part 3: Explore (human request, step 4: its own top-level heading, after the conclusion) ──
  {
    id: 'explore',
    part: 3,
    label: 'Explore all studies',
    title: 'Explore all studies',
    // Human request (AI_LOG Impacts step 34): free browsing as the last Part 2 step.
    text: 'Click a dot to open its study. Rings hold several studies close together: click to spread them out. ' +
      'On a study card, ‹ › steps through all 207 studies from west to east.',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    fly: 2500,
    swipe: 0,
    impacts: { view: 'globe', explore: true },
    muteAudio: true,   // the background hum is muted on arrival; the mute button turns it back on (human, AI_LOG Copy editing step 9)
  },
];

// Steps taken out of the story by the humans, kept here so their sourced text is not lost.
// Iceland: retired (human, AI_LOG step 39, option 3): its +106% comes mostly from pixels that are 0 in 2015
// (EOG v2.1) and faintly lit in 2025 (v2.2); on pixels lit in both years it is -17%
// (data/derived/story/version_sensitivity_2015_2025.json).
// France and Ukraine: retired (human, AI_LOG Story step 41: "replace France with Cote d'ivoire and then
// remove Ukraine. Just two countries").
// Mice (study 278, spectral chapter 'mice'): retired (human, AI_LOG Broader Impacts circle concept step 10: "get rid of
// the DRAFT Mice section under explore, it's a gonner"). Its chapter code in app/src/spectral.js is unused now.
export const retired = [
  // [DRAFT] Explore steps retired (human, AI_LOG Experience refinement step 11: "move all the DRAFT components in the
  // explore section into some archive ... those aren't necessary anymore"): Signal production, Mate-finding, Local
  // firefly, Species perceptions (draft). Their code paths (spectral.js chapters, twoNights.js 'species' mode, the
  // Local firefly ↔ Two measured nights glow transition in main.js) are unused now; not deleted.
  {
    id: 'signal-production',
    part: 3,   // moved to Explore as a draft (human, AI_LOG Impacts reorder step 2)
    label: '[DRAFT] Signal production',
    title: 'Signal production',
    // Card text: agent draft on the human's request (AI_LOG Firefly tabs round 5g), from owens2018_results.json.
    text: '[DRAFT] Male *Aquatica ficta* fireflies in Taiwan, tested one at a time under eight colours of light, each ' +
      'dim and ten times brighter (six males analysed). The authors report brighter, less frequent flashes at 533 nm ' +
      'and below, and no significant change at 597 nm and above. Left: flashing at the dark base values; right: under ' +
      'the chosen light, at the mean rate and relative brightness in Table 1.',
    sources: [
      { label: 'Owens et al. 2018, PLoS ONE, Table 1', url: 'https://doi.org/10.1371/journal.pone.0191576',
        supports: 'mean ± SD flash intensity (counts) and flash frequency (peaks/min), ratio to dark and p, for 8 LED wavelengths (444–663 nm) at dim (1×) and bright (10×); dark base values 5420 counts, 43.167 peaks/min' },
      { label: 'Owens et al. 2018, Methods', url: 'https://doi.org/10.1371/journal.pone.0191576',
        supports: 'A. ficta bioluminescence peak 565 nm; alarm flashes approx. 200 ms; dim 0.107, bright 1.075 μmol m⁻² s⁻¹' },
    ],
    // Zoom-in from the Fireflies point (round 6b): the globe flies closer over the collection site while the glow
    // grows; the 3D scene then opens over it. Altitude and timing: agent choices.
    camera: { lat: 24.990195, lng: 121.555824, altitude: 0.04 },
    fly: 2200,
    swipe: 0,
    // Scene "A + B" (human, AI_LOG Firefly narrative round 4f): 3D beats + Table 1 strip (spectral.js, chapter 'signal').
    // Beats: each wavelength at bright (10×) only; no dim beats and no dark beat (human, AI_LOG Firefly tabs review
    // round 6j: the dark base values stay as the left male). Numbers are read from owens2018_results.json.
    // site: arriving from the step with the same impacts.site, the scene grows out of that point's glow.
    spectral: { chapter: 'signal', manual: true, site: 'owens2018',
      beats: [444, 463, 488, 515, 533, 597, 628, 663].map(nm => ({ nm, exposure: 'bright' })) },
  },
  {
    id: 'mate-finding',
    part: 3,   // moved to Explore as a draft (human, AI_LOG Impacts reorder step 2)
    label: '[DRAFT] Mate-finding',
    title: 'Mate-finding',
    // Card text: agent draft on the human's request (AI_LOG Firefly tabs round 5g), from kivela2023.json.
    text: '[DRAFT] Female *Lampyris noctiluca* glow-worms glow to attract flying males. Over 20 nights in southern ' +
      'Finland (2020), 299 dummy females (green LEDs) were set under blue, white, yellow or red light, or none, and ' +
      'the males each one trapped were counted. Left: no light; right: the chosen light. Each green point is one dummy ' +
      'female, each pale point one trapped male. Under blue and ' +
      'white light 35.0 % and 36.7 % caught at least one male; under yellow, red and no light 71.2 %, 73.3 % and 68.3 %.',
    sources: [
      { label: 'Kivelä et al. 2023, Sci. Total Environ., Tables 1 and 3', url: 'https://doi.org/10.1016/j.scitotenv.2022.159451',
        supports: 'treatments: blue 452 nm, white 449 nm, yellow 575 nm, red 625 nm (peak wavelengths), control off; dummy female LED 562 nm; share of dummy females with ≥ 1 male per treatment (Table 3)' },
      { label: 'Kivelä et al., Dataverse (CC0)', url: 'https://doi.org/10.7910/DVN/QWQPLJ',
        supports: 'males trapped per dummy female, 299 traps over 20 nights (2020), one pillar per trap' },
    ],
    // Globe camera (hidden behind the 3D scene) over the Philadelphia city measurement site, close in, so moving on to
    // Local firefly the scene closes into a glow over that site while the globe zooms out (human: "scene closes into
    // the point", AI_LOG Firefly tabs review round 7d). Altitude and timing: as Signal production (agent choices).
    camera: { lat: 39.952237, lng: -75.188734, altitude: 0.04 },
    fly: 2200,
    swipe: 0,
    // Continuous scene, third band (human, AI_LOG Firefly tabs round 5b). "Dark vs lit pair" (human, review round 6o):
    // control always on the left, the beat's treatment on the right, so no control beat (kivela2023.json).
    // site: between this step and the step with the same impacts.site, the scene closes into / opens out of its glow.
    spectral: { chapter: 'glow', manual: true, site: 'spitschan2016_city',
      beats: ['blue', 'white', 'yellow', 'red'].map(treatment => ({ treatment })) },
  },
  // Local firefly (human, AI_LOG Firefly tabs review round 7d): shown like Fireflies, the point moved from Taipei to
  // Philadelphia. The point = the city measurement site printed by Spitschan et al. 2016 (documented; impacts.js
  // SITE_POINTS), the same site as the Philadelphia spectra in Two measured nights; it is not a firefly record.
  // Arriving from Mate-finding the 3D scene closes into the point's glow while the globe zooms out (main.js, spectral.js).
  // Card text: agent draft on the human's request (round 7d), from the sources below. No source in the repo places
  // P. pyralis in Philadelphia, so the card does not say it.
  {
    id: 'local-firefly',
    part: 3,   // moved to Explore as a draft (human, AI_LOG Fireflies step 8)
    label: '[DRAFT] Local firefly',
    title: 'Local firefly · Philadelphia, Pennsylvania',
    text: '[DRAFT] *Photinus pyralis* courts with flashes too. In the global dataset it appears in two field studies, ' +
      'both in Virginia, on courtship, flashing, dispersal and abundance under LED light. The point marks the roof in ' +
      'Philadelphia where night light was measured in July 2014.',
    note: 'The point is the measurement site (David Rittenhouse Laboratories, University of Pennsylvania; coordinates ' +
      'as printed in the paper), not a firefly record.',
    sources: [
      { label: 'Spitschan et al. 2016, Sci. Rep., Methods', url: 'https://doi.org/10.1038/srep26756',
        supports: 'Locations: City = five-story roof of David Rittenhouse Laboratories, University of Pennsylvania (39.952237° N, −75.188734° W; elevation 12 m); spectra collected in July 2014' },
      { label: 'Firebaugh & Haynes 2016, Oecologia', url: 'https://doi.org/10.1007/s00442-016-3723-1',
        supports: 'Data S1 study 229: P. pyralis, field, Virginia, USA, white cool LED; courtship (males within 1 m of the female, female flashes, proportion of males flashing) and dispersal' },
      { label: 'Firebaugh & Haynes 2019, Basic Appl. Ecol.', url: 'https://doi.org/10.1016/j.baae.2018.07.005',
        supports: 'Data S1 study 028: P. pyralis and Photuris versicolor, field, University of Virginia, white warm LED; abundance' },
      { label: 'Seliger et al. 1964, J. Gen. Physiol., Table I', url: 'https://doi.org/10.1085/jgp.48.1.95',
        supports: 'point colour: P. pyralis in vivo flash, peak 5620 Å (562 nm), photoelectric spectrometer ("Present work, 1963")' },
    ],
    camera: { lat: 39.952237, lng: -75.188734, altitude: 0.35 },
    fly: 2200,
    swipe: 0,
    impacts: { view: 'globe', site: 'spitschan2016_city' },
  },
  // [DRAFT] Species perceptions: copy of the original step as it was, moved to Explore (human, AI_LOG "Species
  // perceptions" steps 1–4). Its cycle now also includes Human day (photopic V(λ)), added to species_curves.json.
  // Species perceptions (human, AI_LOG Firefly tabs review round 7j): the same two sites' measured night light as a
  // rotating cloud, weighted by each species' response curve, one species every 1.5 s (twoNights.js, nights: 'species';
  // data/derived/spectra/species_curves.json). Animal curves provisional (human: sources to be identified; nothing
  // shown on screen). Card text: placeholder.
  {
    id: 'species-perceptions-draft',
    part: 3,
    label: '[DRAFT] Species perceptions',
    title: 'Species perceptions',
    text: '[PLACEHOLDER] The measured night light of Philadelphia and Cherry Springs, weighted by each species\' ' +
      'spectral sensitivity.',
    sources: [
      { label: 'Spitschan et al. 2016, Sci. Rep.', url: 'https://doi.org/10.1038/srep26756',
        supports: 'night spectra, Philadelphia (City) and Cherry Springs (Rural), July 2014' },
      { label: 'CIE 2019, scotopic V′(λ)', url: 'https://doi.org/10.25039/CIE.DS.gr6w4b5g', supports: 'human night curve' },
      { label: 'Bowmaker 1977', supports: 'rock pigeon pigment peaks 460, 515, 567 nm' },
      { label: 'Bennett & Brown 1985', supports: 'Carolina sphinx receptor peaks 357, 450, 520 nm' },
      { label: 'Lall & Worthy 2000', supports: 'Photinus pyralis female response, peak 565 nm' },
      { label: 'Hasselmann 1962, in Lord et al. 2016', supports: 'bronze ground beetle ERG peaks 348, 430, 500, 620 nm' },
      { label: 'Beason & Loew 2008', supports: 'bobolink pigment peaks 372, 403, 505, 564 nm; rod 502 nm' },
    ],
    camera: { lat: 40.808419, lng: -76.500617, altitude: 0.35 },
    swipe: 0,
    nights: 'species',
  },
  // India and Tanzania: retired (human, AI_LOG Copy editing and drafting step 2: "We won't do India and Tanzania
  // to start as examples. Let's toss them."). Kept here so their sourced text is not lost.
  {
    id: 'india',
    part: 1,
    title: 'India',
    // Tagline (human choice I-3, Light story refinement step 4; agent draft). The policy is sourced
    // (PIB); "brought light to places that were dark" is the humans' framing, shown by the sweep.
    // Figure line removed (human): was 'ALAN increased by 93%' (+92.56%, 02_country_change.py, inferred).
    tagline: 'India’s rural electrification policy brought light to places that were dark at night.',
    // text + sources sit behind "Details & sources" when a tagline is set.
    text: 'Lights spread as villages were connected to the grid: under the national DDUGJY scheme, ' +
      'launched in December 2014, the last 18,374 unelectrified villages were reported electrified by April 2018.',
    sources: [
      { label: 'Ministry of Power, DDUGJY factsheet (PIB, 27 May 2022)',
        url: 'https://static.pib.gov.in/WriteReadData/specificdocs/documents/2022/may/doc202253060201.pdf',
        supports: 'launched Dec 2014; all inhabited un-electrified census villages electrified on 28 Apr 2018 ' +
          '(as reported by states); 18,374 villages electrified 2014-15 to 28.04.2018' },
    ],
    camera: { lat: 22, lng: 80, altitude: 0.55 },
    fly: 3000,
    sweep: { east: 97.4, west: 68.1, hold: 800, duration: 3500 },
  },
  {
    id: 'tanzania',
    part: 1,
    title: 'Tanzania',
    // Human request (Light story refinement, 2026-10-04): Tanzania replaces Côte d'Ivoire (now in `retired`).
    // Not computed in 02_country_change.py (human: "Don't compute tanzania").
    // Tagline (human choice T-3; agent draft). Village electrification is sourced; "light reached new
    // places, alongside the ecosystems around them" is the humans' framing.
    tagline: 'As Tanzania’s villages joined the grid, light reached new places, alongside the ecosystems around them.',
    // DRAFT (agent, 2026-10-04): details sentence; numbers documented, sources below.
    text: 'Under the Rural Energy Agency (REA) programme, villages on mainland Tanzania connected to electricity ' +
      'rose from 4,395 of 12,268 (36%) in June 2016 to 11,313 of 12,318 in November 2023. ' +
      'About 40% of Tanzania’s land is protected (2025).',
    sources: [
      { label: 'TanzaniaInvest, “Rural Electrification Program to Reach 7,873 Villages in 5 Years” (9 Aug 2016)',
        url: 'https://www.tanzaniainvest.com/energy/rural-electrification-phase-3',
        supports: '"As of June 2016, 4,395 villages ... connected ... 36% of the 12,268 villages in mainland Tanzania" (news report; page read 2026-10-04)' },
      { label: 'Daily News, “REA to install electricity infrastructure in remaining villages” (24 Nov 2023)',
        url: 'https://dailynews.co.tz/rea-to-install-electricity-infrastructure-in-remaining-villages/',
        supports: 'REA Director of Rural Electrification Eng. Jones Olotu: "out of 12,318 villages, a total of 11,313 villages have been connected" (page read 2026-10-04)' },
      { label: 'World Bank WDI, Terrestrial protected areas (% of land area), from UNEP-WCMC WDPA',
        url: 'https://data.worldbank.org/indicator/ER.LND.PTLD.ZS?locations=TZ',
        supports: 'Tanzania 2025: 39.9% (API, last updated 2026-07-13; read 2026-10-04)' },
    ],
    // Camera and sweep set by hand for display (approximate mainland coast ~40.4 E, Lake Tanganyika ~29.3 E).
    camera: { lat: -6.3, lng: 34.9, altitude: 0.35 },
    fly: 3000,
    sweep: { east: 40.4, west: 29.3, hold: 800, duration: 3500 },
  },
  // ── Parked at the end (human, 2026-10-04, Firefly narrative round 1: "firefly and Mice part both move to the end of
  // all tabs, that may be removed later until everything's built up"). Listed under Explore (part 3) so the step list
  // order matches the story order. The fireflies chapter moved into "Female response" (AI_LOG Firefly tabs round 5a).
  // ── Spectral chapters (human: fireflies F-A + F-C, mice M-B, after "Light type"; Linda's look, two chapters,
  // beats loop automatically, perception layer; AI_LOG Impacts steps 74–78). All titles, texts and number labels
  // are DRAFT placeholders by the agent until the human writes them.
  // `spectral.beats` loop every `every` ms; each beat shows one documented number. Fireflies: `lamp` = the lamp lit
  // (with its firefly-weighted layer), `reply` = documented female reply share driving the dialogue animation,
  // `brighter` = the lamp grows ×10 (dim → bright photons). Mice: `show` = lux | melanopic | activity | clock.
  // Curves: data/derived/impacts/spectra_299.json, perception_299.json, spectra_278.json (inferred).
  {
    id: 'mice',
    part: 3,
    label: '[DRAFT] Mice',
    title: '[DRAFT] Mice: two night lights at 10 lux',
    text: '[DRAFT] Study 278: mice under dim light at night from a blue-rich or a long-wavelength lamp. ' +
      'Blue line: the peak of melanopsin. Dials: one day for each lamp (outer blue-rich, inner long-wavelength); ' +
      'moving points = activity at night.',
    sources: [
      { label: 'Wang et al. 2023, S. Fig. 1 and Methods', url: 'https://doi.org/10.1016/j.nbd.2022.105944',
        supports: 'two LED spectra; 10.0 lx (short-λ) and 10.4 lx (long-λ); melanopic EDI 15 vs 1 mel lx; melanopsin peak ≈480 nm (Hattar 2002; Panda 2005); 12:12 light:dark, ZT 0 = lights on' },
      { label: 'Wang et al. 2023, sec. 3.1, Fig. 1', url: 'https://doi.org/10.1016/j.nbd.2022.105944',
        supports: 'activity suppressed 51 ± 5 % vs 14 ± 7 % (1 h at ZT 14); phase delay −117 ± 6 vs −26 ± 4 min (15 min at CT 16); all 10 lx' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // Dial look after Linda's body-clock scene (human decision, AI_LOG Push task step 5). Lamp beats zoom to
    // the night quarter; the clock test gets its own constant-darkness dial (human: option 2, Push task step 8).
    spectral: { chapter: 'mice', every: 4500, beats: [
      { show: 'lux', value: '10 lx · 10 lx', label: 'same measured brightness · blue-rich · long-wavelength' },
      { lamp: 'short', supp: 0.51, view: 'night', value: '−51 %', colours: ['short'],
        label: 'night activity during 1 h of blue-rich light · 15 melanopic lux' },
      { lamp: 'long', supp: 0.14, view: 'night', value: '−14 %', colours: ['long'],
        label: 'night activity during 1 h of long-wavelength light · 1 melanopic lux' },
      { show: 'dark', view: 'dial', value: '15 min',
        label: '[DRAFT] 10 lx pulse at CT 16, 4 h after activity onset, in constant darkness' },
      { show: 'clock', view: 'dial', minutes: [117, 26], value: '117 vs 26 min', colours: ['short', 'long'],
        label: 'later start of the active night after a 15 min pulse of light' },
    ] },
  },
  {
    id: 'cote-divoire',
    part: 1,
    title: 'Côte d’Ivoire',
    // Retired (human, Light story refinement 2026-10-04: "retire ivory coast yes"); replaced by Tanzania.
    // Human request (AI_LOG Story step 41): Côte d'Ivoire replaces France; Ukraine removed (both in `retired`).
    // Version check: +116..+247% under every variant (03/04 scripts, country_screen_2015_2025.csv).
    figure: 'ALAN increased by 227%',   // radiance change 2015–2025: +226.56%, Côte d'Ivoire (02_country_change.py)
    figureNote: '2015–2025, total radiance measured by VIIRS; our calculation (provisional, audit pending).',
    // DRAFT (agent, 2026-10-03): same pattern as the India card; the fact is sourced, the link to the
    // change in lights is the humans' framing.
    text: 'Lights spread as villages were connected to the grid: under the national rural electrification ' +
      'programme (PRONER), 4,803 rural localities were electrified between 2017 and 2024.',
    sources: [
      { label: 'Ministère des Mines, du Pétrole et de l’Energie, “Electricité” (economie-ivoirienne.ci, 26 Nov 2025)',
        url: 'https://economie-ivoirienne.ci/activites-sectorielles/electricite.html',
        supports: '"la poursuite du PRONER a permis l\'électrification de 4 803 localités rurales de 2017 à 2024"; ' +
          'electrified localities 3,887 (2017) -> 8,035 (2024, RGPH 2014 base); coverage 45.63% -> 94.3% (page read 2026-10-03)' },
    ],
    camera: { lat: 7.6, lng: -5.5, altitude: 0.2 },
    fly: 3000,
    sweep: { east: -2.4, west: -8.7, hold: 800, duration: 3500 },
  },
  // Species groups: retired (human, Firefly transition task step 4: "it's not telling any story").
  // Species groups (human: option D, AI_LOG Impacts steps 54–55). Title and text are DRAFT placeholders
  // until the human writes the question.
  {
    id: 'species',
    part: 2,
    label: 'Species groups',
    title: '[DRAFT] Species groups',
    text: '[DRAFT] The same effects, sorted by the group of the species studied. White line = the median study: ' +
      'each study’s middle effect, then the middle of those.',
    sources: [
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'Phylum and Class of each effect record, grouped into 9 species groups by us (pipeline/impacts/maps/species_groups.csv); median of study medians computed by us from |g|' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    impacts: { view: 'chart', records: true, filter: true, group: 'species', example: '005-2', exampleLabel: 'Black swans, night-time rest' },
  },
  {
    id: 'france',
    part: 1,
    title: 'France',
    // Human request (AI_LOG step 39): France back in place of Iceland (Iceland's +106% depends on the
    // EOG version mask; France stays -38..-48% under every variant of 03_version_sensitivity.py).
    figure: 'ALAN decreased by 41%',   // radiance change 2015–2025: −41.06%, France (mainland incl. Corsica)
    figureNote: '2015–2025, total radiance measured by VIIRS; our calculation (provisional, audit pending).',
    text: 'Lights dimmed under a national rule of December 2018: shop windows, building facades ' +
      'and heritage lighting must be switched off by 1 a.m.',
    // LED caveat on this card: human request, AI_LOG step 15 (wording agent-drafted).
    note: 'Part of a measured decrease can come from switching to white LEDs: VIIRS cannot see ' +
      'blue light below about 500 nm, where white LEDs emit strongly (Kyba et al. 2023).',
    sources: [
      { label: 'Arrêté du 27 décembre 2018 (Légifrance)',
        url: 'https://www.legifrance.gouv.fr/loda/id/JORFTEXT000037864346',
        supports: 'Art. 2: heritage/park lighting off by 1 a.m.; shop windows off by 1 a.m. or 1 h after ' +
          'activity ends; JO 28 Dec 2018' },
      { label: 'Kyba et al. 2023, Science 379:265', url: 'https://doi.org/10.1126/science.abq7781',
        supports: 'note: satellites recording global radiance are insensitive to wavelengths < 500 nm ' +
          'emitted by white LEDs (as reported in summaries of the paper; paper text not yet read by the agent)' },
    ],
    camera: { lat: 46.5, lng: 2.5, altitude: 0.22 },
    fly: 3000,
    sweep: { east: 8.2, west: -4.8, hold: 800, duration: 3500 },
  },
  {
    id: 'ukraine',
    part: 1,
    title: 'Ukraine',
    figure: 'ALAN decreased by 32%',   // radiance change 2015–2025: −32.10%, Ukraine excl. Crimea
    figureNote: '2015–2025, total radiance measured by VIIRS; our calculation (provisional, audit pending).',
    text: 'Lights went out in war: after Russia invaded in 2022, power plants and other infrastructure ' +
      'were damaged, cutting electricity to millions, and some outdoor lighting was dimmed or switched off.',
    sources: [
      { label: 'NASA Earth Observatory, "Tracking Night Lights in Ukraine", 30 Jun 2022',
        url: 'https://science.nasa.gov/earth/earth-observatory/tracking-night-lights-in-ukraine-150002',
        supports: 'infrastructure damaged in the early weeks of the war, cutting electricity to millions; ' +
          'some outdoor lighting may have been dimmed, removed or shut off' },
    ],
    camera: { lat: 49, lng: 31.5, altitude: 0.25 },
    fly: 3000,
    sweep: { east: 40.2, west: 22.1, hold: 800, duration: 3500 },
  },
  {
    id: 'iceland',
    part: 1,
    title: 'Iceland',
    // Human request (AI_LOG step 36): Iceland replaced France; retired again in step 39 (see above).
    figure: 'ALAN increased by 106%',   // radiance change 2015–2025: +105.54%, Iceland (02_country_change.py)
    figureNote: '2015–2025, total radiance measured by VIIRS; our calculation (provisional, audit pending).',
    // DRAFT (agent, 2026-10-03): states the visitor numbers side by side; no cause is claimed.
    text: 'Over the same years, tourism boomed: foreign visitors arriving through Keflavík airport rose from ' +
      'about 1.3 million in 2015 to about 2.3 million in 2025.',
    sources: [
      { label: 'Icelandic Tourist Board, 10 Jan 2017', url: 'https://www.ferdamalastofa.is/en/news/number-of-visitors-smashes-all-earlier-records',
        supports: '"approximately 1.77m in 2016, or 40% more than in 2015" -> 2015 ≈ 1.26 m (inferred: 1.77 / 1.4)' },
      { label: 'Icelandic Tourist Board, numbers of foreign visitors', url: 'https://www.ferdamalastofa.is/en/recearch-and-statistics/numbers-of-foreign-visitors',
        supports: '2025: "Around 2.27 million came on flights through Keflavík International Airport" (page read 2026-10-03)' },
    ],
    camera: { lat: 64.9, lng: -18.6, altitude: 0.22 },
    fly: 3000,
    sweep: { east: -13.5, west: -24.5, hold: 800, duration: 3500 },
  },
  // Black swans, One effect (worked example 005-2) and Fireflies (Taipei, Owens et al. 2018): retired (human, AI_LOG
  // Impacts reorder step 2: "retire the one effect", "retire black swans", "We aren't doing the taipei step anymore").
  {
    id: 'swans',
    part: 2,
    label: 'Black swans',
    title: 'Black swans · Serendip Sanctuary, Australia',
    // Workbook study 005, "nighttime rest (h)": dark 3.43 h, amber LED (0.36 lx) 2.76 h.
    text: 'Swans kept outdoors were lit at night by dim amber streetlights, a colour chosen to reduce blue light. ' +
      'Their night-time rest fell from 3.4 to 2.8 hours, and brain recordings showed that resting swans were almost always asleep.',
    sources: [
      { label: 'Aulsebrook et al. 2020, Front. Ecol. Evol.', url: 'https://doi.org/10.3389/fevo.2020.00131',
        supports: 'abstract (publisher page): rest decreased under amber lights vs dark; resting birds almost always asleep. Numbers: Data S1 row 005-2' },
    ],
    camera: { lat: -38.0, lng: 144.41, altitude: 0.35 },
    fly: 3500,
    swipe: 0,
    impacts: { view: 'globe', study: '005' },
  },
  {
    id: 'one-effect',
    part: 2,
    label: 'One effect',
    title: 'What is an effect?',
    text: 'Each study compared two groups: one kept dark, one lit at night. One such comparison is one *effect*. ' +
      'To compare hours of sleep with hormone levels or insect counts, the difference is divided by the normal ' +
      'spread between individuals. That number is Hedges *g*: about 0.2 is a small effect, 0.5 medium, 0.8 large.',
    sources: [
      { label: 'Czarnecka et al. 2025, sec. 2.5', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'effect sizes computed as standardised mean difference (Hedges g) between control and treatment' },
      { label: 'Cohen 1988, Statistical Power Analysis for the Behavioral Sciences', url: 'https://doi.org/10.4324/9780203771587',
        supports: '0.2 / 0.5 / 0.8 = small / medium / large conventions (human decision B)' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    fly: 2500,
    swipe: 0,
    impacts: { view: 'chart', example: '005-2', exampleLabel: 'Black swans, night-time rest' },
  },
  // ── Firefly section skeleton (human, 2026-10-04, AI_LOG "Firefly narrative" round 1): tab names are the agent's
  // proposal accepted by the human "for now". Each tab is a [PLACEHOLDER] until it is built; text says only what will go there.
  // Order (human): signal production (Owens 2018) → female response (Owens & Lewis 2021) → mate-finding (Kivelä 2023)
  // → synthesis → local firefly (Photinus pyralis) → Philadelphia vs Cherry Springs measured spectra.
  // Fireflies (human, AI_LOG Firefly tabs review round 6b): shown like Black swans, the globe turns to the study.
  // Owens et al. 2018 is not in Data S1, so its point is drawn on its own: the collection site printed in the paper
  // (owens2018_results.json statements.collection_site, documented; camera below = the same printed coordinates).
  // Moving on to Signal production the globe zooms in and the point becomes a yellow-green glow that turns into
  // the scene's two males (human: "point becomes the scene"; main.js, impacts.js `site`, spectral.js).
  // Card text: agent draft on the human's request (round 6b), from owens2018_results.json statements.
  {
    id: 'fireflies',
    part: 2,
    label: 'Fireflies',   // 'Fireflies' → 'Fireflies-step 1' (round 6e) → 'Fireflies' again (human, AI_LOG round 7b)
    title: 'Fireflies · Yongjian Eco Park, Taipei, Taiwan',
    text: '[DRAFT] Male *Aquatica ficta* fireflies were collected here, at Yongjian Eco Park, on 4, 7 and 11 May 2016. ' +
      'Their courtship signal is a single yellow-green flash, peaking at 565 nm. Eight males were recorded on the ' +
      'evenings of 5–9 and 12–14 May.',
    note: 'The point marks where the males were collected (coordinates as printed in the paper). The paper gives no ' +
      'coordinates for where they were tested.',
    sources: [
      { label: 'Owens et al. 2018, PLoS ONE, Methods', url: 'https://doi.org/10.1371/journal.pone.0191576',
        supports: 'p. 3: collected from Yongjian Eco Park (24.990195, 121.555824; May 4, May 7, and May 11, 2016); periodic single yellow-green courtship flashes, peak wavelength 565 nm. p. 4: eight males, evenings of May 5–9 and May 12–14, 2016' },
    ],
    camera: { lat: 24.990195, lng: 121.555824, altitude: 0.35 },
    fly: 3500,
    swipe: 0,
    impacts: { view: 'globe', site: 'owens2018' },
  },
];
