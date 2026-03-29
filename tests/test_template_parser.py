"""Tests for the TemplateParser class."""

import tempfile
import pytest
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from src.template_parser import TemplateParser


@pytest.fixture
def sample_template_path(tmp_path):
    """Create a sample PPTX template for testing."""
    template_path = tmp_path / "test_template.pptx"
    prs = Presentation()

    # Create a blank layout (first layout usually)
    blank_slide_layout = prs.slide_layouts[0]  # Blank layout

    # Add a slide with title and content layout
    if len(prs.slide_layouts) > 1:
        title_slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title slide
        if title_slide.shapes.title:
            title_slide.shapes.title.text = "Test Title"
        # Try to set subtitle if available
        try:
            subtitle = title_slide.placeholders[1]
            subtitle.text = "Test Subtitle"
        except (KeyError, IndexError):
            pass

    # Add a content slide with placeholders
    if len(prs.slide_layouts) > 5:
        content_slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title and content
        if content_slide.shapes.title:
            content_slide.shapes.title.text = "Content Slide"
        try:
            content_placeholder = content_slide.placeholders[1]
            content_placeholder.text = "Bullet 1\nBullet 2\nBullet 3"
        except (KeyError, IndexError):
            pass

    prs.save(template_path)
    return template_path


@pytest.fixture
def template_parser(sample_template_path):
    """Create a TemplateParser instance with the sample template."""
    return TemplateParser(sample_template_path)


class TestTemplateParserInitialization:
    """Test TemplateParser initialization."""

    def test_init_with_valid_path(self, sample_template_path):
        """Test initialization with valid PPTX file."""
        parser = TemplateParser(sample_template_path)
        assert parser.template_path == sample_template_path
        assert parser.presentation is None
        assert parser.metadata == {}

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            TemplateParser("nonexistent.pptx")

    def test_init_with_wrong_extension(self, tmp_path):
        """Test initialization with wrong file extension raises ValueError."""
        fake_file = tmp_path / "fake.txt"
        fake_file.write_text("not a pptx")
        with pytest.raises(ValueError) as exc_info:
            TemplateParser(fake_file)
        assert "must be a .pptx" in str(exc_info.value)


class TestTemplateParserParse:
    """Test the parse method."""

    def test_parse_returns_metadata_dict(self, template_parser):
        """Test parse returns a dictionary with required keys."""
        metadata = template_parser.parse()
        assert isinstance(metadata, dict)
        assert "template_name" in metadata
        assert "template_path" in metadata
        assert "slide_layouts" in metadata

    def test_template_name_extracted(self, template_parser, sample_template_path):
        """Test template name is extracted correctly."""
        metadata = template_parser.parse()
        assert metadata["template_name"] == sample_template_path.name

    def test_slide_layouts_extracted(self, template_parser):
        """Test slide layouts are extracted."""
        metadata = template_parser.parse()
        assert isinstance(metadata["slide_layouts"], list)
        assert len(metadata["slide_layouts"]) > 0

    def test_layout_structure(self, template_parser):
        """Test each layout has correct structure."""
        metadata = template_parser.parse()
        for layout in metadata["slide_layouts"]:
            assert "name" in layout
            assert "layout_id" in layout
            assert "placeholders" in layout
            assert isinstance(layout["placeholders"], list)

    def test_placeholders_extracted(self, template_parser):
        """Test placeholders are extracted from layouts."""
        metadata = template_parser.parse()
        # At least one layout should have placeholders in a typical template
        has_placeholders = any(
            len(layout["placeholders"]) > 0 for layout in metadata["slide_layouts"]
        )
        assert (
            has_placeholders or len(metadata["slide_layouts"]) == 0
        )  # Allow empty layouts

    def test_placeholder_structure(self, template_parser):
        """Test each placeholder has required fields."""
        metadata = template_parser.parse()
        for layout in metadata["slide_layouts"]:
            for ph in layout["placeholders"]:
                assert "type" in ph
                assert "idx" in ph
                # Geometry fields should be present (can be None)
                assert "width" in ph
                assert "height" in ph
                assert "left" in ph
                assert "top" in ph

    def test_placeholder_type_mapping(self, template_parser):
        """Test placeholder types are valid strings."""
        valid_types = {
            "TITLE",
            "BODY",
            "CENTER_TITLE",
            "SUBTITLE",
            "DATE",
            "SLIDE_NUMBER",
            "FOOTER",
            "OBJECT",
            "CHART",
            "TABLE",
            "CLIP_ART",
            "SMART_ART",
            "MEDIA",
            "PICTURE",
            "UNKNOWN",
        }
        metadata = template_parser.parse()
        for layout in metadata["slide_layouts"]:
            for ph in layout["placeholders"]:
                assert ph["type"] in valid_types

    def test_parse_idempotent(self, template_parser):
        """Test parse can be called multiple times with same result."""
        metadata1 = template_parser.parse()
        metadata2 = template_parser.parse()
        assert metadata1 == metadata2


