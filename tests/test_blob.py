import cryptalyzer
import random

def test_size():
    b = cryptalyzer.Blob(data="AAAABBBBCCCCDDDD")
    assert b.size_bytes == 16
    assert b.size_bits == 16*8

    b = cryptalyzer.Blob(data_bits=cryptalyzer.utils.to_bitstr("AAAABBBBCCCCDDDD"))
    assert b.size_bytes == 16
    assert b.size_bits == 16*8

def test_eq():
    b = cryptalyzer.Blob(data="AAAABBBBCCCCDDDD")
    a = cryptalyzer.Blob(data="AAAABBBBCCCCDDDD")

    assert a == b
    assert a == "AAAABBBBCCCCDDDD"

    assert a | '\x20' == 'aaaabbbbccccdddd'

def test_add():
    a = cryptalyzer.Blob(data="A")
    b = cryptalyzer.Blob(data="b")

    assert a+b == cryptalyzer.Blob(data="Ab")
    assert b+a == cryptalyzer.Blob(data="bA")
    assert b+a+a+b == cryptalyzer.Blob(data="bAAb")

def test_rol():
    a = cryptalyzer.Blob(data="ABCD")

    assert a.rol(-4) == "ABCD"
    assert a.rol(-3) == "BCDA"
    assert a.rol(-2) == "CDAB"
    assert a.rol(-1) == "DABC"
    assert a.rol(0) == "ABCD"
    assert a.rol(1) == "BCDA"
    assert a.rol(2) == "CDAB"
    assert a.rol(3) == "DABC"
    assert a.rol(4) == "ABCD"
    assert a.rol(5) == "BCDA"
    assert a.rol(6) == "CDAB"
    assert a.rol(7) == "DABC"
    assert a.rol(8) == "ABCD"

    assert a.rol(float(-4)*8) == "ABCD"
    assert a.rol(float(-3)*8) == "BCDA"
    assert a.rol(float(-2)*8) == "CDAB"
    assert a.rol(float(-1)*8) == "DABC"
    assert a.rol(float(0)*8) == "ABCD"
    assert a.rol(float(1)*8) == "BCDA"
    assert a.rol(float(2)*8) == "CDAB"
    assert a.rol(float(3)*8) == "DABC"
    assert a.rol(float(4)*8) == "ABCD"
    assert a.rol(float(5)*8) == "BCDA"
    assert a.rol(float(6)*8) == "CDAB"
    assert a.rol(float(7)*8) == "DABC"
    assert a.rol(float(8)*8) == "ABCD"

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
    assert b.split(bitsep="01000010") == [ cryptalyzer.Blob(data=i) for i in ('AAAA', 'CCCC') ]

    omg_mp = b.mp_split(bytesize=4).truncate(3).split(bytesize=1).mp_flatten().mp_items
    assert omg_mp == [ cryptalyzer.Blob(data=i) for i in ('A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C') ]

def test_offset():
    b = cryptalyzer.Blob(data="AAAABBBBCCCC")

    assert b.offset(byteoffset=2) == cryptalyzer.Blob(data="AABBBBCCCC")
    assert b.offset(bitoffset=32) == cryptalyzer.Blob(data="BBBBCCCC")
    assert b.offset(bytesep="C") == cryptalyzer.Blob(data="CCCC")
    assert b.offset(bitsep="01000010") == cryptalyzer.Blob("BBBBCCCC")

def test_unpack():
    b = cryptalyzer.Blob(data="AABBBBCC")
    assert b.unpack_struct('>I') == [ 0x41414242, 0x42424343 ]
    assert b.unpack_struct('H') == [ 0x4141, 0x4242, 0x4242, 0x4343 ]
    assert b.unpack_struct('<I') == [ 0x42424141, 0x43434242 ]
    assert b.unpack_struct('c') == list("AABBBBCC")

    b = cryptalyzer.Blob(data_bits=cryptalyzer.utils.to_bitstr("AABBBBCC"))
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

    a |= b
    assert a.data == 'abcd'
    a ^= b
    assert a.data == 'ABCD'
    a &= b
    assert a.data == '\x00\x00\x00\x00'

