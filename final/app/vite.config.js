// Dev server: serves generated tiles from final/data/derived/radiance/tiles at /tiles/.
// Build: copyData() copies the same files into dist/ at the same paths, so dist/ is a complete static site for
// Netlify (human choice, AI_LOG Experience refinement step 69; was: tiles not bundled, hosting undecided, A4).
// The app reads the tile base URL from VITE_TILE_BASE (default /tiles/v1/).
// Impacts (dev): data/derived/impacts at /impacts/, and the human-approved light_types map
// from pipeline/impacts/maps at /impacts/maps/ (allow-list). Publication hosting undecided.
// Colour (dev): the regional white-share grid from data/derived/colour at /colour/ (allow-list).
// Spectra (dev): the Two measured nights files from data/derived/spectra at /spectra/ (allow-list).
import { defineConfig } from 'vite';
import { createReadStream, existsSync, statSync, cpSync, mkdirSync } from 'node:fs';
import { resolve, normalize, sep, dirname } from 'node:path';

const TILE_ROOT = resolve(__dirname, '../data/derived/radiance/tiles');
const IMPACTS_ROOT = resolve(__dirname, '../data/derived/impacts');
const MAPS_ROOT = resolve(__dirname, '../pipeline/impacts/maps');
const APPROVED_MAPS = ['light_types.csv'];
const COLOUR_ROOT = resolve(__dirname, '../data/derived/colour');
const APPROVED_COLOUR = ['iberia_white_share_grid.json', 'global_white_share_grid.json', 'global_white_share_grid.png',
  'global_white_share_values.png'];  // prototype colour modes (human 2026-10-04)
const SPECTRA_ROOT = resolve(__dirname, '../data/derived/spectra');
const APPROVED_SPECTRA = ['philadelphia.json', 'cherry_springs.json', 'spectra_meta.json',  // human 2026-10-04
  'species_curves.json'];   // Species perceptions (human, AI_LOG Firefly tabs review round 7j)
const TYPES = { '.webp': 'image/webp', '.png': 'image/png', '.json': 'application/json', '.csv': 'text/csv; charset=utf-8' };

// Serves files under root at the request path; 404 for anything outside root or missing.
function sendFrom(root, req, res) {
  const file = normalize(resolve(root, '.' + decodeURIComponent(req.url.split('?')[0])));
  if (!file.startsWith(root + sep) || !existsSync(file) || !statSync(file).isFile()) {
    res.statusCode = 404;
    return res.end();
  }
  res.setHeader('Content-Type', TYPES[file.slice(file.lastIndexOf('.'))] || 'application/octet-stream');
  createReadStream(file).pipe(res);
}

function serveTiles() {
  return {
    name: 'serve-derived-tiles',
    configureServer(server) {
      server.middlewares.use('/tiles', (req, res) => sendFrom(TILE_ROOT, req, res));
      server.middlewares.use('/impacts/maps', (req, res) => {
        if (!APPROVED_MAPS.includes(req.url.split('?')[0].slice(1))) { res.statusCode = 404; return res.end(); }
        sendFrom(MAPS_ROOT, req, res);
      });
      server.middlewares.use('/impacts', (req, res) => sendFrom(IMPACTS_ROOT, req, res));
      server.middlewares.use('/colour', (req, res) => {
        if (!APPROVED_COLOUR.includes(req.url.split('?')[0].slice(1))) { res.statusCode = 404; return res.end(); }
        sendFrom(COLOUR_ROOT, req, res);
      });
      server.middlewares.use('/spectra', (req, res) => {
        if (!APPROVED_SPECTRA.includes(req.url.split('?')[0].slice(1))) { res.statusCode = 404; return res.end(); }
        sendFrom(SPECTRA_ROOT, req, res);
      });
    },
  };
}

// Build only: copy the data the app loads into dist/ at the URL paths above (files unchanged). Lists = the files
// committed to git (.gitignore exceptions), so a local build matches the one Netlify makes from the repo. A missing
// file stops the build. Tile set: v1 (VITE_TILE_BASE default).
const PUBLISH = [
  ['tiles/v1', resolve(TILE_ROOT, 'v1')],
  ...['effects', 'studies', 'study_locations', 'study_highlights', 'spectra_278', 'spectra_299', 'perception_299',
    'owens2018_results', 'kivela2023'].map(f => [`impacts/${f}.json`, resolve(IMPACTS_ROOT, `${f}.json`)]),
  ...APPROVED_MAPS.map(f => [`impacts/maps/${f}`, resolve(MAPS_ROOT, f)]),
  ...['global_white_share_grid.json', 'global_white_share_grid.png', 'global_white_share_values.png']
    .map(f => [`colour/${f}`, resolve(COLOUR_ROOT, f)]),
  ...APPROVED_SPECTRA.map(f => [`spectra/${f}`, resolve(SPECTRA_ROOT, f)]),
];
function copyData() {
  let outDir;
  return {
    name: 'copy-data-to-dist',
    apply: 'build',
    configResolved(c) { outDir = resolve(c.root, c.build.outDir); },
    writeBundle() {
      for (const [to, from] of PUBLISH) {
        if (!existsSync(from)) throw new Error(`copy-data-to-dist: missing ${from}`);
        mkdirSync(dirname(resolve(outDir, to)), { recursive: true });
        cpSync(from, resolve(outDir, to), { recursive: true });
      }
    },
  };
}

export default defineConfig({ plugins: [serveTiles(), copyData()] });
