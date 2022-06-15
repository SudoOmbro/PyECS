from functools import cache
from typing import List, Type, Callable, Dict, Tuple
from queue import Queue

from ecs.utils import check_signature, SignedObject, IDManager, CachedCollection, SignatureManager, Collection

COMPONENT_SIGNATURE_MANAGER = SignatureManager()

ENTITY_ID_MANAGER = IDManager()
SIGNAL_TYPE_ID_MANAGER = IDManager()


@cache
def get_signature_from_components(component_types: Tuple[Type["Component"]]) -> int:
    """ returns the signature matching the given combination of components """
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

    def delete_systems(self, systems: List["System"]):
        """ adds and sorts all given systems by priority """
        for system in systems:
            self._systems.remove(system)
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
                (signal.TYPE_ID in system.SIGNAL_HANDLERS)
            ):
                system.signals.put(signal)

    def _add_entities(self):
        while not self._entities_to_add.empty():
            entity = self._entities_to_add.get()
            self.entities.add(entity)

    def _del_entities(self):
        while not self._entities_to_delete.empty():
            entity = self._entities_to_delete.get()
            self.entities.delete(entity)

    def update(self) -> int:
        """ update all the enabled systems in the scene, return 1 if a system set the termination flag """
        # run all enabled systems
        for system in self._systems:
            if system.enabled:
                if system.update() == 1:
                    print(system.exit_message)  # TODO Change this to a logger
                    return 1
        # add & delete entities
        clear: bool = not (self._entities_to_delete.empty() and self._entities_to_add.empty())
        self._del_entities()
        self._add_entities()
        if clear:
            self.entities.clear_cache()
        return 0


class Entity(SignedObject):

    def __init__(self):
        """ add components in the extension to this method by calling add_component """
        self.signature: int = 0
        self.id = ENTITY_ID_MANAGER.next_id()
        self.removed = False
        self.components: List["Component"] = []

    def _calculate_signature(self):
        """ recalculate the signature """
        self.signature = 0
        for component in self.components:
            self.signature = self.signature | component.SIGNATURE

    def add_component(self, component: "Component"):
        """ adds a component to the entity """
        self.signature = self.signature | component.SIGNATURE
        self.components.append(component)

    def remove_components(self, components_to_remove: List["Component"]):
        """ remove a list of components from the entity """
        for component in components_to_remove:
            self.components.remove(component)
        self._calculate_signature()

    def remove_component(self, component_to_remove: "Component"):
        """ remove a component from the entity """
        self.components.remove(component_to_remove)
        self._calculate_signature()

    def has_component(self, component_type: Type["Component"]) -> bool:
        """ returns whether the entity has a component that matches the given type """
        return check_signature(self.signature, component_type.SIGNATURE)

    def get_components_by_signature(self, signature: int) -> List["Component"]:
        result: List[Component] = []
        for component in self.components:
            if check_signature(signature, component.SIGNATURE):
                result.append(component)
        return result

    def get_component_by_signature(self, signature: int) -> "Component" or None:
        for component in self.components:
            if check_signature(signature, component.SIGNATURE):
                return component
        return None

    def get_components_by_types(self, component_types: Tuple[Type["Component"]]) -> List["Component"]:
        signature = get_signature_from_components(component_types)
        return self.get_components_by_signature(signature)

    def get_component_by_type(self, component_type: ["Component"]) -> "Component" or None:
        return self.get_component_by_signature(component_type.SIGNATURE)


class EntityCollection(CachedCollection):

    def add(self, obj: Entity):
        super().add(obj)

    def delete(self, obj: Entity):
        super().delete(obj)

    def filter_by_component_type(self, component_type: Type["Component"]) -> List[Entity]:
        """ returns all entities that have a given component type """
        # noinspection PyTypeChecker
        return self.filter_by_signature(component_type.SIGNATURE)

    def filter_by_component_types(self, component_types: Tuple[Type["Component"]]) -> List[Entity]:
        """ returns all entities that have all given component types """
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

    def __init__(self, involved_entities: List[Entity]):
        self.involved_entities = Collection()
        self.signature = 0
        for entity in involved_entities:
            self.signature = self.signature | entity.signature
            self.involved_entities.add(entity)


def default_handler(system: "System", scene: Scene, signal: Signal):
    """ does nothing, returned by _retrieve_handler if no matching handler is found for the given signal """
    return None


class System:
    PRIORITY: int
    """ The priority the system has on the others. The lower it is, the sooner the system will be processed """
    SIGNAL_HANDLERS: Dict[int, Dict[int, Callable[["System", Scene, Signal], None]]] = {}
    """ 
    A switch that defines which handlers should be used to handle the signal, 
    basically a map between signal ID, signal signature & handler.
    
    Put 0 as signature to have the handler associated with it handle every signal regardless of signature
    """

    def __init__(self, scene: Scene, enabled: bool = True):
        self.scene = scene
        self.signals = Queue()
        self.enabled = enabled
        self.exit_message = ""

    @cache
    def _retrieve_handler(self, signal_id: int, signal_signature: int):
        handler_category = self.SIGNAL_HANDLERS[signal_id]  # we are sure this exists since it's checked while propagating the signal
        for signature in handler_category:
            if check_signature(signal_signature, signature):
                return handler_category[signature]
        return default_handler

    def handle_signals(self):
        """ handle all received signals """
        while not self.signals.empty():
            signal = self.signals.get()
            handler = self._retrieve_handler(signal.TYPE_ID, signal.signature)
            handler(self, self.scene, signal)

    def update(self) -> int:
        """ put system logic here, you can use the return value to exit the loop you presumably implemented """
        raise NotImplemented
