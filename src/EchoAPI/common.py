import hashlib

def hash(data, algorithm = None):
	if not algorithm:
		algorithm = "sha512"
	if type(data) == str:
		data = data.encode("utf-8")
	hash = hashlib.new(algorithm)
	hash.update(data)
	return hash
