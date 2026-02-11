# Blob

A Blob is a nice way to work with unstructured data.
It allows you to have different views into data (bits, bytes, ints, etc), run analyses, and easily slice the data.
I wrote it to save Shellphish some time with crypto and forensics challenges.

## What can it do

Blob provides a `Blob` class that lets you:

- flip between byte and bit views without manually converting
- index/slice by bytes (`int`) or bits (`float`)
- split by size, count, or separator (both byte and bit separators)
- test likely block sizes for crypto-ish data
- run bitwise operations directly on binary blobs
- chop data with offsets and truncation helpers
- unpack structured data with `struct` formats
- do quick statistical checks (`entropy`, `chisquare`) for randomness-ish analysis
- fan out operations to many chunks with MulPyPlexer

It is intentionally small, direct, and useful in CTF workflows.

### Quick example

```python
import blob

# blobs can be created from byte or bit data
a = blob.Blob(data=b'ABCD')
b = blob.Blob(data_bits='01000001010000100100001101000100')
assert a == b

# blobs seamlessly translate between the two
assert a.data_bits == '01000001010000100100001101000100'
assert b.data == b'ABCD'

# use integers to access bytes and floats to access bits
assert b[1] == b'B'
assert a[1.].data_bits == '1'
assert b[1:-1] == b'BC'
assert a[8.:-8.] == b'BC'

# blobs provide lots of useful operations
print(a.size, "divides cleanly into", a.blocksize_candidates())
print(a.size_bits, "divides cleanly into", a.blocksize_bits_candidates())
print("The second half of a is:", a.offset(2))
print("Letters of A are:", a.split(size=1))
print("Split on the 'B':", a.split(sep='B'))

# and bitwise ops!
assert a | b'\x20\x20\x20\x20' == b'abcd'
```

## More examples

### Create blobs from bytes, bits, files, and directories

```python
from pathlib import Path
from blob import Blob

b1 = Blob(data=b"\x00\x01\x02\x03")
b2 = Blob(data_bits="00000000000000010000001000000011")
assert b1 == b2

Path("samples").mkdir(exist_ok=True)
Path("samples/demo.bin").write_bytes(b"hello")
b3 = Blob(filename="demo.bin", dirname="samples")
assert b3.data == b"hello"
```

### Byte indexing (`int`) vs bit indexing (`float`)

```python
from blob import Blob

b = Blob(data=b"AB")  # 01000001 01000010

assert b[0] == b"A"            # byte 0
assert b[1] == b"B"            # byte 1
assert b[8.] == b"B"           # bit index 8 is byte boundary -> one byte
assert b[1.].data_bits == "1"  # single bit as a 1-bit blob
```

### Slicing (byte and bit)

```python
from blob import Blob

b = Blob(data=b"ABCDEFGHIJ")
assert b[2:6] == b"CDEF"       # byte slice
assert b[::2] == b"ACEGI"      # byte stride

bits = Blob(data=b"ABCD")
assert bits[8.:24.] == b"BC"   # bit slice aligned to bytes
assert bits[1.:9.].data == b"\x82"  # unaligned bit slice
```

### Splitting by size, count, and separators (bytes and bits)

```python
from blob import Blob

b = Blob(data=b"AAAABBBBCCCC")

assert b.split(size=4) == [b"AAAA", b"BBBB", b"CCCC"]
assert b.split(n=3) == [b"AAAA", b"BBBB", b"CCCC"]
assert b.split(size_bits=16) == [b"AA", b"AA", b"BB", b"BB", b"CC", b"CC"]

assert b.split(sep=b"B") == [b"AAAA", b"CCCC"]
assert b.split(sep_bits="01000010") == [b"AAAA", b"CCCC"]  # split on byte 'B' as bits
```

### Block size analysis

```python
from blob import Blob

b = Blob(data=b"AAAABBBBCCCC")
print(b.blocksize_candidates())        # [1, 2, 3, 4, 6]
print(b.blocksize_bits_candidates())   # [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]
```

### Bitwise ops (+ rotates and logical shifts)

```python
from blob import Blob

a = Blob(data=b"ABCD")
mask = Blob(data=b"\x20")

assert (a ^ mask).data == b"abcd"
assert (a | mask).data == b"abcd"
assert (a & Blob(data=b"\xdf")).data == b"ABCD"
assert (~Blob(data=b"\x00\xff")).data == b"\xff\x00"

# cyclic shifts (rotate left)
assert a.rol(1) == b"BCDA"     # by bytes
assert a.rol(8.0) == b"BCDA"   # by bits

# logical bit shifts (manual: slice + pad)
x = Blob(data=b"\x81")  # 10000001
left1 = x[1.:] + Blob(data_bits="0")
right1 = Blob(data_bits="0") + x[:-1.]
assert left1.data == b"\x02"   # 00000010
assert right1.data == b"\x40"  # 01000000
```

