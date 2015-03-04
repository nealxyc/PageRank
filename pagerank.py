#!/usr/bin/python

def readGraph(lines):
  g = {} # node number -> out-link counts 
  inG = {} # node number -> set of in-link node numbers
  nodes = set() # all nodes
  for line in lines:
    line = line.strip()
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

def vectorMinus(l1, l2, sign=-1):
  if len(l1) != len(l2):
    raise Exception('Adding two vectors with different length! {0} and {1}'.format(len(l1), len(l2)))
  return [l1[i] + sign * l2[i] for i in range((len(l1)))]  

def vectorAdd(l1, l2):
  return vectorMinus(l1, l2, 1)

def sumAbs(l):
  return sum([abs(i) for i in l])

def pageRank(nodes, g, inG, beta=0.8, e=1e-8, n=1e3):
  r = [1.0/len(nodes)] * len(nodes)
  #r = dict(zip(nodes, [1.0/len(nodes)] * len(nodes)))
  r_ = list(r)
  #r_ = {}
  diff = e + 1
  t = 1
  idx = dict(zip(nodes, range(len(nodes)))) # maps node number -> array index
  while diff > e and (n == -1 or t < n):
    iterate(r, r_, beta, nodes, g, inG, idx)
    diff = sumAbs(vectorMinus(r, r_))
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


