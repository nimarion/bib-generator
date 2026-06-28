from PIL import ImageFont, ImageDraw, Image
import argparse
import pathlib

# Standard canvas presets (landscape orientation at 300 DPI)
PRESETS = {
    "A4": (4960, 3508),
    "A5": (3508, 2480),
    "A6": (2480, 1748),
    "letter": (3300, 2550),
}

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
    stroke_width: int = 1,
    width: int = 3508,
    height: int = 2480
) -> Image.Image:
    """
    Generates a bib image with a header, footer, and centered text scaled dynamically
    using binary search to fit the available space. Supports custom width/height canvas sizes,
    and automatically rescales headers and footers proportionally.
    """
    # Create the custom-sized blank canvas
    image = Image.new("RGBA", (width, height), "white")
    
    # Load and auto-rescale header to match canvas width proportionally
    header_raw = Image.open(header_file).convert("RGBA")
    h_w, h_h = header_raw.size
    new_h_height = int(h_h * (width / h_w))
    header = header_raw.resize((width, new_h_height), Image.Resampling.LANCZOS)

    # Load and auto-rescale footer to match canvas width proportionally
    footer_raw = Image.open(footer_file).convert("RGBA")
    f_w, f_h = footer_raw.size
    new_f_height = int(f_h * (width / f_w))
    footer = footer_raw.resize((width, new_f_height), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(image)
    W, H = image.size

    # The blank area height available for text between the header and footer
    blank_height = H - header.size[1] - footer.size[1]
    blank_width = W - (2 * margin)  # Apply symmetrical horizontal margins

    if blank_height <= 0 or blank_width <= 0:
        raise ValueError(
            f"Canvas is too small for the header/footer dimensions (blank height: {blank_height}px, blank width: {blank_width}px)."
        )

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
    stroke_width: int = 1,
    width: int = 3508,
    height: int = 2480
) -> None:        
    import sys
    
    # Robust pre-flight path validations for standalone CLI runs
    h_path = pathlib.Path(header_file)
    fo_path = pathlib.Path(footer_file)
    f_path = pathlib.Path(font_file)
    
    if not h_path.is_file():
        print(f"Error: Header file '{header_file}' does not exist.", file=sys.stderr)
        sys.exit(1)
    if not fo_path.is_file():
        print(f"Error: Footer file '{footer_file}' does not exist.", file=sys.stderr)
        sys.exit(1)
    if not f_path.is_file():
        print(f"Error: Font file '{font_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    image = generate_image(
        txt=txt,
        header_file=header_file,
        footer_file=footer_file,
        font_file=font_file,
        margin=margin,
        text_color=text_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        width=width,
        height=height
    )
    output_path = pathlib.Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save with lossless PNG optimization enabled for smaller output sizes
    image.save(output_path, optimize=True)


def cli_main() -> None:
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
    
    # Custom size options
    parser.add_argument('--size', type=str, help='Canvas preset (A4, A5, A6, letter)', default="A5", choices=list(PRESETS.keys()))
    parser.add_argument('--width', type=int, help='Custom canvas width in pixels')
    parser.add_argument('--height', type=int, help='Custom canvas height in pixels')

    args = parser.parse_args()

    # Determine canvas dimensions from preset or custom values
    if args.width and args.height:
        w, h = args.width, args.height
    else:
        w, h = PRESETS[args.size]

    main(
        txt=args.text,
        output_file=args.output,
        header_file=args.header,
        footer_file=args.footer,
        font_file=args.font,
        margin=args.margin,
        text_color=args.text_color,
        stroke_color=args.stroke_color,
        stroke_width=args.stroke_width,
        width=w,
        height=h
    )


if __name__ == "__main__":
    cli_main()
