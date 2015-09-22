import os
import struct
import operator
import functools
import itertools
import scipy.stats
import collections

def _fix_other_type(f):
    @functools.wraps(f)
    def fixer(self, o):
        if isinstance(o, Blob):
            return f(self, o)
        elif isinstance(o, str):
            return f(self, Blob(o))
        else:
            raise BlobError("unknown type passed to Blob.%s", f.__name__)
    return fixer

class Blob(object):
    def __init__(self, data=None, dirname=None, filename=None, data_bits=None):
        self.filename = filename
        self._data_bits = None
        self._data_bytes = None

        if data is not None:
            self.data = data
        elif data_bits is not None:
            self.data_bits = data_bits
        elif filename is not None:
            self.data = open(os.path.join(dirname, filename), 'r')
        self.blocksize_bits = None

        if self._data_bits is not None and len(self._data_bits) % 8 != 0:
            raise BlobError("TODO: support non-byte blocksizes")


    #
    # Bit access
    #

    @property
    def data(self):
        if self._data_bytes is None:
            self._data_bytes = utils.from_bitstr(self._data_bits)
        return self._data_bytes

    @data.setter
    def data(self, d):
        self._data_bytes = d
        self._data_bits = None

    @property
    def data_bits(self):
        if self._data_bits is None:
            self._data_bits = utils.to_bitstr(self._data_bytes)
        return self._data_bits

    @data_bits.setter
    def data_bits(self, d):
        self._data_bytes = None
        self._data_bits = d

    #
    # operations
    #

    def __repr__(self):
        return "B(%r)" % self.data

    @_fix_other_type
    def __eq__(self, o):
        return self.data == o.data

    def __hash__(self):
        return hash(self.data)

    @_fix_other_type
    def __xor__(self, o):
        return Blob(data=utils.xor_str(self.data, o.data))

    @_fix_other_type
    def __and__(self, o):
        return Blob(data=utils.and_str(self.data, o.data))

    @_fix_other_type
    def __or__(self, o):
        return Blob(data=utils.or_str(self.data, o.data))

    def __invert__(self):
        return Blob(data=utils.not_str(self.data))

    def __getitem__(self, r):
        if isinstance(r, int):
            if self._data_bytes is not None:
                return Blob(data=self.data[r])
            else:
                return Blob(data_bits=self._data_bits[r*8:r*8+8])
        elif isinstance(r, float):
            r = int(r)

            if self._data_bytes is not None and r % 8 == 0:
                return Blob(data=self.data[r/8])
            else:
                return Blob(data_bits=self.data_bits[r])
        elif isinstance(r, slice):
            start = r.start if r.start is not None else None
            stop = r.stop if r.stop is not None else None
            step = r.step if r.step is not None else None

            if type(start) is float or type(stop) is float: #bit access
                start = int(start) if start is not None else None
                stop = int(stop) if stop is not None else None
                step = int(step) if step is not None else None

                if (start is None or start % 8 == 0) and (stop is None or stop % 8 == 0) and step is None:
                    byte_aligned = True
                else:
                    byte_aligned = False
            else: # byte access
                if start is not None: start *= 8
                if stop is not None: stop *= 8
                if step is not None: step *= 8
                byte_aligned = True

            if byte_aligned and self._data_bytes is not None:
                rr = slice(
                    start/8 if start is not None else None,
                    stop/8 if stop is not None else None,
                    step/8 if step is not None else None
                )
                return Blob(data=self.data[rr])
            else:
                rr = slice(start, stop, step)
                return Blob(data_bits=self.data_bits[rr])

    #
    # Size
    #

    @property
    def size_bytes(self):
        return len(self.data)

    @property
    def size_bits(self):
        if self._data_bits is None:
            return len(self.data) * 8
        else:
            return len(self.data_bits)

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

    def split(self, bytesize=None, bitsize=None, n=None, bytesep=None, bitsep=None, allow_empty=False):
        if bytesep is not None:
            newblocks = [ Blob(data=d) for d in self.data.split(bytesep) if allow_empty or d != '' ]
        elif bitsep is not None:
            newblocks = [ Blob(data_bits=d) for d in self.data_bits.split(bitsep) if allow_empty or d != '' ]
        else:
            if n is not None:
                split_bits_size = self.size_bits/n
            else:
                split_bits_size = self._get_bit_index(byte=bytesize, bit=bitsize)

            if split_bits_size % 8 != 0:
                raise BlobError("TODO: support non-byte blocksizes for splitting")

            newblocks = [ Blob(data=self.data[i:i+split_bits_size/8]) for i in range(0, self.size_bytes, split_bits_size/8) ]

        return newblocks

    def _get_bit_index(self, byte=None, bit=None, bitsep=None, bytesep=None, reverse=False):
        if bit is not None:
            return bit if bit > 0 else self.size_bits + bit
        elif byte is not None:
            return byte * 8 if byte > 0 else self.size_bits + byte*8
        elif bytesep is not None:
            if not bytesep in self.data:
                raise BlobError("separator not found in blob data")
            elif reverse:
                return self.data.rindex(bytesep) * 8
            else:
                return self.data.index(bytesep) * 8
        elif bitsep is not None:
            if not bitsep in self.data_bits:
                raise BlobError("separator not found in blob data")
            elif reverse:
                return self.data_bits.rindex(bitsep)
            else:
                return self.data_bits.index(bitsep)

    def offset(self, byteoffset=None, bitoffset=None, bytesep=None, bitsep=None):
        bitoffset = self._get_bit_index(byte=byteoffset, bit=bitoffset, bytesep=bytesep, bitsep=bitsep)
        if bitoffset % 8 != 0:
            raise BlobError("TODO: support non-byte blocksizes for offset")
        return Blob(data=self.data[bitoffset/8:])

    def truncate(self, byteoffset=None, bitoffset=None, bytesep=None, bitsep=None):
        off = self._get_bit_index(byte=byteoffset, bit=bitoffset, bytesep=bytesep, bitsep=bitsep, reverse=True)

        if off % 8 != 0:
            return Blob(data=self.data[:off/8])
        else:
            return Blob(data_bits=self.data_bits[:off])

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

    #
    # Statistical stuff
    #

    def entropy(self, blocksize_bytes=None, blocksize_bits=None, base=2, **kwargs):
        elements = self.split(bytesize=blocksize_bytes, bitsize=blocksize_bits)
        counts = collections.Counter(elements)

        return float(scipy.stats.entropy(counts.values(), base=base, **kwargs))

    def chisquare(self, blocksize_bytes=None, blocksize_bits=None, **kwargs):
        elements = self.split(bytesize=blocksize_bytes, bitsize=blocksize_bits)
        counts = collections.Counter(elements)

        return map(float, scipy.stats.chisquare(counts.values(), **kwargs))

from . import utils
from .errors import BlobError
