import argparse
import pandas as pd
import pathlib
import io
import sys
import img2pdf
from PIL import Image
from bib import generate_image

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Bib Generator')
    
    parser.add_argument(
        '--data', '-d', help='CSV file name', required=True)
    
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
        help="Unique keys in the CSV file, comma separated", default="lastname,firstname", required=False)

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
        print(f"Error: CSV data file '{data_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    if not font_path.is_file():
        print(f"Error: Font file '{font_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    if not footer_path.is_file():
        print(f"Error: Footer image file '{footer_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_csv(data_path, sep=args.separator)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate required columns
    required_cols = {'firstname', 'lastname', 'header'}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        print(f"Error: CSV is missing required columns: {', '.join(missing_cols)}", file=sys.stderr)
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
    all_bib_bytes = []

    for index, row in df.iterrows():
        firstname = str(row['firstname'])
        lastname = str(row['lastname'])
        
        # Convert to uppercase but retain lowercase sharp s ('ß') instead of converting it to 'SS' or capital 'ẞ'
        text = lastname.replace('ß', 'ẞ').upper()
        text = text.replace('ẞ'.upper(), 'ß')

        text = text.replace('-', '-\n').replace(' ', '\n')

        # Check uniqueness across specified keys
        is_unique = df[df[unique_keys].eq(row[unique_keys]).all(axis=1)].shape[0] == 1
        if not is_unique:
            print("Warning: Duplicate found for", row[unique_keys].to_dict())
            text = f"{firstname[0].upper()}. {lastname.upper()}"
            print("Appending first letter of firstname to text:", text)

        header_file = str(row['header'])
        output_file = output_folder / f"{lastname}_{firstname}"
        
        print(f"Generating bib for {firstname} {lastname} -> Text: {repr(text)}")
        image = generate_image(
            txt=text,
            header_file=header_file,
            footer_file=str(footer_path),
            font_file=str(font_path),
            margin=args.margin,
            text_color=args.text_color,
            stroke_color=args.stroke_color,
            stroke_width=args.stroke_width
        )

        # We always need the PNG bytes if we are doing individual PDFs or a combined PDF
        if args.create_pdf or args.combined_pdf:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            if args.combined_pdf:
                if args.create_duplicate:
                    all_bib_bytes.extend([img_bytes, img_bytes])
                else:
                    all_bib_bytes.append(img_bytes)

            if args.create_pdf:
                letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
                layout = img2pdf.get_layout_fun(letter)
                pdf_path = output_file.with_suffix(".pdf")
                with open(pdf_path, "wb") as f:
                    images = [img_bytes, img_bytes] if args.create_duplicate else [img_bytes]
                    f.write(img2pdf.convert(images, layout_fun=layout))
        
        # Save individual PNGs
        if not args.create_pdf or not args.combined_pdf: # Save PNGs unless requested to only generate a combined PDF without them (wait, we always generate PNG files as standard unless only combined PDF is requested, or we can just always save PNGs to output)
            pass
        
        # To match legacy behavior, we always write standard PNGs to the folder
        if args.create_duplicate:
            image.save(f"{output_file}_1.png")
            image.save(f"{output_file}_2.png")
        else:
            image.save(f"{output_file}.png")

    # If combined PDF generation was requested, compile all accumulated bibs
    if args.combined_pdf and all_bib_bytes:
        letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
        layout = img2pdf.get_layout_fun(letter)
        combined_path = output_folder / "combined_bibs.pdf"
        print(f"Compiling {len(all_bib_bytes)} bib pages into combined PDF: {combined_path}")
        try:
            with open(combined_path, "wb") as f:
                f.write(img2pdf.convert(all_bib_bytes, layout_fun=layout))
        except Exception as e:
            print(f"Error compiling combined PDF: {e}", file=sys.stderr)
