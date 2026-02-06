// Book Index Manager - JavaScript

let allEntries = [];
let allNotes = [];
let searchTimeout = null;
let notesSearchTimeout = null;
let selectedLetter = null;
let selectedNotesLetter = null;
let currentSearchQuery = '';
let autocompleteIndex = -1;
let lastAutocompleteTerm = '';  // Track last autocomplete-selected term
let lastUsedBook = '';
let selectedBookFilter = '';
let recentEntriesOffset = 0;
let recentEntriesLimit = 10;
let allRecentEntries = [];

// Helper function to normalize first letter
// Numbers and special characters become "#"
function normalizeFirstLetter(text) {
    if (!text || text.length === 0) return '#';

    const firstChar = text[0].toUpperCase();

    // Check if it's a letter A-Z
    if (firstChar >= 'A' && firstChar <= 'Z') {
        return firstChar;
    }

    // Everything else (numbers, special characters) becomes "#"
    return '#';
}

// Rotating tagline functionality
let taglines = ["Build your exam reference, fast"];
let currentTaglineIndex = 0;

async function loadTaglines() {
    try {
        const response = await fetch('/static/config.json');
        if (response.ok) {
            const config = await response.json();
            if (config.taglines && config.taglines.length > 0) {
                taglines = config.taglines;
            }
        }
    } catch (error) {
        console.error('Failed to load taglines config:', error);
    }
}

function startTaglineRotation() {
    setInterval(() => {
        currentTaglineIndex = (currentTaglineIndex + 1) % taglines.length;
        const taglineElement = document.getElementById('rotatingTagline');
        if (taglineElement) {
            taglineElement.style.opacity = '0';
            setTimeout(() => {
                taglineElement.textContent = taglines[currentTaglineIndex];
                taglineElement.style.opacity = '1';
            }, 1000);
        }
    }, 7000);
}

// Hamburger Menu Control
let menuLocked = false;

function menuLock() {
    if (menuLocked) return false;
    menuLocked = true;
    setTimeout(() => { menuLocked = false; }, 350);
    return true;
}

function menuHide() {
    if (menuLock()) {
        document.body.classList.remove('is-menu-visible');
    }
}

function menuToggle() {
    if (menuLock()) {
        document.body.classList.toggle('is-menu-visible');
    }
}

function menuNavigate(tabName) {
    menuHide();
    setTimeout(() => { switchTab(tabName); }, 350);
}

// Modal Functions
function showAboutModal() {
    menuHide();
    setTimeout(() => {
        document.getElementById('aboutModal').classList.add('show');
    }, 350);
}

function closeAboutModal() {
    document.getElementById('aboutModal').classList.remove('show');
}

function showHelpModal() {
    menuHide();
    setTimeout(() => {
        document.getElementById('helpModal').classList.add('show');
    }, 350);
}

function closeHelpModal() {
    document.getElementById('helpModal').classList.remove('show');
}

function showCliModal() {
    menuHide();
    setTimeout(() => {
        document.getElementById('cliModal').classList.add('show');
    }, 350);
}

function closeCliModal() {
    document.getElementById('cliModal').classList.remove('show');
}

function showCsvHelpModal() {
    document.getElementById('csvHelpModal').classList.add('show');
}

function closeCsvHelpModal() {
    document.getElementById('csvHelpModal').classList.remove('show');
}

function showAiHelpModal() {
    document.getElementById('aiHelpModal').classList.add('show');
}

function closeAiHelpModal() {
    document.getElementById('aiHelpModal').classList.remove('show');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadEntries();
    loadSettings();
    loadBookDropdowns();
    loadRecentEntries();
    restoreLastOpenedTool();
    restoreLastOpenedSetting();
    initStudyMode();

    // Setup form submission
    document.getElementById('addForm').addEventListener('submit', handleAddEntry);
    document.getElementById('editForm').addEventListener('submit', handleEditEntry);
    document.getElementById('importForm').addEventListener('submit', handleImportCSV);
    document.getElementById('importNotesForm').addEventListener('submit', handleImportNotes);
    document.getElementById('editNotesForm').addEventListener('submit', handleEditNotes);
    document.getElementById('editBookForm').addEventListener('submit', handleEditBook);
    document.getElementById('addBookModalForm').addEventListener('submit', handleAddBookModal);

    // Submit add entry form when Enter is pressed on page inputs
    const pageInput = document.getElementById('page');
    const pageEndInput = document.getElementById('pageEnd');

    pageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('addForm').dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    pageEndInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('addForm').dispatchEvent(new Event('submit', { cancelable: true }));
        }
    });

    // Database management forms
    const importDbForm = document.getElementById('importDatabaseForm');
    if (importDbForm) {
        importDbForm.addEventListener('submit', importDatabase);
    }

    const createDbForm = document.getElementById('createDatabaseForm');
    if (createDbForm) {
        createDbForm.addEventListener('submit', createNewDatabase);
    }

    // Get Started form
    const getStartedForm = document.getElementById('getStartedForm');
    if (getStartedForm) {
        getStartedForm.addEventListener('submit', handleGetStarted);
    }

    // Check if this is a new database that needs setup
    checkNeedsSetup();

    // Close database switcher when clicking outside
    document.addEventListener('click', function(event) {
        const switcher = document.getElementById('databaseSwitcher');
        const indexName = document.getElementById('indexName');

        if (switcher && indexName && !switcher.contains(event.target) && event.target !== indexName) {
            switcher.style.display = 'none';
        }
    });

    // Keyboard shortcut: "0" to toggle index switcher
    document.addEventListener('keydown', function(event) {
        // Ignore if typing in an input, textarea, or select
        const activeElement = document.activeElement;
        const isTyping = activeElement.tagName === 'INPUT' ||
                         activeElement.tagName === 'TEXTAREA' ||
                         activeElement.tagName === 'SELECT' ||
                         activeElement.isContentEditable;

        if (isTyping) return;

        // Check for "0" key
        if (event.key === '0') {
            event.preventDefault();
            showDatabaseSwitcher();
        }
    });

    // Setup search
    document.getElementById('searchInput').addEventListener('input', handleSearch);

    // Close modals on background click - setup all modals with their close functions
    const modalCloseHandlers = {
        'editModal': closeEditModal,
        'editNotesModal': closeEditNotesModal,
        'gapActionModal': closeGapActionModal,
        'reincludeModal': closeReincludeModal,
        'editBookModal': closeEditBookModal,
        'addBookModal': closeAddBookModal,
        'aboutModal': closeAboutModal,
        'helpModal': closeHelpModal,
        'cliModal': closeCliModal,
        'csvHelpModal': closeCsvHelpModal,
        'aiHelpModal': closeAiHelpModal,
        'editPropertyModal': closeEditPropertyModal,
        'editBookPropertyModal': closeEditBookPropertyModal,
        'createIndexModal': closeCreateIndexModal,
        'importDatabaseModal': closeImportDatabaseModal,
        'createDatabaseModal': closeCreateDatabaseModal,
        'getStartedModal': closeGetStartedModal
    };

    Object.entries(modalCloseHandlers).forEach(([modalId, closeFunc]) => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === modalId) closeFunc();
            });
        }
    });

    // Setup hamburger menu
    const menuToggleButton = document.querySelector('a[href="#menu"]');
    const menuPanel = document.getElementById('menu');

    if (menuToggleButton && menuPanel) {
        // Toggle menu on button click
        menuToggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            menuToggle();
        });

        // Stop propagation when clicking inside menu
        menuPanel.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        // Close menu on background click
        document.body.addEventListener('click', function(e) {
            if (document.body.classList.contains('is-menu-visible')) {
                if (!menuPanel.contains(e.target) && !menuToggleButton.contains(e.target)) {
                    menuHide();
                }
            }
        });

        // Append close button to menu
        const closeButton = document.createElement('a');
        closeButton.href = '#menu';
        closeButton.className = 'close';
        closeButton.innerHTML = '<span class="sr-only">Close</span>';
        closeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            menuHide();
        });
        menuPanel.appendChild(closeButton);
    }

    // Setup autocomplete
    setupAutocomplete();

    // Setup book dropdown change handlers
    document.getElementById('book').addEventListener('change', handleBookChange);
    document.getElementById('editBook').addEventListener('change', handleEditBookChange);

    // Setup book filter
    document.getElementById('bookFilter').addEventListener('change', handleBookFilter);

    // Setup term field to auto-populate notes when term exists
    document.getElementById('term').addEventListener('blur', handleTermBlur);

    // Setup number-only validation for page fields
    setupNumberOnlyFields();

    // Setup global keyboard shortcuts
    document.addEventListener('keydown', handleGlobalKeyboardShortcuts);

    // Load taglines from config and start rotating
    loadTaglines().then(() => startTaglineRotation());
});

// Switch tabs
function switchTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => tab.classList.remove('active'));

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => button.classList.remove('active'));

    // Show selected tab content
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Find and activate the correct tab button
    tabButtons.forEach(button => {
        const onclick = button.getAttribute('onclick');
        if (onclick && onclick.includes(`'${tabName}'`)) {
            button.classList.add('active');
        }
    });

    // If switching to add tab, load recent entries
    if (tabName === 'add') {
        loadRecentEntries();
    }

    // If switching to view tab, refresh entries
    if (tabName === 'view') {
        loadEntries();
    }

    // If switching to progress tab, run gap analysis
    if (tabName === 'progress') {
        runGapAnalysis();
    }

    // If switching to books tab, load books
    if (tabName === 'books') {
        loadBooks();
    }

    // If switching to settings tab, load settings
    if (tabName === 'settings') {
        loadSettingsTab();
    }
}

// Toggle tools section with accordion behavior
function toggleToolsSection(section, savePreference = true) {
    const sections = ['import', 'export', 'ai', 'study'];

    sections.forEach(s => {
        const container = document.getElementById(`${s}Container`);
        const toggle = document.getElementById(`${s}Toggle`);

        if (s === section) {
            // Toggle the clicked section
            if (container.classList.contains('collapsed')) {
                container.classList.remove('collapsed');
                toggle.textContent = '▼';

                // Save preference to localStorage
                if (savePreference) {
                    localStorage.setItem('lastOpenedTool', section);
                }

                // Check AI settings to show/hide enrich button
                if (section === 'ai') {
                    loadAiEnrichment();
                }
            } else {
                container.classList.add('collapsed');
                toggle.textContent = '▶';

                // Clear preference when closing
                if (savePreference) {
                    localStorage.removeItem('lastOpenedTool');
                }
            }
        } else {
            // Collapse other sections
            container.classList.add('collapsed');
            toggle.textContent = '▶';
        }
    });
}

// Restore last opened tool section
function restoreLastOpenedTool() {
    const lastTool = localStorage.getItem('lastOpenedTool');
    if (lastTool && ['import', 'export', 'gaps', 'ai'].includes(lastTool)) {
        toggleToolsSection(lastTool, false);
    }
}

// Toggle settings section with accordion behavior
function toggleSettingsSection(section, savePreference = true) {
    const sections = ['indexSettings', 'appearance', 'indexManagement', 'aiFeatures'];

    sections.forEach(s => {
        const container = document.getElementById(`${s}Container`);
        const toggle = document.getElementById(`${s}Toggle`);

        if (s === section) {
            // Toggle the clicked section
            if (container.classList.contains('collapsed')) {
                container.classList.remove('collapsed');
                toggle.textContent = '▼';

                // Save preference to localStorage
                if (savePreference) {
                    localStorage.setItem('lastOpenedSetting', section);
                }
            } else {
                container.classList.add('collapsed');
                toggle.textContent = '▶';

                // Clear preference when closing
                if (savePreference) {
                    localStorage.removeItem('lastOpenedSetting');
                }
            }
        } else {
            // Collapse other sections
            container.classList.add('collapsed');
            toggle.textContent = '▶';
        }
    });
}

// Restore last opened settings section
function restoreLastOpenedSetting() {
    const lastSetting = localStorage.getItem('lastOpenedSetting');
    if (lastSetting && ['indexSettings', 'appearance', 'indexManagement', 'aiFeatures'].includes(lastSetting)) {
        toggleSettingsSection(lastSetting, false);
    }
}

// Export index from dropdown
function exportIndexFromDropdown() {
    const format = document.getElementById('indexExportFormat').value;
    exportIndex(format);
}

// Export notes from dropdown
function exportNotesFromDropdown() {
    const format = document.getElementById('notesExportFormat').value;
    exportNotes(format);
}

// Load recent entries
async function loadRecentEntries(reset = true) {
    if (reset) {
        recentEntriesOffset = 0;
        allRecentEntries = [];
    }

    try {
        // Load more entries than we need to know if there are more
        const response = await fetch(`/api/entries/recent?limit=100`);
        const data = await response.json();
        allRecentEntries = data.entries;
        displayRecentEntries();
    } catch (error) {
        console.error('Error loading recent entries:', error);
        const container = document.getElementById('recentEntriesList');
        if (container) {
            container.innerHTML = '<p class="empty-state">Failed to load recent entries</p>';
        }
    }
}

// Display recent entries
function displayRecentEntries() {
    const container = document.getElementById('recentEntriesList');
    const showMoreBtn = document.getElementById('recentEntriesShowMore');

    if (!container) return;

    if (allRecentEntries.length === 0) {
        container.innerHTML = '<p class="empty-state">No entries yet</p>';
        if (showMoreBtn) showMoreBtn.style.display = 'none';
        return;
    }

    // Get entries to display (offset to offset + limit)
    const entriesToShow = allRecentEntries.slice(0, recentEntriesOffset + recentEntriesLimit);

    // Create comma-separated list of clickable terms
    const termLinks = entriesToShow.map(entry => {
        const escapedTerm = escapeHtml(entry.term);
        const escapedRef = escapeHtml(entry.reference);
        return `<a href="#" class="recent-term-link" onclick="editEntry('${escapedTerm}', '${escapedRef}'); return false;">${escapedTerm}</a>`;
    });

    container.innerHTML = `<div class="recent-terms-comma-list">${termLinks.join(', ')}</div>`;

    // Show or hide the "Show More" button
    if (showMoreBtn) {
        if (entriesToShow.length < allRecentEntries.length) {
            showMoreBtn.style.display = 'block';
        } else {
            showMoreBtn.style.display = 'none';
        }
    }
}

// Show more recent entries
function showMoreRecentEntries() {
    recentEntriesOffset += recentEntriesLimit;
    displayRecentEntries();
}

// Load all entries
async function loadEntries() {
    try {
        // Fetch entries and notes in parallel
        const [entriesResponse, notesResponse] = await Promise.all([
            fetch('/api/entries'),
            fetch('/api/notes')
        ]);

        const entriesData = await entriesResponse.json();
        const notesData = await notesResponse.json();

        // Create notes lookup map
        const notesMap = {};
        if (notesData.notes) {
            notesData.notes.forEach(note => {
                notesMap[note.term.toLowerCase()] = note.notes;
            });
        }

        // Combine entries with their notes
        allEntries = entriesData.entries.map(entry => ({
            ...entry,
            notes: notesMap[entry.term.toLowerCase()] || null
        }));

        // If no letter is selected and we have entries, select the first letter alphabetically
        if (!selectedLetter && allEntries.length > 0) {
            // Get all unique letters
            const letters = new Set();
            allEntries.forEach(entry => {
                letters.add(normalizeFirstLetter(entry.term));
            });

            // Sort letters with # first
            const sortedLetters = Array.from(letters).sort((a, b) => {
                if (a === '#') return -1;
                if (b === '#') return 1;
                return a.localeCompare(b);
            });

            selectedLetter = sortedLetters[0];
        }

        buildLetterNavigation();
        displayEntries(allEntries);
    } catch (error) {
        showMessage('Error loading entries: ' + error.message, 'error');
    }
}

