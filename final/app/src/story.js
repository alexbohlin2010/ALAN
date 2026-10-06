// Story steps: Back/Next buttons and arrow keys move through app/content/story.js.
// Globe controls stay free (human decision A3). The intro is a CSS black overlay (A5a);
// the rest of the UI joins after the lights have faded in.

const escape = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const format = s => escape(s).replace(/\*([^*]+)\*/g, '<em>$1</em>');
const ease = t => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);

const sourceList = sources => {
  const items = (sources || []).map(s =>
    // A source without a url (citation only, e.g. round 7j) is listed as plain text.
    `<li>${s.url ? `<a href="${escape(s.url)}" target="_blank" rel="noopener">${escape(s.label)}</a>` : escape(s.label)}</li>`).join('');
  return items ? `<ul class="sources">${items}</ul>` : '';
};

// `intro` (optional): the ?intro=sunrise prototype scene (introScene.js); without it, the CSS overlay intro runs.
export function startStory({ steps, globe, swipe, onStep, intro, ladder = [] }) {
  const overlay = document.getElementById('intro');
  const introText = overlay.querySelector('.text');
  const card = document.getElementById('card');
  const fact = document.getElementById('fact');
  const counter = document.querySelector('#nav .count');
  const back = document.querySelector('#nav .back');
  const next = document.querySelector('#nav .next');
  let index = -1;
  let timers = [];
  // Ladder marker (content/story.js `ladder`, step `rung`): one label per kind of data, the current one lit, a dot
  // sliding under it between steps. Bottom left above the info button. Test build, 2026-10-05 (AI_LOG "Story review" steps 7–8).
  const rail = Object.assign(document.createElement('nav'), { id: 'ladder', hidden: true });
  rail.setAttribute('aria-label', 'Kind of data');
  rail.innerHTML = ladder.map(r => `<span data-rung="${escape(r.id)}">${escape(r.label)}</span>`).join('') +
    '<i class="mark"></i>';
  document.body.append(rail);
  function placeLadder(step) {
    const on = rail.querySelector(`[data-rung="${step.rung}"]`);
    rail.hidden = !on;
    if (!on) return;
    rail.querySelectorAll('span').forEach(el => el.classList.toggle('on', el === on));
    const mark = rail.querySelector('.mark');
    mark.style.left = `${on.offsetLeft + on.offsetWidth / 2}px`;
  }
  let anim = null;  // running divider animation frame id
  let active = true;  // false while another mode (Impacts) is shown

  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const stopAnim = () => { if (anim) cancelAnimationFrame(anim); anim = null; };

  // Big fact text kept clear of the left menu (human: "that can never happen"; option A "below", AI_LOG colour /
  // design task steps 5-6): the text keeps its place but is pushed down to start FACT_GAP px below the menu's
  // bottom edge whenever they would overlap (re-measured when the menu or the text changes size).
  const FACT_GAP = 24;
  const placeFact = () => {
    fact.style.setProperty('--fact-shift', '0px');
    if (fact.hidden) return;
    const menu = document.getElementById('modes').getBoundingClientRect();
    const box = fact.getBoundingClientRect();
    const clash = box.left < menu.right && box.top < menu.bottom + FACT_GAP;
    fact.style.setProperty('--fact-shift', `${clash ? Math.ceil(menu.bottom + FACT_GAP - box.top) : 0}px`);
  };
  const factObserver = new ResizeObserver(placeFact);
  factObserver.observe(document.getElementById('modes'));
  factObserver.observe(fact);
  window.addEventListener('resize', placeFact);
  const clearAll = () => { timers.forEach(clearTimeout); timers = []; stopAnim(); intro?.stop(); };

  // Glide the divider from its current position to `to` (0..1) over `ms`.
  function glide(to, ms, done) {
    stopAnim();
    const from = swipe.get(), t0 = performance.now();
    const tick = now => {
      const t = Math.min(1, (now - t0) / Math.max(1, ms));
      swipe.set(from + (to - from) * ease(t));
      if (t < 1) anim = requestAnimationFrame(tick); else { anim = null; done?.(); }
    };
    anim = requestAnimationFrame(tick);
  }
  // Viewer grabbing the divider stops any automatic movement.
  document.querySelector('#swipe .handle').addEventListener('pointerdown', stopAnim);

  const lngToFrac = (lat, lng) =>
    Math.min(1, Math.max(0, globe.getScreenCoords(lat, lng).x / window.innerWidth));

  function sweep(step) {
    const s = step.sweep, lat = step.camera.lat;
    glide(1, step.fly ?? 0);  // arrive in the 2015 view
    later(() => glide(lngToFrac(lat, s.east), 400,
      () => glide(lngToFrac(lat, s.west), s.duration)), (step.fly ?? 0) + s.hold);
  }

  function playIntro(step) {
    const t = step.timing;
    document.body.classList.add('arriving');
    document.body.style.setProperty('--ui-in', `${t.uiIn}ms`);
    if (intro) {
      overlay.hidden = false;
      introText.innerHTML = format(step.text);
      intro.play(step, { overlay, text: introText,
        done: () => { overlay.hidden = true; document.body.classList.remove('arriving'); },
        // End of the music: on to the next step without a key (human, AI_LOG Copy editing step 8), if still here.
        end: () => { if (active && steps[index] === step) go(index + 1); } });
      return;
    }
    overlay.style.transition = 'none';
    overlay.style.opacity = 1;
    overlay.hidden = false;
    introText.innerHTML = format(step.text);
    introText.style.transition = `opacity ${t.textIn}ms ease`;
    introText.style.opacity = 0;
    let at = 50;
    later(() => { introText.style.opacity = 1; }, at);
    at += t.textIn + t.hold;
    later(() => {
      introText.style.transition = `opacity ${t.textOut}ms ease`;
      introText.style.opacity = 0;
    }, at);
    at += t.textOut;
    later(() => {
      overlay.style.transition = `opacity ${t.lightsIn}ms ease`;
      overlay.style.opacity = 0;
    }, at);
    at += t.lightsIn;
    later(() => { overlay.hidden = true; document.body.classList.remove('arriving'); }, at);
  }

  function show(step) {
    card.hidden = fact.hidden = true;
    card.classList.remove('revealed');   // `reveal` lines wait for their cue
    if (step.kind === 'intro') return;
    const note = step.note ? `<p class="note">${format(step.note)}</p>` : '';
    if (step.kind === 'fact') {
      // Note and sources sit behind a small "Details & sources" button (pop-up), so the big text
      // stays clear of the left panel (human request, AI_LOG Impacts step 33).
      const extra = note + sourceList(step.sources);
      // `reveal`: the text and these lines are shown one at a time, each on its beat (Two measured nights, main.js
      // onBeat; AI_LOG Firefly flow steps 2 and 4).
      const line = (t, n) => `<p class="big${step.reveal ? ` line${n === 0 ? ' on' : ''}` : ''}">${format(t)}</p>`;
      fact.innerHTML = [step.text, ...(step.reveal || [])].map(line).join('') + (extra
        ? `<button class="more" aria-expanded="false">Details &amp; sources</button><div class="more-body" hidden>${extra}</div>`
        : '');
      fact.querySelector('.more')?.addEventListener('click', () => toggleMore(fact));
      fact.classList.toggle('right', step.side === 'right');   // `side: 'right'` (human, AI_LOG Fireflies step 4)
      fact.hidden = false;
      placeFact();
      return;
    }
    if (step.tagline) {
      // Narrative line on the card; text and sources behind "Details & sources" (human, Light story refinement 2026-10-04).
      card.innerHTML = `${step.title ? `<h2>${escape(step.title)}</h2>` : ''}
        <p class="tagline${step.reveal ? ' lead' : ''}">${format(step.tagline)}</p>
        ${(step.reveal || []).map(r => `<p class="tagline reveal">${format(r)}</p>`).join('')}
        <button class="more" aria-expanded="false">Details &amp; sources</button>
        <div class="more-body" hidden><p>${format(step.text)}</p>${note}${sourceList(step.sources)}</div>`;
      card.querySelector('.more').addEventListener('click', () => toggleMore(card));
      card.hidden = false;
      return;
    }
    card.innerHTML = `${step.title ? `<h2>${escape(step.title)}</h2>` : ''}
      ${step.figure ? `<p class="figure">${format(step.figure)}</p>` : ''}
      ${step.figureNote ? `<p class="figure-note">${format(step.figureNote)}</p>` : ''}
      <p>${format(step.text)}</p>${note}${sourceList(step.sources)}`;
    card.hidden = false;
  }

  function toggleMore(box = fact, open) {
    const btn = box.querySelector('.more'), body = box.querySelector('.more-body');
    if (!btn) return;
    body.hidden = !(open ?? body.hidden);
    btn.setAttribute('aria-expanded', String(!body.hidden));
  }
  window.addEventListener('keydown', e => { if (e.key === 'Escape') { toggleMore(fact, false); toggleMore(card, false); } });
  document.addEventListener('click', e => {
    if (!fact.contains(e.target)) toggleMore(fact, false);
    if (!card.contains(e.target)) toggleMore(card, false);
  });

  function go(i) {
    if (i < 0 || i >= steps.length || i === index) return;
    index = i;
    const step = steps[i];
    clearAll();
    overlay.hidden = true;
    document.body.classList.remove('arriving');
    const keepCamera = intro?.spin(i, steps);   // prototype: globe keeps turning until India
    if (step.muteAudio) intro?.setMuted(true);
    if (step.kind !== 'intro') intro?.humFor(step);   // hum out on Conclusion, back elsewhere
    if (step.kind === 'intro') {
      if (!keepCamera) globe.pointOfView(step.camera, 0);
      playIntro(step);
    } else if (!keepCamera) {
      globe.pointOfView(step.camera, step.fly ?? 0);
    }
    if (step.swipe != null) swipe.set(step.swipe);
    if (step.sweep) sweep(step);
    show(step);
    placeLadder(step);
    counter.textContent = `${i + 1} / ${steps.length}`;
    back.disabled = i === 0;
    next.disabled = i === steps.length - 1;
    onStep?.(i);
  }

  back.addEventListener('click', () => go(index - 1));
  next.addEventListener('click', () => go(index + 1));
  window.addEventListener('keydown', e => {
    if (!active) return;
    if (e.key === 'ArrowRight') go(index + 1);
    else if (e.key === 'ArrowLeft') go(index - 1);
  });
  // Prototype (?intro=sunrise): a Begin button comes first; keys wait for it.
  if (intro) { active = false; intro.begin(() => { active = true; go(0); }); } else go(0);

  // Mode switching (Light / Impacts): pause stops timers and animations and ends the intro;
  // resume shows the current step's text again without moving the camera.
  return {
    go,
    pause() {
      active = false;
      clearAll();
      overlay.hidden = true;
      rail.hidden = true;
      document.body.classList.remove('arriving');
    },
    resume() { active = true; show(steps[index]); placeLadder(steps[index]); },
  };
}
