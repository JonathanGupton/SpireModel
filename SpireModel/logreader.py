from collections import defaultdict
from collections import Counter
from collections.abc import Callable
from itertools import chain
import logging
import re
from typing import Generator, Any, Optional, Dict, List, Tuple

from SpireModel.components import acquire
from SpireModel.components import battle
from SpireModel.components import event_name
from SpireModel.components import go_to
from SpireModel.components import player_chose
from SpireModel.components import skip
from SpireModel.components import remove
from SpireModel.components import transform
from SpireModel.components import upgrade
from SpireModel.components import CHARACTERS


# --- Logging Setup ---
# Configure logging (you might want to configure this externally in a real application)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
# Get a logger for this module
logger = logging.getLogger(__name__)

# --- Tokenization Functions ---


def _tokenize_numbers_individually(number: str) -> Generator[str, None, None]:
    """
    Convert a str number into the individual numbers.

    Parameters
    ----------
    number : str
        The number to tokenize.

    Yields
    ------
    str
        A generator of strings, each a single digit from the input number.

    Raises
    ------
    Exception
        If an unexpected error occurs during tokenization.

     Examples
    --------
    >>> tuple(_tokenize_numbers_individually("1934"))
    ("1", "9", "3", "4")
    """
    try:
        for n in number:
            yield n
    except Exception as e:
        logger.exception(f"Unexpected error during number tokenization for '{number}'.")
        raise



def _tokenize_into_masked_digits(number: str) -> Generator[str, None, None]:
    """
    Converts a str number into a generator of strings, each a single digit from the input number,
    but with all digits after the first one replaced with 'X'.

    Parameters
    ----------
    number : str
        The number to tokenize.

    Yields
    ------
    str
        A generator of strings, each a single digit from the input number, with all digits after
        the first one replaced with 'X'.

    Raises
    ------
    Exception
        If an unexpected error occurs during tokenization.

    Examples
    --------
    >>> tuple(_tokenize_into_masked_digits("1934"))
    ("1XXX", "9XX", "3X", "4")
    """
    length = len(number)
    for i, digit in enumerate(number):
        yield digit + "X" * (length - i - 1)


def tokenize_number(
    number: str,
    number_tokenizer: Callable[
        [str], Generator[str, None, None]
    ] = _tokenize_into_masked_digits,
) -> Generator[str, None, None]:
    """
    Tokenizes a given number into a generator of strings, by default into masked digits.

    Parameters
    ----------
    number : str
        The number to tokenize.
    number_tokenizer : Callable[[str], Generator[str, None, None]], optional
        A function that takes a string and yields a generator of strings. Defaults to
        `_tokenize_into_masked_digits`.

    Yields
    ------
    str
        A generator of strings, either the individual digits of the number or the
        masked digits depending on the `number_tokenizer` used.

    Raises
    ------
    TypeError
        If the input `number` is not a string.
    """
    if not isinstance(number, str):
        logger.error(
            f"Invalid type for tokenize_number: expected str, got {type(number)}. Value: {number}"
        )
        raise TypeError(f"Input 'number' must be a string, got {type(number)}")
    if (
        not number.isdigit() and number
    ):  # Empty string is not an error, just yields nothing.
        logger.warning(f"Input '{number}' to tokenize_number is not purely digits.")
    yield from number_tokenizer(number)


DEFEND_PATTERN = r"Defend_\w{1}"
DEFEND_PLUS_PATTERN = r"Defend_\w{1}\+1"
STRIKE_PATTERN = r"Strike_\w{1}"
STRIKE_PLUS_PATTERN = r"Strike_\w{1}\+1"


def standardize_strikes_and_defends(card: str) -> str:
    """
    Standardize strike and defend card names.

    The Defend and Strike cards with modifiers (+1, +2, etc.) are standardized
    to simply "Defend" and "Strike" respectively.

    Parameters
    ----------
    card : str
        The card name to standardize.

    Returns
    -------
    str
        The standardized card name.

    Examples
    --------
    >>> standardize_strikes_and_defends("Defend_R")
    'Defend'
    >>> standardize_strikes_and_defends("Defend_R+1")
    'Defend+1'
    >>> standardize_strikes_and_defends("Strike_R")
    'Strike'
    >>> standardize_strikes_and_defends("Strike_R+1")
    'Strike+1'
    """
    if re.fullmatch(DEFEND_PATTERN, card):
        return "Defend"
    if re.fullmatch(DEFEND_PLUS_PATTERN, card):
        return "Defend+1"
    if re.fullmatch(STRIKE_PATTERN, card):
        return "Strike"
    if re.fullmatch(STRIKE_PLUS_PATTERN, card):
        return "Strike+1"
    return card


def tokenize_card(card: str) -> Tuple[str, ...]:
    """
    Tokenizes a given card into a tuple of strings.

    Parameters
    ----------
    card : str
        The card name to tokenize.

    Returns
    -------
    tuple[str, ...]
        A tuple of strings, either the individual parts of the card name or the
        card name and level if the card name contains a "+". The level is then
        further tokenized into masked digits.

    Raises
    ------
    TypeError
        If the input `card` is not a string.
    ValueError
        If the input `card` is not in the expected format.
    """
    if not isinstance(card, str):
        logger.error(
            f"Invalid type for tokenize_card: expected str, got {type(card)}. Value: {card}"
        )
        raise TypeError(f"Input 'card' must be a string, got {type(card)}")

    card = standardize_strikes_and_defends(card)
    try:
        if "+" in card:
            parts = card.split("+", 1)
            if len(parts) == 2 and parts[1].isdigit():
                card_name, level = parts
                logger.debug(
                    f"Tokenizing upgraded card: {card} -> ('{card_name}', level '{level}')"
                )
                return (card_name, *tokenize_number(level))
            else:
                logger.warning(
                    f"Card '{card}' contains '+' but not in expected 'Name+Level' format. Treating as simple card name."
                )
                return (card,)
        else:
            logger.debug(f"Tokenizing simple card: {card} -> ('{card}',)")
            return (card,)
    except Exception as e:
        logger.exception(f"Error tokenizing card: '{card}'")
        raise ValueError(f"Failed to tokenize card: {card}") from e


def tokenize_damage_taken(damage_taken: int | str) -> Tuple[str, ...]:
    """('LOSE' '[N]' 'HEALTH')"""
    return ("LOSE", *tokenize_number(str(int(damage_taken))), "HEALTH")


def tokenize_health_healed(health_healed: int | str) -> Tuple[str, ...]:
    """("GAIN", [N], "HEALTH")"""
    return ("GAIN", *tokenize_number(str(int(health_healed))), "HEALTH")


def tokenize_max_health_gained(max_health_gained: int | str) -> Tuple[str, ...]:
    """("INCREASE", [N], "MAX HEALTH")"""
    return (
        "INCREASE",
        *tokenize_number(str(int(max_health_gained))),
        "MAX HEALTH",
    )


def tokenize_max_health_lost(max_health_lost: int | str) -> Tuple[str, ...]:
    """DECREASE [N] MAX HEALTH"""
    return "DECREASE", *tokenize_number(str(int(max_health_lost))), "MAX HEALTH"


def tokenize_gold_gain(gold_gained: int | str) -> Tuple[str, ...]:
    """ACQUIRE [N] GOLD"""
    return "ACQUIRE", *tokenize_number(str(int(gold_gained))), "GOLD"


def tokenize_gold_lost(gold_lost: int | str) -> Tuple[str, ...]:
    """LOSE [N] GOLD"""
    return "LOSE", *tokenize_number(str(int(gold_lost))), "GOLD"


def tokenize_event_card_acquisition(cards: List[str]) -> Tuple[str, ...]:
    """Generates ACQUIRE tokens for a list of cards from an event."""
    if not isinstance(cards, list):
        logger.error(f"Expected list for event card acquisition, got {type(cards)}")
        raise TypeError("Input 'cards' must be a list")

    all_tokens: List[str] = []
    for i, card_str in enumerate(cards):
        if not isinstance(card_str, str):
            logger.warning(
                f"Skipping non-string card at index {i} in event acquisition: {card_str}"
            )
            continue
        try:
            card_tokens = tokenize_card(card_str)
            # Assuming acquire takes the base name and level tokens follow
            all_tokens.extend((acquire(card_tokens)))
            logger.debug(
                f"Event acquired card: {card_str} -> {(acquire(card_tokens[0]), *card_tokens[1:])}"
            )
        except (ValueError, TypeError) as e:  # Catch errors from tokenize_card
            logger.error(
                f"Failed to tokenize card '{card_str}' during event acquisition: {e}"
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card '{card_str}' during event acquisition."
            )
            continue
    return tuple(all_tokens)


