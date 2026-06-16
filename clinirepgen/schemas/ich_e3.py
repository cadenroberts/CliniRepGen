"""
ICH E3 Checklist - Structured representation of ICH E3 CSR sections.

ICH E3 provides the structure for Clinical Study Reports (CSRs).
Each item maps to sections required in regulatory submissions.
"""

from typing import Dict, List

from clinirepgen.schemas.trial_facts import ChecklistCategory, ChecklistItem

# ICH E3 Checklist Items (CSR Structure)
ICH_E3_CHECKLIST: List[ChecklistItem] = [
    # Title Page
    ChecklistItem(
        item_id="1.1",
        description="Study title, investigational product, indication, design, sponsor, protocol ID, phase, key dates, investigators, compliance, and report date",
        category=ChecklistCategory.TITLE_ABSTRACT,
        source="ICH_E3",
        required=True
    ),

    # Synopsis
    ChecklistItem(
        item_id="2.1",
        description="Concise summary of study design, methodology, patient population, treatment, efficacy, safety, and key results",
        category=ChecklistCategory.TITLE_ABSTRACT,
        source="ICH_E3",
        required=True
    ),

    # Ethics
    ChecklistItem(
        item_id="5.1",
        description="Independent Ethics Committee or IRB confirmation of review",
        category=ChecklistCategory.ETHICS,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="5.2",
        description="Ethical Conduct - statement confirming adherence to Declaration of Helsinki",
        category=ChecklistCategory.ETHICS,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="5.3",
        description="Patient Information and Consent description",
        category=ChecklistCategory.ETHICS,
        source="ICH_E3",
        required=True
    ),

    # Investigators
    ChecklistItem(
        item_id="6.1",
        description="Administrative structure, investigators, committees, CROs, monitoring, and statistician roles",
        category=ChecklistCategory.INVESTIGATORS,
        source="ICH_E3",
        required=True
    ),

    # Introduction
    ChecklistItem(
        item_id="7.1",
        description="Context for the study in development of investigational product, rationale, aims, and regulatory background",
        category=ChecklistCategory.INTRODUCTION,
        source="ICH_E3",
        required=True
    ),

    # Objectives
    ChecklistItem(
        item_id="8.1",
        description="Overall purpose(s) of the study, including primary and secondary objectives",
        category=ChecklistCategory.OBJECTIVES,
        source="ICH_E3",
        required=True
    ),

    # Investigational Plan
    ChecklistItem(
        item_id="9.1",
        description="Overall Study Design and Plan - treatments, controls, blinding, assignment, duration, flow diagram",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.2",
        description="Discussion of Study Design - justification of design choices, controls, potential biases",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.3.1",
        description="Inclusion criteria and patient suitability",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.3.2",
        description="Exclusion criteria and rationale",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.3.3",
        description="Removal of patients from therapy or assessment",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.1",
        description="Treatments administered - route, dose, schedule, comparator details",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.2",
        description="Identity of investigational product(s) - formulation, batch numbers, sources",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.3",
        description="Method of assigning patients to treatment groups",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.4",
        description="Selection of doses in the study and justification",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.5",
        description="Selection and timing of dose for each patient",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.6",
        description="Blinding procedures and maintenance",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.4.7",
        description="Prior and concomitant therapy rules",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=False
    ),
    ChecklistItem(
        item_id="9.4.8",
        description="Treatment compliance monitoring",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.5.1",
        description="Efficacy and safety variables assessed and schedule of assessments",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.5.2",
        description="Appropriateness of measurements and validation",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.5.3",
        description="Primary efficacy variable(s)",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.5.4",
        description="Drug concentration measurements and pharmacokinetic assessments",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=False
    ),
    ChecklistItem(
        item_id="9.6",
        description="Data quality assurance - monitoring, audits, inter-laboratory standardization",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.7.1",
        description="Statistical and analytical plans - planned analyses, covariates, interim analyses",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.7.2",
        description="Determination of sample size - basis, methods, assumptions, calculations",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="9.8",
        description="Changes in conduct of study or planned analyses",
        category=ChecklistCategory.INVESTIGATIONAL_PLAN,
        source="ICH_E3",
        required=True
    ),

    # Study Patients
    ChecklistItem(
        item_id="10.1",
        description="Disposition of patients - enrollment, randomization, completion, discontinuation, reasons",
        category=ChecklistCategory.STUDY_PATIENTS,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="10.2",
        description="Protocol deviations - summary by category and center",
        category=ChecklistCategory.STUDY_PATIENTS,
        source="ICH_E3",
        required=True
    ),

    # Efficacy Evaluation
    ChecklistItem(
        item_id="11.1",
        description="Data sets analysed and inclusion/exclusion rules",
        category=ChecklistCategory.EFFICACY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="11.2",
        description="Demographic and baseline characteristics; comparability and tables",
        category=ChecklistCategory.EFFICACY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="11.3",
        description="Measurements of treatment compliance",
        category=ChecklistCategory.EFFICACY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="11.4.1",
        description="Analysis of efficacy - endpoints, comparisons, confidence intervals",
        category=ChecklistCategory.EFFICACY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="11.4.7",
        description="Efficacy conclusions",
        category=ChecklistCategory.EFFICACY,
        source="ICH_E3",
        required=True
    ),

    # Safety Evaluation
    ChecklistItem(
        item_id="12.1",
        description="Extent of exposure - duration, dose, subgroup breakdown",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.2.1",
        description="Brief summary of adverse events",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.2.2",
        description="Display of adverse events by system organ class, severity, causality",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.2.3",
        description="Analysis of adverse events - dose, demographics, time dependence",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.3.1",
        description="Listing of deaths, serious and significant adverse events",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.3.2",
        description="Narratives of deaths, serious and significant adverse events",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.3.3",
        description="Analysis and discussion of deaths, serious and significant adverse events",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),
    ChecklistItem(
        item_id="12.6",
        description="Safety conclusions - overall evaluation, at-risk subgroups, implications",
        category=ChecklistCategory.SAFETY,
        source="ICH_E3",
        required=True
    ),

    # Discussion and Conclusions
    ChecklistItem(
        item_id="13.1",
        description="Summary of efficacy and safety results, benefit-risk assessment, clinical implications",
        category=ChecklistCategory.CONCLUSIONS,
        source="ICH_E3",
        required=True
    ),
]

