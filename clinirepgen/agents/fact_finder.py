"""
FactFinder Agent - Extracts trial facts from the Trial Manifest.

Uses the manifest search/access tools to find and extract facts
for each checklist item, populating the TrialFacts schema.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from clinirepgen.agents.base import AgentConfig, BaseAgent
from clinirepgen.manifest.models import TrialManifest
from clinirepgen.schemas.consort import CONSORT_CHECKLIST, CONSORT_TO_FACTS_MAP
from clinirepgen.schemas.ich_e3 import ICH_E3_CHECKLIST, ICH_E3_TO_FACTS_MAP
from clinirepgen.schemas.provenance import Provenance, ProvenanceType
from clinirepgen.schemas.trial_facts import (
    ChecklistItem,
    ConfidenceLevel,
    FactValue,
    TrialFacts,
)
from clinirepgen.tools.manifest_tools import ManifestTools

logger = logging.getLogger(__name__)


FACT_FINDER_SYSTEM_PROMPT = """You are a clinical trial fact extraction expert. Your task is to find specific information in trial documents to answer checklist questions.

You have access to tools to search and read trial documents:
- search_sections(query, filters): Search document sections by query
- search_tables(query, filters): Search tables by query
- open_section(section_id): Read full content of a section
- get_table(table_id): Get full table data
- get_table_cell(table_id, row, col): Get a specific cell value

For each question, you should:
1. Search for relevant sections/tables using specific clinical terminology
2. Read the most promising results
3. Extract the exact fact with provenance information

