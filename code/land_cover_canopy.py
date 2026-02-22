import geopandas as gpd
from rasterstats import zonal_stats
import pandas as pd
import numpy as np

bldg = gpd.read_file("data/raw/slc_buildings.geojson").to_crs(epsg=26912)
bldg["roof_area_m2"] = bldg.geometry.area

# --- Rasters ---
IMP = "data/raw/FctImp_2024.tif"
LC  = "LandCover_2024.tif"
CAN = "TreeCanopy_2024.tif"   # optional

# Use all_touched so small roofs still sample pixels
bldg["imp_mean"] = [z["mean"] for z in zonal_stats(bldg, IMP, stats=["mean"], all_touched=True)]

# Land cover: take the most common class (mode)
lc_stats = zonal_stats(bldg, LC, stats=["majority"], all_touched=True)
bldg["lc_major"] = [z["majority"] for z in lc_stats]

# Tree canopy mean (optional)
can_stats = zonal_stats(bldg, CAN, stats=["mean"], all_touched=True)
bldg["canopy_mean"] = [z["mean"] for z in can_stats]

# If your impervious/canopy are 0–1 instead of 0–100, scale:
# bldg["imp_mean"] *= 100
# bldg["canopy_mean"] *= 100

# --- Score (transparent) ---
area_norm = (bldg["roof_area_m2"] / bldg["roof_area_m2"].quantile(0.95)).clip(upper=1.0)
imp_norm  = (bldg["imp_mean"] / 100.0).clip(0, 1)

bldg["score"] = (60 * area_norm + 40 * imp_norm).round(1)

# --- QA flags (tune thresholds later) ---
bldg["qa_flag"] = "ok"
bldg.loc[bldg["imp_mean"].isna(), "qa_flag"] = "no impervious sample"
bldg.loc[bldg["imp_mean"] < 20, "qa_flag"] = "needs review: low impervious"
bldg.loc[bldg["canopy_mean"] > 25, "qa_flag"] = "needs review: canopy inside footprint"

# Optional: land cover red flag (you’ll refine once you map class codes)
# bldg.loc[bldg["lc_major"].isin([water_code, wetland_code, shrub_code]), "qa_flag"] = "needs review: land cover"

# --- Tier labels ---
q85 = bldg["score"].quantile(0.85)
q50 = bldg["score"].quantile(0.50)

bldg["tier"] = np.where((bldg["score"] >= q85) & (bldg["qa_flag"] == "ok"), "High",
                np.where(bldg["score"] >= q50, "Medium", "Low"))

# --- “Why” explanation ---
bldg["why_top"] = np.where(bldg["roof_area_m2"] >= bldg["roof_area_m2"].quantile(0.85),
                           "large roof; ", "smaller roof; ")
bldg["why_top"] += np.where(bldg["imp_mean"] >= bldg["imp_mean"].quantile(0.85),
                            "high impervious context", "moderate/low impervious context")

# Export
keep = ["tier","score","roof_area_m2","imp_mean","canopy_mean","lc_major","qa_flag","why_top","geometry"]
out = bldg[keep].to_crs(epsg=4326)
out.to_file("slc_greenroof_userfriendly.geojson", driver="GeoJSON")
print("Wrote slc_greenroof_userfriendly.geojson")