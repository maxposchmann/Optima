#!/bin/bash

cd thermochimica
make -j > make.out
make -j > make.out
cd ..

python3.9 python/thermoOptima.py
