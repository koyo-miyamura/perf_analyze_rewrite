#!/bin/bash

SPECDIR1="/home/koyo/benchmarks/SPECCPU2006/benchspec/CPU2006/"

#sphinx
#SPECDIR2="482.sphinx3/run/run_base_ref_gcc43-64bit.0007/"
#SPECBY="sphinx_livepretend_base.gcc43-64bit ctlfile . args.an4"

#bzip2_1 int
#SPECDIR2="401.bzip2/run/run_base_ref_gcc43-64bit.0002/"
#SPECBY="bzip2_base.gcc43-64bit input.source 280"

#bzip2_2 int
#SPECDIR2="401.bzip2/run/run_base_ref_gcc43-64bit.0002/"
#SPECBY="bzip2_base.gcc43-64bit chicken.jpg 30"

#gcc int
#SPECDIR2="403.gcc/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="gcc_base.gcc43-64bit 166.in -o 166.s"

#mcf
#SPECDIR2="429.mcf/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="mcf_base.gcc43-64bit inp.in"

#perlbench int
SPECDIR2="400.perlbench/run/run_base_ref_gcc43-64bit.0001/"
SPECBY="perlbench_base.gcc43-64bit -I./lib checkspam.pl 2500 5 25 11 150 1 1 1 1"

#astar int
#SPECDIR2="473.astar/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="astar_base.gcc43-64bit BigLakes2048.cfg"

#libquantum int
#SPECDIR2="462.libquantum/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="libquantum_base.gcc43-64bit 1397 8"

#bwaves
#SPECDIR2="410.bwaves/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="bwaves_base.gcc43-64bit"

#lbm
#SPECDIR2="470.lbm/run/run_base_ref_gcc43-64bit.0000/"
#SPECBY="lbm_base.gcc43-64bit 3000 reference.dat 0 0 100_100_130_ldc.of"

#wrf
#SPECDIR2="481.wrf/run/run_base_ref_gcc43-64bit.0000/"
#SPECBY="wrf_base.gcc43-64bit"

#xalancbmk int
#SPECDIR2="483.xalancbmk/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="Xalan_base.gcc43-64bit -v t5.xml xalanc.xsl"

#omnetpp int
#SPECDIR2="471.omnetpp/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="omnetpp_base.gcc43-64bit omnetpp.ini"

#hmmer int
#SPECDIR2="456.hmmer/run/run_base_ref_gcc43-64bit.0001/"
#SPECBY="hmmer_base.gcc43-64bit nph3.hmm swiss41"

cd ${SPECDIR1}${SPECDIR2}

#numactl -C 0 
./${SPECBY}
