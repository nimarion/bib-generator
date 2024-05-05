from fastapi import FastAPI, Response, HTTPException
from typing import Optional
from os import walk
from fastapi.staticfiles import StaticFiles
from bib import generate_image

header_folder = "header"
footer_folder = "footer"
font_folder = "font"

app = FastAPI(title="DLV", docs_url="/swagger",
              openapi_url="/swagger-json", redoc_url=None)

app.mount("/" + header_folder, StaticFiles(directory="header"), name="header")
app.mount("/" + footer_folder, StaticFiles(directory="footer"), name="footer")


def headers():
    header = []
    for (_, _, filenames) in walk(header_folder):
        filenames = [f for f in filenames if f.endswith(
            '.png') or f.endswith('.jpg')]
        header.extend(filenames)
        break
    return header


def footers():
    footer = []
    for (_, _, filenames) in walk(footer_folder):
        filenames = [f for f in filenames if f.endswith(
            '.png') or f.endswith('.jpg')]
        footer.extend(filenames)
        break
    return footer


def fonts():
    fonts = []
    for (_, _, filenames) in walk(font_folder):
        filenames = [f for f in filenames if f.endswith(
            '.ttf')]
        fonts.extend(filenames)
        break
    return fonts


@app.get("/",  responses={
    200: {
        "content": {"image/png": {}}
    }
},  response_class=Response)
def generate_bib(
    text: str,
    header: str,
    footer: str,
    font: str,
    header_offset: Optional[int] = 60,
):
    print("hi")
    if header not in headers():
        raise HTTPException(status_code=404, detail="Header not found")
    if footer not in footers():
        raise HTTPException(status_code=404, detail="Footer not found")
    print(font)
    if font not in fonts():
        raise HTTPException(status_code=404, detail="Font not found")
    print("hi")
    image = generate_image(text, header_folder + "/" + header, footer_folder + "/" + footer,
                           font_folder + "/" + font)
    return Response(content=image, media_type="image/png", headers={"Content-Disposition": "filename=" + text + ".png"})


@app.get("/headers")
def get_headers():
    return headers()

@app.get("/footers")
def get_footers():
    return footers()

@app.get("/fonts")
def get_fonts():
    return fonts()
