from collections import defaultdict
import logging
from typing import Generator, Any, Optional

from SpireModel.components import acquire
from SpireModel.components import battle
from SpireModel.components import go_to
from SpireModel.components import skip
from SpireModel.components import CHARACTERS


# --- Logging Setup ---
# Configure logging (you might want to configure this externally in a real application)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Tokenization Functions ---


def tokenize_number(number: str) -> Generator[str, None, None]:
    """Takes a number in string form and splits it into individual characters."""
    if not isinstance(number, str):
        logger.error(
            f"Invalid type for tokenize_number: expected str, got {type(number)}. Value: {number}"
        )
        raise TypeError(f"Input 'number' must be a string, got {type(number)}")
    if not number.isdigit():
        logger.warning(f"Input '{number}' to tokenize_number is not purely digits.")
        # Depending on requirements, you might raise ValueError here or allow non-digits
    try:
        for n in number:
            yield n
    except Exception as e:
        logger.exception(f"Unexpected error during number tokenization for '{number}'.")
        raise  # Re-raise the exception after logging


def tokenize_card(card: str) -> tuple[str, ...]:
    """Splits a card string like 'Bash+1' into ('Bash', '1') or ('Strike',)"""
    if not isinstance(card, str):
        logger.error(
            f"Invalid type for tokenize_card: expected str, got {type(card)}. Value: {card}"
        )
        raise TypeError(f"Input 'card' must be a string, got {type(card)}")

    try:
        if "+" in card:
            parts = card.split("+", 1)  # Split only once
            if len(parts) == 2 and parts[1].isdigit():
                card_name, level = parts
                logger.debug(
                    f"Tokenizing upgraded card: {card} -> ({card_name}, level {level})"
                )
                return card_name, *tokenize_number(level)
            else:
                logger.warning(
                    f"Card '{card}' contains '+' but not in expected 'Name+Level' format. Treating as simple card name."
                )
                return (card,)
        else:
            logger.debug(f"Tokenizing simple card: {card} -> ({card},)")
            return (card,)
    except Exception as e:
        logger.exception(f"Error tokenizing card: '{card}'")
        # Depending on strictness, either raise or return a default/error token
        # Raising is often better to signal failure clearly.
        raise ValueError(f"Failed to tokenize card: {card}") from e


def _tokenize_value_change(
    action: str, value: int | str, unit: str, value_type: str = "value"
) -> tuple[str, ...]:
    """Helper function for tokenizing gain/loss of health, gold, etc."""
    if not isinstance(value, (int, str)):
        logger.error(
            f"Invalid {value_type} type for {action}: expected int or str, got {type(value)}. Value: {value}"
        )
        raise TypeError(
            f"Input '{value_type}' must be an int or str, got {type(value)}"
        )
    try:
        str_value = str(value)
        tokens = action, *tokenize_number(str_value), unit
        logger.debug(f"Tokenized {action} {value} {unit}: {tokens}")
        return tokens
    except Exception as e:
        logger.exception(f"Error during tokenization: {action} {value} {unit}")
        raise ValueError(f"Failed to tokenize {action} {value} {unit}") from e


def tokenize_damage_taken(damage_taken: int | str) -> tuple[str, ...]:
    """LOSE [N] HEALTH"""
    return _tokenize_value_change("LOSE", damage_taken, "HEALTH", "damage_taken")


def tokenize_health_healed(health_healed: int | str) -> tuple[str, ...]:
    """GAIN [N] HEALTH"""
    return _tokenize_value_change("GAIN", health_healed, "HEALTH", "health_healed")


def tokenize_max_health_gained(max_health_gained: int | str) -> tuple[str, ...]:
    """INCREASE [N] MAX HEALTH"""
    return _tokenize_value_change(
        "INCREASE", max_health_gained, "MAX HEALTH", "max_health_gained"
    )


def tokenize_max_health_lost(max_health_lost: int | str) -> tuple[str, ...]:
    """DECREASE [N] MAX HEALTH"""
    return _tokenize_value_change(
        "DECREASE", max_health_lost, "MAX HEALTH", "max_health_lost"
    )


def tokenize_gold_gain(gold_gained: int | str) -> tuple[str, ...]:
    """ACQUIRE [N] GOLD"""
    return _tokenize_value_change("ACQUIRE", gold_gained, "GOLD", "gold_gained")


