C     SPDX-FileCopyrightText: 2026 ENEA
C     SPDX-FileContributor: Alberto P
C     SPDX-License-Identifier: MPL-2.0
C
C     IMPLICIT NONE + a PARAMETER + all-explicit dummies/locals.
      SUBROUTINE F77IMP(N, X, RES)
      IMPLICIT NONE
      INTEGER N
      REAL X
      REAL RES
      INTEGER I
      REAL, PARAMETER :: PI = 3.14159
      RES = 0.0
      DO 20 I = 1, N
         RES = RES + X * PI
   20 CONTINUE
      END
