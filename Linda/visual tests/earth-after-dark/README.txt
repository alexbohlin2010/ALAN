Earth After Dark — offline copy
================================

Contents
  index.html          the page
  cities.json         the 50-city time series
  mid/2012–2024.webp  4096px globe textures (used for playback)
  hi/2012–2024.webp   8192px globe textures (used when you sit on one year)
  vendor/             globe.gl 2.46.2 + the Archivo / IBM Plex Mono webfonts,
                      both of which the live page loaded from a CDN

Everything is local, so this works with no internet connection.

How to open it
--------------
Run it through a local web server. Double-clicking index.html will show the
layout but the globe will stay dark: browsers treat each file:// document as
its own origin, which blocks both the cities.json fetch and the upload of the
texture images into WebGL. Any static server fixes it.

  macOS / Linux — open Terminal, then:
      cd /path/to/this/folder
      python3 -m http.server 8000
  then visit  http://localhost:8000  in your browser.

  Ctrl-C in the Terminal window stops the server when you're done.

Notes
-----
Two lines of index.html differ from the published version: the <link> to
Google Fonts and the <script> for globe.gl now point at vendor/ instead of
the CDN. Nothing else was changed.

About 380 MB of GPU memory gets used once all 13 years are uploaded; the page
skips that preload on machines reporting under 8 GB of RAM and falls back to
swapping textures per year.
