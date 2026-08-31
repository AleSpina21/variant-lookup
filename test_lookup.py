from lookup import get_variant_info, summarize, lookup_variants, search_by_gene

def test_summarize_with_valid_data():
    fake_data = {
        "hits": [
            {
                "clinvar": {
                    "gene": {"symbol": "APOE"},
                    "rcv": [
                        {"clinical_significance": "Pathogenic", "conditions": {"name": "Alzheimer disease"}, "review_status": "criteria provided, single submitter"}
                    ]
                },
                "gnomad_exome": {"af": {"af": 0.138498}}
            }
        ]
    }
    result = summarize(fake_data)
    assert result["found"] is True
    assert result["gene"] == "APOE"
    assert result["interpretations"][0]["condition"] == "Alzheimer disease"
    assert result["allele_frequency"] == 0.138498

def test_summarize_with_no_hits():
    fake_data = {"hits": []}
    result = summarize(fake_data)
    assert result["found"] is False

def test_lookup_variants_multiple():
    from unittest.mock import patch, Mock

    # Fake response reused for every call inside lookup_variants during this test
    fake_response = Mock()
    fake_response.json.return_value = {
        "hits": [{"clinvar": {"gene": {"symbol": "APOE"}, "rcv": []}}]
    }
    fake_response.raise_for_status.return_value = None

    # Patch requests.get for the duration of this block, so no real network calls happen
    with patch("lookup.requests.get", return_value=fake_response):
        results = lookup_variants(["rs429358", "rs7412"])

    # Two rsIDs in -> two results out, each tagged with the correct rsid
    assert len(results) == 2
    assert results[0]["rsid"] == "rs429358"
    assert results[1]["rsid"] == "rs7412"


def test_search_by_gene():
    from unittest.mock import patch, Mock

    fake_response = Mock()
    fake_response.json.return_value = {
        "hits": [
            {"clinvar": {"rsid": "rs429358"}},
            {"clinvar": {"rsid": "rs7412"}},
            {"clinvar": {}}  # a hit with no rsid — should be skipped
        ]
    }
    fake_response.raise_for_status.return_value = None

    with patch("lookup.requests.get", return_value=fake_response):
        rsids = search_by_gene("APOE")

    assert rsids == ["rs429358", "rs7412"]

def test_summarize_with_single_rcv_as_dict():
    """Some variants return 'rcv' as a single dict instead of a list — must not crash."""
    fake_data = {
        "hits": [
            {
                "clinvar": {
                    "gene": {"symbol": "BRCA1"},
                    "rcv": {"clinical_significance": "Pathogenic", "conditions": {"name": "Breast cancer"}, "review_status": "criteria provided"}
                }
            }
        ]
    }
    result = summarize(fake_data)
    assert result["found"] is True
    assert result["interpretations"][0]["significance"] == "Pathogenic"