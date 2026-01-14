"""
TrialFacts Schema - Provenance-aware truth schema for clinical trial facts.

Aligned to CONSORT 2025 + ICH E3 checklist items. Each fact stores:
- value: the extracted value (or None if not found)
- provenance: where it came from (file, section, table, offsets)
- confidence: extraction confidence score
- notes: any conflicts or issues
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import date
from clinirepgen.schemas.provenance import Provenance, ProvenanceList


class ConfidenceLevel(str, Enum):
    """Confidence level for extracted facts."""
    HIGH = "high"           # Direct extraction with clear match
    MEDIUM = "medium"       # Inferred or partial match
    LOW = "low"             # Uncertain extraction
    UNVERIFIED = "unverified"  # Not yet verified


class FactValue(BaseModel):
    """
    A single fact value with provenance and confidence tracking.
    
    This is the core unit of the Trial Facts schema - every piece of
    information must be wrapped in a FactValue with provenance.
    """
    
    value: Optional[Any] = Field(
        default=None,
        description="The extracted value (None if not found)"
    )
    provenance: ProvenanceList = Field(
        default_factory=ProvenanceList,
        description="Source provenance for this value"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.UNVERIFIED,
        description="Confidence level of extraction"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes about conflicts, ambiguity, or issues"
    )
    checklist_item_id: Optional[str] = Field(
        default=None,
        description="ID of the checklist item this fact addresses"
    )
    
    @property
    def is_null(self) -> bool:
        """Check if value is null/missing."""
        return self.value is None
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if confidence is low or unverified."""
        return self.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.UNVERIFIED]
    
    def add_provenance(self, provenance: Provenance) -> None:
        """Add a provenance record to this fact."""
        self.provenance.add(provenance)


class ChecklistCategory(str, Enum):
    """Categories for CONSORT/ICH E3 checklist items."""
    TITLE_ABSTRACT = "title_abstract"
    OPEN_SCIENCE = "open_science"
    INTRODUCTION = "introduction"
    METHODS = "methods"
    RESULTS = "results"
    DISCUSSION = "discussion"
    ETHICS = "ethics"
    INVESTIGATORS = "investigators"
    OBJECTIVES = "objectives"
    INVESTIGATIONAL_PLAN = "investigational_plan"
    STUDY_PATIENTS = "study_patients"
    EFFICACY = "efficacy"
    SAFETY = "safety"
    CONCLUSIONS = "conclusions"
    APPENDICES = "appendices"


class ChecklistItem(BaseModel):
    """A single checklist item from CONSORT or ICH E3."""
    
    model_config = {"use_enum_values": True}
    
    item_id: str = Field(
        ...,
        description="Unique identifier (e.g., '1a', '12.3.2')"
    )
    description: str = Field(
        ...,
        description="Full description of what's required"
    )
    category: ChecklistCategory = Field(
        ...,
        description="Category this item belongs to"
    )
    source: str = Field(
        ...,
        description="Source guideline ('CONSORT' or 'ICH_E3')"
    )
    required: bool = Field(
        default=True,
        description="Whether this item is required"
    )


# ============================================================================
# Trial Facts Schema - Main Model
# ============================================================================

class TrialIdentification(BaseModel):
    """Basic trial identification information."""
    nct_id: FactValue = Field(default_factory=FactValue)
    trial_title: FactValue = Field(default_factory=FactValue)
    official_title: FactValue = Field(default_factory=FactValue)
    sponsor: FactValue = Field(default_factory=FactValue)
    protocol_id: FactValue = Field(default_factory=FactValue)
    phase: FactValue = Field(default_factory=FactValue)
    registration_date: FactValue = Field(default_factory=FactValue)
    registration_url: FactValue = Field(default_factory=FactValue)


class TrialDesign(BaseModel):
    """Trial design and methodology facts."""
    design_type: FactValue = Field(default_factory=FactValue)  # parallel, crossover, etc.
    allocation_ratio: FactValue = Field(default_factory=FactValue)
    framework: FactValue = Field(default_factory=FactValue)  # superiority, non-inferiority
    blinding: FactValue = Field(default_factory=FactValue)
    blinding_details: FactValue = Field(default_factory=FactValue)
    randomization_method: FactValue = Field(default_factory=FactValue)
    randomization_details: FactValue = Field(default_factory=FactValue)
    stratification: FactValue = Field(default_factory=FactValue)


class TrialPopulation(BaseModel):
    """Population and eligibility facts."""
    target_enrollment: FactValue = Field(default_factory=FactValue)
    actual_enrollment: FactValue = Field(default_factory=FactValue)
    inclusion_criteria: FactValue = Field(default_factory=FactValue)
    exclusion_criteria: FactValue = Field(default_factory=FactValue)
    age_range: FactValue = Field(default_factory=FactValue)
    sex_distribution: FactValue = Field(default_factory=FactValue)


class TrialIntervention(BaseModel):
    """Intervention and comparator facts."""
    intervention_name: FactValue = Field(default_factory=FactValue)
    intervention_type: FactValue = Field(default_factory=FactValue)
    intervention_dose: FactValue = Field(default_factory=FactValue)
    intervention_route: FactValue = Field(default_factory=FactValue)
    intervention_schedule: FactValue = Field(default_factory=FactValue)
    comparator_name: FactValue = Field(default_factory=FactValue)
    comparator_type: FactValue = Field(default_factory=FactValue)
    comparator_details: FactValue = Field(default_factory=FactValue)


