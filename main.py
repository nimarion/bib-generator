import argparse
import pandas as pd
import pathlib
import io
import sys
import re
import img2pdf
import concurrent.futures
from PIL import Image
from bib import PRESETS


def generate_single_bib(
    row_idx: int,
    firstname: str,
    lastname: str,
    header_file: str,
    footer_file: str,
    font_file: str,
    output_folder: str,
    margin: int,
    text_color: str,
    stroke_color: str,
    stroke_width: int,
    create_duplicate: bool,
    create_pdf: bool,
    need_bytes: bool,
    is_unique: bool,
    width: int,
    height: int,
    back_bytes: bytes | None
) -> tuple[int, bytes | None]:
    """
    Worker function executed in parallel to process a single bib row.
    Generates the high-res image, saves the PNG(s) with lossless optimization,
    saves the individual PDF if requested (supporting Duplex alternating pages if back_bytes is provided),
    and returns bytes if needed for a combined PDF.
    """
    import io
    import pathlib
    import img2pdf
    from bib import generate_image
    
    # Convert to uppercase but retain lowercase sharp s ('ß') instead of converting to 'SS'
    text = lastname.replace('ß', 'ẞ').upper()
    text = text.replace('ẞ'.upper(), 'ß')
    text = text.replace('-', '-\n').replace(' ', '\n')

    if firstname and not is_unique:
        text = f"{firstname[0].upper()}. {lastname.upper()}"

    output_path = pathlib.Path(output_folder)
    
    # Avoid trailing underscore if firstname is empty (e.g., in sequential number generation)
    if firstname:
        output_file = output_path / f"{lastname}_{firstname}"
    else:
        output_file = output_path / f"{lastname}"
    
    # Generate the image using our core layout engine
    image = generate_image(
        txt=text,
        header_file=header_file,
        footer_file=footer_file,
        font_file=font_file,
        margin=margin,
        text_color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        width=width,
        height=height
    )

    # Always save high-quality optimized PNG(s)
    if create_duplicate:
        image.save(f"{output_file}_1.png", optimize=True)
        image.save(f"{output_file}_2.png", optimize=True)
    else:
        image.save(f"{output_file}.png", optimize=True)

    img_bytes = None
    if need_bytes or create_pdf:
        # Convert image to PNG bytes for PDF generation
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG', optimize=True)
        img_bytes = img_byte_arr.getvalue()
        
        if create_pdf:
            # Sizing for pdf dimensions dynamically scaled
            pdf_w_pt = img2pdf.mm_to_pt(int(width * (210 / 3508))) if width else img2pdf.mm_to_pt(210)
            pdf_h_pt = img2pdf.mm_to_pt(int(height * (148 / 2480))) if height else img2pdf.mm_to_pt(148)
            letter = (pdf_w_pt, pdf_h_pt)
            layout = img2pdf.get_layout_fun(letter)
            
            pdf_path = output_file.with_suffix(".pdf")
            
            # Construct pages (supporting duplex printing with alternating back-side pages)
            pdf_pages = []
            if create_duplicate:
                if back_bytes:
                    pdf_pages.extend([img_bytes, back_bytes, img_bytes, back_bytes])
                else:
                    pdf_pages.extend([img_bytes, img_bytes])
            else:
                pdf_pages.append(img_bytes)
                if back_bytes:
                    pdf_pages.append(back_bytes)
                    
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(pdf_pages, layout_fun=layout))
                
    return row_idx, img_bytes


