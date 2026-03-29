"""PPTX Writer for populating templates with generated content."""

from pathlib import Path
from typing import Dict, Any, List
import logging
from datetime import datetime

try:
    from pptx import Presentation
except ImportError as e:
    raise ImportError(f"python-pptx is required: {e}")

logger = logging.getLogger(__name__)


class PPTXWriter:
    """Writes generated content into a PowerPoint template."""

    def __init__(
        self,
        template_path: str | Path,
        output_dir: str | Path = "output",
        timestamp: bool = True,
    ):
        """
        Initialize PPTXWriter.

        Args:
            template_path: Path to the PPTX template file
            output_dir: Directory to save output files
            timestamp: Whether to add timestamp to output filename
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = timestamp
        self.prs = None

    def write(
        self,
        mapping: List[Dict[str, Any]],
        generated_content: Dict[str, str],
        output_name: str = None,
    ) -> Path:
        """
        Write generated content to slides based on mapping.

        Args:
            mapping: List of mapping entries from ContentMapper
            generated_content: Dict mapping section identifier to generated content string
            output_name: Optional output filename (without extension)

        Returns:
            Path to the saved PPTX file

        Raises:
            RuntimeError: If writing fails
        """
        try:
            # Load template
            self.prs = Presentation(str(self.template_path))

            # Group mapping by layout for efficient slide creation
            mapping_by_layout = self._group_mapping_by_layout(mapping)

            # Create slides for each layout
            for layout_name, entries in mapping_by_layout.items():
                self._create_slides_for_layout(layout_name, entries, generated_content)

            # Generate output path
            if output_name is None:
                output_name = f"presentation_{self._timestamp_str()}"
            output_path = self.output_dir / f"{output_name}.pptx"

            # Save
            self.prs.save(output_path)
            logger.info(f"Presentation saved to: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to write PPTX: {e}")
            raise RuntimeError(f"PPTX writing failed: {e}") from e

    def _group_mapping_by_layout(
        self, mapping: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group mapping entries by layout name."""
        by_layout = {}
        for entry in mapping:
            layout_name = entry["layout"]["name"]
            if layout_name not in by_layout:
                by_layout[layout_name] = []
            by_layout[layout_name].append(entry)
        return by_layout

    def _create_slides_for_layout(
        self,
        layout_name: str,
        entries: List[Dict[str, Any]],
        generated_content: Dict[str, str],
    ) -> None:
        """
        Create slides for a specific layout.

        Args:
            layout_name: Name of the slide layout to use
            entries: List of mapping entries for this layout
            generated_content: Dict mapping section identifier to content
        """
        # Find the layout index by name
        layout_idx = None
        for idx, slide_layout in enumerate(self.prs.slide_layouts):
            if slide_layout.name == layout_name:
                layout_idx = idx
                break

        if layout_idx is None:
            logger.warning(
                f"Layout '{layout_name}' not found in template, using first layout"
            )
            layout_idx = 0

        layout = self.prs.slide_layouts[layout_idx]

        for entry in entries:
            section = entry["section"]
            placeholder = entry["placeholder"]
            placeholder_idx = placeholder["idx"]

            # Generate section key for content lookup
            section_key = self._make_section_key(section)

            # Get generated content
            content = generated_content.get(section_key, "")
            if not content:
                logger.warning(
                    f"No generated content for section: {section.get('title', 'Unknown')}"
                )
                continue

            # Add slide
            slide = self.prs.slides.add_slide(layout)

            # Fill placeholder
            self._fill_placeholder(slide, placeholder_idx, content, placeholder["type"])

    def _make_section_key(self, section: Dict[str, Any]) -> str:
        """Create a unique key for a section to look up generated content."""
        title = section.get("title", "").replace(" ", "_").lower()
        level = section.get("level", 0)
        return f"{level}_{title}"

    def _fill_placeholder(
        self, slide, placeholder_idx: int, content: str, placeholder_type: str
    ) -> None:
        """
        Fill a specific placeholder on a slide with content.

        Args:
            slide: A slide object from python-pptx
            placeholder_idx: Index of the placeholder
            content: Content string to insert
            placeholder_type: Type of placeholder (TITLE, BODY, etc.)
        """
        try:
            # Try to get placeholder by index
            placeholder = slide.placeholders[placeholder_idx]
        except (KeyError, IndexError):
            logger.warning(f"Placeholder index {placeholder_idx} not found on slide")
            return

        ptype = placeholder_type.upper()

        if ptype in ("TITLE", "CENTER_TITLE", "SUBTITLE"):
            # For title placeholders, set the text frame directly
            if placeholder.has_text_frame:
                placeholder.text = content
            else:
                logger.warning(f"Placeholder {placeholder_idx} has no text frame")
        elif ptype in ("BODY", "OBJECT"):
            # For body/content placeholders, add bullet points
            if placeholder.has_text_frame:
                tf = placeholder.text_frame
                tf.clear()  # Remove any default text
                # Add content as bullet points (assuming each line is a bullet)
                lines = content.strip().split("\n")
                for i, line in enumerate(lines):
                    if i == 0:
                        tf.text = line.strip()
                    else:
                        p = tf.add_paragraph()
                        p.text = line.strip()
                        p.level = 0
            else:
                logger.warning(f"Placeholder {placeholder_idx} has no text frame")
        elif ptype in ("PICTURE", "CLIP_ART"):
            # Picture placeholders need image files; we can't insert from text description
            # Instead, we'll add a text box with the description as a note
            logger.info(f"Picture placeholder received description: {content[:50]}...")
            # Add a text note below the placeholder or in a new textbox
            self._add_text_note(slide, placeholder, content)
        elif ptype == "CHART":
            # Chart placeholders need chart data; we'll add a text description as a note
            logger.info(f"Chart placeholder received description: {content[:50]}...")
            self._add_text_note(slide, placeholder, content)
        else:
            # For other types (DATE, SLIDE_NUMBER, FOOTER), just set text if possible
            if placeholder.has_text_frame:
                placeholder.text = content
            else:
                logger.warning(f"Placeholder type {ptype} has no text frame")

    def _add_text_note(self, slide, placeholder, content: str) -> None:
        """
        Add a text box note near a placeholder (for picture/chart descriptions).

        Args:
            slide: Slide object
            placeholder: The placeholder shape
            content: Text content to add as a note
        """
        try:
            # Get placeholder position and size
            left = placeholder.left
            top = placeholder.top
            width = placeholder.width
            height = placeholder.height

            # Add a textbox below the placeholder
            textbox = slide.shapes.add_textbox(
                left, top + height + 100000, width, 200000
            )
            tf = textbox.text_frame
            tf.text = f"[Note: {content}]"
            tf.paragraphs[0].font.size = 120000  # 12 pt (in EMU)
        except Exception as e:
            logger.warning(f"Could not add text note: {e}")

    def _timestamp_str(self) -> str:
        """Generate timestamp string for filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
