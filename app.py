import streamlit as st
from lookup import lookup_variants, search_by_gene, results_to_csv
from analysis import results_to_dataframe, add_confidence_score, significance_distribution, frequency_by_significance


st.title("Variant Lookup Tool")

search_mode = st.radio("Search by:", ["rsID", "Gene symbol"])

if search_mode == "rsID":
    rsid_input = st.text_area("Enter one or more rsIDs (one per line)", placeholder="rs429358\nrs7412")
    rsids_to_lookup = [line for line in rsid_input.splitlines() if line.strip()]
else:
    gene_input = st.text_input("Enter a gene symbol", placeholder="APOE")
    rsids_to_lookup = None

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

    if not rsids_to_lookup:
        st.warning("Please enter at least one rsID.")
    else:
        with st.spinner("Fetching data..."):
            results = lookup_variants(rsids_to_lookup)

        # Store results in session state so the download button (below) survives
        # Streamlit's re-run behavior without re-fetching everything
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

# Show the download button whenever there are results in session state,
# even after the "Look up" button click has passed (since Streamlit re-runs
# the whole script on every interaction, including clicking Download)
if "results" in st.session_state:
    csv_data = results_to_csv(st.session_state["results"])
    st.download_button(
        label="Download results as CSV",
        data=csv_data,
        file_name="variant_lookup_results.csv",
        mime="text/csv"
    )

    # New analysis section — only makes sense once there's a batch of results to compare
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