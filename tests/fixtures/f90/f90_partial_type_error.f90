! SPDX-FileCopyrightText: 2026 ENEA
! SPDX-FileContributor: Alberto P
! SPDX-License-Identifier: MPL-2.0
!
! Same shape as f90_module_and_program.f90, but f90prog declares IMPLICIT
! NONE while still using undeclared `z` - gfortran hard-errors on `z` but
! still emits a full dump for mymod and the rest of f90prog. Regression
! fixture for the bug where a nonzero gfortran exit code caused a perfectly
! usable partial dump to be discarded entirely.
module mymod
  implicit none
  integer, parameter :: NMAX = 100
  type :: point_t
    real :: x
    real :: y
  end type point_t
contains
  subroutine mod_sub(a, b)
    real, intent(in) :: a
    real, intent(out) :: b
    b = a * 2.0
  end subroutine mod_sub
end module mymod

program f90prog
  use mymod
  implicit none
  integer :: i
  real :: arr(10)
  real :: total
  call mod_sub(1.0, total)
  do i = 1, NMAX
     if (i <= 10) then
        arr(i) = i * total
     end if
     z = z + i
  end do
end program f90prog
