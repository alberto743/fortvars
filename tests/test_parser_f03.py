# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from fortvars.fortran_variables import analyze

from conftest import requires_gfortran

pytestmark = requires_gfortran


def test_derived_type_kind_parameter_and_intent_dummies(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f03" / "f03_derived_kind_intent.f03", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)

    parameter_names = {p.name for p in result.parameters}
    assert parameter_names == {"dp", "tol"}

    scale_vec_vars = {v.name: v for v in result.variables if v.unit == "scale_vec"}
    assert set(scale_vec_vars) == {"v", "factor", "out"}
    assert scale_vec_vars["v"].intent == "IN"
    assert scale_vec_vars["factor"].intent == "IN"
    assert scale_vec_vars["out"].intent == "OUT"
    assert all(not v.implicit for v in scale_vec_vars.values())
