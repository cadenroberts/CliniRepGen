"""
Writer Agent - Generates clinical trial reports from TrialFacts.

Produces two output formats:
1. CONSORT narrative (journal-style)
2. ICH E3 CSR synopsis/structure
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from clinirepgen.agents.base import BaseAgent, AgentConfig
from clinirepgen.schemas.trial_facts import TrialFacts, FactValue, ChecklistCategory
from clinirepgen.schemas.consort import CONSORT_CHECKLIST, get_consort_items_by_category
from clinirepgen.schemas.ich_e3 import ICH_E3_CHECKLIST, get_ich_e3_items_by_category

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """A section of the generated report."""
    title: str
    content: str
    citations: List[str]
    checklist_items_addressed: List[str]
    word_count: int


@dataclass
class GeneratedReport:
    """Complete generated report."""
    report_type: str  # "consort" or "ich_e3"
    title: str
    sections: List[ReportSection]
    total_word_count: int
    checklist_coverage: Dict[str, bool]
    generated_at: str
    facts_used: List[str]


WRITER_SYSTEM_PROMPT = """You are an expert clinical trial report writer. Your task is to generate high-quality, accurate report sections from extracted trial facts.

CRITICAL RULES:
1. ONLY include claims that are directly supported by the provided facts
2. Include inline citations [fact_path] for every factual claim
3. Use precise clinical language appropriate for the target format
4. If a required fact is missing, explicitly note "Not reported" rather than omitting
5. Never hallucinate or infer facts not provided
6. Maintain objectivity and scientific rigor

For CONSORT reports:
- Use journal manuscript style (past tense, third person)
- Structure according to CONSORT 2025 guidelines
- Include all required elements with citations

For ICH E3 reports:
- Use regulatory document style
- Follow ICH E3 section structure
- Be comprehensive but concise
"""


class WriterAgent(BaseAgent):
    """
    Agent that generates clinical trial reports from TrialFacts.
    
    Can produce CONSORT narrative or ICH E3 CSR format.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Writer agent.
        
        Args:
            config: Agent configuration
        """
        super().__init__(config)
        
        # Track which facts are used
        self.facts_used: List[str] = []
    
    def run(
        self,
        trial_facts: TrialFacts,
        report_type: str = "consort",
        sections: Optional[List[str]] = None,
    ) -> GeneratedReport:
        """
        Generate a report from trial facts.
        
        Args:
            trial_facts: Populated TrialFacts object
            report_type: "consort" or "ich_e3"
            sections: Optional list of specific sections to generate
            
        Returns:
            GeneratedReport object
        """
        self.facts_used = []
        
        if report_type == "consort":
            return self._generate_consort_report(trial_facts, sections)
        elif report_type == "ich_e3":
            return self._generate_ich_e3_report(trial_facts, sections)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_consort_report(
        self,
        trial_facts: TrialFacts,
        sections: Optional[List[str]] = None,
    ) -> GeneratedReport:
        """Generate CONSORT-style report."""
        
        # Define CONSORT section structure
        consort_sections = [
            (ChecklistCategory.TITLE_ABSTRACT, "Title and Abstract"),
            (ChecklistCategory.INTRODUCTION, "Introduction"),
            (ChecklistCategory.METHODS, "Methods"),
            (ChecklistCategory.RESULTS, "Results"),
            (ChecklistCategory.DISCUSSION, "Discussion"),
        ]
        
        report_sections = []
        all_items_addressed = []
        
        for category, section_title in consort_sections:
            if sections and category.value not in sections:
                continue
            
            self.logger.info(f"Generating CONSORT section: {section_title}")
            
            # Get checklist items for this category
            items = get_consort_items_by_category(category)
            
            # Get relevant facts
            facts_for_section = self._get_facts_for_items(trial_facts, items)
            
            # Generate section content
            content, citations = self._generate_section_content(
                section_title=section_title,
                category=category.value,
                checklist_items=items,
                facts=facts_for_section,
                report_type="consort",
            )
            
            items_addressed = [f"CONSORT_{item.item_id}" for item in items]
            
            report_sections.append(ReportSection(
                title=section_title,
                content=content,
                citations=citations,
                checklist_items_addressed=items_addressed,
                word_count=len(content.split()),
            ))
            
            all_items_addressed.extend(items_addressed)
        
        # Calculate coverage
        coverage = {}
        for item in CONSORT_CHECKLIST:
            key = f"CONSORT_{item.item_id}"
            coverage[key] = key in all_items_addressed
        
        # Get trial title
        title = "Clinical Trial Report"
        if trial_facts.identification.trial_title.value:
            title = str(trial_facts.identification.trial_title.value)
        
        return GeneratedReport(
            report_type="consort",
            title=title,
            sections=report_sections,
            total_word_count=sum(s.word_count for s in report_sections),
            checklist_coverage=coverage,
            generated_at=datetime.now().isoformat(),
            facts_used=self.facts_used,
        )
    
    def _generate_ich_e3_report(
        self,
        trial_facts: TrialFacts,
        sections: Optional[List[str]] = None,
    ) -> GeneratedReport:
        """Generate ICH E3-style CSR synopsis."""
        
        # Define ICH E3 section structure
        ich_e3_sections = [
            (ChecklistCategory.TITLE_ABSTRACT, "1. Title Page"),
            (ChecklistCategory.TITLE_ABSTRACT, "2. Synopsis"),
            (ChecklistCategory.ETHICS, "5. Ethics"),
            (ChecklistCategory.INTRODUCTION, "7. Introduction"),
            (ChecklistCategory.OBJECTIVES, "8. Study Objectives"),
            (ChecklistCategory.INVESTIGATIONAL_PLAN, "9. Investigational Plan"),
            (ChecklistCategory.STUDY_PATIENTS, "10. Study Patients"),
            (ChecklistCategory.EFFICACY, "11. Efficacy Evaluation"),
            (ChecklistCategory.SAFETY, "12. Safety Evaluation"),
            (ChecklistCategory.CONCLUSIONS, "13. Discussion and Conclusions"),
        ]
        
        report_sections = []
        all_items_addressed = []
        
        for category, section_title in ich_e3_sections:
            if sections and category.value not in sections:
                continue
            
            self.logger.info(f"Generating ICH E3 section: {section_title}")
            
            # Get checklist items for this category
            items = get_ich_e3_items_by_category(category)
            
            # Get relevant facts
            facts_for_section = self._get_facts_for_items(trial_facts, items)
            
            # Generate section content
            content, citations = self._generate_section_content(
                section_title=section_title,
                category=category.value,
                checklist_items=items,
                facts=facts_for_section,
                report_type="ich_e3",
            )
            
            items_addressed = [f"ICH_E3_{item.item_id}" for item in items]
            
            report_sections.append(ReportSection(
                title=section_title,
                content=content,
                citations=citations,
                checklist_items_addressed=items_addressed,
                word_count=len(content.split()),
            ))
            
            all_items_addressed.extend(items_addressed)
        
        # Calculate coverage
        coverage = {}
        for item in ICH_E3_CHECKLIST:
            key = f"ICH_E3_{item.item_id}"
            coverage[key] = key in all_items_addressed
        
        # Get trial title
        title = "Clinical Study Report"
        if trial_facts.identification.trial_title.value:
            title = str(trial_facts.identification.trial_title.value)
        
        return GeneratedReport(
            report_type="ich_e3",
            title=title,
            sections=report_sections,
            total_word_count=sum(s.word_count for s in report_sections),
            checklist_coverage=coverage,
            generated_at=datetime.now().isoformat(),
            facts_used=self.facts_used,
        )
    
    def _get_facts_for_items(
        self,
        trial_facts: TrialFacts,
        items: List[Any],
    ) -> Dict[str, Any]:
        """Get all facts relevant to a list of checklist items."""
        facts = {}
        
        # Get all fact values from trial_facts
        all_facts = trial_facts.get_all_fact_values()
        
        for path, fact_value in all_facts:
            if fact_value.value is not None:
                facts[path] = {
                    "value": fact_value.value,
                    "confidence": fact_value.confidence.value if hasattr(fact_value.confidence, 'value') else str(fact_value.confidence),
                    "citations": fact_value.provenance.to_citations(),
                }
                self.facts_used.append(path)
        
        # Also include additional_facts
        for key, fact_value in trial_facts.additional_facts.items():
            if fact_value.value is not None:
                facts[f"additional.{key}"] = {
                    "value": fact_value.value,
                    "confidence": fact_value.confidence.value if hasattr(fact_value.confidence, 'value') else str(fact_value.confidence),
                    "citations": fact_value.provenance.to_citations(),
                }
                self.facts_used.append(f"additional.{key}")
        
        return facts
    
    def _generate_section_content(
        self,
        section_title: str,
        category: str,
        checklist_items: List[Any],
        facts: Dict[str, Any],
        report_type: str,
    ) -> tuple[str, List[str]]:
        """
        Generate content for a single section.
        
        Returns:
            Tuple of (content string, list of citations used)
        """
        # Build prompt with checklist requirements and available facts
        items_text = "\n".join([
            f"- {item.item_id}: {item.description}"
            for item in checklist_items
        ])
        
        facts_text = json.dumps(facts, indent=2, default=str)
        
        style_guide = ""
        if report_type == "consort":
            style_guide = """
