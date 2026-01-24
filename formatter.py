"""
LaTeX-style index formatter
"""
from typing import List, Tuple
from datetime import datetime


class IndexFormatter:
    def __init__(self):
        pass

    @staticmethod
    def normalize_first_letter(text: str) -> str:
        """
        Get the first letter for grouping
        Numbers and special characters become "#"
        Letters A-Z remain as uppercase letters
        """
        if not text or len(text) == 0:
            return '#'

        first_char = text[0].upper()

        # Check if it's a letter A-Z
        if first_char.isalpha() and first_char.isupper():
            return first_char

        # Everything else (numbers, special characters) becomes "#"
        return '#'

    def format_latex_style(self, entries: List[Tuple[str, List[str]]],
                           title: str = "Index") -> str:
        """
        Format index entries in LaTeX style
        """
        if not entries:
            return "% Empty index\n"

        # Sort entries with "#" (special chars/numbers) at the end
        def sort_key(item):
            term = item[0]
            first_letter = self.normalize_first_letter(term)
            # Put "#" at beginning, otherwise sort alphabetically
            return (first_letter != '#', term.lower())

        entries = sorted(entries, key=sort_key)

        output = []

        # Add header
        output.append("% Book Index")
        output.append(f"% Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append("\\begin{theindex}")
        output.append("")

        current_letter = None

        for term, references in entries:
            # Get first letter (normalize special chars and numbers to "#")
            first_letter = self.normalize_first_letter(term)

            # Add letter heading if new letter
            if first_letter != current_letter:
                if current_letter is not None:
                    output.append("")  # Blank line between letter sections
                output.append(f"  \\indexspace")
                output.append(f"  \\textbf{{{first_letter}}}")
                output.append("")
                current_letter = first_letter

            # Format references
            ref_str = ", ".join(references)

            # Escape special LaTeX characters in term
            escaped_term = self.escape_latex(term)

            output.append(f"  \\item {escaped_term}, {ref_str}")

        output.append("")
        output.append("\\end{theindex}")

        return "\n".join(output)

    def format_plain_text(self, entries: List[Tuple[str, List[str]]],
                          title: str = "Index") -> str:
        """
        Format index entries as plain text with letter headings
        """
        if not entries:
            return "Empty index\n"

        # Sort entries with "#" (special chars/numbers) at the end
        def sort_key(item):
            term = item[0]
            first_letter = self.normalize_first_letter(term)
            # Put "#" at beginning, otherwise sort alphabetically
            return (first_letter != '#', term.lower())

        entries = sorted(entries, key=sort_key)

        output = []

        # Add header
        output.append("=" * 60)
        output.append(title.center(60))
        output.append("=" * 60)
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        output.append("")

        current_letter = None

        for term, references in entries:
            # Get first letter (normalize special chars and numbers to "#")
            first_letter = self.normalize_first_letter(term)

            # Add letter heading if new letter
            if first_letter != current_letter:
                if current_letter is not None:
                    output.append("")  # Blank line between letter sections
                output.append(f"{first_letter}")
                output.append("-" * 40)
                current_letter = first_letter

            # Format references
            ref_str = ", ".join(references)

            output.append(f"  {term}: {ref_str}")

        output.append("")
        output.append("=" * 60)
        output.append(f"Total entries: {len(entries)}")
        output.append("=" * 60)

        return "\n".join(output)

    def format_markdown(self, entries: List[Tuple[str, List[str]]],
                        title: str = "Index") -> str:
        """
        Format index entries as Markdown
        """
        if not entries:
            return "# Index\n\n*Empty index*\n"

        # Sort entries with "#" (special chars/numbers) at the end
        def sort_key(item):
            term = item[0]
            first_letter = self.normalize_first_letter(term)
            # Put "#" at beginning, otherwise sort alphabetically
            return (first_letter != '#', term.lower())

        entries = sorted(entries, key=sort_key)

        output = []

        # Add header
        output.append(f"# {title}")
        output.append("")
        output.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        output.append("")

        current_letter = None

        for term, references in entries:
            # Get first letter (normalize special chars and numbers to "#")
            first_letter = self.normalize_first_letter(term)

            # Add letter heading if new letter
            if first_letter != current_letter:
                if current_letter is not None:
                    output.append("")  # Blank line between letter sections
                output.append(f"## {first_letter}")
                output.append("")
                current_letter = first_letter

            # Format references
            ref_str = ", ".join(references)

            output.append(f"- **{term}**: {ref_str}")

        output.append("")
        output.append(f"---")
        output.append(f"*Total entries: {len(entries)}*")

        return "\n".join(output)

    def format_pdf(self, entries: List[Tuple[str, List[str]]],
                   output_path: str, title: str = "Index") -> bool:
        """
        Format index entries as a 4-column landscape PDF with continuous flow
        Returns True if successful
        """
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
            from reportlab.platypus.frames import Frame

            if not entries:
                return False

            # Sort entries with "#" (special chars/numbers) at the end
            def sort_key(item):
                term = item[0]
                first_letter = self.normalize_first_letter(term)
                # Put "#" at end, otherwise sort alphabetically
                return (first_letter == '#', term.lower())

            entries = sorted(entries, key=sort_key)

            # Define page number footer function
            def add_page_number(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                page_num = canvas.getPageNumber()
                text = f"{page_num}"
                canvas.drawRightString(landscape(letter)[0] - 0.5 * inch, 0.3 * inch, text)
                canvas.restoreState()

            # Create PDF with landscape orientation
            doc = BaseDocTemplate(
                output_path,
                pagesize=landscape(letter),
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.5 * inch
            )

            # Calculate frame dimensions for 4 columns
            page_width, page_height = landscape(letter)
            frame_width = (page_width - 1 * inch - 3 * 0.15 * inch) / 4  # subtract margins and gaps
            frame_height = page_height - 1.25 * inch  # subtract top and bottom margins

            # Create 4 frames (columns)
            frames = []
            for i in range(4):
                x = 0.5 * inch + i * (frame_width + 0.15 * inch)
                frame = Frame(
                    x, 0.5 * inch,
                    frame_width, frame_height,
                    leftPadding=6, rightPadding=6,
                    topPadding=6, bottomPadding=6,
                    showBoundary=0
                )
                frames.append(frame)

            # Create page template with 4 columns and page numbers
            template = PageTemplate(id='FourCol', frames=frames, onPage=add_page_number)
            doc.addPageTemplates([template])

            # Styles
            styles = getSampleStyleSheet()

            # Letter heading style (larger and bold)
            heading_style = ParagraphStyle(
                'LetterHeading',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica-Bold',
                keepWithNext=True
            )

            # Entry style (term in bold, references in normal)
            entry_style = ParagraphStyle(
                'EntryStyle',
                parent=styles['Normal'],
                fontSize=9,
                leftIndent=10,
                spaceAfter=4,
                leading=11
            )

            # Build content as a continuous flow
            story = []
            current_letter = None

            for term, references in entries:
                # Get first letter (normalize special chars and numbers to "#")
                first_letter = self.normalize_first_letter(term)

                # Add letter heading when we encounter a new letter
                if first_letter != current_letter:
                    if current_letter is not None:
                        story.append(Spacer(1, 0.1 * inch))

                    # Add letter heading with grey background
                    heading_para = Paragraph(f"<b>{first_letter}</b>", heading_style)
                    heading_table = Table([[heading_para]], colWidths=[frame_width - 12])
                    heading_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(heading_table)
                    current_letter = first_letter

                # Format entry: term in bold, references in normal text
                ref_str = ", ".join(references)
                entry_text = f"<b>{self.escape_html(term)}</b>: {self.escape_html(ref_str)}"
                story.append(Paragraph(entry_text, entry_style))

            # Build PDF
            doc.build(story)
            return True

        except ImportError:
            return False

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML special characters for use in ReportLab"""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters"""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    def format_notes_text(self, notes: List[Tuple[str, str]]) -> str:
        """
        Format notes as plain text
        """
        if not notes:
            return "Empty notes\n"

        # Sort notes with "#" (special chars/numbers) at the end
        def sort_key(item):
            term = item[0]
            first_letter = self.normalize_first_letter(term)
            # Put "#" at beginning, otherwise sort alphabetically
            return (first_letter != '#', term.lower())

        notes = sorted(notes, key=sort_key)

        output = []

        # Add header
        output.append("=" * 60)
        output.append("Notes".center(60))
        output.append("=" * 60)
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        output.append("")

        for term, note in notes:
            output.append(f"{term}")
            output.append("-" * 40)
            output.append(note)
            output.append("")

        output.append("=" * 60)
        output.append(f"Total notes: {len(notes)}")
        output.append("=" * 60)

        return "\n".join(output)

    def format_notes_csv(self, notes: List[Tuple[str, str]]) -> str:
        """
        Format notes as CSV
        """
        import csv
        from io import StringIO

        # Sort notes with "#" (special chars/numbers) at the end
        def sort_key(item):
            term = item[0]
            first_letter = self.normalize_first_letter(term)
            # Put "#" at beginning, otherwise sort alphabetically
            return (first_letter != '#', term.lower())

        notes = sorted(notes, key=sort_key)

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(['Term', 'Notes'])

        # Write data
        for term, note in notes:
            writer.writerow([term, note])

        return output.getvalue()

    def format_notes_pdf(self, notes: List[Tuple[str, str]], output_path: str) -> bool:
        """
        Format notes as a 2-column landscape PDF
        Returns True if successful
        """
        try:
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
            from reportlab.platypus.frames import Frame

            if not notes:
                return False

            # Sort notes with "#" (special chars/numbers) at the end
            def sort_key(item):
                term = item[0]
                first_letter = self.normalize_first_letter(term)
                # Put "#" at end, otherwise sort alphabetically
                return (first_letter == '#', term.lower())

            notes = sorted(notes, key=sort_key)

            # Define page number footer function
            def add_page_number(canvas, doc):
                canvas.saveState()
                canvas.setFont('Helvetica', 9)
                page_num = canvas.getPageNumber()
                text = f"{page_num}"
                canvas.drawRightString(landscape(letter)[0] - 0.5 * inch, 0.3 * inch, text)
                canvas.restoreState()

            # Create PDF with landscape orientation
            doc = BaseDocTemplate(
                output_path,
                pagesize=landscape(letter),
                rightMargin=0.5 * inch,
                leftMargin=0.5 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.5 * inch
            )

            # Calculate frame dimensions for 2 columns
            page_width, page_height = landscape(letter)
            frame_width = (page_width - 1 * inch - 0.3 * inch) / 2  # subtract margins and gap
            frame_height = page_height - 1.25 * inch  # subtract top and bottom margins

            # Create 2 frames (columns)
            frames = []
            for i in range(2):
                x = 0.5 * inch + i * (frame_width + 0.3 * inch)
                frame = Frame(
                    x, 0.5 * inch,
                    frame_width, frame_height,
                    leftPadding=10, rightPadding=10,
                    topPadding=10, bottomPadding=10,
                    showBoundary=0
                )
                frames.append(frame)

            # Create page template with 2 columns and page numbers
            template = PageTemplate(id='TwoCol', frames=frames, onPage=add_page_number)
            doc.addPageTemplates([template])

            # Styles
            styles = getSampleStyleSheet()

            # Term heading style
            term_style = ParagraphStyle(
                'TermStyle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#2563eb'),
                spaceAfter=6,
                spaceBefore=10,
                fontName='Helvetica-Bold',
                keepWithNext=True
            )

            # Notes text style
            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=styles['Normal'],
                fontSize=9,
                leftIndent=10,
                spaceAfter=12,
                leading=12
            )

            # Build content
            story = []

            for term, note in notes:
                # Add term heading
                story.append(Paragraph(f"<b>{self.escape_html(term)}</b>", term_style))

                # Add notes text
                # Preserve line breaks in notes
                note_html = self.escape_html(note).replace('\n', '<br/>')
                story.append(Paragraph(note_html, notes_style))

            # Build PDF
            doc.build(story)
            return True

        except ImportError:
            return False