def tokenize_gold_lost(gold_lost: int | str) -> tuple[str, ...]:
    """LOSE [N] GOLD"""
    return _tokenize_value_change("LOSE", gold_lost, "GOLD", "gold_lost")


def tokenize_event_card_acquisition(cards: list[str]) -> tuple[str, ...]:
    """Generates ACQUIRE tokens for a list of cards from an event."""
    logger.warning(
        "tokenize_event_card_acquisition: Actual implementation depends on how event card data is structured. Assuming list of card strings."
    )
    if not isinstance(cards, list):
        logger.error(f"Expected list for event card acquisition, got {type(cards)}")
        raise TypeError("Input 'cards' must be a list")

    all_tokens: list[str] = []
    for card in cards:
        try:
            tokens = tokenize_card(card)
            # Assuming acquire takes the base name and level tokens follow
            all_tokens.extend((acquire(tokens[0]), *tokens[1:]))
            logger.debug(f"Event acquired card: {card} -> {tokens}")
        except Exception as e:
            logger.error(
                f"Failed to tokenize card '{card}' during event acquisition: {e}"
            )
            # Decide: skip this card, raise error, or add placeholder? Let's skip with error log.
            continue  # Skip this card
    return tuple(all_tokens)


def tokenize_remove_card(card: str) -> tuple[str, ...]:
    """REMOVE [CARD] [optional N]"""
    logger.debug(f"Tokenizing card removal: {card}")
    try:
        tokens = tokenize_card(card)
        return "REMOVE", *tokens
    except Exception as e:
        logger.exception(f"Error tokenizing card for removal: {card}")
        raise ValueError(f"Failed to tokenize card for removal: {card}") from e


def tokenize_upgrade_card(card: str) -> tuple[str, ...]:
    """UPGRADE CARD [N]"""
    logger.debug(f"Tokenizing card upgrade: {card}")
    try:
        tokens = tokenize_card(card)
        # Ensure it looks like an upgraded card (has level info)
        if len(tokens) > 1 and all(t.isdigit() for t in tokens[1:]):
            return "UPGRADE", *tokens
        else:
            # Handle case where base card name is passed (e.g., from event)
            # This assumes upgrade always results in +1 implicitly if level isn't known
            # Or maybe it should fail? Let's assume +1 for now.
            logger.warning(
                f"Card '{card}' passed to tokenize_upgrade_card lacks level info. Assuming upgrade to +1."
            )
            return "UPGRADE", tokens[0], "1"  # Implicit +1 upgrade?
            # Alternatively: raise ValueError(f"Cannot tokenize upgrade for '{card}': level information missing.")
    except Exception as e:
        logger.exception(f"Error tokenizing card for upgrade: {card}")
        raise ValueError(f"Failed to tokenize card for upgrade: {card}") from e


def tokenize_event_relic_acquisition(relics: list[str]) -> tuple[str, ...]:
    """Generates ACQUIRE tokens for a list of relics from an event."""
    logger.warning(
        "tokenize_event_relic_acquisition: Actual implementation depends on how event relic data is structured. Assuming list of relic strings."
    )
    if not isinstance(relics, list):
        logger.error(f"Expected list for event relic acquisition, got {type(relics)}")
        raise TypeError("Input 'relics' must be a list")

    all_tokens: list[str] = []
    for relic in relics:
        if not isinstance(relic, str) or not relic:
            logger.warning(
                f"Skipping invalid relic entry in event acquisition: {relic}"
            )
            continue
        try:
            token = acquire(relic)  # Relics are usually simple strings
            all_tokens.append(token)
            logger.debug(f"Event acquired relic: {relic} -> {token}")
        except Exception as e:
            logger.error(f"Failed to create acquire token for relic '{relic}': {e}")
            # Decide: skip, raise, placeholder? Skipping.
            continue
    return tuple(all_tokens)


# --- Data Parsing Functions ---


def get_character_token(data: dict[str, Any]) -> tuple[str]:
    """Extracts the character token."""
    try:
        character = data["character_chosen"]
        if not isinstance(character, str):
            raise TypeError(
                f"Expected string for 'character_chosen', got {type(character)}"
            )
        if character not in CHARACTERS:
            logger.warning(
                f"Character '{character}' not in known CHARACTERS: {CHARACTERS}"
            )
            # Depending on strictness, raise ValueError here
        logger.info(f"Character chosen: {character}")
        return (character,)
    except KeyError:
        logger.error("'character_chosen' key not found in data.")
        raise ValueError("Missing 'character_chosen' in input data")
    except TypeError as e:
        logger.error(f"Data structure error accessing character: {e}")
        raise  # Re-raise type error


