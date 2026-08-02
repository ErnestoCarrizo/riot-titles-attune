import pytest

from app.errors import ExternalSchemaError
from app.services.title_catalog import level_to_icon_url, parse_catalog, parse_challenge_graph


def test_extracts_title_rewards_and_resolves_names(fixture_json):
    titles = parse_catalog(fixture_json("challenges.json"), fixture_json("achievementtitles.json"), base_url="https://cdn.test/global", locale="es_ar")
    by_id = {title.title_id: title for title in titles}
    assert by_id["title-med"].title_name == "Cirujano"
    assert len(by_id["title-med"].requirements) == 2
    assert len(by_id) == 2


def test_does_not_duplicate_same_title_thresholds(fixture_json):
    titles = parse_catalog(fixture_json("challenges.json"), fixture_json("achievementtitles.json"), base_url="https://cdn.test/global", locale="es_ar")
    assert [title.title_id for title in titles].count("title-med") == 1


def test_keeps_multiple_requirements_for_one_title(fixture_json):
    titles = parse_catalog(fixture_json("challenges.json"), fixture_json("achievementtitles.json"), base_url="https://cdn.test/global", locale="es_ar")
    calm = next(title for title in titles if title.title_id == "title-calm")
    assert [requirement.target_tier for requirement in calm.requirements] == ["SILVER", "GOLD"]


def test_maps_communitydragon_asset_path():
    path = "/lol-game-data/assets/ASSETS/Challenges/Config/101104/Tokens/GOLD.png"
    assert level_to_icon_url(path, "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global", "es_ar") == "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/es_ar/assets/ASSETS/Challenges/Config/101104/Tokens/GOLD.png"
    assert level_to_icon_url("/unknown/path.png", "https://cdn.test", "default") is None


def test_rejects_incompatible_catalog_schema():
    with pytest.raises(ExternalSchemaError):
        parse_catalog({"wrong": "shape"}, {"achievementTitles": []}, base_url="https://cdn.test", locale="default")


def test_parses_parent_graph_and_capstone_tags():
    challenges = {
        "challenges": {
            "10": {
                "name": "Autoridad",
                "description": "Descripción",
                "tags": {"parent": "1", "isCapstone": "Y"},
                "thresholds": {"MASTER": {"value": 10, "rewards": []}},
            },
            "11": {
                "name": "Rama",
                "description": "Descripción",
                "tags": {"parent": "10"},
                "thresholds": {"GOLD": {"value": 5, "rewards": []}},
            },
        }
    }
    graph = parse_challenge_graph(challenges, base_url="https://cdn.test", locale="default")
    assert graph[10].parent_challenge_id == 1
    assert graph[10].is_capstone is True
    assert graph[11].parent_challenge_id == 10
    assert graph[10].max_requirement.target_tier == "MASTER"
