from collections import defaultdict
from typing import Generator

from SpireModel.components import acquire
from SpireModel.components import battle
from SpireModel.components import go_to
from SpireModel.components import event_name
from SpireModel.components import player_chose
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


def tokenize_damage_taken(damage_taken: int | str) -> tuple[str, ...]:
    # TODO: Finish this
    tokenize_number(str(damage_taken))


def tokenize_health_healed(health_healed: int | str):
    # TODO:  implement this
    pass


def tokenize_max_health_gained(max_health_gained: int | str):
    pass


def tokenize_max_health_lost(max_health_lost: int | str):
    pass


def parse_event_choices(event_choices: list[dict[str, int | str]]):
    event_by_floor: dict[int, list[str]] = defaultdict(list)
    for event in event_choices:
        floor = event["floor"]
        event_by_floor[floor].append(event_name(event["event_name"]))
        event_by_floor[floor].append(player_chose(event["player_choice"]))
        if event.get("damage_healed", 0) != 0:
            pass


# Event choice "Knowing Skull" choices
# choices = (
#     ("SKIP",),
#     ("CARD",),
#     ("GOLD",),
#     ("POTION",),
#     (
#         "CARD",
#         "GOLD",
#     ),
#     ("CARD", "POTION"),
#     ("CARD", "GOLD", "POTION"),
# )


# Event choices "Masked Bandits"
# Fought Bandits
# or "Paid Fearfully", "LOST [all] GOLD"

# Event Choices "N'loth"
# "Ignored"
# "Traded Relic", "LOSE [relic]", "GAIN [Nloth's Gift]"

# Liars Game
# 		Ignored	3625777
# 		AGREE	7169100
# 		disagreed	21401
# 		agreed	43850
# Event Choices "Liars Game"
# "Ignored" or "AGREE"
# Map "disagreed" to "Ignored"
# Map "agreed" to "AGREE"


# Scrap Ooze
# 		Success	10_078_849
# 		Fled	638_341
# 		success	59_758
# 		unsuccessful	3_506
# Event Choices "Scrap Ooze"
# "Success", "Fled"
# Map "success" to "Success"
# Map "unsuccessful" to "Fled"


# Vampires
# 		Became a vampire	1301074
# 		Ignored	3050187
# 		Became a vampire (Vial)	265792
# Need to add log of the five strikes being removed with this event


# Drug Dealer
# 		Obtain J.A.X.	436637
# 		Inject Mutagens	2748255
# 		Became Test Subject	1419615
# 		Got JAX	1843
# 		Got JAXXED	2790
# 		Ignored	4758
# Do I nix the "Got Jax", "Got JAXXED", "Ignored" runs?


