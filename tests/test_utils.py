import cryptalyzer
import operator
import random

def test_factor():
	for _ in range(100):
		num_terms = random.randrange(2, 8)
		terms = [ random.randrange(1, 64) for _ in range(num_terms) ]
		product = reduce(operator.__mul__, terms, 1)
		p_factor = cryptalyzer.utils.factor(product)
		t_factors = sum((cryptalyzer.utils.factor(t) for t in terms), [ ])
		assert sorted(p_factor) == sorted(t_factors)
		assert reduce(operator.__mul__, p_factor) == product

	# some special behavior
	assert cryptalyzer.utils.factor(3) == [ 3 ]
	assert cryptalyzer.utils.factor(17) == [ 17 ]
	assert cryptalyzer.utils.factor(0) == [ 0 ]

def test_bitstr():
	#pylint:disable=unused-variable
	a_i,a_bs,a_s = 0b10101010, '10101010', '\xaa'
	b_i,b_bs,b_s = 0b01010101, '01010101', '\x55'
	c_i,c_bs,c_s = 0b11000101, '11000101', '\xc5'
	d_i,d_bs,d_s = 0b10111000, '10111000', '\xb8'
	e_i,e_bs,e_s = 0b01111101, '01111101', '\x7d'

	assert cryptalyzer.utils.to_bitstr(a_s) == a_bs
	assert cryptalyzer.utils.to_bitstr(b_s) == b_bs
	assert cryptalyzer.utils.to_bitstr(c_s) == c_bs
	assert cryptalyzer.utils.to_bitstr(d_s) == d_bs
	assert cryptalyzer.utils.to_bitstr(e_s) == e_bs
	assert cryptalyzer.utils.from_bitstr(a_bs) == a_s
	assert cryptalyzer.utils.from_bitstr(b_bs) == b_s
	assert cryptalyzer.utils.from_bitstr(c_bs) == c_s
	assert cryptalyzer.utils.from_bitstr(d_bs) == d_s
	assert cryptalyzer.utils.from_bitstr(e_bs) == e_s
	assert cryptalyzer.utils.ror_bitstr(a_bs, 1) == b_bs
	assert cryptalyzer.utils.ror_bitstr(c_bs, 3) == d_bs
	assert cryptalyzer.utils.ror_bitstr(d_bs, -3) == c_bs
	assert cryptalyzer.utils.xor_bitstr(d_bs, c_bs) == e_bs
	assert cryptalyzer.utils.xor_bitstr(d_bs, e_bs) == c_bs
	assert cryptalyzer.utils.xor_bitstr(c_bs, e_bs) == d_bs

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
