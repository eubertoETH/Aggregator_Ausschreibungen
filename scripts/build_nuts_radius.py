"""Generate precise NUTS-3 radius code lists from official GISCO polygons.

Run in the project image after downloading the GISCO NUTS 2024 GeoJSON:
python scripts/build_nuts_radius.py /path/to/NUTS_RG_01M_2024_3035_LEVL_3.geojson
"""
import json
import sys
from pathlib import Path

from shapely.geometry import Point, shape
from pyproj import Transformer

ANCHOR = (9.1826881, 48.7709753)  # Olgastraße 69d, Stuttgart-Mitte
RADII = (25, 50, 75, 100, 150)

source = json.loads(Path(sys.argv[1]).read_text())
transform = Transformer.from_crs(4326, 3035, always_xy=True)
point = Point(*transform.transform(*ANCHOR))
codes = {str(radius): [] for radius in RADII}
for feature in source["features"]:
    code = feature["properties"].get("NUTS_ID")
    geometry = shape(feature["geometry"])
    for radius in RADII:
        if geometry.intersects(point.buffer(radius * 1000)):
            codes[str(radius)].append(code)
output = Path("Code/app/data/nuts_radius_stuttgart.py")
output.write_text('"""Generated from GISCO NUTS 2024 polygons; do not hand-edit."""\nNUTS_CODES = ' + repr(codes) + '\n')
