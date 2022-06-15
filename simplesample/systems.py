import random
from copy import copy
from typing import Dict, Tuple, List

from ecs.generics import System, Scene, Entity
from simplesample.components import Position, Damage, Score, PlayerController, Health
from simplesample.entities import Trap, Player
from simplesample.signals import CollisionEvent, MoveEvent


DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "u": (0, -1),
    "d": (0, 1),
    "l": (-1, 0),
    "r": (1, 0),
    "e": (0, 0)
}
MAP_SIZE = 20


def handle_damage_signal(system: System, scene: Scene, event: CollisionEvent):
    perpetrator: Entity = event.involved_entities.get_first_signature_match(Damage.SIGNATURE)
    target: Entity = event.involved_entities.get_first_signature_match(Health.SIGNATURE)
    damage_component: Damage = perpetrator.get_component_by_type(Damage)
    health_component: Health = target.get_component_by_type(Health)
    health_component.health -= damage_component.damage
    scene.delete_entity(perpetrator)


def handle_move_signal(system: System, scene: Scene, event: MoveEvent):
    target: Entity = event.involved_entities.get_last()
    position: Position = target.get_component_by_type(Position)
    next_x: int = position.x + event.direction[0]
    next_y: int = position.y + event.direction[1]
    if (-1 < next_x < 20) and (-1 < next_y < 20):
        position.x = next_x
        position.y = next_y
        # print(f"Moved to x: {next_x}, y: {next_y}")
    else:
        print("Can't move there!")


class GenerationSystem(System):
    PRIORITY = -1

    def update(self) -> int:
        for _ in range(MAP_SIZE):
            x = random.randrange(0, MAP_SIZE)
            y = random.randrange(0, MAP_SIZE)
            self.scene.add_entity(Trap(x, y))
        x = random.randrange(0, MAP_SIZE)
        y = random.randrange(0, MAP_SIZE)
        self.scene.add_entity(Player(x, y))
        self.scene.delete_systems([self])
        return 0


class InputSystem(System):
    PRIORITY = 0

    def update(self) -> int:
        targets = self.scene.entities.filter_by_component_type(PlayerController)
        input_string: str = ""
        while True:
            input_string = input("Where do you want to go? ")
            if input_string and (input_string[0] in DIRECTIONS):
                break
            print("direction must be ('up', 'down', 'left', 'right')")
        if input_string == "end":
            self.exit_message = "terminated by user"
            return 1
        for target in targets:
            self.scene.propagate_signal(self, MoveEvent([target], DIRECTIONS[input_string[0]]))
        return 0


class PhysicsSystem(System):
    PRIORITY = 1

    SIGNAL_HANDLERS = {
        MoveEvent.TYPE_ID: {
            0: handle_move_signal
        }
    }

    def update(self) -> int:
        self.handle_signals()
        entities = self.scene.entities.filter_by_component_type(Position)
        entities_to_check = copy(entities)
        # This is the most inefficient way possible to do collisions, but it can be parallelized
        for entity in entities:
            entities_to_check.remove(entity)
            for collider in entities_to_check:
                pos1: Position = entity.get_component_by_type(Position)
                pos2: Position = collider.get_component_by_type(Position)
                if pos1 == pos2:
                    self.scene.propagate_signal(self, CollisionEvent([entity, collider]))
        return 0


class DamageSystem(System):
    PRIORITY = 2

    SIGNAL_HANDLERS = {
        CollisionEvent.TYPE_ID: {
            Damage.SIGNATURE | Health.SIGNATURE: handle_damage_signal
        }
    }

    def update(self) -> int:
        self.handle_signals()
        return 0


class ScoringSystem(System):
    PRIORITY = 3

    def update(self) -> int:
        entities = self.scene.entities.filter_by_component_type(Score)
        for entity in entities:
            score_component: Score = entity.get_component_by_type(Score)
            score_component.score += 1
        return 0


class RenderingSystem(System):
    PRIORITY = 4

    def update(self) -> int:
        # os.system('cls')
        players: List[Player] = self.scene.entities.filter_by_component_types((PlayerController, Position, Score))
        for player in players:
            position: Position = player.get_component_by_type(Position)
            score: Score = player.get_component_by_type(Score)
            health: Health = player.get_component_by_type(Health)
            print(f"x: {position.x}, y: {position.y}, score: {score.score}, hp: {health.health}")
        return 0
