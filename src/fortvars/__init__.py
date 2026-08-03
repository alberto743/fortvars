# SPDX-FileCopyrightText: 2025-2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from .fortran_variables import (
    analyze,
    compare,
    Variable,
    Parameter,
    AnalysisResult,
    ComparisonResult,
)

__all__ = [
    "analyze",
    "compare",
    "Variable",
    "Parameter",
    "AnalysisResult",
    "ComparisonResult",
]

try:
    from importlib.metadata import version as _version
    __version__ = _version("fortvars")
except Exception:
    __version__ = "0.0.0+unknown"
