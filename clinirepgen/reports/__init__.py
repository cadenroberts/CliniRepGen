"""
Reports module - Templates and renderers for clinical trial reports.

Provides:
- CONSORT narrative templates
- ICH E3 CSR structure templates
- Markdown and HTML renderers
"""

from clinirepgen.reports.renderer import (
    MarkdownRenderer,
    render_consort,
    render_ich_e3,
)
from clinirepgen.reports.templates import (
    BaseTemplate,
    CONSORTTemplate,
    ICHE3Template,
)

__all__ = [
    "CONSORTTemplate",
    "ICHE3Template",
    "BaseTemplate",
    "MarkdownRenderer",
    "render_consort",
    "render_ich_e3",
]
