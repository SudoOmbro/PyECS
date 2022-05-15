from typing import List, Type, Set, Callable, Dict
from queue import Queue

from ecs.utils import check_signature, get_atomic_signatures

LAST_SIGNATURE: int = 1
LAST_ID: int = 0


def get_new_component_signature() -> int:
    """ this limits the max amount of systems to 32 at worst """
    global LAST_SIGNATURE
    signature = LAST_SIGNATURE
    LAST_SIGNATURE = LAST_SIGNATURE << 1
    return signature


def get_new_entity_id() -> int:
    """ gets a new entity id """
    global LAST_ID
    new_id = LAST_ID
    LAST_ID += 1
    return new_id


class Scene:

    def __init__(self):
        self._systems: List["System"] = []
        self.entities = EntityCollection()
        self._entities_to_add = Queue()
        self._entities_to_delete = Queue()

    def add_systems(self, systems: List["System"]):
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
        for system in self._systems:
            if (system is not current_system) and (check_signature(signal.signature, system.SIGNATURE)):
                system.signals.put(signal)

    def _add_entities(self):
        while not self._entities_to_add.empty():
            entity = self._entities_to_add.get()
            self.entities.add_entity(entity)

    def _del_entities(self):
        while not self._entities_to_delete.empty():
            entity = self._entities_to_add.get()
            self.entities.delete_entity(entity)

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


class Entity:

    components: List["Component"]

    def __init__(self):
        """ add components in the extension to this method by calling add_component """
        self.signature: int = 0
        self.id = get_new_entity_id()
        self.removed = False

    def add_component(self, component: "Component"):
        self.signature = self.signature | component.SIGNATURE
        self.components.append(component)


class EntityCollection:

    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self._component_filter_cache: Dict[int, List[Component]] = {}
        self._affected_components_since_last_clear: int = 0

    def add_entity(self, entity: Entity):
        """ add an entity to the collection """
        self._affected_components_since_last_clear = self._affected_components_since_last_clear | entity.signature
        self.entities[entity.id] = entity

    def delete_entity(self, entity: Entity):
        """ remove an entity from the collection """
        self._affected_components_since_last_clear = self._affected_components_since_last_clear | entity.signature
        self.entities.pop(entity.id)

    def filter_by_signature(self, component_signature: int):
        """ filters all components of all entities given a single component signature, then caches the result """
        if component_signature in self._component_filter_cache:
            return self._component_filter_cache[component_signature]
        result: List[Component] = []
        for entity_id in self.entities:
            entity = self.entities[entity_id]
            if check_signature(entity.signature, component_signature):
                for component in entity.components:
                    if component.SIGNATURE == component_signature:
                        result.append(component)
        self._component_filter_cache[component_signature] = result
        return result

    def filter_by_type(self, component_type: Type["Component"]):
        """ filters all components of all entities given a component type """
        return self.filter_by_signature(component_type.SIGNATURE)

    def clear_cache(self):
        """ clear the component-filter cache """
        signatures_to_delete = get_atomic_signatures(self._affected_components_since_last_clear)
        for signature in signatures_to_delete:
            if signature in self._component_filter_cache:
                del self._component_filter_cache[signature]
        self._affected_components_since_last_clear = 0


class Component:

    SIGNATURE: int
    """ 
    call get_new_component_signature and assign the return 
    value to SIGNATURE for each new type of component you make 
    """

    def __init__(self, owner: Entity):
        self.owner = owner


class Signal:
    """ create your own custom signals to pass to other systems by inheriting from this class """

    def __init__(self, involved_entities: List[Entity]):
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
