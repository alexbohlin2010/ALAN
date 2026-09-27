# Assignment 2 — Project Context Brief

## Format and Constraints

- Four-week pair project; unrelated to Assignment 1.
- Deliverable: interactive data visualization / website, not a standalone analytics product.
- Umbrella: physical places where people live + spatial intelligence.
- Use existing public data; one focused question and one or a few related datasets.
- No user study or self-collected dataset.
- The story should support future reflection, planning, or decisions.
- AI must materially influence the issue, data, or future scenario.
- Practical goal: learn a niche spatial/AI skill, connect with practitioners, and build an internship-relevant portfolio project or downstream product direction.

## Team Interests

**Primary:** AI prediction, uncertainty, evaluation, decision support; HCI trust, explanation, cognitive load, appropriate reliance; spatial intelligence; model blind spots.

**Partner:** built environment, eco-built environment, and biological/low-impact construction materials (not limited to straw panels).

**Shared territory:** human living environments; machine-readable representations of buildings/interiors; differences between physical and mapped places; environmental or social consequences of incomplete spatial data.

## Preferred Questions

- What does a spatial system fail to see?
- Where does a mapped/modelled place differ from a more reliable reference?
- When is the system confident but wrong?
- Which materials, building forms, regions, or communities become less visible in machine-generated maps?
- How might these gaps affect future design, planning, navigation, accessibility, disaster response, or investment?
- Where should automated spatial data require human verification?

## Relevant Data Types

- **Indoor sensing:** RGB/RGB-D, LiDAR depth, confidence, reference depth, point clouds, meshes, camera poses, room layouts, 3D annotations, navigable-space metrics.
- **Buildings/settlements:** footprint polygons, coordinates, area, detection confidence, regional thresholds, temporal change, government footprints, environmental/hazard overlays.
- **Place/history:** street geometry and names, plaque locations and inscriptions, honored people, demographic and historical attributes.
- **Built-environment materials:** material properties, embodied carbon, thermal performance, resource demand, sourcing, supply chains, construction types.

## Most Relevant Sources

### Apple ARKitScenes

- https://github.com/apple-aiml-research/ARKitScenes
- Apple LiDAR depth, confidence, RGB, FARO reference depth, meshes, point clouds, poses, 3D object annotations.
- Best use: missing depth, measurement error, high-confidence errors.
- Paired device/reference data already exist; depth comparison needs calculation but no model training.
- No precomputed per-image failure maps or object-detection predictions.

### Google Open Buildings

- https://sites.research.google/gr/open-buildings/
- 1.8B AI-inferred footprints: coordinates, area, polygon, confidence, regional thresholds.
- Best use: buildings/settlements missed or distorted by satellite-based AI mapping.
- Documented omission, false detection, density, material, region, and imagery-age problems.
- No source imagery or building attributes; select one small region and an external reference source.

### Habitat Matterport 3D (HM3D)

- https://aihabitat.org/datasets/hm3d/
- 1,000 indoor digital twins; rooms, floors, furnishing, area, navigability, clutter, navigation complexity, quality ratings.
- Best use: spatial layout and embodied-agent navigation.
- Strong technical value, but no ready prediction-vs-ground-truth failure labels.

### WAY — Where Are You?

- https://meerahahn.github.io/way/data
- 6,134 indoor localization dialogues, navigation paths, final locations, floor-plan coordinates, connectivity graphs.
- Best use: language, human–AI communication, and indoor localization failure.
- Full visual environments require Matterport3D assets.

### Mapping Diversity

- https://mappingdiversity.eu/
- 56,852 person-named streets in 32 European cities; gender, profession, history, birthplace, and geography from OSM/Wikidata.
- Best use: who is remembered or made invisible in public space.
- Already a polished data-viz project; a new project needs a substantially different question.

### OpenPlaques

- https://openplaques.org/
- Geolocated plaques, inscriptions, people/subjects, organizations, colors, and places.
- Best use: spatial memory and historical visibility.
- Bulk export is unreliable; use a fixed downloaded snapshot.

### Hugging Face Spatial Datasets

- https://huggingface.co/datasets?other=spatial-intelligence
- Discovery platform, not one dataset: point clouds, layouts, spatial QA, affordances, navigation, synthetic interiors.
- Examples: SpatialLM, SceneFun3D, SPAR-7M.
- Check each source for provenance, realism, size, documentation, and license.

## Current Strongest Direction

**Visualize the gap between a physical place and its machine-generated representation, emphasizing what is missed rather than what is detected.**

1. **Indoor:** Apple LiDAR vs FARO reference depth — missing surfaces, error, misleading confidence.
2. **Building/settlement:** Google Open Buildings vs trusted local footprints — omissions, false detections, regional/material invisibility.

Decision-support question: **When is automated spatial data reliable enough to use, and where is human verification necessary?**

## Avoid

- Generic maps or descriptive dashboards
- Covering all meanings of spatial intelligence
- Training a new model or rebuilding the full sensing pipeline
- Combining unrelated datasets
- Treating confidence as accuracy or reference data as perfect reality
- Repeating an existing project without a new analytical question
