import utils.logger
from utils.utils import *
import subprocess
import threading
import sys

DEBUG = False
LOG_FOLDER = 'logs'  # put a directory relative path to write logs to

class IAmNotAlive:
	def __init__(self, log_file=None, check_interval=600, max_fails=10, force_screen_wake=False):
		self.force_screen_wake = force_screen_wake
		self.max_fails = max_fails
		self.check_interval = check_interval

		self.next_check = -1
		self.failed = 0
		self.success = 0
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
					self.logger.info(f'Found YAD (pid: {info[0][0]})')
				elif self.failed > 1:
					self.logger.warning(f'Found YAD (pid: {info[0][0]}. failed {self.failed} times')
				return int(info[0][0])
		except subprocess.CalledProcessError:
			self.logger.debug('\'ps -e\' is empty')
		return -1

	def unlock(self):
		self.logger.info('Unlocking')
		if self.force_screen_wake:
			execute_shell_cmd('xset dpms force on')

		execute_shell_cmd("loginctl unlock-session")

		if is_screen_locked(self.logger):
			self.logger.error('Failed to unlock screen')
			self.failed = self.max_fails

	def lock(self):
		self.logger.info('Locking')
		lock(logger=self.logger)

	def dismiss_yad(self):
		if self.failed >= self.max_fails:
			self.logger.error('Cannot dismiss YAD')
			return

		source, x, y = find_button_pos(self.logger)

		if source is not None:
			s = 'button image' if source == 0 else 'window\'s position'
			self.logger.info(f'Located dismiss button at {x, y} from {s}')
			force_dismiss_yad(x, y, logger=self.logger)
			self.failed += 1
			time.sleep(2)
			if self.check_yad() > 0:
				self.dismiss_yad()
			else:
				self.logger.info('Dismissed YAD')
				self.success += 1
				t = time.strftime("%I:%M:%S %p", time.localtime(time.time() + (60 * 60)))
				self.logger.info(f'Estimating next yad at {t}')

	def run(self):
		self.logger.info('Starting...')
		time.sleep(0.578)
		while True:
			try:
				pid = self.check_yad()
				self.failed = 0
				if pid > 0:
					self.original_mouse_pos = get_mouse_position(self.logger)
					locked = is_screen_locked(self.logger)
					if locked:
						wake_screen()
						self.unlock()
					screenshot_name = f'{get_host_name()}_{format_time(with_date=True)} - {self.success + 1}.png'
					screenshot(name=screenshot_name, logger=self.logger)
					self.dismiss_yad()
					mouse_move(*self.original_mouse_pos, self.logger)
					if locked:
						self.lock()
						execute_shell_cmd('xset dpms force standby')
				self.next_check = time.time() + self.check_interval
				time.sleep(self.check_interval)
			except Exception as e:
				self.logger.error(f"Something went wrong: {str(e)}")


class MultiThread(threading.Thread):
	def __init__(self, func, **kwargs):
		super().__init__()
		self.function = func
		self.func_args = kwargs

	def run(self):
		self.function(**self.func_args)


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

	if LOG_FOLDER:
		date = time.strftime('%d.%m.%Y')
		log_dir = rel_path(f"{LOG_FOLDER}/")
		if not os.path.exists(log_dir):
			os.mkdir(log_dir)

		bot = IAmNotAlive(log_file=f'{log_dir}/{get_host_name()}_{date}.log', force_screen_wake=True, check_interval=100)
	else:
		bot = IAmNotAlive(force_screen_wake=True, check_interval=100)
	try:
		thread1 = MultiThread(next_check_counter, yad_bot=bot)
		thread2 = MultiThread(bot.run)

		thread1.start()
		thread2.start()
	except:
		pass