// Refresh entries
function refreshEntries() {
    document.getElementById('searchInput').value = '';
    currentSearchQuery = '';
    selectedLetter = null;
    loadEntries();
}

// Toggle notes display without resetting view
function toggleNotesDisplay() {
    // Re-display with current filters intact
    if (currentSearchQuery) {
        const lowerQuery = currentSearchQuery.toLowerCase();
        const filtered = allEntries.filter(entry =>
            entry.term.toLowerCase().includes(lowerQuery) ||
            (entry.notes && entry.notes.toLowerCase().includes(lowerQuery))
        );
        displayEntries(filtered);
    } else {
        displayEntries(allEntries);
    }
}

// Build letter navigation
function buildLetterNavigation() {
    const navContainer = document.getElementById('letterNav');

    if (!navContainer) return;

    // Apply book filter if selected
    let entriesToNavigate = allEntries;
    if (selectedBookFilter) {
        entriesToNavigate = allEntries.filter(entry => {
            return entry.references.some(ref => ref.startsWith(selectedBookFilter + ':'));
        });
    }

    // Get all unique first letters from entries
    const letters = new Set();
    entriesToNavigate.forEach(entry => {
        letters.add(normalizeFirstLetter(entry.term));
    });

    // Sort letters, but put "#" at the beginning
    const sortedLetters = Array.from(letters).sort((a, b) => {
        if (a === '#') return -1;  // # goes to the beginning
        if (b === '#') return 1;   // # goes to the beginning
        return a.localeCompare(b);
    });

    // Build navigation HTML
    let html = '';
    sortedLetters.forEach(letter => {
        const activeClass = letter === selectedLetter ? 'active' : '';
        html += `<button class="letter-nav-btn ${activeClass}" onclick="filterByLetter('${letter}')">${letter}</button>`;
    });

    navContainer.innerHTML = html;
}

// Filter entries by letter
function filterByLetter(letter) {
    // Toggle: if clicking the already-selected letter, deselect it to show all
    if (selectedLetter === letter) {
        selectedLetter = null;
    } else {
        selectedLetter = letter;
    }

    currentSearchQuery = '';
    document.getElementById('searchInput').value = '';
    buildLetterNavigation();
    displayEntries(allEntries);
}

// Check for duplicate entry
function checkDuplicate(term, reference) {
    const entry = allEntries.find(e => e.term.toLowerCase() === term.toLowerCase());
    if (entry && entry.references.includes(reference)) {
        return true;
    }
    return false;
}

// Handle adding new entry
async function handleAddEntry(e) {
    e.preventDefault();

    const term = document.getElementById('term').value.trim();
    const book = document.getElementById('book').value.trim();
    const page = document.getElementById('page').value.trim();
    const pageEnd = document.getElementById('pageEnd').value.trim();
    const notes = document.getElementById('notes').value.trim();

    // Check if at least one of reference or notes is provided
    const hasReference = book && page;
    const hasNotes = notes.length > 0;

    if (!hasReference && !hasNotes) {
        showMessage('Please provide either a reference (book and page) or notes', 'error');
        return;
    }

    let reference = '';
    if (hasReference) {
        // Build reference string
        reference = `${book}:${page}`;
        if (pageEnd) {
            reference += `-${pageEnd}`;
        }

        // Check for duplicate only if adding a reference
        if (checkDuplicate(term, reference)) {
            if (!confirm(`This entry already exists: "${term}" → ${reference}\n\nAdd anyway?`)) {
                return;
            }
        }
    }

    try {
        let response, data;

        if (hasReference) {
            // Add reference (which can include notes)
            response = await fetch('/api/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ term, reference, notes })
            });
            data = await response.json();
        } else {
            // Add only notes (no reference)
            response = await fetch('/api/notes/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ term, notes })
            });
            data = await response.json();
        }

        if (response.ok) {
            showMessage(data.message, 'success');

            // Remember the last used book if reference was added
            if (hasReference) {
                lastUsedBook = book;
            }

            // Reset form
            document.getElementById('addForm').reset();
            lastAutocompleteTerm = '';  // Reset autocomplete tracking

            // Restore the last used book in the dropdown
            if (lastUsedBook) {
                document.getElementById('book').value = lastUsedBook;
            }

            document.getElementById('term').focus();
            loadEntries();
            loadRecentEntries(); // Refresh recent entries list
        } else if (response.status === 409) {
            showMessage(data.message, 'warning');
        } else {
            showMessage(data.error || 'Failed to add entry', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Handle CSV import
async function handleImportCSV(e) {
    e.preventDefault();

    const csvData = document.getElementById('csvData').value.trim();

    if (!csvData) {
        showImportMessage('Please paste CSV data to import', 'error');
        return;
    }

    try {
        const response = await fetch('/api/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ csv_data: csvData })
        });

        const data = await response.json();

        if (response.ok) {
            showImportMessage(data.message, 'success');
            displayImportResults(data);
            document.getElementById('csvData').value = '';
            loadEntries();
        } else {
            showImportMessage(data.error || 'Failed to import entries', 'error');
        }
    } catch (error) {
        showImportMessage('Error: ' + error.message, 'error');
    }
}

// Display import results
function displayImportResults(data, isNotesImport = false) {
    const resultsDiv = document.getElementById('importResults');

    let html = '<h3>Import Results:</h3><ul>';

    if (isNotesImport) {
        html += `<li>New terms created: ${data.imported || 0}</li>`;
        if (data.skipped && data.skipped > 0) {
            html += `<li>Existing terms updated: ${data.skipped}</li>`;
        }
    } else {
        html += `<li>Successfully imported: ${data.imported || 0} entries</li>`;
        if (data.skipped && data.skipped > 0) {
            html += `<li>Skipped (duplicates): ${data.skipped} entries</li>`;
        }
    }

    if (data.errors && data.errors.length > 0) {
        html += `<li>Errors: ${data.errors.length}</li>`;
        html += '<ul>';
        data.errors.forEach(error => {
            html += `<li style="color: var(--error-color);">${escapeHtml(error)}</li>`;
        });
        html += '</ul>';
    }

    html += '</ul>';
    resultsDiv.innerHTML = html;
    resultsDiv.classList.add('show');

    // Hide after 10 seconds
    setTimeout(() => {
        resultsDiv.classList.remove('show');
    }, 10000);
}

// Show import message
function showImportMessage(text, type = 'success') {
    const messageDiv = document.getElementById('importMessage');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 5000);
}

// Switch import tabs
function switchImportTab(tab) {
    // Update tab buttons
    document.querySelectorAll('.import-tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.import-tab-content').forEach(content => {
        content.classList.remove('active');
    });

    if (tab === 'references') {
        document.getElementById('importReferencesTab').classList.add('active');
    } else if (tab === 'notes') {
        document.getElementById('importNotesTab').classList.add('active');
    }

    // Clear any previous messages and results
    document.getElementById('importMessage').className = 'message';
    document.getElementById('importResults').classList.remove('show');
}

// Handle notes import
async function handleImportNotes(e) {
    e.preventDefault();

    const csvData = document.getElementById('csvNotesData').value.trim();

    if (!csvData) {
        showImportMessage('Please paste CSV data to import', 'error');
        return;
    }

    try {
        const response = await fetch('/api/import/notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ csv_data: csvData })
        });

        const data = await response.json();

        if (response.ok) {
            showImportMessage(data.message, 'success');
            displayImportResults(data, true);
            document.getElementById('csvNotesData').value = '';
            loadNotes();
        } else {
            showImportMessage(data.error || 'Failed to import notes', 'error');
        }
    } catch (error) {
        showImportMessage('Error: ' + error.message, 'error');
    }
}

// Load all notes
async function loadNotes() {
    try {
        const response = await fetch('/api/notes');
        const data = await response.json();
        allNotes = data.notes;
        buildNotesLetterNavigation();
        displayNotes(allNotes);
    } catch (error) {
        showMessage('Error loading notes: ' + error.message, 'error');
    }
}

// Refresh notes
function refreshNotes() {
    document.getElementById('notesSearchInput').value = '';
    selectedNotesLetter = null;
    loadNotes();
}

// Display notes
function displayNotes(notes) {
    const container = document.getElementById('notesList');

    // Apply letter filter
    let filteredNotes = notes;
    if (selectedNotesLetter) {
        filteredNotes = filteredNotes.filter(note => {
            const firstLetter = normalizeFirstLetter(note.term);
            return firstLetter === selectedNotesLetter;
        });
    }

    if (filteredNotes.length === 0) {
        container.innerHTML = '<p class="empty-state">No notes found</p>';
        updateNotesStats(0);
        return;
    }

    // Group by first letter
    const grouped = {};
    filteredNotes.forEach(note => {
        const letter = normalizeFirstLetter(note.term);
        if (!grouped[letter]) {
            grouped[letter] = [];
        }
        grouped[letter].push(note);
    });

    // Sort letters, but put "#" at the beginning
    const letters = Object.keys(grouped).sort((a, b) => {
        if (a === '#') return -1;
        if (b === '#') return 1;
        return a.localeCompare(b);
    });

    // Build HTML with letter headers
    let html = '';
    let totalShown = 0;

    letters.forEach(letter => {
        html += `<div class="letter-group">`;
        html += `<div class="letter-heading">${letter}</div>`;

        grouped[letter].forEach(note => {
            totalShown++;
            html += `<div class="note-item" onclick="editNotes('${escapeHtml(note.term)}', '${escapeHtml(note.notes)}')">`;
            html += `<div class="note-term">${escapeHtml(note.term)}</div>`;
            html += `<div class="note-text">${escapeHtml(note.notes)}</div>`;
            html += `</div>`;
        });

        html += `</div>`;
    });

    container.innerHTML = html;
    updateNotesStats(totalShown);
}

// Update notes statistics
function updateNotesStats(count) {
    const stats = document.getElementById('notesStats');
    stats.textContent = `Total notes: ${count}`;
}

// Handle notes search
function handleNotesSearch(e) {
    const query = e.target.value.trim();

    // Clear previous timeout
    if (notesSearchTimeout) {
        clearTimeout(notesSearchTimeout);
    }

    // Debounce search
    notesSearchTimeout = setTimeout(() => {
        if (query === '') {
            displayNotes(allNotes);
        } else {
            const filtered = allNotes.filter(note =>
                note.term.toLowerCase().includes(query.toLowerCase()) ||
                note.notes.toLowerCase().includes(query.toLowerCase())
            );
            displayNotes(filtered);
        }
        buildNotesLetterNavigation();
    }, 300);
}

// Build notes letter navigation
function buildNotesLetterNavigation() {
    const navContainer = document.getElementById('notesLetterNav');

    if (!navContainer) return;

    // Apply search if present
    let notesToNavigate = allNotes;
    const searchQuery = document.getElementById('notesSearchInput').value.trim();

    if (searchQuery) {
        notesToNavigate = allNotes.filter(note =>
            note.term.toLowerCase().includes(searchQuery.toLowerCase()) ||
            note.notes.toLowerCase().includes(searchQuery.toLowerCase())
        );
    }

    // Get all unique first letters from notes
    const letters = new Set();
    notesToNavigate.forEach(note => {
        letters.add(normalizeFirstLetter(note.term));
    });

    // Sort letters, but put "#" at the beginning
    const sortedLetters = Array.from(letters).sort((a, b) => {
        if (a === '#') return -1;
        if (b === '#') return 1;
        return a.localeCompare(b);
    });

    // Build navigation HTML
    let html = '';
    sortedLetters.forEach(letter => {
        const activeClass = letter === selectedNotesLetter ? 'active' : '';
        html += `<button class="letter-nav-btn ${activeClass}" onclick="filterNotesByLetter('${letter}')">${letter}</button>`;
    });

    navContainer.innerHTML = html;
}

// Filter notes by letter
function filterNotesByLetter(letter) {
    // Toggle: if clicking the already-selected letter, deselect it to show all
    if (selectedNotesLetter === letter) {
        selectedNotesLetter = null;
    } else {
        selectedNotesLetter = letter;
    }

    document.getElementById('notesSearchInput').value = '';
    buildNotesLetterNavigation();
    displayNotes(allNotes);
}

// Open edit notes modal
function editNotes(term, notes) {
    document.getElementById('editNotesTerm').value = term;
    document.getElementById('editNotesText').value = notes;
    document.getElementById('editNotesText').focus();
    document.getElementById('editNotesModal').classList.add('show');
}

// Close edit notes modal
function closeEditNotesModal() {
    document.getElementById('editNotesModal').classList.remove('show');
    document.getElementById('editNotesForm').reset();
}

// Handle edit notes form submission
async function handleEditNotes(e) {
    e.preventDefault();

    const term = document.getElementById('editNotesTerm').value.trim();
    const notes = document.getElementById('editNotesText').value.trim();

    try {
        const response = await fetch('/api/notes/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term, notes })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');
            closeEditNotesModal();
            loadNotes();
        } else {
            showMessage(data.error || 'Failed to update notes', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Delete notes from modal
async function deleteNotesFromModal() {
    const term = document.getElementById('editNotesTerm').value.trim();

    if (!confirm(`Delete notes for "${term}"?`)) {
        return;
    }

    try {
        const response = await fetch('/api/notes/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');
            closeEditNotesModal();
            loadNotes();
        } else {
            showMessage(data.error || 'Failed to delete notes', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Export notes
function exportNotes(format) {
    window.location.href = `/api/notes/export/${format}`;
}

// Handle search
function handleSearch(e) {
    const query = e.target.value.trim();

    // Clear previous timeout
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }

    // Debounce search
    searchTimeout = setTimeout(() => {
        currentSearchQuery = query;

        if (query === '') {
            // Reset to show selected letter
            buildLetterNavigation();
            displayEntries(allEntries);
        } else {
            // When searching, clear letter selection
            selectedLetter = null;
            buildLetterNavigation();

            const lowerQuery = query.toLowerCase();
            const filtered = allEntries.filter(entry =>
                entry.term.toLowerCase().includes(lowerQuery) ||
                (entry.notes && entry.notes.toLowerCase().includes(lowerQuery))
            );
            displayEntries(filtered);
        }
    }, 300);
}

// Display entries grouped by letter
function displayEntries(entries) {
    const container = document.getElementById('entriesList');

    // Apply book filter if selected
    let filteredEntries = entries;
    if (selectedBookFilter) {
        filteredEntries = entries.filter(entry => {
            return entry.references.some(ref => ref.startsWith(selectedBookFilter + ':'));
        });
    }

    if (filteredEntries.length === 0) {
        let html = '<p class="empty-state">No entries found</p>';

        // If user was searching, show "Add Entry" button
        if (currentSearchQuery) {
            html = `<div class="empty-state">
                        <p>No entries found for "${escapeHtml(currentSearchQuery)}"</p>
                        <div class="empty-state-actions">
                            <button class="btn btn-primary" onclick="addEntryFromSearch('${escapeHtml(currentSearchQuery)}')">
                                + Add Entry for "${escapeHtml(currentSearchQuery)}"
                            </button>
                        </div>
                    </div>`;
        } else if (selectedBookFilter) {
            html = `<p class="empty-state">No entries found for the selected book</p>`;
        }

        container.innerHTML = html;
        updateStats(0);
        return;
    }

    // Group by first letter
    const grouped = {};
    filteredEntries.forEach(entry => {
        const letter = normalizeFirstLetter(entry.term);
        if (!grouped[letter]) {
            grouped[letter] = [];
        }
        grouped[letter].push(entry);
    });

    // Sort letters, but put "#" at the beginning
    const letters = Object.keys(grouped).sort((a, b) => {
        if (a === '#') return -1;  // # goes to the beginning
        if (b === '#') return 1;   // # goes to the beginning
        return a.localeCompare(b);
    });

    // If not searching and a letter is selected, show only that letter
    let lettersToShow = letters;
    if (!currentSearchQuery && selectedLetter) {
        lettersToShow = letters.filter(l => l === selectedLetter);
    }

    // Build HTML
    let html = '';
    let totalShown = 0;

    lettersToShow.forEach(letter => {
        html += `<div class="letter-group">`;
        html += `<div class="letter-heading">${letter}</div>`;

        const showNotes = document.getElementById('showNotesCheckbox')?.checked ?? true;

        grouped[letter].forEach(entry => {
            totalShown++;
            html += `<div class="entry-item">`;
            html += `<div class="entry-content"><div class="entry-term">${escapeHtml(entry.term)}</div>`;

            // Display references on one line, separated by commas
            html += `<div class="entry-refs">`;
            entry.references.forEach((ref, index) => {
                if (index > 0) html += ',';
                html += `<span class="ref-link" onclick="editEntry('${escapeHtml(entry.term)}', '${escapeHtml(ref)}')">${escapeHtml(ref)}</span>`;
            });
            html += `</div>`;

            // Display notes if available and checkbox is checked
            if (showNotes && entry.notes) {
                html += `<div class="entry-notes">${escapeHtml(entry.notes)}</div>`;
            }

            html += `</div></div>`;
        });

        html += `</div>`;
    });

    container.innerHTML = html;
    updateStats(totalShown);
}

// Update statistics
function updateStats(count) {
    const stats = document.getElementById('stats');
    stats.textContent = `Total entries: ${count}`;
}

// Delete entry
async function deleteEntry(term) {
    if (!confirm(`Delete all references for "${term}"?`)) {
        return;
    }

    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term })
        });

        const data = await response.json();

        if (response.ok) {
            showViewEntriesMessage(data.message, 'success');
            loadEntries();
        } else {
            showViewEntriesMessage(data.error || 'Failed to delete entry', 'error');
        }
    } catch (error) {
        showViewEntriesMessage('Error: ' + error.message, 'error');
    }
}