def test_entropy():
    a = cryptalyzer.Blob(data="AABBBBCC")
    b = cryptalyzer.Blob(data="AAAABBBBCCCC")
    c = cryptalyzer.Blob(data="ABABABABABABABABABABABABABABAB")
    d = cryptalyzer.Blob(data="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    e = cryptalyzer.Blob(data=''.join(chr(i) for i in range(256)))

    assert a.entropy(blocksize_bytes=1) == 1.5
    assert b.entropy(blocksize_bytes=1) == 1.584962500721156
    assert c.entropy(blocksize_bytes=1) == 1
    assert c.entropy(blocksize_bytes=3) == 1
    assert c.entropy(blocksize_bytes=2) == 0
    assert d.entropy(blocksize_bytes=1) == 0
    assert d.entropy(blocksize_bytes=3) == 0
    assert round(e.entropy(blocksize_bytes=1), 5) == 8.0

def test_chisquare():
    random_data = ''.join(chr(random.randrange(0, 256)) for _ in range(512*1024))

    r = cryptalyzer.Blob(data=random_data)
    br = cryptalyzer.Blob(data=cryptalyzer.utils.to_bitstr(random_data))
    lr = cryptalyzer.Blob(data=random_data+'A'*1024)
    nr = cryptalyzer.Blob(data='A'*1024+'BBBBB')

    c_r = r.chisquare(blocksize_bytes=1)
    c_br = br.chisquare(blocksize_bytes=1)
    c_lr = lr.chisquare(blocksize_bytes=1)
    c_nr = nr.chisquare(blocksize_bytes=1)

    assert c_br[0] < 2.0
    assert c_br[0] < c_r[0]
    assert c_br[0] < c_lr[0]
    assert c_r[0] < c_lr[0]
    assert c_lr[0] < c_nr[0]

    assert c_br[1] > c_r[1]
    assert c_r[1] > c_lr[1]
    assert c_lr[1] > c_nr[1]
test_chisquare.flag = False

def test_bitbyte():
    a = cryptalyzer.Blob(data="ABCD")

    assert a.data == "ABCD"
    assert a.data_bits == cryptalyzer.utils.to_bitstr("ABCD")
    assert a.data == "ABCD"
    assert a.size_bytes == 4
    assert a.size_bits == 32

    a = cryptalyzer.Blob(data_bits=cryptalyzer.utils.to_bitstr("ABCD"))

    assert a.data == "ABCD"
    assert a.data_bits == cryptalyzer.utils.to_bitstr("ABCD")
    assert a.data == "ABCD"
    assert a.size_bytes == 4
    assert a.size_bits == 32

def test_getitem():
    s = "ABCDEFGHIJKLMNOPQRSTUVWX"
    a = cryptalyzer.Blob(s)

    assert a[1] == cryptalyzer.Blob("B")
    # TODO: assert a[1.] == cryptalyzer.Blob("B")
    assert a[-2] == cryptalyzer.Blob("W")
    assert a[1:-1] == cryptalyzer.Blob(s[1:-1])
    assert a[1:-1:5] == cryptalyzer.Blob(s[1:-1:5])
    assert a[::8] == cryptalyzer.Blob(s[::8])
    assert a[0.::8] == cryptalyzer.Blob('\x00\x00\x00') #pylint:disable=invalid-slice-index
    assert a[1.:9.] == cryptalyzer.Blob(data='\x82') #pylint:disable=invalid-slice-index

def test_truncate():
    a = cryptalyzer.Blob(data="ABCD")

    assert a.truncate(-1) == cryptalyzer.Blob("ABC")
    assert a.truncate(1) == cryptalyzer.Blob("A")
    assert a.truncate(bitoffset=16) == cryptalyzer.Blob("AB")
    assert a.truncate(bytesep="C") == cryptalyzer.Blob("AB")
    assert a.truncate(bitsep="01000010") == cryptalyzer.Blob("A")

def run_all():
    for n,f in globals().iteritems():
        if n.startswith('test'):
            print "RUNNING",n
            try:
                if getattr(f, 'flag', True):
                    f()
                    print "SUCCESS"
                else:
                    print "SKIPPED"
            except Exception:
                print "FAIL"
                raise

if __name__ == '__main__':
    run_all()
