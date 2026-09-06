import pandas as pd

def results_to_dataframe(results):
    """Flatten a list of result dicts (from lookup_variants) into a pandas DataFrame,
    one row per interpretation — same 'long format' logic as the CSV export."""
    rows = []
    for r in results:
        if not r["found"] or not r["interpretations"]:
            continue  # skip variants with no usable interpretation data
        for interp in r["interpretations"]:
            rows.append({
                "rsid": r["rsid"],
                "gene": r["gene"],
                "allele_frequency": r["allele_frequency"],
                "condition": interp["condition"],
                "significance": interp["significance"],
                "review_status": interp["review_status"]
            })
    return pd.DataFrame(rows)


# ClinVar's own "review status star rating" system — a real, established scale
# (0 to 4 stars) representing how much evidence/review backs a classification.
# We map the text status to this numeric score so it can actually be compared/averaged.
REVIEW_STATUS_STARS = {
    "practice guideline": 4,
    "reviewed by expert panel": 3,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, conflicting interpretations": 1,
    "criteria provided, single submitter": 1,
    "no assertion criteria provided": 0,
    "no assertion provided": 0,
}

def add_confidence_score(df):
    """Add a numeric confidence column based on ClinVar's review status star system."""
    df = df.copy()
    df["confidence_stars"] = df["review_status"].map(REVIEW_STATUS_STARS).fillna(0)
    return df


def significance_distribution(df):
    """Count how many interpretations fall into each clinical significance category."""
    return df["significance"].value_counts()


def frequency_by_significance(df):
    """Average allele frequency per significance category — checks the known pattern
    that rarer variants tend to be classified pathogenic more often than common ones."""
    return df.groupby("significance")["allele_frequency"].mean().sort_values()