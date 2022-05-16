from ecs.generics import Component, get_new_component_signature, Entity


class PositionComponent(Component):

    SIGNATURE = get_new_component_signature()

    def __init__(self, owner: Entity, x: float, y: float):
        super().__init__(owner)
        self.x = x
        self.y = y


class MomentumComponent(Component):

    def __init__(self, owner: Entity, x: float, y: float, ):
        super().__init__(owner)


class ColliderComponent(Component):

    SIGNATURE = get_new_component_signature()

    def __init__(self, owner: Entity, ):
        super().__init__(owner)

