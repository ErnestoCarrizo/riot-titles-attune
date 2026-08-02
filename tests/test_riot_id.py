import pytest

from app.routing import account_region_for_platform
from app.utils import normalize_search, parse_riot_id, riot_id_path


def test_parse_riot_id_trims_outer_spaces_but_keeps_unicode_and_inner_spaces():
    assert parse_riot_id("  Luz de Luna # Águila  ") == ("Luz de Luna", "Águila")


@pytest.mark.parametrize("value", ["Nombre", "Nombre#", "#TAG", "A#B#C", "   #   ", ""])
def test_rejects_invalid_riot_ids(value):
    with pytest.raises(ValueError):
        parse_riot_id(value)


def test_url_encodes_riot_id_segments():
    assert riot_id_path("Luz de Luna", "Águila") == "Luz%20de%20Luna/%C3%81guila"


def test_resolves_account_regional_route():
    assert account_region_for_platform("LA2") == "americas"
    assert account_region_for_platform("EUW1") == "europe"
    assert account_region_for_platform("KR") == "asia"


def test_search_normalization_ignores_case_and_accents():
    assert normalize_search("Medicina CÁDUCADA") == normalize_search("medicina caducada")