def get_ascension_tokens(data: dict[str, Any]) -> tuple[str, ...]:
    """Gets ascension tokens if applicable."""
    try:
        is_ascension = data.get(
            "is_ascension_mode", False
        )  # Default to False if key missing
        if not isinstance(is_ascension, bool):
            logger.warning(
                f"Expected bool for 'is_ascension_mode', got {type(is_ascension)}. Assuming False."
            )
            is_ascension = False

        if is_ascension:
            ascension_level = data.get("ascension_level")
            if ascension_level is None:
                logger.error(
                    "Ascension mode is True, but 'ascension_level' is missing."
                )
                raise ValueError("Missing 'ascension_level' while in ascension mode")
            if not isinstance(ascension_level, (str, int)):
                logger.error(
                    f"Expected int or str for 'ascension_level', got {type(ascension_level)}. Value: {ascension_level}"
                )
                raise TypeError("Invalid type for 'ascension_level'")

            str_level = str(ascension_level)
            logger.info(f"Ascension mode active: Level {str_level}")
            return "ASCENSION MODE", *tokenize_number(str_level)
        else:
            logger.info("Ascension mode not active.")
            return ()
    except (TypeError, ValueError) as e:
        logger.error(f"Error processing ascension data: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error getting ascension tokens.")
        raise


def get_starting_cards(data: dict[str, Any]) -> tuple[str, ...]:
    """Determines starting cards based on character."""
    try:
        character = data["character_chosen"]
        if character not in CHARACTERS:
            logger.error(
                f"Unknown character '{character}' found when getting starting cards. Known: {CHARACTERS}"
            )
            raise ValueError(
                f"Character '{character}' not found in known CHARACTERS: {CHARACTERS}"
            )

        logger.debug(f"Determining starting cards for: {character}")
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
            # No default case needed due to initial check

        tokens = []
        for card, count in card_count:
            for _ in range(count):
                try:
                    # Starting cards are never upgraded
                    base_card_tokens = tokenize_card(card)
                    tokens.append(acquire(base_card_tokens[0]))  # Acquire base name
                except Exception as e:
                    logger.error(
                        f"Failed to tokenize or acquire starting card '{card}': {e}"
                    )
                    # Decide whether to raise or continue; raising is safer if starting deck is critical
                    raise ValueError(f"Error processing starting card {card}") from e

        logger.info(f"Generated {len(tokens)} starting card tokens for {character}.")
        return tuple(tokens)

    except KeyError:
        logger.error("'character_chosen' key not found in data for starting cards.")
        raise ValueError("Missing 'character_chosen' in input data")
    except (TypeError, ValueError) as e:
        logger.error(f"Error getting starting cards: {e}")
        raise


def get_starting_relics(data: dict[str, Any]) -> tuple[str, ...]:
    """Determines starting relic based on character."""
    try:
        character = data["character_chosen"]
        if character not in CHARACTERS:
            logger.error(
                f"Unknown character '{character}' found when getting starting relic. Known: {CHARACTERS}"
            )
            raise ValueError(
                f"Character '{character}' not found in known CHARACTERS: {CHARACTERS}"
            )

        logger.debug(f"Determining starting relic for: {character}")
        match character:
            case "IRONCLAD":
                relic = "Burning Blood"
            case "DEFECT":
                relic = "Cracked Core"
            case "THE_SILENT":
                relic = "Ring of the Snake"
            case "WATCHER":
                relic = "Pure Water"  # Corrected name
            # No default case needed due to initial check

        if relic:
            logger.info(f"Starting relic for {character}: {relic}")
            try:
                return (acquire(relic),)
            except Exception as e:
                logger.error(
                    f"Failed to create acquire token for starting relic '{relic}': {e}"
                )
                raise ValueError(f"Error processing starting relic {relic}") from e
        else:
            # Should not happen with current CHARACTERS check, but as safeguard:
            logger.error(f"No starting relic defined for valid character: {character}")
            return ()  # Or raise error

    except KeyError:
        logger.error("'character_chosen' key not found in data for starting relics.")
        raise ValueError("Missing 'character_chosen' in input data")
    except (TypeError, ValueError) as e:
        logger.error(f"Error getting starting relics: {e}")
        raise


