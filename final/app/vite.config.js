// Dev server: serves generated tiles from final/data/derived/radiance/tiles at /tiles/.
// Tiles are not bundled into dist/; hosting for publication is undecided (A4).
// The app reads the tile base URL from VITE_TILE_BASE (default /tiles/v1/).
// Impacts (dev): data/derived/impacts at /impacts/, and the human-approved light_types map
// from pipeline/impacts/maps at /impacts/maps/ (allow-list). Publication hosting undecided.
// Colour (dev): the regional white-share grid from data/derived/colour at /colour/ (allow-list).
import { defineConfig } from 'vite';
import { createReadStream, existsSync, statSync } from 'node:fs';
import { resolve, normalize, sep } from 'node:path';

const TILE_ROOT = resolve(__dirname, '../data/derived/radiance/tiles');
const IMPACTS_ROOT = resolve(__dirname, '../data/derived/impacts');
const MAPS_ROOT = resolve(__dirname, '../pipeline/impacts/maps');
const APPROVED_MAPS = ['light_types.csv'];
const COLOUR_ROOT = resolve(__dirname, '../data/derived/colour');
const APPROVED_COLOUR = ['iberia_white_share_grid.json', 'global_white_share_grid.json', 'global_white_share_grid.png',
  'global_white_share_values.png'];  // prototype colour modes (human 2026-10-04)
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
    },
  };
}

export default defineConfig({ plugins: [serveTiles()] });
