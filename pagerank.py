#!/usr/bin/python

import threading
import sys

from array import array

def readGraph(lines):
  g = {} # node number -> out-link counts 
  inG = {} # node number -> set of in-link node numbers
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
    inG.setdefault(v, set()).add(k)
    nodes.add(k)
    nodes.add(v)
  return g, inG, sorted(nodes)

def diffVector(l1, l2, lower=0, higher=0):
  s = 0.0
  i = lower
  higher = len(l1) if not higher else higher
  while i < higher:
    s += abs(l1[i] - l2[i])
    i += 1
  return s

def transformGraph(nodes, inG, g):
  idxInG = {} # instead of storing node number, store index of node -> index of in-nodexs
  idxG = {}
  idx = dict(zip(nodes, range(len(nodes))))
  for node, inNodes in inG.iteritems():
    idxInG[idx[node]] = set([idx[inNode] for inNode in inNodes])
  for node, outDegree in g.iteritems():
    idxG[idx[node]] = outDegree #set([idx[outNode] for outNode in outNodes])
  return idxInG, idxG

def fillVector(r, num, lower=0, higher=0):
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

def iterate(tid, r, r_, g, inG, idx, shared):
  diff = shared['diff'][tid]
  t = 1
  e = shared['e']
  n = shared['n']
  size = shared['size']
  lower = shared['lower'][tid]
  higher = shared['higher'][tid]
  beta = shared['beta']
  log('T{0}: lower={1}, higher={2}'.format(tid, lower, higher))

  while diff > e and (n == -1 or t < n):
    sum_r = 0.0
    # fill in 0s
    fillVector(r_, 0.0, lower, higher)
    j = lower
    while j < higher:
      if j not in inG:
	r_[j] = 0.0
	j += 1
	continue
      rj = 0.0
      iSet = inG[j]
      for i in iSet:
	rj += r[i] / g[i]
      r_[j] = rj # multiply by beta when fixing leak
      sum_r += rj # multiply by beta later
      j += 1
    
    sum_r *= beta
    shared['sum_r'][tid] = sum_r
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


def pageRank(nodes, g, inG, beta=0.8, e=1e-8, n=1e2, threads=4):
  size = len(nodes)
  r = array('d',[1.0/size] * size)
  r_ = array('d',r)
  idx = dict(zip(nodes, range(len(nodes))))
  threadPool = []
  shared = {
      'e': e,
      'n': n,
      'size': size,
      'lower': [0] * threads, 
      'higher': [0] * threads, 
      'beta': beta,
      'sum_r': [0.0] * threads, 
      'children': [None] * threads, 
      'main': threading.Event(),
      'diff': [e + 1] * threads,
      'threads': threads
      }

  for tid in range(threads):
    shared['lower'][tid] = tid * size / threads
    shared['higher'][tid] = (tid + 1) * size / threads
    shared['children'][tid] = threading.Event()
    threadPool.append(threading.Thread(target=iterate, args=(tid, r, r_, g, inG, idx, shared)))
    threadPool[-1].start()
  diff = 1 + e
  t = 1
  while diff > e and (t == -1 or t < n):
    waitForChildren(shared)

    # now to compute the whole sum_r
    sum_r = sum(shared['sum_r'])
    fillVector(shared['sum_r'], sum_r)
    shared['main'].set()

    waitForChildren(shared) 
    diff = sum(shared['diff'])
    fillVector(shared['diff'], diff)

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

  _debug = True
  timer = time.time()
  lines = fileinput.input()
  g, inG, nodes = readGraph(lines)
  print >> sys.stderr, 'Read graph: {0:.1f} seconds.'.format(time.time() - timer)

  timer = 0 - time.time()
  inG, g = transformGraph(nodes, inG, g)
  timer += time.time()
  print >> sys.stderr, 'Preprocess graph: {0:.1f} seconds'.format(timer)

  timer = 0 - time.time() 
  r, t = pageRank(nodes, g, inG, threads=4)
  timer += time.time()
  print >> sys.stderr, 'Page Rank: {0:.1f} seconds.'.format(timer)
  for idx, i in enumerate(r):
    print '{0} {1:.10e}'.format(nodes[idx], i)
  print >> sys.stderr, 'Done after {0} iterations.'.format(t)


