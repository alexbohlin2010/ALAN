// Impacts: study locations drawn on a 2D canvas over the globe, projected from the globe (R3,
// after Linda's globe_v2/layers/c1-effects.js). Studies whose dots fall within CLUSTER_PX of each
// other on screen are drawn as a Linda-style halo (faint ring, the studies' dots slightly offset
// inside it); clicking it fans the studies out around it (lines back to the spot). The card steps
// through all drawn studies west → east (‹ ›, ← →). Human decisions: AI_LOG Impacts steps 10, 15,
// 18 (rings dropped; expand on click; prev/next), 20 (colour = the source's own Category) and 22
// (solid dots in the study's dominant category, studies.json `dominant_category`; option 2 colours;
// halo clusters).
// Data: /impacts/ = data/derived/impacts, /impacts/maps/ = approved pipeline/impacts/maps (vite.config.js).
import { nmCss } from './spectral.js';

// Source Category (Data S1 "Category " column, documented) → colour. Display choice, not data.
// Palette C "deep heraldic" (agent proposal, chosen by the human 2026-10-04, AI_LOG colour / design task
// step 3); replaces Linda's globe_v2 colours + the step 22 picks (was Behaviour #2fb84a, Physiology #8bb8ff,
// LHT #d99cff, Population #7ce6cf, Community #3d7bff).
const CATEGORY_COLORS = new Map([['Behaviour', '#18b86b'], ['Physiology', '#2f5bff'], ['LHT', '#8a3dff'],
  ['Population', '#e0306b'], ['Community', '#14a8c4']]);
// Species group (effects.json `species_group`, inferred from Phylum + Class via the approved
// pipeline/impacts/maps/species_groups.csv) → colour. Display choice, not data. Heraldic set to match the
// category palette (human 2026-10-04: "also change species colors"; hues = agent draft, AI_LOG colour / design
// task step 3; smallest normal-vision difference between any two = 12.8, OKLab ×100; several pairs merge for
// colour-blind readers). Was: AI_LOG Impacts steps 54–55 (#a76c12 #3375e3 #51bfee #a276c2 #f0a7e9 #c8b222
// #f3669a #36a558 #5ce483). Toggle "Colour: Species group | Effect category"; default = effect
// category since step 63 (human: species colours are there for whoever wants to look into them). Order = the
// human's lane order.
const SPECIES_COLORS = new Map([['Mammals', '#d0344f'], ['Birds', '#2f5bff'], ['Fish', '#14b0d0'],
  ['Amphibians', '#8a3dff'], ['Reptiles', '#c45ae6'], ['Insects', '#c4c41e'],
  ['Arthropods and other invertebrates', '#ff6aa0'], ['Plants', '#18a85e'], ['Algae, fungi & microbes', '#62e6a8']]);
const HALO = 12;                    // cluster ring radius (px), as Linda's country-level ring
const OTHER = '#888888';             // any category not in the list above (none on 2026-10-03)
const DOT = 5, DOT_SELECTED = 7;     // single study dot radius (px)
const CLUSTER_PX = 14;               // screen distance under which dots are merged into one cluster
const FAN_GAP = 18;                  // spacing between fanned-out dots (px)

// Effects chart (story Part 2; AI_LOG Impacts steps 25–29). One dot per effect record
// (data/derived/impacts/effects.json, 04_effects.py), in its source-Category lane, at x = |Hedges g|.
// Scale and 10+ cap: Linda's (log1p). Tick words: Cohen 1988 conventions (human decision B).
// Worked example (human decision A): one record's dark vs lit means become one dot.
const CAP = 10;
const LANES = [...CATEGORY_COLORS.keys()];
const LANE_LABEL = { LHT: 'Life history (LHT)' };
// Other groupings of the same records (human decision, AI_LOG Impacts step 36: option A = re-sorted lanes,
// dots keep their category colour and slide to the new lane; ii = median mark per lane, per study since step 39).
// Bands: article sec. 2.2 (low ≤ 5 lx, moderate 5–20, high > 20). Light types: source order; names shortened
// from the approved plain words (pipeline/impacts/maps/light_types.csv), group = broad / narrow spectrum.
const GROUPS = {
  category: { key: e => e.category, lanes: LANES },
  band: { key: e => e.night_lux_band, lanes: ['low', 'moderate', 'high'],
    name: { low: ['Low light', '≤ 5 lux'], moderate: ['Moderate light', '5–20 lux'], high: ['High light', '> 20 lux'] } },
  type: { key: e => e.light_type_code, lanes: ['BS warm', 'BS cool', 'BS_UV', 'NS yellow-red', 'NS blue', 'NS green'],
    name: { 'BS warm': ['Warm white'], 'BS cool': ['Cool white'], BS_UV: ['With ultraviolet'],
      'NS yellow-red': ['Yellow to red'], 'NS blue': ['Blue'], 'NS green': ['Green'] },
    header: { 'BS warm': 'BROAD-SPECTRUM', 'NS yellow-red': 'NARROW-SPECTRUM' } },
  // Species groups (human: option D, AI_LOG Impacts steps 54–55); long names split over two lines.
  species: { key: e => e.species_group, lanes: [...SPECIES_COLORS.keys()],
    name: Object.fromEntries([...SPECIES_COLORS.keys()].map(k => [k,
      { 'Arthropods and other invertebrates': ['Arthropods and', 'other invertebrates'],
        'Algae, fungi & microbes': ['Algae, fungi', '& microbes'] }[k] ?? [k]])) },
};
const REGROUP_MS = 1400;
const TICKS = [[0, '0'], [0.2, '0.2', 'small'], [0.5, '0.5', 'medium'], [0.8, '0.8', 'large'], [2, '2'], [5, '5'], [10, '10+']];
const MORPH_MS = 1800, FADE_MS = 700, REVEAL_MS = 1600, EXAMPLE_MS = 1300;
const REC_HIT = 5;   // click radius of an effect dot, px (agent choice)
// Study sites outside Data S1 (story key `impacts.site`; human, AI_LOG Firefly tabs review round 6b): the point is read
// from the study's own derived file. Glow = the point turning into the courtship-flash colour while the globe zooms in
// towards Signal production (timings and sizes: agent choices).
const SITE_FILES = { owens2018: 'owens2018_results.json' };
// Sites typed from a paper's printed text (documented; source also in the story step's `sources`).
// spitschan2016_city: Spitschan, Aguirre, Brainard & Sweeney 2016, Sci. Rep. 6: 26756, Methods "Locations": City =
// roof of David Rittenhouse Laboratories, University of Pennsylvania, Philadelphia, 39.952237° N, 75.188734° W (printed
// "−75.188734° W"). The same site as the Philadelphia spectra in Two measured nights; not a firefly record (human,
// AI_LOG Firefly tabs review round 7d). Colour (human, round 7f): P. pyralis in vivo flash peak 562 nm (Seliger, Buck,
// Fastie & McElroy 1964, J. Gen. Physiol. 48: 95–104, Table I, "Present work, 1963": 5620 Å; read in the Europe PMC
// OCR full text of PMC2195396), nm → RGB as in spectral.js.
// spitschan2016_rural: same paper, Rural = Cherry Springs State Park, 41.6646° N, 77.8125° W (printed "−77.8125° W"),
// the Cherry Springs spectra in Two measured nights; shown only in the Local firefly ↔ Two measured nights transition
// (human, round 7f). Colour white: agent choice (no firefly colour for a site without a firefly source).
// owenslewis2021_boston: Owens & Lewis 2021, Insect Conserv. Divers. 14: 199–210, Methods: 2018 fireflies collected at
// Muster Field, Lincoln, MA and the Arnold Arboretum, Boston, MA (42.30469, −71.12099, as printed); Boston only (human,
// AI_LOG Impacts reorder step 4). Colour: P. obscurellus flash peak 567.47 nm (Hall et al. 2016, as cited in the paper).
const SITE_POINTS = {
  owenslewis2021_boston: { lat: 42.30469, lon: -71.12099, colour: nmCss(567.47), label: 'Owens & Lewis 2021 · collection site' },
  spitschan2016_city: { lat: 39.952237, lon: -75.188734, colour: nmCss(562), label: 'Spitschan et al. 2016 · city measurement site' },
  spitschan2016_rural: { lat: 41.6646, lon: -77.8125, colour: '#ffffff', label: 'Spitschan et al. 2016 · rural measurement site' },
};
const GLOW_IN_MS = 2200, GLOW_OUT_MS = 1800;
const clamp01 = v => Math.max(0, Math.min(1, v));
const easeInOut = t => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const median = xs => {
  if (!xs.length) return null;
  const g = [...xs].sort((a, b) => a - b), m = g.length >> 1;
  return g.length % 2 ? g[m] : (g[m - 1] + g[m]) / 2;
};
const fmt = (v, d = 2) => Number(v).toFixed(d).replace(/\.?0+$/, '');

const esc = v => String(v ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c]);

// Minimal CSV parser (quoted fields, "" escapes); enough for the approved map files.
function parseCsv(text) {
  const rows = [];
  let row = [], field = '', quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i += 1;
      row.push(field); rows.push(row); row = []; field = '';
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [head, ...body] = rows.filter(r => r.length > 1 || r[0]);
  return body.map(r => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}

const getJson = async url => { const r = await fetch(url); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); };
const getText = async url => { const r = await fetch(url); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.text(); };

const range = (lo, hi) => lo == null ? null : lo === hi ? `${lo}` : `${lo}–${hi}`;

// Offsets for n fanned-out dots: a ring for small n, a sunflower spiral for large n.
function fan(n) {
  if (n <= 12) {
    const r = Math.max(26, (n * FAN_GAP) / (2 * Math.PI));
    return Array.from({ length: n }, (_, i) => {
      const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
      return { dx: Math.cos(a) * r, dy: Math.sin(a) * r };
    });
  }
  return Array.from({ length: n }, (_, i) => {
    const r = 22 + FAN_GAP * 0.55 * Math.sqrt(i + 0.5) * 1.6, a = i * 2.399963229728653;
    return { dx: Math.cos(a) * r, dy: Math.sin(a) * r };
  });
}

