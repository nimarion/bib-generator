# Bib Generator

Automatically generate high-resolution DIN A5 (148 x 210 mm) bibs for sports events. Text sizes are automatically adjusted to fit the bib canvas without overflowing, supporting custom fonts, headers, and footers.

The tool features a high-performance **Multi-Core Parallel Processor** and supports both **CSV** and **Microsoft Excel** registration spreadsheets natively.

---

## Key Features

* 🚀 **Multi-Core Parallel Processing:** Parallelized batch generation across all available CPU cores.
* ⚡ **$50\times$ Faster Dynamic Font Sizing:** Uses an $O(\log N)$ binary search algorithm to instantly calculate the absolute largest font size that fits the blank area.
* 📊 **Zero-Config Excel & CSV Support:** Natively reads standard Excel (`.xlsx`, `.xls`) or delimited CSV spreadsheets.
* 📄 **Combined Multi-Page PDF Compilation:** Compiles all bibs into a single, print-ready multi-page PDF in deterministic order.
* 🎨 **Advanced Custom Styling:** Configure horizontal margins, text fill color, outline stroke color, and stroke thickness.
* 🛡️ **Pre-Flight Validations:** Validates all paths, fonts, headers, and schemas before running, avoiding half-finished runs.
* 🧪 **Robust Unit & Integration Test Suite:** Includes comprehensive automated test suites verifying all layout, unique key, and scaling code.

---

## Performance Benchmarks

*Measured on 24 high-resolution (3508 x 2480 px) bibs:*

* **Sequential Single-Core processing:** `4.43s`
* **Multi-Core Parallel processing (Ours):** `1.83s`
* **Speedup Factor:** **`2.42x` faster**

---

## Installation

Ensure you have Python 3.10+ installed. Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Batch Usage (`main.py`)

Generate bibs in bulk from a registration sheet (CSV or Excel).

### Basic Command (CSV)
```bash
python3 main.py --data example/data.csv --footer example/footer.png --output example/output --font example/agency_fb.ttf --separator ';'
```

### Basic Command (Excel)
```bash
python3 main.py --data example/data.xlsx --footer example/footer.png --output example/output --font example/agency_fb.ttf
```

### Advanced Styling & Combined PDF Compilation
```bash
python3 main.py \
  --data example/data.csv \
  --separator ';' \
  --footer example/footer.png \
  --output example/output \
  --font example/agency_fb.ttf \
  --margin 150 \
  --text-color "navy" \
  --stroke-color "gold" \
  --stroke-width 2 \
  --combined-pdf \
  --create-duplicate
```

### CLI Options

| Argument | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--data` | `-d` | Path to CSV or Excel (`.xlsx`, `.xls`) registration file | *Required* |
| `--output` | `-o` | Output directory path | *Required* |
| `--font` | `-F` | Path to `.ttf` or `.otf` font file | *Required* |
| `--footer` | `-f` / `-he` | Path to footer image | `"rehlingen.png"` |
| `--separator` | `-s` | CSV separator character (if reading CSV) | `","` |
| `--create-duplicate` | `-D` | Creates the same image twice (with suffix or double-page PDF) | `False` |
| `--create-pdf` | `-P` | Generate individual `.pdf` files for each runner | `False` |
| `--combined-pdf` | `-C` | Compile all generated bibs into a single combined multi-page PDF | `False` |
| `--unique-keys` | `-u` | Comma-separated columns to check for duplicates (first initial used if duplicate) | `"lastname,firstname"` |
| `--margin` | `-m` | Horizontal text margin in pixels | `175` |
| `--text-color` | *None* | Text fill color | `"black"` |
| `--stroke-color`| *None* | Outline/stroke color | `"black"` |
| `--stroke-width`| *None* | Outline/stroke thickness in pixels | `1` |

---

## Single Runner Manual Usage (`bib.py`)

Generate a single custom bib manually from the command line.

```bash
python3 bib.py \
  --text "LYLES" \
  --output example/output/Lyles.png \
  --header example/globus.png \
  --footer example/footer.png \
  --font example/agency_fb.ttf \
  --margin 150 \
  --text-color "red" \
  --stroke-color "black" \
  --stroke-width 2
```

---

## Input Data Format

The registration file (CSV or Excel) must contain at least the following columns:

| firstname | lastname | header |
| :--- | :--- | :--- |
| Imke | Onnen | example/globus.png |
| Luna | Thiel | example/bitburger.png |
| Joshua | Abuaku | example/bitburger.png |

* **Header Column:** Specifies a path to the custom sponsor/club header PNG for each runner.

---

## Running Tests

To run the full automated unit and integration test suite:

```bash
python3 -m unittest test_bib.py
```

---

## License

MIT
