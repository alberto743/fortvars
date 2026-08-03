# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from fortvars.fortran_variables import analyze, run_gfortran_dump

from conftest import requires_gfortran

pytestmark = requires_gfortran


def test_partial_dump_recovered_on_semantic_error(fixtures_dir, modfiles_dir):
    fixture = fixtures_dir / "f90" / "f90_partial_type_error.f90"

    dump = run_gfortran_dump(fixture, modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    assert dump.returncode != 0
    assert dump.stdout

    result = analyze(fixture, modfiles_dir=modfiles_dir, output_dir=modfiles_dir)
    assert result.compiled
    assert not result.ok
    assert any("may be incomplete" in warning for warning in result.warnings)
    assert "nmax" in {p.name for p in result.parameters}


def test_unrecognized_extension_is_flagged_not_reported_as_zero_variables(fixtures_dir, tmp_path):
    source = fixtures_dir / "f77" / "f77_implicit_none.f"
    copy = tmp_path / "f77_implicit_none.f77"
    copy.write_text(source.read_text())

    result = analyze(copy, modfiles_dir=tmp_path)

    assert not result.compiled
    assert any("not a Fortran extension" in warning for warning in result.warnings)


def test_total_compile_failure_returns_no_data(tmp_path):
    result = analyze(tmp_path / "does_not_exist.f90", modfiles_dir=tmp_path)
    assert not result.compiled
    assert not result.ok
    assert not result.variables
    assert not result.parameters
