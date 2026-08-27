from fastapi import FastAPI, HTTPException
from lookup import get_variant_info, summarize
import requests

app = FastAPI()

@app.get("/variant/{rsid}")
def read_variant(rsid: str):
    try:
        data = get_variant_info(rsid)
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Failed to fetch data from upstream API")

    result = summarize(data)
    return {"rsid": rsid, "result": result}