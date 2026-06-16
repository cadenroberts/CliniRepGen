"""
Report Templates - Structure templates for CONSORT and ICH E3 reports.

Templates define the section structure and content requirements
for each report type.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TemplateSection:
    """A section in a report template."""
    id: str
    title: str
    level: int = 1
    required: bool = True
    description: str = ""
    fact_paths: List[str] = field(default_factory=list)
    checklist_items: List[str] = field(default_factory=list)
    subsections: List["TemplateSection"] = field(default_factory=list)


class BaseTemplate(ABC):
    """Base class for report templates."""

    @abstractmethod
    def get_sections(self) -> List[TemplateSection]:
        """Get all sections in the template."""
        pass

    @abstractmethod
    def get_section(self, section_id: str) -> Optional[TemplateSection]:
        """Get a specific section by ID."""
        pass

    def get_required_facts(self) -> List[str]:
        """Get list of all required fact paths."""
        facts = []
        for section in self.get_sections():
            facts.extend(section.fact_paths)
            for sub in section.subsections:
                facts.extend(sub.fact_paths)
        return list(set(facts))

    def get_checklist_items(self) -> List[str]:
        """Get list of all checklist items covered."""
        items = []
        for section in self.get_sections():
            items.extend(section.checklist_items)
            for sub in section.subsections:
                items.extend(sub.checklist_items)
        return list(set(items))


class CONSORTTemplate(BaseTemplate):
    """Template for CONSORT 2025 journal manuscript format."""

    def __init__(self):
        self._sections = self._build_sections()
        self._section_map = {s.id: s for s in self._sections}

    def _build_sections(self) -> List[TemplateSection]:
        return [
            TemplateSection(
                id="title_abstract",
                title="Title and Abstract",
                level=1,
                description="Title identifying trial as randomized; structured abstract",
                checklist_items=["1a", "1b"],
                subsections=[
                    TemplateSection(
                        id="title",
                        title="Title",
                        level=2,
                        fact_paths=["identification.trial_title"],
                        checklist_items=["1a"],
                    ),
                    TemplateSection(
                        id="abstract",
                        title="Abstract",
                        level=2,
                        checklist_items=["1b"],
                    ),
                ],
            ),
            TemplateSection(
                id="introduction",
                title="Introduction",
                level=1,
                description="Background, rationale, and objectives",
                checklist_items=["6", "7"],
                subsections=[
                    TemplateSection(
                        id="background",
                        title="Background and Rationale",
                        level=2,
                        checklist_items=["6"],
                    ),
                    TemplateSection(
                        id="objectives",
                        title="Objectives",
                        level=2,
                        fact_paths=["outcomes.primary_outcome"],
                        checklist_items=["7"],
                    ),
                ],
            ),
            TemplateSection(
                id="methods",
                title="Methods",
                level=1,
                description="Trial design, participants, interventions, outcomes, and analysis",
                checklist_items=["8", "9", "10", "11", "12a", "12b", "13", "14", "15",
                                "16a", "16b", "17a", "17b", "18", "19", "20a", "20b",
                                "21a", "21b", "21c", "21d"],
                subsections=[
                    TemplateSection(
                        id="trial_design",
                        title="Trial Design",
                        level=2,
                        fact_paths=["design.design_type", "design.allocation_ratio", "design.framework"],
                        checklist_items=["9"],
                    ),
                    TemplateSection(
                        id="participants",
                        title="Participants",
                        level=2,
                        fact_paths=["population.inclusion_criteria", "population.exclusion_criteria"],
                        checklist_items=["12a", "12b"],
                    ),
                    TemplateSection(
                        id="interventions",
                        title="Interventions",
                        level=2,
                        fact_paths=["intervention.intervention_name", "intervention.intervention_dose",
                                   "intervention.comparator_name"],
                        checklist_items=["13"],
                    ),
                    TemplateSection(
                        id="outcomes",
                        title="Outcomes",
                        level=2,
                        fact_paths=["outcomes.primary_outcome", "outcomes.secondary_outcomes"],
                        checklist_items=["14"],
                    ),
                    TemplateSection(
                        id="sample_size",
                        title="Sample Size",
                        level=2,
                        fact_paths=["statistics.sample_size_calculation"],
                        checklist_items=["16a", "16b"],
                    ),
                    TemplateSection(
                        id="randomization",
                        title="Randomization",
                        level=2,
                        fact_paths=["design.randomization_method", "design.randomization_details"],
                        checklist_items=["17a", "17b", "18", "19"],
                    ),
                    TemplateSection(
                        id="blinding",
                        title="Blinding",
                        level=2,
                        fact_paths=["design.blinding", "design.blinding_details"],
                        checklist_items=["20a", "20b"],
                    ),
                    TemplateSection(
                        id="statistical_methods",
                        title="Statistical Methods",
                        level=2,
                        fact_paths=["statistics.statistical_methods", "statistics.analysis_population"],
                        checklist_items=["21a", "21b", "21c", "21d"],
                    ),
                ],
            ),
            TemplateSection(
                id="results",
                title="Results",
                level=1,
                description="Participant flow, recruitment, baseline, outcomes, and harms",
                checklist_items=["22a", "22b", "23a", "23b", "24a", "24b", "25", "26", "27", "28"],
                subsections=[
                    TemplateSection(
                        id="participant_flow",
                        title="Participant Flow",
                        level=2,
                        fact_paths=["results.participants_randomized", "results.participants_analyzed"],
                        checklist_items=["22a", "22b"],
                    ),
                    TemplateSection(
                        id="recruitment",
                        title="Recruitment",
                        level=2,
                        fact_paths=["dates.first_enrollment_date", "dates.last_enrollment_date"],
                        checklist_items=["23a", "23b"],
                    ),
                    TemplateSection(
                        id="baseline_data",
                        title="Baseline Data",
                        level=2,
                        fact_paths=["population.actual_enrollment", "population.age_range"],
                        checklist_items=["25"],
                    ),
                    TemplateSection(
                        id="outcomes_estimation",
                        title="Outcomes and Estimation",
                        level=2,
                        fact_paths=["results.primary_result", "results.effect_size",
                                   "results.confidence_interval", "results.p_value"],
                        checklist_items=["26"],
                    ),
                    TemplateSection(
                        id="harms",
                        title="Harms",
                        level=2,
                        fact_paths=["safety.adverse_events_summary", "safety.serious_adverse_events"],
                        checklist_items=["27"],
                    ),
                ],
            ),
            TemplateSection(
                id="discussion",
                title="Discussion",
                level=1,
                description="Interpretation and limitations",
                checklist_items=["29", "30"],
                subsections=[
                    TemplateSection(
                        id="interpretation",
                        title="Interpretation",
                        level=2,
                        checklist_items=["29"],
                    ),
                    TemplateSection(
                        id="limitations",
                        title="Limitations",
                        level=2,
                        checklist_items=["30"],
                    ),
                ],
            ),
        ]

    def get_sections(self) -> List[TemplateSection]:
        return self._sections

    def get_section(self, section_id: str) -> Optional[TemplateSection]:
        return self._section_map.get(section_id)


class ICHE3Template(BaseTemplate):
    """Template for ICH E3 Clinical Study Report format."""

    def __init__(self):
        self._sections = self._build_sections()
        self._section_map = {s.id: s for s in self._sections}

    def _build_sections(self) -> List[TemplateSection]:
        return [
            TemplateSection(
                id="title_page",
                title="1. Title Page",
                level=1,
                description="Study identification and key information",
                fact_paths=["identification.trial_title", "identification.sponsor",
                           "identification.protocol_id", "identification.phase"],
                checklist_items=["1.1"],
            ),
            TemplateSection(
                id="synopsis",
                title="2. Synopsis",
                level=1,
                description="Concise summary of study design, results, and conclusions",
                checklist_items=["2.1"],
            ),
            TemplateSection(
                id="ethics",
                title="5. Ethics",
                level=1,
                description="IRB/IEC review, ethical conduct, informed consent",
                fact_paths=["ethics.irb_approval", "ethics.informed_consent"],
                checklist_items=["5.1", "5.2", "5.3"],
            ),
            TemplateSection(
                id="introduction",
                title="7. Introduction",
                level=1,
                description="Context and rationale for the study",
                checklist_items=["7.1"],
            ),
            TemplateSection(
                id="objectives",
                title="8. Study Objectives",
                level=1,
                description="Primary and secondary objectives",
                fact_paths=["outcomes.primary_outcome", "outcomes.secondary_outcomes"],
                checklist_items=["8.1"],
            ),
            TemplateSection(
                id="investigational_plan",
                title="9. Investigational Plan",
                level=1,
                description="Study design, population, treatments, and analysis plan",
                checklist_items=["9.1", "9.2", "9.3.1", "9.3.2", "9.3.3",
                                "9.4.1", "9.4.2", "9.4.3", "9.4.4", "9.4.5", "9.4.6",
                                "9.5.1", "9.5.2", "9.5.3", "9.6", "9.7.1", "9.7.2", "9.8"],
                subsections=[
                    TemplateSection(
                        id="study_design",
                        title="9.1 Overall Study Design",
                        level=2,
                        fact_paths=["design.design_type", "design.blinding", "design.randomization_method"],
                        checklist_items=["9.1"],
                    ),
                    TemplateSection(
                        id="selection_criteria",
                        title="9.3 Selection of Patients",
                        level=2,
                        fact_paths=["population.inclusion_criteria", "population.exclusion_criteria"],
                        checklist_items=["9.3.1", "9.3.2", "9.3.3"],
                    ),
                    TemplateSection(
                        id="treatments",
                        title="9.4 Treatments",
                        level=2,
                        fact_paths=["intervention.intervention_name", "intervention.intervention_dose"],
                        checklist_items=["9.4.1", "9.4.2", "9.4.3", "9.4.4", "9.4.5", "9.4.6"],
                    ),
                    TemplateSection(
                        id="efficacy_variables",
                        title="9.5 Efficacy and Safety Variables",
                        level=2,
                        fact_paths=["outcomes.primary_outcome_measure", "outcomes.safety_outcomes"],
                        checklist_items=["9.5.1", "9.5.2", "9.5.3"],
                    ),
                    TemplateSection(
                        id="statistical_plan",
                        title="9.7 Statistical Methods",
                        level=2,
                        fact_paths=["statistics.statistical_methods", "statistics.sample_size_calculation"],
                        checklist_items=["9.7.1", "9.7.2"],
                    ),
                ],
            ),
            TemplateSection(
                id="study_patients",
                title="10. Study Patients",
                level=1,
                description="Patient disposition and protocol deviations",
                fact_paths=["results.participants_randomized"],
                checklist_items=["10.1", "10.2"],
            ),
            TemplateSection(
                id="efficacy_evaluation",
                title="11. Efficacy Evaluation",
                level=1,
                description="Analysis populations, demographics, efficacy results",
                fact_paths=["results.primary_result", "results.effect_size"],
                checklist_items=["11.1", "11.2", "11.3", "11.4.1", "11.4.7"],
            ),
            TemplateSection(
                id="safety_evaluation",
                title="12. Safety Evaluation",
                level=1,
                description="Exposure, adverse events, deaths, laboratory findings",
                fact_paths=["safety.adverse_events_summary", "safety.serious_adverse_events", "safety.deaths"],
                checklist_items=["12.1", "12.2.1", "12.2.2", "12.2.3", "12.3.1", "12.3.2", "12.3.3", "12.6"],
            ),
            TemplateSection(
                id="discussion_conclusions",
                title="13. Discussion and Overall Conclusions",
                level=1,
                description="Summary and benefit-risk assessment",
                checklist_items=["13.1"],
            ),
        ]

    def get_sections(self) -> List[TemplateSection]:
        return self._sections

    def get_section(self, section_id: str) -> Optional[TemplateSection]:
        return self._section_map.get(section_id)
