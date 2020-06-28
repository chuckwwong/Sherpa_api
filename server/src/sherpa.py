#!/usr/bin/env python3

### sherpa.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
### Python based SDN flow Evaluation.   Takes a description of an SDN based on formats provided by Boeing
###   and a description of evals (created by user).  A given eval fails a set of specified
### links in the topology and determines for each of a specified number of flows which are possible in that
### topology when failures are not present, which of them is no longer supported by the infrastructure following the
### failures.  The results of each eval (the flows which failed) are written into a file which is a replica
### of the file which describes the eval, save that each eval is augmented with a list of the failing flows.
###


### experim
import pdb
import argparse
import sys
import os
import io
import shutil
import json
import copy
import math

from .                import sherpa_exp
from collections      import defaultdict
from itertools        import combinations
from .utils.network   import buildNetwork
from .utils.ipn       import IPValues, inIPFormat
from .utils.rule      import RuleNewlySeen, MatchNewlySeen, ActionNewlySeen 
from .utils.linkstate import buildLinkState, saveLinkState

### global variables
topo_file  = ''
rules_file = ''
flows_file = ''
ip_file = ''
evals_file  = ''
output_file = ''
switch_file = ''
switchDict = {}
flowsDict = {}
failedToRoute = []


def resetGlobalVariables():
    global topo_file, rules_file, flows_file, ip_file, evals_file, output_file, switch_file
    global switchDict, flowsDict,failedToRoute

    topo_file  = ''
    rules_file = ''
    flows_file = ''
    ip_file = ''
    evals_file  = ''
    output_file = ''
    switch_file = ''
    switchDict = {}
    flowsDict = {}
    failedToRoute = []

def readTopoFile( topo_file ):
    try:
        with open(topo_file,'r') as tf:
            tstr  = tf.read()
            tdict = json.loads(tstr)

    except:
        print('Problem reading topology json file', file=sys.stderr)
        os._exit(1)

    return tdict['one_hop_neighbor_nodes']

def readRulesFile( rules_file ):
    try:
        with open(rules_file,'r') as rf:
            rstr = rf.read()
            rdict = json.loads(rstr)
    except:
        print('Problem reading rules json file', file=sys.stderr )
        os._exit(1)

    return rdict

def readIPFile( ip_file ):
    try:
        with open(ip_file,'r') as ipf:
            ipstr = ipf.read()
            nodeIPs = json.loads(ipstr)
    except:
        print('Problem reading IP json file', file=sys.stderr )
        os._exit(1)

    return nodeIPs

def readFlowsFile( flows_file ): 
    try:
        with open(flows_file,'r') as ff:
            fstr  = ff.read()
            fdict = json.loads(fstr)
    except:
        print('Problem reading flows json file', file=sys.stderr )
        os._exit(1)

    return fdict

def readEvalsFile( evals_file ):
    edict = {}
    try:
        with open(evals_file,'r') as ef:
            estr  = ef.read()
            edict = json.loads(estr)
    except:
        print('Problem reading evaluation json file', file=sys.stderr )
        os._exit(1)

    return edict

def readSwitchFile( switch_file):
    sdict = {}
    try:
        with open(switch_file,'r') as sf:
            sstr  = sf.read()
            sdict = json.loads(sstr)
    except:
        print('Problem reading evaluation json file', file=sys.stderr )
        os._exit(1)

    return sdict

def validateFlows( switches, flowIds, linkState, neighborMap ):
    global failedToRoute
 
    for fId in flowIds:
        flow_desc = flowsDict[ fId ]

        nsrc = flow_desc['nsrc']
        ndst = flow_desc['ndst']
        if 'nw_dst' in flow_desc:
            nw_dst = flow_desc['nw_dst']
        else:
            nw_dst = None

        ### make sure that nsrc and ndst are known nodes
        if nsrc not in switches: 
            print('node', nsrc,'listed in flows but does not appear in topology', file=sys.stderr )
            os._exit(1)

        if ndst not in switches: 
            print('node', dst, 'listed in flows but does not appear in topology', file=sys.stderr )
            os._exit(1)

        ### make sure that if nw_dst exists it is in IP format
        if nw_dst is not None and not inIPFormat( nw_dst ):
            print('nw_dst value', nw_dst,'not recognized as IP address', file=sys.stderr )
            os._exit(1)


    ### try to route each flow
    ###
    valExpDict = {'links':[],'flows': flowIds }

    failedToRoute = sherpa_exp.runSingleEvaluation( valExpDict, switches, linkState, neighborMap )


    if failedToRoute:
        print('the following flows do not route at all', repr(failedToRoute), file=sys.stderr )

