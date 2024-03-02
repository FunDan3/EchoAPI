import asyncio
import json
import pqcryptography as pqc

class User:
	username = None
	client = None

	public_key = None
	public_sign = None
	kem_algorithm = None
	sig_algorithm = None

	def __init__(self, client, username):
		self.username = username
		self.client = client

	async def fetch_data(self):
		async def fetch_keys():
			keys = await self.client.base_request_get("read_public_keys", json_data = {"username": self.username})
			json_data, raw = keys.split(b"\n", 1)
			json_data = json.loads(json_data)
			public_key_size = pqc.encryption.get_details(algorithm = json_data["kem_algorithm"])["length_public_key"]
			self.public_key = raw[:public_key_size]
			self.public_sign = raw[public_key_size:]
			self.kem_algorithm = json_data["kem_algorithm"]
			self.sig_algorithm = json_data["sig_algorithm"]
		await asyncio.gather(fetch_keys())
