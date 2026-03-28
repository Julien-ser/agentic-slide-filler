"""Main SlideFiller class that orchestrates the entire presentation generation pipeline."""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .template_parser import TemplateParser
from .outline_parser import OutlineParser
from .content_mapper import ContentMapper
from .ai_generator import AIContentGenerator
from .validator import ContentValidator
from .pptx_writer import PPTXWriter

logger = logging.getLogger(__name__)


class SlideFiller:
    """
    Orchestrates the end-to-end pipeline for generating presentation slides
    from an outline and a template using AI content generation.
    """

    def __init__(
        self,
        template_path: str | Path,
        outline_path: str | Path,
        api_key: Optional[str] = None,
        output_dir: str | Path = "output",
        cache_dir: str | Path = "cache",
        mapping_strategy: str = "auto",
        validator_max_title_length: int = 100,
        validator_max_subtitle_length: int = 150,
        validator_max_body_bullets: int = 10,
        validator_max_body_length: int = 1000,
        validator_max_image_desc_words: int = 50,
        ai_temperature: float = 0.7,
        ai_model: str = "gpt-4",
        ai_fallback_model: str = "gpt-3.5-turbo",
        ai_max_retries: int = 3,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize SlideFiller with configuration.

        Args:
            template_path: Path to the PowerPoint template (.pptx)
            outline_path: Path to the outline document (.docx or .md)
            api_key: OpenAI API key (if None, uses OPENAI_API_KEY env var)
            output_dir: Directory to save generated presentations
            cache_dir: Directory for AI response caching
            mapping_strategy: Content mapping strategy ("auto", "sequential", "hierarchical")
            validator_*: Content validation constraints
            ai_temperature: AI generation temperature (0.0-1.0)
            ai_model: Primary OpenAI model
            ai_fallback_model: Fallback model if primary fails
            ai_max_retries: Maximum retry attempts for API calls
            dry_run: If True, run through pipeline without generating content or writing files
            verbose: If True, enable verbose logging
        """
        self.template_path = Path(template_path)
        self.outline_path = Path(outline_path)
        self.output_dir = Path(output_dir)
        self.cache_dir = Path(cache_dir)
        self.mapping_strategy = mapping_strategy
        self.dry_run = dry_run
        self.verbose = verbose

        # Setup logging level
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        # Validate paths exist
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found: {self.template_path}")
        if not self.outline_path.exists():
            raise FileNotFoundError(f"Outline not found: {self.outline_path}")

        # Initialize components (dependency injection - we create them with config)
        self.template_parser = TemplateParser(template_path)
        self.outline_parser = OutlineParser(outline_path)
        self.ai_generator = AIContentGenerator(
            api_key=api_key,
            temperature=ai_temperature,
            cache_dir=cache_dir,
            model=ai_model,
            fallback_model=ai_fallback_model,
            max_retries=ai_max_retries,
        )
        self.validator = ContentValidator(
            max_title_length=validator_max_title_length,
            max_subtitle_length=validator_max_subtitle_length,
            max_body_bullets=validator_max_body_bullets,
            max_body_length=validator_max_body_length,
            max_image_desc_words=validator_max_image_desc_words,
        )
        self.pptx_writer = PPTXWriter(template_path, output_dir=output_dir)

        # Storage for parsed data and results
        self.template_metadata: Optional[Dict[str, Any]] = None
        self.outline_structure: Optional[Dict[str, Any]] = None
        self.content_mapper: Optional[ContentMapper] = None
        self.mapping: List[Dict[str, Any]] = []
        self.generated_content: Dict[str, str] = {}
        self.statistics: Optional[Dict[str, Any]] = None

    def run(self, output_name: Optional[str] = None) -> Path:
        """
        Run the complete end-to-end pipeline.

        Steps:
        1. Parse template
        2. Parse outline
        3. Map content
        4. Generate AI content for each mapped section
        5. Validate generated content
        6. Write PPTX

        Args:
            output_name: Optional name for the output file (without .pptx extension)

        Returns:
            Path to the generated presentation file

        Raises:
            RuntimeError: If any step of the pipeline fails
        """
        logger.info("Starting SlideFiller pipeline")
        logger.info(f"Template: {self.template_path}")
        logger.info(f"Outline: {self.outline_path}")

        try:
            # Step 1: Parse template
            logger.info("Step 1: Parsing template...")
            self.template_metadata = self.template_parser.parse()
            logger.info(
                f"Template parsed: {len(self.template_metadata['slide_layouts'])} layouts found"
            )

            # Step 2: Parse outline
            logger.info("Step 2: Parsing outline...")
            self.outline_structure = self.outline_parser.parse()
            section_count = self._count_total_sections(
                self.outline_structure["sections"]
            )
            logger.info(f"Outline parsed: {section_count} sections found")

            # Step 3: Map content
            logger.info("Step 3: Mapping content...")
            self.content_mapper = ContentMapper(
                self.template_metadata,
                self.outline_structure,
                strategy=self.mapping_strategy,
            )
            self.mapping = self.content_mapper.map()
            self.statistics = self.content_mapper.get_statistics()
            logger.info(
                f"Mapping complete: {self.statistics['mapped_sections']}/{self.statistics['total_sections']} "
                f"sections mapped"
            )

            if self.dry_run:
                logger.info(
                    "Dry run mode - skipping content generation and file writing"
                )
                return Path("dry_run_complete")

            # Step 4: Generate AI content
            logger.info("Step 4: Generating AI content...")
            self._generate_content()
            logger.info(f"Generated content for {len(self.generated_content)} sections")

            # Step 5: Validate content
            logger.info("Step 5: Validating content...")
            self._validate_content()
            logger.info("All content passed validation")

            # Step 6: Write PPTX
            logger.info("Step 6: Writing PPTX...")
            output_path = self.pptx_writer.write(
                self.mapping, self.generated_content, output_name
            )
            logger.info(f"Pipeline complete! Output: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise RuntimeError(f"SlideFiller pipeline failed: {e}") from e

    def _count_total_sections(self, sections: List[Dict[str, Any]]) -> int:
        """Recursively count total sections including nested."""
        count = len(sections)
        for section in sections:
            count += self._count_total_sections(section.get("children", []))
        return count

    def _generate_content(self) -> None:
        """Generate AI content for all mapped sections."""
        self.generated_content = {}

        for entry in self.mapping:
            section = entry["section"]
            placeholder_type = entry["placeholder"]["type"]
            layout_name = entry["layout"]["name"]

            # Create a unique key for this section
            section_key = self._make_section_key(section)

            # Prepare context based on placeholder type
            context = {
                "section_title": section.get("title", ""),
                "section_content": section.get("content", ""),
            }

            # For CHART placeholders, we might need chart_data; use section content as data
            if placeholder_type == "CHART":
                context = {"chart_data": section.get("content", "")}

            # Skip if already generated (shouldn't happen but just in case)
            if section_key in self.generated_content:
                logger.debug(f"Content already generated for {section_key}, skipping")
                continue

            logger.debug(
                f"Generating content for section '{section.get('title')}' "
                f"using layout '{layout_name}' placeholder '{placeholder_type}'"
            )

            try:
                content = self.ai_generator.generate(placeholder_type, **context)
                self.generated_content[section_key] = content
            except Exception as e:
                logger.error(
                    f"Failed to generate content for section '{section.get('title')}': {e}"
                )
                # Decide: either fail the whole pipeline or use fallback/placeholder
                # For now, we'll raise to be strict
                raise

    def _validate_content(self) -> None:
        """Validate all generated content."""
        errors = []

        for entry in self.mapping:
            section = entry["section"]
            placeholder_type = entry["placeholder"]["type"]
            section_key = self._make_section_key(section)
            content = self.generated_content.get(section_key, "")

            if not content:
                errors.append(f"Empty content for section '{section.get('title')}'")
                continue

            try:
                self.validator.validate(content, placeholder_type)
            except ValueError as e:
                errors.append(
                    f"Validation failed for section '{section.get('title')}' "
                    f"({placeholder_type}): {e}"
                )

        if errors:
            error_msg = "Content validation errors:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _make_section_key(self, section: Dict[str, Any]) -> str:
        """Create a unique key for a section."""
        title = section.get("title", "").replace(" ", "_").lower()
        level = section.get("level", 0)
        return f"{level}_{title}"

    def get_mapping_report(self) -> str:
        """
        Generate a human-readable report of the content mapping.

        Returns:
            Formatted string report
        """
        if not self.mapping:
            return "No mapping available. Run the pipeline first."

        lines = []
        lines.append("=== Content Mapping Report ===")
        lines.append(f"Template: {self.template_path.name}")
        lines.append(f"Outline: {self.outline_path.name}")
        lines.append(f"Strategy: {self.mapping_strategy}")
        if self.statistics:
            lines.append(
                f"Coverage: {self.statistics['mapped_sections']}/{self.statistics['total_sections']} "
                f"sections ({self.statistics['coverage_ratio'] * 100:.1f}%)"
            )
        lines.append("")
        lines.append("Mapped Sections:")
        for entry in self.mapping:
            section = entry["section"]
            layout = entry["layout"]["name"]
            placeholder = entry["placeholder"]["type"]
            confidence = entry["confidence"]
            reason = entry["match_reason"]
            lines.append(
                f"  [{confidence:.2f}] {section.get('title')} -> {layout} ({placeholder}) [{reason}]"
            )

        # Add unmapped sections if any
        if self.content_mapper:
            unmapped = self.content_mapper.get_unmapped_sections()
            if unmapped:
                lines.append("")
                lines.append("Unmapped Sections:")
                for section in unmapped:
                    lines.append(
                        f"  - {section.get('title')} (level {section.get('level')})"
                    )

        return "\n".join(lines)
