from .pyecm import pyecm

def factor(n):
    return list(pyecm.factors(n, False, True, 10, 1))
