import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import probe
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class InspectRequest(BaseModel):
    url: str


@app.api_route("/", methods=["POST"])
@app.api_route("/{path:path}", methods=["POST"])
def inspect(req: InspectRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    return probe.inspect(url)
