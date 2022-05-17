from ecs.generics import Component, COMPONENT_SIGNATURE_MANAGER, Entity


class Position(Component):

    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    def __init__(self, owner: Entity, x: float, y: float):
        super().__init__(owner)
        self.x = x
        self.y = y


class PhysicsTypes:

    STATIC = 0
    RIGID_BODY = 1
    TILE_MAP = 2


class Physical(Component):

    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    SUBTYPE: int
    """ determines what kind of physics will be applied to the owner entity, if any (see PhysicsTypes) """

    def __init__(self, owner: Entity, x_offset: float, y_offset: float, ):
        super().__init__(owner)
        self.x_offset = x_offset
        self.y_offset = y_offset
