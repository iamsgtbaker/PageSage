# Page Sage

A comprehensive offline application for creating and managing book indexes with both command-line and web interfaces. Built for GIAC/SANS certification exam preparation and anyone working with open-book exams.

## Features

### Core Features
- **Offline Operation**: Works completely offline using SQLite database
- **Dual Interface**: Command-line tool and modern web interface
- **Smart Reference Handling**: Automatically manages duplicates and groups references by term
- **Multiple Export Formats**: LaTeX, PDF, Plain Text, and Markdown
- **Letter-Grouped Display**: Organizes entries alphabetically with letter headings
- **Search Functionality**: Quick search through index terms and notes
- **Simple Reference Format**: Uses `b:p` for single pages and `b:p-p` for page ranges

### Study Tools
- **Study Mode**: Flashcard-based review with terms on front, notes/references on back
- **Keyboard Navigation**: Space to flip, N/P for next/previous cards
- **Notes Support**: Add study notes to any term, displayed in View References

### Book Management
- **Multiple Books**: Track page counts and custom metadata per book
- **Custom Metadata**: Add author, publisher, edition, or any custom properties
- **Drag-to-Reorder**: Organize metadata with intuitive drag and drop

### Organization
- **Multiple Indexes**: Create, switch between, backup, and archive separate indexes
- **Collapsible Sections**: Accordion-style organization in Tools and Settings
- **Customizable Appearance**: Choose from multiple accent colors

### Progress Tracking
- **Visual Progress Charts**: ApexCharts-powered dashboards showing indexing progress
  - Overall progress donut chart
  - Term density by book (terms per 100 pages)
  - Book completion comparison (stacked bar)
  - Gap distribution treemap
- **Summary Statistics**: Total books, pages, indexed pages, and completion percentage
- **Gap Analysis**: Identify unindexed pages with click-to-add functionality
- **Page Exclusions**: Mark front matter, blank pages, or irrelevant sections

### AI Integration (Optional)
- **AI Note Generation**: Automatically generate study notes using Claude or ChatGPT
- **API Key Management**: Secure storage of your AI provider credentials

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **That's it!** The SQLite database will be created automatically on first use.

## Usage

### Web Interface

The web interface provides a user-friendly way to manage your index:

1. **Start the web server:**
   ```bash
   python web_app.py
   ```

2. **Open your browser to:**
   ```
   http://localhost:5000
   ```

3. **Keyboard Shortcuts:**
   | Key | Action |
   |-----|--------|
   | `1-6` | Navigate to tabs (Add Entry, View References, Progress, Books, Tools, Settings) |
   | `/` | Focus search or term input |
   | `Esc` | Close modals or menu |

4. **Study Mode Shortcuts:**
   | Key | Action |
   |-----|--------|
   | `Space` | Flip flashcard |
   | `N` | Next flashcard |
   | `P` | Previous flashcard |
   | `Esc` | End study session |

### Command-Line Interface

The CLI tool provides quick access to all indexing functions:

#### Add an Entry

```bash
# Add a single page reference
python index_cli.py add "machine learning" 1:42

# Add a page range reference
python index_cli.py add "neural networks" 2:15-18
```

#### List All Entries

```bash
python index_cli.py list
```

Output example:
```
A
----------------------------------------
  artificial intelligence: 1:10, 1:25-28, 2:5

B
----------------------------------------
  backpropagation: 2:45-47
  Bayesian inference: 3:12, 3:20

Total: 3 entries
```

#### Search for Entries

```bash
python index_cli.py search "learning"
```

#### Delete an Entry

```bash
# Delete a specific reference
python index_cli.py delete "old term" 1:10

# Delete all references for a term
python index_cli.py delete "old term"
```

#### Export the Index

```bash
# Export to LaTeX format (default)
python index_cli.py export -f latex -o index.tex

# Export to PDF
python index_cli.py export -f pdf -o index.pdf

# Export to plain text
python index_cli.py export -f plain -o index.txt

# Export to Markdown
python index_cli.py export -f markdown -o index.md
```

