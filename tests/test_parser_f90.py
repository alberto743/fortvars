# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

from fortvars.fortran_variables import analyze

from conftest import requires_gfortran

pytestmark = requires_gfortran


def test_module_and_program_units_and_artificial_symbols_filtered(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f90" / "f90_module_and_program.f90", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)

    names = {v.name for v in result.variables} | {p.name for p in result.parameters}
    assert not any(name.startswith("__") for name in names)

    nmax_params = [p for p in result.parameters if p.name == "nmax"]
    assert {(p.unit, p.module) for p in nmax_params} == {("mymod", None), ("f90prog", "mymod")}

    z = next(v for v in result.variables if v.name == "z" and v.unit == "f90prog")
    assert z.implicit
    assert not z.dummy

    mod_sub_args = {v.name: v for v in result.variables if v.unit == "mod_sub"}
    assert mod_sub_args["a"].intent == "IN"
    assert mod_sub_args["b"].intent == "OUT"
    assert mod_sub_args["a"].dummy and mod_sub_args["b"].dummy


def test_renamed_use_association_reports_local_name(fixtures_dir, modfiles_dir):
    result = analyze(fixtures_dir / "f90" / "f90_rename_use.f90", modfiles_dir=modfiles_dir, output_dir=modfiles_dir)

    mv2 = next(v for v in result.variables if v.name == "mv2")
    assert mv2.unit == "renprog"
    assert mv2.module == "renmod"
    assert mv2.origin_name == "modvar"

    myval = next(p for p in result.parameters if p.name == "myval")
    assert myval.unit == "renprog"
    assert myval.module == "renmod"
    assert myval.origin_name == "secretval"

    local = next(v for v in result.variables if v.name == "local")
    assert local.unit == "renprog"
    assert not local.implicit
    assert local.origin_name is None
