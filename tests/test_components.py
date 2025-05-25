from SpireModel.components import acquire


def test_acquire():
    card = ("Searing Blow", "9X", "9")
    acquired = acquire(card)
    assert acquired == ("ACQUIRE", "Searing Blow", "9X", "9")
