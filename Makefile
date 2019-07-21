objects = optimaBroyden.o optima.o optimaDirectionVector.o optimaFunctionalNorm.o
FC = gfortran
optima: $(objects)
	$(FC) -lblas -llapack -o optima $(objects)
optimaBroyden.o: optimaBroyden.f90
	$(FC) -c -Wall optimaBroyden.f90
optimaDirectionVector.o: optimaDirectionVector.f90
	$(FC) -c -Wall optimaDirectionVector.f90
optima.o: optima.f90
	$(FC) -c -Wall optima.f90
optimaFunctionalNorm.o: optimaFunctionalNorm.f90
	$(FC) -c -Wall optimaFunctionalNorm.f90
clean:
	rm $(objects)
