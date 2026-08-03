C     SPDX-FileCopyrightText: 2026 ENEA
C     SPDX-FileContributor: Alberto P
C     SPDX-License-Identifier: MPL-2.0
C
C     Two independent subroutines in one file. Regression fixture for the
C     bug where the parser stopped at the first unit's `code:` marker and
C     silently dropped every subsequent unit (here, SUB_B and its implicit
C     local RTOT would never be seen).
      SUBROUTINE SUB_A(N, X)
      INTEGER N
      REAL X
      X = X + N
      END

      SUBROUTINE SUB_B(K)
      INTEGER K
      RTOT = RTOT + K
      END
