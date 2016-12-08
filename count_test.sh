#!/bin/bash
SCRDIR=$(readlink -f `dirname $0`)
ANALYZE=${SCRDIR}/perf_analyze_count.py 
cd ..
#${ANALYZE} /home/koyo/perftool_timeseries-master_byme/perftool_timeseries-master/perf.data.dir/../perf.csv/20161206170319 4
${ANALYZE}  /home/koyo/perftool_timeseries-master_byme/rewrite_script/perf.data.dir/../perf.csv/20161207182426 4
