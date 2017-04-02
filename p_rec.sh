#!/bin/bash
#
# Created by Teruo Tanimoto
# http://teruo41.github.io/
#

usage_exit() {
cat <<EOT
Usage: $0 [-e event[,event2,...]] [-d DIR] [-p /path/to/perf] -- command
       $0 [-h]
Note:  Root privilege is needed for sample C-state info.
       Events can be set with period or freq like:
         -e cpu/cpu-cycles,period=1000000/
         -e cpu/cpu-cycles,freq=100000/
       Default command is "openssl speed rsa512 (-multi #cpus)."
EOT
exit
}

get_perf_ver() {
  $PERF --version | awk '{print $3}' | cut -f1 -d- | sed "s:\.: :g"
}

check_perf_ver() {
  REQUIRED=(`echo $1 | sed "s:\.: :g"`)
  INSTALLED=(`get_perf_ver`)

  [ ${#REQUIRED[*]} -lt ${#INSTALLED[*]} ] \
    && NUM=${#REQUIRED[*]} \
    || NUM=${#INSTALLED[*]}

  for IDX in `seq 0 $((NUM - 1))`
  do
    if [ ${INSTALLED[$IDX]} -lt ${REQUIRED[$IDX]} ]
    then
      echo 0
      return
    elif [ ${INSTALLED[$IDX]} -gt ${REQUIRED[$IDX]} ]
    then
      echo 1
      return
    fi
  done
  echo 1
}

SCRDIR=$(readlink -f `dirname $0`)

OUTDIR=${SCRDIR}/../perf.data.dir
#EVENTS="cpu/cpu-cycles,freq=10/"
#EVENTS=$EVENTS",cpu/instructions,freq=10/"
#EVENTS=$EVENTS",cpu/cache-misses,freq=10/"
#EVENTS=$EVENTS",cpu/branch-misses,freq=10/"
#EVENTS=$EVENTS",cpu/event=0xc4,umask=0x00,name=branch_instruction_retired,freq=10/"
#EVENTS=$EVENTS",cpu/event=0xc5,umask=0x00,name=Branch_Misses_Retired,freq=10/"
#EVENTS=$EVENTS",cpu/event=0xd1,umask=0x08,name=mem_load_uops_retired.l1_miss,freq=10/"
#EVENTS=$EVENTS",cpu/event=0xd1,umask=0x01,name=mem_load_uops_retired.l1_hit,freq=10/"

#EVENTS="cpu/cpu-cycles,period=1000000/"
EVENTS="cpu/event=0x80,umask=0x02,name=icache.misses,period=1000/"
EVENTS=$EVENTS",cpu/instructions,period=1000000/"
EVENTS=$EVENTS",cpu/event=0x14,umask=0x01,name=arith.fpu_div_active,period=1000/"
EVENTS=$EVENTS",cpu/event=0xd0,umask=0x81,name=mem_uops_retired.all_loads,period=1000/"
EVENTS=$EVENTS",cpu/event=0xd0,umask=0x82,name=mem_uops_retired.all_stores,period=1000/"
#EVENTS=$EVENTS",cpu/event=0xc4,umask=0x10,name=br_inst_retired.not_taken,period=1000/"
#EVENTS=$EVENTS",cpu/cache-misses,period=1000/"
#EVENTS=$EVENTS",cpu/branch-misses,period=1000/"
EVENTS=$EVENTS",cpu/event=0xc4,umask=0x00,name=branch_instruction_retired,period=10000/"
EVENTS=$EVENTS",cpu/event=0xc5,umask=0x00,name=Branch_Misses_Retired,period=1000/"
#EVENTS=$EVENTS",cpu/event=0xd1,umask=0x01,name=mem_load_uops_retired.l1_hit,period=1000/"
EVENTS=$EVENTS",cpu/event=0xd1,umask=0x08,name=mem_load_uops_retired.l1_miss,period=1000/"
PERF=`which perf`
while getopts d:hp: OPT
do
  case $OPT in
    d)
      OUTDIR=$OPTARG
      ;;
    e)
      EVENT=$OPTARG
      ;;
    h)
      usage_exit
      ;;
    p)
      PERF=$OPTARG
      ;;
    \?)
      usage_exit
      ;;
  esac
done

shift $((OPTIND - 1))


[ ! -x "$PERF" ] && echo "perf command not found!" >&2 && exit
[ `check_perf_ver 3.16.7`  == 0 ] \
  && echo "perf is older than 3.16.7. Please update it." && exit

[ ! -d ${OUTDIR} ] && mkdir ${OUTDIR}
OUTPUT=${OUTDIR}/`date +%Y%m%d%H%M%S`

TMPDIR=${SCRDIR}/../tmp
[ ! -d $TMPDIR ] && mkdir ${TMPDIR}
echo ${OUTPUT} > ${TMPDIR}/p_rec.tmp

ARGS="-a -e $EVENTS -o ${OUTPUT}_0"

:<<comment
if [ -z "$@" ]
then
  NUMCPUS=`grep processor /proc/cpuinfo | wc -l`
  if [ $NUMCPUS -gt 1 ]
  then
    CMD="openssl speed rsa512 -multi $NUMCPUS"
  else
    CMD="openssl speed rsa512"
  fi
else
  CMD="$@"
fi
comment

#:<<binary
#SPECDIR1="/home/koyo/benchmarks/SPECCPU2006/benchspec/CPU2006/"
#SPECDIR2="482.sphinx3/run/run_base_ref_gcc43-64bit.0007/"
#SPECBY="${SPECDIR1}${SPECDIR2}./sphinx_livepretend_base.gcc43-64bit ${SPECDIR1}${SPECDIR2}ctlfile ${SPECDIR1}${SPECDIR2} ${SPECDIR1}${SPECDIR2}args.an4"
#CMD="numactl -C 0 ${SPECBY}"

CMD="numactl -C 0 ./spec_binary.sh"
#binary

#CMD="numactl -C 0 runspec --config Linux64-amd64-gcc43+.cfg --iterations 1 --noreportable 482.sphinx3"
#CMD="numactl -C 0 runspec --config Linux64-amd64-gcc43+.cfg --iterations 1 --noreportable 401.bzip2"

#sudo ${PERF} timechart record \
#  ${PERF} record $ARGS -- $CMD

#${PERF} timechart record \
  ${PERF} record $ARGS -- /usr/bin/time $CMD

#/usr/bin/time $CMD

#mv perf.data ${OUTPUT}_p

#sudo isn't needed
#chown ${USER}. ${OUTPUT}_0
#chown ${USER}. ${OUTPUT}_p
