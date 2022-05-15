from functools import cache
from typing import List


@cache
def check_signature(signature: int, contains: int) -> bool:
    """ checks if signature contains 'contains', caches result """
    return (signature & contains) == contains


def get_atomic_signatures(signature: int) -> List[int]:
    """ returns a list of single component signatures given a complex entity signature """
    atom: int = 1
    result: List[int] = []
    while atom <= signature:
        if check_signature(signature, atom):
            result.append(atom)
        atom = atom << 1
    return result
