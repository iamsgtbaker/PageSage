"""
Web interface for Book Index application
"""
from flask import Flask, render_template, request, jsonify, send_file, session
from database import IndexDatabase, DatabaseManager, sanitize_db_name
from formatter import IndexFormatter
from pathlib import Path
import tempfile
from datetime import datetime
import re
import os
import shutil
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Initialize database manager
db_manager = DatabaseManager()
formatter = IndexFormatter()


def get_current_db():
    """Get the active database for the current session. Returns None if no database exists."""
    db_name = session.get('active_database', None)

    # Check if the session's database actually exists
    if db_name:
        db_path = db_manager.databases_dir / db_name
        if not db_path.exists():
            # Session has stale reference - clear it
            db_name = None
            session.pop('active_database', None)

    if not db_name:
        # First run: check for legacy database
        legacy_path = Path('book_index.db')
        if legacy_path.exists():
            # Migrate legacy database
            migrate_legacy_database()
            db_name = session.get('active_database')
        else:
            # Check if any databases exist
            databases = db_manager.list_databases()
            if databases:
                # Use the first available database
                db_name = databases[0]['db_name']
                session['active_database'] = db_name
            else:
                # No databases exist - don't create one automatically
                return None

    if not db_name:
        return None

    return db_manager.get_database(db_name)


def migrate_legacy_database():
    """Migrate existing book_index.db to databases/ directory"""
    legacy_path = Path('book_index.db')
    if not legacy_path.exists():
        return

    try:
        # Read index name from legacy database
        legacy_db = IndexDatabase(str(legacy_path))
        index_name = legacy_db.get_setting('index_name') or 'Book Index'

        # Create new filename
        new_name = sanitize_db_name(index_name)
        new_path = db_manager.databases_dir / new_name

        # Copy database to new location
        shutil.copy2(str(legacy_path), str(new_path))

        # Rename legacy to .bak
        backup_path = legacy_path.with_suffix('.db.bak')
        if not backup_path.exists():
            legacy_path.rename(backup_path)

        # Set as active database
        session['active_database'] = new_name

        print(f"Migrated legacy database to {new_path}")
        print(f"Legacy database backed up to {backup_path}")
    except Exception as e:
        print(f"Error migrating legacy database: {e}")
        # Don't set any default - let user create via Get Started modal

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


@app.route('/prototype/progress')
def progress_prototype():
    """Progress charts prototype page"""
    return render_template('progress_prototype.html')


# Setup Check API Endpoint

@app.route('/api/needs-setup', methods=['GET'])
def needs_setup():
    """Check if the app needs initial setup (no databases exist)"""
    databases = db_manager.list_databases()
    return jsonify({
        'needs_setup': len(databases) == 0
    })


# Database Management API Endpoints

@app.route('/api/databases/list', methods=['GET'])
def list_databases():
    """List all available databases"""
    databases = db_manager.list_databases()
    active_db = session.get('active_database', None)
    return jsonify({
        'databases': databases,
        'active': active_db
    })


@app.route('/api/databases/switch', methods=['POST'])
def switch_database():
    """Switch active database"""
    data = request.json
    db_name = data.get('db_name')

    if not db_name:
        return jsonify({'error': 'Database name required'}), 400

    # Validate database exists
    db_path = db_manager.databases_dir / db_name
    if not db_path.exists():
        return jsonify({'error': 'Database not found'}), 404

    # Switch session database
    session['active_database'] = db_name

    # Get index name for response
    db = db_manager.get_database(db_name)
    index_name = db.get_setting('index_name') or 'Book Index'

    return jsonify({
        'success': True,
        'message': f'Switched to {index_name}',
        'index_name': index_name
    })


