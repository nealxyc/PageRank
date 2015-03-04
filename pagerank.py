#!/usr/bin/python

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
    g.setdefault(k, 0)
    g[k] += 1
    inG.setdefault(v, set()).add(k)
    nodes.add(k)
    nodes.add(v)
  return g, inG, sorted(nodes)

def diffVector(l1, l2,rang):
  return sum([abs(l1[i] - l2[i]) for i in rang])

def transformGraph(nodes, inG, g):
  idxInG = {} # instead of storing node number, store index of node -> index of in-nodexs
  idxG = {}
  idx = dict(zip(nodes, range(len(nodes))))
  for node, inNodes in inG.iteritems():
    idxInG[idx[node]] = set([idx[inNode] for inNode in inNodes])
  for node, outdegree in g.iteritems():
    idxG[idx[node]] = outdegree
  return idxInG, idxG

def pageRank(nodes, g, inG, beta=0.8, e=1e-8, n=1e3):
  r = array('f',[1.0/len(nodes)] * len(nodes))
  r_ = array('f', r)
  rang = array('l', range(len(r)))
  diff = e + 1
  t = 1
  while diff > e and (n == -1 or t < n):
    sum_r = 0.0
    for j in rang:
      rj = 0.0
      if j in inG:
	for i in inG[j]:
	  rj += r[i]/g[i]
	r_[j] = beta * rj
	sum_r += r_[j] 
      else:
	r_[j] = 0.0
    leaked = 1 - sum_r
    if leaked > 0:
      incre = leaked/len(r_)
      for _i in rang:
	r_[_i] += incre
    diff = diffVector(r, r_, rang)
    r, r_ = r_, r
    t += 1
  return r, t
    
if __name__ == '__main__':
  import fileinput
  import sys
  import time
  
  timer = time.time()
  lines = fileinput.input()
  g, inG, nodes = readGraph(lines)
  print >> sys.stderr, 'Read graph: {0:.1f} seconds.'.format(time.time() - timer)

  timer = 0 - time.time()
  idxInG, idxG = transformGraph(nodes, inG, g)
  timer += time.time()
  print >> sys.stderr, 'Preprocess graph: {0:.1f} seconds'.format(timer)

  timer = 0 - time.time() 
  r, t = pageRank(nodes, idxG, idxInG)
  timer += time.time()
  print >> sys.stderr, 'Page Rank: {0:.1f} seconds.'.format(timer)
  for idx, i in enumerate(r):
    print nodes[idx], i
  print >> sys.stderr, 'Done after {0} iterations.'.format(t)


