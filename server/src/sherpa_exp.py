#!/usr/bin/env python3

### sherpa_exp.py
###     release date: June 19, 2020
###     author: Chuck Wong
###     contact: cwwong3@illinois.edu
###
### Python based SDN flow Evaluation.   Helper functions to run evaluation metrics on SDN based on formats provided
###   by Boeing and evals (created by user). All functions that run evaluations or calculate probabilitist metrics 
### are stored here. This subfile uses the global variables flowsDict and switchDict provided from sherpa.py.
###

import pdb
import argparse
import sys
import os
import io
import shutil
import json
import copy
import math

from .                import sherpa
from collections      import defaultdict
from itertools        import combinations
from .utils.network   import buildNetwork
from .utils.flow      import Flow
from .utils.ipn       import IPValues, inIPFormat
from .utils.rule      import RuleNewlySeen, MatchNewlySeen, ActionNewlySeen 
from .utils.linkstate import buildLinkState, saveLinkState

### given a description of the flows to test, the links to fail, the network topology (with rules)
### run an evaluation to see which flows do not complete
###
def runSingleEvaluation( evalDict, switches, linkState, neighborMap ):

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

        fdict = sherpa.flowsDict[ flowName ] 

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
def runEvaluations( evalsDict, switches, linkState, neighborMap ):

    ### results array will be a copy of the incoming evalsDict, with an attribute added that
    ### describes the links which failed, for each evaluation
    ###
    results = {}
    for evalId, evalDict in evalsDict['evaluations'].items():
        ### get list of flows that do not survive the link failures
        failed = runSingleEvaluation( evalDict, switches, linkState, neighborMap )

        ### create the results entry for this evaluation 
        results[ evalId ] = {}
        results[ evalId ].update( evalDict )
        results[ evalId ]['failed'] = failed 

    ### we're done
    return results

# lambda function to calculate combination
nCr = lambda n,r: math.factorial(n)/(math.factorial(n-r)*math.factorial(r))

def calculate_metric(flows,evals, evalsDict, switches, linkState, neighborMap):
    '''
    Here we are calculating the probability the flow Fj fails due to link failure.
    We need to calculate the probability m links fail (p_x) which can be modeled by
    a Poisson distribution, and the probability Fj fails due to m links failing (p_m).
    Input:
        flows:   - An array that holds the flow Fj or flows F to calculate the metric on
        evals:  - An array, where each element (i) holds a list of all unique sets of links of size
                  (i+1).
    Output:
        probability_t: - the metric, which is Sum(i from 1 to L) p_m[i]*p_x[i]
    '''
    probability_t = 0
    probability_e = 0
    params = evalsDict["parameters"]
    tolerance = float(params["tolerance"])
    f_r = float(params["failure_rate"])
    time = int(params["time"])

    L = len(evals)

    for i, link_c in enumerate(evals):
        # calculate probability f fails given i+1 links fail in time T
        p_m = 0
        for comb in link_c:
            eDict = {"flows":flows,"links":comb}
            fail = runSingleEvaluation(eDict,switches,linkState,neighborMap)
            ## dividing by the number of flows is for neighboring switch failure metric
            p_m += len(fail)/len(flows)
        p_m = p_m/nCr(L,i+1)

        # calculate probability that i links fail in time T with Poisson distribution
        # not sure if I should include Time
        p_x = (f_r*time)**(i+1) * math.exp(-f_r*time)/math.factorial(i+1)

        probability_e += p_x
        #print("p_e",(1-probability_e),"p_t",(tolerance*(probability_t+p_m*p_x)))
        if (1- probability_e) < tolerance * (probability_t + p_m*p_x):
            bound = i+1
            return probability_t, bound
        else:
            probability_t += p_m*p_x

    return probability_t, None

def neighToLinks(switch,hops):
    def get_neighbors(switch):
        switches = []
        links = sherpa.switchDict[switch]
        for link in links:
            # parse link and find the neighbor
            sw_pair = link.split('-',1)
            if sw_pair[0] == switch:
                switches.append(sw_pair[1])
            else:
                switches.append(sw_pair[0])
        # return the list
        return switches

    def find_k_neighbors(switch,visited,k):
        '''
        Recursive function to find all switches k hops 
        away from source switch. Worst case runtime is
        O(n*m), where n is nodes and m is edges.
        '''
        #print(switch,visited,k)
        if k == 0:
            return visited

        if switch not in visited:
            visited.add(switch)

        if sherpa.switchDict[switch] == []:
            return visited

        for neigh in get_neighbors(switch):
            if neigh not in visited:
                visited.add(neigh)
                visited.update(find_k_neighbors(neigh,visited,k-1))
        return visited

    explored = find_k_neighbors(switch,{switch},hops)
    #print(explored)
    return switchToLinks(list(explored))

