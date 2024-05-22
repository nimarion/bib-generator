import argparse
import pandas as pd
from bib import generate_image
from PIL import Image
import io

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

    args = argparse.parse_args()

    data_file = args.data
    output_folder = args.output
    font_file = args.font
    footer_file = args.footer
    create_duplicate = args.create_duplicate

    df = pd.read_csv(data_file, sep=args.seperator)

    for index, row in df.iterrows():
        
        firstname = str(row['firstname'])
        lastname = str(row['lastname'])
        text = lastname.replace('ß', 'ẞ').upper()
        text = text.replace('ẞ'.upper(), 'ß')

        # check if lastname is duplicated in the csv file preprend the firstname initial
        if df[df['lastname'] == lastname].shape[0] > 1:
            text = firstname[0].upper() + ". " + lastname.upper()
            print("Duplicated lastname", lastname, "prepending firstname initial", firstname[0])
        
        header_file = row['header']
        output_file = output_folder + "/" + lastname + "_" + firstname + ".png"
        print("Generating image", text, header_file, footer_file, font_file)
        bytes = generate_image(text, header_file, footer_file, font_file)
        image=Image.open(io.BytesIO(bytes))
        if(create_duplicate == True):
            image.save(output_file.replace(".png", "_1.png"))   
            image.save(output_file.replace(".png", "_2.png"))
        else:
            image.save(output_file)