export function createImpacts({ globe, globeEl, card, legend, onDoor }) {
  const canvas = document.createElement('canvas');
  canvas.id = 'impacts-canvas';
  globeEl.after(canvas);
  const ctx = canvas.getContext('2d');

  let places = [], order = [], studies = new Map(), points = new Map(), lightWords = new Map();
  let loaded = null, shown = false, frame = 0, selected = null, expanded = null, hits = [];
  // browse = free exploring in Impacts mode (clicks, card, ← →); off while the story drives the view.
  let browse = true, stage = null, effects = [], filter = null, lastExample = null;
  let effectsById = new Map(), laneCount = new Map();
  // Per study: median |g| of all its records and their count (card line, human choice a, AI_LOG Impacts step 40).
  const studyEffect = new Map();
  // Per study: its species groups, most records first (ties: first in the source table); [0] colours its globe dot.
  const studyGroups = new Map();
  // Dot colours: 'category' (default, step 63) | 'species'; set by the toggle, kept across steps.
  let colourBy = 'category';
  const recColor = e => (colourBy === 'species' ? SPECIES_COLORS.get(e.species_group) : CATEGORY_COLORS.get(e.category)) ?? OTHER;
  // Animated values: { from, to, t0, ms } read with val(); time-based so frame rate does not matter.
  const anim = (v = 0) => ({ from: v, to: v, t0: 0, ms: 1 });
  const val = a => a.from + (a.to - a.from) * easeInOut(clamp01((performance.now() - a.t0) / a.ms));
  const go = (a, to, ms) => { if (a.to === to) return; a.from = val(a); a.to = to; a.t0 = performance.now(); a.ms = ms; };
  const dotsA = anim(1), chartA = anim(0), morphA = anim(0), exampleA = anim(0), groupA = anim(1), glowA = anim(0);
  // Story key `highlight: [{ set, label }, ...]` (ladder plan phase 2; AI_LOG "Story review" steps 7–8): study sets
  // from data/derived/impacts/study_highlights.json (10_study_highlights.py, inferred) lit one after another, the other
  // dots dimmed like filtered-out ones, with a count line at the top centre. A list of several plays as beats
  // (first HL_FIRST after the dots are in, then every HL_STEP); one set is shown at once. Timings: agent choices.
  const HL_FIRST = 2500, HL_STEP = 3500, HL_MS = 900, HL_DIM = 0.12;
  let hlSets = {}, hlLocated = 0, hlFrom = null, hlTo = null, hlTimers = [];
  const hlA = anim(1);
  // Study label fade (story `studyLabel.delay`, AI_LOG Impacts firefly-first step 3): in after `delay` ms, kept on while
  // the next stage shows the same study's label.
  const labelA = anim(0);
  let labelTimer = 0;
  const inSet = (h, id) => (!h ? 1 : hlSets[h.set]?.has(id) ? 1 : HL_DIM);
  const hlOf = id => { const t = val(hlA); return inSet(hlFrom, id) * (1 - t) + inSet(hlTo, id) * t; };
  function hlGo(h) {
    if ((h?.set ?? null) === (hlTo?.set ?? null)) { hlTo = h; return; }
    hlFrom = hlTo; hlTo = h;
    hlA.from = 0; hlA.to = 1; hlA.t0 = performance.now(); hlA.ms = HL_MS;
  }
  // Callout beats (story impacts.callouts; human, AI_LOG Effect dots and examples step 5): { list, k }, k = 0 the step's
  // own sentence, k = 1..n callout k − 1: its study selected and its dot marked. main.js drives k.
  // calloutA: 0 → 1 as the first callout comes in (the worked example's label and marker fade with it).
  // Its card, when opened, sits on the side away from its dot (human, AI_LOG Effect dots and examples step 6).
  // A callout selects its study (white rings) once the chart or circle has settled (pendingSel); it does not open the
  // card: the "Source" button under the quote does (openCallout) (human, AI_LOG Effect dots and examples step 9: "the
  // card is too much information"; was opened on each callout, step 5). calloutX = its dot's x, for the card's side.
  let callout = null, calloutCard = false, pendingSel = null, calloutX = null;
  const calloutA = anim(0);
  const calloutEffect = () => (callout?.k ? effectsById.get(callout.list[callout.k - 1]?.effect) : null);
  const calloutStudy = () => calloutEffect()?.study_id ?? null;
  function applyCallout() {
    const e = calloutEffect();
    go(calloutA, callout?.k ? 1 : 0, FADE_MS);
    if (calloutCard) { closeCard(); calloutCard = false; }
    if (selected && selected !== e?.study_id) selected = null;
    pendingSel = e ? e.study_id : null;
  }
  const openPending = (e, x) => { calloutX = x; if (pendingSel === e.study_id) { pendingSel = null; if (card.hidden) selected = e.study_id; } };
  function openCallout() {
    const id = calloutStudy();
    if (!id || pendingSel) return;
    openCard(id, calloutX); calloutCard = true;
  }
  const circleA = anim(0);   // Broader Impacts circle (stage.circle), 0 = records on their studies, 1 = in the circle
  const noteA = anim(0), circleKeyA = anim(0);   // reading keys (drawKey): chart, circle
  // Sites outside Data S1: key → { lat, lon, colour, label } (filled in load()). siteA: key → fade (stage.site may be
  // one key or a list, e.g. both Spitschan sites during the Two measured nights transition).
  const sites = {}, siteA = {};
  // Chart dots are always effects (one per record): the Dots: Effects | Studies toggle and the study-dot view (AI_LOG
  // Impacts step 60) were removed; every effect dot opens its study's card (human, AI_LOG Effect dots and examples step 2).
  // Worked example: the bars hold (no timer) until the story moves on to a step with all records; then they
  // collapse into the dot at once (human request, Firefly transition task step 4). collapseT0 = start of the collapse.
  let collapseT0 = Infinity, fromGroup = 'category', toGroup = 'category';
  // Per lane of each grouping (and per category filter): records, studies, median of study medians |g| (inferred from g_abs).
  const laneStats = new Map();

  const filterBar = document.createElement('div');
  filterBar.id = 'impacts-filter';
  filterBar.hidden = true;
  canvas.after(filterBar);
  filterBar.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    // The filter follows the colour toggle (human request, AI_LOG Impacts step 56), so a switch clears it.
    if (b.dataset.colour) { if (b.dataset.colour !== colourBy) filter = null; colourBy = b.dataset.colour; renderKey(); }
    else if (b.dataset.size !== undefined) sizeSel = b.dataset.size === sizeSel || !b.dataset.size ? null : b.dataset.size;
    else filter = b.dataset.cat === filter || !b.dataset.cat ? null : b.dataset.cat;
    renderFilter();
  });
  // The bar holds the colour toggle (chart steps and the globe while exploring) and, on chart steps with
  // filter: true, a filter by whatever colours the dots: species groups or categories (step 56).
  let barCats = false, barCircle = false;
  // Broader Impacts circle: highlight one effect size class (human request, AI_LOG Broader Impacts circle concept step 7;
  // button words = the human's). Classes = the chart's tick words, Cohen (1988): small ≥ 0.2, medium ≥ 0.5, large ≥ 0.8;
  // records below 0.2 are in none of them. "All" (default) = agent's addition.
  let sizeSel = null;
  // Grey range under each button (class ann; human, AI_LOG Fireflies step 29: C pick 5b), shown once the circle has
  // settled (style.css #impacts-filter.settled). The key (picks 1a 2a 4c) is drawn in the right column (drawKey).
  const SIZES = [['large', 'Large', '|g| ≥ 0.8', '≥ 0.8'], ['medium', 'Medium', '0.5 ≤ |g| < 0.8', '0.5–0.8'], ['small', 'Small', '0.2 ≤ |g| < 0.5', '0.2–0.5']];
  function renderFilter() {
    if (barCircle) {
      filterBar.innerHTML = `<button data-size="" aria-pressed="${!sizeSel}">All</button>` + SIZES.map(([k, l, tip, range]) =>
        `<button data-size="${k}" title="${tip}" aria-pressed="${sizeSel === k}">${l}<span class="ann range">${range}</span></button>`).join('');
      return;
    }
    const toggle = `<span style="color:#888;font:12px system-ui,sans-serif;align-self:center">Colour</span>` +
      [['species', 'Species group'], ['category', 'Effect category']].map(([k, l]) =>
        `<button data-colour="${k}" aria-pressed="${colourBy === k}">${l}</button>`).join('');
    filterBar.innerHTML = toggle + (!barCats ? '' : `<span style="width:12px"></span>` +
      `<button data-cat="" aria-pressed="${!filter}">All</button>` + [...keyColors()].map(([c, col]) =>
      `<button data-cat="${esc(c)}" aria-pressed="${filter === c}"><i style="background:${col}"></i>${esc(LANE_LABEL[c] ?? c)}</button>`).join(''));
  }
  const keyColors = () => (colourBy === 'species' ? SPECIES_COLORS : CATEGORY_COLORS);
  // Does a record pass the filter? Category and species-group names do not overlap, so one value serves both.
  const passes = e => !filter || e.category === filter || e.species_group === filter;
  // Colour key in the legend (Impacts mode), following the toggle.
  let keyEl = null;
  function renderKey() {
    if (!keyEl) return;
    keyEl.innerHTML = colourBy === 'species'
      ? `${[...SPECIES_COLORS].map(([c, col]) => `<span class="key-dot" style="background:${col}"></span>${esc(c)}`).join(' · ')}
        (species groups from the source's Phylum and Class columns, grouped by an approved map). Each dot takes the
        study's main group: the one with the most effect records (ties: the first in the source table); the card
        lists all of them. Use the Colour buttons to colour by study category instead.`
      : `${[...CATEGORY_COLORS].map(([c, col]) => `<span class="key-dot" style="background:${col}"></span>${c}`).join(' · ')}
        (study categories as given in the source; LHT = life history traits, per the dataset README). Each dot
        takes the study's main category: the one with the most effect records (ties: the first in the source
        table); the card lists all of them.`;
  }

  async function load() {
    const [locs, st, lt, ef, hl, ...siteData] = await Promise.all([
      getJson('/impacts/study_locations.json'), getJson('/impacts/studies.json'),
      getText('/impacts/maps/light_types.csv'), getJson('/impacts/effects.json'), getJson('/impacts/study_highlights.json'),
      ...Object.values(SITE_FILES).map(f => getJson(`/impacts/${f}`))]);
    // Owens 2018: collection site and courtship-flash peak as printed (statements, documented).
    Object.keys(SITE_FILES).forEach((k, i) => {
      const c = siteData[i].statements.collection_site, nm = siteData[i].statements.courtship_flash.peak_wavelength.value;
      sites[k] = { lat: c.latitude.value, lon: c.longitude.value, colour: nmCss(nm), label: 'Owens et al. 2018 · collection site' };
    });
    Object.assign(sites, SITE_POINTS);
    hlLocated = hl.meta.located_studies;
    for (const [k, v] of Object.entries(hl.sets)) hlSets[k] = new Set(v.study_ids);
    effects = ef.effects;
    effectsById = new Map(effects.map(e => [e.effect_id, e]));
    const gs = new Map();
    for (const e of effects) gs.set(e.study_id, [...(gs.get(e.study_id) ?? []), e.g_abs]);
    for (const [id, g] of gs) studyEffect.set(id, { median: median(g), n: g.length });
    const grp = new Map();   // effects are in source-table order, so Map insertion order breaks ties
    for (const e of effects) {
      if (!grp.has(e.study_id)) grp.set(e.study_id, new Map());
      const m = grp.get(e.study_id);
      m.set(e.species_group, (m.get(e.species_group) ?? 0) + 1);
    }
    for (const [id, m] of grp) studyGroups.set(id, [...m].sort((a, b) => b[1] - a[1]).map(([g]) => g));
    for (const e of effects) laneCount.set(e.category, (laneCount.get(e.category) ?? 0) + 1);
    for (const [gname, gr] of Object.entries(GROUPS)) {
      for (const lane of gr.lanes) {
        for (const cat of ['', ...LANES, ...SPECIES_COLORS.keys()]) {   // per filter value (category or group)
          const rs = effects.filter(e => gr.key(e) === lane && (!cat || e.category === cat || e.species_group === cat));
          // Median per study (human request, AI_LOG Impacts step 39): each study's median |g| within the lane,
          // then the median of those, so a study with many records counts once.
          const byStudy = new Map();
          for (const e of rs) byStudy.set(e.study_id, [...(byStudy.get(e.study_id) ?? []), e.g_abs]);
          laneStats.set(`${gname}|${lane}|${cat}`, { records: rs.length, studies: byStudy.size,
            median: median([...byStudy.values()].map(median)) });
        }
      }
    }
    studies = new Map(st.studies.map(s => [s.study_id, s]));
    lightWords = new Map(parseCsv(lt).map(r => [r.code, r.plain_words]));
    // One place per distinct coordinate, holding the ids of the studies located there.
    const byCoord = new Map();
    for (const s of locs.studies) {
      points.set(s.study_id, s.points);
      for (const p of s.points) {
        const key = `${p.lat},${p.lon}`;
        if (!byCoord.has(key)) byCoord.set(key, { lat: p.lat, lng: p.lon, ids: [] });
        byCoord.get(key).ids.push(s.study_id);
      }
    }
    places = [...byCoord.values()];
    // Prev/next order: west → east by the study's first point, then by study id.
    order = locs.studies.map(s => s.study_id).sort((a, b) =>
      points.get(a)[0].lon - points.get(b)[0].lon || a.localeCompare(b));
    legend.insertAdjacentHTML('beforeend', `<div class="impacts-only">
      <p><span class="impacts-key"></span> A faint ring holds several studies close together (click to spread
      them out); dots inside it are offset slightly for display. Some dots mark only a country or region (e.g. "France"), not an exact site.</p>
      <p>Studies: Czarnecka et al. 2025, Data S1, Dryad doi:<a href="https://doi.org/10.5061/dryad.xwdbrv1q0"
      target="_blank" rel="noopener">10.5061/dryad.xwdbrv1q0</a> (CC0). Locations geocoded from the study's
      Location field. Geocoding data © <a href="https://www.openstreetmap.org/copyright" target="_blank"
      rel="noopener">OpenStreetMap contributors</a>, ODbL.</p></div>`);
    keyEl = legend.querySelector('.impacts-key');
    renderKey();
  }

  // Visible places → screen clusters (greedy: biggest place first absorbs neighbours within CLUSTER_PX).
  function clusters() {
    const cam = globe.camera().position, R2 = globe.getGlobeRadius() ** 2, vis = [];
    // Story key `only: [id, ...]`: just these studies are drawn, the others hidden and left out of clusters (human,
    // AI_LOG Impacts firefly-first step 2, B1: study 299 alone on Fireflies).
    const only = stage?.only;
    for (const p of places) {
      const ids = only ? p.ids.filter(id => only.includes(id)) : p.ids;
      if (!ids.length) continue;
      const c = globe.getCoords(p.lat, p.lng, 0);
      if (c.x * cam.x + c.y * cam.y + c.z * cam.z <= R2) continue;   // far side of the globe
      const s = globe.getScreenCoords(p.lat, p.lng, 0);
      vis.push({ x: s.x, y: s.y, ids });
    }
    vis.sort((a, b) => b.ids.length - a.ids.length);
    const out = [];
    for (const v of vis) {
      const c = out.find(o => (o.x - v.x) ** 2 + (o.y - v.y) ** 2 < CLUSTER_PX ** 2);
      if (c) { for (const id of v.ids) if (!c.ids.includes(id)) c.ids.push(id); }
      else out.push({ x: v.x, y: v.y, ids: [...v.ids] });
    }
    return out;
  }

  // Card order: the dominant category first, then the others in source order.
  const catsOf = id => {
    const s = studies.get(id), d = s?.dominant_category;
    return d ? [d, ...s.category.filter(c => c !== d)] : (s?.category ?? []);
  };
  const colorOf = id => (colourBy === 'species' ? SPECIES_COLORS.get(studyGroups.get(id)?.[0])
    : CATEGORY_COLORS.get(studies.get(id)?.dominant_category)) ?? OTHER;

  // FNV-1a hash to [0, 1]; same as Linda's hashUnit, so halo offsets are stable across reloads.
  function hashUnit(text) {
    let h = 2166136261;
    for (let i = 0; i < text.length; i += 1) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); }
    return (h >>> 0) / 4294967295;
  }

  // A solid dot with a thin dark rim; white ring when selected.
  function dot(x, y, r, color, isSel, alpha = 1) {
    ctx.globalAlpha = (isSel ? 1 : 0.85) * alpha;
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = alpha;
    ctx.strokeStyle = isSel ? '#fff' : '#000'; ctx.lineWidth = isSel ? 2 : 0.8;
    ctx.stroke();
  }

  function draw() {
    const w = window.innerWidth, h = window.innerHeight, dpr = globe.renderer().getPixelRatio();
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    hits = [];
    const ga = val(dotsA);
    // Bar: colour toggle + category filter on chart steps with filter: true; colour toggle alone on the globe
    // while exploring (Explore all studies, free Impacts mode).
    const ca = val(chartA), cats = Boolean(stage?.filter) && ca > 0.5, globeBar = browse && ca < 0.5;
    const circ = Boolean(stage?.circle) && val(circleA) > 0.5;
    if (cats !== barCats || circ !== barCircle) { barCats = cats; barCircle = circ; renderFilter(); }
    filterBar.hidden = !(cats || globeBar || circ);
    // Circle step: the size buttons sit in a row above the circle, as the chart's bar (human, AI_LOG Fireflies step 29;
    // was a column left of the circle, step 8).
    filterBar.classList.toggle('settled', circ && val(circleA) >= 1);
    if (circ) {
      const b = chartBox(w, h);
      filterBar.style.left = `${b.left}px`; filterBar.style.top = `${Math.max(8, b.top - 10 - filterBar.offsetHeight)}px`;
    }
    // Study card on the chart and circle steps: bottom left of the chart area, clear of the big text in the right
    // column (human, AI_LOG Effect dots and examples step 2: P3, "could change later"); elsewhere as style.css.
    placeCard(ca > 0.5 || circ);
    if (globeBar) {
      const panel = document.getElementById('modes')?.getBoundingClientRect().right ?? 0;
      filterBar.style.left = `${panel + 24}px`; filterBar.style.top = '76px';
    }
    if (ga > 0.005) drawGlobeDots(ga);
    if (ga > 0.005 && stage?.studyLabel) drawStudyLabel(stage.studyLabel, ga * val(labelA));
    if (ga > 0.005) drawHighlightLabel(ga, w);
    const sa = Math.max(ga, val(glowA));
    for (const k in siteA) { const v = val(siteA[k]); if (v > 0.005) drawSite(k, v * sa, w, h); }
    drawChart(w, h);
    drawCircle(w, h);
    ctx.globalAlpha = 1;
  }

  // Studies lit by the filter: any record in that category or species group (Linda's rule; agent default).
  const act = id => (!filter || studies.get(id)?.category.includes(filter) || studyGroups.get(id)?.includes(filter) ? 1 : 0.12)
    * hlOf(id);
  // Highlight count line (story `highlight`): "<label> · n of N studies", top centre; old and new crossfade.
  function drawHighlightLabel(ga, w) {
    const t = val(hlA);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '500 15px system-ui, sans-serif'; ctx.fillStyle = '#fff';
    [[hlFrom, 1 - t], [hlTo, t]].forEach(([h, a]) => {
      if (!h || a * ga < 0.01) return;
      ctx.globalAlpha = a * ga;
      ctx.fillText(`${h.label} · ${hlSets[h.set]?.size ?? 0} of ${hlLocated} studies`, w / 2, 56);
    });
  }

  function drawGlobeDots(ga) {
    const all = clusters();
    const open = expanded ? all.find(c => c.ids.length > 1 && c.ids.includes(expanded)) : null;
    const dim = (open ? 0.25 : 1) * ga;   // everything else fades while a cluster is spread out
    for (const c of all) {
      if (c === open) continue;
      if (c.ids.length === 1) {
        const isSel = c.ids[0] === selected;
        dot(c.x, c.y, isSel ? DOT_SELECTED : DOT, colorOf(c.ids[0]), isSel, dim * act(c.ids[0]));
        if (browse) hits.push({ x: c.x, y: c.y, r: 9, id: c.ids[0] });
      } else {
        // Linda-style halo: faint fill + dotted ring, the studies' dots offset 2–9 px inside it.
        ctx.globalAlpha = 0.08 * dim; ctx.fillStyle = '#fff';
        ctx.beginPath(); ctx.arc(c.x, c.y, HALO, 0, Math.PI * 2); ctx.fill();
        ctx.globalAlpha = 0.5 * dim; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.setLineDash([2, 3]);
        ctx.beginPath(); ctx.arc(c.x, c.y, HALO, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);
        for (const id of c.ids) {
          const a = hashUnit(`${id}-offset`) * Math.PI * 2, r = 2 + hashUnit(`${id}-radius`) * 7;
          dot(c.x + Math.cos(a) * r, c.y + Math.sin(a) * r, 3, colorOf(id), id === selected, dim * act(id));
        }
        if (browse) hits.push({ x: c.x, y: c.y, r: HALO, cluster: c.ids });
      }
    }
    if (open) {   // drawn last so the fan sits on top of everything else
      const ids = [...open.ids].sort((a, b) => a.localeCompare(b));
      const offs = fan(ids.length);
      const reach = Math.max(...offs.map(o => Math.hypot(o.dx, o.dy))) + 12;
      ctx.globalAlpha = 0.75; ctx.fillStyle = '#000';
      ctx.beginPath(); ctx.arc(open.x, open.y, reach, 0, Math.PI * 2); ctx.fill();
      ctx.globalAlpha = 0.7; ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(open.x, open.y, 2.5, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.3)'; ctx.lineWidth = 1;
      ids.forEach((id, i) => {
        const x = open.x + offs[i].dx, y = open.y + offs[i].dy;
        ctx.globalAlpha = 1;
        ctx.beginPath(); ctx.moveTo(open.x, open.y); ctx.lineTo(x, y); ctx.stroke();
      });
      ids.forEach((id, i) => {
        const x = open.x + offs[i].dx, y = open.y + offs[i].dy, isSel = id === selected;
        dot(x, y, isSel ? DOT_SELECTED : DOT + 0.5, colorOf(id), isSel, ga * act(id));
        if (browse) hits.push({ x, y, r: 9, id, fanned: true });
      });
    }
  }

  // Story key `studyLabel: { id, authors }` (human, AI_LOG Fireflies step 4): two centred lines under the study's dot,
  // its title, then authors (as given in the story) and year (studies.json). Font as the site label; spacing: agent choice.
  function drawStudyLabel({ id, authors }, a) {
    const s = studies.get(id), p = points.get(id)?.[0];
    if (!s || !p) return;
    const cam = globe.camera().position, c = globe.getCoords(p.lat, p.lon, 0);
    if (c.x * cam.x + c.y * cam.y + c.z * cam.z <= globe.getGlobeRadius() ** 2) return;
    const xy = globe.getScreenCoords(p.lat, p.lon, 0);
    const lines = [`“${s.title.join(' / ')}”`, `${authors} ${s.publication_year.join(', ')}`];
    ctx.font = '12px system-ui, sans-serif';
    // Card background as #card in style.css (black 0.8, 1 px #444 border; human, AI_LOG Fireflies step 5);
    // padding 6 / 10 px: agent choice.
    const w = Math.max(...lines.map(t => ctx.measureText(t).width)) + 20, h = 2 * 16 + 12, x = xy.x - w / 2, y = xy.y + 10;
    ctx.globalAlpha = a; ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = '#444'; ctx.lineWidth = 1; ctx.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    lines.forEach((t, i) => ctx.fillText(t, xy.x, y + 7 + i * 16));
  }

  // Site keys 'study:<id>' (human, AI_LOG Impacts firefly-first step 8, option T2): the study's own dot is the site, so
  // its glow grows from the dot (same place, the dot's colour) and no second marker or label is drawn.
  const siteOf = key => sites[key] ?? (key.startsWith('study:') && points.get(key.slice(6))?.[0]
    ? { ...points.get(key.slice(6))[0], colour: colorOf(key.slice(6)), study: true } : null);
  // Screen position of a site point; null when not loaded or on the far side of the globe.
  function siteXY(key) {
    const p = siteOf(key);
    if (!p) return null;
    const cam = globe.camera().position, c = globe.getCoords(p.lat, p.lon, 0);
    if (c.x * cam.x + c.y * cam.y + c.z * cam.z <= globe.getGlobeRadius() ** 2) return null;
    return globe.getScreenCoords(p.lat, p.lon, 0);
  }

  // A site outside Data S1, in its own style: a dot in the courtship-flash colour (565 nm, nm → RGB as in
  // spectral.js) with a white ring and a short label. glowA 0 → 1 turns it into a growing glow and drops the label.
  function drawSite(key, a, w, h) {
    const p = siteOf(key), s = siteXY(key);
    if (!p || !s || a < 0.005) return;
    const g = val(glowA);
    if (g > 0.001) {
      const r = DOT_SELECTED + 0.1 * Math.min(w, h) * g, grad = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, r);
      grad.addColorStop(0, '#fffbe6'); grad.addColorStop(0.18, p.colour); grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.globalAlpha = g; ctx.fillStyle = grad;
      ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, Math.PI * 2); ctx.fill();
    }
    if (p.study) return;   // the study's own dot (drawGlobeDots) fades as the glow grows
    dot(s.x, s.y, DOT_SELECTED, p.colour, true, a * (1 - g));
    ctx.globalAlpha = a * (1 - g); ctx.fillStyle = '#fff'; ctx.font = '12px system-ui, sans-serif';
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillText(p.label, s.x + 13, s.y);
  }

  // A frame already queued when hide() runs must not draw: hide() resets browse = true, so draw() would show
  // the colour toggle again on Light steps.
  function loop() { if (!shown) { frame = 0; return; } draw(); frame = requestAnimationFrame(loop); }

  // ── Broader Impacts circle (human, AI_LOG Broader Impacts circle concept steps 3 and 7: A2, log1p; sector angle ∝
  // the group's share of records since step 7 (was: equal sectors); on the main URL since step 7) ───────────────────
  // Every record in one circle of species-group sectors (lane order, clockwise from the top), coloured by species
  // group whatever the Colour toggle says. Dot area ∝ log1p(min(|g|, CAP)), the chart's x scale; smallest
  // radius = 0.16 × the largest (sketch: 0.9 vs 5.5 px). The largest radius is set so the most densely filled sector is
  // about 55 % covered; dots are scattered at random in their sector (seeded, so the same every load), then pushed apart.
  // Agent choices (not yet decided by the human): records fly in from their studies on the globe (as the chart);
  // labels = group name + record count; no clicking.
  let circleUnit = null;   // record → { x, y, r } in units of the circle radius (computed once)
  function circleLayout() {
    if (circleUnit) return circleUnit;
    const groups = [...SPECIES_COLORS.keys()], MIN = 0.16;
    const size = e => Math.max(MIN * MIN, Math.log1p(Math.min(CAP, e.g_abs)) / Math.log(CAP + 1));
    const fill = new Map(groups.map(g => [g, 0])), count = new Map(groups.map(g => [g, 0]));
    for (const e of effects) if (fill.has(e.species_group)) {
      fill.set(e.species_group, fill.get(e.species_group) + size(e)); count.set(e.species_group, count.get(e.species_group) + 1);
    }
    const total = [...count.values()].reduce((s, n) => s + n, 0);
    let start = -Math.PI / 2;
    const sectors = groups.map(g => { const span = (2 * Math.PI * count.get(g)) / total, s = { g, a0: start, span, n: count.get(g) }; start += span; return s; });
    // Coverage of a sector (unit circle) = 2π · rmax² · fill / span.
    const rmax = Math.sqrt(0.55 / Math.max(...sectors.filter(s => s.n).map(s => (2 * Math.PI * fill.get(s.g)) / s.span)));
    // Seeded random sequence in file order (mulberry32, seed 7): two hashes of the same id are correlated and drew spirals.
    let seed = 7;
    const rnd = () => { seed = (seed + 0x6d2b79f5) | 0; let z = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      z = (z + Math.imul(z ^ (z >>> 7), 61 | z)) ^ z; return ((z ^ (z >>> 14)) >>> 0) / 4294967296; };
    const ds = [];
    for (const e of effects) {
      const gi = groups.indexOf(e.species_group);
      if (gi < 0) continue;
      const { a0, span } = sectors[gi], a = a0 + span * (0.02 + 0.96 * rnd());
      const r = 0.97 * Math.sqrt(rnd());
      ds.push({ e, a0, span, x: r * Math.cos(a), y: r * Math.sin(a), r: rmax * Math.sqrt(size(e)) });
    }
    const cell = 2 * rmax, gap = rmax * 0.08;
    for (let k = 0; k < 40; k += 1) {
      const grid = new Map();
      ds.forEach((d, i) => { const key = `${Math.floor(d.x / cell)},${Math.floor(d.y / cell)}`; (grid.get(key) ?? grid.set(key, []).get(key)).push(i); });
      ds.forEach((p, i) => {
        const gx = Math.floor(p.x / cell), gy = Math.floor(p.y / cell);
        for (let ox = -1; ox <= 1; ox += 1) for (let oy = -1; oy <= 1; oy += 1) for (const j of grid.get(`${gx + ox},${gy + oy}`) ?? []) {
          if (j <= i) continue;
          const q = ds[j], dx = q.x - p.x, dy = q.y - p.y, m = p.r + q.r + gap, d = Math.hypot(dx, dy) || 1e-6;
          if (d < m) { const f = (m - d) / 2 / d; p.x -= dx * f; p.y -= dy * f; q.x += dx * f; q.y += dy * f; }
        }
      });
      for (const d of ds) {   // keep each dot inside its own sector and the circle
        let a = Math.atan2(d.y, d.x), r = Math.hypot(d.x, d.y);
        while (a < d.a0) a += 2 * Math.PI;
        while (a > d.a0 + 2 * Math.PI) a -= 2 * Math.PI;
        const lo = d.a0 + 0.004, hi = d.a0 + d.span - 0.004, a2 = a > hi ? (a - hi < lo + 2 * Math.PI - a ? hi : lo) : Math.max(a, lo);
        const r2 = Math.min(r, 1 - d.r);
        if (a2 !== a || r2 !== r) { d.x = r2 * Math.cos(a2); d.y = r2 * Math.sin(a2); }
      }
    }
    circleUnit = new Map(ds.map(d => [d.e, d]));
    circleUnit.sectors = sectors;
    // Per group: records in each size class (the label count follows the size toggle; human request, step 9).
    for (const s of sectors) s.byClass = {};
    for (const d of ds) { const c = sectors[groups.indexOf(d.e.species_group)].byClass, w = word(d.e.g_abs); c[w] = (c[w] ?? 0) + 1; }
    return circleUnit;
  }

  // Circle centre and radius: in the chart's box (left of the right-column text, below the size buttons), room for
  // labels (human, AI_LOG Fireflies step 29: same layout as the charts; was right of the step panel and the text).
  function circleBox(w, h) {
    // Top-anchored (50 px for the top labels), so the key level with the circle's top stays above the big text.
    const b = chartBox(w, h), height = h - b.top - 60;
    const R = Math.max(80, Math.min(b.width / 2 - 110, height / 2 - 50));
    return { x: b.left + b.width / 2, y: b.top + 50 + R, R };
  }

  function drawCircle(w, h) {
    const k = val(circleA);
    go(circleKeyA, k >= 1 ? 1 : 0, k >= 1 ? 600 : 300);   // key once the circle has settled (timing (i))
    if (k < 0.005 || !effects.length) return;
    const L = circleLayout(), b = circleBox(w, h), from = studyScreen(), sel = [];
    ctx.globalAlpha = 0.82 * k; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
    for (const e of effects) {
      const d = L.get(e), s = from.get(e.study_id);
      if (!d || !s) continue;
      // Linda's arc path and per-record delay, as drawRecords.
      const delay = hashUnit(`${e.effect_id}-t`) * 0.25, t = clamp01((k - delay) / (1 - delay));
      const tx = b.x + d.x * b.R, ty = b.y + d.y * b.R;
      const dx = tx - s.x, dy = ty - s.y, len = Math.max(1, Math.hypot(dx, dy));
      const bend = Math.sin(Math.PI * t) * (18 + hashUnit(`${e.effect_id}-a`) * 34) * (hashUnit(`${e.effect_id}-s`) > 0.5 ? 1 : -1);
      const x = s.x + dx * t - (dy / len) * bend, y = s.y + dy * t + (dx / len) * bend;
      const on = !sizeSel || word(e.g_abs) === sizeSel, r = 1.8 + (d.r * b.R - 1.8) * t;
      // Settled dots open their study's card; the open study's dots get a white ring (as the chart, AI_LOG Effect
      // dots and examples step 2).
      if (k >= 1 && on) hits.push({ x, y, r: Math.max(REC_HIT, r + 1), id: e.study_id, chart: true });
      if (e.study_id === selected && on) { sel.push([x, y, r, e]); continue; }
      ctx.globalAlpha = (s.vis ? 1 : t) * Math.min(1, k * 4) * (on ? 0.85 : 0.08);
      ctx.fillStyle = SPECIES_COLORS.get(e.species_group);
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    }
    for (const [x, y, r, e] of sel) dot(x, y, Math.max(3.2, r), SPECIES_COLORS.get(e.species_group), true, k);
    const ce = calloutEffect(), cd = ce && L.get(ce);
    if (cd && k >= 1) {
      dot(b.x + cd.x * b.R, b.y + cd.y * b.R, Math.max(5.5, cd.r * b.R + 2), SPECIES_COLORS.get(ce.species_group), true, val(calloutA));
      openPending(ce, b.x + cd.x * b.R);
    }
    ctx.lineWidth = 1;
    // Labels: group name (as the species lanes) and its number of records, outside the middle of each sector. Thin
    // sectors (Amphibians, Reptiles) sit side by side, so labels on each side are pushed apart vertically, with a
    // short line back to their sector when moved.
    if (val(circleKeyA) > 0.005) drawKey('circle', b.y - b.R, val(circleKeyA) * Math.min(1, k * 4));
    const la = clamp01((k - 0.85) / 0.15);
    if (la <= 0) return;
    const LH = 15, labels = L.sectors.filter(s => s.n).map(s => {
      const a = s.a0 + s.span / 2, c = Math.cos(a), sn = Math.sin(a), lines = [...GROUPS.species.name[s.g]];
      const hgt = (lines.length + 1) * LH, ly = b.y + (b.R + 14) * sn;
      const top = ly + (sn > 0.25 ? 0 : sn < -0.25 ? -hgt : -hgt / 2);
      return { s, c, sn, lines, hgt, top, want: top, ax: b.x + (b.R + 4) * c, ay: b.y + (b.R + 4) * sn,
        lx: b.x + (b.R + 14) * c, side: c >= 0 ? 1 : -1 };
    });
    for (const side of [1, -1]) {
      const col = labels.filter(l => l.side === side).sort((p, q) => p.top - q.top);
      for (let i = 1; i < col.length; i += 1) col[i].top = Math.max(col[i].top, col[i - 1].top + col[i - 1].hgt + 4);
    }
    ctx.font = '12px system-ui, sans-serif'; ctx.textBaseline = 'top';
    for (const l of labels) {
      ctx.textAlign = l.c > 0.25 ? 'left' : l.c < -0.25 ? 'right' : 'center';
      const moved = Math.abs(l.top - l.want) > 2;
      const lx = moved ? l.lx + l.side * 14 : l.lx;
      if (moved) {
        ctx.globalAlpha = la * 0.5; ctx.strokeStyle = '#888'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(l.ax, l.ay); ctx.lineTo(lx - l.side * 3, l.top + LH / 2); ctx.stroke();
      }
      l.lines.forEach((t, i) => { ctx.globalAlpha = la; ctx.fillStyle = '#ddd'; ctx.fillText(t, lx, l.top + i * LH + 2); });
      ctx.globalAlpha = la * 0.8; ctx.fillStyle = '#999'; ctx.fillText(String(sizeSel ? l.s.byClass[sizeSel] ?? 0 : l.s.n), lx, l.top + l.lines.length * LH + 2);
    }
  }

  // ── Effects chart (story Part 2) ──────────────────────────────────────────────────
  function chartBox(w, h) {
    const narrow = w < 700;
    // Keep the lane labels clear of the left step panel (#modes).
    const panel = document.getElementById('modes')?.getBoundingClientRect().right ?? 0;
    const left = narrow ? 92 : Math.max(170, panel + 130), right = narrow ? 16 : Math.min(420, w * 0.34);
    const top = narrow ? 150 : 120, bottom = narrow ? 250 : 120;
    return { left, top, width: Math.max(160, w - left - right), height: Math.max(180, h - top - bottom), narrow };
  }
  const word = g => (g >= 0.8 ? 'large' : g >= 0.5 ? 'medium' : g >= 0.2 ? 'small' : 'below small');

  // Screen position of each study's first point; vis = on the near side of the globe.
  function studyScreen() {
    const cam = globe.camera().position, R2 = globe.getGlobeRadius() ** 2, out = new Map();
    for (const [id, pts] of points) {
      const p = pts[0], c = globe.getCoords(p.lat, p.lon, 0), s = globe.getScreenCoords(p.lat, p.lon, 0);
      out.set(id, { x: s.x, y: s.y, vis: c.x * cam.x + c.y * cam.y + c.z * cam.z > R2 });
    }
    return out;
  }

  function drawChart(w, h) {
    const ca = val(chartA);
    if (ca < 0.005) return;
    const b = chartBox(w, h);
    const sx = v => b.left + Math.log1p(Math.min(CAP, Math.max(0, v))) / Math.log(CAP + 1) * b.width;
    // Lane centre of a record's group key, sliding from the previous grouping to the current one.
    const gp = val(groupA), gFrom = geom(b, fromGroup), gTo = geom(b, toGroup);
    const ly = e => gFrom.y(GROUPS[fromGroup].key(e)) + (gTo.y(GROUPS[toGroup].key(e)) - gFrom.y(GROUPS[fromGroup].key(e))) * gp;
    // Bar above the chart: bottom edge 10 px over the top lane however many rows it wraps to, and its right end
    // clear of the study card (360 px + margins; human request, AI_LOG Impacts step 61).
    filterBar.style.left = `${b.left}px`;
    const beside = w - b.left - 392;   // narrow windows: use the full width (the card may cover the bar's end)
    filterBar.style.maxWidth = `${beside >= 500 ? beside : w - b.left - 16}px`;
    filterBar.style.top = `${Math.max(8, b.top - 10 - filterBar.offsetHeight)}px`;

    ctx.globalAlpha = 0.82 * ca; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, w, h);
    if (fromGroup !== toGroup) drawLanes(b, sx, fromGroup, ca * (1 - gp));
    drawLanes(b, sx, toGroup, fromGroup !== toGroup ? ca * gp : ca);
    ctx.globalAlpha = ca;
    ctx.textAlign = 'center'; ctx.textBaseline = 'top';
    const base = b.top + b.height;
    for (const [v, num, w2] of TICKS) {
      const x = sx(v);
      ctx.strokeStyle = v === 0.2 || v === 0.5 || v === 0.8 ? 'rgba(255,255,255,0.18)' : 'rgba(255,255,255,0.08)';
      ctx.beginPath(); ctx.moveTo(x, b.top); ctx.lineTo(x, base); ctx.stroke();
      ctx.fillStyle = '#999'; ctx.font = '11px system-ui, sans-serif'; ctx.fillText(num, x, base + 8);
      if (w2) { ctx.fillStyle = '#ddd'; ctx.font = '500 11px system-ui, sans-serif'; ctx.fillText(w2, x, base + 22); }
    }
    ctx.fillStyle = '#fff'; ctx.font = `400 ${b.narrow ? 13 : 15}px system-ui, sans-serif`;
    ctx.fillText('How much did light at night change what was measured?', b.left + b.width / 2, base + 44);
    ctx.fillStyle = '#888'; ctx.font = '11px system-ui, sans-serif';
    ctx.fillText('|Hedges g| = difference between lit and dark groups ÷ the normal spread between individuals',
      b.left + b.width / 2, base + 64);
    ctx.fillText('Log scale; values above 10 sit at the edge. small / medium / large: Cohen (1988) conventions.',
      b.left + b.width / 2, base + 79);

    const ex = stage?.example ? effectsById.get(stage.example) : lastExample;
    const p = val(morphA), ea = val(exampleA);
    if (p > 0.001) {
      drawRecords(b, sx, gFrom, gTo, gp, p, ca, ea > 0.005 ? ex : null);
      if (fromGroup !== toGroup) drawMedians(b, sx, fromGroup, p * ca * (1 - gp));
      drawMedians(b, sx, toGroup, p * ca * (fromGroup !== toGroup ? gp : 1));
    }
    if (ex && ea > 0.005) { lastExample = ex; drawExample(b, sx, ly, ex, ea * ca); }
    // Callout: its record marked like the example's dot (5.5 px, white rim), once the lanes have settled.
    const ce = calloutEffect();
    if (ce && p >= 1 && val(groupA) >= 1) {
      const { x, y } = doorXY(ce, b, sx);
      dot(x, y, 5.5, recColor(ce), true, ca * val(calloutA));
      if (ca >= 1) openPending(ce, x);
    }
    if (stage?.door && p > 0.9) drawDoor(b, sx, ca);
    // Reading key once the dots have settled (timing (i): in over 0.6 s, stays; out over 0.3 s when the lanes move).
    // Only on the plain view (no filter).
    const settled = p >= 1 && gp >= 1 && !filter;
    go(noteA, settled ? 1 : 0, settled ? 600 : 300);
    const na = val(noteA) * ca;
    if (na > 0.005) drawKey('chart', b.top, na);
  }

  // Reading keys in the right column (human, AI_LOG Fireflies step 29): samples (not real records), 14 px text, the
  // first row level with the top of the visualization (human: "aligned with the top of the visualization"; was
  // above the big text, before that next to a dot in the chart). Chart (A1 picks 1a, 2a; "White line …" removed by
  // the human): a dot, an arrow. Circle (C picks 1a, 2a; "Numbers = …" removed by the human): a dot, a
  // small and a big dot.
  // Agent choices: sizes, spacing, sample dot colour.
  const KEY_ROWS = {
    chart: [['One dot = one measured effect', x => dot(x + 10, 0, 5, '#bbb', true, ctx.globalAlpha)],
      ['bigger change under light', x => { ctx.strokeStyle = '#ddd'; ctx.lineWidth = 1.5; ctx.beginPath();
        ctx.moveTo(x + 2, 0); ctx.lineTo(x + 40, 0); ctx.moveTo(x + 34, -5); ctx.lineTo(x + 40, 0); ctx.lineTo(x + 34, 5); ctx.stroke(); }]],
    circle: [['One dot = one measured effect', x => dot(x + 10, 0, 5, '#bbb', true, ctx.globalAlpha)],
      ['Bigger dot = bigger change', x => { dot(x + 6, 0, 2.5, '#bbb', false, ctx.globalAlpha); dot(x + 24, 0, 7, '#bbb', false, ctx.globalAlpha); }]],
  };
  function drawKey(kind, top, a) {
    const fact = document.getElementById('fact');
    if (!fact || fact.hidden || !fact.classList.contains('right')) return;
    const x = fact.getBoundingClientRect().left, ROW = 30;
    KEY_ROWS[kind].forEach(([text, sample], i) => {
      ctx.save(); ctx.translate(0, top + 8 + i * ROW); ctx.globalAlpha = a; ctx.lineJoin = 'round';
      sample(x);
      ctx.font = '400 14px system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#ddd';
      ctx.fillText(text, x + 50, 0);
      ctx.restore();
    });
  }

  // Door into a spectral chapter (human: option B + click, door = record 299-3; Firefly transition task step 2):
  // a pulsing ring on one record; clicking it calls onDoor, and main.js grows the 3D chapter out of this spot.
  // Position = where drawRecords puts the record once settled.
  function doorXY(e, b, sx) {
    const g = geom(b, toGroup);
    return { x: sx(e.g_abs), y: g.y(GROUPS[toGroup].key(e)) + (hashUnit(e.effect_id) - 0.5) * g.h * 0.7 };
  }
  function drawDoor(b, sx, a) {
    const e = effectsById.get(stage.door);
    if (!e || !passes(e) || val(groupA) < 1) return;
    const { x, y } = doorXY(e, b, sx), pulse = (performance.now() % 1600) / 1600;
    ctx.globalAlpha = a;
    dot(x, y, 4, recColor(e), true, a);
    ctx.globalAlpha = a * (1 - pulse); ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.arc(x, y, 6 + pulse * 12, 0, Math.PI * 2); ctx.stroke();
    ctx.globalAlpha = a; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#fff'; ctx.font = '500 12px system-ui, sans-serif';
    ctx.fillText(stage.doorLabel ?? '', x + 14, y + 14);
    ctx.lineWidth = 1;
    hits.push({ x, y, r: 12, door: e.effect_id });
  }

  function geom(b, gname) {
    const lanes = GROUPS[gname].lanes, h = b.height / lanes.length;
    return { h, y: k => b.top + h * (lanes.indexOf(k) + 0.5) };
  }

  // Lane lines and labels of one grouping. Category lanes: label in the category colour + record count
  // (unchanged). Band / light-type lanes: neutral label, records and studies (follow the category filter).
  function drawLanes(b, sx, gname, a) {
    if (a < 0.005) return;
    const gr = GROUPS[gname], { y: ly } = geom(b, gname), fs = b.narrow ? 10 : 11;
    ctx.globalAlpha = a; ctx.textBaseline = 'middle'; ctx.lineWidth = 1; ctx.textAlign = 'right';
    for (const c of gr.lanes) {
      const y = ly(c);
      ctx.strokeStyle = 'rgba(255,255,255,0.12)';
      ctx.beginPath(); ctx.moveTo(b.left, y); ctx.lineTo(b.left + b.width, y); ctx.stroke();
      ctx.font = `500 ${b.narrow ? 11 : 13}px system-ui, sans-serif`;
      if (gname === 'category') {
        const on = !filter || filter === c || colourBy === 'species';
        ctx.fillStyle = !on ? '#555' : colourBy === 'category' ? CATEGORY_COLORS.get(c) : '#eee';
        ctx.fillText(LANE_LABEL[c] ?? c, b.left - 12, y - 7);
        ctx.fillStyle = on ? '#888' : '#444'; ctx.font = `${fs}px system-ui, sans-serif`;
        ctx.fillText(`${laneCount.get(c) ?? 0} records`, b.left - 12, y + 9);
        continue;
      }
      const s = laneStats.get(`${gname}|${c}|${filter ?? ''}`), lines = gr.name[c];
      let ty = y - (lines.length + 1) * 7;
      ctx.fillStyle = '#eee'; ctx.fillText(lines[0], b.left - 12, ty);
      if (gname === 'species' && colourBy === 'species') {   // colour key beside the group name
        ctx.fillStyle = SPECIES_COLORS.get(c);
        ctx.beginPath(); ctx.arc(b.left - 20 - ctx.measureText(lines[0]).width, ty, 4, 0, Math.PI * 2); ctx.fill();
      }
      ctx.font = `${fs}px system-ui, sans-serif`;
      for (const l of lines.slice(1)) { ty += 15; ctx.fillStyle = '#bbb'; ctx.fillText(l, b.left - 12, ty); }
      ctx.fillStyle = '#888';
      ctx.fillText(`${s.records.toLocaleString('en')} records`, b.left - 12, ty += 15);
      ctx.fillText(`${s.studies} studies`, b.left - 12, ty + 14);
      if (gr.header?.[c]) {
        ctx.fillStyle = '#777'; ctx.font = `600 ${b.narrow ? 9 : 10}px system-ui, sans-serif`; ctx.textAlign = 'left';
        ctx.fillText(gr.header[c], b.left + 2, y - geom(b, gname).h / 2 + 8);
        ctx.textAlign = 'right';
      }
    }
  }

  // Median of the lane's study medians |g| (option ii, per study; within the category filter), drawn over the dots.
  function drawMedians(b, sx, gname, a) {
    if (a < 0.005) return;
    const { y: ly, h } = geom(b, gname);
    ctx.globalAlpha = a; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
    for (const c of GROUPS[gname].lanes) {
      const s = laneStats.get(`${gname}|${c}|${filter ?? ''}`);
      if (s.median == null) continue;
      const x = sx(s.median), y = ly(c), half = Math.min(h * 0.42, 40);
      ctx.strokeStyle = '#000'; ctx.lineWidth = 5;
      ctx.beginPath(); ctx.moveTo(x, y - half); ctx.lineTo(x, y + half); ctx.stroke();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.font = '500 11px system-ui, sans-serif';
      ctx.fillText(`study median ${fmt(s.median)}`, x + 5, y - half + 10);
    }
    ctx.lineWidth = 1;
  }

  // All records: they lift off their study's spot on the globe and settle in their lane (Linda's
  // arc path and per-record delay); p = 0 on the globe, 1 in the chart.
  // Between groupings (gp 0 → 1) each record slides vertically from its old lane to its new one; x stays.
  // Once settled, every record is a hit that opens its study's card (human, AI_LOG Effect dots and examples step 2;
  // nearest dot within REC_HIT px wins). The open study's records are drawn on top with a white ring.
  function drawRecords(b, sx, gFrom, gTo, gp, p, ca, ex) {
    const from = studyScreen(), kFrom = GROUPS[fromGroup].key, kTo = GROUPS[toGroup].key;
    const clickable = p >= 1 && gp >= 1 && ca > 0.9, sel = [];
    for (const e of effects) {
      if (e === ex) continue;
      const s = from.get(e.study_id);
      const delay = hashUnit(`${e.effect_id}-t`) * 0.25, t = clamp01((p - delay) / (1 - delay));
      const u = gp >= 1 ? 1 : clamp01((gp - delay) / (1 - delay)), j = hashUnit(e.effect_id) - 0.5;
      const yA = gFrom.y(kFrom(e)) + j * gFrom.h * 0.7, yB = gTo.y(kTo(e)) + j * gTo.h * 0.7;
      const tx = sx(e.g_abs), ty = yA + (yB - yA) * u;
      const dx = tx - s.x, dy = ty - s.y, len = Math.max(1, Math.hypot(dx, dy));
      const bend = Math.sin(Math.PI * t) * (18 + hashUnit(`${e.effect_id}-a`) * 34) * (hashUnit(`${e.effect_id}-s`) > 0.5 ? 1 : -1);
      const x = s.x + dx * t - (dy / len) * bend, y = s.y + dy * t + (dx / len) * bend;
      const on = passes(e);
      if (e.study_id === selected && on) { sel.push([x, y, e]); continue; }
      ctx.globalAlpha = (s.vis ? 1 : t) * Math.min(1, p * 4) * (on ? 0.8 : 0.06) * ca;
      ctx.fillStyle = recColor(e);
      ctx.beginPath(); ctx.arc(x, y, 1.8, 0, Math.PI * 2); ctx.fill();
      if (clickable && on) hits.push({ x, y, r: REC_HIT, id: e.study_id, chart: true });
    }
    for (const [x, y, e] of sel) {
      dot(x, y, 3.2, recColor(e), true, ca);
      if (clickable) hits.push({ x, y, r: REC_HIT, id: e.study_id, chart: true });
    }
    ctx.lineWidth = 1;
  }

  // Worked example: the record's dark and lit means (± SD) as two bars, which then collapse into
  // one dot at its |g|. Pooled SD and the small-sample factor J as in the recomputation (AI_LOG step 25).
  function drawExample(b, sx, ly, e, a) {
    const k = easeInOut(clamp01((performance.now() - collapseT0) / EXAMPLE_MS));
    const unit = (e.measured_effect?.match(/\(([^)]+)\)\s*$/) || [])[1] ?? '';
    const name = (stage?.exampleLabel ?? e.measured_effect ?? '').trim();
    const col = recColor(e), target = { x: sx(e.g_abs), y: ly(e) };
    const x0 = b.left, bw = b.width * 0.6, y0 = b.top + b.height * 0.12, bh = 16;
    const max = Math.max(e.control_mean + (e.control_sd ?? 0), e.lit_mean + (e.lit_sd ?? 0)) * 1.1;
    const bx = v => x0 + (v / max) * bw;
    const sd = Math.sqrt(((e.control_n - 1) * e.control_sd ** 2 + (e.lit_n - 1) * e.lit_sd ** 2) / (e.control_n + e.lit_n - 2));
    if (k < 1) {
      ctx.globalAlpha = a * (1 - k);
      ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
      ctx.fillStyle = '#fff'; ctx.font = '500 15px system-ui, sans-serif';
      ctx.fillText(name, x0, y0 - 14);
      const rows = [['In the dark', e.control_mean, e.control_sd, e.control_n, '#9a9a9a', y0 + 8],
        [`Under light: ${e.light_source ?? ''}${e.night_lux ? `, ${e.night_lux} lx` : ''}`, e.lit_mean, e.lit_sd, e.lit_n, col, y0 + 58]];
      for (const [label, m, s, n, c, y] of rows) {
        ctx.fillStyle = '#bbb'; ctx.font = '12px system-ui, sans-serif'; ctx.fillText(`${label}  (n = ${n})`, x0, y);
        ctx.fillStyle = c; ctx.fillRect(x0, y + 6, bx(m) - x0, bh);
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1;   // ± SD whisker
        ctx.beginPath(); ctx.moveTo(bx(m - s), y + 6 + bh / 2); ctx.lineTo(bx(m + s), y + 6 + bh / 2); ctx.stroke();
        ctx.fillStyle = '#fff'; ctx.font = '12px system-ui, sans-serif';
        ctx.fillText(`${fmt(m)} ${unit}`, bx(m + s) + 8, y + 6 + bh - 3);
      }
      ctx.fillStyle = '#ddd'; ctx.font = '13px system-ui, sans-serif';
      ctx.fillText(`Difference ${fmt(Math.abs(e.lit_mean - e.control_mean))} ${unit} ÷ normal spread ${fmt(sd)} ${unit}` +
        ` → g = ${fmt(e.g_abs)} (with a small-sample correction)`, x0, y0 + 112);
      ctx.fillStyle = '#888'; ctx.font = '11px system-ui, sans-serif';
      ctx.fillText('Bars: group means; white line: ± 1 standard deviation (spread between individuals).', x0, y0 + 130);
    }
    const sx0 = bx(e.lit_mean), sy0 = y0 + 58 + 6 + bh / 2;
    const x = sx0 + (target.x - sx0) * k, y = sy0 + (target.y - sy0) * k;
    // From the first callout on, the example becomes a plain record (human, AI_LOG Effect dots and examples step 5).
    const off = val(calloutA);
    ctx.globalAlpha = a;
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, 5.5 - 3.7 * off, 0, Math.PI * 2); ctx.fill();
    ctx.globalAlpha = a * (1 - off); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
    if (k >= 1) {
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#fff'; ctx.font = '500 12px system-ui, sans-serif';
      ctx.fillText(`${name}: |g| = ${fmt(e.g_abs)} (${word(e.g_abs)})`, x + 12, y - 14);
      ctx.globalAlpha = a;
      if (a > 0.9 && passes(e)) hits.push({ x, y, r: 8, id: e.study_id, chart: true });
    }
  }

  // Story stage (set by a story step; null = free browsing in Impacts mode).
  // { view: 'globe'|'chart', dots: false, reveal: true, study: id, example: effect_id, exampleLabel, records: true,
  //   filter: true, explore: true }  explore = dots clickable with the study card inside the story (step 34).
  // snap: jump straight to the step's end state (used when the chart is uncovered by a closing 3D chapter).
  function setStage(s, { snap = false } = {}) {
    const prev = stage;
    stage = s ?? null;
    browse = !s || Boolean(s.explore);
    if (s) { expanded = null; closeCard(); selected = s.study ?? null; }
    const chart = s?.view === 'chart';
    go(dotsA, !s ? 1 : chart || s.dots === false || s.glow ? 0 : 1, s?.reveal ? REVEAL_MS : FADE_MS);
    go(glowA, s?.glow ? 1 : 0, s?.glow ? GLOW_IN_MS : GLOW_OUT_MS);
    const keys = [].concat(s?.site ?? []);
    for (const k of new Set([...Object.keys(siteA), ...keys])) go(siteA[k] ??= anim(0), keys.includes(k) ? 1 : 0, FADE_MS);
    go(chartA, chart ? 1 : 0, FADE_MS);
    go(circleA, s?.circle ? 1 : 0, MORPH_MS);
    clearTimeout(labelTimer);
    const lab = s?.studyLabel;
    if (!lab) go(labelA, 0, FADE_MS);
    else if (snap) { labelA.from = labelA.to = 1; }
    else if (lab.id !== prev?.studyLabel?.id || labelA.to === 0) {
      labelA.from = labelA.to = 0;
      labelTimer = setTimeout(() => go(labelA, 1, FADE_MS), lab.delay ?? 0);
    }
    hlTimers.forEach(clearTimeout); hlTimers = [];
    const seq = s?.highlight ?? [];
    if (!seq.length || seq[0].set !== hlTo?.set) hlGo(null);
    const first = seq.length > 1 ? (s.reveal ? REVEAL_MS : 0) + HL_FIRST : 0;
    seq.forEach((h, i) => { const ms = first + i * HL_STEP; if (ms === 0) hlGo(h); else hlTimers.push(setTimeout(() => hlGo(h), ms)); });
    go(morphA, chart && s.records ? 1 : 0, MORPH_MS);
    // Grouping of the records (s.group: 'category' default | 'band' | 'type' | 'species'). A change while the chart is
    // showing slides the dots to their new lanes; otherwise the new grouping is set at once.
    const group = chart ? s.group ?? 'category' : toGroup;
    if (group !== toGroup) {
      if (val(chartA) > 0.05) {
        fromGroup = val(groupA) > 0.5 ? toGroup : fromGroup;
        toGroup = group; groupA.from = 0; groupA.to = 1; groupA.t0 = performance.now(); groupA.ms = REGROUP_MS;
      } else { fromGroup = toGroup = group; groupA.from = groupA.to = 1; }
    }
    if (chart && s.example) {
      // The dark-vs-lit bars play only on the worked-example step itself; arriving straight at a step with
      // all records shows the example already as its dot (human request, AI_LOG Impacts step 38).
      if (exampleA.to !== 1 || (!s.records && prev?.records)) {
        collapseT0 = s.records ? -Infinity : Infinity;
        go(exampleA, 1, s.records ? FADE_MS : 1);
      } else if (s.records && collapseT0 === Infinity) collapseT0 = performance.now();   // moving on: collapse now
    } else go(exampleA, 0, FADE_MS);
    if (!s?.filter) filter = null;   // the filter lives only on steps that show its buttons
    if (!s?.circle) sizeSel = null;
    if (snap) for (const a of [dotsA, chartA, morphA, exampleA, groupA, glowA, circleA, hlA, ...Object.values(siteA)]) { a.from = a.to; a.t0 = 0; }
    if (callout?.k) applyCallout();   // setStage cleared the selection; the current callout selects again once settled
    renderFilter();
  }

  // Fanned-out dots win over anything under them; otherwise the nearest hit within its radius.
  function hitAt(x, y) {
    let best = null, bd = Infinity;
    for (const h of hits) {
      const d = (h.x - x) ** 2 + (h.y - y) ** 2;
      if (d > h.r ** 2) continue;
      const score = h.fanned ? d - 1e6 : d;
      if (score < bd) { bd = score; best = h; }
    }
    return best;
  }

  // at: screen x of the dot that opened the card (chart / circle), for the side rule in placeCard.
  function openCard(id, at = null) {
    const s = studies.get(id);
    if (!s) return;
    selected = id; cardAt = at; dragged = false;
    const n = order.indexOf(id);
    const light = s.light_type_code.map(c => esc(lightWords.get(c) ?? c));
    const night = range(s.night_lux_min, s.night_lux_max), control = range(s.control_lux_min, s.control_lux_max);
    const lux = night != null
      ? `${night} lx at night${control != null ? ` (control ${control} lx)` : ''}`
      : s.night_lux_band.length ? `night light level: ${esc(s.night_lux_band.join(', '))}` : '';
    const eff = studyEffect.get(id);
    const where = [...new Set(points.get(id).map(p => p.location))].map(esc).join('; ');
    const doi = s.doi_url
      ? `<a href="${esc(s.doi_url)}" target="_blank" rel="noopener">doi.org/${esc(s.doi)} ↗</a>`
      : `<span>No single DOI in the source data</span>`;
    card.innerHTML = `<button class="close" aria-label="Close">×</button>
      <h2>${esc(s.title.join(' / '))}</h2>
      <div class="meta">${[where, [...s.study_type, ...s.habitat].map(esc).join(' · ')].filter(Boolean).join(' · ')}</div>
      <div class="cats">${(studyGroups.get(id) ?? []).map(g => `<span><i style="background:${SPECIES_COLORS.get(g) ?? OTHER}"></i>${esc(g)}</span>`).join('')}</div>
      <div class="cats">${catsOf(id).map(c => `<span><i style="background:${CATEGORY_COLORS.get(c) ?? OTHER}"></i>${esc(c)}</span>`).join('')}</div>
      <div class="light">${[light.join(', '), s.light_source.map(esc).join(', '), lux].filter(Boolean).join('<br>')}</div>
      ${eff ? `<div class="light">Median effect: |g| ${fmt(eff.median)} (${word(eff.median)}), across ${eff.n} measured effect${eff.n === 1 ? '' : 's'}</div>` : ''}
      <div class="cite">
        <div>${esc(s.authors.join('; '))} · ${esc(s.publication_year.join(', '))} · ${esc(s.journal.join(', '))}</div>
        <div class="doi">${doi}</div>
      </div>
      <div class="step"><button class="prev" aria-label="Previous study">‹</button>
        <span>${n + 1} of ${order.length}</span>
        <button class="next" aria-label="Next study">›</button></div>`;
    placeCard();
    card.hidden = false;
    card.querySelector('.close').addEventListener('click', closeCard);
    card.querySelector('.prev').addEventListener('click', () => step(-1));
    card.querySelector('.next').addEventListener('click', () => step(1));
  }

  // Next/previous study (wraps around); the globe turns to it and its cluster is spread out.
  function step(delta) {
    const i = selected ? order.indexOf(selected) : -1;
    const id = order[(i + delta + order.length) % order.length];
    const p = points.get(id)[0];
    expanded = id;
    openCard(id);
    globe.pointOfView({ lat: p.lat, lng: p.lon, altitude: globe.pointOfView().altitude }, 800);
  }

  // Card position on chart / circle steps: at the bottom of the chart area, on the side away from its dot (human, AI_LOG
  // Effect dots and examples step 6; was bottom left, P3): a dot in the left half → bottom right, else bottom left.
  // Elsewhere style.css. Also set on open, so a card never shows a frame at its default place. A dragged card stays put.
  let cardAt = null, dragged = false;
  function placeCard(onChart = val(chartA) > 0.5 || Boolean(stage?.circle) && val(circleA) > 0.5) {
    if (dragged) return;
    const b = chartBox(window.innerWidth, window.innerHeight), cw = Math.min(380, window.innerWidth - 32);
    const right = cardAt != null && cardAt < b.left + b.width / 2;
    card.style.left = onChart ? `${right ? b.left + b.width - cw : b.left}px` : '';
    card.style.right = card.style.top = onChart ? 'auto' : '';
    card.style.bottom = onChart ? '16px' : '';
  }
  // Draggable by its title (human, step 6: "I would prefer them to be draggable"); kept on screen. Handle = the title,
  // so the rest of the card's text stays selectable (agent choice).
  card.addEventListener('pointerdown', e => {
    if (e.button !== 0 || !e.target.closest('h2')) return;
    e.preventDefault();
    const r = card.getBoundingClientRect(), ox = e.clientX - r.left, oy = e.clientY - r.top;
    try { card.setPointerCapture(e.pointerId); } catch { /* no active pointer (synthetic event) */ }
    const move = ev => {
      dragged = true;
      const x = Math.min(Math.max(0, ev.clientX - ox), window.innerWidth - r.width);
      const y = Math.min(Math.max(0, ev.clientY - oy), window.innerHeight - 40);
      Object.assign(card.style, { left: `${x}px`, top: `${y}px`, right: 'auto', bottom: 'auto' });
    };
    const up = () => card.removeEventListener('pointermove', move);
    card.addEventListener('pointermove', move);
    card.addEventListener('pointerup', up, { once: true });
    card.addEventListener('pointercancel', up, { once: true });
  });

  // Closing a card keeps the current callout's selection (its rings) once it has settled.
  function closeCard() { card.hidden = true; selected = pendingSel ? null : calloutStudy(); }

  // Clicks go to the globe element (the overlay ignores pointer events); a drag is not a click.
  let down = null;
  globeEl.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY }; });
  globeEl.addEventListener('click', e => {
    if (!shown || !down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5) return;
    const h = hitAt(e.clientX, e.clientY);
    // Study dots on the chart are clickable inside the story too (step 60); other clicks keep the old rules.
    if (h?.door) { onDoor?.(h.door); return; }
    if (!browse) { if (h?.chart) openCard(h.id, h.x); else if (!card.hidden) closeCard(); return; }
    if (!h) { expanded = null; closeCard(); }
    else if (h.cluster) expanded = h.cluster[0];
    else { if (!h.fanned) expanded = null; openCard(h.id); }
  });
  globeEl.addEventListener('pointermove', e => {
    if (shown) globeEl.style.cursor = hitAt(e.clientX, e.clientY) ? 'pointer' : '';
  });
  window.addEventListener('keydown', e => {
    if (!shown || !browse) return;
    if (e.key === 'Escape') { expanded = null; closeCard(); }
    else if (stage) return;   // inside the story, ← → belong to the story (the card's ‹ › still work)
    else if (e.key === 'ArrowRight') step(1);
    else if (e.key === 'ArrowLeft') step(-1);
  });

  return {
    async show() {
      shown = true;
      canvas.hidden = false;
      loaded ??= load().catch(err => { console.error('Impacts data failed to load', err); loaded = null; });
      await loaded;
      if (shown && !frame) loop();
    },
    hide() {
      shown = false;
      canvas.hidden = true;
      filterBar.hidden = true;
      expanded = null;
      closeCard();
      globeEl.style.cursor = '';
      stage = null; browse = true; filter = null; callout = null; calloutCard = false; pendingSel = null; Object.assign(calloutA, anim(0));
      for (const [a, v] of [[dotsA, 0], [chartA, 0], [morphA, 0], [exampleA, 0], [glowA, 0], [circleA, 0]]) Object.assign(a, anim(v));
      for (const k in siteA) siteA[k] = anim(0);
    },
    setStage,
    // Callout beat k of `list` (story impacts.callouts), or none (list empty / k = 0). Waits for the data.
    // The current callout's card ("Source" button under the quote).
    openCallout,
    setCallout(list, k) {
      callout = list?.length ? { list, k } : null;
      if (!callout) calloutA.from = calloutA.to = 0;
      Promise.resolve(loaded).then(applyCallout);
    },
    // Screen position of a site point (story key `impacts.site`), or null.
    siteAt: siteXY,
    // A site's full glow as drawn in drawSite (glowA = 1): screen centre, radius, colour; null if not on screen.
    // Used by twoNights.js to take the glows over (Local firefly ↔ Two measured nights, round 7f).
    siteGlow(key) {
      const s = siteXY(key);
      return s && { x: s.x, y: s.y, r: DOT_SELECTED + 0.1 * Math.min(window.innerWidth, window.innerHeight), colour: siteOf(key).colour };
    },
    // Screen position of the door record in the chart as currently laid out (null if not in the chart).
    doorAt(id) {
      const e = effectsById.get(id);
      if (!e || !effects.length) return null;
      const b = chartBox(window.innerWidth, window.innerHeight);
      return doorXY(e, b, v => b.left + Math.log1p(Math.min(CAP, Math.max(0, v))) / Math.log(CAP + 1) * b.width);
    },
  };
}
