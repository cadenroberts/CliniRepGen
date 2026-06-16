"""
Report Renderer - Renders reports to various output formats.

Supports:
- Markdown
- JSON
- HTML (basic)
"""

from typing import Optional

from clinirepgen.agents.critic import CritiqueResult
from clinirepgen.agents.writer import GeneratedReport
from clinirepgen.reports.templates import CONSORTTemplate, ICHE3Template
from clinirepgen.schemas.trial_facts import TrialFacts


class MarkdownRenderer:
    """Renders reports to Markdown format."""

    def render_report(self, report: GeneratedReport) -> str:
        """Render a GeneratedReport to markdown."""
        lines = [
            f"# {report.title}",
            "",
            f"*Report Type: {report.report_type.upper()}*",
            f"*Generated: {report.generated_at}*",
            f"*Total Words: {report.total_word_count}*",
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
                citations_str = ", ".join(section.citations[:10])
                if len(section.citations) > 10:
                    citations_str += f" (+{len(section.citations) - 10} more)"
                lines.append(f"*Citations: {citations_str}*")
                lines.append("")

        # Coverage summary
        lines.append("---")
        lines.append("")
        lines.append("## Checklist Coverage")
        lines.append("")

        covered = sum(1 for v in report.checklist_coverage.values() if v)
        total = len(report.checklist_coverage)
        lines.append(f"**Coverage: {covered}/{total} items ({covered/total*100:.1f}%)**")
        lines.append("")

        return "\n".join(lines)

    def render_critique(self, critique: CritiqueResult) -> str:
        """Render a CritiqueResult to markdown."""
        lines = [
            "# Report Critique",
            "",
            f"**Report Type:** {critique.report_type}",
            f"**Score:** {critique.overall_score:.1f}/100",
            f"**Validation:** {'✅ PASSED' if critique.passes_validation else '❌ FAILED'}",
            "",
            "---",
            "",
        ]

        # Summary counts
        critical = sum(1 for i in critique.issues if i.severity == "critical")
        major = sum(1 for i in critique.issues if i.severity == "major")
        minor = sum(1 for i in critique.issues if i.severity == "minor")

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- 🔴 Critical Issues: {critical}")
        lines.append(f"- 🟠 Major Issues: {major}")
        lines.append(f"- 🟡 Minor Issues: {minor}")
        lines.append(f"- Missing Items: {len(critique.missing_items)}")
        lines.append(f"- Unused Facts: {len(critique.unused_facts)}")
        lines.append("")

        # Issues detail
        if critique.issues:
            lines.append("## Issues")
            lines.append("")

            for i, issue in enumerate(critique.issues, 1):
                severity_emoji = {"critical": "🔴", "major": "🟠", "minor": "🟡"}.get(issue.severity, "⚪")
                lines.append(f"### {i}. {severity_emoji} {issue.issue_type.replace('_', ' ').title()}")
                lines.append("")
                lines.append(f"**Severity:** {issue.severity}")
                lines.append(f"**Location:** {issue.location}")
                lines.append(f"**Description:** {issue.description}")
                lines.append(f"**Suggestion:** {issue.suggestion}")
                lines.append("")

        # Suggestions
        if critique.suggested_queries:
            lines.append("## Suggested Follow-up Searches")
            lines.append("")
            for query in critique.suggested_queries:
                lines.append(f"- `{query}`")
            lines.append("")

        return "\n".join(lines)

    def render_facts_summary(self, facts: TrialFacts) -> str:
        """Render a summary of TrialFacts to markdown."""
        lines = [
            "# Trial Facts Summary",
            "",
            f"**Trial ID:** {facts.trial_id}",
            f"**Last Updated:** {facts.last_updated}",
            "",
            "---",
            "",
        ]

        # Get all facts
        all_facts = facts.get_all_fact_values()
        populated = [(p, f) for p, f in all_facts if f.value is not None]
        facts.get_null_facts()

        lines.append(f"## Coverage: {len(populated)}/{len(all_facts)} facts populated")
        lines.append("")

        # Group by category
        categories = {}
        for path, fact in populated:
            category = path.split(".")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((path, fact))

        for category, items in sorted(categories.items()):
            lines.append(f"### {category.replace('_', ' ').title()}")
            lines.append("")
            for path, fact in items:
                field = path.split(".")[-1]
                value_str = str(fact.value)[:100]
                if len(str(fact.value)) > 100:
                    value_str += "..."
                confidence = fact.confidence.value if hasattr(fact.confidence, 'value') else str(fact.confidence)
                lines.append(f"- **{field}:** {value_str} _{confidence}_")
            lines.append("")

        return "\n".join(lines)


def render_consort(
    trial_facts: TrialFacts,
    output_path: Optional[str] = None,
) -> str:
    """
    Render a CONSORT-style report from TrialFacts.

    Args:
        trial_facts: Facts to render
        output_path: Optional path to save output

    Returns:
        Markdown string
    """
    template = CONSORTTemplate()
    MarkdownRenderer()

    # Build basic report structure
    lines = [
        f"# {trial_facts.identification.trial_title.value or 'Clinical Trial Report'}",
        "",
        "*CONSORT 2025 Format*",
        "",
        "---",
        "",
    ]

    for section in template.get_sections():
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(f"*{section.description}*")
        lines.append("")

        # Add facts for this section
        for fact_path in section.fact_paths:
            fact = trial_facts.get_fact_by_path(fact_path)
            if fact and fact.value:
                field = fact_path.split(".")[-1].replace("_", " ").title()
                lines.append(f"**{field}:** {fact.value}")
                if fact.provenance.provenances:
                    cites = fact.provenance.to_citations()
                    lines.append(f"  *Source: {', '.join(cites[:3])}*")
                lines.append("")

        # Add subsections
        for sub in section.subsections:
            lines.append(f"### {sub.title}")
            lines.append("")
            for fact_path in sub.fact_paths:
                fact = trial_facts.get_fact_by_path(fact_path)
                if fact and fact.value:
                    field = fact_path.split(".")[-1].replace("_", " ").title()
                    lines.append(f"**{field}:** {fact.value}")
                    lines.append("")

        lines.append("")

    content = "\n".join(lines)

    if output_path:
        with open(output_path, "w") as f:
            f.write(content)

    return content


def render_ich_e3(
    trial_facts: TrialFacts,
    output_path: Optional[str] = None,
) -> str:
    """
    Render an ICH E3-style CSR synopsis from TrialFacts.

    Args:
        trial_facts: Facts to render
        output_path: Optional path to save output

    Returns:
        Markdown string
    """
    template = ICHE3Template()

    lines = [
        "# CLINICAL STUDY REPORT",
        "",
        f"## {trial_facts.identification.trial_title.value or 'Study Title'}",
        "",
        "*ICH E3 Format*",
        "",
        "---",
        "",
    ]

    for section in template.get_sections():
        lines.append(f"## {section.title}")
        lines.append("")

        if section.description:
            lines.append(f"*{section.description}*")
            lines.append("")

        # Add facts for this section
        for fact_path in section.fact_paths:
            fact = trial_facts.get_fact_by_path(fact_path)
            if fact and fact.value:
                field = fact_path.split(".")[-1].replace("_", " ").title()
                lines.append(f"**{field}:** {fact.value}")
                lines.append("")

        # Add subsections
        for sub in section.subsections:
            lines.append(f"### {sub.title}")
            lines.append("")
            for fact_path in sub.fact_paths:
                fact = trial_facts.get_fact_by_path(fact_path)
                if fact and fact.value:
                    field = fact_path.split(".")[-1].replace("_", " ").title()
                    lines.append(f"**{field}:** {fact.value}")
                    lines.append("")

        lines.append("")

    content = "\n".join(lines)

    if output_path:
        with open(output_path, "w") as f:
            f.write(content)

    return content
