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

    # MyVariant.info sometimes returns a single dict instead of a list when
    # there's only one entry. Normalize to always be a list before iterating.
    if isinstance(rcvs, dict):
        rcvs = [rcvs]

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


def lookup_variants(rsids):
    """Look up multiple rsIDs and return a list of result dicts, each tagged with its rsid."""
    results = []

    for rsid in rsids:
        # Remove stray whitespace (relevant once users start pasting lists of rsIDs)
        rsid = rsid.strip()

        # Skip empty entries (e.g. blank lines from pasted input)
        if not rsid:
            continue

        try:
            # Fetch and summarize this one rsID, same as the single-lookup flow
            data = get_variant_info(rsid)
            summary = summarize(data)
        except requests.exceptions.RequestException as e:
            # If this specific rsID fails (network issue, bad request, etc.),
            # log it and build a fallback summary — this failure should NOT
            # stop the rest of the batch from being processed
            logging.error("Failed to look up rsID %s: %s", rsid, e)
            summary = {
                "found": False,
                "gene": None,
                "interpretations": [],
                "allele_frequency": None,
                "error": str(e)
            }

        # Tag each result with its own rsid, so results can be matched back
        # to their input once they're all together in one list
        results.append({"rsid": rsid, **summary})

    return results


def search_by_gene(gene_symbol, max_results=10):
    """Search for variant rsIDs associated with a given gene symbol (e.g. 'APOE')."""
    logging.info("Searching for variants in gene: %s", gene_symbol)

    # Query MyVariant.info for ClinVar entries matching this gene symbol.
    # 'fields' limits the response to just what we need (faster, smaller payload).
    # 'size' caps how many results come back, since a gene can have hundreds of variants.
    url = (
        f"https://myvariant.info/v1/query?"
        f"q=clinvar.gene.symbol:{gene_symbol}"
        f"&fields=clinvar.rsid"
        f"&size={max_results}"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error("Gene search failed for %s: %s", gene_symbol, e)
        raise

    data = response.json()
    hits = data.get("hits", [])

    # Extract rsIDs from the results, skipping any hit that doesn't have one
    rsids = []
    for hit in hits:
        rsid = hit.get("clinvar", {}).get("rsid")
        if rsid:
            rsids.append(rsid)

    logging.info("Found %d rsIDs for gene %s", len(rsids), gene_symbol)
    return rsids


if __name__ == "__main__":
    # Ensure this code only runs when the script is executed directly (not imported)

    # Require at least one rsID; now supports multiple (unlike before, where exactly
    # one was required)
    if len(sys.argv) < 2:
        print("Usage: python lookup.py <rsID> [<rsID2> ...]")
        sys.exit(1)  # Exit with error code to indicate incorrect usage

    # Take all arguments after the script name — could be one rsID or several
    rsids = sys.argv[1:]

    # lookup_variants() handles fetching + summarizing for each rsID internally,
    # and catches per-rsID failures so one bad ID doesn't crash the whole batch
    results = lookup_variants(rsids)

    # Print a separate block of results for each rsID that was looked up
    for r in results:
        print(f"\n--- {r['rsid']} ---")

        if r["found"]:
            print(f"Gene: {r['gene']}")

            # Print allele frequency only if it exists
            if r["allele_frequency"] is not None:
                print(f"Population allele frequency: {r['allele_frequency']}")

            print("Interpretations:")
            # Print each clinical interpretation with significance, condition, and review status
            for interp in r["interpretations"]:
                print(f"  - {interp['significance']} (condition: {interp['condition']}, review: {interp['review_status']})")

        elif "error" in r:
            # This rsID specifically failed (e.g. network error during its lookup)
            print(f"Error: {r['error']}")

        else:
            # No hits were found for this rsID (valid request, just nothing in the databases)
            print("No results found.")