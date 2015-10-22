import blob
import random

def test_size():
    b = blob.Blob(data="AAAABBBBCCCCDDDD")
    assert b.size == 16
    assert b.size_bits == 16*8

    b = blob.Blob(data_bits=blob.utils.to_bitstr("AAAABBBBCCCCDDDD"))
    assert b.size == 16
    assert b.size_bits == 16*8

def test_eq():
    b = blob.Blob(data="AAAABBBBCCCCDDDD")
    a = blob.Blob(data="AAAABBBBCCCCDDDD")

    assert a == b
    assert a == "AAAABBBBCCCCDDDD"

    assert a | '\x20' == 'aaaabbbbccccdddd'

def test_add():
    a = blob.Blob(data="A")
    b = blob.Blob(data="b")

    assert a+b == blob.Blob(data="Ab")
    assert b+a == blob.Blob(data="bA")
    assert b+a+a+b == blob.Blob(data="bAAb")

def test_rol():
    a = blob.Blob(data="ABCD")

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
    b = blob.Blob(data="AAAABBBBCCCC")

    bs_bits_candidates = b.blocksize_bits_candidates()
    bs_bytes_candidates = b.blocksize_candidates()
    assert bs_bits_candidates == [ 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 ]
    assert bs_bytes_candidates == [ 1, 2, 3, 4, 6 ]

def test_split():
    b = blob.Blob(data="AAAABBBBCCCC")

    assert b.split(n=3) == [ blob.Blob(data=i) for i in ('AAAA', 'BBBB', 'CCCC') ]
    assert b.split(size=3) == [ blob.Blob(data=i) for i in ('AAA', 'ABB', 'BBC', 'CCC') ]
    assert b.split(size_bits=16) == [ blob.Blob(data=i) for i in ('AA', 'AA', 'BB', 'BB', 'CC', 'CC') ]
    assert b.split(sep='B') == [ blob.Blob(data=i) for i in ('AAAA', 'CCCC') ]
    assert b.split(sep='B', allow_empty=True) == [ blob.Blob(data=i) for i in ('AAAA', '','','', 'CCCC') ]
    assert b.split(sep_bits="01000010") == [ blob.Blob(data=i) for i in ('AAAA', 'CCCC') ]

def test_mp_split():
    b = blob.Blob(data="AAAABBBBCCCC")

    omg_mp = b.mp_split(size=4).truncate(3).split(size=1).mp_flatten().mp_items
    assert omg_mp == [ blob.Blob(data=i) for i in ('A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C') ]

def test_offset():
    b = blob.Blob(data="AAAABBBBCCCC")

    assert b.offset(offset=2) == blob.Blob(data="AABBBBCCCC")
    assert b.offset(offset_bits=32) == blob.Blob(data="BBBBCCCC")
    assert b.offset(sep="C") == blob.Blob(data="CCCC")
    assert b.offset(sep_bits="01000010") == blob.Blob("BBBBCCCC")

def test_unpack():
    b = blob.Blob(data="AABBBBCC")
    assert b.unpack('>I') == [ 0x41414242, 0x42424343 ]
    assert b.unpack('H') == [ 0x4141, 0x4242, 0x4242, 0x4343 ]
    assert b.unpack('<I') == [ 0x42424141, 0x43434242 ]
    assert b.unpack('c') == list("AABBBBCC")

    b = blob.Blob(data_bits=blob.utils.to_bitstr("AABBBBCC"))
    assert b.unpack('>I') == [ 0x41414242, 0x42424343 ]
    assert b.unpack('H') == [ 0x4141, 0x4242, 0x4242, 0x4343 ]
    assert b.unpack('<I') == [ 0x42424141, 0x43434242 ]
    assert b.unpack('c') == list("AABBBBCC")

