C     SPDX-FileCopyrightText: 2026 ENEA
C     SPDX-FileContributor: Alberto P
C     SPDX-License-Identifier: MPL-2.0
C
C     No IMPLICIT NONE: I, IA, IB, Y are implicitly typed.
      SUBROUTINE F77NOIM(N, X)
      INTEGER N
      REAL X
      COMMON /BLK1/ IA, IB
      DO 10 I = 1, N
         X = X + I
   10 CONTINUE
      Y = X * 2.0
      END
