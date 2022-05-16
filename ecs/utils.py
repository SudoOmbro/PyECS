from functools import cache
from typing import List, Dict


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


class IDManager:
    """ Manages IDs """

    def __init__(self):
        self._last_id: int = 0

    def next_id(self) -> int:
        current: int = self._last_id
        self._last_id += 1
        return current


class SignedObject:
    """ Basic object that has a signature and an id """

    signature: int
    id: int


class Collection:
    """ A generic collection of SignedObjects that can be filtered by signature """

    def __init__(self):
        self.objects: Dict[int, SignedObject] = {}
        self._filter_cache: Dict[int, List[SignedObject]] = {}
        self._affected_signatures_since_last_clear: int = 0

    def add(self, obj: SignedObject):
        """ adds an object to the collection """
        self._affected_signatures_since_last_clear = self._affected_signatures_since_last_clear | obj.signature
        self.objects[obj.id] = obj

    def delete(self, obj: SignedObject):
        """ removes an object from the collection """
        self._affected_signatures_since_last_clear = self._affected_signatures_since_last_clear | obj.signature
        self.objects.pop(obj.id)

    def filter_by_signature(self, signature: int) -> List[SignedObject]:
        """ filters all objects given a single signature, then caches the result """
        if signature in self._filter_cache:
            return self._filter_cache[signature]
        result: List[SignedObject] = []
        for entity_id in self.objects:
            obj = self.objects[entity_id]
            if check_signature(obj.signature, signature):
                result.append(obj)
        self._filter_cache[signature] = result
        return result

    def clear_cache(self):
        """ clear the filter cache, should be called every time one or more object are added/removed """
        signatures_to_delete = get_atomic_signatures(self._affected_signatures_since_last_clear)
        for signature in signatures_to_delete:
            if signature in self._filter_cache:
                del self._filter_cache[signature]
        self._affected_signatures_since_last_clear = 0
