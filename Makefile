EXE = $(BIN_DIR)/optima

AR          = ar
FC          = gfortran
FCFLAGS     = -Wall -g -O0 -fno-automatic -fbounds-check -ffpe-trap=zero

# links to lapack and blas libraries:
LDLOC     =  -L/usr/lib/lapack -llapack -L/usr/lib/libblas -lblas -lgfortran

# link flags for linux users:
LDFLAGS     =  -O0 -g -fno-automatic -fbounds-check

SRC = $(notdir $(wildcard $(SRC_DIR)/*.f90))
OBJ = $(patsubst %,$(OBJ_DIR)/%,$(SRC:.f90=.o))

OBJ_DIR     = obj
BIN_DIR     = bin
SRC_DIR     = src

all: $(OBJ)
	$(FC) -I$(OBJ_DIR) -J$(OBJ_DIR) $(FCFLAGS) $(LDFLAGS) -o $(EXE) $(OBJ) $(LDLOC)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.f90
	$(FC) -I$(OBJ_DIR) -J$(OBJ_DIR) $(FCFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ_DIR)/*
	rm -f $(BIN_DIR)/*
	rm -f $(EXE)
