"""
Agents module - LLM agents for fact extraction, writing, and critique.

Three main agents:
- FactFinder: Extracts facts from Trial Manifest to populate TrialFacts
- Writer: Generates CONSORT/ICH E3 compliant reports from TrialFacts
- Critic: Validates reports and identifies gaps/issues
"""

from clinirepgen.agents.base import AgentConfig, BaseAgent
from clinirepgen.agents.critic import CriticAgent
from clinirepgen.agents.fact_finder import FactFinderAgent
from clinirepgen.agents.writer import WriterAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "FactFinderAgent",
    "WriterAgent",
    "CriticAgent",
]
