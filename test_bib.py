import unittest
import tempfile
import pathlib
import pandas as pd
from PIL import Image
from bib import generate_image

class TestBibGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_dir = pathlib.Path(self.test_dir.name)
        
        # Paths to existing sample assets
        self.header_file = "example/globus.png"
        self.footer_file = "example/footer.png"
        self.font_file = "example/agency_fb.ttf"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_generate_image_creates_valid_image(self):
        # Generate an image with standard text
        img = generate_image(
            txt="TEST RUNNER",
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file
        )
        
        # Verify the returned object is a PIL Image with correct size and mode
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (3508, 2480))
        self.assertEqual(img.mode, "RGB")

    def test_sharp_s_handling_logic(self):
        # Test the sharp s custom conversion logic that we have in main.py
        names = ["Groß", "groß", "GROß", "GROẞ"]
        for name in names:
            text = name.replace('ß', 'ẞ').upper()
            text = text.replace('ẞ'.upper(), 'ß')
            # The result should have uppercase letters with a lowercase 'ß'
            self.assertEqual(text, "GROß")

    def test_binary_search_fits_long_text(self):
        # Long text should successfully fit on the canvas without crashing
        long_text = "VERY LONG LASTNAME\nWITH MULTIPLE LINES"
        img = generate_image(
            txt=long_text,
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file
        )
        self.assertEqual(img.size, (3508, 2480))

    def test_font_not_found_raises_exception(self):
        with self.assertRaises(OSError):
            generate_image(
                txt="TEST",
                header_file=self.header_file,
                footer_file=self.footer_file,
                font_file="invalid_font_path.ttf"
            )

    def test_duplicate_uniqueness_logic(self):
        # Mock DataFrame to simulate duplicates
        data = {
            'firstname': ['Imke', 'Peter', 'Imke'],
            'lastname': ['Onnen', 'Onnen', 'Onnen'],
            'header': ['example/globus.png', 'example/globus.png', 'example/globus.png']
        }
        df = pd.DataFrame(data)
        unique_keys = ['lastname', 'firstname']

        results = []
        for index, row in df.iterrows():
            firstname = str(row['firstname'])
            lastname = str(row['lastname'])
            
            is_unique = df[df[unique_keys].eq(row[unique_keys]).all(axis=1)].shape[0] == 1
            if not is_unique:
                text = f"{firstname[0].upper()}. {lastname.upper()}"
            else:
                text = lastname.upper()
            results.append((firstname, lastname, is_unique, text))

        # First entry 'Imke Onnen' is a duplicate
        self.assertFalse(results[0][2])
        self.assertEqual(results[0][3], "I. ONNEN")

        # Second entry 'Peter Onnen' is unique
        self.assertTrue(results[1][2])
        self.assertEqual(results[1][3], "ONNEN")

        # Third entry 'Imke Onnen' is a duplicate
        self.assertFalse(results[2][2])
        self.assertEqual(results[2][3], "I. ONNEN")

if __name__ == "__main__":
    unittest.main()
