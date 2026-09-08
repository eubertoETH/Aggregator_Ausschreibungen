"""Transparent NUTS radius prefilter for the first, no-geocoder phase."""

# The lists are generated from official GISCO NUTS-2024 polygons by
# scripts/build_nuts_radius.py.  A NUTS polygon is retained if it intersects
# the air-line circle around Olgastraße 69d (48.7709753, 9.1826881).
RADIUS_KM = (25, 50, 75, 100, 150)


def nuts_codes_for_radius(radius_km: int) -> set[str]:
    from .data.nuts_radius_stuttgart import NUTS_CODES
    return set(NUTS_CODES.get(str(radius_km), ()))


def matches_nuts_radius(nuts_region: str | None, radius_km: int | None) -> bool:
    if not radius_km:
        return True
    return bool(nuts_region and any(nuts_region.startswith(code) for code in nuts_codes_for_radius(radius_km)))