@app.route('/api/databases/import', methods=['POST'])
def import_database():
    """Import a .db file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if not file.filename.endswith('.db'):
        return jsonify({'error': 'File must be a .db file'}), 400

    success, db_name, error = db_manager.import_database(file, file.filename)

    if not success:
        return jsonify({'error': error}), 400

    return jsonify({
        'success': True,
        'db_name': db_name,
        'message': 'Database imported successfully'
    })


@app.route('/api/databases/create', methods=['POST'])
def create_database():
    """Create a new database"""
    data = request.json
    index_name = data.get('index_name', 'Book Index')

    db_name = sanitize_db_name(index_name)
    db_path = db_manager.databases_dir / db_name

    # Check if database already exists, add suffix if needed
    counter = 2
    while db_path.exists():
        base_name = sanitize_db_name(index_name).replace('.db', '')
        db_name = f"{base_name}_{counter}.db"
        db_path = db_manager.databases_dir / db_name
        counter += 1

    # Create new database
    new_db = IndexDatabase(str(db_path))
    new_db.set_setting('index_name', index_name)

    return jsonify({
        'success': True,
        'db_name': db_name,
        'message': f'Created new index: {index_name}'
    })


@app.route('/api/databases/load-demo', methods=['POST'])
def load_demo_database():
    """Load the demo database"""
    demo_path = Path('demo/demo_index.db')

    if not demo_path.exists():
        return jsonify({'error': 'Demo database not found'}), 404

    # Copy demo to databases folder with unique name
    db_name = 'index_CISSP_Study_Guide.db'
    db_path = db_manager.databases_dir / db_name

    # If demo already exists, add suffix
    counter = 2
    while db_path.exists():
        db_name = f'index_CISSP_Study_Guide_{counter}.db'
        db_path = db_manager.databases_dir / db_name
        counter += 1

    try:
        shutil.copy(str(demo_path), str(db_path))
        session['active_database'] = db_name

        return jsonify({
            'success': True,
            'db_name': db_name,
            'message': 'Demo index loaded successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/databases/archive', methods=['POST'])
def archive_database():
    """Archive the current database"""
    db_name = session.get('active_database')

    if not db_name:
        return jsonify({'error': 'No active database'}), 400

    # Archive the database
    success, error = db_manager.archive_database(db_name)

    if not success:
        return jsonify({'error': error}), 400

    # Clear session and switch to another database if available
    session.pop('active_database', None)

    # Get list of remaining databases
    databases = db_manager.list_databases()

    if databases:
        # Switch to first available database
        session['active_database'] = databases[0]['db_name']
        return jsonify({
            'success': True,
            'message': f'Index archived successfully',
            'switched_to': databases[0]['index_name'],
            'new_db_name': databases[0]['db_name']
        })
    else:
        # No databases left - don't create a default one
        return jsonify({
            'success': True,
            'message': f'Index archived successfully. Create a new index to continue.',
            'switched_to': None,
            'new_db_name': None,
            'needs_setup': True
        })


@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all entries"""
    db = get_current_db()
    if db is None:
        return jsonify({'entries': []})
    entries = db.get_all_entries()
    return jsonify({
        'entries': [{'term': term, 'references': refs} for term, refs in entries]
    })

@app.route('/api/entries/recent', methods=['GET'])
def get_recent_entries():
    """Get most recent entries"""
    db = get_current_db()
    if db is None:
        return jsonify({'entries': []})
    limit = request.args.get('limit', 5, type=int)
    entries = db.get_recent_entries(limit)
    return jsonify({
        'entries': [{'term': term, 'reference': ref, 'id': ref_id} for term, ref, ref_id in entries]
    })

@app.route('/api/add', methods=['POST'])
def add_entry():
    """Add a new entry"""
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
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

