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

def pageRank(nodes, g, inG, beta=0.8, e=1e-8, n=1e3):
  r = array('f',[1.0/len(nodes)] * len(nodes))
  r_ = array('f', r)
  rang = array('l', range(len(r)))
  diff = e + 1
  t = 1
  idx = dict(zip(nodes, rang)) # maps node number -> array index
  while diff > e and (n == -1 or t < n):
    sum_r = 0.0
    for _i in rang:
      j = nodes[_i]
      r_[_i] = beta * sum([r[idx[i]]/g[i] for i in inG[j]]) if j in inG else 0.0
      sum_r += r_[_i]
    leaked = 1 - sum_r
    if leaked > 0:
      incre = leaked/len(r_)
      for _i in rang:
	r_[_i] += incre
    diff = diffVector(r, r_, rang)
    r, r_ = r_, r
    t += 1
  return r, t
    
def iterate(r, r_, beta, nodes,  g, inG, idx):
  for _i, j in enumerate(nodes):
    r_[_i] = beta * sum([r[idx[i]]/g[i] for i in inG[j]]) if j in inG else 0.0
#  r_ = [beta*sum([r[idx[i]]/g[i]) for i in inG[j]]) if j in inG else 0.0 for j in nodes]
  leaked = 1 - sum(r_)
  if leaked > 0:
    incre = leaked/len(r_)
    for _i in range(len(r_)):
      r_[_i] += incre
  return r_

if __name__ == '__main__':
  import fileinput
  import sys
  import time
  
  timer = time.time()
  lines = fileinput.input()
  g, inG, nodes = readGraph(lines)
  print >> sys.stderr, 'Read graph: {0} seconds.'.format(time.time() - timer)
  print >> sys.stderr, 'Read {0} nodes in graph'.format(len(nodes))
  timer = 0 - time.time() 
  r, t = pageRank(nodes, g, inG)
  timer += time.time()
  print >> sys.stderr, 'Page Rank: {0} seconds.'.format(timer)
  for idx, i in enumerate(r):
    print nodes[idx], i
  print >> sys.stderr, 'Done after {0} iterations.'.format(t)