def get_starting_gold() -> tuple[str, ...]:
    """Returns fixed starting gold tokens (99 Gold)."""
    logger.info("Generating starting gold tokens (99).")
    try:
        # Replicates tokenize_gold_gain("99")
        return "ACQUIRE", "9", "9", "GOLD"
    except Exception as e:
        # Unlikely, but capture potential errors in tokenize_number if it were complex
        logger.exception("Unexpected error generating starting gold tokens.")
        raise RuntimeError("Failed to generate starting gold tokens") from e


def get_neow_bonus(data: dict[str, Any]) -> tuple[str, ...]:
    """Gets Neow bonus token."""
    try:
        bonus = data.get("neow_bonus")
        if bonus is None:
            logger.warning("'neow_bonus' key not found in data.")
            return ()  # No bonus recorded or key missing
        if not isinstance(bonus, str):
            logger.error(
                f"Expected string for 'neow_bonus', got {type(bonus)}. Value: {bonus}"
            )
            raise TypeError("Invalid type for 'neow_bonus'")

        logger.info(f"Neow bonus: {bonus}")
        # Assuming the bonus string itself is the token
        return "NEOW BONUS", bonus
    except TypeError as e:
        logger.error(f"Data structure error accessing Neow bonus: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error getting Neow bonus.")
        raise


def get_neow_cost(data: dict[str, Any]) -> tuple[str, ...]:
    """Gets Neow cost token if present."""
    try:
        cost = data.get("neow_cost")  # Use .get to handle absence gracefully
        if cost is None:
            logger.info("No Neow cost found in data.")
            return ()  # No cost recorded or key missing
        if not isinstance(cost, str):
            logger.error(
                f"Expected string for 'neow_cost', got {type(cost)}. Value: {cost}"
            )
            raise TypeError("Invalid type for 'neow_cost'")

        logger.info(f"Neow cost: {cost}")
        # Assuming the cost string itself is the token
        return "NEOW COST", cost
    except TypeError as e:
        logger.error(f"Data structure error accessing Neow cost: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error getting Neow cost.")
        raise


# --- Parsing Specific Event Lists ---


def parse_card_choices(
    card_choices: list[dict[str, Any]],
) -> dict[int, tuple[str, ...]]:
    """Parses card choice events, mapping floor to choice tokens."""
    if not isinstance(card_choices, list):
        logger.error(
            f"Invalid type for parse_card_choices: expected list, got {type(card_choices)}."
        )
        raise TypeError("Input 'card_choices' must be a list of dicts")

    card_choices_by_floor: dict[int, tuple[str, ...]] = {}
    logger.info(f"Parsing {len(card_choices)} card choice entries.")

    for i, choice_event in enumerate(card_choices):
        if not isinstance(choice_event, dict):
            logger.warning(
                f"Skipping invalid card choice entry at index {i}: Expected dict, got {type(choice_event)}. Value: {choice_event}"
            )
            continue

        try:
            floor = choice_event["floor"]
            if not isinstance(
                floor, (int, float)
            ):  # Allow float if sometimes read from JSON? Cast to int.
                raise TypeError(f"Expected int/float for 'floor', got {type(floor)}")
            floor = int(floor)

            picked_tokens: list[str] = []
            if "picked" in choice_event:
                picked_card = choice_event["picked"]
                if (
                    not isinstance(picked_card, str) or picked_card.lower() == "skip"
                ):  # Handle explicit skips
                    logger.debug(
                        f"Floor {floor}: Card choice skipped ('{picked_card}')."
                    )
                    picked_tokens.append(
                        skip("CARD")
                    )  # Generic skip token? Or specific?
                else:
                    logger.debug(f"Floor {floor}: Picked card '{picked_card}'.")
                    card_tokens = tokenize_card(picked_card)
                    # Assume acquire applies to base card name, level tokens follow
                    picked_tokens.extend([acquire(card_tokens[0]), *card_tokens[1:]])

            not_picked_tokens: list[str] = []
            if "not_picked" in choice_event:
                not_picked_list = choice_event["not_picked"]
                if not isinstance(not_picked_list, list):
                    raise TypeError(
                        f"Expected list for 'not_picked', got {type(not_picked_list)}"
                    )

                for card in not_picked_list:
                    if not isinstance(card, str):
                        logger.warning(
                            f"Floor {floor}: Skipping non-string card in 'not_picked': {card}"
                        )
                        continue
                    logger.debug(f"Floor {floor}: Not picked card '{card}'.")
                    card_tokens = tokenize_card(card)
                    # Assume skip applies to base card name, level tokens follow
                    not_picked_tokens.extend([skip(card_tokens[0]), *card_tokens[1:]])

            all_tokens = (*picked_tokens, *not_picked_tokens)
            if floor in card_choices_by_floor:
                logger.warning(
                    f"Floor {floor} encountered multiple times in card choices. Overwriting previous entry."
                )
            card_choices_by_floor[floor] = all_tokens
            logger.debug(f"Floor {floor} card choice tokens: {all_tokens}")

        except KeyError as e:
            logger.error(
                f"Missing key '{e}' in card choice entry at index {i}: {choice_event}. Skipping entry."
            )
            continue  # Skip this entry
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing card choice entry at index {i}: {e}. Entry: {choice_event}. Skipping entry."
            )
            continue  # Skip this entry
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card choice entry at index {i}: {choice_event}. Skipping entry."
            )
            continue  # Skip this entry

    logger.info(
        f"Successfully parsed {len(card_choices_by_floor)} floors with card choices."
    )
    return card_choices_by_floor