### Statistical analysis (entropy, chi-square, randomness checks)

```python
import os
from blob import Blob

# requires scipy: pip install "blob[scipy]" or "blob[all]"
randomish = Blob(data=os.urandom(4096))
biased = Blob(data=b"A" * 4096)

e_rand = randomish.entropy(blocksize=1)
e_bias = biased.entropy(blocksize=1)
print("entropy:", e_rand, e_bias)  # random-ish should be much higher

chi_rand = randomish.chisquare(blocksize=1)  # [statistic, pvalue]
chi_bias = biased.chisquare(blocksize=1)
print("chi-square:", chi_rand, chi_bias)     # random-ish usually lower statistic, higher p-value
```

### Struct-style conversions (`to_ints`, `to_uint_list`, etc.)

Blob keeps this in one primitive: `unpack(fmt)`. If you like helper names like `to_uint_list`, it is a thin wrapper:

```python
from blob import Blob

def to_uint_list(b, bits=16, endian=">"):
    fmts = {8: "B", 16: "H", 32: "I", 64: "Q"}
    return b.unpack(endian + fmts[bits])

def to_ints(b, bits=16, endian=">"):
    fmts = {8: "b", 16: "h", 32: "i", 64: "q"}
    return b.unpack(endian + fmts[bits])

hdr = Blob(data=b"\x00\x10\xff\xf0")
assert to_uint_list(hdr, 16) == [16, 65520]
assert to_ints(hdr, 16) == [16, -16]

assert Blob(data=b"\x41\x42\x43\x44").unpack(">I", repeat=False) == (0x41424344,)
```

### Repeating pattern detection

```python
from blob import Blob

data = Blob(data=b"XYZXYZXYZXYZ")

# candidate period sizes that tile the blob
print(data.blocksize_candidates())  # includes 3 here

# direct period check: rotating by one period gives same data
assert data == data.rol(3)

# repeated-block signal (ECB-ish quick check)
blocks = Blob(data=b"A" * 16 + b"B" * 16 + b"A" * 16).split(size=16)
duplicate_blocks = len(blocks) - len(set(blocks))
assert duplicate_blocks == 1
```

### Offset and truncation operations

```python
from blob import Blob

b = Blob(data=b"AAAABBBBCCCC")

assert b.offset(offset=4) == b"BBBBCCCC"           # drop first 4 bytes
assert b.offset(offset_bits=32) == b"BBBBCCCC"     # same thing in bits
assert b.offset(sep=b"C") == b"CCCC"               # jump to first separator
assert b.offset(sep_bits="01000010") == b"BBBBCCCC"

assert b.truncate(offset=4) == b"AAAA"             # keep first 4 bytes
assert b.truncate(offset_bits=16) == b"AA"
assert Blob(data=b"ABCD").truncate(sep=b"C") == b"AB"
```

### MulPyPlexer integration (operate on many blobs at once)

```python
from blob import Blob

# requires mulpyplexer: pip install "blob[mulpyplexer]" or "blob[all]"
b = Blob(data=b"AAAABBBBCCCC")

# split into 4-byte chunks, truncate each to 3 bytes, split each into bytes, flatten
mp = b.mp_split(size=4).truncate(3).split(size=1).mp_flatten().mp_items
assert [x.data for x in mp] == [b"A", b"A", b"A", b"B", b"B", b"B", b"C", b"C", b"C"]
```

## Design goals

The design goals for blob are:

- well tested - we should be able to use this in CTFs without worrying that it's buggy
- familiar - blobs should comply with other Python API where possible
- flexible - we should be able to do stuff that we don't necessarily anticipate with blobs

## Software planning

Each blob should be able to:

* load some data as a blob (bits or bytes)
* reason about "block size" (i.e., even divisions of the blob)
* split the blob by blocksize
* split the blob into n chunks
* split the blob by a byte separator
* split the blob by a bit separator
* produce arrays of integers
* xor/or/and blobs together
* bitwise not on blobs
* calculate entropy
* calculate chi-square
* offset the blob by some number of bits or bytes
* produce arrays of bitstrings
* support blobs that aren't byte-aligned (testing needed)
* analyze randomness of data
- run sliding-window entropy and randomness tests
- do a distribution of various n-grams
- find repeating patterns
- swap endness
- append/interleave blobs
- get printable strings
- get dictionary words
- apply error-correction like reed-solomon
- compute hashes and checksums
- track the blob hierarchy, do automatic analysis, and organize blobs ('input', 'keys', 'interesting', 'unknown')
- crypto functionality to apply a cipher to some code (pass-through to pycrypto for real stuff, but might be nice to implement for reuse?)
- block chaining functionality to apply cbc/ebc/ctr/etc
