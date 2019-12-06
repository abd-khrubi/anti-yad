from .utils import format_time, get_machine_name
import sys
from IANA import DEBUG


class Logger:
	def __init__(self, file_name=None):
		self.file_name = file_name

	def print(self, message, error=False):
		print(message, file=sys.stderr if error else sys.stdout)
		if self.file_name:
			file = open(self.file_name, mode='a')
			file.write(message + '\n')
			file.close()

	def log(self, message, prefix=None, error=False):
		if prefix:
			self.print(f'[{get_machine_name()}] [{format_time()}] [{prefix}] {message}', error=error)
		else:
			self.print(f'[{get_machine_name()}] [{format_time()}] {message}', error=error)

	def error(self, message):
		self.log(message, prefix='ERROR', error=True)

	def debug(self, message):
		if DEBUG:
			self.log(message, prefix='DEBUG')

	def info(self, message: str):
		self.log(message, prefix='INFO')

	def warning(self, message):
		self.log(message, prefix='WARNING')