def _parse_enemy_damage_taken(battle_info: dict[str, Any]) -> tuple[str, ...]:
    """Helper to create battle token from damage event."""
    try:
        enemies = battle_info["enemies"]
        if not isinstance(enemies, str):
            raise TypeError(f"Expected string for 'enemies', got {type(enemies)}")
        logger.debug(f"Creating battle token for enemies: {enemies}")
        return (battle(enemies),)
    except KeyError:
        logger.error("'enemies' key not found in battle info for damage taken.")
        raise ValueError("Missing 'enemies' key in damage_taken battle info")
    except TypeError as e:
        logger.error(f"Data error in battle info: {e}")
        raise


def parse_damage_taken(
    damage_taken_list: list[dict[str, Any]],
) -> dict[int, tuple[str, ...]]:
    """Parses damage taken events, mapping floor to battle tokens."""
    if not isinstance(damage_taken_list, list):
        logger.error(
            f"Invalid type for parse_damage_taken: expected list, got {type(damage_taken_list)}."
        )
        raise TypeError("Input 'damage_taken' must be a list of dicts")

    damage_taken_by_floor: dict[int, tuple[str, ...]] = {}
    logger.info(f"Parsing {len(damage_taken_list)} damage taken entries.")

    for i, floor_event in enumerate(damage_taken_list):
        if not isinstance(floor_event, dict):
            logger.warning(
                f"Skipping invalid damage taken entry at index {i}: Expected dict, got {type(floor_event)}. Value: {floor_event}"
            )
            continue

        try:
            floor_number = floor_event["floor"]
            if not isinstance(floor_number, (int, float)):
                raise TypeError(
                    f"Expected int/float for 'floor', got {type(floor_number)}"
                )
            floor_number = int(floor_number)

            # Original code differentiates based on 'enemies' key presence
            # Let's stick to that logic, assuming damage entries *always* relate to a battle context if 'enemies' is present
            if "enemies" in floor_event:
                tokens = _parse_enemy_damage_taken(floor_event)
                if floor_number in damage_taken_by_floor:
                    logger.warning(
                        f"Floor {floor_number} encountered multiple times in damage taken (battle context). Overwriting."
                    )
                damage_taken_by_floor[floor_number] = tokens
                logger.debug(
                    f"Floor {floor_number} damage taken (battle) tokens: {tokens}"
                )
            else:
                # Original code raised ValueError here. Maybe log instead?
                # This implies damage taken outside of a recorded enemy encounter (e.g., events)
                # How should this be tokenized? Using tokenize_damage_taken perhaps?
                damage_amount = floor_event.get(
                    "damage"
                )  # Assuming 'damage' key exists
                if damage_amount is not None:
                    logger.warning(
                        f"Floor {floor_number}: Damage taken event lacks 'enemies' key. Assuming event damage: {damage_amount}. Original data: {floor_event}"
                    )
                    # Option 1: Tokenize as generic damage
                    # tokens = tokenize_damage_taken(damage_amount)
                    # Option 2: Skip or log only (as original code effectively errorred out)
                    # Let's log and skip adding tokens for now, as the original code didn't handle this path.
                    pass  # Logged warning above
                else:
                    logger.error(
                        f"Floor {floor_number}: Damage taken event lacks 'enemies' and 'damage' keys. Cannot process. Original data: {floor_event}"
                    )
                    # This *was* the case that raised ValueError implicitly in original code's print statement.

        except KeyError as e:
            logger.error(
                f"Missing key '{e}' in damage taken entry at index {i}: {floor_event}. Skipping entry."
            )
            continue
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing damage taken entry at index {i}: {e}. Entry: {floor_event}. Skipping entry."
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing damage taken entry at index {i}: {floor_event}. Skipping entry."
            )
            continue

    logger.info(
        f"Successfully parsed {len(damage_taken_by_floor)} floors with damage taken (battle context)."
    )
    return damage_taken_by_floor


