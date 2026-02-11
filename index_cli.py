#!/usr/bin/env python3
"""
Page Sage - Command Line Interface

A tool for creating and managing book indexes offline.
"""
import argparse
import sys
from pathlib import Path

from database import IndexDatabase
from formatter import IndexFormatter

def add_command(args):
    """Add a new index entry"""
    db = IndexDatabase(args.database)
    
    try:
        added = db.add_entry(args.term, args.reference)
        if added:
            print(f"✓ Added: '{args.term}' → {args.reference}")
        else:
            print(f"⚠ Duplicate entry (already exists): '{args.term}' → {args.reference}")
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def list_command(args):
    """List all index entries"""
    db = IndexDatabase(args.database)
    entries = db.get_all_entries()
    
    if not entries:
        print("No entries in index.")
        return
    
    current_letter = None
    for term, references in entries:
        first_letter = term[0].upper()
        if first_letter != current_letter:
            if current_letter is not None:
                print()
            print(f"\n{first_letter}")
            print("-" * 40)
            current_letter = first_letter
        
        ref_str = ", ".join(references)
        print(f"  {term}: {ref_str}")
    
    print(f"\nTotal: {len(entries)} entries")

def search_command(args):
    """Search for index entries"""
    db = IndexDatabase(args.database)
    entries = db.search_terms(args.pattern)
    
    if not entries:
        print(f"No entries found matching '{args.pattern}'")
        return
    
    print(f"Found {len(entries)} entries matching '{args.pattern}':\n")
    
    for term, references in entries:
        ref_str = ", ".join(references)
        print(f"  {term}: {ref_str}")

def delete_command(args):
    """Delete an index entry"""
    db = IndexDatabase(args.database)
    
    try:
        deleted = db.delete_entry(args.term, args.reference)
        if deleted:
            if args.reference:
                print(f"✓ Deleted reference: '{args.term}' → {args.reference}")
            else:
                print(f"✓ Deleted all references for: '{args.term}'")
        else:
            print(f"⚠ Entry not found: '{args.term}'")
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def update_command(args):
    """Update an index entry reference"""
    db = IndexDatabase(args.database)
    
    try:
        updated = db.update_reference(args.term, args.old_reference, args.new_reference)
        if updated:
            print(f"✓ Updated: '{args.term}' → {args.old_reference} changed to {args.new_reference}")
        else:
            print(f"⚠ Entry not found: '{args.term}' → {args.old_reference}")
    except ValueError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def export_command(args):
    """Export index to file"""
    db = IndexDatabase(args.database)
    formatter = IndexFormatter()
    
    entries = db.get_all_entries()
    
    if not entries:
        print("⚠ Warning: Index is empty", file=sys.stderr)
    
    # Choose format
    if args.format == 'latex':
        content = formatter.format_latex_style(entries, args.title)
        # Write to file
        try:
            Path(args.output).write_text(content, encoding='utf-8')
            print(f"✓ Index exported to: {args.output}")
            print(f"  Format: {args.format}")
            print(f"  Entries: {len(entries)}")
        except IOError as e:
            print(f"✗ Error writing file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.format == 'markdown':
        content = formatter.format_markdown(entries, args.title)
        try:
            Path(args.output).write_text(content, encoding='utf-8')
            print(f"✓ Index exported to: {args.output}")
            print(f"  Format: {args.format}")
            print(f"  Entries: {len(entries)}")
        except IOError as e:
            print(f"✗ Error writing file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.format == 'pdf':
        try:
            success = formatter.format_pdf(entries, args.output, args.title)
            if success:
                print(f"✓ Index exported to: {args.output}")
                print(f"  Format: {args.format}")
                print(f"  Entries: {len(entries)}")
            else:
                print(f"✗ Error: PDF export failed. Make sure reportlab is installed:", file=sys.stderr)
                print(f"  pip install reportlab", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"✗ Error creating PDF: {e}", file=sys.stderr)
            sys.exit(1)
    else:  # plain
        content = formatter.format_plain_text(entries, args.title)
        try:
            Path(args.output).write_text(content, encoding='utf-8')
            print(f"✓ Index exported to: {args.output}")
            print(f"  Format: {args.format}")
            print(f"  Entries: {len(entries)}")
        except IOError as e:
            print(f"✗ Error writing file: {e}", file=sys.stderr)
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Book Index - Manage and create book indexes offline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a single page reference
  %(prog)s add "machine learning" 1:42
  
  # Add a page range reference
  %(prog)s add "neural networks" 2:15-18
  
  # List all entries
  %(prog)s list
  
  # Search for entries
  %(prog)s search "learning"
  
  # Delete a specific reference
  %(prog)s delete "old term" 1:10
  
  # Delete all references for a term
  %(prog)s delete "old term"
  
  # Update a reference
  %(prog)s update "machine learning" 1:42 1:45
  
  # Export to LaTeX format
  %(prog)s export -f latex -o index.tex
  
  # Export to PDF format (4-column landscape)
  %(prog)s export -f pdf -o index.pdf
  
  # Export to plain text
  %(prog)s export -f plain -o index.txt
        """
    )
    
    parser.add_argument('-d', '--database', 
                       default='book_index.db',
                       help='Database file path (default: book_index.db)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add an index entry')
    add_parser.add_argument('term', help='Index term')
    add_parser.add_argument('reference', 
                           help='Reference (format: b:p or b:p-p)')
    add_parser.set_defaults(func=add_command)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all entries')
    list_parser.set_defaults(func=list_command)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for entries')
    search_parser.add_argument('pattern', help='Search pattern')
    search_parser.set_defaults(func=search_command)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an entry')
    delete_parser.add_argument('term', help='Index term to delete')
    delete_parser.add_argument('reference', nargs='?',
                              help='Specific reference to delete (optional)')
    delete_parser.set_defaults(func=delete_command)
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a reference')
    update_parser.add_argument('term', help='Index term to update')
    update_parser.add_argument('old_reference', help='Current reference')
    update_parser.add_argument('new_reference', help='New reference')
    update_parser.set_defaults(func=update_command)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export index to file')
    export_parser.add_argument('-o', '--output', 
                              default='index.txt',
                              help='Output file (default: index.txt)')
    export_parser.add_argument('-f', '--format', 
                              choices=['latex', 'plain', 'markdown', 'pdf'],
                              default='latex',
                              help='Output format (default: latex)')
    export_parser.add_argument('-t', '--title',
                              default='Index',
                              help='Index title (default: Index)')
    export_parser.set_defaults(func=export_command)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
