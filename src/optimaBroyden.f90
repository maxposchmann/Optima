

    !-------------------------------------------------------------------------------------------------------------
    !
    ! DISCLAIMER
    ! ==========
    ! 
    ! All of the programming herein is original unless otherwise specified.  Details of contributions to the 
    ! programming are given below.
    !
    !
    ! Revisions:
    ! ==========
    ! 
    !    Date          Programmer         Description of change
    !    ----          ----------         ---------------------
    !    09/12/2013    M.H.A. Piro        Original code
    !
    !
    ! Purpose:
    ! ========
    !
    ! The purpose of this subroutine is to calculate the update to the Broyden matrix that can be used for
    ! the Levenberg-Marquartd Algorithm (LMA).  For this case, the Broyden matrix is rectangular.
    !
    !
    ! Pertinent variables:
    ! ====================
    !
    !> \param[in] m             The number of data-points to be optimized.
    !> \param[in] n             The number of unknown parameters.
    !> \param[inout] s          The change of the unknown variable vector.
    !> \param[in] y             The change of the functional vector.
    !> \param[in] f             The functional vector.
    !> \param[inout] dBroyden   The Broyden matrix (rectangular).
    !
    !-------------------------------------------------------------------------------------------------------------


subroutine optimaBroyden(m, n, y, s, dBroyden)

    implicit none
    
    integer                :: i, j, m, n   
    real(8)                :: dTempVar 
    real(8),dimension(m)   :: y, dTempVec
    real(8),dimension(n)   :: s
    real(8),dimension(m,n) :: dBroyden


    ! Initialize variables:
    dTempVar = 0D0
    dTempVec = 0D0

    ! Check input variables:
    if (n > m) then        
        print *, 'The number of data-points must be greater than or equal to the '
        print *, 'number of unknown parameters.  The program will hault.'
        print *
        stop
    end if
    
    ! Compute Bs:
    do j = 1, n
        do i = 1, m
            dTempVec(i) = dTempVec(i) + dBroyden(i,j) * s(j)
        end do
    end do

    ! Compute sTs:
    do j = 1, n
        dTempVar = dTempVar + s(j)**2
    end do
    
    ! Make sTs multiplicative:
    dTempVar = 1D0 / dTempVar

    ! Compute (y - Bs) / sTs
    do i = 1, m
        dTempVec(i) = (y(i) - dTempVec(i)) * dTempVar
    end do

    ! Update the Broyden matrix:
    do j = 1, n
        do i = 1, m
            dBroyden(i,j) = dBroyden(i,j) + dTempVec(i) * s(j)
        end do
    end do

    return
    
end subroutine optimaBroyden
