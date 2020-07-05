#!/usr/bin/env python3

### makeEvals.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
### Provides interactive interface with user to define a set of evals to be run
### on psa.py.   Takes as input the system description created by findFlows.py,
### and writes out a file describing a set of evals, to be read by psa.py
###

import pdb
import argparse
import sys
import os
import io
import shutil
import json
#from sets import Set
from collections import defaultdict
from .utils.network import buildNetwork

topo_file  = ''
flows_file = ''
rules_file = ''
switch_file = ''
evals_file = ''

n2n = defaultdict(int)
evalsDict = {}
outputDict = {}

def wrapUp(outputDict, evalsDict):
    
    if len(evalsDict):
        outputDict['evaluations'] = evalsDict
        with open(evals_file,'w') as ef:
            ef_str = json.dumps(outputDict, indent=4)
            ef.write(ef_str)

def readFile( fileName, errMessage ):
    try:
        with open(fileName,'r') as f:
            fstr  = f.read()
            fdict = json.loads(fstr)
    except:
        print(errMessage, file=sys.stderr )
        os._exit(1)
    return fdict

def make_flowsTable( flowDict ):
    fips = sorted( flowDict )
    flowsTable = []

    ### pad the end of sips with ''
    residuals = len(fips)%4
    if residuals:
        for sidx in range(0,4-residuals):
            fips.append(' ')

    for idx in range(0,len(fips),4):
        flowsTable.append( '\t\t'.join([fips[idx],fips[idx+1],fips[idx+2],fips[idx+3]]))

    return flowsTable

def mineLinkDefs( topoDict ):

    links = set() 
    for nodeId in topoDict:
        for nbrId in topoDict[ nodeId ]:
            if nodeId < nbrId:
                links.add( (nodeId,nbrId) ) 
            else:
                links.add( (nbrId, nodeId) ) 
 
    linksList = sorted(links) 
    return linksList

def make_linksTable( linkDefs ):
    
    linkTable = []
    linkNames = []

    ### pad the end of sips with ''
    
    for (n1,n2) in linkDefs:
        linkNames.append(n1+'-'+n2)

    residuals = len(linkNames)%4

    if residuals:
        for sidx in range(0,4-residuals):
            linkNames.append(' ')

    for idx in range(0,len(linkNames),4):
        linkTable.append( '\t'.join([linkNames[idx],linkNames[idx+1],\
            linkNames[idx+2],linkNames[idx+3]]))

    if residuals:
        for sidx in range(0,4-residuals):
            linkNames.pop()

    return linkNames, linkTable

### functions to run with Sherpa API

def get_flows_rules(session_path):
    '''
    This corresponds to api "upload"
    Return the flows and links for the evalution user selection
    '''
    # parse session path to get session file to get topoDict and flowDict
    topoDict, flowsDict, switchNodes,_ = parseSession(session_path)
    # then create linkDefs, then create links and flows
    linkDefs = mineLinkDefs(topoDict)

    linkNames, _ = make_linksTable(linkDefs)
    
    return linkNames, flowsDict, switchNodes

def parseSession(session_path,eval_path=''):
    '''
    Modification of parseArgs function to parse session_path file to
    get topoDict and flowsDict
    '''
    global evals_file
    session_file = session_path
    if not os.path.isfile(session_file):
        print('Session file',session_file,'does not exist', file=sys.stderr )
        #### replace with return Error
        os._exit(1)

    session_dict = readFile( session_file, 'Problem reading sessions file '+session_file )

    topo_file = session_dict['topo_file']
    fullTopoDict = readFile( topo_file, 'Problem reading topology file '+topo_file )
    topoDict = fullTopoDict['one_hop_neighbor_nodes']

    rules_file = session_dict['rules_file']
    rulesDict = readFile( rules_file, 'Problem reading rules file '+rules_file)

    flows_file = session_dict['flows_file']
    flowsDict = readFile( flows_file, 'Problem reading flows file '+flows_file)

    switch_file = session_dict['switch_file']
    switchNodes = readFile( switch_file, 'Problem reading switch file'+switch_file)
    
    evals_file = eval_path

    output = {}

    output['session'] = {}
    output['session'].update( session_dict )
    output['session']['session_file'] = session_file
    
    return topoDict, flowsDict, switchNodes, output

def switch2Link(session_path,switch):
    '''
    Given a list of switches, get the list of links that correspond to the
    selected switches
    '''
    links_set = set()
    # parse session path to get session file to get topoDict and flowDict
    _,_, switchNodes,_ = parseSession(session_path)
    for sn in switch:
        links_set.update(switchNodes[sn])
    return list(links_set)

def findPath(flow, links, flowsDict, switchNodes):
    visited_links = []
    flow_desc = flowsDict[flow]
    visited = flow_desc["visited"]
    visit_d = len(visited)
    cur_n = visited[0]
    for i in range(1,visit_d):
        nxt_n = visited[i]
        # add flow to list
        sw_link = switchNodes[cur_n]
        # its either in the form cn-nn or nn-cn, make sure the visited link is in the 
        # user selected links
        if str(cur_n+'-'+nxt_n) in links or str(nxt_n+'-'+cur_n) in links:
            if str(cur_n+'-'+nxt_n) in sw_link:
                visited_links.append(str(cur_n+'-'+nxt_n))
            else:
                visited_links.append(str(nxt_n+'-'+cur_n))
        cur_n = nxt_n

    return visited_links


def make_Eval(session_path,eval_path,flows,links,param=None,type_m=None):
    '''
    This corresponds to 
    Take in user selected flows and rules
    '''
    topoDict, flowsDict,switchNodes ,outputDict = parseSession(session_path,eval_path) 
    #### change for later, when there are multiple evaluations
    evalDic = {}
    if type_m == "link":
        outputDict['parameters'] = param
        for f in flows:
            visited_links = findPath(f, links,flowsDict,switchNodes)
            evalDic[f] = {'links':links,"visited":visited_links}
    elif type_m == "switch":
        outputDict['parameters'] = param
        for f in flows:
            evalDic[f] = {'switches':links,"visited":flowsDict[f]["visited"]}
    elif type_m == "neigh":
        # make sure "hops" is included in the parameters
        outputDict['parameters'] = param
        evalDic['switches'] = links
    else:
        evalDic[1] = {'flows':flows,'links':links}
    wrapUp(outputDict,evalDic)
