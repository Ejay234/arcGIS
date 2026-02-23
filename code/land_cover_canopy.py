import geopandas as gpd
from rasterstats import zonal_stats
import numpy as np
import rasterio

bldg = gpd.read_file("/Users/ejay/Downloads/geo/data/raw/slc_buildings.geojson").to_crs(epsg=26912)
bldg["roof_area_m2"] = bldg.geometry.area

# --- Rasters ---
IMP = "/Users/ejay/Downloads/geo/data/raw/FctImp_2024.tiff"
LC  = "/Users/ejay/Downloads/geo/data/raw/land_cover_2024.tiff"
CAN = "/Users/ejay/Downloads/geo/data/raw/tree_canopy_2023.tiff"

# Reproject buildings to match raster CRS
with rasterio.open(IMP) as src:
    raster_crs = src.crs

bldg_aligned = bldg.to_crs(raster_crs)

# Zonal stats
bldg["imp_mean"] = [z["mean"] for z in zonal_stats(bldg_aligned, IMP, stats=["mean"], all_touched=True)]
bldg["lc_major"] = [z["majority"] for z in zonal_stats(bldg_aligned, LC, stats=["majority"], all_touched=True)]
bldg["canopy_mean"] = [z["mean"] for z in zonal_stats(bldg_aligned, CAN, stats=["mean"], all_touched=True)]

# If your impervious/canopy are 0-1 instead of 0-100, uncomment:
# bldg["imp_mean"] *= 100
# bldg["canopy_mean"] *= 100

# --- Score ---
area_norm = (bldg["roof_area_m2"] / bldg["roof_area_m2"].quantile(0.95)).clip(upper=1.0)
imp_norm  = (bldg["imp_mean"] / 100.0).clip(0, 1)
bldg["score"] = (60 * area_norm + 40 * imp_norm).round(1)

# --- QA flags ---
# NLCD codes: 11=open water, 90=woody wetlands, 95=emergent wetlands, 52=shrub
conditions = [
    bldg["imp_mean"].isna(),
    bldg["canopy_mean"] > 25,
    bldg["lc_major"].isin([11, 90, 95, 52]),
    bldg["imp_mean"] < 20,
]
choices = [
    "no impervious sample",
    "needs review: canopy inside footprint",
    "needs review: land cover",
    "needs review: low impervious",
]
bldg["qa_flag"] = np.select(conditions, choices, default="ok")

# --- Tier labels ---
q85 = bldg["score"].quantile(0.85)
q50 = bldg["score"].quantile(0.50)

bldg["tier"] = np.where(
    (bldg["score"] >= q85) & (bldg["qa_flag"] == "ok"), "High",
    np.where(bldg["score"] >= q50, "Medium", "Low")
)

# --- Why explanation ---
bldg["why_top"] = np.where(
    bldg["roof_area_m2"] >= bldg["roof_area_m2"].quantile(0.85),
    "large roof; ", "smaller roof; "
)
bldg["why_top"] += np.where(
    bldg["imp_mean"] >= bldg["imp_mean"].quantile(0.85),
    "high impervious context", "moderate/low impervious context"
)

# --- Export ---
keep = ["tier", "score", "roof_area_m2", "imp_mean", "canopy_mean", "lc_major", "qa_flag", "why_top", "geometry"]
out = bldg[keep].to_crs(epsg=4326)
out.to_file("/Users/ejay/Downloads/geo/data/output/slc_greenroof_userfriendly.geojson", driver="GeoJSON")
print("Wrote /data/output/slc_greenroof_userfriendly.geojson")