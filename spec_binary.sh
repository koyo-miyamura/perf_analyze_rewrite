#!/bin/bash

SPECDIR1="/home/koyo/benchmarks/SPECCPU2006/benchspec/CPU2006/"
SPECDIR2="482.sphinx3/run/run_base_ref_gcc43-64bit.0007/"

cd ${SPECDIR1}${SPECDIR2}

SPECBY="sphinx_livepretend_base.gcc43-64bit ctlfile . args.an4"
#numactl -C 0 
./${SPECBY}