CRITICAL RULES:
- Only extract facts that are EXPLICITLY stated in the documents
- Never hallucinate or infer facts not directly supported by text
- If information is not found, report null with low confidence
- Always record the exact source (document, section, page) for each fact
- For numerical values, copy exactly as stated (don't round or convert)
- Note any conflicts between different sources

Respond with a JSON object containing:
{
    "value": <extracted value or null if not found>,
    "confidence": "high" | "medium" | "low" | "unverified",
    "provenance": {
        "file_name": <source document>,
        "section_title": <section where found>,
        "text_span": <exact quote>,
        "page_num": <page number if known>
    },
    "notes": <any conflicts or issues>
}
"""


class FactFinderAgent(BaseAgent):
    """
    Agent that extracts trial facts from the Trial Manifest.

    Uses checklist items as questions and searches the manifest
    to find and extract the relevant information.
    """

    def __init__(
        self,
        manifest: TrialManifest,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the FactFinder agent.

        Args:
            manifest: Trial Manifest to search
            config: Agent configuration
        """
        super().__init__(config)

        self.manifest = manifest
        self.tools = ManifestTools(manifest)

        # Track extraction progress
        self.extraction_log: List[Dict[str, Any]] = []

    def run(
        self,
        checklist: str = "both",
        fact_paths: Optional[List[str]] = None,
    ) -> TrialFacts:
        """
        Extract trial facts for checklist items.

        Args:
            checklist: Which checklist to use ("consort", "ich_e3", or "both")
            fact_paths: Optional specific fact paths to extract (overrides checklist)

        Returns:
            Populated TrialFacts object
        """
        # Initialize TrialFacts
        trial_facts = TrialFacts(
            trial_id=self.manifest.trial_id,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )

        # Get checklist items to process
        if fact_paths:
            items_to_extract = self._get_items_for_paths(fact_paths)
        else:
            items_to_extract = self._get_checklist_items(checklist)

        self.logger.info(f"Extracting {len(items_to_extract)} items")

        # Extract each item
        for item in items_to_extract:
            try:
                self.logger.info(f"Extracting: {item.item_id} - {item.description[:50]}...")
                fact_value = self._extract_fact(item)

                # Store in TrialFacts
                self._store_fact(trial_facts, item, fact_value)

                # Log progress
                self.extraction_log.append({
                    "item_id": item.item_id,
                    "description": item.description,
                    "value": fact_value.value,
                    "confidence": fact_value.confidence,
                    "has_provenance": len(fact_value.provenance.provenances) > 0,
                })

            except Exception as e:
                self.logger.error(f"Failed to extract {item.item_id}: {e}")
                self.extraction_log.append({
                    "item_id": item.item_id,
                    "error": str(e),
                })

        # Update completion stats
        trial_facts.last_updated = datetime.now().isoformat()
        trial_facts.checklist_coverage = self._calculate_coverage(trial_facts, items_to_extract)

        return trial_facts

    def _extract_fact(self, item: ChecklistItem) -> FactValue:
        """
        Extract a single fact for a checklist item.

        Args:
            item: The checklist item to extract

        Returns:
            FactValue with extracted data and provenance
        """
        # Build extraction prompt
        question = f"""Extract the following information from the trial documents:

Checklist Item: {item.item_id}
Category: {item.category}
Question: {item.description}

Search the documents and find the relevant information. If found, extract the exact value with its source."""

        messages = [
            {"role": "system", "content": FACT_FINDER_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        # First, search for relevant content
        search_results = self._search_for_item(item)

        if search_results:
            # Add search results to context
            context = self._format_search_results(search_results)
            messages.append({"role": "assistant", "content": f"I found these relevant sections:\n{context}\n\nLet me extract the specific information."})

        # Call LLM to extract
        try:
            result = self.call_llm_json(messages)
            return self._parse_extraction_result(result, item)
        except Exception as e:
            self.logger.warning(f"Extraction failed for {item.item_id}: {e}")
            return FactValue(
                value=None,
                confidence=ConfidenceLevel.UNVERIFIED,
                notes=f"Extraction failed: {str(e)}",
                checklist_item_id=item.item_id,
            )

    def _search_for_item(self, item: ChecklistItem) -> List[Dict]:
        """Search the manifest for content relevant to a checklist item."""
        results = []

        # Build search queries from the item description
        queries = self._generate_search_queries(item)

        # Search sections
        for query in queries[:3]:  # Limit queries
            section_results = self.tools.search_sections(
                query=query,
                tags=[item.category.value] if item.category else None,
                max_results=3,
            )
            results.extend([
                {"type": "section", "result": r}
                for r in section_results
            ])

        # Search tables for quantitative items
        if any(kw in item.description.lower() for kw in
               ["number", "sample size", "enrollment", "participants", "baseline", "adverse"]):
            for query in queries[:2]:
                table_results = self.tools.search_tables(query=query, max_results=3)
                results.extend([
                    {"type": "table", "result": r}
                    for r in table_results
                ])

        return results

    def _generate_search_queries(self, item: ChecklistItem) -> List[str]:
        """Generate search queries from a checklist item."""
        queries = []

        # Use key terms from description
        desc_lower = item.description.lower()

        # Direct query from description (first 100 chars)
        queries.append(item.description[:100])

        # Extract key clinical terms
        term_patterns = [
            ("randomization", "randomization method"),
            ("randomisation", "randomisation method"),
            ("blinding", "blinding method"),
            ("masking", "masking method"),
            ("sample size", "sample size calculation"),
            ("eligibility", "eligibility criteria"),
            ("inclusion", "inclusion criteria"),
            ("exclusion", "exclusion criteria"),
            ("primary outcome", "primary endpoint"),
            ("secondary outcome", "secondary endpoint"),
            ("adverse event", "adverse events safety"),
            ("serious adverse", "serious adverse events"),
            ("baseline", "baseline characteristics"),
            ("intervention", "intervention treatment"),
            ("comparator", "comparator control"),
            ("statistical", "statistical analysis"),
        ]

        for pattern, query in term_patterns:
            if pattern in desc_lower:
                queries.append(query)

        return queries[:5]

    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results for inclusion in prompt."""
        formatted = []

        for i, item in enumerate(results[:10], 1):
            r = item["result"]
            formatted.append(f"{i}. [{r.source_type.upper()}] {r.title}")
            formatted.append(f"   Score: {r.score:.1f} | ID: {r.id}")
            formatted.append(f"   Snippet: {r.snippet[:150]}...")

            # Get full content for top results
            if i <= 3:
                if r.source_type == "section":
                    content = self.tools.open_section(r.id)
                    if content:
                        formatted.append(f"   Full content:\n   {content['content'][:500]}...")
                elif r.source_type == "table":
                    table = self.tools.get_table(r.id)
                    if table:
                        formatted.append(f"   Table data:\n   {table['markdown'][:500] if table.get('markdown') else 'N/A'}...")

            formatted.append("")

        return "\n".join(formatted)

    def _parse_extraction_result(self, result: Dict, item: ChecklistItem) -> FactValue:
        """Parse the LLM extraction result into a FactValue."""
        fact_value = FactValue(checklist_item_id=item.item_id)

        # Extract value
        fact_value.value = result.get("value")

        # Parse confidence
        confidence_str = result.get("confidence", "unverified").lower()
        confidence_map = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
            "unverified": ConfidenceLevel.UNVERIFIED,
        }
        fact_value.confidence = confidence_map.get(confidence_str, ConfidenceLevel.UNVERIFIED)

        # Parse provenance
        prov_data = result.get("provenance", {})
        if prov_data and prov_data.get("file_name"):
            provenance = Provenance(
                file_id="unknown",
                file_name=prov_data.get("file_name", "unknown"),
                section_title=prov_data.get("section_title"),
                text_span=prov_data.get("text_span"),
                page_num=prov_data.get("page_num"),
                source_type=ProvenanceType.SECTION,
                extraction_method="llm",
                extraction_timestamp=datetime.now().isoformat(),
            )
            fact_value.add_provenance(provenance)

        # Add notes
        fact_value.notes = result.get("notes")

        return fact_value

    def _store_fact(self, trial_facts: TrialFacts, item: ChecklistItem, fact_value: FactValue) -> None:
        """Store extracted fact in the appropriate TrialFacts field."""
        # Get the fact paths for this item
        if item.source == "CONSORT":
            paths = CONSORT_TO_FACTS_MAP.get(item.item_id, [])
        else:
            paths = ICH_E3_TO_FACTS_MAP.get(item.item_id, [])

        if not paths:
            # Store in additional_facts
            key = f"{item.source}_{item.item_id}"
            trial_facts.additional_facts[key] = fact_value
            return

        # Store in first matching path
        for path in paths:
            existing = trial_facts.get_fact_by_path(path)
            if existing and existing.is_null:
                # Update the existing null fact
                existing.value = fact_value.value
                existing.confidence = fact_value.confidence
                existing.notes = fact_value.notes
                for prov in fact_value.provenance.provenances:
                    existing.add_provenance(prov)
                break

    def _get_checklist_items(self, checklist: str) -> List[ChecklistItem]:
        """Get checklist items based on selection."""
        items = []

        if checklist in ["consort", "both"]:
            items.extend(CONSORT_CHECKLIST)

        if checklist in ["ich_e3", "both"]:
            items.extend(ICH_E3_CHECKLIST)

        return items

    def _get_items_for_paths(self, fact_paths: List[str]) -> List[ChecklistItem]:
        """Get checklist items that map to specific fact paths."""
        items = []

        for path in fact_paths:
            # Search CONSORT mapping
            for item_id, paths in CONSORT_TO_FACTS_MAP.items():
                if path in paths:
                    for item in CONSORT_CHECKLIST:
                        if item.item_id == item_id:
                            items.append(item)
                            break

            # Search ICH E3 mapping
            for item_id, paths in ICH_E3_TO_FACTS_MAP.items():
                if path in paths:
                    for item in ICH_E3_CHECKLIST:
                        if item.item_id == item_id:
                            items.append(item)
                            break

        return items

    def _calculate_coverage(self, trial_facts: TrialFacts, items: List[ChecklistItem]) -> Dict[str, bool]:
        """Calculate which checklist items have been covered."""
        coverage = {}

        for item in items:
            key = f"{item.source}_{item.item_id}"

            # Check if any mapped paths have values
            if item.source == "CONSORT":
                paths = CONSORT_TO_FACTS_MAP.get(item.item_id, [])
            else:
                paths = ICH_E3_TO_FACTS_MAP.get(item.item_id, [])

            has_value = False
            for path in paths:
                fact = trial_facts.get_fact_by_path(path)
                if fact and not fact.is_null:
                    has_value = True
                    break

            # Also check additional_facts
            if key in trial_facts.additional_facts:
                if not trial_facts.additional_facts[key].is_null:
                    has_value = True

            coverage[key] = has_value

        return coverage
