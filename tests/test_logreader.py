import pytest

from SpireModel.logreader import STARTING_CARDS
from SpireModel.logreader import get_ascension_tokens
from SpireModel.logreader import get_character_token
from SpireModel.logreader import get_neow_bonus
from SpireModel.logreader import get_neow_cost
from SpireModel.logreader import get_starting_cards
from SpireModel.logreader import get_starting_gold
from SpireModel.logreader import parse_boss_relic_values
from SpireModel.logreader import parse_boss_relics_obtained_by_floor
from SpireModel.logreader import parse_campfire_choices_by_floor
from SpireModel.logreader import parse_card_choices_by_floor
from SpireModel.logreader import parse_events_by_floor
from SpireModel.logreader import parse_relics_obtained_by_floor
from SpireModel.logreader import _tokenize_into_masked_digits
from SpireModel.logreader import parse_purchases_by_floor
from SpireModel.logreader import parse_items_purged_by_floor
from SpireModel.logreader import parse_potion_usage_by_floor
from SpireModel.logreader import standardize_strikes_and_defends
from SpireModel.logreader import tokenize_card
from SpireModel.logreader import tokenize_damage_taken
from SpireModel.logreader import tokenize_gold_lost
from SpireModel.logreader import tokenize_health_healed
from SpireModel.logreader import tokenize_max_health_gained


def test_each_card_remove():
    events = [
        {
            "cards_removed": ["Strike_R", "Strike_R+1"],
            "player_choice": "Card Removal",
            "event_name": "The Cleric",
            "floor": 5,
        },
    ]
    parsed = parse_events_by_floor(events)
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
    parsed = parse_events_by_floor(events)
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
    out = parse_events_by_floor(events)
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


class TestTokenizeCard:
    def test_tokenize_card_base(self):
        card = tokenize_card("Strike_G")
        assert card == ("Strike",)

    def test_tokenize_card_plus_one(self):
        card = tokenize_card("Strike_G+1")
        assert card == ("Strike", "1")

    def test_tokenize_card_plus_number(self):
        card = tokenize_card("Searing Blow+99")
        assert card == ("Searing Blow", "9X", "9")