def tokenize_transform_card(card: str) -> Tuple[str, ...]:
    """('TRANSFORM', '[CARD]', '[optional N]')"""
    if not isinstance(card, str):
        logger.error(
            f"Invalid type for tokenize_transform_card: expected str, got {type(card)}. Value: {card}"
        )
        raise TypeError(f"Input 'card' must be a string, got {type(card)}")
    try:
        tokens = tokenize_card(card)
        return transform(tokens)
    except (ValueError, TypeError) as e:  # Catch errors from tokenize_card
        logger.error(f"Failed to tokenize card '{card}' for transform: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error tokenizing card '{card}' for transform.")
        raise


def tokenize_remove_card(card: str) -> Tuple[str, ...]:
    """('REMOVE', '[CARD]' '[optional N]'"""
    if not isinstance(card, str):
        logger.error(
            f"Invalid type for tokenize_remove_card: expected str, got {type(card)}. Value: {card}"
        )
        raise TypeError(f"Input 'card' must be a string, got {type(card)}")
    logger.debug(f"Tokenizing card removal: {card}")
    try:
        tokens = tokenize_card(card)
        return remove(tokens)
    except (ValueError, TypeError) as e:  # Catch errors from tokenize_card
        logger.error(f"Error tokenizing card for removal: {card}. Error: {e}")
        raise ValueError(f"Failed to tokenize card for removal: {card}") from e
    except Exception as e:
        logger.exception(f"Unexpected error tokenizing card for removal: {card}")
        raise


def tokenize_event_card_removal(cards: List[str]) -> Tuple[str, ...]:
    if not isinstance(cards, list):
        logger.error(f"Expected list for event card removal, got {type(cards)}")
        raise TypeError("Input 'cards' must be a list")
    all_tokens: List[str] = []
    for i, card_str in enumerate(cards):
        if not isinstance(card_str, str):
            logger.warning(
                f"Skipping non-string card at index {i} in event removal: {card_str}"
            )
            continue
        try:
            all_tokens.extend(tokenize_remove_card(card_str))
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to tokenize card '{card_str}' for event removal: {e}")
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card '{card_str}' for event removal."
            )
            continue
    return tuple(all_tokens)


def tokenize_upgrade_card(card: str) -> Tuple[str, ...]:
    """('UPGRADE', '[CARD]', '[N]')"""
    if not isinstance(card, str):
        logger.error(
            f"Invalid type for tokenize_upgrade_card: expected str, got {type(card)}. Value: {card}"
        )
        raise TypeError(f"Input 'card' must be a string, got {type(card)}")
    logger.debug(f"Tokenizing card upgrade: {card}")
    try:
        tokens = tokenize_card(card)
        # Ensure it looks like an upgraded card (has level info after name)
        return upgrade(tokens)
    except (ValueError, TypeError) as e:  # Catch errors from tokenize_card
        logger.error(f"Error tokenizing card for upgrade: {card}. Error: {e}")
        raise ValueError(f"Failed to tokenize card for upgrade: {card}") from e
    except Exception as e:
        logger.exception(f"Unexpected error tokenizing card for upgrade: {card}")
        raise


def tokenize_event_relic_acquisition(relics: List[str]) -> Tuple[str, ...]:
    if not isinstance(relics, list):
        logger.error(f"Expected list for event relic acquisition, got {type(relics)}")
        raise TypeError("Input 'relics' must be a list")

    all_tokens: List[str] = []
    for i, relic in enumerate(relics):
        if not isinstance(relic, str) or not relic:  # Check for empty string too
            logger.warning(
                f"Skipping invalid or empty relic entry at index {i} in event acquisition: '{relic}'"
            )
            continue
        try:
            token = acquire(relic)  # Relics are usually simple strings
            all_tokens.append(token)
            logger.debug(f"Event acquired relic: {relic} -> {token}")
        except Exception as e:  # acquire itself might raise an error on invalid input
            logger.error(f"Failed to create acquire token for relic '{relic}': {e}")
            continue
    return tuple(all_tokens)


# --- Data Parsing Functions ---


def get_character_token(data: Dict[str, Any]) -> Tuple[str, ...]:
    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        character = data["character_chosen"]
        if not isinstance(character, str):
            logger.error(
                f"Expected string for 'character_chosen', got {type(character)}. Value: {character}"
            )
            raise TypeError(
                f"Expected string for 'character_chosen', got {type(character)}"
            )
        if character not in CHARACTERS:
            logger.warning(
                f"Character '{character}' not in known CHARACTERS: {CHARACTERS}. Proceeding, but this may indicate an issue."
            )
        logger.info(f"Character chosen: {character}")
        return (character,)
    except KeyError:
        logger.error("'character_chosen' key not found in data.")
        raise ValueError("Missing 'character_chosen' in input data")
    except TypeError as e:  # Handles if data['character_chosen'] is not string
        logger.error(f"Data structure error accessing character: {e}")
        raise


def get_ascension_tokens(data: Dict[str, Any]) -> Tuple[str, ...]:
    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        is_ascension = data.get("is_ascension_mode", False)
        if not isinstance(is_ascension, bool):
            logger.warning(
                f"Expected bool for 'is_ascension_mode', got {type(is_ascension)}. Assuming False."
            )
            is_ascension = (
                False  # Coerce to bool or handle as error based on strictness
            )

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
                raise TypeError(
                    f"Invalid type for 'ascension_level', expected int or str, got {type(ascension_level)}"
                )

            str_level = str(ascension_level)
            if not str_level.isdigit():
                logger.warning(
                    f"Ascension level '{str_level}' is not purely digits. Proceeding with tokenization."
                )
            logger.info(f"Ascension mode active: Level {str_level}")
            return ("ASCENSION MODE", *tokenize_number(str_level))
        else:
            logger.info("Ascension mode not active.")
            return ()
    except (TypeError, ValueError) as e:  # Catch our specific raises
        logger.error(f"Error processing ascension data: {e}")
        raise
    except Exception as e:  # Catch unexpected errors
        logger.exception("Unexpected error getting ascension tokens.")
        raise


def get_starting_cards(data: Dict[str, Any]) -> Tuple[str, ...]:
    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        character = data["character_chosen"]
        if not isinstance(
            character, str
        ):  # Should be caught by get_character_token if used prior, but good here too
            raise TypeError(
                f"Expected string for 'character_chosen', got {type(character)}"
            )
        if character not in CHARACTERS:
            logger.error(
                f"Unknown character '{character}' found when getting starting cards. Known: {CHARACTERS}"
            )
            raise ValueError(
                f"Character '{character}' not found in known CHARACTERS: {CHARACTERS}"
            )

        logger.debug(f"Determining starting cards for: {character}")
        card_counts: Tuple[Tuple[str, int], ...]
        if character == "IRONCLAD":
            card_counts = (("Strike", 5), ("Defend", 4), ("Bash", 1))
        elif character == "DEFECT":
            card_counts = (("Strike", 4), ("Defend", 4), ("Zap", 1), ("Dualcast", 1))
        elif character == "THE_SILENT":
            card_counts = (
                ("Strike", 5),
                ("Defend", 5),
                ("Survivor", 1),
                ("Neutralize", 1),
            )
        elif character == "WATCHER":
            card_counts = (
                ("Strike", 4),
                ("Defend", 4),
                ("Eruption", 1),
                ("Vigilance", 1),
            )
        else:  # Should not be reached if CHARACTERS check is exhaustive
            logger.error(
                f"Logic error: Character '{character}' passed CHARACTERS check but has no defined starting cards."
            )
            raise ValueError(f"No starting cards defined for character: {character}")

        tokens_list: List[str] = []
        for card_name, count in card_counts:
            for _ in range(count):
                try:
                    # Starting cards are never upgraded, so tokenize_card will return (card_name,)
                    base_card_tokens = tokenize_card(
                        card_name
                    )  # Should just be (card_name,)
                    tokens_list.append(acquire(base_card_tokens[0]))
                except Exception as e:  # Broad exception for tokenize_card or acquire
                    logger.error(
                        f"Failed to tokenize or acquire starting card '{card_name}': {e}"
                    )
                    raise ValueError(
                        f"Error processing starting card {card_name}"
                    ) from e

        logger.info(
            f"Generated {len(tokens_list)} starting card tokens for {character}."
        )
        return tuple(tokens_list)

    except KeyError:
        logger.error("'character_chosen' key not found in data for starting cards.")
        raise ValueError("Missing 'character_chosen' in input data")
    except (TypeError, ValueError) as e:  # Catch our specific raises
        logger.error(f"Error getting starting cards: {e}")
        raise
    except Exception as e:  # Catch unexpected errors
        logger.exception(f"Unexpected error getting starting cards for data: {data}")
        raise


