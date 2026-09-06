import pandas as pd
from analysis import results_to_dataframe, add_confidence_score, significance_distribution, frequency_by_significance
from lookup import get_variant_info, summarize, lookup_variants, search_by_gene, results_to_csv

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

def test_results_to_csv():
    results = [
        {
            "rsid": "rs429358",
            "found": True,
            "gene": "APOE",
            "allele_frequency": 0.138,
            "interpretations": [
                {"condition": "Alzheimer disease", "significance": "Pathogenic", "review_status": "criteria provided"}
            ]
        },
        {
            "rsid": "rs000000",
            "found": False,
            "gene": None,
            "allele_frequency": None,
            "interpretations": []
        }
    ]
    csv_text = results_to_csv(results)
    assert "rs429358" in csv_text
    assert "Pathogenic" in csv_text
    assert "rs000000" in csv_text

def sample_results():
    return [
        {
            "rsid": "rs1", "found": True, "gene": "APOE", "allele_frequency": 0.15,
            "interpretations": [{"condition": "Alzheimer disease", "significance": "Pathogenic", "review_status": "criteria provided, single submitter"}]
        },
        {
            "rsid": "rs2", "found": True, "gene": "APOE", "allele_frequency": 0.40,
            "interpretations": [{"condition": "not specified", "significance": "Benign", "review_status": "reviewed by expert panel"}]
        }
    ]

def test_results_to_dataframe():
    df = results_to_dataframe(sample_results())
    assert len(df) == 2
    assert "gene" in df.columns

def test_add_confidence_score():
    df = results_to_dataframe(sample_results())
    df = add_confidence_score(df)
    assert df.loc[df["significance"] == "Benign", "confidence_stars"].iloc[0] == 3

def test_frequency_by_significance():
    df = results_to_dataframe(sample_results())
    result = frequency_by_significance(df)
    # Pathogenic variant is rarer than the Benign one in this sample data
    assert result["Pathogenic"] < result["Benign"]