class TestEventProcessing:
    def test_tokenize_max_hp_gain(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "max_hp_gain": 275,
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:7] == ("INCREASE", "2XX", "7X", "5", "MAX HEALTH")

    def test_tokenize_max_hp_loss(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "max_hp_loss": 275,
            },
        ]
        out = parse_events_by_floor(events)
        print(out)
        out = out[5]
        assert out[2:7] == ("DECREASE", "2XX", "7X", "5", "MAX HEALTH")

    def test_relics_obtained(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "relics_obtained": ["Relic obtained 1", "Relic obtained 2"],
            }
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:4] == ("ACQUIRE", "Relic obtained 1")

    def test_relics_lost(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "relics_lost": ["Relic lost 1", "Relic lost 2"],
            }
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        print(out)
        assert out[2:4] == ("REMOVE", "Relic lost 1")

    def test_acquire_potion(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "potions_obtained": ["Potion obtained 1", "Potion obtained 2"],
            }
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        print(out)
        assert out[2:4] == ("ACQUIRE", "Potion obtained 1")

    def test_tokenize_transform_card(self):
        events = [
            {
                "cards_transformed": ["Strike_P"],
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "cards_obtained": ["Wallop"],
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:4] == ("TRANSFORM", "Strike")

    def test_tokenize_damage_taken(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "damage_taken": 99.0,
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:6] == ("LOSE", "9X", "9", "HEALTH")

    def test_tokenize_damage_healed(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "damage_healed": 99.0,
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:6] == ("GAIN", "9X", "9", "HEALTH")

    def test_tokenize_gold_gain(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "gold_gain": 275,
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:7] == ("ACQUIRE", "2XX", "7X", "5", "GOLD")

    def test_tokenize_gold_loss(self):
        events = [
            {
                "player_choice": "Change",
                "event_name": "Living Wall",
                "floor": 5,
                "gold_loss": 275,
            },
        ]
        out = parse_events_by_floor(events)
        out = out[5]
        assert out[2:7] == ("LOSE", "2XX", "7X", "5", "GOLD")


class TestTokenizeDamageTaken:
    def test_tokenize_1_damage(self):
        damage = 1
        damage_out = tokenize_damage_taken(damage)
        assert damage_out == ("LOSE", "1", "HEALTH")

    def test_tokenize_10_damage(self):
        damage = 10
        damage_out = tokenize_damage_taken(damage)
        assert damage_out == ("LOSE", "1X", "0", "HEALTH")


class TestDamageHealed:
    @pytest.mark.parametrize(
        "health,expected",
        [(1, ("GAIN", "1", "HEALTH")), (10, ("GAIN", "1X", "0", "HEALTH"))],
    )
    def test_tokenize_health_healed(self, health, expected):
        assert tokenize_health_healed(health) == expected

    @pytest.mark.parametrize(
        "health,expected",
        [("1", ("GAIN", "1", "HEALTH")), ("10", ("GAIN", "1X", "0", "HEALTH"))],
    )
    def test_tokenize_health_healed_strs(self, health, expected):
        assert tokenize_health_healed(health) == expected


class TestTokenizeMaxHealthGained:
    @pytest.mark.parametrize(
        "max_health,expected",
        [
            (1, ("INCREASE", "1", "MAX HEALTH")),
            (200, ("INCREASE", "2XX", "0X", "0", "MAX HEALTH")),
        ],
    )
    def test_max_health_gained_ints(self, max_health, expected):
        assert tokenize_max_health_gained(max_health) == expected

    @pytest.mark.parametrize(
        "max_health,expected",
        [
            ("1", ("INCREASE", "1", "MAX HEALTH")),
            ("200", ("INCREASE", "2XX", "0X", "0", "MAX HEALTH")),
        ],
    )
    def test_max_health_gained_ints(self, max_health, expected):
        assert tokenize_max_health_gained(max_health) == expected


class TestTokenizeGoldLost:
    @pytest.mark.parametrize(
        "gold_lost,expected",
        [(1, ("LOSE", "1", "GOLD")), (123, ("LOSE", "1XX", "2X", "3", "GOLD"))],
    )
    def test_tokenize_gold_lost_int(self, gold_lost, expected):
        assert tokenize_gold_lost(gold_lost) == expected

    @pytest.mark.parametrize(
        "gold_lost,expected",
        [("1", ("LOSE", "1", "GOLD")), ("123", ("LOSE", "1XX", "2X", "3", "GOLD"))],
    )
    def test_tokenize_gold_lost_str(self, gold_lost, expected):
        assert tokenize_gold_lost(gold_lost) == expected


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
    parsed_choices = parse_campfire_choices_by_floor(campfire_choices)
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


def test_parse_floor_purchases():
    items_purchased = [
        "Apotheosis",
        "Loop+1",
        "Happy Flower",
        "Sweeping Beam+1",
        "Secret Technique",
    ]
    item_purchase_floors = [7, 7, 38, 38, 38]
    parsed_purchases = parse_purchases_by_floor(
        items_purchased, item_purchase_floors
    )
    assert len(parsed_purchases) == len(set(item_purchase_floors))
    assert parsed_purchases[7] == ["ACQUIRE", "Apotheosis", "ACQUIRE", "Loop", "1"]
    assert parsed_purchases[38] == [
        "ACQUIRE",
        "Happy Flower",
        "ACQUIRE",
        "Sweeping Beam",
        "1",
        "ACQUIRE",
        "Secret Technique",
    ]


def test_parse_items_purged():
    items_purged = ["Strike_G", "Regret", "Strike_G+1"]
    items_purged_floors = [2, 7, 20]
    parsed_purged = parse_items_purged_by_floor(items_purged, items_purged_floors)
    assert len(parsed_purged) == len(set(items_purged_floors))
    assert parsed_purged[2] == ["REMOVE", "Strike"]
    assert parsed_purged[7] == ["REMOVE", "Regret"]
    assert parsed_purged[20] == ["REMOVE", "Strike", "1"]


def test_parse_potion_usage():
    potions_obtained = [
        {"floor": 6, "key": "Strength Potion"},
        {"floor": 7, "key": "FairyPotion"},
        {"floor": 21, "key": "Explosive Potion"},
        {"floor": 28, "key": "BlessingOfTheForge"},
        {"floor": 29, "key": "BloodPotion"},
        {"floor": 30, "key": "Energy Potion"},
    ]
    potion_usage = [7, 28, 30, 31, 31]
    potion_activity = parse_potion_usage_by_floor(potions_obtained, potion_usage)
    assert potion_activity


def test_parse_potion_usage_single_potion_acquired_then_used():
    potions_obtained = [{"floor": 6, "key": "Strength Potion"}]
    potion_usage = [7]
    potion_activity = parse_potion_usage_by_floor(potions_obtained, potion_usage)
    assert potion_activity == {7: ("POTION USED", "Strength Potion")}


def test_parse_potion_usage_two_potions_acquired_then_used():
    potions_obtained = [
        {"floor": 6, "key": "Strength Potion"},
        {"floor": 7, "key": "Dummy Potion"},
    ]
    potion_usage = [8, 8]
    potion_activity = parse_potion_usage_by_floor(potions_obtained, potion_usage)
    assert potion_activity == {
        8: ("POTION USED", "Strength Potion", "POTION USED", "Dummy Potion")
    }


def test_parse_potion_usage_three_potions_acquired_two_used():
    potions_obtained = [
        {"floor": 6, "key": "Strength Potion"},
        {"floor": 7, "key": "Dummy Potion"},
        {"floor": 8, "key": "Dummy Potion"},
    ]
    potion_usage = [9, 9]
    potion_activity = parse_potion_usage_by_floor(potions_obtained, potion_usage)
    assert potion_activity == {
        9: (
            "POTION POTENTIALLY USED",
            "Strength Potion",
            "POTION POTENTIALLY USED",
            "Dummy Potion",
        )
    }


def test_parse_potion_usage_three_potions_acquired_two_used():
    potions_obtained = [
        {"floor": 6, "key": "Strength Potion"},
        {"floor": 7, "key": "Dummy Potion"},
        {"floor": 8, "key": "Dummy Potion"},
    ]
    potion_usage = [9, 9]
    potion_activity = parse_potion_usage_by_floor(potions_obtained, potion_usage)
    assert potion_activity == {
        9: (
            "POTION POTENTIALLY USED",
            "Strength Potion",
            "POTION POTENTIALLY USED",
            "Dummy Potion",
        )
    }


class TestStandardizeStrikesAndDefends:
    def test_defend_r_returns_defend(self):
        card = "Defend_R"
        card = standardize_strikes_and_defends(card)
        assert card == "Defend"

    def test_defend_r1_returns_defend_1(self):
        card = "Defend_R+1"
        card = standardize_strikes_and_defends(card)
        assert card == "Defend+1"

    def test_strike_r_returns_strike(self):
        card = "Strike_R"
        card = standardize_strikes_and_defends(card)
        assert card == "Strike"

    def test_strike_r1_returns_strike_1(self):
        card = "Strike_R+1"
        card = standardize_strikes_and_defends(card)
        assert card == "Strike+1"

    def test_unrelated_card_returns_itself(self):
        card = "Unrelated"
        card = standardize_strikes_and_defends(card)
        assert card == "Unrelated"


class TestGetCharacterToken:
    @pytest.mark.parametrize(
        "character",
        [
            "IRONCLAD",
            "DEFECT",
            "THE_SILENT",
            "WATCHER",
        ],
    )
    def test_get_character_token_valid_character(self, character):
        data = {"character_chosen": character}
        assert get_character_token(data) == (character,)

    def test_get_character_token_invalid_character(self):
        data = {"character_chosen": "invalid"}
        with pytest.raises(ValueError):
            get_character_token(data)

    def test_get_character_token_non_dict_input(self):
        data = "not a dict"
        with pytest.raises(TypeError):
            get_character_token(data)

    def test_get_character_token_non_str_character_chosen(self):
        data = {"character_chosen": 123}
        with pytest.raises(TypeError):
            get_character_token(data)

    def test_get_character_token_missing_character_chosen(self):
        data = {}
        with pytest.raises(ValueError):
            get_character_token(data)


class TestGetAscensionTokens:
    @pytest.mark.parametrize(
        "data,expected",
        [
            (({"is_ascension_mode": False}), ()),
            (
                {"is_ascension_mode": True, "ascension_level": 1},
                ("ASCENSION MODE", "1"),
            ),
            (
                {"is_ascension_mode": True, "ascension_level": 15},
                ("ASCENSION MODE", "1X", "5"),
            ),
        ],
    )
    def test_get_ascension_token(self, data, expected):
        assert get_ascension_tokens(data) == expected

    def test_get_ascension_token_ascension_mode_non_bool(self):
        data = {"is_ascension_mode": 0}
        assert get_ascension_tokens(data) == ()

    def test_get_ascension_tokens_non_dict_input(self):
        data = "not a dict"
        with pytest.raises(TypeError):
            get_ascension_tokens(data)

    def test_get_ascension_tokens_non_digit_ascension_level(self):
        data = {"is_ascension_mode": True, "ascension_level": "a"}
        with pytest.raises(ValueError):
            get_ascension_tokens(data)

    def test_get_ascension_tokens_missing_ascension_level(self):
        data = {"is_ascension_mode": True}
        with pytest.raises(ValueError):
            get_ascension_tokens(data)

    def test_get_ascension_tokens_non_int_or_str_ascension_level(self):
        data = {"is_ascension_mode": True, "ascension_level": [1, 2, 3]}
        with pytest.raises(TypeError):
            get_ascension_tokens(data)

    def test_get_ascension_tokens_valid_input(self):
        data = {"is_ascension_mode": True, "ascension_level": 15}
        assert get_ascension_tokens(data) == ("ASCENSION MODE", "1X", "5")


class TestGetStartingCards:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"character_chosen": "IRONCLAD"},
                STARTING_CARDS["IRONCLAD"],
            ),
            (
                {"character_chosen": "DEFECT"},
                STARTING_CARDS["DEFECT"],
            ),
            (
                {"character_chosen": "THE_SILENT"},
                STARTING_CARDS["THE_SILENT"],
            ),
            (
                {"character_chosen": "WATCHER"},
                STARTING_CARDS["WATCHER"],
            ),
        ],
    )
    def test_get_starting_cards_valid_character(self, data, expected):
        assert get_starting_cards(data) == expected

    def test_get_starting_cards_non_dict_input(self):
        data = "not a dict"
        with pytest.raises(TypeError):
            get_starting_cards(data)

    def test_non_character_value(self):
        data = {"character_chosen": "not_a_character"}
        with pytest.raises(TypeError):
            get_starting_cards(data)


