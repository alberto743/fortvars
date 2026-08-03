# SPDX-FileCopyrightText: 2026 ENEA
# SPDX-FileContributor: Alberto P
#
# SPDX-License-Identifier: MPL-2.0

import shutil
from pathlib import Path

import pytest

GFORTRAN_AVAILABLE = shutil.which("gfortran") is not None
requires_gfortran = pytest.mark.skipif(
    not GFORTRAN_AVAILABLE, reason="gfortran not found on PATH"
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def modfiles_dir(tmp_path) -> Path:
    return tmp_path
