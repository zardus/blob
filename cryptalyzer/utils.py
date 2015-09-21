from .pyecm import pyecm

def factor(n):
    if n == 0:
        return [ 0 ]
    return list(pyecm.factors(n, False, True, 10, 1))

def insert_separators(st, sep, wordsize):
    return sep.join([ st[i:i+wordsize] for i in range(0, len(st), wordsize) ])

#
# bitstring stuff
#

def to_bitstr(st):
    bits = bin(int(st.encode('hex'), 16))[2:].rjust(8*len(st), '0')
    return bits

def from_bitstr(st):
    return ('%x' % int(st, 2)).rjust(len(st)/4, '0').decode('hex')

def ror_bitstr(s, n):
    n %= len(s)
    return s[-n:] + s[:-n]

def xor_bitstr(a, b):
    return ''.join(('1' if ab != bb else '0') for ab,bb in zip(a,b))
