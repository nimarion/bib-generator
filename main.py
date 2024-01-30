import argparse
import pandas as pd
from bib import main as bib_generator

if __name__ == "__main__":
    argparse = argparse.ArgumentParser(
        prog='Bib Generator')
    argparse.add_argument(
        '--excel', '-e', help='Excel file name', required=True)
    argparse.add_argument(
        '--output', '-o', help='Output folder', required=True)
    argparse.add_argument('--font', '-F', help='Font file name', required=True)
    argparse.add_argument(
        '--footer', '-he', help='Footer file name', default="rehlingen.png", required=False)
    argparse.add_argument(
        '--header-offset', '-ho', help='Header offset', default=0, required=False, type=int)

    args = argparse.parse_args()

    excel_file = args.excel
    output_folder = args.output
    font_file = args.font
    footer_file = args.footer
    header_offset = args.header_offset

    df = pd.read_excel(excel_file)

    for index, row in df.iterrows():
        firstname = row['Vorname']
        lastname = row['Nachname']
        text = lastname.upper()
        sponsor = row['Sponsor']
        header_file = sponsor + ".png"
        output_file = output_folder + "/" + lastname + "_" + firstname + ".png"
        print("Generating bib for", firstname, lastname, "with sponsor", sponsor)
        bib_generator(text, output_file, header_file, footer_file, font_file, header_offset)