# Mapping from ICH E3 items to Trial Facts paths
ICH_E3_TO_FACTS_MAP: Dict[str, List[str]] = {
    "1.1": ["identification.trial_title", "identification.sponsor", "identification.protocol_id",
            "identification.phase", "dates.start_date", "dates.completion_date"],
    "2.1": ["design.design_type", "population.actual_enrollment", "intervention.intervention_name",
            "results.primary_result", "safety.adverse_events_summary"],
    "5.1": ["ethics.irb_approval"],
    "5.2": ["ethics.declaration_of_helsinki"],
    "5.3": ["ethics.informed_consent"],
    "7.1": [],  # Background prose
    "8.1": ["outcomes.primary_outcome", "outcomes.secondary_outcomes"],
    "9.1": ["design.design_type", "design.blinding", "design.randomization_method"],
    "9.3.1": ["population.inclusion_criteria"],
    "9.3.2": ["population.exclusion_criteria"],
    "9.4.1": ["intervention.intervention_dose", "intervention.intervention_route",
              "intervention.intervention_schedule"],
    "9.4.3": ["design.randomization_method", "design.randomization_details"],
    "9.4.6": ["design.blinding", "design.blinding_details"],
    "9.5.1": ["outcomes.primary_outcome_measure", "outcomes.safety_outcomes"],
    "9.5.3": ["outcomes.primary_outcome"],
    "9.7.1": ["statistics.statistical_methods", "statistics.interim_analyses"],
    "9.7.2": ["statistics.sample_size_calculation"],
    "10.1": ["results.participants_randomized", "results.participants_analyzed"],
    "11.2": ["population.age_range", "population.sex_distribution"],
    "11.4.1": ["results.primary_result", "results.effect_size", "results.confidence_interval"],
    "12.1": [],  # Exposure details - varies
    "12.2.1": ["safety.adverse_events_summary"],
    "12.3.1": ["safety.serious_adverse_events", "safety.deaths"],
    "12.6": [],  # Safety conclusions - prose
    "13.1": [],  # Discussion - prose
}


def get_ich_e3_item(item_id: str) -> ChecklistItem | None:
    """Get an ICH E3 checklist item by ID."""
    for item in ICH_E3_CHECKLIST:
        if item.item_id == item_id:
            return item
    return None


def get_ich_e3_items_by_category(category: ChecklistCategory) -> List[ChecklistItem]:
    """Get all ICH E3 items for a given category."""
    return [item for item in ICH_E3_CHECKLIST if item.category == category]


def get_facts_for_ich_e3_item(item_id: str) -> List[str]:
    """Get the Trial Facts paths that map to an ICH E3 item."""
    return ICH_E3_TO_FACTS_MAP.get(item_id, [])
