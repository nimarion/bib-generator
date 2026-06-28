import argparse
import pandas as pd
import pathlib
import sys
import img2pdf
import concurrent.futures


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
    is_unique: bool
) -> tuple[int, bytes | None]:
    """
    Worker function executed in parallel to process a single bib row.
    Generates the high-res image, saves the PNG(s) with lossless optimization,
    saves the individual PDF if requested, and returns bytes if needed for a combined PDF.
    """
    import io
    import pathlib
    import img2pdf
    from bib import generate_image
    
    # Convert to uppercase but retain lowercase sharp s ('ß') instead of converting to 'SS'
    text = lastname.replace('ß', 'ẞ').upper()
    text = text.replace('ẞ'.upper(), 'ß')
    text = text.replace('-', '-\n').replace(' ', '\n')

    if not is_unique:
        text = f"{firstname[0].upper()}. {lastname.upper()}"

    output_path = pathlib.Path(output_folder)
    output_file = output_path / f"{lastname}_{firstname}"
    
    # Generate the image using our core layout engine
    image = generate_image(
        txt=text,
        header_file=header_file,
        footer_file=footer_file,
        font_file=font_file,
        margin=margin,
        text_color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
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
            letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
            layout = img2pdf.get_layout_fun(letter)
            pdf_path = output_file.with_suffix(".pdf")
            with open(pdf_path, "wb") as f:
                images = [img_bytes, img_bytes] if create_duplicate else [img_bytes]
                f.write(img2pdf.convert(images, layout_fun=layout))
                
    return row_idx, img_bytes


def cli_main() -> None:
    parser = argparse.ArgumentParser(prog='Bib Generator')
    
    parser.add_argument(
        '--data', '-d', help='CSV or Excel (.xlsx/.xls) file name', required=True)
    
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
        dest='footer', help='Footer file name', default="rehlingen.png", required=False)
    
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

    args = parser.parse_args()

    # Pre-execution Validation
    data_path = pathlib.Path(args.data)
    font_path = pathlib.Path(args.font)
    footer_path = pathlib.Path(args.footer)
    output_folder = pathlib.Path(args.output)

    if not data_path.is_file():
        print(f"Error: Data file '{data_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    if not font_path.is_file():
        print(f"Error: Font file '{font_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    if not footer_path.is_file():
        print(f"Error: Footer image file '{footer_path}' does not exist.", file=sys.stderr)
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
    required_cols = {'firstname', 'lastname', 'header'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        print(f"Error: Dataset is missing required columns: {', '.join(missing_cols)}", file=sys.stderr)
        sys.exit(1)

    # Validate that all referenced headers exist
    unique_headers = df['header'].dropna().unique()
    missing_headers = []
    for h_file in unique_headers:
        if not pathlib.Path(h_file).is_file():
            missing_headers.append(h_file)
    if missing_headers:
        print("Error: The following referenced header files were not found:", file=sys.stderr)
        for missing in missing_headers:
            print(f"  - {missing}", file=sys.stderr)
        sys.exit(1)

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    unique_keys = args.unique_keys.split(',')
    
    # Prepare parameter tuples for multiprocessing workers
    tasks = []
    for index, row in df.iterrows():
        firstname = str(row['firstname'])
        lastname = str(row['lastname'])
        is_unique = df[df[unique_keys].eq(row[unique_keys]).all(axis=1)].shape[0] == 1
        
        if not is_unique:
            print(f"Warning: Duplicate found for {lastname}, {firstname} across keys: {unique_keys}")

        tasks.append((
            index,
            firstname,
            lastname,
            str(row['header']),
            str(footer_path),
            str(font_path),
            str(output_folder),
            args.margin,
            args.text_color,
            args.stroke_color,
            args.stroke_width,
            args.create_duplicate,
            args.create_pdf,
            args.combined_pdf,  # We only need bytes in memory if combined_pdf is True
            is_unique
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
                ordered_bytes.extend([img_bytes, img_bytes])
            else:
                ordered_bytes.append(img_bytes)

        letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
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
