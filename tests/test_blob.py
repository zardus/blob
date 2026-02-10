import pytest
import random

import blob


# --- Construction ---

class TestConstruction:
    def test_from_bytes(self):
        b = blob.Blob(data=b"ABCD")
        assert b.data == b"ABCD"

    def test_from_str_auto_encodes(self):
        b = blob.Blob(data="ABCD")
        assert b.data == b"ABCD"

    def test_from_bits(self):
        b = blob.Blob(data_bits='01000001010000100100001101000100')
        assert b.data == b"ABCD"

    def test_from_file(self, tmp_path):
        p = tmp_path / "test.bin"
        p.write_bytes(b"hello")
        b = blob.Blob(filename="test.bin", dirname=str(tmp_path))
        assert b.data == b"hello"

    def test_empty_blob(self):
        b = blob.Blob(data=b"")
        assert b.size == 0
        assert b.size_bits == 0

    def test_single_byte(self):
        b = blob.Blob(data=b"\x00")
        assert b.size == 1
        assert b.size_bits == 8

    def test_none_data(self):
        b = blob.Blob()
        # No data set at all - accessing data will fail, but construction succeeds
        assert b._data_bytes is None
        assert b._data_bits is None


# --- Size ---

class TestSize:
    def test_size_bytes(self):
        b = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        assert b.size == 16
        assert b.size_bits == 16 * 8

    def test_size_from_bits(self):
        b = blob.Blob(data_bits=blob.utils.to_bitstr(b"AAAABBBBCCCCDDDD"))
        assert b.size == 16
        assert b.size_bits == 16 * 8

    def test_byte_aligned(self):
        b = blob.Blob(data=b"AB")
        assert b.byte_aligned is True

    def test_not_byte_aligned(self):
        b = blob.Blob(data_bits="111")
        assert b.byte_aligned is False


# --- Equality ---

class TestEquality:
    def test_eq_blobs(self):
        a = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        b = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        assert a == b

    def test_eq_bytes(self):
        a = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        assert a == b"AAAABBBBCCCCDDDD"

    def test_eq_str(self):
        a = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        assert a == "AAAABBBBCCCCDDDD"

    def test_neq(self):
        a = blob.Blob(data=b"AAAA")
        b = blob.Blob(data=b"BBBB")
        assert not (a == b)

    def test_hash_consistent(self):
        a = blob.Blob(data=b"ABCD")
        b = blob.Blob(data=b"ABCD")
        assert hash(a) == hash(b)

    def test_hash_in_set(self):
        a = blob.Blob(data=b"ABCD")
        b = blob.Blob(data=b"ABCD")
        s = {a}
        assert b in s

    def test_repr_bytes(self):
        a = blob.Blob(data=b"AB")
        r = repr(a)
        assert r.startswith("B(")

    def test_repr_bits(self):
        a = blob.Blob(data_bits="111")
        r = repr(a)
        assert "b'" in r


# --- Bitwise Operations ---

