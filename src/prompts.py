"""Prompt engineering module for generating LLM prompts for different slide placeholder types."""

from typing import Dict, Any


PROMPT_TEMPLATES: Dict[str, str] = {
    "TITLE": """You are a presentation designer. Generate a title and subtitle for a slide with the following context:

Outline section: {section_title}
Content: {section_content}

Provide a concise title and an optional subtitle.

Example:
Input: Section: "Introduction", Content: "This project aims to..."
Output:
Title: Project Overview
Subtitle: Goals and Objectives
""",
    "BODY": """Generate bullet points for a content slide based on the following outline:

Section: {section_title}
Content: {section_content}

Create 3-5 bullet points, each starting with a bold heading followed by a brief explanation.

Example:
Input: Section: "Methodology", Content: "We used a mixed-methods approach..."
Output:
- **Research Design**: Mixed-methods approach combining qualitative and quantitative data.
- **Data Collection**: Surveys and interviews conducted over 6 months.
- **Analysis**: Statistical and thematic analysis.

Now generate bullet points:
""",
    "CHART": """You are a data visualization expert. Based on the following data summary, generate a description for a chart that could be used on a slide.

Data summary: {chart_data}

Provide a concise chart title and a brief description of the chart type and key insights.

Example:
Input: Chart data: "Sales increased by 20% each quarter"
Output:
Title: Quarterly Sales Growth
Description: A line chart showing steady upward trend, with Q1 at $100K, Q2 at $120K, Q3 at $144K, Q4 at $173K.

Generate description:
""",
    "PICTURE": """Generate a detailed image description for a slide illustration based on the following context:

Section: {section_title}
Content: {section_content}

Describe a relevant image that would enhance the slide, including subjects, style, and mood.

Example:
Input: Section: "Nature Conservation", Content: "Impacts of climate change on coral reefs"
Output:
A vibrant underwater scene showing colorful coral reefs with some bleaching areas, sunlight filtering through water, diverse marine life. Style: photorealistic, dramatic lighting.

Generate description:
""",
}


def get_prompt(placeholder_type: str, **kwargs: Any) -> str:
    """
    Get a rendered prompt for the specified placeholder type.

    Args:
        placeholder_type: The placeholder type string (e.g., "TITLE", "BODY", "CHART", "PICTURE").
        **kwargs: Context variables to fill the prompt template.

    Returns:
        Rendered prompt string.

    Raises:
        ValueError: If no template exists for the placeholder type.
    """
    # Map CLIP_ART to PICTURE as they are similar
    if placeholder_type == "CLIP_ART":
        placeholder_type = "PICTURE"

    template = PROMPT_TEMPLATES.get(placeholder_type)
    if template is None:
        raise ValueError(f"No prompt template for placeholder type: {placeholder_type}")

    try:
        return template.format(**kwargs)
    except KeyError as e:
        missing = e.args[0]
        raise ValueError(f"Missing required context variable: {missing}") from e
