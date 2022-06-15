from ecs.generics import Scene
from simplesample.systems import GenerationSystem, InputSystem, PhysicsSystem, DamageSystem, ScoringSystem, \
    RenderingSystem


def main():
    """
    implements a 20 by 20 randomly generated grid in which you walk.
    By walking you score points & if walk on a trap you lose hp.
    """
    current_scene: Scene = Scene()
    # generate and render first frame
    current_scene.add_systems([
        GenerationSystem(current_scene),
        RenderingSystem(current_scene)
    ])
    current_scene.update()
    current_scene.update()
    # add gameplay systems
    current_scene.add_systems([
        InputSystem(current_scene),
        PhysicsSystem(current_scene),
        DamageSystem(current_scene),
        ScoringSystem(current_scene),
    ])
    # run game loop until finished
    while True:
        if current_scene.update() == 1:
            return


if __name__ == "__main__":
    main()
