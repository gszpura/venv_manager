"""Project requirements parsing."""

from vvm.requirements.parsers import (
    ProjectRequirements,
    ProjectRequirementsReader,
    PyprojectParser,
    RequirementsParser,
    RequirementsTxtParser,
    default_reader,
    parse_requirement,
)

__all__ = [
    "ProjectRequirements",
    "ProjectRequirementsReader",
    "PyprojectParser",
    "RequirementsParser",
    "RequirementsTxtParser",
    "default_reader",
    "parse_requirement",
]
