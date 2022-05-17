from functools import cache
from typing import List, Type, Callable, Dict, Tuple
from queue import Queue

from ecs.utils import check_signature, SignedObject, IDManager, Collection, SignatureManager

COMPONENT_SIGNATURE_MANAGER = SignatureManager()

ENTITY_ID_MANAGER = IDManager()
SIGNAL_TYPE_ID_MANAGER = IDManager()


@cache
def get_signature_from_components(component_types: Tuple[Type["Component"]]) -> int:
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
            if (
                (system is not current_system) and
                (signal.TYPE_ID in system.SIGNAL_HANDLERS) and
                (check_signature(signal.signature, system.SIGNATURE))
            ):
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

    def get_components_by_types(self, component_types: Tuple[Type["Component"]]) -> List["Component"]:
        signature = get_signature_from_components(component_types)
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

    def filter_by_types(self, component_types: Tuple[Type["Component"]]) -> List[Entity]:
        """ filters all components of all entities given a list of component types """
        signature = get_signature_from_components(component_types)
        # noinspection PyTypeChecker
        return self.filter_by_signature(signature)


class Component:
    SIGNATURE: int
    """ 
    call COMPONENT_SIGNATURE_MANAGER.next_signature() and assign the return 
    value to SIGNATURE for each new type of component you make 
    """

    def __init__(self, owner: Entity):
        self.owner = owner


class Signal(SignedObject):
    """ create your own custom signals to pass to other systems by inheriting from this class """

    TYPE_ID: int
    """
    assign the return value of SIGNAL_TYPE_ID_MANAGER.next_id() when writing a new signal
    """


class System:
    PRIORITY: int
    """ The priority the system has on the others. The lower it is, the sooner the system will be processed """
    REQUIRE: Tuple[Type[Component]]
    """  """
    SIGNATURE: int = 0
    """ 
    call calculate_required_signature and assign the return 
    value to SIGNATURE for each new type of system you make 
    """
    SIGNAL_HANDLERS: Dict[int, Callable[["System", Scene, Signal], None]]
    """ 
    A switch that defines which handlers should be used to handle the signal, 
    basically a map between signal signature & handler.
    """

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

    def handle_signals(self):
        """ handle all received signals """
        while not self.signals.empty():
            signal = self.signals.get()
            handler = self.SIGNAL_HANDLERS[signal.TYPE_ID]
            handler(self, self.room, signal)

    def update(self):
        """ put system logic here """
        raise NotImplemented
