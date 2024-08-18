import typing
from .entity import Entity
from .components import BaseComponent, BaseSystem, ExtendedSystem
import time


class EntityManager:
    __slots__ = ("_count", "_entities",
                 "component_manager",
                 "_entities_to_remove_next_frame")

    system_manager: "SystemManager" = None

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
        self.system_manager._remove_all_entities()

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

    def get_component(self, entity: Entity, component_type: typing.Type[BaseComponent]) -> BaseComponent:
        try:
            return self._components[component_type][entity]
        except KeyError:
            raise KeyError(f"Entity: {entity} does not have component type: {component_type}")


class SystemManager:
    __slots__ = ("entity_manager", "component_manager",
                 "_systems", "_extended_systems",
                 "_systems_ran_already", "_extended_systems_ran_already", "ret")

    def __init__(self, entity_manager: EntityManager, component_manager: ComponentManager) -> None:
        self.entity_manager = entity_manager
        self.component_manager = component_manager
        self._systems: dict[BaseSystem, set[int]] = dict()
        self._extended_systems: dict[ExtendedSystem, set[int]] = dict()
        self._systems_ran_already: set[BaseSystem] = set()
        self._extended_systems_ran_already: set[ExtendedSystem] = set()

        self.ret = {}
        for sys in BaseSystem.__subclasses__():
            self.ret[sys] = {}
        for sys in ExtendedSystem.__subclasses__():
            self.ret[sys] = {}

        BaseSystem.entity_manager = self.entity_manager
        BaseSystem.component_manager = self.component_manager
        BaseSystem.system_manager = self
        ExtendedSystem.entity_manager = self.entity_manager
        ExtendedSystem.component_manager = self.component_manager
        ExtendedSystem.system_manager = self

        EntityManager.system_manager = self

    def add_system(self, entity: Entity, system: BaseSystem) -> None:
        if system not in self._systems:
            self._systems[system] = set()
        self._systems[system].add(hash(entity))

    def add_extended_system(self, entity: Entity, system: ExtendedSystem) -> None:
        if system not in self._extended_systems:
            self._extended_systems[system] = set()
        self._extended_systems[system].add(hash(entity))

    def run_all_systems(self, /, **kwargs) -> dict[typing.Type[BaseSystem] | typing.Type[ExtendedSystem], dict]:
        # t0 = time.time()

        for base_system, entities in self._systems.items():
            self.ret[type(base_system)][base_system] = {}
            if base_system in self._systems_ran_already:
                continue
            for entity in entities:
                self.ret[type(base_system)][base_system][entity] = base_system.update_entity(self.entity_manager._entities[entity], self.component_manager.get_all_components(entity, base_system.required_component_types), **kwargs)  # type: ignore

        # t1 = time.time()

        for ext_system, entities in self._extended_systems.items():
            if ext_system in self._extended_systems_ran_already:
                continue
            data = {self.entity_manager._entities[entity_]: self.component_manager.get_all_components(self.entity_manager._entities[entity_], ext_system.required_component_types) for entity_ in entities}
            self.ret[type(ext_system)][ext_system] = ext_system.update_entities(data, **kwargs)

        # print(f"To run all systems it took: {time.time() - t0:.4f} seconds. (BaseSystem: {t1 - t0:.7f} sec. ExtendedSystem: {time.time() - t1:.7f})")

        # self._remove_all_entities()
        self._systems_ran_already.clear()
        self._extended_systems_ran_already.clear()

        return self.ret

    def run_base_system(self, system: BaseSystem, **kwargs) -> dict[int, object]:
        entities = self._systems[system]
        ret = {}
        for entity in entities:
            ret[entity] = system.update_entity(self.entity_manager._entities[entity], self.component_manager.get_all_components(entity, system.required_component_types), **kwargs)  # type: ignore

        self._systems_ran_already.add(system)
        return ret

    def run_extended_system(self, system: ExtendedSystem, **kwargs) -> object:
        entities = self._extended_systems[system]
        data = {self.entity_manager._entities[e]: self.component_manager.get_all_components(self.entity_manager._entities[e], system.required_component_types) for e in entities}
        ret = system.update_entities(data, **kwargs)

        self._extended_systems_ran_already.add(system)
        return ret

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
            for ext_system, ens in self._extended_systems.items():
                if en in ens:
                    to_remove["extended"].add((ext_system, en))

        for (s, e) in to_remove["base"]:
            self._systems[s].remove(e)
            self.component_manager.remove_entity(e)
        for (s, e) in to_remove["extended"]:
            self._extended_systems[s].remove(e)
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
