from medkit.io import medkit_json
from tests.unit.io.medkit_json._audio_common import (
    DOC_JSON_FILE,
    DOCS_JSONL_FILE,
    ANNS_JSONL_FILE,
    build_doc,
    build_docs,
    build_anns,
)


def test_load_document():
    doc = medkit_json.load_audio_document(DOC_JSON_FILE)

    expected_doc = build_doc()
    assert doc == expected_doc


def test_load_documents():
    docs = medkit_json.load_audio_documents(DOCS_JSONL_FILE)

    expected_docs = build_docs()
    assert list(docs) == expected_docs


def test_load_anns():
    anns = medkit_json.load_audio_anns(ANNS_JSONL_FILE)

    expected_anns = build_anns()
    assert list(anns) == expected_anns
