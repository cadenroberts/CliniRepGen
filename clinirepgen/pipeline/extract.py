"""
Extract Stage - Extracts trial facts from the manifest.

Uses the FactFinder agent to answer checklist questions
and populate the TrialFacts schema.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from clinirepgen.agents.base import AgentConfig
from clinirepgen.agents.fact_finder import FactFinderAgent
from clinirepgen.manifest.models import TrialManifest
from clinirepgen.schemas.trial_facts import TrialFacts

logger = logging.getLogger(__name__)


class ExtractStage:
    """
    Handles fact extraction from Trial Manifest.

    Uses checklist items as questions to find and extract
    relevant facts with provenance tracking.
    """

    def __init__(
        self,
        manifest: TrialManifest,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the extract stage.

        Args:
            manifest: Trial Manifest to extract from
            config: Agent configuration
        """
        self.manifest = manifest
        self.config = config

        self.fact_finder = FactFinderAgent(
            manifest=manifest,
            config=config,
        )

    def extract(
        self,
        checklist: str = "both",
        fact_paths: Optional[List[str]] = None,
    ) -> TrialFacts:
        """
        Extract trial facts.

        Args:
            checklist: Which checklist to use ("consort", "ich_e3", "both")
            fact_paths: Optional specific fact paths to extract

        Returns:
            Populated TrialFacts object
        """
        logger.info(f"Starting extraction with checklist={checklist}")

        trial_facts = self.fact_finder.run(
            checklist=checklist,
            fact_paths=fact_paths,
        )

        logger.info(f"Extraction complete: {len(trial_facts.get_null_facts())} null facts")

        return trial_facts

    def extract_targeted(
        self,
        existing_facts: TrialFacts,
        missing_items: List[str],
    ) -> TrialFacts:
        """
        Extract only missing facts.

        Args:
            existing_facts: Existing TrialFacts to update
            missing_items: List of missing item IDs to extract

        Returns:
            Updated TrialFacts
        """
        logger.info(f"Targeted extraction for {len(missing_items)} items")

        new_facts = self.fact_finder.run(
            fact_paths=missing_items,
        )

        # Merge new facts into existing
        for path, fact in new_facts.get_all_fact_values():
            if fact.value is not None:
                existing_fact = existing_facts.get_fact_by_path(path)
                if existing_fact:
                    existing_fact.value = fact.value
                    existing_fact.confidence = fact.confidence
                    existing_fact.notes = fact.notes
                    for prov in fact.provenance.provenances:
                        existing_fact.add_provenance(prov)

        existing_facts.last_updated = datetime.now().isoformat()

        return existing_facts

    def get_extraction_log(self) -> List[Dict[str, Any]]:
        """Get the extraction log from the fact finder."""
        return self.fact_finder.extraction_log

    def get_coverage_summary(self, trial_facts: TrialFacts) -> Dict[str, Any]:
        """
        Get a summary of fact coverage.

        Returns:
            Dict with coverage statistics
        """
        all_facts = trial_facts.get_all_fact_values()

        total = len(all_facts)
        populated = sum(1 for _, f in all_facts if f.value is not None)
        high_confidence = sum(1 for _, f in all_facts
                             if (f.confidence.value == "high" if hasattr(f.confidence, 'value') else str(f.confidence) == "high"))
        low_confidence = sum(1 for _, f in all_facts if f.is_low_confidence)

        return {
            "total_facts": total,
            "populated": populated,
            "null": total - populated,
            "high_confidence": high_confidence,
            "low_confidence": low_confidence,
            "coverage_pct": (populated / total * 100) if total > 0 else 0,
        }
