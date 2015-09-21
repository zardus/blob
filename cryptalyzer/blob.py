import os
import operator
import itertools

class Blob(object):
    def __init__(self, dirname=None, filename=None, data=None):
        self.filename = filename
        self.data = data if data is not None else open(os.path.join(dirname, filename), 'r')
        self.blocksize_bits = None

    #
    # Size
    #

    @property
    def size_bytes(self):
        return len(self.data)

    @property
    def size_bits(self):
        return len(self.data)*8

    def size_blocks(self):
        if self.blocksize_bits is None:
            raise BlobError("must set a blocksize before calling Blob.size_blocks()")
        return self.size_bits / self.blocksize_bits

    #
    # Block size
    #

    @property
    def blocksize_bytes(self):
        return (self.blocksize_bits+7)*8

    @blocksize_bytes.setter
    def blocksize_bytes_setter(self, b):
        self.blocksize_bits = b*8

    def even_blocks(self):
        return self.size_bits % self.blocksize_bits == 0

    def blocksize_bits_candidates(self, min_blocks=None, min_blocksize=None):
        min_blocks = 2 if min_blocks is None else min_blocks
        min_blocksize = 1 if min_blocksize is None else min_blocksize

        prime_factors = utils.factor(self.size_bits)
        nonprime_factors = { min_blocksize }
        for i in range(1, len(prime_factors)):
            combinations = set(itertools.combinations(prime_factors, i))
            for c in combinations:
                npf = reduce(operator.__mul__, c, 1)
                if npf >= min_blocksize:
                    nonprime_factors.add(npf)

        return [ f for f in sorted(nonprime_factors) if self.size_bits/f >= min_blocks ]

    def blocksize_bytes_candidates(self, min_blocks=None, min_blocksize=None):
        min_blocksize = 8 if min_blocksize is None else min_blocksize * 8
        bit_candidates = self.blocksize_bits_candidates(min_blocks=min_blocks, min_blocksize=min_blocksize)
        return [ f/8 for f in bit_candidates if f%8 == 0]

from . import utils
from .errors import BlobError
