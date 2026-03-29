"""Content validation and sanitization for AI-generated text."""

from typing import Optional


class ContentValidator:
    """
    Validates generated content based on placeholder type and constraints.
    """

    def __init__(
        self,
        max_title_length: int = 100,
        max_subtitle_length: int = 150,
        max_body_bullets: int = 10,
        max_body_length: int = 1000,
        max_image_desc_words: int = 50,
    ):
        self.max_title_length = max_title_length
        self.max_subtitle_length = max_subtitle_length
        self.max_body_bullets = max_body_bullets
        self.max_body_length = max_body_length
        self.max_image_desc_words = max_image_desc_words

    def validate(self, content: str, placeholder_type: str) -> None:
        """
        Validate content for a given placeholder type.

        Args:
            content: The generated text content.
            placeholder_type: Type of placeholder (e.g., "TITLE", "BODY").

        Raises:
            ValueError: If content fails validation.
        """
        if not content or not content.strip():
            raise ValueError("Generated content is empty")

        # Normalize type for comparison
        ptype = placeholder_type.upper()

        if ptype in ("TITLE", "CENTER_TITLE"):
            self._validate_title(content)
        elif ptype in ("SUBTITLE",):
            self._validate_subtitle(content)
        elif ptype in ("BODY", "OBJECT"):
            self._validate_body(content)
        elif ptype in ("PICTURE", "CLIP_ART"):
            self._validate_image_description(content)
        elif ptype == "CHART":
            self._validate_chart_description(content)
        # Other types (DATE, SLIDE_NUMBER, FOOTER) have minimal constraints

    def _validate_title(self, content: str) -> None:
        if len(content) > self.max_title_length:
            raise ValueError(
                f"Title exceeds maximum length of {self.max_title_length} characters"
            )
        if "\n" in content:
            raise ValueError("Title should not contain line breaks")

    def _validate_subtitle(self, content: str) -> None:
        if len(content) > self.max_subtitle_length:
            raise ValueError(
                f"Subtitle exceeds maximum length of {self.max_subtitle_length} characters"
            )

    def _validate_body(self, content: str) -> None:
        if len(content) > self.max_body_length:
            raise ValueError(
                f"Body content exceeds maximum length of {self.max_body_length} characters"
            )
        lines = content.strip().split("\n")
        if len(lines) > self.max_body_bullets:
            raise ValueError(
                f"Body has {len(lines)} bullet points, maximum allowed is {self.max_body_bullets}"
            )
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if not stripped.startswith(("-", "*", "•", ">", "•")):
                raise ValueError(
                    f"Bullet {i} does not start with a recognized bullet marker: {stripped[:20]}..."
                )

    def _validate_image_description(self, content: str) -> None:
        words = content.split()
        if len(words) > self.max_image_desc_words:
            raise ValueError(
                f"Image description too long ({len(words)} words), maximum {self.max_image_desc_words}"
            )

    def _validate_chart_description(self, content: str) -> None:
        # Basic check: chart descriptions should be reasonably short and may include numbers
        if len(content) > 200:
            raise ValueError("Chart description is too long (>200 characters)")
