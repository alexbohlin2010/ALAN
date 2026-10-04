// Story steps: Back/Next buttons and arrow keys move through app/content/story.js.
// Globe controls stay free (human decision A3). The intro is a CSS black overlay (A5a);
// the rest of the UI joins after the lights have faded in.

const escape = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const format = s => escape(s).replace(/\*([^*]+)\*/g, '<em>$1</em>');
const ease = t => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);

const sourceList = sources => {
  const items = (sources || []).map(s =>
    `<li><a href="${escape(s.url)}" target="_blank" rel="noopener">${escape(s.label)}</a></li>`).join('');
  return items ? `<ul class="sources">${items}</ul>` : '';
};

// `intro` (optional): the ?intro=sunrise prototype scene (introScene.js); without it, the CSS overlay intro runs.
export function startStory({ steps, globe, swipe, onStep, intro }) {
  const overlay = document.getElementById('intro');
  const introText = overlay.querySelector('.text');
  const card = document.getElementById('card');
  const fact = document.getElementById('fact');
  const counter = document.querySelector('#nav .count');
  const back = document.querySelector('#nav .back');
  const next = document.querySelector('#nav .next');
  let index = -1;
  let timers = [];
  let anim = null;  // running divider animation frame id
  let active = true;  // false while another mode (Impacts) is shown

  const later = (fn, ms) => timers.push(setTimeout(fn, ms));
  const stopAnim = () => { if (anim) cancelAnimationFrame(anim); anim = null; };
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
        done: () => { overlay.hidden = true; document.body.classList.remove('arriving'); } });
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
    if (step.kind === 'intro') return;
    const note = step.note ? `<p class="note">${format(step.note)}</p>` : '';
    if (step.kind === 'fact') {
      // Note and sources sit behind a small "Details & sources" button (pop-up), so the big text
      // stays clear of the left panel (human request, AI_LOG Impacts step 33).
      const extra = note + sourceList(step.sources);
      fact.innerHTML = `<p class="big">${format(step.text)}</p>` + (extra
        ? `<button class="more" aria-expanded="false">Details &amp; sources</button><div class="more-body" hidden>${extra}</div>`
        : '');
      fact.querySelector('.more')?.addEventListener('click', () => toggleMore(fact));
      fact.hidden = false;
      return;
    }
    if (step.tagline) {
      // Narrative line on the card; text and sources behind "Details & sources" (human, Light story refinement 2026-10-04).
      card.innerHTML = `${step.title ? `<h2>${escape(step.title)}</h2>` : ''}
        <p class="tagline">${format(step.tagline)}</p>
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
    if (step.kind === 'intro') {
      if (!keepCamera) globe.pointOfView(step.camera, 0);
      playIntro(step);
    } else if (!keepCamera) {
      globe.pointOfView(step.camera, step.fly ?? 0);
    }
    if (step.swipe != null) swipe.set(step.swipe);
    if (step.sweep) sweep(step);
    show(step);
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
      document.body.classList.remove('arriving');
    },
    resume() { active = true; show(steps[index]); },
  };
}
