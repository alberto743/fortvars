# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from fortvars.fortran_variables import analyze

from conftest import requires_gfortran

pytestmark = requires_gfortran


def test_every_unit_in_a_multi_unit_file_is_parsed(fixtures_dir, modfiles_dir):
    '''Regression test: the parser used to stop at the first `code:` marker
    in the gfortran dump, silently dropping every unit after the first.'''
    result = analyze(fixtures_dir / "f77" / "f77_multi_unit.f", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)

    by_unit = {}
    for variable in result.variables:
        by_unit.setdefault(variable.unit, set()).add(variable.name)

    assert by_unit.get("sub_a") == {"n", "x"}
    assert by_unit.get("sub_b") == {"k", "rtot"}

    rtot = next(v for v in result.variables if v.name == "rtot")
    assert rtot.implicit
    assert not rtot.dummy
