from lookup import summarize

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