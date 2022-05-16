from functools import cache
from typing import List, Type, Set, Callable, Dict
from queue import Queue

from ecs.utils import check_signature, SignedObject, IDManager, Collection

LAST_SIGNATURE: int = 1

ENTITY_ID_MANAGER = IDManager()
SIGNAL_ID_MANAGER = IDManager()


def get_new_component_signature() -> int:
    """ this limits the max amount of systems to 32 at worst """
    global LAST_SIGNATURE
    signature = LAST_SIGNATURE
    LAST_SIGNATURE = LAST_SIGNATURE << 1
    return signature


@cache
def get_signature_from_list_of_components(component_types: List[Type["Component"]]) -> int:
    signature: int = 0
    for c_type in component_types:
        signature = signature | c_type.SIGNATURE
    return signature


class Scene:

    def __init__(self):
        self._systems: List["System"] = []
        self.entities = EntityCollection()
        self._entities_to_add = Queue()
        self._entities_to_delete = Queue()

    def add_systems(self, systems: List["System"]):
        """ adds and sorts all given systems by priority """
        for system in systems:
            self._systems.append(system)
        self._systems.sort(key=lambda s: s.PRIORITY)

    def add_entity(self, entity: "Entity"):
        """ add an entity to the scene """
        self._entities_to_add.put(entity)

    def delete_entity(self, entity: "Entity"):
        """ remove an entity from the scene """
        if entity.removed:
            return
        self._entities_to_delete.put(entity)
        entity.removed = True

    def propagate_signal(self, current_system: "System", signal: "Signal"):
        """ propagates the given signal to the systems that have a matching signature """
        for system in self._systems:
            if (system is not current_system) and (check_signature(signal.signature, system.SIGNATURE)):
                system.signals.put(signal)

    def _add_entities(self):
        while not self._entities_to_add.empty():
            entity = self._entities_to_add.get()
            self.entities.add(entity)

    def _del_entities(self):
        while not self._entities_to_delete.empty():
            entity = self._entities_to_add.get()
            self.entities.delete(entity)

    def update(self):
        """ update the scene """
        # run all enabled systems
        for system in self._systems:
            if system.enabled:
                system.update()
        # add & delete entities
        clear: bool = not (self._entities_to_delete.empty() and self._entities_to_add.empty())
        self._del_entities()
        self._add_entities()
        if clear:
            self.entities.clear_cache()


class Entity(SignedObject):

    components: List["Component"]

    def __init__(self):
        """ add components in the extension to this method by calling add_component """
        self.signature: int = 0
        self.id = ENTITY_ID_MANAGER.next_id()
        self.removed = False

    def add_component(self, component: "Component"):
        """ adds a component to the entity """
        self.signature = self.signature | component.SIGNATURE
        self.components.append(component)

    def has_component(self, component_type: Type["Component"]) -> bool:
        """ returns whether the entity has a component that matches the given type """
        return check_signature(self.signature, component_type.SIGNATURE)

    def get_components_by_signature(self, signature: int) -> List["Component"]:
        result: List[Component] = []
        for component in self.components:
            if check_signature(signature, component.SIGNATURE):
                result.append(component)
        return result

    def get_components_by_types(self, component_types: List[Type["Component"]]) -> List["Component"]:
        signature = get_signature_from_list_of_components(component_types)
        return self.get_components_by_signature(signature)


class EntityCollection(Collection):

    def add(self, obj: Entity):
        super().add(obj)

    def delete(self, obj: Entity):
        super().delete(obj)

    def filter_by_type(self, component_type: Type["Component"]) -> List[Entity]:
        """ filters all components of all entities given a component type """
        # noinspection PyTypeChecker
        return self.filter_by_signature(component_type.SIGNATURE)

    def filter_by_types(self, component_types: List[Type["Component"]]) -> List[Entity]:
        """ filters all components of all entities given a list of component types """
        signature = get_signature_from_list_of_components(component_types)
        # noinspection PyTypeChecker
        return self.filter_by_signature(signature)


class Component:

    SIGNATURE: int
    """ 
    call get_new_component_signature and assign the return 
    value to SIGNATURE for each new type of component you make 
    """

    def __init__(self, owner: Entity):
        self.owner = owner


class Signal(SignedObject):
    """ create your own custom signals to pass to other systems by inheriting from this class """

    def __init__(self, involved_entities: List[Entity]):
        self.id = SIGNAL_ID_MANAGER.next_id()
        self.signature = 0
        for entity in involved_entities:
            self.signature = self.signature | entity.signature


class System:

    PRIORITY: int
    """ The priority the system has on the others. The lower it is, the sooner the system will be processed """
    REQUIRE: Set[Type[Component]]
    """ A set containing all the required components to make the system work """
    SIGNATURE: int = 0
    """ 
    call calculate_required_signature and assign the return 
    value to SIGNATURE for each new type of system you make 
    """
    SIGNAL_HANDLERS: Dict[Type[Signal], Callable[["System", Scene, Signal], None]]
    """ A switch that defines which handlers should be used to handle the signal """

    @classmethod
    def calculate_required_signature(cls):
        """ call this function at class creation time and assign the value to SIGNATURE """
        for ctype in cls.REQUIRE:
            cls.SIGNATURE = cls.SIGNATURE | ctype.SIGNATURE

    def __init__(self, room: Scene, enabled: bool = True):
        self.room = room
        self.entities = []
        self.signals = Queue()
        self.enabled = enabled

    def signature_match(self, entity: Entity) -> bool:
        """ returns whether the given entity's signature matches with the system's """
        return check_signature(entity.signature, self.SIGNATURE)

    def handle_signals(self):
        """ handle all received signals """
        while not self.signals.empty():
            signal = self.signals.get()
            handler = self.SIGNAL_HANDLERS.get(type(signal), default_signal_handler)
            handler(self, self.room, signal)

    def update(self):
        """ put system logic here """
        raise NotImplemented


def default_signal_handler(system: System, room: Scene, signal: Signal):
    """ does nothing :) """
    return None
