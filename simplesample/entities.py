from ecs.generics import Entity
from simplesample.components import Position, Health, Damage, Score, PlayerController


class Player(Entity):

    def __init__(self, x: int, y: int):
        super().__init__()
        self.add_component(PlayerController(self))
        self.add_component(Position(self, x, y))
        self.add_component(Health(self, 10, 10))
        self.add_component(Score(self))


class Trap(Entity):

    def __init__(self, x: int, y: int):
        super().__init__()
        self.add_component(Position(self, x, y))
        self.add_component(Damage(self, 1))
