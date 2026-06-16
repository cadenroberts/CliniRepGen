"""
Critic Agent - Validates reports against TrialFacts and checklists.

Checks for:
1. Missing checklist items
2. Unused facts
3. Unsupported narrative claims
4. Factual inconsistencies

Provides actionable feedback for revision.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from clinirepgen.agents.base import AgentConfig, BaseAgent
from clinirepgen.agents.writer import GeneratedReport
from clinirepgen.schemas.consort import CONSORT_CHECKLIST
from clinirepgen.schemas.ich_e3 import ICH_E3_CHECKLIST
from clinirepgen.schemas.trial_facts import ChecklistItem, TrialFacts

logger = logging.getLogger(__name__)


@dataclass
class CritiqueIssue:
    """A single issue identified by the critic."""
    issue_type: str  # "missing_item", "unused_fact", "unsupported_claim", "inconsistency"
    severity: str    # "critical", "major", "minor"
    location: str    # Section/paragraph where issue occurs
    description: str
    suggestion: str  # Suggested fix
    checklist_item_id: Optional[str] = None
    fact_path: Optional[str] = None


@dataclass
class CritiqueResult:
    """Complete critique of a report."""
    report_type: str
    issues: List[CritiqueIssue]
    missing_items: List[str]
    unused_facts: List[str]
    unsupported_claims: List[str]
    overall_score: float  # 0-100
    passes_validation: bool
    suggested_queries: List[str]  # Follow-up searches to address issues
    critique_timestamp: str


CRITIC_SYSTEM_PROMPT = """You are a rigorous clinical trial report reviewer. Your task is to identify issues in generated reports.

Check for:
1. MISSING ITEMS: Required checklist items not addressed
2. UNUSED FACTS: Available facts that weren't included in the report
3. UNSUPPORTED CLAIMS: Statements without proper fact citations
4. INCONSISTENCIES: Claims that contradict the provided facts

For each issue, provide:
- Type of issue
- Severity (critical/major/minor)
- Exact location in the report
- Description of the problem
- Suggested fix

