"""
This module aims to provide facilities for accessing data from e3c corpus.

**Version** : 2.0.0
**License**: The E3C corpus is released under Creative Commons NonCommercial license
(CC BY-NC).

**Github**: https://github.com/hltfbk/E3C-Corpus

**Reference**

B. magnini, B. Altuna, A. Lavelli, M. Speranza, and R. Zanoli. 2020.
The E3C Project: Collection and Annotation of a Multilingual Corpus of Clinical Cases.
In Proceedings of the Seventh Italian Conference on Computational Linguistics, Bologna,
Italy, December.
Associazione Italiana di Linguistica Computazionale.
"""

__all__ = [
    "load_document",
    "load_data_collection",
    "convert_data_collection_to_medkit",
    "load_annotated_document",
    "load_data_annotation",
    "convert_data_annotation_to_medkit",
]

import json
import logging
from xml.etree import ElementTree

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Optional, List, Union

from medkit.core.text import Entity, Segment, Span, TextDocument
from medkit.io.medkit_json import save_text_documents
from medkit.text.ner import UMLSNormAttribute


logger = logging.getLogger(__name__)


@dataclass
class E3CDocument:
    """
    Represents the data structure of a json document
    in data collection folder of the E3C corpus
    """

    authors: List[Dict]  # list of {'author': '<name>'}
    doi: str
    publication_date: str
    id: str
    url: str
    source: str
    source_url: str
    licence: str
    language: str
    type: str
    description: str
    text: str

    def extract_metadata(self) -> dict:
        """Returns the metadata dict for medkit text document"""
        dict_repr = self.__dict__.copy()
        dict_repr.pop("text")
        return dict_repr


def load_document(
    filepath: Union[str, Path],
    encoding: str = "utf-8",
    keep_id: bool = False,
) -> TextDocument:
    """
    Load a E3C corpus document (json document) as medkit text document.
    For example, one in data collection folder.

    Parameters
    ----------
    filepath
        The path to the json file of the E3C corpus
    encoding
        The encoding of the file. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept i medkit document
        metadata.

    Returns
    -------
    TextDocument
        The corresponding medkit text document
    """
    with open(filepath, encoding=encoding) as f:
        doc = E3CDocument(**json.load(f))
    return TextDocument(
        text=doc.text, uid=doc.id if keep_id else None, metadata=doc.extract_metadata()
    )