#### Using a Different Database

```bash
# All commands support the -d flag to specify a database file
python index_cli.py -d myproject.db add "term" 1:5
python index_cli.py -d myproject.db list
```

#### Help

```bash
# Get general help
python index_cli.py -h

# Get help for a specific command
python index_cli.py add -h
```

## Reference Format

The application uses a simple format for book and page references:

- **Single page**: `b:p` (e.g., `1:42` = book 1, page 42)
- **Page range**: `b:p-p` (e.g., `2:15-18` = book 2, pages 15-18)

Where:
- `b` = book number (integer)
- `p` = page number (integer)

## Export Formats

### LaTeX Format

Produces output styled for LaTeX documents with proper escaping of special characters.

### PDF Format

Direct PDF generation with professional formatting, ready to print.

### Plain Text Format

Clean, readable plain text with letter headings and timestamps.

### Markdown Format

GitHub-flavored Markdown for documentation or web publishing.

## Database Structure

The application uses SQLite with the following main tables:

### Terms Table
- `id`: Primary key
- `term`: Index term (unique, case-insensitive)
- `note`: Study notes for the term
- `created_at`: Timestamp

### References Table
- `id`: Primary key
- `term_id`: Foreign key to terms
- `book_number`: Book number
- `page_start`: Starting page
- `page_end`: Ending page (NULL for single pages)
- `created_at`: Timestamp

### Books Table
- `book_number`: Primary key
- `book_name`: Name/title of the book
- `page_count`: Total pages (for gap analysis)
- `created_at`: Timestamp

## File Structure

```
PageSage/
├── database.py          # Database operations
├── formatter.py         # Export formatting
├── index_cli.py         # Command-line interface
├── web_app.py           # Flask web application
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── QUICKSTART.md        # Quick reference guide
├── MARKETING.md         # Feature overview
├── templates/
│   └── index.html       # Web interface template
├── static/
│   ├── style.css        # Styling
│   ├── script.js        # JavaScript functionality
│   ├── logo-icon.jpg    # Application logo
│   └── favicon.ico      # Browser favicon
├── demo/
│   └── demo_index.db    # Demo database
└── databases/           # User databases (git-ignored)
```

## Tips and Best Practices

1. **Set Page Counts**: Add page counts to books to enable progress tracking and gap analysis.

2. **Use Notes**: Add study notes to terms for flashcard-based review in Study Mode.

3. **Track Progress**: Check the View Progress tab regularly to identify under-indexed books.

4. **Regular Backups**: Use Settings → Index Management → Backup to save your work.

5. **Multiple Databases**: Use separate database files for different courses or exams.

6. **Keyboard Shortcuts**: Use number keys 1-6 to quickly switch between tabs.

## Troubleshooting

### "Invalid reference format" error
- Make sure you're using the correct format: `b:p` or `b:p-p`
- Use only numbers for book and page values
- Don't include spaces

### Web interface won't start
- Check that Flask is installed: `pip install -r requirements.txt`
- Make sure port 5000 is not already in use
- Try a different port: edit `web_app.py` and change the port number

### Database locked error
- Close the web interface before using the CLI on the same database
- Or use a different database file with the `-d` flag

### Progress charts not showing
- Ensure page counts are set for books in the Books tab
- Check browser console for JavaScript errors

## Third-Party Libraries

This project uses the following open-source libraries:

- **[Flask](https://flask.palletsprojects.com/)** - MIT License
- **[ApexCharts](https://apexcharts.com/)** - ApexCharts Community License (free for individuals, non-profits, educators, and organizations with < $2M annual revenue). See [ApexCharts License](https://apexcharts.com/license/).

## License

This project is released under the **MIT License**.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Note**: ApexCharts (used for progress visualization) has its own license terms. See [ApexCharts License](https://apexcharts.com/license/) for details.

## Contributing

Suggestions and improvements welcome! This is a standalone offline tool designed for exam preparation and study.

## Created For

SANS/GIAC students, certification candidates, and anyone facing open-book exams with massive reference materials.
