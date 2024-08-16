import typing
from .entity import Entity

if typing.TYPE_CHECKING:
    from .managers import EntityManager, ComponentManager, SystemManager


class BaseComponent:
    __slots__ = ("__dict__")

    def __init__(self) -> None:
        pass

    def __repr__(self):
        return f"<Component {type(self).__name__}>"

    def __str__(self):
        return f"<Component {type(self).__name__}>"


class BaseSystem:
    __slots__ = ("required_component_types", )

    entity_manager: "EntityManager" = None
    component_manager: "ComponentManager" = None
    system_manager: "SystemManager" = None

    def __init__(self, required_component_types: typing.List[typing.Type[BaseComponent]]) -> None:
        self.required_component_types = required_component_types

    def update_entity(self, entity: Entity, entity_components: dict[typing.Type[BaseComponent], BaseComponent], **kwargs) -> None:
        pass

    def __str__(self) -> str:
        return f"<{type(self).__name__}>"

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"


class ExtendedSystem:
    __slots__ = ("required_component_types", )

    entity_manager: "EntityManager" = None
    component_manager: "ComponentManager" = None
    system_manager: "SystemManager" = None

    def __init__(self, required_component_types: typing.List[typing.Type[BaseComponent]]) -> None:
        self.required_component_types = required_component_types

    def update_entities(self, entites_data: dict[Entity, dict[typing.Type[BaseComponent], BaseComponent]], **kwargs) -> None:
        """
        How to get entites and components from the parameter:

        ```
        for entity, entity_components in entites_data.items():
            component = entity_components[Type]
        ```
        """
        pass

    def __str__(self) -> str:
        return f"<{type(self).__name__}>"

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"
