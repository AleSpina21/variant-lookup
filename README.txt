To reactivate the virtual environment, cd into the folder of the project and then: venv\Scripts\Activate.ps1


Overview
--------

This script queries the MyVariant.info API for a genetic variant given its rsID
(e.g. rs429358), extracts key clinical and population-genetics information,
logs the process, and prints a human-readable summary to the console.

It is intended as a simple command-line lookup tool for:

- Gene symbol associated with the variant (from ClinVar)
- Clinical interpretations (pathogenicity, condition, review status)
- Population allele frequency (from gnomAD exome data, if available)


How it works (data model)
-------------------------

API response and "hits"
~~~~~~~~~~~~~~~~~~~~~~~

The MyVariant.info /v1/query endpoint returns JSON of the form:

{
  "took": 10,
  "total": 1,
  "hits": [
    { /* variant record */ }
  ]
}

- "hits" is a list of variant records that match the query.
- Each element of "hits" is called a "hit".
- The script uses the first hit: hit = hits[0].


Variant record structure
~~~~~~~~~~~~~~~~~~~~~~~~

Each hit is a nested JSON object with:

- Basic variant info: rsid, chrom, pos, ref, alt, etc.
- Source-specific annotation blocks, such as:
  - clinvar: clinical annotations from ClinVar
  - gnomad_exome, gnomad_genome: population frequencies from gnomAD
  - dbsnp, cadd, and others (depending on the variant)

The script primarily uses:

  clinvar = hit.get("clinvar", {})
  allele_frequency = hit.get("gnomad_exome", {}).get("af", {}).get("af")


ClinVar section
~~~~~~~~~~~~~~~

Inside a hit, the clinvar block contains clinical interpretations, typically
structured like:

"clinvar": {
  "gene": {
    "symbol": "APOE",
    "name": "apolipoprotein E"
  },
  "rcv": [
    {
      "clinical_significance": "Pathogenic",
      "conditions": {
        "name": "Alzheimer disease"
      },
      "review_status": "reviewed by expert panel"
    }
  ]
}

Key fields used by the script:

- clinvar.gene.symbol → gene symbol (e.g. "APOE")
- clinvar.rcv → list of ClinVar records, each with:
  - clinical_significance (e.g. "Pathogenic", "Benign")
  - conditions.name (phenotype/condition name)
  - review_status (e.g. "reviewed by expert panel")

The script iterates over rcv entries and builds a simplified list of
interpretations.


Allele frequency
~~~~~~~~~~~~~~~~

Population allele frequency is taken from gnomAD exome data, if present:

"gnomad_exome": {
  "af": {
    "af": 0.1234
  }
}

The script accesses this as:

  allele_frequency = hit.get("gnomad_exome", {}).get("af", {}).get("af")

If any part is missing, allele_frequency is None.