#!/usr/bin/python
# -*- coding: utf-8 -*-
# by teruo
# changed by koyo

## Readme ##
# usage: ./perf_analyze.py input cpu event offset length
# args:  input  := csv file (output of perf2csv.sh, without _p)
#        cpu    := logical CPU core count, like 32
#        event  := event name, like 'cpu-cycles'
#        offset := start offset[sec], like 10.0
#        length := length[sec], like 0.1
# note:  This script executes analysis from offset[sec] to offset + length[sec].
# note:  sqlite3 and numpy library is required (maybe optional)

import os
import sys
import math
import csv
import sqlite3
import numpy
import re
import multiprocessing

import time

def gettime(db):
  con = sqlite3.connect(db)
  cur = con.cursor()

#  min = float("inf")
#  max = float("-inf")
#  sql = u"select time from perf_event"
#  for row in cur.execute(sql):
#    if min > row[0]:
#      min = row[0]
#    if max < row[0]:
#      max = row[0]
  
  sql_min = u"select min(time) from perf_event"
  sql_max = u"select max(time) from perf_event"
  for row in cur.execute(sql_min):
    min = row[0]
  for row in cur.execute(sql_max):
    max = row[0]
  con.close()
  return (min, max)

def reduce_gettime(list):
  min = float("inf")
  max = float("-inf")
  for i in range(len(list)):
    if min > list[i][0]:
      min = list[i][0]
    if max < list[i][1]:
      max = list[i][1]
  return (min, max)

def analyze_events(args):
  db    = args[0]
  #event must be array
  event = args[1]
  cpu   = args[2]
  start = args[3]
  end   = args[4]

  con = sqlite3.connect(db)
  cur = con.cursor()

#  dict = {}
#  for cpuid in range(cpu):
#    sql  = u"select comm,sym,bin from perf_event"
#    sql += u" where event like \"%%%s%%\" and cpu=%d" % (event, cpuid)
#    sql += u" and  time between %f and %f"   % (start, end)
#    for row in cur.execute(sql):
#      funcname = ";".join(row)
#      if dict.has_key(funcname):
#        value = dict[funcname]
#        value[cpuid] += 1
#        dict[funcname] = value
#      else:
#        value = [ 0 for i in range(cpu) ]
#        value[cpuid] += 1
#        dict[funcname] = value
#  con.close()
#  return dict
  
  dict = [0 for i in range(len(event))]
  #only cpu0 is analyzed
  for i in range(len(event)):
    sql  = u"select count from perf_event"
    sql += u" where event like \"%%%s%%\" and cpu=%d" % (event[i], 0)
    sql += u" and  time between %f and %f"   % (start, end)
    #the count of PC

#    for row in cur.execute(sql):
#      if(len(row)!=0):
#        dict[i] += row[0]    

    cur.execute(sql)
    list = cur.fetchall()
    if(len(list)!=0):
      dict[i] =list[0][0]*len(list)
    else:
      dict[i] =0
  con.close()
  return dict


def reduce_analyze_events(li):
#  summary = {}
#  for dict in li:
#    for key in dict.keys():
#      if summary.has_key(key):
#        summary[key] = summary[key] + numpy.array(dict[key])
#      else:
#        summary[key] = numpy.array(dict[key])
#  return summary

  #summary = {}
  #for dict in li:
  #  for event_name in dict.keys():
  #    if summary.has_key(event_name):
  #      summary[event_name] = summary[event_name] + dict[event_name]
  #    else:
  #      summary[event_name] = dict[event_name]
  #return summary

  summary = [0 for i in range(len(li[0]))]
  for each_li in li:
    for i in range(len(each_li)):
      summary[i] += each_li[i]
  return summary


### Parse Arguments
argvs = sys.argv
argc  = len(argvs)

print "ARGVS = (" + ", ".join(argvs) + ")"
# print "ARGC  = %d" % argc

ncpus  = multiprocessing.cpu_count()
scrdir = os.path.dirname(__file__)

cpu    = 32               # ARG2
#Hard coding (it is not good)
#event  = "cpu-cycles"               # ARG3
#--event hard coding
event  =["icache.misses"
        ,"cpu/instructions"
        ,"arith.fpu_div_active"
        ,"mem_uops_retired.all_loads"
        ,"mem_uops_retired.all_stores"
#        ,"br_inst_retired.not_taken"
        ,"branch_instruction_retired"
        ,"Branch_Misses_Retired"
#        ,"mem_load_uops_retired.l1_hit"
        ,"mem_load_uops_retired.l1_miss"]
