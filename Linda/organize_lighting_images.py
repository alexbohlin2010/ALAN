import os
import shutil
from pathlib import Path

import pandas as pd


project_dir = Path(__file__).resolve().parent
area_dir = project_dir / "data" / "nyc_financial_district"
image_root = area_dir / "02_night_images_sampled" / "mly_svi"
classification_root = area_dir / "03_lighting_classification_sampled"
organized_root = area_dir / "04_organized_images_sampled"

# One image can intentionally appear in more than one category. Hard links make
# that possible without duplicating the underlying image data on disk.
categories = {
    "low_light_candidates": classification_root / "visual_low_light_candidates.csv",
    "rejected_day": classification_root / "rejected_day.csv",
    "strict_night": classification_root / "confirmed_night.csv",
    "dusk_dawn": classification_root / "dusk_dawn.csv",
}


def build_image_index(root: Path) -> dict[str, Path]:
    supported = {".png", ".jpg", ".jpeg"}
    index: dict[str, Path] = {}
    duplicates: set[str] = set()

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in supported:
            if path.stem in index:
                duplicates.add(path.stem)
            else:
                index[path.stem] = path

    if duplicates:
        preview = ", ".join(sorted(duplicates)[:10])
        raise SystemExit(f"Duplicate image IDs found in the source folders: {preview}")
    return index


def link_or_copy(source: Path, destination: Path) -> tuple[str, str]:
    if destination.exists():
        try:
            if source.samefile(destination):
                return "existing", "already linked"
        except OSError:
            pass
        return "conflict", "destination already exists and is not the same file"

    try:
        os.link(source, destination)
        return "linked", "hard link"
    except OSError:
        shutil.copy2(source, destination)
        return "copied", "hard link unavailable; copied instead"


if not image_root.exists():
    raise SystemExit(f"Image folder not found: {image_root}")

missing_csv = [str(path) for path in categories.values() if not path.exists()]
if missing_csv:
    raise SystemExit("Missing classification CSV files:\n" + "\n".join(missing_csv))

image_index = build_image_index(image_root)
organized_root.mkdir(parents=True, exist_ok=True)
manifest_rows = []

print(f"Source images indexed: {len(image_index)}")

for category, csv_path in categories.items():
    destination_dir = organized_root / category
    destination_dir.mkdir(parents=True, exist_ok=True)

    records = pd.read_csv(csv_path, dtype={"id": str, "filename_key": str})
    id_column = "id" if "id" in records.columns else "filename_key"
    image_ids = records[id_column].dropna().astype(str).drop_duplicates()

    counts = {"linked": 0, "copied": 0, "existing": 0, "missing": 0, "conflict": 0}

    for image_id in image_ids:
        source = image_index.get(image_id)
        if source is None:
            counts["missing"] += 1
            manifest_rows.append(
                {
                    "category": category,
                    "image_id": image_id,
                    "source_path": "",
                    "destination_path": "",
                    "status": "missing",
                    "method": "source image not found",
                }
            )
            continue

        destination = destination_dir / source.name
        status, method = link_or_copy(source, destination)
        counts[status] += 1
        manifest_rows.append(
            {
                "category": category,
                "image_id": image_id,
                "source_path": str(source),
                "destination_path": str(destination),
                "status": status,
                "method": method,
            }
        )

    print(
        f"{category}: requested={len(image_ids)}, "
        f"linked={counts['linked']}, copied={counts['copied']}, "
        f"existing={counts['existing']}, missing={counts['missing']}, "
        f"conflicts={counts['conflict']}"
    )

manifest_file = organized_root / "organized_manifest.csv"
pd.DataFrame(manifest_rows).to_csv(manifest_file, index=False)

print(f"\nFinished. Organized folders: {organized_root}")
print(f"Manifest: {manifest_file}")
