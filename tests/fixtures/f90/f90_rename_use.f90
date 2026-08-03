! SPDX-FileCopyrightText: 2026 ENEA
! SPDX-FileContributor: Alberto P
! SPDX-License-Identifier: MPL-2.0
!
! USE ... ONLY: local => original renaming, for both a variable and a
! parameter. Regression fixture for reporting the local (source-visible)
! name rather than the module's origin name.
module renmod
  implicit none
  integer, parameter :: SECRETVAL = 42
  real :: modvar = 1.0
end module renmod

program renprog
  use renmod, only: myval => SECRETVAL
  use renmod, only: mv2 => modvar
  implicit none
  integer :: local
  local = myval
  mv2 = mv2 + 1.0
end program renprog
