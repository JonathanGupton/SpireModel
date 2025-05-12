from collections import defaultdict
from typing import Generator

from SpireModel.components import acquire
from SpireModel.components import battle
from SpireModel.components import go_to
from SpireModel.components import player_chose
from SpireModel.components import skip
from SpireModel.components import CHARACTERS


def tokenize_number(number: str) -> Generator[str, None, None]:
    """Takes a number in string form and splits it into individual characters"""
    for n in number:
        yield n


def tokenize_card(card: str) -> tuple[str, ...]:
    if "+" in card:
        card, level = card.split("+")
        return card, *tokenize_number(level)
    return (card,)


def tokenize_damage_taken(damage_taken: int | str) -> tuple[str, ...]:
    """
    LOSE [N] HEALTH
    """

    return "LOSE", *tokenize_number(str(damage_taken)), "HEALTH"


def tokenize_health_healed(health_healed: int | str):
    """
    GAIN [N] HEALTH
    """
    return "GAIN", *tokenize_number(str(health_healed)), "HEALTH"


def tokenize_max_health_gained(max_health_gained: int | str):
    """
    INCREASE [N] MAX HEALTH
    """
    return "INCREASE", *tokenize_number(str(max_health_gained)), "MAX HEALTH"


def tokenize_max_health_lost(max_health_lost: int | str):
    """
    DECREASE [N] MAX HEALTH
    """
    return "DECREASE", *tokenize_number(str(max_health_lost)), "MAX HEALTH"


def tokenize_gold_gain(gold_gained: int | str) -> tuple[str, ...]:
    """
    ACQUIRE [N] GOLD
    """
    return "ACQUIRE", *tokenize_number(str(gold_gained)), "GOLD"


def tokenize_gold_lost(gold_lost: int | str) -> tuple[str, ...]:
    """
    LOSE [N] GOLD
    """
    return "LOSE", *tokenize_number(str(gold_lost)), "GOLD"


def tokenize_event_card_acquisition(cards):
    """
    Need to iterate over cards and acquire with tokenize_card?
    """
    # TODO:  Whatever this is
    pass


def tokenize_remove_card(card: str) -> tuple[str, ...]:
    """
    REMOVE [CARD] [optional N]
    """
    return "REMOVE", *tokenize_card(card)


def tokenize_upgrade_card(card: str) -> tuple[str, ...]:
    """UPGRADE CARD [N]"""
    return "UPGRADE", *tokenize_card(card)


def tokenize_event_relic_acquisition(relics):
    """
    Need to iterate over relics and call acquire(relic)
    """
    # TODO:  Whatever this is
    pass


def get_character_token(data) -> tuple[str]:
    return (data["character_chosen"],)


def get_ascension_tokens(data) -> tuple[str, ...]:
    if data["is_ascension_mode"]:
        return "ASCENSION MODE", *tokenize_number(data["ascension_level"])
    return ()


def get_starting_cards(data) -> tuple[str, ...]:
    character = data["character_chosen"]
    if character not in CHARACTERS:
        raise ValueError(f"{character} not found in f{CHARACTERS}")
    match character:
        case "IRONCLAD":
            card_count = (("Strike", 5), ("Defend", 4), ("Bash", 1))
        case "DEFECT":
            card_count = (("Strike", 4), ("Defend", 4), ("Zap", 1), ("Dualcast", 1))
        case "THE_SILENT":
            card_count = (
                ("Strike", 5),
                ("Defend", 5),
                ("Survivor", 1),
                ("Neutralize", 1),
            )
        case "WATCHER":
            card_count = (
                ("Strike", 4),
                ("Defend", 4),
                ("Eruption", 1),
                ("Vigilance", 1),
            )
        case _:
            card_count = ()

    return tuple(acquire(card) for card, count in card_count for _ in range(count))


def get_starting_relics(data) -> tuple[str, ...]:
    character = data["character_chosen"]
    if character not in CHARACTERS:
        raise ValueError(f"{character} not found in f{CHARACTERS}")
    match character:
        case "IRONCLAD":
            relic = "Burning Blood"
        case "DEFECT":
            relic = "Cracked Core"
        case "THE_SILENT":
            relic = "Ring of the Snake"
        case "WATCHER":
            relic = "PureWater"
        case _:
            relic = ""
    return (acquire(relic),)


