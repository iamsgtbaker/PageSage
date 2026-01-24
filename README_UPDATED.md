# Book Index Manager - Updated

A comprehensive offline application for creating and managing book indexes with both command-line and web interfaces.

## New Features ✨

### Edit/Update References
- **Edit individual references** if you make a mistake when entering
- **Web interface**: Click the ✏️ icon next to any reference to edit it
- **CLI**: Use the `update` command to change references

### PDF Export (4-Column Landscape)
- **Professional PDF output** in landscape orientation
- **4-column layout** for compact printing
- **Bold section headings** for each letter
- **Clean, readable formatting**

## Features

- **Offline Operation**: Works completely offline using SQLite database
- **Dual Interface**: Command-line tool and web interface
- **Edit Functionality**: Update references when you make mistakes
- **Smart Reference Handling**: Automatically manages duplicates and groups references by term
- **Multiple Export Formats**: LaTeX, PDF (4-column landscape), Plain Text, and Markdown
- **Letter-Grouped Display**: Organizes entries alphabetically with letter headings
- **Search Functionality**: Quick search through index terms
- **Simple Reference Format**: Uses `b:p` for single pages and `b:p-p` for page ranges

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   This installs Flask (for web interface) and reportlab (for PDF export).

2. **That's it!** The SQLite database will be created automatically on first use.

## Usage

### Command-Line Interface

#### Add an Entry

```bash
# Add a single page reference
python index_cli.py add "machine learning" 1:42

# Add a page range reference
python index_cli.py add "neural networks" 2:15-18
```

#### Update a Reference (NEW!)

```bash
# Fix a mistake in a reference
python index_cli.py update "machine learning" 1:42 1:45

# Update a page range
python index_cli.py update "neural networks" 2:15-18 2:16-20
```

#### List All Entries

```bash
python index_cli.py list
```

#### Search for Entries

```bash
python index_cli.py search "learning"
```

#### Delete Entries

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

# Export to PDF format (4-column landscape) - NEW!
python index_cli.py export -f pdf -o index.pdf

# Export to plain text
python index_cli.py export -f plain -o index.txt

# Export to Markdown
python index_cli.py export -f markdown -o index.md
```

### Web Interface

The web interface now includes **inline editing** and **PDF export**!

1. **Start the web server:**
   ```bash
   python web_app.py
   ```

2. **Open your browser to:**
   ```
   http://127.0.0.1:5000
   ```

3. **New features in the web interface:**
   - **✏️ Edit button** next to each reference - click to update
   - **🗑️ Delete button** to remove individual references
   - **Delete All button** to remove all references for a term
   - **PDF Export button** to download 4-column landscape PDF
   - Real-time validation and error handling
   - Modal dialog for editing references

## Reference Format

The application uses a simple format for book and page references:

- **Single page**: `b:p` (e.g., `1:42` = book 1, page 42)
- **Page range**: `b:p-p` (e.g., `2:15-18` = book 2, pages 15-18)

Where:
- `b` = book number (integer)
- `p` = page number (integer)

## Export Formats

### LaTeX Format

Produces output styled for LaTeX documents:

```latex
\begin{theindex}

  \indexspace
  \textbf{A}

  \item artificial intelligence, 1:10, 1:25-28, 2:5

\end{theindex}
```

### PDF Format (NEW! 4-Column Landscape)

Produces a professional PDF with:
- **Landscape orientation** (11" x 8.5")
- **4 columns** for space-efficient layout
- **Bold letter headings** (larger font, blue color)
- **Compact formatting** suitable for printing
- **Professional appearance** using ReportLab

Perfect for:
- Printing and binding with your book
- Professional publications
- Compact reference materials

### Plain Text Format

Clean, readable plain text with letter headings.

### Markdown Format

GitHub-flavored Markdown with proper formatting.

## Editing Workflow

### Web Interface Editing

1. Find the entry you want to edit
2. Click the **✏️** (edit) icon next to the reference
3. A modal dialog appears with the current reference
4. Enter the new reference value
5. Click **Update**

### Command-Line Editing

```bash
# If you entered the wrong page number
python index_cli.py update "algorithm" 1:42 1:45

# If you need to change a range
python index_cli.py update "recursion" 3:1-8 3:2-10
```

## Examples

### Creating and Editing an Index

```bash
# Add entries
python index_cli.py add "algorithms" 1:15
python index_cli.py add "algorithms" 1:45-52

# Oops, made a mistake! Fix it
python index_cli.py update "algorithms" 1:15 1:16

# Add more entries
python index_cli.py add "binary search" 1:23-25
python index_cli.py add "data structures" 1:30

# Export to PDF
python index_cli.py export -f pdf -o my_index.pdf
```

### Web Interface Workflow

1. Start the web server: `python web_app.py`
2. Open browser to http://127.0.0.1:5000
3. Add entries using the form
4. Click ✏️ to edit any reference you mistyped
5. Click 📕 "Export as PDF" for a professional 4-column PDF
6. Download and print!

## Database Structure

The application uses SQLite with two main tables:

### Terms Table
- `id`: Primary key
- `term`: Index term (unique, case-insensitive)
- `created_at`: Timestamp

### Page References Table
- `id`: Primary key
- `term_id`: Foreign key to terms
- `book_number`: Book number
- `page_start`: Starting page
- `page_end`: Ending page (NULL for single pages)
- `created_at`: Timestamp

The schema ensures:
- No duplicate terms (case-insensitive)
- No duplicate references for the same term
- Orphaned terms are automatically cleaned up when references are deleted
- References can be updated individually

## Tips and Best Practices

1. **Use the Edit Feature**: Don't delete and re-add if you make a typo - just edit!

2. **PDF Export**: The 4-column landscape PDF is perfect for printing. It fits a lot of entries on one page.

3. **Batch Updates**: If you need to change many references, consider using the CLI with a script.

4. **Backup**: The SQLite database file (`book_index.db`) is your only data store. Back it up regularly!

5. **Multiple Projects**: Use separate database files (`-d` flag) for different books.

## Troubleshooting

### PDF export fails
- Make sure reportlab is installed: `pip install reportlab`
- Check the error message in the terminal

### Can't edit in web interface
- Make sure you have the latest versions of all files
- Check browser console for JavaScript errors
- Try refreshing the page

### "Entry not found" when updating
- The term and old reference must match exactly
- References are case-sensitive: `1:42` is different from `1:42-43`

## Requirements

- Python 3.7+
- Flask 3.0.0 (for web interface)
- reportlab 4.0.7+ (for PDF export)

## License

This is free and unencumbered software released into the public domain.
