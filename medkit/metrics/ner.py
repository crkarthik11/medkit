import itertools
from typing import Dict, List

from seqeval.metrics import accuracy_score, classification_report
from seqeval.scheme import BILOU, IOB2

from medkit.training.utils import BatchData

SPECIAL_TAG_ID_HF: int = -100


class SeqEvalMetricsComputer:
    """Implementation of :class:`~medkit.training.MetricsComputer` that use `seqeval`
    to compute sequence metrics in NER operations.

    Could be used with
    :class:`~medkit.training.Trainer>` to control the training of NER trainable operations.
    """

    def __init__(
        self,
        id_to_label: Dict[int, str],
        use_bilou_scheme: bool,
        return_entity_metrics: bool,
    ):
        self.id_to_label = id_to_label
        self.scheme = BILOU if use_bilou_scheme else IOB2
        self.return_entity_metrics = return_entity_metrics

    def prepare_batch(
        self, model_output: BatchData, input_batch: BatchData
    ) -> Dict[str, List[List[str]]]:
        predictions_ids = (
            model_output["logits"].argmax(dim=-1).detach().to("cpu").numpy()
        )
        references_ids = input_batch["labels"].detach().to("cpu").numpy()

        # ignore special tokens
        mask_special_tokens = references_ids != SPECIAL_TAG_ID_HF

        batch_true_tags = [
            [self.id_to_label[tag] for tag in ref[mask_special_tokens[i]]]
            for i, ref in enumerate(references_ids)
        ]
        batch_pred_tags = [
            [self.id_to_label[tag] for tag in pred[mask_special_tokens[i]]]
            for i, pred in enumerate(predictions_ids)
        ]
        return {"y_true": batch_true_tags, "y_pred": batch_pred_tags}

    def compute(self, all_data: Dict[str, List[any]]) -> Dict[str, float]:
        # extract and format data from all_data
        y_true_all = all_data.get("y_true", [])
        y_pred_all = all_data.get("y_pred", [])

        if not len(y_true_all) or not len(y_pred_all):
            raise ValueError("'all_data' has no required data to compute the metric")

        size_last_dim = len(y_pred_all[0][0][0])
        if size_last_dim > 1:
            # dim of all_data is (nb_batches,n,m), metric requires (nb_batches*n,nb_batches*m)
            y_true_all = list(itertools.chain(*y_true_all))
            y_pred_all = list(itertools.chain(*y_pred_all))

        report = classification_report(
            y_true=y_true_all,
            y_pred=y_pred_all,
            scheme=self.scheme,
            output_dict=True,
            zero_division=0,
        )
        # add overall_metrics
        scores = {f"overall_{key}": value for key, value in report["micro avg"].items()}
        scores["overall_acc"] = accuracy_score(y_pred=y_pred_all, y_true=y_true_all)

        if self.return_entity_metrics:
            ent_keys = [key for key in report.keys() if not key.endswith("avg")]
            for ent_key in ent_keys:
                for metric_key, metric_value in report[ent_key].items():
                    scores[f"{ent_key}_{metric_key}"] = metric_value

        return scores
