from PIL import ImageFont, ImageDraw, Image
import argparse
import io
import re

def contains_umlaut(s):
    s = s.lower()
    pattern = r'[äöüëïíš]'
    return bool(re.search(pattern, s))

def generate_image(txt, header_file, footer_file, font_file, offset_x=0, offset_y=0):
    # A5 size
    image = Image.new("RGB", (3508, 2480), "white")
    header = Image.open(header_file)
    footer = Image.open(footer_file)
    draw = ImageDraw.Draw(image)
    fontsize = 1  # starting font size

    W, H = image.size

    # portion of image width you want text width to be
    blank_height = image.size[1] - header.size[1] - footer.size[1];
    blank = Image.new('RGB', (W - 25, blank_height), "white")

    font = ImageFont.truetype(font_file, fontsize)

    # print("Image size:", image.size)
    # print("Textarea size:", blank.size)

    while (font.getbbox(txt)[2] < blank.size[0]) and (font.getbbox(txt)[3] < blank.size[1]):
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype(font_file, fontsize)

    # optionally de-increment to be sure it is less than criteria
    fontsize -= 0
    font = ImageFont.truetype(font_file, fontsize)
   
    #if(contains_umlaut(txt)):
    #    print("Contains umlaut")
    #    offset_y += 70
    #    fontsize = int(fontsize * 0.8)
    #    font = ImageFont.truetype(font_file, fontsize)
    

    _, _, w, h = draw.textbbox((0, 0), txt, font=font)
    x = (W - w) // 2
    y = header.size[1] + ((blank_height - h) // 2)

    position = ((W - w) / 2 + offset_x, (H - h) / 2 + offset_y)
    draw.text(position, txt, font=font, fill="black", align="center", stroke_width=1, stroke_fill="black")

    # draw.rectangle([0, 0, blank.size[0] - 1, blank.size[1] - 1], outline="red", width=10)

    # draw rectanble around text area with blank size
    # draw.rectangle([0, header.size[1], W - 1, H - footer.size[1] - 1], outline="red", width=10)

    # draw.text((2100, 442), "150", font=font, fill="black", align="center", stroke_width=1, stroke_fill="black")

    # draw text on top right of text area

    image.paste(header, (0, 0))
    image.paste(footer, (0, image.size[1] - footer.size[1]))

    img_byte_arr=io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr=img_byte_arr.getvalue()
    return img_byte_arr



def main(txt, output_file, header_file, footer_file, font_file):        
    bytes=generate_image(txt, header_file, footer_file, font_file)
    image=Image.open(io.BytesIO(bytes))
    image.save(output_file)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(
                    prog='Bib Generator')
    parser.add_argument(
        '--text', '-t', help='Text to be printed on bib', required=True)
    parser.add_argument(
        '--output', '-o', help='Output file name', required=True)
    parser.add_argument('--header', '-he',
                        help='Header file name', required=True)
    parser.add_argument(
        '--footer', '-f', help='Footer file name', required=True)
    parser.add_argument('--font', '-F', help='Font file name', required=True)

    args=parser.parse_args()

    header_file=args.header
    footer_file=args.footer
    font_file=args.font
    txt=args.text
    output_file=args.output

    main(txt, output_file, header_file, footer_file, font_file)
