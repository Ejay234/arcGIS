import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

# 1) Load buildings
bldg = gpd.read_file("slc_buildings.geojson")

# 2) Raster path
raster_path = "nlcd_impervious_2019.tiff"

# 3) Compute roof area – project to UTM Zone 12N (meters) for Utah
bldg_m = bldg.to_crs(epsg=26912)
bldg_m["roof_area_m2"] = bldg_m.geometry.area

# 4) Reproject buildings to match raster CRS before zonal stats
with rasterio.open(raster_path) as src:
    raster_crs = src.crs

bldg_aligned = bldg_m.to_crs(raster_crs)

# 5) Zonal stats: mean impervious within each building footprint
# nodata is read automatically from raster metadata
zs = zonal_stats(bldg_aligned, raster_path, stats=["mean"])
bldg_m["imp_mean"] = [z["mean"] for z in zs]

# 6) Simple screening score (transparent + explainable)
# Normalize roughly to 0-100
area_norm = (bldg_m["roof_area_m2"] / bldg_m["roof_area_m2"].quantile(0.95)).clip(upper=1.0)
imp_norm  = (bldg_m["imp_mean"] / 100.0).clip(lower=0.0, upper=1.0)
bldg_m["score"] = (60 * area_norm + 40 * imp_norm).round(1)

# 7) Keep only useful fields and export to GeoJSON
out = bldg_m[["roof_area_m2", "imp_mean", "score", "geometry"]].dropna(subset=["imp_mean"])
out.to_crs(epsg=4326).to_file("slc_greenroof_screening.geojson", driver="GeoJSON")
print("Wrote slc_greenroof_screening.geojson")