class TestGetStartingGold:
    def test_get_starting_gold(self):
        assert get_starting_gold() == ("ACQUIRE", "9X", "9", "GOLD")


class TestGetNeowBonus:
    def test_get_neow_bonus_non_dict_input(self):
        data = "not a dict"
        with pytest.raises(TypeError):
            get_neow_bonus(data)

    def test_get_neow_bonus_missing_key(self):
        data = {}
        assert get_neow_bonus(data) == ()

    def test_get_neow_bonus_non_str_value(self):
        data = {"neow_bonus": 123}
        with pytest.raises(TypeError):
            get_neow_bonus(data)

    def test_get_neow_bonus_empty_str_value(self):
        data = {"neow_bonus": ""}
        assert get_neow_bonus(data) == ()

    def test_get_neow_bonus_valid_input(self):
        data = {"neow_bonus": "Test Neow Bonus"}
        assert get_neow_bonus(data) == ("NEOW BONUS", "Test Neow Bonus")


class TestGetNeowCost:
    def test_get_neow_cost_non_dict_input(self):
        data = "not a dict"
        with pytest.raises(TypeError):
            get_neow_cost(data)

    def test_get_neow_cost_missing_key(self):
        data = {}
        assert get_neow_cost(data) == ()

    def test_get_neow_cost_non_str_value(self):
        data = {"neow_cost": 123}
        with pytest.raises(TypeError):
            get_neow_cost(data)

    def test_get_neow_cost_empty_str_value(self):
        data = {"neow_cost": ""}
        assert get_neow_cost(data) == ()

    def test_get_neow_cost_valid_input(self):
        data = {"neow_cost": "Test Neow Cost"}
        assert get_neow_cost(data) == ("NEOW COST", "Test Neow Cost")


