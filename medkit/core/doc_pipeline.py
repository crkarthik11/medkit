__all__ = ["DocPipeline"]

from typing import Dict, List, Optional, Tuple, cast

from medkit.core.annotation import Annotation
from medkit.core.document import Document
from medkit.core.operation import ProcessingOperation, OperationDescription
from medkit.core.pipeline import Pipeline, PipelineStep, DescribableOperation
from medkit.core.prov_builder import ProvBuilder


class DocPipeline(ProcessingOperation):
    """Wrapper around the `Pipeline` class that applies a list of a document or a`collection
    of documents

    Existing annotations, that are not generated by an operation in the pipeline
    but rather that should be retrieved from documents, can be handled by associating
    an annotation label to an input key. Pipeline steps using this input key will then
    receive as input all the existing document annotations having the associated label..
    """

    def __init__(
        self,
        steps: List[PipelineStep],
        labels_by_input_key: Dict[str, List[str]],
        output_keys: List[str],
        id: Optional[str] = None,
    ):
        """Initialize the pipeline

        Params
        ------
        steps:
            List of pipeline steps.

            Steps will be executed in the order in which they were added,
            so make sure to add first the steps generating data used by other steps.

        labels_by_input_key:
            Mapping of input key to document annotation labels.

            This is a way to feed into the pipeline annotations
            that are not the result of a pipeline step, but that
            are pre-attached to the document on which the pipeline
            is running.

            For all pipeline step using `key` as an input key,
            the annotations of the document having the label `label'
            will be used as input.

            It is possible to associate several labels to one key,
            as well as to associate a label to several keys

        output_keys:
            List of keys corresponding to the output annotations that should be
            added to documents
        """

        self.steps: List[PipelineStep] = steps
        self.labels_by_input_key: Dict[str, List[str]] = labels_by_input_key
        self.output_keys: List[str] = output_keys

        input_keys = list(labels_by_input_key.keys())
        pipeline_steps = [
            PipelineStep(s.operation, s.input_keys, s.output_keys) for s in steps
        ]
        self._pipeline: Pipeline = Pipeline(
            id=id,
            steps=pipeline_steps,
            input_keys=input_keys,
            output_keys=output_keys,
        )

    @property
    def description(self) -> OperationDescription:
        steps_config = [
            dict(
                operation=s.operation.description
                if isinstance(s.operation, DescribableOperation)
                else None,
                input_keys=s.input_keys,
                output_keys=s.output_keys,
            )
            for s in self.steps
        ]
        config = dict(
            steps=steps_config,
            labels_by_input_key=self.labels_by_input_key,
            output_keys=self.output_keys,
        )
        return OperationDescription(
            id=self._pipeline.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._pipeline.set_prov_builder(prov_builder)

    def process(self, docs: List[Document]):
        """Run the pipeline on a list of documents, adding
        the output annotations to each document

        Params
        ------
        docs:
            The documents on which to run the pipeline.
            Labels to input keys association will be used to retrieve existing
            annotations from each document, and all output annotations will also
            be added to each corresponding document.
        """
        for doc in docs:
            self._process_doc(doc)

    def _process_doc(self, doc: Document):
        all_input_anns = {}
        for input_key, labels in self.labels_by_input_key.items():
            for label in labels:
                if input_key not in all_input_anns:
                    all_input_anns[input_key] = doc.get_annotations_by_label(label)
                else:
                    all_input_anns[input_key] += doc.get_annotations_by_label(label)

        all_output_anns = self._pipeline.process(*all_input_anns.values())

        # wrap output in tuple if necessary
        # (operations performing in-place modifications
        # have no output and return None,
        # operations with single output may return a
        # single list instead of a tuple of lists)
        if all_output_anns is None:
            all_output_anns = tuple()
        elif not isinstance(all_output_anns, tuple):
            all_output_anns = (all_output_anns,)

        # operations must return annotations
        all_output_anns = cast(Tuple[List[Annotation], ...], all_output_anns)

        # add output anns to doc
        for output_anns in all_output_anns:
            for output_ann in output_anns:
                doc.add_annotation(output_ann)
