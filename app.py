import streamlit as st
import io
from lookup import lookup_variants, search_by_gene, results_to_csv, extract_rsids_from_vcf
from analysis import results_to_dataframe, add_confidence_score, significance_distribution, frequency_by_significance
from gene_condition_analysis import load_clinvar_data, explode_conditions, gene_condition_significance, top_genes_for_condition
from reclassification_analysis import add_review_age, flag_due_for_review, gene_reclassification_summary


@st.cache_data
def get_ranked_gene_conditions():
    """Load and process the full ClinVar file once, then cache the result."""
    df = load_clinvar_data("variant_summary.txt.gz")
    exploded = explode_conditions(df)
    ranked = gene_condition_significance(exploded)
    return ranked

@st.cache_data
def get_reclassification_summary():
    from reclassification_analysis import add_review_age, flag_due_for_review, gene_reclassification_summary
    df = load_clinvar_data("variant_summary.txt.gz")
    df = add_review_age(df)
    df = flag_due_for_review(df)
    return gene_reclassification_summary(df)


st.title("Variant Lookup Tool")

search_mode = st.radio("Search by:", ["rsID", "Gene symbol", "VCF file upload", "Condition analysis", "Reclassification risk"])


if search_mode == "rsID":
    rsid_input = st.text_area("Enter one or more rsIDs (one per line)", placeholder="rs429358\nrs7412")
    rsids_to_lookup = [line for line in rsid_input.splitlines() if line.strip()]

elif search_mode == "Gene symbol":
    gene_input = st.text_input("Enter a gene symbol", placeholder="APOE")
    rsids_to_lookup = None

elif search_mode == "VCF file upload":
    uploaded_file = st.file_uploader("Upload a VCF file", type=["vcf"])
    rsids_to_lookup = None

# --- The "Look up" button and its results only apply to the three modes above ---
if search_mode in ["rsID", "Gene symbol", "VCF file upload"]:
    if st.button("Look up"):
        if search_mode == "Gene symbol":
            if not gene_input:
                st.warning("Please enter a gene symbol.")
                st.stop()
            with st.spinner(f"Finding variants for {gene_input}..."):
                try:
                    rsids_to_lookup = search_by_gene(gene_input)
                except Exception:
                    st.error("Something went wrong searching for this gene.")
                    st.stop()
            if not rsids_to_lookup:
                st.warning(f"No variants found for gene {gene_input}.")
                st.stop()
            st.info(f"Found {len(rsids_to_lookup)} variant(s) for {gene_input}.")

        if search_mode == "VCF file upload":
            if uploaded_file is None:
                st.warning("Please upload a VCF file.")
                st.stop()
            text_wrapper = io.TextIOWrapper(uploaded_file, encoding="utf-8")
            rsids_to_lookup = extract_rsids_from_vcf(text_wrapper)
            if not rsids_to_lookup:
                st.warning("No rsIDs found in this VCF file.")
                st.stop()
            st.info(f"Found {len(rsids_to_lookup)} rsID(s) in the uploaded file.")

        if not rsids_to_lookup:
            st.warning("Please enter at least one rsID.")
        else:
            with st.spinner("Fetching data..."):
                results = lookup_variants(rsids_to_lookup)

            st.session_state["results"] = results

            for r in results:
                st.subheader(r["rsid"])
                if r["found"]:
                    st.write(f"**Gene:** {r['gene']}")
                    if r["allele_frequency"] is not None:
                        st.write(f"**Population allele frequency:** {r['allele_frequency']}")
                    st.table(r["interpretations"])
                else:
                    st.warning(r.get("error", "No results found."))

    # Analysis + CSV download — only relevant once there are results to show
    if "results" in st.session_state:
        csv_data = results_to_csv(st.session_state["results"])
        st.download_button(
            label="Download results as CSV",
            data=csv_data,
            file_name="variant_lookup_results.csv",
            mime="text/csv",
            key="download_csv_results"
        )

        st.header("Analysis")
        df = results_to_dataframe(st.session_state["results"])

        if df.empty:
            st.info("Not enough interpretation data across these variants for analysis.")
        else:
            df = add_confidence_score(df)

            st.subheader("Clinical significance distribution")
            st.bar_chart(significance_distribution(df))

            st.subheader("Average allele frequency by significance")
            st.bar_chart(frequency_by_significance(df))

            st.subheader("Confidence (review status) per interpretation")
            st.dataframe(df[["rsid", "gene", "significance", "confidence_stars"]])


# --- Condition analysis mode: entirely separate, doesn't use the button/results flow above ---
elif search_mode == "Condition analysis":
    st.header("Gene-Condition Significance Analysis")
    st.caption("Based on the full ClinVar database — which genes contribute the most pathogenic variants for a given condition.")

    condition_query = st.text_input("Enter a condition or disease name", placeholder="Alzheimer")
    min_variants = st.slider("Minimum total variants tested (filters out low-sample noise)", 1, 50, 5)

    if condition_query:
        with st.spinner("Loading ClinVar data (first run may take a minute)..."):
            ranked = get_ranked_gene_conditions()

        matches = top_genes_for_condition(ranked, condition_query, top_n=1000)
        matches = matches[matches["total_variants"] >= min_variants]

        if matches.empty:
            st.warning(f"No results found for '{condition_query}' with at least {min_variants} variants tested.")
        else:
            st.write(f"Found {len(matches)} gene(s) associated with conditions matching '{condition_query}'")

            st.subheader("Top genes by pathogenic variant count")
            top_by_count = matches.sort_values("pathogenic_variants", ascending=False).head(15)
            st.bar_chart(top_by_count.set_index("GeneSymbol")["pathogenic_variants"])

            st.subheader("Top genes by pathogenic fraction")
            top_by_fraction = matches.sort_values("pathogenic_fraction", ascending=False).head(15)
            st.bar_chart(top_by_fraction.set_index("GeneSymbol")["pathogenic_fraction"])

            st.subheader("Full results")
            st.dataframe(matches[["PhenotypeList", "GeneSymbol", "total_variants", "pathogenic_variants", "pathogenic_fraction"]])

elif search_mode == "Reclassification risk":
    st.header("Genes Most Likely Due for Reclassification Review")
    st.caption("Flags variants that are either currently conflicting, or evaluated long ago with weak review support.")

    min_variants = st.slider("Minimum total variants for a gene to be included", 5, 100, 20)

    with st.spinner("Loading ClinVar data (first run may take a minute)..."):
        summary = get_reclassification_summary()

    filtered = summary[summary["total_variants"] >= min_variants]

    st.subheader("Top genes by number of variants due for review")
    top = filtered.sort_values("due_for_review", ascending=False).head(15)
    st.bar_chart(top.set_index("GeneSymbol")["due_for_review"])

    st.subheader("Top genes by fraction due for review")
    top_frac = filtered.sort_values("review_fraction", ascending=False).head(15)
    st.bar_chart(top_frac.set_index("GeneSymbol")["review_fraction"])

    st.subheader("Full results")
    st.dataframe(filtered)



