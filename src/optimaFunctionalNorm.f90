


    !-------------------------------------------------------------------------------------------------------------
    !
    ! DISCLAIMER
    ! ==========
    ! 
    ! All of the programming herein is original unless otherwise specified. 
    !
    !
    ! Revisions:
    ! ==========
    ! 
    !    Date          Programmer        Description of change
    !    ----          ----------        ---------------------
    !    07/21/2019    M.H.A. Piro       Moved to a new file to clean up code.
    !
    !
    ! Purpose:
    ! ========
    !
    ! The purpose of this program is to compute the functional norm of the objective function, which is
    ! an indicator as to the nearness of convergence and whether the iterative routine is converging or
    ! diverging. 
    !
    !
    !
    ! Pertinent variables:
    ! ====================
    !
    !   Variable                    Brief Description
    !   --------                    -----------------
    !
    !
    !-------------------------------------------------------------------------------------------------------------

subroutine optimaFunctionalNorm(m, f, dFuncNorm, dFuncNormLast)

    implicit none
    
    integer              :: i, m
    real(8)              :: dFuncNorm, dFuncNormLast
    real(8),dimension(m) :: f


    ! Initialize variables:
    dFuncNormLast = dFuncNorm
    dFuncNorm     = 0D0

    ! Compute the functional norm:
    do i = 1, m
        dFuncNorm = dFuncNorm + f(i)
    end do
    
    ! Normalize the functional norm:
    dFuncNorm = (dFuncNorm)**(0.5)
    
    print *, 'The functional norm is: ', dFuncNorm
    print *

    ! Check if the system is diverging:
    if (dFuncNorm > dFuncNormLast) then
        print *, '********************************************************************************'
        print *
        print *, 'WARNING: The system is diverging.  Be careful when selecting a steplength in the following'
        print *, 'iteration.'
        print *
        print *, '********************************************************************************'
        print *
    end if

    return

end subroutine optimaFunctionalNorm
