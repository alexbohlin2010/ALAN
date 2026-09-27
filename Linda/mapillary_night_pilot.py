from getpass import getpass
from pathlib import Path

import pandas as pd
from zensvi.download import MLYDownloader
from zensvi.download.mapillary.models.exceptions import InvalidTokenError
from zensvi.metadata import MLYMetadata


# Wall Street-Broad Street core in Manhattan's Financial District: office
# interiors, institutional facades, public-space lighting, and nighttime use.
AREA_NAME = "nyc_financial_district"
LATITUDE = 40.7069
LONGITUDE = -74.0095
BUFFER_METERS = 300

project_dir = Path(__file__).resolve().parent
area_dir = project_dir / "data" / AREA_NAME
metadata_dir = area_dir / "01_metadata"
metadata_dir.mkdir(parents=True, exist_ok=True)

token = getpass("Paste your Mapillary Client Token (hidden): ")
# Remove harmless copy/paste artifacts without ever printing the token.
token = "".join(token.split()).strip('"\'')
if token.lower().startswith("bearer"):
    token = token[6:].lstrip(":=").strip()
if token.lower().startswith("access_token="):
    token = token.split("=", 1)[1].strip()
if not token:
    raise SystemExit("No token entered. Nothing was downloaded.")

print(
    "Token format check:",
    f"starts with MLY| = {token.startswith('MLY|')},",
    f"separator count = {token.count('|')},",
    f"length = {len(token)}",
)
if not token.startswith("MLY|"):
    raise SystemExit(
        "This does not look like a Mapillary client access token. "
        "Copy the complete value under Access Token > View; do not use App ID or Client secret."
    )

print("\n1/3 Fetching Mapillary metadata only (no images yet)...")
try:
    downloader = MLYDownloader(mly_api_key=token)
except InvalidTokenError as error:
    raise SystemExit(
        "Mapillary rejected this token (401 Unauthorized). Return to the developer dashboard, "
        "open Access Token > View, and copy the complete token again. If the same complete token "
        "still fails, create a new application/token and retry."
    ) from error
downloader.download_svi(
    dir_output=str(metadata_dir),
    lat=LATITUDE,
    lon=LONGITUDE,
    buffer=BUFFER_METERS,
    metadata_only=True,
)

raw_metadata = metadata_dir / "mly_pids.csv"
if not raw_metadata.exists():
    raise SystemExit(f"Expected metadata file was not created: {raw_metadata}")

print("\n2/3 Computing local time and day/night status...")
all_images_file = area_dir / "all_images_with_time.csv"
metadata = MLYMetadata(str(raw_metadata)).compute_metadata(
    unit="image",
    indicator_list="year month day hour daytime_nighttime",
)
metadata["id"] = metadata["id"].astype(str)
metadata.to_csv(all_images_file, index=False)

night = metadata[
    metadata["daytime_nighttime"]
    .astype(str)
    .str.lower()
    .str.contains("night", na=False)
].copy()

# Keep the complete set. This is the input for downloading every available
# night image, while the sampled file below is useful for a faster pilot.
all_night_file = area_dir / "night_candidates_all.csv"
night.to_csv(all_night_file, index=False)

print("\n3/3 Sampling repeated frames from each Mapillary sequence...")
night = night.sort_values(["sequence_id", "captured_at"])
sampled_groups = [group.iloc[::5] for _, group in night.groupby("sequence_id")]
sampled = pd.concat(sampled_groups, ignore_index=True) if sampled_groups else night.copy()

night_file = area_dir / "night_candidates_sampled.csv"
sampled.to_csv(night_file, index=False)

print("\nFinished")
print(f"All images: {len(metadata)}")
print(f"Night candidates: {len(night)}")
print(f"Unique night sequences: {night['sequence_id'].nunique()}")
print(f"Sampled night candidates: {len(sampled)}")
print(f"\nAll night candidates: {all_night_file}")
print(f"Sampled night candidates: {night_file}")
