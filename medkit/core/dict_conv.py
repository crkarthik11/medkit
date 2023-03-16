from __future__ import annotations

__all__ = [
    "DictConvertible",
    "SubclassMapping",
    "get_class_name",
    "add_class_name_to_data_dict",
    "get_class_name_from_data_dict",
]

import warnings

from typing import Any, Dict, Optional, Type
from typing_extensions import Protocol, Self, runtime_checkable


_CLASS_NAME_KEY: str = "_class_name"


def get_class_name(class_: Type) -> str:
    return class_.__module__ + "." + class_.__qualname__


def add_class_name_to_data_dict(instance: object, data_dict: Dict[str, Any]):
    """
    Add a class name to a data dict returned by a `to_dict()` method, so we
    later know upon which class to call `from_dict()` when re-instantiating the
    corresponding object.

    Parameters
    ----------
    instance:
        The instance of class to which `data_dict` corresponds
    data_dict:
        The data dict on which to add the class name
    """
    if _CLASS_NAME_KEY in data_dict:
        raise ValueError(
            f"Found pre-existing entry for key {_CLASS_NAME_KEY} in data dict"
        )
    data_dict[_CLASS_NAME_KEY] = get_class_name(type(instance))


def get_class_name_from_data_dict(data_dict: Dict[str, Any]):
    """
    Get the class name written in the data_dict by the `to_dict` method.

    Parameters
    ----------
    data_dict
        The data dict returned by `to_dict` of the class to extract

    Returns
    -------
    class_name
        The name of the class which has generated the data_dict

    """
    class_name = data_dict.get(_CLASS_NAME_KEY, None)
    if class_name is None:
        raise ValueError(
            f"Data dict does not contain expected '{_CLASS_NAME_KEY}' key. Make"
            " sure it was created by a to_dict() method and that this method"
            " called the 'add_class_name_to_data_dict()' helper function"
        )
    return class_name


@runtime_checkable
class DictConvertible(Protocol):
    """
    Base protocol that must be implemented for all classes supporting conversion
    to a data dict and re-instantiation from a data dict.
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert current instance into a data dict that can later be used to rebuild
        the exact same instance

        Returns
        -------
        Dict[str, Any]:
            A data dict containing all the information needed to re-instantiate the object
        """

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> Self:
        """
        Re-instantiate an object from a datadict obtained via `to_dict()`

        Parameters
        ----------
            data_dict:
                Data dict returned by `to_dict()`
        Returns
        -------
        Self:
            An instance of the class `to_dict()` was called on.
        """


class SubclassMapping:
    """
    Base class for managing subclasses
    """

    _subclasses: Dict[str, Type[Self]] = {}

    def __init_subclass__(cls):
        # make sure we have a distinct list of subclasses for each class relying on SubclassMapping
        cls._subclasses = {}

    @classmethod
    def register_subclass(cls, subclass: Type[Self]):
        subclass_name = get_class_name(subclass)
        if subclass_name in cls._subclasses:
            other_subclass = cls._subclasses[subclass_name]
            raise KeyError(
                f"Trying to register child class {subclass} of"
                f" {get_class_name(cls)} with name {subclass_name}, but other child"
                f" class {other_subclass} is already registered with identical name"
            )
        cls._subclasses[subclass_name] = subclass

    @classmethod
    def get_subclass(cls, name: str) -> Optional[Type[Self]]:
        return cls._subclasses.get(name)

    @classmethod
    def get_subclass_for_data_dict(
        cls,
        data_dict: Dict[str, Any],
    ) -> Optional[Type[Self]]:
        """
        Return the subclass that corresponds to the class name found in a data dict

        Parameters
        ----------
        data_dict:
            Data dict returned by the `to_dict()` method of a subclass

        Returns
        -------
        subclass
            Subclass that generated `data_dict`
        """
        class_name = get_class_name_from_data_dict(data_dict)
        subclass = cls.get_subclass(class_name)
        if subclass is None:
            warnings.warn(
                f"{class_name} does not exist. Fallback to base class"
                f" {get_class_name(cls)}."
            )
            return None
        return subclass
