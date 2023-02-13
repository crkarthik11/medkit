from __future__ import annotations

__all__ = ["Attribute"]

import dataclasses
from typing import Any, Dict, Optional

from medkit.core.id import generate_id


@dataclasses.dataclass
class Attribute:
    """
    Medkit attribute, to be added to an annotation

    Attributes
    ----------
    label:
        The attribute label
    value:
        The value of the attribute
    metadata:
        The metadata of the attribute
    uid:
        The identifier of the attribute
    """

    label: str
    value: Optional[Any] = None
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)
    uid: str = dataclasses.field(default_factory=generate_id)

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            uid=self.uid,
            label=self.label,
            value=self.value,
            metadata=self.metadata,
        )

    def copy(self) -> Attribute:
        """
        Create a new attribute that is a copy of the current instance, but
        with a new identifier

        This is used when we want to duplicate an existing attribute onto a
        different annotation.
        """
        return dataclasses.replace(self, uid=generate_id())

    @classmethod
    def from_dict(cls, attribute_dict: Dict[str, Any]) -> Attribute:
        """
        Creates an Attribute from a dict

        Parameters
        ----------
        attribute_dict: dict
            A dictionary from a serialized Attribute as generated by to_dict()
        """
        return cls(
            uid=attribute_dict["uid"],
            label=attribute_dict["label"],
            value=attribute_dict["value"],
            metadata=attribute_dict["metadata"],
        )
