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

from collections    import defaultdict
from utils.network  import buildNetwork
from utils.flow     import Flow
from utils.ipn      import IPValues, inIPFormat
from utils.rule     import RuleNewlySeen, MatchNewlySeen, ActionNewlySeen 
from utils.linkstate import buildLinkState, saveLinkState

### global variables
topo_file  = ''
rules_file = ''
flows_file = ''
evals_file  = ''
output_file = ''
flowsDict = {}
failedToRoute = []
linkState = {}


def resetGlobalVariables():
    global topo_file, rules_file, flows_file, evals_file, output_file, flowsDict, failedToRoute, linkState

    topo_file  = ''
    rules_file = ''
    flows_file = ''
    evals_file  = ''
    output_file = ''
    flowsDict = {}
    failedToRoute = []
    linkState = {}


def parseArgs(cmd_input):
    global topo_file, rules_file, flows_file, evals_file, output_file, discoverFlows, ip_file

    ### if cmd_input is just -is scriptname get the script name
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

    ### the topology files are ones from Boeing topoX_topology.json
    parser.add_argument('-t', metavar='file containing topology', dest='topo', required=True)

    ### the rules files are ones from Boeing topoX_flows.json
    parser.add_argument('-r', metavar='file containing rules', dest='rules',   required=True)

    ### the ips mapping file is one that as of March 16 had to be created by hand from a network
    ### diagram of the topology.   I expect we'll have changes once we have topology or rules
    ### files that embed this mapping
    parser.add_argument('-ips', metavar='file containing node IP mappings', \
            dest='ips',   required=True)

    ### the eval file identifies the flows to track by their name. That name is an index
    ### into a table of flow descriptions, contained in this file
    parser.add_argument('-f', metavar='file containing flows', dest='flows',   required=True)

    ### the eval file has a number of evals, each specifying the links to fail and the
    ### flows to check for impact of those failures.   Each eval is a dictionary with a list
    ### 'links' of links to fail, and a list 'flows' of flows to evaluate after failing the links
    parser.add_argument('-e', metavar='file containing evals', dest='evals', required=True)

    ### the results of these evaluations are added to the evaluation file, by adding the list
    ### 'failed' which identifies the flows which no longer work after the named links are failed
    parser.add_argument('-o', metavar='file containing evaluational output', dest='output', required=True)
        
    args = parser.parse_args(cmdline)
    
    topo_file     = args.topo
    output_file   = args.output

    if not os.path.isfile(topo_file):
        print('Topology file',topo_file,'does not exist', file=sys.stderr)
        os._exit(1)
        
    rules_file = args.rules
    if not os.path.isfile(rules_file):
        print('Switch rules file',rules_file,'does not exist', file=sys.stderr)
        os._exit(1)
        
    flows_file = args.flows
    if flows_file and not os.path.isfile(flows_file):
        print('Flows file',flows_file,'does not exist', file=sys.stderr)
        os._exit(1)
    
    ip_file = args.ips
    if ip_file and not os.path.isfile(ip_file):
        print('IP file',ip_file,'does not exist', file=sys.stderr)
        os._exit(1)
        
    evals_file = args.evals
    if evals_file and not os.path.isfile(evals_file):
        print('Evaluation file',evals_file,'does not exist', file=sys.stderr )
        os._exit(1)

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


def validateFlows( switches, flowIds, flowsDict, linkState, neighborMap ):
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

    failedToRoute = runSingleEvaluation( valExpDict, flowsDict, switches, linkState, neighborMap )


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


