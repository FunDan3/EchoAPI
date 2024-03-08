import pqcryptography as pqc
import json

from . import exceptions
from . import common

def process_content(content):
	t = type(content)
	if t == str:
		return content.encode("utf-8"), "text/plain", "utf-8"
	elif t in [float, int]:
		return str(content).encode("utf-8"), "text/plain", "utf-8"
	elif t in [dict or list]:
		return json.dumps(content).encode("utf-8"), "text/json", "utf-8"
	else:
		raise exceptions.UnrecognizedContentType(f"Client doenst know how to interprete '{t}' content type")

class IngoingMessage:
	author = None
	client = None
	content = None
	sent_time = None
	metadata = None
	def __init__(self, client, author_username):
		self.author = author_username
		self.client = client
	async def load(self):
		self.author = await self.client.fetch_user(self.author)
	async def read(self):
		raw_content = await self.client.auth_request_get("./read_direct_message", json_data = {"username": self.author.username})
		raw_content = raw_content.split(b"\n", 1)
		json_data = json.loads(raw_content[0])
		self.sent_at = json_data["sent_time"]
		encrypted_content = raw_content[1]
		signed_content = pqc.encryption.decrypt(self.client.private_key, encrypted_content)
		content = pqc.signing.verify(self.author.public_sign, signed_content).split(b"\n", 1)
		message_json = json.loads(content[0])
		self.content = content[1]
		split_type = message_json["Type"].split("#")
		type = split_type[0]
		if len(split_type) == 2:
			self.content = self.content.decode(split_type[1])
		self.metadata = common.folder(**message_json["Metadata"])

class OutgoingMessage: #outgoing
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
			content_type += f"#{encoding}"
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
