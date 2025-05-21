from pytest import fixture

from SpireModel.logreader import parse_events
from SpireModel.logreader import _tokenize_into_masked_digits


@fixture()
def events_list():
    return [
        {
            "cards_removed": ["Strike_G"],
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 0.0,
            "event_name": "Purifier",
            "player_choice": "Purged",
            "floor": 2.0,
            "gold_loss": 0.0,
            "damage_taken": 0.0,
        },
        {
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 0.0,
            "event_name": "Back to Basics",
            "player_choice": "Simplicity",
            "floor": 20.0,
            "gold_loss": 0.0,
            "damage_taken": 0.0,
            "cards_upgraded": [
                "Strike_G",
                "Strike_G",
                "Strike_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
            ],
        },
        {
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 0.0,
            "event_name": "Big Fish",
            "player_choice": "Box",
            "floor": 1.0,
            "gold_loss": 0.0,
            "damage_taken": 0.0,
            "relics_obtained": ["Tiny Chest"],
            "cards_obtained": ["Regret"],
        },
        {
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 175.0,
            "event_name": "Liars Game",
            "player_choice": "AGREE",
            "floor": 5.0,
            "gold_loss": 0.0,
            "damage_taken": 0.0,
            "cards_obtained": ["Doubt"],
        },
        {
            "cards_removed": ["Doubt"],
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 0.0,
            "event_name": "The Cleric",
            "player_choice": "Card Removal",
            "floor": 10.0,
            "gold_loss": 50.0,
            "damage_taken": 0.0,
        },
    ]


def test_each_card_remove_is_single_string():
    events = [
        {
            "cards_removed": ["Strike_R"],
            "damage_healed": 0,
            "gold_gain": 0,
            "player_choice": "Card Removal",
            "damage_taken": 0,
            "max_hp_gain": 0,
            "max_hp_loss": 0,
            "event_name": "The Cleric",
            "floor": 5,
            "gold_loss": 50,
        },
    ]
    parsed = parse_events(events)
    out = parsed[5]
    assert "REMOVE Strike" in out


def test_each_card_upgrade_is_single_string():
    events = [
        {
            "damage_healed": 0.0,
            "max_hp_gain": 0.0,
            "max_hp_loss": 0.0,
            "gold_gain": 0.0,
            "event_name": "Back to Basics",
            "player_choice": "Simplicity",
            "floor": 20.0,
            "gold_loss": 0.0,
            "damage_taken": 0.0,
            "cards_upgraded": [
                "Strike_G",
                "Strike_G",
                "Strike_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
                "Defend_G",
            ],
        },
    ]
    parsed = parse_events(events)
    out = parsed[20]
    assert "UPGRADE Strike" in out


def test_parse_event():
    events = [
        {
            "damage_healed": 99.0,
            "gold_gain": 99.0,
            "player_choice": "Players Choice",
            "damage_taken": 99.0,
            "max_hp_gain": 100.0,
            "max_hp_loss": 1.0,
            "event_name": "Fake Event",
            "floor": 1,
            "gold_loss": 199.0,
            "cards_obtained": [
                "Strike_G",
                "Strike_G+1",
                "Defend_R",
                "Defend_S+1",
                "Searing Blow+99",
            ],
            "cards_removed": [
                "Strike_G",
                "Strike_G+1",
                "Defend_R",
                "Defend_S+1",
                "Searing Blow+99",
            ],
            "cards_upgraded": [
                "Strike_G",
                "Strike_G+1",
                "Defend_R",
                "Defend_S+1",
                "Searing Blow+99",
            ],
            "relics_obtained": ["Relic 1", "Relic 2"],
            "potions_obtained": ["Potion 1", "Potion 2"],
            "cards_transformed": [
                "Strike_G",
                "Strike_G+1",
                "Defend_R",
                "Defend_S+1",
                "Searing Blow+99",
            ],
            "relics_lost": ["Relic lost 1", "Relic lost 2"],
        }
    ]
    out = parse_events(events)
    print(out)
    assert out


def test_tokenize_into_masked_digits():
    single_num = "1"
    masked = tuple(_tokenize_into_masked_digits(single_num))
    assert masked == ("1",)

    tens_num = "19"
    masked = tuple(_tokenize_into_masked_digits(tens_num))
    assert masked == ("1X", "9")

    hundreds_num = "193"
    masked = tuple(_tokenize_into_masked_digits(hundreds_num))
    assert masked == ("1XX", "9X", "3")

    thousands_num = "1934"
    masked = tuple(_tokenize_into_masked_digits(thousands_num))
    assert masked == ("1XXX", "9XX", "3X", "4")