def get_starting_relics(data: Dict[str, Any]) -> Tuple[str, ...]:

    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        character = data["character_chosen"]
        if not isinstance(character, str):
            raise TypeError(
                f"Expected string for 'character_chosen', got {type(character)}"
            )
        if character not in CHARACTERS:
            logger.error(
                f"Unknown character '{character}' found when getting starting relic. Known: {CHARACTERS}"
            )
            raise ValueError(
                f"Character '{character}' not found in known CHARACTERS: {CHARACTERS}"
            )

        logger.debug(f"Determining starting relic for: {character}")
        relic: Optional[str] = None
        if character == "IRONCLAD":
            relic = "Burning Blood"
        elif character == "DEFECT":
            relic = "Cracked Core"
        elif character == "THE_SILENT":
            relic = "Ring of the Snake"
        elif character == "WATCHER":
            relic = "Pure Water"
        # No default needed due to CHARACTERS check

        if relic:
            logger.info(f"Starting relic for {character}: {relic}")
            try:
                return (acquire(relic),)
            except Exception as e:  # acquire might fail
                logger.error(
                    f"Failed to create acquire token for starting relic '{relic}': {e}"
                )
                raise ValueError(f"Error processing starting relic {relic}") from e
        else:
            # This case should ideally not be reached if CHARACTERS is aligned with logic
            logger.error(f"No starting relic defined for valid character: {character}")
            return ()

    except KeyError:
        logger.error("'character_chosen' key not found in data for starting relics.")
        raise ValueError("Missing 'character_chosen' in input data")
    except (TypeError, ValueError) as e:
        logger.error(f"Error getting starting relics: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting starting relics for data: {data}")
        raise


def get_starting_gold() -> Tuple[str, ...]:
    logger.info("Generating starting gold tokens (99).")
    try:
        # Replicates tokenize_gold_gain("99")
        return ("ACQUIRE", "9", "9", "GOLD")
    except Exception as e:
        logger.exception("Unexpected error generating starting gold tokens.")
        # This is extremely unlikely for hardcoded values but good for robustness
        raise RuntimeError("Failed to generate starting gold tokens") from e


def get_neow_bonus(data: Dict[str, Any]) -> Tuple[str, ...]:

    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        bonus = data.get("neow_bonus")
        if bonus is None:
            logger.info(
                "'neow_bonus' key not found in data or is null. No Neow bonus token generated."
            )
            return ()
        if not isinstance(bonus, str):
            logger.error(
                f"Expected string for 'neow_bonus', got {type(bonus)}. Value: {bonus}"
            )
            raise TypeError(
                f"Invalid type for 'neow_bonus', expected str, got {type(bonus)}"
            )
        if not bonus:  # Empty string bonus
            logger.info("Neow bonus string is empty. No Neow bonus token generated.")
            return ()

        logger.info(f"Neow bonus: {bonus}")
        return ("NEOW BONUS", bonus)
    except TypeError as e:
        logger.error(f"Data structure error accessing Neow bonus: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting Neow bonus for data: {data}")
        raise


def get_neow_cost(data: Dict[str, Any]) -> Tuple[str, ...]:

    if not isinstance(data, dict):
        raise TypeError(f"Input 'data' must be a dict, got {type(data)}")
    try:
        cost = data.get("neow_cost")
        if cost is None:
            logger.info(
                "'neow_cost' key not found in data or is null. No Neow cost token generated."
            )
            return ()
        if not isinstance(cost, str):
            logger.error(
                f"Expected string for 'neow_cost', got {type(cost)}. Value: {cost}"
            )
            raise TypeError(
                f"Invalid type for 'neow_cost', expected str, got {type(cost)}"
            )
        if not cost:  # Empty string cost
            logger.info("Neow cost string is empty. No Neow cost token generated.")
            return ()

        logger.info(f"Neow cost: {cost}")
        return ("NEOW COST", cost)
    except TypeError as e:
        logger.error(f"Data structure error accessing Neow cost: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error getting Neow cost for data: {data}")
        raise


# --- Parsing Specific Event Lists ---


def parse_card_choices(
    card_choices: List[Dict[str, Any]],
) -> Dict[int, Tuple[str, ...]]:

    if not isinstance(card_choices, list):
        logger.error(
            f"Invalid type for parse_card_choices: expected list, got {type(card_choices)}."
        )
        raise TypeError("Input 'card_choices' must be a list of dicts")

    card_choices_by_floor: Dict[int, Tuple[str, ...]] = {}
    logger.info(f"Parsing {len(card_choices)} card choice entries.")

    for i, choice_event in enumerate(card_choices):
        if not isinstance(choice_event, dict):
            logger.warning(
                f"Skipping invalid card choice entry at index {i}: Expected dict, got {type(choice_event)}. Value: {choice_event}"
            )
            continue

        try:
            floor_val = choice_event.get("floor")
            if floor_val is None:
                raise ValueError("Missing 'floor' key.")
            if not isinstance(floor_val, (int, float)):
                raise TypeError(
                    f"Expected int/float for 'floor', got {type(floor_val)}"
                )
            floor = int(floor_val)

            current_event_tokens: List[str] = []
            picked_card = choice_event.get(
                "picked"
            )  # Can be str (card name) or str ("SKIP") or None

            if picked_card is not None:  # if "picked" key exists
                if not isinstance(picked_card, str):
                    raise TypeError(
                        f"Expected string for 'picked' card, got {type(picked_card)}"
                    )
                if picked_card.upper() == "SKIP":  # Standardize "skip" check
                    logger.debug(
                        f"Floor {floor}: Card choice explicitly skipped ('{picked_card}')."
                    )
                    current_event_tokens.append(
                        skip("CARD")
                    )  # Standard token for skipping a card choice
                else:
                    logger.debug(f"Floor {floor}: Picked card '{picked_card}'.")
                    card_tokens = tokenize_card(picked_card)
                    current_event_tokens.extend(
                        (acquire(card_tokens[0]), *card_tokens[1:])
                    )
            # If "picked" key is absent, it implies a skip or no choice made/logged in that way.

            not_picked_list = choice_event.get("not_picked")
            if not_picked_list is not None:  # if "not_picked" key exists
                if not isinstance(not_picked_list, list):
                    raise TypeError(
                        f"Expected list for 'not_picked', got {type(not_picked_list)}"
                    )
                for card_str in not_picked_list:
                    if not isinstance(card_str, str):
                        logger.warning(
                            f"Floor {floor}: Skipping non-string card in 'not_picked': {card_str}"
                        )
                        continue
                    logger.debug(f"Floor {floor}: Not picked card '{card_str}'.")
                    card_tokens = tokenize_card(card_str)
                    current_event_tokens.extend(
                        (skip(card_tokens[0]), *card_tokens[1:])
                    )

            if (
                not current_event_tokens
                and picked_card is None
                and not_picked_list is None
            ):
                logger.info(
                    f"Floor {floor}: Card choice event has no 'picked' or 'not_picked' cards. No tokens generated for this entry."
                )

            if current_event_tokens:  # Only add if there are tokens
                if floor in card_choices_by_floor:
                    # Appending makes more sense if multiple card choices can happen on one floor (e.g. ? room choice, then boss reward)
                    logger.warning(
                        f"Floor {floor} encountered multiple times in card choices. Appending new tokens to existing ones."
                    )
                    card_choices_by_floor[floor] += tuple(current_event_tokens)
                else:
                    card_choices_by_floor[floor] = tuple(current_event_tokens)
                logger.debug(
                    f"Floor {floor} card choice tokens: {card_choices_by_floor[floor]}"
                )

        except KeyError as e:
            logger.error(
                f"Missing key '{e}' in card choice entry at index {i}: {choice_event}. Skipping entry."
            )
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing card choice entry at index {i}: {e}. Entry: {choice_event}. Skipping entry."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card choice entry at index {i}: {choice_event}. Skipping entry."
            )

    logger.info(
        f"Successfully processed {len(card_choices)} entries, resulting in {len(card_choices_by_floor)} floors with card choice tokens."
    )
    return card_choices_by_floor


