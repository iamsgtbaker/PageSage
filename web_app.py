"""
Web interface for Book Index application
"""
from flask import Flask, render_template, request, jsonify, send_file
from database import IndexDatabase
from formatter import IndexFormatter
from pathlib import Path
import tempfile

app = Flask(__name__)
db = IndexDatabase()
formatter = IndexFormatter()

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all entries"""
    entries = db.get_all_entries()
    return jsonify({
        'entries': [{'term': term, 'references': refs} for term, refs in entries]
    })

@app.route('/api/entries/recent', methods=['GET'])
def get_recent_entries():
    """Get most recent entries"""
    limit = request.args.get('limit', 5, type=int)
    entries = db.get_recent_entries(limit)
    return jsonify({
        'entries': [{'term': term, 'reference': ref, 'id': ref_id} for term, ref, ref_id in entries]
    })

@app.route('/api/add', methods=['POST'])
def add_entry():
    """Add a new entry"""
    data = request.json
    term = data.get('term', '').strip()
    reference = data.get('reference', '').strip()
    notes = data.get('notes', '').strip()

    if not term or not reference:
        return jsonify({'error': 'Term and reference are required'}), 400

    try:
        added = db.add_entry(term, reference)

        # Update notes if provided
        notes_added = False
        if notes:
            db.update_notes(term, notes)
            notes_added = True

        if added:
            # Build message based on what was added
            if notes_added:
                message = f"Added reference and note for '{term}' → {reference}"
            else:
                message = f"Added reference '{term}' → {reference}"
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': 'Duplicate entry (already exists)'}), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/search', methods=['GET'])
def search_entries():
    """Search for entries"""
    pattern = request.args.get('q', '')
    if not pattern:
        return jsonify({'entries': []})
    
    entries = db.search_terms(pattern)
    return jsonify({
        'entries': [{'term': term, 'references': refs} for term, refs in entries]
    })

@app.route('/api/delete', methods=['POST'])
def delete_entry():
    """Delete an entry"""
    data = request.json
    term = data.get('term', '').strip()
    reference = data.get('reference', '').strip() if data.get('reference') else None
    
    if not term:
        return jsonify({'error': 'Term is required'}), 400
    
    try:
        deleted = db.delete_entry(term, reference)
        if deleted:
            if reference:
                msg = f"Deleted '{term}' → {reference}"
            else:
                msg = f"Deleted all references for '{term}'"
            return jsonify({'success': True, 'message': msg})
        else:
            return jsonify({'error': 'Entry not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/update', methods=['POST'])
def update_entry():
    """Update a reference"""
    data = request.json
    term = data.get('term', '').strip()
    old_term = data.get('old_term', '').strip()
    old_reference = data.get('old_reference', '').strip()
    new_reference = data.get('new_reference', '').strip()

    # If old_term not provided, assume term hasn't changed
    if not old_term:
        old_term = term

    if not term or not old_reference or not new_reference:
        return jsonify({'error': 'Term, old reference, and new reference are required'}), 400

    try:
        # If term has changed, delete old reference and add new one
        if old_term.lower() != term.lower():
            # Delete the old reference from the old term
            deleted = db.delete_entry(old_term, old_reference)
            if not deleted:
                return jsonify({'error': 'Old reference not found'}), 404

            # Add the new reference to the new term
            added = db.add_entry(term, new_reference)
            message = f"Moved '{old_term}' → '{term}': {old_reference} → {new_reference}"
        else:
            # Term hasn't changed, just update the reference
            updated = db.update_reference(term, old_reference, new_reference)
            if not updated:
                return jsonify({'error': 'Reference not found'}), 404
            message = f"Updated '{term}': {old_reference} → {new_reference}"

        return jsonify({'success': True, 'message': message})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/import', methods=['POST'])
def import_csv():
    """Import entries from CSV data"""
    data = request.json
    csv_data = data.get('csv_data', '').strip()

    if not csv_data:
        return jsonify({'error': 'No CSV data provided'}), 400

    lines = csv_data.split('\n')
    imported = 0
    skipped = 0
    errors = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # Parse CSV line (simple comma split)
        parts = line.split(',')
        if len(parts) < 2:
            errors.append(f"Line {line_num}: Invalid format (expected: term,reference1,reference2,...)")
            continue

        term = parts[0].strip()
        references = [ref.strip() for ref in parts[1:]]

        if not term:
            errors.append(f"Line {line_num}: Missing term")
            continue

        if not any(references):
            errors.append(f"Line {line_num}: Missing references")
            continue

        # Process each reference for this term
        for ref in references:
            if not ref:
                continue

            try:
                added = db.add_entry(term, ref)
                if added:
                    imported += 1
                else:
                    skipped += 1
            except ValueError as e:
                errors.append(f"Line {line_num} (ref: {ref}): {str(e)}")

    return jsonify({
        'success': True,
        'message': f'Import complete: {imported} imported, {skipped} skipped (duplicates), {len(errors)} errors',
        'imported': imported,
        'skipped': skipped,
        'errors': errors
    })

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes"""
    notes = db.get_all_notes()
    return jsonify({
        'notes': [{'term': term, 'notes': note} for term, note in notes]
    })

