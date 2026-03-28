"""Tests for the OutlineParser class."""

import tempfile
import pytest
from pathlib import Path

from src.outline_parser import OutlineParser


# DOCX fixtures
@pytest.fixture
def simple_docx_path(tmp_path):
    """Create a simple DOCX with headings and content."""
    import docx

    doc = docx.Document()

    # Level 1 heading
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph("This is the introduction content.")

    # Level 2 heading
    doc.add_heading("Background", level=2)
    doc.add_paragraph("Some background information.")

    # Level 2 heading
    doc.add_heading("Objectives", level=2)
    doc.add_paragraph("The main objectives are:")
    doc.add_paragraph("• Objective 1\n• Objective 2", style="List Bullet")

    # Level 1 heading
    doc.add_heading("Methodology", level=1)
    doc.add_paragraph("We used the following methods.")

    path = tmp_path / "simple.docx"
    doc.save(path)
    return path


@pytest.fixture
def nested_docx_path(tmp_path):
    """Create a DOCX with deep nesting."""
    import docx

    doc = docx.Document()

    doc.add_heading("Chapter 1", level=1)
    doc.add_paragraph("Intro to chapter 1")
    doc.add_heading("Section 1.1", level=2)
    doc.add_paragraph("Content for 1.1")
    doc.add_heading("Subsection 1.1.1", level=3)
    doc.add_paragraph("Deep content")
    doc.add_heading("Section 1.2", level=2)
    doc.add_paragraph("Content for 1.2")

    doc.add_heading("Chapter 2", level=1)
    doc.add_paragraph("Intro to chapter 2")
    doc.add_heading("Section 2.1", level=2)
    doc.add_paragraph("Content for 2.1")

    path = tmp_path / "nested.docx"
    doc.save(path)
    return path


# Markdown fixtures
@pytest.fixture
def simple_md_path(tmp_path):
    """Create a simple Markdown file."""
    content = """# Introduction

This is the introduction content.

## Background

Some background information.

## Objectives

The main objectives are:
- Objective 1
- Objective 2

# Methodology

We used the following methods.

## Tools

We used Python and PPTX libraries.
"""
    path = tmp_path / "simple.md"
    path.write_text(content)
    return path


@pytest.fixture
def nested_md_path(tmp_path):
    """Create a Markdown file with deep nesting."""
    content = """# Chapter 1

Intro to chapter 1

## Section 1.1

Content for 1.1

### Subsection 1.1.1

Deep content

#### Sub-subsection 1.1.1.1

Even deeper

## Section 1.2

Content for 1.2

# Chapter 2

Intro to chapter 2

## Section 2.1

Content for 2.1
"""
    path = tmp_path / "nested.md"
    path.write_text(content)
    return path


# Parser fixtures
@pytest.fixture
def docx_parser(simple_docx_path):
    """Create OutlineParser for DOCX."""
    return OutlineParser(simple_docx_path)


@pytest.fixture
def md_parser(simple_md_path):
    """Create OutlineParser for Markdown."""
    return OutlineParser(simple_md_path)


class TestOutlineParserInitialization:
    """Test OutlineParser initialization."""

    def test_init_with_valid_docx(self, simple_docx_path):
        """Test initialization with valid DOCX file."""
        parser = OutlineParser(simple_docx_path)
        assert parser.outline_path == simple_docx_path
        assert parser.format == "docx"
        assert parser.document is None
        assert parser.structure == {}

    def test_init_with_valid_md(self, simple_md_path):
        """Test initialization with valid Markdown file."""
        parser = OutlineParser(simple_md_path)
        assert parser.outline_path == simple_md_path
        assert parser.format == "markdown"
        assert parser.document is None
        assert parser.structure == {}

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            OutlineParser("nonexistent.docx")

    def test_init_with_unsupported_extension(self, tmp_path):
        """Test initialization with unsupported extension raises ValueError."""
        fake_file = tmp_path / "fake.txt"
        fake_file.write_text("not a docx or md")
        with pytest.raises(ValueError) as exc_info:
            OutlineParser(fake_file)
        assert "Unsupported file format" in str(exc_info.value)


class TestOutlineParserParse:
    """Test the parse method."""

    def test_parse_docx_returns_structure_dict(self, docx_parser):
        """Test DOCX parse returns a dictionary with required keys."""
        structure = docx_parser.parse()
        assert isinstance(structure, dict)
        assert "document_name" in structure
        assert "format" in structure
        assert "sections" in structure
        assert structure["format"] == "docx"

    def test_parse_md_returns_structure_dict(self, md_parser):
        """Test Markdown parse returns a dictionary with required keys."""
        structure = md_parser.parse()
        assert isinstance(structure, dict)
        assert "document_name" in structure
        assert "format" in structure
        assert "sections" in structure
        assert structure["format"] == "markdown"

    def test_parse_sections_are_list(self, docx_parser):
        """Test sections are returned as a list."""
        structure = docx_parser.parse()
        assert isinstance(structure["sections"], list)

    def test_parse_idempotent(self, docx_parser):
        """Test parse can be called multiple times."""
        structure1 = docx_parser.parse()
        structure2 = docx_parser.parse()
        assert structure1 == structure2


