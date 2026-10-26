"""Distance, ranking and OpenStreetMap parsing. No network: uses saved fixture JSON."""
import json
from pathlib import Path

import pytest

from app.services.geo import haversine_km, rank, round_coords, weighted_rating
from app.services.osm import directions_url, matches_specialty, overpass_query, parse_places

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# ---------- haversine ----------
def test_same_point_is_zero():
    assert haversine_km(23.75, 90.38, 23.75, 90.38) == 0


def test_one_degree_of_latitude_is_about_111_km():
    assert haversine_km(23.0, 90.0, 24.0, 90.0) == pytest.approx(111.2, abs=0.2)


def test_distance_is_symmetric():
    a = haversine_km(23.7465, 90.3760, 23.7925, 90.4078)
    assert a == pytest.approx(haversine_km(23.7925, 90.4078, 23.7465, 90.3760))
    assert 5 < a < 7      # Dhanmondi to Gulshan is roughly 6 km in a straight line


# ---------- weighted rating ----------
def test_few_reviews_are_pulled_toward_the_mean():
    few = weighted_rating(5.0, 2, global_mean=4.0)
    many = weighted_rating(4.6, 80, global_mean=4.0)
    assert few < many       # 5.0 from 2 reviews does not beat 4.6 from 80


def test_no_reviews_means_no_score():
    assert weighted_rating(None, 0, 4.0) is None


@pytest.mark.parametrize("count", [1, 5, 50, 500])
def test_weighted_rating_stays_between_mean_and_average(count):
    w = weighted_rating(5.0, count, 3.5)
    assert 3.5 < w < 5.0


# ---------- ranking ----------
ITEMS = [
    {"name": "near-unrated", "distance_km": 0.5, "score": None},
    {"name": "far-best", "distance_km": 4.0, "score": 4.8},
    {"name": "mid-good", "distance_km": 2.0, "score": 4.2},
    {"name": "tie-near", "distance_km": 1.0, "score": 4.2},
]


def test_rank_by_rating_then_distance_unrated_last():
    assert [i["name"] for i in rank(ITEMS, "rating")] == ["far-best", "tie-near", "mid-good", "near-unrated"]


def test_rank_by_distance():
    assert [i["name"] for i in rank(ITEMS, "distance")] == ["near-unrated", "tie-near", "mid-good", "far-best"]


def test_coordinates_are_rounded_before_leaving_the_app():
    assert round_coords(23.746123, 90.374219) == (23.75, 90.37)


# ---------- OpenStreetMap parsing ----------
def places():
    return parse_places(json.loads((FIXTURES / "overpass_dhaka.json").read_text(encoding="utf-8")))


def test_parse_skips_nameless_and_duplicates_and_reads_way_centers():
    names = [p["name"] for p in places()]
    assert names.count("Sample City Hospital") == 1          # node + duplicate collapsed
    assert "Sample Skin Clinic" in names                       # 'way' uses its center point
    assert len(names) == 5                                     # nameless clinic dropped


def test_specialty_tags_and_dentist_mapping():
    by_name = {p["name"]: p for p in places()}
    assert by_name["Sample Skin Clinic"]["specialties"] == ["Dermatology"]
    assert by_name["Sample Dental Care"]["specialties"] == ["Dentistry"]
    assert by_name["Sample City Hospital"]["phone"] == "+880-2-0000-1111"


@pytest.mark.parametrize("specialty, expected", [
    ("Dermatology", {"Sample City Hospital", "Sample Skin Clinic", "Far Away Hospital"}),
    ("Dentistry", {"Sample City Hospital", "Sample Dental Care", "Far Away Hospital"}),
    ("General Medicine", {"Sample City Hospital", "Sample Family Doctor", "Far Away Hospital"}),
])
def test_matches_specialty(specialty, expected):
    assert {p["name"] for p in places() if matches_specialty(p, specialty)} == expected


def test_query_contains_no_health_details():
    q = overpass_query(23.75, 90.37, 5000)
    assert "around:5000,23.75,90.37" in q
    for word in ("Dermatology", "headache", "speciality"):
        assert word not in q            # specialty filtering happens inside Her Aura


def test_directions_link_needs_no_api_key():
    url = directions_url(23.75, 90.38)
    assert url == "https://www.google.com/maps/dir/?api=1&destination=23.75,90.38" and "key=" not in url


# ---------- provider resilience ----------
class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def test_falls_back_to_mirror_when_main_server_times_out(monkeypatch):
    import httpx
    from app.services import osm
    monkeypatch.delenv("OSM_FIXTURE", raising=False)
    osm._cache.clear()
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            raise httpx.ReadTimeout("busy")
        return FakeResponse({"elements": [{"type": "node", "id": 1, "lat": 23.75, "lon": 90.37,
                                           "tags": {"amenity": "hospital", "name": "Mirror Hospital"}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    places = osm.nearby_places(23.7461, 90.3742, 3)
    assert [p["name"] for p in places] == ["Mirror Hospital"]
    assert calls == list(osm.OVERPASS_URLS)


def test_all_servers_down_raises_provider_error(monkeypatch):
    import httpx
    from app.services import osm
    monkeypatch.delenv("OSM_FIXTURE", raising=False)
    osm._cache.clear()
    monkeypatch.setattr(httpx, "post", lambda url, **k: (_ for _ in ()).throw(httpx.ConnectError("down")))
    with pytest.raises(osm.ProviderError):
        osm.nearby_places(23.0, 90.0, 3)
