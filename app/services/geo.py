"""Distance and ranking for "doctors near me". Pure functions, unit tested."""
import math

EARTH_RADIUS_KM = 6371.0
MIN_REVIEWS = 5          # weighted rating: how many reviews before a doctor's own average counts fully
DEFAULT_MEAN = 3.5       # prior when nobody has any reviews yet


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line ("as the crow flies") distance on the globe, in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def weighted_rating(average: float | None, count: int, global_mean: float, min_reviews: int = MIN_REVIEWS) -> float | None:
    """Bayesian average: few reviews are pulled toward the overall mean, so 5.0 from 2 reviews
    does not beat 4.6 from 80. None when there are no reviews at all."""
    if not count or average is None:
        return None
    return (count / (count + min_reviews)) * average + (min_reviews / (count + min_reviews)) * global_mean


def rank(items: list[dict], sort: str = "rating") -> list[dict]:
    """items need 'distance_km' and optionally 'score'.
    rating: best score first, ties and unrated by distance. distance: nearest first, ties by score."""
    def score_key(i):
        return -(i.get("score") if i.get("score") is not None else -1)

    if sort == "distance":
        return sorted(items, key=lambda i: (i["distance_km"], score_key(i)))
    return sorted(items, key=lambda i: (i.get("score") is None, score_key(i), i["distance_km"]))


def round_coords(lat: float, lng: float, places: int = 2) -> tuple[float, float]:
    """About 1 km precision: what we send to third parties instead of the user's exact position."""
    return round(lat, places), round(lng, places)
