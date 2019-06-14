import pyautogui
import utils.logger
from utils.utils import *
import subprocess
import threading
import sys

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True  # point mouse to (0, 0) in order to force stop the script

DEBUG = False
LOG_FILE = 'logs'  # put a directory relative path to write logs to

PASSWORD = 'Fuckoff'  # So safe  Much security`


class IAmNotAlive:
	def __init__(self, log_file=None, check_interval=600, max_fails=10):
		self.max_fails = max_fails
		self.check_interval = check_interval

		self.next_check = -1
		self.failed = 0
		self.estimated_next = -1
		self.logger = utils.logger.Logger(log_file)
		self.original_mouse_pos = None

	def check_yad(self):
		self.logger.debug('Searching for YAD process')
		try:
			res = execute_shell_cmd('ps -e | grep yad')
			processes = filter(lambda x: len(x) > 0, res)
			info = []
			for p in processes:
				process = list(filter(lambda x: x != '', p.split(' ')))
				info.append(process)
			if len(info) != 0:
				if self.failed == 0:
					self.logger.info(f'Found YAD (pid: {info[0][0]}')
				elif self.failed > 1:
					self.logger.warning(f'Found YAD (pid: {info[0][0]}. failed {self.failed} times')
				return int(info[0][0])
		except subprocess.CalledProcessError:
			self.logger.debug('\'ps -e\' is empty')
		return -1

	def unlock(self, password):
		self.logger.info('Unlocking')

		# change keyboard layout to english
		current_layout = get_current_layout()
		change_keyboard_layout()

		temp_pause = pyautogui.PAUSE
		pyautogui.PAUSE = 2
		pyautogui.moveTo(None, 100, duration=0.1)  # To wake the screen
		pyautogui.click(980, 600, duration=0.5)
		pyautogui.PAUSE = 0.5
		pyautogui.typewrite(password, interval=0.1)
		pyautogui.typewrite('\n')
		pyautogui.PAUSE = temp_pause

		# change keyboard layout back
		change_keyboard_layout(current_layout)

		time.sleep(2)
		if is_screen_locked(self.logger):
			self.logger.error('Failed to unlock screen')
			self.failed = self.max_fails

	def lock(self):
		self.logger.info('Locking')
		pyautogui.hotkey('ctrleft', 'altleft', 'l')

	def dismiss_yad(self):
		if self.failed >= self.max_fails:
			self.logger.error('Cannot dismiss YAD')
			return

		source, x, y = find_button_pos(self.logger)

		if source is not None:
			s = 'button image' if source == 0 else 'window\'s position'
			self.logger.info(f'Located dismiss button at {x, y} from {s}')
			pyautogui.click(x, y, duration=0.2)
			self.failed += 1
			time.sleep(3)
			if self.check_yad() > 0:
				self.dismiss_yad()
			else:
				self.logger.info('Dismissed YAD')
				t = time.strftime("%I:%M:%S %p", time.localtime(time.time() + (60 * 60)))
				self.logger.info(f'Estimating next yad at {t}')

	def run(self):
		self.logger.info('Starting...')
		time.sleep(0.5)
		while True:
			try:
				pid = self.check_yad()
				self.failed = 0
				if pid > 0:
					self.original_mouse_pos = pyautogui.position()
					locked = is_screen_locked(self.logger)
					if locked:
						self.unlock(PASSWORD)
					self.dismiss_yad()
					if locked:
						self.lock()

					pyautogui.moveTo()
				else:
					self.logger.info('Nope')
				self.next_check = time.time() + self.check_interval
				time.sleep(self.check_interval)
			except Exception as e:
				self.logger.error(f"Something went wrong: {str(e)}")


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
			# print(time.mktime(t))
			# if time.mktime(t) < 0:
			# 	t = 0
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

		bot = IAmNotAlive(log_file=f'{log_dir}/{date}.log')
	else:
		bot = IAmNotAlive()
	try:
		thread1 = MultiThread(next_check_counter, bot)
		thread2 = MultiThread(bot.run)

		thread1.start()
		thread2.start()
	except Exception as _:
		pass
