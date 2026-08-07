from app.services.title_catalog import CatalogChallenge, CatalogRequirement, CatalogTitle
from app.services.title_progress import build_summary, build_title, parse_player_challenges


def requirement(challenge_id=1, reverse=False, target=15, tier="GOLD", start=None):
    return CatalogRequirement(challenge_id, "Desafío", "Descripción", tier, target, reverse, None, start)


def test_normal_progress_and_remaining():
    title = CatalogTitle("normal", "Objetivo", (requirement(),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "SILVER", "value": 11}]}))
    assert result.status == "in_progress"
    assert result.progressPercent == 73.33
    assert result.requirements[0].remainingValue == 4
    assert result.requirements[0].progressDirection == "increase"


def test_positive_value_with_none_level_is_in_progress():
    title = CatalogTitle("value-only", "Objetivo", (requirement(),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "NONE", "value": 2}]}))
    assert result.status == "in_progress"
    assert result.progressPercent == 13.33


def test_requirement_exposes_when_it_has_child_challenges():
    title = CatalogTitle("tree", "Árbol", (requirement(challenge_id=10),))
    result = build_title(title, {}, {10: [11]})
    assert result.requirements[0].hasChildren is True


def test_reverse_progress_is_estimated_and_requires_decrease():
    title = CatalogTitle("reverse", "Objetivo", (requirement(reverse=True, target=2, tier="GOLD", start=6),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "SILVER", "value": 6}]}))
    assert result.status == "in_progress"
    assert result.progressPercent == 0
    assert result.progressIsEstimate is True
    assert result.requirements[0].remainingValue == 4


def test_missing_challenge_is_not_started_and_reverse_has_null_remaining():
    normal = build_title(CatalogTitle("n", "Normal", (requirement(),)), {})
    reverse = build_title(CatalogTitle("r", "Reverse", (requirement(reverse=True, target=2, start=6),)), {})
    assert normal.status == "not_started"
    assert normal.requirements[0].currentTier == "NONE"
    assert reverse.requirements[0].remainingValue is None
    assert reverse.progressPercent is None


def test_zero_threshold_does_not_divide_by_zero():
    title = CatalogTitle("zero", "Cero", (requirement(target=0, tier="GOLD"),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "SILVER", "value": 0}]}))
    assert result.progressPercent is None


def test_unknown_tier_uses_value_fallback():
    title = CatalogTitle("unknown", "Fallback", (requirement(tier="LEGENDARY", target=10),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "MYSTERY", "value": 11}]}))
    assert result.status == "unlocked"


def test_unlocked_by_tier():
    title = CatalogTitle("tier", "Tier", (requirement(target=15, tier="GOLD"),))
    result = build_title(title, parse_player_challenges({"challenges": [{"challengeId": 1, "level": "PLATINUM", "value": 1}]}))
    assert result.unlocked is True
    assert result.progressPercent == 100


def test_reverse_absent_does_not_unlock_with_zero():
    title = CatalogTitle("reverse", "Reverse", (requirement(reverse=True, target=0, tier="NONE"),))
    result = build_title(title, {})
    assert result.unlocked is False


def test_summary_and_closest_order():
    titles = [
        build_title(CatalogTitle("a", "Zeta", (requirement(1, target=10),)), parse_player_challenges({"challenges": [{"challengeId": 1, "level": "SILVER", "value": 8}]})),
        build_title(CatalogTitle("b", "Alfa", (requirement(2, target=10),)), parse_player_challenges({"challenges": [{"challengeId": 2, "level": "SILVER", "value": 8}]})),
        build_title(CatalogTitle("c", "Listo", (requirement(3, target=10),)), parse_player_challenges({"challenges": [{"challengeId": 3, "level": "GOLD", "value": 10}]})),
    ]
    summary = build_summary(titles)
    assert summary.completionPercentage == 33.33
    assert summary.closestTitleIds == ["b", "a"]


def test_tree_builder_recurses_through_child_challenges():
    root_requirement = requirement(challenge_id=10, target=10, tier="MASTER")
    child_requirement = requirement(challenge_id=11, target=5, tier="GOLD")
    root = CatalogChallenge(10, "Autoridad", "Descripción", 1, True, False, root_requirement)
    child = CatalogChallenge(11, "Rama", "Descripción", 10, False, False, child_requirement)
    service = __import__("app.services.title_progress", fromlist=["TitleProgressService"]).TitleProgressService(None, None, 60)
    tree = service._build_tree_node(root, root_requirement, {}, {10: root, 11: child}, {10: [11]}, set())
    assert tree.challengeName == "Autoridad"
    assert len(tree.children) == 1
    assert tree.children[0].challengeName == "Rama"
