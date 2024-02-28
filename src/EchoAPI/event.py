from . import exceptions

class event:
	on_connected_function = None
	def __init__(self):
		async def on_connected_function(self):
			pass
		self.on_connected_function = on_connected_function

	def on_connected(self): #decorator
		def init_wrapper(function):
			def _decorated_event_exception(*args, **kwargs):
				raise exceptions.DecoratedEventCalledException(f"Attempt to call decorated event '{function.__name__}'")
			self.on_connected_function = function
			return _decorated_event_exception
		return init_wrapper
