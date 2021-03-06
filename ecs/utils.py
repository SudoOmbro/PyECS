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


def combine_signatures(objects: List["SignedObject"]) -> int:
    result: int = 0
    for obj in objects:
        result = result | obj.signature
    return result


class IDManager:
    """ Manages IDs """

    def __init__(self):
        self._last_id: int = 0

    def next_id(self) -> int:
        current: int = self._last_id
        self._last_id += 1
        return current


class SignatureManager:
    """ Manages signatures """

    def __init__(self):
        self._last_signature: int = 1

    def next_signature(self) -> int:
        current: int = self._last_signature
        self._last_signature = self._last_signature << 1
        return current


class SignedObject:
    """ Basic object that has a signature and an id """

    signature: int
    id: int


class Collection:
    """
    A generic collection of SignedObjects that can be filtered by signature.
    """

    def __init__(self):
        self.objects: Dict[int, SignedObject] = {}
        self.last_added_id: int = 0

    def add(self, obj: SignedObject):
        """ adds an object to the collection """
        self.last_added_id = obj.id
        self.objects[obj.id] = obj

    def delete(self, obj: SignedObject):
        """ removes an object from the collection """
        self.objects.pop(obj.id)

    def get_last(self) -> SignedObject or None:
        """ returns the last object added to the collection """
        return self.objects.get(self.last_added_id, None)

    def filter_by_signature(self, signature: int) -> List[SignedObject]:
        """ filters all objects given a single signature """
        result: List[SignedObject] = []
        for entity_id in self.objects:
            obj = self.objects[entity_id]
            if check_signature(obj.signature, signature):
                result.append(obj)
        return result

    def get_first_signature_match(self, signature: int) -> SignedObject or None:
        for entity_id in self.objects:
            obj = self.objects[entity_id]
            if check_signature(obj.signature, signature):
                return obj
        return None


class CachedCollection(Collection):
    """
    A generic collection of SignedObjects that can be filtered by signature, also includes a cache to speed up lookups.
    """

    def __init__(self):
        super().__init__()
        self._filter_cache: Dict[int, List[SignedObject]] = {}
        self._affected_signatures_since_last_clear: int = 0

    def add(self, obj: SignedObject):
        """ adds an object to the collection """
        self._affected_signatures_since_last_clear = self._affected_signatures_since_last_clear | obj.signature
        super().add(obj)

    def delete(self, obj: SignedObject):
        """ removes an object from the collection """
        self._affected_signatures_since_last_clear = self._affected_signatures_since_last_clear | obj.signature
        super().delete(obj)

    def filter_by_signature(self, signature: int) -> List[SignedObject]:
        """ filters all objects given a single signature, then caches the result """
        if signature in self._filter_cache:
            return self._filter_cache[signature]
        result: List[SignedObject] = super().filter_by_signature(signature)
        self._filter_cache[signature] = result
        return result

    def clear_cache(self):
        """ clear the filter cache, should be called every time one or more object are added/removed """
        signatures_to_delete = get_atomic_signatures(self._affected_signatures_since_last_clear)
        for signature in signatures_to_delete:
            if signature in self._filter_cache:
                del self._filter_cache[signature]
        self._affected_signatures_since_last_clear = 0
