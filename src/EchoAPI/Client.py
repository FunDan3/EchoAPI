import pqcryptography as pqc
from pqcryptography import AES
import aiohttp
import asyncio
import json

from . import exceptions

class client:
	server_addr = None
	session = None
	server_privacy_policy = None
	server_terms_and_conditions = None
	def __init__(self, server_addr = None):
		if not server_addr:
			server_addr = "https://foxomet.ru:23515/"
		server_addr = ("https://" if not server_addr.startswith("http") else "") + server_addr + ("/" if not server_addr.endswith("/") else "")
		self.server_addr = server_addr
	async def verify_response(self, response):
		if response.status not in range(200, 300): #if not successful:
			text = await response.text()
			raise exceptions.FailedRequestError(f"Request failed with {response.status} status code: {text.decode('utf-8')}")
	async def base_request_get(self, path, json = None):
		if not json:
			json = {}
		request_variables = ""
		for key, value in json.items():
			request_variables += ("&" if request_variables else "?")
			request_variables += f"{key}={value}"
		path += request_variables
		async with self.session.get(self.server_addr + path) as response:
			await self.verify_response(response)
			return await response.text()

	async def connect(self):
		async with aiohttp.ClientSession() as session:
			self.session = session
			server_privacy_policy = await self.base_request_get("ReadPrivacyPolicy")
			server_terms_and_conditions = await self.base_request_get("ReadTermsAndConditions")
		print(server_privacy_policy)
	def start(self):
		asyncio.run(self.connect())
