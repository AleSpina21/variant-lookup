import requests
import sys
import logging


# Configure logging: write INFO and above to app.log with timestamp, level, and message
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s %(levelname)s %(message)s"
)


def get_variant_info(rsid):
    """
    Fetch variant info from MyVariant.info given an rsID (e.g. 'rs429358').

    Returns the raw JSON response as a Python dict/list.
    Raises a requests.exceptions.RequestException if the HTTP request fails.
    """
    # Log that we're starting to fetch data for this rsID
    logging.info("Fetching data for rsID: %s", rsid)

    # Build the MyVariant.info API URL with the rsID as the query parameter
    url = f"https://myvariant.info/v1/query?q={rsid}"

    try:
        # Send an HTTP GET request to the API
        response = requests.get(url)

        # Raise an exception if the response status code indicates an error (4xx/5xx)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        # If any request-related error occurs, log it and re-raise so the caller knows
        logging.error("Request failed for rsID %s: %s", rsid, e)
        raise

    # Log successful retrieval of data
    logging.info("Successfully fetched data for rsID: %s", rsid)

    # Parse the JSON response into Python objects and return it
    return response.json()


def summarize(data):
    """
    Extract key fields from the raw MyVariant.info API response.

    Returns a dict with:
      - found: bool
      - gene: str or None
      - interpretations: list of dicts with condition/significance/review_status
      - allele_frequency: float or None
    """
    # Get the list of result "hits" from the response; default to empty list if missing
    hits = data.get("hits", [])

    # If there are no hits, log a warning and return a "not found" summary
    if not hits:
        logging.warning("No hits found in response.")
        return {
            "found": False,
            "gene": None,
            "interpretations": [],
            "allele_frequency": None
        }

    # Work with the first hit in the results
    hit = hits[0]

    # Extract the ClinVar section from the hit (or an empty dict if missing)
    clinvar = hit.get("clinvar", {})

    # Get the gene symbol from ClinVar (e.g. "APOE"), or "Unknown" if not present
    gene = clinvar.get("gene", {}).get("symbol", "Unknown")

    # Get the list of ClinVar records (RCVs) for this variant
    rcvs = clinvar.get("rcv", [])

    # Build a list of simplified interpretation records
    interpretations = []
    for rcv in rcvs:
        # Get the clinical significance (e.g. "Pathogenic", "Benign")
        significance = rcv.get("clinical_significance")

        # Skip entries without a clinical significance
        if not significance:
            continue

        # Append a simplified dict for this interpretation
        interpretations.append({
            # Condition name, or "Not specified" if missing
            "condition": rcv.get("conditions", {}).get("name", "Not specified"),
            # Clinical significance string
            "significance": significance,
            # Review status (e.g. "reviewed by expert panel"), or "Unknown"
            "review_status": rcv.get("review_status", "Unknown")
        })

    # Extract population allele frequency from gnomAD exome data, if available
    # Structure: hits[0].gnomad_exome.af.af
    allele_frequency = data.get("hits", [{}])[0].get("gnomad_exome", {}).get("af", {}).get("af")

    # Log a summary of what was parsed: gene symbol and number of interpretations
    logging.info("Parsed result — gene: %s, interpretations found: %d", gene, len(interpretations))

    # Return the structured summary dict
    return {
        "found": True,
        "gene": gene,
        "interpretations": interpretations,
        "allele_frequency": allele_frequency
    }


if __name__ == "__main__":
    # Ensure this code only runs when the script is executed directly (not imported)

    # Check that exactly one command-line argument is provided (the rsID)
    if len(sys.argv) != 2:
        print("Usage: python lookup.py <rsID>")
        sys.exit(1)  # Exit with error code to indicate incorrect usage

    # Take the rsID from the command line
    rsid = sys.argv[1]

    try:
        # Fetch raw variant data from the API
        result = get_variant_info(rsid)

        # Summarize the raw data into a simpler structure
        summary = summarize(result)

        # If a variant was found, print the summary in a human-readable format
        if summary["found"]:
            print(f"Gene: {summary['gene']}")

            # Print allele frequency only if it exists
            if summary["allele_frequency"] is not None:
                print(f"Population allele frequency: {summary['allele_frequency']}")

            print("Interpretations:")
            # Print each clinical interpretation with significance, condition, and review status
            for interp in summary["interpretations"]:
                print(f"  - {interp['significance']} (condition: {interp['condition']}, review: {interp['review_status']})")

        else:
            # No hits were found for this rsID
            print("No results found.")

    except requests.exceptions.RequestException:
        # If any request error occurred (network issue, HTTP error, etc.), inform the user
        print("Something went wrong fetching the data. Check app.log for details.")
        sys.exit(1)  # Exit with error code to indicate failure