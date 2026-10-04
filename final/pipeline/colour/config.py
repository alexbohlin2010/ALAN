"""Shared paths and constants for the colour (ISS) pipeline. Paths are relative to final/."""
import socket, sys
from pathlib import Path

# The archive's IPv6 address does not answer from this network (tested 2026-10-03: IPv6
# times out, IPv4 answers in <1 s). Python tries IPv6 first and stalls ~90 s per request,
# so name lookups in this pipeline return IPv4 addresses only.
_getaddrinfo = socket.getaddrinfo
def _ipv4_only(*args, **kwargs):
    return [r for r in _getaddrinfo(*args, **kwargs) if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4_only

FINAL = Path(__file__).resolve().parents[2]
RAW_DIR = FINAL / "data/raw/colour/eol"          # archive responses as fetched (read-only after fetch)
DERIVED = FINAL / "data/derived/colour"

EOL = "https://eol.jsc.nasa.gov/SearchPhotos/"
USER_AGENT = "Mozilla/5.0 (ALAN research; read-only metadata queries)"
REQUEST_PAUSE_S = 1.0  # pause between requests to the archive

# Regions. Box in degrees, EPSG:4326, matched against the archive's listed lat/lon (centre
# point; nadir for uncatalogued records). Chosen with `--pilot <name>` on any script (default iberia).
#   iberia (human, 2026-10-03): the pilot.
#   global (human, 2026-10-03, AI_LOG colour step 28): all longitudes, -56..+60 lat (ISS nadir
#   coverage ends ~+-52 deg; a few degrees margin for tilted frames).
PILOTS = {"iberia": dict(lower_lat=35.5, upper_lat=44.0, left_lon=-10.0, right_lon=4.5),
          "global": dict(lower_lat=-56.0, upper_lat=60.0, left_lon=-180.0, right_lon=180.0)}
PILOT = "iberia"
if "--pilot" in sys.argv:
    _i = sys.argv.index("--pilot"); PILOT = sys.argv[_i + 1]; del sys.argv[_i:_i + 2]
BBOX = PILOTS[PILOT]

# Epochs (human, 2026-10-03): "2015" may use 2012-2015; "2025" = after 2020, as late as possible.
EPOCHS = {2015: (20120101, 20151231), 2025: (20210101, 20991231)}
# Expeditions whose dates overlap the epochs (filtered by photo date afterwards).
MISSIONS = [f"ISS{n:03d}" for n in list(range(30, 47)) + list(range(64, 76))]

# Photo pool (human, 2026-10-03): human-catalogued with centre point + machine-learning catalogued.
RECORD_TYPES = ("Cataloged With Center Point", "Cataloged By Machine Learning")
RETRIES, RETRY_WAIT_S = 3, 60  # on HTTP errors from the archive
PARALLEL_REQUESTS = 5  # fetches at once (02, 03; human 2026-10-03: 3 -> 5 for the global run)
PARALLEL_QUERIES = 3   # mission queries at once (01_query_eol.py, global run)

# Test cities (human, 2026-10-03: "3-4 cities", one photo per epoch). Reference points are
# approximate city centres (lat, lon; agent-typed, used only to select photos, not as data).
TEST_CITIES = {"Madrid": (40.42, -3.70), "Lisbon": (38.72, -9.14),
               "Barcelona": (41.39, 2.17), "Valencia": (39.47, -0.38)}
SELECT_RADIUS_DEG = 0.25        # photo centre within this distance of the reference point
SELECT_FOCAL_MM = (50, 400)     # city-scale frames

# City classes (human, 2026-10-03). A bright pixel (same mask as 04_colour_ratios.py) is
# "white" if linear G/R >= WHITE_GR. A photo's class comes from its white share:
#   < SHARE_CUTS[0] -> 1 mostly sodium, SHARE_CUTS[0]..SHARE_CUTS[1] -> 2 mixed, > SHARE_CUTS[1] -> 3 mostly LED
WHITE_GR = 0.8
SHARE_CUTS = (0.10, 0.50)
CLASSES = {0: "no estimate", 1: "mostly sodium", 2: "mixed", 3: "mostly LED"}
# Area a city's class applies to (human, 2026-10-03): lit pixels (radiance > 0 in that
# year) whose centre is within CITY_RADIUS_KM (great circle) of the city's reference point.
CITY_RADIUS_KM = 25.0
EARTH_RADIUS_KM = 6371.0088  # IUGG mean radius
CLASS_RASTER = DERIVED / "classes" / f"{PILOT}_classes_v1.tif"
# Display tints (human, 2026-10-03): nominal CCT per class, shown as blackbody colours.
TINT_CCT_K = {1: 2000, 2: 3000, 3: 4000}
