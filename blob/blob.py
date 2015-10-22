import os
import struct
import operator
import functools
import itertools

try:
    import scipy.stats
    _scipy_fail = False
except ImportError:
    _scipy_fail = True

try:
    import mulpyplexer
    _mp_fail = False
except ImportError:
    _mp_fail = True

import collections

def _blobify(o):
    if isinstance(o, Blob):
        return o
    elif isinstance(o, str):
        return Blob(o)
    else:
        raise BlobError("can't blobify type %s", type(o))

def _fix_other_type(f):
    @functools.wraps(f)
    def fixer(self, o):
        return f(self, _blobify(o))
    return fixer

class Blob(object):
    '''
    A Blob object enables rich operations on unstructured data. By encapsulating
    bytes in a Blob, one can easily split them, do bit operations on them,
    index them as bytestreams, bitstreams, or other data types, and do
    statistical analyses.
    '''

    def __init__(self, data=None, data_bits=None, dirname=None, filename=None):
        '''
        Initializes a Blob object. Blobs can be created from different types of
        data:

            @param data: a string containing the data
            @param data_bits: a string of bits (as '1' and '0' chars)
                              representing the data
            @param filename: the name of a file to read the data from
            @param dirname: the name of the directory for the aforementioned
                            file. $PWD by default.
        '''

        self.filename = filename
        self._data_bits = None
        self._data_bytes = None

        if data is not None:
            self.data = data
        elif data_bits is not None:
            self.data_bits = data_bits
        elif filename is not None:
            if dirname is None: dirname = '.'
            self.data = open(os.path.join(dirname, filename), 'r')
        self.blocksize_bits = None

    #
    # Bit access
    #

    @property
    def data(self):
        '''
        The data of the Blob, in bytes.

        @returns a string, representing the data
        '''

        if self._data_bytes is None:
            self._data_bytes = utils.from_bitstr(self._data_bits)
        return self._data_bytes

    @data.setter
    def data(self, d):
        self._data_bytes = d
        self._data_bits = None

    @property
    def data_bits(self):
        '''
        The data of the Blob, in bits.

        @returns a string of bits, representing the data
        '''

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
        if self.byte_aligned:
            return "B(%r)" % self.data
        else:
            return "B(b%r)" % self.data_bits

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

    @_fix_other_type
    def __add__(self, o):
        if self._data_bytes is not None and o._data_bytes is not None:
            return Blob(data=self._data_bytes+o._data_bytes)
        else:
            return Blob(data_bits=self._data_bits+o._data_bits)

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

    def _rol_bytes(self, n):
        n = n % self.size_bytes
        return self[n:] + self[:n]

    def _rol_bits(self, n):
        n = n % self.size_bits
        if n % 8 == 0 and self.byte_aligned:
            return self._rol_bytes(n/8)

        return self[float(n):] + self[:float(n)] #pylint:disable=invalid-slice-index

    def rol(self, n):
        if type(n) is float:
            return self._rol_bits(int(n))
        elif type(n) is int:
            return self._rol_bytes(n)
        else:
            raise ValueError("invalid type for rotation amount")

    def ljust(self, n, what=None):
        '''
        Returns a left-justified Blob.

        @param n: the size to justify to. Float for bits, int for bytes.
        @param what: the char to justify with. The default is ' ' for bytes
                     and '0' for bits.
        '''
        if type(n) is int:
            what = ' ' if what is None else what
            return Blob(data=self.data.ljust(n, what))
        elif type(n) is float:
            what = '0' if what is None else what
            return Blob(data_bits=self.data_bits.ljust(int(n), what))
        else:
            raise ValueError("invalid type for ljust amount")

    def rjust(self, n, what=None):
        '''
        Returns a right-justified Blob.

        @param n: the size to justify to. Float for bits, int for bytes.
        @param what: the char to justify with. The default is ' ' for bytes
                     and '0' for bits.
        '''
        if type(n) is int:
            what = ' ' if what is None else what
            return Blob(data=self.data.rjust(n, what))
        elif type(n) is float:
            what = '0' if what is None else what
            return Blob(data_bits=self.data_bits.rjust(int(n), what))
        else:
            raise ValueError("invalid type for rjust amount")

    #
    # Size
    #

    @property
    def byte_aligned(self):
        return self.size_bits % 8 == 0

    @property
    def size_bytes(self):
        '''
        The number of bytes in the Blob.

        @returns a int
        '''
        return len(self.data)

    @property
    def size_bits(self):
        '''
        The number of bits in the Blob.

        @returns a int
        '''
        if self._data_bits is None:
            return len(self.data) * 8
        else:
            return len(self.data_bits)

    #
    # Blocks
    #

    def blocksize_bits_candidates(self, min_blocks=None, min_blocksize=None):
        '''
        Returns possibilities for a "block size", in bits. The possibilities are
        integers which divide evenly into the size of the Blob. These include
        sizes that evenly divide the bits in the block, even if they don't
        evenly divide the bytes.

        @returns a list of ints
        '''

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
        '''
        Returns possibilities for a "block size", in bytes. The possibilities are
        integers which divide evenly into the size of the Blob.

        @returns a list of ints
        '''
        min_blocksize = 8 if min_blocksize is None else min_blocksize * 8
        bit_candidates = self.blocksize_bits_candidates(min_blocks=min_blocks, min_blocksize=min_blocksize)
        return [ f/8 for f in bit_candidates if f%8 == 0]

    def split(self, bytesep=None, bitsep=None, bytesize=None, bitsize=None, n=None, allow_empty=False):
        '''
        This splits the Blob into several smaller Blobs according to the
        provided parameters.

        @param bytesep: split the Blob along this byte separator
        @param bitsep: split the Blob along this bit separator
        @param bytesize: each Blob should be this many bytes long
        @param bitsize: each Blob should be this many bits long
        @param n: split the Blob into this many blocks
        @param allow_empty: when splitting with a separator, keep empty blobs
                            (default: False)

        @returns a list of Blobs
        '''

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
                newblocks = [ Blob(data_bits=self.data_bits[i:i+split_bits_size]) for i in range(0, self.size_bits, split_bits_size) ]
            else:
                newblocks = [ Blob(data=self.data[i:i+split_bits_size/8]) for i in range(0, self.size_bytes, split_bits_size/8) ]

        return newblocks

    def mp_split(self, *args, **kwargs):
        '''
        This is a convenience function that returns a mulpyplexer object
        encapsulating the results of the split of the Blob. Operations
        on this object are reflected on the entire list.

        @returns a mulpyplexer.MP object full of Blobs
        '''
        if _mp_fail:
            raise BlobError("please install the mulpyplexer module (`pip install mulpyplexer`) to use mulpyplexing features!")

        if args:
            kwargs['bytesize'] = args[0]
        return mulpyplexer.MP(self.split(**kwargs))

    def _get_bit_index(self, byte=None, bit=None, bitsep=None, bytesep=None, reverse=False):
        '''
        This is a convenience function to translate indexing data (according to
        bits, bytes, etc) into an absolute bit index.

        @returns an int
        '''
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
        '''
        Chops off the beginning of a Blob.

        @param byteoffset: the number of bytes to chop
        @param bitoffset: the number of bits to chop
        @param bytesep: chop everything after a separator of bytes (keep the
                        separator)
        @param bitsep: chop everything after a separator of bits (keep the separator)
        '''
        bitoffset = self._get_bit_index(byte=byteoffset, bit=bitoffset, bytesep=bytesep, bitsep=bitsep)
        if bitoffset % 8 != 0:
            raise BlobError("TODO: support non-byte blocksizes for offset")
        return Blob(data=self.data[bitoffset/8:])

    def truncate(self, byteoffset=None, bitoffset=None, bytesep=None, bitsep=None):
        '''
        Chops off the end of a Blob.

        @param byteoffset: the number of bytes to keep
        @param bitoffset: the number of bits to keep
        @param bytesep: chop everything after a separator of bytes (including
                        the separator)
        @param bitsep: chop everything after a separator of bits (including the
                       separator)
        '''
        off = self._get_bit_index(byte=byteoffset, bit=bitoffset, bytesep=bytesep, bitsep=bitsep, reverse=True)

        if off % 8 != 0:
            return Blob(data=self.data[:off/8])
        else:
            return Blob(data_bits=self.data_bits[:off])

    #
    # data converters
    #

    def unpack_struct(self, fmt, repeat=True, s=None):
        '''
        Unpacks a Blob according to a struct format and returns the results.

        @param fmt: the format
        @param repeat: repeat the unpacking until the whole Blob is unpacked
                       (default: True)
        @param s: internal option to pass in a struct.Struct object and
                  speed things up

        @return a list of the resulting numbers
        '''

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

    def entropy(self, blocksize_bytes=None, blocksize_bits=None, base=2, **split_kwargs):
        '''
        Calculate the entropy of the data.

        @param blocksize_bytes: use this blocksize (in bytes) for splitting
                                data for the probability calculation.
        @param blocksize_bits: use this blocksize (in bits) for splitting
                                data for the probability calculation.

        You can also pass in kwargs that will be forwarded to Blob.split() (for
        more advanced splitting).

        @param base: an alternate base for the entropy
        '''
        elements = self.split(bytesize=blocksize_bytes, bitsize=blocksize_bits, **split_kwargs)
        counts = collections.Counter(elements)

        if _scipy_fail:
            raise BlobError("please install the scipy to use statistical analyses!")

        return float(scipy.stats.entropy(counts.values(), base=base))

    def chisquare(self, blocksize_bytes=None, blocksize_bits=None, f_exp=None, **split_kwargs):
        '''
        Perform the chi-squared test on the data.

        @param blocksize_bytes: use this blocksize (in bytes) for splitting
                                data for the probability calculation.
        @param blocksize_bits: use this blocksize (in bits) for splitting
                                data for the probability calculation.
        @param f_exp: the *expected* frequencies of occurrence, used internally
                      by chi-square (default: None for even distribution)

        You can also pass in kwargs that will be forwarded to Blob.split() (for
        more advanced splitting).

        @param base: an alternate base for the entropy
        '''
        elements = self.split(bytesize=blocksize_bytes, bitsize=blocksize_bits, **split_kwargs)
        counts = collections.Counter(elements)

        if _scipy_fail:
            raise BlobError("please install the scipy to use statistical analyses!")

        return map(float, scipy.stats.chisquare(counts.values(), f_exp=f_exp))

    #
    # Some other weird operations
    #

    def rotating_xors(self, other=None, step_bits=None):
        '''
        Yields a sequence of blobs, representing this blob XORed with a elements
        in a sequence of "other" blobs rotated by each other.

        That description made no sense.

        @params other: the other blob (default: self)
        @params step_bits: the bits to rotate (left) by every time (default: 8)
        '''
        other = self if other is None else _blobify(other)
        step_bits = 8 if step_bits is None else step_bits

        for i in range(other.size_bits/step_bits):
            if step_bits == 8:
                yield self ^ other._rol_bytes(i)
            else:
                yield self ^ other._rol_bits(i)

    def count_elements(self, i):
        '''
        Returns the number of occurrences of elements of iterable s in the blob.
        '''

        count = 0
        for e in i:
            eb = _blobify(e)
            if eb.byte_aligned:
                count += self._data_bytes.count(eb._data_bytes)
            else:
                count += self._data_bits.count(eb._data_bits)

        return count

from . import utils
from .errors import BlobError
