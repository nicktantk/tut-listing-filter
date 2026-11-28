from geo import Geocoder, distance_km, km_between

COORDS = {"470629": [1.3330, 103.9210], "460166": [1.3210, 103.9330], "519933": [1.3730, 103.9490]}


def make_geo(tmp_path):
    calls = []

    def fetch(code):
        calls.append(code)
        return COORDS.get(code)

    return Geocoder(fetch=fetch), calls


def test_km_between_is_reasonable():
    # 0.012 deg lat and lon apart is about 1.9 km in Singapore
    assert 1.7 < km_between(COORDS["470629"], COORDS["460166"]) < 2.1


def test_distance_uses_first_known_postal_code(tmp_path):
    geo, _ = make_geo(tmp_path)
    km = distance_km("Job Code: 999999\nAddress: 166 Bedok South Ave 3 (S)460166", "470629", geo)
    assert km is not None and 1.7 < km < 2.1


def test_no_postal_code_means_no_distance(tmp_path):
    geo, _ = make_geo(tmp_path)
    assert distance_km("Bedok North, near MRT", "470629", geo) is None


def test_lookups_are_cached(tmp_path):
    geo, calls = make_geo(tmp_path)
    distance_km("(S)460166", "470629", geo)
    distance_km("(S)460166", "470629", geo)
    assert calls.count("460166") == 1


def test_failed_lookup_is_not_cached(tmp_path):
    def boom(code):
        raise RuntimeError("network down")

    geo = Geocoder(fetch=boom)
    assert geo.coords("460166") is None
    assert "460166" not in geo.cache