def _parse_enemy_damage_taken(battle_info: Dict[str, Any]) -> Tuple[str, ...]:
    if not isinstance(battle_info, dict):
        raise TypeError(f"Input 'battle_info' must be a dict, got {type(battle_info)}")
    try:
        enemies = battle_info["enemies"]
        if not isinstance(enemies, str):
            raise TypeError(f"Expected string for 'enemies', got {type(enemies)}")
        if not enemies:  # Empty string for enemies
            logger.warning(
                f"Empty 'enemies' string found in battle_info: {battle_info}. Token will reflect this."
            )
        logger.debug(f"Creating battle token for enemies: {enemies}")
        return (battle(enemies),)
    except KeyError:
        logger.error("'enemies' key not found in battle info for damage taken.")
        raise ValueError("Missing 'enemies' key in damage_taken battle info")
    except TypeError as e:  # handles if battle_info['enemies'] is not string
        logger.error(f"Data error in battle info 'enemies' field: {e}")
        raise


def parse_damage_taken(
    damage_taken_list: List[Dict[str, Any]],
) -> Dict[int, Tuple[str, ...]]:
    """
    Parse a list of damage taken events from a run log into a dictionary
    mapping floor numbers to tuples of tokens.

    Each damage taken event is a dict containing at least the key "floor"
    with an integer or float value representing the floor number. If the
    event has a "battle" key, it is considered a battle damage event and
    the tokens are generated based on the battle information.

    If the event does not have a "battle" key, it is considered a generic
    damage taken event and the tokens are generated based on the "damage"
    key, which should have an integer or str value representing the amount
    of damage taken.

    If an event lacks a "floor" key or has an invalid value, it is skipped.
    If an event lacks a "damage" key or has an invalid value, it is also
    skipped.

    The function returns a dictionary mapping floor numbers to tuples of
    tokens, where each tuple contains the tokens generated for the
    corresponding damage taken event.

    Parameters
    ----------
    damage_taken_list : List[Dict[str, Any]]
        The list of damage taken events to parse.

    Returns
    -------
    Dict[int, Tuple[str, ...]]
        A dictionary mapping floor numbers to tuples of tokens.
    """
    if not isinstance(damage_taken_list, list):
        logger.error(
            f"Invalid type for parse_damage_taken: expected list, got {type(damage_taken_list)}."
        )
        raise TypeError("Input 'damage_taken' must be a list of dicts")

    damage_events_by_floor: Dict[int, Tuple[str, ...]] = {}
    logger.info(f"Parsing {len(damage_taken_list)} damage taken entries.")

    for i, floor_event in enumerate(damage_taken_list):
        if not isinstance(floor_event, dict):
            logger.warning(
                f"Skipping invalid damage taken entry at index {i}: Expected dict, got {type(floor_event)}. Value: {floor_event}"
            )
            continue

        try:
            floor_val = floor_event.get("floor")
            if floor_val is None:
                raise ValueError("Missing 'floor' key.")
            if not isinstance(floor_val, (int, float)):
                raise TypeError(
                    f"Expected int/float for 'floor', got {type(floor_val)}"
                )
            floor_number = int(floor_val)

            current_floor_tokens: List[str] = []
            if "enemies" in floor_event:  # Damage related to a specific battle
                battle_tokens = _parse_enemy_damage_taken(floor_event)
                current_floor_tokens.extend(battle_tokens)
                # Original code only considered battle tokens. If damage amount is also present, should it be tokenized?
                # For now, sticking to original focus on battle context if 'enemies' is present.

            # Regardless of 'enemies', check for 'damage' amount for player
            damage_amount = floor_event.get("damage")
            if damage_amount is not None:  # Can be 0, which is valid damage
                if not isinstance(
                    damage_amount, (int, str)
                ):  # Allow str for flexibility, will be converted
                    raise TypeError(
                        f"Expected int or str for 'damage', got {type(damage_amount)}"
                    )
                logger.debug(
                    f"Floor {floor_number}: Player took {damage_amount} damage."
                )
                current_floor_tokens.extend(tokenize_damage_taken(damage_amount))
            else:  # No 'damage' key
                if (
                    "enemies" not in floor_event
                ):  # No enemies and no damage, unclear event
                    logger.warning(
                        f"Floor {floor_number}: Damage taken event lacks 'enemies' and 'damage' keys. Original: {floor_event}. No tokens generated."
                    )

            if current_floor_tokens:
                if floor_number in damage_events_by_floor:
                    logger.warning(
                        f"Floor {floor_number} encountered multiple times for damage events. Appending new tokens."
                    )
                    damage_events_by_floor[floor_number] += tuple(current_floor_tokens)
                else:
                    damage_events_by_floor[floor_number] = tuple(current_floor_tokens)
                logger.debug(
                    f"Floor {floor_number} damage event tokens: {damage_events_by_floor[floor_number]}"
                )

        except KeyError as e:
            logger.error(
                f"Missing key '{e}' in damage taken entry at index {i}: {floor_event}. Skipping entry."
            )
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing damage taken entry at index {i}: {e}. Entry: {floor_event}. Skipping entry."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error processing damage taken entry at index {i}: {floor_event}. Skipping entry."
            )

    logger.info(
        f"Successfully processed {len(damage_taken_list)} entries, resulting in {len(damage_events_by_floor)} floors with damage event tokens."
    )
    return damage_events_by_floor


def parse_potions_obtained(potions: List[Dict[str, Any]]) -> Dict[int, Tuple[str, ...]]:
    """
    Parse potion obtained events, mapping floor to "ACQUIRE" and potion name tokens.

    Parameters
    ----------
    potions : list[dict[str, Any]]
        List of dictionaries, where each dictionary represents a potion obtained event.
        Each dictionary should contain keys "floor" and "key" with values representing the floor the potion was obtained on and the potion name, respectively.

    Returns
    -------
    dict[int, tuple[str, ...]]
        Dictionary mapping floor numbers to tuples of "ACQUIRE" and potion name tokens.
    """
    if not isinstance(potions, list):
        logger.error(
            f"Invalid type for parse_potions_obtained: expected list, got {type(potions)}."
        )
        raise TypeError("Input 'potions' must be a list of dicts")

    potions_by_floor: Dict[int, Tuple[str, ...]] = {}
    logger.info(f"Parsing {len(potions)} potion obtained entries.")

    for i, potion_obj in enumerate(potions):
        if not isinstance(potion_obj, dict):
            logger.warning(
                f"Skipping invalid potion entry at index {i}: Expected dict, got {type(potion_obj)}. Value: {potion_obj}"
            )
            continue

        try:
            floor_val = potion_obj.get("floor")
            if floor_val is None:
                raise ValueError("Missing 'floor' key.")
            if not isinstance(floor_val, (int, float)):
                raise TypeError(
                    f"Expected int/float for 'floor', got {type(floor_val)}"
                )
            floor = int(floor_val)

            potion_name = potion_obj.get("key")
            if potion_name is None:
                raise ValueError("Missing 'key' for potion name.")
            if not isinstance(potion_name, str) or not potion_name:
                raise ValueError(f"Invalid or empty potion name found: '{potion_name}'")

            token = (acquire(potion_name),)
            if floor in potions_by_floor:
                logger.info(  # Changed to info as multiple potions on a floor is plausible
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
        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing potion entry at index {i}: {e}. Entry: {potion_obj}. Skipping entry."
            )
        except Exception as e:  # Catch acquire errors or others
            logger.exception(
                f"Unexpected error processing potion entry at index {i}: {potion_obj}. Skipping entry."
            )

    logger.info(
        f"Successfully processed {len(potions)} entries, resulting in {len(potions_by_floor)} floors with potion acquisitions."
    )
    return potions_by_floor