@app.route('/api/notes/update', methods=['POST'])
def update_notes():
    """Update notes for a term"""
    data = request.json
    term = data.get('term', '').strip()
    notes = data.get('notes', '').strip()

    if not term:
        return jsonify({'error': 'Term is required'}), 400

    try:
        db.update_notes(term, notes)
        return jsonify({'success': True, 'message': f"Updated notes for '{term}'"})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/notes/delete', methods=['POST'])
def delete_notes():
    """Delete notes for a term"""
    data = request.json
    term = data.get('term', '').strip()

    if not term:
        return jsonify({'error': 'Term is required'}), 400

    try:
        deleted = db.delete_notes(term)
        if deleted:
            return jsonify({'success': True, 'message': f"Deleted notes for '{term}'"})
        else:
            return jsonify({'error': 'Notes not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/notes/export/<format_type>')
def export_notes(format_type):
    """Export notes in specified format"""
    notes = db.get_all_notes()

    if format_type == 'txt':
        content = formatter.format_notes_text(notes)
        filename = 'notes.txt'
        mimetype = 'text/plain'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.txt', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'csv':
        content = formatter.format_notes_csv(notes)
        filename = 'notes.csv'
        mimetype = 'text/csv'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.csv', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'pdf':
        filename = 'notes.pdf'
        mimetype = 'application/pdf'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        success = formatter.format_notes_pdf(notes, temp_file.name)
        if not success:
            return jsonify({'error': 'PDF generation failed. Install reportlab: pip install reportlab'}), 500
    else:
        return jsonify({'error': 'Invalid format type'}), 400

    return send_file(temp_file.name,
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename)

@app.route('/api/export/<format_type>')
def export_index(format_type):
    """Export index in specified format"""
    entries = db.get_all_entries()
    
    if format_type == 'latex':
        content = formatter.format_latex_style(entries)
        filename = 'index.tex'
        mimetype = 'text/plain'
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                               suffix='.tex', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'markdown':
        content = formatter.format_markdown(entries)
        filename = 'index.md'
        mimetype = 'text/markdown'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                               suffix='.md', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'pdf':
        filename = 'index.pdf'
        mimetype = 'application/pdf'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        success = formatter.format_pdf(entries, temp_file.name)
        if not success:
            return jsonify({'error': 'PDF generation failed. Install reportlab: pip install reportlab'}), 500
    else:  # plain
        content = formatter.format_plain_text(entries)
        filename = 'index.txt'
        mimetype = 'text/plain'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                               suffix='.txt', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    
    return send_file(temp_file.name, 
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    index_name = db.get_setting('index_name') or 'Book Index'
    index_year = db.get_setting('index_year') or ''
    index_version = db.get_setting('index_version') or ''
    return jsonify({
        'index_name': index_name,
        'index_year': index_year,
        'index_version': index_version
    })

@app.route('/api/settings/index-name', methods=['POST'])
def set_index_name():
    """Set index settings (name, year, version)"""
    data = request.json
    name = data.get('name', '').strip()
    year = data.get('year', '').strip()
    version = data.get('version', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    try:
        db.set_setting('index_name', name)
        if year:
            db.set_setting('index_year', year)
        if version:
            db.set_setting('index_version', version)
        return jsonify({'success': True, 'message': 'Index settings saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/settings/backup', methods=['GET'])
def backup_database():
    """Download the SQLite database file"""
    db_path = db.db_path
    index_name = db.get_setting('index_name') or 'book_index'
    # Sanitize filename
    safe_name = "".join(c for c in index_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_name = safe_name.replace(' ', '_')
    filename = f"{safe_name}.db"

    return send_file(db_path,
                    mimetype='application/x-sqlite3',
                    as_attachment=True,
                    download_name=filename)

@app.route('/api/settings/clear', methods=['POST'])
def clear_database():
    """Clear all data (create new index)"""
    try:
        db.clear_all_data()
        return jsonify({'success': True, 'message': 'All data cleared. New index created.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books"""
    books = db.get_all_books()
    return jsonify({
        'books': [{'book_number': num, 'book_name': name, 'page_count': pages}
                  for num, name, pages in books]
    })

@app.route('/api/books/add', methods=['POST'])
def add_book():
    """Add a new book"""
    data = request.json
    book_number = data.get('book_number', '').strip()
    book_name = data.get('book_name', '').strip()
    page_count = data.get('page_count', 0)

    if not book_number or not book_name:
        return jsonify({'error': 'Book number and name are required'}), 400

    try:
        page_count = int(page_count) if page_count else 0
    except ValueError:
        return jsonify({'error': 'Page count must be a number'}), 400

    try:
        added = db.add_book(book_number, book_name, page_count)
        if added:
            return jsonify({'success': True, 'message': f'Book {book_number} added'})
        else:
            return jsonify({'error': 'Book number already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/update', methods=['POST'])
def update_book():
    """Update a book"""
    data = request.json
    old_number = data.get('old_number', '').strip()
    book_number = data.get('book_number', '').strip()
    book_name = data.get('book_name', '').strip()
    page_count = data.get('page_count', 0)

    if not old_number or not book_number or not book_name:
        return jsonify({'error': 'All fields are required'}), 400

    try:
        page_count = int(page_count) if page_count else 0
    except ValueError:
        return jsonify({'error': 'Page count must be a number'}), 400

    try:
        updated = db.update_book(old_number, book_number, book_name, page_count)
        if updated:
            return jsonify({'success': True, 'message': f'Book {book_number} updated'})
        else:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/reference-count/<book_number>', methods=['GET'])
def get_book_reference_count(book_number):
    """Get count of references and exclusions for a book"""
    try:
        ref_count, exclusion_count = db.get_book_reference_count(book_number)
        return jsonify({
            'book_number': book_number,
            'reference_count': ref_count,
            'exclusion_count': exclusion_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/delete', methods=['POST'])
def delete_book():
    """Delete a book and all associated references and exclusions"""
    data = request.json
    book_number = data.get('book_number', '').strip()

    if not book_number:
        return jsonify({'error': 'Book number is required'}), 400

    try:
        deleted = db.delete_book(book_number)
        if deleted:
            return jsonify({'success': True, 'message': f'Book {book_number} and all associated data deleted'})
        else:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/gap-analysis', methods=['GET'])
def gap_analysis():
    """Perform gap analysis on all books"""
    try:
        results = db.get_gap_analysis()
        return jsonify({
            'results': [
                {
                    'book_number': num,
                    'book_name': name,
                    'page_count': pages,
                    'gaps': gap_ranges,
                    'gap_count': len(gap_ranges),
                    'excluded': excluded_ranges,
                    'term_count': term_count
                }
                for num, name, pages, gap_ranges, excluded_ranges, term_count in results
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/gap-exclusions/add', methods=['POST'])
def add_gap_exclusion():
    """Add a gap exclusion"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    book_number = data.get('book_number', '').strip()
    page_range = data.get('page_range', '').strip()

    if not book_number or not page_range:
        return jsonify({'error': 'Book number and page range are required'}), 400

    try:
        # Parse page range (e.g., "10" or "10-15")
        if '-' in page_range:
            parts = page_range.split('-')
            page_start = int(parts[0])
            page_end = int(parts[1])
        else:
            page_start = int(page_range)
            page_end = page_start

        added = db.add_gap_exclusion(book_number, page_start, page_end)
        if added:
            return jsonify({'success': True, 'message': f'Excluded pages {page_range} from gap analysis'})
        else:
            return jsonify({'error': 'Exclusion already exists'}), 409
    except ValueError as e:
        return jsonify({'error': f'Invalid page range: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/gap-exclusions/remove', methods=['POST'])
def remove_gap_exclusion():
    """Remove a gap exclusion"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    book_number = data.get('book_number', '').strip()
    page_range = data.get('page_range', '').strip()

    if not book_number or not page_range:
        return jsonify({'error': 'Book number and page range are required'}), 400

    try:
        # Parse page range
        if '-' in page_range:
            parts = page_range.split('-')
            page_start = int(parts[0])
            page_end = int(parts[1])
        else:
            page_start = int(page_range)
            page_end = page_start

        deleted = db.remove_gap_exclusion(book_number, page_start, page_end)
        if deleted:
            return jsonify({'success': True, 'message': f'Re-included pages {page_range} in gap analysis'})
        else:
            return jsonify({'error': 'Exclusion not found'}), 404
    except ValueError as e:
        return jsonify({'error': f'Invalid page range: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("=" * 60)
    print("Book Index Web Interface")
    print("=" * 60)
    print("\nStarting server...")
    print("Open your browser to: http://127.0.0.1:5000")
    print("  Alternative: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
