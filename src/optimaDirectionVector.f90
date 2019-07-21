

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
    ! The purpose of this subroutine is to calculate the direction vector using an updated Broyden matrix.
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


subroutine optimaDirectionVector(m, n, f, dBroyden, x)

    implicit none
    
    integer                :: i, j, m, n, k, INFO
    integer,dimension(n)   :: IPIV
    real(8)                :: dTempVar, lambda
    real(8),dimension(m)   :: f
    real(8),dimension(n)   :: B, x
    real(8),dimension(m,n) :: dBroyden
    real(8),dimension(n,n) :: A


    ! Request a value of lambda from the user:
    3000 print *, 'Enter a value for lambda (default = 1):'
    read *, lambda
    
    if (lambda < 0D0) then
        print *, 'Lambda must be positive. '
        print *
        go to 3000
    end if
    
    ! Initialize variables:
    INFO     = 0
    IPIV     = 0
    A        = 0D0
    B        = 0D0
    dTempVar = 0D0
    
    ! Compute the (J^T J) matrix:
    do j = 1, n
        do i = j, n
            dTempVar = 0D0
            do k = 1, m
                dTempVar = dTempVar + dBroyden(k,i) * dBroyden(k,j)
            end do
            
            ! Compute the coefficient for the A matrix:
            A(i,j) = dTempVar
            
            ! Apply symmetry:
            A(j,i) = dTempVar
        end do
    end do
    
    ! Compute the right hand side vector:
    do j = 1, n
        do i = 1, m 
            B(j) = B(j) + dBroyden(i,j) * f(i)
        end do 
        A(j,j) = A(j,j) + lambda
    end do
    
    ! Call the linear equation solver:
    call DGESV( n, 1, A, n, IPIV, B, n, INFO )  

    ! Check if there were any errors with the linear equation solver:
    if (INFO == 0) then
        ! Successful calculation.
        
        3010 print *, 'Enter a steplength (0 < alpha >= 1):'
        read *, dTempVar
        print *

        ! Check the steplength:
        if ((dTempVar <= 0D0).OR.(dTempVar > 1D0)) then
            print *, 'The steplength must be greater than zero and less than or equal to one.'
            print *
            goto 3010
        end if
        
        ! Print results to screen:
        print *, 'Index | direction vector | new values:'
        print * 
        do j = 1, n
            !print *, j, B(j)
            print *, j, B(j), x(j) + dTempVar * B(j)
        end do
        print *  
    else
        ! Unsuccessful exit.  Report an error and stop.
        print *, 'There was a problem in solving the system of linear equations. '
        print *, 'Error code = ', INFO
        print *
        stop  
    end if

    return
    
end subroutine optimaDirectionVector
