from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import pathlib
import io
import base64
import img2pdf
from PIL import Image
from bib import generate_image, PRESETS

def optimize_image_to_bytes(image: Image.Image, quality: int = 85) -> bytes:
    """
    Optimizes PIL Image into compressed JPEG byte stream for PDF assembly.
    Converts RGBA/CMYK to RGB on white background and applies JPEG compression,
    drastically reducing server memory footprint and output PDF file size.
    """
    if image.mode == 'RGBA':
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        r, g, b, a = image.split()
        rgb_image.paste(image, mask=a)
    elif image.mode != 'RGB':
        rgb_image = image.convert('RGB')
    else:
        rgb_image = image

    img_io = io.BytesIO()
    rgb_image.save(img_io, format='JPEG', quality=quality, optimize=True)
    return img_io.getvalue()

def compress_pdf_bytes(pdf_bytes: bytes) -> bytes:
    """
    Compresses PDF streams, strips redundant object metadata, and linearizes
    the PDF document using pikepdf (QPDF) on the server if available.
    """
    try:
        import pikepdf
        pdf = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
        out_io = io.BytesIO()
        pdf.save(out_io, linearize=True, compress_streams=True)
        return out_io.getvalue()
    except Exception as e:
        print(f"[Server] pikepdf stream compression fallback: {e}")
        return pdf_bytes