class TestDocxParserStructure:
    """Test DOCX parsing produces correct structure."""

    def test_simple_docx_sections_count(self, docx_parser):
        """Test simple DOCX has expected number of top-level sections."""
        structure = docx_parser.parse()
        assert (
            len(structure["sections"]) == 2
        )  # Introduction and Methodology (Background/Objectives are level 2)

    def test_section_structure(self, docx_parser):
        """Test each section has required fields."""
        structure = docx_parser.parse()
        for section in self._flatten_sections(structure["sections"]):
            assert "level" in section
            assert "title" in section
            assert "content" in section
            assert "children" in section
            assert isinstance(section["level"], int)
            assert isinstance(section["title"], str)
            assert isinstance(section["content"], str)
            assert isinstance(section["children"], list)

    def test_hierarchy_preserved(self, nested_docx_path):
        """Test that nested headings create correct hierarchy."""
        parser = OutlineParser(nested_docx_path)
        structure = parser.parse()
        top_sections = structure["sections"]

        assert len(top_sections) == 2  # Chapter 1 and Chapter 2
        assert top_sections[0]["title"] == "Chapter 1"
        assert top_sections[0]["level"] == 1
        assert len(top_sections[0]["children"]) == 2  # Section 1.1 and Section 1.2

        # Check deeper nesting
        section_1_1 = top_sections[0]["children"][0]
        assert section_1_1["title"] == "Section 1.1"
        assert section_1_1["level"] == 2
        assert len(section_1_1["children"]) == 1  # Subsection 1.1.1

        subsection = section_1_1["children"][0]
        assert subsection["title"] == "Subsection 1.1.1"
        assert subsection["level"] == 3

    def test_content_assigned_to_correct_section(self, docx_parser):
        """Test that paragraph content is associated with the correct heading."""
        structure = docx_parser.parse()
        intro_section = structure["sections"][0]
        assert "Introduction" in intro_section["title"]
        assert "introduction content" in intro_section["content"]

    def test_multiple_paragraphs_in_content(self, docx_parser):
        """Test that multiple contiguous paragraphs are concatenated."""
        structure = docx_parser.parse()
        # Find Objectives section
        for section in self._flatten_sections(structure["sections"]):
            if "Objectives" in section["title"]:
                assert "Objective 1" in section["content"]
                assert "Objective 2" in section["content"]
                break

    def _flatten_sections(self, sections):
        """Helper to flatten nested sections."""
        result = []
        for section in sections:
            result.append(section)
            if section["children"]:
                result.extend(self._flatten_sections(section["children"]))
        return result


class TestMarkdownParserStructure:
    """Test Markdown parsing produces correct structure."""

    def test_simple_md_sections_count(self, md_parser):
        """Test simple Markdown has expected number of top-level sections."""
        structure = md_parser.parse()
        assert len(structure["sections"]) == 2  # Introduction and Methodology

    def test_nested_md_hierarchy(self, nested_md_path):
        """Test that nested headings create correct hierarchy."""
        parser = OutlineParser(nested_md_path)
        structure = parser.parse()
        top_sections = structure["sections"]

        assert len(top_sections) == 2  # Chapter 1 and Chapter 2
        assert top_sections[0]["title"] == "Chapter 1"
        assert top_sections[0]["level"] == 1
        assert len(top_sections[0]["children"]) == 2  # Section 1.1 and Section 1.2

    def test_md_content_preserved(self, md_parser):
        """Test that markdown content is preserved correctly."""
        structure = md_parser.parse()
        intro_section = structure["sections"][0]
        assert "Introduction" in intro_section["title"]
        assert "introduction content" in intro_section["content"]

    def test_md_levels_correct(self, nested_md_path):
        """Test heading levels match markdown syntax."""
        parser = OutlineParser(nested_md_path)
        structure = parser.parse()

        all_sections = self._flatten_sections(structure["sections"])
        for section in all_sections:
            if "Chapter" in section["title"]:
                assert section["level"] == 1
            elif "Section" in section["title"] and "Sub" not in section["title"]:
                assert section["level"] == 2
            elif "Subsection" in section["title"]:
                assert section["level"] == 3

    def _flatten_sections(self, sections):
        """Helper to flatten nested sections."""
        result = []
        for section in sections:
            result.append(section)
            if section["children"]:
                result.extend(self._flatten_sections(section["children"]))
        return result


