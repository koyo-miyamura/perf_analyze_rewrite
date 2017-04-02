#!/usr/bin/python
# -*- coding: utf-8 -*-
# by teruo
# changed by Koyo

## Readme ##
# usage: ./perf_analyze.py input cpu event offset length
# args:  input  := csv file (output of perf2csv.sh, without _p)
#        cpu    := logical CPU core count, like 32
#        event  := event name, like 'cpu-cycles' (Koyo changed here to analysis all events at one execution.)
#        offset := start offset[sec], like 10.0
#        length := length[sec], like 0.1
# note:  This script executes analysis from offset[sec] to offset + length[sec].
# note:  sqlite3 and numpy library is required (maybe optional)
# note:  Original script is perf_analyze.py and Koyo rewrite it. (Some rewriting may be makeshift)

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
  
  dict = [0 for i in range(len(event))]
  #only cpu0 is analyzed
  for i in range(len(event)):
    sql  = u"select count from perf_event"
    sql += u" where event like \"%%%s%%\" and cpu=%d" % (event[i], 0)
    sql += u" and  time between %f and %f"   % (start, end)
    cur.execute(sql)
    list = cur.fetchall()
    if(len(list)!=0):
      dict[i] =list[0][0]*len(list)
    else:
      dict[i] =0
  con.close()
  return dict


def reduce_analyze_events(li):
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
#You can change here
#Hard coding (It's makeshift)
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
    for idx, row in enumerate(reader):
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
    end   = start + length
  ### Count CPU events
    args = []
    for i in range(ncpus):
     args.append((dbs[i], event, cpu, start, end))
    result2 = p.map(analyze_events, args)
    summary.append(reduce_analyze_events(result2))
    start= start + length

  ### Save Result
  writer = csv.writer(open('perf_analyze.csv', 'wb'), delimiter=';')
  #print(summary)
  writer.writerow(["time"] + [ "%s" % event[i] for i in range(len(event)) ] + ["label"])
  for i in range(len(summary) - 1):
    t = [length*(i+1)]
    #You can change here
    #--label for classification
    label = [0]
    writer.writerow(t + summary[i] + label)

