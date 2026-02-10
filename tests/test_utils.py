import functools
import operator
import random

import blob


# --- Factoring ---

class TestFactor:
    def test_factor_random(self):
        for _ in range(100):
            num_terms = random.randrange(2, 8)
            terms = [random.randrange(1, 64) for _ in range(num_terms)]
            product = functools.reduce(operator.__mul__, terms, 1)
            p_factor = blob.utils.factor(product)
            t_factors = sum((blob.utils.factor(t) for t in terms), [])
            assert sorted(p_factor) == sorted(t_factors)
            assert functools.reduce(operator.__mul__, p_factor) == product

    def test_factor_prime(self):
        assert blob.utils.factor(3) == [3]
        assert blob.utils.factor(17) == [17]

    def test_factor_zero(self):
        assert blob.utils.factor(0) == [0]

    def test_factor_small_composites(self):
        assert sorted(blob.utils.factor(12)) == [2, 2, 3]
        assert sorted(blob.utils.factor(100)) == [2, 2, 5, 5]

    def test_factor_one(self):
        result = blob.utils.factor(1)
        assert result == [] or result == [1]

    def test_factor_power_of_two(self):
        result = sorted(blob.utils.factor(64))
        assert functools.reduce(operator.__mul__, result) == 64


# --- Bit String Conversions ---

class TestBitStr:
    def test_to_bitstr(self):
        assert blob.utils.to_bitstr(b'\xaa') == '10101010'
        assert blob.utils.to_bitstr(b'\x55') == '01010101'
        assert blob.utils.to_bitstr(b'\xc5') == '11000101'
        assert blob.utils.to_bitstr(b'\xb8') == '10111000'
        assert blob.utils.to_bitstr(b'\x7d') == '01111101'

    def test_from_bitstr(self):
        assert blob.utils.from_bitstr('10101010') == b'\xaa'
        assert blob.utils.from_bitstr('01010101') == b'\x55'
        assert blob.utils.from_bitstr('11000101') == b'\xc5'
        assert blob.utils.from_bitstr('10111000') == b'\xb8'
        assert blob.utils.from_bitstr('01111101') == b'\x7d'

    def test_roundtrip(self):
        for val in [b'\x00', b'\xff', b'\x42', b'\xab\xcd']:
            assert blob.utils.from_bitstr(blob.utils.to_bitstr(val)) == val

    def test_ror_bitstr(self):
        assert blob.utils.ror_bitstr('10101010', 1) == '01010101'
        assert blob.utils.ror_bitstr('11000101', 3) == '10111000'
        assert blob.utils.ror_bitstr('10111000', -3) == '11000101'

    def test_ror_bitstr_full_rotation(self):
        s = '10101010'
        assert blob.utils.ror_bitstr(s, 8) == s

    def test_xor_bitstr(self):
        assert blob.utils.xor_bitstr('10111000', '11000101') == '01111101'
        assert blob.utils.xor_bitstr('10111000', '01111101') == '11000101'
        assert blob.utils.xor_bitstr('11000101', '01111101') == '10111000'

    def test_xor_bitstr_cycle(self):
        assert blob.utils.xor_bitstr('1110001100', '1') == '0001110011'

    def test_xor_bitstr_identity(self):
        s = '10101010'
        assert blob.utils.xor_bitstr(s, '00000000') == s

    def test_xor_bitstr_self(self):
        s = '10101010'
        assert blob.utils.xor_bitstr(s, s) == '00000000'


# --- Byte String Operations ---

class TestStr:
    def test_xor_str_basic(self):
        assert blob.utils.xor_str(b' ', b'secret') == b'SECRET'
        assert blob.utils.xor_str(b'secret', b' ') == b'SECRET'

    def test_xor_str_exact(self):
        assert blob.utils.xor_str(b'\x01\x01\x01\x01', b'\x10\x10\x10\x10') == b'\x11\x11\x11\x11'

    def test_xor_str_cycle(self):
        assert blob.utils.xor_str(b'\x11', b'\xff\xfe\x10\x11') == b'\xee\xef\x01\x00'

    def test_and_str(self):
        mask = blob.utils.xor_str(b' ', b'\xff')
        assert blob.utils.and_str(mask, b'secret') == b'SECRET'
        assert blob.utils.and_str(b'\x01\x01\x01\x01', b'\x10\x10\x10\x10') == b'\x00\x00\x00\x00'
        assert blob.utils.and_str(b'\x11', b'\xff\xfe\x10\x11') == b'\x11\x10\x10\x11'

    def test_or_str(self):
        assert blob.utils.or_str(b' ', b'SECRET') == b'secret'
        assert blob.utils.or_str(b'\x01\x01\x01\x01', b'\x10\x10\x10\x10') == b'\x11\x11\x11\x11'
        assert blob.utils.or_str(b'\x11', b'\xff\xfe\x10\x11') == b'\xff\xff\x11\x11'

    def test_not_str(self):
        assert blob.utils.not_str(b'SECRET') == blob.utils.xor_str(b'SECRET', b'\xff')
        assert blob.utils.not_str(b'\x01\x01\x01\x01') == b'\xfe\xfe\xfe\xfe'
        assert blob.utils.not_str(b'\xff\xfe\x10\x11') == b'\x00\x01\xef\xee'

    def test_xor_str_identity(self):
        data = b'\xab\xcd\xef'
        assert blob.utils.xor_str(data, b'\x00\x00\x00') == data

    def test_xor_str_self_is_zero(self):
        data = b'\xab\xcd\xef'
        assert blob.utils.xor_str(data, data) == b'\x00\x00\x00'

    def test_not_str_involution(self):
        data = b'\xab\xcd\xef'
        assert blob.utils.not_str(blob.utils.not_str(data)) == data

    def test_and_str_with_ones(self):
        data = b'\xab\xcd\xef'
        assert blob.utils.and_str(data, b'\xff\xff\xff') == data

    def test_or_str_with_zeros(self):
        data = b'\xab\xcd\xef'
        assert blob.utils.or_str(data, b'\x00\x00\x00') == data


# --- Insert Separators ---

class TestInsertSeparators:
    def test_basic(self):
        assert blob.utils.insert_separators('AABBCCDD', '-', 2) == 'AA-BB-CC-DD'

    def test_no_split(self):
        assert blob.utils.insert_separators('AB', '-', 4) == 'AB'

    def test_single_char(self):
        assert blob.utils.insert_separators('ABCD', '.', 1) == 'A.B.C.D'