def parse_items_purchased(
    items_purchased: List[str], item_purchase_floors: List[int]
) -> Dict[int, Tuple[str, ...]]:
    """
    Parse purchased items, given lists of purchased items and floors on which they were purchased.

    Parameters
    ----------
    items_purchased : list[str]
        List of item names that were purchased from the merchant in the run file.
    item_purchase_floors : list[int]
        List of floors on which items were purchased, in same order as the items in `items_purchased`.

    Returns
    -------
    dict[int, tuple[str, ...]]
        Dictionary mapping floors to tuples of "ACQUIRE" and item name tokens.
    """
    if not isinstance(items_purchased, list):
        raise TypeError(
            f"Input 'items_purchased' must be a list, got {type(items_purchased)}"
        )
    if not isinstance(item_purchase_floors, list):
        raise TypeError(
            f"Input 'item_purchase_floors' must be a list, got {type(item_purchase_floors)}"
        )

    if len(items_purchased) != len(item_purchase_floors):
        logger.warning(
            f"Mismatch in lengths for items purchased ({len(items_purchased)}) and floors ({len(item_purchase_floors)}). Parsing up to shortest length: {min(len(items_purchased), len(item_purchase_floors))}."
        )

    items_by_floor_list_val = defaultdict(list)  # Intermediate with list values
    logger.info(
        f"Parsing {min(len(items_purchased), len(item_purchase_floors))} potential purchased item entries."
    )
    processed_count = 0

    for i, (floor_val, item) in enumerate(zip(item_purchase_floors, items_purchased)):
        try:
            if not isinstance(floor_val, (int, float)):  # Allow float if from JSON
                raise TypeError(
                    f"Expected int/float for floor at index {i}, got {type(floor_val)}"
                )
            floor = int(floor_val)

            if not isinstance(item, str) or not item:  # Check for empty string
                raise ValueError(
                    f"Invalid or empty item name found at index {i}: '{item}'"
                )

            token = acquire(item)
            items_by_floor_list_val[floor].append(token)
            logger.debug(f"Floor {floor}: Purchased item '{item}' -> {token}")
            processed_count += 1

        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing purchased item at index {i}: Floor={floor_val}, Item='{item}'. Error: {e}. Skipping entry."
            )
        except Exception as e:  # Catch acquire errors
            logger.exception(
                f"Unexpected error processing purchased item at index {i}: Floor={floor_val}, Item='{item}'. Skipping entry."
            )

    items_by_floor_tuple_val: Dict[int, Tuple[str, ...]] = {
        k: tuple(v) for k, v in items_by_floor_list_val.items()
    }

    logger.info(
        f"Successfully parsed {processed_count} purchased items across {len(items_by_floor_tuple_val)} floors."
    )
    return items_by_floor_tuple_val


def parse_path_per_floor(
    path_per_floor: List[Optional[str]],
) -> Dict[int, Dict[int, Tuple[str, ...]]]:
    """
    Parse the path taken per floor, given a list of node types.

    Parameters
    ----------
    path_per_floor : list[Optional[str]]
        List of node types, where each node type is a string or None. If None, the
        next entry will be in the next act level (e.g., Act 2, Floor 1).

    Returns
    -------
    dict[int, dict[int, tuple[str, ...]]]
        Dictionary mapping act levels to dictionaries of floor numbers to tuples of
        "GO_TO" and node type tokens.

    Notes
    -----
    The returned dictionary has act levels as keys (0-indexed), and dictionaries as
    values. These dictionaries then map floor numbers (1-indexed, continuous through
    the run) to tuples of tokens. The tokens are "GO_TO" and the node type string.
    """
    if not isinstance(path_per_floor, list):
        logger.error(
            f"Invalid type for parse_path_per_floor: expected list, got {type(path_per_floor)}."
        )
        raise TypeError("Input 'path_per_floor' must be a list")

    path_map: Dict[int, Dict[int, Tuple[str, ...]]] = defaultdict(dict)
    act_level = 0  # Start with Act 1 (0-indexed)
    current_floor_in_run = (
        0  # Overall floor counter, matching typical run file floor numbering
    )

    logger.info(f"Parsing {len(path_per_floor)} path entries.")

    for i, floor_node_type in enumerate(path_per_floor):
        current_floor_in_run += 1  # Standard run file floors are 1-indexed
        try:
            if floor_node_type is None:
                act_level += 1
                logger.debug(
                    f"Path entry {i} (Overall Floor ~{current_floor_in_run-1}-{current_floor_in_run}): Null entry, advancing to Act Level {act_level} (Act {act_level + 1})."
                )
                continue  # Move to next entry, floor number for path_map will continue from here

            if not isinstance(floor_node_type, str):
                raise TypeError(
                    f"Expected string or None for path node at index {i}, got {type(floor_node_type)}"
                )
            if not floor_node_type:  # Empty string node type
                logger.warning(
                    f"Path entry {i} (Act {act_level}, Floor {current_floor_in_run}) is an empty string. Skipping node."
                )
                continue

            token = (go_to(floor_node_type),)
            # path_map keys: act_level (0-indexed), then floor_number (1-indexed, continuous through run)
            if current_floor_in_run in path_map[act_level]:
                logger.warning(
                    f"Duplicate floor number {current_floor_in_run} encountered for Act Level {act_level}. Overwriting node '{path_map[act_level][current_floor_in_run]}' with '{token}'."
                )

            path_map[act_level][current_floor_in_run] = token
            logger.debug(
                f"Path entry {i}: Act {act_level}, Floor {current_floor_in_run} -> Node '{floor_node_type}' -> Token {token}"
            )

        except (TypeError, ValueError) as e:
            logger.error(
                f"Data error processing path entry at index {i} (Floor {current_floor_in_run}): Node='{floor_node_type}'. Error: {e}. Skipping entry."
            )
        except Exception as e:  # Catch go_to errors
            logger.exception(
                f"Unexpected error processing path entry at index {i} (Floor {current_floor_in_run}): Node='{floor_node_type}'. Skipping entry."
            )

    logger.info(
        f"Successfully parsed path across {len(path_map)} act levels, up to overall floor {current_floor_in_run}."
    )
    return dict(path_map)


def parse_cards_transformed(cards_transformed: List[str]) -> Tuple[str, ...]:
    """
    Parse a list of transformed cards into a tuple of tokens.

    This function takes a list of strings, where each pair of strings represents a card
    transformation. The first element of the pair is the original card name, and the second
    element is the transformed card name. The function returns a tuple of tokens, where
    each token is either "TRANSFORM", the original card name, "TO", or the transformed
    card name.

    The function logs the number of processed transform pairs and any errors
    encountered while processing the input list.

    Parameters
    ----------
    cards_transformed : List[str]
        A list of strings, where each pair of strings represents a card transformation.

    Returns
    -------
    Tuple[str, ...]
        A tuple of tokens, where each token is either "TRANSFORM", the original card name,
        "TO", or the transformed card name.
    """
    if not isinstance(cards_transformed, list):
        logger.error(
            f"Expected list for cards_transformed, got {type(cards_transformed)}"
        )
        raise TypeError("Input 'cards_transformed' must be a list")

    all_tokens: List[str] = []
    if len(cards_transformed) % 2 != 0:
        logger.warning(
            f"cards_transformed list has an odd number of elements ({len(cards_transformed)}). The last element ('{cards_transformed[-1]}') will be ignored."
        )

    logger.info(f"Parsing {len(cards_transformed)//2} potential card transform pairs.")
    for i in range(0, len(cards_transformed) - 1, 2):
        old_card_str = cards_transformed[i]
        new_card_str = cards_transformed[i + 1]

        try:
            if not isinstance(old_card_str, str):
                raise ValueError(f"Non-string element for old card: '{old_card_str}'")
            if not isinstance(new_card_str, str):
                raise ValueError(f"Non-string element for new card: '{new_card_str}'")
            if not old_card_str or not new_card_str:
                raise ValueError(
                    f"Empty string found in transform pair: ('{old_card_str}', '{new_card_str}')"
                )

            old_tokens = tokenize_card(old_card_str)
            new_tokens = tokenize_card(new_card_str)

            transform_tokens = ("TRANSFORM", *old_tokens, "TO", *new_tokens)
            all_tokens.extend(transform_tokens)
            logger.debug(
                f"Parsed transform: '{old_card_str}' -> '{new_card_str}'. Tokens: {transform_tokens}"
            )

        except (TypeError, ValueError) as e:  # Catch our raises or from tokenize_card
            logger.error(
                f"Error processing card transform pair at index {i}: ('{old_card_str}', '{new_card_str}'). Error: {e}. Skipping pair."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card transform pair at index {i}: ('{old_card_str}', '{new_card_str}'). Skipping pair."
            )

    logger.info(
        f"Generated {len(all_tokens)} tokens from {len(all_tokens) // (2 + len(old_tokens) + len(new_tokens)) if all_tokens else 0} processed card transform pairs."  # A bit complex to count pairs this way if token lengths vary
    )
    return tuple(all_tokens)


