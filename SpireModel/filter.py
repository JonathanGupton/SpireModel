from SpireModel.components import EVENTS
from SpireModel.components import MODDED_ENEMIES
from SpireModel.components import NEOWS_BLESSING
from SpireModel.components import VALID_CARDS

# New constant defining event_name and player_choice combinations to filter
FILTERED_EVENT_CHOICE_COMBINATIONS = {
    "Liars Game": {"disagreed", "agreed"},
    "Scrap Ooze": {"success", "unsuccessful"},
    "Drug Dealer": {"Got JAX", "Got JAXXED", "Ignored"},
    "Wheel of Change": {"Curse", "Damage"},
    "Golden Wing": {"Card R? ? al"},
    "The Mausoleum": ["Yes", "No"],
    "WeMeetAgain": {"Gold", "Potion", "Card", "Attack"},
    "World of Goop": ["Left"],
    "Accursed Blacksmith": ["Ignore"],
    "Transmorgrifier": ["Skipped"],
    "Golden Shrine": ["Skipped"],
    "The Cleric": ["Purge"],
    "Mysterious Sphere": ["Ignore"],
    "Falling": ["Ignored"],
    "Purifier": ["One Purge", "Skipped"],
    "Designer": {
        "Upgrade Card",
        "Full Service",
        "Remove Card",
        "Removal",
        "Upgrade 2 Random Cards",
        "Transform 2 Cards",
        "Punch",
        "Tried to Upgrade",
    },
    "Addict": ["Gave JAX"],
    "Upgrade Shrine": ["Skipped"],
    "Bonfire Elementals": {"UNCOMMON", "BASIC", "RARE", "CURSE", "COMMON", "SPECIAL"},
    "FaceTrader": {"Took Face Of Cleric", "Took Mask Of The Ssserpant"},
    "Duplicator": ["One dupe"],
    "Fountain of Cleansing": ["Removed Curse"],
    "SecretPortal": ["Rejected Portal.", "Took Portal."],
    "N'loth": {
        "Traded a Bag of Marbles",
        "Traded a WristBlade",
        "Traded a Oddly Smooth Stone",
        "Traded a Astrolabe",
        "Traded a Juzu Bracelet",
        "Traded a Boot",
        "Traded a Centennial Puzzle",
        "Traded a Whetstone",
        "Traded a Question Card",
        "Traded a CultistMask",
        "Traded a Bag of Preparation",
        "Traded a Regal Pillow",
        "Traded a Nilry's Codex",
        "Traded a Omamori",
        "Traded a Orrery",
        "Traded a Sundial",
        "Traded a Busted Crown",
        "Traded a Cracked Core",
        "Traded a NeowsBlessing",
        "Traded a MawBank",
        "Traded a Gremlin Horn",
        "Traded a Pear",
        "Traded a Pantograph",
        "Traded a Runic Dome",
        "Traded a Dodecahedron",
        "Traded a PreservedInsect",
        "Traded a Toxic Egg 2",
        "Traded a Lantern",
        "Traded a Bottled Lightning",
        "Traded a Ring of the Snake",
        "Traded a Potion Belt",
        "Traded a Bronze Scales",
        "Traded a Ectoplasm",
        "Traded a Red Skull",
        "Traded a Dream Catcher",
        "Traded a Tiny Chest",
        "Traded a Pocketwatch",
        "Traded a Golden Idol",
        "Traded a Runic Pyramid",
        "Traded a Art of War",
        "Traded a Odd Mushroom",
        "Traded a Bird Faced Urn",
        "Traded a Calling Bell",
        "Traded a Calipers",
        "Traded a Lizard Tail",
        "Traded a Tiny House",
        "Traded a Kunai",
        "Traded a Mercury Hourglass",
        "Traded a Empty Cage",
        "Traded a Gambling Chip",
        "Traded a Bottled Flame",
        "Traded a Blood Vial",
        "Traded a Singing Bowl",
        "Traded a Letter Opener",
        "Traded a Darkstone Periapt",
        "Traded a Strawberry",
        "Traded a War Paint",
        "Traded a Burning Blood",
        "Traded a Blue Candle",
        "Traded a TheAbacus",
        "Traded a Happy Flower",
        "Traded a Sozu",
        "Traded a Matryoshka",
        "Traded a Vajra",
        "Traded a Molten Egg 2",
        "Traded a Ancient Tea Set",
        "Traded a Pen Nib",
        "Traded a Smiling Mask",
        "Traded a DollysMirror",
        "Traded a Torii",
        "Traded a Frozen Egg 2",
        "Traded a Anchor",
        "Traded a Mummified Hand",
        "Traded a Inserter",
        "Traded a Ginger",
        "Traded a ClockworkSouvenir",
        "Traded a Eternal Feather",
        "Traded a Membership Card",
        "Traded a Mango",
        "Traded a HoveringKite",
        "Traded a Orichalcum",
        "Traded a Charon's Ashes",
        "Traded a Du-Vu Doll",
        "Traded a Thread and Needle",
        "Traded a Unceasing Top",
        "Traded a Black Star",
        "Traded a Self Forming Clay",
        "Traded a Strange Spoon",
        "Traded a The Courier",
        "Traded a FaceOfCleric",
        "Traded a Meat on the Bone",
        "Traded a Ornamental Fan",
        "Traded a StoneCalendar",
        "Traded a Old Coin",
        "Traded a Tingsha",
        "Traded a Velvet Choker",
        "Traded a Toolbox",
        "Traded a Necronomicon",
        "Traded a NlothsMask",
        "Traded a Nunchaku",
        "Traded a Shuriken",
        "Traded a Turnip",
        "Traded a Cursed Key",
        "Traded a Bottled Tornado",
        "Traded a Bloody Idol",
        "Traded a Lee's Waffle",
        "Traded a Peace Pipe",
        "Traded a Nuclear Battery",
        "Traded a Paper Frog",
        "Traded a Champion Belt",
        "Traded a Runic Cube",
        "Traded a White Beast Statue",
        "Traded a Tough Bandages",
        "Traded a Red Mask",
        "Traded a Incense Burner",
        "Traded a Dead Branch",
        "Traded a MutagenicStrength",
        "Traded a GremlinMask",
        "Traded a Pandora's Box",
        "Traded a Philosopher's Stone",
        "Traded a Mark of Pain",
        "Traded a FossilizedHelix",
        "Traded a Shovel",
        "Traded a WingedGreaves",
        "Traded a Ice Cream",
        "Traded a Medical Kit",
        "Traded a Emotion Chip",
        "Traded a Cauldron",
        "Traded a Snake Skull",
        "Traded a Cables",
        "Traded a Girya",
        "Traded a Ninja Scroll",
        "Traded a HandDrill",
        "Traded a Chemical X",
        "Traded a FrozenCore",
        "Traded a Coffee Dripper",
        "Traded a SsserpentHead",
        "Traded a Snecko Eye",
        "Traded a Paper Crane",
        "Traded a Magic Flower",
        "Traded a Prayer Wheel",
        "Traded a Sling",
        "Traded a Fusion Hammer",
        "Traded a DataDisk",
        "Traded a Symbiotic Virus",
    },
    "Masked Bandits": {
        "Paid Bandits 279 gold",
        "Paid Bandits 38 gold",
        "Paid Bandits 30 gold",
        "Paid Bandits 458 gold",
        "Paid Bandits 396 gold",
        "Paid Bandits 19 gold",
        "Paid Bandits 112 gold",
        "Paid Bandits 118 gold",
        "Paid Bandits 149 gold",
        "Paid Bandits 32 gold",
        "Paid Bandits 17 gold",
        "Paid Bandits 29 gold",
        "Paid Bandits 172 gold",
        "Paid Bandits 106 gold",
        "Paid Bandits 31 gold",
        "Paid Bandits 250 gold",
        "Paid Bandits 116 gold",
        "Paid Bandits 39 gold",
        "Paid Bandits 159 gold",
        "Paid Bandits 101 gold",
        "Paid Bandits 97 gold",
        "Paid Bandits 69 gold",
        "Paid Bandits 122 gold",
        "Paid Bandits 415 gold",
        "Paid Bandits 285 gold",
        "Paid Bandits 83 gold",
        "Paid Bandits 94 gold",
        "Paid Bandits 67 gold",
        "Paid Bandits 86 gold",
        "Paid Bandits 209 gold",
        "Paid Bandits 128 gold",
        "Paid Bandits 132 gold",
        "Paid Bandits 49 gold",
        "Paid Bandits 443 gold",
        "Paid Bandits 175 gold",
        "Paid Bandits 34 gold",
        "Paid Bandits 102 gold",
        "Paid Bandits 26 gold",
        "Paid Bandits 146 gold",
        "Paid Bandits 353 gold",
        "Paid Bandits 52 gold",
        "Paid Bandits 200 gold",
        "Paid Bandits 401 gold",
        "Paid Bandits 147 gold",
        "Paid Bandits 368 gold",
        "Paid Bandits 51 gold",
        "Paid Bandits 181 gold",
        "Paid Bandits 14 gold",
        "Paid Bandits 80 gold",
        "Paid Bandits 144 gold",
        "Paid Bandits 64 gold",
        "Paid Bandits 13 gold",
        "Paid Bandits 65 gold",
        "Paid Bandits 9 gold",
        "Paid Bandits 7 gold",
        "Paid Bandits 56 gold",
        "Paid Bandits 231 gold",
        "Paid Bandits 48 gold",
        "Paid Bandits 73 gold",
        "Paid Bandits 109 gold",
        "Paid Bandits 10 gold",
        "Paid Bandits 4 gold",
        "Paid Bandits 47 gold",
        "Paid Bandits 46 gold",
        "Paid Bandits 131 gold",
        "Paid Bandits 140 gold",
        "Paid Bandits 110 gold",
        "Paid Bandits 191 gold",
        "Paid Bandits 348 gold",
        "Paid Bandits 27 gold",
        "Paid Bandits 66 gold",
        "Paid Bandits 6 gold",
        "Paid Bandits 234 gold",
        "Paid Bandits 18 gold",
        "Paid Bandits 84 gold",
        "Paid Bandits 37 gold",
        "Paid Bandits 117 gold",
        "Paid Bandits 89 gold",
        "Paid Bandits 164 gold",
        "Paid Bandits 105 gold",
        "Paid Bandits 1 gold",
        "Paid Bandits 3 gold",
        "Paid Bandits 33 gold",
        "Paid Bandits 365 gold",
        "Paid Bandits 50 gold",
        "Paid Bandits 22 gold",
        "Paid Bandits 57 gold",
        "Paid Bandits 42 gold",
        "Paid Bandits 62 gold",
        "Paid Bandits 103 gold",
        "Paid Bandits 173 gold",
        "Paid Bandits 219 gold",
        "Paid Bandits 8 gold",
        "Paid Bandits 228 gold",
        "Paid Bandits 24 gold",
        "Paid Bandits 43 gold",
        "Paid Bandits 53 gold",
        "Paid Bandits 141 gold",
        "Paid Bandits 78 gold",
        "Paid Bandits 171 gold",
        "Paid Bandits 170 gold",
        "Paid Bandits 108 gold",
        "Paid Bandits 96 gold",
        "Paid Bandits 210 gold",
        "Paid Bandits 187 gold",
        "Paid Bandits 45 gold",
        "Paid Bandits 23 gold",
        "Paid Bandits 151 gold",
        "Paid Bandits 300 gold",
        "Paid Bandits 16 gold",
        "Paid Bandits 90 gold",
        "Paid Bandits 178 gold",
        "Paid Bandits 465 gold",
        "Paid Bandits 216 gold",
        "Paid Bandits 85 gold",
        "Paid Bandits 303 gold",
        "Paid Bandits 201 gold",
        "Paid Bandits 434 gold",
        "Paid Bandits 58 gold",
        "Paid Bandits 2 gold",
        "Paid Bandits 163 gold",
        "Paid Bandits 211 gold",
        "Paid Bandits 41 gold",
        "Paid Bandits 115 gold",
        "Paid Bandits 185 gold",
        "Paid Bandits 229 gold",
        "Paid Bandits 137 gold",
        "Paid Bandits 0 gold",
        "Paid Bandits 75 gold",
        "Paid Bandits 28 gold",
        "Paid Bandits 21 gold",
        "Paid Bandits 68 gold",
        "Paid Bandits 195 gold",
        "Paid Bandits 387 gold",
        "Paid Bandits 91 gold",
        "Paid Bandits 40 gold",
        "Paid Bandits 139 gold",
        "Paid Bandits 127 gold",
        "Paid Bandits 437 gold",
        "Paid Bandits 126 gold",
        "Paid Bandits 125 gold",
        "Paid Bandits 207 gold",
        "Paid Bandits 148 gold",
        "Paid Bandits 213 gold",
        "Paid Bandits 2293 gold",
        "Paid Bandits 296 gold",
        "Paid Bandits 160 gold",
        "Paid Bandits 88 gold",
        "Paid Bandits 100 gold",
        "Paid Bandits 111 gold",
        "Paid Bandits 11 gold",
        "Paid Bandits 177 gold",
        "Paid Bandits 301 gold",
        "Paid Bandits 63 gold",
        "Paid Bandits 153 gold",
        "Paid Bandits 99 gold",
        "Paid Bandits 282 gold",
        "Paid Bandits 199 gold",
        "Paid Bandits 145 gold",
        "Paid Bandits 114 gold",
        "Paid Bandits 319 gold",
        "Paid Bandits 82 gold",
        "Paid Bandits 55 gold",
        "Paid Bandits 258 gold",
        "Paid Bandits 129 gold",
        "Paid Bandits 186 gold",
        "Paid Bandits 423 gold",
        "Paid Bandits 136 gold",
        "Paid Bandits 314 gold",
        "Paid Bandits 408 gold",
        "Paid Bandits 15 gold",
        "Paid Bandits 174 gold",
        "Paid Bandits 356 gold",
        "Paid Bandits 270 gold",
        "Paid Bandits 77 gold",
        "Paid Bandits 397 gold",
        "Paid Bandits 5 gold",
        "Paid Bandits 104 gold",
        "Paid Bandits 20 gold",
        "Paid Bandits 92 gold",
        "Paid Bandits 44 gold",
        "Paid Bandits 293 gold",
        "Paid Bandits 93 gold",
        "Paid Bandits 113 gold",
        "Fought over 420 gold",
        "Paid Bandits 71 gold",
        "Paid Bandits 337 gold",
        "Paid Bandits 70 gold",
        "Paid Bandits 76 gold",
        "Paid Bandits 54 gold",
        "Paid Bandits 107 gold",
        "Paid Bandits 297 gold",
        "Paid Bandits 215 gold",
        "Paid Bandits 189 gold",
        "Paid Bandits 143 gold",
        "Paid Bandits 182 gold",
        "Paid Bandits 299 gold",
        "Paid Bandits 98 gold",
        "Paid Bandits 138 gold",
        "Paid Bandits 119 gold",
        "Paid Bandits 35 gold",
        "Paid Bandits 190 gold",
        "Paid Bandits 518 gold",
        "Paid Bandits 309 gold",
        "Paid Bandits 124 gold",
        "Paid Bandits 214 gold",
        "Paid Bandits 133 gold",
        "Paid Bandits 120 gold",
        "Paid Bandits 227 gold",
        "Paid Bandits 247 gold",
        "Paid Bandits 95 gold",
        "Paid Bandits 36 gold",
        "Paid Bandits 288 gold",
        "Paid Bandits 25 gold",
        "Paid Bandits 601 gold",
    },
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
