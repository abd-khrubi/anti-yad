import os
import time
import pyautogui
import subprocess
import threading
import sys
from fuck_the_yad import get_position

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True  # point mouse to (0, 0) in order to force stop the script

DEBUG = False
LOG_FILE = 'logs'  # put a directory relative path to write logs to

PASSWORD = 'Fuckoff'  # So safe  Much security`


def format_time(seconds=None):
	if seconds:
		t = time.gmtime(seconds)
		return time.strftime('%H:%M:%S', t)
	else:
		return time.strftime("%I:%M:%S %p")


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
			self.print(f'[{format_time()}] [{prefix}] {message}', error=error)
		else:
			self.print(f'[{format_time()}] {message}', error=error)

	def error(self, message):
		self.log(message, prefix='ERROR', error=True)

	def debug(self, message):
		if DEBUG:
			self.log(message, prefix='DEBUG')

	def info(self, message: str):
		self.log(message, prefix='INFO')

	def warning(self, message):
		self.log(message, prefix='WARNING')


class AntiYad:
	BUTTON_POSITION = (1090, 655)  # x,y position of the yes button

	def __init__(self, log_file=None, check_interval=600, max_fails=10):
		self.check_interval = check_interval
		self.failed = 0
		self.max_fails = max_fails
		self.next_check = -1
		self.estimated_next = -1
		self.logger = Logger(log_file)
		self.original_mouse_pos = None

	def check_yad(self):
		self.logger.debug('Searching for any YAD process')
		try:
			res = str(subprocess.check_output('ps -e | grep yad', shell=True))[2:-1]
			processes = list(filter(lambda x: len(x) > 0, res.split('\\n')))
			info = []
			for p in processes:
				process = list(filter(lambda x: x != '', p.split(' ')))
				info.append(process)
			if len(processes) > 0:
				# at this point we know that there is at least one yad process
				if self.failed == 0:
					self.logger.info(f'Found a yad (pid: {info[0][0]})')
				elif self.failed > 1:  # "failed 1 times" ??
					self.logger.warning(f'Found a yad (pid: {info[0][0]}) - failed {self.failed} times')
				return int(info[0][0])
		except subprocess.CalledProcessError:
			self.logger.debug('`ps -e` is empty')
		return -1

	def is_locked(self):
		try:
			res = str(subprocess.check_output('mate-screensaver-command -q', shell=True))[2:-1]
			res = res.split('\\n')[0]
			return res.endswith('is active')
		except subprocess.CalledProcessError:
			pass
		self.logger.error("No response from mate-screensaver")
		return False

	def unlock(self, password):
		os.system('python3 /cs/usr/abd_khrubi/log/system-logger.py yad')
		self.logger.info("Unlocking")
		temp_pause = pyautogui.PAUSE
		pyautogui.PAUSE = 2
		pyautogui.moveTo(None, 100, duration=0.1)  # To wake the screen
		pyautogui.click(980, 600, duration=0.5)
		pyautogui.PAUSE = 0.5
		pyautogui.typewrite(password, interval=0.1)
		pyautogui.typewrite('\n')
		pyautogui.PAUSE = temp_pause
		time.sleep(2)
		if self.is_locked():
			self.logger.error('Failed to unlock... Skipping this check.')
			self.failed = self.max_fails

	def lock(self):
		self.logger.info('Locking')
		pyautogui.hotkey('ctrlleft', 'altleft', 'l')

	def click_the_yad(self):
		if self.failed >= self.max_fails:
			self.logger.error('Cannot dismiss yad GUI')
			return
		source, x, y = get_position(self.logger)
		# if not x or not y:  # What if the button is at (0, 0)
		if x is None or y is None:
			x, y = self.BUTTON_POSITION
			self.logger.warning('Could not determine dismiss button position. Using default location.')
		else:
			s = ''
			if source == 0:
				s = 'button image'
			elif source == 1:
				s = 'window position'
			self.logger.info(f'Located dismiss button at {x, y} from {s}')
		pyautogui.click(x, y, duration=0.2)
		self.failed += 1
		time.sleep(3)
		if self.check_yad() > 0:
			self.click_the_yad()
		else:
			self.logger.info('Dismissed Yad')
			t = time.strftime("%I:%M:%S %p", time.localtime(time.time() + (60 * 60)))
			self.logger.info(f'Estimating next yad at {t}')

	def run(self):
		self.logger.log('Starting Anti yad')
		time.sleep(1.5)
		while True:
			pid = self.check_yad()
			self.failed = 0
			if pid > 0:
				self.original_mouse_pos = pyautogui.position()
				locked = self.is_locked()
				if locked:
					self.unlock(PASSWORD)
				self.click_the_yad()
				if locked:
					self.lock()
				pyautogui.moveTo(*self.original_mouse_pos)
				self.original_mouse_pos = None
			else:
				self.logger.info('Nope')
			self.next_check = time.time() + self.check_interval
			time.sleep(self.check_interval)


class MultiThread(threading.Thread):
	def __init__(self, func, *args):
		super().__init__()
		self.function = func
		self.func_args = args

	def run(self):
		self.function(*self.func_args)


def next_check_counter(yad_bot):
	"""
	Changes the title of the console to show when the next check is
	"""
	if not (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()):  # Do not print anything if the console is not atty
		return
	while True:
		if yad_bot.next_check > 0:
			t = time.gmtime(yad_bot.next_check - time.time())
			s = time.strftime("%H:%M:%S", t)
			print(f'\33]0;Next check in {s}\a', end='', flush=True)
			time.sleep(1)


def rel_path(filename):
	return os.path.join(os.path.dirname(__file__), filename)


if __name__ == '__main__':
	subprocess.call('clear', shell=True)

	if LOG_FILE:
		date = time.strftime('%d.%m.%Y')
		log_dir = rel_path(f"{LOG_FILE}/")
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)

		bot = AntiYad(log_file=f'{log_dir}/{date}.log')
	else:
		bot = AntiYad()
	try:
		thread1 = MultiThread(next_check_counter, bot)
		thread2 = MultiThread(bot.run)

		thread1.start()
		thread2.start()
	except:
		pass
