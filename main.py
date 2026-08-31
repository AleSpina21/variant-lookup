from fastapi import FastAPI, HTTPException
from lookup import get_variant_info, summarize, lookup_variants
import requests

app = FastAPI()

# Single-variant lookup
@app.get("/variant/{rsid}")
def read_variant(rsid: str):
    try:
        data = get_variant_info(rsid)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Failed to fetch data from upstream API")

    summary = summarize(data)
    return {"rsid": rsid, **summary}


# Batch lookup — new endpoint, added without touching the one above
@app.get("/variants")
def read_variants(rsids: str):
    """Batch lookup. Pass a comma-separated list, e.g. /variants?rsids=rs429358,rs7412"""
    # rsids arrives as one string (query parameter), so split it into a list first
    rsid_list = rsids.split(",")

    # lookup_variants() already handles per-rsID errors internally,
    # so no extra try/except is needed here
    return lookup_variants(rsid_list)