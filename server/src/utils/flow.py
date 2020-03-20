###     flow.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
###     Flow is a class to carry information about a flow's header.  The attributes used in 'match'
###     are carried in the 'vars' dictionary.   We track the identities of switches a flow visits
###     in the list visited, mostly for information.   We don't assume that cycles are detected as part of normal
###     SDN processing, but in makeFlows.py when we are looking for flows that complete we do look for
###     flow headers that get trapped in loops, and these flows are not considered to be viable.
###

import pdb

keepAttributes  = ('dl_type','ip_dscp','nw_dst','nw_proto','nw_src', 'nsrc','ndst', 'ingress_port','visited')

flow_id = 1

class Flow:
    def __init__(self,name,stateDict):
        global flow_id
        self.vars = {}
        self.fid = flow_id
        flow_id += 1
        self.vars.update( stateDict )
        self.visited = []
        self.tagged = False

def cleanUp(flow):
    theseAttribs = list( flow.keys() )
    for attrib in theseAttribs:
        if attrib not in keepAttributes:
            del flow[attrib] 