class BibServerHandler(BaseHTTPRequestHandler):
    # Class attributes to store global configs safely
    args = None
    font_path = None
    back_bytes = None

    def log_message(self, format, *args_msg):
        print(f"[Server] {self.address_string()} - {format % args_msg}")

    def send_error_json(self, message: str, status_code: int):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = {"error": message, "status": "failed"}
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def discover_assets(self) -> dict:
        """Discovers available font files and header/footer logos in project workspace."""
        fonts = sorted([str(p) for p in pathlib.Path(".").glob("**/*.ttf")] + [str(p) for p in pathlib.Path(".").glob("**/*.otf")])
        headers = sorted([str(p) for p in pathlib.Path("header").glob("*.png")] + [str(p) for p in pathlib.Path("header").glob("*.jpg")] + [str(p) for p in pathlib.Path("example").glob("*globus*.png")])
        footers = sorted([str(p) for p in pathlib.Path("footer").glob("*.png")] + [str(p) for p in pathlib.Path("footer").glob("*.jpg")] + [str(p) for p in pathlib.Path("example").glob("*footer*.png")])
        
        return {
            "fonts": list(set(fonts)),
            "headers": list(set(headers)),
            "footers": list(set(footers)),
            "presets": list(PRESETS.keys())
        }

    def process_runner(self, runner: dict, idx: int, render_opts: dict) -> tuple[Image.Image | None, str | None]:
        """
        Validates runner parameters, formats name text, and returns generated PIL Image
        or error message if validation fails.
        """
        firstname = runner.get("firstname", "")
        lastname = runner.get("lastname", "")
        if not lastname:
            return None, f"Runner at index {idx} is missing required field 'lastname'"

        text = lastname.replace('ß', 'ẞ').upper()
        text = text.replace('ẞ'.upper(), 'ß')
        text = text.replace('-', '-\n').replace(' ', '\n')

        row_header = runner.get("header") or (self.args.header if self.args else None)
        row_footer = runner.get("footer") or (self.args.footer if self.args else None)
        row_font = runner.get("font") or (str(self.font_path) if self.font_path else None)

        discovered = self.discover_assets()
        if (not row_font or not pathlib.Path(row_font).is_file()) and discovered.get("fonts"):
            row_font = discovered["fonts"][0]
        if (not row_header or not pathlib.Path(row_header).is_file()) and discovered.get("headers"):
            row_header = discovered["headers"][0]
        if (not row_footer or not pathlib.Path(row_footer).is_file()) and discovered.get("footers"):
            row_footer = discovered["footers"][0]

        if not row_header or not pathlib.Path(row_header).is_file():
            return None, f"Header file '{row_header}' for runner at index {idx} not found."
        if not row_footer or not pathlib.Path(row_footer).is_file():
            return None, f"Footer file '{row_footer}' for runner at index {idx} not found."
        if not row_font or not pathlib.Path(row_font).is_file():
            return None, f"Font file '{row_font}' for runner at index {idx} not found."

        image = generate_image(
            txt=text,
            header_file=str(row_header),
            footer_file=str(row_footer),
            font_file=str(row_font),
            margin=render_opts['margin'],
            text_color=render_opts['text_color'],
            stroke_color=render_opts['stroke_color'],
            stroke_width=render_opts['stroke_width'],
            width=render_opts['w'],
            height=render_opts['h']
        )
        return image, None

    def extract_render_opts(self, parsed_url) -> dict:
        """Parses common query string options for canvas dimensions and styling."""
        query_params = urllib.parse.parse_qs(parsed_url.query)
        margin = int(query_params.get("margin", [self.args.margin if self.args else 175])[0])
        text_color = query_params.get("text_color", [self.args.text_color if self.args else "black"])[0]
        stroke_color = query_params.get("stroke_color", [self.args.stroke_color if self.args else "black"])[0]
        stroke_width = int(query_params.get("stroke_width", [self.args.stroke_width if self.args else 1])[0])
        jpeg_quality = int(query_params.get("quality", [85])[0])

        size_preset = query_params.get("size", [self.args.size if self.args else "A5"])[0]
        custom_w = query_params.get("width", [None])[0]
        custom_h = query_params.get("height", [None])[0]

        if custom_w and custom_h:
            w, h = int(custom_w), int(custom_h)
        else:
            w, h = PRESETS.get(size_preset, PRESETS["A5"])

        return {
            'margin': margin,
            'text_color': text_color,
            'stroke_color': stroke_color,
            'stroke_width': stroke_width,
            'jpeg_quality': jpeg_quality,
            'w': w,
            'h': h
        }

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Endpoint 1: GET /health
        if parsed_url.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "bib-generator"}).encode("utf-8"))
            return

        # Endpoint 2: GET /assets
        if parsed_url.path == "/assets":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(self.discover_assets()).encode("utf-8"))
            return

        # Endpoint 3: GET /generate (Single bib PNG preview feed)
        if parsed_url.path == "/generate":
            try:
                query_params = urllib.parse.parse_qs(parsed_url.query)
                txt = query_params.get("text", ["SAMPLE"])[0]
                opts = self.extract_render_opts(parsed_url)
                
                header_file = query_params.get("header", [self.args.header if self.args else None])[0]
                footer_file = query_params.get("footer", [self.args.footer if self.args else None])[0]
                row_font = query_params.get("font", [str(self.font_path) if self.font_path else None])[0]

                discovered = self.discover_assets()
                if (not row_font or not pathlib.Path(row_font).is_file()) and discovered.get("fonts"):
                    row_font = discovered["fonts"][0]
                if (not header_file or not pathlib.Path(header_file).is_file()) and discovered.get("headers"):
                    header_file = discovered["headers"][0]
                if (not footer_file or not pathlib.Path(footer_file).is_file()) and discovered.get("footers"):
                    footer_file = discovered["footers"][0]

                if not header_file or not footer_file or not row_font:
                    self.send_error_json("Missing required asset parameter(s)", 400)
                    return

                runner_data = {
                    "firstname": "",
                    "lastname": txt,
                    "header": header_file,
                    "footer": footer_file,
                    "font": row_font
                }

                image, err = self.process_runner(runner_data, 0, opts)
                if err or image is None:
                    self.send_error_json(err or "Failed to render image", 400)
                    return

                img_io = io.BytesIO()
                image.save(img_io, format='PNG', optimize=True)
                img_bytes = img_io.getvalue()

                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(img_bytes)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(img_bytes)

            except Exception as e:
                self.send_error_json(f"Internal generator error: {e}", 500)
        else:
            self.send_error_json("Endpoint not found. Use /assets or /generate?text=NAME", 404)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Endpoint 4: POST /generate-batch-stream (Real-time SSE progress streaming & compressed PDF)
        if parsed_url.path == "/generate-batch-stream":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                runners = json.loads(post_data.decode("utf-8"))
                
                if not isinstance(runners, list):
                    self.send_error_json("JSON body must be a list of runner objects", 400)
                    return
                    
                opts = self.extract_render_opts(parsed_url)

                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                total = len(runners)
                all_pages_bytes = []

                for idx, runner in enumerate(runners):
                    image, err = self.process_runner(runner, idx, opts)
                    if err or image is None:
                        err_msg = json.dumps({"event": "error", "error": err or "Render error"})
                        self.wfile.write(f"data: {err_msg}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        return

                    img_bytes = optimize_image_to_bytes(image, quality=opts['jpeg_quality'])
                    all_pages_bytes.append(img_bytes)

                    if self.back_bytes:
                        all_pages_bytes.append(self.back_bytes)

                    # Stream progress update to client
                    progress_msg = json.dumps({
                        "event": "progress",
                        "current": idx + 1,
                        "total": total,
                        "percent": int(((idx + 1) / total) * 100),
                        "firstname": runner.get("firstname", ""),
                        "lastname": runner.get("lastname", "")
                    })
                    self.wfile.write(f"data: {progress_msg}\n\n".encode("utf-8"))
                    self.wfile.flush()

                if not all_pages_bytes:
                    err_msg = json.dumps({"event": "error", "error": "No bib pages generated"})
                    self.wfile.write(f"data: {err_msg}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    return

                pdf_w_pt = img2pdf.mm_to_pt(int(opts['w'] * (210 / 3508))) if opts['w'] else img2pdf.mm_to_pt(210)
                pdf_h_pt = img2pdf.mm_to_pt(int(opts['h'] * (148 / 2480))) if opts['h'] else img2pdf.mm_to_pt(148)
                letter = (pdf_w_pt, pdf_h_pt)
                layout = img2pdf.get_layout_fun(letter)

                raw_pdf_bytes = img2pdf.convert(all_pages_bytes, layout_fun=layout)
                compressed_pdf_bytes = compress_pdf_bytes(raw_pdf_bytes)
                pdf_b64 = base64.b64encode(compressed_pdf_bytes).decode('utf-8')

                complete_msg = json.dumps({
                    "event": "complete",
                    "total": total,
                    "percent": 100,
                    "pdf_base64": pdf_b64
                })
                self.wfile.write(f"data: {complete_msg}\n\n".encode("utf-8"))
                self.wfile.flush()

            except Exception as e:
                err_msg = json.dumps({"event": "error", "error": f"Streaming batch error: {e}"})
                try:
                    self.wfile.write(f"data: {err_msg}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    pass

        # Endpoint 5: POST /generate-batch (Direct binary PDF download)
        elif parsed_url.path == "/generate-batch":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                runners = json.loads(post_data.decode("utf-8"))
                
                if not isinstance(runners, list):
                    self.send_error_json("JSON body must be a list of runner objects", 400)
                    return
                    
                opts = self.extract_render_opts(parsed_url)
                all_pages_bytes = []
                
                for idx, runner in enumerate(runners):
                    image, err = self.process_runner(runner, idx, opts)
                    if err or image is None:
                        self.send_error_json(err or "Render error", 400)
                        return

                    img_bytes = optimize_image_to_bytes(image, quality=opts['jpeg_quality'])
                    all_pages_bytes.append(img_bytes)
                    
                    if self.back_bytes:
                        all_pages_bytes.append(self.back_bytes)
                        
                if not all_pages_bytes:
                    self.send_error_json("No bib pages generated", 400)
                    return
                    
                pdf_w_pt = img2pdf.mm_to_pt(int(opts['w'] * (210 / 3508))) if opts['w'] else img2pdf.mm_to_pt(210)
                pdf_h_pt = img2pdf.mm_to_pt(int(opts['h'] * (148 / 2480))) if opts['h'] else img2pdf.mm_to_pt(148)
                letter = (pdf_w_pt, pdf_h_pt)
                layout = img2pdf.get_layout_fun(letter)
                
                raw_pdf_bytes = img2pdf.convert(all_pages_bytes, layout_fun=layout)
                compressed_pdf_bytes = compress_pdf_bytes(raw_pdf_bytes)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(compressed_pdf_bytes)))
                self.send_header("Content-Disposition", "attachment; filename=\"combined_bibs.pdf\"")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(compressed_pdf_bytes)
                
            except Exception as e:
                self.send_error_json(f"Batch generation failed: {e}", 500)
        else:
            self.send_error_json("Not Found. Use POST /generate-batch or POST /generate-batch-stream.", 404)


def run_server(args, font_path, back_bytes) -> None:
    BibServerHandler.args = args
    BibServerHandler.font_path = font_path
    BibServerHandler.back_bytes = back_bytes

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, BibServerHandler)
    print(f"\n[Server] Starting real-time Bib Kiosk Server on http://{args.host}:{args.port} ...")
    print(f"[Server] GET  Dropdown Assets: http://{args.host}:{args.port}/assets")
    print(f"[Server] GET  Single Bib     : http://{args.host}:{args.port}/generate?text=NAME")
    print(f"[Server] POST Batch PDF      : http://{args.host}:{args.port}/generate-batch")
    print(f"[Server] POST Batch SSE Stream: http://{args.host}:{args.port}/generate-batch-stream")
    print("[Server] Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Stopping HTTP server gracefully...")
        httpd.server_close()
        import sys
        sys.exit(0)
