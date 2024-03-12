import pqcryptography as pqc
from pqcryptography import AES
import hashlib
import aiohttp
import asyncio
import pickle
import json

from . import common
from . import exceptions
from .User import User
from .event import event as event_creator
from .Message import IngoingMessage

class Client:
	user = None

	username = None
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

	inbox = None

	users_cache = None

	interface_version = "0.0.1" # Version of server-client interface.
	def __init__(self, server_addr = None):
		if not server_addr:
			server_addr = "https://foxomet.ru:23515/"
		server_addr = ("https://" if not server_addr.startswith("http") else "") + server_addr + ("/" if not server_addr.endswith("/") else "")
		self.server_addr = server_addr
		self.event = event_creator()
		self.users_cache = {}
		self.inbox = {}

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

	async def auth_request_post(self, path, json_data = None, raw_data = None):
		if not json_data:
			json_data = {}
		json_data["token"] = self.token
		json_data["login"] = self.username
		return await self.base_request_post(path, json_data, raw_data)

	async def auth_request_get(self, path, json_data = None):
		if not json_data:
			json_data = {}
		json_data["token"] = self.token
		json_data["login"] = self.username
		return await self.base_request_get(path, json_data)

	async def connect(self, ignore_incompatible_server = False):
		async with aiohttp.ClientSession() as session:
			self.session = session

			server_info = json.loads(await self.base_request_get("EchoMessagerServerInfo"))

			if server_info["version"] != self.interface_version and not ignore_incompatible_server:
				raise exceptions.IncompatibleServerException(f"Client's version is {self.interface_version}, and server's version is {server_info['version']}")

			self.server_privacy_policy, self.server_terms_and_conditions = await asyncio.gather(
				self.base_request_get("ReadPrivacyPolicy"),
				self.base_request_get("ReadTermsAndConditions"))
			self.server_privacy_policy = self.server_privacy_policy.decode("utf-8")
			self.server_terms_and_conditions = self.server_terms_and_conditions.decode("utf-8")
			await self.event.on_connected_function()

	async def register(self, username, password, kem_algorithm = None, sig_algorithm = None, store_container_on_server = True):
		if not kem_algorithm:
			kem_algorithm = pqc.default_kem_algorithm
		if not sig_algorithm:
			sig_algorithm = pqc.default_sig_algorithm
		token = common.hash(f"{username}{common.hash(password).hexdigest()}").hexdigest() #Attempt to hide password from server while still allowing for login by password and username. Password is used to encrypt container which may be stored on server. Probably should use TOTP or smth later...

		public_key, private_key = pqc.encryption.generate_keypair(kem_algorithm)
		public_sign, private_sign = pqc.signing.generate_signs(sig_algorithm)

		registration_json = {"login": username,
			"token": token,
			"kem_algorithm": kem_algorithm,
			"sig_algorithm": sig_algorithm}

		registration_data = public_key+public_sign
		await self.base_request_post("register", json_data = registration_json, raw_data = registration_data)

		self.username = username
		self.password = password
		self.token = token
		self.kem_algorithm = kem_algorithm
		self.sig_algorithm = sig_algorithm
		self.public_key = public_key
		self.private_key = private_key
		self.public_sign = public_sign
		self.private_sign = private_sign

		tasks = [self.message_loop(), self.event.on_login_function()]
		if store_container_on_server:
			tasks.append(self.store_container_on_server())
		await asyncio.gather(*tasks)
		self.user = await self.fetch_user(self.username)

	async def login(self, username, password, container = None):
		self.username = username
		self.password = password
		self.token = common.hash(f"{username}{common.hash(password).hexdigest()}").hexdigest() #Attempt to hide password from server while still allowing for login by password and username. Password is used to encrypt container which may be stored on server.
		server_container = await self.auth_request_post("login", json_data = {"ReadContainer": ("yes" if not container else "no")})
		self.load_container(container if container else server_container)
		self.user = await self.fetch_user(self.username)
		await asyncio.gather(self.message_loop(), self.event.on_login_function())

	def load_container(self, container):
		container = AES.decrypt(common.hash(self.password, "sha256").digest(), container)
		container = pickle.loads(container)
		for attribute, value in container.items():
			self_value = getattr(self, attribute)
			if self_value and self_value != value:
				raise exceptions.DeceptiveServerError(f"Attribute {attribute} value of container doesnt match with client's value. Probably server is deceptive.")
			setattr(self, attribute, value)

	async def store_container_on_server(self):
		encrypted_container = self.generate_container()
		await self.auth_request_post("store_container", raw_data = encrypted_container)

	def generate_container(self):
		data = {"username": self.username,
			"token": self.token,
			"kem_algorithm": self.kem_algorithm,
			"sig_algorithm": self.sig_algorithm,
			"public_key": self.public_key,
			"private_key": self.private_key,
			"public_sign": self.public_sign,
			"private_sign": self.private_sign}
		data = pickle.dumps(data)
		data = AES.encrypt(common.hash(self.password, "sha256").digest(), data)
		return data

	async def fetch_user(self, username):
		if username not in self.users_cache:
			user = User(self, username)
			await user.fetch_data()
			self.users_cache[username] = user
		else:
			user = self.users_cache[username]
		return user

	async def _index_inbox(self):
		index = await self.auth_request_get("/index_inbox")
		index = json.loads(index)
		return index

	async def message_loop(self):
		def generate_messages(count, author):
			local_messages = []
			for _ in range(count):
				local_messages.append(IngoingMessage(self, author))
			return local_messages
		while True:
			new_inbox = await self._index_inbox()
			messages = []
			for author, message_count in new_inbox.items():
				await self.fetch_user(author) # To add to cache
				if author in self.inbox:
					new_message_count = new_inbox[author] - self.inbox[author]
					if new_message_count > 0:
						messages += generate_messages(new_message_count, author)
				else:
					messages += generate_messages(message_count, author)
			self.inbox = new_inbox
			tasks = []
			for message in messages:
				tasks.append(message.load())
			await asyncio.gather(*tasks)

			for message in messages:
				await self.event.on_message_function(message)

			await asyncio.sleep(2)

	def start(self, ignore_incompatible_server = False):
		asyncio.run(self.connect(ignore_incompatible_server))

