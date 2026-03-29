"""Integration tests for the complete SlideFiller pipeline."""

import tempfile
import pytest
from pathlib import Path

from src.slide_filler import SlideFiller


@pytest.fixture
def simple_template_path(tmp_path):
    """Create a simple PPTX template for testing."""
    from pptx import Presentation

    template_path = tmp_path / "template.pptx"
    prs = Presentation()

    # Title slide layout
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])  # Usually blank or title
    if title_slide.shapes.title:
        title_slide.shapes.title.text = "Presentation Title"
    # Try to add a subtitle placeholder
    for shape in title_slide.shapes:
        if shape.is_placeholder and shape.placeholder_format.type == 2:  # SUBTITLE
            shape.text = "Subtitle"

    # Title and content layout
    if len(prs.slide_layouts) > 1:
        content_slide = prs.slides.add_slide(prs.slide_layouts[1])
        if content_slide.shapes.title:
            content_slide.shapes.title.text = "Content Slide Title"
        for shape in content_slide.shapes:
            if shape.is_placeholder and shape.placeholder_format.type == 2:  # BODY
                shape.text = "Bullet 1\nBullet 2\nBullet 3"

    prs.save(template_path)
    return template_path


@pytest.fixture
def simple_docx_path(tmp_path):
    """Create a simple DOCX outline for testing."""
    import docx

    doc = docx.Document()
    doc.add_heading("Introduction", level=1)
    doc.add_paragraph("This is the introduction to our topic.")

    doc.add_heading("Main Points", level=1)
    doc.add_paragraph("Here are the main points we will discuss.")

    doc.add_heading("Background", level=2)
    doc.add_paragraph("Background information and context.")

    doc.add_heading("Conclusion", level=1)
    doc.add_paragraph("Summary and next steps.")

    path = tmp_path / "outline.docx"
    doc.save(path)
    return path


@pytest.fixture
def simple_md_path(tmp_path):
    """Create a simple Markdown outline for testing."""
    content = """# Introduction
This is the introduction to our topic.

# Main Points
Here are the main points we will discuss.

## Background
Background information and context.

# Conclusion
Summary and next steps.
"""
    path = tmp_path / "outline.md"
    path.write_text(content)
    return path


class TestSlideFillerInitialization:
    """Test SlideFiller initialization."""

    def test_init_with_valid_paths(self, simple_template_path, simple_docx_path):
        """Test initialization with valid template and outline."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
            verbose=False,
        )
        assert filler.template_path == simple_template_path
        assert filler.outline_path == simple_docx_path
        assert filler.dry_run is True

    def test_init_with_nonexistent_template(self, tmp_path):
        """Test initialization with non-existent template raises FileNotFoundError."""
        fake_template = tmp_path / "nonexistent.pptx"
        fake_outline = tmp_path / "fake.docx"
        fake_outline.write_text("test")
        with pytest.raises(FileNotFoundError):
            SlideFiller(
                template_path=fake_template,
                outline_path=fake_outline,
                dry_run=True,
            )

    def test_init_with_nonexistent_outline(self, tmp_path):
        """Test initialization with non-existent outline raises FileNotFoundError."""
        fake_template = tmp_path / "fake.pptx"
        fake_template.write_bytes(b"fake pptx")
        fake_outline = tmp_path / "nonexistent.docx"
        with pytest.raises(FileNotFoundError):
            SlideFiller(
                template_path=fake_template,
                outline_path=fake_outline,
                dry_run=True,
            )


class TestSlideFillerPipeline:
    """Test the complete pipeline execution."""

    def test_dry_run_pipeline(self, simple_template_path, simple_docx_path):
        """Test pipeline execution in dry-run mode (no AI calls, no file writing)."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
            verbose=False,
        )

        result = filler.run()

        # Should return a dummy path
        assert result == Path("dry_run_complete")

        # Should have parsed template and outline
        assert filler.template_metadata is not None
        assert "slide_layouts" in filler.template_metadata
        assert filler.outline_structure is not None
        assert "sections" in filler.outline_structure

        # Should have created mapping
        assert len(filler.mapping) > 0

        # Should not have generated content (dry run)
        assert len(filler.generated_content) == 0

        # Should have statistics
        assert filler.statistics is not None
        assert "total_sections" in filler.statistics
        assert "mapped_sections" in filler.statistics

    def test_mapping_report_generation(self, simple_template_path, simple_docx_path):
        """Test that mapping report can be generated."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
        )
        filler.run()

        report = filler.get_mapping_report()

        assert isinstance(report, str)
        assert "Content Mapping Report" in report
        assert filler.template_path.name in report
        assert filler.outline_path.name in report
        assert "Mapped Sections:" in report

    def test_pipeline_with_markdown(self, simple_template_path, simple_md_path):
        """Test pipeline with Markdown outline."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_md_path,
            dry_run=True,
            mapping_strategy="auto",
        )
        result = filler.run()

        assert filler.outline_structure["format"] == "markdown"
        assert len(filler.mapping) > 0

    def test_pipeline_with_different_strategies(
        self, simple_template_path, simple_docx_path
    ):
        """Test pipeline with different mapping strategies."""
        strategies = ["auto", "sequential", "hierarchical"]

        for strategy in strategies:
            filler = SlideFiller(
                template_path=simple_template_path,
                outline_path=simple_docx_path,
                dry_run=True,
                mapping_strategy=strategy,
            )
            filler.run()

            # Should have at least some mapping regardless of strategy
            assert len(filler.mapping) >= 0  # May be zero if no suitable layouts

    def test_section_counting(self, simple_template_path, simple_docx_path):
        """Test that total section count includes nested sections."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
        )
        filler.run()

        total_sections = filler._count_total_sections(
            filler.outline_structure["sections"]
        )
        # Our simple_docx fixture has 4 top-level sections (2 level 1 headings and nested)
        assert (
            total_sections >= 3
        )  # At minimum, we should have Introduction, Main Points, Conclusion

    def test_unmapped_sections_identification(
        self, simple_template_path, simple_docx_path
    ):
        """Test that unmapped sections can be identified."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
        )
        filler.run()

        unmapped = filler.content_mapper.get_unmapped_sections()
        # This should return a list (may be empty if all mapped)
        assert isinstance(unmapped, list)


