"""Module containing the requirement class."""
from __future__ import annotations

from collections.abc import Iterable


class Requirement:
    """Simple class containing the requirement properties."""

    def __init__(self, attribute_name: str,
                 submodel_types: type | tuple[type, ...],
                 description: str | None = None,
                 hard_requirement: bool = False,
                 full_name: str | None = None,
                 type_name: str | None = None) -> None:
        """Initialize a new instance of the requirement.

        Parameters
        ----------
        attribute_name : str
            Name of the attribute that is used to store the submodel in the parent.
        submodel_types : type | tuple[type, ...]
            Supported types of the submodel.
        description : str, optional
            Description of the submodel, by default None.
        hard_requirement : bool, optional
            Whether the submodel is a hard requirement, by default False.
        full_name : str, optional
            Full name of the submodel, by default capitalized version of the attribute
            name, where the underscores are replaced by spaces.
        type_name : str, optional
            Names of the supported types of the submodel. The names of the type classes
            are used by default.

        """
        attribute_name = str(attribute_name)
        if not attribute_name.isidentifier():
            raise ValueError(f"'{attribute_name}' is not a valid attribute name, "
                             f"because it cannot be used as a variable name.")
        self._attribute_name = attribute_name
        if not isinstance(submodel_types, Iterable):
            submodel_types = (submodel_types,)
        self._types = tuple(submodel_types)
        if description is None:
            description = self.types[0].__doc__.split("\n", 1)[0]
        self._description = str(description)
        self._hard = bool(hard_requirement)
        if full_name is None:
            full_name = self.attribute_name.replace("_", " ").capitalize()
        self._full_name = str(full_name)
        if type_name is None:
            type_name = " or ".join(tp.__name__ for tp in self.types)
        self._type_name = str(type_name)

    @property
    def attribute_name(self) -> str:
        """Name of the attribute that is used to store the submodel in the parent."""
        return self._attribute_name

    @property
    def types(self) -> tuple[type, ...]:
        """Supported types of the submodel."""
        return self._types

    @property
    def description(self) -> str:
        """Description of the submodel."""
        return self._description

    @property
    def hard(self) -> bool:
        """Whether the submodel is a hard requirement."""
        return self._hard

    @property
    def full_name(self) -> str:
        """Full name of the submodel."""
        return self._full_name

    @property
    def type_name(self) -> str:
        """Names of the supported types of the submodel."""
        return self._type_name

    def __str__(self):
        return self.attribute_name
