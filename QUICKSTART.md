# Book Index Manager - Quick Start Guide

## Installation

1. **Extract the files** to a directory on your computer

2. **Install Flask** (required for the web interface):
   ```bash
   pip install -r requirements.txt
   ```

## Option 1: Command-Line Interface (Recommended for Quick Use)

### Basic Commands

```bash
# Add entries
python index_cli.py add "term name" 1:42
python index_cli.py add "term name" 2:15-18

# View all entries
python index_cli.py list

# Search for entries
python index_cli.py search "keyword"

# Export to LaTeX
python index_cli.py export -f latex -o my_index.tex

# Get help
python index_cli.py -h
```

### Quick Example

```bash
# Create some entries
python index_cli.py add "algorithms" 1:10
python index_cli.py add "algorithms" 1:25-30
python index_cli.py add "data structures" 2:5

# View them
python index_cli.py list

# Export
python index_cli.py export -o index.tex
```

## Option 2: Web Interface (Best for Regular Use)

1. **Start the web server:**
   ```bash
   python web_app.py
   ```

2. **Open your browser** to: `http://localhost:5000`

3. **Use the web interface** to:
   - Add new entries
   - Search existing entries
   - View all entries organized by letter
   - Export in multiple formats

## Reference Format

- Single page: `1:42` (book 1, page 42)
- Page range: `2:15-18` (book 2, pages 15 through 18)

## Try the Demo

Run the demo script to see sample data:

```bash
python demo.py
python index_cli.py -d demo_index.db list
```

## Key Features

✓ Works completely offline
✓ No internet connection required
✓ Automatic duplicate detection
✓ LaTeX-formatted output
✓ Search functionality
✓ Both CLI and web interfaces

## Need Help?

See README.md for complete documentation.
