ifeq (,$(COSMOSIS_SRC_DIR))
$(error "You must source config/setup_for_dev.sh <path-to-ups-product-directory> before building.")
endif

CXX=g++
CC=gcc
FC=gfortran

COMMON_FLAGS=-O3 -g -fPIC
COMMON_C_FLAGS=$(COMMON_FLAGS) -I${COSMOSIS_SRC_DIR} -Wall -Wextra -pedantic
CXXFLAGS=$(COMMON_C_FLAGS) $(USER_CXXFLAGS) -std=c++11
CFLAGS=$(COMMON_C_FLAGS) $(USER_CFLAGS) -std=c99
FFLAGS=$(COMMON_FLAGS) -J${COSMOSIS_SRC_DIR}/cosmosis/datablock $(USER_FFLAGS) -std=gnu -fimplicit-none  -ffree-line-length-none
LDFLAGS=$(USER_LDFLAGS) -L${COSMOSIS_SRC_DIR}/cosmosis/datablock
PYTHON=python