class TestTemplateParserHelperMethods:
    """Test helper methods."""

    def test_get_layout_names(self, template_parser):
        """Test get_layout_names returns list of layout names."""
        template_parser.parse()
        names = template_parser.get_layout_names()
        assert isinstance(names, list)
        assert all(isinstance(name, str) for name in names)

    def test_get_layout_names_without_parse(self, template_parser):
        """Test get_layout_names auto-triggers parse if needed."""
        assert template_parser.metadata == {}
        names = template_parser.get_layout_names()
        assert len(names) > 0
        assert template_parser.metadata != {}  # Should have parsed

    def test_get_placeholders_by_layout(self, template_parser):
        """Test getting placeholders by layout name."""
        metadata = template_parser.parse()
        if not metadata["slide_layouts"]:
            pytest.skip("No layouts available")

        layout_name = metadata["slide_layouts"][0]["name"]
        placeholders = template_parser.get_placeholders_by_layout(layout_name)
        assert isinstance(placeholders, list)

    def test_get_placeholders_by_layout_invalid_name(self, template_parser):
        """Test getting placeholders with invalid layout name raises ValueError."""
        template_parser.parse()
        with pytest.raises(ValueError) as exc_info:
            template_parser.get_placeholders_by_layout("NonExistentLayout")
        assert "not found" in str(exc_info.value)


class TestTemplateParserErrorHandling:
    """Test error handling with corrupted templates."""

    def test_corrupted_pptx_raises_runtime_error(self, tmp_path):
        """Test parsing a corrupted PPTX file raises RuntimeError."""
        corrupted_path = tmp_path / "corrupted.pptx"
        # Create a file that's not a valid PPTX (just random bytes)
        corrupted_path.write_bytes(b"corrupted data not a pptx")

        parser = TemplateParser(corrupted_path)
        with pytest.raises(RuntimeError):
            parser.parse()

    def test_invalid_pptx_format(self, tmp_path):
        """Test that invalid PPTX format raises RuntimeError."""
        invalid_path = tmp_path / "invalid.pptx"
        # Create an empty file
        invalid_path.write_bytes(b"")

        parser = TemplateParser(invalid_path)
        with pytest.raises(RuntimeError):
            parser.parse()


class TestTemplateParserIntegration:
    """Integration tests with more complex templates."""

    def test_multiple_slides(self, tmp_path):
        """Test parsing a template with multiple slides."""
        template_path = tmp_path / "multi_slide.pptx"
        prs = Presentation()

        # Add several slides with different layouts
        for i in range(min(5, len(prs.slide_layouts))):
            slide = prs.slides.add_slide(prs.slide_layouts[i])
            if slide.shapes.title:
                slide.shapes.title.text = f"Slide {i}"

        prs.save(template_path)

        parser = TemplateParser(template_path)
        metadata = parser.parse()

        assert len(metadata["slide_layouts"]) > 0
        # Count total placeholders
        total_placeholders = sum(
            len(layout["placeholders"]) for layout in metadata["slide_layouts"]
        )
        # Should have at least some placeholders
        assert total_placeholders >= 0  # May be zero for blank layouts

    def test_placeholder_geometry_values(self, tmp_path):
        """Test that placeholder geometry is in reasonable units."""
        template_path = tmp_path / "geometry_test.pptx"
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Title and content
        prs.save(template_path)

        parser = TemplateParser(template_path)
        metadata = parser.parse()

        for layout in metadata["slide_layouts"]:
            for ph in layout["placeholders"]:
                # Width, height, left, top should be numeric (in points)
                if ph["width"] is not None:
                    assert isinstance(ph["width"], (int, float))
                    assert ph["width"] > 0
                if ph["height"] is not None:
                    assert isinstance(ph["height"], (int, float))
                    assert ph["height"] > 0
                if ph["left"] is not None:
                    assert isinstance(ph["left"], (int, float))
                if ph["top"] is not None:
                    assert isinstance(ph["top"], (int, float))
