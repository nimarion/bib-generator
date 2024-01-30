from fastapi import FastAPI, Response
from typing import Optional
from os import walk
from fastapi.staticfiles import StaticFiles
from bib import generate_image

app = FastAPI(title="DLV", docs_url="/swagger",
              openapi_url="/swagger-json", redoc_url=None)

app.mount("/header", StaticFiles(directory="header"), name="header")
app.mount("/footer", StaticFiles(directory="footer"), name="footer")


def headers():
    header = []
    for (dirpath, dirnames, filenames) in walk("header"):
        filenames = [f for f in filenames if f.endswith(
            '.png') or f.endswith('.jpg')]
        header.extend(filenames)
        break
    return header


def footers():
    footer = []
    for (dirpath, dirnames, filenames) in walk("footer"):
        filenames = [f for f in filenames if f.endswith(
            '.png') or f.endswith('.jpg')]
        footer.extend(filenames)
        break
    return footer


@app.get("/",  responses={
    200: {
        "content": {"image/png": {}}
    }
},  response_class=Response)
def generate_bib(
    text: str,
    header: str,
    footer: str,
    header_offset: Optional[int] = 60,
):
    # check if header and footer are valid
    if header not in headers():
        return {"error": "Header not found"}
    if footer not in footers():
        return {"error": "Footer not found"}
    image = generate_image(text, header, footer,
                           "agency_fb.ttf", header_offset)
    return Response(content=image, media_type="image/png", headers={"Content-Disposition": "filename=" + text + ".png"})


@app.get("/headers")
def get_headers():
    return headers()


@app.get("/footers")
def get_footers():
    return footers()
