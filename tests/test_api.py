# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

import json
from pathlib import Path

from fortvars.fortran_variables import (
    AnalysisResult,
    ComparisonResult,
    Parameter,
    Variable,
    analyze,
    compare,
)

from conftest import requires_gfortran


def test_variables_df_and_combined_df_shape():
    variables = (
        Variable(name="x", unit="sub", dummy=True, intent="IN", module=None, origin_name=None, implicit=False),
        Variable(name="y", unit="sub", dummy=False, intent=None, module=None, origin_name=None, implicit=True),
    )
    parameters = (Parameter(name="pi", unit="sub", module=None, origin_name=None),)
    result = AnalysisResult(Path("dummy.f"), variables, parameters, ok=True, compiled=True, warnings=())

    variables_df = result.variables_df()
    assert list(variables_df.columns) == ["Name", "Unit", "Dummy", "Intent", "Module", "OriginName", "Implicit"]
    assert len(variables_df) == 2

    parameters_df = result.parameters_df()
    assert list(parameters_df.columns) == ["Name", "Unit", "Module", "OriginName"]
    assert len(parameters_df) == 1

    combined_df = result.combined_df()
    assert set(combined_df["Kind"]) == {"Variable", "Parameter"}
    assert len(combined_df) == 3


def test_to_json_round_trips():
    variables = (
        Variable(name="x", unit="sub", dummy=True, intent="IN", module=None, origin_name=None, implicit=False),
    )
    result = AnalysisResult(Path("dummy.f"), variables, (), ok=True, compiled=True, warnings=("a warning",))

    payload = json.loads(result.to_json())
    assert payload["variables"][0]["name"] == "x"
    assert payload["warnings"] == ["a warning"]


def test_comparison_summary_and_dataframe():
    a_vars = (Variable("x", "sub", True, "IN", None, None, False),)
    b_vars = (
        Variable("x", "sub", True, "IN", None, None, False),
        Variable("z", "sub", False, None, None, None, True),
    )
    a = AnalysisResult(Path("a.f"), a_vars, (), ok=True, compiled=True, warnings=())
    b = AnalysisResult(Path("b.f"), b_vars, (), ok=True, compiled=True, warnings=())
    result = ComparisonResult(
        a=a, b=b,
        added_variables=(b_vars[1],), removed_variables=(),
        added_parameters=(), removed_parameters=(),
    )

    assert "1 variable(s) added" in result.summary()
    dataframe = result.to_dataframe()
    assert len(dataframe) == 1
    assert dataframe.iloc[0]["Name"] == "z"


@requires_gfortran
def test_analyze_public_entry_point(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f77" / "f77_implicit_none.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    assert result.compiled and result.ok
    assert {v.name for v in result.variables} == {"i", "n", "res", "x"}
    assert {p.name for p in result.parameters} == {"pi"}


@requires_gfortran
def test_compare_between_completely_different_files(fixtures_dir, modfiles_dir):
    a_path = fixtures_dir / "f90" / "f90_module_and_program.f90"
    b_path = fixtures_dir / "f90" / "f90_rename_use.f90"

    a_result = analyze(a_path, modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    b_result = analyze(b_path, modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    result = compare(a_path, b_path, modfiles_dir=modfiles_dir, output_dir=modfiles_dir)

    assert isinstance(result.summary(), str)
    assert len(result.removed_variables) == len(a_result.variables)
    assert len(result.added_variables) == len(b_result.variables)