class TestBitops:
    def test_xor(self):
        a = blob.Blob(data=b'ABCD')
        b = blob.Blob(data=b'    ')
        assert (a ^ b).data == b'abcd'

    def test_or(self):
        a = blob.Blob(data=b'ABCD')
        b = blob.Blob(data=b'    ')
        assert (a | b).data == b'abcd'

    def test_or_with_str(self):
        a = blob.Blob(data=b"AAAABBBBCCCCDDDD")
        assert a | b'\x20' == b'aaaabbbbccccdddd'

    def test_and(self):
        a = blob.Blob(data=b'ABCD')
        b = blob.Blob(data=b'    ')
        assert (a & b).data == b'\x00\x00\x00\x00'

    def test_invert(self):
        c = blob.Blob(data=b'\x21\xff\xee\x11')
        assert (~c).data == b'\xde\x00\x11\xee'

    def test_ixor(self):
        a = blob.Blob(data=b'ABCD')
        b = blob.Blob(data=b'    ')
        a |= b
        assert a.data == b'abcd'
        a ^= b
        assert a.data == b'ABCD'

    def test_iand(self):
        a = blob.Blob(data=b'ABCD')
        b = blob.Blob(data=b'    ')
        a &= b
        assert a.data == b'\x00\x00\x00\x00'

    def test_xor_identity(self):
        a = blob.Blob(data=b'\x00\x00\x00\x00')
        b = blob.Blob(data=b'ABCD')
        assert (a ^ b).data == b'ABCD'

    def test_xor_self_is_zero(self):
        a = blob.Blob(data=b'ABCD')
        result = a ^ a
        assert result.data == b'\x00\x00\x00\x00'

    def test_invert_twice_is_identity(self):
        a = blob.Blob(data=b'ABCD')
        assert (~(~a)).data == b'ABCD'

    def test_xor_all_ones(self):
        a = blob.Blob(data=b'\xff\xff')
        b = blob.Blob(data=b'\xff\xff')
        assert (a ^ b).data == b'\x00\x00'

    def test_and_all_ones(self):
        a = blob.Blob(data=b'\xff\xff')
        b = blob.Blob(data=b'AB')
        assert (a & b).data == b'AB'


# --- Concatenation ---

class TestAdd:
    def test_add(self):
        a = blob.Blob(data=b"A")
        b = blob.Blob(data=b"b")
        assert a + b == blob.Blob(data=b"Ab")
        assert b + a == blob.Blob(data=b"bA")
        assert b + a + a + b == blob.Blob(data=b"bAAb")

    def test_add_empty(self):
        a = blob.Blob(data=b"A")
        e = blob.Blob(data=b"")
        assert (a + e).data == b"A"
        assert (e + a).data == b"A"

    def test_add_bits(self):
        a = blob.Blob(data_bits="111")
        b = blob.Blob(data_bits="000")
        result = a + b
        assert result.data_bits == "111000"


# --- Rotation ---

class TestRol:
    def test_rol_bytes(self):
        a = blob.Blob(data=b"ABCD")
        assert a.rol(0) == b"ABCD"
        assert a.rol(1) == b"BCDA"
        assert a.rol(2) == b"CDAB"
        assert a.rol(3) == b"DABC"
        assert a.rol(4) == b"ABCD"

    def test_rol_negative(self):
        a = blob.Blob(data=b"ABCD")
        assert a.rol(-1) == b"DABC"
        assert a.rol(-2) == b"CDAB"
        assert a.rol(-3) == b"BCDA"
        assert a.rol(-4) == b"ABCD"

    def test_rol_wrap(self):
        a = blob.Blob(data=b"ABCD")
        assert a.rol(5) == b"BCDA"
        assert a.rol(8) == b"ABCD"

    def test_rol_bits(self):
        a = blob.Blob(data=b"ABCD")
        assert a.rol(float(0) * 8) == b"ABCD"
        assert a.rol(float(1) * 8) == b"BCDA"
        assert a.rol(float(2) * 8) == b"CDAB"
        assert a.rol(float(3) * 8) == b"DABC"
        assert a.rol(float(4) * 8) == b"ABCD"

    def test_rol_bits_negative(self):
        a = blob.Blob(data=b"ABCD")
        assert a.rol(float(-1) * 8) == b"DABC"
        assert a.rol(float(-4) * 8) == b"ABCD"

    def test_rol_invalid_type(self):
        a = blob.Blob(data=b"ABCD")
        with pytest.raises(ValueError):
            a.rol("3")


# --- Block Size Candidates ---

