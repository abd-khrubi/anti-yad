import os
import subprocess
import time
from pynput.keyboard import Controller as KBController


def rel_path(filename):
	"""
	Gets the relative path of the given file
	:param filename: The file to get its relative path
	:return: the relative path of the given file
	"""
	return os.path.join(os.path.dirname(__file__), filename)


def execute_shell_cmd(cmd: str, logger=None):
	"""
	execute shell command and returns a list of the output lines
	"""
	res = subprocess.check_output(cmd, shell=True)
	res = str(res)[2:-1]
	res = list(filter(lambda x: len(x) > 0, res.split('\\n')))
	if logger:
		logger.debug(res)
	return res


def get_yad_id():
	"""
	Gets the ID of the window which has title 'Are you alive?'
	"""
	windows = execute_shell_cmd('xwininfo -root -tree|sed -e \'s/^ *//\'|grep -E \"^0x\"|awk \'{ print $1 }\'')
	windows = sorted(windows)
	for window in windows:
		window_name = execute_shell_cmd(f'xprop -id {window} WM_NAME')[0].split(' = ')
		if len(window_name) > 1 and window_name[1][1:-1] == 'Are you alive?':
			return window
	return None


def get_window_rect(window_id):
	"""
	Gets the position and dimensions of the given window ID
	"""
	attrs = execute_shell_cmd(f'xwininfo -id {window_id} -stats')
	x, y, w, h = -1, -1, -1, -1
	for line in attrs:
		line = line.strip()
		if line.startswith('Absolute upper-left X:'):
			x = int(line[len('Absolute upper-left X:'):].strip())
		if line.startswith('Absolute upper-left Y:'):
			y = int(line[len('Absolute upper-left Y:'):].strip())
		if line.startswith('Width'):
			w = int(line[len('Width:'):].strip())
		if line.startswith("Height"):
			h = int(line[len("Height:"):].strip())
	return x, y, w, h


def find_button_pos(logger):
	"""
	Get button position from window's position
	"""

	window_id = get_yad_id()
	if window_id is not None:
		base_x, base_y, width, height = get_window_rect(window_id)
		x = base_x + width - 20
		y = base_y + height - 15
		if x > 0 and y > 0:
			return 1, x, y

	logger.error('Fatal: Could not find button\'s position.')
	return None, None, None


def force_dismiss_yad(x, y, logger=None):
	try:

		window_id = get_yad_id()
		keyboard = KBController()
		execute_shell_cmd(f"xprop -id {window_id} -f  WM_HINTS 32c -set WM_HINTS '0x2, 0x0, 0x1, 0x4, 0x0'",
		                  logger=logger)
		mouse_click(x, y, logger=logger)
		keyboard.type(' ')
		return True
	except:
		return False


def is_screen_locked(logger):
	try:
		res = execute_shell_cmd('mate-screensaver-command -q')[0]
		return res.endswith('is active')
	except subprocess.CalledProcessError:
		logger.error('No response from mate-screensaver')
	return None

def wake_screen():
	execute_shell_cmd('xset dpms force on')
	pass


def get_machine_name():
	host = execute_shell_cmd('hostname')[0]
	user = execute_shell_cmd('whoami')[0]
	return f'{user}@{host}'


def get_host_name():
	return execute_shell_cmd('hostname')[0]


def format_time(seconds=None, with_date=False):
	if seconds:
		t = time.gmtime(seconds)
		return time.strftime(f'%H:%M:%S{"-%D" if with_date else ""}', t)
	else:
		return time.strftime(f'%I:%M:%S %p{"-%D" if with_date else ""}')


def lock(timeout=60, interval=10, logger=None):
	tries = int(timeout / interval)

	execute_shell_cmd('mate-screensaver-command -l')
	while tries > 0 and not is_screen_locked(logger):
		time.sleep(interval)
		wake_screen()
		execute_shell_cmd('killall mate-screensaver && matescreensaver &')
		execute_shell_cmd('mate-screensaver-command -l')
		tries -= 1

	if logger:
		if tries > 0:
			logger.info('Successfully locked the screen')
		else:
			logger.error('Failed to lock the screen')


def mouse_move(x, y, logger=None):
	execute_shell_cmd(rel_path(f"./XMouse move {x} {y}"), logger)


def mouse_click(x, y, logger=None):
	print(execute_shell_cmd(rel_path(f'./XMouse move-click {x} {y} 1'), logger))


def screenshot(name=None,logger=None):
	if name:
		execute_shell_cmd('cd ~/log/screenshots && scrot {name}', logger)
	else:
		execute_shell_cmd('cd ~/log/screenshots && scrot', logger)



def get_mouse_position(logger=None):
	out = execute_shell_cmd(rel_path(f'./XMouse position'), logger)[0]
	out = out.strip().split(',')
	x, y = 0, 0
	try:
		x = int(out[0])
		y = int(out[1])
	except:
		pass
	return x, y
