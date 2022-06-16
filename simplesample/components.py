from ecs.generics import Component, Entity, MetaComponent


class Position(Component, metaclass=MetaComponent):

    def __init__(self, owner: Entity, x: int, y: int):
        super().__init__(owner)
        self.x = x
        self.y = y

    def __eq__(self, other: "Position"):
        return (self.x == other.x) and (self.y == other.y)


class Health(Component, metaclass=MetaComponent):

    def __init__(self, owner: Entity, health: int, max_health: int):
        super().__init__(owner)
        self.health = health
        self.max_health = max_health


class Damage(Component, metaclass=MetaComponent):

    def __init__(self, owner: Entity, damage: int):
        super().__init__(owner)
        self.damage = damage


class Score(Component, metaclass=MetaComponent):

    def __init__(self, owner: Entity):
        super().__init__(owner)
        self.score = 0


class PlayerController(Component, metaclass=MetaComponent):
    pass
