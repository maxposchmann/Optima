


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
    !    09/12/2013    M.H.A. Piro       Original code
    !    03/20/2014    M.H.A. Piro       Added three capabilities:
    !                                       1) edit previous entry;
    !                                       2) accept new estimates automatically;
    !                                       3) added weighting factors.
    !
    !
    ! Purpose:
    ! ========
    !
    ! The purpose of optima is to perform a non-linear least squares calculation using the
    ! Levenberg-Marquardt algorithm without requiring an analytical calculation of the Jacobian
    ! matrix.  The Jacobian is initiated with a unit rectangular matrix and it is updated using
    ! Broyden's method.  One can use this program to perform a regression analysis (i.e., curve
    ! fitting) of a non-linear function with a given data-set.
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



program optima

    implicit none

    integer                              :: i, m, n, iter
    real(8)                              :: dFuncNorm, dFuncNormLast
    real(8), dimension(:),   allocatable :: x, y, f, s, dDependent, dTempVec
    real(8), dimension(:,:), allocatable :: dBroyden
    character(1)                         :: cYN


    print *, '======================================================================'
    print *
    print *, ' This is a general numerical optimization tool that has not yet'
    print *, ' been groomed for release and it is still considered a prototype.'
    print *, ' Please send me an e-mail if you discover any bugs or general '
    print *, ' comments.'
    print *
    print *, ' Written by M.H.A. Piro; markuspiro@gmail.com; compiled Mar. 19, 2014.'
    print *
    print *, '======================================================================'
    print *
    print *


    ! Request from the user the number of data-points:
    1000 print *, 'How many data-points?'
    read *, m
    print *

    ! Check the input:
    if (m <= 0) then
        print *, 'The number of data-points must be a positive integer.'
        print *
        go to 1000
    end if

    ! Request from the user the number of coefficients:
    1001 print *, 'How many unknown coefficients?'
    read *, n
    print *

    ! Check the input:
    if (n <= 0) then
        print *, 'The number of coefficients must be a positive integer.'
        print *
        go to 1001
    end if

    ! Check input variables:
    if (n > m) then
        print *, 'The number of data-points must be greater than or equal to the '
        print *, 'number of unknown parameters.  The program will hault.'
        print *
        stop
    end if

    ! Deallocate arrays if already allocated:
    if (allocated(x))            deallocate(x)
    if (allocated(f))            deallocate(f)
    if (allocated(dDependent))   deallocate(dDependent)
    if (allocated(f))            deallocate(f)
    if (allocated(s))            deallocate(s)
    if (allocated(y))            deallocate(y)
    if (allocated(dTempVec))     deallocate(dTempVec)

    ! Allocate allocatable arrays:
    allocate(dDependent(m), x(n), f(m), s(n), y(m))
    allocate(dBroyden(m,n))
    allocate(dTempVec(m))

    ! Initialize variables:
    dBroyden     = 1D0
    dFuncNorm    = 0D0
    dDependent   = 0D0
    x            = 0D0
    f            = 0D0
    s            = 0D0
    y            = 0D0
    dTempVec     = 0D0

    ! Request from the user to enter the values to be fitted:
    LOOP_Input_Data: do i = 1, m

        print *, 'Enter the dependent variable for each data-point (y):', i
        read *, dDependent(i)
        print *

    end do LOOP_Input_Data

    ! Request the user to provide two sets of initial estimates:
    print *, 'To initialize the calculation, you will have to enter two sets of initial estimates '
    print *, 'of the coefficients and the resulting functional values.'
    print *

    ! Request user to provide first initial estimates of the coefficients:
    do i = 1, n
        print *, 'Enter first estimate of coefficient ', i
        read *, s(i)
        print *
    end do

    ! Request user to provide first set of functional values resulting from the first estimate:
    do i = 1, m
        print *, 'Enter functional value resulting from the first set of coefficients for variable ', i
        read *, f(i)
        f(i) = f(i) - dDependent(i)
        y(i) = f(i)
        print *
    end do

    ! Compute the functional norm:
    call optimaFunctionalNorm(m, f, dFuncNorm, dFuncNormLast)

    ! Iteration loop to minimize the objective function:
    LOOP_Iter: do iter = 1, 100

        print *, '============='
        print *, 'Iteration ', iter
        print *, '============='
        print *

        ! Request the user to enter new estimates of the coefficients:
        2000 do i = 1, n
            print *, 'Enter a new value for coefficient ', i
            read *, x(i)
            print *
            !read *, x(i)
            !s(i) = x(i) - s(i)
        end do

        ! Check to see if the user accepts these values or wants to re-enter the data:
        print *, 'Accept new sets of estimates for the new coefficients [y/n]?'
        read *, cYN
        print *
        if (cYN == 'n') goto 2000

        ! Update new estimates of the coefficients:
        do i = 1, n
            x(i) = dTempVec(i)
            s(i) = x(i) - s(i)
        end do
        dTempVec = 0D0

        ! Request the user to enter new functional values that are computed from the current set of coefficients:
        2010 do i = 1, m
            print *, 'Enter a new value of function ', i
            read *, dTempVec(i)
            !read *, f(i)
            !f(i) = f(i) - dDependent(i)
            !y(i) = y(i) - f(i)
            print *
        end do

        print *, 'Accept new sets of functional values [y/n]?'
        read *,cYN
        print *
        if (cYN == 'n') goto 2010

        ! Update new functional values:
        do i = 1, m
            f(i) = dTempVec(i)
            f(i) = f(i) - dDependent(i)
            y(i) = y(i) - f(i)
        end do
        dTempVec = 0D0

        ! Compute the functional norm:
        call optimaFunctionalNorm(m, f, dFuncNorm, dFuncNormLast)

        ! Update the Broyden matrix:
        call optimaBroyden(m, n, y, s, dBroyden)

        ! Compute the direction vector:
        call optimaDirectionVector(m, n, f, dBroyden, x)

        ! Update vectors for succeeding iteration:
        do i = 1, n
            s(i) = x(i)
        end do

        do i = 1, m
            y(i) = f(i)
        end do

    end do LOOP_Iter

    ! Deallocate allocatable arrays:
    deallocate(dDependent, x, f, s, y, dBroyden)

end program optima