def tokenize_relic_lost(relic: str) -> Tuple[str, ...]:
    """
    Tokenizes a single relic name into a tuple of tokens for losing that relic.

    Parameters
    ----------
    relic : str
        Relic name to be lost.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is a REMOVE token followed by the relic name.

    Raises
    ------
    TypeError
        If input 'relic' is not a string.
    ValueError
        If input 'relic' is empty.
    RuntimeError
        If there is an unexpected error during tokenization.
    """
    if not isinstance(relic, str) or not relic:  # Check for empty string
        logger.error(
            f"Invalid input for tokenize_relic_lost: Expected non-empty string, got {type(relic)}. Value: '{relic}'"
        )
        raise ValueError("Invalid or empty relic name for tokenization")
    try:
        logger.debug(f"Tokenizing relic loss: {relic}")
        return (remove(relic),)
    except Exception as e:  # remove(relic) might raise error
        logger.exception(f"Unexpected error tokenizing relic loss for '{relic}'.")
        raise RuntimeError(f"Failed to tokenize lost relic: {relic}") from e


def parse_relics_lost(relics_lost: List[str]) -> Tuple[str, ...]:
    """
    Converts a list of relic names into a tuple of tokens for losing each relic.

    Parameters
    ----------
    relics_lost : List[str]
        List of relic names to be lost.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is a REMOVE token followed by the relic name.

    Raises
    ------
    TypeError
        If input 'relics_lost' is not a list.
    ValueError
        If any element in 'relics_lost' is not a string or empty.
    RuntimeError
        If any element in 'relics_lost' fails to be tokenized.
    """
    if not isinstance(relics_lost, list):
        logger.error(f"Expected list for relics_lost, got {type(relics_lost)}")
        raise TypeError("Input 'relics_lost' must be a list")

    all_tokens: List[str] = []
    logger.info(f"Parsing {len(relics_lost)} lost relic entries.")

    for i, relic_str in enumerate(relics_lost):
        try:
            # tokenize_relic_lost already checks for non-str or empty string.
            tokens = tokenize_relic_lost(relic_str)
            all_tokens.extend(tokens)
            logger.debug(f"Parsed lost relic at index {i}: '{relic_str}' -> {tokens}")
        except (
            TypeError,
            ValueError,
            RuntimeError,
        ) as e:  # Catch from tokenize_relic_lost
            logger.error(
                f"Error processing lost relic at index {i}: '{relic_str}'. Error: {e}. Skipping entry."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error processing lost relic at index {i}: '{relic_str}'. Skipping entry."
            )

    logger.info(f"Generated {len(all_tokens)} tokens from processed lost relics.")
    return tuple(all_tokens)


def tokenize_knowing_skull_choices(event_choice: str) -> str:
    """
    Tokenizes the lengthy Knowing Skull choice string into a single string token.

    Example logic: "Gain 1 Strength. Lose 5 HP." -> "Strength HP"

    Args:
        event_choice: str, the Knowing Skull choice event string.

    Returns:
        str, a single string token representing the choice.

    Raises:
        TypeError: if input is not a string.
        RuntimeError: if an unexpected error occurs during tokenization.
    """
    if not isinstance(event_choice, str):
        logger.error(
            f"Invalid type for Knowing Skull choice: expected str, got {type(event_choice)}. Value: {event_choice}"
        )
        raise TypeError(f"Expects string for event_choice, got {type(event_choice)}")

    try:
        cleaned_choice = event_choice.strip()
        if not cleaned_choice:
            logger.debug("Tokenizing empty Knowing Skull choice as SKIP.")
            return "SKIP"  # Return a standardized "SKIP" token string

        # Example logic: "Gain 1 Strength. Lose 5 HP." -> "Strength HP"
        # This is highly specific to the event choice format.
        # The original code's logic:
        options = sorted(list(set(cleaned_choice.split(" "))))
        options = [opt for opt in options if opt]  # Remove empty strings

        tokenized_choice_str = " ".join(options)
        if not tokenized_choice_str:  # If all parts were spaces or empty
            logger.warning(
                f"Knowing Skull choice '{event_choice}' resulted in empty token string. Returning 'UNKNOWN_CHOICE'."
            )
            return "UNKNOWN_CHOICE"

        logger.debug(
            f"Tokenized Knowing Skull choice: '{event_choice}' -> '{tokenized_choice_str}'"
        )
        return tokenized_choice_str

    except Exception as e:
        logger.exception(
            f"Unexpected error tokenizing Knowing Skull choice: '{event_choice}'"
        )
        raise RuntimeError(
            f"Failed to tokenize Knowing Skull choice: {event_choice}"
        ) from e


def tokenize_event_name(event_name_val: str) -> Tuple[str, ...]:
    """
    Tokenize an event name into a single string token.

    Parameters
    ----------
    event_name_val : str
        The event name to tokenize.

    Returns
    -------
    Tuple[str, ...]
        A tuple containing the single string token for the event name.
    """
    if not isinstance(event_name_val, str):
        raise TypeError(f"Event name must be a string, got {type(event_name_val)}")
    if not event_name_val:
        raise ValueError("Event name cannot be empty")
    return (event_name(event_name_val),)


def tokenize_player_choice(player_choice: str, event_name_val: str) -> Tuple[str, ...]:
    """
    Tokenize a player choice into a single string token.

    The provided `event_name_val` is used to determine if the choice is a
    "Knowing Skull" choice, in which case it is processed differently.
    Otherwise, the `player_choice` is passed directly to `player_chose` to
    determine the token.

    Parameters
    ----------
    player_choice : str
        The player choice to tokenize.
    event_name_val : str
        The name of the event which the player choice was made for.

    Returns
    -------
    Tuple[str, ...]
        A tuple containing a single string token representing the player choice.
    """
    if not isinstance(player_choice, str):
        raise TypeError(f"Player choice must be a string, got {type(player_choice)}")
    if not isinstance(event_name_val, str):  # Should be validated before this typically
        raise TypeError(
            f"Event name (for context) must be a string, got {type(event_name_val)}"
        )

    processed_choice_str = player_choice
    if event_name_val == "Knowing Skull":
        # tokenize_knowing_skull_choices returns str, which is what player_chose expects
        processed_choice_str = tokenize_knowing_skull_choices(player_choice)

    # player_chose returns a string token
    token_str = player_chose(processed_choice_str)
    return (token_str,)


def tokenize_event_card_upgrade(cards_upgraded: List[str]) -> Tuple[str, ...]:
    """
    Tokenizes a list of card upgrades from an event.

    Parameters
    ----------
    cards_upgraded : List[str]
        List of card names upgraded by an event.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is an upgraded card name.
    """
    if not isinstance(cards_upgraded, list):
        raise TypeError(
            f"Input 'cards_upgraded' must be a list, got {type(cards_upgraded)}"
        )
    all_tokens: List[str] = []
    for i, card_str in enumerate(cards_upgraded):
        if not isinstance(card_str, str):
            logger.warning(
                f"Skipping non-string card at index {i} for event upgrade: {card_str}"
            )
            continue
        try:
            all_tokens.extend(tokenize_upgrade_card(card_str))
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to tokenize card '{card_str}' for event upgrade: {e}")
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card '{card_str}' for event upgrade."
            )
            continue
    return tuple(all_tokens)


