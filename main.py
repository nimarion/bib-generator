import argparse
import pandas as pd
from bib import main as bib_generator

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
        '--header-offset', '-ho', help='Header offset', default=0, required=False, type=int)

    args = argparse.parse_args()

    data_file = args.data
    output_folder = args.output
    font_file = args.font
    footer_file = args.footer
    header_offset = args.header_offset

    df = pd.read_csv(data_file, sep=args.seperator)

    for index, row in df.iterrows():
        
        firstname = str(row['firstname'])
        lastname = str(row['lastname'])
        text = lastname.upper()

        # check if lastname is duplicated in the csv file preprend the firstname initial
        if df[df['lastname'] == lastname].shape[0] > 1:
            text = firstname[0].upper() + ". " + lastname.upper()
            print("Duplicated lastname", lastname, "prepending firstname initial", firstname[0])
        
        header_file = row['header']
        output_file = output_folder + "/" + lastname + "_" + firstname + ".png"
        bib_generator(text, output_file, header_file, footer_file, font_file, header_offset)