class TestBlocks:
    def test_blocksize_bits_candidates(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        bs = b.blocksize_bits_candidates()
        assert bs == [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]

    def test_blocksize_candidates(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        bs = b.blocksize_candidates()
        assert bs == [1, 2, 3, 4, 6]

    def test_blocksize_min_blocks(self):
        b = blob.Blob(data=b"AABB")
        bs = b.blocksize_candidates(min_blocks=4)
        assert all(b.size // s >= 4 for s in bs)

    def test_blocksize_min_blocksize(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        bs = b.blocksize_candidates(min_blocksize=2)
        assert all(s >= 2 for s in bs)


# --- Split ---

class TestSplit:
    def test_split_n(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(n=3) == [blob.Blob(data=d) for d in (b'AAAA', b'BBBB', b'CCCC')]

    def test_split_size(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(size=3) == [blob.Blob(data=d) for d in (b'AAA', b'ABB', b'BBC', b'CCC')]

    def test_split_size_maxsplit(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(size=3, maxsplit=2) == [blob.Blob(data=d) for d in (b'AAA', b'ABB', b'BBCCCC')]

    def test_split_size_bits(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(size_bits=16) == [blob.Blob(data=d) for d in (b'AA', b'AA', b'BB', b'BB', b'CC', b'CC')]

    def test_split_size_bits_maxsplit(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(size_bits=16, maxsplit=3) == [blob.Blob(data=d) for d in (b'AA', b'AA', b'BB', b'BBCCCC')]

    def test_split_sep(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(sep=b'B') == [blob.Blob(data=d) for d in (b'AAAA', b'CCCC')]

    def test_split_sep_str(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(sep='B') == [blob.Blob(data=d) for d in (b'AAAA', b'CCCC')]

    def test_split_sep_allow_empty(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        result = b.split(sep=b'B', allow_empty=True)
        assert result == [blob.Blob(data=d) for d in (b'AAAA', b'', b'', b'', b'CCCC')]

    def test_split_sep_bits(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.split(sep_bits="01000010") == [blob.Blob(data=d) for d in (b'AAAA', b'CCCC')]

    def test_split_by_sep_with_maxsplit(self):
        c = blob.Blob(data=b"ABABABABA")
        assert c.split(sep=b'B') == [blob.Blob(data=d) for d in (b'A', b'A', b'A', b'A', b'A')]
        assert c.split(sep=b'B', maxsplit=2) == [blob.Blob(data=d) for d in (b'A', b'A', b'ABABA')]

    def test_split_sep_bits_maxsplit(self):
        c = blob.Blob(data=b"ABABABABA")
        assert c.split(sep_bits='01000010', maxsplit=3) == [blob.Blob(data=d) for d in (b'A', b'A', b'A', b'ABA')]

    def test_split_single_byte(self):
        b = blob.Blob(data=b"ABCD")
        parts = b.split(size=1)
        assert len(parts) == 4
        assert parts[0] == b"A"
        assert parts[3] == b"D"


# --- MP Split ---

class TestMpSplit:
    def test_mp_split(self):
        try:
            import mulpyplexer  # noqa: F401
        except ImportError:
            pytest.skip("mulpyplexer not installed")

        b = blob.Blob(data=b"AAAABBBBCCCC")
        omg_mp = b.mp_split(size=4).truncate(3).split(size=1).mp_flatten().mp_items
        assert omg_mp == [blob.Blob(data=d) for d in (b'A', b'A', b'A', b'B', b'B', b'B', b'C', b'C', b'C')]

    def test_mp_split_unavailable(self):
        import blob.blob as bb
        orig = bb._mp_fail
        bb._mp_fail = True
        try:
            b = blob.Blob(data=b"ABCD")
            with pytest.raises(blob.blob.BlobError):
                b.mp_split(size=2)
        finally:
            bb._mp_fail = orig


# --- Offset ---

class TestOffset:
    def test_offset_bytes(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.offset(offset=2) == blob.Blob(data=b"AABBBBCCCC")

    def test_offset_bits(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.offset(offset_bits=32) == blob.Blob(data=b"BBBBCCCC")

    def test_offset_sep(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.offset(sep=b"C") == blob.Blob(data=b"CCCC")

    def test_offset_sep_bits(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.offset(sep_bits="01000010") == blob.Blob(data=b"BBBBCCCC")

    def test_offset_sep_str(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.offset(sep="C") == blob.Blob(data=b"CCCC")


# --- Truncate ---

class TestTruncate:
    def test_truncate_negative(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(-1) == blob.Blob(data=b"ABC")

    def test_truncate_positive(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(1) == blob.Blob(data=b"A")

    def test_truncate_bits(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(offset_bits=16) == blob.Blob(data=b"AB")

    def test_truncate_sep(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(sep=b"C") == blob.Blob(data=b"AB")

    def test_truncate_sep_str(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(sep="C") == blob.Blob(data=b"AB")

    def test_truncate_sep_bits(self):
        a = blob.Blob(data=b"ABCD")
        assert a.truncate(sep_bits="01000010") == blob.Blob(data=b"A")


# --- Unpack ---

class TestUnpack:
    def test_unpack_big_endian(self):
        b = blob.Blob(data=b"AABBBBCC")
        assert b.unpack('>I') == [0x41414242, 0x42424343]

    def test_unpack_native(self):
        b = blob.Blob(data=b"AABBBBCC")
        assert b.unpack('H') == [0x4141, 0x4242, 0x4242, 0x4343]

    def test_unpack_little_endian(self):
        b = blob.Blob(data=b"AABBBBCC")
        assert b.unpack('<I') == [0x42424141, 0x43434242]

    def test_unpack_char(self):
        b = blob.Blob(data=b"AABBBBCC")
        assert b.unpack('c') == [b'A', b'A', b'B', b'B', b'B', b'B', b'C', b'C']

    def test_unpack_from_bits(self):
        b = blob.Blob(data_bits=blob.utils.to_bitstr(b"AABBBBCC"))
        assert b.unpack('>I') == [0x41414242, 0x42424343]

    def test_unpack_bad_size(self):
        b = blob.Blob(data=b"ABC")
        with pytest.raises(blob.blob.BlobError):
            b.unpack('>I')

    def test_unpack_single(self):
        b = blob.Blob(data=b"ABCD")
        result = b.unpack('>I', repeat=False)
        assert result == (0x41424344,)

    def test_unpack_single_bad_size(self):
        b = blob.Blob(data=b"AABBBBCC")
        with pytest.raises(blob.blob.BlobError):
            b.unpack('>I', repeat=False)


# --- Bit/Byte Conversion ---

class TestBitByte:
    def test_data_to_bits_and_back(self):
        a = blob.Blob(data=b"ABCD")
        assert a.data == b"ABCD"
        assert a.data_bits == blob.utils.to_bitstr(b"ABCD")
        assert a.data == b"ABCD"
        assert a.size == 4
        assert a.size_bits == 32

    def test_bits_to_data_and_back(self):
        a = blob.Blob(data_bits=blob.utils.to_bitstr(b"ABCD"))
        assert a.data == b"ABCD"
        assert a.data_bits == blob.utils.to_bitstr(b"ABCD")
        assert a.data == b"ABCD"
        assert a.size == 4
        assert a.size_bits == 32

    def test_lazy_conversion(self):
        a = blob.Blob(data=b"ABCD")
        assert a._data_bits is None  # Not yet computed
        _ = a.data_bits
        assert a._data_bits is not None  # Now computed


# --- Indexing ---

class TestGetItem:
    def test_int_index(self):
        a = blob.Blob(data=b"ABCDEFGHIJKLMNOPQRSTUVWX")
        assert a[1] == blob.Blob(data=b"B")

    def test_negative_index(self):
        a = blob.Blob(data=b"ABCDEFGHIJKLMNOPQRSTUVWX")
        assert a[-2] == blob.Blob(data=b"W")

    def test_byte_slice(self):
        s = b"ABCDEFGHIJKLMNOPQRSTUVWX"
        a = blob.Blob(data=s)
        assert a[1:-1] == blob.Blob(data=s[1:-1])

    def test_byte_slice_with_step(self):
        s = b"ABCDEFGHIJKLMNOPQRSTUVWX"
        a = blob.Blob(data=s)
        assert a[1:-1:5] == blob.Blob(data=s[1:-1:5])
        assert a[::8] == blob.Blob(data=s[::8])

    def test_bit_slice(self):
        a = blob.Blob(data=b"ABCDEFGHIJKLMNOPQRSTUVWX")
        assert a[0.::8] == blob.Blob(data=b'\x00\x00\x00')  #pylint:disable=invalid-slice-index
        assert a[1.:9.] == blob.Blob(data=b'\x82')  #pylint:disable=invalid-slice-index

    def test_first_byte(self):
        a = blob.Blob(data=b"AB")
        assert a[0] == blob.Blob(data=b"A")

    def test_last_byte(self):
        a = blob.Blob(data=b"AB")
        assert a[-1] == blob.Blob(data=b"B")


# --- Entropy ---

class TestEntropy:
    @pytest.fixture(autouse=True)
    def check_scipy(self):
        try:
            import scipy.stats  # noqa: F401
        except ImportError:
            pytest.skip("scipy not installed")

    def test_entropy_basic(self):
        a = blob.Blob(data=b"AABBBBCC")
        assert a.entropy(blocksize=1) == 1.5

    def test_entropy_uniform(self):
        b = blob.Blob(data=b"AAAABBBBCCCC")
        assert b.entropy(blocksize=1) == pytest.approx(1.584962500721156)

    def test_entropy_binary(self):
        c = blob.Blob(data=b"ABABABABABABABABABABABABABABAB")
        assert c.entropy(blocksize=1) == 1

    def test_entropy_block2(self):
        c = blob.Blob(data=b"ABABABABABABABABABABABABABABAB")
        assert c.entropy(blocksize=2) == 0

    def test_entropy_block3(self):
        c = blob.Blob(data=b"ABABABABABABABABABABABABABABAB")
        assert c.entropy(blocksize=3) == 1

    def test_entropy_constant(self):
        d = blob.Blob(data=b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        assert d.entropy(blocksize=1) == 0

    def test_entropy_max(self):
        e = blob.Blob(data=bytes(range(256)))
        assert round(e.entropy(blocksize=1), 5) == 8.0

    def test_entropy_no_scipy(self):
        import blob.blob as bb
        orig = bb._scipy_fail
        bb._scipy_fail = True
        try:
            b = blob.Blob(data=b"AABB")
            with pytest.raises(blob.blob.BlobError):
                b.entropy(blocksize=1)
        finally:
            bb._scipy_fail = orig


# --- Chi-Square ---

class TestChiSquare:
    @pytest.fixture(autouse=True)
    def check_scipy(self):
        try:
            import scipy.stats  # noqa: F401
        except ImportError:
            pytest.skip("scipy not installed")

    def test_chisquare_random_vs_nonrandom(self):
        random_data = bytes(random.randrange(0, 256) for _ in range(512 * 1024))
        nr = blob.Blob(data=b'A' * 1024 + b'BBBBB')

        c_r = blob.Blob(data=random_data).chisquare(blocksize=1)
        c_nr = nr.chisquare(blocksize=1)

        # Random data should have lower chi-square statistic
        assert c_r[0] < c_nr[0]
        # Random data should have higher p-value
        assert c_r[1] > c_nr[1]

    def test_chisquare_returns_list(self):
        b = blob.Blob(data=b"AABBCCDD")
        result = b.chisquare(blocksize=1)
        assert isinstance(result, list)
        assert len(result) == 2


# --- Rotating XORs ---

class TestRotatingXors:
    def test_rotating_xors(self):
        a = blob.Blob(data=b"\x01\x02\x04\x08")
        expected = [
            b"\x00\x00\x00\x00",
            b"\x03\x06\x0c\x09",
            b"\x05\x0a\x05\x0a",
            b"\x09\x03\x06\x0c",
        ]
        assert list(a.rotating_xors()) == expected

    def test_rotating_xors_other(self):
        a = blob.Blob(data=b"\xff\x00")
        b = blob.Blob(data=b"\x0f\xf0")
        results = list(a.rotating_xors(other=b))
        assert len(results) == 2

    def test_rotating_xors_single_byte(self):
        a = blob.Blob(data=b"\xAA")
        results = list(a.rotating_xors())
        assert len(results) == 1
        assert results[0].data == b"\x00"


# --- Count Elements ---

class TestCountElements:
    def test_count_single(self):
        a = blob.Blob(data=b"AABCDDDD")
        assert a.count_elements({b"A"}) == 2

    def test_count_multiple(self):
        a = blob.Blob(data=b"AABCDDDD")
        assert a.count_elements({b"D"}) == 4
        assert a.count_elements({b"A", b"D"}) == 6
        assert a.count_elements({b"C", b"D"}) == 5

    def test_count_from_bits(self):
        a = blob.Blob(data=b"AABCDDDD")
        assert a.count_elements({blob.Blob(data_bits=blob.utils.to_bitstr(b"A"))}) == 2

    def test_count_zero(self):
        a = blob.Blob(data=b"AABCDDDD")
        assert a.count_elements({b"Z"}) == 0


# --- Justify ---

class TestJust:
    def test_ljust(self):
        a = blob.Blob(data=b"A")
        assert a.ljust(4) == b"A   "

    def test_ljust_custom(self):
        a = blob.Blob(data=b"A")
        assert a.ljust(4, b'B') == b"ABBB"

    def test_ljust_bits(self):
        o = blob.Blob(data_bits="111")
        assert o.ljust(float(4)).data_bits == "1110"
        assert o.ljust(float(4), '1').data_bits == "1111"

    def test_rjust(self):
        a = blob.Blob(data=b"A")
        assert a.rjust(4) == b"   A"

    def test_rjust_custom(self):
        a = blob.Blob(data=b"A")
        assert a.rjust(4, b'B') == b"BBBA"

    def test_rjust_bits(self):
        o = blob.Blob(data_bits="111")
        assert o.rjust(float(4)).data_bits == "0111"
        assert o.rjust(float(4), '1').data_bits == "1111"

    def test_ljust_invalid_type(self):
        a = blob.Blob(data=b"A")
        with pytest.raises(ValueError):
            a.ljust("4")

    def test_rjust_invalid_type(self):
        a = blob.Blob(data=b"A")
        with pytest.raises(ValueError):
            a.rjust("4")


# --- Edge Cases ---

class TestEdgeCases:
    def test_blobify_invalid(self):
        from blob.blob import _blobify, BlobError
        with pytest.raises(BlobError):
            _blobify(12345)

    def test_separator_not_found(self):
        b = blob.Blob(data=b"ABCD")
        with pytest.raises(blob.blob.BlobError):
            b.offset(sep=b"Z")

    def test_separator_bits_not_found(self):
        b = blob.Blob(data=b"ABCD")
        with pytest.raises(blob.blob.BlobError):
            b.offset(sep_bits="11111111111111111")

    def test_all_zero_bytes(self):
        b = blob.Blob(data=b"\x00\x00\x00\x00")
        assert b.size == 4
        assert (~b).data == b"\xff\xff\xff\xff"

    def test_all_ff_bytes(self):
        b = blob.Blob(data=b"\xff\xff\xff\xff")
        assert (~b).data == b"\x00\x00\x00\x00"

    def test_binary_data_roundtrip(self):
        data = bytes(range(256))
        b = blob.Blob(data=data)
        assert b.data == data
        # Force bit conversion and back
        _ = b.data_bits
        assert b.data == data

    def test_large_blob(self):
        data = b"X" * 10000
        b = blob.Blob(data=data)
        assert b.size == 10000
        parts = b.split(size=1000)
        assert len(parts) == 10

    def test_alias_B(self):
        b = blob.B(data=b"test")
        assert b.data == b"test"
