from typing import Generator

class Log:
    pass



def get_character(data) -> str:
    return data["character_chosen"]


def get_starting_cards(character: str) -> Generator[str, None, None]:
    pass