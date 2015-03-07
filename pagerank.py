#!/usr/bin/python

import sys

from array import array
from multiprocessing import Process,Event,Pipe,Array
from ctypes import c_double

def readGraph(lines):
  g = {} # node number -> out-link counts 
  ing = {} # node number -> set of in-link node numbers
  nodes = set() # all nodes
  for line in lines:
    #line = line.strip()
    if line.startswith('#'):
      continue
    l = line.split()
    k = int(l[0])
    v = int(l[-1])
    #g.setdefault(k, set()).add(v)
    g.setdefault(k, 0)
    g[k] += 1
    ing.setdefault(v, set()).add(k)
    nodes.add(k)
    nodes.add(v)
  return g, ing, sorted(nodes)

def diffVector(l1, l2, lower=0, higher=0):
  s = 0.0
  i = lower
  higher = len(l1) if not higher else higher
  while i < higher:
    s += abs(l1[i] - l2[i])
    i += 1
  return s

def transformGraph(nodes, ing, g):
  idxInG = {} # instead of storing node number, store index of node -> index of in-nodexs
  idxG = {}
  idx = dict(zip(nodes, range(len(nodes))))
  for node, inNodes in ing.iteritems():
    idxInG[idx[node]] = set([idx[inNode] for inNode in inNodes])
  for node, outDegree in g.iteritems():
    idxG[idx[node]] = outDegree #set([idx[outNode] for outNode in outNodes])
  return idxInG, idxG

def transformToArray(nodes, ing, g):
  inA = array('l')
  a = array('l')
  idxInG, idxG = transformGraph(nodes, ing, g)
  ing_pos = array('l') # array contains the starting index in inA for each entry in ing
  i = 0
  ing_cur = 0
  while i < len(nodes): #[<index>, <size>, <out node list>]
    if i in idxG:
      a.append(idxG[i])
    else:
      a.append(0)
    if i in idxInG:
      ing_pos.append(ing_cur)
      inA.append(i)
      inNodes = idxInG[i]
      inA.append(len(inNodes))
      inA.extend(inNodes)
      ing_cur += len(inNodes) + 2
    i += 1
  
  return Array('l',inA, lock=False), Array('l',a, lock=False), Array('l', ing_pos, lock=False)

def fill_vector(r, num, lower=0, higher=0):
  if lower > higher:
    lower , higher = higher, lower
  i = lower
  size = len(r) if not higher else higher
  while i < size:
    r[i] = num
    i += 1

def forEachElement(r, func):
  i = 0
  size = len(r)
  while i < size:
    r[i] = func(r[i], i)
    i += 1

_debug = False
def log(msg):
  if _debug:
   print >>sys.stderr, msg

def iterate(tid, r, r_, g, ing, idx, shared):
  t = 1
  e = shared['e']
  diff = e + 1
  n = shared['n']
  size = shared['size']
  lower = shared['lower'][tid]
  higher = shared['higher'][tid]
  ing_low = shared['ing_low'][tid]
  ing_high = shared['ing_high'][tid]
  beta = shared['beta']
  log('T{0}: lower={1}, higher={2}; ing_low={3}, ing_high={4}'.format(tid, lower, higher, ing_low, ing_high))

  while diff > e and (n == -1 or t < n):
    sum_r = 0.0
    # fill in 0s
    fill_vector(r_, 0.0, lower, higher)
    cursor = ing_low
    while cursor < ing_high:
      j = ing[cursor]
      cursor += 1
      row_size = ing[cursor]
      cursor += 1
      row_end = cursor + row_size
      rj = 0.0
      while cursor < row_end :
	i = ing[cursor]
	rj += r[i] / g[i]
	cursor += 1
      r_[j] += rj
      sum_r += rj
    
    sum_r *= beta
    shared['sum_r'][tid] = sum_r
    #shared['sum_r'][tid] = sum_r
    shared['children'][tid].set() # shared['childEvents'] is a list of threading.Event objects
    waitForMain(shared)
    sum_r = shared['sum_r'][tid]
    leaked = 1 - sum_r
    leakedShare = leaked / size if leaked > 0 else 0.0
    _i = lower
    while _i < higher:
      # multiply by beta and fix leak at the same time
      r_[_i] = r_[_i] * beta + leakedShare
      _i +=1

    diff = diffVector(r, r_, lower, higher)
    shared['diff'][tid] = diff
    shared['children'][tid].set()
    waitForMain(shared)

    diff = shared['diff'][tid]
    r, r_ = r_, r
    t += 1