Write in journal manuscript style:
- Past tense, third person
- Concise but complete
- Include all CONSORT required elements
- Use inline citations [fact_path] for every factual claim
"""
        else:
            style_guide = """
Write in regulatory document style:
- Formal, precise language
- Follow ICH E3 structure
- Be comprehensive
- Use inline citations [fact_path] for every factual claim
"""
        
        prompt = f"""Generate the "{section_title}" section for a clinical trial report.

{style_guide}

Checklist items to address:
{items_text}

Available facts (use [path] citations):
{facts_text}

IMPORTANT:
- Only make claims supported by the provided facts
- If a required item has no data, state "Not reported"
- Include citation for every factual statement

Generate the section content now:"""

        messages = [
            {"role": "system", "content": WRITER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        
        try:
            result = self.call_llm(messages)
            content = result["content"] or ""
            
            # Extract citations used
            import re
            citations = re.findall(r'\[([^\]]+)\]', content)
            
            return content, citations
            
        except Exception as e:
            self.logger.error(f"Failed to generate {section_title}: {e}")
            return f"[Section generation failed: {e}]", []
    
    def to_markdown(self, report: GeneratedReport) -> str:
        """Convert a GeneratedReport to markdown format."""
        lines = [
            f"# {report.title}",
            "",
            f"*Report Type: {report.report_type.upper()}*",
            f"*Generated: {report.generated_at}*",
            f"*Word Count: {report.total_word_count}*",
            "",
            "---",
            "",
        ]
        
        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            
            if section.citations:
                lines.append(f"*Sources: {', '.join(section.citations[:5])}{'...' if len(section.citations) > 5 else ''}*")
                lines.append("")
        
        return "\n".join(lines)
