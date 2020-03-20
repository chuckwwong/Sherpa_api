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
from collections import defaultdict
from utils.network import buildNetwork

topo_file  = ''
flows_file = ''
rules_file = ''
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

def parseArgs(cmd_input):
    global outputDict, evals_file

    ### if cmd_input is just -cmd scriptname get the script name
    ### This file will be openek and the (single) line found within will be 
    ### used just as though it were typed on the command line and is passed to the command line parser
    ###
    cmdline = cmd_input
    if cmd_input[0] == '-cmd':
        try:
            with open(cmd_input[1],'r') as cf:
                cmd = cf.readline()
                cmd.strip()
                cmdline = cmd.split()
        except:
            print('unable to open command script file', cmd_input[1], file=sys.stderr)
            os._exit(1)
 
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', metavar='file containing topology/rules/flows session information', dest='session', required=True)
    parser.add_argument('-o', metavar='evals description output', dest='evals', \
            required=True)
        
    args = parser.parse_args(cmdline)

    session_file = args.session
    if not os.path.isfile(session_file):
        print('Session file',session_file,'does not exist', file=sys.stderr )
        os._exit(1)

    session_dict = readFile( session_file, 'Problem reading sessions file '+session_file )

    topo_file = session_dict['topo_file']
    fullTopoDict = readFile( topo_file, 'Problem reading topology file '+topo_file )
    topoDict = fullTopoDict['one_hop_neighbor_nodes']

    rules_file = session_dict['rules_file']
    rulesDict = readFile( rules_file, 'Problem reading rules file '+rules_file)

    flows_file = session_dict['flows_file']
    flowsDict = readFile( flows_file, 'Problem reading flows file '+flows_file)

    evals_file = args.evals

    outputDict['session'] = {}
    outputDict['session'].update( session_dict )
    outputDict['session']['session_file'] = session_file
    return topoDict, flowsDict

def readFile( fileName, errMessage ):
    try:
        with open(fileName,'r') as f:
            fstr  = f.read()
            fdict = json.loads(fstr)
    except:
        print(errMessage, file=sys.stderr )
        os._exit(1)
    return fdict


def listTerms(flowsTable, linksTable):
    print('flow names')
    for idx in range(0,len(flowsTable)):
        print('\t', flowsTable[idx])
    
    print('link names')
    for idx in range(0,len(linksTable)):
        print('\t', linksTable[idx])
   

def displayFlow( fdict ):
    fstr = json.dumps( fdict, indent=4 ) 
    print(fstr)


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


def makeEvals( flowDict, linkDefs ):
    flowsTable             = make_flowsTable( list( flowDict.keys() ))
    linkNames, linksTable  = make_linksTable( linkDefs )
   
    eDict = {}
    evalNumber = 1

    done = False
    while not done:
        ans = input('Create another evaluation? > ' )
        if ans in ('yes','1','Yes','y','YES'):
            oneEval = makeOneEval( flowDict, linkNames, flowsTable, linksTable )
            eDict[evalNumber] = oneEval
            evalNumber += 1
        else:
            done = True

    return eDict

def showFlowList( flowSet ):
    flist = sorted(list(flowSet))
    fstr  = 'selected flows = [' +','.join(flist)+']'
    print( fstr, flush=True )

def showLinkList( linkSet ):
    llist = sorted(list(linkSet))
    lstr  = 'selected links = [' +','.join(llist)+']'
    print (lstr, flush=True )

def makeOneEval( flowsDict, linkNames, flowsTable, linksTable ):
    global topo_file, rules_file, flows_file

    listTerms(flowsTable, linksTable)

    doFlows = set()
    doLinks = set()

    done = False
    print('enter \'cmds\' for list of commands')
    while not done:
        ans = input('> ')
        if ans.find('cmd') > -1:
            print('list, flow [flowname], link [linkname], display [flowname], show, remove, done')
            continue

        if ans.find('list') > -1:
            listTerms(flowsTable, linksTable)
            print('\n') 
            continue

        if ans.find('flow') > -1:
            here = ans.find('flow')+len('flow')
            flowName = ans[here+1:]
            flowName = flowName.replace(' ','')
            flowName = flowName.replace('[','')
            flowName = flowName.replace(']','')

            ### possible to include a comma-separated list of flows
            flows = flowName.split(',')
            bufferFlows = set()
            unrecognized = set()

            for flow in flows:
                if flow in flowsDict:
                    bufferFlows.add(flow)
                else:
                    unrecognized.add(flow)

            if bufferFlows:
                doFlows = doFlows.union( bufferFlows )

            if unrecognized:
                print(list(unrecognized),'not found in list of flows')
                continue
            
            continue

        if ans.find('display') > -1:
            cmd,flowName = ans.split()
            flowName = flowName.strip()
            if not flowName in flowsDict:
                print(flowName,'not found in list of flows')
                continue
            
            fstr = json.dumps( flowsDict[flowName], indent = 4)
            print(fstr)
            continue

        if ans.find('link') > -1:
            here = ans.find('link')+len('link')
            linkName = ans[here+1:]
            linkName = linkName.replace(' ','')
            linkName = linkName.replace('[','')
            linkName = linkName.replace(']','')

            ### possible to include a comma-separated list of links 
            links = linkName.split(',')
            bufferLinks = set()
            unrecognized = set()

            for link in links:
                if link in linkNames:
                    bufferLinks.add(link)
                else:
                    if link.find('-') > -1:
                        try:
                            end1,end2 = link.split('-')
                            test = end2+'-'+end2
                            if not test in linkNames:
                                unrecognized.add(link)
                            else:
                                bufferLinks.add(test) 
                        except:
                            unrecognized.add(link)

            if bufferLinks:
                doLinks = doLinks.union( bufferLinks )

            if unrecognized:
                print(list(unrecognized),'not found in list of links')
                continue
            
            continue

        if ans.find('show') > -1:
            showFlowList( doFlows )
            showLinkList( doLinks)
            continue

        if ans.find('remove') > -1 or ans.find('rm') > -1:
            try:
                cmd, ans = ans.split()
            except:
                print('do not recognize remove argument as a link or flow name')
                continue
 
            ans = ans.strip()
            if ans in doFlows:
                doFlows.discard( ans )
                showFlowList( doFlows )

            elif ans in doLinks:
                doLinks.discard( ans )
                showLinkList( doLinks )
            else:
                print(ans,'not found as name for either flow nor link')
            continue 

        if ans.find('done') > -1:
            done = True
            break

        print('command', ans,'not recognized. Recognized commands are')
        print('list, flow [flowname], link [linkname], display [flowname], done')
    
    flows = sorted( list(doFlows) )
    links = sorted( list(doLinks) )
    if not flows or not links:
        print('no flows or no links given.  Eavluation skipped')
        return {} 
    return {'flows':flows, 'links':links }

def main():

    topoDict, flowDict = parseArgs(sys.argv[1:])

    linkDefs  = mineLinkDefs( topoDict )

    flowNames = list(flowDict.keys())

    evalsDict = makeEvals( flowDict, linkDefs )

    wrapUp(outputDict, evalsDict )

if __name__ == "__main__":
    main()