class TrialOutcomes(BaseModel):
    """Primary and secondary outcomes facts."""
    primary_outcome: FactValue = Field(default_factory=FactValue)
    primary_outcome_measure: FactValue = Field(default_factory=FactValue)
    primary_outcome_timeframe: FactValue = Field(default_factory=FactValue)
    secondary_outcomes: FactValue = Field(default_factory=FactValue)
    safety_outcomes: FactValue = Field(default_factory=FactValue)


class TrialResults(BaseModel):
    """Results and efficacy facts."""
    participants_randomized: FactValue = Field(default_factory=FactValue)
    participants_analyzed: FactValue = Field(default_factory=FactValue)
    primary_result: FactValue = Field(default_factory=FactValue)
    effect_size: FactValue = Field(default_factory=FactValue)
    confidence_interval: FactValue = Field(default_factory=FactValue)
    p_value: FactValue = Field(default_factory=FactValue)
    secondary_results: FactValue = Field(default_factory=FactValue)


class TrialSafety(BaseModel):
    """Safety and adverse events facts."""
    adverse_events_summary: FactValue = Field(default_factory=FactValue)
    serious_adverse_events: FactValue = Field(default_factory=FactValue)
    deaths: FactValue = Field(default_factory=FactValue)
    discontinuations_due_to_ae: FactValue = Field(default_factory=FactValue)
    common_adverse_events: FactValue = Field(default_factory=FactValue)


class TrialDates(BaseModel):
    """Key trial dates."""
    start_date: FactValue = Field(default_factory=FactValue)
    completion_date: FactValue = Field(default_factory=FactValue)
    primary_completion_date: FactValue = Field(default_factory=FactValue)
    first_enrollment_date: FactValue = Field(default_factory=FactValue)
    last_enrollment_date: FactValue = Field(default_factory=FactValue)


class TrialStatistics(BaseModel):
    """Statistical methodology facts."""
    sample_size_calculation: FactValue = Field(default_factory=FactValue)
    statistical_methods: FactValue = Field(default_factory=FactValue)
    analysis_population: FactValue = Field(default_factory=FactValue)
    missing_data_handling: FactValue = Field(default_factory=FactValue)
    interim_analyses: FactValue = Field(default_factory=FactValue)


class TrialEthics(BaseModel):
    """Ethics and compliance facts."""
    irb_approval: FactValue = Field(default_factory=FactValue)
    informed_consent: FactValue = Field(default_factory=FactValue)
    data_monitoring_committee: FactValue = Field(default_factory=FactValue)
    declaration_of_helsinki: FactValue = Field(default_factory=FactValue)


class TrialFacts(BaseModel):
    """
    Complete Trial Facts schema with provenance tracking.
    
    This is the central truth store for all extracted trial information.
    Every field is a FactValue with provenance tracking.
    """
    
    # Metadata
    trial_id: str = Field(
        ...,
        description="Unique identifier for this trial facts record"
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp when facts were extracted"
    )
    last_updated: str = Field(
        ...,
        description="ISO timestamp of last update"
    )
    extraction_version: str = Field(
        default="1.0",
        description="Version of extraction pipeline"
    )
    
    # Fact categories
    identification: TrialIdentification = Field(default_factory=TrialIdentification)
    design: TrialDesign = Field(default_factory=TrialDesign)
    population: TrialPopulation = Field(default_factory=TrialPopulation)
    intervention: TrialIntervention = Field(default_factory=TrialIntervention)
    outcomes: TrialOutcomes = Field(default_factory=TrialOutcomes)
    results: TrialResults = Field(default_factory=TrialResults)
    safety: TrialSafety = Field(default_factory=TrialSafety)
    dates: TrialDates = Field(default_factory=TrialDates)
    statistics: TrialStatistics = Field(default_factory=TrialStatistics)
    ethics: TrialEthics = Field(default_factory=TrialEthics)
    
    # Additional facts as key-value pairs for flexibility
    additional_facts: Dict[str, FactValue] = Field(
        default_factory=dict,
        description="Additional facts not covered by structured fields"
    )
    
    # Checklist coverage tracking
    checklist_coverage: Dict[str, bool] = Field(
        default_factory=dict,
        description="Mapping of checklist item IDs to coverage status"
    )
    
    def get_all_fact_values(self) -> List[tuple[str, FactValue]]:
        """Get all FactValue fields with their paths."""
        results = []
        
        for category_name in ['identification', 'design', 'population', 
                              'intervention', 'outcomes', 'results',
                              'safety', 'dates', 'statistics', 'ethics']:
            category = getattr(self, category_name)
            for field_name, field_value in category:
                if isinstance(field_value, FactValue):
                    results.append((f"{category_name}.{field_name}", field_value))
        
        for key, value in self.additional_facts.items():
            results.append((f"additional.{key}", value))
            
        return results
    
    def get_null_facts(self) -> List[str]:
        """Get list of fact paths that are null/missing."""
        return [path for path, fv in self.get_all_fact_values() if fv.is_null]
    
    def get_low_confidence_facts(self) -> List[str]:
        """Get list of fact paths with low confidence."""
        return [path for path, fv in self.get_all_fact_values() if fv.is_low_confidence]
    
    def get_fact_by_path(self, path: str) -> Optional[FactValue]:
        """Get a fact value by its dot-notation path."""
        parts = path.split(".")
        if len(parts) == 2:
            category_name, field_name = parts
            if category_name == "additional":
                return self.additional_facts.get(field_name)
            category = getattr(self, category_name, None)
            if category:
                return getattr(category, field_name, None)
        return None
    
    def set_fact(self, path: str, value: Any, provenance: Provenance, 
                 confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> None:
        """Set a fact value with provenance."""
        fact_value = self.get_fact_by_path(path)
        if fact_value:
            fact_value.value = value
            fact_value.add_provenance(provenance)
            fact_value.confidence = confidence
