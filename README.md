# Cryptalyzer

Cryptalyzer is Shellphish's tool for saving time with crypto and forensics challenges.
It tries to automatically solve challenges by decrypting, extracting, and analyzing crypto/forensics challenges.

## What can it do

At the moment, cryptalyzer provides a `Blob` class that enables all sorts of cool operations:

```python
#
# blobs can be created from byte or bit data
#

a = cryptalyzer.Blob('ABCD')
a = cryptalyzer.Blob(data_bits='01000001010000100100001101000100')
assert a == b

# blobs seamlessly translate between the two
assert a.data_bits == '01000001010000100100001101000100'
assert b.data == 'ABCD'

# use integers to access bytes and floats to access bits
assert b[1] == 'B'
assert a[1.] == '1'
assert b[1:-1] == 'BC'
assert a[8.:-8.] == 'BC'

# blobs provide lots of useful operations
print a.size_bytes, "divides cleanly into", a.blocksize_bytes_candidates()
print a.size_bits, "divides cleanly into", a.blocksize_bits_candidates()
print "The second half of a is:", a.offset(2)
print "Letters of A are:", a.split(bytesize=1)
print "Split on the 'B':", a.split(bytesep='B')

# and bitwise ops!
assert a | '\x20\x20\x20\x20' == 'abcd'
```

## How it works

Cryptalyzer models each file as a Blob object.
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
- support blobs that aren't byte-aligned
- analyze randomness of data
- run sliding-window entropy and randomness tests
- do a distribution of various n-grams
- find repeating patterns
- swap endness
- append/interleave blobs
- get printable strings
- get dictionary words
- apply error-correction like reed-solomon
- compute hashes and checksums
- track the blob hierarchy
- keep input blobs in 'input/'
- keep blobs determined to be potential keys in 'keys/'
- keep blobs that look interesting in 'interesting/'
- keep other blobs in "unknown"

This functionality will require some of the following:

- crypto functionality to apply a cipher to some code (pass-through to pycrypto for real stuff, but might be nice to implement for reuse?)
- block chaining functionality to apply cbc/ebc/ctr/etc
- error-correction implementations
