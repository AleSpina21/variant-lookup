import streamlit as st
from lookup import lookup_variants, search_by_gene

st.title("Variant Lookup Tool")

# Let the user choose how they want to provide input
search_mode = st.radio("Search by:", ["rsID", "Gene symbol"])

if search_mode == "rsID":
    rsid_input = st.text_area("Enter one or more rsIDs (one per line)", placeholder="rs429358\nrs7412")
    rsids_to_lookup = [line for line in rsid_input.splitlines() if line.strip()]
else:
    gene_input = st.text_input("Enter a gene symbol", placeholder="APOE")
    rsids_to_lookup = None  # will be resolved below, after the button is clicked

if st.button("Look up"):
    # If searching by gene, resolve the gene symbol into a list of rsIDs first
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

        for r in results:
            st.subheader(r["rsid"])
            if r["found"]:
                st.write(f"**Gene:** {r['gene']}")
                if r["allele_frequency"] is not None:
                    st.write(f"**Population allele frequency:** {r['allele_frequency']}")
                st.table(r["interpretations"])
            else:
                st.warning(r.get("error", "No results found."))