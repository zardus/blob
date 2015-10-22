import blob
import operator
import random

def test_factor():
	for _ in range(100):
		num_terms = random.randrange(2, 8)
		terms = [ random.randrange(1, 64) for _ in range(num_terms) ]
		product = reduce(operator.__mul__, terms, 1)
		p_factor = blob.utils.factor(product)
		t_factors = sum((blob.utils.factor(t) for t in terms), [ ])
		assert sorted(p_factor) == sorted(t_factors)
		assert reduce(operator.__mul__, p_factor) == product

	# some special behavior
	assert blob.utils.factor(3) == [ 3 ]
	assert blob.utils.factor(17) == [ 17 ]
	assert blob.utils.factor(0) == [ 0 ]

def test_bitstr():
	#pylint:disable=unused-variable
	a_i,a_bs,a_s = 0b10101010, '10101010', '\xaa'
	b_i,b_bs,b_s = 0b01010101, '01010101', '\x55'
	c_i,c_bs,c_s = 0b11000101, '11000101', '\xc5'
	d_i,d_bs,d_s = 0b10111000, '10111000', '\xb8'
	e_i,e_bs,e_s = 0b01111101, '01111101', '\x7d'

	assert blob.utils.to_bitstr(a_s) == a_bs
	assert blob.utils.to_bitstr(b_s) == b_bs
	assert blob.utils.to_bitstr(c_s) == c_bs
	assert blob.utils.to_bitstr(d_s) == d_bs
	assert blob.utils.to_bitstr(e_s) == e_bs
	assert blob.utils.from_bitstr(a_bs) == a_s
	assert blob.utils.from_bitstr(b_bs) == b_s
	assert blob.utils.from_bitstr(c_bs) == c_s
	assert blob.utils.from_bitstr(d_bs) == d_s
	assert blob.utils.from_bitstr(e_bs) == e_s
	assert blob.utils.ror_bitstr(a_bs, 1) == b_bs
	assert blob.utils.ror_bitstr(c_bs, 3) == d_bs
	assert blob.utils.ror_bitstr(d_bs, -3) == c_bs
	assert blob.utils.xor_bitstr(d_bs, c_bs) == e_bs
	assert blob.utils.xor_bitstr(d_bs, e_bs) == c_bs
	assert blob.utils.xor_bitstr(c_bs, e_bs) == d_bs
	assert blob.utils.xor_bitstr('1110001100', '1') == '0001110011'

def test_str():
	assert blob.utils.xor_str(' ', 'secret') == 'SECRET'
	assert blob.utils.xor_str('secret', ' ') == 'SECRET'
	assert blob.utils.xor_str('\x01\x01\x01\x01', '\x10\x10\x10\x10') == '\x11\x11\x11\x11'
	assert blob.utils.xor_str('\x11', '\xff\xfe\x10\x11') == '\xee\xef\x01\x00'

	assert blob.utils.and_str(blob.utils.xor_str(' ','\xff'), 'secret') == 'SECRET'
	assert blob.utils.and_str('\x01\x01\x01\x01', '\x10\x10\x10\x10') == '\x00\x00\x00\x00'
	assert blob.utils.and_str('\x11', '\xff\xfe\x10\x11') == '\x11\x10\x10\x11'

	assert blob.utils.or_str(' ', 'SECRET') == 'secret'
	assert blob.utils.or_str('\x01\x01\x01\x01', '\x10\x10\x10\x10') == '\x11\x11\x11\x11'
	assert blob.utils.or_str('\x11', '\xff\xfe\x10\x11') == '\xff\xff\x11\x11'

	assert blob.utils.not_str('SECRET') == blob.utils.xor_str('SECRET', '\xff')
	assert blob.utils.not_str('\x01\x01\x01\x01') == '\xfe\xfe\xfe\xfe'
	assert blob.utils.not_str('\xff\xfe\x10\x11') == '\x00\x01\xef\xee'

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
