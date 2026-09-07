import pandas as pd

def load_clinvar_data(filepath="variant_summary.txt.gz"):
    """Load ClinVar bulk data, keeping only GRCh38 rows to avoid double-counting
    (each variant appears once per genome assembly in this file)."""
    df = pd.read_csv(filepath, sep="\t", low_memory=False)
    df = df[df["Assembly"] == "GRCh38"].copy()
    return df

def explode_conditions(df):
    """Each row can list multiple conditions in PhenotypeList, separated by '|' or ';'.
    Split on both, so each condition gets its own row."""
    df = df.copy()
    # Split on either character using a regex pattern
    df["PhenotypeList"] = df["PhenotypeList"].fillna("").str.split(r"[|;]")
    df = df.explode("PhenotypeList")
    df["PhenotypeList"] = df["PhenotypeList"].str.strip()

    df = df[~df["PhenotypeList"].isin(["", "not provided", "not specified", "See cases"])]
    return df

def gene_condition_significance(df):
    """For each gene-condition pair, count how many variants are pathogenic
    (ClinSigSimple == 1) vs. total variants reported, and rank genes per condition
    by how many pathogenic variants they contribute."""
    grouped = df.groupby(["PhenotypeList", "GeneSymbol"]).agg(
        total_variants=("ClinSigSimple", "count"),
        pathogenic_variants=("ClinSigSimple", lambda x: (x == 1).sum())
    ).reset_index()

    grouped["pathogenic_fraction"] = grouped["pathogenic_variants"] / grouped["total_variants"]
    return grouped.sort_values(["PhenotypeList", "pathogenic_variants"], ascending=[True, False])

def top_genes_for_condition(ranked_df, condition_name, top_n=10):
    """Filter the ranked table down to one condition, case-insensitive partial match."""
    matches = ranked_df[ranked_df["PhenotypeList"].str.contains(condition_name, case=False, na=False)]
    return matches.head(top_n)