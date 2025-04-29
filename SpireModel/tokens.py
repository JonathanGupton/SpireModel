from SpireModel.components import BASE_TOKENS
from SpireModel.components import NUMBERS
from SpireModel.components import CURSECARDS
from SpireModel.components import NEOWS_BLESSING
from SpireModel.components import EVENTS
from SpireModel.components import VALID_CARDS
from SpireModel.components import ENEMIES
from SpireModel.components import NEOW_COST
from SpireModel.components import CHARACTERS
from SpireModel.components import POTIONS
from SpireModel.components import PATHS


TOKEN_COLLECTION = sorted(
    [
        *BASE_TOKENS
        | NUMBERS
        | CURSECARDS
        | NEOWS_BLESSING
        | EVENTS
        | VALID_CARDS
        | ENEMIES
        | NEOW_COST
        | CHARACTERS
        | POTIONS
        | PATHS
    ]
)

TOKEN_MAP = {word: idx for word, idx in enumerate(TOKEN_COLLECTION)}
