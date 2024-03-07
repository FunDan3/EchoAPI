from . import exceptions

async def on_connected_function():
	pass
async def on_login_function():
	pass
async def on_message(message):
	pass

class event:
	on_connected_function = None
	on_login_function = None
	on_message_function = None
	def __init__(self):
		self.on_connected_function = on_connected_function
		self.on_login_function = on_login_function
		self.on_message_function = on_message
	def on_connected(self, function): #decorator
		def _decorated_event_exception(*args, **kwargs):
			raise exceptions.DecoratedEventCalledException(f"Attempt to call decorated event '{function.__name__}'")
		self.on_connected_function = function
		return _decorated_event_exception

	def on_login(self, function): #decorator
		def _decorated_event_exception(*args, **kwargs):
			raise exceptions.DecoratedEventCalledException(f"Attempt to call decorated event '{function.__name__}'")
		self.on_login_function = function
		return _decorated_event_exception

	def on_message(self, function): #decorator
		def _decorated_event_exception(*args, **kwargs):
			raise exceptions.DecoratedEventCalledException(f"Attempt to call decorated event '{function.__name__}'")
		self.on_message_function = function
		return _decorated_event_exception

