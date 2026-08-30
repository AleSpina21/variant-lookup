import streamlit as st
from lookup import get_variant_info, summarize
import requests

st.title("Variant Lookup Tool")

rsid = st.text_input("Enter an rsID (e.g. rs429358)")

if st.button("Look up"):
    if not rsid:
        st.warning("Please enter an rsID first.")
    else:
        with st.spinner("Fetching data..."):
            try:
                data = get_variant_info(rsid)
                summary = summarize(data)
                if summary["found"]:
                    st.write(f"**Gene:** {summary['gene']}")
                    if summary["allele_frequency"] is not None:
                        st.write(f"**Population allele frequency:** {summary['allele_frequency']}")
                    st.write("**Interpretations:**")
                    st.table(summary["interpretations"])
                else:
                    st.warning("No results found.")
            except requests.exceptions.RequestException:
                st.error("Something went wrong fetching the data. Check app.log for details.")