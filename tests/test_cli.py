# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

import json
import sys

from fortvars.fortran_variables import main

from conftest import requires_gfortran

pytestmark = requires_gfortran


def _run_cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["fortran_variables", *args])
    try:
        main()
    except SystemExit as exc:
        return exc.code or 0
    return 0


def test_verbose_always_shows_both_sections_even_when_empty(fixtures_dir, monkeypatch, capsys, tmp_path):
    fixture = fixtures_dir / "f77" / "f77_blockdata_common.f"
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(fixture), "-v", "-j", str(tmp_path)])
    out = capsys.readouterr().out

    assert code == 0
    assert ">>> Variables <<<" in out
    assert ">>> Parameters <<<" in out
    assert "Empty DataFrame" in out


def test_write_always_creates_both_csvs_even_when_empty(fixtures_dir, monkeypatch, tmp_path):
    fixture = fixtures_dir / "f77" / "f77_blockdata_common.f"
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(fixture), "-w", "-j", str(tmp_path)])

    assert code == 0
    variables_csv = tmp_path / "f77_blockdata_common.variables.csv"
    parameters_csv = tmp_path / "f77_blockdata_common.parameters.csv"
    assert variables_csv.exists()
    assert parameters_csv.exists()
    assert parameters_csv.read_text().strip() == "Name,Unit,Module,OriginName"


def test_format_combined_csv_writes_single_file(fixtures_dir, monkeypatch, tmp_path):
    fixture = fixtures_dir / "f90" / "f90_rename_use.f90"
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(fixture), "-w", "--format", "combined-csv", "-j", str(tmp_path)])

    assert code == 0
    combined = tmp_path / "f90_rename_use.fortvars.csv"
    assert combined.exists()
    assert combined.read_text().splitlines()[0].split(",")[0] == "Kind"


def test_format_json_prints_valid_json(fixtures_dir, monkeypatch, capsys, tmp_path):
    fixture = fixtures_dir / "f03" / "f03_derived_kind_intent.f03"
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(fixture), "-v", "--format", "json", "-j", str(tmp_path)])
    out = capsys.readouterr().out

    assert code == 0
    payload = json.loads(out)
    assert {p["name"] for p in payload["parameters"]} == {"dp", "tol"}


def test_partial_dump_exits_zero_with_stderr_warning(fixtures_dir, monkeypatch, capsys, tmp_path):
    fixture = fixtures_dir / "f90" / "f90_partial_type_error.f90"
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(fixture), "-v", "-j", str(tmp_path)])
    err = capsys.readouterr().err

    assert code == 0
    assert "may be incomplete" in err


def test_total_compile_failure_exits_nonzero(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    code = _run_cli(monkeypatch, [str(tmp_path / "does_not_exist.f90")])

    assert code == 1
