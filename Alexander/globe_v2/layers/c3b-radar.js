(function () {
  'use strict';

  const MODES = {
    regional: {
      label: 'Regional proximity',
      low: [53, 88, 124],
      high: [255, 132, 91],
    },
    local: {
      label: 'Local brightness',
      low: [43, 92, 122],
      high: [255, 193, 90],
    },
  };

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    })[character]);
  }

  function weighted(points, field) {
    let numerator = 0;
    let denominator = 0;
    for (const point of points) {
      const weight = Math.max(1, Number(point.source_cell_count) || 1);
      numerator += Number(point[field]) * weight;
      denominator += weight;
    }
    return denominator ? numerator / denominator : 0;
  }

  function summarize(bin) {
    const points = bin.points || [];
    const center = bin.center || {
      lat: weighted(points, 'latitude'),
      lng: weighted(points, 'longitude'),
    };
    const sourceCells = points.reduce((total, point) => total + Number(point.source_cell_count || 1), 0);
    return {
      id: `hex-${Number(center.lat).toFixed(3)}-${Number(center.lng).toFixed(3)}`,
      latitude: Number(center.lat),
      longitude: Number(center.lng),
      display_coordinate_count: points.length,
      source_cell_count: sourceCells,
      mean_vir: weighted(points, 'mean_vir'),
      density_percentile: weighted(points, 'density_percentile'),
      alan_ratio: weighted(points, 'alan_ratio'),
      distance_bright_km: weighted(points, 'distance_bright_km'),
      distance_radar_km: weighted(points, 'distance_radar_km'),
      distance_atlantic_km: weighted(points, 'distance_atlantic_km'),
      deciduous_cover: weighted(points, 'deciduous_cover'),
      developed_cover: weighted(points, 'developed_cover'),
      regional_proximity: weighted(points, 'regional_proximity'),
      local_brightness: weighted(points, 'local_brightness'),
      source_ids: points.map(point => point.id),
    };
  }

  function interpolateColor(low, high, t, density, selected) {
    const value = Math.max(0, Math.min(1, t));
    const luminosity = 0.48 + 0.52 * Math.sqrt(Math.max(0, Math.min(1, density)));
    const boost = selected ? 1.18 : 1;
    const rgb = low.map((channel, index) => Math.min(255, Math.round(
      (channel + (high[index] - channel) * value) * luminosity * boost
    )));
    return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
  }

  function label(bin, mode) {
    const summary = summarize(bin);
    const modeLine = mode === 'local'
      ? `2014 ALAN ratio ${summary.alan_ratio.toFixed(2)}× natural sky brightness`
      : `${summary.distance_bright_km.toFixed(0)} km from a ≥5× bright source`;
    return `<div class="radar-tip"><b>Radar stopover-response field</b>` +
      `<span>${escapeHtml(modeLine)}</span>` +
      `<span>VIR proxy ${summary.mean_vir.toFixed(2)} cm²/ha · ${Math.round(summary.density_percentile * 100)}th display percentile</span>` +
      `<span>${summary.source_cell_count.toLocaleString()} source cells · ${summary.display_coordinate_count.toLocaleString()} approximate coordinates</span>` +
      `<small>Aggregated community response, not an individual flight route.</small></div>`;
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`C3B radar data failed to load: ${response.status}`);
    return response.json();
  }

  function create(globe, payload, onSelect) {
    const state = {
      mode: 'regional',
      visible: false,
      selectedIds: new Set(),
    };

    function binValue(bin) {
      const summary = summarize(bin);
      return state.mode === 'local' ? summary.local_brightness : summary.regional_proximity;
    }

    function isSelected(bin) {
      return state.selectedIds.size > 0 && bin.points.some(point => state.selectedIds.has(point.id));
    }

    function paintTop(bin) {
      const palette = MODES[state.mode];
      const summary = summarize(bin);
      return interpolateColor(
        palette.low,
        palette.high,
        binValue(bin),
        summary.density_percentile,
        isSelected(bin)
      );
    }

    function paintSide(bin) {
      const palette = MODES[state.mode];
      const summary = summarize(bin);
      return interpolateColor(
        palette.low.map(channel => channel * 0.55),
        palette.high.map(channel => channel * 0.55),
        binValue(bin),
        summary.density_percentile,
        isSelected(bin)
      );
    }

    globe
      .hexBinPointLat('latitude')
      .hexBinPointLng('longitude')
      .hexBinPointWeight(() => 1)
      .hexBinResolution(Number(payload.meta.display_hex_h3_resolution || 5))
      .hexBinMerge(false)
      .hexMargin(0.12)
      .hexAltitude(bin => 0.004 + 0.052 * Math.pow(summarize(bin).density_percentile, 1.25))
      .hexTopColor(paintTop)
      .hexSideColor(paintSide)
      .hexTransitionDuration(450)
      .hexLabel(bin => label(bin, state.mode))
      .onHexClick(bin => onSelect(summarize(bin), true));

    function render() {
      globe
        .hexTopColor(paintTop)
        .hexSideColor(paintSide)
        .hexLabel(bin => label(bin, state.mode))
        .hexBinPointsData(state.visible ? payload.cells : []);
    }

    return {
      modes: MODES,
      show() {
        state.visible = true;
        render();
      },
      hide() {
        state.visible = false;
        state.selectedIds.clear();
        render();
      },
      setMode(mode) {
        state.mode = MODES[mode] ? mode : 'regional';
        render();
      },
      select(selection) {
        state.selectedIds = new Set(selection?.source_ids || (selection?.id ? [selection.id] : []));
        render();
      },
      defaultSelection() {
        return payload.cells
          .filter(cell => Number(cell.distance_bright_km) <= 50)
          .sort((a, b) => Number(b.density_percentile) - Number(a.density_percentile))[0] || payload.cells[0];
      },
    };
  }

  window.C3BRadarLayer = { MODES, create, load, summarize };
})();