offset = 1.0              # ARG4
#--length change
length = 0.1              # ARG5

if argc >= 2:
  input = argvs[1]
if argc >= 3:
  cpu   = int(argvs[2])
if argc >= 4:
#event must be list
  event = argvs[3]
if argc >= 5:
  offset = float(argvs[4])
if argc == 6:
  length = float(argvs[5])
if argc >  6:
  print "Invalid Arguments"
  quit()

print "cpu = %d, event = %s, offset = %f, length = %f" % (cpu, event, offset, length)

### Create DB
dbs  = [ scrdir+"/../perf.db/"+os.path.basename(input)+".%02d" % i for i in range(ncpus) ]
#print(dbs)
print(os.path.isdir(scrdir+"/../perf.db"))
print(os.path.isfile(dbs[0]))

if not os.path.isdir(scrdir+"/../perf.db"):
  os.makedirs(scrdir+"/../perf.db")

if not os.path.isfile(dbs[0]):
  ### Create DB
  cons = [ sqlite3.connect(db) for db in dbs ]
  
  ### Create Table
  sql = u"""
  create table perf_event (
    comm  TEXT,
    pid   INTEGER,
    cpu   INTEGER,
    time  REAL,
    count INTEGER,
    event TEXT,
    addr  TEXT,
    sym   TEXT,
    bin   TEXT
  )
  """
  
  for i in range(ncpus):
    cons[i].execute(sql)
#    cons[i].execute("create index analyze on perf_event(time,count,event)")
  
  time_insert_s = time.time()
  ### Insert Data
  for i in range(len(event)):
    reader = csv.reader(open(input+"_"+str(i)+".csv", 'rb'), delimiter=';')
    sql = u"insert into perf_event values (?, ?, ?, ?, ?, ?, ?, ?, ?)"
#    insert_row = []
#    insert_count = 0
    for idx, row in enumerate(reader):
#      row[2] = int(re.search('[0-9]+', row[2]).group(0))
#      #only cpu0 is inserted
#      if(row[2]==0):
#        insert_row.append(row)
#        insert_count += 1
#      if(insert_count % 200000 == 0):
#        cons[idx%ncpus].executemany(sql, insert_row)
#    else:
#        cons[idx%ncpus].executemany(sql, insert_row)
#    print("event %s" % event[i])  
#    print("insert_time from start:"+str(time.time()-time_insert_s)+"[s]")

      row[2] = int(re.search('[0-9]+', row[2]).group(0))
      #only cpu0 is inserted
      if(row[2]==0):
#        print(row)
        cons[idx%ncpus].execute(sql, row)
    print("insert_time from start:"+str(time.time()-time_insert_s)+"[s]")

  time_commit_s = time.time()
  ### Close DB
  for i in range(ncpus):
    cons[i].commit()
    cons[i].execute("create index analyze on perf_event(time,count,event)")
    cons[i].close()
    print("commit_%d" %i)
    print("commit_index_time from start:"+str(time.time()-time_commit_s)+"[s]")

### Main
if __name__ == '__main__':

  ### Create Process Pool
  p = multiprocessing.Pool()
  
  ### Get Time Range
  result0 = p.map(gettime, dbs)
  time_range = reduce_gettime(result0)
  print "TIME Range = ", time_range

##########start loop########

  ### Search for Certain Range
  start = time_range[0] + offset
  summary = []
  while start < time_range[1]: 
#  for i in range(100):
#    time_s = time.time()
    end   = start + length

  ### Count CPU events
 # if event in [ "cpu-cycles", "instructions", "cache-misses" ]:
    args = []
    for i in range(ncpus):
     args.append((dbs[i], event, cpu, start, end))
    result2 = p.map(analyze_events, args)
#    print("time:"+str(time.time()-time_s)+"[s]")
    summary.append(reduce_analyze_events(result2))
#    cpu_events = numpy.array([ 0 for i in range(cpu) ])
#    for key in summary.keys():
#      cpu_events += summary[key]
#      summary[key] = numpy.append(summary[key], numpy.sum(summary[key]))
#
    start= start + length
