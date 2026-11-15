"""Write a scaled copy of a rate GeoTIFF (and its uncertainty), keeping georeferencing.

Used to make the 'annualized' NISAR input: NISAR covers only Jun-Oct 2026 (summer pumping
season). Sentinel-1 shows full-year rates ~0.75x the Mar-Sep (summer) rates over Quetta
(bowl max -10.8 vs -14.6 cm/yr LOS; city centre -9.3 vs ~-12.3), so the scale factor is 0.75.

usage: scale_rate.py <in.tif> <out.tif> <factor>
"""
import sys

import rasterio

src_path, dst_path, factor = sys.argv[1], sys.argv[2], float(sys.argv[3])
with rasterio.open(src_path) as src:
    data = src.read(1)
    profile = src.profile
    tags = src.tags()
with rasterio.open(dst_path, "w", **profile) as dst:
    dst.write((data * factor).astype(profile["dtype"]), 1)
    tags["SCALING"] = f"multiplied by {factor} (summer-to-annual factor from Sentinel-1)"
    dst.update_tags(**tags)
print("wrote", dst_path, "factor", factor)
