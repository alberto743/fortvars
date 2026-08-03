! SPDX-FileCopyrightText: 2026 ENEA
! SPDX-FileContributor: Alberto P
! SPDX-License-Identifier: MPL-2.0
!
! A module (derived type + PARAMETER + CONTAINed subroutine) used by a
! separate program unit that also has an implicitly-typed variable (z).
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