def parse_potions_obtained(potions: list[dict[str, Any]]) -> dict[int, tuple[str, ...]]:
    """Parses potion obtained events, mapping floor to acquire tokens."""
    if not isinstance(potions, list):
        logger.error(
            f"Invalid type for parse_potions_obtained: expected list, got {type(potions)}."
        )
        raise TypeError("Input 'potions' must be a list of dicts")

    potions_by_floor: dict[int, tuple[str, ...]] = {}
    logger.info(f"Parsing {len(potions)} potion obtained entries.")

    for i, potion_obj in enumerate(potions):
        if not isinstance(potion_obj, dict):
            logger.warning(
                f"Skipping invalid potion entry at index {i}: Expected dict, got {type(potion_obj)}. Value: {potion_obj}"
            )
            continue

        try:
            floor = potion_obj["floor"]
            potion_name = potion_obj[
                "key"
            ]  # Assuming key 'key' holds the potion name based on typical run file structure

            if not isinstance(floor, (int, float)):
                raise TypeError(f"Expected int/float for 'floor', got {type(floor)}")
            floor = int(floor)

            if not isinstance(potion_name, str) or not potion_name:
                raise ValueError(f"Invalid potion name found: {potion_name}")

            token = (acquire(potion_name),)
            if floor in potions_by_floor:
                # This could happen (e.g., event gives potion, then battle drop). Append or overwrite?
                # Let's append for now, assuming multiple potions on a floor are possible.
                logger.warning(
                    f"Floor {floor} encountered multiple times for potion obtained. Appending new potion: {potion_name}"
                )
                potions_by_floor[floor] += token
            else:
                potions_by_floor[floor] = token

            logger.debug(f"Floor {floor} potion obtained: {potion_name} -> {token}")

        except KeyError as e:
            logger.error(
                f"Missing key '{e}' in potion entry at index {i}: {potion_obj}. Skipping entry."
            )
            continue
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing potion entry at index {i}: {e}. Entry: {potion_obj}. Skipping entry."
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing potion entry at index {i}: {potion_obj}. Skipping entry."
            )
            continue

    logger.info(
        f"Successfully parsed {len(potions_by_floor)} floors with potion acquisitions."
    )
    return potions_by_floor


def parse_items_purchased(
    items_purchased: list[str], item_purchase_floors: list[int]
) -> dict[int, list[str]]:
    """Parses purchased items, grouping acquire tokens by floor."""
    if not isinstance(items_purchased, list) or not isinstance(
        item_purchase_floors, list
    ):
        logger.error(
            f"Invalid input types for parse_items_purchased: Expected two lists, got {type(items_purchased)} and {type(item_purchase_floors)}."
        )
        raise TypeError(
            "Inputs 'items_purchased' and 'item_purchase_floors' must be lists"
        )

    if len(items_purchased) != len(item_purchase_floors):
        logger.warning(
            f"Mismatch in lengths for items purchased ({len(items_purchased)}) and floors ({len(item_purchase_floors)}). Parsing up to shortest length."
        )
        # Decide: Raise error or proceed with zip's default behavior (shortest)? Proceeding.

    items_by_floor = defaultdict(list)
    logger.info(f"Parsing {len(items_purchased)} purchased item entries.")
    processed_count = 0

    for i, (floor, item) in enumerate(zip(item_purchase_floors, items_purchased)):
        try:
            if not isinstance(floor, (int, float)):
                raise TypeError(
                    f"Expected int/float for floor at index {i}, got {type(floor)}"
                )
            floor = int(floor)

            if not isinstance(item, str) or not item:
                raise ValueError(f"Invalid item name found at index {i}: {item}")

            token = acquire(item)
            items_by_floor[floor].append(token)
            logger.debug(f"Floor {floor}: Purchased item '{item}' -> {token}")
            processed_count += 1

        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing purchased item at index {i}: Floor={floor}, Item='{item}'. Error: {e}. Skipping entry."
            )
            continue  # Skip this item/floor pair
        except Exception as e:
            logger.exception(
                f"Unexpected error processing purchased item at index {i}: Floor={floor}, Item='{item}'. Skipping entry."
            )
            continue  # Skip this item/floor pair

    logger.info(
        f"Successfully parsed {processed_count} purchased items across {len(items_by_floor)} floors."
    )
    return dict(items_by_floor)  # Convert back to regular dict if needed