class TestParseCardChoices:
    def test_parse_card_choices_non_list_input(self):
        card_choices = "not a list"
        with pytest.raises(TypeError):
            parse_card_choices_by_floor(card_choices)

    def test_parse_card_choices_empty_list(self):
        card_choices = []
        assert parse_card_choices_by_floor(card_choices) == {}

    def test_parse_card_choices_non_dict_element(self):
        card_choices = [123]
        with pytest.raises(TypeError):
            parse_card_choices_by_floor(card_choices)

    def test_parse_card_choices_missing_floor(self):
        card_choices = [{"picked": "Test Card"}]
        with pytest.raises(KeyError):
            parse_card_choices_by_floor(card_choices)

    def test_parse_card_choices_non_str_picked(self):
        card_choices = [{"picked": 123, "floor": 1}]
        with pytest.raises(TypeError):
            parse_card_choices_by_floor(card_choices)

    def test_parse_card_choices_non_list_not_picked(self):
        card_choices = [{"picked": "Test Card", "floor": 1, "not_picked": 123}]
        with pytest.raises(TypeError):
            parse_card_choices_by_floor(card_choices)

    def test_parse_card_choices_valid_input(self):
        card_choices = [
            {
                "not_picked": ["Backflip", "Crippling Poison"],
                "picked": "Accuracy",
                "floor": 1,
            },
            {
                "not_picked": ["Sucker Punch", "Tactician"],
                "picked": "Infinite Blades",
                "floor": 5,
            },
        ]
        assert parse_card_choices_by_floor(card_choices) == {
            1: ("ACQUIRE", "Accuracy", "SKIP", "Backflip", "SKIP", "Crippling Poison"),
            5: (
                "ACQUIRE",
                "Infinite Blades",
                "SKIP",
                "Sucker Punch",
                "SKIP",
                "Tactician",
            ),
        }

    def test_parse_card_choices_are_upgraded(self):
        card_choices = [
            {
                "not_picked": ["Backflip+99", "Crippling Poison"],
                "picked": "Accuracy+1",
                "floor": 1,
            },
        ]
        assert parse_card_choices_by_floor(card_choices) == {
            1: (
                "ACQUIRE",
                "Accuracy",
                "1",
                "SKIP",
                "Backflip",
                "9X",
                "9",
                "SKIP",
                "Crippling Poison",
            ),
        }

    def test_parse_card_choices_none_taken(self):
        card_choices = [
            {
                "not_picked": ["Accuracy+1", "Backflip+99", "Crippling Poison"],
                "floor": 1,
            }
        ]
        assert parse_card_choices_by_floor(card_choices) == {
            1: (
                "SKIP",
                "Accuracy",
                "1",
                "SKIP",
                "Backflip",
                "9X",
                "9",
                "SKIP",
                "Crippling Poison",
            ),
        }


