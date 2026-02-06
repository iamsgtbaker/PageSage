"""
Database management for book indexing application
"""
import sqlite3
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Required tables and their columns for database validation
REQUIRED_TABLES = {
    'terms': ['id', 'term', 'notes', 'created_at'],
    'page_references': ['id', 'term_id', 'book_number', 'page_start', 'page_end', 'created_at'],
    'books': ['id', 'book_number', 'book_name', 'page_count', 'created_at'],
    'settings': ['key', 'value'],
    'custom_properties': ['id', 'property_name', 'property_value', 'display_order', 'created_at'],
    'book_custom_properties': ['id', 'book_number', 'property_name', 'property_value', 'display_order', 'created_at'],
    'gap_exclusions': ['id', 'book_number', 'page_start', 'page_end', 'created_at']
}

def sanitize_db_name(index_name: str) -> str:
    """Convert index name to safe filename: 'My Index' -> 'index_My_Index.db'"""
    safe = re.sub(r'[^\w\s-]', '', index_name).strip().replace(' ', '_')
    return f"index_{safe}.db"


class DatabaseManager:
    """Manages multiple database instances"""

    def __init__(self, databases_dir="databases"):
        self.databases_dir = Path(databases_dir)
        self.databases_dir.mkdir(exist_ok=True)
        self.cache = {}  # Cache for loaded database instances

    def list_databases(self) -> List[Dict[str, str]]:
        """Discover all .db files and extract their index names"""
        databases = []

        for db_file in self.databases_dir.glob('*.db'):
            try:
                # Try to extract index name from database
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM settings WHERE key = 'index_name'")
                result = cursor.fetchone()
                conn.close()

                index_name = result[0] if result else db_file.stem
                databases.append({
                    'db_name': db_file.name,
                    'index_name': index_name
                })
            except:
                # If can't read index name, use filename
                databases.append({
                    'db_name': db_file.name,
                    'index_name': db_file.stem
                })

        return sorted(databases, key=lambda x: x['index_name'])

    def validate_database(self, db_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate database has required schema
        Returns: (is_valid, index_name, error_message)
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

            # Check required tables
            missing_tables = set(REQUIRED_TABLES.keys()) - tables
            if missing_tables:
                conn.close()
                error = f"Database missing required tables: {', '.join(sorted(missing_tables))}"
                return False, None, error

            # Check columns for each table
            for table, required_cols in REQUIRED_TABLES.items():
                cursor.execute(f"PRAGMA table_info({table})")
                existing_cols = {row[1] for row in cursor.fetchall()}
                missing_cols = set(required_cols) - existing_cols

                if missing_cols:
                    conn.close()
                    error = f"Table '{table}' missing columns: {', '.join(sorted(missing_cols))}"
                    return False, None, error

            # Extract index name
            cursor.execute("SELECT value FROM settings WHERE key = 'index_name'")
            result = cursor.fetchone()

            if not result:
                conn.close()
                return False, None, "Database settings missing index_name"

            index_name = result[0]
            conn.close()

            return True, index_name, None

        except sqlite3.DatabaseError as e:
            return False, None, f"Database file is corrupted or invalid: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"

    def get_database(self, db_name: str) -> 'IndexDatabase':
        """Load and return database instance (with caching)"""
        # Check cache first
        if db_name in self.cache:
            return self.cache[db_name]

        db_path = self.databases_dir / db_name

        # Create database instance
        db = IndexDatabase(str(db_path))
        self.cache[db_name] = db

        return db

    def rename_database(self, old_db_name: str, new_index_name: str) -> Tuple[bool, str, Optional[str]]:
        """
        Rename a database file to match the new index name.
        Returns: (success, new_db_name, error_message)
        """
        old_path = self.databases_dir / old_db_name
        if not old_path.exists():
            return False, old_db_name, "Database file not found"

        # Generate new filename from index name
        new_db_name = sanitize_db_name(new_index_name)
        new_path = self.databases_dir / new_db_name

        # If the filename hasn't changed, nothing to do
        if old_db_name == new_db_name:
            return True, old_db_name, None

        # Check if target filename already exists
        if new_path.exists():
            # Try adding a number suffix to make it unique
            base_name = new_db_name.replace('.db', '')
            counter = 1
            while new_path.exists() and counter < 100:
                new_db_name = f"{base_name}_{counter}.db"
                new_path = self.databases_dir / new_db_name
                counter += 1

            if new_path.exists():
                return False, old_db_name, "Could not find unique filename"

        # Remove from cache if present (to release any file handles)
        if old_db_name in self.cache:
            del self.cache[old_db_name]

        # Rename the file
        try:
            old_path.rename(new_path)
        except OSError as e:
            return False, old_db_name, f"Failed to rename file: {str(e)}"

        return True, new_db_name, None

    def import_database(self, uploaded_file, filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        Import uploaded .db file
        Returns: (success, db_name, error_message)
        """
        # Save to temporary location
        temp_path = self.databases_dir / f"temp_{filename}"

        try:
            uploaded_file.save(str(temp_path))

            # Validate database
            is_valid, index_name, error = self.validate_database(str(temp_path))

            if not is_valid:
                temp_path.unlink()  # Delete temp file
                return False, None, error

            # Generate final filename
            db_name = sanitize_db_name(index_name)
            final_path = self.databases_dir / db_name

            # Check if database already exists, add suffix if needed
            counter = 2
            while final_path.exists():
                base_name = sanitize_db_name(index_name).replace('.db', '')
                db_name = f"{base_name}_{counter}.db"
                final_path = self.databases_dir / db_name
                counter += 1

            # Move temp file to final location
            shutil.move(str(temp_path), str(final_path))

            return True, db_name, None

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False, None, f"Error importing database: {str(e)}"

    def archive_database(self, db_name: str) -> Tuple[bool, Optional[str]]:
        """
        Archive a database by moving it to the archive subfolder
        Returns: (success, error_message)
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = self.databases_dir / 'archive'
            archive_dir.mkdir(exist_ok=True)

            # Source and destination paths
            source_path = self.databases_dir / db_name
            dest_path = archive_dir / db_name

            # Check if source exists
            if not source_path.exists():
                return False, f"Database {db_name} not found"

            # Handle duplicate names in archive
            counter = 2
            while dest_path.exists():
                base_name = db_name.replace('.db', '')
                archived_name = f"{base_name}_archived_{counter}.db"
                dest_path = archive_dir / archived_name
                counter += 1

            # Move database to archive
            shutil.move(str(source_path), str(dest_path))

            # Remove from cache if present
            if db_name in self.cache:
                del self.cache[db_name]

            return True, None

        except Exception as e:
            return False, f"Error archiving database: {str(e)}"


class IndexDatabase:
    def __init__(self, db_path: str = "book_index.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create terms table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add notes column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(terms)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'notes' not in columns:
                cursor.execute('ALTER TABLE terms ADD COLUMN notes TEXT DEFAULT ""')

            # Add AI enrichment columns if they don't exist
            if 'ai_description' not in columns:
                cursor.execute('ALTER TABLE terms ADD COLUMN ai_description TEXT')
            if 'is_tool' not in columns:
                cursor.execute('ALTER TABLE terms ADD COLUMN is_tool INTEGER')
            if 'ai_enriched_at' not in columns:
                cursor.execute('ALTER TABLE terms ADD COLUMN ai_enriched_at TIMESTAMP')

            # Create references table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term_id INTEGER NOT NULL,
                    book_number INTEGER NOT NULL,
                    page_start INTEGER NOT NULL,
                    page_end INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (term_id) REFERENCES terms(id),
                    UNIQUE(term_id, book_number, page_start, page_end)
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_term_lookup
                ON terms(term COLLATE NOCASE)
            ''')

            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Set default index name if not exists
            cursor.execute('SELECT value FROM settings WHERE key = ?', ('index_name',))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?)',
                             ('index_name', 'Book Index'))

            # Create books table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_number TEXT NOT NULL UNIQUE,
                    book_name TEXT NOT NULL,
                    page_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create gap_exclusions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gap_exclusions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_number TEXT NOT NULL,
                    page_start INTEGER NOT NULL,
                    page_end INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(book_number, page_start, page_end)
                )
            ''')

            # Create custom_properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_name TEXT NOT NULL,
                    property_value TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create book_custom_properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book_custom_properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_number INTEGER NOT NULL,
                    property_name TEXT NOT NULL,
                    property_value TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_number) REFERENCES books(book_number)
                )
            ''')

            conn.commit()
    
    def parse_reference(self, ref_str: str) -> Tuple[int, int, Optional[int]]:
        """
        Parse reference string in format b:p or b:p-p
        Returns (book_number, page_start, page_end)
        """
        pattern = r'^(\d+):(\d+)(?:-(\d+))?$'
        match = re.match(pattern, ref_str.strip())
        
        if not match:
            raise ValueError(f"Invalid reference format: {ref_str}. Use b:p or b:p-p")
        
        book = int(match.group(1))
        page_start = int(match.group(2))
        page_end = int(match.group(3)) if match.group(3) else None
        
        if page_end and page_end < page_start:
            raise ValueError(f"End page {page_end} cannot be less than start page {page_start}")
        
        return book, page_start, page_end
    
    def add_entry(self, term: str, reference: str) -> bool:
        """
        Add an index entry
        Returns True if added, False if duplicate
        """
        book, page_start, page_end = self.parse_reference(reference)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get or create term
            cursor.execute('SELECT id FROM terms WHERE term = ? COLLATE NOCASE', (term,))
            result = cursor.fetchone()

            if result:
                term_id = result[0]
            else:
                cursor.execute('INSERT INTO terms (term) VALUES (?)', (term,))
                term_id = cursor.lastrowid

            # Try to add reference
            try:
                cursor.execute('''
                    INSERT INTO page_references (term_id, book_number, page_start, page_end)
                    VALUES (?, ?, ?, ?)
                ''', (term_id, book, page_start, page_end))
                conn.commit()

                # Remove any gap exclusions that overlap with this reference
                if page_end:
                    # It's a range - remove exclusions for all pages in the range
                    for page in range(page_start, page_end + 1):
                        self.remove_exclusions_for_page(book, page)
                else:
                    # Single page
                    self.remove_exclusions_for_page(book, page_start)

                return True
            except sqlite3.IntegrityError:
                # Duplicate reference
                return False
    
    def get_all_entries(self) -> List[Tuple[str, List[str]]]:
        """
        Get all index entries grouped by term
        Returns list of (term, [references])
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT t.term, r.book_number, r.page_start, r.page_end
                FROM terms t
                LEFT JOIN page_references r ON t.id = r.term_id
                ORDER BY t.term COLLATE NOCASE, r.book_number, r.page_start
            ''')

            results = cursor.fetchall()

            # Group by term
            entries = {}
            for term, book, page_start, page_end in results:
                if term not in entries:
                    entries[term] = []

                if book is not None:  # Skip terms with no references
                    if page_end:
                        ref = f"{book}:{page_start}-{page_end}"
                    else:
                        ref = f"{book}:{page_start}"
                    entries[term].append(ref)

            # Remove terms with no references
            entries = {k: v for k, v in entries.items() if v}

            return sorted(entries.items(), key=lambda x: x[0].lower())

    def get_recent_entries(self, limit: int = 5) -> List[Tuple[str, str, int]]:
        """
        Get most recently added entries
        Returns list of (term, reference, id) tuples, ordered by most recent first
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT t.term, r.book_number, r.page_start, r.page_end, r.id
                FROM page_references r
                JOIN terms t ON t.id = r.term_id
                ORDER BY r.id DESC
                LIMIT ?
            ''', (limit,))

            results = cursor.fetchall()

            # Format as (term, reference, id)
            entries = []
            for term, book, page_start, page_end, ref_id in results:
                if page_end:
                    ref = f"{book}:{page_start}-{page_end}"
                else:
                    ref = f"{book}:{page_start}"
                entries.append((term, ref, ref_id))

            return entries
    
    def delete_entry(self, term: str, reference: Optional[str] = None) -> bool:
        """
        Delete an entry. If reference is None, delete all references for the term.
        Returns True if something was deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get term ID
            cursor.execute('SELECT id FROM terms WHERE term = ? COLLATE NOCASE', (term,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            term_id = result[0]
            
            if reference:
                # Delete specific reference
                book, page_start, page_end = self.parse_reference(reference)
                cursor.execute('''
                    DELETE FROM page_references 
                    WHERE term_id = ? AND book_number = ? 
                    AND page_start = ? AND (page_end = ? OR (page_end IS NULL AND ? IS NULL))
                ''', (term_id, book, page_start, page_end, page_end))
            else:
                # Delete all references for this term
                cursor.execute('DELETE FROM page_references WHERE term_id = ?', (term_id,))
            
            deleted = cursor.rowcount > 0
            
            # Clean up orphaned terms
            cursor.execute('''
                DELETE FROM terms 
                WHERE id NOT IN (SELECT DISTINCT term_id FROM page_references)
            ''')
            
            conn.commit()
            return deleted
    
    def update_reference(self, term: str, old_reference: str, new_reference: str) -> bool:
        """
        Update a specific reference for a term
        Returns True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get term ID
            cursor.execute('SELECT id FROM terms WHERE term = ? COLLATE NOCASE', (term,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            term_id = result[0]
            
            # Parse old reference
            old_book, old_page_start, old_page_end = self.parse_reference(old_reference)
            
            # Parse new reference
            new_book, new_page_start, new_page_end = self.parse_reference(new_reference)
            
            # Update the reference
            cursor.execute('''
                UPDATE page_references 
                SET book_number = ?, page_start = ?, page_end = ?
                WHERE term_id = ? AND book_number = ? 
                AND page_start = ? AND (page_end = ? OR (page_end IS NULL AND ? IS NULL))
            ''', (new_book, new_page_start, new_page_end, term_id, old_book, old_page_start, old_page_end, old_page_end))
            
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
    
    def search_terms(self, pattern: str) -> List[Tuple[str, List[str]]]:
        """Search for terms matching a pattern (case-insensitive)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT t.term, r.book_number, r.page_start, r.page_end
                FROM terms t
                LEFT JOIN page_references r ON t.id = r.term_id
                WHERE t.term LIKE ? COLLATE NOCASE
                ORDER BY t.term COLLATE NOCASE, r.book_number, r.page_start
            ''', (f'%{pattern}%',))
            
            results = cursor.fetchall()
            
            entries = {}
            for term, book, page_start, page_end in results:
                if term not in entries:
                    entries[term] = []
                
                if book is not None:
                    if page_end:
                        ref = f"{book}:{page_start}-{page_end}"
                    else:
                        ref = f"{book}:{page_start}"
                    entries[term].append(ref)
            
            entries = {k: v for k, v in entries.items() if v}
            return sorted(entries.items(), key=lambda x: x[0].lower())

    def update_notes(self, term: str, notes: str) -> bool:
        """
        Update notes for a term
        Returns True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get or create term
            cursor.execute('SELECT id FROM terms WHERE term = ? COLLATE NOCASE', (term,))
            result = cursor.fetchone()

            if result:
                # Update existing term's notes
                cursor.execute('UPDATE terms SET notes = ? WHERE id = ?', (notes, result[0]))
            else:
                # Create new term with notes
                cursor.execute('INSERT INTO terms (term, notes) VALUES (?, ?)', (term, notes))

            conn.commit()
            return True

    def get_all_notes(self) -> List[Tuple[str, str]]:
        """
        Get all terms with notes
        Returns list of (term, notes) tuples, excluding empty notes
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT term, notes
                FROM terms
                WHERE notes IS NOT NULL AND notes != ''
                ORDER BY term COLLATE NOCASE
            ''')

            return cursor.fetchall()

    def get_notes(self, term: str) -> Optional[str]:
        """
        Get notes for a specific term
        Returns notes string or None if term doesn't exist
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT notes FROM terms WHERE term = ? COLLATE NOCASE', (term,))
            result = cursor.fetchone()

            return result[0] if result else None

    def delete_notes(self, term: str) -> bool:
        """
        Delete notes for a term (sets to empty string)
        Returns True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('UPDATE terms SET notes = "" WHERE term = ? COLLATE NOCASE', (term,))
            updated = cursor.rowcount > 0
            conn.commit()

            # Clean up term if it has no references
            cursor.execute('''
                DELETE FROM terms
                WHERE term = ? COLLATE NOCASE
                AND notes = ""
                AND id NOT IN (SELECT DISTINCT term_id FROM page_references)
            ''', (term,))
            conn.commit()

            return updated

    def get_setting(self, key: str) -> Optional[str]:
        """
        Get a setting value by key
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else None

    def set_setting(self, key: str, value: str) -> bool:
        """
        Set a setting value
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
            ''', (key, value, value))
            conn.commit()
            return True

    def clear_all_data(self) -> bool:
        """
        Clear all entries and notes but keep settings and books
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM page_references')
            cursor.execute('DELETE FROM terms')
            conn.commit()
            return True

    def add_book(self, book_number: str, book_name: str, page_count: int) -> bool:
        """
        Add a new book
        Returns True if added, False if duplicate
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO books (book_number, book_name, page_count)
                    VALUES (?, ?, ?)
                ''', (book_number, book_name, page_count))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_all_books(self) -> List[Tuple[str, str, int]]:
        """
        Get all books
        Returns list of (book_number, book_name, page_count)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT book_number, book_name, page_count
                FROM books
                ORDER BY book_number
            ''')
            return cursor.fetchall()

    def update_book(self, old_number: str, book_number: str, book_name: str, page_count: int) -> bool:
        """
        Update a book
        Returns True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE books
                SET book_number = ?, book_name = ?, page_count = ?
                WHERE book_number = ?
            ''', (book_number, book_name, page_count, old_number))
            updated = cursor.rowcount > 0
            conn.commit()
            return updated

    def get_book_reference_count(self, book_number: str) -> Tuple[int, int]:
        """
        Get count of references and exclusions for a book
        Returns (reference_count, exclusion_count)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count page references
            cursor.execute('''
                SELECT COUNT(*) FROM page_references
                WHERE book_number = ?
            ''', (int(book_number),))
            ref_count = cursor.fetchone()[0]

            # Count gap exclusions
            cursor.execute('''
                SELECT COUNT(*) FROM gap_exclusions
                WHERE book_number = ?
            ''', (book_number,))
            exclusion_count = cursor.fetchone()[0]

            return (ref_count, exclusion_count)

    def delete_book(self, book_number: str) -> bool:
        """
        Delete a book and all associated references and exclusions
        Returns True if deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Delete all page references for this book
            cursor.execute('''
                DELETE FROM page_references
                WHERE book_number = ?
            ''', (int(book_number),))

            # Delete all gap exclusions for this book
            cursor.execute('''
                DELETE FROM gap_exclusions
                WHERE book_number = ?
            ''', (book_number,))

            # Clean up orphaned terms (terms with no references)
            cursor.execute('''
                DELETE FROM terms
                WHERE id NOT IN (SELECT DISTINCT term_id FROM page_references)
                AND (notes IS NULL OR notes = '')
            ''')

            # Delete the book itself
            cursor.execute('DELETE FROM books WHERE book_number = ?', (book_number,))
            deleted = cursor.rowcount > 0

            conn.commit()
            return deleted

    def get_gap_analysis(self) -> List[Tuple[str, str, int, List[str]]]:
        """
        Perform gap analysis for all books
        Returns list of (book_number, book_name, page_count, [gap_ranges], [excluded_ranges], term_count)
        """
        books = self.get_all_books()
        results = []

        for book_number, book_name, page_count in books:
            if not page_count or page_count <= 0:
                # Include book but with empty gap analysis data
                results.append((book_number, book_name, 0, [], [], 0))
                continue

            # Get all references for this book
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT r.page_start, r.page_end
                    FROM page_references r
                    JOIN terms t ON r.term_id = t.id
                    WHERE r.book_number = ?
                    ORDER BY r.page_start
                ''', (int(book_number),))

                references = cursor.fetchall()

                # Get count of distinct terms for this book
                cursor.execute('''
                    SELECT COUNT(DISTINCT t.term)
                    FROM page_references r
                    JOIN terms t ON r.term_id = t.id
                    WHERE r.book_number = ?
                ''', (int(book_number),))

                term_count = cursor.fetchone()[0]

            # Build set of all referenced pages
            referenced_pages = set()
            for page_start, page_end in references:
                if page_end:
                    # It's a range
                    for page in range(page_start, page_end + 1):
                        referenced_pages.add(page)
                else:
                    # Single page
                    referenced_pages.add(page_start)

            # Get excluded pages for this book
            exclusions = self.get_gap_exclusions(book_number)
            excluded_pages = set()
            for page_start, page_end in exclusions:
                for page in range(page_start, page_end + 1):
                    excluded_pages.add(page)

            # Find gaps (pages not referenced and not excluded)
            gaps = []
            for page in range(1, page_count + 1):
                if page not in referenced_pages and page not in excluded_pages:
                    gaps.append(page)

            # Consolidate consecutive gaps into ranges
            gap_ranges = []
            if gaps:
                range_start = gaps[0]
                range_end = gaps[0]

                for i in range(1, len(gaps)):
                    if gaps[i] == range_end + 1:
                        # Consecutive, extend the range
                        range_end = gaps[i]
                    else:
                        # Gap in sequence, save current range and start new one
                        if range_start == range_end:
                            gap_ranges.append(str(range_start))
                        else:
                            gap_ranges.append(f"{range_start}-{range_end}")
                        range_start = gaps[i]
                        range_end = gaps[i]

                # Add the last range
                if range_start == range_end:
                    gap_ranges.append(str(range_start))
                else:
                    gap_ranges.append(f"{range_start}-{range_end}")

            # Format excluded ranges for display
            excluded_ranges = []
            for page_start, page_end in exclusions:
                if page_start == page_end:
                    excluded_ranges.append(str(page_start))
                else:
                    excluded_ranges.append(f"{page_start}-{page_end}")

            results.append((book_number, book_name, page_count, gap_ranges, excluded_ranges, term_count))

        return results

    def add_gap_exclusion(self, book_number: str, page_start: int, page_end: int) -> bool:
        """
        Add a gap exclusion (pages to ignore in gap analysis)
        Returns True if added, False if duplicate
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO gap_exclusions (book_number, page_start, page_end)
                    VALUES (?, ?, ?)
                ''', (book_number, page_start, page_end))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def remove_gap_exclusion(self, book_number: str, page_start: int, page_end: int) -> bool:
        """
        Remove a gap exclusion
        Returns True if deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM gap_exclusions
                WHERE book_number = ? AND page_start = ? AND page_end = ?
            ''', (book_number, page_start, page_end))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def get_gap_exclusions(self, book_number: str) -> List[Tuple[int, int]]:
        """
        Get all gap exclusions for a book
        Returns list of (page_start, page_end) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT page_start, page_end
                FROM gap_exclusions
                WHERE book_number = ?
                ORDER BY page_start
            ''', (book_number,))
            return cursor.fetchall()

    def remove_exclusions_for_page(self, book_number: int, page: int) -> int:
        """
        Remove any exclusions that contain the given page
        Returns number of exclusions removed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM gap_exclusions
                WHERE book_number = ? AND page_start <= ? AND page_end >= ?
            ''', (str(book_number), page, page))
            removed = cursor.rowcount
            conn.commit()
            return removed

    def add_custom_property(self, property_name: str, property_value: str) -> int:
        """
        Add a new custom property
        Returns the ID of the added property
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get the next display order
            cursor.execute('SELECT COALESCE(MAX(display_order), -1) + 1 FROM custom_properties')
            next_order = cursor.fetchone()[0]

            cursor.execute('''
                INSERT INTO custom_properties (property_name, property_value, display_order)
                VALUES (?, ?, ?)
            ''', (property_name, property_value, next_order))
            conn.commit()
            return cursor.lastrowid

    def get_all_custom_properties(self) -> List[Tuple[int, str, str, int]]:
        """
        Get all custom properties ordered by display_order
        Returns list of (id, property_name, property_value, display_order) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, property_name, property_value, display_order
                FROM custom_properties
                ORDER BY display_order
            ''')
            return cursor.fetchall()

    def update_custom_property(self, property_id: int, property_name: str, property_value: str) -> bool:
        """
        Update an existing custom property
        Returns True if updated, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE custom_properties
                SET property_name = ?, property_value = ?
                WHERE id = ?
            ''', (property_name, property_value, property_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_custom_property(self, property_id: int) -> bool:
        """
        Delete a custom property
        Returns True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM custom_properties WHERE id = ?', (property_id,))
            conn.commit()
            return cursor.rowcount > 0

    def reorder_custom_properties(self, property_ids: List[int]) -> bool:
        """
        Reorder custom properties based on the provided list of IDs
        The order in the list determines the new display_order
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for order, property_id in enumerate(property_ids):
                cursor.execute('''
                    UPDATE custom_properties
                    SET display_order = ?
                    WHERE id = ?
                ''', (order, property_id))
            conn.commit()
            return True

    # Book Custom Properties Methods
    def add_book_custom_property(self, book_number: int, property_name: str, property_value: str) -> int:
        """
        Add a custom property for a specific book
        Returns the ID of the added property
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Get the next display order for this book
            cursor.execute(
                'SELECT COALESCE(MAX(display_order), -1) + 1 FROM book_custom_properties WHERE book_number = ?',
                (book_number,)
            )
            next_order = cursor.fetchone()[0]

            cursor.execute('''
                INSERT INTO book_custom_properties (book_number, property_name, property_value, display_order)
                VALUES (?, ?, ?, ?)
            ''', (book_number, property_name, property_value, next_order))
            conn.commit()
            return cursor.lastrowid

    def get_book_custom_properties(self, book_number: int) -> List[Tuple[int, str, str, int]]:
        """
        Get all custom properties for a specific book ordered by display_order
        Returns list of (id, property_name, property_value, display_order) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, property_name, property_value, display_order
                FROM book_custom_properties
                WHERE book_number = ?
                ORDER BY display_order
            ''', (book_number,))
            return cursor.fetchall()

    def update_book_custom_property(self, property_id: int, property_name: str, property_value: str) -> bool:
        """
        Update a book custom property
        Returns True if updated, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE book_custom_properties
                SET property_name = ?, property_value = ?
                WHERE id = ?
            ''', (property_name, property_value, property_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_book_custom_property(self, property_id: int) -> bool:
        """
        Delete a book custom property
        Returns True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM book_custom_properties WHERE id = ?', (property_id,))
            conn.commit()
            return cursor.rowcount > 0

    def reorder_book_custom_properties(self, book_number: int, property_ids: List[int]) -> bool:
        """
        Reorder custom properties for a book based on the provided list of IDs
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for order, property_id in enumerate(property_ids):
                cursor.execute('''
                    UPDATE book_custom_properties
                    SET display_order = ?
                    WHERE id = ? AND book_number = ?
                ''', (order, property_id, book_number))
            conn.commit()
            return True

    def delete_book_custom_properties(self, book_number: int) -> bool:
        """
        Delete all custom properties for a book (used when deleting a book)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM book_custom_properties WHERE book_number = ?', (book_number,))
            conn.commit()
            return True

    def get_all_terms_for_enrichment(self) -> List[Tuple[int, str, Optional[str], Optional[int]]]:
        """
        Get all terms for AI enrichment
        Returns list of (id, term, ai_description, is_tool) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, term, ai_description, is_tool
                FROM terms
                ORDER BY term COLLATE NOCASE
            ''')
            return cursor.fetchall()

    def get_unenriched_terms(self) -> List[Tuple[int, str]]:
        """
        Get terms that haven't been enriched yet
        Returns list of (id, term) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, term
                FROM terms
                WHERE ai_description IS NULL
                ORDER BY term COLLATE NOCASE
            ''')
            return cursor.fetchall()

    def get_terms_without_notes(self) -> List[Tuple[int, str]]:
        """
        Get terms that don't have notes
        Returns list of (id, term) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, term
                FROM terms
                WHERE notes IS NULL OR notes = ''
                ORDER BY term COLLATE NOCASE
            ''')
            return cursor.fetchall()

    def update_term_ai_data(self, term_id: int, description: str, is_tool: bool) -> bool:
        """
        Update AI enrichment data for a term
        Returns True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE terms
                SET ai_description = ?, is_tool = ?, ai_enriched_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (description, 1 if is_tool else 0, term_id))
            conn.commit()
            return cursor.rowcount > 0

    def clear_term_ai_data(self, term_id: int) -> bool:
        """
        Clear AI enrichment data for a term
        Returns True if updated successfully
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE terms
                SET ai_description = NULL, is_tool = NULL, ai_enriched_at = NULL
                WHERE id = ?
            ''', (term_id,))
            conn.commit()
            return cursor.rowcount > 0