def parse_path_per_floor(
    path_per_floor: list[Optional[str]],
) -> dict[int, dict[int, tuple[str]]]:
    """Parses the map path, creating go_to tokens indexed by act level and floor number."""
    if not isinstance(path_per_floor, list):
        logger.error(
            f"Invalid type for parse_path_per_floor: expected list, got {type(path_per_floor)}."
        )
        raise TypeError("Input 'path_per_floor' must be a list")

    # Using defaultdict for acts, regular dict for floors within act
    path_map: dict[int, dict[int, tuple[str]]] = defaultdict(dict)
    act_level = 0  # Slay the Spire acts are typically 0-indexed internally (Act 1 = 0)
    # Floor numbers in run files usually start at 0 (Neow) or 1 (first combat/event)
    # Let's follow the original code's logic assuming floor_number increments for non-None entries
    floor_number = 0  # Start at 0, increment *before* adding if not None? Let's test.
    # Original code started floor_number at 1 and incremented after. Let's match that.
    floor_number = 1

    logger.info(f"Parsing {len(path_per_floor)} path entries.")

    for i, floor_node in enumerate(path_per_floor):
        try:
            if floor_node is None:
                # This typically signifies moving to the next act
                act_level += 1
                # Reset floor number? Run files don't usually reset floor numbers globally.
                # The original code didn't reset floor_number, so let's keep it continuous.
                logger.debug(
                    f"Path entry {i}: Null entry encountered, advancing to Act Level {act_level}."
                )
                continue

            if not isinstance(floor_node, str):
                raise TypeError(
                    f"Expected string or None for path node at index {i}, got {type(floor_node)}"
                )

            token = (go_to(floor_node),)
            if floor_number in path_map[act_level]:
                # This shouldn't happen with standard run files, indicates data issue or logic mismatch
                logger.warning(
                    f"Duplicate floor number {floor_number} encountered for Act Level {act_level}. Overwriting node '{path_map[act_level][floor_number]}' with '{token}'."
                )

            path_map[act_level][floor_number] = token
            logger.debug(
                f"Path entry {i}: Act {act_level}, Floor {floor_number} -> Node '{floor_node}' -> Token {token}"
            )
            floor_number += 1  # Increment for the next non-None node

        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing path entry at index {i}: Node='{floor_node}'. Error: {e}. Skipping entry."
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing path entry at index {i}: Node='{floor_node}'. Skipping entry."
            )
            continue

    logger.info(
        f"Successfully parsed path across {len(path_map)} act levels, up to floor {floor_number -1}."
    )
    # Convert defaultdict back to regular dict if preferred by consumers
    return dict(path_map)


