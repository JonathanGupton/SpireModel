"""Module containing the complete corpus of tokens with the numeric mapping"""

from SpireModel.components import BASE_TOKENS
from SpireModel.components import NUMBERS
from SpireModel.components import CARD_ACTIONS
from SpireModel.components import CURSECARDS
from SpireModel.components import NEOWS_BLESSING
from SpireModel.components import EVENTS
from SpireModel.components import VALID_CARDS
from SpireModel.components import ENEMIES
from SpireModel.components import NEOW_COST
from SpireModel.components import CHARACTERS
from SpireModel.components import PATHS
from SpireModel.components import PATH_ACTIONS
from SpireModel.components import POTIONS
from SpireModel.components import POTION_ACTIONS
from SpireModel.components import POTION_SLOT_ACTIONS
from SpireModel.components import RELIC_ACTIONS


CARD_TOKENS = set()
for card in VALID_CARDS:
    if "+" in card:
        continue
    for action in CARD_ACTIONS:
        CARD_TOKENS.add(action(card))


CURSECARD_TOKENS = set()
for card in CURSECARDS:
    for action in CARD_ACTIONS:
        CURSECARD_TOKENS.add(action(card))


POTION_TOKENS = set()
for potion in POTIONS:
    for action in POTION_ACTIONS:
        POTION_TOKENS.add(action(potion))

RELIC_TOKENS = set()
for relic in RELIC_TOKENS:
    for action in RELIC_ACTIONS:
        RELIC_TOKENS.add(action(relic))

PATH_TOKENS = set()
for path in PATHS:
    for action in PATH_ACTIONS:
        PATH_TOKENS.add(action(path))

## Combine all the collections, sort them, then map the token to the sorted index value
TOKEN_COLLECTION = sorted(
    [
        *BASE_TOKENS
        | NUMBERS
        | CURSECARD_TOKENS
        | NEOWS_BLESSING
        | EVENTS
        | CARD_TOKENS
        | ENEMIES
        | NEOW_COST
        | CHARACTERS
        | POTION_TOKENS
        | PATH_TOKENS
        | POTION_SLOT_ACTIONS
    ]
)


TOKEN_MAP = {word: idx for word, idx in enumerate(TOKEN_COLLECTION)}
