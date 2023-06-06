"""Registry to keep track of all existing model and connection types in BRiM."""
from __future__ import annotations

from typing import TYPE_CHECKING

from brim.core.requirement import ConnectionRequirement, ModelRequirement
from brim.core.singleton import Singleton

if TYPE_CHECKING:
    from brim.core.model_base import ConnectionBase, ModelBase

__all__ = ["Registry"]


class Registry(Singleton):
    """Registry to keep track of all existing model and connection types in BRiM."""

    def __init__(self) -> None:
        self._models = set()
        self._connections = set()

    def register_model(self, model: type) -> None:
        """Register a new type in the registry."""
        self._models.add(model)

    def register_connection(self, conn: type) -> None:
        """Register a new type in the registry."""
        self._connections.add(conn)

    @property
    def models(self) -> frozenset[type]:
        """Return the registered models."""
        return frozenset(self._models)

    @property
    def connections(self) -> frozenset[type]:
        """Return the registered connections."""
        return frozenset(self._connections)

    def get_from_property(self, obj: ModelBase | ConnectionBase, prop: str,
                          drop_abstract: bool = True) -> list[type]:
        """Return all models or connections that could be used as property.

        Parameters
        ----------
        obj : ModelBase | ConnectionBase
            The object to get the property from.
        prop : str
            The name of the property.
        drop_abstract : bool, optional
            Whether to drop abstract classes, by default True.

        Returns
        -------
        list[type]
            All models or connections that could be used as property.
        """
        for req in tuple(obj.required_models) + tuple(obj.required_connections):
            if prop == req.attribute_name:
                return self.get_from_requirement(req, drop_abstract=drop_abstract)
        raise ValueError(f"Could not find property {prop} in {obj}.")

    def get_from_requirement(
            self, requirement: ConnectionRequirement | ModelRequirement,
            drop_abstract: bool = True) -> list[type]:
        """Return all models or connections that satisfy the given requirement.

        Parameters
        ----------
        requirement : ConnectionRequirement | ModelRequirement
            The requirement to satisfy.
        drop_abstract : bool, optional
            Whether to drop abstract classes, by default True.

        Returns
        -------
        list[type]
            All models or connections that satisfy the given requirement.
        """
        if isinstance(requirement, ModelRequirement):
            options = [
                model for model in self.models if requirement.is_satisfied_by(model)
            ]
        elif isinstance(requirement, ConnectionRequirement):
            options = [
                conn for conn in self.connections if requirement.is_satisfied_by(conn)
            ]
        else:
            raise TypeError(
                f"Expected requirement to be of type {ModelRequirement} or "
                f"{ConnectionRequirement}, but got {type(requirement)} instead."
            )
        if drop_abstract:
            options = [option for option in options if option.__name__[-4:] != "Base"]
        return options
