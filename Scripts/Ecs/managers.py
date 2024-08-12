import typing
from .entity import Entity
from .components import BaseComponent, BaseSystem, ExtendedSystem
import time


class EntityManager:
    __slots__ = ("_count", "_entities",
                 "component_manager",
                 "_entities_to_remove_next_frame")

    def __init__(self, component_manager: "ComponentManager") -> None:
        self.component_manager = component_manager
        self._count = 0
        self._entities: dict[int, Entity] = dict()
        self._entities_to_remove_next_frame: set[int] = set()

    def add_entity(self) -> Entity:
        entity = Entity(self._count)
        self._entities[hash(entity)] = entity
        self._count += 1
        return entity

    def remove_entity(self, entity: Entity) -> None:
        self._entities_to_remove_next_frame.add(hash(entity))

    def final_remove(self) -> set[int]:
        if self._entities_to_remove_next_frame:
            # t0 = time.time()

            copy = self._entities_to_remove_next_frame.copy()
            self._entities_to_remove_next_frame.clear()

            for e in copy:
                del self._entities[e]

            # print(f"To remove {len(copy)} entities it took: {time.time() - t0} seconds")
            return copy
        return set()


ComponentInstanceType = typing.TypeVar("ComponentInstanceType", bound=BaseComponent)


class ComponentManager:
    __slots__ = ("_components", )

    def __init__(self) -> None:
        self._components: dict[typing.Type[BaseComponent], dict[Entity, ComponentInstanceType]] = dict()  # type: ignore

        self.__init_components()

    def __init_components(self) -> None:
        for subclass in BaseComponent.__subclasses__():
            self._components[subclass] = dict()

    def add_component(self, entity: Entity, components: typing.List[BaseComponent]) -> None:
        for component in components:
            self._components[type(component)][entity] = component

    def remove_component(self, entity: Entity, component_type) -> None:
        try:
            del self._components[component_type][entity]
        except KeyError:
            raise KeyError(f"Entity: {entity} does not have component type: {component_type}")

    def remove_entity(self, entity: Entity) -> None:
        for component_type in self._components:
            try:
                del self._components[component_type][entity]
            except KeyError:
                pass

    def get_all_components(self, entity: Entity, component_types: typing.List[typing.Type[BaseComponent]]) -> dict[typing.Type[BaseComponent], BaseComponent]:
        ret = dict()
        for t in component_types:
            ret[t] = self._components[t][entity]
        return ret


class SystemManager:
    __slots__ = ("entity_manager", "component_manager",
                 "_systems", "_systems_extended")

    def __init__(self, entity_manager: EntityManager, component_manager: ComponentManager) -> None:
        self.entity_manager = entity_manager
        self.component_manager = component_manager
        self._systems: dict[BaseSystem, set[int]] = dict()
        self._systems_extended: dict[ExtendedSystem, set[int]] = dict()

    def add_system(self, entity: Entity, system: BaseSystem) -> None:
        if system not in self._systems:
            self._systems[system] = set()
        self._systems[system].add(hash(entity))

    def add_extended_system(self, entity: Entity, system: ExtendedSystem) -> None:
        if system not in self._systems_extended:
            self._systems_extended[system] = set()
        self._systems_extended[system].add(hash(entity))

    def run_all_systems(self, /, **kwargs) -> None:
        # t0 = time.time()

        for base_system, entities in self._systems.items():
            for entity in entities:
                base_system.update_entity(self.entity_manager._entities[entity], self.component_manager.get_all_components(entity, base_system.required_component_types), **kwargs)  # type: ignore

        # t1 = time.time()

        for ext_system, entities in self._systems_extended.items():
            data = {self.entity_manager._entities[entity_]: self.component_manager.get_all_components(self.entity_manager._entities[entity_], ext_system.required_component_types) for entity_ in entities}
            ext_system.update_entities(data, **kwargs)

        # print(f"To run all systems it took: {time.time() - t0:.4f} seconds. (BaseSystem: {t1 - t0:.7f} sec. ExtendedSystem: {time.time() - t1:.7f})")

        self._remove_all_entities()

    def _remove_all_entities(self) -> None:
        entities = self.entity_manager.final_remove()
        if not entities:
            return

        # t0 = time.time()
        to_remove = {"base": set(), "extended": set()}  # type: ignore

        for en in entities:
            for base_system, ens in self._systems.items():
                if en in ens:
                    to_remove["base"].add((base_system, en))
            for ext_system, ens in self._systems_extended.items():
                if en in ens:
                    to_remove["extended"].add((ext_system, en))

        for (s, e) in to_remove["base"]:
            self._systems[s].remove(e)
            self.component_manager.remove_entity(e)
        for (s, e) in to_remove["extended"]:
            self._systems_extended[s].remove(e)
            self.component_manager.remove_entity(e)

        # print(f"To execute the final removal of entities it took: {time.time() - t0} seconds")

    def debug(self) -> None:
        d = dict()
        for s, i in self._systems.items():
            d[s] = len(i)
        print(d)


def make_all_managers() -> typing.Tuple:
    component_manager = ComponentManager()
    entity_manager = EntityManager(component_manager)
    system_manager = SystemManager(entity_manager, component_manager)
    return (component_manager, entity_manager, system_manager)
