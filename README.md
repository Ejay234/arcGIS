# # SLC Green Roof Opportunity Screening

StoryMap (public): https://arcg.is/1zHC8H

## What this is
A lightweight GIS screening workflow that ranks Salt Lake City building footprints for **green roof opportunity** using open Annual NLCD products. The output is a web-map-ready layer for ArcGIS Online with **tiers** and **QA flags** (to catch likely false positives like open structures).

# Outputs
- `slc_greenroof_userfriendly.geojson` — upload to ArcGIS Online Map Viewer
- (optional) `slc_greenroof_userfriendly.csv` — table export for reporting

Key fields:
- `tier` (High / Medium / Low), `score`, `roof_area_m2`, `imp_mean`
- optional: `lc_major`, `canopy_mean`
- `qa_flag`, `why_top`

## Data
- Building footprints: `slc_buildings.geojson`
- Annual NLCD rasters (same extent):
  - Fractional Impervious Surface (required)
  - Land Cover (optional)
  - Tree Canopy (optional)

## Method
1. Compute roof footprint area (`roof_area_m2`).
2. Zonal stats per building from NLCD rasters (impervious mean, land cover majority, canopy mean).
3. Screening score:
   - `score = 0.6 * normalized_roof_area + 0.4 * normalized_impervious`
4. Convert to `tier` and apply `qa_flag` to mark features needing review.

## Reproduce
```bash
pip install geopandas rasterio rasterstats shapely pyproj fiona pandas numpy
python land_cover_canopy.py
```

Upload the output GeoJSON to ArcGIS Online Map Viewer and configure:
- Styles: unique symbols on `tier`
- Pop-ups: `tier`, `score`, `roof_area_m2`, `imp_mean`, `qa_flag`, `why_top`
- Two views: “Candidates (OK)” vs “Needs Review” using `qa_flag`

## Limitations
Screening only—does not determine roof feasibility (slope, structure/load, condition, ownership/access, rooftop obstructions, cost). QA flags support follow-up verification.

## Data inputs

### Required
1. **Building footprints** (UGRC, exported to GeoJSON for SLC):  
   `slc_buildings.geojson`  
   Source service (ArcGIS FeatureServer):  
   https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/Buildings/FeatureServer/0
2. **SLC Boundary**: https://maps.slc.gov/server/rest/services/Hosted/SLC_Boundary/FeatureServer 
3. **Annual NLCD Fractional Impervious Surface (2024)**, GeoTIFF clipped to SLC area:    
4. **Annual NLCD Land Cover (2024)**, GeoTIFF clipped to the same extent.
5. **Annual NLCD Tree Canopy (2023)**, GeoTIFF clipped to the same extent.
 - Downloaded via MRLC Annual NLCD viewer:
   https://www.mrlc.gov/viewer/