def tokenize_event_card_transformed(cards_transformed: List[str]) -> Tuple[str, ...]:
    """
    Tokenizes a list of cards transformed by an event.

    Parameters
    ----------
    cards_transformed : List[str]
        List of card names transformed by an event.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is either "TRANSFORM" or a card name.
    """
    if not isinstance(cards_transformed, list):
        raise TypeError(
            f"Input 'cards_transformed' must be a list, got {type(cards_transformed)}"
        )
    all_tokens: List[str] = []
    for i, card_str in enumerate(
        cards_transformed
    ):  # Here, each card_str is a card that gets transformed
        if not isinstance(card_str, str):
            logger.warning(
                f"Skipping non-string card at index {i} for event transform: {card_str}"
            )
            continue
        try:
            all_tokens.extend(tokenize_transform_card(card_str))
        except (ValueError, TypeError) as e:
            logger.error(
                f"Failed to tokenize card '{card_str}' for event transform: {e}"
            )
            continue
        except Exception as e:
            logger.exception(
                f"Unexpected error processing card '{card_str}' for event transform."
            )
            continue
    return tuple(all_tokens)


def tokenize_relic_gained(relic: str) -> Tuple[str, ...]:  # Changed return type
    """
    Tokenizes a single relic obtained from an event.

    Parameters
    ----------
    relic : str
        Name of the relic obtained.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where the first token is "ACQUIRE" and the second token
        is the relic name.
    """
    if not isinstance(relic, str):
        raise TypeError(f"Relic name must be a string, got {type(relic)}")
    if not relic:
        raise ValueError("Relic name cannot be empty")
    return acquire(relic)


def tokenize_event_relics_obtained(relics_gained: List[str]) -> Tuple[str, ...]:
    """
    Tokenizes a list of relics obtained from an event.

    Parameters
    ----------
    relics_gained : List[str]
        List of relic names obtained from an event.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is either "ACQUIRE" or a relic name.
    """
    if not isinstance(relics_gained, list):
        raise TypeError(
            f"Input 'relics_gained' must be a list, got {type(relics_gained)}"
        )
    all_tokens: List[str] = []
    for i, relic_str in enumerate(relics_gained):
        try:
            all_tokens.extend(
                ("ACQUIRE", relic_str)
            )  # Use extend as it returns a tuple
        except (ValueError, TypeError) as e:
            logger.error(
                f"Failed to tokenize relic '{relic_str}' for event obtained: {e}"
            )
            continue
        except Exception as e:  # acquire might fail
            logger.exception(
                f"Unexpected error processing relic '{relic_str}' for event obtained."
            )
            continue
    return tuple(all_tokens)


