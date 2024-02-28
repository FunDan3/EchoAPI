import pqcryptography as pqc
from pqcryptography import AES
import hashlib
import aiohttp
import asyncio
import json

from . import exceptions
from .event import event as event_creator

class client:
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
			self.server_privacy_policy, self.server_terms_and_conditions = await asyncio.gather(
				self.base_request_get("ReadPrivacyPolicy"),
				self.base_request_get("ReadTermsAndConditions"))
			await self.event.on_connected_function()

	def start(self):
		asyncio.run(self.connect())
