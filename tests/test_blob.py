import cryptalyzer

def test_size():
    b = cryptalyzer.Blob(data="AAAABBBBCCCCDDDD")
    assert b.size_bytes == 16
    assert b.size_bits == 16*8

def test_blocks():
    b = cryptalyzer.Blob(data="AAAABBBBCCCC")

    bs_bits_candidates = b.blocksize_bits_candidates()
    bs_bytes_candidates = b.blocksize_bytes_candidates()
    assert bs_bits_candidates == [ 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 ]
    assert bs_bytes_candidates == [ 1, 2, 3, 4, 6 ]

def run_all():
    for n,f in globals().iteritems():
        if n.startswith('test'):
            print "RUNNING",n
            try:
                f()
                print "SUCCESS"
            except Exception:
                print "FAIL"
                raise

if __name__ == '__main__':
    run_all()