// Delete specific reference
async function deleteReference(term, reference) {
    if (!confirm(`Delete reference "${reference}" for term "${term}"?`)) {
        return;
    }

    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term, reference })
        });

        const data = await response.json();

        if (response.ok) {
            showViewEntriesMessage(data.message, 'success');
            loadEntries();
        } else {
            showViewEntriesMessage(data.error || 'Failed to delete reference', 'error');
        }
    } catch (error) {
        showViewEntriesMessage('Error: ' + error.message, 'error');
    }
}

// Open edit modal
async function editEntry(term, reference) {
    document.getElementById('editTerm').value = term;
    document.getElementById('editTerm').setAttribute('data-original-term', term);
    document.getElementById('editOldReference').value = reference;

    // Parse the reference to populate individual fields
    const parts = reference.split(':');
    if (parts.length === 2) {
        const book = parts[0];
        const pageparts = parts[1].split('-');

        // Set book dropdown value
        const editBookSelect = document.getElementById('editBook');
        // Check if this book exists in the dropdown
        let bookExists = false;
        for (let i = 0; i < editBookSelect.options.length; i++) {
            if (editBookSelect.options[i].value === book) {
                editBookSelect.value = book;
                bookExists = true;
                break;
            }
        }

        // If book doesn't exist in dropdown, add it as custom option
        if (!bookExists && book) {
            const customOption = document.createElement('option');
            customOption.value = book;
            customOption.textContent = book;
            customOption.selected = true;
            // Insert before "Other" option
            editBookSelect.insertBefore(customOption, editBookSelect.lastElementChild);
        }

        document.getElementById('editPage').value = pageparts[0];
        document.getElementById('editPageEnd').value = pageparts[1] || '';
    }

    // Load notes for this term
    try {
        const response = await fetch('/api/notes');
        const data = await response.json();
        const noteEntry = data.notes.find(n => n.term.toLowerCase() === term.toLowerCase());
        document.getElementById('editNotes').value = noteEntry ? noteEntry.notes : '';
    } catch (error) {
        console.error('Error loading notes:', error);
        document.getElementById('editNotes').value = '';
    }

    document.getElementById('editBook').focus();
    document.getElementById('editModal').classList.add('show');
}

// Close edit modal
function closeEditModal() {
    document.getElementById('editModal').classList.remove('show');
    document.getElementById('editForm').reset();
}

// Handle edit form submission
async function handleEditEntry(e) {
    e.preventDefault();

    const term = document.getElementById('editTerm').value.trim();
    const oldTerm = document.getElementById('editTerm').getAttribute('data-original-term');
    const oldReference = document.getElementById('editOldReference').value.trim();
    const notes = document.getElementById('editNotes').value.trim();

    const book = document.getElementById('editBook').value.trim();
    const page = document.getElementById('editPage').value.trim();
    const pageEnd = document.getElementById('editPageEnd').value.trim();

    // Build new reference string
    let newReference = `${book}:${page}`;
    if (pageEnd) {
        newReference += `-${pageEnd}`;
    }

    try {
        const response = await fetch('/api/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term, old_term: oldTerm, old_reference: oldReference, new_reference: newReference })
        });

        const data = await response.json();

        if (response.ok) {
            // Always update notes (even if empty, to allow clearing them)
            await fetch('/api/notes/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ term, notes })
            });

            // Check if we're on the View Entries tab or Add Entry tab
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-view') {
                showViewEntriesMessage(data.message, 'success');
            } else {
                showMessage(data.message, 'success');
            }
            closeEditModal();
            loadEntries();
            loadRecentEntries(); // Refresh recent entries
        } else {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-view') {
                showViewEntriesMessage(data.error || 'Failed to update reference', 'error');
            } else {
                showMessage(data.error || 'Failed to update reference', 'error');
            }
        }
    } catch (error) {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'tab-view') {
            showViewEntriesMessage('Error: ' + error.message, 'error');
        } else {
            showMessage('Error: ' + error.message, 'error');
        }
    }
}

// Delete reference from modal
async function deleteReferenceFromModal() {
    const term = document.getElementById('editTerm').value.trim();
    const reference = document.getElementById('editOldReference').value.trim();

    if (!confirm(`Delete reference "${reference}" for term "${term}"?`)) {
        return;
    }

    try {
        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ term, reference })
        });

        const data = await response.json();

        if (response.ok) {
            // Check if we're on the View Entries tab or Add Entry tab
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-view') {
                showViewEntriesMessage(data.message, 'success');
            } else {
                showMessage(data.message, 'success');
            }
            closeEditModal();
            loadEntries();
            loadRecentEntries(); // Refresh recent entries
        } else {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-view') {
                showViewEntriesMessage(data.error || 'Failed to delete reference', 'error');
            } else {
                showMessage(data.error || 'Failed to delete reference', 'error');
            }
        }
    } catch (error) {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'tab-view') {
            showViewEntriesMessage('Error: ' + error.message, 'error');
        } else {
            showMessage('Error: ' + error.message, 'error');
        }
    }
}

// Add entry from search
function addEntryFromSearch(term) {
    // Switch to Add Entry tab
    switchTab('add');

    // Pre-populate the term field
    document.getElementById('term').value = term;
    document.getElementById('book').focus();

    // Clear the search
    document.getElementById('searchInput').value = '';
    currentSearchQuery = '';
}

// Export index
function exportIndex(format) {
    window.location.href = `/api/export/${format}`;
}

// Show message
function showMessage(text, type = 'success') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 5000);
}

// Show message on View Entries tab
function showViewEntriesMessage(text, type = 'success') {
    const messageDiv = document.getElementById('viewEntriesMessage');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 5000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();

        // Update index name in header
        if (data.index_name) {
            document.getElementById('indexName').textContent = data.index_name;
        }

        // Apply saved color scheme
        if (data.color_scheme) {
            applyColorScheme(data.color_scheme);
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Load settings tab
async function loadSettingsTab() {
    try {
        const response = await fetch('/api/settings');
        const data = await response.json();
        document.getElementById('settingsIndexName').value = data.index_name || '';

        // Set color scheme dropdown
        const colorSelect = document.getElementById('colorScheme');
        if (colorSelect && data.color_scheme) {
            colorSelect.value = data.color_scheme;
            updateColorSelectBackground(data.color_scheme);
        }

        // Load custom properties
        loadCustomProperties();

        // Load AI settings
        loadAiEnrichment();
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Save all settings (index name and optionally add new property)
async function saveAllSettings() {
    const name = document.getElementById('settingsIndexName').value.trim();

    if (!name) {
        showSettingsMessage('indexSettingsMessage', 'Please enter an index name', 'error');
        return;
    }

    // Save index name
    try {
        const response = await fetch('/api/settings/index-name', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name })
        });

        const data = await response.json();

        if (response.ok) {
            showSettingsMessage('indexSettingsMessage', 'Settings saved', 'success');
            loadSettings();

            // Check if user is adding a new custom property
            const propertyName = document.getElementById('propertyName').value.trim();
            const propertyValue = document.getElementById('propertyValue').value.trim();

            if (propertyName && propertyValue) {
                await addNewCustomProperty(propertyName, propertyValue);
            }
        } else {
            showSettingsMessage('indexSettingsMessage', data.error || 'Failed to save settings', 'error');
        }
    } catch (error) {
        showSettingsMessage('indexSettingsMessage', 'Error: ' + error.message, 'error');
    }
}

// Add new custom property
async function addNewCustomProperty(propertyName, propertyValue) {
    try {
        const response = await fetch('/api/custom-properties', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                property_name: propertyName,
                property_value: propertyValue
            })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('propertyName').value = '';
            document.getElementById('propertyValue').value = '';
            loadCustomProperties();
        } else {
            showSettingsMessage('indexSettingsMessage', data.error || 'Failed to add property', 'error');
        }
    } catch (error) {
        showSettingsMessage('indexSettingsMessage', 'Error: ' + error.message, 'error');
    }
}

// Change color scheme
async function changeColorScheme() {
    const colorSelect = document.getElementById('colorScheme');
    const color = colorSelect.value;

    try {
        const response = await fetch('/api/settings/color-scheme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ color })
        });

        const data = await response.json();

        if (response.ok) {
            applyColorScheme(color);
            updateColorSelectBackground(color);
            showSettingsMessage('colorSchemeMessage', 'Color scheme updated', 'success');
            setTimeout(() => {
                document.getElementById('colorSchemeMessage').innerHTML = '';
            }, 2000);
        } else {
            showSettingsMessage('colorSchemeMessage', data.error || 'Failed to save color scheme', 'error');
        }
    } catch (error) {
        showSettingsMessage('colorSchemeMessage', 'Error: ' + error.message, 'error');
    }
}

// Apply color scheme to the page
function applyColorScheme(color) {
    document.documentElement.style.setProperty('--secondary-color', color);

    // Convert hex to rgba for message background
    const rgb = hexToRgb(color);
    if (rgb) {
        const messageSuccessBg = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.15)`;
        document.documentElement.style.setProperty('--message-success-bg', messageSuccessBg);
    }

    const colorSelect = document.getElementById('colorScheme');
    if (colorSelect) {
        colorSelect.value = color;
        updateColorSelectBackground(color);
    }

    // Update hamburger menu hover color
    updateHamburgerMenuColor(color);
}

// Helper function to convert hex to rgb
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

// Update color select background to match selected color
function updateColorSelectBackground(color) {
    const colorSelect = document.getElementById('colorScheme');
    if (colorSelect) {
        colorSelect.style.backgroundColor = color;
    }
}

// Update hamburger menu and close icon hover colors
function updateHamburgerMenuColor(color) {
    // Remove '#' from color and URL-encode it for SVG
    const colorEncoded = encodeURIComponent(color);

    // Create SVG data URI with the new color for hamburger icon
    const hamburgerSvg = `url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100' preserveAspectRatio='none'%3E%3Cstyle%3Eline %7B stroke-width: 8px%3B stroke: ${colorEncoded}%3B %7D%3C/style%3E%3Cline x1='0' y1='25' x2='100' y2='25' /%3E%3Cline x1='0' y1='50' x2='100' y2='50' /%3E%3Cline x1='0' y1='75' x2='100' y2='75' /%3E%3C/svg%3E")`;

    // Create SVG data URI with the new color for close icon
    const closeSvg = `url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100' preserveAspectRatio='none'%3E%3Cstyle%3Eline %7B stroke-width: 8px%3B stroke: ${colorEncoded}%3B %7D%3C/style%3E%3Cline x1='15' y1='15' x2='85' y2='85' /%3E%3Cline x1='85' y1='15' x2='15' y2='85' /%3E%3C/svg%3E")`;

    // Update CSS custom properties
    document.documentElement.style.setProperty('--hamburger-hover-icon', hamburgerSvg);
    document.documentElement.style.setProperty('--close-hover-icon', closeSvg);
}

// Backup database
function backupDatabase() {
    window.location.href = '/api/settings/backup';
    // Don't show message as the file download will indicate success
}

// Execute index management action from dropdown
function executeIndexManagementAction() {
    const action = document.getElementById('indexManagementAction').value;

    switch (action) {
        case 'create':
            showCreateDatabaseModal();
            break;
        case 'backup':
            backupDatabase();
            break;
        case 'import':
            showImportDatabaseModal();
            break;
        case 'archive':
            archiveCurrentDatabase();
            break;
        default:
            // No action selected
            break;
    }

    // Reset dropdown after action
    document.getElementById('indexManagementAction').value = '';
}