def load_data_collection(
    dir_path: Union[Path, str],
    encoding: str = "utf-8",
    keep_id: bool = False,
) -> Iterator[TextDocument]:
    """
    Load the E3C corpus data collection as medkit text documents

    Parameters
    ----------
    dir_path
        The path to the E3C corpus data collection directory containing the json files
        (e.g., /tmp/E3C-Corpus-2.0.0/data_collection/French/layer1)
    encoding
        The encoding of the files. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept i medkit document
        metadata.

    Returns
    -------
    Iterator[TextDocument]
        An iterator on corresponding medkit text documents
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError("%s is not a directory or does not exist", dir_path)

    for filename in dir_path.glob("*.json"):
        filepath = dir_path / filename
        yield load_document(filepath, keep_id=keep_id, encoding=encoding)


def convert_data_collection_to_medkit(
    dir_path: Union[Path, str],
    output_file: Union[str, Path],
    encoding: Optional[str] = "utf-8",
    keep_id: bool = False,
):
    """
    Convert E3C corpus data collection to medkit jsonl file

    Parameters
    ----------
    dir_path
        The path to the E3C corpus data collection directory containing the json files
        (e.g., /tmp/E3C-Corpus-2.0.0/data_collection/French/layer1)
    output_file
        The medkit jsonl output file which will contain medkit text documents
    encoding
        The encoding of the files. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept in medkit document
        metadata.
    """
    docs = load_data_collection(dir_path=dir_path, encoding=encoding, keep_id=keep_id)
    save_text_documents(docs=docs, output_file=output_file, encoding=encoding)


def load_annotated_document(
    filepath: Union[str, Path],
    encoding: str = "utf-8",
    keep_id: bool = False,
    keep_sentences=False,
) -> TextDocument:
    """
    Load a E3C corpus annotated document (xml document) as medkit text document.
    For example, one in data annotation folder.

    For the time being, only supports 'CLINENTITY' annotations.
    'SENTENCE' annotations may be also loaded.

    Parameters
    ----------
    filepath
        The path to the xml file of the E3C corpus
    encoding
        The encoding of the file. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept in medkit document
        metadata.
    keep_sentences
        Whether to load sentences into medkit documents.

    Returns
    -------
    TextDocument
        The corresponding medkit text document
    """
    xml_parser = ElementTree.XMLParser(encoding=encoding)
    root = ElementTree.parse(filepath, parser=xml_parser).getroot()
    # get xml namespaces
    ns = dict(
        [node for _, node in ElementTree.iterparse(filepath, events=["start-ns"])]
    )
    metadata = root.find("custom:METADATA", ns).attrib
    text = root.find("cas:Sofa", ns).attrib.get("sofaString", "")
    doc = E3CDocument(
        authors=[
            {"author": author.strip()} for author in metadata["docAuthor"].split(";")
        ],
        doi=metadata["docDOI"],
        publication_date=metadata["docTime"],
        id=metadata["docName"],
        url=metadata["docUrl"],
        source=metadata["docSource"],
        source_url=metadata["docSourceUrl"],
        licence=metadata["docLicense"],
        language=metadata["docLanguage"],
        type=metadata["pubType"],
        description=metadata["note"],
        text=text,
    )

    # create medkit text document
    medkit_doc = TextDocument(
        text=doc.text, uid=doc.id if keep_id else None, metadata=doc.extract_metadata()
    )

    # parse sentences if wanted by user
    if keep_sentences:
        for elem in root.findall("type4:Sentence", ns):
            sentence = elem.attrib
            span = Span(int(sentence["begin"]), int(sentence["end"]))
            medkit_sentence = Segment(
                label="sentence", spans=[span], text=doc.text[span.start : span.end]
            )

            # attach medkit sentence to medkit document
            medkit_doc.anns.add(medkit_sentence)

    # parse clinical entities
    for elem in root.findall("custom:CLINENTITY", ns):
        clin_entity = elem.attrib
        span = Span(int(clin_entity["begin"]), int(clin_entity["end"]))
        medkit_entity = Entity(
            label="disorder", spans=[span], text=doc.text[span.start : span.end]
        )
        # add normalization attribute to medkit entity
        cui = clin_entity.get("entityID")
        if cui is not None:
            metadata = {
                "id": clin_entity.get("id"),
                "entityIDEN": clin_entity.get("entityIDEN"),
                "discontinuous": clin_entity.get("discontinuous"),
                "xtra": clin_entity.get("xtra"),
            }
            attr = UMLSNormAttribute(cui=cui, umls_version="", metadata=metadata)
            medkit_entity.attrs.add(attr)

        else:
            logger.debug(f"no cui for {medkit_entity}")

        # attach medkit entity to medkit document
        medkit_doc.anns.add(medkit_entity)

    return medkit_doc


def load_data_annotation(
    dir_path: Union[Path, str],
    encoding: str = "utf-8",
    keep_id: bool = False,
    keep_sentences: bool = False,
) -> Iterator[TextDocument]:
    """
    Load the E3C corpus data annotation as medkit text documents

    Parameters
    ----------
    dir_path
        The path to the E3C corpus data annotation directory containing the xml files
        (e.g., /tmp/E3C-Corpus-2.0.0/data_annotation/French/layer1)
    encoding
        The encoding of the files. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept in medkit document
        metadata.
    keep_sentences
        Whether to load sentences into medkit documents.

    Returns
    -------
    Iterator[TextDocument]
        An iterator on corresponding medkit text documents
    """

    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError("%s is not a directory or does not exist", dir_path)

    for filename in dir_path.glob("*.xml"):
        filepath = dir_path / filename
        yield load_annotated_document(
            filepath, keep_id=keep_id, encoding=encoding, keep_sentences=keep_sentences
        )


def convert_data_annotation_to_medkit(
    dir_path: Union[Path, str],
    output_file: Union[str, Path],
    encoding: Optional[str] = "utf-8",
    keep_id: bool = False,
    keep_sentences: bool = False,
):
    """
    Convert E3C corpus data annotation to medkit jsonl file

    Parameters
    ----------
    dir_path
        The path to the E3C corpus data collection directory containing the json files
        (e.g., /tmp/E3C-Corpus-2.0.0/data_collection/French/layer1)
    output_file
        The medkit jsonl output file which will contain medkit text documents
    encoding
        The encoding of the files. Default: 'utf-8'
    keep_id
        Whether to set medkit text document uid to the document id.
        Whatever this boolean value, the document id is always kept in medkit document
        metadata.
    keep_sentences
        Whether to load sentences into medkit documents.
    """
    docs = load_data_annotation(
        dir_path=dir_path,
        encoding=encoding,
        keep_id=keep_id,
        keep_sentences=keep_sentences,
    )
    save_text_documents(docs=docs, output_file=output_file, encoding=encoding)
