# Cryptalyzer

Cryptalyzer is Shellphish's tool for saving us time with crypto and forensics challenges.
It tries to automatically solve challenges by decrypting, extracting, and analyzing crypto/forensics challenges.

## How it works

Cryptalyzer models each file as a Blob object.
Each blob should be able to:

* load some data as a blob
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
- analyze randomness of data
- in-place blob operations
- produce arrays of bitstrings
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
