! SPDX-FileCopyrightText: 2026 ENEA
! SPDX-FileContributor: Alberto P
! SPDX-License-Identifier: MPL-2.0
!
! Fortran 2003: derived TYPE, a KIND parameter, and a procedure with
! INTENT(IN)/INTENT(OUT) derived-type dummy arguments.
module f03mod
  implicit none
  integer, parameter :: dp = selected_real_kind(15, 307)
  type :: vec3_t
    real(dp) :: x, y, z
    integer :: tag
  end type vec3_t
  real(dp), parameter :: TOL = 1.0e-9_dp
contains
  subroutine scale_vec(v, factor, out)
    type(vec3_t), intent(in) :: v
    real(dp), intent(in) :: factor
    type(vec3_t), intent(out) :: out
    out%x = v%x * factor
    out%y = v%y * factor
    out%z = v%z * factor
    out%tag = v%tag
  end subroutine scale_vec
end module f03mod
