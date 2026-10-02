(function () {
  'use strict';

  const COLORS = {
    terrestrial: '#b6f36a',
    aquatic: '#72c7ff',
    mixed: '#7ce6cf'
  };

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function placeName(site) {
    return (site.localities && site.localities[0]) ||
      (site.state_provinces && site.state_provinces[0]) ||
      (site.countries && site.countries[0]) ||
      'Night observation site';
  }

  function ecosystemClass(site) {
    const values = new Set((site.ecosystems || []).map(value => String(value).toLowerCase()));
    if (values.has('aquatic') && values.has('terrestrial')) return 'mixed';
    if (values.has('aquatic')) return 'aquatic';
    return 'terrestrial';
  }

  function pulsePeriod(siteId) {
    const tail = String(siteId).replace(/[^0-9a-f]/gi, '').slice(-6);
    const value = Number.parseInt(tail || '0', 16);
    return 2200 + (value % 2200);
  }

  function fadingRing(hex) {
    const red = Number.parseInt(hex.slice(1, 3), 16);
    const green = Number.parseInt(hex.slice(3, 5), 16);
    const blue = Number.parseInt(hex.slice(5, 7), 16);
    return progress => `rgba(${red},${green},${blue},${(0.72 * (1 - progress)).toFixed(3)})`;
  }

  function prepare(payload) {
    const sites = (payload && payload.sites ? payload.sites : []).map(site => {
      const ecosystem = ecosystemClass(site);
      const name = placeName(site);
      return {
        ...site,
        name,
        ecosystem,
        __kind: 'insect-night',
        __color: COLORS[ecosystem],
        __ringColor: fadingRing(COLORS[ecosystem]),
        __pulsePeriod: pulsePeriod(site.site_id)
      };
    });
    sites.sort((a, b) => b.measurement_count - a.measurement_count || a.name.localeCompare(b.name));
    return sites;
  }

  function label(site) {
    const country = (site.countries || []).join(', ');
    const habitat = (site.habitats || []).join(', ') || 'not specified';
    return `<div class="tip insect-tip"><b>${escapeHtml(site.name)}</b>` +
      `<span>${escapeHtml(country)}</span>` +
      `<span>${escapeHtml(site.ecosystem)} · ${escapeHtml(habitat)}</span>` +
      `<small>${site.study_count} source ${site.study_count === 1 ? 'study' : 'studies'} · coverage, not intensity</small></div>`;
  }

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Insect night data failed to load: ${response.status}`);
    return prepare(await response.json());
  }

  window.InsectNightLayer = { COLORS, label, load };
})();
