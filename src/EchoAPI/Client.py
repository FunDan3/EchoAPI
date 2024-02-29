import pqcryptography as pqc
from pqcryptography import AES
import hashlib
import aiohttp
import asyncio
import json

from . import common
from . import exceptions
from . import User
from .event import event as event_creator

class client:
	login = None
	password = None
	token = None
	kem_algorithm = None
	sig_algorithm = None

	public_key = None
	private_key = None
	public_sign = None
	private_sign = None

	server_addr = None
	session = None
	server_privacy_policy = None
	server_terms_and_conditions = None
	event_creator = None
	def __init__(self, server_addr = None):
		if not server_addr:
			server_addr = "https://foxomet.ru:23515/"
		server_addr = ("https://" if not server_addr.startswith("http") else "") + server_addr + ("/" if not server_addr.endswith("/") else "")
		self.server_addr = server_addr
		self.event = event_creator()


	async def verify_response(self, response):
		if response.status not in range(200, 300): #if not successful:
			text = await response.read()
			raise exceptions.FailedRequestError(f"Request failed with {response.status} status code: {text.decode('utf-8')}")

	async def base_request_get(self, path, json_data = None):
		if not json_data:
			json_data = {}
		request_variables = ""
		for key, value in json_data.items():
			request_variables += ("&" if request_variables else "?")
			request_variables += f"{key}={value}"
		path += request_variables
		async with self.session.get(self.server_addr + path) as response:
			await self.verify_response(response)
			return await response.read()

	async def base_request_post(self, path, json_data = None, raw_data = None):
		if not json_data:
			json_data = {}
		if not raw_data:
			raw_data = b""
		if type(raw_data) == str:
			raw_data = raw_data.encode("utf-8")
		to_send = json.dumps(json_data).encode("utf-8") + b"\n" + raw_data
		async with self.session.post(self.server_addr + path, data = to_send) as response:
			await self.verify_response(response)
			return await response.read()

	async def connect(self):
		async with aiohttp.ClientSession() as session:
			self.session = session
			self.server_privacy_policy, self.server_terms_and_conditions = await asyncio.gather(
				self.base_request_get("ReadPrivacyPolicy"),
				self.base_request_get("ReadTermsAndConditions"))
			self.server_privacy_policy = self.server_privacy_policy.decode("utf-8")
			self.server_terms_and_conditions = self.server_terms_and_conditions.decode("utf-8")
			await self.event.on_connected_function()

	async def register(self, login, password, kem_algorithm = None, sig_algorithm = None):
		if not kem_algorithm:
			self.kem_algorithm = pqc.default_kem_algorithm
		if not sig_algorithm:
			self.sig_algorithm = pqc.default_sig_algorithm
		self.login = login
		self.password = password
		self.token = common.hash(f"{login}{common.hash(password)}").hexdigest() #Attempt to hide password from server while still allowing for login by password and username. Password is used to encrypt container which may be stored on server.
		self.public_key, self.private_key = pqc.encryption.generate_keypair(self.kem_algorithm)
		self.public_sign, self.private_sign = pqc.signing.generate_signs(self.sig_algorithm)

		login_json = {"login": self.login,
			"token": self.token,
			"kem_algorithm": self.kem_algorithm,
			"sig_algorithm": self.sig_algorithm}

		login_data = self.public_key+self.public_sign
		await self.base_request_post("register", json_data = login_json, raw_data = login_data)

	def start(self):
		asyncio.run(self.connect())