#  elif event in [ "mpki", "ipc" ]:
#    if event == "mpki":
#      event1 = "cache-misses"
#      event2 = "instructions"
#    elif event == "ipc":
#      event1 = "instructions"
#      event2 = "cpu-cycles"
#
#    args = []
#    for i in range(ncpus):
#      args.append((dbs[i], event1, cpu, start, end))
#    for i in range(ncpus):
#      args.append((dbs[i], event2, cpu, start, end))
#    result2 = p.map(analyze_events, args)
#
#    summary  = {}
#    summary1 = reduce_analyze_events(result2[0:ncpus-1])
#    summary2 = reduce_analyze_events(result2[ncpus:ncpus*2-1])
#
#    cpu_events  = numpy.array([ 0 for i in range(cpu) ])
#    cpu_events1 = numpy.array([ 0 for i in range(cpu) ])
#    cpu_events2 = numpy.array([ 0 for i in range(cpu) ])
#
#    for key in summary1.keys():
#      tmp = numpy.array([], dtype=numpy.float64)
#      if summary2.has_key(key):
#        cpu_events1 += summary1[key]
#        cpu_events2 += summary2[key]
#        for idx, num in enumerate(summary2[key]):
#          if num == 0:
#            tmp = numpy.append(tmp, 0.0)
#          else:
#            tmp = numpy.append(tmp, summary1[key][idx] / float(num))
#        else:
#          tmp = numpy.append(tmp, numpy.sum(summary1[key]) / float(numpy.sum(summary2[key])))
#        summary[key] = tmp
#    cpu_events_ratio = numpy.array([], dtype=numpy.float64)
#    for idx, num in enumerate(cpu_events2):
#      if num == 0:
#        cpu_events_ratio = numpy.append(cpu_events_ratio, 0)
#      else:
#        cpu_events_ratio = numpy.append(cpu_events_ratio, cpu_events1[idx]/float(cpu_events2[idx]))
#    else:
#      cpu_events_ratio = numpy.append(cpu_events_ratio, sum(cpu_events1) / float(sum(cpu_events2)))
#  else:
#    quit()
    

#  for key, value in sorted(summary.items(), key=lambda x:x[1][cpu], reverse=True):
#    if event in [ "cpu-cycles", "instructions", "cache-misses" ]:
#      for cpuid in cpulist:
#        if cpu_events[cpuid]:
#          tmp = value[cpuid]/float(cpu_events[cpuid])*100
#          print "%6.2f" % tmp,
#        else:
#          print "%6.2f" % 0,
#      else:
#        tmp = value[cpu]/float(sum(cpu_events))*100
#        print "%6.2f" % tmp,
#    elif event in [ "mpki", "ipc" ]:
#      for cpuid in cpulist:
#        print "%6.2f" % value[cpuid],
#      else:
#        print "%6.2f" % value[cpu],
#    print "%10s;" % key

  ### Save Result
  writer = csv.writer(open('perf_analyze.csv', 'wb'), delimiter=';')
  #print(summary)
  writer.writerow(["time"] + [ "%s" % event[i] for i in range(len(event)) ] + ["label"])
#  time_csv_s =time.time()
  for i in range(len(summary)):
    t = [length*(i+1)]
    #--label for classification
    label = [0]
    writer.writerow(t + summary[i] + label)
#  print("write csv time:"+str(time.time()-time_csv_s)+"[s]")
  #writer.writerows(summary)

#  writer.writerow(["C0-State Ratio[%]"] + cpurunning + ["nan"])
#  writer.writerow(["%s" % event] + cpu_events_ratio.tolist() + ["100.0"])
  
#  for key, value in sorted(summary.items(), key=lambda x:x[1][cpu], reverse=True):
#    row = [key]
#    if event in [ "cpu-cycles", "instructions", "cache-misses" ]:
#      for cpuid in range(cpu):
#        if cpu_events[cpuid]:
#          row.append(value[cpuid]/float(cpu_events[cpuid])*100)
#        else:
#          row.append(0.0)
#      else:
#        row.append(value[cpu]/float(sum(cpu_events))*100)
#    elif event in [ "mpki", "ipc" ]:
#      for cpuid in range(cpu):
#        row.append(value[cpuid])
#      else:
#        row.append(value[cpu])
#    writer.writerow(row)
