import cryptalyzer

def test_size():
    b = cryptalyzer.Blob(data="AAAABBBBCCCCDDDD")
    assert b.size_bytes == 16
    assert b.size_bits == 16*8

    b = cryptalyzer.Blob(bitdata=cryptalyzer.utils.to_bitstr("AAAABBBBCCCCDDDD"))
    assert b.size_bytes == 16
    assert b.size_bits == 16*8

def test_blocks():
    b = cryptalyzer.Blob(data="AAAABBBBCCCC")

    bs_bits_candidates = b.blocksize_bits_candidates()
    bs_bytes_candidates = b.blocksize_bytes_candidates()
    assert bs_bits_candidates == [ 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 ]
    assert bs_bytes_candidates == [ 1, 2, 3, 4, 6 ]

def test_split():
    b = cryptalyzer.Blob(data="AAAABBBBCCCC")

    assert b.split(n=3) == [ cryptalyzer.Blob(data=i) for i in ('AAAA', 'BBBB', 'CCCC') ]
    assert b.split(bytesize=3) == [ cryptalyzer.Blob(data=i) for i in ('AAA', 'ABB', 'BBC', 'CCC') ]
    assert b.split(bitsize=16) == [ cryptalyzer.Blob(data=i) for i in ('AA', 'AA', 'BB', 'BB', 'CC', 'CC') ]
    assert b.split(bytesep='B') == [ cryptalyzer.Blob(data=i) for i in ('AAAA', 'CCCC') ]
    assert b.split(bytesep='B', allow_empty=True) == [ cryptalyzer.Blob(data=i) for i in ('AAAA', '','','', 'CCCC') ]

def test_unpack():
    b = cryptalyzer.Blob(data="AABBBBCC")
    assert b.unpack_struct('>I') == [ 0x41414242, 0x42424343 ]
    assert b.unpack_struct('H') == [ 0x4141, 0x4242, 0x4242, 0x4343 ]
    assert b.unpack_struct('<I') == [ 0x42424141, 0x43434242 ]
    assert b.unpack_struct('c') == list("AABBBBCC")

    b = cryptalyzer.Blob(bitdata=cryptalyzer.utils.to_bitstr("AABBBBCC"))
    assert b.unpack_struct('>I') == [ 0x41414242, 0x42424343 ]
    assert b.unpack_struct('H') == [ 0x4141, 0x4242, 0x4242, 0x4343 ]
    assert b.unpack_struct('<I') == [ 0x42424141, 0x43434242 ]
    assert b.unpack_struct('c') == list("AABBBBCC")

def test_bitops():
    a = cryptalyzer.Blob(data='ABCD')
    b = cryptalyzer.Blob(data='    ')
    c = cryptalyzer.Blob(data='\x21\xff\xee\x11')

    assert (a ^ b).data == 'abcd'
    assert (a | b).data == 'abcd'
    assert (a & b).data == '\x00\x00\x00\x00'
    assert (~c).data == '\xde\x00\x11\xee'

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
