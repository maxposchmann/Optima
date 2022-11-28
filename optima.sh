#!/bin/bash

cd thermochimica
make -j > make.out
make -j > make.out
cd ..

source setPython.sh

$python_for_thermochimica python/thermoOptima.py &
