#!/usr/bin/python

from array import array
from ctypes import c_double,pointer

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
    g.setdefault(k, set()).add(v)
    #inG.setdefault(v, set()).add(k)
    nodes.add(k)
    nodes.add(v)
  return g, inG, sorted(nodes)

def diff_vector(l1, l2):
  s = 0.0
  i = 0
  size = len(l1)
  while i < size:
    s += abs(l1[i] - l2[i])
    i += 1
  return s

def transformGraph(nodes, inG, g):
  idxInG = {} # instead of storing node number, store index of node -> index of in-nodexs
  idxG = {}
  idx = dict(zip(nodes, range(len(nodes))))
  for node, inNodes in inG.iteritems():
    idxInG[idx[node]] = set([idx[inNode] for inNode in inNodes])
  for node, outNodes in g.iteritems():
    idxG[idx[node]] = set([idx[outNode] for outNode in outNodes])
  return idxInG, idxG

def transformToArray(nodes, inG, g):
  a = array('l')
  idxInG, idxG = transformGraph(nodes, inG, g)
  for i in range(len(nodes)): #[ <size>, <out node list>]
    if i not in idxG:
      a.append(0)
      continue
    outNodes = idxG[i]
    a.append(len(outNodes))
    a.extend(outNodes)
  return idxInG, a


def fillVector(r, num):
  i = 0
  size = len(r)
  while i < size:
    r[i] = num
    i += 1

def forEachElement(r, func):
  i = 0
  size = len(r)
  while i < size:
    r[i] = func(r[i], i)
    i += 1

def pageRank(nodes, g, inG, beta=0.8, e=1e-8, n=1e2):
  
  r = array('d',[1.0/len(nodes)] * len(nodes))
  r_ = array('d', r)

  size = len(nodes)
  gSize = len(g)
  diff = e + 1
  t = 1
  while diff > e and (n == -1 or t < n):
    sum_r = 0.0
    # fill in 0s
    fillVector(r_, 0.0)

    # start iteration
    i = 0
    row_start = 0
    while i < size:
      row_size = g[row_start]
      row_end = row_start + 1
      if row_size:
        score_share = r[i] / row_size 
        sum_r += r[i]
        cursor = row_end # same as row_start + 1
	row_end = cursor + row_size
        while cursor < row_end:
	  r_[ g[cursor] ] += score_share
	  cursor += 1
      row_start = row_end
      i += 1
    
    # multiply by beta
    sum_r = sum_r * beta
    leaked = 1 - sum_r
    leaked_share = leaked / size if leaked > 0 else 0.0
    
    _i = 0
    while _i < size:
      # multiply by beta and fix leak at the same time
      r_[_i] = r_[_i] * beta + leaked_share
      _i +=1
    
    diff = diff_vector(r, r_)
    r, r_ = r_, r
    t += 1
  return r, t
    
if __name__ == '__main__':
  import fileinput
  import sys
  import time
  import os
  
  print >> sys.stderr, 'PID {0}'.format(os.getpid())
  timer = time.time()
  lines = fileinput.input()
  g, inG, nodes = readGraph(lines)
  print >> sys.stderr, 'Read graph: {0:.1f} seconds.'.format(time.time() - timer)

  timer = 0 - time.time()
  inG, g = transformToArray(nodes, inG, g)
  timer += time.time()
  print >> sys.stderr, 'Preprocess graph: {0:.1f} seconds'.format(timer)

  timer = 0 - time.time() 
  r, t = pageRank(nodes, g, inG)
  timer += time.time()
  print >> sys.stderr, 'Page Rank: {0:.1f} seconds.'.format(timer)
  for idx, i in enumerate(r):
    print '{0} {1:.10e}'.format(nodes[idx], i)
  print >> sys.stderr, 'Done after {0} iterations.'.format(t)


