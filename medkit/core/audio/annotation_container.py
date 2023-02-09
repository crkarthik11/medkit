__all__ = ["AudioAnnotationContainer"]

from typing import List, Optional

from medkit.core.annotation_container import AnnotationContainer
from medkit.core.audio.annotation import Segment


class AudioAnnotationContainer(AnnotationContainer[Segment]):
    """
    Manage a list of audio annotations belonging to an audio document.

    This behaves more or less like a list: calling `len()` and iterating are
    supported. Additional filtering is available through the `get()` method.

    Also provides handling of raw segment.
    """

    def __init__(self, raw_segment: Segment):
        super().__init__()

        # auto-generated RAW_AUDIO segment
        # not stored with other annotations but injected in calls to get()
        # and get_by_id()
        self.raw_segment = raw_segment

    def add(self, ann: Segment):
        if ann.label == self.raw_segment.label:
            raise RuntimeError(
                f"Cannot add annotation with reserved label {self.raw_segment.label}"
            )

        super().add(ann)

    def get(
        self, *, label: Optional[str] = None, key: Optional[str] = None
    ) -> List[Segment]:
        # inject raw segment
        if label == self.raw_segment.label and key is None:
            return [self.raw_segment]
        return super().get(label=label, key=key)

    def get_by_id(self, uid) -> Segment:
        # inject raw segment
        if uid == self.raw_segment.uid:
            return self.raw_segment
        return super().get_by_id(uid)