Be thorough but fair. Not every missing element is critical.
"""


class CriticAgent(BaseAgent):
    """
    Agent that critiques generated reports.

    Validates against checklist requirements and identifies
    issues that need to be addressed.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the Critic agent.

        Args:
            config: Agent configuration
        """
        super().__init__(config)

    def run(
        self,
        report: GeneratedReport,
        trial_facts: TrialFacts,
        strict: bool = False,
    ) -> CritiqueResult:
        """
        Critique a generated report.

        Args:
            report: The generated report to critique
            trial_facts: The TrialFacts used to generate the report
            strict: If True, requires all items to pass

        Returns:
            CritiqueResult with identified issues
        """
        issues = []

        # Get appropriate checklist
        if report.report_type == "consort":
            checklist = CONSORT_CHECKLIST
        else:
            checklist = ICH_E3_CHECKLIST

        # Check for missing checklist items
        missing_items = self._check_missing_items(report, checklist)
        for item_id in missing_items:
            issues.append(CritiqueIssue(
                issue_type="missing_item",
                severity="major",
                location="Overall",
                description=f"Checklist item {item_id} not addressed in report",
                suggestion=f"Search for and include information about: {self._get_item_description(item_id, checklist)}",
                checklist_item_id=item_id,
            ))

        # Check for unused facts
        unused_facts = self._check_unused_facts(report, trial_facts)
        for fact_path in unused_facts:
            fact = trial_facts.get_fact_by_path(fact_path)
            if fact and fact.value is not None:
                issues.append(CritiqueIssue(
                    issue_type="unused_fact",
                    severity="minor",
                    location="Overall",
                    description=f"Fact '{fact_path}' with value '{fact.value}' not included",
                    suggestion="Consider including this fact in relevant section",
                    fact_path=fact_path,
                ))

        # Check for unsupported claims using LLM
        unsupported = self._check_unsupported_claims(report, trial_facts)
        for claim in unsupported:
            issues.append(CritiqueIssue(
                issue_type="unsupported_claim",
                severity="critical",
                location=claim.get("location", "Unknown"),
                description=claim.get("description", "Unsupported claim found"),
                suggestion=claim.get("suggestion", "Remove or add citation"),
            ))

        # Calculate overall score
        score = self._calculate_score(issues, len(checklist))

        # Generate suggested queries for missing items
        suggested_queries = self._generate_followup_queries(missing_items, checklist)

        # Determine if validation passes
        critical_issues = [i for i in issues if i.severity == "critical"]
        major_issues = [i for i in issues if i.severity == "major"]

        passes = True
        if strict:
            passes = len(issues) == 0
        else:
            passes = len(critical_issues) == 0 and len(major_issues) <= 3

        return CritiqueResult(
            report_type=report.report_type,
            issues=issues,
            missing_items=missing_items,
            unused_facts=unused_facts,
            unsupported_claims=[c.get("claim", "") for c in unsupported],
            overall_score=score,
            passes_validation=passes,
            suggested_queries=suggested_queries,
            critique_timestamp=datetime.now().isoformat(),
        )

    def _check_missing_items(
        self,
        report: GeneratedReport,
        checklist: List[ChecklistItem],
    ) -> List[str]:
        """Find checklist items not addressed in the report."""
        missing = []

        # Get all items addressed by the report
        addressed = set()
        for section in report.sections:
            addressed.update(section.checklist_items_addressed)

        # Find required items not addressed
        for item in checklist:
            if item.required:
                key = f"{item.source}_{item.item_id}"
                if key not in addressed:
                    # Also check if coverage shows it as covered
                    if not report.checklist_coverage.get(key, False):
                        missing.append(key)

        return missing

    def _check_unused_facts(
        self,
        report: GeneratedReport,
        trial_facts: TrialFacts,
    ) -> List[str]:
        """Find facts that weren't used in the report."""
        # Get all non-null fact paths
        all_facts = set()
        for path, fact in trial_facts.get_all_fact_values():
            if fact.value is not None:
                all_facts.add(path)

        # Get facts that were used
        used_facts = set(report.facts_used)

        # Return unused
        return list(all_facts - used_facts)

    def _check_unsupported_claims(
        self,
        report: GeneratedReport,
        trial_facts: TrialFacts,
    ) -> List[Dict[str, str]]:
        """Use LLM to identify unsupported claims in the report."""
        unsupported = []

        # Build facts reference
        facts_dict = {}
        for path, fact in trial_facts.get_all_fact_values():
            if fact.value is not None:
                facts_dict[path] = str(fact.value)

        for section in report.sections:
            # Skip if section is short
            if section.word_count < 50:
                continue

            # Check for statements without citations
            sentences = re.split(r'[.!?]', section.content)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 20:
                    continue

                # Check if sentence has a citation
                has_citation = bool(re.search(r'\[[^\]]+\]', sentence))

                # Check if sentence makes a factual claim (contains numbers or specific terms)
                makes_claim = bool(re.search(
                    r'\d+%?|\d+\.\d+|patients?|subjects?|participants?|significantly|'
                    r'primary|secondary|adverse|efficacy|safety',
                    sentence,
                    re.IGNORECASE
                ))

                if makes_claim and not has_citation:
                    # This is potentially unsupported
                    unsupported.append({
                        "claim": sentence,
                        "location": section.title,
                        "description": f"Factual claim without citation: '{sentence[:100]}...'",
                        "suggestion": "Add citation [fact_path] or remove if not supported by facts",
                    })

        return unsupported[:10]  # Limit to top 10

    def _calculate_score(self, issues: List[CritiqueIssue], total_items: int) -> float:
        """Calculate overall quality score (0-100)."""
        if total_items == 0:
            return 100.0

        # Deduct points based on issues
        score = 100.0

        for issue in issues:
            if issue.severity == "critical":
                score -= 10
            elif issue.severity == "major":
                score -= 5
            else:
                score -= 1

        return max(0.0, score)

    def _generate_followup_queries(
        self,
        missing_items: List[str],
        checklist: List[ChecklistItem],
    ) -> List[str]:
        """Generate suggested search queries for missing items."""
        queries = []

        for item_key in missing_items[:5]:  # Limit to top 5
            # Parse item key
            parts = item_key.split("_", 1)
            if len(parts) != 2:
                continue

            source, item_id = parts

            # Find the item
            for item in checklist:
                if item.item_id == item_id:
                    # Generate query from description
                    desc_words = item.description.lower().split()[:10]
                    query = " ".join(desc_words)
                    queries.append(query)
                    break

        return queries

    def _get_item_description(self, item_key: str, checklist: List[ChecklistItem]) -> str:
        """Get description for a checklist item key."""
        parts = item_key.split("_", 1)
        if len(parts) != 2:
            return item_key

        source, item_id = parts

        for item in checklist:
            if item.item_id == item_id:
                return item.description

        return item_key

    def to_markdown(self, critique: CritiqueResult) -> str:
        """Convert critique result to markdown format."""
        lines = [
            "# Report Critique",
            "",
            f"**Report Type:** {critique.report_type}",
            f"**Overall Score:** {critique.overall_score:.1f}/100",
            f"**Passes Validation:** {'✅ Yes' if critique.passes_validation else '❌ No'}",
            f"**Timestamp:** {critique.critique_timestamp}",
            "",
            "---",
            "",
        ]

        # Issues summary
        lines.append("## Issues Summary")
        lines.append("")

        critical = [i for i in critique.issues if i.severity == "critical"]
        major = [i for i in critique.issues if i.severity == "major"]
        minor = [i for i in critique.issues if i.severity == "minor"]

        lines.append(f"- 🔴 Critical: {len(critical)}")
        lines.append(f"- 🟠 Major: {len(major)}")
        lines.append(f"- 🟡 Minor: {len(minor)}")
        lines.append("")

        # Detailed issues
        if critique.issues:
            lines.append("## Detailed Issues")
            lines.append("")

            for i, issue in enumerate(critique.issues, 1):
                emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(issue.severity, "⚪")
                lines.append(f"### {i}. {emoji} {issue.issue_type.replace('_', ' ').title()}")
                lines.append(f"**Location:** {issue.location}")
                lines.append(f"**Description:** {issue.description}")
                lines.append(f"**Suggestion:** {issue.suggestion}")
                lines.append("")

        # Suggested queries
        if critique.suggested_queries:
            lines.append("## Suggested Follow-up Queries")
            lines.append("")
            for query in critique.suggested_queries:
                lines.append(f"- `{query}`")
            lines.append("")

        return "\n".join(lines)
