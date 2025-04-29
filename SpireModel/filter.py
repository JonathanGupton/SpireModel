from SpireModel.components import EVENTS
from SpireModel.components import MODDED_ENEMIES
from SpireModel.components import NEOWS_BLESSING
from SpireModel.components import VALID_CARDS


def _is_modded_neow_bonus(neow_bonus: str) -> bool:
    """Check if the Neow bonus is modded or invalid."""
    # Consider an empty bonus valid unless explicitly defined otherwise
    if neow_bonus and neow_bonus not in NEOWS_BLESSING:
        return True
    return False


def _has_modded_events(event_choices: list) -> bool:
    """Check if any event in the list is non-standard."""
    if not isinstance(event_choices, list):
        # Or raise TypeError, depending on desired strictness
        return True  # Treat malformed data as potentially modded/invalid

    for event in event_choices:
        # Basic check for expected structure
        if not isinstance(event, dict) or "event_name" not in event:
            return True  # Malformed event data

        event_name = event.get("event_name", "")
        if event_name not in EVENTS:
            return True
    return False


def _has_modded_cards(master_deck: list) -> bool:
    """Check if any card in the master deck is invalid."""
    if not isinstance(master_deck, list):
        return True  # Malformed data

    for card in master_deck:
        # Assuming cards are strings as per original logic
        if not isinstance(card, str) or card not in VALID_CARDS:
            return True
    return False


def _has_modded_enemies(damage_taken: list) -> bool:
    """Check for known modded or malformed enemy names in battle history."""
    if not isinstance(damage_taken, list):
        # Original function returned False here, implying non-list is not modded.
        # Returning True might be safer if unexpected types indicate issues.
        # Let's stick to original logic for now:
        return False  # Treat non-list as not containing modded enemies *by this check*

    for battle in damage_taken:
        if isinstance(battle, dict):
            enemy = battle.get("enemies", "")
            # Check 1: Mod Indicator (like BaseMod)
            if isinstance(enemy, str) and ":" in enemy:
                return True
            # Check 2: Explicit Modded Enemy List
            if enemy in MODDED_ENEMIES:
                return True
        else:
            # Malformed battle entry in damage_taken list
            return True  # Treat malformed data as potentially modded/invalid
    return False


def _is_invalid_floor(floor_reached_val: object) -> bool:
    """Check if the floor reached is outside the valid range (0 to 999)."""
    try:
        floor_reached = int(floor_reached_val)
        if floor_reached < 0 or floor_reached >= 1000:
            return True
    except (ValueError, TypeError):
        # Failed to convert to int, treat as invalid/modded
        return True
    return False


def _is_modded_neow_cost(
    neow_cost, modded_neow_costs=frozenset(("", "FIFTY_PERCENT_DAMAGE", "BASIC_CARDS"))
):
    if neow_cost in modded_neow_costs:
        return True
    return False


def _is_modded_character(character_chosen):
    if character_chosen == "SCHOLAR":
        return True
    return False


def _nonzero_circlet_count(circlet_count):
    if circlet_count > 0:
        return True
    return False


def _special_seed_selected(special_seed):
    if special_seed > 0:
        return True
    return False


