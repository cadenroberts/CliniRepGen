"""
Section Splitter - Splits documents into logical sections.

Uses heading detection and structural analysis to segment
documents into hierarchical sections.
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DetectedHeading:
    """A detected heading in the document."""
    text: str
    level: int
    char_start: int
    char_end: int
    section_number: Optional[str] = None
    page_num: Optional[int] = None


class SectionSplitter:
    """
    Splits document text into hierarchical sections.
    
    Detects headings using patterns like:
    - Numbered sections (1., 1.1, 1.1.1)
    - Uppercase headings
    - Common section names
    """
    
    # Common section heading patterns
    NUMBERED_HEADING = re.compile(
        r'^(\d+(?:\.\d+)*\.?)\s+([A-Z][^\n]{3,80})$',
        re.MULTILINE
    )
    
    UPPERCASE_HEADING = re.compile(
        r'^([A-Z][A-Z\s]{5,60})$',
        re.MULTILINE
    )
    
    # Common clinical trial section names
    COMMON_SECTIONS = [
        "ABSTRACT", "INTRODUCTION", "BACKGROUND", "OBJECTIVES",
        "METHODS", "METHODOLOGY", "STUDY DESIGN", "STUDY POPULATION",
        "ELIGIBILITY CRITERIA", "INCLUSION CRITERIA", "EXCLUSION CRITERIA",
        "INTERVENTIONS", "OUTCOMES", "ENDPOINTS", "STATISTICAL ANALYSIS",
        "SAMPLE SIZE", "RANDOMIZATION", "BLINDING", "RESULTS",
        "EFFICACY", "SAFETY", "ADVERSE EVENTS", "DISCUSSION",
        "CONCLUSIONS", "REFERENCES", "APPENDIX", "APPENDICES",
        "SYNOPSIS", "TITLE PAGE", "TABLE OF CONTENTS",
    ]
    
    def __init__(self, min_section_length: int = 100):
        """
        Initialize the section splitter.
        
        Args:
            min_section_length: Minimum characters for a valid section
        """
        self.min_section_length = min_section_length
    
    def detect_headings(self, text: str) -> List[DetectedHeading]:
        """
        Detect all headings in the document text.
        
        Returns list of DetectedHeading sorted by position.
        """
        headings = []
        
        # Find numbered headings (e.g., "1. Introduction", "3.2.1 Inclusion Criteria")
        for match in self.NUMBERED_HEADING.finditer(text):
            section_num = match.group(1).rstrip('.')
            title = match.group(2).strip()
            level = section_num.count('.') + 1
            
            headings.append(DetectedHeading(
                text=title,
                level=level,
                char_start=match.start(),
                char_end=match.end(),
                section_number=section_num,
            ))
        
        # Find uppercase headings
        for match in self.UPPERCASE_HEADING.finditer(text):
            title = match.group(1).strip()
            
            # Skip if too short or just numbers
            if len(title) < 4 or title.isdigit():
                continue
            
            # Skip if already captured as numbered heading
            overlap = False
            for h in headings:
                if abs(h.char_start - match.start()) < 10:
                    overlap = True
                    break
            if overlap:
                continue
            
            # Check if it's a common section name
            is_common = any(
                title.upper().startswith(common) 
                for common in self.COMMON_SECTIONS
            )
            
            headings.append(DetectedHeading(
                text=title,
                level=1 if is_common else 2,
                char_start=match.start(),
                char_end=match.end(),
            ))
        
        # Sort by position
        headings.sort(key=lambda h: h.char_start)
        
        return headings
    
    def split(self, text: str, doc_id: str) -> List[dict]:
        """
        Split text into sections.
        
        Args:
            text: Full document text
            doc_id: Document ID for generating section IDs
            
        Returns:
            List of section dicts with id, title, content, etc.
        """
        headings = self.detect_headings(text)
        
        if not headings:
            # No headings found - return whole doc as one section
            logger.warning(f"No headings detected in {doc_id}")
            return [{
                "section_id": f"sec_{doc_id}_full",
                "title": "Full Document",
                "level": 1,
                "content": text,
                "char_start": 0,
                "char_end": len(text),
                "section_number": None,
            }]
        
        sections = []
        
        for i, heading in enumerate(headings):
            # Content ends at next heading or document end
            if i + 1 < len(headings):
                content_end = headings[i + 1].char_start
            else:
                content_end = len(text)
            
            content = text[heading.char_end:content_end].strip()
            
            # Skip sections that are too short
            if len(content) < self.min_section_length:
                continue
            
            from clinirepgen.manifest.models import Section
            section_id = Section.generate_id(doc_id, heading.text, heading.char_start)
            
            sections.append({
                "section_id": section_id,
                "title": heading.text,
                "level": heading.level,
                "section_number": heading.section_number,
                "content": content,
                "char_start": heading.char_start,
                "char_end": content_end,
            })
        
        # Build parent-child relationships
        sections = self._build_hierarchy(sections)
        
        return sections
    
    def _build_hierarchy(self, sections: List[dict]) -> List[dict]:
        """Build parent-child relationships between sections."""
        
        for i, section in enumerate(sections):
            section["parent_section_id"] = None
            section["child_section_ids"] = []
            
            # Look backwards for parent (lower level number = higher in hierarchy)
            for j in range(i - 1, -1, -1):
                if sections[j]["level"] < section["level"]:
                    section["parent_section_id"] = sections[j]["section_id"]
                    sections[j]["child_section_ids"].append(section["section_id"])
                    break
        
        return sections
    
    def estimate_page_numbers(self, sections: List[dict], 
                             chars_per_page: int = 3000) -> List[dict]:
        """Estimate page numbers for sections based on character positions."""
        
        for section in sections:
            section["page_start"] = section["char_start"] // chars_per_page + 1
            section["page_end"] = section["char_end"] // chars_per_page + 1
        
        return sections
