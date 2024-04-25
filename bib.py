from PIL import ImageFont, ImageDraw, Image
import argparse
import io

def generate_image(txt, header_file, footer_file, font_file, header_offset = 0):
    print("Generating image", txt, header_file, footer_file, font_file, header_offset)
    # A5 size
    image = Image.new("RGB", (3508, 2480), "white") 
    header = Image.open(header_file)
    footer = Image.open(footer_file)
    draw = ImageDraw.Draw(image)
    fontsize = 1  # starting font size

    W, H = image.size

    # portion of image width you want text width to be
    blank = Image.new('RGB',(W - 50, 1100))


    font = ImageFont.truetype(font_file, fontsize)

    #print("Image size:", image.size)
    #print("Textarea size:", blank.size)


    while (font.getbbox(txt)[2] < blank.size[0]) and (font.getbbox(txt)[3] < blank.size[1]):
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype(font_file, fontsize)

    # optionally de-increment to be sure it is less than criteria
    fontsize -= 0
    font = ImageFont.truetype(font_file, fontsize)

    _, _, w, h = draw.textbbox((0, 0), txt, font=font)

    #print('Fontsize:',fontsize)
    draw.text(((W-w)/2,(H-h)/2), txt, font=font, fill="black", align="center", stroke_width=1, stroke_fill="black")
    #draw.rectangle([0, 0, blank.size[0] - 1, blank.size[1] - 1], outline="red", width=10)

    #draw.text((2100, 442), "150", font=font, fill="black", align="center", stroke_width=1, stroke_fill="black")

    # draw text on top right of text area

    #draw.text((((W-w)/2) +w, (H-h)/2), "15", font=font, fill="black", align="center", stroke_width=3, stroke_fill="black")

    image.paste(header, (0, header_offset))
    image.paste(footer, (0, image.size[1] - footer.size[1]))

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

    

def main(txt, output_file, header_file, footer_file, font_file, header_offset = 0):
    bytes = generate_image(txt, header_file, footer_file, font_file, header_offset)
    image = Image.open(io.BytesIO(bytes))
    image.save(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Bib Generator')
    parser.add_argument('--text', '-t', help='Text to be printed on bib', required=True)
    parser.add_argument('--output', '-o', help='Output file name', required=True)
    parser.add_argument('--header', '-he', help='Header file name', required=True)
    parser.add_argument('--footer', '-f', help='Footer file name', required=True)
    parser.add_argument('--font', '-F', help='Font file name', required=True)
    parser.add_argument('--header-offset', '-ho', help='Header offset', default=0, required=False, type=int)

    args = parser.parse_args()

    header_file = args.header
    footer_file = args.footer
    font_file = args.font
    txt = args.text
    output_file = args.output
    header_offset = args.header_offset

    main(txt, output_file, header_file, footer_file, font_file, header_offset)

    

