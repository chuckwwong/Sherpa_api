###     rule.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
###     The Rule class organizes information about an individual rule in a switch's table.
###     A rule is constructed from a dictionary read out of the rules input file.
###     Various attributes from that dictionary become attributes in the rule's dictionary rule['state']
###     The Rule constructor checks that an input rule has required attributes, and looks for other
###         attributes it doesn't know about (which end up being reported)
###     A rule has a dictionary 'match' of attributes and their values, to be compared against
###     the values of the same attributes in a flow header.   The code is written to be able to customize
###     the comparison, by associating with each attribute in the 'match' dictionary a comparison function
###     which returns a Boolean value indicating whether the flow ought to be considered to 'match' in that attribute.
###
###     A flow header which matches in every of the rule's match attributed has actions applied to it.  The rule
###     has a dictionary 'actions' which is indexed by the action verb (e.g. 'OUTPUT'), a semi-colon, and then some argument
###     to the action verb.  In the case of 'OUTPUT' the argument is a port number.  Like the rule match functions, the actions
###     are customized, selected by the attribute of the rule's 'action' dictionary. 
###
from collections import defaultdict
from utils.ipn  import inIPFormat, IPValues
import pdb

RuleAttributes = ('actions','idle_timeout','packet_count','hard_timeout','byte_count',
    'duration_sec','duration_nsec','priority','length','flags','table_id','match','cookie')

RequiredRuleAttributes = ('actions','table_id','match')

ActionAttributes = ('SET_FIELD','OUTPUT','DEC_NW_TTL')
MatchAttributes  = ('dl_type','ip_dscp','in_port','nw_dst','nw_proto','nw_src','nw_ttl')

### ------- Comparison functions used by rule matching checks -----------
def equal(v1,v2):

    ### equality if the arguments are the same, or at least one of them is a wildcard
    return True if (v1==v2 or v1=='*' or v2=='*') else False

### 'contains' determines whether an IP address from the flow header is contained within a CIDR
### block in the rule's match dictionary

### ip1 is the value from the rule, ip2 is the value from the flow
def contains(ip1,ip2):
    ipv1Low, ipv1High = IPValues(ip1)
    ipv2Low, ipv2High = IPValues(ip1)
    return ipv1Low <= ipv2Low and ipv2High <= ipv1High


### ---------- Action routines using by selected rule actions ------------
###
### set_field used to implement SET_FIELD action

def set_field(**kwargs):
    flow = kwargs['hdr'] 
    flow.vars[ kwargs['field'] ] = kwargs['value']
    return

### portIsLive used to determine whether a give OUTPUT action should be applied,
### returning a Boolean indicating whether the port the OUTPUT would use is alive
###
def portIsLive(**kwargs):

    ### look up the state of the link between this switch and
    ### the switch pointed to by the action code. 
    switch   = kwargs['switch']
    portId   = int(kwargs['portId'])
    linkUp   = switch.checkLinkState( portId ) 
    return   linkUp

### decrement the flow header's TTL value
###
def decTTL(**kwargs):
    flow = kwargs['hdr']
    flow.vars['nw_ttl'] -= 1


cmpFunc = {'dl_type':equal, 'ip_dscp':equal,'in_port':equal,'nw_dst':contains}
actionFunc = {'SET_FIELD':set_field,'OUTPUT':portIsLive,'DEC_NW_TTL':decTTL }

RuleNewlySeen   = set()
MatchNewlySeen  = set()
ActionNewlySeen = set()

class Rule:
    def __init__(self,switch,rdict):
        global RuleNewlySeen, MatchNewlySeen, ActionNewlySeen

        ### remember which switch this rule is on
        ###
        self.switch = switch

        ### record the rule state variables and check whether any rule attribute
        ### is one we've not seen before
        ###
        ### what this rule refers to
        seenAttributes = list(rdict.keys())

        ### make sure all the required attributes are present
        for reqAttribute in RequiredRuleAttributes:
            if reqAttribute not in seenAttributes:
                print('rule attribute', reqAttribute,'required but missing')
                os._exit(1)

        ### self.state holds the integer-valued state values for the rule
        self.state = defaultdict(int)

        self.table_id = rdict['table_id']

        for seen in seenAttributes:

            ### if we don't see it, remember the attribute name, reported once
            if seen not in RuleAttributes:
                RuleNewlySeen.add(seen)

            ### 'actions' and 'match' are special, not state variables, remember the value 
            elif seen not in ('actions','match'):
                self.state[seen] = int( rdict[seen] )

        ### match dictionary gives the attributes on which this rule looks for a match.
        ### check that we've seen them all
        seenAttributes = list(rdict['match'].keys())
        self.match = {}
        for seen in seenAttributes:
            if seen in MatchAttributes:
                matchField = rdict['match'][seen] 
                self.match[seen] = int( matchField ) \
                    if isinstance(matchField,int) or matchField.isdigit() else matchField
            else:
                MatchNewlySeen.add(seen)

        ### action list gives the list of actions to take upon a match.
        ### check that we've seen them all
        self.action = []
        for action in rdict['actions']:
            if action.find(':') > -1:
                here = action.find(':')
                pre  = action[:here]
                post = action[here+1:] 
                pre  = pre.strip() 
                post = post.strip() 
            else:
                pre  = action.strip()
                post = None

            if pre not in ActionAttributes:
                ActionNewlySeen.add(pre)                
            if post is not None:
                self.action.append((pre,post))
            else:
                self.action.append((pre,None))


    ### if offered flow matches the rule apply the actions.  If those actions
    ### include routing to (potentially multiple) nodes, return the list of node identifiers
    ### 
    def matchAndAction(self, flow):
        ### check for match
        for matchAttribute, matchField in self.match.items():
            ### if matchAttribute not an attribute of the flow, there's no match
            if matchAttribute not in flow.vars:
                return None

            ### look up the function to use to compare the field from the rule with the field from the flow
            cmpF = cmpFunc[matchAttribute]
            if not cmpF( matchField, flow.vars[ matchAttribute ] ):
                return None

        ### survived all the match tests, now apply the actions
        ###
        toRoute = []
        for actionAttribute, actionField in self.action:
            actionF = actionFunc[ actionAttribute ]

            ### if this rule has multiple OUTPUT statements only the first one routing to a live link is used
            if actionAttribute == 'OUTPUT' and len(toRoute) == 0:

                # ability to route dependent on state of link, to be tested inside of actionF
                routed = actionF( switch=self.switch, portId=actionField )
                if routed:
                    ### remember the port out of which the flow is to pass
                    toRoute.append( int(actionField) )
            
            elif actionAttribute == 'DEC_NW_TTL':
                actionF(hdr=flow)
     
            elif actionAttribute == 'SET_FIELD': 
                if actionField.find(':') > -1:
                    actionField = actionField.replace('{','')
                    actionField = actionField.replace('}','')
                    here = actionField.find(':')
                    actionF(hdr=flow, field=actionField[:here], value=actionField[here+1:])

        ### if toRoute is not empty and the flow's TTL is non-zero pass along toRoute
        ###
        if flow.vars['nw_ttl'] > 0  and len(toRoute) > 0:
            return toRoute
        else:
            return None

    def isComplex(self):
        if len(self.match) > 1:
            return True

        if 'in_port' in self.match:
            return False


