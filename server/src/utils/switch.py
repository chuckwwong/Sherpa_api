###     switch.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
###     The Switch class holds information about a network switch, namely
###         - its name
###         - a dictionary, indexed by (local) port number, of neighbors reached through the indexing port
###         - tables, a list of list of rule tables.  So far we have only one table
###         - cidr, a list of pairs of integer ranges corresponding to IP ranges seemingly associated with a switch
###
###     Switch has method 'atDestination' which determines whether the nw_dst value in the flow header
###       is contained within one of the switches IP ranges.
###
###     Switch has method 'route' which accepts a flow header and returns a list of local ports through which the
###         packet is to be pushed.  In concept there might be more than one if an OUTPUT action specifies a broadcast
###         multi-cast.  We have not seen such, but have written the code to be prepared for the possiblity.  If the list
###         is empty, the flow does not route.
###
###     Switch has method 'discoverFlows' which is used to find viable flows.  It is like route, except that it looks
###      for loops in the paths and rejects evolving paths that encounter them
###
from collections import defaultdict
from .rule import Rule
from .ipn import IPValues, Int2IP

import copy
import pdb

class Switch:
    def __init__(self,name,nbrs,rules, nodeIPs):
        self.name   = name
        self.nbrs   = nbrs
        self.tables = []
        self.cidr   = nodeIPs 
        
        ### only attribute of node following name is an integer valued string we'll take for
        ### a code

        switchCodes = list( rules.keys() )
        if len(switchCodes) != 1:
            print('problem')
            os._exit(1)

        self.code = switchCodes[0]
        rlist = rules[ self.code ]

        for rdict in rlist:
            rule = Rule( self, rdict )

            ### make sure there is a table list
            table_id = rule.table_id         
            while len(self.tables) < table_id+1:
                self.tables.append([])
        
            ### append the rule to the end of the proper table
            self.tables[ table_id ].append(rule)

    def saveLinkState(self, linkState):
        self.linkState = linkState

    ### see if the link between self and nbr accessable through portId is up
    ###
    def checkLinkState(self, portId ):

        ### we've see the action to route through a non-existent port. Nope.
        if portId not in self.nbrs:
            return False

        nbr = self.nbrs[ portId ]
        linkName = self.name+'-'+nbr if self.name < nbr else nbr+'-'+self.name
        return self.linkState[ linkName ]

    ### the flow is considered to have arrived if the destination is contained in any of the 
    ### CIDR addresses associated with the switch
    ###
    def atDestination(self, flow):
        
        flowLow, flowHigh = IPValues( flow.vars['nw_dst'] )
        for low, high in self.cidr:
            if low <= flowLow and flowHigh <= high:
               return True

        return False  

    ### try to route a flow entering the switch on input port in_port.  Return
    ### either None (not routed) or next nbr 
    ###
    def route(self, in_port, flow ):
        flow.vars['in_port'] = in_port

        ### go through list of rules in table[0] and look for routing actions
        ###
        for rule in self.tables[0]:

            nbrs = rule.matchAndAction(flow)

            ### if nbrs is not None we found a match
            if nbrs:
                break

        ### either went through the loop without a match (or expired TTL), or found a port to go through
        ### 
        moveIt = []
        if nbrs is not None:

            # pass along the flow and the identify of the port through which it passes for the next hop
            moveIt.append( (flow, nbrs[0]) )
 
            for idx in range(1,len(nbrs)):
                newFlow = copy.deepcopy( flow )
                moveIt.append( (newFlow, nbrs[idx]) )

        return moveIt 

    def discoverFlows(self, flow, port, switches, neighborMap):

        discoveries = []

        flow.visited.append( self.name )

        if self.atDestination( flow ):
            flow.vars['ndst'] = self.name 
            return [flow]


        toRoute = self.route( port, flow )

        if not toRoute:
            return []

        failures = 0
        for (flow, portId) in toRoute:
            if portId not in neighborMap[ self.name ]:
                failures += 1
                continue
            ### find the port number of the next switches connection to self
            ###
            (nbrId, nbrPort) = neighborMap[ self.name ][ portId ]

            ### if we've already visited nbrId don't circle back
            ###
            if nbrId in flow.visited:
                failures += 1
                continue

        if failures == len(toRoute) and flow.tagged:
            print('\t', repr(flow.visited),'dropped because all routes exit network or loop back',\
                file = sys.stdout )
            return []

        for (flow, portId) in toRoute:
           
            ### portId might not map to a neighbor so it is routed off to no-where
            ###
            if portId not in neighborMap[ self.name ]:
                continue
 
            ### find the port number of the next switches connection to self
            ###
            (nbrId, nbrPort) = neighborMap[ self.name ][ portId ]

            ### if we've already visited nbrId don't circle back
            ###
            if nbrId in flow.visited:
                #print('warning...loop detected')
                continue

            nbr              = switches[ nbrId ]
            routed           = nbr.discoverFlows( flow, nbrPort, switches,  neighborMap )
            if routed:
                discoveries.extend( routed )

        return discoveries
 
