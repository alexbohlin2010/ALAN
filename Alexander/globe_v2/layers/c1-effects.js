(function () {
  const ALL = 'All processes';
  const clamp = value => Math.max(0, Math.min(1, value));
  const ease = value => 1 - Math.pow(1 - clamp(value), 3);

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[char]);
  }

  function hashUnit(text) {
    let hash = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0) / 4294967295;
  }

  function effectLabel(effect) {
    const species = effect.species || effect.order || effect.class || effect.phylum || 'Taxon not specified';
    const context = effect.study_type === 'Laboratory'
      ? 'Lab study · location identifies where the experiment was conducted, not environmental exposure.'
      : effect.study_type === 'Field'
        ? 'Field study · VIIRS is present-day environmental context, not a causal exposure estimate.'
        : `${effect.study_type || 'Study context unknown'} · geographic context only.`;
    return `<div class="effect-tip"><b>${escapeHtml(effect.measured_effect)}</b>` +
      `<span>${escapeHtml(species)} · ${escapeHtml(effect.category)}</span>` +
      `<span>Hedges g ${Number(effect.effect_size).toFixed(2)} · |g| ${Number(effect.effect_abs).toFixed(2)}</span>` +
      `<span>${escapeHtml(effect.location || 'Location unavailable')}</span>` +
      `<small>${escapeHtml(context)}</small></div>`;
  }

  function anchorLabel(group) {
    const categories = Object.entries(group.category_counts || {})
      .sort((a, b) => b[1] - a[1])
      .map(([name, count]) => `${name} ${count}`)
      .join(' · ');
    const geography = group.point_eligible
      ? `${group.precision.replaceAll('_', ' ')} · reviewed point placement`
      : group.geometry_type === 'country_region'
        ? 'Country-level context · not an exact study site'
        : 'Regional context · halo shows location uncertainty';
    return `<div class="effect-tip"><b>${escapeHtml(group.label)}</b>` +
      `<span>Study ${escapeHtml(group.study_id)} · ${escapeHtml(group.publication_year || 'year unavailable')} · ${escapeHtml(group.study_type)}</span>` +
      `<span>${group.effect_count.toLocaleString()} effect records · ${escapeHtml(categories)}</span>` +
      `<small>${escapeHtml(geography)}. Select to expand this study's records.</small></div>`;
  }

  function create(canvas, tooltip, onSelect) {
    const context = canvas.getContext('2d');
    const state = {
      payload: null,
      filter: ALL,
      selectedId: null,
      selectedGroupId: null,
      points: [],
      keyboardIndex: -1,
      progress: 0,
      mode: 'effect',
      projection: null,
      transitionFrame: 0,
      continuousFrame: 0,
      pointerStart: null,
      effectsById: new Map(),
      groupsById: new Map(),
      anchorsByGroupId: new Map(),
      flattenedAnchors: [],
    };

    function scaleX(value, left, width) {
      const capped = Math.min(10, Math.max(0, Number(value) || 0));
      return left + Math.log1p(capped) / Math.log(11) * width;
    }

    function visibleEffects() {
      if (!state.payload) return [];
      return state.filter === ALL
        ? state.payload.effects
        : state.payload.effects.filter(effect => effect.category === state.filter);
    }

    function groupEffects(group) {
      return group.effect_ids
        .map(id => state.effectsById.get(id))
        .filter(effect => effect && (state.filter === ALL || effect.category === state.filter));
    }

    function groupIsActive(group) {
      return state.filter === ALL || Boolean(group.category_counts?.[state.filter]);
    }

    function chartGeometry(rect) {
      const compact = rect.width < 680;
      const left = compact ? 88 : 126;
      const right = compact ? 18 : 34;
      const top = compact ? 166 : 184;
      const bottom = compact ? 48 : 62;
      return {
        compact, left, right, top, bottom,
        plotWidth: Math.max(120, rect.width - left - right),
        plotHeight: Math.max(118, rect.height - top - bottom),
      };
    }

    function effectPosition(effect, geometry, categoryIndex) {
      const lane = categoryIndex.get(effect.category);
      const laneHeight = geometry.plotHeight / state.payload.categories.length;
      return {
        x: scaleX(effect.effect_abs_display, geometry.left, geometry.plotWidth),
        y: geometry.top + laneHeight * (lane + 0.5) + (hashUnit(effect.effect_id) - 0.5) * laneHeight * 0.7,
      };
    }

    function drawAxes(geometry, alpha) {
      if (alpha <= 0.001) return;
      const categories = state.payload.categories;
      const laneHeight = geometry.plotHeight / categories.length;
      context.save();
      context.globalAlpha = alpha;
      context.font = `${geometry.compact ? 9 : 10}px "IBM Plex Mono", monospace`;
      context.textBaseline = 'middle';
      context.lineWidth = 1;
      categories.forEach((category, lane) => {
        const y = geometry.top + laneHeight * (lane + 0.5);
        context.strokeStyle = 'rgba(90,104,125,.18)';
        context.beginPath();
        context.moveTo(geometry.left, y);
        context.lineTo(geometry.left + geometry.plotWidth, y);
        context.stroke();
        context.fillStyle = state.filter === ALL || state.filter === category.category
          ? category.color
          : 'rgba(125,138,158,.38)';
        context.textAlign = 'right';
        const label = geometry.compact && category.category === 'Life history' ? 'Life hist.' : category.category;
        context.fillText(label.toUpperCase(), geometry.left - 11, y);
      });

      context.textAlign = 'center';
      context.textBaseline = 'top';
      [0, 0.2, 0.5, 1, 2, 5, 10].forEach(value => {
        const x = scaleX(value, geometry.left, geometry.plotWidth);
        context.strokeStyle = 'rgba(90,104,125,.16)';
        context.beginPath();
        context.moveTo(x, geometry.top);
        context.lineTo(x, geometry.top + geometry.plotHeight);
        context.stroke();
        context.fillStyle = 'rgba(149,161,178,.8)';
        context.fillText(value === 10 ? '10+' : String(value), x, geometry.top + geometry.plotHeight + 12);
      });
      context.fillStyle = 'rgba(149,161,178,.72)';
      context.fillText(
        'ABSOLUTE HEDGES g · LOG SCALE · VALUES ABOVE 10 SHARE THE EDGE',
        geometry.left + geometry.plotWidth / 2,
        geometry.top + geometry.plotHeight + 35
      );
      context.restore();
    }

    function drawEffectPoint(effect, x, y, radius, color, alpha, selected, mapForm) {
      if (alpha <= 0.003) return;
      const laboratory = effect.study_type === 'Laboratory';
      const field = effect.study_type === 'Field';
      context.save();
      context.globalAlpha = alpha;
      context.lineWidth = selected ? 1.8 : mapForm ? 1.3 : 0.8;
      context.strokeStyle = selected ? '#ffffff' : color;
      context.fillStyle = color;
      context.beginPath();
      context.arc(x, y, selected ? Math.max(radius, 5.3) : radius, 0, Math.PI * 2);
      if (!mapForm || field) context.fill();
      if (selected || mapForm || laboratory || effect.effect_abs_over_cap) context.stroke();
      context.restore();
    }

    function projectedAnchor(flattened) {
      if (!state.projection) return null;
      const target = state.projection(flattened);
      if (!target) return null;
      const group = flattened.group;
      const exact = group.point_eligible;
      const angle = hashUnit(`${group.anchor_group_id}-offset`) * Math.PI * 2;
      const radius = exact
        ? hashUnit(`${group.anchor_group_id}-radius`) * 5
        : 2 + hashUnit(`${group.anchor_group_id}-radius`) * 7;
      return {
        x: target.x + Math.cos(angle) * radius,
        y: target.y + Math.sin(angle) * radius,
        visible: target.visible,
      };
    }

    function drawAnchor(flattened, colorByCategory, alphaScale) {
      const group = flattened.group;
      const target = projectedAnchor(flattened);
      if (!target || !target.visible) return;
      const active = groupIsActive(group);
      const selected = group.anchor_group_id === state.selectedGroupId;
      const color = colorByCategory.get(group.dominant_category) || '#f4f6fa';
      const coreRadius = selected ? 5.7 : 3.5;
      const contextRadius = group.geometry_type === 'country_region' ? 12 : 8;
      const alpha = (selected ? 1 : active ? 0.72 : 0.08) * alphaScale;

      context.save();
      context.globalAlpha = alpha;
      if (!group.point_eligible) {
        context.fillStyle = color;
        context.globalAlpha = alpha * 0.055;
        context.beginPath();
        context.arc(target.x, target.y, contextRadius, 0, Math.PI * 2);
        context.fill();
        context.globalAlpha = alpha * 0.5;
        context.strokeStyle = selected ? '#ffffff' : color;
        context.lineWidth = selected ? 1.7 : 1;
        context.setLineDash(group.geometry_type === 'country_region' ? [2, 4] : [4, 3]);
        context.beginPath();
        context.arc(target.x, target.y, contextRadius, 0, Math.PI * 2);
        context.stroke();
        context.setLineDash([]);
      }

      context.globalAlpha = alpha;
      context.strokeStyle = selected ? '#ffffff' : color;
      context.fillStyle = color;
      context.lineWidth = selected ? 2 : 1.5;
      context.beginPath();
      context.arc(target.x, target.y, coreRadius, 0, Math.PI * 2);
      if (group.study_type === 'Field') context.fill();
      context.stroke();
      if (group.study_type === 'Mixed') {
        context.beginPath();
        context.moveTo(target.x - coreRadius * 0.7, target.y);
        context.lineTo(target.x + coreRadius * 0.7, target.y);
        context.stroke();
      }
      context.restore();

      state.points.push({
        kind: 'anchor', group, flattened, x: target.x, y: target.y, active,
        visible: true, radius: Math.max(9, group.point_eligible ? coreRadius + 4 : contextRadius),
      });
    }

    function drawExpandedEffects(colorByCategory) {
      const group = state.groupsById.get(state.selectedGroupId);
      if (!group) return;
      const anchor = state.anchorsByGroupId.get(group.anchor_group_id)?.[0];
      if (!anchor) return;
      const target = projectedAnchor(anchor);
      if (!target || !target.visible) return;
      const effects = groupEffects(group);
      if (!effects.length) return;
      const spread = Math.min(46, 18 + Math.sqrt(effects.length) * 2.25);
      effects.forEach((effect, index) => {
        const angle = index * 2.399963229728653 + hashUnit(effect.effect_id) * 0.5;
        const distance = 12 + Math.sqrt((index + 0.5) / effects.length) * spread;
        const x = target.x + Math.cos(angle) * distance;
        const y = target.y + Math.sin(angle) * distance;
        const color = colorByCategory.get(effect.category) || '#f4f6fa';
        const selected = effect.effect_id === state.selectedId;
        const radius = selected ? 4.8 : Math.min(3.6, 1.6 + Math.sqrt(Number(effect.effect_abs_display) || 0) * 0.45);
        context.save();
        context.strokeStyle = 'rgba(244,246,250,.16)';
        context.lineWidth = 0.7;
        context.beginPath();
        context.moveTo(target.x, target.y);
        context.lineTo(x, y);
        context.stroke();
        context.restore();
        drawEffectPoint(effect, x, y, radius, color, selected ? 1 : 0.88, selected, true);
        state.points.push({kind:'effect', effect, x, y, active:true, visible:true, radius:7});
      });
    }

    function drawMap(colorByCategory, alphaScale = 1) {
      const contextAnchors = state.flattenedAnchors.filter(item => !item.group.point_eligible);
      const exactAnchors = state.flattenedAnchors.filter(item => item.group.point_eligible);
      contextAnchors.forEach(anchor => drawAnchor(anchor, colorByCategory, alphaScale));
      exactAnchors.forEach(anchor => drawAnchor(anchor, colorByCategory, alphaScale));
      if (alphaScale > 0.98) drawExpandedEffects(colorByCategory);
    }

    function transitionTarget(effect) {
      const group = state.groupsById.get(effect.anchor_group_id);
      if (!group) return null;
      const anchors = state.anchorsByGroupId.get(group.anchor_group_id) || [];
      if (!anchors.length) return null;
      const targetAnchor = anchors[Math.floor(hashUnit(effect.effect_id) * anchors.length) % anchors.length];
      return projectedAnchor(targetAnchor);
    }

    function draw() {
      if (!state.payload) return;
      const rect = canvas.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const pixelWidth = Math.round(rect.width * dpr);
      const pixelHeight = Math.round(rect.height * dpr);
      if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
        canvas.width = pixelWidth;
        canvas.height = pixelHeight;
      }
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      context.clearRect(0, 0, rect.width, rect.height);

      const geometry = chartGeometry(rect);
      const categories = state.payload.categories;
      const categoryIndex = new Map(categories.map((category, index) => [category.category, index]));
      const colorByCategory = new Map(categories.map(category => [category.category, category.color]));
      drawAxes(geometry, clamp(1 - state.progress * 1.7));
      state.points = [];

      if (state.progress >= 0.999) {
        drawMap(colorByCategory, 1);
        return;
      }

      for (const effect of state.payload.effects) {
        const start = effectPosition(effect, geometry, categoryIndex);
        const target = effect.geo_context_available ? transitionTarget(effect) : null;
        const delay = hashUnit(`${effect.effect_id}-transition`) * 0.18;
        const localProgress = ease((state.progress - delay) / (1 - delay));
        const active = state.filter === ALL || state.filter === effect.category;
        const selected = effect.effect_id === state.selectedId;
        const color = colorByCategory.get(effect.category) || '#f4f6fa';

        if (!target) {
          const alpha = (selected ? 1 : active ? 0.72 : 0.055) * clamp(1 - state.progress / 0.72);
          drawEffectPoint(effect, start.x, start.y + state.progress * 18, selected ? 4.2 : 1.75, color, alpha, selected, false);
          if (alpha > 0.05) state.points.push({kind:'effect', effect, x:start.x, y:start.y, active, visible:true, radius:6});
          continue;
        }

        const dx = target.x - start.x;
        const dy = target.y - start.y;
        const length = Math.max(1, Math.hypot(dx, dy));
        const arc = Math.sin(Math.PI * localProgress) * (18 + hashUnit(effect.effect_id) * 34);
        const direction = hashUnit(`${effect.effect_id}-side`) > 0.5 ? 1 : -1;
        const x = start.x + dx * localProgress + (-dy / length) * arc * direction;
        const y = start.y + dy * localProgress + (dx / length) * arc * direction;
        const visibility = target.visible ? 1 : clamp(1 - localProgress * 1.7);
        const alpha = (selected ? 1 : active ? 0.82 : 0.06) * visibility * clamp(1 - localProgress * 0.35);
        drawEffectPoint(effect, x, y, selected ? 4.2 : 1.75, color, alpha, selected, localProgress > 0.55);
      }

      const anchorAlpha = ease((state.progress - 0.76) / 0.24);
      if (anchorAlpha > 0.002) drawMap(colorByCategory, anchorAlpha);
    }

    function nearestAt(x, y) {
      let best = null;
      for (const point of state.points) {
        if (!point.active || !point.visible) continue;
        const current = (point.x - x) ** 2 + (point.y - y) ** 2;
        const threshold = point.radius ** 2;
        if (current <= threshold && (!best || current < best.distance || point.kind === 'effect')) {
          best = {...point, distance:current};
        }
      }
      return best;
    }

    function showTooltip(point, clientX, clientY) {
      if (!point) {
        tooltip.hidden = true;
        return;
      }
      tooltip.innerHTML = point.kind === 'anchor' ? anchorLabel(point.group) : effectLabel(point.effect);
      tooltip.hidden = false;
      const bounds = canvas.parentElement.getBoundingClientRect();
      tooltip.style.left = `${Math.min(bounds.width - 278, Math.max(12, clientX - bounds.left + 14))}px`;
      tooltip.style.top = `${Math.min(bounds.height - 142, Math.max(12, clientY - bounds.top + 14))}px`;
    }

    function eventPoint(event) {
      const rect = canvas.getBoundingClientRect();
      return {x:event.clientX - rect.left, y:event.clientY - rect.top};
    }

    function choosePoint(point) {
      if (!point) return;
      if (point.kind === 'effect') {
        onSelect(point.effect);
        return;
      }
      state.selectedGroupId = point.group.anchor_group_id;
      const effect = groupEffects(point.group)[0];
      if (effect) onSelect(effect);
      draw();
    }

    canvas.addEventListener('pointermove', event => {
      if (state.progress > 0.5) return;
      const position = eventPoint(event);
      showTooltip(nearestAt(position.x, position.y), event.clientX, event.clientY);
    });
    canvas.addEventListener('pointerleave', () => { tooltip.hidden = true; });
    canvas.addEventListener('click', event => {
      if (state.progress > 0.5) return;
      const position = eventPoint(event);
      choosePoint(nearestAt(position.x, position.y));
    });
    canvas.addEventListener('keydown', event => {
      if (!['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
      const items = state.progress > 0.5
        ? state.payload.anchor_groups.filter(groupIsActive)
        : visibleEffects();
      if (!items.length) return;
      state.keyboardIndex = (state.keyboardIndex + (event.key === 'ArrowRight' ? 1 : -1) + items.length) % items.length;
      if (state.progress > 0.5) {
        const group = items[state.keyboardIndex];
        const effect = groupEffects(group)[0];
        if (effect) onSelect(effect);
      } else {
        onSelect(items[state.keyboardIndex]);
      }
      event.preventDefault();
    });

    function stopContinuous() {
      if (state.continuousFrame) cancelAnimationFrame(state.continuousFrame);
      state.continuousFrame = 0;
    }

    function startContinuous() {
      stopContinuous();
      const frame = () => {
        if (state.mode !== 'map' || state.transitionFrame) {
          state.continuousFrame = 0;
          return;
        }
        draw();
        state.continuousFrame = requestAnimationFrame(frame);
      };
      state.continuousFrame = requestAnimationFrame(frame);
    }

    function attachMapSurface(surface) {
      surface.addEventListener('pointerdown', event => {
        if (state.progress < 0.5) return;
        state.pointerStart = {x:event.clientX,y:event.clientY};
      }, true);
      surface.addEventListener('pointermove', event => {
        if (state.progress < 0.5 || event.target.closest?.('#sceneSwitch,button,input')) return;
        const position = eventPoint(event);
        showTooltip(nearestAt(position.x, position.y), event.clientX, event.clientY);
      }, true);
      surface.addEventListener('pointerleave', () => {
        if (state.progress >= 0.5) tooltip.hidden = true;
      });
      surface.addEventListener('click', event => {
        if (state.progress < 0.5 || event.target.closest?.('#sceneSwitch,button,input')) return;
        if (state.pointerStart && Math.hypot(event.clientX-state.pointerStart.x,event.clientY-state.pointerStart.y)>5) return;
        const position = eventPoint(event);
        choosePoint(nearestAt(position.x, position.y));
      }, true);
    }

    function setMode(mode) {
      if (state.transitionFrame) cancelAnimationFrame(state.transitionFrame);
      state.transitionFrame = 0;
      state.mode = mode === 'map' ? 'map' : 'effect';
      state.progress = state.mode === 'map' ? 1 : 0;
      tooltip.hidden = true;
      draw();
      if (state.mode === 'map') startContinuous(); else stopContinuous();
    }

    function transitionTo(mode, duration = 1800) {
      if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
        setMode(mode);
        return;
      }
      if (state.transitionFrame) cancelAnimationFrame(state.transitionFrame);
      stopContinuous();
      const target = mode === 'map' ? 1 : 0;
      const from = state.progress;
      const started = performance.now();
      state.mode = 'transition';
      const frame = now => {
        const elapsed = clamp((now - started) / duration);
        const eased = elapsed < 0.5 ? 4*elapsed*elapsed*elapsed : 1-Math.pow(-2*elapsed+2,3)/2;
        state.progress = from + (target - from) * eased;
        draw();
        if (elapsed < 1) {
          state.transitionFrame = requestAnimationFrame(frame);
        } else {
          state.transitionFrame = 0;
          state.mode = target ? 'map' : 'effect';
          state.progress = target;
          draw();
          if (state.mode === 'map') startContinuous();
        }
      };
      state.transitionFrame = requestAnimationFrame(frame);
    }

    return {
      setData(payload) {
        state.payload = payload;
        state.effectsById = new Map(payload.effects.map(effect => [effect.effect_id, effect]));
        state.groupsById = new Map(payload.anchor_groups.map(group => [group.anchor_group_id, group]));
        state.flattenedAnchors = payload.anchor_groups.flatMap(group =>
          group.anchors.map(anchor => ({...anchor, group}))
        );
        state.anchorsByGroupId = new Map(payload.anchor_groups.map(group => [
          group.anchor_group_id,
          state.flattenedAnchors.filter(anchor => anchor.group.anchor_group_id === group.anchor_group_id),
        ]));
        draw();
      },
      setProjection(project) {
        state.projection = project;
        draw();
      },
      attachMapSurface,
      setFilter(category) {
        state.filter = category || ALL;
        state.keyboardIndex = -1;
        draw();
      },
      select(effect) {
        state.selectedId = effect ? effect.effect_id : null;
        state.selectedGroupId = effect?.anchor_group_id || null;
        draw();
      },
      setMode,
      transitionTo,
      resize: draw,
      allLabel: ALL,
    };
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`C1 effect data failed to load: ${response.status}`);
    return response.json();
  }

  window.C1EffectsLayer = { create, load, effectLabel, anchorLabel, allLabel: ALL };
})();
