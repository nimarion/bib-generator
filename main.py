import argparse
import pandas as pd
from bib import generate_image
from PIL import Image
import io
import img2pdf

if __name__ == "__main__":
    argparse = argparse.ArgumentParser(
        prog='Bib Generator')
    argparse.add_argument(
        '--data', '-d', help='CSV file name', required=True)
    argparse.add_argument('--seperator', '-s', help='CSV seperator', default=',', required=False)
    argparse.add_argument(
        '--output', '-o', help='Output folder', required=True)
    argparse.add_argument('--font', '-F', help='Font file name', required=True)
    argparse.add_argument(
        '--footer', '-he', help='Footer file name', default="rehlingen.png", required=False)
    argparse.add_argument(
        '--create-duplicate', '-D', help='Create the same image two times with suffix', default=False, required=False, action='store_true')
    argparse.add_argument('--create-pdf', '-P', help='Create a pdf file', default=False, required=False, action='store_true')

    argparse.add_argument("--unique-keys", "-u", help="Unique keys in the CSV file, comma separated", default="lastname,firstname", required=False)

    args = argparse.parse_args()

    data_file = args.data
    output_folder = args.output
    font_file = args.font
    footer_file = args.footer
    create_duplicate = args.create_duplicate
    create_pdf = args.create_pdf
    unique_keys = args.unique_keys.split(',')

    df = pd.read_csv(data_file, sep=args.seperator)

    for index, row in df.iterrows():
        firstname = str(row['firstname'])
        lastname = str(row['lastname'])
        text = lastname.replace('ß', 'ẞ').upper()
        text = text.replace('ẞ'.upper(), 'ß')

        text = text.replace('-', '-\n').replace(' ', '\n')

        is_unique = df[df[unique_keys].eq(row[unique_keys]).all(axis=1)].shape[0] == 1
        if not is_unique:
            print("Warning: Duplicate found for", row[unique_keys].to_dict())
            text = text = firstname[0].upper() + ". " + lastname.upper()
            print("Appending first letter of firstname to text:", text)
            continue
        
        header_file = row['header']
        output_file = output_folder + "/" + lastname + "_" + firstname
        print("Generating image", text, header_file, footer_file, font_file)
        bytes = generate_image(text, header_file, footer_file, font_file)

        if create_pdf:
            letter = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(148))
            layout = img2pdf.get_layout_fun(letter)
            with open(output_file + ".pdf", "wb") as f:
                images = [bytes, bytes] if create_duplicate else [bytes]
                f.write(img2pdf.convert(images, layout_fun=layout))
        else:
            image=Image.open(io.BytesIO(bytes))
            if(create_duplicate == True):
                image.save(output_file + "_1.png")
                image.save(output_file + "_2.png")
            else:
                image.save(output_file + ".png")