### given a description of the flows to test, the links to fail, the network topology (with rules)
### run an evaluation to see which flows do not complete
###
def runSingleEvaluation( evalDict, flowsDict, switches, linkState, neighborMap ):

    ### reset the linkState structure to have only the links to fail in the failed state

    for linkName in linkState:

        ### a link name being in evalDict['links'] means it is one being failed
        if linkName in evalDict['links']:
            linkState[ linkName ] = False
        else:
            ### otherwise it is up
            linkState[ linkName ] = True

    ### push a pointer to the linkState structure down to each switch for reference during routing
    for switchName, switch in switches.items():
        switch.saveLinkState( linkState )

    ### initialize the set of flows that route despite the failures
    routed = set()
    
    ### see impact of failed links on the specified flows
    ###
    for flowName in evalDict['flows']:

        fdict = flowsDict[ flowName ] 

        fdict['ttl'] = 24

        ### the Flow structure copies all the attributes of a flow in the flowsDict
        ### into a 'vars' dictionary in the flow, so references to attributes in the
        ### actual flow being pushed around is through .vars
        ###
        flow     = Flow(flowName, fdict)
        flow.vars['nw_ttl'] = 24

        ### build the first entry point in the path exploration
        src      = fdict['nsrc']
        in_port  = fdict['ingress_port']

        ### to_route will be a stack describing the routing attempts still to be made
        switch = switches[ src ]
        to_route = [ (src, in_port, flow) ]

        while len(to_route) > 0:
            (to_switch, to_port, route_flow) = to_route.pop()

            switch = switches[ to_switch ]
            
            ### see if the flow arrives at destination
            if switch.atDestination( route_flow ):
                failed = False
                break

            ### try to route flow through to_switch using ingress port to_port
            nxt_hop = switch.route( to_port, route_flow )

            ### if nxt_hop is empty the routing failed    
            if not nxt_hop:
                failed = True
                break

            ### nxt_hop is list where each element has form (nxt_flow, portId )
            for (nxt_flow, nxt_port ) in nxt_hop:

                ### nxt_port may not lead to a switch within the network. We can route only those that do
                if nxt_port in switch.nbrs:
                    (nbrSwitchId, nbrPortId) = neighborMap[ to_switch ][nxt_port]
                    to_route.append( (nbrSwitchId, nbrPortId, nxt_flow) )             

        ### save the identities of flows that _did_ get routed.  This because there is multi-cast, perhaps
        ### for redundency, and if any of them gets through it is a save
        ###
        if not failed:
            routed.add( flowName )

    ### return list of flows impacted by the set of link failures

    allFlows = set( evalDict['flows'] )
    return sorted( list( allFlows.difference( routed ) ))

### run each evaluation.  Simple enough, pull off the evaluation description from
### evalsDict and call runSingleEvaluation on it
###
def runEvaluations( evalsDict, flowsDict, switches, linkState, neighborMap ):

    ### results array will be a copy of the incoming evalsDict, with an attribute added that
    ### describes the links which failed, for each evaluation
    ###
    results = {}
    for evalId, evalDict in evalsDict['evaluations'].items():
        ### get list of flows that do not survive the link failures
        failed = runSingleEvaluation( evalDict, flowsDict, switches, linkState, neighborMap )

        ### create the results entry for this evaluation 
        results[ evalId ] = {}
        results[ evalId ].update( evalDict )
        results[ evalId ]['failed'] = failed 

    ### we're done
    return results

def findFlowsToTest( evalDict, flowsDict ):
    ff2test = set()
    for evalNum, eDict in evalDict['evaluations'].items():
        for fId in eDict['flows']:
            if fId not in flowsDict:
                print('evaluation',evalNum,'names flow',fId,'which is not found in the flows file', file=sys.stderr )

            ff2test.add( fId )

    return sorted(list(ff2test))

def sherpa(cmd_list):
    global topo_file, rules_file, flows_file, ip_file, evals_file

    ### to support access through this function call rather than a command line, we'll clear
    ### the global variables in case sherpa was called earlier from within another script
    ###
    resetGlobalVariables()

    parseArgs(cmd_list)

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

    buildLinkState( switches, linkState )

    ### save a pointer to the linkState structure in all the switches
    saveLinkState( switches, linkState ) 

    ### create a data structure that aids in routing 
    neighborMap = makeNeighborMap( switches )

    flowsToTest = findFlowsToTest( evalsDict, flowsDict )

    ### make sure the flows to be tested have what they need to have in their description, and
    ### that without link loss the flows can route
    ###
    validateFlows( switches, flowsToTest, flowsDict, linkState, neighborMap )

    ### the resultsDict just adds to each entry in the evalsDict a new attribute 'failed' which maps to a list
    ### of flow identifiers from the original list that do not survive the link failures
    ###
    resultsDict = runEvaluations( evalsDict, flowsDict, switches, linkState, neighborMap )

    evalsDict['evaluations'] = resultsDict
    if output_file:     

        ### overwrite the 'evaluations' part of evalsDict with the results
        ###

        ### write back the modified evaluations file
        ###
        with open(output_file,'w') as of:
            estr = json.dumps( evalsDict, indent=4 )
            of.write(estr)

    return evalsDict 
        

if __name__ == "__main__":
    sherpa(sys.argv[1:])


