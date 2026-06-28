from PIL import ImageFont, ImageDraw, Image
import argparse
import pathlib

def generate_image(
    txt: str,
    header_file: str,
    footer_file: str,
    font_file: str,
    offset_x: int = 0,
    offset_y: int = 0,
    margin: int = 175,
    text_color: str = "black",
    stroke_color: str = "black",
    stroke_width: int = 1
) -> Image.Image:
    """
    Generates a bib image (A5 size, high-res 3508x2480) with a header, footer,
    and centered text scaled dynamically using binary search to fit the available space.
    
    Args:
        txt: Text to be printed on the bib.
        header_file: Path to the header image file.
        footer_file: Path to the footer image file.
        font_file: Path to the TTF/OTF font file.
        offset_x: Horizontal text draw offset in pixels.
        offset_y: Vertical text draw offset in pixels.
        margin: Horizontal margin from left/right canvas edges in pixels.
        text_color: Color of the main text fill.
        stroke_color: Color of the text outline/stroke.
        stroke_width: Thickness of the text outline/stroke in pixels.
    """
    # A5 size at 300 DPI is approximately 3508 x 2480
    image = Image.new("RGBA", (3508, 2480), "white")
    
    header = Image.open(header_file).convert("RGBA")
    footer = Image.open(footer_file).convert("RGBA")
    draw = ImageDraw.Draw(image)

    W, H = image.size

    # The blank area height available for text between the header and footer
    blank_height = H - header.size[1] - footer.size[1]
    blank_width = W - (2 * margin)  # Apply symmetrical horizontal margins

    # Optimize font sizing using Binary Search to find the maximum fitting size.
    # Set the search ceiling dynamically based on the image size to prevent artificial caps.
    low = 1
    high = max(W, H)
    best_size = 1

    while low <= high:
        mid = (low + high) // 2
        try:
            font = ImageFont.truetype(font_file, mid)
        except OSError as e:
            raise OSError(f"Could not load font file '{font_file}': {e}")
            
        bbox = draw.multiline_textbbox((0, 0), txt, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        if w < blank_width and h < blank_height:
            best_size = mid
            low = mid + 1
        else:
            high = mid - 1

    # Load the best font size found
    font = ImageFont.truetype(font_file, best_size)
    bbox = draw.multiline_textbbox((0, 0), txt, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Calculate centered position in the blank area, compensating for internal font offsets
    x = (W - w) // 2 - bbox[0] + offset_x
    y = header.size[1] + (blank_height - h) // 2 - bbox[1] + offset_y

    # Draw the multiline text
    draw.text(
        (x, y),
        txt,
        font=font,
        fill=text_color,
        align="center",
        stroke_width=stroke_width,
        stroke_fill=stroke_color
    )

    # Paste header and footer, using their own alpha channels as masks to preserve transparency
    image.paste(header, (0, 0), mask=header)
    image.paste(footer, (0, H - footer.size[1]), mask=footer)
    
    # Convert RGBA to RGB for standard image saving
    return image.convert("RGB")


def main(
    txt: str,
    output_file: str,
    header_file: str,
    footer_file: str,
    font_file: str,
    margin: int = 175,
    text_color: str = "black",
    stroke_color: str = "black",
    stroke_width: int = 1
) -> None:        
    image = generate_image(
        txt=txt,
        header_file=header_file,
        footer_file=footer_file,
        font_file=font_file,
        margin=margin,
        text_color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Bib Generator')
    parser.add_argument('--text', '-t', help='Text to be printed on bib', required=True)
    parser.add_argument('--output', '-o', help='Output file name', required=True)
    parser.add_argument('--header', '-he', help='Header file name', required=True)
    parser.add_argument('--footer', '-f', help='Footer file name', required=True)
    parser.add_argument('--font', '-F', help='Font file name', required=True)
    parser.add_argument('--margin', '-m', type=int, help='Horizontal margin in pixels', default=175)
    parser.add_argument('--text-color', type=str, help='Text fill color', default="black")
    parser.add_argument('--stroke-color', type=str, help='Text stroke/outline color', default="black")
    parser.add_argument('--stroke-width', type=int, help='Text stroke/outline thickness', default=1)

    args = parser.parse_args()

    main(
        txt=args.text,
        output_file=args.output,
        header_file=args.header,
        footer_file=args.footer,
        font_file=args.font,
        margin=args.margin,
        text_color=args.text_color,
        stroke_color=args.stroke_color,
        stroke_width=args.stroke_width
    )
