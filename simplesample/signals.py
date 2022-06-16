from typing import Tuple, List

from ecs.generics import Signal, Entity, MetaSignal


class CollisionEvent(Signal, metaclass=MetaSignal):
    pass


class MoveEvent(Signal, metaclass=MetaSignal):

    def __init__(self, involved_entities: List[Entity], direction: Tuple[int, int]):
        super().__init__(involved_entities)
        self.direction = direction