def tokenize_event_relics_lost(relics_lost_list: List[str]) -> Tuple[str, ...]:
    """
    Tokenizes a list of lost relics from an event.

    Parameters
    ----------
    relics_lost_list : List[str]
        List of lost relic names from an event.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is a REMOVE token followed by the relic name.
    """
    if not isinstance(relics_lost_list, list):
        raise TypeError(
            f"Input 'relics_lost' must be a list, got {type(relics_lost_list)}"
        )
    all_tokens: List[str] = []
    for i, relic_str in enumerate(relics_lost_list):
        # tokenize_relic_lost validates str and non-empty
        try:
            all_tokens.extend(
                ("REMOVE", relic_str)
            )  # tokenize_relic_lost returns tuple
        except (ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Failed to tokenize relic '{relic_str}' for event lost: {e}")
            continue
        except Exception as e:  # remove() might fail
            logger.exception(
                f"Unexpected error processing relic '{relic_str}' for event lost."
            )
            continue
    return tuple(all_tokens)


def tokenize_potions_obtained_single(
    potion: str,
) -> Tuple[str, ...]:  # Renamed to avoid confusion
    """
    Tokenizes a single potion obtained from an event.

    Parameters
    ----------
    potion : str
        Name of the potion obtained from an event.

    Returns
    -------
    tuple[str, ...]
        Tuple containing a single token, which is the ACQUIRE token for the potion.
    """
    if not isinstance(potion, str):
        raise TypeError(f"Potion name must be a string, got {type(potion)}")
    if not potion:
        raise ValueError("Potion name cannot be empty")
    return (acquire(potion),)


def tokenize_event_potions_obtained(potions: List[str]) -> Tuple[str, ...]:
    """
    Tokenizes a list of potions obtained from an event.

    Parameters
    ----------
    potions : List[str]
        List of potion names obtained from an event.

    Returns
    -------
    tuple[str, ...]
        Tuple of tokens, where each token is either "ACQUIRE" or a potion name.
    """
    if not isinstance(potions, list):
        raise TypeError(f"Input 'potions' must be a list, got {type(potions)}")
    all_tokens: List[str] = []
    for i, potion_str in enumerate(potions):
        # tokenize_potions_obtained_single validates str and non-empty
        try:
            all_tokens.extend(("ACQUIRE", potion_str))  # Use extend
        except (ValueError, TypeError) as e:
            logger.error(
                f"Failed to tokenize potion '{potion_str}' for event obtained: {e}"
            )
            continue
        except Exception as e:  # acquire might fail
            logger.exception(
                f"Unexpected error processing potion '{potion_str}' for event obtained."
            )
            continue
    return tuple(all_tokens)


def parse_events(events: List[Dict[str, Any]]) -> Dict[int, Tuple[str, ...]]:
    """
    Parse a list of event entries, each being a dictionary with specific keys,
    into a dictionary mapping the floor to the corresponding event tokens.

    Parameters
    ----------
    events: List[Dict[str, Any]]
        The list of event entries to parse.

    Returns
    -------
    Dict[int, Tuple[str, ...]]
        A dictionary mapping each floor to its corresponding event tokens.
    """
    if not isinstance(events, list):
        raise TypeError(f"Input 'events' must be a list of dicts, got {type(events)}")

    event_output: Dict[int, Tuple[str, ...]] = {}
    logger.info(f"Parsing {len(events)} event entries.")

    for i, event_data in enumerate(events):
        if not isinstance(event_data, dict):
            logger.warning(
                f"Skipping invalid event entry at index {i}: Expected dict, got {type(event_data)}. Value: {event_data}"
            )
            continue

        try:
            floor_val = event_data.get("floor")
            if floor_val is None:
                raise ValueError("Missing 'floor' key in event data.")
            if not isinstance(floor_val, (int, float)):  # Allow float from JSON
                raise TypeError(
                    f"Expected int/float for 'floor', got {type(floor_val)}"
                )
            floor = int(floor_val)

            tokens: List[str] = []

            event_name_val = event_data.get("event_name")
            if not event_name_val or not isinstance(
                event_name_val, str
            ):  # Must have a name, and must be string
                # Original code used .get("event_name", "") then raised if empty. This is more direct.
                logger.error(
                    f"Event name missing or invalid in event data at index {i}: {event_data}. Skipping event."
                )
                raise ValueError(
                    f"Event name missing or invalid from event data: {event_data}"
                )
            tokens.extend(tokenize_event_name(event_name_val))

            player_choice = event_data.get("player_choice")
            if player_choice is not None:  # Choice is optional
                if not isinstance(player_choice, str):
                    logger.warning(
                        f"Floor {floor}, Event '{event_name_val}': 'player_choice' is not a string ({type(player_choice)}). Skipping choice tokenization."
                    )
                else:  # Empty string player_choice is allowed, might be tokenized specifically (e.g. "SKIP")
                    tokens.extend(tokenize_player_choice(player_choice, event_name_val))

            # Numeric value processing: get, check type, then tokenize if valid
            # For these, 0 is a valid value. Empty string from .get("", "") is problematic.
            # So, check for non-None and non-empty string before tokenizing.

            damage_healed = event_data.get("damage_healed")
            if (
                damage_healed
                and damage_healed is not None
                and (
                    isinstance(damage_healed, float)
                    or isinstance(damage_healed, int)
                    or (isinstance(damage_healed, str) and damage_healed)
                )
            ):
                tokens.extend(tokenize_health_healed(damage_healed))

            damage_taken = event_data.get("damage_taken", 0)
            if (
                damage_taken
                and damage_taken is not None
                and (
                    isinstance(damage_taken, float)
                    or isinstance(damage_taken, int)
                    or (isinstance(damage_taken, str) and damage_taken)
                )
            ):
                tokens.extend(tokenize_damage_taken(damage_taken))

            max_hp_gain = event_data.get("max_hp_gain", 0)
            if (
                max_hp_gain
                and max_hp_gain is not None
                and (
                    isinstance(max_hp_gain, int)
                    or isinstance(max_hp_gain, float)
                    or (isinstance(max_hp_gain, str) and max_hp_gain)
                )
            ):
                tokens.extend(tokenize_max_health_gained(max_hp_gain))

            max_hp_loss = event_data.get("max_hp_loss", 0)
            if (
                max_hp_loss
                and max_hp_loss is not None
                and (
                    isinstance(max_hp_loss, int)
                    or isinstance(max_hp_loss, float)
                    or (isinstance(max_hp_loss, str) and max_hp_loss)
                )
            ):
                tokens.extend(tokenize_max_health_lost(max_hp_loss))

            gold_loss = event_data.get("gold_loss", 0)
            if (
                gold_loss
                and gold_loss is not None
                and (
                    isinstance(gold_loss, int)
                    or (isinstance(gold_loss, str) and gold_loss)
                )
            ):
                tokens.extend(tokenize_gold_lost(gold_loss))

            gold_gain = event_data.get("gold_gain", 0)
            if (
                gold_gain
                and gold_gain is not None
                and (
                    isinstance(gold_gain, int)
                    or (isinstance(gold_gain, str) and gold_gain)
                )
            ):
                tokens.extend(tokenize_gold_gain(gold_gain))

            # List-based fields
            cards_transformed = event_data.get("cards_transformed", [])
            if not isinstance(cards_transformed, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'cards_transformed' not a list."
                )
                cards_transformed = []
            if cards_transformed:
                tokens.extend(tokenize_event_card_transformed(cards_transformed))

            cards_upgraded = event_data.get("cards_upgraded", [])
            if not isinstance(cards_upgraded, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'cards_upgraded' not a list."
                )
                cards_upgraded = []
            if cards_upgraded:
                tokens.extend(tokenize_event_card_upgrade(cards_upgraded))

            cards_removed = event_data.get("cards_removed", [])
            if not isinstance(cards_removed, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'cards_removed' not a list."
                )
                cards_removed = []
            if cards_removed:
                tokens.extend(tokenize_event_card_removal(cards_removed))

            cards_obtained = event_data.get("cards_obtained", [])
            if not isinstance(cards_obtained, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'cards_obtained' not a list."
                )
                cards_obtained = []
            if cards_obtained:
                tokens.extend(tokenize_event_card_acquisition(cards_obtained))

            relics_obtained = event_data.get("relics_obtained", [])
            if not isinstance(relics_obtained, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'relics_obtained' not a list."
                )
                relics_obtained = []
            if relics_obtained:
                tokens.extend(tokenize_event_relics_obtained(relics_obtained))

            relics_lost = event_data.get("relics_lost", [])
            if not isinstance(relics_lost, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'relics_lost' not a list."
                )
                relics_lost = []
            if relics_lost:
                tokens.extend(tokenize_event_relics_lost(relics_lost))

            potions_obtained = event_data.get("potions_obtained", [])
            if not isinstance(potions_obtained, list):
                logger.warning(
                    f"Floor {floor}, Event '{event_name_val}': 'potions_obtained' not a list."
                )
                potions_obtained = []
            if potions_obtained:
                tokens.extend(tokenize_event_potions_obtained(potions_obtained))

            if floor in event_output:
                logger.warning(
                    f"Floor {floor} has multiple event entries. Appending tokens from event '{event_name_val}'."
                )
                event_output[floor] += tuple(tokens)
            else:
                event_output[floor] = tuple(tokens)
            logger.debug(
                f"Floor {floor}, Event '{event_name_val}' tokens: {event_output[floor]}"
            )

        except (KeyError, ValueError, TypeError) as e:  # Catch our specific raises
            logger.error(
                f"Data error processing event entry at index {i}: {e}. Entry: {event_data}. Skipping event for this floor."
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error processing event entry at index {i}: {event_data}. Skipping event for this floor."
            )

    logger.info(
        f"Successfully processed {len(events)} entries, resulting in {len(event_output)} floors with event tokens."
    )
    return event_output


def parse_campfire_choices(
    campfire_choices: list[dict[str, Any]],
) -> dict[int, tuple[str, ...]]:
    """
    Parse campfire choices, mapping floor to choice tokens.

    Parameters
    ----------
    campfire_choices: list[dict[str, Any]]
        A list of dictionaries, each representing a campfire choice.
        Required keys in each dictionary are:
        - "floor": The floor on which the choice was made.
        - "key": The type of choice made, which may be one of
          - "REST": Rest at the campfire.
          - "SMITH": Smith a card.
          - "LIFT": Lift a curse.
          - "DIG": Dig a relic.
          - "PURGE": Purge a card.
          - "RECALL": Recall a card.

    Returns
    -------
    parsed_choices: dict[int, tuple[str, ...]]
        A dictionary mapping each floor to a tuple of tokens representing the choice made.
    """
    parsed_choices = {}
    for choice in campfire_choices:
        floor = choice["floor"]
        match choice["key"]:
            case "REST":
                parsed_choices[floor] = ("REST",)
            case "SMITH":
                parsed_choices[floor] = (
                    "SMITH",
                    "Upgrade",
                    *tokenize_card(choice["data"]),
                )
            case "LIFT":
                parsed_choices[floor] = ("LIFT",)
            case "DIG":
                parsed_choices[floor] = ("DIG",)
            case "PURGE":
                parsed_choices[floor] = ("REMOVE", *tokenize_card(choice["data"]))
            case "RECALL":
                parsed_choices[floor] = ("RECALL",)
            case _:
                raise ValueError(f"Unknown campfire choice key: {choice["key"]}")
    return parsed_choices


def parse_floor_purchases(
    items_purchased: list[str], item_purchase_floors: list[int]
) -> dict[int, list[str]]:
    """
    Parse purchased items, given lists of purchased items and floors on which they were purchased.

    Parameters
    ----------
    items_purchased : list[str]
        List of item names that were purchased from the merchant in the run file.
    item_purchase_floors : list[int]
        List of floors on which items were purchased, in same order as the items in `items_purchased`.

    Returns
    -------
    dict[int, list[str]]
        Dictionary mapping floors to tuples of "ACQUIRE" and item name tokens.
    """
    purchases = defaultdict(list)
    for item, floor in zip(items_purchased, item_purchase_floors):
        purchases[floor].extend(("ACQUIRE", *tokenize_card(item)))
    return purchases


def parse_items_purged(
    items_purged: list[str], items_purged_floors: list[int]
) -> dict[int, list[str]]:
    """
    Parse items purged, given lists of purged items and floors on which they were purged.

    Parameters
    ----------
    items_purged : list[str]
        List of item names that were purged from the run file.
    items_purged_floors : list[int]
        List of floors on which items were purged, in same order as the items in `items_purged`.

    Returns
    -------
    dict[int, list[str]]
        Dictionary mapping floors to tuples of "REMOVE" and item name tokens.
    """
    purged = defaultdict(list)
    for item, floor in zip(items_purged, items_purged_floors):
        purged[floor].extend(("REMOVE", *tokenize_card(item)))
    return purged


def parse_potion_usage(
    potions_obtained: list[dict[str, int | str]], potion_usage: list[int]
) -> dict[int, tuple[str, ...]]:
    """
    Parse potion usage, given potion acquisition data and floors on which potions were used.

    Parameters
    ----------
    potions_obtained : list[dict[str, int | str]]
        List of dictionaries, each containing "floor" and "key" (potion name) from run file.
    potion_usage : list[int]
        List of floors on which potions were used from run file.

    Returns
    -------
    dict[int, tuple[str, ...]]
        Dictionary mapping floors to tuples of "POTION USED" or "POTION POTENTIALLY USED" tokens and their corresponding potion names.
    """
    potion_acquisition = {p_o["floor"]: p_o["key"] for p_o in potions_obtained}
    unique_floors = set(chain(potion_acquisition.keys(), potion_usage))
    all_floors = sorted(list(unique_floors))
    potion_usage = Counter(potion_usage)
    potion_activity: dict[int, tuple[str, ...]] = {}
    potion_inventory = Counter()
    for floor in all_floors:
        if floor in potion_usage:
            if potion_inventory.total() == potion_usage[floor]:
                actions = []
                for potion in potion_inventory.keys():
                    actions.extend(("POTION USED", potion))
                potion_inventory.clear()
                potion_activity[floor] = tuple(actions)
            else:
                actions = []
                for potion in potion_inventory.keys():
                    actions.extend(("POTION POTENTIALLY USED", potion))
                potion_activity[floor] = tuple(actions)
        if floor in potion_acquisition:
            potion_inventory[potion_acquisition[floor]] += 1
    return potion_activity
