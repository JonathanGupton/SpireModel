from typing import Generator

from SpireModel.components import acquire
from SpireModel.components import skip
from SpireModel.components import CHARACTERS


class Log:
    pass


def tokenize_number(number: str) -> Generator[str, None, None]:
    """Takes a number in string form and splits it into individual characters"""
    for n in number:
        yield n


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


def tokenize_card(card: str) -> tuple[str, ...]:
    if "+" in card:
        card, level = card.split("+")
        return card, *tokenize_number(level)
    return (card,)


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
