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
//
// DRAFT NOTICE: the case-study and caveat sentences below were drafted by an AI agent
// (claude-opus-5-5, 2026-10-03) at the human's request as prototype placeholders.
// Each cites one source for its factual part. The link between the fact and the change in
// lights is the humans' framing; neither the source nor our data shows that cause.

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
    kind: 'fact',              // large text on the left of the globe instead of a card
    // Values from pipeline/story/01_radiance_change.py -> data/derived/story/radiance_change_2015_2025.json
    // (label: inferred; lit = > 0, sphere areas, pairwise -1.5 exclusion): radiance +40.99% vs 2015.
    // Lit area (+25.28%) removed by the human (AI_LOG step 39): it ranges +25..+83% depending on the
    // threshold (EOG version difference, 03_version_sensitivity.py). PROVISIONAL: not yet audited (RULES section 3).
    // Wording: human's (AI_LOG step 11: say "ALAN", radiance moved to the footnote).
    text: 'Artificial Light at Night (ALAN) increased by 41% between 2015 and 2025.',  // wording: human, 2026-10-04
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
    // No camera move and no sweep (human, AI_LOG Story step 41: the India/China pan made India feel
    // shown twice). Camera = the intro view, so the globe stays where the intro left it.
    // Was: camera { lat: 25, lng: 72, altitude: 1.6 }, fly 2500, sweep east 122 -> west 68.1.
    camera: { lat: 20, lng: 10, altitude: 2.2 },
  },
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
  // ── Part 2: light impacts ─────────────────────────────────────────────────
  // Sequence: human (AI_LOG Impacts steps 26–27). The question is the human's wording.
  // DRAFT NOTICE: all other Part 2 text (cards, chart labels in app/src/impacts.js) was drafted by an
  // AI agent (claude-opus-5-5, 2026-10-03) at the human's request as placeholders. Featured studies
  // (165, 005) and the worked example (005-2) were proposed by the agent, refinable.
  // impacts: stage of the Impacts layer (see setStage in app/src/impacts.js).
  {
    id: 'question',
    part: 2,
    kind: 'fact',
    label: 'Ecosystems',
    text: 'But how does light impact our ecosystems?',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    fly: 3000,
    swipe: 0,
    impacts: { view: 'globe', dots: false },
  },
  {
    id: 'studies',
    part: 2,
    label: 'Studies',
    text: 'Each dot is one study that compared living things under artificial light at night with the same ' +
      'under natural darkness. These are 207 of the 314 studies gathered in a 2025 meta-analysis: ' +
      'the ones we could place on the map. Colour = the study’s main category.',
    sources: [
      { label: 'Czarnecka et al. 2025, Global Change Biology', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'sec. 2.1: 314 studies, 4,905 effect sizes; control group under dark night conditions vs light up to 180 lx' },
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'study records; locations geocoded by us (02_geocode.py)' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    impacts: { view: 'globe', reveal: true },
  },
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
  {
    id: 'effects',
    part: 2,
    label: 'All effects',
    title: '3,254 effects',
    text: 'The 207 studies on the globe measured 3,254 effects. Each dot is one, in the lane of what was measured. ' +
      'Further right = a bigger change under light. Only the size of the change is shown, not its direction: ' +
      'for some measures more is harmful, for others less. White line = the median study: each study’s middle ' +
      'effect, then the middle of those.',
    sources: [
      { label: 'Czarnecka et al. 2025, sec. 2.5', url: 'https://doi.org/10.1111/gcb.70569',
        supports: 'absolute values |g| used for magnitude because opposite effects within a category could cancel out' },
      { label: 'Data S1, Dryad (CC0)', url: 'https://doi.org/10.5061/dryad.xwdbrv1q0',
        supports: 'category and |g| of each effect record; median of study medians computed by us from |g|' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    impacts: { view: 'chart', records: true, filter: true, example: '005-2', exampleLabel: 'Black swans, night-time rest' },
  },
  // The next two questions and their one-word answers ("Yes", "Not as much as thought") are the human's
  // (AI_LOG Impacts steps 29, 35–36); the rest of each text is a DRAFT placeholder by the agent.
  {
    id: 'intensity',
    part: 2,
    label: 'Light level',
    title: 'Does light intensity affect biota?',
    text: 'Yes. [DRAFT] The same effects, now sorted by how bright the light was. Effects appear at every level, ' +
      'even below 5 lux. The meta-analysis found them mostly not dose-dependent: low light had an impact ' +
      'comparable to moderate and high light. White line = the median study: each study’s middle effect, then the middle of those.',
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
    impacts: { view: 'chart', records: true, filter: true, group: 'band', example: '005-2', exampleLabel: 'Black swans, night-time rest' },
  },
  {
    id: 'light-type',
    part: 2,
    label: 'Light type',
    title: 'Does light temperature affect biota?',
    text: 'Not as much as thought. [DRAFT] The same effects, sorted by type of light. Warm white light ' +
      '(below 3000 K) had an impact similar to cool white light, contrary to the common view that warm light is ' +
      'gentler. White light that also emits ultraviolet had the strongest impact. The narrow-spectrum lanes rest ' +
      'on few studies, so read them with caution.',
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
    impacts: { view: 'chart', records: true, filter: true, group: 'type', example: '005-2', exampleLabel: 'Black swans, night-time rest' },
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
    label: 'Fireflies-step 1',   // renamed from 'Fireflies' (human, AI_LOG Firefly tabs review round 6e)
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
  {
    id: 'signal-production',
    part: 2,
    label: 'Signal production',
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
    id: 'female-response',
    part: 2,
    label: 'Female response',
    title: 'Female response',
    // The former '[DRAFT] Fireflies' chapter (study 299), moved here from Explore (human, AI_LOG Firefly tabs round 5a);
    // its door from Light type removed (round 5b). Card text: agent draft on the human's request (round 5g), values as in
    // the sources below.
    text: '[DRAFT] Courting *Photinus obscurellus* fireflies: a male flashes, a female answers. In the dark 98.7 % of ' +
      'females answered; under bright cool white 10.3 %, dim warm white 11.6 %, dim blue 36.1 %, dim red 48.6 % and ' +
      'bright amber 0 %. Each lamp in turn, with the part of its light a firefly eye takes in (green).',
    sources: [
      { label: 'Owens & Lewis 2021, Fig. 1 and Methods', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'five LED spectra, area (photons) standardised; P. scintillans sensitivity (Lall et al. 1988); flash peak 567.47 nm (Hall et al. 2016); dim 2.079 × 10^19, bright 2.079 × 10^20 photons cm⁻² s⁻¹' },
      { label: 'Owens & Lewis 2021, Results', url: 'https://doi.org/10.1111/icad.12487',
        supports: 'female response: dark 98.7 %, bright cool white 10.3 %, dim warm white 11.6 %, dim blue 36.1 %, dim red 48.6 %, bright amber 0 %. The other five colour × intensity values are only in Fig. 2b (not shown)' },
    ],
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // manual: no auto-advance; a toggle (top right) and ← → step through the beats (human, Firefly transition task step 3).
    spectral: { chapter: 'fireflies', manual: true, beats: [
      { value: '98.7 %', label: 'females answer · dark', reply: 0.987 },
      { lamp: 'cool_white', value: '10.3 %', label: 'females answer · bright cool white', reply: 0.103 },
      { lamp: 'warm_white', value: '11.6 %', label: 'females answer · dim warm white', reply: 0.116 },
      { lamp: 'blue', value: '36.1 %', label: 'females answer · dim blue', reply: 0.361 },
      { lamp: 'red', value: '48.6 %', label: 'females answer · dim red', reply: 0.486 },
      { lamp: 'amber', brighter: true, value: '0 %', label: 'females answer · bright amber (10× photons)', reply: 0 },
    ] },
  },
  {
    id: 'mate-finding',
    part: 2,
    label: 'Mate-finding',
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
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // Continuous scene, third band (human, AI_LOG Firefly tabs round 5b). "Dark vs lit pair" (human, review round 6o):
    // control always on the left, the beat's treatment on the right, so no control beat (kivela2023.json).
    spectral: { chapter: 'glow', manual: true, beats: ['blue', 'white', 'yellow', 'red'].map(treatment => ({ treatment })) },
  },
  {
    id: 'communication',
    part: 2,
    label: 'One communication problem',
    title: 'One communication problem',
    text: '[PLACEHOLDER] Synthesis of the three studies.',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
  },
  {
    id: 'local-firefly',
    part: 2,
    label: 'Local firefly',
    title: 'Local firefly',
    text: '[PLACEHOLDER] *Photinus pyralis*, Philadelphia and Cherry Springs.',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
  },
  {
    id: 'two-nights',
    part: 2,
    label: 'Two measured nights',
    title: 'Two measured nights',
    text: '[PLACEHOLDER] Measured night spectra, Philadelphia and Cherry Springs.',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    // 3D night spectra, Philadelphia | Cherry Springs (app/src/twoNights.js; data/derived/spectra/, Spitschan et al.
    // 2016; human decisions: handoff 2026-10-04_two-nights-spectra.md, AI_LOG Firefly narrative round 3c).
    nights: true,
  },
  // Broader Impacts (human request, Firefly transition task step 4): filler screen with the human's question;
  // charts, data and sources on ecosystem-level impacts may follow here (not started).
  {
    id: 'broader',
    part: 2,
    kind: 'fact',
    label: 'Broader Impacts',
    text: 'So how does this translate to ecosystem level impacts?',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    fly: 2500,
    swipe: 0,
    impacts: { view: 'globe', dots: false },
  },
  // Conclusion (human request, step 4): dark screen (dark: true fades the globe out, main.js); call to action is a
  // DRAFT in the human's suggested wording.
  {
    id: 'conclusion',
    part: 2,
    kind: 'fact',
    label: 'Conclusion',
    text: '[DRAFT] We need light at night, but do we need it all the time, everywhere?',
    camera: { lat: 20, lng: 10, altitude: 2.2 },
    swipe: 0,
    dark: true,
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
];

// Steps taken out of the story by the humans, kept here so their sourced text is not lost.
// Iceland: retired (human, AI_LOG step 39, option 3): its +106% comes mostly from pixels that are 0 in 2015
// (EOG v2.1) and faintly lit in 2025 (v2.2); on pixels lit in both years it is -17%
// (data/derived/story/version_sensitivity_2015_2025.json).
// France and Ukraine: retired (human, AI_LOG Story step 41: "replace France with Cote d'ivoire and then
// remove Ukraine. Just two countries").
export const retired = [
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
];
