from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import pathlib
import io
import img2pdf
from PIL import Image
from bib import generate_image, PRESETS

class BibServerHandler(BaseHTTPRequestHandler):
    # Class attributes to store global configs safely
    args = None
    font_path = None
    back_bytes = None

    def log_message(self, format, *args_msg):
        # Clean custom formatted console logging
        print(f"[Server] {self.address_string()} - {format % args_msg}")

    def send_error_json(self, message: str, status_code: int):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        response = {"error": message, "status": "failed"}
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def discover_assets(self):
        # Dynamic project workspace discovery
        fonts = sorted([str(p) for p in pathlib.Path(".").glob("**/*.ttf")] + [str(p) for p in pathlib.Path(".").glob("**/*.otf")])
        headers = sorted([str(p) for p in pathlib.Path("header").glob("*.png")] + [str(p) for p in pathlib.Path("header").glob("*.jpg")] + [str(p) for p in pathlib.Path("example").glob("*globus*.png")])
        footers = sorted([str(p) for p in pathlib.Path("footer").glob("*.png")] + [str(p) for p in pathlib.Path("footer").glob("*.jpg")] + [str(p) for p in pathlib.Path("example").glob("*footer*.png")])
        
        return {
            "fonts": list(set(fonts)),
            "headers": list(set(headers)),
            "footers": list(set(footers)),
            "presets": list(PRESETS.keys())
        }

    def do_OPTIONS(self):
        # Dynamic browser SPA pre-flight CORS permissions
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Endpoint 1: Health Probes
        if parsed_url.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode("utf-8"))
            return

        # Endpoint 2: Discover Assets
        if parsed_url.path == "/assets":
            try:
                assets = self.discover_assets()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(assets).encode("utf-8"))
            except Exception as e:
                self.send_error_json(f"Failed to discover assets: {e}", 500)
            return

        # Endpoint 3: Primary Real-Time Single Generation
        if parsed_url.path in ("/generate", "/"):
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            try:
                text_list = query_params.get("text", [])
                if not text_list:
                    self.send_error_json("Missing required query parameter: 'text'", 400)
                    return
                txt = text_list[0]

                # Dynamic assets with global command-line fallbacks
                header_file = query_params.get("header", [None])[0] or (self.args.header if self.args.header else None)
                footer_file = query_params.get("footer", [None])[0] or (self.args.footer if self.args.footer else None)
                row_font = query_params.get("font", [None])[0] or (str(self.font_path) if self.font_path else None)
                
                # Style options with fallbacks
                margin = int(query_params.get("margin", [self.args.margin])[0])
                text_color = query_params.get("text_color", [self.args.text_color])[0]
                stroke_color = query_params.get("stroke_color", [self.args.stroke_color])[0]
                stroke_width = int(query_params.get("stroke_width", [self.args.stroke_width])[0])
                
                # Size options with fallbacks
                size_preset = query_params.get("size", [self.args.size])[0]
                custom_w = query_params.get("width", [None])[0]
                custom_h = query_params.get("height", [None])[0]

                if custom_w and custom_h:
                    w, h = int(custom_w), int(custom_h)
                else:
                    w, h = PRESETS.get(size_preset, PRESETS["A5"])

                if not header_file:
                    self.send_error_json("Header image path is required (pass 'header' query param or --header global argument)", 400)
                    return
                if not footer_file:
                    self.send_error_json("Footer image path is required (pass 'footer' query param or --footer global argument)", 400)
                    return
                if not row_font:
                    self.send_error_json("Font file path is required (pass 'font' query param or specify global fallback font on server startup)", 400)
                    return

                header_p = pathlib.Path(header_file)
                footer_p = pathlib.Path(footer_file)
                font_p = pathlib.Path(row_font)

                if not header_p.is_file():
                    self.send_error_json(f"Header image file '{header_file}' not found", 404)
                    return
                if not footer_p.is_file():
                    self.send_error_json(f"Footer image file '{footer_file}' not found", 404)
                    return
                if not font_p.is_file():
                    self.send_error_json(f"Font file '{row_font}' not found", 404)
                    return

                # Generate image completely in memory
                image = generate_image(
                    txt=txt,
                    header_file=str(header_p),
                    footer_file=str(footer_p),
                    font_file=str(font_p),
                    margin=margin,
                    text_color=text_color,
                    stroke_color=stroke_color,
                    stroke_width=stroke_width,
                    width=w,
                    height=h
                )

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
        
        # Endpoint 4: POST /generate-batch (Renders multiple custom bibs into a combined PDF in memory)
        if parsed_url.path == "/generate-batch":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                runners = json.loads(post_data.decode("utf-8"))
                
                if not isinstance(runners, list):
                    self.send_error_json("JSON body must be a list of runner objects", 400)
                    return
                    
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                margin = int(query_params.get("margin", [self.args.margin])[0])
                text_color = query_params.get("text_color", [self.args.text_color])[0]
                stroke_color = query_params.get("stroke_color", [self.args.stroke_color])[0]
                stroke_width = int(query_params.get("stroke_width", [self.args.stroke_width])[0])
                
                size_preset = query_params.get("size", [self.args.size])[0]
                custom_w = query_params.get("width", [None])[0]
                custom_h = query_params.get("height", [None])[0]

                if custom_w and custom_h:
                    w, h = int(custom_w), int(custom_h)
                else:
                    w, h = PRESETS.get(size_preset, PRESETS["A5"])

                all_pages_bytes = []
                
                for idx, runner in enumerate(runners):
                    firstname = runner.get("firstname", "")
                    lastname = runner.get("lastname", "")
                    if not lastname:
                        self.send_error_json(f"Runner at index {idx} is missing required field 'lastname'", 400)
                        return
                        
                    text = lastname.replace('ß', 'ẞ').upper()
                    text = text.replace('ẞ'.upper(), 'ß')
                    text = text.replace('-', '-\n').replace(' ', '\n')
                    
                    row_header = runner.get("header") or self.args.header
                    row_footer = runner.get("footer") or self.args.footer
                    row_font = runner.get("font") or (str(self.font_path) if self.font_path else None)
                    
                    if not row_header or not pathlib.Path(row_header).is_file():
                        self.send_error_json(f"Header file '{row_header}' for runner at index {idx} not found.", 404)
                        return
                    if not row_footer or not pathlib.Path(row_footer).is_file():
                        self.send_error_json(f"Footer file '{row_footer}' for runner at index {idx} not found.", 404)
                        return
                    if not row_font:
                        self.send_error_json(f"Font file is required for runner at index {idx} (pass 'font' field or specify global fallback font on server startup).", 400)
                        return
                    
                    font_p = pathlib.Path(row_font)
                    if not font_p.is_file():
                        self.send_error_json(f"Font file '{row_font}' for runner at index {idx} not found.", 404)
                        return
                        
                    image = generate_image(
                        txt=text,
                        header_file=str(row_header),
                        footer_file=str(row_footer),
                        font_file=str(font_p),
                        margin=margin,
                        text_color=text_color,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width,
                        width=w,
                        height=h
                    )
                    
                    img_io = io.BytesIO()
                    image.save(img_io, format='PNG', optimize=True)
                    img_bytes = img_io.getvalue()
                    
                    all_pages_bytes.append(img_bytes)
                    
                    if self.back_bytes:
                        all_pages_bytes.append(self.back_bytes)
                        
                if not all_pages_bytes:
                    self.send_error_json("No bib pages generated", 400)
                    return
                    
                pdf_w_pt = img2pdf.mm_to_pt(int(w * (210 / 3508))) if w else img2pdf.mm_to_pt(210)
                pdf_h_pt = img2pdf.mm_to_pt(int(h * (148 / 2480))) if h else img2pdf.mm_to_pt(148)
                letter = (pdf_w_pt, pdf_h_pt)
                layout = img2pdf.get_layout_fun(letter)
                
                pdf_bytes = img2pdf.convert(all_pages_bytes, layout_fun=layout)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.send_header("Content-Disposition", "attachment; filename=\"combined_bibs.pdf\"")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(pdf_bytes)
                
            except Exception as e:
                self.send_error_json(f"Batch generation failed: {e}", 500)
        else:
            self.send_error_json("Not Found. Use POST /generate-batch.", 404)


def run_server(args, font_path, back_bytes) -> None:
    # Inject parameters to the handler safely
    BibServerHandler.args = args
    BibServerHandler.font_path = font_path
    BibServerHandler.back_bytes = back_bytes

    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, BibServerHandler)
    print(f"\n[Server] Starting real-time Bib Kiosk Server on http://{args.host}:{args.port} ...")
    print(f"[Server] GET  Dropdown Assets: http://{args.host}:{args.port}/assets")
    print(f"[Server] GET  Single Bib     : http://{args.host}:{args.port}/generate?text=NAME")
    print(f"[Server] POST Batch PDF      : http://{args.host}:{args.port}/generate-batch")
    print("[Server] Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Stopping HTTP server gracefully...")
        httpd.server_close()
        import sys
        sys.exit(0)
