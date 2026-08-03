# SPDX-FileCopyrightText: 2025-2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

'''Extract variables and parameters from Fortran units via gfortran's symbol dump'''

import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Union


_FIXED_EXTENSIONS = {".f", ".for", ".ftn", ".F", ".FOR", ".FTN"}
_FREE_EXTENSIONS = {".f90", ".f95", ".f03", ".f08", ".F90", ".F95", ".F03", ".F08"}
_RECOGNIZED_EXTENSIONS = _FIXED_EXTENSIONS | _FREE_EXTENSIONS

_SYMTREE_RE = re.compile(r"symtree:\s*'([^']*)'.*?symbol:\s*'([^']*)'(.*)$")


@dataclass(frozen=True)
class Variable:
    '''A variable declaration found in a Fortran unit.'''
    name: str
    unit: str
    dummy: bool
    intent: Optional[str]
    module: Optional[str]
    origin_name: Optional[str]
    implicit: bool


@dataclass(frozen=True)
class Parameter:
    '''A PARAMETER declaration found in a Fortran unit.'''
    name: str
    unit: str
    module: Optional[str]
    origin_name: Optional[str]


@dataclass(frozen=True)
class ParseResult:
    variables: tuple
    parameters: tuple


@dataclass(frozen=True)
class CompileDump:
    '''Raw result of invoking gfortran, kept even on a nonzero return code
    since gfortran still emits a usable dump for units it processed before
    hitting a later error.'''
    stdout: str
    stderr: str
    returncode: int
    unrecognized_extension: bool

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_gfortran_dump(sourcefile, modfiles_dir=None, output_dir=None) -> CompileDump:
    '''Invoke gfortran -fdump-fortran-original and return whatever it produced,
    regardless of return code.'''
    sourcefile = Path(sourcefile)

    modfiles_opts = ["-J", str(modfiles_dir)] if modfiles_dir is not None else []
    outdir_opts = (
        ["-o", str(Path(output_dir) / (sourcefile.stem + ".o"))]
        if output_dir is not None else []
    )

    result = subprocess.run(
        ["gfortran", "-fdump-fortran-original", *modfiles_opts, *outdir_opts, "-c", str(sourcefile)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return CompileDump(
        stdout=result.stdout,
        stderr=result.stderr,
        returncode=result.returncode,
        unrecognized_extension=sourcefile.suffix not in _RECOGNIZED_EXTENSIONS,
    )


def _parse_attributes(line: str) -> list:
    inner = line.split("attributes:", 1)[1].strip()
    if inner.startswith("(") and inner.endswith(")"):
        inner = inner[1:-1]
    return inner.split()


def _is_artificial(name: str, attrs: list) -> bool:
    return name.startswith("__") or "ARTIFICIAL" in attrs


def _use_assoc_module(attrs: list) -> Optional[str]:
    for attr in attrs:
        if attr.startswith("USE-ASSOC"):
            match = re.search(r"\(([^)]*)\)", attr)
            return match.group(1) if match else None
    return None


def _dummy_intent(attrs: list) -> Optional[str]:
    for attr in attrs:
        if attr.startswith("DUMMY"):
            if "(" in attr:
                return attr[attr.index("(") + 1: attr.index(")")]
            return None
    return None


def parse_gfortran_dump(dump_text: str) -> ParseResult:
    '''Parse the full stdout of `gfortran -fdump-fortran-original`.

    gfortran dumps every program unit in the file as its own
    Namespace/`procedure name =`/symtree/`code:` block, one after another
    (including nested CONTAINS units). A unit's `code:` line ends only that
    unit's own declaration section, not the whole dump, so `current_unit` is
    simply reassigned on every `procedure name =` line rather than treated
    as a stack - no unit ever needs to be "closed" explicitly.
    '''
    variables = []
    parameters = []
    current_unit = None
    pending = None  # (local_name, origin_name_or_None), set while awaiting its `attributes:` line

    for line in dump_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("procedure name ="):
            current_unit = stripped.split("=", 1)[1].strip()
            pending = None
            continue

        if stripped == "code:":
            pending = None
            continue

        if stripped.startswith("symtree:"):
            match = _SYMTREE_RE.search(stripped)
            if not match:
                continue
            local, origin, trailing = match.groups()
            if "from namespace" in trailing:
                # back-reference to a symbol declared in an enclosing unit;
                # has no attributes: line of its own
                pending = None
            else:
                pending = (local, origin if origin.lower() != local.lower() else None)
            continue

        if pending is not None and stripped.startswith("attributes:"):
            name, origin_name = pending
            pending = None

            attrs = _parse_attributes(stripped)
            if not attrs or current_unit is None or _is_artificial(name, attrs):
                continue

            module = _use_assoc_module(attrs)
            kind = attrs[0]

            if kind == "PARAMETER":
                parameters.append(Parameter(name, current_unit, module, origin_name))
            elif kind == "VARIABLE":
                variables.append(Variable(
                    name=name,
                    unit=current_unit,
                    dummy=any(a.startswith("DUMMY") for a in attrs),
                    intent=_dummy_intent(attrs),
                    module=module,
                    origin_name=origin_name,
                    implicit="IMPLICIT-TYPE" in attrs,
                ))
            continue

    return ParseResult(tuple(variables), tuple(parameters))


@dataclass(frozen=True)
class AnalysisResult:
    '''Structured, notebook-friendly result of analyzing one Fortran source file.'''
    sourcefile: Path
    variables: tuple
    parameters: tuple
    ok: bool
    compiled: bool
    warnings: tuple

    def variables_df(self):
        import pandas as pd
        columns = ["Name", "Unit", "Dummy", "Intent", "Module", "OriginName", "Implicit"]
        rows = [
            {
                "Name": v.name, "Unit": v.unit, "Dummy": v.dummy, "Intent": v.intent,
                "Module": v.module, "OriginName": v.origin_name, "Implicit": v.implicit,
            }
            for v in self.variables
        ]
        return pd.DataFrame(rows, columns=columns)

    def parameters_df(self):
        import pandas as pd
        columns = ["Name", "Unit", "Module", "OriginName"]
        rows = [
            {"Name": p.name, "Unit": p.unit, "Module": p.module, "OriginName": p.origin_name}
            for p in self.parameters
        ]
        return pd.DataFrame(rows, columns=columns)

    def combined_df(self):
        import pandas as pd
        variables_df = self.variables_df()
        variables_df.insert(0, "Kind", "Variable")
        parameters_df = self.parameters_df()
        parameters_df.insert(0, "Kind", "Parameter")
        return pd.concat([variables_df, parameters_df], ignore_index=True, sort=False)

    def to_json(self) -> str:
        payload = {
            "sourcefile": str(self.sourcefile),
            "ok": self.ok,
            "warnings": list(self.warnings),
            "variables": [asdict(v) for v in self.variables],
            "parameters": [asdict(p) for p in self.parameters],
        }
        return json.dumps(payload, indent=2)


def analyze(sourcefile: Union[str, Path], modfiles_dir=None, output_dir=None) -> AnalysisResult:
    '''Compile `sourcefile` with gfortran and return its variables/parameters
    as structured data. This is the primary entry point for notebook/script use.'''
    sourcefile = Path(sourcefile)
    dump = run_gfortran_dump(sourcefile, modfiles_dir=modfiles_dir, output_dir=output_dir)

    warnings = []
    if dump.unrecognized_extension:
        warnings.append(
            f"'{sourcefile.suffix}' is not a Fortran extension gfortran recognizes; "
            "compilation may have silently produced no output"
        )

    if not dump.stdout:
        warnings.append(
            f"gfortran produced no output (exit code {dump.returncode}): {dump.stderr.strip()}"
        )
        return AnalysisResult(sourcefile, (), (), ok=False, compiled=False, warnings=tuple(warnings))

    if not dump.ok:
        warnings.append(f"gfortran exited with code {dump.returncode}; results may be incomplete")

    parsed = parse_gfortran_dump(dump.stdout)
    return AnalysisResult(
        sourcefile, parsed.variables, parsed.parameters,
        ok=dump.ok, compiled=True, warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class ComparisonResult:
    '''Structural diff of two analyzed Fortran files, matched by (unit, name).

    This is a simple structural diff, not a semantic one: renaming a
    procedure (or a variable) between the two files shows up as a full
    remove+add rather than a match.
    '''
    a: AnalysisResult
    b: AnalysisResult
    added_variables: tuple
    removed_variables: tuple
    added_parameters: tuple
    removed_parameters: tuple

    def to_dataframe(self):
        import pandas as pd
        rows = []
        for v in self.added_variables:
            rows.append({"Kind": "Variable", "Change": "added", "Name": v.name, "Unit": v.unit, "Implicit": v.implicit})
        for v in self.removed_variables:
            rows.append({"Kind": "Variable", "Change": "removed", "Name": v.name, "Unit": v.unit, "Implicit": v.implicit})
        for p in self.added_parameters:
            rows.append({"Kind": "Parameter", "Change": "added", "Name": p.name, "Unit": p.unit, "Implicit": None})
        for p in self.removed_parameters:
            rows.append({"Kind": "Parameter", "Change": "removed", "Name": p.name, "Unit": p.unit, "Implicit": None})
        return pd.DataFrame(rows, columns=["Kind", "Change", "Name", "Unit", "Implicit"])

    def summary(self) -> str:
        return (
            f"{len(self.added_variables)} variable(s) added, {len(self.removed_variables)} removed; "
            f"{len(self.added_parameters)} parameter(s) added, {len(self.removed_parameters)} removed"
        )


def compare(sourcefile_a, sourcefile_b, modfiles_dir=None, output_dir=None) -> ComparisonResult:
    '''Analyze two Fortran files and diff their variables/parameters, matched
    by (unit, name). Intended for before/after comparison of a rewrite, to
    spot new or dropped IMPLICIT-typed variables.'''
    a = analyze(sourcefile_a, modfiles_dir=modfiles_dir, output_dir=output_dir)
    b = analyze(sourcefile_b, modfiles_dir=modfiles_dir, output_dir=output_dir)

    a_vars = {(v.unit, v.name): v for v in a.variables}
    b_vars = {(v.unit, v.name): v for v in b.variables}
    a_params = {(p.unit, p.name): p for p in a.parameters}
    b_params = {(p.unit, p.name): p for p in b.parameters}

    return ComparisonResult(
        a=a, b=b,
        added_variables=tuple(v for k, v in b_vars.items() if k not in a_vars),
        removed_variables=tuple(v for k, v in a_vars.items() if k not in b_vars),
        added_parameters=tuple(p for k, p in b_params.items() if k not in a_params),
        removed_parameters=tuple(p for k, p in a_params.items() if k not in b_params),
    )


def _print_result(result: AnalysisResult, fmt: str) -> None:
    if fmt == "json":
        print(result.to_json())
    elif fmt == "combined-csv":
        print(">>> Variables & Parameters <<<")
        print(result.combined_df().to_string(index=False))
    else:
        print(">>> Variables <<<")
        print(result.variables_df().to_string(index=False))
        print(">>> Parameters <<<")
        print(result.parameters_df().to_string(index=False))


def _write_result(result: AnalysisResult, fmt: str) -> None:
    stem = result.sourcefile.stem
    if fmt == "json":
        Path(f"{stem}.fortvars.json").write_text(result.to_json())
    elif fmt == "combined-csv":
        result.combined_df().to_csv(f"{stem}.fortvars.csv", index=False)
    else:
        result.variables_df().to_csv(f"{stem}.variables.csv", index=False)
        result.parameters_df().to_csv(f"{stem}.parameters.csv", index=False)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract variables from a Fortran source file.")
    parser.add_argument("sourcefile", help="Path to the Fortran source file")
    parser.add_argument(
        "-o", "--output-dir",
        help="Directory to store the compiled object file",
        default=None
    )
    parser.add_argument(
        "-j", "--modfiles-dir",
        help="Directory to store the module files",
        default=None
    )
    parser.add_argument(
        "-w", "--write",
        help="Write the output to file(s)",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Print the extracted tables",
        action="store_true",
        default=False
    )
    parser.add_argument(
        "--format",
        help="Output shape for -v/-w: two CSVs, one combined CSV, or JSON",
        choices=["csv", "combined-csv", "json"],
        default="csv",
    )
    args = parser.parse_args()

    result = analyze(args.sourcefile, modfiles_dir=args.modfiles_dir, output_dir=args.output_dir)
    for warning in result.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if not result.compiled:
        sys.exit(1)

    if args.verbose:
        _print_result(result, args.format)
    if args.write:
        _write_result(result, args.format)