def test_bitops():
    a = blob.Blob(data='ABCD')
    b = blob.Blob(data='    ')
    c = blob.Blob(data='\x21\xff\xee\x11')

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
    a = blob.Blob(data="AABBBBCC")
    b = blob.Blob(data="AAAABBBBCCCC")
    c = blob.Blob(data="ABABABABABABABABABABABABABABAB")
    d = blob.Blob(data="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
    e = blob.Blob(data=''.join(chr(i) for i in range(256)))

    assert a.entropy(blocksize=1) == 1.5
    assert b.entropy(blocksize=1) == 1.584962500721156
    assert c.entropy(blocksize=1) == 1
    assert c.entropy(blocksize=3) == 1
    assert c.entropy(blocksize=2) == 0
    assert d.entropy(blocksize=1) == 0
    assert d.entropy(blocksize=3) == 0
    assert round(e.entropy(blocksize=1), 5) == 8.0

def test_chisquare():
    random_data = ''.join(chr(random.randrange(0, 256)) for _ in range(512*1024))

    r = blob.Blob(data=random_data)
    br = blob.Blob(data=blob.utils.to_bitstr(random_data))
    lr = blob.Blob(data=random_data+'A'*1024)
    nr = blob.Blob(data='A'*1024+'BBBBB')

    c_r = r.chisquare(blocksize=1)
    c_br = br.chisquare(blocksize=1)
    c_lr = lr.chisquare(blocksize=1)
    c_nr = nr.chisquare(blocksize=1)

    assert c_br[0] < 3.0
    assert c_br[0] < c_r[0]
    assert c_br[0] < c_lr[0]
    assert c_r[0] < c_lr[0]
    assert c_lr[0] < c_nr[0]

    assert c_br[1] > c_r[1]
    assert c_r[1] > c_lr[1]
    assert c_lr[1] > c_nr[1]
test_chisquare.flag = False

def test_bitbyte():
    a = blob.Blob(data="ABCD")

    assert a.data == "ABCD"
    assert a.data_bits == blob.utils.to_bitstr("ABCD")
    assert a.data == "ABCD"
    assert a.size == 4
    assert a.size_bits == 32

    a = blob.Blob(data_bits=blob.utils.to_bitstr("ABCD"))

    assert a.data == "ABCD"
    assert a.data_bits == blob.utils.to_bitstr("ABCD")
    assert a.data == "ABCD"
    assert a.size == 4
    assert a.size_bits == 32

def test_getitem():
    s = "ABCDEFGHIJKLMNOPQRSTUVWX"
    a = blob.Blob(s)

    assert a[1] == blob.Blob("B")
    # TODO: assert a[1.] == blob.Blob("B")
    assert a[-2] == blob.Blob("W")
    assert a[1:-1] == blob.Blob(s[1:-1])
    assert a[1:-1:5] == blob.Blob(s[1:-1:5])
    assert a[::8] == blob.Blob(s[::8])
    assert a[0.::8] == blob.Blob('\x00\x00\x00') #pylint:disable=invalid-slice-index
    assert a[1.:9.] == blob.Blob(data='\x82') #pylint:disable=invalid-slice-index

def test_truncate():
    a = blob.Blob(data="ABCD")

    assert a.truncate(-1) == blob.Blob("ABC")
    assert a.truncate(1) == blob.Blob("A")
    assert a.truncate(offset_bits=16) == blob.Blob("AB")
    assert a.truncate(sep="C") == blob.Blob("AB")
    assert a.truncate(sep_bits="01000010") == blob.Blob("A")

def test_rotation_xors():
    a = blob.Blob(data="\x01\x02\x04\x08")

    assert list(a.rotating_xors()) == [ "\x00\x00\x00\x00", "\x03\x06\x0c\x09", "\x05\x0a\x05\x0a", "\x09\x03\x06\x0c" ]

def test_count_elements():
    a = blob.Blob(data="AABCDDDD")

    assert a.count_elements({"A"}) == 2
    assert a.count_elements({"D"}) == 4
    assert a.count_elements({"A", "D"}) == 6
    assert a.count_elements({"C", "D"}) == 5
    assert a.count_elements({blob.Blob(data_bits=blob.utils.to_bitstr("A"))}) == 2

def test_just():
    a = blob.Blob(data="A")
    o = blob.Blob(data_bits="111")

    assert a.ljust(4) == "A   "
    assert a.ljust(4, 'B') == "ABBB"
    assert o.ljust(float(4)).data_bits == "1110"
    assert o.ljust(float(4), '1').data_bits == "1111"

    assert a.rjust(4) == "   A"
    assert a.rjust(4, 'B') == "BBBA"
    assert o.rjust(float(4)).data_bits == "0111"
    assert o.rjust(float(4), '1').data_bits == "1111"

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
