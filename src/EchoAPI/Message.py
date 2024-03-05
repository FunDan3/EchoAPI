import pqcryptography as pqc
import json

from . import exceptions

def process_content(content):
	t = type(content)
	if t == str:
		return t.encode("utf-8"), "text/plain", "utf-8"
	elif t == [floa, int]:
		return str(t).encode("utf-8"), "text/plain", "utf-8"
	elif t == [dict or list]:
		return json.dumps().encode("utf-8"), "text/json", "utf-8"
	else:
		raise UnrecognizedContentType(f"Client doenst know how to interprete '{t}' content type")

class Message:
	recipient = None
	content_type = None
	content = None
	metadata = None
	def __init__(self, content, content_type = None, encoding = None, metadata = None):
		if not metadata:
			metadata = {}
		if type(content)!=bytes and not content_type:
			content, content_type, encoding = process_content(content)
		elif type(content)==bytes and not content_type:
			raise exceptions.TypeNotSetException("Message is bytes but type isnt set")
		if encoding:
			content_type += f"#encoding"
		self.content_type = content_type
		self.content = content
		self.metadata = metadata

	def serialize(self):
		bytes_data = json.dumps({
			"Type": self.content_type,
			"Metadata": self.metadata}).encode("utf-8")+b"\n"+self.content
		return bytes_data

	async def send(self): #recipient was set in User class
		sig_algo = self.recipient.client.sig_algorithm
		kem_algo = self.recipient.kem_algorithm

		public_key = self.recipient.public_key
		private_sign = self.recipient.client.private_sign

		data = self.serialize()
		data = pqc.signing.sign(private_sign, data, algorithm = sig_algo)
		data = pqc.encryption.encrypt(public_key, data, algorithm = kem_algo)

		await self.recipient.client.auth_request_post("direct_message", json_data = {"username": self.recipient.username}, raw_data = data)
