"""Nearby hospitals/clinics/doctors from OpenStreetMap (free, no API key).

- Overpass API: places with amenity=hospital|clinic|doctors|dentist around a point.
- Nominatim: turn a typed area ("Dhanmondi") into coordinates, limited to Bangladesh.

Privacy: we only send rounded coordinates (~1 km) and generic place types. The user's
specialty, symptoms and health logs never leave Her Aura; filtering happens here.
Fair use: identifying User-Agent, short timeouts, in-memory caching. Data (c) OpenStreetMap
contributors, ODbL: the UI shows that attribution.

Tests and e2e runs set OSM_FIXTURE / NOMINATIM_FIXTURE to JSON files so nothing hits the network.
"""
import json
import os
import time

import httpx

from app.services.geo import round_coords

USER_AGENT = "HerAura/1.0 (portfolio demo; +https://github.com/Noshin-Arthi/her-aura)"
# Public Overpass servers are free but often busy: try the main one, then a mirror.
OVERPASS_URLS = ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_SECONDS = 600
TIMEOUT = 12.0
OVERPASS_TIMEOUT = 25.0
ATTRIBUTION = "Map data © OpenStreetMap contributors"

# OSM healthcare:speciality values -> Her Aura specialties
SPECIALTY_MAP = {
    "gynaecology": "Gynecology", "obstetrics": "Gynecology", "gynecology": "Gynecology",
    "dermatology": "Dermatology", "neurology": "Neurology", "orthopaedics": "Orthopedics",
    "orthopedics": "Orthopedics", "psychiatry": "Psychiatry", "gastroenterology": "Gastroenterology",
    "dentistry": "Dentistry", "dental": "Dentistry", "oncology": "Gynecologic Oncology",
    "general": "General Medicine", "family_medicine": "General Medicine", "internal": "General Medicine",
}

_cache: dict[str, tuple[float, object]] = {}


class ProviderError(RuntimeError):
    """The map provider failed (timeout, rate limit, bad response)."""


def _cached(key: str, loader):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    value = loader()
    _cache[key] = (time.time(), value)
    return value


def overpass_query(lat: float, lng: float, radius_m: int) -> str:
    kinds = "hospital|clinic|doctors|dentist"
    return (f'[out:json][timeout:20];'
            f'(nwr["amenity"~"^({kinds})$"](around:{radius_m},{lat},{lng});'
            f'nwr["healthcare"~"^({kinds})$"](around:{radius_m},{lat},{lng}););'
            f'out center tags 80;')


def parse_places(payload: dict) -> list[dict]:
    """Overpass JSON -> simple place dicts. Pure function, unit tested."""
    places, seen = [], set()
    for el in payload.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name:en") or tags.get("name")
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lng = el.get("lon") or (el.get("center") or {}).get("lon")
        if not name or lat is None or lng is None:
            continue
        key = (name.strip().lower(), round(lat, 4), round(lng, 4))
        if key in seen:                       # same place mapped as node and building
            continue
        seen.add(key)
        kind = tags.get("amenity") or tags.get("healthcare") or "clinic"
        raw = tags.get("healthcare:speciality", "")
        specialties = sorted({SPECIALTY_MAP[s.strip()] for s in raw.split(";") if s.strip() in SPECIALTY_MAP})
        if kind == "dentist" and "Dentistry" not in specialties:
            specialties.append("Dentistry")
        address = ", ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street"),
                                        tags.get("addr:suburb") or tags.get("addr:city")) if p)
        places.append({
            "name": name, "lat": float(lat), "lng": float(lng), "kind": kind,
            "specialties": specialties, "phone": tags.get("phone") or tags.get("contact:phone") or "",
            "address": address, "opening_hours": tags.get("opening_hours", ""),
            "osm_url": f"https://www.openstreetmap.org/{el.get('type', 'node')}/{el.get('id')}",
        })
    return places


def matches_specialty(place: dict, specialty: str | None) -> bool:
    """Hospitals treat many specialties; clinics/doctors match on their tag; untagged ones count as general."""
    if not specialty:
        return True
    if place["kind"] == "hospital" or specialty in place["specialties"]:
        return True
    return specialty == "General Medicine" and not place["specialties"] and place["kind"] in ("clinic", "doctors")


def nearby_places(lat: float, lng: float, radius_km: float = 5) -> list[dict]:
    fixture = os.getenv("OSM_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            return parse_places(json.load(f))
    rlat, rlng = round_coords(lat, lng)
    radius_m = int(min(max(radius_km, 1), 15) * 1000)

    def load():
        last_error = None
        for url in OVERPASS_URLS:
            try:
                r = httpx.post(url, data={"data": overpass_query(rlat, rlng, radius_m)},
                               headers={"User-Agent": USER_AGENT}, timeout=OVERPASS_TIMEOUT)
                r.raise_for_status()
                return parse_places(r.json())
            except (httpx.HTTPError, ValueError) as e:
                last_error = e
        raise ProviderError(f"Map service unavailable: {type(last_error).__name__}") from last_error

    return _cached(f"osm:{rlat}:{rlng}:{radius_m}", load)


def geocode(query: str) -> dict | None:
    """'Dhanmondi' -> {'lat', 'lng', 'label'} within Bangladesh, or None."""
    query = query.strip()[:100]
    if not query:
        return None
    fixture = os.getenv("NOMINATIM_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            data = json.load(f)
    else:
        def load():
            try:
                r = httpx.get(NOMINATIM_URL, params={"q": query, "format": "json", "limit": 1, "countrycodes": "bd"},
                              headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as e:
                raise ProviderError(f"Address search unavailable: {type(e).__name__}") from e
        data = _cached(f"geo:{query.lower()}", load)
    if not data:
        return None
    first = data[0]
    return {"lat": float(first["lat"]), "lng": float(first["lon"]), "label": first.get("display_name", query)}


def directions_url(lat: float, lng: float) -> str:
    """Opens Google Maps directions in the user's browser/app. A plain link: no API, no key."""
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
