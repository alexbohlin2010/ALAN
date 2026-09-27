from pathlib import Path

import pandas as pd
from zensvi.cv import ClassifierLighting


project_dir = Path(__file__).resolve().parent
area_dir = project_dir / "data" / "nyc_financial_district"
image_dir = area_dir / "02_night_images_sampled" / "mly_svi"
metadata_file = area_dir / "night_candidates_sampled.csv"
result_dir = area_dir / "03_lighting_classification_sampled"
result_dir.mkdir(parents=True, exist_ok=True)

image_files = [
    path
    for path in image_dir.rglob("*")
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}
]
if not image_files:
    raise SystemExit(f"No images found in: {image_dir}")
if not metadata_file.exists():
    raise SystemExit(f"Metadata file not found: {metadata_file}")

print(f"Images found: {len(image_files)}")
print("Running visual lighting classification...")

classifier = ClassifierLighting()
results = classifier.classify(
    dir_input=image_dir,
    dir_summary_output=result_dir,
    batch_size=8,
    save_format="csv",
)

predictions = pd.DataFrame(results)
predictions["filename_key"] = predictions["filename_key"].astype(str)

metadata = pd.read_csv(metadata_file, dtype={"id": str})
combined = metadata.merge(
    predictions,
    left_on="id",
    right_on="filename_key",
    how="left",
)

combined_file = result_dir / "night_candidates_with_visual_label.csv"
combined.to_csv(combined_file, index=False)

for label, filename in {
    "night": "confirmed_night.csv",
    "dusk/dawn": "dusk_dawn.csv",
    "day": "rejected_day.csv",
}.items():
    combined[combined["lighting"] == label].to_csv(result_dir / filename, index=False)

# For this research, keep both strict night and dusk/dawn for visual review.
low_light = combined[combined["lighting"].isin(["night", "dusk/dawn"])]
low_light.to_csv(result_dir / "visual_low_light_candidates.csv", index=False)

print("\nClassification counts:")
print(combined["lighting"].fillna("missing").value_counts().to_string())
print(f"\nCombined results: {combined_file}")
print(f"Output folder: {result_dir}")
