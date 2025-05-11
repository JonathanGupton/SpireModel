from SpireModel.components import EVENTS
from SpireModel.components import MODDED_ENEMIES
from SpireModel.components import NEOWS_BLESSING
from SpireModel.components import VALID_CARDS

# New constant defining event_name and player_choice combinations to filter
FILTERED_EVENT_CHOICE_COMBINATIONS = {
    "Liars Game": ["disagreed", "agreed"],
    "Scrap Ooze": ["success", "unsuccessful"],
    "Drug Dealer": ["Got JAX", "Got JAXXED", "Ignored"],
    "Wheel of Change": ["Curse", "Damage"],
    "Golden Wing": ["Card R? ? al"],
    "The Mausoleum": ["Yes", "No"],
    "WeMeetAgain": ["Gold", "Potion", "Card", "Attack"],
    "World of Goop": ["Left"],
    "Accursed Blacksmith": ["Ignore"],
    "Transmorgrifier": ["Skipped"],
    "Golden Shrine": ["Skipped"],
    "The Cleric": ["Purge"],
    "Mysterious Sphere": ["Ignore"],
    "Falling": ["Ignored"],
    "Purifier": ["One Purge", "Skipped"],
    "Designer": [
        "Upgrade Card",
        "Full Service",
        "Remove Card",
        "Removal",
        "Upgrade 2 Random Cards",
        "Transform 2 Cards",
        "Punch",
        "Tried to Upgrade",
    ],
    "Addict": ["Gave JAX"],
    "Upgrade Shrine": ["Skipped"],
    "Bonfire Elementals": ["UNCOMMON", "BASIC", "RARE", "CURSE", "COMMON", "SPECIAL"],
    "FaceTrader": ["Took Face Of Cleric", "Took Mask Of The Ssserpant"],
    "Duplicator": ["One dupe"],
    "Fountain of Cleansing": ["Removed Curse"],
    "SecretPortal": ["Rejected Portal.", "Took Portal."],
}


def _is_modded_neow_bonus(neow_bonus: str) -> bool:
    """Check if the Neow bonus is modded or invalid."""
    if neow_bonus and neow_bonus not in NEOWS_BLESSING:
        return True
    return False


def _has_modded_events(event_choices: list) -> bool:
    """Check if any event in the list is non-standard (unknown name or malformed)."""
    if not isinstance(event_choices, list):
        return True  # Treat malformed data as potentially modded/invalid

    for event in event_choices:
        if not isinstance(event, dict) or "event_name" not in event:
            return True  # Malformed event data

        event_name = event.get("event_name", "")
        if event_name not in EVENTS:
            return True
    return False


def _has_filtered_event_choice_combination(event_choices: list) -> bool:
    """Check if any event choice matches predefined filter combinations."""
    if not isinstance(event_choices, list):
        return False  # This specific filter not met; malformed data handled elsewhere

    for event in event_choices:
        if not isinstance(event, dict):
            continue  # Skip malformed event entries for this specific check

        event_name = event.get("event_name")
        player_choice = event.get("player_choice")

        if event_name in FILTERED_EVENT_CHOICE_COMBINATIONS:
            if player_choice in FILTERED_EVENT_CHOICE_COMBINATIONS[event_name]:
                return True
    return False


def _has_modded_cards(master_deck: list) -> bool:
    """Check if any card in the master deck is invalid."""
    if not isinstance(master_deck, list):
        return True  # Malformed data

    for card in master_deck:
        if not isinstance(card, str) or card not in VALID_CARDS:
            return True
    return False


def _has_modded_enemies(damage_taken: list) -> bool:
    """Check for known modded or malformed enemy names in battle history."""
    if not isinstance(damage_taken, list):
        return False

    for battle in damage_taken:
        if isinstance(battle, dict):
            enemy = battle.get("enemies", "")
            if isinstance(enemy, str) and ":" in enemy:
                return True
            if enemy in MODDED_ENEMIES:
                return True
        else:
            return True
    return False