### a link between switches is seen by one switch as a particular port id, and by the other switch
### by a potentially different port id.  This function creates a nested dictionary structure which,
### given a switch id and a port number as viewed from that switch is mapped to a tuple describing the
### the switch at the other end and the port id of the link as viewed by that switch.
###
def makeNeighborMap(switches):

    neighborMap = defaultdict(dict)

    for switchId, switch in switches.items():

        for portId, nbrId in switch.nbrs.items():
            nbr = switches[ nbrId ]

            for peerPortId, peerSwitchId in nbr.nbrs.items():
                if peerSwitchId == switchId:
                    neighborMap[ switchId ][ portId ] = ( nbrId, peerPortId )
            
    return neighborMap

def findFlowsToTest( evalDict, type_m = None ):
    ff2test = set()
    if type_m == "link" or type_m == "switch":
        for fName, fDict in evalDict['evaluations'].items():
            if fName not in flowsDict:
                print('evaluation names flow',fName,'which is not found in the flows file', file=sys.stderr )

            ff2test.add( fName )
    elif type_m == "neigh":
        flows = flowsDict.keys()
        for fId in flows:
            ff2test.add(fId)
        '''
        ### in the case where we want to specify select flows impacted by a neigborhood of switch failures
        for sName, sDict in evalDict['evaluations'].items():
            for fId in sDict['flows']:
                if fId not in flowsDict:
                    print('evaluation ',sName,' names flow',fId,'which is not found in the flows file', file=sys.stderr )

                ff2test.add( sName )
        '''
    else:
        for evalNum, eDict in evalDict['evaluations'].items():
            for fId in eDict['flows']:
                if fId not in flowsDict:
                    print('evaluation',evalNum,'names flow',fId,'which is not found in the flows file', file=sys.stderr )

                ff2test.add( fId )

    return sorted(list(ff2test))

def sherpa(eval_path,out_path):
    ## set up the network
    evalsDict, switches, linkState, neighborMap = build_network(eval_path,out_path)

    ### the resultsDict just adds to each entry in the evalsDict a new attribute 'failed' which maps to a list
    ### of flow identifiers from the original list that do not survive the link failures
    ###
    resultsDict = sherpa_exp.runEvaluations( evalsDict, switches, linkState, neighborMap )

    ### overwrite the 'evaluations' part of evalsDict with the results
    ###
    evalsDict['evaluations'] = resultsDict
    
    ### write back the modified evaluations file
    ###
    with open(output_file,'w') as of:
        estr = json.dumps( evalsDict, indent=4 )
        of.write(estr)

    return evalsDict 

def critical_flow(eval_path,out_path,type_m):
    ## set up the network
    evalsDict, switches, linkState, neighborMap = build_network(eval_path,out_path,type_m)

    results = {}
    ## generate evals from evalDict to run on sherpa
    evaluations = sherpa_exp.make_eval_link(evalsDict,type_m)
    print(evaluations)
    ## generate probabilities and run experiment
    for flowName, combinations in evaluations.items():
        probability, bound = sherpa_exp.calculate_metric([flowName],combinations,evalsDict,switches,linkState,neighborMap)
        #print(probability,bound)
        ## compile it all together
        if bound != None:
            result = {'probability':probability,"uppper bound":bound}
        else:
            result = {'probability':probability}
        results[flowName] = {}
        results[flowName].update( evalsDict['evaluations'][flowName])
        results[flowName]['result'] = result

    ### overwrite the 'evaluations' part of evalsDict with the results
    ###
    evalsDict['evaluations'] = results

    ### write back the modified evaluations file
    ###
    with open(output_file,'w') as of:
        estr = json.dumps( evalsDict, indent=4 )
        of.write(estr)

    return evalsDict

