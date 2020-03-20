###     network.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
###     This file contains routines used to build data structures used by the various entry-level 
###     scripts
###
###     buildNetwork is called from outside this file to create a data structure of the network
###     whose basic elements are switches.   A switch has fields that describe its connection
###     (and ports) to other switches
###    
from collections  import defaultdict
from utils.switch import Switch
from utils.ipn    import IPValues
import pdb

### topoDict has format of node id (e.g. 'n17') as index into dictionary, with a value of a list
### of other node ids, order is assumed to reflect assignment to ports. Transform this into a dictionary
### similarly indexed by node id, but whose value is a dictionary indexed by port number, port number mapping to 
### neighbor id
###
def nbrThruPort( topoDict ):

    ### topo will be the output dictionary
    topo = defaultdict(dict)

    for nodeName, nbrs in topoDict.items():
        
        ### for each port in the node record which neighboring node is reached
        ###   by passing through that port
        ###
        for port,nbr in enumerate(nbrs,1):
            topo[ nodeName ][ port ] = nbr

    return topo


### topoDict is the dictionary from the topology file whose attributes are nodes.
###
### rulesDict is the dictionary from the rules file which is the value of the attribute
###     with a long integer code for _something_
###
### nodeIPs is a dictionary, indexed by node id, each mapped to a list of CIDR expressions of
###     IP ranges associated with the node
###
### buildNetwork calls the constructors for Switches, passing each its name, dictionary mapping
### ports to the neighboring nodes reached through the port,  list of
###     rules for table[0], and list of associated CIDR blocks
###
def buildNetwork( topoDict, rulesDict, nodeIPs ):
    switches = {}

    ### nbr[ nId ] gives a list of nodes connected to node nId by ports
    ntp = nbrThruPort( topoDict )

    ### rulesDict is Straight 'Outta Input Files
    rdict = rulesDict['nodes']

    ### for every node we're going to build
    for nodeName in rdict:

        ### build the cidr entry.  Rather than store the code, store the integer range of values the code represents
        cidrMatch = []
        for cidr in nodeIPs[ nodeName ]:
            low, high = IPValues(cidr)
            cidrMatch.append( (low,high) )

        ### create the switch, passing the name, a dictionary indicating which neighbor is reached passing through
        ### a specific port, and a list of CIDR blocks associated with the switch
        ###
        switches[nodeName] = Switch( nodeName, ntp[nodeName], rdict[nodeName], cidrMatch )

    return switches

