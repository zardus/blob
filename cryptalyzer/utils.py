from .pyecm import pyecm
import itertools
import operator
import array

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

def xor_bitstr(a, b, cycle=True):
    if len(a) < len(b): b,a = a,b
    if len(a) != len(b) and not cycle: raise XORError('unequal sizes (maybe add cycle=True?)')

    return ''.join(('1' if ab != bb else '0') for ab,bb in itertools.izip(a,itertools.cycle(b)))

#
# byte stuff
#

def _op_str(op, a, b, cycle):
    if len(a) < len(b): b,a = a,b
    if len(a) != len(b) and not cycle: raise XORError('unequal sizes (maybe add cycle=True?)')

    aa = array.array('B', a)
    bb = array.array('B', b)
    bc = itertools.cycle(bb)
    bci = iter(bc)

    for i in range(len(a)):
        aa[i] = op(aa[i], next(bci))
    return aa.tostring()

def xor_str(a, b, cycle=True):
    return _op_str(operator.xor, a, b, cycle)

def and_str(a, b, cycle=True):
    return _op_str(operator.and_, a, b, cycle)

def or_str(a, b, cycle=True):
    return _op_str(operator.or_, a, b, cycle)

def not_str(a):
    return _op_str(operator.xor, a, '\xff', True)

from .errors import XORError
