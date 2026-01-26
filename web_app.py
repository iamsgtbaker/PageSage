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

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Initialize database manager
db_manager = DatabaseManager()
formatter = IndexFormatter()


def get_current_db() -> IndexDatabase:
    """Get the active database for the current session"""
    db_name = session.get('active_database', None)

    if not db_name:
        # First run: check for legacy database
        legacy_path = Path('book_index.db')
        if legacy_path.exists():
            # Migrate legacy database
            migrate_legacy_database()
            db_name = session['active_database']
        else:
            # Create default database
            db_name = 'index_Book_Index.db'
            default_path = db_manager.databases_dir / db_name
            if not default_path.exists():
                # Create new default database
                db = IndexDatabase(str(default_path))
                db.set_setting('index_name', 'Book Index')
            session['active_database'] = db_name

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
        # Fall back to default
        session['active_database'] = 'index_Book_Index.db'

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
            'message': f'Database archived successfully',
            'switched_to': databases[0]['index_name'],
            'new_db_name': databases[0]['db_name']
        })
    else:
        # No databases left, create a default one
        default_db_name = 'index_Book_Index.db'
        default_path = db_manager.databases_dir / default_db_name
        new_db = IndexDatabase(str(default_path))
        new_db.set_setting('index_name', 'Book Index')
        session['active_database'] = default_db_name

        return jsonify({
            'success': True,
            'message': f'Database archived successfully. Created new default database.',
            'switched_to': 'Book Index',
            'new_db_name': default_db_name
        })


@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all entries"""
    db = get_current_db()
    entries = db.get_all_entries()
    return jsonify({
        'entries': [{'term': term, 'references': refs} for term, refs in entries]
    })

@app.route('/api/entries/recent', methods=['GET'])
def get_recent_entries():
    """Get most recent entries"""
    db = get_current_db()
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

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all notes"""
    db = get_current_db()
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

    # Get index name for filename
    index_name = db.get_setting('index_name') or 'Book Index'
    sanitized_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

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
        success = formatter.format_notes_pdf(notes, temp_file.name)
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

    # Gather index metadata
    index_name = db.get_setting('index_name') or 'Book Index'
    color_scheme = db.get_setting('color_scheme') or '#f2849e'
    books = db.get_all_books()
    custom_properties = db.get_all_custom_properties()

    metadata = {
        'index_name': index_name,
        'color_scheme': color_scheme,
        'books': [{'book_number': b[0], 'book_name': b[1], 'page_count': b[2]} for b in books],
        'custom_properties': [{'name': p[1], 'value': p[2]} for p in custom_properties]
    }

    # Create filename from index name and timestamp
    sanitized_name = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

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
    index_name = db.get_setting('index_name') or 'Book Index'
    color_scheme = db.get_setting('color_scheme') or '#f2849e'
    return jsonify({
        'index_name': index_name,
        'color_scheme': color_scheme
    })

@app.route('/api/settings/index-name', methods=['POST'])
def set_index_name():
    """Set index name"""
    db = get_current_db()
    data = request.json
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    try:
        db.set_setting('index_name', name)
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