def cli_main() -> None:
    parser = argparse.ArgumentParser(prog='Bib Generator')
    
    parser.add_argument(
        '--data', '-d', help='CSV or Excel (.xlsx/.xls) file name (optional if using --sequence)', required=False)
    
    parser.add_argument(
        '--sequence', '-S', help='Generic sequential number range (e.g. "1-500" or "10,20,30")', required=False)

    parser.add_argument(
        '--header', '-H', help='Header image file (required if --sequence is used or not in spreadsheet)', required=False)
    
    # Support both spelling variants for separator to ensure backward compatibility
    parser.add_argument(
        '--separator', '--seperator', '-s',
        dest='separator', help='CSV separator character', default=',', required=False)
    
    parser.add_argument(
        '--output', '-o', help='Output folder', required=True)
    
    parser.add_argument(
        '--font', '-F', help='Font file name', required=True)
    
    # Support both proper -f and legacy -he options for footer
    parser.add_argument(
        '--footer', '-f', '-he',
        dest='footer', help='Footer file name (required if not in spreadsheet)', required=False)
    
    parser.add_argument(
        '--create-duplicate', '-D',
        help='Create the same image two times with suffix', default=False, required=False, action='store_true')
    
    parser.add_argument(
        '--create-pdf', '-P',
        help='Create individual pdf files', default=False, required=False, action='store_true')

    parser.add_argument(
        '--combined-pdf', '-C',
        help='Compile all generated bibs into a single multi-page PDF inside the output folder',
        default=False, required=False, action='store_true')

    parser.add_argument(
        "--unique-keys", "-u",
        help="Unique keys in the data file, comma separated", default="lastname,firstname", required=False)

    # Advanced styling options
    parser.add_argument(
        '--margin', '-m', type=int,
        help='Horizontal margin in pixels', default=175, required=False)
    
    parser.add_argument(
        '--text-color', type=str,
        help='Color of the main text', default='black', required=False)
    
    parser.add_argument(
        '--stroke-color', type=str,
        help='Color of the text outline/stroke', default='black', required=False)
    
    parser.add_argument(
        '--stroke-width', type=int,
        help='Thickness of the text outline/stroke in pixels', default=1, required=False)

    # Custom canvas sizing options
    parser.add_argument(
        '--size', type=str,
        help='Canvas size preset (A4, A5, A6, letter)', default="A5", choices=list(PRESETS.keys()), required=False)
    
    parser.add_argument(
        '--width', type=int,
        help='Custom canvas width in pixels (overrides --size preset)', required=False)
    
    parser.add_argument(
        '--height', type=int,
        help='Custom canvas height in pixels (overrides --size preset)', required=False)

    # Duplex Printing Option
    parser.add_argument(
        '--back-side', '-B',
        help='Optional path to template image for the back side of bibs (for duplex double-sided printing)',
        required=False)

    args = parser.parse_args()

    # Pre-execution Validation
    font_path = pathlib.Path(args.font)
    output_folder = pathlib.Path(args.output)

    # 1. Ensure at least one data source is supplied
    if not args.data and not args.sequence:
        print("Error: Either --data (spreadsheet) or --sequence (number range) must be provided.", file=sys.stderr)
        sys.exit(1)

    # 2. Validate font file
    if not font_path.is_file():
        print(f"Error: Font file '{font_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    # Determine canvas dimensions from preset or custom values
    if args.width and args.height:
        canvas_w, canvas_h = args.width, args.height
    else:
        canvas_w, canvas_h = PRESETS[args.size]

    # Pre-process duplex back-side bytes once in main process to maximize performance
    back_bytes = None
    if args.back_side:
        back_side_path = pathlib.Path(args.back_side)
        if not back_side_path.is_file():
            print(f"Error: Duplex back-side image '{back_side_path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        try:
            print(f"Loading and auto-rescaling back-side image to canvas size: {canvas_w} x {canvas_h}")
            back_raw = Image.open(back_side_path).convert("RGB")
            back_resized = back_raw.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            back_io = io.BytesIO()
            back_resized.save(back_io, format='PNG', optimize=True)
            back_bytes = back_io.getvalue()
        except Exception as e:
            print(f"Error pre-processing back-side image: {e}", file=sys.stderr)
            sys.exit(1)

    # Data Loader Phase: Parse CSV, Excel, or build synthetic sequence
    if args.sequence:
        if not args.header:
            print("Error: --header (-H) logo is required when generating generic sequential numbers.", file=sys.stderr)
            sys.exit(1)
            
        header_path = pathlib.Path(args.header)
        if not header_path.is_file():
            print(f"Error: Header logo file '{header_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        if not args.footer:
            print("Error: --footer (-f) image is required when generating generic sequential numbers.", file=sys.stderr)
            sys.exit(1)
            
        footer_path = pathlib.Path(args.footer)
        if not footer_path.is_file():
            print(f"Error: Footer image file '{footer_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        # Parse sequence pattern (e.g. "1-500" or comma-separated "1,2,3")
        range_match = re.match(r"^(\d+)-(\d+)$", args.sequence.strip())
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if start > end:
                start, end = end, start
            numbers = list(range(start, end + 1))
        else:
            numbers = [n.strip() for n in args.sequence.split(",") if n.strip()]

        print(f"Generating sequential dataset for {len(numbers)} generic race numbers: {args.sequence}")
        data_list = []
        for num in numbers:
            data_list.append({
                "firstname": "",
                "lastname": str(num),
                "header": str(header_path),
                "footer": str(footer_path)
            })
        df = pd.DataFrame(data_list)
    else:
        # Load from spreadsheet
        data_path = pathlib.Path(args.data)
        if not data_path.is_file():
            print(f"Error: Data file '{data_path}' does not exist.", file=sys.stderr)
            sys.exit(1)

        # Zero-Config file type auto-detection (CSV vs Excel)
        is_excel = data_path.suffix.lower() in ('.xlsx', '.xls')
        try:
            if is_excel:
                print(f"Reading registration data from Excel spreadsheet: {data_path}")
                df = pd.read_excel(data_path)
            else:
                print(f"Reading registration data from Delimiter-Separated CSV: {data_path}")
                df = pd.read_csv(data_path, sep=args.separator)
        except Exception as e:
            print(f"Error reading registration file: {e}", file=sys.stderr)
            sys.exit(1)

        # Validate required columns
        required_cols = {'firstname', 'lastname'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            print(f"Error: Dataset is missing required columns: {', '.join(missing_cols)}", file=sys.stderr)
            sys.exit(1)

        # Validate that we have header logos either globally or per-row
        has_header_col = 'header' in df.columns
        if not has_header_col and not args.header:
            print("Error: Header logo is required (either as a 'header' column in the data file or globally via --header/-H).", file=sys.stderr)
            sys.exit(1)

        # Validate that we have footers either globally or per-row
        has_footer_col = 'footer' in df.columns
        if not has_footer_col and not args.footer:
            print("Error: Footer image is required (either as a 'footer' column in the data file or globally via --footer/-f).", file=sys.stderr)
            sys.exit(1)

        # Pre-flight asset existence validations
        unique_headers = df['header'].dropna().unique() if has_header_col else ([args.header] if args.header else [])
        unique_footers = df['footer'].dropna().unique() if has_footer_col else ([args.footer] if args.footer else [])

        missing_headers = [h for h in unique_headers if not pathlib.Path(h).is_file()]
        missing_footers = [f for f in unique_footers if not pathlib.Path(f).is_file()]

        if missing_headers or missing_footers:
            if missing_headers:
                print("Error: The following referenced header files were not found:", file=sys.stderr)
                for m in missing_headers:
                    print(f"  - {m}", file=sys.stderr)
            if missing_footers:
                print("Error: The following referenced footer files were not found:", file=sys.stderr)
                for m in missing_footers:
                    print(f"  - {m}", file=sys.stderr)
            sys.exit(1)

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    unique_keys = args.unique_keys.split(',')
    
    # Prepare parameter tuples for multiprocessing workers
    tasks = []
    for index, row in df.iterrows():
        firstname = str(row['firstname']) if pd.notna(row['firstname']) else ""
        lastname = str(row['lastname'])
        
        # Determine header and footer for this row (supporting spreadsheet column or global fallback)
        row_header = str(row['header']) if 'header' in df.columns and pd.notna(row['header']) else str(args.header)
        row_footer = str(row['footer']) if 'footer' in df.columns and pd.notna(row['footer']) else str(args.footer)

        # Check uniqueness across specified keys (only if we have both fields)
        is_unique = True
        if firstname:
            is_unique = df[df[unique_keys].eq(row[unique_keys]).all(axis=1)].shape[0] == 1
            if not is_unique:
                print(f"Warning: Duplicate found for {lastname}, {firstname} across keys: {unique_keys}")

        tasks.append((
            index,
            firstname,
            lastname,
            row_header,
            row_footer,
            str(font_path),
            str(output_folder),
            args.margin,
            args.text_color,
            args.stroke_color,
            args.stroke_width,
            args.create_duplicate,
            args.create_pdf,
            args.combined_pdf,  # We only need bytes in memory if combined_pdf is True
            is_unique,
            canvas_w,
            canvas_h,
            back_bytes
        ))

    all_bib_bytes_map = {}
    print(f"Processing {len(tasks)} bibs in parallel across multi-core CPU...")
    
    # Run the multiprocessing pool
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(generate_single_bib, *task): task for task in tasks}
        for future in concurrent.futures.as_completed(futures):
            try:
                row_idx, img_bytes = future.result()
                if img_bytes is not None:
                    all_bib_bytes_map[row_idx] = img_bytes
            except Exception as e:
                task_data = futures[future]
                print(f"Error processing bib for {task_data[1]} {task_data[2]}: {e}", file=sys.stderr)

    # If combined PDF generation was requested, compile in deterministic row order
    if args.combined_pdf and all_bib_bytes_map:
        ordered_bytes = []
        for idx in sorted(all_bib_bytes_map.keys()):
            img_bytes = all_bib_bytes_map[idx]
            
            if args.create_duplicate:
                if back_bytes:
                    ordered_bytes.extend([img_bytes, back_bytes, img_bytes, back_bytes])
                else:
                    ordered_bytes.extend([img_bytes, img_bytes])
            else:
                ordered_bytes.append(img_bytes)
                if back_bytes:
                    ordered_bytes.append(back_bytes)

        # Scale layout dimensions based on actual width and height
        pdf_w_pt = img2pdf.mm_to_pt(int(canvas_w * (210 / 3508))) if canvas_w else img2pdf.mm_to_pt(210)
        pdf_h_pt = img2pdf.mm_to_pt(int(canvas_h * (148 / 2480))) if canvas_h else img2pdf.mm_to_pt(148)
        letter = (pdf_w_pt, pdf_h_pt)
        layout = img2pdf.get_layout_fun(letter)
        combined_path = output_folder / "combined_bibs.pdf"
        
        print(f"Compiling {len(ordered_bytes)} bib pages into combined PDF: {combined_path}")
        try:
            with open(combined_path, "wb") as f:
                f.write(img2pdf.convert(ordered_bytes, layout_fun=layout))
        except Exception as e:
            print(f"Error compiling combined PDF: {e}", file=sys.stderr)
            
    print("Execution complete. All bib files successfully optimized and saved.")


if __name__ == "__main__":
    cli_main()
