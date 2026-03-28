"""Content Mapper for aligning outline sections with template slide placeholders."""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ContentMapper:
    """Maps outline sections to template slide placeholders based on content analysis."""

    # Keyword mappings to placeholder types
    KEYWORD_TO_PLACEHOLDER = {
        'title': 'TITLE',
        'header': 'TITLE',
        'heading': 'TITLE',
        'subtitle': 'SUBTITLE',
        'chart': 'CHART',
        'graph': 'CHART',
        'data': 'CHART',
        'table': 'TABLE',
        'picture': 'PICTURE',
        'image': 'PICTURE',
        'photo': 'PICTURE',
        'diagram': 'PICTURE',
        'bullet': 'BODY',
        'list': 'BODY',
        'text': 'BODY',
        'content': 'BODY',
    }

    def __init__(
        self,
        template_metadata: Dict[str, Any],
        outline_structure: Dict[str, Any],
        strategy: str = "auto"
    ):
        """
        Initialize ContentMapper.

        Args:
            template_metadata: Parsed template metadata from TemplateParser
            outline_structure: Parsed outline structure from OutlineParser
            strategy: Mapping strategy - "auto" (smart matching), "sequential" (first fit),
                     or "hierarchical" (respect outline hierarchy)
        """
        self.template_metadata = template_metadata
        self.outline_structure = outline_structure
        self.strategy = strategy
        self.mapping: List[Dict[str, Any]] = []
        self._stats: Dict[str, int] = {
            'total_sections': 0,
            'mapped_sections': 0,
            'unmapped_sections': 0,
        }

    def map(self) -> List[Dict[str, Any]]:
        """
        Execute the content mapping process.

        Returns:
            List of mapping entries, each containing:
            {
                'section': section dict (with title, level, content, children),
                'layout': layout dict (name, id, placeholders),
                'placeholder': placeholder dict (type, idx, geometry),
                'confidence': float (0.0-1.0),
                'match_reason': str
            }

        Raises:
            RuntimeError: If mapping fails
        """
        try:
            logger.info(
                f"Starting content mapping with strategy '{self.strategy}': "
                f"{self._get_total_section_count()} sections, "
                f"{len(self.template_metadata['slide_layouts'])} layouts"
            )

            self.mapping = []
            self._reset_stats()

            flat_sections = self._flatten_sections(self.outline_structure['sections'])
            self._stats['total_sections'] = len(flat_sections)

            if self.strategy == "hierarchical":
                self._map_hierarchical(flat_sections)
            elif self.strategy == "sequential":
                self._map_sequential(flat_sections)
            else:  # auto (default)
                self._map_auto(flat_sections)

            self._stats['mapped_sections'] = len(self.mapping)
            self._stats['unmapped_sections'] = self._stats['total_sections'] - self._stats['mapped_sections']

            logger.info(
                f"Mapping complete: {self._stats['mapped_sections']}/{self._stats['total_sections']} "
                f"sections mapped, {self._stats['unmapped_sections']} unmatched"
            )

            return self.mapping

        except Exception as e:
            logger.error(f"Content mapping failed: {e}")
            raise RuntimeError(f"Content mapping failed: {e}") from e

    def _get_total_section_count(self, sections: Optional[List[Dict]] = None) -> int:
        """Count total sections including nested."""
        if sections is None:
            sections = self.outline_structure.get('sections', [])
        count = len(sections)
        for section in sections:
            count += self._get_total_section_count(section.get('children', []))
        return count

    def _flatten_sections(self, sections: List[Dict], parent_id: Optional[int] = None) -> List[Dict]:
        """
        Flatten hierarchical sections into a list with parent references.

        Args:
            sections: List of section dictionaries
            parent_id: ID of parent section (for tracking)

        Returns:
            Flat list of all sections with 'parent_id' added
        """
        flat = []
        for section in sections:
            section_copy = section.copy()
            section_copy['parent_id'] = parent_id
            flat.append(section_copy)
            if section.get('children'):
                flat.extend(self._flatten_sections(section['children'], id(section)))
        return flat

    def _reset_stats(self) -> None:
        """Reset mapping statistics."""
        self._stats = {'total_sections': 0, 'mapped_sections': 0, 'unmapped_sections': 0}

    def _map_auto(self, flat_sections: List[Dict]) -> None:
        """
        Auto mapping strategy: intelligent matching based on section properties
        and placeholder capabilities.
        """
        layouts = self.template_metadata['slide_layouts']

        for section in flat_sections:
            # Primary: match by placeholder type based on section title/content keywords
            placeholder_type = self._infer_placeholder_type(section)

            # Find layout with that placeholder type
            layout, placeholder = self._find_layout_with_placeholder(placeholder_type)

            if layout and placeholder:
                confidence = self._calculate_confidence(section, layout, placeholder)
                self.mapping.append({
                    'section': section,
                    'layout': layout,
                    'placeholder': placeholder,
                    'confidence': confidence,
                    'match_reason': f'keyword_match:{placeholder_type}'
                })
                continue

            # Fallback 1: match by section level (hierarchical)
            layout = self._match_layout_by_level(section['level'])
            if layout:
                placeholder = self._select_placeholder_in_layout(layout, section)
                if placeholder:
                    confidence = self._calculate_confidence(section, layout, placeholder)
                    self.mapping.append({
                        'section': section,
                        'layout': layout,
                        'placeholder': placeholder,
                        'confidence': confidence,
                        'match_reason': 'level_based_fallback'
                    })
                    continue

            # Fallback 2: any layout with any content placeholder
            layout, placeholder = self._find_any_content_placeholder()
            if layout and placeholder:
                confidence = 0.3  # Low confidence
                self.mapping.append({
                    'section': section,
                    'layout': layout,
                    'placeholder': placeholder,
                    'confidence': confidence,
                    'match_reason': 'last_resort'
                })
            else:
                logger.warning(f"Could not map section: {section.get('title', 'Unknown')}")

    def _map_sequential(self, flat_sections: List[Dict]) -> None:
        """
        Sequential mapping: assign sections to layouts/placeholders in order,
        cycling through available layouts.
        """
        layouts = self.template_metadata['slide_layouts']
        if not layouts:
            logger.error("No layouts available for sequential mapping")
            return

        # Prepare pool of available placeholder-layout pairs
        placement_pool = []
        for layout in layouts:
            for placeholder in layout['placeholders']:
                placement_pool.append((layout, placeholder))

        if not placement_pool:
            logger.error("No placeholders found in any layout")
            return

        # Cycle through placements
        for idx, section in enumerate(flat_sections):
            layout, placeholder = placement_pool[idx % len(placement_pool)]
            confidence = 1.0 - (0.1 * (idx // len(placement_pool)))  # Decreasing confidence
            confidence = max(0.1, confidence)

            self.mapping.append({
                'section': section,
                'layout': layout,
                'placeholder': placeholder,
                'confidence': confidence,
                'match_reason': 'sequential_cycle'
            })

    def _map_hierarchical(self, flat_sections: List[Dict]) -> None:
        """
        Hierarchical mapping: respects the outline structure, potentially merging
        subsections into parent slide content.
        """
        # Group sections by top-level parent
        top_level_sections = [s for s in flat_sections if s['parent_id'] is None]

        for top_section in top_level_sections:
            # Map top-level section to a title/content slide
            layout, placeholder = self._find_layout_with_placeholder('BODY')
            if not layout:
                layout = self._match_layout_by_level(top_section['level'])
            if not layout:
                continue

            # Decide: does this top section get its own slide or absorb children?
            children = [s for s in flat_sections if s.get('parent_id') == id(top_section)]

            if children and self._should_merge_children(top_section, children):
                # Merge children into top section content - assign to one placeholder
                merged_content = self._merge_section_content(top_section, children)
                top_section['_merged_content'] = merged_content

                placeholder = self._select_placeholder_in_layout(layout, top_section)
                if placeholder:
                    self.mapping.append({
                        'section': top_section,
                        'layout': layout,
                        'placeholder': placeholder,
                        'confidence': 0.9,
                        'match_reason': 'hierarchical_merge'
                    })
                # Skip mapping children individually
                continue
            else:
                # Map top section to its own slide
                placeholder = self._select_placeholder_in_layout(layout, top_section)
                if placeholder:
                    self.mapping.append({
                        'section': top_section,
                        'layout': layout,
                        'placeholder': placeholder,
                        'confidence': 0.85,
                        'match_reason': 'hierarchical_top'
                    })

                # Map children to separate slides
                for child in children:
                    child_layout, child_placeholder = self._find_layout_with_placeholder('BODY')
                    if not child_layout:
                        child_layout = self._match_layout_by_level(child['level'])
                    if child_layout:
                        child_placeholder = self._select_placeholder_in_layout(child_layout, child)
                        if child_placeholder:
                            self.mapping.append({
                                'section': child,
                                'layout': child_layout,
                                'placeholder': child_placeholder,
                                'confidence': 0.8,
                                'match_reason': 'hierarchical_child'
                            })

    def _should_merge_children(self, parent: Dict, children: List[Dict]) -> bool:
        """
        Decide whether children should be merged into parent slide.
        Heuristic: if children are very short or numerous.
        """
        if len(children) > 5:
            return True
        avg_child_length = sum(len(c.get('content', '').split()) for c in children) / len(children)
        return avg_child_length < 10  # Less than 10 words on average

    def _merge_section_content(self, parent: Dict, children: List[Dict]) -> str:
        """Merge parent and children content into a single string."""
        parts = [parent.get('content', '')]
        for child in children:
            parts.append(f"\n{child.get('title', '')}: {child.get('content', '')}")
        return "\n".join(parts)

    def _infer_placeholder_type(self, section: Dict) -> str:
        """
        Infer the desired placeholder type from section title and content.

        Args:
            section: Section dictionary with title and content

        Returns:
            Placeholder type string (e.g., 'TITLE', 'BODY', 'CHART')
        """
        title = section.get('title', '').lower()
        content = section.get('content', '').lower()
        combined = f"{title} {content}"

        for keyword, ph_type in self.KEYWORD_TO_PLACEHOLDER.items():
            if keyword in combined:
                return ph_type

        # Default based on level
        if section.get('level', 0) == 1:
            return 'TITLE'
        else:
            return 'BODY'

    def _find_layout_with_placeholder(self, placeholder_type: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Find a layout that has a placeholder of the specified type.

        Args:
            placeholder_type: Desired placeholder type (e.g., 'TITLE', 'BODY')

        Returns:
            Tuple of (layout_dict, placeholder_dict) or (None, None)
        """
        for layout in self.template_metadata['slide_layouts']:
            for placeholder in layout['placeholders']:
                if placeholder['type'] == placeholder_type:
                    return layout, placeholder
        return None, None

    def _find_any_content_placeholder(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Find any layout with a usable content placeholder (BODY, OBJECT, etc.)."""
        content_types = ['BODY', 'OBJECT', 'CHART', 'TABLE', 'PICTURE']
        for layout in self.template_metadata['slide_layouts']:
            for placeholder in layout['placeholders']:
                if placeholder['type'] in content_types:
                    return layout, placeholder
        return None, None

    def _match_layout_by_level(self, level: int) -> Optional[Dict]:
        """
        Match a section level to an appropriate layout.

        Args:
            level: Section hierarchy level (1 = top, 2 = second, etc.)

        Returns:
            Layout dictionary or None if no match
        """
        layouts = self.template_metadata['slide_layouts']

        if level == 1:
            # Title layouts
            for layout in layouts:
                ph_types = [p['type'] for p in layout['placeholders']]
                if 'TITLE' in ph_types or 'CENTER_TITLE' in ph_types or 'SUBTITLE' in ph_types:
                    return layout
        else:
            # Content layouts
            for layout in layouts:
                ph_types = [p['type'] for p in layout['placeholders']]
                if 'BODY' in ph_types:
                    return layout

        # Fallback: first layout
        return layouts[0] if layouts else None

    def _select_placeholder_in_layout(self, layout: Dict, section: Dict) -> Optional[Dict]:
        """
        Select the most appropriate placeholder in a layout for a section.

        Args:
            layout: Layout dictionary
            section: Section dictionary

        Returns:
            Placeholder dictionary or None if none suitable
        """
        placeholders = layout['placeholders']
        if not placeholders:
            return None

        # Prefer placeholder type inferred from section
        preferred_type = self._infer_placeholder_type(section)
        for ph in placeholders:
            if ph['type'] == preferred_type:
                return ph

        # If title section, prefer any title-type placeholder
        if section.get('level', 0) == 1:
            title_types = ['TITLE', 'CENTER_TITLE', 'SUBTITLE']
            for ph in placeholders:
                if ph['type'] in title_types:
                    return ph

        # Default: first body-type or any
        body_types = ['BODY', 'OBJECT', 'CHART', 'TABLE', 'PICTURE']
        for ph in placeholders:
            if ph['type'] in body_types:
                return ph

        return placeholders[0]

    def _calculate_confidence(self, section: Dict, layout: Dict, placeholder: Dict) -> float:
        """
        Calculate confidence score for a mapping (0.0 to 1.0).

        Factors:
        - Placeholder type matches section intent (0.4)
        - Layout name relevance to section title (0.3)
        - Section level appropriateness (0.3)
        """
        score = 0.0

        # Type match (0.4)
        inferred_type = self._infer_placeholder_type(section)
        if placeholder['type'] == inferred_type:
            score += 0.4
        elif placeholder['type'] in ['OBJECT', 'BODY']:
            score += 0.2

        # Layout name relevance (0.3)
        layout_name = layout['name'].lower()
        title = section.get('title', '').lower()
        if any(word in layout_name for word in title.split() if len(word) > 3)):
            score += 0.3
        elif 'title' in layout_name and section.get('level', 0) == 1:
            score += 0.25

        # Level appropriateness (0.3)
        level = section.get('level', 0)
        if level == 1 and placeholder['type'] in ['TITLE', 'CENTER_TITLE', 'SUBTITLE']:
            score += 0.3
        elif level > 1 and placeholder['type'] in ['BODY', 'OBJECT', 'CHART', 'TABLE']:
            score += 0.3
        elif placeholder['type'] not in ['DATE', 'SLIDE_NUMBER', 'FOOTER']:
            score += 0.1  # Some content placeholder is okay

        return min(1.0, score)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get mapping statistics.

        Returns:
            Dictionary with mapping stats and coverage
        """
        return {
            **self._stats,
            'total_layouts': len(self.template_metadata['slide_layouts']),
            'total_placeholders': sum(len(l['placeholders']) for l in self.template_metadata['slide_layouts']),
            'coverage_ratio': self._stats['mapped_sections'] / max(1, self._stats['total_sections'])
        }

    def get_mapping_by_layout(self) -> Dict[str, List[Dict]]:
        """
        Group mapping entries by layout.

        Returns:
            Dictionary: {layout_name: [mapping_entries, ...]}
        """
        by_layout = {}
        for entry in self.mapping:
            layout_name = entry['layout']['name']
            if layout_name not in by_layout:
                by_layout[layout_name] = []
            by_layout[layout_name].append(entry)
        return by_layout

    def get_unmapped_sections(self) -> List[Dict]:
        """
        Get sections that could not be mapped.

        Returns:
            List of section dictionaries that have no mapping
        """
        mapped_section_ids = {id(entry['section']) for entry in self.mapping}
        flat_sections = self._flatten_sections(self.outline_structure['sections'])
        return [s for s in flat_sections if id(s) not in mapped_section_ids]