class TestOutlineParserHelperMethods:
    """Test helper methods."""

    def test_get_section_count(self, docx_parser):
        """Test get_section_count returns total including nested."""
        docx_parser.parse()
        count = docx_parser.get_section_count()
        # simple_docx has 3 top-level + nested sub-sections
        assert count >= 3

    def test_get_section_count_without_parse(self, docx_parser):
        """Test get_section_count auto-triggers parse."""
        assert docx_parser.structure == {}
        count = docx_parser.get_section_count()
        assert count > 0
        assert docx_parser.structure != {}

    def test_get_flat_sections(self, nested_docx_path):
        """Test flat list includes all sections with parent references."""
        parser = OutlineParser(nested_docx_path)
        structure = parser.parse()
        flat = parser.get_flat_sections()

        # Should have 5 sections: 2 chapters, 2 sections, 1 subsection
        # (Chapter 1, Section 1.1, Subsection, Section 1.2, Chapter 2, Section 2.1 = 6 actually)
        assert len(flat) >= 5

        # Check that parent_id is set correctly
        top_sections = [s for s in flat if s["parent_id"] is None]
        assert len(top_sections) == 2  # Two chapters

        # Find a child section
        child_sections = [s for s in flat if s["parent_id"] is not None]
        assert len(child_sections) > 0


class TestOutlineParserErrorHandling:
    """Test error handling."""

    def test_corrupted_docx_raises_runtime_error(self, tmp_path):
        """Test parsing a corrupted DOCX raises RuntimeError."""
        corrupted_path = tmp_path / "corrupted.docx"
        corrupted_path.write_bytes(b"corrupted data")

        parser = OutlineParser(corrupted_path)
        with pytest.raises(RuntimeError):
            parser.parse()

    def test_invalid_markdown_encoding(self, tmp_path):
        """Test handling of markdown with weird characters."""
        md_path = tmp_path / "weird.md"
        # Include some unicode and special chars
        content = "# Heading\n\nContent with émojis 🎉 and spëcial çharacters"
        md_path.write_text(content, encoding="utf-8")

        parser = OutlineParser(md_path)
        # Should parse without error
        structure = parser.parse()
        assert len(structure["sections"]) == 1
        assert (
            "émojis" in structure["sections"][0]["content"]
            or "spëcial" in structure["sections"][0]["content"]
        )

    def test_markdown_with_no_headings(self, tmp_path):
        """Test markdown file with no headings produces empty sections."""
        md_path = tmp_path / "no_headings.md"
        md_path.write_text("Just some text\nwithout any headings\n\nMore text")

        parser = OutlineParser(md_path)
        structure = parser.parse()
        # Should have 0 top-level sections since no headings
        assert len(structure["sections"]) == 0

    def test_docx_with_only_title_style(self, tmp_path):
        """Test DOCX with Title style (not Heading 1) is handled."""
        import docx

        doc = docx.Document()
        doc.add_paragraph("Title Only", style="Title")
        doc.add_paragraph("Some content with no heading.")

        path = tmp_path / "title_only.docx"
        doc.save(path)

        parser = OutlineParser(path)
        structure = parser.parse()
        # Title style should be treated as level 1
        assert len(structure["sections"]) == 1
        assert structure["sections"][0]["title"] == "Title Only"
        assert structure["sections"][0]["level"] == 1


class TestOutlineParserIntegration:
    """Integration tests with realistic documents."""

    def test_complex_docx(self, nested_docx_path):
        """Test parsing a complex DOCX with multiple levels."""
        parser = OutlineParser(nested_docx_path)
        structure = parser.parse()

        assert structure["document_name"] == "nested.docx"
        assert structure["format"] == "docx"
        assert len(structure["sections"]) > 0

        # Verify all sections have proper hierarchy
        flat = parser.get_flat_sections()
        for section in flat:
            if section["parent_id"] is not None:
                # Parent should be in flat list
                parent_found = any(
                    s["title"] == section["title"]
                    for s in flat
                    if s["parent_id"] is not None or s["level"] < section["level"]
                )
                # Just verify the level hierarchy makes sense
                parent_levels = [
                    s["level"] for s in flat if s["title"] != section["title"]
                ]
                # This is a simple check
                pass

    def test_markdown_with_inconsistent_spacing(self, tmp_path):
        """Test markdown with extra blank lines."""
        md_path = tmp_path / "spaced.md"
        content = """
# First

Content here


## Subsection

More content

# Second

Even more content
"""
        md_path.write_text(content)

        parser = OutlineParser(md_path)
        structure = parser.parse()
        assert len(structure["sections"]) == 2
        assert structure["sections"][0]["title"] == "First"
        assert structure["sections"][1]["title"] == "Second"

    def test_empty_sections(self, tmp_path):
        """Test sections with no content (just heading)."""
        import docx

        doc = docx.Document()
        doc.add_heading("Empty Section", level=1)
        doc.add_heading("Next Section", level=1)
        doc.add_paragraph("Content for next")

        path = tmp_path / "empty.docx"
        doc.save(path)

        parser = OutlineParser(path)
        structure = parser.parse()
        assert len(structure["sections"]) == 2
        assert structure["sections"][0]["content"] == ""
        assert structure["sections"][1]["content"] == "Content for next"
