(function () {
  'use strict';

  const ALL = 'All species';
  const COLORS = {
    'Eastern Whip-poor-will': '#79ddff',
    'American Robin': '#ffc15a',
  };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[character]);
  }

  function brightnessColor(hex, brightness, emphasis) {
    const red = Number.parseInt(hex.slice(1, 3), 16);
    const green = Number.parseInt(hex.slice(3, 5), 16);
    const blue = Number.parseInt(hex.slice(5, 7), 16);
    const strength = Math.min(1, (0.45 + Math.sqrt(Math.max(0, brightness)) * 0.55) * emphasis);
    return `rgb(${Math.round(red * strength)},${Math.round(green * strength)},${Math.round(blue * strength)})`;
  }

  function segmentLabel(segment) {
    const quality = segment.sensor_type === 'Argos'
      ? 'Argos · lower spatial precision · dashed route'
      : 'GPS · finer spatial precision · solid route';
    const brightness = Math.round(segment.brightness * 100);
    return `<div class="migration-tip"><b>${escapeHtml(segment.species)}</b>` +
      `<span>${escapeHtml(segment.individual_id)} · ${escapeHtml(quality)}</span>` +
      `<span>${escapeHtml(segment.start_timestamp.slice(0, 10))} → ${escapeHtml(segment.end_timestamp.slice(0, 10))}</span>` +
      `<span>2024 VIIRS relative display brightness ${brightness}%</span>` +
      `<small>Geographic overlap only — not evidence that light caused this route.</small></div>`;
  }

  function prepare(payload) {
    const pointsBySegment = new Map();
    for (const point of payload.points || []) {
      if (!pointsBySegment.has(point.segment_id)) pointsBySegment.set(point.segment_id, []);
      pointsBySegment.get(point.segment_id).push(point);
    }
    const segments = [];
    for (const [segmentId, points] of pointsBySegment) {
      points.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
      for (let index = 1; index < points.length; index += 1) {
        const start = points[index - 1];
        const end = points[index];
        const brightness = (Number(start.viirs_relative_brightness) + Number(end.viirs_relative_brightness)) / 2;
        segments.push({
          segment_id: segmentId,
          species: end.species,
          individual_id: end.individual_id,
          sensor_type: end.sensor_type,
          start_timestamp: start.timestamp,
          end_timestamp: end.timestamp,
          brightness,
          elevated: Boolean(start.high_relative_brightness || end.high_relative_brightness),
          end_point: end,
          points: [
            {lat: Number(start.latitude), lng: Number(start.longitude), alt: 0.006},
            {lat: Number(end.latitude), lng: Number(end.longitude), alt: 0.006},
          ],
        });
      }
    }
    return segments;
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`C3A migration data failed to load: ${response.status}`);
    return response.json();
  }

  function create(globe, payload, onSelect) {
    const state = {
      payload,
      segments: prepare(payload),
      filter: ALL,
      selectedIndividual: null,
      visible: false,
    };

    globe
      .pathPoints('points')
      .pathPointLat('lat')
      .pathPointLng('lng')
      .pathPointAlt('alt')
      .pathResolution(1)
      .pathTransitionDuration(0)
      .pathLabel(segmentLabel)
      .onPathClick(segment => onSelect(segment.end_point, true));

    function render() {
      if (!state.visible) {
        globe.pathsData([]);
        return;
      }
      const visible = state.filter === ALL
        ? state.segments
        : state.segments.filter(segment => segment.species === state.filter);
      globe
        .pathColor(segment => {
          const selected = !state.selectedIndividual || state.selectedIndividual === `${segment.species}:${segment.individual_id}`;
          const base = COLORS[segment.species] || '#f4f6fa';
          return brightnessColor(base, segment.brightness, selected ? 1 : 0.85);
        })
        .pathStroke(segment => {
          const selected = state.selectedIndividual === `${segment.species}:${segment.individual_id}`;
          return (0.22 + Math.sqrt(Math.max(0, segment.brightness)) * 0.58) * (selected ? 1.28 : 1);
        })
        .pathDashLength(segment => segment.sensor_type === 'Argos' ? 0.28 : 1)
        .pathDashGap(segment => segment.sensor_type === 'Argos' ? 0.14 : 0)
        .pathsData(visible);
    }

    return {
      allLabel: ALL,
      colors: COLORS,
      show() {
        state.visible = true;
        render();
      },
      hide() {
        state.visible = false;
        state.selectedIndividual = null;
        render();
      },
      setFilter(species) {
        state.filter = species || ALL;
        state.selectedIndividual = null;
        render();
      },
      select(point) {
        state.selectedIndividual = point ? `${point.species}:${point.individual_id}` : null;
        render();
      },
      segments: state.segments,
    };
  }

  window.C3AMigrationLayer = { ALL, COLORS, create, load, segmentLabel };
})();
