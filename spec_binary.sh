#!/bin/bash

SPECDIR1="/home/koyo/benchmarks/SPECCPU2006/benchspec/CPU2006/"
#sphinx
#SPECDIR2="482.sphinx3/run/run_base_ref_gcc43-64bit.0007/"
#SPECBY="sphinx_livepretend_base.gcc43-64bit ctlfile . args.an4"

#bzip2_1
#SPECDIR2="401.bzip2/run/run_base_ref_gcc43-64bit.0002/"
#SPECBY="bzip2_base.gcc43-64bit input.source 280"

#bzip2_2
SPECDIR2="401.bzip2/run/run_base_ref_gcc43-64bit.0002/"
SPECBY="bzip2_base.gcc43-64bit chicken.jpg 30"

#gcc


#mcf

cd ${SPECDIR1}${SPECDIR2}

#numactl -C 0 
./${SPECBY}
