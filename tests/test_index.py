from friendly_parakeet.index import Document, DocumentIndex


def test_document_index_returns_results_in_relevance_order():
    docs = [
        Document(content="Section 25 plomberie et chauffage", metadata={"page_number": 1, "project": "A"}),
        Document(content="Section 23 ventilation", metadata={"page_number": 2, "project": "A"}),
        Document(content="Section 25 isolation et finitions", metadata={"page_number": 3, "project": "A"}),
    ]
    index = DocumentIndex(docs)

    results = index.search("plomberie section 25", top_k=2)
    assert len(results) == 2
    assert results[0].document.metadata["page_number"] == 1
    assert results[0].score >= results[1].score
