import random
from typing import Sequence

READABLE_CHARACTERS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"


def generate_readable_password(length: int = 10, alphabet: Sequence[str] = READABLE_CHARACTERS) -> str:
    """Generates a human-readable password avoiding ambiguous characters."""
    secure_random = random.SystemRandom()
    return ''.join(secure_random.choice(alphabet) for _ in range(length))