def is_modded_log(log_event: dict) -> bool:
    """
    Validate if the log is modded by checking various components.

    Checks performed:
    - Neow Bonus validity
    - Event name validity
    - Master Deck card validity
    - Enemy names in damage_taken history
    - Floor reached range
    """
    if not isinstance(log_event, dict):
        # Handle case where input is not a dictionary at all
        return True  # Or raise TypeError, depending on desired behavior

    if "daily_mods" in log_event or "neow_cos3" in log_event:
        return True

    chose_seed = log_event.get("chose_seed", 1)
    if chose_seed:
        return True

    circlet_count = log_event.get("circlet_count", 1)
    if _nonzero_circlet_count(circlet_count):
        return True

    is_beta = log_event.get("is_beta", True)
    if is_beta:
        return True

    special_seed = log_event.get("special_seed", 1)
    if _special_seed_selected(special_seed):
        return True

    character_chosen = log_event.get("character_chosen", "")
    if _is_modded_character(character_chosen):
        return True

    neow_cost = log_event.get("neow_cost", "")
    if _is_modded_neow_cost(neow_cost):
        return True

    # 1. Check Neow Bonus
    neow_bonus = log_event.get("neow_bonus", "")
    if _is_modded_neow_bonus(neow_bonus):
        # print("Debug: Modded Neow Bonus") # Optional: for debugging
        return True

    # 2. Check Events
    event_choices = log_event.get("event_choices", [])
    if _has_modded_events(event_choices):
        # print("Debug: Modded Events") # Optional: for debugging
        return True

    # 3. Check Cards
    master_deck = log_event.get("master_deck", [])
    if _has_modded_cards(master_deck):
        # print("Debug: Modded Cards") # Optional: for debugging
        return True

    # 4. Check Enemies
    damage_taken = log_event.get("damage_taken", [])
    if _has_modded_enemies(damage_taken):
        # print("Debug: Modded Enemies") # Optional: for debugging
        return True

    # 5. Check Floor Reached
    # Use a default unlikely to trigger the check if key is missing,
    # or handle missing key explicitly if required. Let's default to 0.
    floor_reached = log_event.get("floor_reached", 0)
    if _is_invalid_floor(floor_reached):
        # print("Debug: Invalid Floor") # Optional: for debugging
        return True

    # If none of the checks returned True, the log is considered not modded
    return False


def get_modded_reason(log_event: dict) -> str | None:
    """
    Validate if the log is modded and return the reason.

    Returns the reason string if modded, otherwise returns None.

    Checks performed (in order, first match returns):
    - Invalid input type
    - Presence of 'daily_mods' or 'neow_cos3'
    - Chose seed enabled
    - Non-zero circlet_count
    - is_beta flag true
    - Special seed used
    - Modded character chosen
    - Modded Neow cost
    - Modded Neow bonus
    - Modded events found
    - Modded cards found
    - Modded enemies found
    - Invalid floor reached value
    """
    if not isinstance(log_event, dict):
        return "invalid_input_type"  # Handle non-dict input

    # Early checks for specific mod indicators or settings
    if "daily_mods" in log_event or "neow_cos3" in log_event:
        return "daily_mods_or_neow_cos3_present"

    # Using .get with default that *won't* trigger the mod check if key is missing
    chose_seed = log_event.get("chose_seed", False)  # Default to False if missing
    if chose_seed:  # Check if True
        return "chose_seed_true"

    circlet_count = log_event.get("circlet_count", 0)  # Default to 0 if missing
    if _nonzero_circlet_count(circlet_count):
        return "nonzero_circlet_count"

    is_beta = log_event.get("is_beta", False)  # Default to False if missing
    if is_beta:  # Check if True
        return "is_beta_true"

    special_seed = log_event.get("special_seed", 0)  # Default to 0 if missing
    if _special_seed_selected(special_seed):
        return "special_seed_used"

    character_chosen = log_event.get("character_chosen", "")
    if _is_modded_character(character_chosen):
        return "modded_character"

    neow_cost = log_event.get("neow_cost")  # Check specific values, None is okay
    if _is_modded_neow_cost(neow_cost):
        return "modded_neow_cost"

    # Checks using helper functions
    neow_bonus = log_event.get("neow_bonus", "")
    if _is_modded_neow_bonus(neow_bonus):
        return "modded_neow_bonus"

    event_choices = log_event.get("event_choices", [])
    if _has_modded_events(event_choices):
        return "modded_event_found"

    master_deck = log_event.get("master_deck", [])
    if _has_modded_cards(master_deck):
        return "modded_card_found"

    damage_taken = log_event.get("damage_taken", [])
    if _has_modded_enemies(damage_taken):
        return "modded_enemy_found"

    floor_reached = log_event.get(
        "floor_reached"
    )  # Check explicitly for None later if needed
    if floor_reached is None:
        # Decide if missing floor_reached is implicitly modded/invalid
        # return "missing_floor_reached" # Uncomment if needed
        pass  # Or assume valid if missing, depending on requirements
    elif _is_invalid_floor(floor_reached):
        return "invalid_floor_value"

    # If none of the checks returned a reason, the log is considered not modded
    return None
