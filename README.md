# inmate-scraper

## Getting Started

### Prerequisites

- Python 3.x

### Installation

1. Create a virtual environment:
   ```sh
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Command Prompt:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - PowerShell:
     ```ps1
     .venv\Scripts\Activate.ps1
     ```

3. Install dependencies:
   ```sh
   pip install beautifulsoup4 mechanize
   ```

### Usage

Run the scraper:
```sh
python scrape_inmates.py
```

By default, running the script without arguments will perform all actions: scrape data, update the database, and generate a CSV file.

You can also run specific steps using flags:
```sh
python scrape_inmates.py --scrape --db --csv
```

Arguments:
- `--scrape`: Run the scraper to fetch data.
- `--db`: Update the SQLite database with the scraped data.
- `--csv`: Generate a CSV file from the database.