// Create new index (clear all data)
async function archiveCurrentDatabase() {
    const confirmed = confirm(
        'This will archive the current database and move it to the archive folder.\n\n' +
        'The database will no longer appear in the index switcher.\n\n' +
        'Are you sure you want to archive this database?'
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch('/api/databases/archive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (response.ok) {
            showColorSchemeMessage(
                data.message + (data.switched_to ? ` Switched to ${data.switched_to}` : ''),
                'success'
            );
            // Reload page to show new database
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showMessage(data.error || 'Failed to archive database', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Show settings message
function showSettingsMessage(messageId, text, type = 'success') {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) {
        console.error('Message div not found:', messageId);
        return;
    }
    messageDiv.textContent = text;
    messageDiv.className = `message ${type} show`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 5000);
}

// Custom Properties Management
let draggedPropertyElement = null;
let allCustomProperties = [];

// Load custom properties
async function loadCustomProperties() {
    try {
        const response = await fetch('/api/custom-properties');
        const data = await response.json();
        allCustomProperties = data.properties;
        displayCustomProperties(allCustomProperties);
    } catch (error) {
        console.error('Error loading custom properties:', error);
    }
}

// Display custom properties
function displayCustomProperties(properties) {
    const container = document.getElementById('customPropertiesTable');

    if (properties.length === 0) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    properties.forEach(prop => {
        html += `<div class="property-row" draggable="true" data-property-id="${prop.id}">`;
        html += `<span class="drag-handle">☰</span>`;
        html += `<div class="property-row-content" onclick="openEditPropertyModal(${prop.id})">`;
        html += `<div class="property-name">${escapeHtml(prop.property_name)}</div>`;
        html += `<div class="property-value">${escapeHtml(prop.property_value)}</div>`;
        html += `</div>`;
        html += `</div>`;
    });

    container.innerHTML = html;

    // Add drag and drop event listeners
    const propertyRows = container.querySelectorAll('.property-row');
    propertyRows.forEach(row => {
        row.addEventListener('dragstart', handleDragStart);
        row.addEventListener('dragend', handleDragEnd);
        row.addEventListener('dragover', handleDragOver);
        row.addEventListener('drop', handleDrop);
        row.addEventListener('dragenter', handleDragEnter);
        row.addEventListener('dragleave', handleDragLeave);
    });
}

// Open edit property modal
function openEditPropertyModal(propertyId) {
    const property = allCustomProperties.find(p => p.id === propertyId);
    if (property) {
        document.getElementById('editPropertyModalId').value = property.id;
        document.getElementById('editPropertyModalName').value = property.property_name;
        document.getElementById('editPropertyModalValue').value = property.property_value;
        document.getElementById('editPropertyModal').classList.add('show');
    }
}

// Close edit property modal
function closeEditPropertyModal() {
    document.getElementById('editPropertyModal').classList.remove('show');
    document.getElementById('editPropertyForm').reset();
}

// Save edited property from modal
async function saveEditedProperty(event) {
    event.preventDefault();

    const propertyId = document.getElementById('editPropertyModalId').value;
    const propertyName = document.getElementById('editPropertyModalName').value.trim();
    const propertyValue = document.getElementById('editPropertyModalValue').value.trim();

    if (!propertyName || !propertyValue) {
        return;
    }

    try {
        const response = await fetch(`/api/custom-properties/${propertyId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                property_name: propertyName,
                property_value: propertyValue
            })
        });

        const data = await response.json();

        if (response.ok) {
            closeEditPropertyModal();
            loadCustomProperties();
            showSettingsMessage('indexSettingsMessage', 'Property updated', 'success');
        } else {
            alert(data.error || 'Failed to save property');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Delete property from modal
async function deletePropertyFromModal() {
    const propertyId = document.getElementById('editPropertyModalId').value;

    try {
        const response = await fetch(`/api/custom-properties/${propertyId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            closeEditPropertyModal();
            loadCustomProperties();
            showSettingsMessage('indexSettingsMessage', 'Property deleted', 'success');
        } else {
            alert(data.error || 'Failed to delete property');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Drag and drop handlers
function handleDragStart(e) {
    draggedPropertyElement = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragEnd(e) {
    this.classList.remove('dragging');

    // Remove drag-over class from all rows
    document.querySelectorAll('.property-row').forEach(row => {
        row.classList.remove('drag-over');
    });
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    if (this !== draggedPropertyElement) {
        this.classList.add('drag-over');
    }
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }

    if (draggedPropertyElement !== this) {
        // Get all property rows
        const container = document.getElementById('customPropertiesTable');
        const rows = Array.from(container.querySelectorAll('.property-row'));

        // Remove dragged element from its current position
        const draggedIndex = rows.indexOf(draggedPropertyElement);
        const targetIndex = rows.indexOf(this);

        // Reorder in DOM
        if (draggedIndex < targetIndex) {
            this.parentNode.insertBefore(draggedPropertyElement, this.nextSibling);
        } else {
            this.parentNode.insertBefore(draggedPropertyElement, this);
        }

        // Get new order of property IDs
        const newOrder = Array.from(container.querySelectorAll('.property-row'))
            .map(row => parseInt(row.getAttribute('data-property-id')));

        // Save new order to server
        savePropertyOrder(newOrder);
    }

    return false;
}

// Save property order to server
async function savePropertyOrder(propertyIds) {
    try {
        const response = await fetch('/api/custom-properties/reorder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                property_ids: propertyIds
            })
        });

        if (!response.ok) {
            const data = await response.json();
            console.error('Failed to save property order:', data.error);
        }
    } catch (error) {
        console.error('Error saving property order:', error);
    }
}

// Load book dropdowns
async function loadBookDropdowns() {
    try {
        const response = await fetch('/api/books');
        const data = await response.json();

        // Populate all dropdowns
        const bookSelect = document.getElementById('book');
        const editBookSelect = document.getElementById('editBook');
        const bookFilter = document.getElementById('bookFilter');

        // Clear existing options except the first placeholder
        bookSelect.innerHTML = '<option value="">Book</option>';
        editBookSelect.innerHTML = '<option value="">Book</option>';
        bookFilter.innerHTML = '<option value="">All Books</option>';

        // Add books as options
        data.books.forEach(book => {
            const option1 = document.createElement('option');
            option1.value = book.book_number;
            option1.textContent = `${book.book_number}: ${book.book_name}`;
            bookSelect.appendChild(option1);

            const option2 = document.createElement('option');
            option2.value = book.book_number;
            option2.textContent = `${book.book_number}: ${book.book_name}`;
            editBookSelect.appendChild(option2);

            const option3 = document.createElement('option');
            option3.value = book.book_number;
            option3.textContent = `Book ${book.book_number}: ${book.book_name}`;
            bookFilter.appendChild(option3);
        });

        // Add "Other" option for manual entry (not for filter)
        const otherOption1 = document.createElement('option');
        otherOption1.value = 'other';
        otherOption1.textContent = 'Other (manual entry)';
        bookSelect.appendChild(otherOption1);

        const otherOption2 = document.createElement('option');
        otherOption2.value = 'other';
        otherOption2.textContent = 'Other (manual entry)';
        editBookSelect.appendChild(otherOption2);

    } catch (error) {
        console.error('Error loading book dropdowns:', error);
    }
}

// Load books list
async function loadBooks() {
    try {
        const response = await fetch('/api/books');
        const data = await response.json();
        displayBooks(data.books);
    } catch (error) {
        console.error('Error loading books:', error);
    }
}

// Display books list
function displayBooks(books) {
    const container = document.getElementById('booksList');

    if (books.length === 0) {
        container.innerHTML = '<p class="empty-state">No books added yet</p>';
        return;
    }

    let html = '';
    books.forEach(book => {
        html += `<div class="book-item" data-book-number="${escapeHtml(book.book_number)}">`;
        html += `<div class="book-header" onclick="toggleBookExpand(${escapeHtml(book.book_number)})">`;
        html += `<div class="book-info">`;
        html += `<span class="book-expand-icon" id="bookExpandIcon_${book.book_number}">▶</span>`;
        html += `<span class="book-number">Book ${escapeHtml(book.book_number)}:</span>`;
        html += `<span class="book-name">${escapeHtml(book.book_name)}</span>`;
        html += `<span class="book-pages">(${book.page_count} pages)</span>`;
        html += `</div>`;
        html += `<div class="book-actions">`;
        html += `<button class="btn btn-secondary book-edit-btn" data-number="${escapeHtml(book.book_number)}" data-name="${escapeHtml(book.book_name)}" data-pages="${book.page_count}" onclick="event.stopPropagation();">Edit</button>`;
        html += `</div></div>`;
        html += `<div class="book-details" id="bookDetails_${book.book_number}" style="display: none;">`;
        html += `<div class="book-metadata-section">`;
        html += `<p class="settings-help" style="margin: 0 0 0.75rem 0;">Click a property to edit, drag to reorder.</p>`;
        html += `<div class="form-row" style="display: flex; gap: 1rem; margin-bottom: 1rem;">`;
        html += `<div class="form-group" style="flex: 1; margin: 0;">`;
        html += `<label>Metadata:</label>`;
        html += `<input type="text" id="bookPropName_${book.book_number}" placeholder="e.g., Author, Publisher">`;
        html += `</div>`;
        html += `<div class="form-group" style="flex: 1; margin: 0;">`;
        html += `<label>Value:</label>`;
        html += `<input type="text" id="bookPropValue_${book.book_number}" placeholder="e.g., John Smith">`;
        html += `</div>`;
        html += `</div>`;
        html += `<button class="btn btn-primary" onclick="addBookProperty(${book.book_number})">Add Metadata</button>`;
        html += `<div class="custom-properties-table" id="bookProperties_${book.book_number}" style="margin-top: 1rem;"></div>`;
        html += `</div></div></div>`;
    });

    container.innerHTML = html;

    // Add event listeners to edit buttons
    const editButtons = container.querySelectorAll('.book-edit-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const bookNumber = this.getAttribute('data-number');
            const bookName = this.getAttribute('data-name');
            const pageCount = this.getAttribute('data-pages');
            editBook(bookNumber, bookName, pageCount);
        });
    });
}

