###     switch.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###

### support for constructing and saving (to switches) the linkState array
### separated into utils because both makeFlows.py and sherpa.py use these functions
###

def buildLinkState( switches, linkState ):
    for switchName in switches:
        for port in switches[ switchName ].nbrs:
            nbr = switches[ switchName ].nbrs[port]
            key = switchName+'-'+nbr if switchName < nbr else nbr+'-'+switchName
            linkState[ key ] = True

def saveLinkState( switches, linkState ):
    for switchId, switch in switches.items():
        switch.saveLinkState( linkState )