def pageRank(nodes, g, ing, ing_pos, beta=0.8, e=1e-8, n=1e2, threads=4):
  size = len(nodes)
  r = Array(c_double,[1.0/size] * size, lock=False)
  r_ = Array(c_double,r, lock=False)
  idx = dict(zip(nodes, range(len(nodes))))
  threadPool = []
  shared = {
      'e': e,
      'n': n,
      'size': size,
      'lower': [0] * threads, 
      'higher': [0] * threads, 
      'ing_low': [0] * threads,
      'ing_high': [0] * threads,
      'beta': beta,
      'sum_r': Array(c_double, [0.0] * threads, lock=False), 
      'children': [None] * threads, 
      'main': Event(),
      'diff': Array(c_double, [0.0] * threads, lock=False) ,
      'threads': threads
      }

  for tid in range(threads):
    shared['lower'][tid] = tid * size / threads
    shared['higher'][tid] = (tid + 1) * size / threads
    shared['ing_low'][tid] = ing_pos[tid * len(ing_pos) / threads]
    shared['ing_high'][tid] = ing_pos[(tid + 1 ) * len(ing_pos) / threads - 1] + 1
    shared['children'][tid] = Event()
#    shared['sum_r'][tid] = Pipe()
#    shared['diff'][tid] = Pipe()
    threadPool.append(Process(target=iterate, args=(tid, r, r_, g, ing, idx, shared)))
    threadPool[-1].start()
  diff = 1 + e
  t = 1
  while diff > e and (t == -1 or t < n):
    waitForChildren(shared)

    # now to compute the whole sum_r
#    sum_r = sum([tup[1].recv() for tup in shared['sum_r']])
    sum_r = sum(shared['sum_r'])
    fill_vector(shared['sum_r'], sum_r)
#    temp = [tup[1].send(sum_r) for tup in shared['sum_r']]
    shared['main'].set()

    waitForChildren(shared) 
#    diff = sum([tup[1].recv() for tup in shared['diff']])
    diff = sum(shared['diff'])
    fill_vector(shared['diff'], diff)
#    temp = [tup[1].send(diff) for tup in shared['diff']]

    shared['main'].set()
    t += 1
  for th in threadPool:
    th.join()
  return r, t

def waitForChildren(shared):
  for tid in range(shared['threads']):
    shared['children'][tid].wait()
  for tid in range(shared['threads']):
    shared['children'][tid].clear()

def waitForMain(shared):
  shared['main'].wait()
  shared['main'].clear()
    
if __name__ == '__main__':
  import fileinput
  import time
  import argparse
  import os

  parser = argparse.ArgumentParser()
  parser.add_argument('-v', dest='debug', action='store_true')
  parser.add_argument('-p', dest='p', type=int, default=1)
  args = parser.parse_args()
 
  print >> sys.stderr, 'PID: {0}'.format(os.getpid())
  _debug = args.debug
  timer = 0 - time.time()
  lines = fileinput.input()
  g, ing, nodes = readGraph(sys.stdin)
  timer += time.time()
  print >> sys.stderr, 'Read graph: {0:.1f} seconds.'.format(timer)

  timer = 0 - time.time()
  ing, g, ing_pos = transformToArray(nodes, ing, g)
  timer += time.time()
  print >> sys.stderr, 'Preprocess graph: {0:.1f} seconds'.format(timer)

  log('Processes: {0}'.format(args.p))
  timer = 0 - time.time() 
  r, t = pageRank(nodes, g, ing, ing_pos, threads=args.p)
  timer += time.time()
  print >> sys.stderr, 'Page Rank: {0:.1f} seconds.'.format(timer)
  for idx, i in enumerate(r):
    print '{0} {1:.10e}'.format(nodes[idx], i)
  print >> sys.stderr, 'Done after {0} iterations.'.format(t)


