C     SPDX-FileCopyrightText: 2026 ENEA
C     SPDX-FileContributor: Alberto P
C     SPDX-License-Identifier: MPL-2.0
C
C     Custom IMPLICIT rule: DVAL (starts with D) is implicitly DOUBLE PRECISION.
      SUBROUTINE CUSTIMP(N)
      IMPLICIT DOUBLE PRECISION (D)
      INTEGER N
      DVAL = N * 2.0D0
      END