def get_starting_gold():
    return "ACQUIRE", "9", "9", "GOLD"


def get_neow_bonus(data):
    return "NEOW BONUS", data["neow_bonus"]


def get_neow_cost(data):
    if neow_cost := data.get("neow_cost", ""):
        return "NEOW COST", neow_cost
    return ()


def parse_card_choices(card_choices: list[dict]) -> dict[int, tuple[str, ...]]:
    card_choices_by_floor: dict[int, tuple[str, ...]] = {}
    for choices in card_choices:
        floor = choices["floor"]
        picked = ()

        if "picked" in choices:
            tokens = tokenize_card(choices["picked"])
            picked = (acquire(tokens[0]), *tokens[1:])

        not_picked_cards = []
        for card in choices["not_picked"]:
            tokens = tokenize_card(card)
            not_picked_cards.append(skip(tokens[0]))
            not_picked_cards.extend(tokens[1:])
        card_choices_by_floor[floor] = (*picked, *not_picked_cards)
    return card_choices_by_floor


def _parse_enemy_damage_taken(battle_info: dict) -> tuple[str, ...]:
    return (battle(battle_info["enemies"]),)


def parse_damage_taken(damage_taken: list[dict]) -> dict[int, tuple[str, ...]]:
    damage_taken_by_floor: dict[int, tuple[str, ...]] = {}
    for floor in damage_taken:
        floor_number = floor["floor"]
        if "enemies" in floor:
            damage_taken_by_floor[floor_number] = _parse_enemy_damage_taken(floor)
        else:
            print(floor)
            raise ValueError("Enemies not found in floor")
    return damage_taken_by_floor


def parse_potions_obtained(
    potions: list[dict[str, float | str]],
) -> dict[int, tuple[str]]:
    return {
        int(potion_obj["floor"]): (acquire(potion_obj["potion"]),)
        for potion_obj in potions
    }


def parse_items_purchased(
    items_purchased: list[str], item_purchase_floors: list[int]
) -> dict[int, list[str]]:
    items_by_floor = defaultdict(list)
    for floor, item in zip(item_purchase_floors, items_purchased):
        items_by_floor[floor].append(acquire(item))
    return items_by_floor


def parse_path_per_floor(
    path_per_floor: list[str | None],
) -> dict[int, dict[int, tuple[str]]]:
    path_map = defaultdict(dict)
    level = 0
    floor_number = 1
    for floor in path_per_floor:
        if floor is None:
            level += 1
            continue
        path_map[level][floor_number] = (go_to(floor),)
        floor_number += 1
    return path_map


def parse_cards_transformed(cards_transformed: list[str]) -> tuple[str, ...]:
    """TRANSFORM [card] [N]"""
    # TODO:  Whatever this is
    pass


def tokenize_relic_lost(relic: str) -> str:
    """REMOVE [relic]"""
    # TODO:  Whatever this is
    pass


def parse_relics_lost(relics: list[str]) -> tuple[str, ...]:
    # TODO:  Whatever this is
    pass


def tokenize_knowing_skull_choices(event_choice: str) -> str:
    """Convert the lengthy Knowing Skull choice down to one word per option"""
    if not isinstance(event_choice, str):
        raise TypeError("Expects string")
    if event_choice == "":
        return "SKIP"
    options = sorted(list(set(event_choice.strip().split(" "))))
    return " ".join(options)


def parse_event_choices(event_choices: list[dict[str, int | str]]):
    event_by_floor: dict[int, list[str]] = defaultdict(list)
    for event in event_choices:
        floor = event["floor"]
        event_name = event_name(event["event_name"])
        event_by_floor[floor].append(event_name)
        player_choice = event["player_choice"]
        if player_choice == "Knowing Skull":
            player_choice = tokenize_knowing_skull_choices(player_choice)
        event_by_floor[floor].append(player_chose(player_choice))

        if event.get("damage_healed", 0) != 0:
            pass
        """
        "potions_obtained"

        """

    """
    Prepped functions:
    "event_name"
    "floor"
    "player_choice"
    "damage_healed"
    "damage_taken"
    "max_hp_gain"
    "max_hp_loss"
    "gold_loss"
    "gold_gain"
    "cards_obtained" 
    "cards_removed"
    "cards_upgraded"
    "relics_obtained"
    "cards_transformed"
    "relics_lost"
    """
