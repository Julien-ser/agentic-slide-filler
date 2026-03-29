"""Document Outline Parser for extracting hierarchical content from DOCX and Markdown."""

from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import re

try:
    import docx
except ImportError as e:
    raise ImportError(f"python-docx is required: {e}")

logger = logging.getLogger(__name__)


class OutlineParser:
    """Parses document outlines (DOCX and Markdown) to extract hierarchical content."""

    def __init__(self, outline_path: str | Path):
        """
        Initialize OutlineParser with a document file.

        Args:
            outline_path: Path to the DOCX or Markdown file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        self.outline_path = Path(outline_path)
        if not self.outline_path.exists():
            raise FileNotFoundError(f"Outline file not found: {self.outline_path}")

        suffix = self.outline_path.suffix.lower()
        if suffix not in [".docx", ".md", ".markdown"]:
            raise ValueError(f"Unsupported file format: {suffix}. Use .docx or .md")

        self.format = "docx" if suffix == ".docx" else "markdown"
        self.document: Optional[Any] = None
        self.structure: Dict[str, Any] = {}

    def parse(self) -> Dict[str, Any]:
        """
        Parse the document and extract hierarchical content structure.

        Returns:
            Dictionary containing document structure:
            {
                'document_name': str,
                'format': str,
                'sections': [
                    {
                        'level': int,
                        'title': str,
                        'content': str,
                        'children': [...]
                    }
                ]
            }

        Raises:
            RuntimeError: If parsing fails
        """
        try:
            if self.format == "docx":
                self._parse_docx()
            else:
                self._parse_markdown()
            return self.structure
        except Exception as e:
            logger.error(f"Failed to parse outline {self.outline_path}: {e}")
            raise RuntimeError(f"Outline parsing failed: {e}") from e

    def _parse_docx(self) -> None:
        """Parse DOCX file by identifying headings and their content."""
        try:
            self.document = docx.Document(str(self.outline_path))
        except Exception as e:
            raise RuntimeError(f"Failed to open DOCX file: {e}") from e

        paragraphs = self.document.paragraphs
        sections = []
        section_stack = []  # For tracking hierarchy

        for paragraph in paragraphs:
            # Skip empty paragraphs
            if not paragraph.text.strip():
                continue

            # Check if this is a heading
            heading_level = self._get_heading_level(paragraph.style.name)

            if heading_level:
                # Create new section
                section = {
                    "level": heading_level,
                    "title": paragraph.text.strip(),
                    "content": "",
                    "children": [],
                }

                # Insert into hierarchy
                self._insert_section(sections, section_stack, section, heading_level)
            else:
                # Regular paragraph - add to current section's content
                if section_stack:
                    current_section = section_stack[-1]
                    if current_section["content"]:
                        current_section["content"] += "\n" + paragraph.text.strip()
                    else:
                        current_section["content"] = paragraph.text.strip()
                else:
                    # Orphan content - could be intro before first heading
                    # We'll create a level 0 section for this
                    pass

        # Handle orphan content (content before first heading)
        # We could accumulate it and add as a preamble, but for now we'll skip

        self.structure = {
            "document_name": self.outline_path.name,
            "format": "docx",
            "sections": sections,
        }

    def _get_heading_level(self, style_name: str) -> Optional[int]:
        """
        Extract heading level from DOCX style name.

        Args:
            style_name: The style name from a paragraph (e.g., "Heading 1")

        Returns:
            Integer level (1-9) or None if not a heading
        """
        if not style_name:
            return None

        style_lower = style_name.lower()
        if style_lower.startswith("heading"):
            try:
                # Extract number from "Heading 1", "Heading 2", etc.
                level_str = style_name.split()[-1]
                level = int(level_str)
                if 1 <= level <= 9:
                    return level
            except (ValueError, IndexError):
                pass

        # Also check for Title style
        if style_lower == "title":
            return 1

        return None

    def _parse_markdown(self) -> None:
        """Parse Markdown file by identifying headings (# syntax) and their content."""
        try:
            with open(self.outline_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise RuntimeError(f"Failed to read Markdown file: {e}") from e

        sections = []
        section_stack = []

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip("\n")

            # Check if this is a heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                section = {
                    "level": level,
                    "title": title,
                    "content": "",
                    "children": [],
                }

                self._insert_section(sections, section_stack, section, level)
            else:
                # Regular text - add to current section
                text = line.strip()
                if text:
                    if section_stack:
                        current_section = section_stack[-1]
                        if current_section["content"]:
                            current_section["content"] += "\n" + text
                        else:
                            current_section["content"] = text
                    else:
                        # Orphan content (before first heading) - could be intro
                        pass

        self.structure = {
            "document_name": self.outline_path.name,
            "format": "markdown",
            "sections": sections,
        }

    def _insert_section(
        self,
        sections: List[Dict[str, Any]],
        section_stack: List[Dict[str, Any]],
        new_section: Dict[str, Any],
        level: int,
    ) -> None:
        """
        Insert a section into the hierarchy based on its level.

        Args:
            sections: Top-level sections list
            section_stack: Current stack of sections (maintained during parsing)
            new_section: Section to insert
            level: Heading level (1 = top, 2 = child, etc.)
        """
        # Pop from stack until we find the parent
        while section_stack and section_stack[-1]["level"] >= level:
            section_stack.pop()

        if not section_stack:
            # This is a top-level section
            sections.append(new_section)
            section_stack.append(new_section)
        else:
            # This is a child of the top of stack
            parent = section_stack[-1]
            parent["children"].append(new_section)
            section_stack.append(new_section)

    def get_section_count(self) -> int:
        """Get total number of sections (including nested)."""
        if not self.structure:
            self.parse()
        return self._count_sections(self.structure["sections"])

    def _count_sections(self, sections: List[Dict[str, Any]]) -> int:
        """Recursively count sections."""
        count = len(sections)
        for section in sections:
            count += self._count_sections(section["children"])
        return count

    def get_flat_sections(self) -> List[Dict[str, Any]]:
        """
        Get all sections in a flat list with added 'parent' reference.

        Returns:
            List of all sections with 'parent_id' (None for top-level)
        """
        if not self.structure:
            self.parse()

        flat = []
        section_map = {}  # id -> section

        def flatten(sections, parent_id=None):
            for section in sections:
                section_id = id(section)
                section_copy = section.copy()
                section_copy["parent_id"] = parent_id
                section_copy["children"] = [id(child) for child in section["children"]]
                flat.append(section_copy)
                section_map[section_id] = section_copy
                if section["children"]:
                    # Map children references to actual IDs
                    flatten(section["children"], section_id)

        flatten(self.structure["sections"])
        return flat
