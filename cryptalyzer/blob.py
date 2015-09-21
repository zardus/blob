import os
import struct
import operator
import itertools

class Blob(object):
    def __init__(self, dirname=None, filename=None, data=None, bitdata=None):
        self.filename = filename

        if data is not None:
            self.data = data
        elif bitdata is not None:
            self.data = utils.from_bitstr(bitdata)
        elif filename is not None:
            self.data = open(os.path.join(dirname, filename), 'r')
        self.blocksize_bits = None

    def __eq__(self, o):
        return self.data == o.data

    #
    # operations
    #

    def __xor__(self, o):
        return Blob(data=utils.xor_str(self.data, o.data))

    def __and__(self, o):
        return Blob(data=utils.and_str(self.data, o.data))

    def __or__(self, o):
        return Blob(data=utils.or_str(self.data, o.data))

    def __invert__(self):
        return Blob(data=utils.not_str(self.data))

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
    # Blocks
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

    def split(self, bytesize=None, bitsize=None, n=None, bytesep=None, allow_empty=False):
        if bytesize is None and bitsize is None and n is None:
            split_bits_size = self.blocksize_bits
        elif n is not None:
            split_bits_size = self.size_bits/n
        elif bytesize is not None:
            split_bits_size = bytesize * 8
        elif bitsize is not None:
            split_bits_size = bitsize

        if bytesep is not None:
            newblocks = [ Blob(data=d) for d in self.data.split(bytesep) if allow_empty or d != '' ]
        elif split_bits_size % 8 != 0:
            raise BlobError("TODO: support non-byte blocksizes")
        else:
            newblocks = [ Blob(data=self.data[i:i+split_bits_size/8]) for i in range(0, self.size_bytes, split_bits_size/8) ]

        return newblocks

    #
    # data converters
    #

    def unpack_struct(self, fmt, repeat=True, s=None):
        s = struct.Struct(fmt) if s is None else s
        if self.size_bytes % s.size != 0:
            raise BlobError("format size does not evenly divide blob size")

        if not repeat:
            if s.size != self.size_bytes:
                raise BlobError("size of non-repeating format is not equal to the blob size")
            return s.unpack(self.data)
        else:
            o = [ ]
            for b in self.split(bytesize=s.size):
                o.extend(b.unpack_struct(fmt, repeat=False, s=s))
            return o

from . import utils
from .errors import BlobError
