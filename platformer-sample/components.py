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

    def __init__(self, owner: Entity, x_offset: float, y_offset: float, x_size: float, y_size: float):
        super().__init__(owner)
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.x_size = x_size
        self.y_size = y_size


class RigidBody(Physical):

    SUBTYPE = PhysicsTypes.RIGID_BODY

    def __init__(
            self,
            owner: Entity,
            x_offset: float,
            y_offset: float,
            x_size: float,
            y_size: float,
            x_speed: float,
            y_speed: float,
            gravity: bool
    ):
        super().__init__(owner, x_offset, y_offset, x_size, y_size)
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.gravity = gravity
