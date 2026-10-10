# ALAN app: run it locally

How to run the web app in `final/app` on your own computer. How this project is worked on (rules for AI agents, the log,
handoffs) is in [RULES.md](RULES.md) and [AI_LOG.md](AI_LOG.md).

## Requirements

- **Git**
- **Node.js 20.19 or newer** (or 22.12+; Vite 8 needs one of these). Check with `node -v`. Install from
  [nodejs.org](https://nodejs.org) if needed.
- A desktop browser with WebGL (recent Chrome, Safari, Firefox or Edge).
- About 300 MB of disk space for the globe tiles in the repo.

Python and the scripts in `pipeline/` are **not** needed to run the app. Everything the app reads is already committed.

## Run

```bash
git clone https://github.com/alexbohlin2010/ALAN.git
cd ALAN/final/app
npm install
npm run dev
```

Open the address it prints, normally **http://localhost:5173**. Click **Begin** to start (with audio). Use the arrows
at the bottom right, the arrow keys, or the menu on the left to move through the story.

Stop the server with `Ctrl+C` in the terminal.

If port 5173 is taken, Vite picks the next free port (5174, …) and prints it. To pick one yourself:

```bash
npm run dev -- --port 5180
```

## What the dev server serves

The app's code and its small assets (audio, photos) are in `app/`. The data comes from outside `app/`, served by a small
plugin in [app/vite.config.js](app/vite.config.js):

| URL path | Folder in `final/` | What |
|---|---|---|
| `/tiles/` | `data/derived/radiance/tiles/` | globe night-light tiles (default set `v1`) |
| `/impacts/` | `data/derived/impacts/` | studies and effects shown on the chart and globe |
| `/impacts/maps/` | `pipeline/impacts/maps/` | `light_types.csv` only |
| `/colour/` | `data/derived/colour/` | the white-share grids only |
| `/spectra/` | `data/derived/spectra/` | the Spectra / Perception files only |

To use another tile set, set `VITE_TILE_BASE` (for example `/tiles/v2/`). This needs the v2 tiles on disk, and they
are not in git:

```bash
VITE_TILE_BASE=/tiles/v2/ npm run dev
```

## Production build

```bash
npm run build      # writes app/dist/: the app plus the data above, about 290 MB and 20,400 files
npm run preview    # serves dist/ at http://localhost:4173 to check it
```

`dist/` is a complete static site: the build copies the files in the table above into it at the same paths (tile set
v1 only). Upload it to any static web host.

## Deploy on Netlify

The site is set up for [Netlify](https://www.netlify.com). The settings are in [app/netlify.toml](app/netlify.toml).

1. Push the repo to GitHub.
2. On Netlify: **Add new site → Import an existing project → GitHub**, then pick the `ALAN` repository.
3. Set **Base directory** to `final/app`. The build command (`npm run build`), publish directory (`dist`) and Node
   version come from `netlify.toml`.
4. Click **Deploy**. The first deploy uploads about 290 MB, so it takes a few minutes.

After that, every push to `main` rebuilds and republishes the site. Netlify gives an address like
`https://<name>.netlify.app`; you can rename it, or add your own domain, under **Domain management**.

## Troubleshooting

- **The globe stays black or tiles are missing:** check that `final/data/derived/radiance/tiles/v1/` exists (it is part
  of the clone), and look for 404 errors in the browser console.
- **No sound:** click **Begin**, and check the speaker button at the top right and your system volume.
- **`npm install` fails or Vite won't start:** check `node -v` against the requirement above.
- **Working with Claude Code:** the launch configuration is named `alan-final-app` (port 5173). If another session
  already runs a server on 5173, open http://localhost:5173 in a new tab instead of starting a second one.
