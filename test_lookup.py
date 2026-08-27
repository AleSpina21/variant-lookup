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



from unittest.mock import patch, Mock
from lookup import get_variant_info

def test_get_variant_info_success():
    fake_response = Mock()
    fake_response.json.return_value = {"hits": [{"clinvar": {"gene": {"symbol": "APOE"}}}]}
    fake_response.raise_for_status.return_value = None

    with patch("lookup.requests.get", return_value=fake_response):
        result = get_variant_info("rs429358")

    assert result["hits"][0]["clinvar"]["gene"]["symbol"] == "APOE"