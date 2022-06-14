from ecs.generics import Component, COMPONENT_SIGNATURE_MANAGER, Entity


class Position(Component):
    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    def __init__(self, owner: Entity, x: int, y: int):
        super().__init__(owner)
        self.x = x
        self.y = y

    def __eq__(self, other: "Position"):
        return (self.x == other.x) and (self.y == other.y)


class Health(Component):
    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    def __init__(self, owner: Entity, health: int, max_health: int):
        super().__init__(owner)
        self.health = health
        self.max_health = max_health


class Damage(Component):
    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    def __init__(self, owner: Entity, damage: int):
        super().__init__(owner)
        self.damage = damage


class Score(Component):
    SIGNATURE = COMPONENT_SIGNATURE_MANAGER.next_signature()

    def __init__(self, owner: Entity):
        super().__init__(owner)
        self.score = 0
