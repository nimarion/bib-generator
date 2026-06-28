import argparse
import pandas as pd
import pathlib
import io
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
        help='Create a pdf file', default=False, required=False, action='store_true')

    parser.add_argument(
        "--unique-keys", "-u",
        help="Unique keys in the CSV file, comma separated", default="lastname,firstname", required=False)

    args = parser.parse_args()

    data_file = args.data
    output_folder = pathlib.Path(args.output)
    font_file = args.font
    footer_file = args.footer
    create_duplicate = args.create_duplicate
    create_pdf = args.create_pdf
    unique_keys = args.unique_keys.split(',')

    # Ensure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_file, sep=args.separator)

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
            # For non-unique rows, prepend the first initial of the first name to distinguish them
            text = f"{firstname[0].upper()}. {lastname.upper()}"
            print("Appending first letter of firstname to text:", text)
            # Do NOT use 'continue' here, as that skips bib generation completely!

        header_file = row['header']
        output_file = output_folder / f"{lastname}_{firstname}"
        
        print(f"Generating bib for {firstname} {lastname} -> Text: {repr(text)}")
        image = generate_image(text, header_file, footer_file, font_file)

        if create_pdf:
            # We must serialize to bytes for img2pdf
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
            layout = img2pdf.get_layout_fun(letter)
            
            pdf_path = output_file.with_suffix(".pdf")
            with open(pdf_path, "wb") as f:
                images = [img_bytes, img_bytes] if create_duplicate else [img_bytes]
                f.write(img2pdf.convert(images, layout_fun=layout))
        else:
            if create_duplicate:
                image.save(f"{output_file}_1.png")
                image.save(f"{output_file}_2.png")
            else:
                image.save(f"{output_file}.png")
