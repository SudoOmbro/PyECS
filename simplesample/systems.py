from ecs.generics import System, Scene
from simplesample.components import Position, Damage, Score
from simplesample.signals import CollisionEvent


def handle_damage_signal(system: System, scene: Scene, event: CollisionEvent):
    damage_component: Damage = event.perpetrator.get_component_by_type(Damage)
    event.entity -= damage_component.damage


class InputSystem(System):
    PRIORITY = 0

    def update(self):
        pass  # TODO


class PhysicsSystem(System):
    PRIORITY = 1

    def update(self):
        entities = self.scene.entities.filter_by_component_type(Position)
        for entity in entities:
            for collider in entities:
                if entity == collider:
                    continue
                pos1: Position = entity.get_component_by_type(Position)
                pos2: Position = collider.get_component_by_type(Position)
                if pos1 == pos2:
                    self.scene.propagate_signal(self, CollisionEvent(entity, collider))


class DamageSystem(System):
    PRIORITY = 2

    SIGNAL_HANDLERS = {
        CollisionEvent.TYPE_ID: {
            Damage.SIGNATURE: handle_damage_signal
        }
    }

    def update(self):
        self.handle_signals()


class ScoringSystem(System):
    PRIORITY = 3

    def update(self):
        entities = self.scene.entities.filter_by_component_type(Score)
        for entity in entities:
            score_component: Score = entity.get_component_by_type(Score)
            score_component.score += 1
