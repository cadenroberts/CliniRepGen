"""
Generate Stage - Generates reports and runs critique loop.

Handles:
- Report generation (CONSORT, ICH E3)
- Critique and validation
- Iterative refinement
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from clinirepgen.agents.base import AgentConfig
from clinirepgen.agents.critic import CriticAgent, CritiqueResult
from clinirepgen.agents.writer import GeneratedReport, WriterAgent
from clinirepgen.schemas.trial_facts import TrialFacts

logger = logging.getLogger(__name__)


class GenerateStage:
    """
    Handles report generation and critique.

    Runs the write-critique-revise loop until validation
    passes or max iterations reached.
    """

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        output_dir: str = "output",
    ):
        """
        Initialize the generate stage.

        Args:
            config: Agent configuration
            output_dir: Directory for output files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.writer = WriterAgent(config=config)
        self.critic = CriticAgent(config=config)

    def generate(
        self,
        trial_facts: TrialFacts,
        report_type: str,
        sections: Optional[List[str]] = None,
    ) -> GeneratedReport:
        """
        Generate a single report.

        Args:
            trial_facts: Facts to generate from
            report_type: "consort" or "ich_e3"
            sections: Optional specific sections to generate

        Returns:
            GeneratedReport object
        """
        logger.info(f"Generating {report_type} report")

        return self.writer.run(
            trial_facts=trial_facts,
            report_type=report_type,
            sections=sections,
        )

    def critique(
        self,
        report: GeneratedReport,
        trial_facts: TrialFacts,
        strict: bool = False,
    ) -> CritiqueResult:
        """
        Critique a generated report.

        Args:
            report: Report to critique
            trial_facts: Facts the report was generated from
            strict: If True, require all items to pass

        Returns:
            CritiqueResult with issues
        """
        logger.info(f"Critiquing {report.report_type} report")

        return self.critic.run(
            report=report,
            trial_facts=trial_facts,
            strict=strict,
        )

    def generate_with_critique(
        self,
        trial_facts: TrialFacts,
        report_type: str,
        max_iterations: int = 3,
        strict: bool = False,
    ) -> Tuple[GeneratedReport, CritiqueResult, int]:
        """
        Generate report with critique loop.

        Args:
            trial_facts: Facts to generate from
            report_type: "consort" or "ich_e3"
            max_iterations: Max revision attempts
            strict: Strict validation mode

        Returns:
            Tuple of (final report, final critique, iterations)
        """
        iteration = 0
        report = None
        critique = None

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Generation iteration {iteration}/{max_iterations}")

            # Generate
            report = self.generate(trial_facts, report_type)

            # Critique
            critique = self.critique(report, trial_facts, strict)

            if critique.passes_validation:
                logger.info(f"Report passed validation at iteration {iteration}")
                break
            else:
                logger.info(f"Critique found {len(critique.issues)} issues, score {critique.overall_score:.1f}")

        return report, critique, iteration

    def generate_all(
        self,
        trial_facts: TrialFacts,
        report_types: Optional[List[str]] = None,
        with_critique: bool = True,
        max_iterations: int = 3,
    ) -> Dict[str, Tuple[GeneratedReport, Optional[CritiqueResult]]]:
        """
        Generate all report types.

        Args:
            trial_facts: Facts to generate from
            report_types: List of report types (default: both)
            with_critique: Whether to run critique
            max_iterations: Max iterations if using critique

        Returns:
            Dict mapping report_type to (report, critique)
        """
        types = report_types or ["consort", "ich_e3"]
        results = {}

        for report_type in types:
            if with_critique:
                report, critique, _ = self.generate_with_critique(
                    trial_facts, report_type, max_iterations
                )
                results[report_type] = (report, critique)
            else:
                report = self.generate(trial_facts, report_type)
                results[report_type] = (report, None)

        return results

    def save_report(
        self,
        report: GeneratedReport,
        filename: Optional[str] = None,
        format: str = "markdown",
    ) -> str:
        """
        Save a report to file.

        Args:
            report: Report to save
            filename: Optional filename (auto-generated if not provided)
            format: Output format ("markdown", "json")

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{report.report_type}_{timestamp}"

        if format == "markdown":
            ext = ".md"
            content = self.writer.to_markdown(report)
        else:
            ext = ".json"
            content = report.model_dump_json(indent=2)

        filepath = self.output_dir / f"{filename}{ext}"
        with open(filepath, "w") as f:
            f.write(content)

        logger.info(f"Saved report to {filepath}")
        return str(filepath)

    def save_critique(
        self,
        critique: CritiqueResult,
        filename: Optional[str] = None,
    ) -> str:
        """
        Save a critique to file.

        Args:
            critique: Critique to save
            filename: Optional filename

        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"critique_{critique.report_type}_{timestamp}"

        filepath = self.output_dir / f"{filename}.md"
        with open(filepath, "w") as f:
            f.write(self.critic.to_markdown(critique))

        logger.info(f"Saved critique to {filepath}")
        return str(filepath)
