import requests
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s %(levelname)s %(message)s"
)

def get_variant_info(rsid):
    """Fetch variant info from MyVariant.info given an rsID (e.g. 'rs429358')."""
    logging.info("Fetching data for rsID: %s", rsid)
    url = f"https://myvariant.info/v1/query?q={rsid}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Request failed for rsID %s: %s", rsid, e)
        raise

    logging.info("Successfully fetched data for rsID: %s", rsid)
    return response.json()

def summarize(data):
    """Pull out the useful bits from the raw API response."""
    hits = data.get("hits", [])
    if not hits:
        logging.warning("No hits found in response.")
        return "No results found."

    hit = hits[0]
    clinvar = hit.get("clinvar", {})
    gene = clinvar.get("gene", {}).get("symbol", "Unknown")

    rcvs = clinvar.get("rcv", [])
    significances = {rcv.get("clinical_significance") for rcv in rcvs if rcv.get("clinical_significance")}

    logging.info("Parsed result — gene: %s, significances found: %d", gene, len(significances))
    return f"Gene: {gene}\nClinical significance found: {', '.join(significances) if significances else 'None reported'}"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lookup.py <rsID>")
        sys.exit(1)

    rsid = sys.argv[1]

    try:
        result = get_variant_info(rsid)
        print(summarize(result))
    except requests.exceptions.RequestException:
        print("Something went wrong fetching the data. Check app.log for details.")
        sys.exit(1)