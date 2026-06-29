import io
import pathlib
import img2pdf
from bib import generate_image

def generate_single_bib(
    row_idx: int,
    firstname: str,
    lastname: str,
    header_file: str,
    footer_file: str,
    font_file: str,
    output_folder: str,
    margin: int,
    text_color: str,
    stroke_color: str,
    stroke_width: int,
    create_duplicate: bool,
    create_pdf: bool,
    need_bytes: bool,
    is_unique: bool,
    width: int,
    height: int,
    back_bytes: bytes | None
) -> tuple[int, bytes | None]:
    """
    Worker function executed in parallel to process a single bib row.
    Generates the high-res image, saves the PNG(s) with lossless optimization,
    saves the individual PDF if requested (supporting Duplex alternating pages if back_bytes is provided),
    and returns bytes if needed for a combined PDF.
    """
    # Convert to uppercase but retain lowercase sharp s ('ß') instead of converting to 'SS'
    text = lastname.replace('ß', 'ẞ').upper()
    text = text.replace('ẞ'.upper(), 'ß')
    text = text.replace('-', '-\n').replace(' ', '\n')

    if firstname and not is_unique:
        text = f"{firstname[0].upper()}. {lastname.upper()}"

    output_path = pathlib.Path(output_folder)
    
    # Avoid trailing underscore if firstname is empty
    if firstname:
        output_file = output_path / f"{lastname}_{firstname}"
    else:
        output_file = output_path / f"{lastname}"
    
    # Generate the image using our core layout engine
    image = generate_image(
        txt=text,
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

    # Always save high-quality optimized PNG(s)
    if create_duplicate:
        image.save(f"{output_file}_1.png", optimize=True)
        image.save(f"{output_file}_2.png", optimize=True)
    else:
        image.save(f"{output_file}.png", optimize=True)

    img_bytes = None
    if need_bytes or create_pdf:
        # Convert image to PNG bytes for PDF generation
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG', optimize=True)
        img_bytes = img_byte_arr.getvalue()
        
        if create_pdf:
            # Sizing for pdf dimensions dynamically scaled
            pdf_w_pt = img2pdf.mm_to_pt(int(width * (210 / 3508))) if width else img2pdf.mm_to_pt(210)
            pdf_h_pt = img2pdf.mm_to_pt(int(height * (148 / 2480))) if height else img2pdf.mm_to_pt(148)
            letter = (pdf_w_pt, pdf_h_pt)
            layout = img2pdf.get_layout_fun(letter)
            
            pdf_path = output_file.with_suffix(".pdf")
            
            # Construct pages (supporting duplex printing with alternating back-side pages)
            pdf_pages = []
            if create_duplicate:
                if back_bytes:
                    pdf_pages.extend([img_bytes, back_bytes, img_bytes, back_bytes])
                else:
                    pdf_pages.extend([img_bytes, img_bytes])
            else:
                pdf_pages.append(img_bytes)
                if back_bytes:
                    pdf_pages.append(back_bytes)
                    
            with open(pdf_path, "wb") as f:
                f.write(img2pdf.convert(pdf_pages, layout_fun=layout))
                
    return row_idx, img_bytes
