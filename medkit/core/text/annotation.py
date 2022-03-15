from __future__ import annotations

__all__ = ["TextBoundAnnotation", "Entity", "Attribute", "Relation"]

from typing import TYPE_CHECKING

from medkit.core.annotation import Annotation
from medkit.core.text import span as span_utils

if TYPE_CHECKING:
    from medkit.core.text.document import TextDocument


class TextBoundAnnotation(Annotation):
    def __init__(self, origin, label, spans, text, ann_id=None, metadata=None):
        """
        Initialize a medkit text-bound annotation

        Parameters
        ----------
        origin: Origin
            Description of how this annotation was generated
        label: str
            The label for this annotation (e.g., SENTENCE)
        spans: List[Span]
            The annotation span
        text: str
            The annotation text
        ann_id: str, Optional
            The id of the annotation (if existing)
        metadata: dict[str, Any], Optional
            The metadata of the annotation
        """
        super().__init__(ann_id=ann_id, origin=origin, label=label, metadata=metadata)
        self.spans = spans
        self.text = text

    def get_snippet(self, doc: TextDocument, max_extend_length: int) -> str:
        """Return a portion of the original text contaning the annotation

        Parameters
        ----------
        doc:
            The document to which the annotation is attached

        max_extend_length:
            Maximum number of characters to use around the annotation

        Returns
        -------
        str:
            A portion of the text around the annotation
        """
        spans_normalized = span_utils.normalize_spans(self.spans)
        start = min(s.start for s in spans_normalized)
        end = max(s.end for s in spans_normalized)
        start_extended = max(start - max_extend_length // 2, 0)
        remaining_max_extend_length = max_extend_length - (start - start_extended)
        end_extended = min(end + remaining_max_extend_length, len(doc.text))
        return doc.text[start_extended:end_extended]

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, spans={self.spans!r}, text={self.text!r}"


class Entity(TextBoundAnnotation):
    def __init__(self, origin, label, spans, text, entity_id=None, metadata=None):
        """
        Initialize a medkit text entity

        Parameters
        ----------
        origin: Origin
            Description of how this entity annotation was generated
        label: str
            The entity label
        spans: List[Span]
            The entity span
        text: str
            The entity text
        entity_id: str, Optional
            The id of the entity (if existing)
        metadata: dict[str, Any], Optional
            The metadata of the entity
        """
        super().__init__(origin, label, spans, text, entity_id, metadata)


class Attribute(Annotation):
    def __init__(
        self, origin, label, target_id, value=None, attr_id=None, metadata=None
    ):
        """
        Initialize a medkit attribute

        Parameters
        ----------
        origin: Origin
            Description of how this attribute annotation was generated
        label: str
            The attribute label
        target_id: str
            The id of the entity on which the attribute is applied
        value: str, Optional
            The value of the attribute
        attr_id: str, Optional
            The id of the attribute (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the attribute
        """
        super().__init__(ann_id=attr_id, origin=origin, label=label, metadata=metadata)
        self.target_id = target_id
        self.value = value

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, target_id={self.target_id!r}, value={self.value}"


class Relation(Annotation):
    def __init__(self, origin, label, source_id, target_id, rel_id=None, metadata=None):
        """
        Initialize the medkit relation

        Parameters
        ----------
        origin: Origin
            Description of how this relation annotation was generated
        label: str
            The relation label
        source_id: str
            The id of the entity from which the relation is defined
        target_id: str
            The id of the entity to which the relation is defined
        rel_id: str, Optional
            The id of the relation (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the relation
        """
        super().__init__(ann_id=rel_id, origin=origin, label=label, metadata=metadata)
        self.source_id = source_id
        self.target_id = target_id

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, source={self.source_id}, target_id={self.target_id}"
