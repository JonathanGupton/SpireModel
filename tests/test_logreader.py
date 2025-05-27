from pytest import fixture

from SpireModel.logreader import parse_campfire_choices
from SpireModel.logreader import parse_events
from SpireModel.logreader import _tokenize_into_masked_digits
from SpireModel.logreader import tokenize_card


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


def test_each_card_remove():
    events = [
        {
            "cards_removed": ["Strike_R", "Strike_R+1"],
            "player_choice": "Card Removal",
            "event_name": "The Cleric",
            "floor": 5,
        },
    ]
    parsed = parse_events(events)
    out = parsed[5]
    assert out[2:4] == ("REMOVE", "Strike")
    assert out[4:7] == ("REMOVE", "Strike", "1")


def test_each_card_upgrade():
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
                "Strike_G+1",
                "Searing Blow+99",
            ],
        },
    ]
    parsed = parse_events(events)
    out = parsed[20]
    assert ("UPGRADE", "Strike") == out[2:4]
    assert ("UPGRADE", "Strike", "1") == out[4:7]
    assert ("UPGRADE", "Searing Blow", "9X", "9") == out[7:11]


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


def test_tokenize_card():
    card = tokenize_card("Strike_G")
    assert card == ("Strike",)

    card = tokenize_card("Strike_G+1")
    assert card == ("Strike", "1")

    card = tokenize_card("Searing Blow+99")
    assert card == ("Searing Blow", "9X", "9")


def test_tokenize_transform_card():
    events = [
        {
            "cards_transformed": ["Strike_P"],
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "cards_obtained": ["Wallop"],
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:4] == ("TRANSFORM", "Strike")


def test_tokenize_damage_taken():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "damage_taken": 99.0,
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:6] == ("LOSE", "9X", "9", "HEALTH")


def test_tokenize_damage_healed():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "damage_healed": 99.0,
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:6] == ("GAIN", "9X", "9", "HEALTH")


def test_tokenize_gold_gain():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "gold_gain": 275,
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:7] == ("ACQUIRE", "2XX", "7X", "5", "GOLD")


def test_tokenize_gold_loss():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "gold_loss": 275,
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:7] == ("LOSE", "2XX", "7X", "5", "GOLD")


def test_tokenize_max_hp_gain():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "max_hp_gain": 275,
        },
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:7] == ("INCREASE", "2XX", "7X", "5", "MAX HEALTH")


def test_tokenize_max_hp_loss():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "max_hp_loss": 275,
        },
    ]
    out = parse_events(events)
    print(out)
    out = out[5]
    assert out[2:7] == ("DECREASE", "2XX", "7X", "5", "MAX HEALTH")


def test_relics_obtained():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "relics_obtained": ["Relic obtained 1", "Relic obtained 2"],
        }
    ]
    out = parse_events(events)
    out = out[5]
    assert out[2:4] == ("ACQUIRE", "Relic obtained 1")


def test_relics_lost():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "relics_lost": ["Relic lost 1", "Relic lost 2"],
        }
    ]
    out = parse_events(events)
    out = out[5]
    print(out)
    assert out[2:4] == ("REMOVE", "Relic lost 1")


def test_acquire_potion():
    events = [
        {
            "player_choice": "Change",
            "event_name": "Living Wall",
            "floor": 5,
            "potions_obtained": ["Potion obtained 1", "Potion obtained 2"],
        }
    ]
    out = parse_events(events)
    out = out[5]
    print(out)
    assert out[2:4] == ("ACQUIRE", "Potion obtained 1")


def test_parse_campfire_choices():
    campfire_choices = [
        {"data": "Fire Breathing+1", "floor": 8, "key": "SMITH"},
        {"data": "Armaments", "floor": 10, "key": "SMITH"},
        {"data": "Seeing Red", "floor": 13, "key": "SMITH"},
        {"data": "Fire Breathing", "floor": 15, "key": "SMITH"},
        {"floor": 23, "key": "REST"},
        {"floor": 1, "key": "LIFT"},
        {"floor": 2, "key": "DIG"},
        {"floor": 3, "key": "PURGE", "data": "Strike_B+1"},
        {"floor": 4, "key": "RECALL"},
    ]
    parsed_choices = parse_campfire_choices(campfire_choices)
    assert len(parsed_choices) == len(campfire_choices)
    assert parsed_choices[8] == ("SMITH", "Upgrade", "Fire Breathing", "1")
    assert parsed_choices[10] == ("SMITH", "Upgrade", "Armaments")
    assert parsed_choices[13] == ("SMITH", "Upgrade", "Seeing Red")
    assert parsed_choices[15] == ("SMITH", "Upgrade", "Fire Breathing")
    assert parsed_choices[23] == ("REST",)
    assert parsed_choices[1] == ("LIFT",)
    assert parsed_choices[2] == ("DIG",)
    assert parsed_choices[3] == (
        "REMOVE",
        "Strike",
        "1",
    )
    assert parsed_choices[4] == ("RECALL",)
