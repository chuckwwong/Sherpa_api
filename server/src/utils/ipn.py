###     ipn.py
###     release date: March 20, 2020
###     author: David Nicol
###     contact: dmnicol@illinois.edu
###
###    this file contains utility functions for dealing with IP addresses.
###      IPValues(ip) :  the argument ip may be a single IP, or may be a CIDR block.
###         The routine converts the argument into an integer-based range.
###
###      inIPFormat(ipstr) : determines whether the argument string ipstr is in IP address
###         format or in IP CIDR format
###
###      Int2IP(ipv) : takes an integer argument ipv and turns it into a string of the IP address
###         corresponding to that integer.             
###
import pdb

def IPValues(ip):
    if isinstance(ip,int) or isinstance(ip,int):
        return ip
    if ip.find('/') > -1:
        ip,dim = ip.split('/')
        dim = int(dim)
    else:
        dim = 32

    try:
        [high,midhigh,midlow,low] = ip.split('.')

        v = int(high)*16777216
        v = v+int(midhigh)*65536
        v = v+int(midlow)*256
        v = v+int(low)
    except:
        return None


    ### clear out lower bits
    nv = v >> (32-dim)
    v  = nv << (32-dim)

    upperV = v + (1<<32-dim)-1
    return v, upperV

# return True or False depending on whether the input string is in IP format
#
def inIPFormat(adrs):
    if adrs is None:
        return False
    adrs = str(adrs)
    if '/' in adrs:
        if adrs.count('/') > 1:
            return False
        adrs, nxt = adrs.split('/')

    fields = adrs.split('.')
    if not len(fields) == 4:
        return False
    for idx in range(0,4):
        if not fields[idx].isdigit():
            return False

        value = int(fields[idx])
        if value < 0 or 255 < value:
            return False
    return True

def Int2IP(ipnum):
    ipn  = int(ipnum)

    o4   = ipn % 256
    ipn  = int(ipn>>8)
    o3   = ipn % 256
    ipn  = int(ipn>>8)
    o2   = ipn % 256
    ipn  = int(ipn>>8)
    o1   = ipn

    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()