def switchToLinks(switches):
    links = set()
    for s in switches:
        links.update(sherpa.switchDict[s])
    return list(links)

def make_eval_neigh(evalsDict,hops=0):
    # get all flows as a list
    flows = list(sherpa.flowsDict.keys())
    
    switch_evals = {}

    hops = evalsDict['parameters']['hops']
    eval_dict = evalsDict['evaluations']

    for switchName in eval_dict['switches']:
        # compile affected switches in number of hops and convert it to links
        links_affected = neighToLinks(switchName,hops)
        # create flow and link dictionary for metric calculation
        switch_evals[switchName] = {"flows":flows,"links":links_affected}
    return switch_evals

def make_eval_switch(evalsDict):
    '''
    This takes in the evaluation dictionary and finds all unique
    combinations of links from sets of 1 to sets of number of total links selected
    and each set has at least one link that the flow goes through

    The output flow_evals is a dictionary that maps the user selected flow to 
    a list of evaluations, each element in the list is a list of combination of links
    all with the length index of the evaluation.
    '''
    # uses global variables flowDict and switchDict
    flow_evals = {}
    for flowName, evalDict in evalsDict['evaluations'].items():
        evaluations = []
        f_visited = sherpa.flowsDict[flowName]["visited"]
        visited = [v for v in f_visited if v in evalDict["switches"]]
        # if the switches that will be failing don't include switches that the flow uses
        # there's no point in running evaluation
        if not visited:
            # evaluations corresponding to this flow is empty, signifying 0 probability of failing
            continue
        else:
            switches = evalDict["switches"]
            for i in range(1,len(switches)+1):
                # link_comb is list of all unique combinations of flows of length i
                sw_comb = []
                sw_set = set(switches)
                # find all combinations of unique link pairs with at least one visited link
                for v in visited:
                    # take out the node from visited
                    sw_set.remove(v)
                    # out of L-h Choose i - 1, for h in V, i-1, since v will be added in
                    unique = combinations(sw_set,i-1)
                    for su in list(unique):
                        combin = list(su)
                        # add in the visited link back into the unique combination
                        combin.append(v)
                        # here is where the switches are converted to links (not in this function)
                        combin = switchToLinks(combin)
                        sw_comb.append(combin)
                evaluations.append(sw_comb)
        flow_evals[flowName] = evaluations
    return flow_evals

def make_eval_link(evalsDict, type_m="link"):
    '''
    This takes in the evaluation dictionary and finds all unique
    combinations of links from sets of 1 to sets of number of total links selected
    and each set has at least one link that the flow goes through

    The output flow_evals is a dictionary that maps the user selected flow to 
    a list of evaluations, each element in the list is a list of combination of links
    all with the length index of the evaluation.
    '''
    # uses global variables flowDict and switchDict
    flow_evals = {}
    for flowName, evalDict in evalsDict['evaluations'].items():
        evaluations = []
        # pull links/switches to fail during the test that the flow visits 
        if type_m == "switch":
            f_visited = sherpa.flowsDict[flowName]["visited"]
            visited = [v for v in f_visited if v in evalDict["switches"]]
        else:
            visited = evalDict["visited"]

        # if the links that will be failing don't include links that the flow uses
        # there's no point in running evaluation
        if not visited:
            # evaluations corresponding to this flow is empty, signifying 0 probability of failing
            continue
        else:
            if type_m == "switch":
                links = evalDict["switches"]
            else:
                links = evalDict["links"]

            for i in range(1,len(links)+1):
                # link_comb is list of all unique combinations of flows of length i
                link_comb = []
                lk_set = set(links)
                # find all combinations of unique link pairs with at least one visited link
                for v in visited:
                    # take out the node from visited
                    lk_set.remove(v)
                    # out of L-h Choose i - 1, for h in V, i-1, since v will be added in
                    unique = combinations(lk_set,i-1)
                    for lu in list(unique):
                        combin = list(lu)
                        # add in the visited link back into the unique combination
                        combin.append(v)
                        # here is where the switches are converted to links
                        if type_m == "switch":
                            combin = switchToLinks(combin)
                        link_comb.append(combin)
                evaluations.append(link_comb)
        flow_evals[flowName] = evaluations
    return flow_evals
