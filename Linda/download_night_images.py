from getpass import getpass
from pathlib import Path

from zensvi.download import MLYDownloader
from zensvi.download.mapillary.models.exceptions import InvalidTokenError


project_dir = Path(__file__).resolve().parent
area_dir = project_dir / "data" / "nyc_financial_district"
night_candidates = area_dir / "night_candidates_sampled.csv"
image_output = area_dir / "02_night_images_sampled"

if not night_candidates.exists():
    raise SystemExit(
        "night_candidates_sampled.csv was not found. Run mapillary_night_pilot.py first."
    )

token = getpass("Paste your Mapillary Client Token (hidden): ")
token = "".join(token.split()).strip('"\'')
if token.lower().startswith("bearer"):
    token = token[6:].lstrip(":=").strip()
if token.lower().startswith("access_token="):
    token = token.split("=", 1)[1].strip()
if not token.startswith("MLY|"):
    raise SystemExit("The value does not look like a complete Mapillary Access Token.")

try:
    downloader = MLYDownloader(mly_api_key=token)
except InvalidTokenError as error:
    raise SystemExit("Mapillary rejected this token (401 Unauthorized).") from error

print("Downloading sampled night candidates at 1024 px...")
downloader.download_svi(
    dir_output=str(image_output),
    path_pid=night_candidates,
    resolution=1024,
)

downloaded = list((image_output / "mly_svi").glob("*.png"))
print(f"Finished. Downloaded image files: {len(downloaded)}")
print(f"Image folder: {image_output / 'mly_svi'}")
