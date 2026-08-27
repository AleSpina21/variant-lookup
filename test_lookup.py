from lookup import summarize

def test_summarize_with_valid_data():
    fake_data = {
        "hits": [
            {
                "clinvar": {
                    "gene": {"symbol": "APOE"},
                    "rcv": [
                        {"clinical_significance": "Pathogenic"},
                        {"clinical_significance": "Uncertain significance"}
                    ]
                }
            }
        ]
    }
    result = summarize(fake_data)
    assert "APOE" in result
    assert "Pathogenic" in result

def test_summarize_with_no_hits():
    fake_data = {"hits": []}
    result = summarize(fake_data)
    assert result == "No results found."