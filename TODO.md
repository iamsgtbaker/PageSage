# IndexTool TODO

## Completed

### Claude AI Term Enrichment (Done)

Send indexed terms to Claude API to generate descriptions identifying each term's concept and whether it's a tool.

**Implementation includes:**
- AI enrichment columns in database (`ai_description`, `is_tool`, `ai_enriched_at`)
- API endpoints for status, terms, enrich, import, export
- Manual workflow: Copy Terms button for use with Claude/ChatGPT
- Paste AI Response modal for importing results
- API enrichment when `ANTHROPIC_API_KEY` is set
- Export descriptions as CSV

---

### Gap Analysis Refresh Button (Done)

Added refresh button to reload gap analysis without navigating away.

---

### Remember Last Opened Tool (Done)

Tools page remembers last opened section using localStorage.

---

### Index Switcher Keyboard Shortcut (Done)

Press `0` key to open the index switcher dropdown (when not typing in an input field).

---

### Rename Index File on Disk (Done)

When renaming an index, the underlying `.db` file is automatically renamed to match.

**Implementation includes:**
- Sanitizes index name for valid filename (removes special characters, spaces to underscores)
- Handles conflicts by appending numeric suffix if target filename exists
- Updates session to point to new filename
- Clears database cache to release file handles before rename
- Graceful fallback if rename fails (name still saved in database)

---

## Planned Features

(No pending items)
