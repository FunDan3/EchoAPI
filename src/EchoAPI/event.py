from . import exceptions

class event:
	on_connected_function = None
	on_login_function = None
	def __init__(self):
		async def on_connected_function(self):
			pass
		async def on_login_function(self):
			pass
		self.on_connected_function = on_connected_function
		self.on_login_function = on_login_function

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
