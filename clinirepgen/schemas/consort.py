"""
CONSORT 2025 Checklist - Structured representation of CONSORT items.

Each item is mapped to the Trial Facts schema and used to:
1. Guide fact extraction (each item becomes a question to answer)
2. Validate report completeness
3. Generate the CONSORT narrative structure
"""

from typing import Dict, List

from clinirepgen.schemas.trial_facts import ChecklistCategory, ChecklistItem

# CONSORT 2025 Checklist Items
CONSORT_CHECKLIST: List[ChecklistItem] = [
    # Title and Abstract
    ChecklistItem(
        item_id="1a",
        description="Identification as a randomized trial in the title",
        category=ChecklistCategory.TITLE_ABSTRACT,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="1b",
        description="Structured summary of trial design, methods, results, and conclusions",
        category=ChecklistCategory.TITLE_ABSTRACT,
        source="CONSORT",
        required=True
    ),

    # Open Science
    ChecklistItem(
        item_id="2",
        description="Name of trial registry and identifying number (with URL) and date of registration",
        category=ChecklistCategory.OPEN_SCIENCE,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="3",
        description="Where the trial protocol and statistical analysis plan can be accessed",
        category=ChecklistCategory.OPEN_SCIENCE,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="4",
        description="Where and how the individual de-identified participant data can be accessed",
        category=ChecklistCategory.OPEN_SCIENCE,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="5a",
        description="Sources of funding and role of funders in the trial",
        category=ChecklistCategory.OPEN_SCIENCE,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="5b",
        description="Financial and other conflicts of interest of the manuscript authors",
        category=ChecklistCategory.OPEN_SCIENCE,
        source="CONSORT",
        required=True
    ),

    # Introduction
    ChecklistItem(
        item_id="6",
        description="Scientific background and rationale",
        category=ChecklistCategory.INTRODUCTION,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="7",
        description="Specific objectives related to benefits and harms",
        category=ChecklistCategory.INTRODUCTION,
        source="CONSORT",
        required=True
    ),

    # Methods
    ChecklistItem(
        item_id="8",
        description="Details of patient or public involvement in the design, conduct and reporting",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="9",
        description="Description of trial design including type, allocation ratio, and framework",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="10",
        description="Important changes to trial after commencement with reasons",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="11",
        description="Settings and locations where trial was conducted",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="12a",
        description="Eligibility criteria for participants",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="12b",
        description="Eligibility criteria for sites and individuals delivering interventions",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="13",
        description="Intervention and comparator with sufficient details to allow replication",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="14",
        description="Prespecified primary and secondary outcomes with measurement details",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="15",
        description="How harms were defined and assessed",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="16a",
        description="How sample size was determined with assumptions",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="16b",
        description="Explanation of interim analyses and stopping guidelines",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="17a",
        description="Who generated the random allocation sequence and method used",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="17b",
        description="Type of randomization and restriction details",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="18",
        description="Mechanism for allocation concealment",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="19",
        description="Who enrolled and assigned participants to interventions",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="20a",
        description="Who was blinded after assignment to interventions",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="20b",
        description="How blinding was achieved and similarity of interventions",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="21a",
        description="Statistical methods for comparing groups",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="21b",
        description="Definition of analysis populations",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="21c",
        description="How missing data were handled",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="21d",
        description="Methods for additional analyses distinguishing prespecified from post hoc",
        category=ChecklistCategory.METHODS,
        source="CONSORT",
        required=False
    ),

    # Results
    ChecklistItem(
        item_id="22a",
        description="Numbers randomly assigned, received intervention, and analyzed per group",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="22b",
        description="Losses and exclusions after randomization with reasons",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="23a",
        description="Dates of recruitment and follow-up periods",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="23b",
        description="Why trial ended or was stopped",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="24a",
        description="Intervention and comparator as actually administered",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="24b",
        description="Concomitant care received during trial",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=False
    ),
    ChecklistItem(
        item_id="25",
        description="Table of baseline demographic and clinical characteristics",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="26",
        description="Results for each outcome with effect sizes and confidence intervals",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="27",
        description="All harms or unintended events in each group",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="28",
        description="Other analyses performed including subgroup analyses",
        category=ChecklistCategory.RESULTS,
        source="CONSORT",
        required=False
    ),

    # Discussion
    ChecklistItem(
        item_id="29",
        description="Interpretation consistent with results, balancing benefits and harms",
        category=ChecklistCategory.DISCUSSION,
        source="CONSORT",
        required=True
    ),
    ChecklistItem(
        item_id="30",
        description="Trial limitations addressing bias, imprecision, and generalizability",
        category=ChecklistCategory.DISCUSSION,
        source="CONSORT",
        required=True
    ),
]

# Mapping from CONSORT items to Trial Facts paths
CONSORT_TO_FACTS_MAP: Dict[str, List[str]] = {
    "1a": ["identification.trial_title"],
    "1b": ["identification.trial_title", "design.design_type", "results.primary_result"],
    "2": ["identification.nct_id", "identification.registration_date", "identification.registration_url"],
    "5a": ["identification.sponsor"],
    "6": [],  # Background - typically prose, not structured
    "7": ["outcomes.primary_outcome"],
    "9": ["design.design_type", "design.allocation_ratio", "design.framework"],
    "11": [],  # Settings - varies
    "12a": ["population.inclusion_criteria", "population.exclusion_criteria"],
    "13": ["intervention.intervention_name", "intervention.intervention_dose",
           "intervention.comparator_name"],
    "14": ["outcomes.primary_outcome", "outcomes.primary_outcome_measure",
           "outcomes.primary_outcome_timeframe", "outcomes.secondary_outcomes"],
    "15": ["outcomes.safety_outcomes"],
    "16a": ["statistics.sample_size_calculation"],
    "17a": ["design.randomization_method"],
    "17b": ["design.randomization_details", "design.stratification"],
    "20a": ["design.blinding"],
    "20b": ["design.blinding_details"],
    "21a": ["statistics.statistical_methods"],
    "21b": ["statistics.analysis_population"],
    "21c": ["statistics.missing_data_handling"],
    "22a": ["results.participants_randomized", "results.participants_analyzed"],
    "23a": ["dates.first_enrollment_date", "dates.last_enrollment_date"],
    "25": ["population.actual_enrollment", "population.age_range", "population.sex_distribution"],
    "26": ["results.primary_result", "results.effect_size",
           "results.confidence_interval", "results.p_value"],
    "27": ["safety.adverse_events_summary", "safety.serious_adverse_events"],
}


def get_consort_item(item_id: str) -> ChecklistItem | None:
    """Get a CONSORT checklist item by ID."""
    for item in CONSORT_CHECKLIST:
        if item.item_id == item_id:
            return item
    return None


def get_consort_items_by_category(category: ChecklistCategory) -> List[ChecklistItem]:
    """Get all CONSORT items for a given category."""
    return [item for item in CONSORT_CHECKLIST if item.category == category]


def get_facts_for_consort_item(item_id: str) -> List[str]:
    """Get the Trial Facts paths that map to a CONSORT item."""
    return CONSORT_TO_FACTS_MAP.get(item_id, [])
