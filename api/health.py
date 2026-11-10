import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.api_route("/", methods=["GET"])
@app.api_route("/{path:path}", methods=["GET"])
def health():
    return JSONResponse({"status": "ok", "service": "downer"})