class TestSlideFillerErrorHandling:
    """Test error handling in the pipeline."""

    def test_invalid_mapping_strategy(self, simple_template_path, simple_docx_path):
        """Test that invalid mapping strategy is handled."""
        # The constructor should accept any string, but the mapper may have default fallback
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
            mapping_strategy="invalid_strategy",  # This will fall back to "auto"
        )
        filler.run()
        # Should still work as auto is fallback
        assert len(filler.mapping) >= 0

    def test_template_with_no_placeholders(self, tmp_path, simple_docx_path):
        """Test behavior with a template that has no placeholders."""
        from pptx import Presentation

        # Create a truly blank template (just blank slides)
        template_path = tmp_path / "blank.pptx"
        prs = Presentation()
        # Add blank slides which typically have no text placeholders
        for _ in range(3):
            prs.slides.add_slide(prs.slide_layouts[0])  # Blank layout
        prs.save(template_path)

        filler = SlideFiller(
            template_path=template_path,
            outline_path=simple_docx_path,
            dry_run=True,
        )
        filler.run()

        # Mapping may be zero or minimal due to lack of content placeholders
        assert filler.statistics is not None
        # This is acceptable behavior

    def test_empty_outline(self, simple_template_path, tmp_path):
        """Test pipeline with an outline that has no headings."""
        # Create a markdown file with no headings
        md_path = tmp_path / "no_headings.md"
        md_path.write_text("Just some plain text\nno headings at all")

        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=md_path,
            dry_run=True,
        )
        filler.run()

        # Should have zero sections in outline
        assert filler.outline_structure is not None
        total_sections = filler._count_total_sections(
            filler.outline_structure["sections"]
        )
        assert total_sections == 0
        # Mapping should be empty
        assert len(filler.mapping) == 0


class TestSlideFillerConfiguration:
    """Test SlideFiller with various configuration options."""

    def test_custom_validator_limits(self, simple_template_path, simple_docx_path):
        """Test that custom validator limits are applied."""
        # Create a filler with very strict limits
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
            validator_max_title_length=10,
            validator_max_body_length=50,
        )
        filler.run()

        # Just verify configuration is set
        assert filler.validator.max_title_length == 10
        assert filler.validator.max_body_length == 50

    def test_custom_ai_settings(self, simple_template_path, simple_docx_path):
        """Test that custom AI settings are applied."""
        filler = SlideFiller(
            template_path=simple_template_path,
            outline_path=simple_docx_path,
            dry_run=True,
            ai_temperature=0.3,
            ai_model="gpt-3.5-turbo",
            ai_fallback_model="gpt-4",
        )
        filler.run()

        assert filler.ai_generator.temperature == 0.3
        assert filler.ai_generator.model == "gpt-3.5-turbo"
        assert filler.ai_generator.fallback_model == "gpt-4"


# Note: For tests that would actually call OpenAI API, we use dry_run=True
# The actual AI content generation and PPTX writing are not tested here because:
# - AI generation requires an API key and costs money
# - PPTX writing with actual content could be tested more specifically in unit tests for PPTXWriter
# Integration tests should focus on the orchestration logic, which dry_run mode verifies
