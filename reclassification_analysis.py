import pandas as pd

CONFLICTING_STATUS = "criteria provided, conflicting classifications"

def add_review_age(df):
    """Parse LastEvaluated into a real date, and compute how many years old
    each variant's classification is, relative to the most recent date in the dataset."""
    df = df.copy()
    df["LastEvaluated"] = pd.to_datetime(df["LastEvaluated"], format="%b %d, %Y", errors="coerce")

    most_recent = df["LastEvaluated"].max()
    df["years_since_evaluated"] = (most_recent - df["LastEvaluated"]).dt.days / 365.25
    return df

def flag_due_for_review(df, age_threshold_years=5):
    """Flag variants likely worth re-examining: either currently flagged as
    conflicting, or evaluated a long time ago with weak review support."""
    df = df.copy()
    df["is_conflicting"] = df["ReviewStatus"] == CONFLICTING_STATUS
    df["is_stale"] = (df["years_since_evaluated"] > age_threshold_years) & (
        df["ReviewStatus"].isin(["criteria provided, single submitter", "no assertion criteria provided"])
    )
    df["due_for_review"] = df["is_conflicting"] | df["is_stale"]
    return df

def gene_reclassification_summary(df):
    """Per gene, what fraction of variants are flagged as due for review —
    highlights genes where classifications may be less stable/reliable."""
    summary = df.groupby("GeneSymbol").agg(
        total_variants=("VariationID", "count"),
        due_for_review=("due_for_review", "sum")
    ).reset_index()
    summary["review_fraction"] = summary["due_for_review"] / summary["total_variants"]
    return summary.sort_values("due_for_review", ascending=False)