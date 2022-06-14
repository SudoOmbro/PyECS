from ecs.generics import Signal, SIGNAL_TYPE_ID_MANAGER, Entity


class CollisionEvent(Signal):
    TYPE_ID = SIGNAL_TYPE_ID_MANAGER.next_id()

    def __init__(self, perpetrator: Entity, victim: Entity):
        self.signature = perpetrator.signature
        self.perpetrator = perpetrator
        self.entity = victim

