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
    """Pull out the useful bits from the raw API response as a structured dict."""
    hits = data.get("hits", [])
    if not hits:
        logging.warning("No hits found in response.")
        return {"found": False, "gene": None, "interpretations": [], "allele_frequency": None}

    hit = hits[0]
    clinvar = hit.get("clinvar", {})
    gene = clinvar.get("gene", {}).get("symbol", "Unknown")

    rcvs = clinvar.get("rcv", [])
    interpretations = []
    for rcv in rcvs:
        significance = rcv.get("clinical_significance")
        if not significance:
            continue
        interpretations.append({
            "condition": rcv.get("conditions", {}).get("name", "Not specified"),
            "significance": significance,
            "review_status": rcv.get("review_status", "Unknown")
        })

    # Population allele frequency, from gnomAD exome data if available
    allele_frequency = data.get("hits", [{}])[0].get("gnomad_exome", {}).get("af", {}).get("af")

    logging.info("Parsed result — gene: %s, interpretations found: %d", gene, len(interpretations))
    return {
        "found": True,
        "gene": gene,
        "interpretations": interpretations,
        "allele_frequency": allele_frequency
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python lookup.py <rsID>")
        sys.exit(1)

    rsid = sys.argv[1]

    try:
        result = get_variant_info(rsid)
        summary = summarize(result)
        if summary["found"]:
            print(f"Gene: {summary['gene']}")
            if summary["allele_frequency"] is not None:
                print(f"Population allele frequency: {summary['allele_frequency']}")
            print("Interpretations:")
            for interp in summary["interpretations"]:
                print(f"  - {interp['significance']} (condition: {interp['condition']}, review: {interp['review_status']})")
        else:
            print("No results found.")
    except requests.exceptions.RequestException:
        print("Something went wrong fetching the data. Check app.log for details.")
        sys.exit(1)