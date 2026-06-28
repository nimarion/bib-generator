import unittest
import tempfile
import pathlib
import pandas as pd
import subprocess
import sys
from PIL import Image
from bib import generate_image, PRESETS

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
        # Generate an image with standard text and custom styling
        img = generate_image(
            txt="TEST RUNNER",
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file,
            margin=100,
            text_color="blue",
            stroke_color="red",
            stroke_width=3
        )
        
        # Verify the returned object is a PIL Image with correct size and mode
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (3508, 2480))
        self.assertEqual(img.mode, "RGB")

    def test_sharp_s_handling_logic(self):
        # Test the sharp s custom conversion logic
        names = ["Groß", "groß", "GROß", "GROẞ"]
        for name in names:
            text = name.replace('ß', 'ẞ').upper()
            text = text.replace('ẞ'.upper(), 'ß')
            self.assertEqual(text, "GROß")

    def test_binary_search_fits_long_text(self):
        # Long text should successfully fit on the canvas without crashing
        long_text = "VERY LONG LASTNAME\nWITH MULTIPLE LINES"
        img = generate_image(
            txt=long_text,
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file,
            margin=200
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

        self.assertFalse(results[0][2])
        self.assertEqual(results[0][3], "I. ONNEN")
        self.assertTrue(results[1][2])
        self.assertEqual(results[1][3], "ONNEN")

    def test_cli_execution_with_csv_and_styling(self):
        # Create a mock CSV file in our temp folder
        mock_csv = self.output_dir / "test_data.csv"
        df = pd.DataFrame({
            "firstname": ["John", "Jane"],
            "lastname": ["Doe", "Smith"],
            "header": [self.header_file, self.header_file]
        })
        df.to_csv(mock_csv, index=False, sep=";")

        # Run main.py via subprocess to test the full CLI integration
        cmd = [
            sys.executable, "main.py",
            "--data", str(mock_csv),
            "--output", str(self.output_dir),
            "--font", self.font_file,
            "--footer", self.footer_file,
            "--separator", ";",
            "--combined-pdf",
            "--margin", "120",
            "--text-color", "navy",
            "--stroke-color", "gold",
            "--stroke-width", "2"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"CSV CLI failed with error:\n{result.stderr}")

        # Check that PNGs and the combined PDF exist
        self.assertTrue((self.output_dir / "Doe_John.png").is_file())
        self.assertTrue((self.output_dir / "Smith_Jane.png").is_file())
        self.assertTrue((self.output_dir / "combined_bibs.pdf").is_file())

    def test_cli_execution_with_csv_assets_in_data_file(self):
        # Create a mock CSV file where both header and footer are provided as spreadsheet columns
        mock_csv = self.output_dir / "test_data.csv"
        df = pd.DataFrame({
            "firstname": ["John", "Jane"],
            "lastname": ["Doe", "Smith"],
            "header": [self.header_file, self.header_file],
            "footer": [self.footer_file, self.footer_file]
        })
        df.to_csv(mock_csv, index=False, sep=";")

        # Run main.py WITHOUT --footer or --header CLI parameters
        cmd = [
            sys.executable, "main.py",
            "--data", str(mock_csv),
            "--output", str(self.output_dir),
            "--font", self.font_file,
            "--separator", ";",
            "--combined-pdf"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"CLI with inline assets failed:\n{result.stderr}")

        self.assertTrue((self.output_dir / "Doe_John.png").is_file())
        self.assertTrue((self.output_dir / "Smith_Jane.png").is_file())
        self.assertTrue((self.output_dir / "combined_bibs.pdf").is_file())

    def test_cli_execution_with_excel_and_multiprocessing(self):
        # Create a mock Excel file in our temp folder
        mock_xlsx = self.output_dir / "test_data.xlsx"
        df = pd.DataFrame({
            "firstname": ["Bob", "Alice"],
            "lastname": ["Johnson", "Williams"],
            "header": [self.header_file, self.header_file]
        })
        df.to_excel(mock_xlsx, index=False)

        # Run main.py via subprocess to test full Excel and Parallel execution
        cmd = [
            sys.executable, "main.py",
            "--data", str(mock_xlsx),
            "--output", str(self.output_dir),
            "--font", self.font_file,
            "--footer", self.footer_file,
            "--combined-pdf"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"Excel Parallel CLI failed with error:\n{result.stderr}")

        self.assertTrue((self.output_dir / "Johnson_Bob.png").is_file())
        self.assertTrue((self.output_dir / "Williams_Alice.png").is_file())
        self.assertTrue((self.output_dir / "combined_bibs.pdf").is_file())

    def test_universal_canvas_sizing_presets(self):
        # Test A4 preset (which is 4960 x 3508)
        img_a4 = generate_image(
            txt="A4 RUNNER",
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file,
            width=PRESETS["A4"][0],
            height=PRESETS["A4"][1]
        )
        self.assertEqual(img_a4.size, (4960, 3508))

        # Test custom resolution (e.g. 2000 x 1000)
        img_custom = generate_image(
            txt="CUSTOM SIZE",
            header_file=self.header_file,
            footer_file=self.footer_file,
            font_file=self.font_file,
            width=2000,
            height=1000
        )
        self.assertEqual(img_custom.size, (2000, 1000))

    def test_sequential_generation_and_duplex_printing(self):
        # Run main.py with --sequence "1-3" and --back-side footer
        cmd = [
            sys.executable, "main.py",
            "--sequence", "1-3",
            "--header", self.header_file,
            "--footer", self.footer_file,
            "--font", self.font_file,
            "--output", str(self.output_dir),
            "--combined-pdf",
            "--create-pdf",
            "--back-side", self.footer_file # Use footer image as mock back-side
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, msg=f"CLI with Sequence & Duplex failed:\n{result.stderr}")

        # Check sequential files are created without trailing underscores
        self.assertTrue((self.output_dir / "1.png").is_file())
        self.assertTrue((self.output_dir / "2.png").is_file())
        self.assertTrue((self.output_dir / "3.png").is_file())

        # Check that individual duplex PDFs are generated and contain exactly 2 pages (Front and Back)
        pdf_1_path = self.output_dir / "1.pdf"
        self.assertTrue(pdf_1_path.is_file())
        
        # Count pages using standard PDF structure binary search (zero dependencies)
        with open(pdf_1_path, "rb") as f:
            content = f.read()
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            self.assertEqual(page_count, 2, "Individual duplex PDF must contain exactly 2 pages.")

        # Check that combined PDF has exactly 6 pages (3 front, 3 back, alternating)
        combined_pdf_path = self.output_dir / "combined_bibs.pdf"
        self.assertTrue(combined_pdf_path.is_file())
        
        with open(combined_pdf_path, "rb") as f:
            content = f.read()
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            self.assertEqual(page_count, 6, "Combined duplex PDF must contain exactly 6 pages (3 front, 3 back).")

if __name__ == "__main__":
    unittest.main()