def _is_invalid_floor(floor_reached_val: object) -> bool:
    """Check if the floor reached is outside the valid range (0 to 999)."""
    try:
        floor_reached = int(floor_reached_val)
        if floor_reached < 0 or floor_reached >= 1000:
            return True
    except (ValueError, TypeError):
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
    Validate if the log is modded or should be filtered.

    Checks performed:
    - Invalid input type
    - Presence of 'daily_mods' or 'neow_cos3'
    - Chose seed enabled
    - Non-zero circlet_count
    - is_beta flag true
    - Special seed used
    - Modded character chosen
    - Modded Neow cost
    - Modded Neow Bonus validity
    - Specific event name/player choice combinations (filtered)
    - Event name validity / malformed event data
    - Master Deck card validity
    - Enemy names in damage_taken history
    - Floor reached range
    """
    if not isinstance(log_event, dict):
        return True

    if "daily_mods" in log_event or "neow_cos3" in log_event:
        return True

    chose_seed = log_event.get("chose_seed", False)
    if chose_seed:
        return True

    circlet_count = log_event.get("circlet_count", 0)
    if _nonzero_circlet_count(circlet_count):
        return True

    is_beta = log_event.get("is_beta", False)
    if is_beta:
        return True

    special_seed = log_event.get("special_seed", 0)
    if _special_seed_selected(special_seed):
        return True

    character_chosen = log_event.get("character_chosen", "")
    if _is_modded_character(character_chosen):
        return True

    neow_cost = log_event.get(
        "neow_cost", ""
    )  # Allow None by not making it "" default if missing
    if _is_modded_neow_cost(neow_cost):
        return True

    neow_bonus = log_event.get("neow_bonus", "")
    if _is_modded_neow_bonus(neow_bonus):
        return True

    event_choices = log_event.get("event_choices", [])
    # New check for specific event/choice combinations to filter
    if _has_filtered_event_choice_combination(event_choices):
        return True

    # Check for unknown event names or malformed event data
    if _has_modded_events(event_choices):
        return True

    master_deck = log_event.get("master_deck", [])
    if _has_modded_cards(master_deck):
        return True

    damage_taken = log_event.get("damage_taken", [])
    if _has_modded_enemies(damage_taken):
        return True

    floor_reached = log_event.get("floor_reached", 0)
    if _is_invalid_floor(floor_reached):
        return True

    return False


def get_modded_reason(log_event: dict) -> str | None:
    """
    Validate if the log is modded/filtered and return the reason.

    Returns the reason string if modded/filtered, otherwise returns None.

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
    - Filtered due to specific event name/player choice combination
    - Modded events found (unknown name or malformed)
    - Modded cards found
    - Modded enemies found
    - Invalid floor reached value
    """
    if not isinstance(log_event, dict):
        return "invalid_input_type"

    if "daily_mods" in log_event or "neow_cos3" in log_event:
        return "daily_mods_or_neow_cos3_present"

    chose_seed = log_event.get("chose_seed", False)
    if chose_seed:
        return "chose_seed_true"

    circlet_count = log_event.get("circlet_count", 0)
    if _nonzero_circlet_count(circlet_count):
        return "nonzero_circlet_count"

    is_beta = log_event.get("is_beta", False)
    if is_beta:
        return "is_beta_true"

    special_seed = log_event.get("special_seed", 0)
    if _special_seed_selected(special_seed):
        return "special_seed_used"

    character_chosen = log_event.get("character_chosen", "")
    if _is_modded_character(character_chosen):
        return "modded_character"

    neow_cost = log_event.get("neow_cost")
    if _is_modded_neow_cost(neow_cost):
        return "modded_neow_cost"

    neow_bonus = log_event.get("neow_bonus", "")
    if _is_modded_neow_bonus(neow_bonus):
        return "modded_neow_bonus"

    event_choices = log_event.get("event_choices", [])
    # New check for specific event/choice combinations
    if _has_filtered_event_choice_combination(event_choices):
        return "filtered_event_choice_combination"

    # Check for unknown event names or malformed event data
    if _has_modded_events(event_choices):
        return "modded_event_found"

    master_deck = log_event.get("master_deck", [])
    if _has_modded_cards(master_deck):
        return "modded_card_found"

    damage_taken = log_event.get("damage_taken", [])
    if _has_modded_enemies(damage_taken):
        return "modded_enemy_found"

    floor_reached = log_event.get("floor_reached")
    if floor_reached is None:
        pass  # Or return "missing_floor_reached" if this should be flagged
    elif _is_invalid_floor(floor_reached):
        return "invalid_floor_value"

    return None
