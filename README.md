# SLC Green Roof Screening (Free ArcGIS Online + Annual NLCD)

This project produces a **user-friendly, shareable web map layer** that screens Salt Lake City building footprints for **green roof opportunity** using open geospatial data—without requiring an ArcGIS Pro/ArcGIS Online organizational subscription.

You will end up with a GeoJSON layer you can upload into ArcGIS Online Map Viewer and style by **Tier** (High/Medium/Low), with built-in **QA flags** that catch obvious false-positives (e.g., open stadium footprints).

## What the map tells you

Each building footprint gets:
- **roof_area_m2** – footprint area (proxy for maximum green roof area)
- **imp_mean** – mean **Fractional Impervious Surface** value within the footprint (Annual NLCD)
- **lc_major / lc_label** – dominant **land cover class** within the footprint (Annual NLCD)
- **canopy_mean** – mean **tree canopy %** within the footprint (Annual NLCD canopy; optional)
- **score** – transparent screening score (bigger roofs + more impervious context)
- **tier** – High / Medium / Low (for nontechnical viewers)
- **qa_flag** – “ok” or “needs review …” flags (e.g., low impervious, non-developed land cover, high canopy)

**Important:** this is a *screening* tool, not an engineering feasibility decision. It does **not** account for roof slope, structural capacity, waterproofing condition, ownership/permissions, roof obstructions, or cost.

## Data inputs

### Required
1. **Building footprints** (UGRC, exported to GeoJSON for SLC):  
   `slc_buildings.geojson`  
   Source service (ArcGIS FeatureServer):  
   https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Buildings/FeatureServer/0

2. **Annual NLCD Fractional Impervious Surface (single year)**, GeoTIFF clipped to SLC area:  
   Example: `Annual_NLCD_FctImp_2024_....tif(f)`  
   Downloaded via MRLC Annual NLCD viewer:
   https://www.mrlc.gov/viewer/

### Optional but recommended
3. **Annual NLCD Land Cover (same year)**, GeoTIFF clipped to the same extent.
4. **Annual NLCD Tree Canopy (same year)**, GeoTIFF clipped to the same extent.


## Setup

### Python environment
Install dependencies:

```bash
pip install geopandas rasterio rasterstats shapely pyproj fiona pandas numpy
```

## Run the pipeline

1. Put these files in the same folder as the script:
   - `slc_buildings.geojson`
   - `FctImp_2024.tif` (or your downloaded impervious GeoTIFF)
   - (optional) `LandCover_2024.tif`
   - (optional) `TreeCanopy_2024.tif`

2. Run:

```bash
python build_greenroof_candidates.py \
  --buildings slc_buildings.geojson \
  --impervious FctImp_2024.tif \
  --landcover LandCover_2024.tif \
  --canopy TreeCanopy_2024.tif \
  --out slc_greenroof_userfriendly.geojson
```

If you don't have land cover or canopy yet, omit those flags.

## Upload to ArcGIS Online (free account)

1. ArcGIS Online → **Map Viewer**
2. **Add → Add layer from file** → select `slc_greenroof_userfriendly.geojson`
3. Style:
   - **tier** (Unique symbols): High / Medium / Low
   - Add a filter for decision-makers: `qa_flag = ok`
4. Pop-ups: show `tier`, `score`, `roof_area_m2`, `imp_mean`, `lc_label`, `canopy_mean`, `qa_flag`


## Scoring + QA logic (transparent)

### Score
A simple weighted score (0–100-ish) is computed from:
- **Roof area** (normalized by the 95th percentile)
- **Imperviousness** (scaled to 0–1)

Default:
- 60% roof area
- 40% imperviousness

### QA flags (examples)
- **imp_mean < 20%** → likely not a solid roof / open structure → `needs review`
- **dominant land cover not Developed (21–24)** → likely not a roof → `needs review`
- **canopy_mean > 25%** → trees inside footprint (bad footprint or open structure) → `needs review`
- `TYPE` text contains “likely” → `needs review`

This is why a stadium footprint can still show up, but it will be flagged instead of incorrectly treated as a “High” candidate.

## Next improvements (if you have time)
- Add a **30m buffer** around buildings and compute imperviousness *around* roofs (context), not only inside them.
- Add a “**roof feasibility**” proxy using building `TYPE`, land cover, and canopy thresholds.
- Integrate a lightweight “verification” workflow (Google Form + ID field) since Survey123 requires an ArcGIS org subscription.
