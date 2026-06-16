"""
CliniRepGen - Clinical Report Generator

A production-ready pipeline for generating CONSORT + ICH E3 compliant
clinical trial reports from structured and unstructured trial artifacts.
"""

__version__ = "0.1.0"
__author__ = "CliniRepGen Team"

from clinirepgen.manifest.models import TrialManifest
from clinirepgen.schemas.provenance import Provenance
from clinirepgen.schemas.trial_facts import TrialFacts

__all__ = [
    "TrialFacts",
    "Provenance",
    "TrialManifest",
    "__version__",
]