def critical_flow_neigh(eval_path,out_path):
    ## set up the network
    evalsDict, switches, linkState, neighborMap = build_network(eval_path,out_path,"neigh")

    results = {}
    # generate evals from evalDict to run on sherpa
    evaluations = sherpa_exp.make_eval_neigh(evalsDict)
    #print(evaluations)
    ## generate probabilities and run experiment
    for switch, dict_fl in evaluations.items():
        probability, bound = sherpa_exp.calculate_metric(dict_fl['flows'],[dict_fl['links']],evalsDict,switches,linkState,neighborMap)

        if bound != None:
            result = {'probability':probability,"uppper bound":bound}
        else:
            result = {'probability':probability}
        results[switch] = {'result': result}

    ### overwrite the 'evaluations' part of evalsDict with the results
    ###
    evalsDict['evaluations'] = results

    ### write back the modified evaluations file
    ###
    with open(output_file,'w') as of:
        estr = json.dumps( evalsDict, indent=4 )
        of.write(estr)

    return evalsDict


### functions to initialize the Sherpa api
def build_network(eval_path,out_path,type_m=None):
    global topo_file, rules_file, flows_file, ip_file, evals_file, switch_file
    global flowsDict, switchDict

    resetGlobalVariables()
    
    parseArgs_exp(eval_path,out_path)

    ### if the evaluation file has a 'session' block, that block contains file path descriptors
    ### for the topology, rules, ip addresses, and flows. Use these if present, but report
    ### variation from those placed on the command line
    ###
    evalsDict  = readEvalsFile( evals_file )
    if 'session' in evalsDict:
        sessionDict = evalsDict['session']
        if topo_file != sessionDict['topo_file']:
            print('topology file in evaluation\'s session block', sessionDict['topo_file'],'varies from command line', \
                topo_file, file=sys.stderr )
            print('\t Using path-name from session block', file=sys.stderr )
            topo_file = sessionDict['topo_file']

        if rules_file != sessionDict['rules_file']:
            print('rules file in evaluation\'s session block', sessionDict['rules_file'],'varies from command line', \
                rules_file, file=sys.stderr )
            print('\t Using path-name from session block', file=sys.stderr )
            rules_file = sessionDict['rules_file']

        if ip_file != sessionDict['ip_file']:
            print('ip mapping file in evaluation\'s session block', sessionDict['ip_file'],'varies from command line', \
                ip_file, file=sys.stderr )
            print('\t Using path-name from session block', file=sys.stderr )
            ip_file = sessionDict['ips_file']

        if flows_file != sessionDict['flows_file']:
            print('flows file in evaluation\'s session block', sessionDict['flows_file'],'varies from command line', \
                flows_file, file=sys.stderr )
            print('\t Using path-name from session block', file=sys.stderr )
            flows_file = sessionDict['flows_file']

    ### topology dictionary is index by node id (e.g. 'n17') with value equal to a list of other 
    ### node ids of neighbors, where we assume that the order in the list corresponds to port numbers
    ### 1, 2, and so on
    topoDict  = readTopoFile( topo_file )

    ### rules file has one key 'nodes', which leads to a dictionary indexed by node id (e.g. 'n17')
    ### which leads to a dictionary with a mysterious single key which is a numerical code of some kind,
    ### which leads to a list of dictionaries, each of which describes a rule
    rulesDict = readRulesFile( rules_file )

    ### the ip file describes IP addresses associated with the switches.  The dictionary is
    ### indexed by the node id, maps to a list of CIDR addresses
    ###
    nodeIPs   = readIPFile( ip_file )

    ### the format of a flows file is a dictionary indexed by a code for a flow 
    ### comprised of srcId-dstId-number, where srcId is the id of the node which is the source,
    ### dstId is the id of the node which is the destination, and number is a uniqifier to allow for 
    ### multiple distinct flows.   The value associated with a flow id is a flow dictionary
    ### described by makeFlow.py:
    ###
    ### return { 'nsrc':nsrc, 'in_port':in_port, 'ndst':ndst,'dl_type':dl_type,\
    ###            'ip_dscp':ip_dscp,'nw_dst':nw_dst, 'ttl':ttl }
    ###
    ### nsrc     = node id of flow source
    ### ndst     = node id of flow destination
    ### in_port  = identify of ingress port of nsrc where the flow enters
    ### dl_type  = seems to be a code describing the communication mechanism, I've seen only 2048 as a value
    ### ip_dscp  = a code reflecting priority level, I think
    ### nw_dst   = IP address at destination
    ### ttl      = time-to-live counter, decremented on passage through switch if so directed. Flow stops when
    ###              counter expires to zero
    flowsDict = readFlowsFile( flows_file )

    ### this sets the _global_ variable switchDict to hold a dicitonary of switches in the network
    ### that maps the switch node as the keys to the list of links connected to that switch as the value
    switchDict = readSwitchFile( switch_file)

    ### switches is a dictionary indexed by switch (node) id, each mapped to a dictionary
    ### whose integer keys are port numbers and whose value for a port number is the node identity
    ### of a neighbor
    ###
    switches = buildNetwork(topoDict, rulesDict, nodeIPs )

    ### the parsing of the topo and rules files may encounter attributes in the rules that we have not seen
    ### before.   These should be flagged for the developer to include in the code
    ###   sets RuleNewlySeen, MatchNewlySeen and ActionNewlySeen are modified in utils/rule.py when
    ### these new attributes are discovered
    ###
    newAttributes = False
    if RuleNewlySeen:
        print('unknown rule attributes seen in configuration, report to developer', repr(RuleNewlySeen),\
            file = sys.stderr)
        newAttributes = True

    if MatchNewlySeen:
        print('unknown match attributes seen in configuration, report to developer', repr(MatchNewlySeen),\
            file = sys.stderr)
        newAttributes = True

    if ActionNewlySeen:
        print('unknown action attributes seen in configuration, report to developer', repr(ActionNewlySeen),\
            file = sys.stderr )
        newAttributes = True

    if newAttributes:
        os._exit(1)

    linkState = {}
    buildLinkState( switches, linkState )

    ### save a pointer to the linkState structure in all the switches
    saveLinkState( switches, linkState ) 

    ### create a data structure that aids in routing 
    neighborMap = makeNeighborMap( switches )

    flowsToTest = findFlowsToTest( evalsDict,type_m=type_m)

    ### make sure the flows to be tested have what they need to have in their description, and
    ### that without link loss the flows can route
    ###
    validateFlows( switches, flowsToTest, linkState, neighborMap )

    return evalsDict, switches, linkState, neighborMap

def parseArgs_exp(eval_path,out_path):
    global output_file, evals_file, topo_file, rules_file, flows_file, ip_file, switch_file
    output_file = out_path
    evals_file = eval_path
    with open(eval_path,'r') as ep:
        eval_args = json.load(ep)
        sessionDict = eval_args['session']
        topo_file = sessionDict['topo_file']
        rules_file = sessionDict['rules_file']
        flows_file = sessionDict['flows_file']
        ip_file = sessionDict['ip_file']
        switch_file = sessionDict['switch_file']

### backend calls these functions to run experiments
def run_exp(eval_path,out_path):
    '''
    Run SDN flow evaluation given eval json
    '''
    # run a modified parseArgs
    # then run sherpa function
    sherpa(eval_path,out_path)

def run_critf(eval_path,out_path,type_m="link"):
    '''
    Run evaluation for case 1, modified case 1, and modified case 3
    '''
    if type_m == "neigh":
        critical_flow_neigh(eval_path,out_path) 
    else:
        critical_flow(eval_path,out_path,type_m)