// Toggle book expand/collapse
async function toggleBookExpand(bookNumber) {
    const details = document.getElementById(`bookDetails_${bookNumber}`);
    const icon = document.getElementById(`bookExpandIcon_${bookNumber}`);

    if (details.style.display === 'none') {
        details.style.display = 'block';
        icon.textContent = '▼';
        // Load book properties
        await loadBookProperties(bookNumber);
    } else {
        details.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Load book custom properties
async function loadBookProperties(bookNumber) {
    try {
        const response = await fetch(`/api/books/${bookNumber}/properties`);
        const data = await response.json();
        displayBookProperties(bookNumber, data.properties);
    } catch (error) {
        console.error('Error loading book properties:', error);
    }
}

// Display book custom properties
// Store book properties for each book
let bookPropertiesCache = {};

function displayBookProperties(bookNumber, properties) {
    const container = document.getElementById(`bookProperties_${bookNumber}`);

    // Cache properties for this book
    bookPropertiesCache[bookNumber] = properties;

    if (properties.length === 0) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    properties.forEach(prop => {
        html += `<div class="property-row" draggable="true" data-property-id="${prop.id}" data-book-number="${bookNumber}">`;
        html += `<span class="drag-handle">☰</span>`;
        html += `<div class="property-row-content" onclick="openEditBookPropertyModal(${prop.id}, ${bookNumber})">`;
        html += `<div class="property-name">${escapeHtml(prop.property_name)}</div>`;
        html += `<div class="property-value">${escapeHtml(prop.property_value)}</div>`;
        html += `</div>`;
        html += `</div>`;
    });

    container.innerHTML = html;

    // Add drag and drop event listeners
    const propertyRows = container.querySelectorAll('.property-row');
    propertyRows.forEach(row => {
        row.addEventListener('dragstart', handleBookPropertyDragStart);
        row.addEventListener('dragend', handleBookPropertyDragEnd);
        row.addEventListener('dragover', handleBookPropertyDragOver);
        row.addEventListener('drop', handleBookPropertyDrop);
        row.addEventListener('dragenter', handleBookPropertyDragEnter);
        row.addEventListener('dragleave', handleBookPropertyDragLeave);
    });
}

// Add book custom property
async function addBookProperty(bookNumber) {
    const nameInput = document.getElementById(`bookPropName_${bookNumber}`);
    const valueInput = document.getElementById(`bookPropValue_${bookNumber}`);
    const propertyName = nameInput.value.trim();
    const propertyValue = valueInput.value.trim();

    if (!propertyName || !propertyValue) {
        showSettingsMessage('bookManagementMessage', 'Property name and value are required', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/books/${bookNumber}/properties`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                property_name: propertyName,
                property_value: propertyValue
            })
        });

        const data = await response.json();

        if (response.ok) {
            nameInput.value = '';
            valueInput.value = '';
            loadBookProperties(bookNumber);
        } else {
            showSettingsMessage('bookManagementMessage', data.error || 'Failed to add property', 'error');
        }
    } catch (error) {
        showSettingsMessage('bookManagementMessage', 'Error: ' + error.message, 'error');
    }
}

// Open edit book property modal
function openEditBookPropertyModal(propertyId, bookNumber) {
    const properties = bookPropertiesCache[bookNumber] || [];
    const property = properties.find(p => p.id === propertyId);
    if (property) {
        document.getElementById('editBookPropertyModalId').value = property.id;
        document.getElementById('editBookPropertyModalBookNumber').value = bookNumber;
        document.getElementById('editBookPropertyModalName').value = property.property_name;
        document.getElementById('editBookPropertyModalValue').value = property.property_value;
        document.getElementById('editBookPropertyModal').classList.add('show');
    }
}

// Close edit book property modal
function closeEditBookPropertyModal() {
    document.getElementById('editBookPropertyModal').classList.remove('show');
    document.getElementById('editBookPropertyForm').reset();
}

// Save edited book property from modal
async function saveEditedBookProperty(event) {
    event.preventDefault();

    const propertyId = document.getElementById('editBookPropertyModalId').value;
    const bookNumber = document.getElementById('editBookPropertyModalBookNumber').value;
    const propertyName = document.getElementById('editBookPropertyModalName').value.trim();
    const propertyValue = document.getElementById('editBookPropertyModalValue').value.trim();

    if (!propertyName || !propertyValue) {
        alert('Property name and value are required');
        return;
    }

    try {
        const response = await fetch(`/api/books/properties/${propertyId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                property_name: propertyName,
                property_value: propertyValue
            })
        });

        const data = await response.json();

        if (response.ok) {
            closeEditBookPropertyModal();
            loadBookProperties(bookNumber);
        } else {
            alert(data.error || 'Failed to update property');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Delete book property from modal
async function deleteBookPropertyFromModal() {
    const propertyId = document.getElementById('editBookPropertyModalId').value;
    const bookNumber = document.getElementById('editBookPropertyModalBookNumber').value;

    try {
        const response = await fetch(`/api/books/properties/${propertyId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            closeEditBookPropertyModal();
            loadBookProperties(bookNumber);
        } else {
            alert(data.error || 'Failed to delete property');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Book property drag and drop handlers
let draggedBookProperty = null;

function handleBookPropertyDragStart(e) {
    draggedBookProperty = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleBookPropertyDragEnd(e) {
    this.classList.remove('dragging');
    document.querySelectorAll('.property-row').forEach(row => {
        row.classList.remove('drag-over');
    });
}

function handleBookPropertyDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleBookPropertyDragEnter(e) {
    e.preventDefault();
    if (this !== draggedBookProperty && this.dataset.bookNumber === draggedBookProperty.dataset.bookNumber) {
        this.classList.add('drag-over');
    }
}

function handleBookPropertyDragLeave(e) {
    this.classList.remove('drag-over');
}

async function handleBookPropertyDrop(e) {
    e.preventDefault();
    this.classList.remove('drag-over');

    if (this === draggedBookProperty) return;
    if (this.dataset.bookNumber !== draggedBookProperty.dataset.bookNumber) return;

    const bookNumber = this.dataset.bookNumber;
    const container = this.parentNode;
    const allRows = Array.from(container.querySelectorAll('.property-row'));

    const fromIndex = allRows.indexOf(draggedBookProperty);
    const toIndex = allRows.indexOf(this);

    // Reorder in DOM
    if (fromIndex < toIndex) {
        container.insertBefore(draggedBookProperty, this.nextSibling);
    } else {
        container.insertBefore(draggedBookProperty, this);
    }

    // Get new order and save
    const newOrder = Array.from(container.querySelectorAll('.property-row'))
        .map(row => parseInt(row.dataset.propertyId));

    await saveBookPropertyOrder(bookNumber, newOrder);
}

// Save book property order
async function saveBookPropertyOrder(bookNumber, propertyIds) {
    try {
        const response = await fetch(`/api/books/${bookNumber}/properties/reorder`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ property_ids: propertyIds })
        });

        if (!response.ok) {
            console.error('Failed to save property order');
            loadBookProperties(bookNumber); // Reload to reset order
        }
    } catch (error) {
        console.error('Error saving property order:', error);
        loadBookProperties(bookNumber);
    }
}


// Add a new book
async function addBook() {
    const bookNumber = document.getElementById('newBookNumber').value.trim();
    const bookName = document.getElementById('newBookName').value.trim();
    const pageCount = document.getElementById('newBookPages').value.trim();

    if (!bookNumber || !bookName) {
        showSettingsMessage('addBookMessage', 'Book number and name are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/books/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_number: bookNumber,
                book_name: bookName,
                page_count: pageCount
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSettingsMessage('addBookMessage', data.message, 'success');
            document.getElementById('newBookNumber').value = '';
            document.getElementById('newBookName').value = '';
            document.getElementById('newBookPages').value = '';
            loadBooks();
            loadBookDropdowns(); // Refresh dropdowns
        } else {
            showSettingsMessage('addBookMessage', data.error || 'Failed to add book', 'error');
        }
    } catch (error) {
        showSettingsMessage('addBookMessage', 'Error: ' + error.message, 'error');
    }
}

// Open edit book modal
function editBook(bookNumber, bookName, pageCount) {
    document.getElementById('editBookOldNumber').value = bookNumber;
    document.getElementById('editBookNumber').value = bookNumber;
    document.getElementById('editBookName').value = bookName;
    document.getElementById('editBookPages').value = pageCount || '';
    document.getElementById('editBookNumber').focus();
    document.getElementById('editBookModal').classList.add('show');
}

// Close edit book modal
function closeEditBookModal() {
    document.getElementById('editBookModal').classList.remove('show');
    document.getElementById('editBookForm').reset();
}

// Handle edit book form submission
async function handleEditBook(e) {
    e.preventDefault();

    const oldNumber = document.getElementById('editBookOldNumber').value.trim();
    const bookNumber = document.getElementById('editBookNumber').value.trim();
    const bookName = document.getElementById('editBookName').value.trim();
    const pageCount = document.getElementById('editBookPages').value.trim();

    if (!bookNumber || !bookName) {
        showSettingsMessage('bookManagementMessage', 'Book number and name are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/books/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                old_number: oldNumber,
                book_number: bookNumber,
                book_name: bookName,
                page_count: pageCount
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSettingsMessage('bookManagementMessage', data.message, 'success');
            closeEditBookModal();
            loadBooks();
            loadBookDropdowns(); // Refresh dropdowns
        } else {
            showSettingsMessage('bookManagementMessage', data.error || 'Failed to update book', 'error');
        }
    } catch (error) {
        showSettingsMessage('bookManagementMessage', 'Error: ' + error.message, 'error');
    }
}

// Delete book from modal
async function deleteBookFromModal() {
    const bookNumber = document.getElementById('editBookNumber').value.trim();

    try {
        // First, get the count of references and exclusions
        const countResponse = await fetch(`/api/books/reference-count/${bookNumber}`);
        const countData = await countResponse.json();

        if (!countResponse.ok) {
            showSettingsMessage('bookManagementMessage', countData.error || 'Failed to get reference count', 'error');
            return;
        }

        const refCount = countData.reference_count;
        const exclusionCount = countData.exclusion_count;

        // Build confirmation message
        let message = `Delete book ${bookNumber}?\n\nThis will permanently delete:\n`;
        message += `- The book registration\n`;
        if (refCount > 0) {
            message += `- ${refCount} page reference${refCount !== 1 ? 's' : ''}\n`;
        }
        if (exclusionCount > 0) {
            message += `- ${exclusionCount} gap exclusion${exclusionCount !== 1 ? 's' : ''}\n`;
        }
        message += `\nThis action cannot be undone.`;

        if (!confirm(message)) {
            return;
        }

        // Proceed with deletion
        const response = await fetch('/api/books/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ book_number: bookNumber })
        });

        const data = await response.json();

        if (response.ok) {
            showSettingsMessage('bookManagementMessage', data.message, 'success');
            closeEditBookModal();
            loadBooks();
            loadBookDropdowns(); // Refresh dropdowns
        } else {
            showSettingsMessage('bookManagementMessage', data.error || 'Failed to delete book', 'error');
        }
    } catch (error) {
        showSettingsMessage('bookManagementMessage', 'Error: ' + error.message, 'error');
    }
}

// Setup autocomplete for term input
function setupAutocomplete() {
    const input = document.getElementById('term');
    const autocompleteList = document.getElementById('autocomplete-list');

    if (!input || !autocompleteList) return;

    // Handle input changes
    input.addEventListener('input', function(e) {
        const value = this.value.trim();
        autocompleteIndex = -1;

        if (!value) {
            autocompleteList.classList.remove('show');
            autocompleteList.innerHTML = '';
            return;
        }

        // Filter existing terms
        const matches = allEntries
            .map(entry => entry.term)
            .filter(term => term.toLowerCase().includes(value.toLowerCase()))
            .sort((a, b) => {
                // Prioritize matches at the start
                const aStarts = a.toLowerCase().startsWith(value.toLowerCase());
                const bStarts = b.toLowerCase().startsWith(value.toLowerCase());
                if (aStarts && !bStarts) return -1;
                if (!aStarts && bStarts) return 1;
                return a.localeCompare(b);
            })
            .slice(0, 10); // Limit to 10 suggestions

        if (matches.length === 0) {
            autocompleteList.classList.remove('show');
            autocompleteList.innerHTML = '';
            return;
        }

        // Build autocomplete items
        let html = '';
        matches.forEach((term, index) => {
            // Highlight matching part
            const termLower = term.toLowerCase();
            const valueLower = value.toLowerCase();
            const matchIndex = termLower.indexOf(valueLower);

            let displayTerm = term;
            if (matchIndex >= 0) {
                displayTerm = term.substring(0, matchIndex) +
                    '<strong>' + term.substring(matchIndex, matchIndex + value.length) + '</strong>' +
                    term.substring(matchIndex + value.length);
            }

            html += `<div class="autocomplete-item" data-value="${escapeHtml(term)}">${displayTerm}</div>`;
        });

        autocompleteList.innerHTML = html;
        autocompleteList.classList.add('show');

        // Add click handlers to items
        const items = autocompleteList.querySelectorAll('.autocomplete-item');
        items.forEach(item => {
            item.addEventListener('click', async function() {
                const selectedTerm = this.getAttribute('data-value');
                lastAutocompleteTerm = selectedTerm;  // Track selected term BEFORE setting value
                input.value = selectedTerm;
                autocompleteList.classList.remove('show');
                autocompleteList.innerHTML = '';

                // Auto-populate notes for existing term
                await populateNotesForTerm(selectedTerm);

                document.getElementById('book').focus();
            });
        });
    });

    // Clear pre-loaded data when term is modified after autocomplete selection
    input.addEventListener('input', function() {
        if (lastAutocompleteTerm && input.value !== lastAutocompleteTerm) {
            // Term was modified after autocomplete selection - clear notes
            document.getElementById('notes').value = '';
            // Keep tracking - update to current value so we detect further changes
            // but notes are already cleared so it won't matter
        }
    });

    // Handle keyboard navigation
    input.addEventListener('keydown', function(e) {
        const items = autocompleteList.querySelectorAll('.autocomplete-item');

        if (items.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            autocompleteIndex = Math.min(autocompleteIndex + 1, items.length - 1);
            updateAutocompleteActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            autocompleteIndex = Math.max(autocompleteIndex - 1, -1);
            updateAutocompleteActive(items);
        } else if (e.key === 'Enter' || e.key === 'Tab') {
            if (autocompleteIndex >= 0) {
                e.preventDefault();
                const selectedTerm = items[autocompleteIndex].getAttribute('data-value');
                lastAutocompleteTerm = selectedTerm;  // Track selected term BEFORE setting value
                input.value = selectedTerm;
                autocompleteList.classList.remove('show');
                autocompleteList.innerHTML = '';
                autocompleteIndex = -1;

                // Auto-populate notes for existing term
                populateNotesForTerm(selectedTerm).then(() => {
                    if (e.key === 'Tab' || e.key === 'Enter') {
                        document.getElementById('book').focus();
                    }
                });
            }
        } else if (e.key === 'Escape') {
            autocompleteList.classList.remove('show');
            autocompleteList.innerHTML = '';
            autocompleteIndex = -1;
        }
    });

    // Close autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (e.target !== input) {
            autocompleteList.classList.remove('show');
            autocompleteList.innerHTML = '';
            autocompleteIndex = -1;
        }
    });
}

// Update active autocomplete item
function updateAutocompleteActive(items) {
    items.forEach((item, index) => {
        if (index === autocompleteIndex) {
            item.classList.add('active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('active');
        }
    });
}

// Populate notes for an existing term
async function populateNotesForTerm(term) {
    const notesTextarea = document.getElementById('notes');

    if (!term) return;

    // Check if this term already exists in our entries
    const existingEntry = allEntries.find(entry =>
        entry.term.toLowerCase() === term.toLowerCase()
    );

    if (existingEntry) {
        // Fetch notes for this term
        try {
            const response = await fetch('/api/notes');
            const data = await response.json();
            const noteEntry = data.notes.find(n => n.term.toLowerCase() === term.toLowerCase());

            if (noteEntry && noteEntry.notes) {
                // Only populate if notes field is currently empty
                if (!notesTextarea.value.trim()) {
                    notesTextarea.value = noteEntry.notes;
                }
            }
        } catch (error) {
            console.error('Error fetching notes:', error);
        }
    }
}

// Handle term field blur to auto-populate notes
async function handleTermBlur() {
    const termInput = document.getElementById('term');
    const term = termInput.value.trim();
    await populateNotesForTerm(term);
}

// Handle book dropdown change (for "Other" option)
function handleBookChange(e) {
    if (e.target.value === 'other') {
        // Set the source to track which dropdown triggered the modal
        document.getElementById('addBookSource').value = 'book';
        // Open the Add Book Modal
        document.getElementById('addBookModal').classList.add('show');
        document.getElementById('addBookModalNumber').focus();
        // Reset the dropdown to empty
        e.target.value = '';
    }
}

// Handle edit book dropdown change (for "Other" option)
function handleEditBookChange(e) {
    if (e.target.value === 'other') {
        // Set the source to track which dropdown triggered the modal
        document.getElementById('addBookSource').value = 'editBook';
        // Open the Add Book Modal
        document.getElementById('addBookModal').classList.add('show');
        document.getElementById('addBookModalNumber').focus();
        // Reset the dropdown to empty
        e.target.value = '';
    }
}

// Close add book modal
function closeAddBookModal() {
    document.getElementById('addBookModal').classList.remove('show');
    document.getElementById('addBookModalForm').reset();
}

// Handle add book modal form submission
async function handleAddBookModal(e) {
    e.preventDefault();

    const bookNumber = document.getElementById('addBookModalNumber').value.trim();
    const bookName = document.getElementById('addBookModalName').value.trim();
    const pageCount = document.getElementById('addBookModalPages').value.trim();
    const source = document.getElementById('addBookSource').value;

    if (!bookNumber || !bookName) {
        showMessage('Book number and name are required', 'error');
        return;
    }

    try {
        const response = await fetch('/api/books/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_number: bookNumber,
                book_name: bookName,
                page_count: pageCount
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');
            closeAddBookModal();

            // Refresh all book dropdowns
            await loadBookDropdowns();

            // Select the newly added book in the dropdown that triggered the modal
            if (source === 'book') {
                document.getElementById('book').value = bookNumber;
            } else if (source === 'editBook') {
                document.getElementById('editBook').value = bookNumber;
            }

            // If we're on the settings tab, refresh the books list
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab && activeTab.id === 'tab-settings') {
                loadBooks();
            }
        } else {
            showMessage(data.error || 'Failed to add book', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Handle book filter change
function handleBookFilter(e) {
    selectedBookFilter = e.target.value;
    // Reset letter selection when changing book filter
    selectedLetter = null;
    buildLetterNavigation();
    displayEntries(allEntries);
}

// Handle global keyboard shortcuts
function handleGlobalKeyboardShortcuts(e) {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modifierKey = isMac ? e.metaKey : e.ctrlKey;

    // Don't trigger shortcuts when typing in input fields (except Esc)
    const isInputField = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);

    // Esc - Close hamburger menu or modals
    if (e.key === 'Escape') {
        // Close hamburger menu first if open
        if (document.body.classList.contains('is-menu-visible')) {
            menuHide();
            return;
        }

        // Close any open modals
        if (document.getElementById('editModal').classList.contains('show')) {
            closeEditModal();
        } else if (document.getElementById('editNotesModal').classList.contains('show')) {
            closeEditNotesModal();
        } else if (document.getElementById('gapActionModal').classList.contains('show')) {
            closeGapActionModal();
        } else if (document.getElementById('reincludeModal').classList.contains('show')) {
            closeReincludeModal();
        } else if (document.getElementById('editBookModal').classList.contains('show')) {
            closeEditBookModal();
        } else if (document.getElementById('addBookModal').classList.contains('show')) {
            closeAddBookModal();
        } else if (document.getElementById('aboutModal').classList.contains('show')) {
            closeAboutModal();
        } else if (document.getElementById('helpModal').classList.contains('show')) {
            closeHelpModal();
        } else if (document.getElementById('cliModal').classList.contains('show')) {
            closeCliModal();
        } else if (document.getElementById('editBookPropertyModal').classList.contains('show')) {
            closeEditBookPropertyModal();
        }
        return;
    }

    // / (forward slash) - Focus search or term input (common pattern like GitHub/Slack)
    // Only when not in an input field
    if (e.key === '/' && !isInputField) {
        e.preventDefault();
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'tab-view') {
            document.getElementById('searchInput').focus();
        } else if (activeTab && activeTab.id === 'tab-add') {
            document.getElementById('term').focus();
        }
        return;
    }

    // Don't process other shortcuts if in an input field
    if (isInputField && e.key !== 'Escape') {
        return;
    }

    // Number keys 1-6 - Navigate between tabs
    const tabMap = {
        '1': 'add',
        '2': 'view',
        '3': 'progress',
        '4': 'books',
        '5': 'tools',
        '6': 'settings'
    };

    if (tabMap[e.key]) {
        e.preventDefault();
        switchTab(tabMap[e.key]);
    }

    // Ctrl/Cmd + S - Save current form (prevent browser save dialog)
    if (modifierKey && e.key === 's') {
        e.preventDefault();
        // Could trigger submit on active form if needed
    }
}

// Number-only validation for page fields
function setupNumberOnlyFields() {
    const numberFields = [
        document.getElementById('page'),
        document.getElementById('pageEnd'),
        document.getElementById('editPage'),
        document.getElementById('editPageEnd'),
        document.getElementById('settingsIndexYear'),
        document.getElementById('newBookNumber'),
        document.getElementById('editBookNumber'),
        document.getElementById('addBookModalNumber'),
        document.getElementById('createIndexBookNumber'),
        document.getElementById('getStartedBookNumber')
    ];

    numberFields.forEach(field => {
        if (field) {
            field.addEventListener('input', function(e) {
                // Remove any non-digit characters
                this.value = this.value.replace(/[^0-9]/g, '');
            });
        }
    });
}

// Progress chart instances (to destroy before re-rendering)
let progressCharts = {
    donut: null,
    density: null,
    stacked: null,
    treemap: null
};

// Chart colors
const chartColors = {
    indexed: '#4ade80',    // Green
    excluded: '#6b7280',   // Gray
    gaps: '#ef4444',       // Red
    primary: '#e94560'
};

// Run gap analysis
async function runGapAnalysis() {
    const resultsContainer = document.getElementById('gapAnalysisResults');
    resultsContainer.innerHTML = '<p class="loading">Running gap analysis...</p>';

    try {
        const response = await fetch('/api/gap-analysis');
        const data = await response.json();

        if (response.ok) {
            displayGapAnalysis(data.results);
            updateProgressCharts(data.results);
        } else {
            resultsContainer.innerHTML = `<p class="empty-state error">${data.error || 'Failed to run gap analysis'}</p>`;
        }
    } catch (error) {
        resultsContainer.innerHTML = `<p class="empty-state error">Error: ${error.message}</p>`;
    }
}

// Calculate book stats from gap analysis result
function calculateBookStats(book) {
    const pageCount = book.page_count || 0;
    if (pageCount === 0) return { indexed: 0, excluded: 0, gaps: 0 };

    // Count gap pages
    let gapPages = 0;
    (book.gaps || []).forEach(gap => {
        if (gap.includes('-')) {
            const [start, end] = gap.split('-').map(Number);
            gapPages += end - start + 1;
        } else {
            gapPages += 1;
        }
    });

    // Count excluded pages
    let excludedPages = 0;
    (book.excluded || []).forEach(exc => {
        if (exc.includes('-')) {
            const [start, end] = exc.split('-').map(Number);
            excludedPages += end - start + 1;
        } else {
            excludedPages += 1;
        }
    });

    const indexedPages = pageCount - gapPages - excludedPages;

    return {
        indexed: Math.max(0, indexedPages),
        excluded: excludedPages,
        gaps: gapPages
    };
}

// Update progress charts
function updateProgressCharts(results) {
    // Update summary stats
    updateProgressSummaryStats(results);

    // Filter books with page counts for charts
    const booksWithPages = results.filter(b => b.page_count > 0);

    // Render charts
    renderProgressDonutChart(booksWithPages);
    renderProgressDensityChart(booksWithPages);
    renderProgressStackedBarChart(booksWithPages);
    renderProgressTreemapChart(booksWithPages);
}

// Update summary stats cards
function updateProgressSummaryStats(results) {
    const booksWithPages = results.filter(b => b.page_count > 0);
    let totalPages = 0;
    let totalIndexed = 0;

    booksWithPages.forEach(book => {
        const stats = calculateBookStats(book);
        totalPages += book.page_count;
        totalIndexed += stats.indexed + stats.excluded;
    });

    document.getElementById('statTotalBooks').textContent = results.length;
    document.getElementById('statTotalPages').textContent = totalPages.toLocaleString();
    document.getElementById('statIndexedPages').textContent = totalIndexed.toLocaleString();

    const progress = totalPages > 0 ? Math.round((totalIndexed / totalPages) * 100) : 0;
    document.getElementById('statOverallProgress').textContent = progress + '%';
}

// Render donut chart
function renderProgressDonutChart(booksWithPages) {
    // Destroy existing chart if any
    if (progressCharts.donut) {
        progressCharts.donut.destroy();
    }

    let totalIndexed = 0, totalExcluded = 0, totalGaps = 0;

    booksWithPages.forEach(book => {
        const stats = calculateBookStats(book);
        totalIndexed += stats.indexed;
        totalExcluded += stats.excluded;
        totalGaps += stats.gaps;
    });

    const options = {
        series: [totalIndexed, totalExcluded, totalGaps],
        chart: {
            type: 'donut',
            height: 280,
            background: 'transparent',
            toolbar: { show: false }
        },
        labels: ['Indexed', 'Excluded', 'Gaps'],
        colors: [chartColors.indexed, chartColors.excluded, chartColors.gaps],
        legend: {
            position: 'bottom',
            labels: { colors: '#585858' }
        },
        plotOptions: {
            pie: {
                donut: {
                    size: '65%',
                    labels: {
                        show: true,
                        total: {
                            show: true,
                            label: 'Total Pages',
                            color: '#585858',
                            formatter: () => (totalIndexed + totalExcluded + totalGaps).toLocaleString()
                        }
                    }
                }
            }
        },
        dataLabels: {
            enabled: true,
            formatter: (val) => Math.round(val) + '%'
        },
        stroke: {
            show: false
        }
    };

    const container = document.getElementById('progressDonutChart');
    if (container) {
        progressCharts.donut = new ApexCharts(container, options);
        progressCharts.donut.render();
    }
}

// Render density chart
function renderProgressDensityChart(booksWithPages) {
    // Destroy existing chart if any
    if (progressCharts.density) {
        progressCharts.density.destroy();
    }

    // Store full labels for tooltips
    const fullLabels = booksWithPages.map(b => `Book ${b.book_number}: ${b.book_name}`);

    // Use book number only for display
    const categories = booksWithPages.map(b => `Book ${b.book_number}`);

    const densities = booksWithPages.map(b => {
        const density = (b.term_count / b.page_count) * 100;
        return Math.round(density * 10) / 10;
    });

    const options = {
        series: [{
            name: 'Terms per 100 pages',
            data: densities
        }],
        chart: {
            type: 'bar',
            height: 280,
            background: 'transparent',
            toolbar: { show: false }
        },
        plotOptions: {
            bar: {
                horizontal: true,
                borderRadius: 4
            }
        },
        colors: [chartColors.primary],
        xaxis: {
            categories: categories,
            title: { text: 'Terms per 100 pages', style: { color: '#585858' } },
            labels: { style: { colors: '#585858' } }
        },
        yaxis: {
            labels: { style: { colors: '#585858' } }
        },
        dataLabels: {
            enabled: true,
            formatter: (val) => val.toFixed(1),
            style: { colors: ['#fff'] }
        },
        tooltip: {
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const value = series[seriesIndex][dataPointIndex];
                const fullLabel = fullLabels[dataPointIndex];
                return '<div style="padding: 8px 12px; background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">' +
                    '<div style="font-weight: 600; color: #585858; margin-bottom: 4px;">' + fullLabel + '</div>' +
                    '<div style="color: #e94560;">' + value.toFixed(1) + ' terms per 100 pages</div>' +
                    '</div>';
            }
        },
        grid: {
            borderColor: '#e5e7eb'
        }
    };

    const container = document.getElementById('progressDensityChart');
    if (container) {
        progressCharts.density = new ApexCharts(container, options);
        progressCharts.density.render();
    }
}

// Render stacked bar chart
function renderProgressStackedBarChart(booksWithPages) {
    // Destroy existing chart if any
    if (progressCharts.stacked) {
        progressCharts.stacked.destroy();
    }

    // Store full labels for tooltips
    const fullLabels = booksWithPages.map(b => `Book ${b.book_number}: ${b.book_name}`);

    // Use book number only for display
    const categories = booksWithPages.map(b => `Book ${b.book_number}`);

    const indexedData = [];
    const excludedData = [];
    const gapsData = [];

    booksWithPages.forEach(book => {
        const stats = calculateBookStats(book);
        indexedData.push(stats.indexed);
        excludedData.push(stats.excluded);
        gapsData.push(stats.gaps);
    });

    const options = {
        series: [
            { name: 'Indexed', data: indexedData },
            { name: 'Excluded', data: excludedData },
            { name: 'Gaps', data: gapsData }
        ],
        chart: {
            type: 'bar',
            height: 280,
            stacked: true,
            stackType: '100%',
            background: 'transparent',
            toolbar: { show: false }
        },
        plotOptions: {
            bar: {
                horizontal: true,
                borderRadius: 4
            }
        },
        colors: [chartColors.indexed, chartColors.excluded, chartColors.gaps],
        xaxis: {
            categories: categories,
            labels: { style: { colors: '#585858' } }
        },
        yaxis: {
            labels: { style: { colors: '#585858' } }
        },
        legend: {
            position: 'top',
            labels: { colors: '#585858' }
        },
        tooltip: {
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const fullLabel = fullLabels[dataPointIndex];
                const indexed = indexedData[dataPointIndex];
                const excluded = excludedData[dataPointIndex];
                const gaps = gapsData[dataPointIndex];
                return '<div style="padding: 8px 12px; background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">' +
                    '<div style="font-weight: 600; color: #585858; margin-bottom: 4px;">' + fullLabel + '</div>' +
                    '<div style="color: #4ade80;">Indexed: ' + indexed + ' pages</div>' +
                    '<div style="color: #6b7280;">Excluded: ' + excluded + ' pages</div>' +
                    '<div style="color: #ef4444;">Gaps: ' + gaps + ' pages</div>' +
                    '</div>';
            }
        },
        grid: {
            borderColor: '#e5e7eb'
        }
    };

    const container = document.getElementById('progressStackedBarChart');
    if (container) {
        progressCharts.stacked = new ApexCharts(container, options);
        progressCharts.stacked.render();
    }
}

// Render treemap chart for gap distribution
function renderProgressTreemapChart(booksWithPages) {
    // Destroy existing chart if any
    if (progressCharts.treemap) {
        progressCharts.treemap.destroy();
    }

    const container = document.getElementById('progressTreemapChart');
    if (!container) return;

    // Store full labels for tooltips
    const fullLabels = {};
    booksWithPages.forEach(book => {
        fullLabels[`Book ${book.book_number}`] = `Book ${book.book_number}: ${book.book_name}`;
    });

    const data = booksWithPages.map(book => {
        const stats = calculateBookStats(book);
        return {
            x: `Book ${book.book_number}`,
            y: stats.gaps
        };
    }).filter(d => d.y > 0); // Only show books with gaps

    if (data.length === 0) {
        container.innerHTML = '<div style="display:flex;justify-content:center;align-items:center;height:100%;color:#585858;font-size:0.95rem;">No gaps to display - all pages indexed!</div>';
        return;
    }

    const options = {
        series: [{
            data: data
        }],
        chart: {
            type: 'treemap',
            height: 280,
            background: 'transparent',
            toolbar: { show: false }
        },
        colors: [chartColors.gaps],
        plotOptions: {
            treemap: {
                distributed: false,
                enableShades: true,
                shadeIntensity: 0.5
            }
        },
        dataLabels: {
            enabled: true,
            formatter: (text, op) => {
                return [text, op.value + ' pages'];
            },
            style: {
                fontSize: '12px'
            }
        },
        tooltip: {
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const dataPoint = w.config.series[seriesIndex].data[dataPointIndex];
                const bookKey = dataPoint.x;
                const fullLabel = fullLabels[bookKey] || bookKey;
                const value = dataPoint.y;
                return '<div style="padding: 8px 12px; background: #fff; border: 1px solid #e5e7eb; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">' +
                    '<div style="font-weight: 600; color: #585858; margin-bottom: 4px;">' + fullLabel + '</div>' +
                    '<div style="color: #ef4444;">' + value + ' gap pages</div>' +
                    '</div>';
            }
        }
    };

    progressCharts.treemap = new ApexCharts(container, options);
    progressCharts.treemap.render();
}

// Display gap analysis results
function displayGapAnalysis(results) {
    const container = document.getElementById('gapAnalysisResults');

    if (results.length === 0) {
        container.innerHTML = '<p class="empty-state">No books found. Add books in Settings to perform gap analysis.</p>';
        return;
    }

    let html = '<div class="gap-analysis-results">';

    results.forEach(result => {
        const totalPages = result.page_count;

        html += `<div class="gap-book">`;
        html += `<div class="gap-book-header" onclick="toggleGapBookExpand('${escapeHtml(result.book_number)}')">`;
        html += `<div class="gap-book-info">`;
        html += `<span class="gap-expand-icon" id="gapExpandIcon_${result.book_number}">▶</span>`;
        html += `<h3>Book ${escapeHtml(result.book_number)}: ${escapeHtml(result.book_name)}</h3>`;
        html += `</div>`;

        // Check if page count is set
        if (!totalPages || totalPages === 0) {
            html += `<span class="gap-header-status gap-header-warning">No page count</span>`;
            html += `</div>`; // Close gap-book-header
            html += `<div class="gap-book-details" id="gapDetails_${result.book_number}" style="display: none;">`;
            html += `<div class="gap-no-pagecount">`;
            html += `<p>A page count must be set for gap analysis to be performed on this book.</p>`;
            html += `<p><a href="#" onclick="switchTab('books'); return false;">Set page count in Books</a></p>`;
            html += `</div>`;
            html += `</div>`; // Close gap-book-details
            html += `</div>`; // Close gap-book
            return;
        }

        const gapsCount = result.gaps.length;

        // Calculate gap pages
        const gapPages = result.gaps.reduce((sum, gap) => {
            if (gap.includes('-')) {
                const [start, end] = gap.split('-').map(Number);
                return sum + (end - start + 1);
            }
            return sum + 1;
        }, 0);

        // Calculate excluded pages
        const excludedPages = (result.excluded || []).reduce((sum, gap) => {
            if (gap.includes('-')) {
                const [start, end] = gap.split('-').map(Number);
                return sum + (end - start + 1);
            }
            return sum + 1;
        }, 0);

        const coveredPages = totalPages - gapPages;
        const coveragePercent = totalPages > 0 ? ((coveredPages / totalPages) * 100).toFixed(1) : 0;

        // Show coverage status in header
        if (gapsCount === 0) {
            html += `<span class="gap-header-status gap-header-complete">${coveragePercent}% Complete</span>`;
        } else {
            html += `<span class="gap-header-status">${coveragePercent}% Coverage</span>`;
        }
        html += `</div>`; // Close gap-book-header

        // Collapsible details section
        html += `<div class="gap-book-details" id="gapDetails_${result.book_number}" style="display: none;">`;

        const exclusionCount = (result.excluded || []).length;

        // Calculate term density (terms per 100 pages)
        const termDensity = totalPages > 0 ? ((result.term_count || 0) / totalPages * 100).toFixed(1) : 0;

        html += `<div class="gap-stats">`;
        html += `<span class="gap-stat">Total Pages: ${totalPages}</span>`;
        html += `<span class="gap-stat">Indexed Terms: ${result.term_count || 0}</span>`;
        html += `<span class="gap-stat">Term Density: ${termDensity}/100pg</span>`;
        html += `<span class="gap-stat">Coverage: ${coveragePercent}%</span>`;
        html += `<span class="gap-stat">Gap Ranges: ${gapsCount}</span>`;
        if (exclusionCount > 0) {
            html += `<span class="gap-stat">Exclusion Ranges: ${exclusionCount}</span>`;
        }
        if (excludedPages > 0) {
            html += `<span class="gap-stat">Excluded Pages: ${excludedPages}</span>`;
        }
        html += `</div>`;

        if (result.gaps.length === 0 && (result.excluded || []).length === 0) {
            html += `<p class="gap-complete">✓ All pages indexed!</p>`;
        } else {
            if (result.gaps.length > 0) {
                html += `<div class="gap-list">`;
                html += `<strong>Missing pages:</strong> `;
                html += result.gaps.map(gap =>
                    `<span class="gap-range clickable" onclick="handleGapRangeClick('${escapeHtml(result.book_number)}', '${escapeHtml(gap)}')">${escapeHtml(gap)}</span>`
                ).join(', ');
                html += `</div>`;
            }

            if (result.excluded && result.excluded.length > 0) {
                html += `<div class="gap-list excluded-list">`;
                html += `<strong>Page exclusions:</strong> `;
                html += result.excluded.map(gap =>
                    `<span class="gap-range excluded clickable" onclick="reincludeGapRange('${escapeHtml(result.book_number)}', '${escapeHtml(gap)}')">${escapeHtml(gap)}</span>`
                ).join(', ');
                html += `</div>`;
            }
        }

        html += `</div>`; // Close gap-book-details
        html += `</div>`; // Close gap-book
    });

    html += '</div>';
    container.innerHTML = html;
}

// Toggle gap book expand/collapse
function toggleGapBookExpand(bookNumber) {
    const details = document.getElementById(`gapDetails_${bookNumber}`);
    const icon = document.getElementById(`gapExpandIcon_${bookNumber}`);

    if (details.style.display === 'none') {
        details.style.display = 'block';
        icon.textContent = '▼';
    } else {
        details.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Store current gap action context
let currentGapAction = {
    bookNumber: null,
    pageRange: null
};

// Handle click on gap range - present options
function handleGapRangeClick(bookNumber, pageRange) {
    currentGapAction.bookNumber = bookNumber;
    currentGapAction.pageRange = pageRange;

    document.getElementById('gapActionTitle').textContent = `Missing Pages: ${pageRange}`;
    document.getElementById('gapActionMessage').textContent = `Book ${bookNumber} - What would you like to do with pages ${pageRange}?`;
    document.getElementById('gapActionModal').classList.add('show');
}

// Close gap action modal
function closeGapActionModal() {
    document.getElementById('gapActionModal').classList.remove('show');
    currentGapAction.bookNumber = null;
    currentGapAction.pageRange = null;
}

// Handle create reference action from modal
function gapActionCreateReference() {
    // Save values before closing modal (which nulls them)
    const bookNumber = currentGapAction.bookNumber;
    const pageRange = currentGapAction.pageRange;
    closeGapActionModal();
    createReferenceFromGap(bookNumber, pageRange);
}

// Handle exclude action from modal
function gapActionExclude() {
    // Save values before closing modal (which nulls them)
    const bookNumber = currentGapAction.bookNumber;
    const pageRange = currentGapAction.pageRange;
    closeGapActionModal();
    excludeGapRange(bookNumber, pageRange);
}

// Create reference from gap range
function createReferenceFromGap(bookNumber, pageRange) {
    // Parse the page range to get the start page
    let startPage;
    if (pageRange.includes('-')) {
        startPage = pageRange.split('-')[0];
    } else {
        startPage = pageRange;
    }

    // Switch to Add Entry tab
    switchTab('add');

    // Use setTimeout to ensure tab switch completes before setting values
    setTimeout(() => {
        // Pre-populate the form
        document.getElementById('book').value = bookNumber;
        document.getElementById('page').value = startPage;
        document.getElementById('pageEnd').value = '';

        // Clear term and notes
        document.getElementById('term').value = '';
        document.getElementById('notes').value = '';

        // Focus on term field
        document.getElementById('term').focus();

        showMessage(`Book ${bookNumber}, page ${startPage} - ready to add reference`, 'success');
    }, 100);
}

// Exclude a gap range from analysis
async function excludeGapRange(bookNumber, pageRange) {
    try {
        const response = await fetch('/api/gap-exclusions/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_number: bookNumber,
                page_range: pageRange
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');
            runGapAnalysis(); // Refresh the analysis
        } else {
            showMessage(data.error || 'Failed to exclude range', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Store current re-include action context
let currentReincludeAction = {
    bookNumber: null,
    pageRange: null
};

// Handle click on excluded range - show re-include modal
function reincludeGapRange(bookNumber, pageRange) {
    currentReincludeAction.bookNumber = bookNumber;
    currentReincludeAction.pageRange = pageRange;

    document.getElementById('reincludeTitle').textContent = `Re-include Pages: ${pageRange}`;
    document.getElementById('reincludeMessage').textContent = `Book ${bookNumber} - Re-including pages ${pageRange} will make them appear as gaps again in the gap analysis.`;
    document.getElementById('reincludeModal').classList.add('show');
}

// Close re-include modal
function closeReincludeModal() {
    document.getElementById('reincludeModal').classList.remove('show');
    currentReincludeAction.bookNumber = null;
    currentReincludeAction.pageRange = null;
}

// Confirm re-include action
async function confirmReinclude() {
    // Save values before closing modal
    const bookNumber = currentReincludeAction.bookNumber;
    const pageRange = currentReincludeAction.pageRange;
    closeReincludeModal();

    try {
        const response = await fetch('/api/gap-exclusions/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                book_number: bookNumber,
                page_range: pageRange
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage(data.message, 'success');
            runGapAnalysis(); // Refresh the analysis
        } else {
            showMessage(data.error || 'Failed to re-include pages', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}


// ===================================
// AI Term Enrichment Functions
// ===================================

// Load AI enrichment settings
async function loadAiEnrichment() {
    try {
        const response = await fetch('/api/ai/settings');
        const data = await response.json();

        const checkbox = document.getElementById('enableAiFeatures');
        const hint = document.getElementById('enableAiHint');
        const enrichBtn = document.getElementById('enrichApiBtn');

        checkbox.checked = data.enabled;
        document.getElementById('aiProvider').value = data.provider || '';
        // Don't populate the API key field for security - just show placeholder
        document.getElementById('aiApiKey').placeholder = data.has_key ? '••••••••••••••••' : 'Enter your API key';

        // Enable checkbox only if API key is configured
        if (data.has_key) {
            checkbox.disabled = false;
            hint.style.display = 'none';
        } else {
            checkbox.disabled = true;
            checkbox.checked = false;
            hint.style.display = 'block';
        }

        // Show enrich button if enabled and API key is configured
        if (data.enabled && data.has_key) {
            enrichBtn.style.display = 'inline-block';
        } else {
            enrichBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading AI settings:', error);
    }
}

// Save AI settings
async function saveAiSettings() {
    const provider = document.getElementById('aiProvider').value;
    const apiKey = document.getElementById('aiApiKey').value;
    const enabled = document.getElementById('enableAiFeatures').checked;
    const messageDiv = document.getElementById('aiSettingsMessage');

    try {
        const response = await fetch('/api/ai/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled: enabled,
                provider: provider,
                api_key: apiKey || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.className = 'message success show';
            messageDiv.textContent = 'AI settings saved successfully';

            // If API key was provided, enable the checkbox
            if (apiKey) {
                document.getElementById('aiApiKey').value = '';
                document.getElementById('aiApiKey').placeholder = '••••••••••••••••';
                document.getElementById('enableAiFeatures').disabled = false;
                document.getElementById('enableAiHint').style.display = 'none';
            }

            // Show the enrich button only if enabled
            if (enabled) {
                document.getElementById('enrichApiBtn').style.display = 'inline-block';
            }

            setTimeout(() => {
                messageDiv.className = 'message';
                messageDiv.textContent = '';
            }, 3000);
        } else {
            messageDiv.className = 'message error show';
            messageDiv.textContent = data.error || 'Failed to save settings';
        }
    } catch (error) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Error: ' + error.message;
    }
}

// Validate AI API key
async function validateAiApiKey() {
    const provider = document.getElementById('aiProvider').value;
    const apiKey = document.getElementById('aiApiKey').value;
    const btn = document.getElementById('validateKeyBtn');
    const statusEl = document.getElementById('apiKeyValidationStatus');

    if (!provider) {
        statusEl.textContent = 'Please select an AI Provider first';
        statusEl.style.display = 'block';
        statusEl.style.color = 'var(--warning-color, #f59e0b)';
        return;
    }

    if (!apiKey) {
        statusEl.textContent = 'Please enter an API key';
        statusEl.style.display = 'block';
        statusEl.style.color = 'var(--warning-color, #f59e0b)';
        return;
    }

    const originalText = btn.textContent;
    btn.textContent = 'Validating...';
    btn.disabled = true;
    statusEl.style.display = 'none';

    try {
        const response = await fetch('/api/ai/validate-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey
            })
        });

        const data = await response.json();

        statusEl.style.display = 'block';
        if (data.valid) {
            statusEl.textContent = 'API key is valid';
            statusEl.style.color = 'var(--success-color, #10b981)';
        } else {
            statusEl.textContent = data.message || 'Invalid API key';
            statusEl.style.color = 'var(--error-color, #ef4444)';
        }
    } catch (error) {
        statusEl.style.display = 'block';
        statusEl.textContent = 'Validation failed: ' + error.message;
        statusEl.style.color = 'var(--error-color, #ef4444)';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Clear API key from database
async function clearAiApiKey() {
    const messageDiv = document.getElementById('aiSettingsMessage');

    try {
        const response = await fetch('/api/ai/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                enabled: false,  // Disable AI features when clearing key
                provider: document.getElementById('aiProvider').value,
                api_key: '',
                clear_key: true
            })
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.className = 'message success show';
            messageDiv.textContent = 'API key cleared';
            document.getElementById('aiApiKey').value = '';
            document.getElementById('aiApiKey').placeholder = 'Enter your API key';
            document.getElementById('enableAiFeatures').checked = false;
            document.getElementById('enableAiFeatures').disabled = true;
            document.getElementById('enableAiHint').style.display = 'block';
            document.getElementById('enrichApiBtn').style.display = 'none';

            setTimeout(() => {
                messageDiv.className = 'message';
                messageDiv.textContent = '';
            }, 3000);
        } else {
            messageDiv.className = 'message error show';
            messageDiv.textContent = data.error || 'Failed to clear API key';
        }
    } catch (error) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Error: ' + error.message;
    }
}

// Copy AI prompt to clipboard for manual workflow
async function copyAiPrompt() {
    const messageDiv = document.getElementById('aiMessage');

    try {
        // Get the selected AI provider from settings
        const provider = document.getElementById('aiProvider').value;

        if (!provider) {
            messageDiv.className = 'message warning show';
            messageDiv.textContent = 'Please select an AI Provider in the Settings tab first.';
            setTimeout(() => {
                messageDiv.className = 'message';
                messageDiv.textContent = '';
            }, 5000);
            return;
        }

        // Load prompts from API
        const promptsResponse = await fetch('/api/ai/prompts');
        const promptsData = await promptsResponse.json();

        if (!promptsData.prompts[provider]) {
            messageDiv.className = 'message error show';
            messageDiv.textContent = 'No prompt configured for this provider.';
            return;
        }

        // Get terms without notes from the API
        const termsResponse = await fetch('/api/ai/terms?without_notes=true');
        const termsData = await termsResponse.json();

        if (!termsData.terms || termsData.terms.length === 0) {
            messageDiv.className = 'message warning show';
            messageDiv.textContent = 'No terms without notes to enrich. All terms already have notes.';
            setTimeout(() => {
                messageDiv.className = 'message';
                messageDiv.textContent = '';
            }, 3000);
            return;
        }

        // Build the term list
        const termPrefix = promptsData.term_prefix || '- ';
        const termSeparator = promptsData.term_list_separator || '\n';
        const termList = termsData.terms.map(t => termPrefix + t.term).join(termSeparator);

        // Get index name for $course_title replacement
        const indexName = document.getElementById('indexName').textContent || 'Untitled Index';

        // Get model from prompts config
        const model = promptsData.prompts[provider].model || '';

        // Combine the prompt with the term list, replacing placeholders
        let promptTemplate = promptsData.prompts[provider].prompt;
        promptTemplate = promptTemplate.replace(/\$course_title/g, indexName);
        promptTemplate = promptTemplate.replace(/\$model/g, model);
        const fullPrompt = promptTemplate + '\n' + termList;

        // Copy to clipboard
        await navigator.clipboard.writeText(fullPrompt);

        const providerName = promptsData.prompts[provider].name;
        messageDiv.className = 'message success show';
        messageDiv.textContent = `Copied ${providerName} prompt with ${termsData.terms.length} terms to clipboard.`;
        setTimeout(() => {
            messageDiv.className = 'message';
            messageDiv.textContent = '';
        }, 5000);
    } catch (error) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Error copying prompt: ' + error.message;
    }
}

// Enrich terms using API
async function enrichTermsWithApi() {
    const btn = document.getElementById('enrichApiBtn');
    const messageDiv = document.getElementById('aiMessage');
    const originalText = btn.textContent;
    btn.textContent = 'Enriching...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/ai/enrich', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.className = 'message success show';
            messageDiv.textContent = data.message;
            setTimeout(() => {
                messageDiv.className = 'message';
                messageDiv.textContent = '';
            }, 5000);
        } else {
            messageDiv.className = 'message error show';
            messageDiv.textContent = data.error || 'Failed to enrich terms';
        }
    } catch (error) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Error: ' + error.message;
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}


// ===================================
// Study Mode Functions
// ===================================

let studyCards = [];
let currentCardIndex = 0;

// Initialize study mode filter dropdown
function initStudyMode() {
    const filterSelect = document.getElementById('studyFilter');
    const bookFilterDiv = document.getElementById('studyBookFilter');
    const bookSelect = document.getElementById('studyBookSelect');

    filterSelect.addEventListener('change', async function() {
        if (this.value === 'book') {
            bookFilterDiv.style.display = 'block';
            // Populate book dropdown
            try {
                const response = await fetch('/api/books');
                const data = await response.json();
                bookSelect.innerHTML = '';
                data.books.forEach(book => {
                    const option = document.createElement('option');
                    option.value = book.book_number;
                    option.textContent = `Book ${book.book_number}: ${book.book_name}`;
                    bookSelect.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading books:', error);
            }
        } else {
            bookFilterDiv.style.display = 'none';
        }
    });
}

// Start study session
async function startStudyMode() {
    const filterType = document.getElementById('studyFilter').value;
    const shuffle = document.getElementById('studyShuffle').checked;

    try {
        // Fetch terms with notes
        const response = await fetch('/api/notes');
        const data = await response.json();

        if (!data.notes || data.notes.length === 0) {
            alert('No terms with notes found. Add notes to your terms first.');
            return;
        }

        // Filter cards based on selection
        let cards = data.notes;

        if (filterType === 'book') {
            const bookNumber = document.getElementById('studyBookSelect').value;
            // Need to fetch entries to filter by book
            const entriesResponse = await fetch('/api/entries');
            const entriesData = await entriesResponse.json();

            // Get terms that have references in the selected book
            const termsInBook = new Set();
            entriesData.entries.forEach(entry => {
                if (entry.references) {
                    entry.references.forEach(ref => {
                        if (ref.startsWith(bookNumber + ':')) {
                            termsInBook.add(entry.term.toLowerCase());
                        }
                    });
                }
            });

            cards = cards.filter(card => termsInBook.has(card.term.toLowerCase()));

            if (cards.length === 0) {
                alert('No terms with notes found for the selected book.');
                return;
            }
        }

        // Shuffle if enabled
        if (shuffle) {
            cards = shuffleArray([...cards]);
        }

        studyCards = cards;
        currentCardIndex = 0;

        // Fetch references for all terms
        const entriesResponse = await fetch('/api/entries');
        const entriesData = await entriesResponse.json();
        const refsMap = {};
        entriesData.entries.forEach(entry => {
            refsMap[entry.term.toLowerCase()] = entry.references || [];
        });

        // Add references to cards
        studyCards = studyCards.map(card => ({
            ...card,
            references: refsMap[card.term.toLowerCase()] || []
        }));

        // Show study overlay
        document.getElementById('studyOverlay').classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
        document.addEventListener('keydown', handleStudyKeyboard);

        showCurrentCard();
    } catch (error) {
        console.error('Error starting study mode:', error);
        alert('Error starting study session: ' + error.message);
    }
}

// Keyboard handler for study mode
function handleStudyKeyboard(e) {
    // Don't handle if study overlay is not active
    if (!document.getElementById('studyOverlay').classList.contains('active')) return;

    // Don't handle if typing in an input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    switch (e.key.toLowerCase()) {
        case 'n':
            nextFlashcard();
            break;
        case 'p':
            prevFlashcard();
            break;
        case ' ':  // Spacebar to flip
            e.preventDefault();
            flipFlashcard();
            break;
        case 'escape':
            endStudyMode();
            break;
        case 'enter':
            // Prevent Enter from activating focused buttons
            e.preventDefault();
            break;
    }
}

// End study session
function endStudyMode() {
    document.getElementById('studyOverlay').classList.remove('active');
    document.body.style.overflow = ''; // Restore scrolling
    document.removeEventListener('keydown', handleStudyKeyboard);
    resetStudyOverlay();
    studyCards = [];
    currentCardIndex = 0;
}

// Reset study overlay to initial state
function resetStudyOverlay() {
    const container = document.querySelector('.study-session-container');
    container.innerHTML = `
        <div class="study-header">
            <div class="study-progress">
                <span id="studyProgress">0 / 0</span>
            </div>
            <button type="button" class="btn-end-session" onclick="endStudyMode()" title="End Session">&times;</button>
        </div>

        <div class="flashcard-wrapper">
            <div class="flashcard" id="flashcard" onclick="flipFlashcard()">
                <div class="flashcard-inner" id="flashcardInner">
                    <div class="flashcard-front">
                        <div class="flashcard-term" id="flashcardTerm"></div>
                        <div class="flashcard-hint">Click to reveal</div>
                    </div>
                    <div class="flashcard-back">
                        <div class="flashcard-term" id="flashcardTermBack"></div>
                        <div class="flashcard-notes" id="flashcardNotes"></div>
                        <div class="flashcard-refs" id="flashcardRefs"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="study-controls">
            <button type="button" class="btn btn-secondary" onclick="prevFlashcard()" id="prevCardBtn">Previous</button>
            <button type="button" class="btn btn-primary" onclick="nextFlashcard()" id="nextCardBtn">Next</button>
        </div>
    `;
}

// Show current flashcard
function showCurrentCard() {
    if (studyCards.length === 0) return;

    const card = studyCards[currentCardIndex];
    const flashcard = document.getElementById('flashcard');

    // Reset flip state
    flashcard.classList.remove('flipped');

    // Update card content
    document.getElementById('flashcardTerm').textContent = card.term;
    document.getElementById('flashcardTermBack').textContent = card.term;
    document.getElementById('flashcardNotes').textContent = card.notes;

    // Show references if available
    const refsEl = document.getElementById('flashcardRefs');
    if (card.references && card.references.length > 0) {
        refsEl.textContent = 'References: ' + card.references.join(', ');
    } else {
        refsEl.textContent = '';
    }

    // Update progress
    document.getElementById('studyProgress').textContent = `${currentCardIndex + 1} / ${studyCards.length}`;

    // Update button states
    document.getElementById('prevCardBtn').disabled = currentCardIndex === 0;
    document.getElementById('nextCardBtn').textContent = currentCardIndex === studyCards.length - 1 ? 'Finish' : 'Next';
}

// Flip flashcard
function flipFlashcard() {
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.toggle('flipped');
}

// Previous flashcard
function prevFlashcard() {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        showCurrentCard();
    }
}

// Next flashcard
function nextFlashcard() {
    if (currentCardIndex < studyCards.length - 1) {
        currentCardIndex++;
        showCurrentCard();
    } else {
        // Study session complete
        showStudyComplete();
    }
}

// Show study complete screen
function showStudyComplete() {
    const container = document.querySelector('.study-session-container');
    container.innerHTML = `
        <div class="study-complete">
            <h3>Session Complete!</h3>
            <p>You reviewed ${studyCards.length} cards.</p>
            <div style="display: flex; gap: 1rem; justify-content: center;">
                <button type="button" class="btn btn-secondary" onclick="restartStudySession()">Study Again</button>
                <button type="button" class="btn btn-primary" onclick="endStudyMode()">Done</button>
            </div>
        </div>
    `;
}

// Restart study session with same cards
function restartStudySession() {
    const shuffle = document.getElementById('studyShuffle').checked;
    if (shuffle) {
        studyCards = shuffleArray([...studyCards]);
    }
    currentCardIndex = 0;

    // Restore session UI
    resetStudyOverlay();
    showCurrentCard();
}

// Shuffle array (Fisher-Yates algorithm)
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}


// ===================================
// Database Management Functions
// ===================================

// Show/hide database switcher dropdown
async function showDatabaseSwitcher() {
    const switcher = document.getElementById('databaseSwitcher');

    if (switcher.style.display === 'block') {
        switcher.style.display = 'none';
        return;
    }

    try {
        // Fetch available databases
        const response = await fetch('/api/databases/list');
        const data = await response.json();

        // Build dropdown list
        const listDiv = switcher.querySelector('.database-list');
        listDiv.innerHTML = '<h3>Switch Index</h3>';

        if (data.databases.length === 0) {
            listDiv.innerHTML += '<p>No databases found</p>';
        } else {
            const ul = document.createElement('ul');

            data.databases.forEach(db => {
                const li = document.createElement('li');
                const isActive = db.db_name === data.active;
                li.innerHTML = `<a href="#" onclick="switchDatabase('${db.db_name}'); return false;">
                    ${isActive ? '✓ ' : ''}${db.index_name}
                </a>`;
                if (isActive) {
                    li.classList.add('active');
                }
                ul.appendChild(li);
            });

            listDiv.appendChild(ul);
        }

        // Add "Create new index" link at the bottom
        const createLink = document.createElement('div');
        createLink.className = 'database-switcher-create';
        createLink.innerHTML = '<a href="#" onclick="showCreateIndexModal(); return false;">+ Create new index</a>';
        listDiv.appendChild(createLink);

        switcher.style.display = 'block';
    } catch (error) {
        console.error('Error loading databases:', error);
        showMessage('Error loading databases', 'error');
    }
}

// Switch to a different database
async function switchDatabase(dbName) {
    try {
        const response = await fetch('/api/databases/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_name: dbName })
        });

        const data = await response.json();

        if (response.ok) {
            showColorSchemeMessage(`Switched to ${data.index_name}`, 'success');
            document.getElementById('databaseSwitcher').style.display = 'none';

            // Reload the page to refresh all data
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showColorSchemeMessage(data.error || 'Failed to switch database', 'error');
        }
    } catch (error) {
        console.error('Error switching database:', error);
        showColorSchemeMessage('Error switching database', 'error');
    }
}

// Show create index modal
function showCreateIndexModal() {
    document.getElementById('databaseSwitcher').style.display = 'none';
    document.getElementById('createIndexModal').classList.add('show');
    document.getElementById('createIndexForm').reset();
    document.getElementById('createIndexBookNumber').value = '1';
    document.getElementById('createIndexMessage').className = 'message';
    document.getElementById('createIndexMessage').textContent = '';
    document.getElementById('createIndexName').focus();
}

// Close create index modal
function closeCreateIndexModal() {
    document.getElementById('createIndexModal').classList.remove('show');
}

// Submit create index form
async function submitCreateIndex(event) {
    event.preventDefault();

    const indexName = document.getElementById('createIndexName').value.trim();
    const bookName = document.getElementById('createIndexBookName').value.trim();
    const bookNumber = document.getElementById('createIndexBookNumber').value.trim();
    const bookPages = document.getElementById('createIndexBookPages').value.trim();
    const messageDiv = document.getElementById('createIndexMessage');

    if (!indexName || !bookName || !bookNumber) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Please fill in all required fields';
        return;
    }

    try {
        const response = await fetch('/api/databases/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                index_name: indexName,
                book_name: bookName,
                book_number: bookNumber,
                book_pages: bookPages || null
            })
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.className = 'message success show';
            messageDiv.textContent = 'Index created successfully!';

            setTimeout(() => {
                closeCreateIndexModal();
                window.location.reload();
            }, 1000);
        } else {
            messageDiv.className = 'message error show';
            messageDiv.textContent = data.error || 'Failed to create index';
        }
    } catch (error) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Error: ' + error.message;
    }
}

// Import database
async function importDatabase(event) {
    event.preventDefault();

    const form = document.getElementById('importDatabaseForm');
    const formData = new FormData(form);
    const messageDiv = document.getElementById('importDatabaseMessage');

    try {
        const response = await fetch('/api/databases/import', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.innerHTML = `<div class="success">${data.message}</div>`;

            // Switch to the newly imported database
            setTimeout(() => {
                switchDatabase(data.db_name);
            }, 1000);
        } else {
            messageDiv.innerHTML = `<div class="error">${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error importing database:', error);
        messageDiv.innerHTML = `<div class="error">Error importing database</div>`;
    }
}

// Create new database
async function createNewDatabase(event) {
    event.preventDefault();

    const indexName = document.getElementById('newDatabaseName').value;
    const messageDiv = document.getElementById('createDatabaseMessage');

    try {
        const response = await fetch('/api/databases/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index_name: indexName })
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.innerHTML = `<div class="success">${data.message}</div>`;

            // Switch to the newly created database
            setTimeout(() => {
                switchDatabase(data.db_name);
            }, 1000);
        } else {
            messageDiv.innerHTML = `<div class="error">${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error creating database:', error);
        messageDiv.innerHTML = `<div class="error">Error creating database</div>`;
    }
}

// Show import database modal
function showImportDatabaseModal() {
    document.getElementById('importDatabaseModal').classList.add('show');
}

// Close import database modal
function closeImportDatabaseModal() {
    document.getElementById('importDatabaseModal').classList.remove('show');
    document.getElementById('importDatabaseForm').reset();
    document.getElementById('importDatabaseMessage').innerHTML = '';
}

// Show create database modal
function showCreateDatabaseModal() {
    document.getElementById('createDatabaseModal').classList.add('show');
}

// Close create database modal
function closeCreateDatabaseModal() {
    document.getElementById('createDatabaseModal').classList.remove('show');
    document.getElementById('createDatabaseForm').reset();
    document.getElementById('createDatabaseMessage').innerHTML = '';
}

// ===================================
// Get Started Modal Functions
// ===================================

// Check if this is a new/empty database that needs setup
async function checkNeedsSetup() {
    try {
        // First check if any database exists at all
        const setupRes = await fetch('/api/needs-setup');
        const setupData = await setupRes.json();

        if (setupData.needs_setup) {
            // No database exists - show Get Started modal
            showGetStartedModal();
            return;
        }

        // Database exists - check if it's still in default state
        const [settingsRes, booksRes, entriesRes] = await Promise.all([
            fetch('/api/settings'),
            fetch('/api/books'),
            fetch('/api/entries')
        ]);

        const settings = await settingsRes.json();
        const books = await booksRes.json();
        const entries = await entriesRes.json();

        // Show Get Started modal if:
        // - Index name is the default "Book Index" AND
        // - No books have been added AND
        // - No entries have been added
        const isDefaultName = !settings.index_name || settings.index_name === 'Book Index';
        const hasNoBooks = !books.books || books.books.length === 0;
        const hasNoEntries = !entries.entries || entries.entries.length === 0;

        if (isDefaultName && hasNoBooks && hasNoEntries) {
            showGetStartedModal();
        }
    } catch (error) {
        console.error('Error checking setup status:', error);
    }
}

// Show Get Started modal
function showGetStartedModal() {
    document.getElementById('getStartedModal').classList.add('show');
}

// Close Get Started modal
function closeGetStartedModal() {
    document.getElementById('getStartedModal').classList.remove('show');
    document.getElementById('getStartedForm').reset();
    document.getElementById('getStartedMessage').innerHTML = '';

    // Hide all sections and remove active states
    document.querySelectorAll('.get-started-section').forEach(s => s.classList.remove('show'));
    document.querySelectorAll('.get-started-btn').forEach(b => b.classList.remove('active'));
}

// Handle Get Started form submission
async function handleGetStarted(event) {
    event.preventDefault();

    const indexName = document.getElementById('getStartedIndexName').value.trim();
    const bookNumber = document.getElementById('getStartedBookNumber').value.trim();
    const bookName = document.getElementById('getStartedBookName').value.trim();
    const bookPages = document.getElementById('getStartedBookPages').value.trim();
    const messageDiv = document.getElementById('getStartedMessage');

    if (!indexName || !bookNumber || !bookName) {
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'Please fill in all required fields';
        return;
    }

    try {
        // Check if we need to create a new database first
        const setupRes = await fetch('/api/needs-setup');
        const setupData = await setupRes.json();

        if (setupData.needs_setup) {
            // Create the database first
            const createResponse = await fetch('/api/databases/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index_name: indexName })
            });

            if (!createResponse.ok) {
                const createData = await createResponse.json();
                messageDiv.className = 'message error show';
                messageDiv.textContent = createData.error || 'Failed to create index';
                return;
            }
        } else {
            // Database exists, just update the index name
            const settingsResponse = await fetch('/api/settings/index-name', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: indexName })
            });

            if (!settingsResponse.ok) {
                const settingsData = await settingsResponse.json();
                messageDiv.className = 'message error show';
                messageDiv.textContent = settingsData.error || 'Failed to save index name';
                return;
            }
        }

        // Add the first book
        const bookResponse = await fetch('/api/books/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                book_number: bookNumber,
                book_name: bookName,
                page_count: bookPages ? parseInt(bookPages) : 0
            })
        });

        if (!bookResponse.ok) {
            const bookData = await bookResponse.json();
            messageDiv.className = 'message warning show';
            messageDiv.textContent = 'Index created but failed to add book: ' + (bookData.error || 'Unknown error');
            return;
        }

        // Success - close modal and reload
        messageDiv.className = 'message success show';
        messageDiv.textContent = 'Setup complete!';

        setTimeout(() => {
            closeGetStartedModal();
            // Reload the page to show the updated index
            window.location.reload();
        }, 1000);

    } catch (error) {
        console.error('Error in Get Started:', error);
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'An error occurred. Please try again.';
    }
}

// Toggle Get Started sections
function toggleGetStartedSection(section) {
    const sections = {
        create: document.getElementById('getStartedCreateSection'),
        import: document.getElementById('getStartedImportSection'),
        demo: document.getElementById('getStartedDemoSection')
    };

    const buttons = document.querySelectorAll('.get-started-btn');

    // Check if this section is already open
    const isOpen = sections[section].classList.contains('show');

    // Close all sections and remove active state from buttons
    Object.values(sections).forEach(s => s.classList.remove('show'));
    buttons.forEach(b => b.classList.remove('active'));

    // If it wasn't open, open it
    if (!isOpen) {
        sections[section].classList.add('show');
        // Find and activate the corresponding button
        const btn = sections[section].previousElementSibling;
        if (btn) btn.classList.add('active');
    }
}

// Load demo index
async function loadDemoIndex() {
    const messageDiv = document.getElementById('getStartedMessage');

    try {
        messageDiv.className = 'message show';
        messageDiv.textContent = 'Loading demo index...';

        const response = await fetch('/api/databases/load-demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (response.ok) {
            messageDiv.className = 'message success show';
            messageDiv.textContent = 'Demo index loaded!';

            setTimeout(() => {
                closeGetStartedModal();
                window.location.reload();
            }, 1000);
        } else {
            messageDiv.className = 'message error show';
            messageDiv.textContent = data.error || 'Failed to load demo index';
        }
    } catch (error) {
        console.error('Error loading demo:', error);
        messageDiv.className = 'message error show';
        messageDiv.textContent = 'An error occurred. Please try again.';
    }
}

// Show color scheme message (reused for database switching confirmations)
function showColorSchemeMessage(message, type = 'success') {
    const messageDiv = document.getElementById('colorSchemeMessage');
    if (messageDiv) {
        messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
        setTimeout(() => {
            messageDiv.innerHTML = '';
        }, 3000);
    }
}