@app.route('/api/import/notes', methods=['POST'])
def import_notes():
    """Import notes from CSV data"""
    db = get_current_db()
    data = request.json
    csv_data = data.get('csv_data', '').strip()

    if not csv_data:
        return jsonify({'error': 'No CSV data provided'}), 400

    lines = csv_data.split('\n')
    imported = 0
    updated = 0
    errors = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # Parse CSV line - find first comma to split term from note
        # This allows notes to contain commas
        comma_idx = line.find(',')
        if comma_idx == -1:
            errors.append(f"Line {line_num}: Invalid format (expected: term,note)")
            continue

        term = line[:comma_idx].strip()
        note = line[comma_idx + 1:].strip()

        if not term:
            errors.append(f"Line {line_num}: Missing term")
            continue

        if not note:
            errors.append(f"Line {line_num}: Missing note")
            continue

        try:
            # Check if term exists
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, notes FROM terms WHERE term = ? COLLATE NOCASE', (term,))
                result = cursor.fetchone()

            if result:
                # Term exists - overwrite note
                db.update_notes(term, note)
                updated += 1
            else:
                # Term doesn't exist - create it with the note
                db.update_notes(term, note)
                imported += 1
        except Exception as e:
            errors.append(f"Line {line_num}: {str(e)}")

    return jsonify({
        'success': True,
        'message': f'Import complete: {imported} new terms, {updated} updated, {len(errors)} errors',
        'imported': imported,
        'skipped': updated,  # Using 'skipped' field to show updated count for compatibility
        'errors': errors
    })

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes"""
    db = get_current_db()
    if db is None:
        return jsonify({'notes': []})
    notes = db.get_all_notes()
    return jsonify({
        'notes': [{'term': term, 'notes': note} for term, note in notes]
    })

@app.route('/api/notes/update', methods=['POST'])
def update_notes():
    """Update notes for a term"""
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
    notes = db.get_all_notes()

    # Get book filter from query parameter
    book_filter = request.args.get('book', '')

    # Get index name for filename
    index_name = db.get_setting('index_name') or 'Book Index'
    color_scheme = db.get_setting('color_scheme') or '#87AE73'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Gather metadata for PDF export (same as index export)
    books = db.get_all_books()
    custom_properties = db.get_all_custom_properties()

    books_with_metadata = []
    for b in books:
        book_props = db.get_book_custom_properties(b[0])
        books_with_metadata.append({
            'book_number': b[0],
            'book_name': b[1],
            'page_count': b[2],
            'metadata': [{'name': p[1], 'value': p[2]} for p in book_props]
        })

    # If filtering by specific book, filter notes to only include terms with references from that book
    selected_book_number = None
    if book_filter:
        selected_book_number = int(book_filter)
        # Get all entries to check which terms have references in this book
        entries = db.get_all_entries()
        terms_in_book = set()
        for term, references in entries:
            for ref in references:
                if ref.startswith(f"{selected_book_number}:"):
                    terms_in_book.add(term.lower())
                    break

        # Filter notes to only include terms that have references in the selected book
        notes = [(term, note) for term, note in notes if term.lower() in terms_in_book]

        # Filter metadata to only show the selected book (compare as int)
        books_with_metadata = [b for b in books_with_metadata if int(b['book_number']) == selected_book_number]

    metadata = {
        'index_name': index_name,
        'color_scheme': color_scheme,
        'books': books_with_metadata,
        'custom_properties': [{'name': p[1], 'value': p[2]} for p in custom_properties],
        'single_book': bool(book_filter)
    }

    # Add book number to filename if filtering by specific book
    if selected_book_number:
        sanitized_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_') + f"_Book{selected_book_number}"
    else:
        sanitized_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')

    if format_type == 'txt':
        content = formatter.format_notes_text(notes)
        filename = f'{sanitized_name}_notes_{timestamp}.txt'
        mimetype = 'text/plain'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.txt', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'csv':
        content = formatter.format_notes_csv(notes)
        filename = f'{sanitized_name}_notes_{timestamp}.csv'
        mimetype = 'text/csv'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.csv', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'markdown':
        content = formatter.format_notes_markdown(notes)
        filename = f'{sanitized_name}_notes_{timestamp}.md'
        mimetype = 'text/markdown'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.md', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'latex':
        content = formatter.format_notes_latex(notes)
        filename = f'{sanitized_name}_notes_{timestamp}.tex'
        mimetype = 'text/plain'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.tex', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'pdf':
        filename = f'{sanitized_name}_notes_{timestamp}.pdf'
        mimetype = 'application/pdf'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        success = formatter.format_notes_pdf(notes, temp_file.name, metadata)
        if not success:
            return jsonify({'error': 'PDF generation failed. Install reportlab: pip install reportlab'}), 500
    elif format_type == 'excel':
        filename = f'{sanitized_name}_notes_{timestamp}.xlsx'
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        success = formatter.format_notes_excel(notes, temp_file.name)
        if not success:
            return jsonify({'error': 'Excel generation failed. Install openpyxl: pip install openpyxl'}), 500
    else:
        return jsonify({'error': 'Invalid format type'}), 400

    return send_file(temp_file.name,
                    mimetype=mimetype,
                    as_attachment=True,
                    download_name=filename)

@app.route('/api/export/<format_type>')
def export_index(format_type):
    """Export index in specified format"""
    db = get_current_db()
    entries = db.get_all_entries()

    # Get book filter from query parameter
    book_filter = request.args.get('book', '')

    # Gather index metadata
    index_name = db.get_setting('index_name') or 'Book Index'
    color_scheme = db.get_setting('color_scheme') or '#87AE73'
    books = db.get_all_books()
    custom_properties = db.get_all_custom_properties()

    books_with_metadata = []
    for b in books:
        book_props = db.get_book_custom_properties(b[0])
        books_with_metadata.append({
            'book_number': b[0],
            'book_name': b[1],
            'page_count': b[2],
            'metadata': [{'name': p[1], 'value': p[2]} for p in book_props]
        })

    # If filtering by specific book, filter entries and metadata
    selected_book_number = None
    if book_filter:
        selected_book_number = int(book_filter)
        # Filter entries to only include references from this book
        filtered_entries = []
        for term, references in entries:
            book_refs = []
            for ref in references:
                if ref.startswith(f"{selected_book_number}:"):
                    # Convert "book:page" to just "page" for single-book export
                    page_part = ref.split(':', 1)[1]
                    book_refs.append(page_part)
            if book_refs:
                filtered_entries.append((term, book_refs))
        entries = filtered_entries

        # Filter metadata to only show the selected book (compare as int)
        books_with_metadata = [b for b in books_with_metadata if int(b['book_number']) == selected_book_number]

    metadata = {
        'index_name': index_name,
        'color_scheme': color_scheme,
        'books': books_with_metadata,
        'custom_properties': [{'name': p[1], 'value': p[2]} for p in custom_properties],
        'single_book': bool(book_filter)
    }

    # Create filename from index name and timestamp
    base_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Add book number to filename if filtering by specific book
    if selected_book_number:
        sanitized_name = f"{base_name}_Book{selected_book_number}"
    else:
        sanitized_name = base_name

    if format_type == 'latex':
        content = formatter.format_latex_style(entries, metadata)
        filename = f'{sanitized_name}_{timestamp}.tex'
        mimetype = 'text/plain'
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.tex', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'markdown':
        content = formatter.format_markdown(entries, metadata)
        filename = f'{sanitized_name}_{timestamp}.md'
        mimetype = 'text/markdown'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.md', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'pdf':
        filename = f'{sanitized_name}_{timestamp}.pdf'
        mimetype = 'application/pdf'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        success = formatter.format_pdf(entries, temp_file.name, metadata)
        if not success:
            return jsonify({'error': 'PDF generation failed. Install reportlab: pip install reportlab'}), 500
    elif format_type == 'csv':
        content = formatter.format_csv(entries, metadata)
        filename = f'{sanitized_name}_{timestamp}.csv'
        mimetype = 'text/csv'
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False,
                                               suffix='.csv', encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
    elif format_type == 'excel':
        filename = f'{sanitized_name}_{timestamp}.xlsx'
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        success = formatter.format_excel(entries, temp_file.name, metadata)
        if not success:
            return jsonify({'error': 'Excel generation failed. Install openpyxl: pip install openpyxl'}), 500
    else:  # plain
        content = formatter.format_plain_text(entries, metadata)
        filename = f'{sanitized_name}_{timestamp}.txt'
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
    db = get_current_db()
    if db is None:
        # No database yet - return defaults
        return jsonify({
            'index_name': 'Book Index',
            'color_scheme': '#87AE73',
            'no_database': True
        })
    index_name = db.get_setting('index_name') or 'Book Index'
    color_scheme = db.get_setting('color_scheme') or '#87AE73'
    return jsonify({
        'index_name': index_name,
        'color_scheme': color_scheme
    })

@app.route('/api/settings/index-name', methods=['POST'])
def set_index_name():
    """Set index name and rename database file to match"""
    db = get_current_db()
    data = request.json
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    try:
        # Get current database filename
        old_db_name = session.get('active_database')

        # Update the index name in the database first
        db.set_setting('index_name', name)

        # Now rename the database file to match
        if old_db_name:
            success, new_db_name, error = db_manager.rename_database(old_db_name, name)

            if success and new_db_name != old_db_name:
                # Update session to point to new filename
                session['active_database'] = new_db_name
                return jsonify({
                    'success': True,
                    'message': 'Index name saved and file renamed',
                    'new_db_name': new_db_name
                })
            elif not success and error:
                # Name was saved but file rename failed - still a partial success
                return jsonify({
                    'success': True,
                    'message': f'Index name saved (file rename skipped: {error})',
                    'warning': error
                })

        return jsonify({'success': True, 'message': 'Index name saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/settings/color-scheme', methods=['POST'])
def set_color_scheme():
    """Set color scheme"""
    db = get_current_db()
    data = request.json
    color = data.get('color', '').strip()

    # Validate color format (hex color)
    if not color or not color.startswith('#') or len(color) != 7:
        return jsonify({'error': 'Invalid color format'}), 400

    try:
        db.set_setting('color_scheme', color)
        return jsonify({'success': True, 'message': 'Color scheme saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/settings/backup', methods=['GET'])
def backup_database():
    """Download the SQLite database file with timestamp"""
    db = get_current_db()
    db_path = db.db_path
    index_name = db.get_setting('index_name') or 'book_index'
    # Sanitize filename and add timestamp
    safe_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{safe_name}_{timestamp}.db"

    return send_file(db_path,
                    mimetype='application/x-sqlite3',
                    as_attachment=True,
                    download_name=filename)

@app.route('/api/settings/clear', methods=['POST'])
def clear_database():
    """Clear all data (create new index)"""
    db = get_current_db()
    try:
        db.clear_all_data()
        return jsonify({'success': True, 'message': 'All data cleared. New index created.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/custom-properties', methods=['GET'])
def get_custom_properties():
    """Get all custom properties"""
    db = get_current_db()
    if db is None:
        return jsonify({'properties': []})
    properties = db.get_all_custom_properties()
    return jsonify({
        'properties': [{
            'id': prop[0],
            'property_name': prop[1],
            'property_value': prop[2],
            'display_order': prop[3]
        } for prop in properties]
    })

@app.route('/api/custom-properties', methods=['POST'])
def add_custom_property():
    """Add a new custom property"""
    db = get_current_db()
    data = request.json
    property_name = data.get('property_name', '').strip()
    property_value = data.get('property_value', '').strip()

    if not property_name or not property_value:
        return jsonify({'error': 'Property name and value are required'}), 400

    try:
        property_id = db.add_custom_property(property_name, property_value)
        return jsonify({
            'success': True,
            'message': 'Property added',
            'id': property_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/custom-properties/<int:property_id>', methods=['PUT'])
def update_custom_property(property_id):
    """Update an existing custom property"""
    db = get_current_db()
    data = request.json
    property_name = data.get('property_name', '').strip()
    property_value = data.get('property_value', '').strip()

    if not property_name or not property_value:
        return jsonify({'error': 'Property name and value are required'}), 400

    try:
        success = db.update_custom_property(property_id, property_name, property_value)
        if success:
            return jsonify({'success': True, 'message': 'Property updated'})
        else:
            return jsonify({'error': 'Property not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/custom-properties/<int:property_id>', methods=['DELETE'])
def delete_custom_property(property_id):
    """Delete a custom property"""
    db = get_current_db()
    try:
        success = db.delete_custom_property(property_id)
        if success:
            return jsonify({'success': True, 'message': 'Property deleted'})
        else:
            return jsonify({'error': 'Property not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/custom-properties/reorder', methods=['POST'])
def reorder_custom_properties():
    """Reorder custom properties"""
    db = get_current_db()
    data = request.json
    property_ids = data.get('property_ids', [])

    if not property_ids:
        return jsonify({'error': 'Property IDs are required'}), 400

    try:
        db.reorder_custom_properties(property_ids)
        return jsonify({'success': True, 'message': 'Properties reordered'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books"""
    db = get_current_db()
    if db is None:
        return jsonify({'books': []})
    books = db.get_all_books()
    return jsonify({
        'books': [{'book_number': num, 'book_name': name, 'page_count': pages}
                  for num, name, pages in books]
    })