class TestRelicsObtained:
    def test_parse_relics_obtained_by_floor(self):
        relics_obtained = [
            {"floor": 7, "key": "Juzu Bracelet"},
            {"floor": 9, "key": "Mercury Hourglass"},
            {"floor": 26, "key": "Singing Bowl"},
        ]
        assert parse_relics_obtained_by_floor(relics_obtained) == {
            7: ("ACQUIRE", "Juzu Bracelet"),
            9: ("ACQUIRE", "Mercury Hourglass"),
            26: ("ACQUIRE", "Singing Bowl"),
        }


class TestBossRelicsObtainedByFloor:
    def test_boss_relics_obtained_by_floor_one_boss_and_one_relic(self):
        path_taken = [
            "M",
            "M",
            "?",
            "?",
            "M",
            "M",
            "E",
            "R",
            "T",
            "R",
            "M",
            "$",
            "R",
            "$",
            "R",
            "BOSS",
            "M",
            "?",
            "?",
            "M",
            "?",
            "R",
            "M",
            "?",
            "T",
            "?",
            "M",
            "M",
            "E",
            "M",
        ]
        boss_relics = [
            {"not_picked": ["Astrolabe", "Runic Dome"], "picked": "Mark of Pain"}
        ]
        assert parse_boss_relics_obtained_by_floor(boss_relics, path_taken) == {
            15: (
                "ACQUIRE",
                "Mark of Pain",
                "SKIP",
                "Astrolabe",
                "SKIP",
                "Runic Dome",
            )
        }

    def test_boss_relics_obtained_by_floor_two_bosses_and_one_relic(self):
        path_taken = [
            "M",
            "M",
            "?",
            "?",
            "M",
            "M",
            "E",
            "R",
            "T",
            "R",
            "M",
            "$",
            "R",
            "$",
            "R",
            "BOSS",
            "M",
            "?",
            "?",
            "M",
            "?",
            "R",
            "M",
            "?",
            "T",
            "?",
            "M",
            "M",
            "E",
            "M",
            "BOSS",
        ]
        boss_relics = [
            {"not_picked": ["Astrolabe", "Runic Dome"], "picked": "Mark of Pain"}
        ]
        assert parse_boss_relics_obtained_by_floor(boss_relics, path_taken) == {
            15: (
                "ACQUIRE",
                "Mark of Pain",
                "SKIP",
                "Astrolabe",
                "SKIP",
                "Runic Dome",
            )
        }

    def test_boss_relics_obtained_by_floor_two_bosses_and_two_relics(self):
        path_taken = [
            "M",
            "M",
            "?",
            "?",
            "M",
            "M",
            "E",
            "R",
            "T",
            "R",
            "M",
            "$",
            "R",
            "$",
            "R",
            "BOSS",
            "M",
            "?",
            "?",
            "M",
            "?",
            "R",
            "M",
            "?",
            "T",
            "?",
            "M",
            "M",
            "E",
            "M",
            "BOSS",
        ]
        boss_relics = [
            {"not_picked": ["Astrolabe", "Runic Dome"], "picked": "Mark of Pain"},
            {
                "not_picked": ["HoveringKite", "Busted Crown", "Velvet Choker"],
            },
        ]
        assert parse_boss_relics_obtained_by_floor(boss_relics, path_taken) == {
            15: (
                "ACQUIRE",
                "Mark of Pain",
                "SKIP",
                "Astrolabe",
                "SKIP",
                "Runic Dome",
            ),
            30: (
                "SKIP",
                "HoveringKite",
                "SKIP",
                "Busted Crown",
                "SKIP",
                "Velvet Choker",
            ),
        }

    def test_empty_boss_relics(self):
        """In case the player dies before defeating the boss"""
        path_taken = [
            "M",
            "?",
            "M",
            "?",
            "?",
            "R",
            "E",
            "M",
            "T",
            "M",
            "M",
            "$",
            "R",
            "M",
            "R",
            "BOSS",
        ]
        boss_relics = []
        assert parse_boss_relics_obtained_by_floor(boss_relics, path_taken) == {}


class TestParseBossRelicValues:
    def test_parse_boss_relic_values(self):
        assert parse_boss_relic_values(
            {"not_picked": ["Astrolabe", "Runic Dome"], "picked": "Mark of Pain"}
        ) == (
            "ACQUIRE",
            "Mark of Pain",
            "SKIP",
            "Astrolabe",
            "SKIP",
            "Runic Dome",
        )

    def test_parse_boss_relic_values_none_taken(self):
        assert parse_boss_relic_values(
            {
                "not_picked": ["HoveringKite", "Busted Crown", "Velvet Choker"],
            }
        ) == (
            "SKIP",
            "HoveringKite",
            "SKIP",
            "Busted Crown",
            "SKIP",
            "Velvet Choker",
        )