# Wheel of Change
# 		Full Heal	761072
# 		Card Removal	761113
# 		Relic	764114
# 		Gold	762496
# 		Cursed	739372
# 		Damaged	744841
# 		Curse	4544
# 		Damage	4588
# Golden Wing
# 		Card Removal	7045840
# 		Ignored	1777829
# 		Gained Gold	2007510
# 		Card R??al	1
# The Mausoleum
# 		Opened	3984459
# 		Ignored	602232
# 		Yes	23627
# 		No	2674
# Forgotten Altar
# 		Shed Blood	3031002
# 		Gave Idol	771738
# 		Smashed Altar	796158
# Colosseum
# 		Fight	3969815
# 		Fought Nobs	2116570
# 		Fled From Nobs	1555560
# WeMeetAgain
# 		Gave Potion	2341365
# 		Gave Card	789272
# 		Paid Gold	1107333
# 		Ignored	150042
# 		Gold	5241
# 		Potion	11194
# 		Card	4083
# 		Attack	669
# The Lab
# 		Got Potions	141428
# Match and Keep!
# 		1 cards matched	1883123
# 		2 cards matched	1569434
# 		3 cards matched	416872
# 		0 cards matched	766891
# 		5 cards matched	21993
# 		4 cards matched	58560
# 		6 cards matched	11
# Big Fish
# 		Donut	4940596
# 		Box	4299196
# 		Banana	1595501
# World of Goop
# 		Gather Gold	9451396
# 		Left Gold	1365962
# 		Left	9085
# Shining Light
# 		Entered Light	9470815
# 		Ignored	1315318
# Accursed Blacksmith
# 		Forge	2592554
# 		Rummage	1812913
# 		Ignored	6197
# 		Ignore	732
# Cursed Tome
# 		Ignored	980262
# 		Obtained Book	3477717
# 		Stopped	101485
# Transmorgrifier
# 		Transformed	4313854
# 		Ignored	202877
# 		Transform	25951
# 		Skipped	942
# Living Wall
# 		Forget	2674635
# 		Grow	5885996
# 		Change	2368018
# Dead Adventurer
# 		Searched '2' times	1482753
# 		Searched '3' times	588279
# 		Searched '1' times	1640542
# 		Searched '0' times	317138
# Golden Shrine
# 		Desecrate	1579251
# 		Pray	2965700
# 		Ignored	21248
# 		Skipped	146
# Nest
# 		Stole From Cult	3097467
# 		Joined the Cult	1522142
# The Cleric
# 		Leave	2707237
# 		Card Removal	5588981
# 		Healed	2360160
# 		Purge	1
# The Library
# 		Heal	1694831
# 		Read	2910143
# Back to Basics
# 		Simplicity	3071997
# 		Elegance	1537705
# Ghosts
# 		Ignored	3757777
# 		Became a Ghost	855663
# Mushrooms
# 		Healed and dodged fight	966338
# 		Fought Mushrooms	3043278
# Golden Idol
# 		Take Damage	4394183
# 		Take Wound	3288390
# 		Ignored	718908
# 		Lose Max HP	2549891
# Mysterious Sphere
# 		Fight	2599662
# 		Ignored	1245627
# 		Ignore	4296
# Falling
# 		Removed Skill	1410465
# 		Removed Power	426211
# 		Removed Attack	1964129
# 		Ignored	4
# SensoryStone
# 		Memory 3	840983
# 		Memory 1	2637450
# 		Memory 2	317942
# The Joust
# 		Bet on Murderer	693651
# 		Bet on Owner	297118
# Purifier
# 		Purged	4227394
# 		Ignored	368163
# 		One Purge	24623
# 		Skipped	3292
# The Woman in Blue
# 		Bought 1 Potion	1089517
# 		Bought 3 Potions	484410
# 		Bought 0 Potions	1585522
# 		Bought 2 Potions	677726
# Designer
# 		Upgraded Two	322988
# 		Upgrade	248006
# 		Upgrade and Remove	565850
# 		Punched	35738
# 		Transformed Cards	76413
# 		Upgrade Card	1034
# 		Single Remove	51484
# 		Full Service	2203
# 		Remove Card	199
# 		Removal	1489
# 		Upgrade 2 Random Cards	1380
# 		Transform 2 Cards	363
# 		Punch	180
# 		Tried to Upgrade	362
# Addict
# 		Obtained Relic	3120691
# 		Stole Relic	1046383
# 		Ignored	1783
# 		Gave JAX	121
# Upgrade Shrine
# 		Upgraded	4635070
# 		Ignored	9856
# 		Skipped	60
# Beggar
# 		Gave Gold	2921824
# 		Ignored	1479374
# Tomb of Lord Red Mask
# 		Paid	1794713
# 		Ignored	1570242
# 		Wore Mask	431995
# MindBloom
# 		Fight	3013957
# 		Upgrade	262721
# 		Gold	312664
# 		Heal	201104
# The Moai Head
# 		Ignored	182160
# 		Heal	443128
# 		Gave Idol	378648
# Bonfire Elementals
# 		Offered Basic	2589564
# 		Offered Curse	395928
# 		Offered Uncommon	674532
# 		Offered Common	346724
# 		Offered Special	353849
# 		Offered Rare	443565
# 		UNCOMMON	4037
# 		BASIC	15067
# 		RARE	2583
# 		CURSE	2795
# 		COMMON	2463
# 		SPECIAL	54
# Winding Halls
# 		Embrace Madness	1516640
# 		Writhe	949869
# 		Max HP	1338451
# FaceTrader
# 		Touch	1069190
# 		Trade	3093011
# 		Leave	254830
# 		Took Face Of Cleric	1
# 		Took Mask Of The Ssserpant	3
# Duplicator
# 		Copied	1671896
# 		One dupe	9270
# 		Ignored	27926
# Fountain of Cleansing
# 		Removed Curses	616099
# 		Removed Curse	4054
# 		Ignored	15479
# SecretPortal
# 		Ignored	429110
# 		Took Portal	115595
# 		Rejected Portal.	1949
# 		Took Portal.	742
# NoteForYourself
# 		Took Card	820468
# 		Ignored	825103
# Lab
# 		Got Potions	4309710