@app.route('/api/books/add', methods=['POST'])
def add_book():
    """Add a new book"""
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
    data = request.json
    book_number = data.get('book_number', '').strip()

    if not book_number:
        return jsonify({'error': 'Book number is required'}), 400

    try:
        # Delete book custom properties first
        db.delete_book_custom_properties(book_number)
        deleted = db.delete_book(book_number)
        if deleted:
            return jsonify({'success': True, 'message': f'Book {book_number} and all associated data deleted'})
        else:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Book Custom Properties endpoints
@app.route('/api/books/<book_number>/properties', methods=['GET'])
def get_book_properties(book_number):
    """Get all custom properties for a book"""
    db = get_current_db()
    try:
        properties = db.get_book_custom_properties(int(book_number))
        return jsonify({
            'properties': [
                {
                    'id': p[0],
                    'property_name': p[1],
                    'property_value': p[2],
                    'display_order': p[3]
                }
                for p in properties
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/<book_number>/properties', methods=['POST'])
def add_book_property(book_number):
    """Add a custom property for a book"""
    db = get_current_db()
    data = request.json
    property_name = data.get('property_name', '').strip()
    property_value = data.get('property_value', '').strip()

    if not property_name or not property_value:
        return jsonify({'error': 'Property name and value are required'}), 400

    try:
        property_id = db.add_book_custom_property(int(book_number), property_name, property_value)
        return jsonify({'success': True, 'id': property_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/properties/<int:property_id>', methods=['PUT'])
def update_book_property(property_id):
    """Update a book custom property"""
    db = get_current_db()
    data = request.json
    property_name = data.get('property_name', '').strip()
    property_value = data.get('property_value', '').strip()

    if not property_name or not property_value:
        return jsonify({'error': 'Property name and value are required'}), 400

    try:
        updated = db.update_book_custom_property(property_id, property_name, property_value)
        if updated:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Property not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/properties/<int:property_id>', methods=['DELETE'])
def delete_book_property(property_id):
    """Delete a book custom property"""
    db = get_current_db()
    try:
        deleted = db.delete_book_custom_property(property_id)
        if deleted:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Property not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/books/<book_number>/properties/reorder', methods=['POST'])
def reorder_book_properties(book_number):
    """Reorder custom properties for a book"""
    db = get_current_db()
    data = request.json
    property_ids = data.get('property_ids', [])

    try:
        db.reorder_book_custom_properties(int(book_number), property_ids)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/gap-analysis', methods=['GET'])
def gap_analysis():
    """Perform gap analysis on all books"""
    db = get_current_db()
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
    db = get_current_db()
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
    db = get_current_db()
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

# AI Term Enrichment endpoints
@app.route('/api/ai/settings', methods=['GET'])
def get_ai_settings():
    """Get AI settings"""
    db = get_current_db()
    if db is None:
        return jsonify({
            'enabled': False,
            'provider': '',
            'has_key': False
        })

    enabled = db.get_setting('ai_enabled') == 'true'
    provider = db.get_setting('ai_provider') or ''
    api_key = db.get_setting('ai_api_key')

    return jsonify({
        'enabled': enabled,
        'provider': provider,
        'has_key': bool(api_key)
    })

@app.route('/api/ai/settings', methods=['POST'])
def save_ai_settings():
    """Save AI settings"""
    db = get_current_db()
    if db is None:
        return jsonify({'error': 'No database selected'}), 400

    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    enabled = data.get('enabled', False)
    provider = data.get('provider', '')
    api_key = data.get('api_key')
    clear_key = data.get('clear_key', False)

    db.set_setting('ai_enabled', 'true' if enabled else 'false')
    db.set_setting('ai_provider', provider)

    # Clear API key if requested
    if clear_key:
        db.set_setting('ai_api_key', '')
    # Only update API key if provided
    elif api_key:
        db.set_setting('ai_api_key', api_key)

    return jsonify({
        'success': True,
        'message': 'AI settings saved'
    })

@app.route('/api/ai/validate-key', methods=['POST'])
def validate_ai_key():
    """Validate an AI API key by making a minimal API call"""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    provider = data.get('provider')
    api_key = data.get('api_key')

    if not provider:
        return jsonify({'error': 'No provider specified'}), 400
    if not api_key:
        return jsonify({'error': 'No API key provided'}), 400

    try:
        if provider == 'anthropic':
            try:
                import anthropic
            except ImportError:
                return jsonify({'error': 'anthropic package not installed'}), 400

            client = anthropic.Anthropic(api_key=api_key)
            # Make a minimal API call to validate the key
            message = client.messages.create(
                model="claude-haiku-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return jsonify({'valid': True, 'message': 'API key is valid'})

        elif provider == 'openai':
            try:
                import openai
            except ImportError:
                return jsonify({'error': 'openai package not installed'}), 400

            client = openai.OpenAI(api_key=api_key)
            # Make a minimal API call to validate the key
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return jsonify({'valid': True, 'message': 'API key is valid'})

        else:
            return jsonify({'error': f'Unknown provider: {provider}'}), 400

    except Exception as e:
        error_msg = str(e)
        # Check for common authentication errors
        if 'invalid' in error_msg.lower() or 'auth' in error_msg.lower() or 'key' in error_msg.lower():
            return jsonify({'valid': False, 'message': 'Invalid API key'})
        return jsonify({'valid': False, 'message': f'Validation failed: {error_msg}'})

@app.route('/api/ai/prompts', methods=['GET'])
def get_ai_prompts():
    """Get AI prompts configuration"""
    import json
    prompts_path = os.path.join(app.static_folder, 'ai_prompts.json')
    try:
        with open(prompts_path, 'r') as f:
            prompts_data = json.load(f)
        return jsonify(prompts_data)
    except FileNotFoundError:
        return jsonify({'error': 'Prompts file not found'}), 404
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 500

@app.route('/api/ai/terms', methods=['GET'])
def get_ai_terms():
    """Get terms for AI enrichment, optionally filtering for terms without notes"""
    db = get_current_db()
    without_notes = request.args.get('without_notes', 'false').lower() == 'true'

    if without_notes:
        terms = db.get_terms_without_notes()
        return jsonify({
            'terms': [
                {
                    'id': t[0],
                    'term': t[1]
                }
                for t in terms
            ]
        })
    else:
        terms = db.get_all_terms_for_enrichment()
        return jsonify({
            'terms': [
                {
                    'id': t[0],
                    'term': t[1],
                    'description': t[2],
                    'is_tool': t[3]
                }
                for t in terms
            ]
        })

@app.route('/api/ai/enrich', methods=['POST'])
def enrich_terms():
    """Enrich terms using AI API"""
    import json as json_module

    db = get_current_db()
    if db is None:
        return jsonify({'error': 'No database selected'}), 400

    # Get API settings from database
    provider = db.get_setting('ai_provider')
    api_key = db.get_setting('ai_api_key')

    if not provider:
        return jsonify({'error': 'No AI provider selected. Please select a provider in AI settings.'}), 400

    if not api_key:
        return jsonify({'error': 'API key not configured. Please save your API key in AI settings.'}), 400

    # Get terms without notes to enrich
    terms = db.get_terms_without_notes()

    if not terms:
        return jsonify({'message': 'No terms without notes to enrich', 'enriched': 0})

    # Load prompt configuration from JSON file
    prompts_path = os.path.join(app.static_folder, 'ai_prompts.json')
    try:
        with open(prompts_path, 'r') as f:
            prompts_config = json_module.load(f)
    except (FileNotFoundError, json_module.JSONDecodeError):
        return jsonify({'error': 'Could not load AI prompts configuration'}), 500

    if provider not in prompts_config.get('prompts', {}):
        return jsonify({'error': f'No prompt configured for provider: {provider}'}), 400

    provider_config = prompts_config['prompts'][provider]

    # Build prompt with term list
    term_prefix = prompts_config.get('term_prefix', '- ')
    term_separator = prompts_config.get('term_list_separator', '\n')
    term_list = term_separator.join(f"{term_prefix}{t[1]}" for t in terms)

    # Get index name for $course_title
    index_name = db.get_setting('index_name') or 'Untitled Index'

    # Build the full prompt with replacements
    prompt_template = provider_config.get('prompt', '')
    model_name = provider_config.get('model', '')
    prompt = prompt_template.replace('$course_title', index_name).replace('$model', model_name)
    prompt = prompt + '\n' + term_list

    try:
        if provider == 'anthropic':
            try:
                import anthropic
            except ImportError:
                return jsonify({'error': 'anthropic package not installed. Run: pip install anthropic'}), 400

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-20250514",  # Cost-effective model
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text

        elif provider == 'openai':
            try:
                import openai
            except ImportError:
                return jsonify({'error': 'openai package not installed. Run: pip install openai'}), 400

            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective model
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content

        else:
            return jsonify({'error': f'Unknown provider: {provider}'}), 400

        # Parse CSV response and update notes
        enriched_count = 0
        term_map = {t[1].lower(): t[0] for t in terms}

        # Parse CSV response
        import csv
        import io
        reader = csv.reader(io.StringIO(response_text))
        header_skipped = False

        for row in reader:
            if len(row) >= 2:
                # Skip header row
                if not header_skipped and row[0].lower() == 'term':
                    header_skipped = True
                    continue
                header_skipped = True

                term_name = row[0].strip()
                description = row[1].strip()

                # Find matching term and update notes
                term_id = term_map.get(term_name.lower())
                if term_id:
                    db.update_notes(term_name, description)
                    enriched_count += 1

        return jsonify({
            'success': True,
            'message': f'Enriched {enriched_count} terms with notes',
            'enriched': enriched_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/import', methods=['POST'])
def import_ai_data():
    """Import AI enrichment data from pasted text"""
    db = get_current_db()
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    response_text = data['text']

    # Get all terms for matching
    all_terms = db.get_all_terms_for_enrichment()
    term_map = {t[1].lower(): t[0] for t in all_terms}

    # Parse response
    enriched_count = 0
    blocks = response_text.split('---')
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        term_match = re.search(r'TERM:\s*(.+)', block, re.IGNORECASE)
        desc_match = re.search(r'DESCRIPTION:\s*(.+)', block, re.IGNORECASE)
        tool_match = re.search(r'TOOL:\s*(Yes|No)', block, re.IGNORECASE)

        if term_match and desc_match and tool_match:
            term_name = term_match.group(1).strip()
            description = desc_match.group(1).strip()
            is_tool = tool_match.group(1).lower() == 'yes'

            term_id = term_map.get(term_name.lower())
            if term_id:
                db.update_term_ai_data(term_id, description, is_tool)
                enriched_count += 1

    return jsonify({
        'success': True,
        'message': f'Imported {enriched_count} term descriptions',
        'enriched': enriched_count
    })

@app.route('/api/ai/export', methods=['GET'])
def export_ai_data():
    """Export AI enrichment data as CSV"""
    db = get_current_db()
    terms = db.get_all_terms_for_enrichment()

    # Build CSV content
    lines = ['Term,Description,Tool']
    for term_id, term, description, is_tool in terms:
        desc_escaped = (description or '').replace('"', '""')
        tool_str = 'Yes' if is_tool == 1 else ('No' if is_tool == 0 else '')
        lines.append(f'"{term}","{desc_escaped}","{tool_str}"')

    content = '\n'.join(lines)

    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = f.name

    return send_file(
        temp_path,
        as_attachment=True,
        download_name='term_descriptions.csv',
        mimetype='text/csv'
    )

@app.route('/api/ai/copy-prompt', methods=['GET'])
def get_copy_prompt():
    """Get terms formatted as a prompt for manual copy/paste workflow"""
    db = get_current_db()
    data = request.args
    unenriched_only = data.get('unenriched', 'false').lower() == 'true'

    if unenriched_only:
        terms = db.get_unenriched_terms()
        term_list = '\n'.join(f"- {t[1]}" for t in terms)
    else:
        terms = db.get_all_terms_for_enrichment()
        term_list = '\n'.join(f"- {t[1]}" for t in terms)

    prompt = f"""For each term below, provide:
1. A brief description (1-2 sentences) covering the concept or primary purpose
2. Whether it's a tool (Yes/No)

Terms:
{term_list}

Respond in this exact format for each term:
TERM: [term name]
DESCRIPTION: [brief description]
TOOL: [Yes/No]
---"""

    return jsonify({
        'prompt': prompt,
        'term_count': len(terms)
    })


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