def parse_cards_transformed(cards_transformed: list[str]) -> tuple[str, ...]:
    """Parses card transform events. Generates ('TRANSFORM', old_card, [level], 'TO', new_card, [level]) tokens."""
    # TODO: The exact format of `cards_transformed` in run files needs clarification.
    # Assuming it's a flat list like ['Bash', 'Strike'] meaning Bash -> Strike
    # Or maybe ['Bash', 'Defend+1'] meaning Bash -> Defend+1?
    # Or maybe pairs: [['Bash', 'Strike'], ['Defend', 'Defend+1']]?
    # Let's assume the simplest: a flat list where pairs represent transforms.
    logger.warning(
        "parse_cards_transformed: Implementation assumes a flat list where every two elements form a transform pair (old -> new). Verify data format."
    )

    if not isinstance(cards_transformed, list):
        logger.error(
            f"Expected list for cards_transformed, got {type(cards_transformed)}"
        )
        raise TypeError("Input 'cards_transformed' must be a list")

    all_tokens: list[str] = []
    if len(cards_transformed) % 2 != 0:
        logger.warning(
            f"cards_transformed list has an odd number of elements ({len(cards_transformed)}). The last element will be ignored."
        )

    for i in range(0, len(cards_transformed) - 1, 2):
        old_card_str = cards_transformed[i]
        new_card_str = cards_transformed[i + 1]

        try:
            if not isinstance(old_card_str, str) or not isinstance(new_card_str, str):
                raise ValueError("Non-string element found in transform pair.")

            old_tokens = tokenize_card(old_card_str)
            new_tokens = tokenize_card(new_card_str)

            transform_tokens = ("TRANSFORM", *old_tokens, "TO", *new_tokens)
            all_tokens.extend(transform_tokens)
            logger.debug(
                f"Parsed transform: '{old_card_str}' -> '{new_card_str}'. Tokens: {transform_tokens}"
            )

        except (TypeError, ValueError) as e:
            logger.error(
                f"Error processing card transform pair at index {i}: ('{old_card_str}', '{new_card_str}'). Error: {e}. Skipping pair."
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card transform pair at index {i}: ('{old_card_str}', '{new_card_str}'). Skipping pair."
            )
            continue

    logger.info(
        f"Generated {len(all_tokens)} tokens from {len(cards_transformed)//2} card transform pairs."
    )
    return tuple(all_tokens)


def tokenize_relic_lost(relic: str) -> tuple[str, ...]:
    """Creates tokens for losing a relic: ('REMOVE', relic_name)"""
    if not isinstance(relic, str) or not relic:
        logger.error(
            f"Invalid input for tokenize_relic_lost: Expected non-empty string, got {type(relic)}. Value: '{relic}'"
        )
        raise ValueError("Invalid relic name for tokenization")
    try:
        # Relics typically don't have levels like cards
        logger.debug(f"Tokenizing relic loss: {relic}")
        return ("REMOVE", relic)
    except Exception as e:
        # Should be very unlikely for simple string handling
        logger.exception(f"Unexpected error tokenizing relic loss for '{relic}'.")
        raise RuntimeError(f"Failed to tokenize lost relic: {relic}") from e


def parse_relics_lost(relics_lost: list[str]) -> tuple[str, ...]:
    """Parses a list of lost relics into REMOVE tokens."""
    if not isinstance(relics_lost, list):
        logger.error(f"Expected list for relics_lost, got {type(relics_lost)}")
        raise TypeError("Input 'relics_lost' must be a list")

    all_tokens: list[str] = []
    logger.info(f"Parsing {len(relics_lost)} lost relic entries.")

    for i, relic in enumerate(relics_lost):
        try:
            tokens = tokenize_relic_lost(relic)
            all_tokens.extend(tokens)
            logger.debug(f"Parsed lost relic at index {i}: '{relic}' -> {tokens}")
        except (TypeError, ValueError) as e:
            logger.error(
                f"Error processing lost relic at index {i}: '{relic}'. Error: {e}. Skipping entry."
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing lost relic at index {i}: '{relic}'. Skipping entry."
            )
            continue

    logger.info(
        f"Generated {len(all_tokens)} tokens from {len(relics_lost)} lost relics."
    )
    return tuple(all_tokens)


def tokenize_knowing_skull_choices(event_choice: str) -> str:
    """Convert the lengthy Knowing Skull choice down to one word per option"""
    if not isinstance(event_choice, str):
        # Log the error before raising
        logger.error(
            f"Invalid type for Knowing Skull choice: expected str, got {type(event_choice)}. Value: {event_choice}"
        )
        raise TypeError(f"Expects string for event_choice, got {type(event_choice)}")

    try:
        cleaned_choice = event_choice.strip()
        if not cleaned_choice:
            logger.debug("Tokenizing empty Knowing Skull choice as SKIP.")
            return "SKIP"

        # Split, remove duplicates, sort for consistency
        options = sorted(list(set(cleaned_choice.split(" "))))
        # Remove empty strings that might result from multiple spaces
        options = [opt for opt in options if opt]

        tokenized_choice = " ".join(options)
        logger.debug(
            f"Tokenized Knowing Skull choice: '{event_choice}' -> '{tokenized_choice}'"
        )
        return tokenized_choice

    except Exception as e:
        logger.exception(
            f"Unexpected error tokenizing Knowing Skull choice: '{event_choice}'"
        )
        # Re-raise to indicate failure
        raise RuntimeError(
            f"Failed to tokenize Knowing Skull choice: {event_choice}"
        ) from e
