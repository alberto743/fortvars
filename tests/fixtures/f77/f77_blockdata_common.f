C     SPDX-FileCopyrightText: 2026 ENEA
C     SPDX-FileContributor: Alberto P
C     SPDX-License-Identifier: MPL-2.0
C
C     BLOCK DATA unit initializing an implicitly-typed COMMON block.
      BLOCK DATA INITBD
      COMMON /BLK2/ IX, IY, RZ
      DATA IX, IY, RZ /1, 2, 3.5/
      END
