# Book Index Manager

A comprehensive offline application for creating and managing book indexes with both command-line and web interfaces.

## Features

- **Offline Operation**: Works completely offline using SQLite database
- **Dual Interface**: Command-line tool and web interface
- **Smart Reference Handling**: Automatically manages duplicates and groups references by term
- **Multiple Export Formats**: LaTeX, Plain Text, and Markdown
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

2. **That's it!** The SQLite database will be created automatically on first use.

## Usage

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

3. **Features available in the web interface:**
   - Add new index entries with validation
   - View all entries organized by letter
   - Search for specific terms
   - Delete entries
   - Export in multiple formats
   - Real-time feedback and error handling

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

  \indexspace
  \textbf{B}

  \item backpropagation, 2:45-47

\end{theindex}
```

This format:
- Uses `\begin{theindex}` and `\end{theindex}` environments
- Includes `\indexspace` for letter separation
- Bold letter headings with `\textbf{}`
- Automatically escapes LaTeX special characters

### Plain Text Format

Produces clean, readable plain text:

```
============================================================
                          Index
============================================================
Generated: 2025-01-13 14:30:00
============================================================

A
----------------------------------------
  artificial intelligence: 1:10, 1:25-28, 2:5

B
----------------------------------------
  backpropagation: 2:45-47

============================================================
Total entries: 2
============================================================
```

### Markdown Format

Produces GitHub-flavored Markdown:

```markdown
# Index

*Generated: 2025-01-13 14:30:00*

## A

- **artificial intelligence**: 1:10, 1:25-28, 2:5

## B

- **backpropagation**: 2:45-47

---
*Total entries: 2*
```

## Database Structure

The application uses SQLite with two main tables:

### Terms Table
- `id`: Primary key
- `term`: Index term (unique, case-insensitive)
- `created_at`: Timestamp

### References Table
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

## File Structure

```
book_index/
├── database.py          # Database operations
├── formatter.py         # Export formatting
├── index_cli.py         # Command-line interface
├── web_app.py          # Flask web application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── templates/
│   └── index.html      # Web interface template
├── static/
│   ├── style.css       # Styling
│   └── script.js       # JavaScript functionality
└── book_index.db       # SQLite database (created on first use)
```

## Examples

### Creating a Comprehensive Index

```bash
# Add entries for a multi-volume work
python index_cli.py add "algorithms" 1:15
python index_cli.py add "algorithms" 1:45-52
python index_cli.py add "algorithms" 2:8

python index_cli.py add "binary search" 1:23-25
python index_cli.py add "data structures" 1:30
python index_cli.py add "recursion" 2:10-15

# View the index
python index_cli.py list

# Export to LaTeX
python index_cli.py export -f latex -o my_index.tex
```

### Working with Multiple Projects

```bash
# Project 1: Computer Science textbook
python index_cli.py -d cs_book.db add "algorithms" 1:10
python index_cli.py -d cs_book.db export -o cs_index.tex

# Project 2: History book
python index_cli.py -d history.db add "World War II" 1:45
python index_cli.py -d history.db export -o history_index.tex
```

## Tips and Best Practices

1. **Consistent Capitalization**: The application is case-insensitive for terms but preserves the first entry's capitalization. Be consistent!

2. **Broad to Specific**: Use the search function to check if similar terms already exist before adding new ones.

3. **Regular Exports**: Export your index regularly to avoid data loss.

4. **Multiple Databases**: Use separate database files for different projects to keep indexes organized.

5. **Backup**: The SQLite database file (`book_index.db`) is your only data store. Back it up regularly!

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

## License

This is free and unencumbered software released into the public domain.

## Contributing

Suggestions and improvements welcome! This is a standalone offline tool, so it should work without internet connectivity.
