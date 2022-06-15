from typing import Tuple, List

from ecs.generics import Signal, SIGNAL_TYPE_ID_MANAGER, Entity


class CollisionEvent(Signal):
    TYPE_ID = SIGNAL_TYPE_ID_MANAGER.next_id()


class MoveEvent(Signal):
    TYPE_ID = SIGNAL_TYPE_ID_MANAGER.next_id()

    def __init__(self, involved_entities: List[Entity], direction: Tuple[int, int]):
        super().__init__(involved_entities)
        self.direction = direction
