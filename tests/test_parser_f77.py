# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from fortvars.fortran_variables import analyze

from conftest import requires_gfortran

pytestmark = requires_gfortran


def _by_name(items):
    return {item.name: item for item in items}


def test_implicit_variables_without_implicit_none(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f77" / "f77_implicit_common.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    variables = _by_name(result.variables)

    assert variables["n"].dummy and not variables["n"].implicit
    assert variables["x"].dummy and not variables["x"].implicit
    assert not variables["i"].dummy and variables["i"].implicit
    assert not variables["y"].dummy and variables["y"].implicit
    assert variables["ia"].implicit
    assert variables["ib"].implicit
    assert not result.parameters


def test_implicit_none_with_parameter(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f77" / "f77_implicit_none.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    variables = _by_name(result.variables)
    parameters = _by_name(result.parameters)

    for name in ("n", "x", "res"):
        assert variables[name].dummy
        assert not variables[name].implicit
        assert variables[name].intent is None  # F77 has no INTENT keyword

    assert not variables["i"].dummy and not variables["i"].implicit
    assert "pi" in parameters
    assert "pi" not in variables


def test_custom_implicit_statement(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f77" / "f77_custom_implicit.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    variables = _by_name(result.variables)

    assert not variables["n"].implicit
    assert variables["dval"].implicit


def test_blockdata_common_members_are_implicit(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f77" / "f77_blockdata_common.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    variables = _by_name(result.variables)

    assert set(variables) == {"ix", "iy", "rz"}
    for var in variables.values():
        assert var.unit == "initbd"
        assert var.implicit
        assert not var.dummy
